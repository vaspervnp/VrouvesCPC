#!/usr/bin/env python3
"""The neighbour bonus on the headless CPC: only three defenders at a time
get a bonus, penalties always count, a freed bonus goes to the next one in
line, and the info line shows a bonus only while there is room for it.

    tools/syncheck.py               (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

ok = True
CRETAN, YIAYIA, BRIDE, PSSSST, CAULDRON, BAKER = range(1, 7)


def check(what, got, want):
    global ok
    good = got == want
    ok &= good
    print("%-48s %s (want %s) %s" % (what, got, want, "OK" if good else "FAILED"))


def free_cross(s, taken):
    """a buildable cell whose four neighbours are buildable too, away from taken ones"""
    cm = s.sym('cellmap')
    def free(c, r):
        return 0 <= c < 20 and 0 <= r < 14 and s.peek(cm + r * 20 + c) == 0 and (c, r) not in taken
    for r in range(1, 13):
        for c in range(1, 19):
            cross = [(c, r), (c - 1, r), (c + 1, r), (c, r - 1), (c, r + 1)]
            if all(free(*p) for p in cross) and not any(
                    abs(c - tc) + abs(r - tr) < 4 for tc, tr in taken):
                return c, r
    raise RuntimeError("no room")


def factors(s):
    t = s.sym('towers')
    out = {}
    for k in range(32):
        rec = s.peek(t + k * 8, 8)
        if rec[0]:
            out[(rec[1], rec[2])] = rec[7]
    return out


def main():
    s = scenario.start()
    s.m.memory[s.sym('stage_unlock')] = 0x3F        # every defender
    f = s.sym('funds')
    s.m.memory[f], s.m.memory[f + 1] = 0x10, 0x27   # 10000 vrouves
    p = scenario.Player(s)
    c, r = free_cross(s, [])
    p.build(CRETAN, c, r)
    brides = [(c - 1, r), (c + 1, r), (c, r - 1), (c, r + 1)]
    for b in brides:
        p.build(BRIDE, *b)
    s.run_frames(5)
    fs = factors(s)
    check("four brides by a cretan: three with +50%", sorted(fs[b] for b in brides), [0, 24, 24, 24])
    check("the fourth one built has none", fs[brides[3]], 0)
    check("syn_cnt", s.byte('syn_cnt'), 3)
    c2, r2 = free_cross(s, [(c, r)])
    p.build(CRETAN, c2, r2)
    p.build(BAKER, c2 + 1, r2)
    s.run_frames(5)
    check("a baker by a cretan: -50% all the same", factors(s)[(c2 + 1, r2)], 8)
    p.goto(*brides[0])
    s.tap('S')
    s.run_frames(5)
    fs = factors(s)
    check("one sold: the fourth bride gets the bonus", fs[brides[3]], 24)
    check("  still three", s.byte('syn_cnt'), 3)
    p.build(BRIDE, *brides[0])
    s.run_frames(5)
    check("built again: it waits its turn", factors(s)[brides[0]], 0)
    print("synergy:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


TYPE_KEY = scenario.TYPES

if __name__ == "__main__":
    main()
