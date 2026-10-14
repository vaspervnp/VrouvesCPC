#!/usr/bin/env python3
"""Drive Caprice32 for testing: launch a .sna/.dsk with a private config,
send keys to *our* window only (found by PID) and collect screenshots.

usage: tools/emu.py FILE "script" [outdir]
script: space separated actions
   w<sec>      wait (float seconds)
   s           screenshot (F3)
   k<key>      tap an xdotool key (e.g. kRight, kspace, k1, kn)
   h<key>:<s>  hold a key for s seconds
   t<text>     autocmd-free typing of plain text (letters, digits)
"""
import glob
import os
import shutil
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
CFG = HOME + "/snap/caprice32/4/vrouves/cap32.cfg"
SHOTS = HOME + "/snap/caprice32/4/vrouves/shots"


def main():
    f = os.path.abspath(sys.argv[1])
    script = sys.argv[2].split()
    out = sys.argv[3] if len(sys.argv) > 3 else "build/shots"
    os.makedirs(out, exist_ok=True)
    for old in glob.glob(SHOTS + "/*.png"):
        os.remove(old)
    extra = os.environ.get("EMU_OPTS", "")
    autocmd = os.environ.get("EMU_AUTOCMD", "")
    acmd = ("-a '%s'" % autocmd) if autocmd else ""
    proc = subprocess.Popen(
        ["snap", "run", "--shell", "caprice32.launcher", "-c",
         "exec $SNAP/usr/bin/cap32 --cfg_file=%s -O system.model=%s %s %s '%s'"
         % (CFG, os.environ.get("MODEL", "2"), extra, acmd, f)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    win = None
    for _ in range(100):
        time.sleep(0.2)
        try:
            pids = subprocess.check_output(["pgrep", "-f", "cap32 --cfg_file=%s" % CFG]).split()
        except subprocess.CalledProcessError:
            continue
        for pid in pids:
            r = subprocess.run(["xdotool", "search", "--pid", pid.decode()], capture_output=True, text=True)
            if r.stdout.strip():
                win = r.stdout.split()[-1]
                break
        if win:
            break
    if not win:
        print("no window")
        proc.kill()
        return
    n = 0
    try:
        for act in script:
            c, arg = act[0], act[1:]
            if c == 'w':
                time.sleep(float(arg))
            elif c == 's':
                subprocess.run(["xdotool", "key", "--window", win, "F3"])
                time.sleep(0.6)
            elif c == 'k':
                subprocess.run(["xdotool", "keydown", "--window", win, arg])
                time.sleep(0.08)
                subprocess.run(["xdotool", "keyup", "--window", win, arg])
                time.sleep(0.08)
            elif c == 'h':
                key, sec = arg.split(':')
                subprocess.run(["xdotool", "keydown", "--window", win, key])
                time.sleep(float(sec))
                subprocess.run(["xdotool", "keyup", "--window", win, key])
            elif c == 't':
                for ch in arg:
                    subprocess.run(["xdotool", "key", "--window", win, ch])
                    time.sleep(0.1)
    finally:
        time.sleep(0.5)
        subprocess.run(["pkill", "-f", "cap32 --cfg_file=%s" % CFG])
        proc.wait()
    for p in sorted(glob.glob(SHOTS + "/*.png")):
        n += 1
        dst = os.path.join(out, "%02d.png" % n)
        shutil.move(p, dst)
        print(dst)


if __name__ == "__main__":
    main()
