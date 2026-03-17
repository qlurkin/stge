from __future__ import annotations
import stge


class Rect:
    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

    @property
    def topleft(self) -> tuple[int, int]:
        return self.x, self.y

    @topleft.setter
    def topleft(self, value: tuple[float, float]):
        self.x, self.y = int(value[0]), int(value[1])

    @property
    def center(self) -> tuple[int, int]:
        return int(self.x + self.w / 2), int(self.y + self.h / 2)

    @center.setter
    def center(self, value: tuple[float, float]):
        self.x, self.y = (
            int(value[0] - self.w / 2),
            int(value[1] - self.h / 2),
        )

    @property
    def top(self) -> int:
        return self.y

    @top.setter
    def top(self, value: float):
        self.y = int(value)

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @bottom.setter
    def bottom(self, value: float):
        self.y = int(value) - self.h

    @property
    def left(self) -> int:
        return self.x

    @left.setter
    def left(self, value: float):
        self.x = int(value)

    @property
    def right(self) -> int:
        return self.x + self.w

    @right.setter
    def right(self, value: float):
        self.x = int(value) - self.w

    def collide(self, rect: Rect) -> bool:
        """Test collision with another Rect"""

        on_x = self.left < rect.right and self.right > rect.left
        on_y = self.top < rect.bottom and self.bottom > rect.top

        return on_x and on_y


class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @property
    def xy(self) -> tuple[float, float]:
        """Returns the vector as a tuple"""
        return (self.x, self.y)

    @xy.setter
    def xy(self, value: tuple[float, float]):
        """Unpack from a tuple"""
        self.x, self.y = value

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> Vector2:
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> Vector2:
        return Vector2(self.x / other, self.y / other)

    def length(self) -> float:
        """Returns the length of the vector"""
        return (self.x**2 + self.y**2) ** (1 / 2)

    def distance_to(self, vector: Vector2) -> float:
        """Returns the distance to another vector"""
        return (vector - self).length()

    def normalize(self):
        """Returns the normalized vector"""
        return self / self.length()


class Surface:
    """Helper class to manage a 2D array of pixels.
    Surfaces manages their own storage and keep references to that storage valid.
    """

    def __init__(self, w: int, h: int, color: tuple[int, int, int] = (0, 0, 0)):
        self.surface = [[color for column in range(w)] for line in range(h)]

    @property
    def w(self) -> int:
        return len(self.surface[0])

    @property
    def h(self) -> int:
        return len(self.surface)

    def __setitem__(self, index: tuple[int, int], value: tuple[int, int, int]):
        """Put a color at a specific coordinate (x, y)"""
        column, line = index
        self.surface[line][column] = value

    def fill(self, color: tuple[int, int, int]):
        """Fill the surface with a color"""
        for line in range(self.h):
            for column in range(self.w):
                self[column, line] = color

    @staticmethod
    def load(pixels: list[list[tuple[int, int, int]]]) -> Surface:
        """Create a new Surface and copy `pixels` into it"""
        surface = Surface(len(pixels[0]), len(pixels))
        for line in range(len(surface.surface)):
            surface.surface[line][:] = pixels[line]
        return surface

    def blit(
        self, source: Surface, dest: tuple[int, int] = (0, 0), area: Rect | None = None
    ):
        """Draw another Surface onto this one"""

        if area is None:
            area = source.get_rect()

        dest_rect = Rect(dest[0], dest[1], area.w, area.h)

        if not dest_rect.collide(self.get_rect()):
            stge.write_at(5, 5, "No Collide")
            return

        dest_x_start = max(0, dest_rect.x)
        dest_y_start = max(0, dest_rect.y)
        dest_x_end = min(self.w, dest_rect.right)
        dest_y_end = min(self.h, dest_rect.bottom)

        draw_w = dest_x_end - dest_x_start
        draw_h = dest_y_end - dest_y_start

        for y in range(draw_h):
            d_y = dest_y_start + y
            s_y = area.y + y

            self.surface[d_y][dest_x_start:dest_x_end] = source.surface[s_y][
                area.x : area.x + draw_w
            ]

    def get_pixels(self) -> list[list[tuple[int, int, int]]]:
        """Get a reference to this surface pixels. This reference will remain valid."""
        return self.surface

    def get_rect(self) -> Rect:
        """Returns the Rect of the Surface"""
        return Rect(0, 0, self.w, self.h)
