#!/usr/bin/env python3
"""What costs the most: CPU time by game activity during a busy wave of a
normal game.  Samples PC every 64 T-states and charges each sample to the
nearest known caller found on the stack."""
import bisect
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402
from cpcsim import SLICE  # noqa: E402

WAVE = int(sys.argv[1]) if len(sys.argv) > 1 else 8
CATS = [
    ('INT_HANDLER', 'interrupt: music, sfx, keyboard scan'),
    ('WAIT_FRAME', 'waiting for the frame (idle)'),
    ('FLIP', 'waiting for the frame (idle)'),
    ('RESTORE_DIRTY', 'erase: restore background under sprites'),
    ('DRAW_ENEMIES', 'draw enemies (+ health bars)'),
    ('DRAW_PROJS', 'draw projectiles'),
    ('DRAW_FX', 'draw effects'),
    ('DRAW_FLAG', 'draw flag + cursor'),
    ('DRAW_CURSOR', 'draw flag + cursor'),
    ('HUD_REFRESH', 'HUD text'),
    ('UPDATE_TOWERS', 'towers: targeting and firing'),
    ('UPDATE_ENEMIES', 'enemies: movement'),
    ('UPDATE_PROJS', 'projectiles: flight and hits'),
    ('UPDATE_FX', 'effects: timers'),
    ('WAVE_UPDATE', 'waves / spawning'),
    ('HANDLE_INPUT', 'input'),
    ('KBD_UPDATE', 'input'),
]

s = scenario.start()
p = scenario.Player(s)
todo = list(scenario.FULL_PLAN)
while s.byte('wave_num') < WAVE or s.byte('wave_state') == 0:
    while todo and s.word('funds') >= scenario.COST[todo[0][0]]:
        t, c, r = todo.pop(0)
        p.build(t, c, r)
    if s.byte('wave_state') == 0:
        s.tap('N')
    s.run_frames(25)
s.run_frames(150)

syms = sorted((v, n) for n, v in s.syms.items() if 0x40 <= v < 0x4000 and '.' not in n)
keys = [v for v, n in syms]
roots = {s.sym(n): d for n, d in CATS}


def func(a):
    i = bisect.bisect_right(keys, a) - 1
    return syms[i][0] if i >= 0 else None


def category():
    f = func(s.m.pc)
    if f in roots:
        return roots[f]
    sp = s.m.sp
    for k in range(12):
        ret = s.peek(sp + 2 * k) | s.peek(sp + 2 * k + 1) << 8
        f = func(ret)
        if f in roots:
            return roots[f]
    return 'other'


prof = collections.Counter()
counts = collections.Counter()
draws = 0
last = s.byte('last_flip')
FR = 600
for _ in range(FR):
    for k in range(6):
        s.vsync = (k == 0)
        pend, left = True, SLICE
        while left > 0:
            if pend and s.m.on_handle_active_int():
                pend = False
            s.m.ticks_to_stop = 64
            s.m.run()
            left -= 64
            prof[category()] += 1
    s.frame += 1
    v = s.byte('last_flip')
    if v != last:
        draws += 1
        last = v
        counts['enemies'] += s.byte('en_count')
        counts['projectiles'] += sum(1 for i in range(20) if s.peek(0xBE00 + i * 10))
        counts['effects'] += sum(1 for i in range(8) if s.peek(0xBEC8 + i * 4))
tot = sum(prof.values())
idle = prof['waiting for the frame (idle)']
print("wave %d, %d drawn frames, average on screen: %s" % (
    WAVE, draws, ", ".join("%.1f %s" % (counts[k] / draws, k) for k in counts)))
print("%-42s %6s %8s" % ("", "total", "of work"))
for name, c in prof.most_common():
    pct_work = "" if name.startswith('waiting') else "%7.1f%%" % (100 * c / (tot - idle))
    print("%-42s %5.1f%% %8s" % (name, 100 * c / tot, pct_work))
