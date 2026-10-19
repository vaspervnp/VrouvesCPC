#!/usr/bin/env python3
"""The cassette version played through on the headless CPC, from
build/vrouves.cdt: the title, every stage loaded in turn, a lost stage
played again without loading, the ending loaded, and the reset after it.

    tools/tapecheck.py              (after ./build.sh)
"""
import os
import sys

os.environ["TAPE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402
from cpcsim import Crash  # noqa: E402


def lose_and_retry():
    """no defenders at all: stage 1 falls, and comes back with no tape motion"""
    s = scenario.start()
    while not s.byte('game_over'):
        s.tap('N')
        s.run_frames(100)
    print("stage 1 lost:", scenario.status(s))
    pos = s.tape.pos
    for _ in range(50):
        s.tap('SPACE')
        s.run_frames(20)
        if not s.byte('game_over'):
            break
    s.run_frames(100)
    ok = not s.byte('game_over') and s.byte('stage') == 0 and s.tape.pos == pos and not s.tape.motor
    print("played again, no reload:", "OK" if ok else "FAILED", scenario.status(s))
    return ok


def full_and_ending():
    s = scenario.start()
    for stg in range(len(scenario.PLANS)):
        scenario.play_stage(s, scenario.PLANS[stg], verbose=False)
        print("stage %d:" % (stg + 1), "WON" if s.byte('game_over') == 1 else "LOST", scenario.status(s))
        if s.byte('game_over') != 1:
            return False
        if stg + 1 < len(scenario.PLANS):
            scenario.next_stage(s)
    for _ in range(100):            # the victory banner, then the ending loads
        s.tap('SPACE')
        s.run_frames(20)
        if s.tape.motor:
            break
    scenario.wait_load(s)
    s.run_frames(50)
    end = open("build/tape/ENDING.SCR", "rb").read()
    ok = s.peek(0xC000, 2000) == end[:2000]
    s.screenshot("build/tape_ending.png", scale=2)
    print("ending loaded:", "OK" if ok else "FAILED")
    try:
        s.tap('SPACE')
        s.run_frames(50)
        print("no reset after the ending: FAILED")
        return False
    except Crash as e:
        # the firmware's ROM is not emulated: it was switched in, for the RST 0 to reset
        reset = s.lower_rom
        print("reset after the ending:", "OK" if reset else "FAILED", "(%s)" % e)
        return ok and reset


if __name__ == "__main__":
    good = lose_and_retry() and full_and_ending()
    print("tape:", "OK" if good else "FAILED")
    sys.exit(0 if good else 1)
