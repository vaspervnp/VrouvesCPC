#!/usr/bin/env python3
"""Minimal headless Amstrad CPC for testing the game: Z80 core (python 'z80'
package), 300 Hz interrupts with VSYNC on PPI port B, keyboard matrix through
the PPI/AY, gate array palette, CRTC screen base.  Renders the shown screen
to PNG and checks for crashes (PC or SP out of range).

usage as a library:
    sim = CPC("build/VROUVES.BIN", "build/vrouves.sym")
    sim.run_frames(100)
    sim.tap("SPACE"); sim.run_frames(20)
    sim.screenshot("x.png")
"""
import os
import sys

import z80
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 4 MHz * 19.968 ms; CPC_SPEED < 1 approximates the CPC's memory wait states
T_FRAME = int(79872 * float(os.environ.get("CPC_SPEED", "1")))
SLICE = T_FRAME // 6 // 64 * 64

KEYS = {
    'UP': 0, 'RIGHT': 1, 'DOWN': 2, 'ENTER': 6, 'LEFT': 8, 'COPY': 9, 'RETURN': 18,
    'P': 27, 'O': 34, 'L': 36, 'M': 38, 'H': 44, 'N': 46, 'SPACE': 47,
    '6': 48, '5': 49, '4': 56, '3': 57, 'S': 60, 'X': 63, '1': 64, '2': 65, 'ESC': 66,
    'Q': 67, 'A': 69, 'DEL': 79, 'J_UP': 72, 'J_DOWN': 73, 'J_LEFT': 74, 'J_RIGHT': 75,
    'J_FIRE1': 77,
}

FW_RGB = []
for n in range(27):
    g, r, b = n // 9, (n // 3) % 3, n % 3
    lv = (0, 128, 255)
    FW_RGB.append((lv[r], lv[g], lv[b]))
HW_TO_FW = {0x54: 0, 0x44: 1, 0x55: 2, 0x5C: 3, 0x58: 4, 0x5D: 5, 0x4C: 6, 0x45: 7, 0x4D: 8,
            0x56: 9, 0x46: 10, 0x57: 11, 0x5E: 12, 0x40: 13, 0x5F: 14, 0x4E: 15, 0x47: 16,
            0x4F: 17, 0x52: 18, 0x42: 19, 0x53: 20, 0x5A: 21, 0x59: 22, 0x5B: 23, 0x4A: 24,
            0x43: 25, 0x4B: 26}


class Crash(Exception):
    pass


class FDC:
    """uPD765 as the CPC sees it (non-DMA, drive 0): just the commands the
    game's loader uses, with no timing: specify, recalibrate, seek, sense
    interrupt status and read data from a .dsk image."""
    LEN = {0x03: 3, 0x07: 2, 0x08: 1, 0x0F: 3, 0x06: 9}

    def __init__(self, dskfile):
        from diskmap import Dsk
        self.dsk = Dsk(dskfile) if dskfile and os.path.exists(dskfile) else None
        self.cmd = []
        self.data = b""
        self.res = []
        self.pcn = 0
        self.seek_end = False
        self.motor = 0
        self.reads = 0

    def msr(self):
        if self.data:
            return 0xF0
        if self.res:
            return 0xD0
        return 0x90 if self.cmd else 0x80

    def read(self):
        if self.data:
            b, self.data = self.data[0], self.data[1:]
            return b
        if self.res:
            return self.res.pop(0)
        return 0xFF

    def write(self, v):
        if self.data or self.res:
            return
        self.cmd.append(v)
        op = self.cmd[0] & 0x1F
        if len(self.cmd) < self.LEN.get(op, 1):
            return
        c, self.cmd = self.cmd, []
        if op == 0x07:
            self.pcn, self.seek_end = 0, True
        elif op == 0x0F:
            self.pcn, self.seek_end = c[2], True
        elif op == 0x08:
            self.res = [0x20, self.pcn] if self.seek_end else [0x80]
            self.seek_end = False
        elif op == 0x06:
            C, H, R, N = c[2:6]
            sec = self.dsk.sec.get((self.pcn, R)) if self.dsk and self.motor else None
            if sec is None or C != self.pcn:
                self.res = [0x40, 0x04, 0, C, H, R, N]
            else:
                self.data = bytes(sec)
                self.reads += 1
                self.res = [0x40, 0x80, 0, C, H, R, N]   # end of cylinder: no TC on the CPC
        elif op != 0x03:
            self.res = [0x80]


