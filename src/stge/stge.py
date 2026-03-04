import sys
import shutil
import platform
import time
import threading
import queue
from dataclasses import dataclass, field
import atexit


@dataclass
class StgeState:
    frame_time_target: float = 0.0
    delta_time: float = 0.0
    frame_start: float = 0.0
    frame_buffer: list[str] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    char_queue: queue.Queue = field(default_factory=queue.Queue)


class NoKey(Exception):
    pass


_state = StgeState()

IS_WINDOWS = platform.system() == "Windows"


if IS_WINDOWS:
    import msvcrt

    def enter_raw():
        pass

    def exit_raw():
        pass

    def getch():  # type: ignore
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
        tty.setraw(__fd)

    def exit_raw():
        termios.tcsetattr(__fd, termios.TCSADRAIN, __old)

    def getch():
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


def input_thread():
    while True:
        ch = getch()
        if len(ch) > 0:
            _state.char_queue.put(ch)


def read_key():
    try:
        ch = _state.char_queue.get_nowait()
        if ch == "SIGINT":
            _restore()
            raise KeyboardInterrupt
        return ch
    except queue.Empty:
        raise NoKey


def flush():
    frame = "".join(_state.frame_buffer)
    _state.frame_buffer.clear()
    sys.stdout.write(frame)
    sys.stdout.flush()


def write(msg):
    _state.frame_buffer.append(str(msg))


def clear():
    write("\033[2J\033[H")


def move(column, row):
    write(f"\033[{row + 1};{column + 1}H")


def set_fg(red, green, blue):
    write(f"\033[38;2;{red};{green};{blue}m")


def reset_fg():
    write("\033[39m")


def set_bg(red, green, blue):
    write(f"\033[48;2;{red};{green};{blue}m")


def reset_bg():
    write("\033[49m")


def set_bold():
    write("\033[1m")


def set_italic():
    write("\033[3m")


def set_underline():
    write("\033[4m")


def set_strikethrough():
    write("\033[9m")


def reset_bold():
    write("\033[22m")


def reset_italic():
    write("\033[23m")


def reset_underline():
    write("\033[24m")


def reset_strikethrough():
    write("\033[29m")


def reset():
    write("\033[0m")


def write_at(
    column,
    row,
    string,
    fg=None,
    bg=None,
    bold=False,
    italic=False,
    underline=False,
    strikethrough=False,
):
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
    write(str(string))
    reset()


def pixels(rows, column=0, row=0):
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


def size():
    size = shutil.get_terminal_size()
    return size.columns, size.lines


def init(fps):
    _state.frame_time_target = 1 / fps

    threading.Thread(target=input_thread, daemon=True).start()

    write("\033[?25l")
    enter_raw()
    atexit.register(_restore)
    flush()


def _restore():
    exit_raw()
    write("\033[?25h")
    flush()


def quit():
    sys.exit()


def _keypresses():
    res = []
    while True:
        try:
            key = read_key()
            res.append(key)
        except NoKey:
            break
    return res


def keypresses():
    return _state.keys


def begin_frame():
    _state.frame_start = time.perf_counter()
    _state.keys = _keypresses()
    clear()


def end_frame():
    flush()
    remaining = _state.frame_time_target - (time.perf_counter() - _state.frame_start)
    if remaining > 0:
        time.sleep(remaining)
    _state.delta_time = time.perf_counter() - _state.frame_start


def delta_time():
    return _state.delta_time


def ensure_tuple(value):
    if not isinstance(value, tuple):
        if value is not None:
            return (value,)
        return tuple()
    return value


def run(setup, loop, fps=30):
    init(fps)
    state = ensure_tuple(setup())
    while True:
        begin_frame()
        state = ensure_tuple(loop(*state))
        end_frame()
