#!/usr/bin/env python3
"""assets/vrouves.jpeg -> the splash screen: build/SPLASH.SCR (Mode 0, 16K,
loads at &C000) and build/splash_inks.txt (its 16 firmware colours, read by
tools/make_boot.py), plus build/preview/splash.png.

The 16 inks are picked from the 27 CPC colours to fit the picture (in Lab,
which keeps the hues), which is then lightly dithered; the English title goes
over the sky in its own chunky letters.
"""
import os
import sys
from collections import Counter

from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "vrouves.jpeg")
W, H = 160, 200
SATURATION = 1.6        # the CPC colours are bold: push the picture towards them
DITHER = 0.25           # how much of each pixel's error is spread to its neighbours
CPC = [art.fw_rgb(n) for n in range(27)]


def lab(c):
    """sRGB -> CIE Lab: distances there keep the hues (purple mountains, blue door)"""
    def lin(u):
        u /= 255
        return ((u + 0.055) / 1.055) ** 2.4 if u > 0.04045 else u / 12.92
    r, g, b = map(lin, c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.9505
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.089

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


CPC_LAB = [lab(c) for c in CPC]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def pick_inks(labs):
    """greedy: start from black, add the CPC colour that lowers the error most"""
    counts = Counter(tuple(round(v / 4) * 4 for v in c) for c in labs)
    cols = list(counts.items())
    best = [dist(c, CPC_LAB[0]) for c, _ in cols]
    inks = [0]
    while len(inks) < 16:
        top = None
        for k in range(27):
            if k in inks:
                continue
            nb = [min(b_, dist(c, CPC_LAB[k])) for (c, _), b_ in zip(cols, best)]
            err = sum(b_ * n for b_, (_, n) in zip(nb, cols))
            if top is None or err < top[0]:
                top = (err, k, nb)
        inks.append(top[1])
        best = top[2]
    return inks


def dither(labs, pal):
    """Floyd-Steinberg in Lab, with only part of the error passed on"""
    buf = [list(c) for c in labs]
    out = [0] * (W * H)
    for y in range(H):
        for x in range(W):
            i = y * W + x
            c = buf[i]
            k = min(range(len(pal)), key=lambda j: dist(c, pal[j]))
            out[i] = k
            err = [(a - b) * DITHER for a, b in zip(c, pal[k])]
            for dx, dy, f in ((1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and yy < H:
                    t = buf[yy * W + xx]
                    for ch in range(3):
                        t[ch] += err[ch] * f / 16
    return out


# the title's own chunky letters (Mode 0 pixels, so each '#' is twice as wide
# as tall): a small set for "LET'S GO FOR" and a big one for "VROUVES!"
SMALL = {
    "L": ["##....", "##....", "##....", "##....", "##....", "##....", "##....", "######", "######"],
    "E": ["######", "######", "##....", "##....", "#####.", "##....", "##....", "######", "######"],
    "T": ["######", "######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    "'": ["##", "##", ".#", "..", "..", "..", "..", "..", ".."],
    "S": [".#####", "######", "##....", "#####.", ".#####", "....##", "....##", "######", "#####."],
    "G": [".#####", "######", "##....", "##....", "##.###", "##..##", "##..##", "######", ".####."],
    "O": [".####.", "######", "##..##", "##..##", "##..##", "##..##", "##..##", "######", ".####."],
    "F": ["######", "######", "##....", "##....", "#####.", "#####.", "##....", "##....", "##...."],
    "R": ["#####.", "######", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##", "##..##"],
    " ": ["..."] * 9,
}
BIG = {
    "V": ["##....##"] * 7 + [".##..##."] * 3 + ["..####.."] * 2 + ["...##..."] * 2,
    "R": ["######..", "#######.", "##...###", "##....##", "##....##", "##...###", "#######.",
          "######..", "##..##..", "##..###.", "##...##.", "##...###", "##....##", "##....##"],
    "O": [".######.", "########"] + ["##....##"] * 10 + ["########", ".######."],
    "U": ["##....##"] * 12 + ["########", ".######."],
    "E": ["########", "########"] + ["##......"] * 4 + ["######..", "######.."] +
         ["##......"] * 4 + ["########", "########"],
    "S": [".#######", "########", "##......", "##......", "##......", "#######.", ".#######",
          "......##", "......##", "......##", "......##", "......##", "########", "#######."],
    "!": ["##"] * 10 + ["..", "..", "##", "##"],
}


def stretch(rows, w, h):
    """a glyph made wider and taller: the outer two rows and columns stay as
    they are, the inner ones are repeated, so the strokes keep their width"""
    def index(n, old, new):
        if n < 2:
            return n
        if n >= new - 2:
            return old - (new - n)
        return 2 + (n - 2) * (old - 4) // (new - 4)
    ow, oh = len(rows[0]), len(rows)
    nw = w if ow > 2 else ow
    return ["".join(rows[index(j, oh, h)][index(i, ow, nw)] for i in range(nw)) for j in range(h)]


BIG = {c: stretch(r, 10, 20) for c, r in BIG.items()}


def logo(pens, near, lines):
    """lines = [(text, font, x, y)]: letters filled with a gradient from white
    through yellow and orange to red, a black outline and a dark red shadow"""
    fill = {}
    for s, fnt, x0, y0 in lines:
        h = len(next(iter(fnt.values())))
        ramp = [near(26)] + [near(24)] * (h * 2 // 5) + [near(15)] * (h - 2 - h * 2 // 5) + [near(6)]
        x = x0
        for ch in s:
            rows = fnt[ch]
            for j, r in enumerate(rows):
                for i, c in enumerate(r):
                    if c == '#':
                        fill[(x + i, y0 + j)] = ramp[j]
            x += len(rows[0]) + 1
    ring = {(x + dx, y + dy) for x, y in fill for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    shadow = {(x + 1, y + 2) for x, y in ring}
    for pts, pen in ((shadow, near(3)), (ring, near(0))):
        for x, y in pts:
            if 0 <= x < W and 0 <= y < H:
                pens[y * W + x] = pen
    for (x, y), pen in fill.items():
        pens[y * W + x] = pen


def width(s, fnt):
    return sum(len(fnt[c][0]) + 1 for c in s) - 1


def enc_byte(p0, p1):
    b = ((p0 >> 0) & 1) << 7 | ((p0 >> 1) & 1) << 3 | ((p0 >> 2) & 1) << 5 | ((p0 >> 3) & 1) << 1
    return b | ((p1 >> 0) & 1) << 6 | ((p1 >> 1) & 1) << 2 | ((p1 >> 2) & 1) << 4 | ((p1 >> 3) & 1)


def main():
    im = ImageEnhance.Color(Image.open(SRC).convert("RGB")).enhance(SATURATION)
    im = im.resize((W, H), Image.LANCZOS)
    labs = [lab(p) for p in im.get_flattened_data()]
    inks = pick_inks(labs)
    pal = [CPC[c] for c in inks]
    pens = dither(labs, [CPC_LAB[c] for c in inks])
    near = lambda fw: min(range(16), key=lambda j: dist(CPC_LAB[fw], CPC_LAB[inks[j]]))  # noqa: E731
    l1, l2 = "LET'S GO FOR", "VROUVES!"
    w1, w2 = width(l1, SMALL), width(l2, BIG)
    x0 = 6
    logo(pens, near, [(l1, SMALL, x0 + max(0, w2 - w1) // 2, 4),
                      (l2, BIG, x0 + max(0, w1 - w2) // 2, 18)])
    scr = bytearray(16384)
    for y in range(H):
        for x in range(0, W, 2):
            scr[(y % 8) * 2048 + (y // 8) * 80 + x // 2] = enc_byte(pens[y * W + x], pens[y * W + x + 1])
    os.makedirs(os.path.join(ROOT, "build", "preview"), exist_ok=True)
    open(os.path.join(ROOT, "build", "SPLASH.SCR"), "wb").write(scr)
    with open(os.path.join(ROOT, "build", "splash_inks.txt"), "w") as f:
        f.write(" ".join(map(str, inks)) + "\n")
    prev = Image.new("RGB", (W, H))
    prev.putdata([pal[p] for p in pens])
    prev.resize((W * 4, H * 2), Image.NEAREST).save(os.path.join(ROOT, "build", "preview", "splash.png"))
    print("splash inks", inks)


if __name__ == "__main__":
    main()
