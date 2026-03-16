import sys
import shutil
import platform
import time
import threading
import queue
from dataclasses import dataclass, field
import atexit
from typing import Any, Callable


@dataclass
class StgeState:
    frame_time_target: float = 0.0
    delta_time: float = 0.0
    frame_start: float = 0.0
    frame_buffer: list[str] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    char_queue: queue.Queue = field(default_factory=queue.Queue)
    input_thread: threading.Thread | None = None
    input_thread_exception: Exception | None = None


class NoKey(Exception):
    pass


class Rect:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

    @property
    def topleft(self):
        return self.x, self.y

    @topleft.setter
    def topleft(self, value):
        self.x, self.y = round(value[0]), round(value[1])

    @property
    def center(self) -> tuple[int, int]:
        return int(self.x + self.w / 2), int(self.y + self.h / 2)

    @center.setter
    def center(self, value: tuple[int, int]):
        self.x, self.y = value[0] - int(self.w / 2), value[1] - int(self.h / 2)

    @property
    def top(self) -> int:
        return self.y

    @top.setter
    def top(self, value):
        self.y = value

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @bottom.setter
    def bottom(self, value):
        self.y = value - self.h

    @property
    def left(self) -> int:
        return self.x

    @left.setter
    def left(self, value):
        self.x = value

    @property
    def right(self) -> int:
        return self.x + self.w

    @right.setter
    def right(self, value):
        self.x = value - self.w

    def collide(self, rect: "Rect") -> bool:
        """Renvoi si collision avec un autre Rect"""

        on_x = self.left < rect.right and self.right > rect.left
        on_y = self.top < rect.bottom and self.bottom > rect.top

        return on_x and on_y


class Vector2:
    def __init__(self, x: int | float, y: int | float):
        self.x = x
        self.y = y

    @property
    def xy(self) -> tuple[int, int]:
        return (self.x, self.y)

    @xy.setter
    def xy(self, value: tuple[int, int]):
        self.x, self.y = value

    def distance_to(self, vector: "Vector2") -> int:
        """Renvoie la distance entre soit et un autre Vector2"""
        dx, dy = vector.x - self.x, vector.y - self.y
        distance = int(((dx**2) + (dy**2)) ** (1 / 2))

        return distance


class Surface:
    _COLORS = {
        0: (0, 0, 0),  # Black
        1: (255, 0, 0),  # Red
        2: (0, 0, 255),  # Green
        3: (0, 255, 0),  # Blue
    }

    def __init__(self, w: int, h: int):
        self.surface = self.init(w, h)
        self.refresh()

    @property
    def w(self) -> int:
        return len(self.surface[0])

    @property
    def h(self) -> int:
        return len(self.surface)

    def init(self, width, height) -> list[list[int]]:
        return [[0] * width for line in range(height)]

    def refresh(self) -> None:
        """Permet de set la surface au noir ( reset )"""
        self.surface = [[0] * self.w for _ in range(self.h)]

    def fill(self, color: int) -> None:
        """Remplie la surface d'une couleur donner en int ( ref au dico des couleurs )"""
        self.surface = [[color] * self.w for _ in range(self.h)]

    def load(self, image: list[list[int]]) -> None:
        """Permet de charger un image ( list de list ) ! FORME RECTANGULAIRE !"""
        # Verification de l'image
        if not image:
            return
        if not image[0]:
            return
        if type(image[0][0]) != int:
            return

        # Verification de l'image de la forme
        len_line = len(image[0])
        for line in image:
            lenght = len(line)
            if lenght != len_line:
                return

        # Au cas ou l'image est un tuple
        self.surface = [list(line) for line in image]
        # Update taille de la surface
        self.h = len(self.surface)
        self.w = len(self.surface[0]) if self.h > 0 else 0

    def blit(self, surface: "Surface", rect_s: Rect) -> None:
        """Dessiner une Surface sur soit"""
        dest_rect = self.get_rect()
        # Verifiaction si les surface se superpose
        if not dest_rect.collide(rect_s):
            return

        # Calcul de debut et fin de la zone de superposition
        dest_x_start = max(0, rect_s.x)
        dest_y_start = max(0, rect_s.y)
        dest_x_end = min(self.w, rect_s.x + rect_s.w)
        dest_y_end = min(self.h, rect_s.y + rect_s.h)

        # Calcul de la longeur et largueur de la zone
        draw_w = dest_x_end - dest_x_start
        draw_h = dest_y_end - dest_y_start

        # Calcul du debut du slicing de la source
        src_x_start = dest_x_start - rect_s.x
        src_y_start = dest_y_start - rect_s.y

        # Copie par Slicing
        for y in range(draw_h):
            d_y = dest_y_start + y
            s_y = src_y_start + y

            self.surface[d_y][dest_x_start:dest_x_end] = surface.surface[s_y][
                src_x_start : src_x_start + draw_w
            ]

    def flip(self) -> None:
        """Permet de metre a jour notre Terminal"""
        render_display = [
            [self._COLORS.get(x, (0, 0, 0)) for x in line] for line in self.surface
        ]

        pixels(render_display)

    def get_rect(self) -> Rect:
        """Renvoi le rect de la Surface"""
        return Rect(0, 0, self.w, self.h)