class CPC:
    def __init__(self, binfile, symfile=None, load=0x40, dskfile="build/vrouves.dsk"):
        self.m = z80.Z80Machine()
        data = open(binfile, 'rb').read()
        self.m.set_memory_block(load, data)
        self.code_end = load + len(data)
        self.m.pc = load
        self.m.sp = 0xC000
        self.syms = {}
        if symfile:
            for line in open(symfile):
                p = line.split()
                if len(p) >= 2 and p[1].startswith('#'):
                    self.syms[p[0].upper()] = int(p[1][1:], 16)
        self.keys = [0xFF] * 10
        self.ppi_c = 0
        self.psg_reg = 0
        self.psg_latch = 0
        self.psg = [0] * 16
        self.ink = [0x54] * 17
        self.pen_sel = 0
        self.crtc_reg = 0
        self.crtc = [0] * 18
        self.crtc[12] = 0x30
        self.vsync = False
        self.frame = 0
        self.held = {}
        self.m.set_input_callback(self._in)
        self.m.set_output_callback(self._out)
        self.ldir_watch = []
        self.fdc = FDC(dskfile)
        self.overlay = (0x8000, self.syms.get('TITLE_END', 0x8000))

    # ---------------------------------------------------------------- I/O
    def _in(self, port):
        hi = port >> 8
        if hi == 0xFB:
            return self.fdc.msr() if port & 1 == 0 else self.fdc.read()
        if hi == 0xF5:
            return 0x5E | (1 if self.vsync else 0)
        if hi == 0xF4:
            if self.psg_reg == 14:
                return self.keys[self.ppi_c & 15] if (self.ppi_c & 15) < 10 else 0xFF
            return 0xFF
        return 0xFF

    def _out(self, port, value):
        hi = port >> 8
        if hi == 0xFB and port & 1:
            self.fdc.write(value)
        elif hi == 0xFA:
            self.fdc.motor = value & 1
        elif hi == 0x7F:
            if value & 0xC0 == 0x00:
                self.pen_sel = value & 0x1F
            elif value & 0xC0 == 0x40:
                self.ink[min(self.pen_sel, 16)] = value & 0x5F | 0x40
        elif hi == 0xBC:
            self.crtc_reg = value & 31
        elif hi == 0xBD:
            if self.crtc_reg < 18:
                self.crtc[self.crtc_reg] = value
        elif hi == 0xF4:
            self.psg_latch = value
        elif hi == 0xF6:
            self.ppi_c = value
            mode = value >> 6
            if mode == 3:
                self.psg_reg = self.psg_latch & 15
            elif mode == 2:
                self.psg[self.psg_reg] = self.psg_latch
        elif hi == 0xF7:
            pass

    # ---------------------------------------------------------------- keys
    def set_key(self, name, down):
        code = KEYS[name]
        line, bit = code >> 3, code & 7
        if down:
            self.keys[line] &= ~(1 << bit) & 0xFF
        else:
            self.keys[line] |= 1 << bit

    def tap(self, name, frames=3, gap=4):
        self.set_key(name, True)
        self.run_frames(frames)
        self.set_key(name, False)
        self.run_frames(gap)

    # ---------------------------------------------------------------- run
    def _check(self):
        pc, sp = self.m.pc, self.m.sp
        # code also runs from the hidden tails of the screen blocks (#x7D0-#x7FF)
        if not (0x38 <= pc < self.code_end or
                self.overlay[0] <= pc < self.overlay[1] or
                (0x4000 <= pc < 0x8000 or pc >= 0xC000) and pc & 0x7FF >= 0x7D0):
            raise Crash("PC out of code: #%04X (SP #%04X) frame %d" % (pc, sp, self.frame))
        if not (0xBE00 <= sp <= 0xC000):
            raise Crash("SP out of range: #%04X (PC #%04X) frame %d" % (sp, pc, self.frame))

    def run_frames(self, n):
        for _ in range(n):
            for k in range(6):
                self.vsync = (k == 0)
                pending = True
                left = SLICE
                while left > 0:
                    if pending and self.m.on_handle_active_int():
                        pending = False
                    step = 256 if pending else left
                    step = min(step, left)
                    self.m.ticks_to_stop = step
                    self.m.run()
                    left -= step
                    self._check()
            self.frame += 1

    def peek(self, addr, n=1):
        mem = self.m.memory
        if n == 1:
            return mem[addr & 0xFFFF]
        return bytes(mem[(addr + i) & 0xFFFF] for i in range(n))

    def sym(self, name):
        return self.syms[name.upper()]

    def word(self, name):
        a = self.sym(name)
        return self.peek(a) | self.peek(a + 1) << 8

    def byte(self, name):
        return self.peek(self.sym(name))

    # ---------------------------------------------------------------- video
    def screenshot(self, path, scale=3):
        base = (self.crtc[12] & 0x30) << 10
        pal = []
        for i in range(16):
            pal.append(FW_RGB[HW_TO_FW.get(self.ink[i], 0)])
        im = Image.new('RGB', (160, 200))
        px = im.load()
        mem = self.m.memory
        for y in range(200):
            a = base + (y >> 3) * 80 + (y & 7) * 0x800
            for xb in range(80):
                b = mem[(a + xb) & 0xFFFF]
                p0 = (b >> 7 & 1) | (b >> 3 & 1) << 1 | (b >> 5 & 1) << 2 | (b >> 1 & 1) << 3
                p1 = (b >> 6 & 1) | (b >> 2 & 1) << 1 | (b >> 4 & 1) << 2 | (b & 1) << 3
                px[xb * 2, y] = pal[p0]
                px[xb * 2 + 1, y] = pal[p1]
        im = im.resize((160 * 2 * scale, 200 * scale), Image.NEAREST)
        im.save(path)


if __name__ == "__main__":
    sim = CPC(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sim.run_frames(int(sys.argv[3]) if len(sys.argv) > 3 else 100)
    sim.screenshot("build/sim.png")
    print("ok, frame", sim.frame)
