#!/usr/bin/env python3
"""Screenshots of the game in English for assets/screenshots/: the title
pages, then every stage played by the test bot (tools/scenario.py), caught
mid-battle when the road is busy, and the stage announcements.

    tools/screenshots.py          (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402
from cpcsim import CPC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "screenshots")
BUSY = 9            # invaders on screen for a battle shot


def shot(s, name):
    path = os.path.join(OUT, name + ".png")
    s.screenshot(path, scale=2)
    print(path)


def title_pages():
    s = CPC(os.path.join(ROOT, "build/VROUVES.BIN"), os.path.join(ROOT, "build/vrouves.sym"))
    s.run_frames(120)
    for k, name in enumerate(("keys", "story", "defenders", "invaders")):
        if k:
            s.tap('RIGHT')
            s.run_frames(40)
        shot(s, "title_%d_%s" % (k + 1, name))


def play(s, plan, stg):
    """scenario.play_stage, with a shot of the start and of a busy wave"""
    p = scenario.Player(s)
    todo = scenario.available(s, plan)
    s.run_frames(40)                # palette on, the stage announced
    shot(s, "stage%d_start" % stg)
    taken = False
    while s.byte('game_over') == 0:
        while todo and s.word('funds') >= scenario.COST[todo[0][0]] and not s.byte('game_over'):
            p.build(*todo.pop(0))
        if s.byte('wave_state') == 0 and (not todo or s.word('funds') < scenario.COST[todo[0][0]]):
            s.tap('N')
        s.run_frames(25)
        if not taken and s.byte('wave_num') >= 6 and s.byte('en_count') >= BUSY:
            s.run_frames(30)
            shot(s, "stage%d_battle" % stg)
            taken = True
        if s.frame > 400000:
            break
    if not taken:
        shot(s, "stage%d_battle" % stg)


def stages():
    s = scenario.start()
    while True:
        stg = s.byte('stage') + 1
        play(s, scenario.PLANS[stg - 1], stg)
        print("stage %d:" % stg, "WON" if s.byte('game_over') == 1 else "LOST")
        if s.byte('game_over') != 1:
            break
        if stg == len(scenario.PLANS):
            s.run_frames(50)
            shot(s, "victory")
            break
        scenario.next_stage(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.chdir(ROOT)
    title_pages()
    stages()


if __name__ == "__main__":
    main()
