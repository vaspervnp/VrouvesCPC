#!/usr/bin/env python3
"""Pictures for the manuals (docs/img/): the defenders and invaders drawn
from tools/art.py, the stages from the asset previews, and the title and
game screens from the headless CPC in both languages.

    tools/manual_images.py        (after ./build.sh)
"""
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402
import scenario  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "img")

SPRITES = {
    "cretan": art.CRETAN, "yiayia": art.YIAYIA, "bride": art.BRIDE,
    "psssst": art.PSSSST, "cauldron": art.CAULDRON, "baker": art.BAKER,
    "drone": art.DRONE_A, "guard": art.GUARD_A, "tank": art.TANK_V_A,
}


def sprite_png(rows, path, scale=6):
    """Mode 0 pixels are twice as wide as tall; transparent stays transparent"""
    w, h = len(rows[0]), len(rows)
    im = Image.new("RGBA", (w * 2 * scale, h * scale), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.':
                continue
            pen = 0 if ch in 'kn' else art.CH[ch]
            rgb = art.PEN_RGB[pen] + (255,)
            for dy in range(scale):
                for dx in range(2 * scale):
                    im.putpixel((x * 2 * scale + dx, y * scale + dy), rgb)
    im.save(path)


def screens():
    s = scenario.start()
    p = scenario.Player(s)
    s.run_frames(5)
    for t, c, r in [(1, 3, 2), (1, 16, 2), (4, 14, 3), (1, 12, 5), (4, 9, 3)]:
        p.build(t, c, r)
    s.tap('N')
    s.run_frames(700)
    s.screenshot(os.path.join(OUT, "game_en.png"), scale=2)
    s.tap('L')
    s.run_frames(20)
    s.screenshot(os.path.join(OUT, "game_gr.png"), scale=2)


def title():
    from cpcsim import CPC
    s = CPC(os.path.join(ROOT, "build/VROUVES.BIN"), os.path.join(ROOT, "build/vrouves.sym"))
    s.run_frames(120)
    s.screenshot(os.path.join(OUT, "title_en.png"), scale=2)
    s.tap('L')
    s.run_frames(30)
    s.screenshot(os.path.join(OUT, "title_gr.png"), scale=2)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, rows in SPRITES.items():
        sprite_png(rows, os.path.join(OUT, name + ".png"))
    prev = os.path.join(ROOT, "build", "preview")
    k = 1
    while os.path.exists(os.path.join(prev, "playfield%d.png" % k)):
        shutil.copy(os.path.join(prev, "playfield%d.png" % k), os.path.join(OUT, "stage%d.png" % k))
        k += 1
    os.chdir(ROOT)
    title()
    screens()
    print("pictures in", OUT)


if __name__ == "__main__":
    main()
