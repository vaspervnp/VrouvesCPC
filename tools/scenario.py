#!/usr/bin/env python3
"""Scripted play-throughs on the headless CPC (tools/cpcsim.py).

    tools/scenario.py stress      many towers, later waves, look for crashes
    tools/scenario.py full        a normal game from wave 1 with a build plan
    tools/scenario.py stage       just the stage the build starts at
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cpcsim import CPC, Crash  # noqa: E402

TYPES = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6'}


class Player:
    def __init__(self, sim):
        self.sim = sim
        self.c, self.r = 7, 3

    def goto(self, c, r):
        s = self.sim
        for _ in range(200):
            cc, rr = s.byte('cur_c'), s.byte('cur_r')
            if (cc, rr) == (c, r) or s.byte('game_over'):
                return
            if cc < c:
                s.tap('RIGHT')
            elif cc > c:
                s.tap('LEFT')
            elif rr < r:
                s.tap('DOWN')
            else:
                s.tap('UP')
            for _ in range(16):     # wait until the game has moved the cursor
                if (s.byte('cur_c'), s.byte('cur_r')) != (cc, rr):
                    break
                s.run_frames(1)
        raise RuntimeError("cursor stuck")

    def build(self, t, c, r):
        self.goto(c, r)
        s = self.sim
        if s.byte('game_over'):
            return False
        s.tap(TYPES[t])
        for _ in range(20):
            if s.byte('sel_type') == t:
                break
            s.run_frames(1)
        before = s.word('funds')
        s.tap('SPACE')
        for _ in range(20):         # wait for the game to take the keypress
            if s.word('funds') < before:
                return True
            s.run_frames(1)
        return False


def status(s):
    return "frame %d stage %d wave %d state %d hp %d funds %d enemies %d" % (
        s.frame, s.byte('stage') + 1, s.byte('wave_num'), s.byte('wave_state'), s.byte('hp'),
        s.word('funds'), s.byte('en_count'))


TAPE = os.environ.get("TAPE") == "1"     # the cassette version, played from build/vrouves.cdt


def wait_load(s):
    """on tape: until the block the game asked for has loaded"""
    if TAPE:
        for _ in range(100):
            if s.tape.motor:
                break
            s.run_frames(2)
        while s.tape.motor:
            s.run_frames(25)


def start(binf="build/VROUVES.BIN", sym="build/vrouves.sym"):
    if TAPE:
        s = CPC("build/tape/VROUVES.BIN", "build/tape/vrouves.sym", cdtfile="build/vrouves.cdt")
        title = open("build/tape/TITLE.BIN", "rb").read()
        while s.peek(0x8000, 64) != title[:64] or s.tape.motor:      # the title loads
            s.run_frames(50)
    else:
        s = CPC(binf, sym)
    s.run_frames(60)
    s.tap('SPACE')
    wait_load(s)
    while not s.byte('msg_on') or s.ink[1] == 0x54:     # game set up and showing its message
        s.run_frames(5)
    s.run_frames(5)
    return s


PLAN = [(1, 7, 3), (3, 9, 2), (4, 5, 2), (5, 6, 3), (2, 3, 2), (1, 11, 5), (3, 13, 5),
        (6, 16, 5), (4, 13, 6), (5, 9, 6), (2, 7, 6), (1, 9, 8), (3, 11, 8), (4, 10, 9),
        (6, 12, 9), (5, 14, 9), (3, 16, 9), (1, 12, 11), (2, 14, 11), (4, 16, 11),
        (6, 9, 11), (3, 8, 13), (1, 13, 13)]


def stress():
    s = start()
    p = Player(s)
    for t, c, r in stress_plan(s):
        p.build(t, c, r)
    print("built:", status(s))
    s.tap('N')
    try:
        for i in range(60):
            s.run_frames(50)
            if i % 10 == 0:
                print(status(s))
                s.screenshot("build/stress_%02d.png" % i)
    except Crash as e:
        print("CRASH", e)
        s.screenshot("build/stress_crash.png")
        return 1
    s.screenshot("build/stress_end.png")
    print("end:", status(s))
    return 0


COST = {1: 35, 2: 50, 3: 70, 4: 80, 5: 110, 6: 60}

# a sensible build order for Stage 01
FULL_PLAN = [(1, 3, 2), (1, 16, 2), (2, 3, 3), (3, 14, 3), (6, 9, 3), (1, 12, 5), (5, 3, 5),
             (4, 16, 5), (2, 9, 6), (3, 13, 6), (5, 9, 8), (6, 15, 9), (4, 12, 11), (3, 16, 11),
             (1, 7, 13), (2, 11, 11), (5, 14, 11), (4, 7, 9), (6, 5, 10), (3, 6, 6)]
# and for Stage 02, the church
PLAN2 = [(1, 8, 8), (1, 11, 7), (3, 9, 4), (6, 9, 11), (2, 9, 9), (1, 16, 10), (5, 11, 11),
         (4, 14, 7), (3, 12, 8), (2, 16, 8), (5, 9, 8), (6, 2, 8), (1, 3, 5), (4, 12, 10),
         (3, 6, 3), (2, 8, 3), (5, 16, 11), (6, 14, 11), (3, 2, 11), (1, 13, 6)]
# and for Stage 03, the town hall
PLAN3 = [(1, 4, 8), (1, 9, 6), (3, 8, 10), (6, 3, 3), (2, 4, 9), (1, 11, 10), (5, 8, 7),
         (4, 12, 7), (3, 14, 4), (2, 8, 12), (5, 4, 4), (6, 11, 9), (1, 16, 4), (4, 7, 3),
         (3, 3, 8), (2, 9, 3), (5, 12, 4), (6, 8, 4), (3, 7, 12), (1, 13, 4),
         (1, 5, 1), (3, 9, 1), (6, 14, 1), (1, 16, 3), (2, 5, 6), (4, 13, 6), (3, 16, 6),
         (5, 15, 7), (6, 5, 9), (1, 9, 10), (3, 7, 9), (2, 11, 7)]
# and for Stage 04, the bakery
PLAN4 = [(1, 7, 4), (1, 10, 7), (3, 7, 8), (6, 9, 4), (2, 5, 10), (1, 15, 10), (5, 9, 11),
         (4, 10, 4), (3, 14, 7), (2, 16, 7), (5, 12, 8), (6, 3, 7), (1, 18, 8), (4, 7, 1),
         (3, 12, 10), (2, 9, 3), (5, 3, 10), (6, 13, 11), (3, 18, 11), (1, 5, 7),
         (6, 12, 5), (2, 11, 5), (5, 14, 5), (3, 6, 10), (1, 15, 8), (6, 11, 10), (3, 4, 5),
         (2, 18, 10)]
# and for Stage 05, the school
PLAN5 = [(1, 8, 7), (1, 14, 5), (3, 12, 7), (6, 8, 10), (2, 5, 7), (1, 15, 4), (5, 11, 8),
         (4, 4, 8), (3, 13, 10), (2, 14, 7), (5, 6, 10), (6, 7, 5), (1, 18, 10), (4, 15, 8),
         (3, 5, 11), (2, 10, 11), (5, 13, 5), (6, 18, 7), (3, 8, 8), (1, 3, 7), (6, 12, 5),
         (2, 11, 10), (5, 15, 10), (3, 9, 5), (1, 6, 11), (6, 12, 10), (3, 18, 8),
         (5, 9, 7), (2, 15, 5)]
# and for Stage 06, the pitch
PLAN6 = [(1, 4, 5), (1, 16, 6), (3, 4, 9), (6, 8, 2), (2, 3, 6), (1, 15, 3), (5, 15, 9),
         (4, 13, 2), (3, 16, 10), (2, 16, 4), (5, 5, 4), (6, 14, 4), (1, 5, 10), (3, 12, 2),
         (4, 3, 10), (2, 9, 2), (5, 14, 10), (6, 15, 6), (3, 1, 5), (1, 18, 8), (5, 7, 2),
         (3, 5, 7), (6, 14, 7), (2, 18, 10)]
# and for Stage 07, the cemetery church
PLAN7 = [(1, 11, 10), (1, 9, 10), (3, 9, 6), (6, 11, 12), (2, 11, 9), (1, 9, 2), (5, 9, 12),
         (3, 13, 12), (4, 12, 10), (2, 9, 11), (6, 3, 5), (1, 15, 12), (5, 11, 8), (3, 15, 10),
         (4, 12, 4), (6, 9, 5), (2, 13, 10), (5, 3, 6), (3, 4, 2), (1, 15, 2), (6, 7, 5),
         (3, 11, 6), (5, 15, 4), (2, 7, 6), (3, 14, 10), (1, 9, 9), (6, 11, 5),
         (3, 5, 5)]
PLANS = [FULL_PLAN, PLAN2, PLAN3, PLAN4, PLAN5, PLAN6, PLAN7]


def stress_plan(s):
    """many defenders for a rich (-DDEBUG) game on the current stage"""
    return [PLAN, PLAN2, PLAN3, PLAN4, PLAN5, PLAN6, PLAN7][s.byte('stage')]


def full_plan(s):
    return PLANS[s.byte('stage')]


SUBSTITUTE = {2: [1], 3: [1, 4], 5: [4, 1], 6: [1]}


def available(s, plan):
    """the plan with defenders this stage does not have yet replaced"""
    mask = s.peek(s.sym('stage_unlock'))
    out = []
    for t, c, r in plan:
        if not mask >> (t - 1) & 1:
            t = next(u for u in SUBSTITUTE[t] if mask >> (u - 1) & 1)
        out.append((t, c, r))
    return out


def play_stage(s, plan, verbose=True):
    p = Player(s)
    todo = available(s, plan)
    last_wave = -1
    while s.byte('game_over') == 0:
        while todo and s.word('funds') >= COST[todo[0][0]] and not s.byte('game_over'):
            t, c, r = todo.pop(0)
            if not p.build(t, c, r) and verbose and not s.byte('game_over'):
                print("could not build", t, c, r, "cursor", s.byte('cur_c'), s.byte('cur_r'),
                      "sel", s.byte('sel_type'), "funds", s.word('funds'),
                      "paused", s.byte('paused'), "cell", s.peek(s.sym('cellmap') + r * 20 + c))
        if s.byte('wave_state') == 0 and not todo or (s.byte('wave_state') == 0 and
                                                      s.word('funds') < COST[todo[0][0]]):
            s.tap('N')
        s.run_frames(25)
        w = s.byte('wave_num')
        if w != last_wave:
            if verbose:
                print(status(s))
            last_wave = w
        if s.frame > 400000:
            break


def next_stage(s):
    """after a won stage: press fire on the banner, wait for the next stage"""
    stg = s.byte('stage')
    for _ in range(100):
        s.tap('SPACE')
        s.run_frames(20)
        if s.byte('stage') != stg:
            break
    wait_load(s)
    while not (s.byte('msg_on') and s.byte('stage') != stg) or s.ink[1] == 0x54:
        s.run_frames(5)
    s.run_frames(5)


def full(plan=None, verbose=True):
    s = start()
    try:
        while True:
            stg = s.byte('stage')
            play_stage(s, plan or PLANS[stg], verbose)
            print("stage %d:" % (stg + 1), "WON" if s.byte('game_over') == 1 else "LOST", status(s))
            s.screenshot("build/full_stage%d.png" % (stg + 1))
            if s.byte('game_over') != 1 or stg + 1 >= len(PLANS) or plan:
                break
            next_stage(s)
    except Crash as e:
        print("CRASH", e)
        s.screenshot("build/full_crash.png")
        return 1
    s.screenshot("build/full_end.png")
    print("result:", "WON" if s.byte('game_over') == 1 else "LOST", status(s),
          "game minutes %.1f" % (s.frame / 50 / 60))
    return 0


def one_stage():
    s = start()
    play_stage(s, full_plan(s), verbose=False)
    print("stage %d:" % (s.byte('stage') + 1), "WON" if s.byte('game_over') == 1 else "LOST",
          status(s))
    return 0


if __name__ == "__main__":
    sys.exit({"stress": stress, "full": full, "stage": one_stage}[sys.argv[1]]())