_state = StgeState()

IS_WINDOWS = platform.system() == "Windows"


if IS_WINDOWS:
    import msvcrt

    def enter_raw():
        """Put the terminal in raw mode"""
        pass

    def exit_raw():
        """Exit terminal raw mode"""
        pass

    def getch():  # type: ignore
        """Get a character from standard input"""
        b = msvcrt.getch()  # type: ignore

        if b in (b"\x00", b"\xe0"):
            b = msvcrt.getch()  # type: ignore
            return {
                b"H": "UP",
                b"P": "DOWN",
                b"K": "LEFT",
                b"M": "RIGHT",
            }.get(b, "")

        try:
            return {
                b"\r": "ENTER",
                b"\n": "ENTER",
                b"\t": "TAB",
                b"\x1b": "",
                b"\x08": "BACKSPACE",
                b"\x03": "SIGINT",
                b" ": "SPACE",
            }.get(b, b.decode("ascii"))
        except UnicodeDecodeError:
            return ""


else:
    import tty
    import termios

    __fd = sys.stdin.fileno()
    __old = termios.tcgetattr(__fd)

    def enter_raw():
        """Put the terminal in raw mode"""
        tty.setraw(__fd)

    def exit_raw():
        """Exit terminal raw mode"""
        termios.tcsetattr(__fd, termios.TCSADRAIN, __old)

    def getch():
        """Get a character from standard input"""
        ch = sys.stdin.read(1)
        while ch == "\x1b":
            ch = sys.stdin.read(1)
            if ch in ("[", "O"):
                ch = sys.stdin.read(1)
                return {
                    "A": "UP",
                    "B": "DOWN",
                    "C": "RIGHT",
                    "D": "LEFT",
                }.get(ch, "")

        return {
            "\r": "ENTER",
            "\n": "ENTER",
            "\t": "TAB",
            "\x7f": "BACKSPACE",
            "\x03": "SIGINT",
            " ": "SPACE",
        }.get(ch, ch)


def _input_thread():
    try:
        while True:
            ch = getch()
            if len(ch) > 0:
                _state.char_queue.put(ch)
    except Exception as e:
        _state.input_thread_exception = e


def _read_key():
    try:
        ch = _state.char_queue.get_nowait()
        if ch == "SIGINT":
            raise KeyboardInterrupt
        return ch
    except queue.Empty:
        raise NoKey


def _flush():
    frame = "".join(_state.frame_buffer)
    _state.frame_buffer.clear()
    sys.stdout.write(frame)
    sys.stdout.flush()


def write(msg: Any):
    """Write something at the current cursor position"""
    _state.frame_buffer.append(str(msg))


def clear():
    """Clear the terminal"""
    write("\033[3J\033[2J\033[H")


def move(column: int, row: int):
    """Move the cursor to a new position"""
    write(f"\033[{row + 1};{column + 1}H")


def set_fg(red: int, green: int, blue: int):
    """Change the color of font"""
    write(f"\033[38;2;{red};{green};{blue}m")


def reset_fg():
    """Get the default font color back"""
    write("\033[39m")


def set_bg(red: int, green: int, blue: int):
    """Change the background color of font"""
    write(f"\033[48;2;{red};{green};{blue}m")


def reset_bg():
    """Get the default font background color back"""
    write("\033[49m")


def set_bold():
    """Set the font in bold mode"""
    write("\033[1m")


