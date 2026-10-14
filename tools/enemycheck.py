#!/usr/bin/env python3
"""At every flip, check that each enemy's opaque pixels are really on the
freshly drawn back buffer (ignoring pixels where another sprite overlaps)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402
from cpcsim import SLICE  # noqa: E402

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'stress'
s = scenario.start()
p = scenario.Player(s)
plan = scenario.PLAN if DEBUG else scenario.FULL_PLAN[:12]
for t, c, r in plan:
    p.build(t, c, r)
s.tap('N')
mem = s.m.memory
FLIP = s.sym('FLIP')
ESPR = s.sym('ENEMY_SPRITES')
s.m.set_breakpoint(FLIP)


def rects():
    out = []
    for i in range(16):
        e = 0xBC00 + i * 16
        if mem[e]:
            out.append(('e', i, mem[e + 8], mem[e + 9], 4, 12))
    for i in range(20):
        q = 0xBE00 + i * 10
        if mem[q]:
            out.append(('p', i, mem[q + 1] >> 1, mem[q + 2], 2, 5))
    for i in range(8):
        f = 0xBEC8 + i * 4
        if mem[f]:
            out.append(('f', i, mem[f + 1], mem[f + 2], 4, 12))
    out.append(('c', 0, s.byte('cur_c') * 4, s.byte('cur_r') * 12, 4, 12))
    out.append(('g', 0, 14, 99, 4, 8))
    return out


def check():
    back = 0xC000 if s.byte('back_mask') == 0xFF else 0x4000
    est = s.word('es_base')
    rs = rects()
    bad = 0
    for i in range(16):
        e = 0xBC00 + i * 16
        if not mem[e]:
            continue
        x, y = mem[e + 8], mem[e + 9]
        st = est + i * 4
        idx = mem[st + 3]
        spr = mem[ESPR + idx * 2] | mem[ESPR + idx * 2 + 1] << 8
        for row in range(12):
            sy = y + row + 16
            a = back + (sy >> 3) * 80 + (sy & 7) * 0x800
            for col in range(4):
                d = mem[spr + 2 + row * 4 + col]
                for mask in (0xAA, 0x55):
                    if d & mask == 0:
                        continue      # transparent pixel
                    px, py = x + col, y + row
                    if any(not (k == 'e' and j == i) and rx <= px < rx + rw and ry <= py < ry + rh
                           for k, j, rx, ry, rw, rh in rs):
                        continue
                    if mem[a + x + col] & mask != d & mask:
                        bad += 1
    return bad


flips = badflips = 0
for f in range(2500):
    for k in range(6):
        s.vsync = (k == 0)
        pend, left = True, SLICE
        while left > 0:
            if pend and s.m.on_handle_active_int():
                pend = False
            s.m.ticks_to_stop = left
            ev = s.m.run()
            if ev & s.m._BREAKPOINT_HIT:
                flips += 1
                b = check()
                if b:
                    badflips += 1
                    if badflips <= 3:
                        print("frame %d: %d enemy pixels missing" % (s.frame, b))
                s.m.clear_breakpoint(FLIP)
                s.m.ticks_to_stop = 8
                s.m.run()
                s.m.set_breakpoint(FLIP)
                left = max(0, left - 8 - (left - s.m.ticks_to_stop if s.m.ticks_to_stop else 0))
            else:
                left = 0
    s.frame += 1
    if s.byte('game_over'):
        break
print("checked %d frames, %d with missing enemy pixels" % (flips, badflips))
sys.exit(1 if badflips else 0)
