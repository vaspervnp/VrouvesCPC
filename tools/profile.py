#!/usr/bin/env python3
"""Where does the CPU go during the stress fight (see bench.py)."""
import bisect
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402
from cpcsim import SLICE  # noqa: E402

s = scenario.start()
p = scenario.Player(s)
for t, c, r in scenario.PLAN:
    p.build(t, c, r)
s.tap('N')
s.run_frames(400)
syms = sorted((v, n.split('.')[0]) for n, v in s.syms.items() if 0x40 <= v < 0x4000)
keys = [v for v, n in syms]
prof = collections.Counter()
for f in range(300):
    for k in range(6):
        s.vsync = (k == 0)
        pend, left = True, SLICE
        while left > 0:
            if pend and s.m.on_handle_active_int():
                pend = False
            s.m.ticks_to_stop = 64
            s.m.run()
            left -= 64
            prof[syms[bisect.bisect_right(keys, s.m.pc) - 1][1]] += 1
    s.frame += 1
tot = sum(prof.values())
for n, c in prof.most_common(25):
    print("%-22s %5.1f%%" % (n, 100 * c / tot))
