#!/usr/bin/env python3
"""The score and the high score table on the headless CPC:
each kind of points, a won stage, a lost game, the name entered, the
sector written to the disk and read back, the table page.

    tools/scorecheck.py             (after ./build.sh)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scenario  # noqa: E402

ok = True


def check(what, got, want):
    global ok
    good = got == want
    ok &= good
    print("%-44s %s (want %s) %s" % (what, got, want, "OK" if good else "FAILED"))


def parts():
    s = scenario.start()
    p = scenario.Player(s)
    check("score at the start", s.word('score'), 0)
    c, r = 3, 2
    p.build(1, c, r)
    s.run_frames(5)
    check("a Cretan built: its damage", s.word('score'), 6)
    p.goto(c, r)
    s.tap('S')
    s.run_frames(5)
    check("and sold again", s.word('score'), 0)
    p.build(1, c, r)
    s.run_frames(5)
    left = s.byte('cd_sec')
    s.tap('N')
    s.run_frames(5)
    check("N with %d seconds left" % left, s.word('score'), 6 + left)
    before = s.word('score')
    for _ in range(3000):           # wave 1, drones only: 4 points each
        s.run_frames(1)
        if s.byte('wave_state') == 0:
            break
    got = s.word('score') - before
    print("wave 1: %d points from the invaders stopped" % got)
    ok_kill = got > 0 and got % 4 == 0
    check("points from kills, in fours (drones)", ok_kill, True)
    return s


def won_stage():
    s = scenario.start()
    scenario.play_stage(s, scenario.PLANS[0], verbose=False)
    funds = s.word('funds')
    sc = s.word('score')
    print("stage 1 won: score %d, funds left %d" % (sc, funds))
    return s


def lose(s):
    """the stage lost: no defenders, every wave called at once"""
    while not s.byte('game_over'):
        s.tap('N')
        s.run_frames(100)


def lives():
    """medium: 3 lives.  A lost stage is played again, the score back to
    what it was when the stage began; the fourth loss ends the game"""
    s = scenario.start()
    check("lives on medium", s.byte('rt_lives'), 3)
    scenario.play_stage(s, scenario.PLANS[0], verbose=False)
    scenario.next_stage(s)
    begun = s.word('score')
    for left in (2, 1, 0):
        lose(s)
        for _ in range(100):        # the banner, then the stage again
            s.tap('SPACE')
            s.run_frames(20)
            if not s.byte('game_over'):
                break
        s.run_frames(50)
        check("lost: the stage again, lives left", (s.byte('stage'), s.byte('rt_lives')), (1, left))
        check("  the score as the stage began", s.word('score'), begun)
    lose(s)
    for _ in range(100):            # no life left: back to the title
        s.tap('SPACE')
        s.run_frames(20)
        if s.peek(0xB000, 4) == b"VRV1":
            break
    check("the fourth loss: the title", s.peek(0xB000, 4), b"VRV1")
    for n, want in ((1, 2), (2, 0), (3, 4)):
        check("lives after 'D' x%d" % n, scenario.start(difficulty=n).byte('rt_lives'), want)


def lost_game():
    """hardest: stage 1 won, stage 2 lost with no defenders: a score for the table"""
    s = scenario.start(difficulty=2)
    scenario.play_stage(s, scenario.PLANS[0], verbose=False)
    scenario.next_stage(s)
    lose(s)
    sc = s.word('score')
    print("stage 2 lost, the game ends with score %d" % sc)
    for _ in range(100):            # the banner, then the title and its table load
        s.tap('SPACE')
        s.run_frames(20)
        if s.peek(0xB000, 4) == b"VRV1":
            break
    s.run_frames(150)
    s.screenshot("build/hs_entry.png", scale=2)
    for k in ('DOWN', 'DOWN', 'SPACE', 'UP', 'SPACE', 'SPACE'):    # C, then the last one, A
        s.tap(k)
        s.run_frames(6)
    s.run_frames(150)
    s.screenshot("build/hs_table.png", scale=2)
    check("the sector written to the disk", s.fdc.writes, 1)
    want = [s.peek(0xB000 + k) for k in range(64)]
    t, sct = s.sym('DISK_HISCORE_TRACK'), s.sym('DISK_HISCORE_SECTOR')
    disk = list(s.fdc.dsk.sec[(t, sct)][:64])
    check("what is on the disk is the table", disk == want, True)
    ent = [(bytes(want[4 + k * 5:7 + k * 5]), want[7 + k * 5] | want[8 + k * 5] << 8) for k in range(8)]
    print("table:", ent)
    check("the new score in the table", any(v == sc for _, v in ent), True)
    check("the score cleared", s.word('score'), 0)
    return s


if __name__ == "__main__":
    parts()
    won_stage()
    lives()
    lost_game()
    print("score:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)
