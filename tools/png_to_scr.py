#!/usr/bin/env python3
"""A picture already in CPC colours (Mode 0: 160x200, or 640x400 in 4x2
blocks, at most 16 of the 27 colours) -> a 16K screen file for &C000.

    tools/png_to_scr.py <in.png> <out.scr> [PAL_OFFSET [CODE.BIN@OFFSET]]

With PAL_OFFSET the 16 gate array colours go into the file at that offset,
and CODE.BIN at its own: both meant for the hidden 48 byte tails of the
screen blocks (offsets #7D0, #FD0, ...), which the picture does not use.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402

RGB_TO_FW = {art.fw_rgb(n): n for n in range(27)}
TAILS = [k * 0x800 + 0x7D0 for k in range(8)]


def enc_byte(p0, p1):
    b = ((p0 >> 0) & 1) << 7 | ((p0 >> 1) & 1) << 3 | ((p0 >> 2) & 1) << 5 | ((p0 >> 3) & 1) << 1
    return b | ((p1 >> 0) & 1) << 6 | ((p1 >> 1) & 1) << 2 | ((p1 >> 2) & 1) << 4 | ((p1 >> 3) & 1)


def main():
    im = Image.open(sys.argv[1]).convert("RGB")
    sx, sy = im.width // 160, im.height // 200
    assert im.width == 160 * sx and im.height == 200 * sy, im.size
    px = im.load()
    fw = [[RGB_TO_FW.get(px[x * sx, y * sy]) for x in range(160)] for y in range(200)]
    missing = {px[x * sx, y * sy] for y in range(200) for x in range(160) if fw[y][x] is None}
    assert not missing, "not CPC colours: %s" % sorted(missing)[:8]
    count = {}
    for row in fw:
        for c in row:
            count[c] = count.get(c, 0) + 1
    inks = sorted(count, key=lambda c: (c != 0, -count[c]))     # black first, if there is any
    assert len(inks) <= 16, "%d colours" % len(inks)
    inks += [0] * (16 - len(inks))
    pen = {c: inks.index(c) for c in count}
    scr = bytearray(16384)
    for y in range(200):
        for x in range(0, 160, 2):
            scr[(y % 8) * 2048 + (y // 8) * 80 + x // 2] = enc_byte(pen[fw[y][x]], pen[fw[y][x + 1]])
    if len(sys.argv) > 3:
        off = int(sys.argv[3], 0)
        assert off in TAILS
        scr[off:off + 16] = bytes(art.FW_TO_HW[c] for c in inks)
    if len(sys.argv) > 4:
        path, off = sys.argv[4].split("@")
        off = int(off, 0)
        code = open(path, "rb").read()
        assert off in TAILS and len(code) <= 48, (off, len(code))
        scr[off:off + len(code)] = code
    open(sys.argv[2], "wb").write(scr)
    print("%s: inks %s" % (sys.argv[2], inks))


if __name__ == "__main__":
    main()
