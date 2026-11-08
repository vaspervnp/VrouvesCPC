#!/usr/bin/env python3
"""Stages 8-10 on the headless CPC: the Lyra player (built with 7, his tune
hits walkers and drones around him and slows the drones, his neighbours),
the two roads of the olive press, and the wedding without the Bride.

    tools/lyracheck.py              (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

ok = True
CRETAN, YIAYIA, BRIDE, PSSSST, CAULDRON, BAKER, LYRA = range(1, 8)
E_TYPE, E_HP, E_MAXHP, E_X, E_SLOW, E_SEG = 0, 1, 2, 8, 10, 13


def check(what, got, want):
    global ok
    good = got == want
    ok &= good
    print("%-48s %s (want %s) %s" % (what, got, want, "OK" if good else "FAIL"))


def towers(s):
    t = s.sym('towers')
    out = []
    for k in range(32):
        rec = s.peek(t + 8 * k, 8)
        if rec[0]:
            out.append(rec)
    return out


def enemies(s):
    e = s.sym('enemies')
    return [s.peek(e + 16 * k, 16) for k in range(16) if s.peek(e + 16 * k)]


def ids(s, *names):
    return tuple(s.sym(n) for n in names)


def stage8():
    s = scenario.start(stage=8)
    check("stage 8: every defender, the Lyra player too", s.peek(s.sym('stage_unlock')), 0x7F)
    check("  his announcement", (s.byte('ban_id1'), s.byte('ban_id2')), ids(s, 'B_NEWDEF', 'S_INFO7'))
    p = scenario.Player(s)
    score = s.word('score')
    check("  7 builds him", p.build(LYRA, 4, 5), True)     # by the drones' route
    t = [r for r in towers(s) if r[0] == LYRA]
    check("  one Lyra player on the map", len(t), 1)
    check("  his damage as points", s.word('score') - score, 4)
    check("  and his price", s.word('funds'), 120 - 90)
    s.tap('N')          # wave 1: drones, along the first road and over the hut
    slowed = hit = notes = 0
    for _ in range(1500):
        s.run_frames(1)
        for e in enemies(s):
            if e[E_TYPE] == 1 and e[E_SLOW]:
                slowed += 1
            if e[E_HP] < e[E_MAXHP]:
                hit += 1
        fx = s.sym('fxs')
        notes += sum(1 for k in range(8) if s.peek(fx + 4 * k) == 7)
        if s.byte('wave_state') == 0 and s.byte('wave_num') == 1:
            break
    check("  drones charmed into slowing down", slowed > 0, True)
    check("  and hurt by the tune", hit > 0, True)
    check("  notes over them", notes > 0, True)
    s.screenshot("build/lyra_stage8.png")
    # his neighbours: a Yiayia +50%; another Lyra player -50%, and that comes first
    s2 = scenario.start(stage=8, difficulty=0)
    p = scenario.Player(s2)
    s2.m.set_memory_block(s2.sym('funds'), bytes([0xE8, 0x03]))      # 1000 vrouves
    p.build(LYRA, 8, 6)
    p.build(YIAYIA, 9, 6)
    syn = {(r[1], r[2]): r[7] for r in towers(s2)}
    check("  by a Yiayia: +50%", syn[(8, 6)], 24)
    check("  the Yiayia gets nothing from him", syn[(9, 6)], 0)
    p.build(LYRA, 7, 6)
    syn = {(r[1], r[2]): r[7] for r in towers(s2)}
    check("  two side by side: -50% for both", (syn[(8, 6)], syn[(7, 6)]), (8, 8))


def stage9():
    s = scenario.start(stage=9)
    road2 = s.peek(s.sym('stage_unlock') + 4)
    check("stage 9: a second road", road2 > 0, True)
    s.tap('N')          # wave 1: guards
    starts = {}
    seen = set()
    for _ in range(1500):
        s.run_frames(1)
        e0 = s.sym('enemies')
        for k in range(16):
            e = s.peek(e0 + 16 * k, 16)
            key = (k, e[12])            # slot, generation
            if e[0] == 2 and key not in seen:
                seen.add(key)
                starts[key] = e[E_X]
        if len(seen) >= 6:
            break
    xs = sorted(set(starts.values()))
    check("  walkers come from both sides", (min(xs) < 20, max(xs) > 60), (True, True))
    for _ in range(3000):
        s.run_frames(2)
        if s.byte('hp') < 100 or s.byte('wave_state') == 0:
            break
    check("  and reach the press", s.byte('hp') < 100, True)
    s.screenshot("build/lyra_stage9.png")


def stage10():
    s = scenario.start(stage=10)
    mask = s.peek(s.sym('stage_unlock'))
    check("stage 10: no Bride", mask >> 2 & 1, 0)
    check("  the Lyra player is there", mask >> 6 & 1, 1)
    check("  the announcement", (s.byte('ban_id1'), s.byte('ban_id2')), ids(s, 'B_BRIDE', 'B_BRIDE2'))
    s.tap('3')
    s.run_frames(10)
    check("  3 does not choose her", s.byte('sel_type') != BRIDE, True)
    s.tap('7')
    s.run_frames(10)
    check("  7 the Lyra player", s.byte('sel_type'), LYRA)
    s.screenshot("build/lyra_stage10.png")


stage8()
stage9()
stage10()
print("lyra:", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
