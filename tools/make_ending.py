#!/usr/bin/env python3
"""The Blender render of the ending (tools/wedding_blender.py) -> a picture in
CPC colours for tools/png_to_scr.py: 640x400, Mode 0 pixels as 4x2 blocks,
16 of the 27 colours, picked to fit it (as for the splash screen) and
lightly dithered.

    tools/make_ending.py <render.png> <out.png>
"""
import os
import sys

from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
import make_splash as ms  # noqa: E402

SATURATION = 1.5
DITHER = 0.25           # a cartoon: mostly flat colours
SKY = 11                # the flat sky of the render becomes the CPC's sky blue


def main():
    src, out = sys.argv[1:3]
    im = ImageEnhance.Color(Image.open(src).convert("RGB")).enhance(SATURATION)
    im = im.resize((ms.W, ms.H), Image.LANCZOS)
    pixels = list(im.get_flattened_data())
    sky = pixels[0]
    pixels = [ms.CPC[SKY] if ms.dist(p, sky) < 300 else p for p in pixels]
    inks = ms.pick_inks(pixels)
    pal = [ms.CPC[c] for c in inks]
    ms.DITHER = DITHER
    pens = ms.dither(pixels, pal)
    res = Image.new("RGB", (ms.W, ms.H))
    res.putdata([pal[p] for p in pens])
    res.resize((ms.W * 4, ms.H * 2), Image.NEAREST).save(out)
    print("ending inks", inks)


if __name__ == "__main__":
    main()
