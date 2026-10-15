#!/usr/bin/env python3
"""build/VROUVES.BAS: the ASCII BASIC loader that RUN"VROUVES picks before
VROUVES.BIN. It shows two Mode 0 screens, each for 10 seconds or until
SPACE / FIRE, then runs the game:
  the REVIVE8BIT screen (assets/revive8b.scr, inks from assets/revive8b.txt)
  the splash screen (build/SPLASH.SCR and build/splash_inks.txt, made by
  tools/make_splash.py from assets/vrouves.jpeg)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIVE_INKS = [0, 13, 26, 15, 25, 10, 3, 1, 11, 23, 6, 24, 20, 16, 12, 4]
SPLASH_INKS = [int(c) for c in open(os.path.join(ROOT, "build", "splash_inks.txt")).read().split()]


def inks(n, pens):
    return ["%d MODE 0:BORDER 0:" % n + ":".join("INK %d,%d" % (i, c) for i, c in enumerate(pens[:8])),
            "%d " % (n + 1) + ":".join("INK %d,%d" % (i + 8, c) for i, c in enumerate(pens[8:]))]


lines = inks(10, REVIVE_INKS) + [
    '30 LOAD"REVIVE8B.SCR",&C000',
    "40 GOSUB 100",
] + inks(50, SPLASH_INKS) + [
    '70 LOAD"SPLASH.SCR",&C000',
    "80 GOSUB 100",
    '90 RUN"VROUVES.BIN"',
    "100 T=TIME:WHILE TIME-T<3000 AND INKEY(47)=-1 AND INKEY(76)=-1:WEND",
    "110 WHILE INKEY(47)<>-1 OR INKEY(76)<>-1:WEND:RETURN",
]
data = ("\r\n".join(lines) + "\r\n").encode("ascii") + b"\x1a"
data += b"\x1a" * (-len(data) % 128)
open(os.path.join(ROOT, "build", "VROUVES.BAS"), "wb").write(data)
