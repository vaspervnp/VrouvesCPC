#!/usr/bin/env python3
"""Play a normal game; whenever the field is empty (between waves) both screen
buffers must equal the background buffer except under the cursor and flag."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402


def diffs(s):
    mem = s.m.memory
    cc, cr = s.byte('cur_c'), s.byte('cur_r')
    fl = s.sym('stage_flag')
    fy, fx = mem[fl], mem[fl + 1]
    bad = []
    for base in (0xC000, 0x4000):
        for y in range(168):
            sy = y + 16
            a = base + (sy >> 3) * 80 + (sy & 7) * 0x800
            bg = 0x8000 + y * 80
            for x in range(80):
                if mem[a + x] != mem[bg + x]:
                    if cc * 4 <= x < cc * 4 + 4 and cr * 12 <= y < cr * 12 + 12:
                        continue
                    if fx <= x < fx + 4 and fy <= y < fy + 8:
                        continue
                    bad.append((hex(base), x, y))
    return bad


s = scenario.start()
p = scenario.Player(s)
todo = scenario.available(s, scenario.full_plan(s))
checks = errors = 0
while s.byte('game_over') == 0 and s.frame < 60000:
    while todo and s.word('funds') >= scenario.COST[todo[0][0]]:
        t, c, r = todo.pop(0)
        p.build(t, c, r)
    if s.byte('wave_state') == 0:
        s.run_frames(60)           # let effects finish, both buffers redrawn
        empty = (s.byte('en_count') == 0 and
                 not any(s.peek(0xBE00 + i * 10) for i in range(20)) and
                 not any(s.peek(0xBEC8 + i * 4) for i in range(8)))
        if empty:
            checks += 1
            d = diffs(s)
            if d:
                errors += 1
                print("wave %d: %d differing bytes, e.g. %s" % (s.byte('wave_num'), len(d), d[:4]))
                s.screenshot("build/ghost_%d.png" % s.byte('wave_num'))
        s.tap('N')
    s.run_frames(25)
print("checks %d, with leftovers %d, result %s hp %d" % (
    checks, errors, "WON" if s.byte('game_over') == 1 else "LOST", s.byte('hp')))
sys.exit(1 if errors else 0)
