#!/usr/bin/env python3
"""The background of the itch.io page: assets/itch_background.png, a village of
the game's own cells and sprites, 1920x1152, that tiles in both directions.
The page's column covers the middle, so everything happens at the sides.

    tools/make_itch_bg.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402
import gen_assets as g  # noqa: E402

COLS, ROWS = 30, 24
SX, SY = 8, 4               # Mode 0 pixels are twice as wide as tall
OUT = os.path.join(g.ROOT, "assets", "itch_background.png")


def crop(stage, c0, r0, cols, rows):
    """those cells of a stage as the game draws them"""
    grid = g.carve_path(stage.map, stage.ground)
    cv = g.render_background(stage, grid, True)
    return [row[c0 * g.TW:(c0 + cols) * g.TW] for row in cv.p[r0 * g.TH:(r0 + rows) * g.TH]]


KAFENIO = crop(g.STAGES[0], 0, 8, 6, 6)     # goes at columns 0-5, rows 13-18
CHURCH = crop(g.STAGES[1], 15, 0, 5, 6)     # goes at columns 25-29, rows 2-7

MAP = [
    "T....Y.......T..........T..Y.T",
    ".R.......T.........T.......C..",
    "...T...T....Y....T.......KKKKK",
    "T........................KKKKK",
    "..G....R.....T.....T.....KKKKK",
    "T.......T.........Y......KKKKK",
    "......Y......T...........PPPPP",
    "T.R.....T.........T..T...PPPPP",
    "..............Y..............T",
    "T.......T............T........",
    ".......Y....T.....T.......WW.T",
    "..WWW.......................Y.",
    "T.......T.........T..........T",
    "KKKKKK.............T...S......",
    "KKKKKK...T....Y..............T",
    "KKKKKK...........T.....Y......",
    "KKKKKK.T.....................T",
    "PPPPPP.......T.......T....S...",
    "PPPPPP...Y.........T......C..T",
    "T.......T....T...........S....",
    ".S..T................T......T.",
    "T.....R......T.....Y.....G...T",
    "..J.........T.........T..R....",
    "T...Y..T.........T.......T...T",
]
LEFT = [(4, 0), (4, 3), (1, 3), (1, 8), (6, 8), (6, 22), (4, 22), (4, 23)]
RIGHT = [(23, 0), (23, 9), (28, 9), (28, 15), (24, 15), (24, 20), (23, 20), (23, 23)]
GATE = [(27, 9), (27, 8)]
PORCH = [(6, 17), (5, 17)]

# cells: defenders by the road, invaders on it
PEOPLE = [
    (art.CRETAN, 3, 5), (art.BRIDE, 4, 5), (art.PSSSST, 1, 12), (art.YIAYIA, 5, 11),
    (art.LYRA, 5, 10), (art.CAULDRON, 3, 10), (art.BAKER, 2, 7),
    (art.CRETAN, 24, 4), (art.BAKER, 24, 7), (art.LYRA, 25, 11), (art.YIAYIA, 26, 11),
    (art.BRIDE, 25, 14), (art.CRETAN, 26, 14), (art.CAULDRON, 26, 17), (art.PSSSST, 25, 17),
]
INVADERS = [
    (art.GUARD_A, 4, 1), (art.GUARD_B, 1, 5), (art.TANK_L_A, 3, 8), (art.GUARD_A, 6, 10),
    (art.TANK_V_A, 6, 13), (art.GUARD_B, 6, 20), (art.GUARD_A, 5, 22),
    (art.GUARD_B, 23, 1), (art.TANK_V_B, 23, 6), (art.GUARD_A, 26, 9), (art.GUARD_B, 28, 12),
    (art.TANK_L_B, 26, 15), (art.GUARD_A, 24, 18), (art.GUARD_B, 23, 22),
    (art.DRONE_A, 2, 1), (art.DRONE_B, 0, 11), (art.DRONE_A, 3, 20), (art.DRONE_B, 6, 4),
    (art.DRONE_A, 24, 13), (art.DRONE_B, 29, 19), (art.DRONE_A, 27, 21), (art.DRONE_B, 25, 1),
]


def base(cv, with_sacks):
    for rows, c0, r0 in ((KAFENIO, 0, 13), (CHURCH, 25, 2)):
        for j, row in enumerate(rows):
            for i, pen in enumerate(row):
                cv.set(c0 * g.TW + i, r0 * g.TH + j, pen)
    cv.blit(art.FLAG_A, 28, 13 * g.TH + 3)
    cv.blit(art.FLAG_B, g.STAGES_FLAG2[0] * 2 - 15 * g.TW + 25 * g.TW, 2 * g.TH + g.STAGES_FLAG2[1])
    for rows, c, r in PEOPLE + INVADERS:
        cv.blit(rows, c * g.TW, r * g.TH)
    cv.blit(art.CURSOR_OK, 5 * g.TW, 11 * g.TH)
    cv.blit(art.NOTE_A, 25 * g.TW + 1, 10 * g.TH + 2)
    cv.blit(art.NOTE_B, 3 * g.TW, 9 * g.TH + 2)
    cv.blit(art.BOOM_A, 28 * g.TW, 11 * g.TH)
    cv.blit(g.SACK, 2 * g.TW, 7 * g.TH + 5)


def main():
    assert len(MAP) == ROWS and all(len(r) == COLS for r in MAP)
    g.MW, g.MH, g.PFW, g.PFH = COLS, ROWS, COLS * g.TW, ROWS * g.TH
    grid = MAP
    for road in (LEFT, RIGHT, GATE, PORCH):
        grid = g.carve_path(grid, road)
    cv = g.render_background(g.Stage(base=base), grid, True)
    im = Image.new("RGB", (cv.w, cv.h))
    im.putdata([art.PEN_RGB[p] for row in cv.p for p in row])
    im = im.resize((cv.w * SX, cv.h * SY), Image.NEAREST)
    im.quantize(colors=16, dither=Image.Dither.NONE).save(OUT, optimize=True)
    print(OUT, im.size, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
