import stge
import colorsys
import random

PIECE_I = [
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 0, 0],
]

PIECE_L = [
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 0],
]

PIECE_J = [
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 0],
]

PIECE_O = [
    [0, 0, 0, 0],
    [0, 1, 1, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 0],
]

PIECE_T = [
    [0, 0, 0, 0],
    [1, 1, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
]

PIECE_Z = [
    [0, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 0],
]

PIECE_S = [
    [0, 0, 0, 0],
    [0, 1, 1, 0],
    [1, 1, 0, 0],
    [0, 0, 0, 0],
]

PIECES = [PIECE_O, PIECE_S, PIECE_T, PIECE_Z, PIECE_I, PIECE_J, PIECE_L]
COLORS = [
    (0xFF, 0xAD, 0xAD),
    (0xFF, 0xD6, 0xA5),
    (0xFD, 0xFF, 0xB6),
    (0xCA, 0xFF, 0xBF),
    (0x9B, 0xF6, 0xFF),
    (0xA0, 0xC4, 0xFF),
    (0xBD, 0xB2, 0xFF),
]

WALL_KICKS = [(0, 0), (-1, 0), (1, 0), (0, -1)]


def adjust_luminosity(rgb, percent):
    r, g, b = rgb
    p = percent / 100.0

    r /= 255
    g /= 255
    b /= 255

    # RGB -> HLS
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    if p > 0:
        l = l + (1 - l) * p
    else:
        l = l * (1 + p)

    # clamp
    l = max(0.0, min(1.0, l))

    # HLS -> RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)

    return (
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255)),
    )


def render_piece(index):
    piece = PIECES[index]
    color = COLORS[index]
    res = []
    for row in piece:
        res.append([])
        for cell in row:
            if cell == 0:
                res[-1].append(None)
            else:
                res[-1].append(color)
    return 0, 3, res


def setup():
    board: list[list[None | tuple]] = [[None for j in range(10)] for i in range(22)]

    index = random.randrange(7)
    piece = render_piece(index)

    return board, piece, index


def render_board(board, piece):
    di, dj, piece = piece

    pixels = [
        [(0, 0, 0) for j in range(len(board[0]) * 2)]
        for i in range((len(board) - 2) * 2)
    ]

    for i in range(2, len(board)):
        for j in range(len(board[i])):
            if board[i][j] is not None:
                r = i - 2
                c = j
                pixels[r * 2][c * 2] = board[i][j]
                pixels[r * 2 + 1][c * 2] = board[i][j]
                pixels[r * 2][c * 2 + 1] = board[i][j]
                pixels[r * 2 + 1][c * 2 + 1] = board[i][j]

    for i in range(4):
        for j in range(4):
            if piece[i][j] is not None:
                r = i + di - 2
                c = j + dj
                if r >= 0:
                    pixels[r * 2][c * 2] = piece[i][j]
                    pixels[r * 2 + 1][c * 2] = piece[i][j]
                    pixels[r * 2][c * 2 + 1] = piece[i][j]
                    pixels[r * 2 + 1][c * 2 + 1] = piece[i][j]

    return pixels


def burn_piece_to_board(board, piece):
    di, dj, piece = piece
    for i in range(4):
        for j in range(4):
            if piece[i][j] is not None:
                board[i + di][j + dj] = piece[i][j]


def move(piece, dr=1, dc=0):
    di, dj, piece = piece
    return di + dr, dj + dc, piece


def collide(board, piece):
    di, dj, piece = piece
    for i in range(4):
        for j in range(4):
            if piece[i][j] is not None:
                if i + di > 21:
                    return True
                if j + dj < 0 or j + dj > 9:
                    return True
                if board[i + di][j + dj] is not None:
                    return True

    return False


def rotate_cw(piece):
    di, dj, piece = piece
    piece = [[piece[4 - 1 - y][x] for y in range(4)] for x in range(4)]
    return di, dj, piece


def rotate_ccw(piece):
    di, dj, piece = piece
    piece = [[piece[y][4 - 1 - x] for y in range(4)] for x in range(4)]
    return di, dj, piece


def loop(keys, board, piece, index):
    for key in keys:
        if key == "q":
            stge.quit()

        if key == "n":
            index = (index + 1) % 7
            piece = render_piece(index)

        if key == "UP":
            rot = rotate_cw(piece)
            for dc, dr in WALL_KICKS:
                nxt = move(rot, dr, dc)
                if not collide(board, nxt):
                    piece = nxt
                    break

        if key == "RIGHT":
            nxt = move(piece, 0, 1)
            if not collide(board, nxt):
                piece = nxt

        if key == "LEFT":
            nxt = move(piece, 0, -1)
            if not collide(board, nxt):
                piece = nxt

        if key == "DOWN":
            nxt = move(piece)
            if collide(board, nxt):
                burn_piece_to_board(board, piece)
                index = random.randrange(7)
                piece = render_piece(index)
            else:
                piece = nxt

    stge.pixels(render_board(board, piece))

    return board, piece, index


stge.run(setup, loop)
