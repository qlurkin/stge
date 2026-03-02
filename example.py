import stge


def loop(keys, out):
    if "q" in keys or "Q" in keys:
        stge.quit()
    if len(keys) > 0:
        out.extend(keys)
    width, height = stge.size()
    stge.write_at(width // 2 - 2, height // 2, out, italic=True)
    stge.pixels(
        [
            [(255, 0, 0), (255, 0, 0), (255, 0, 0)],
            [(255, 0, 0), (0, 0, 255), (255, 0, 0)],
            [(255, 0, 0), (255, 0, 0), (255, 0, 0)],
        ],
    )
    stge.write_at(width // 2 - 4, height - 1, "[Q: Quit]")
    return out


stge.run(setup=list, loop=loop)
