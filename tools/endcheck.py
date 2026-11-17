#!/usr/bin/env python3
"""The ending on the headless CPC: the last stage won, ENDING.SCR loads onto
the screen and stays there, and SPACE goes back to the title.

    tools/endcheck.py               (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

scr = open("build/ENDING.SCR", "rb").read()
title = open("build/TITLE.BIN", "rb").read()
s = scenario.start(stage=int(sys.argv[1]) if len(sys.argv) > 1 else 20)
s.m.set_memory_block(s.sym('game_over'), bytes([1]))       # the last stage won
for _ in range(60):
    s.tap('SPACE')
    s.run_frames(20)
    if s.peek(0xC000, 0x7D0) == scr[:0x7D0]:
        break
for _ in range(40):
    if s.peek(0xC000, 0x7D0) == scr[:0x7D0]:
        break
    s.run_frames(25)
shown = s.peek(0xC000, 0x7D0) == scr[:0x7D0]
s.run_frames(150)
stays = s.peek(0xC000, 0x7D0) == scr[:0x7D0]
s.screenshot("build/ending_check.png")
s.tap('SPACE')
s.run_frames(400)
back = s.peek(0x8000, 64) == title[:64]
print("ending on screen:", shown, " still there:", stays, " SPACE, back to the title:", back)
sys.exit(0 if shown and stays and back else 1)