def set_italic():
    """Set the font in italic mode"""
    write("\033[3m")


def set_underline():
    """Set the font in underlined mode"""
    write("\033[4m")


def set_strikethrough():
    """Set the font in strikethrough mode"""
    write("\033[9m")


def reset_bold():
    """Reset the font from bold mode"""
    write("\033[22m")


def reset_italic():
    """Reset the font from italic mode"""
    write("\033[23m")


def reset_underline():
    """Reset the font from underlined mode"""
    write("\033[24m")


def reset_strikethrough():
    """Reset the font from strikethrough mode"""
    write("\033[29m")


def reset():
    """Reset the font to its default"""
    write("\033[0m")


def write_at(
    column: int,
    row: int,
    msg: Any,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
):
    """Write something at a specific position ans with a specific style. The style is reseted afterward."""
    move(column, row)
    if fg is not None:
        set_fg(*fg)
    if bg is not None:
        set_bg(*bg)
    if bold:
        set_bold()
    if italic:
        set_italic()
    if underline:
        set_underline()
    if strikethrough:
        set_strikethrough()
    write(msg)
    reset()


def pixels(rows: list[list[tuple[int, int, int]]], column: int = 0, row: int = 0):
    """Display a grid of pixels with Half Block Characters. `rows` must be a list of rows of colors."""
    move(column, row)
    for i in range(len(rows) // 2):
        for j in range(len(rows[i])):
            set_fg(*rows[i * 2][j])
            set_bg(*rows[i * 2 + 1][j])
            write("▀")
        row += 1
        move(column, row)
    if len(rows) % 2 == 1:
        reset_bg()
        for j in range(len(rows[-1])):
            set_fg(*rows[-1][j])
            write("▀")
    reset()


def size() -> tuple[int, int]:
    """Returns the size of the terminal in characters. (columns, rows)"""
    size = shutil.get_terminal_size()
    return size.columns, size.lines


def _exception_hook(exc_type, exc_value, exc_traceback):
    clear()
    _restore()
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def init(fps):
    """Initialize STGE. Must be called before anything else."""
    _state.frame_time_target = 1 / fps

    _state.input_thread = threading.Thread(target=_input_thread, daemon=True)
    _state.input_thread.start()

    write("\033[?25l")
    enter_raw()
    atexit.register(_restore)
    sys.excepthook = _exception_hook
    _flush()


def _restore():
    exit_raw()
    write("\033[?25h")
    _flush()


def quit():
    """Quit the program"""
    sys.exit()


def _keypresses():
    res = []
    while True:
        try:
            key = _read_key()
            res.append(key)
        except NoKey:
            break
    return res


def keypresses() -> list[str]:
    """Returns the keys pressed from last frame"""
    return _state.keys


def begin_frame():
    """Begin a Frame. Must be called at the beginning of each frame."""
    assert _state.input_thread is not None, "init() must be called before begin_frame()"
    if not _state.input_thread.is_alive():
        if _state.input_thread_exception is not None:
            raise _state.input_thread_exception
        else:
            raise Exception("Input Thread Crached")
    _state.frame_start = time.perf_counter()
    _state.keys = _keypresses()
    clear()


def end_frame():
    """End a frame. Must be called at the end of each frame"""
    _flush()
    remaining = _state.frame_time_target - (time.perf_counter() - _state.frame_start)
    if remaining > 0:
        time.sleep(remaining)
    _state.delta_time = time.perf_counter() - _state.frame_start


def delta_time() -> float:
    """Get the ellapsed time from last frame in seconds."""
    return _state.delta_time


def run(setup: Callable[[], Any], loop: Callable[[Any], Any], fps: int = 30):
    """Runs a game loop. This function takes care of calling `stge.init()`, `stge.begin_frame()`
    and `stge.end_frame()`. You must call `stge.quit()` to terminate the game loop.

    - `setup`: is a collable that returns the initial app state.
    - `loop`: is a callable that receive the app state as an argument and returns that state for
              the next `loop` call.
    - `fps`: is the target frame per seconds

    It does basically:

    ```
    stge.init(fps)
    state = setup()
    while True:
        stge.begin_frame()
        state = loop(state)
        stge.end_frame()
    ```
    """
    init(fps)
    state = setup()
    while True:
        begin_frame()
        state = loop(state)
        end_frame()
