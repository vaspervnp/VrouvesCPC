#!/usr/bin/env python3
"""Scripted play-throughs on the headless CPC (tools/cpcsim.py).

    tools/scenario.py stress      many towers, later waves, look for crashes
    tools/scenario.py full        a normal game from wave 1 with a build plan
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
            if (cc, rr) == (c, r):
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
    return "frame %d wave %d state %d hp %d funds %d enemies %d" % (
        s.frame, s.byte('wave_num'), s.byte('wave_state'), s.byte('hp'),
        s.word('funds'), s.byte('en_count'))


def start(binf="build/VROUVES.BIN", sym="build/vrouves.sym"):
    s = CPC(binf, sym)
    s.run_frames(60)
    s.tap('SPACE')
    while not s.byte('msg_on'):     # game set up and showing its message
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
    for t, c, r in PLAN:
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


COST = {1: 30, 2: 50, 3: 70, 4: 80, 5: 110, 6: 60}

# a sensible build order for Stage 01
FULL_PLAN = [(1, 3, 2), (1, 16, 2), (2, 3, 3), (3, 14, 3), (6, 9, 3), (1, 12, 5), (5, 3, 5),
             (4, 16, 5), (2, 9, 6), (3, 13, 6), (5, 9, 8), (6, 16, 8), (4, 12, 11), (3, 16, 11),
             (1, 7, 13), (2, 10, 11), (5, 14, 11), (4, 7, 9), (6, 5, 10), (3, 6, 6)]


def full(plan=FULL_PLAN, verbose=True):
    s = start()
    p = Player(s)
    todo = list(plan)
    last_wave = -1
    try:
        while s.byte('game_over') == 0:
            while todo and s.word('funds') >= COST[todo[0][0]]:
                t, c, r = todo.pop(0)
                if not p.build(t, c, r) and verbose:
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
            if s.frame > 200000:
                break
    except Crash as e:
        print("CRASH", e)
        s.screenshot("build/full_crash.png")
        return 1
    s.screenshot("build/full_end.png")
    print("result:", "WON" if s.byte('game_over') == 1 else "LOST", status(s),
          "game minutes %.1f" % (s.frame / 50 / 60))
    return 0


if __name__ == "__main__":
    sys.exit({"stress": stress, "full": full}[sys.argv[1]]())
