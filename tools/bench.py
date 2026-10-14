#!/usr/bin/env python3
"""Rendering benchmark on the headless CPC: build two dozen defenders (debug
build, rich start at wave 9), send the wave and count game ticks.
usage: RASMFLAGS=-DDEBUG=9 ./build.sh && tools/bench.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

s = scenario.start()
p = scenario.Player(s)
for t, c, r in scenario.PLAN:
    p.build(t, c, r)
s.tap('N')
s.run_frames(100)
import collections
hist = collections.Counter()
last, frames = s.byte('last_flip'), 3000
for _ in range(frames):
    s.run_frames(1)
    v = s.byte('last_flip')
    if v != last:
        hist[s.byte('dbg_el')] += 1     # frames this drawn frame took
        last = v
ticks = sum(hist.values())
print("%.2f fps, frames per draw %s, enemies %d" % (
    50 * ticks / sum(k * n for k, n in hist.items()), dict(sorted(hist.items())),
    s.byte('en_count')))
