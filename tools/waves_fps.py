#!/usr/bin/env python3
"""Frame rate per wave in a normal game (build order from scenario.FULL_PLAN)."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

s = scenario.start()
p = scenario.Player(s)
todo = list(scenario.FULL_PLAN)
per = collections.defaultdict(collections.Counter)
last = s.byte('last_flip')
while s.byte('game_over') == 0 and s.frame < 60000:
    while todo and s.word('funds') >= scenario.COST[todo[0][0]]:
        t, c, r = todo.pop(0)
        p.build(t, c, r)
    if s.byte('wave_state') == 0:
        s.tap('N')
    for _ in range(25):
        s.run_frames(1)
        v = s.byte('last_flip')
        if v != last:
            if s.byte('wave_state') == 1:
                per[s.byte('wave_num')][s.byte('dbg_el')] += 1
            last = v
for w in sorted(per):
    h = per[w]
    n, f = sum(h.values()), sum(k * c for k, c in h.items())
    print("wave %2d: %.1f fps, %s" % (w, 50 * n / f, dict(sorted(h.items()))))
print("result:", "WON" if s.byte('game_over') == 1 else "LOST", "hp", s.byte('hp'))
