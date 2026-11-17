#!/usr/bin/env python3
"""The defenders and stages that came after the first seven, on the headless
CPC: the Lyra player (built with 7, his tune hits walkers and drones around
him and slows the drones, his neighbours), the two roads of the olive press,
the Shepherd (8, his stones throw guards back), the Priest (9, his bell holds
the invaders still, his neighbours reload twice as fast), and the wedding
without the Bride and the Priest.

    tools/lyracheck.py              (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

ok = True
CRETAN, YIAYIA, BRIDE, PSSSST, CAULDRON, BAKER, LYRA, SHEPHERD, PRIEST = range(1, 10)
E_TYPE, E_HP, E_MAXHP, E_PROG, E_X, E_Y, E_SLOW, E_SEG = 0, 1, 2, 6, 8, 9, 10, 13


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


def mask(s):
    return s.word('stage_unlock')


def rich(s):
    s.m.set_memory_block(s.sym('funds'), bytes([0xE8, 0x03]))      # 1000 vrouves


def stage8():
    s = scenario.start(stage=8)
    check("stage 8: the first seven defenders", mask(s), 0x7F)
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
    rich(s2)
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
    road2 = s.peek(s.sym('stage_road2'))
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
    check("stage 10: the Shepherd joins", mask(s), 0xFF)
    check("  his announcement", (s.byte('ban_id1'), s.byte('ban_id2')), ids(s, 'B_NEWDEF', 'S_INFO8'))
    p = scenario.Player(s)
    rich(s)
    check("  8 builds him", p.build(SHEPHERD, 10, 10), True)       # by two lanes
    p.build(CRETAN, 11, 10)
    s.tap('N')          # wave 1: guards
    last, back = {}, 0
    for _ in range(3000):
        s.run_frames(1)
        e0 = s.sym('enemies')
        for k in range(16):
            e = s.peek(e0 + 16 * k, 16)
            if e[E_TYPE] != 2:
                last.pop(k, None)
                continue
            prog = e[E_PROG] | e[E_PROG + 1] << 8
            if k in last and last[k][0] == e[12] and prog < last[k][1]:
                back += 1
            last[k] = (e[12], prog)
        if back >= 3 or s.byte('wave_state') == 0:
            break
    check("  his stones throw guards back", back >= 3, True)
    s.screenshot("build/shepherd_stage10.png")
    # his neighbour: the Lyra player +50%
    s2 = scenario.start(stage=10)
    p = scenario.Player(s2)
    rich(s2)
    p.build(SHEPHERD, 10, 10)
    p.build(LYRA, 11, 10)
    syn = {(r[1], r[2]): r[7] for r in towers(s2)}
    check("  by a Lyra player: +50%", syn[(10, 10)], 24)


def stage13():
    s = scenario.start(stage=13)
    check("stage 13: the Priest joins", mask(s), 0x1FF)
    check("  his announcement", (s.byte('ban_id1'), s.byte('ban_id2')), ids(s, 'B_NEWDEF', 'S_INFO9'))
    p = scenario.Player(s)
    rich(s)
    check("  9 builds him", p.build(PRIEST, 16, 11), True)         # by the corner of the road
    p.build(CRETAN, 15, 11)             # blessed
    p.build(CRETAN, 1, 11)              # not: at the road's start
    t0 = s.sym('towers')
    slot = {(s.peek(t0 + 8 * k + 1), s.peek(t0 + 8 * k + 2)): k for k in range(32) if s.peek(t0 + 8 * k)}
    s.tap('N')          # wave 1: guards
    still = 0
    seen = {}
    cds = {(15, 11): 0, (1, 11): 0}
    for _ in range(4000):
        s.run_frames(1)
        e0 = s.sym('enemies')
        for k in range(16):
            e = s.peek(e0 + 16 * k, 16)
            if e[E_TYPE] and e[E_SLOW] > 40:
                if seen.get(k) == (e[E_X], e[E_Y]):
                    still += 1
                seen[k] = (e[E_X], e[E_Y])
        for cell in cds:
            cds[cell] = max(cds[cell], s.peek(t0 + 8 * slot[cell] + 3))
        if s.byte('wave_state') == 0 and s.byte('wave_num') == 1:
            break
    check("  his bell holds them still", still > 0, True)
    check("  a Cretan by him reloads in half the time", cds[(15, 11)], 9)
    check("  one away from him as ever", cds[(1, 11)], 18)
    s.screenshot("build/priest_stage13.png")


def stage20():
    s = scenario.start(stage=20)
    m = mask(s)
    check("stage 20: no Bride, no Priest", (m >> 2 & 1, m >> 8 & 1), (0, 0))
    check("  the Lyra player and the Shepherd are there", (m >> 6 & 1, m >> 7 & 1), (1, 1))
    check("  the announcement", (s.byte('ban_id1'), s.byte('ban_id2')), ids(s, 'B_BRIDE', 'B_BRIDE2'))
    for key, t in (('3', BRIDE), ('9', PRIEST)):
        s.tap(key)
        s.run_frames(10)
        check("  %s does not choose them" % key, s.byte('sel_type') != t, True)
    s.tap('8')
    s.run_frames(10)
    check("  8 the Shepherd", s.byte('sel_type'), SHEPHERD)
    s.screenshot("build/wedding_stage20.png")


stage8()
stage9()
stage10()
stage13()
stage20()
print("lyra:", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
