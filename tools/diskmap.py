#!/usr/bin/env python3
"""Where files sit on an AMSDOS data-format disk image (.dsk), for the game's
own disk loader (the firmware is switched off while the game runs).

    tools/diskmap.py <dsk> asm <out.asm> NAME...   equates for files on the disk,
                                                   plus NEXT_* for the next free block
    tools/diskmap.py <dsk> seq <track>|all         put that track's (or every track's)
                                                   sectors in the order of their ids
                                                   (no interleave)
    tools/diskmap.py <dsk> ext                     to an EXTENDED image (see to_extended)
    tools/diskmap.py <dsk> verify <diskmap.asm> NAME=localfile ...
                                                   files are where the equates say
                                                   (TITLE at NEXT, the next ones
                                                   right after it) and hold the data

A file must occupy consecutive blocks; block b of the data format starts at
logical sector 2b: track 2b // 9, sector #C1 + 2b % 9.
"""
import sys

SECTORS = 9
SECTOR_SIZE = 512


class Dsk:
    def __init__(self, path):
        d = open(path, 'rb').read()
        self.sec = {}           # (track, sector id) -> bytes
        if d.startswith(b"MV - CPC"):
            ntr, tsize = d[0x30], d[0x32] | d[0x33] << 8
            sizes = [tsize] * ntr
        elif d.startswith(b"EXTENDED"):
            ntr = d[0x30]
            sizes = [d[0x34 + t] * 256 for t in range(ntr)]
        else:
            raise SystemExit("not a dsk image: " + path)
        off = 0x100
        for t in range(ntr):
            if sizes[t] == 0:
                continue
            ti = d[off:off + sizes[t]]
            n = ti[0x15]
            p = 0x100
            for k in range(n):
                c, h, r, sz = ti[0x18 + k * 8:0x18 + k * 8 + 4]
                ln = 128 << sz
                self.sec[(c, r)] = ti[p:p + ln]
                p += ln
            off += sizes[t]

    @staticmethod
    def block_pos(b):
        s = 2 * b
        return s // SECTORS, 0xC1 + s % SECTORS

    def read_block(self, b):
        out = b""
        for k in range(2):
            s = 2 * b + k
            out += self.sec[(s // SECTORS, 0xC1 + s % SECTORS)]
        return out

    def directory(self):
        raw = b"".join(self.sec[(0, 0xC1 + i)] for i in range(4))
        files = {}
        for i in range(0, len(raw), 32):
            e = raw[i:i + 32]
            if e[0] == 0xE5:
                continue
            name = (e[1:9].decode('ascii', 'replace').strip() + "." +
                    bytes(x & 0x7F for x in e[9:12]).decode('ascii').strip())
            ext = e[12]
            blocks = [x for x in e[16:32] if x]
            f = files.setdefault(name, {})
            f[ext] = (e[15], blocks)
        out = {}
        for name, exts in files.items():
            blocks = []
            for k in sorted(exts):
                blocks += exts[k][1]
            out[name] = blocks
        return out


def seq_track(path, track):
    d = bytearray(open(path, 'rb').read())
    assert d.startswith(b"MV - CPC"), "a standard dsk image"
    tsize = d[0x32] | d[0x33] << 8
    off = 0x100 + track * tsize
    n = d[off + 0x15]
    infos = [bytes(d[off + 0x18 + k * 8:off + 0x20 + k * 8]) for k in range(n)]
    size = 128 << d[off + 0x14]
    data = [bytes(d[off + 0x100 + k * size:off + 0x100 + (k + 1) * size]) for k in range(n)]
    order = sorted(range(n), key=lambda k: infos[k][2])
    for j, k in enumerate(order):
        d[off + 0x18 + j * 8:off + 0x20 + j * 8] = infos[k]
        d[off + 0x100 + j * size:off + 0x100 + (j + 1) * size] = data[k]
    open(path, 'wb').write(d)


def to_extended(path):
    """Retro Virtual Machine (and WinAPE), writing a sector to a standard
    dsk, save it back as an EXTENDED one holding only the track written: the
    rest of the disk is lost.  An EXTENDED image is updated as it is."""
    d = open(path, 'rb').read()
    if d.startswith(b"EXTENDED"):
        return
    assert d.startswith(b"MV - CPC"), "a standard dsk image"
    ntr, tsize = d[0x30], d[0x32] | d[0x33] << 8
    hdr = bytearray(256)
    hdr[0:34] = b"EXTENDED CPC DSK File\r\nDisk-Info\r\n"
    hdr[0x22:0x30] = b"diskmap.py    "
    hdr[0x30], hdr[0x31] = ntr, d[0x31]
    for t in range(ntr):
        hdr[0x34 + t] = tsize >> 8
    out = bytearray(hdr)
    for t in range(ntr):
        ti = bytearray(d[0x100 + t * tsize:0x100 + (t + 1) * tsize])
        assert ti.startswith(b"Track-Info"), t
        for k in range(ti[0x15]):            # each sector's actual length
            e = 0x18 + k * 8
            ti[e + 6:e + 8] = (128 << ti[e + 3]).to_bytes(2, "little")
        out += ti
    open(path, 'wb').write(out)


def main():
    dsk = Dsk(sys.argv[1])
    files = dsk.directory()
    used = {b for bl in files.values() for b in bl}
    mode = sys.argv[2]
    if mode == "asm":
        lines = ["; generated by tools/diskmap.py - do not edit"]
        for name in sys.argv[4:]:
            bl = files[name]
            assert bl == list(range(bl[0], bl[0] + len(bl))), (name, bl)
            t, s = dsk.block_pos(bl[0])
            key = name.split('.')[0].upper()
            lines.append("DISK_%s_TRACK equ %d" % (key, t))
            lines.append("DISK_%s_SECTOR equ #%02X" % (key, s))
        stages = [n for n in sys.argv[4:] if n.startswith("STAGE")]
        lines.append("disk_stages:")
        for name in stages:
            key = name.split('.')[0].upper()
            lines.append("        db DISK_%s_TRACK,DISK_%s_SECTOR,STAGE_SECTORS" % (key, key))
            lines.append("        dw STAGE_AREA")
        nxt = max(used | {1}) + 1
        t, s = dsk.block_pos(nxt)
        lines.append("DISK_NEXT_BLOCK equ %d" % nxt)
        lines.append("DISK_NEXT_TRACK equ %d" % t)
        lines.append("DISK_NEXT_SECTOR equ #%02X" % s)
        open(sys.argv[3], "w").write("\n".join(lines) + "\n")
    elif mode == "verify":
        eq = {}
        for line in open(sys.argv[3]):
            p = line.split()
            if len(p) == 3 and p[1] == "equ":
                eq[p[0]] = int(p[2].replace('#', '0x'), 0)
        bad = 0
        after = None        # files with no equates of their own: the first at NEXT,
        for spec in sys.argv[4:]:   # each following one right after the one before
            name, local = spec.split("=")
            key = name.split('.')[0].upper()
            bl = files.get(name)
            if "DISK_%s_TRACK" % key in eq:
                want = (eq["DISK_%s_TRACK" % key], eq["DISK_%s_SECTOR" % key])
            elif after is None:
                want = (eq["DISK_NEXT_TRACK"], eq["DISK_NEXT_SECTOR"])
            else:
                want = dsk.block_pos(after)
            if "DISK_%s_TRACK" % key not in eq and bl:
                after = bl[-1] + 1
            data = open(local, "rb").read()
            got = b"".join(dsk.read_block(b) for b in bl) if bl else b""
            if (not bl or bl != list(range(bl[0], bl[0] + len(bl))) or
                    dsk.block_pos(bl[0]) != want or not got.startswith(data)):
                print("diskmap: %s is not where the loader expects it (blocks %s)" % (name, bl))
                bad = 1
        sys.exit(bad)
    elif mode == "seq":
        # The high score sector is written by the game.  On a track whose
        # sectors are interleaved, an emulator that writes by a sector's
        # place on the track rather than by its id, or that runs on into the
        # next sector, would hit the directory (C1-C4 on track 0); in id
        # order the place is the id, and the sectors after it are the file's
        # own (HISCORE.BIN takes the rest of the track).
        tracks = range(open(sys.argv[1], "rb").read()[0x30]) if sys.argv[3] == "all" else [int(sys.argv[3])]
        for t in tracks:
            seq_track(sys.argv[1], t)
    elif mode == "ext":
        to_extended(sys.argv[1])
    elif mode == "dump":
        for name, bl in files.items():
            print(name, bl, dsk.block_pos(bl[0]) if bl else None)


if __name__ == "__main__":
    main()
