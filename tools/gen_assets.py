#!/usr/bin/env python3
"""Generates src/gen/assets.asm (and preview PNGs) for LET'S GO FOR VROUVES.

Everything graphical is authored here: the font, sprites, the Stage 01 map
(rendered to an 8x12 tile set), the enemy paths, text in both languages,
music and sound effects.
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402
import font  # noqa: E402
import texts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "gen", "assets.asm")
PREVIEW = os.path.join(ROOT, "build", "preview")

MW, MH = 20, 14          # map size in cells
TW, TH = 8, 12           # cell size: 8 Mode 0 pixels x 12 lines
PFW, PFH = MW * TW, MH * TH

# ------------------------------------------------------------------ helpers


def enc_byte(p0, p1):
    """Mode 0 byte holding pixel p0 (left) and p1 (right)."""
    b = 0
    b |= ((p0 >> 0) & 1) << 7 | ((p0 >> 1) & 1) << 3 | ((p0 >> 2) & 1) << 5 | ((p0 >> 3) & 1) << 1
    b |= ((p1 >> 0) & 1) << 6 | ((p1 >> 1) & 1) << 2 | ((p1 >> 2) & 1) << 4 | ((p1 >> 3) & 1) << 0
    return b


def sprite_bytes(rows):
    """w, h, then w*h bytes.  Pen 0 is transparent, so sprite black uses pen 15."""
    h = len(rows)
    w = len(rows[0])
    assert w % 2 == 0 and w <= 8, rows
    assert all(len(r) == w for r in rows), rows
    out = [w // 2, h]
    for r in rows:
        for x in range(0, w, 2):
            p = []
            for ch in r[x:x + 2]:
                if ch == '.':
                    p.append(0)
                elif ch in 'kn':
                    p.append(15)
                else:
                    p.append(art.CH[ch])
            out.append(enc_byte(p[0], p[1]))
    return out


def db_lines(data, per=16):
    lines = []
    for i in range(0, len(data), per):
        lines.append("    db " + ",".join("#%02X" % (v & 0xFF) for v in data[i:i + per]))
    return lines


def dw_lines(data, per=8):
    lines = []
    for i in range(0, len(data), per):
        lines.append("    dw " + ",".join("#%04X" % (v & 0xFFFF) for v in data[i:i + per]))
    return lines


# ------------------------------------------------------------------ map

MAP = [
    "T.G..T...T..T.C...TT",
    "T..................T",
    "..........WWWWWW..T.",
    "T...C..........W...T",
    ".G.................T",
    "T...WWWWWW..........",
    "..T........C...TG..T",
    "T..................T",
    "KKKKK.......WWWWWW.T",
    "KKKKK..T...........T",
    "KKKKK...............",
    "KKKKK..WWWW....G...T",
    "PPPPP..............T",
    "PPPPPPT..T.CT..T.G.T",
]
MAP = [r.ljust(MW, '.')[:MW] for r in MAP]

GROUND_WP = [(17, 0), (17, 1), (2, 1), (2, 4), (15, 4), (15, 7), (8, 7),
             (8, 10), (17, 10), (17, 12), (5, 12)]
AIR_WP = [(17, 0), (12, 5), (12, 8), (8, 12), (5, 12)]

SACK_CELLS = [(3, 12), (4, 12), (3, 13), (4, 13), (5, 13)]


def carve_path(grid):
    cells = set()
    for (a, b) in zip(GROUND_WP, GROUND_WP[1:]):
        (c0, r0), (c1, r1) = a, b
        dc = (c1 > c0) - (c1 < c0)
        dr = (r1 > r0) - (r1 < r0)
        c, r = c0, r0
        cells.add((c, r))
        while (c, r) != (c1, r1):
            c += dc
            r += dr
            cells.add((c, r))
    for (c, r) in cells:
        row = list(grid[r])
        row[c] = '#'
        grid[r] = "".join(row)
    return grid


def path_steps(wps):
    pts = []
    for (a, b) in zip(wps, wps[1:]):
        (c0, r0), (c1, r1) = a, b
        n = 12 * max(abs(c1 - c0), abs(r1 - r0))
        for k in range(n):
            c = c0 + (c1 - c0) * k / n
            r = r0 + (r1 - r0) * k / n
            pts.append((int(round(c * 4)), int(round(r * 12))))
    c, r = wps[-1]
    pts.append((c * 4, r * 12))
    while pts[0][1] < 2:
        pts.pop(0)
    return pts


# ------------------------------------------------------------------ background renderer

class Canvas:
    def __init__(self, w, h, fill):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def blit(self, rows, x0, y0):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch != '.':
                    self.set(x0 + i, y0 + j, art.CH[ch])

    def text(self, s, x0, y0, c):
        for k, ch in enumerate(s):
            g = font.glyph_rows(font.glyph_index(ch))
            for j, bits in enumerate(g):
                for i in range(3):
                    if bits & (4 >> i):
                        self.set(x0 + k * 4 + i, y0 + j, c)


TREE = [
    "..tttt..",
    ".tpptttk"[:8],
    "tppttttt",
    "tpttpttt",
    "tttttttk",
    "ttpttttk",
    "tttttptk",
    "tttttttk",
    ".ttttttk",
    "..ttttk.",
    "...kkk..",
    "........",
]
TREE = [r.ljust(8, '.')[:8] for r in TREE]
TREE2 = [
    "...tt...",
    ".ttpttt.",
    "tppttttk",
    "tpttttpk",
    "ttttpttk",
    ".tttttk.",
    "..tktk..",
    ".ttpttt.",
    "tpttttpk",
    "tttptttk",
    ".ttttkk.",
    "..kkk...",
]
CACTUS = [
    "...y....",
    "..ppt...",
    ".pppptR.",
    ".ppppt..",
    "..ppt.y.",
    "y.tt.ppt",
    "pt.t.pppt"[:8],
    "pppttppt",
    "pppt.tt.",
    ".ptt.t..",
    "..ttt...",
    "........",
]
GOAT_W = [
    "........",
    "..r..r..",
    "...ee...",
    "...WW...",
    "..WWWW..",
    ".WWWWWW.",
    ".WWeWWW.",
    ".WWWWWW.",
    ".WWWWWW.",
    "..WWWW..",
    "..W..W..",
    "...e....",
]
GOAT_B = [
    "........",
    "..e..e..",
    "...rr...",
    "...oo...",
    "..oooo..",
    ".ooWooo.",
    ".oooooo.",
    ".oorooo.",
    ".oooooo.",
    "..oooo..",
    "..o..o..",
    "....r...",
]
TABLE = [
    ".rrr.",
    "rorWr",
    "rrorr",
    ".rrr.",
]
SACK = [
    ".lp.",
    "rpl.",
    ".rr.",
    "oooo",
    "oroo",
    "oooo",
    "oooo",
    "rooo",
    ".rr.",
]
SACK = [r.ljust(4, '.') for r in SACK]


def grass_cell(cv, c, r):
    x0, y0 = c * TW, r * TH
    cv.rect(x0, y0, x0 + TW - 1, y0 + TH - 1, art.CH['g'])
    v = (c * 7 + r * 13 + (c * r) % 3) % 5

    def tuft(x, y):
        cv.set(x0 + x, y0 + y, art.CH['t'])
        cv.set(x0 + x + 2, y0 + y, art.CH['t'])
        cv.set(x0 + x + 1, y0 + y + 1, art.CH['t'])

    if v == 0:
        tuft(1, 2); tuft(4, 8)
    elif v == 1:
        tuft(4, 3); cv.set(x0 + 1, y0 + 9, art.CH['y'])
    elif v == 2:
        tuft(1, 6); tuft(5, 1)
    elif v == 3:
        cv.set(x0 + 5, y0 + 6, art.CH['t']); cv.set(x0 + 2, y0 + 10, art.CH['p'])
    else:
        cv.set(x0 + 5, y0 + 4, art.CH['W']); tuft(1, 9)


def is_path(grid, c, r):
    return 0 <= c < MW and 0 <= r < MH and grid[r][c] == '#'


def path_cell(cv, grid, c, r):
    x0, y0 = c * TW, r * TH
    cv.rect(x0, y0, x0 + TW - 1, y0 + TH - 1, art.CH['o'])
    for (x, y) in ((2, 3), (6, 7), (3, 10), (5, 1)):
        cv.set(x0 + x, y0 + y, art.CH['r'])
    for (x, y) in ((1, 7), (6, 2)):
        cv.set(x0 + x, y0 + y, art.CH['y'])
    edge = art.CH['r']
    if not is_path(grid, c, r - 1) and r > 0:
        for x in range(TW):
            cv.set(x0 + x, y0, edge)
    if not is_path(grid, c, r + 1) and r < MH - 1:
        for x in range(TW):
            cv.set(x0 + x, y0 + TH - 1, edge)
    if not is_path(grid, c - 1, r) and c > 0:
        for y in range(TH):
            cv.set(x0, y0 + y, edge)
    if not is_path(grid, c + 1, r) and c < MW - 1:
        for y in range(TH):
            cv.set(x0 + TW - 1, y0 + y, edge)


def wall_cell(cv, grid, c, r):
    grass_cell(cv, c, r)
    x0, y0 = c * TW, r * TH

    def w(cc, rr):
        return 0 <= cc < MW and 0 <= rr < MH and grid[rr][cc] == 'W'
    horiz = w(c - 1, r) or w(c + 1, r)
    vert = w(c, r - 1) or w(c, r + 1)
    if not horiz and not vert:
        horiz = True
    K, E, Wh, T = art.CH['k'], art.CH['e'], art.CH['W'], art.CH['t']
    if horiz:
        xa = 0 if w(c - 1, r) else 1
        xb = TW - 1 if w(c + 1, r) else TW - 2
        for x in range(xa, xb + 1):
            for y in range(3, 9):
                cv.set(x0 + x, y0 + y, E)
            cv.set(x0 + x, y0 + 3, K)
            cv.set(x0 + x, y0 + 8, K)
            cv.set(x0 + x, y0 + 9, T)
            cv.set(x0 + x, y0 + 6, K if (x % 4) in (1, 2) and False else E)
        for x in range(xa, xb + 1):
            if (x + 1) % 4 == 0:
                for y in (4, 5):
                    cv.set(x0 + x, y0 + y, K)
            if (x + 3) % 4 == 0:
                for y in (6, 7):
                    cv.set(x0 + x, y0 + y, K)
            if x % 4 == 0:
                cv.set(x0 + x, y0 + 4, Wh)
            if (x + 2) % 4 == 0:
                cv.set(x0 + x, y0 + 6, Wh)
        if not w(c - 1, r):
            for y in range(3, 9):
                cv.set(x0 + xa, y0 + y, K)
        if not w(c + 1, r):
            for y in range(3, 9):
                cv.set(x0 + xb, y0 + y, K)
    if vert:
        ya = 0 if w(c, r - 1) else 2
        yb = TH - 1 if w(c, r + 1) else TH - 3
        for y in range(ya, yb + 1):
            for x in range(2, 6):
                cv.set(x0 + x, y0 + y, E)
            cv.set(x0 + 2, y0 + y, K)
            cv.set(x0 + 5, y0 + y, K)
            cv.set(x0 + 6, y0 + y, T)
            if y % 4 == 0:
                cv.set(x0 + 3, y0 + y, K)
                cv.set(x0 + 4, y0 + y, K)
            if y % 4 == 1:
                cv.set(x0 + 3, y0 + y, Wh)
        if not w(c, r - 1):
            for x in range(2, 6):
                cv.set(x0 + x, y0 + ya, K)
        if not w(c, r + 1):
            for x in range(2, 6):
                cv.set(x0 + x, y0 + yb, K)


def kafenio(cv):
    K, Wh, E, B, C, R = (art.CH[k] for k in "kWeBcr")
    x0, y0, x1, y1 = 0, 96, 39, 143
    cv.rect(x0, y0, x1, y1, Wh)
    # roof texture
    for y in range(y0 + 4, y1 - 10, 6):
        for x in range(x0 + 3, x1 - 2, 4):
            cv.set(x + (2 if (y // 6) % 2 else 0), y, E)
    # outline and blue parapet
    for x in range(x0, x1 + 1):
        cv.set(x, y0, K)
        cv.set(x, y0 + 1, B)
        cv.set(x, y0 + 2, B)
    for y in range(y0, y1 + 1):
        cv.set(x1, y, K)
        cv.set(x1 - 1, y, B)
        cv.set(x0, y, B)
    cv.set(x0, y0, K)
    # solar water heater
    cv.rect(3, 100, 10, 101, E)
    cv.rect(3, 100, 10, 100, Wh)
    for x in range(3, 11):
        cv.set(x, 102, K)
    cv.rect(3, 103, 10, 109, C)
    for y in range(103, 110, 3):
        for x in range(3, 11):
            cv.set(x, y, art.CH['B'])
    for y in range(103, 110):
        cv.set(6, y, art.CH['B'])
    for x in range(3, 11):
        cv.set(x, 110, K)
    # flag (static part of the pole; the cloth is an animated sprite)
    for y in range(99, 113):
        cv.set(28, y, art.CH['r'])
    cv.set(28, 113, K)
    # chimney
    cv.rect(16, 102, 19, 107, E)
    cv.rect(17, 103, 18, 105, K)
    # sign: white letters on blue
    cv.rect(2, 116, 37, 129, B)
    for x in range(2, 38):
        cv.set(x, 116, K)
        cv.set(x, 129, K)
    for y in range(116, 130):
        cv.set(2, y, K)
        cv.set(37, y, K)
    cv.text("ΚΑΦΕΝΕΙΟ", 4, 120, Wh)
    # awning with blue/white stripes along the porch side
    for y in range(134, 144):
        for x in range(x0, x1 + 1):
            cv.set(x, y, B if (x // 2) % 2 == 0 else Wh)
    for x in range(x0, x1 + 1):
        cv.set(x, 133, K)
        if x % 4 == 1:
            cv.set(x, 143, K)


def porch(cv, with_sacks):
    K, Wh, E = art.CH['k'], art.CH['W'], art.CH['e']
    cells = [(c, 12) for c in range(5)] + [(c, 13) for c in range(6)]
    for (c, r) in cells:
        x0, y0 = c * TW, r * TH
        cv.rect(x0, y0, x0 + TW - 1, y0 + TH - 1, Wh)
        for y in range(TH):
            for x in range(TW):
                gy = (y0 + y) % 6 == 5
                gx = ((x0 + x) + (3 if ((y0 + y) // 6) % 2 else 0)) % 6 == 5
                if gy or gx:
                    cv.set(x0 + x, y0 + y, E)
    # tables with patrons (heads seen from above)
    patrons = [
        ((5, 149), [(1, 148, 'k'), (10, 149, 'e'), (5, 145, 'k')]),
        ((17, 149), [(13, 149, 'e'), (22, 148, 'k')]),
        ((4, 160), [(0, 160, 'e'), (9, 161, 'k'), (5, 165, 'k')]),
        ((16, 160), [(12, 160, 'k'), (21, 161, 'e')]),
    ]
    for (tx, ty), heads in patrons:
        cv.blit(TABLE, tx - 2, ty - 2)
        for (hx, hy, hair) in heads:
            cv.set(hx, hy, art.CH['s'])
            cv.set(hx + 1, hy, art.CH[hair])
            cv.set(hx, hy + 1, art.CH[hair])
            cv.set(hx + 1, hy + 1, art.CH[hair])
            cv.set(hx, hy + 2, art.CH['B'] if hair == 'k' else art.CH['k'])
            cv.set(hx + 1, hy + 2, art.CH['B'] if hair == 'k' else art.CH['k'])
    # a cat
    cv.blit(["y.y", "yyy", ".y.", "yyy", "..y"], 26, 160)
    if with_sacks:
        for (c, r) in SACK_CELLS:
            x0, y0 = c * TW, r * TH
            cv.blit(SACK, x0, y0 + 1)
            cv.blit(SACK, x0 + 4, y0 + 3)


def render_background(grid, with_sacks=True):
    cv = Canvas(PFW, PFH, art.CH['g'])
    for r in range(MH):
        for c in range(MW):
            t = grid[r][c]
            if t == '#':
                path_cell(cv, grid, c, r)
            elif t == 'W':
                wall_cell(cv, grid, c, r)
            elif t in 'KP':
                pass
            else:
                grass_cell(cv, c, r)
                if t == 'T':
                    cv.blit(TREE if (c + r) % 3 else TREE2, c * TW, r * TH)
                elif t == 'C':
                    cv.blit(CACTUS, c * TW, r * TH)
                elif t == 'G':
                    cv.blit(GOAT_W if (c + r) % 2 else GOAT_B, c * TW, r * TH)
    kafenio(cv)
    porch(cv, with_sacks)
    return cv


def cell_bytes(cv, c, r):
    out = []
    for y in range(TH):
        for x in range(0, TW, 2):
            out.append(enc_byte(cv.get(c * TW + x, r * TH + y), cv.get(c * TW + x + 1, r * TH + y)))
    return tuple(out)


# ------------------------------------------------------------------ music

NOTE_IDX = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
            'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def note_period(name):
    n, octv = name[:-1], int(name[-1])
    midi = 12 * (octv + 1) + NOTE_IDX[n]
    f = 440.0 * 2 ** ((midi - 69) / 12)
    return int(round(1000000 / (16 * f)))


MEL_A = """
D4/2 E4/2 F4/2 G4/2 A4/4 G4/2 F4/2 E4/2 F4/2 G4/2 E4/2 D4/8
A4/2 Bb4/2 A4/2 G4/2 F4/2 G4/2 A4/4 G4/2 F4/2 E4/2 F4/2 D4/8
D5/2 C5/2 Bb4/2 A4/2 Bb4/2 A4/2 G4/4 A4/2 G4/2 F4/2 E4/2 F4/4 E4/4
D4/2 E4/2 F4/2 G4/2 A4/2 G4/2 F4/2 E4/2 E4/2 F4/2 E4/2 C#4/2 D4/8
"""
MEL_B = """
A4/1 Bb4/1 A4/1 G4/1 A4/2 D4/2 A4/1 Bb4/1 A4/1 G4/1 A4/2 D4/2
G4/1 A4/1 G4/1 F4/1 G4/2 C4/2 G4/1 A4/1 G4/1 F4/1 E4/4
F4/1 G4/1 F4/1 E4/1 F4/2 A4/2 E4/1 F4/1 E4/1 D4/1 E4/2 G4/2
F4/2 E4/2 D4/2 C#4/2 D4/8
"""
BASS_A = "D D C D Bb F C D Bb G A A D C A D".split()
BASS_B = "D D C A F C A D".split()
BASS_ROOTS = BASS_A + BASS_A + BASS_B
FIFTH = {'D': 'A', 'C': 'G', 'Bb': 'F', 'F': 'C', 'G': 'D', 'A': 'E'}
SIXTEENTH = 6   # frames


def parse_mel(s):
    out = []
    for tok in s.split():
        n, d = tok.split('/')
        out.append((n, int(d) * SIXTEENTH))
    return out


def bass_line():
    out = []
    for root in BASS_ROOTS:
        fifth = FIFTH[root]
        lo = 2 if root in ('D', 'C') else (1 if root in ('Bb', 'A', 'G') else 2)
        if root in ('Bb', 'A', 'G'):
            out += [(root + "2", 3 * SIXTEENTH), ("R", SIXTEENTH),
                    (fifth + ("3" if fifth in ('D', 'E', 'F') else "2"), 3 * SIXTEENTH), ("R", SIXTEENTH)]
        else:
            out += [(root + "2", 3 * SIXTEENTH), ("R", SIXTEENTH),
                    (fifth + "2", 3 * SIXTEENTH), ("R", SIXTEENTH)]
        del lo
    return out


# sound effects: list of (tone period, noise period (0 = none), volume)
SFX = {
    "SFX_RIFLE": [(0, 6, 13), (0, 9, 10), (0, 12, 7), (0, 15, 4)],
    "SFX_PISTOL": [(0, 3, 10), (0, 5, 6), (0, 7, 3)],
    "SFX_LASER": [(30, 0, 12), (45, 0, 11), (60, 0, 10), (80, 0, 9), (100, 0, 7), (130, 0, 5)],
    "SFX_THROW": [(300, 0, 10), (260, 0, 10), (220, 0, 9), (190, 0, 7), (170, 0, 5)],
    "SFX_BASH": [(400, 14, 14), (500, 18, 12), (0, 22, 9), (0, 26, 5)],
    "SFX_PUFF": [(0, 20, 10), (0, 22, 11), (0, 24, 10), (0, 26, 9), (0, 28, 8), (0, 30, 6), (0, 31, 4)],
    "SFX_DIE": [(200, 8, 13), (300, 12, 12), (400, 16, 10), (500, 20, 8), (600, 24, 5)],
    "SFX_HURT": [(900, 0, 15), (1000, 0, 14), (1100, 25, 13), (1200, 28, 11), (1300, 31, 9), (1400, 31, 6)],
    "SFX_BUILD": [(250, 0, 12), (250, 0, 12), (180, 0, 12), (180, 0, 12), (125, 0, 12), (125, 0, 9)],
    "SFX_ERROR": [(700, 0, 12), (700, 0, 12), (700, 0, 0), (700, 0, 12), (700, 0, 12), (700, 0, 6)],
    "SFX_SELL": [(125, 0, 12), (125, 0, 12), (180, 0, 10), (250, 0, 8)],
    "SFX_WAVE": [(213, 0, 13)] * 4 + [(169, 0, 13)] * 4 + [(142, 0, 13)] * 4 + [(106, 0, 13)] * 8 + [(106, 0, 8)] * 4,
    "SFX_CRUSH": [(1500, 10, 15), (1700, 14, 14), (2000, 18, 12), (2200, 24, 10), (2500, 31, 7)],
    "SFX_MOVE": [(80, 0, 6)],
}
SFX_PRIO = {"SFX_MOVE": 0, "SFX_PISTOL": 1, "SFX_RIFLE": 1, "SFX_LASER": 1, "SFX_THROW": 1,
            "SFX_PUFF": 2, "SFX_BASH": 2, "SFX_DIE": 3, "SFX_SELL": 4, "SFX_BUILD": 4,
            "SFX_ERROR": 4, "SFX_CRUSH": 5, "SFX_HURT": 6, "SFX_WAVE": 7}

# ------------------------------------------------------------------ waves
# enemy types: 1 drone, 2 guard, 3 tank.  (type, count, interval in frames)
WAVES = [
    [(2, 6, 45)],
    [(1, 8, 28)],
    [(2, 6, 36), (1, 6, 24)],
    [(2, 6, 30), (3, 2, 70)],
    [(1, 12, 18), (2, 5, 30)],
    [(2, 10, 26), (3, 3, 60)],
    [(1, 14, 16), (2, 8, 24), (3, 2, 50)],
    [(3, 5, 50), (2, 10, 22), (1, 8, 16)],
    [(1, 18, 14), (2, 10, 20), (3, 4, 40)],
    [(2, 12, 18), (1, 16, 12), (3, 8, 36)],
]

# ------------------------------------------------------------------ build


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    A = []

    def emit(s=""):
        A.append(s)

    emit("; generated by tools/gen_assets.py - do not edit")
    emit()

    # palette
    emit("palette_hw:")
    A.extend(db_lines([art.FW_TO_HW[c] for c in art.PALETTE_FW]))
    for i in range(16):
        emit("PENBYTE_%d equ #%02X" % (i, enc_byte(i, i)))
    emit("BAR_GG equ #%02X" % enc_byte(10, 10))
    emit("BAR_GR equ #%02X" % enc_byte(10, 9))
    emit("BAR_RR equ #%02X" % enc_byte(9, 9))
    emit("pen_left:")
    A.extend(db_lines([enc_byte(c, 0) for c in range(16)]))
    emit()

    # font
    emit("GLYPH_0 equ %d" % font.glyph_index('0'))
    emit("GLYPH_SPACE equ 0")
    emit("GLYPH_SLASH equ %d" % font.glyph_index('/'))
    emit("font:")
    fdata = []
    for i in range(len(font.GLYPHS)):
        fdata += font.glyph_rows(i)
    A.extend(db_lines(fdata, 12))
    emit()

    # map / tiles
    grid = carve_path(list(MAP))
    cv_full = render_background(grid, True)
    cv_empty = render_background(grid, False)
    tiles = {}
    tile_list = []

    def tile_index(tb):
        if tb not in tiles:
            tiles[tb] = len(tile_list)
            tile_list.append(tb)
        return tiles[tb]

    tilemap = []
    celltype = []
    for r in range(MH):
        for c in range(MW):
            tilemap.append(tile_index(cell_bytes(cv_full, c, r)))
            t = grid[r][c]
            celltype.append(0 if t == '.' else 1 if t == '#' else 3 if t in 'KP' else 2)
    sack_data = []
    for i, (c, r) in enumerate(SACK_CELLS):
        full = tilemap[r * MW + c]
        empty = tile_index(cell_bytes(cv_empty, c, r))
        sack_data += [c, r, full, empty]
    assert len(tile_list) < 256
    emit("NUM_TILES equ %d" % len(tile_list))
    emit("tiles:")
    for tb in tile_list:
        A.extend(db_lines(list(tb), 16))
    emit("tilemap:")
    A.extend(db_lines(tilemap, 20))
    emit("cellmap:")
    A.extend(db_lines(celltype, 20))
    emit("NUM_SACKS equ %d" % len(SACK_CELLS))
    emit("sack_cells:")
    A.extend(db_lines(sack_data, 4))
    emit()

    # paths: x0, y0, sub0, rem0, then (dx, dy, n) segments, 0,0,0 terminated
    for name, wps in (("path_ground", GROUND_WP), ("path_air", AIR_WP)):
        segs = []
        for (a, b) in zip(wps, wps[1:]):
            (c0, r0), (c1, r1) = a, b
            dc, dr = c1 - c0, r1 - r0
            assert dc == 0 or dr == 0 or abs(dc) == abs(dr)
            n = 12 * max(abs(dc), abs(dr))
            assert n < 256
            segs.append(((dc > 0) - (dc < 0), (dr > 0) - (dr < 0), n))
        c0, r0 = wps[0]
        x0, y0, sub0, rem0 = c0 * 4, r0 * 12, 0, segs[0][2]
        while y0 < 2:   # start low enough for the health bar
            dx, dy, _ = segs[0]
            y0 += dy
            sub0 += 1
            if sub0 == 3:
                sub0 = 0
                x0 += dx
            rem0 -= 1
        emit("%s:" % name)
        data = [x0, y0, sub0, rem0]
        for (dx, dy, n) in segs:
            data += [dx & 0xFF, dy & 0xFF, n]
        data += [0, 0, 0]
        A.extend(db_lines(data, 16))
        emit("%s_len equ %d" % (name, sum(n for _, _, n in segs)))
    emit()


    # sprites
    for name, rows in art.SPRITES:
        emit("%s:" % name)
        A.extend(db_lines(sprite_bytes(rows), 16))
    emit()

    # strings
    ids = []
    en_lines, gr_lines = [], []

    def enc_text(s):
        out = []
        for line_no, line in enumerate(s.split("\n")):
            if line_no:
                out.append(0xFE)
            assert len(line) <= 40, line
            out += font.encode(line)
        out.append(0xFF)
        return out

    all_strings = list(texts.STRINGS)
    for sid, en, gr in all_strings:
        if sid.startswith("T_CAST") or sid.startswith("T_ENE"):
            for t in (en, gr):
                for line in t.split("\n"):
                    assert len(line) <= 35, line
    all_strings.append(("T_STORY", texts.wrap(texts.STORY_EN), texts.wrap(texts.STORY_GR)))
    for sid, en, gr in all_strings:
        if gr is None:
            gr = en
        ids.append(sid)
        en_lines.append(("se_" + sid, enc_text(en)))
        gr_lines.append(("sg_" + sid, enc_text(gr)))
    for i, sid in enumerate(ids):
        emit("%s equ %d" % (sid, i))
    # deduplicate, then byte-pair encode all strings together
    uniq = []
    lbl_of = {}
    alias = []
    for lbl, data in en_lines + gr_lines:
        key = tuple(data)
        if key in lbl_of:
            alias.append((lbl, lbl_of[key]))
        else:
            lbl_of[key] = lbl
            uniq.append([lbl, list(data)])
    NG = len(font.GLYPHS)
    raw_size = sum(len(d) for _, d in uniq)
    pairs = []
    code = NG
    while code < 0xFE:
        counts = {}
        for _, d in uniq:
            for a, b in zip(d, d[1:]):
                if a >= 0xFE or b >= 0xFE:
                    continue
                counts[(a, b)] = counts.get((a, b), 0) + 1
        if not counts:
            break
        best, n = max(counts.items(), key=lambda kv: kv[1])
        if n < 3:
            break
        pairs.append(best)
        for item in uniq:
            d = item[1]
            out = []
            i = 0
            while i < len(d):
                if i + 1 < len(d) and (d[i], d[i + 1]) == best:
                    out.append(code)
                    i += 2
                else:
                    out.append(d[i])
                    i += 1
            item[1] = out
        code += 1
    emit("NUM_GLYPHS equ %d" % NG)
    emit("pair_table:")
    flat = []
    for a, b in pairs:
        flat += [a, b]
    A.extend(db_lines(flat, 16))
    emit("strtab_en:")
    A.extend("    dw " + lbl for lbl, _ in en_lines)
    emit("strtab_gr:")
    A.extend("    dw " + lbl for lbl, _ in gr_lines)
    for lbl, target in alias:
        emit("%s equ %s" % (lbl, target))
    for lbl, d in uniq:
        emit("%s:" % lbl)
        A.extend(db_lines(d, 20))
    packed = sum(len(d) for _, d in uniq) + 2 * len(pairs)
    print("text: %d bytes raw, %d packed (%d pairs)" % (raw_size, packed, len(pairs)))
    emit()

    # music
    mel = parse_mel(MEL_A) + parse_mel(MEL_A) + parse_mel(MEL_B)
    bass = bass_line()
    durs = sorted({d for _, d in mel + bass})
    assert len(durs) <= 15
    emit("music_durs:")
    A.extend(db_lines(durs))

    def chan(name, seq):
        notes = sorted({n for n, _ in seq if n != 'R'}, key=note_period, reverse=True)
        assert len(notes) <= 14, notes
        emit("%s_notes:" % name)
        A.extend(dw_lines([0] + [note_period(n) for n in notes]))
        out = []
        for n, d in seq:
            out.append(((0 if n == 'R' else notes.index(n) + 1) << 4) | durs.index(d))
        emit("%s:" % name)
        A.extend(db_lines(out + [0xFF], 16))
    assert sum(d for _, d in mel) == sum(d for _, d in bass), (sum(d for _, d in mel), sum(d for _, d in bass))
    chan("music_a", mel)
    chan("music_b", bass)
    emit()

    # sfx
    names = list(SFX.keys())
    for i, n in enumerate(names):
        emit("%s equ %d" % (n, i))
    emit("sfx_table:")
    A.extend("    dw sfx_%d" % i for i in range(len(names)))
    emit("sfx_prio:")
    A.extend(db_lines([SFX_PRIO[n] for n in names]))
    for i, n in enumerate(names):
        emit("sfx_%d:" % i)
        data = []
        for (p, nz, v) in SFX[n]:
            data += [v, nz, p & 0xFF, p >> 8]
        data.append(0xFF)
        A.extend(db_lines(data, 16))
    emit()

    # waves
    emit("NUM_WAVES equ %d" % len(WAVES))
    emit("wave_table:")
    A.extend("    dw wave_%d" % i for i in range(len(WAVES)))
    for i, w in enumerate(WAVES):
        emit("wave_%d:" % i)
        data = []
        for (t, n, iv) in w:
            data += [t, n, iv]
        data.append(0)
        A.extend(db_lines(data, 16))
    emit()

    with open(OUT, "w") as f:
        f.write("\n".join(A) + "\n")

    # ---------------------------------------------------------------- previews
    def save(cv, name, scale_x=4, scale_y=2):
        im = Image.new("RGB", (cv.w, cv.h))
        for y in range(cv.h):
            for x in range(cv.w):
                im.putpixel((x, y), art.PEN_RGB[cv.p[y][x]])
        im = im.resize((cv.w * scale_x, cv.h * scale_y), Image.NEAREST)
        im.save(os.path.join(PREVIEW, name))

    # playfield with a few units to judge the art
    demo = render_background(grid, True)
    placed = [(art.CRETAN, 4, 2), (art.YIAYIA, 9, 3), (art.BRIDE, 13, 5), (art.PSSSST, 6, 5),
              (art.CAULDRON, 10, 8), (art.BAKER, 12, 11), (art.CAULDRON_CRUSHED, 16, 11)]
    for rows, c, r in placed:
        demo.blit(rows, c * TW, r * TH)
    gp = path_steps(GROUND_WP)
    ap = path_steps(AIR_WP)
    for rows, (x, y) in ((art.DRONE_A, ap[60]), (art.GUARD_A, gp[100]), (art.TANK_L_A, gp[40]),
                         (art.TANK_V_A, gp[200]), (art.GUARD_B, gp[300]), (art.DRONE_B, ap[120])):
        demo.blit(rows, x * 2, y)
    demo.blit(art.FLAG_A, 28, 99)
    save(demo, "playfield.png")

    sheet = Canvas(10 * 10, 5 * 14, art.CH['n'])
    for i, (name, rows) in enumerate(art.SPRITES):
        sheet.blit(rows, (i % 10) * 10, (i // 10) * 14)
    save(sheet, "sprites.png", 8, 4)

    ft = Canvas(4 * 20, 8 * 5, art.CH['k'])
    for i, (ch, _) in enumerate(font.GLYPHS):
        ft.text(ch, (i % 20) * 4, (i // 20) * 8 + 1, art.CH['W'])
    save(ft, "font.png", 8, 4)

    print("tiles: %d (%d bytes)" % (len(tile_list), len(tile_list) * 48))


if __name__ == "__main__":
    main()
