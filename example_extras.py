import stge
from stge.extras import Vector2, Surface


background = Surface(80, 80)
pawn = Surface(5, 5, (255, 255, 0))
screen = Surface(80, 80)


def setup():
    center = Vector2(40, 40)
    for x in range(background.w):
        for y in range(background.h):
            value = int(Vector2(x, y).distance_to(center) / (40 * 1.5) * 255)
            background[x, y] = (value, value, value)

    screen.blit(background)

    pawn[1, 1] = (0, 0, 0)
    pawn[3, 1] = (0, 0, 0)
    pawn[1, 3] = (0, 0, 0)
    pawn[2, 3] = (0, 0, 0)
    pawn[3, 3] = (0, 0, 0)

    return 5, 5


def loop(state):
    x, y = state

    rect = pawn.get_rect()
    rect.center = x, y

    screen.blit(background, rect.topleft, rect)

    for key in stge.keypresses():
        if key == "UP":
            y -= 1
        elif key == "DOWN":
            y += 1
        elif key == "RIGHT":
            x += 1
        elif key == "LEFT":
            x -= 1
        elif key in ["q", "Q"]:
            stge.quit()

    rect.center = x, y
    screen.blit(pawn, rect.topleft)
    stge.pixels(screen.get_pixels())

    return x, y


stge.run(setup, loop)
