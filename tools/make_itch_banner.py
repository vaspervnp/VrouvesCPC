#!/usr/bin/env python3
"""The banner of the itch.io page: assets/itch_banner.png, 960x252, the width of
the page's column.  The name in the letters of the splash screen (make_splash.py),
over the game's own cells and sprites.

    tools/make_itch_banner.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402
import gen_assets as g  # noqa: E402
import make_splash as ms  # noqa: E402

COLS, ROWS = 20, 7
SX, SY = 6, 3               # Mode 0 pixels are twice as wide as tall
OUT = os.path.join(g.ROOT, "assets", "itch_banner.png")
SMALL = {c: ms.stretch(r, 7, 10) for c, r in ms.SMALL.items()}
BIG = {c: ms.stretch(r, 13, 26) for c, r in ms.BIG.items()}
GAP = 3                     # room for the outlines between the letters
TOP, BIG_Y, GREEK_Y = 3, 18, 49

MAP = [
    "T.Y...............YT",
    "..T..............T..",
    "T..................T",
    ".Y................T.",
    "T..................T",
    "....................",
    "T.R.T.Y..T...Y.T.R.T",
]
ROAD = [(0, 5), (19, 5)]
PEOPLE = [(art.CRETAN, 2, 4), (art.BRIDE, 4, 4), (art.YIAYIA, 8, 6), (art.LYRA, 11, 6),
          (art.BAKER, 15, 4), (art.CAULDRON, 17, 4)]
INVADERS = [(art.GUARD_A, 1, 5), (art.TANK_L_A, 4, 5), (art.GUARD_B, 7, 5), (art.GUARD_A, 10, 5),
            (art.TANK_L_B, 13, 5), (art.GUARD_B, 16, 5), (art.GUARD_A, 18, 5)]
FLYING = [(art.DRONE_A, 1, 2), (art.DRONE_B, 18, 1)]


def line(cv, text, font, y0):
    """letters filled from white through yellow and orange to red, with a black
    outline and a dark red shadow, centred"""
    h = len(next(iter(font.values())))
    ramp = [art.CH['W']] * 2 + [art.CH['y']] * (h * 2 // 5) + [art.CH['o']] * (h - 3 - h * 2 // 5) + [art.CH['R']]
    fill = {}
    x = (cv.w - sum(len(font[c][0]) + GAP for c in text) + GAP) // 2
    for ch in text:
        rows = font[ch]
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c == '#':
                    fill[(x + i, y0 + j)] = ramp[j]
        x += len(rows[0]) + GAP
    ring = {(x + dx, y + dy) for x, y in fill for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for x, y in ring:
        cv.set(x + 1, y + 2, art.CH['r'])
    for x, y in ring:
        cv.set(x, y, art.CH['k'])
    for (x, y), pen in fill.items():
        cv.set(x, y, pen)


def base(cv, with_sacks):
    for rows, c, r in PEOPLE + INVADERS + FLYING:
        cv.blit(rows, c * g.TW, r * g.TH)
    cv.blit(art.PSSSST, 1 * g.TW, 3 * g.TH)
    cv.blit(art.NOTE_A, 11 * g.TW + 1, 5 * g.TH + 1)
    line(cv, "LET'S GO FOR", SMALL, TOP)
    line(cv, "VROUVES!", BIG, BIG_Y)
    greek = "ΠΑΜΕ ΓΙΑ ΒΡΟΥΒΕΣ"
    x = (cv.w - len(greek) * 4) // 2
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cv.text(greek, x + dx, GREEK_Y + dy, art.CH['k'])
    cv.text(greek, x, GREEK_Y, art.CH['W'])


def main():
    assert len(MAP) == ROWS and all(len(r) == COLS for r in MAP)
    g.MW, g.MH, g.PFW, g.PFH = COLS, ROWS, COLS * g.TW, ROWS * g.TH
    cv = g.render_background(g.Stage(base=base), g.carve_path(MAP, ROAD), True)
    im = Image.new("RGB", (cv.w, cv.h))
    im.putdata([art.PEN_RGB[p] for row in cv.p for p in row])
    im = im.resize((cv.w * SX, cv.h * SY), Image.NEAREST)
    im.quantize(colors=16, dither=Image.Dither.NONE).save(OUT, optimize=True)
    print(OUT, im.size, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
