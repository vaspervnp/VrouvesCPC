#!/usr/bin/env python3
"""The cassette image (.cdt, the TZX format) of LET'S GO FOR VROUVES.

    tools/make_cdt.py <out.cdt> fw:NAME:<file>:<load>:<entry> id:<n>:<file> ...

fw:  a file in the firmware's own format, that RUN"" loads: 2K blocks,
     each a header record and a data record (leader, sync byte, 256 byte
     segments with their CRC, trailer), at 1000 baud
id:  a block for the game's own loader (src/tape.asm): pilot, sync, then
     block id, length, data and an XOR checksum
"""
import struct
import sys

T = 3.5            # TZX timing: T-states at 3.5 MHz per microsecond


def turbo(pilot, sync1, sync2, zero, one, pilot_len, data, pause):
    return (b"\x11" + struct.pack("<HHHHHHBH", pilot, sync1, sync2, zero, one, pilot_len, 8, pause) +
            struct.pack("<I", len(data))[:3] + bytes(data))


# ------------------------------------------------------------------ the firmware's format
FW_ZERO = round(333 * T)        # 1000 baud: a 0 bit is two 333us pulses, a 1 bit two 667us ones
FW_ONE = 2 * FW_ZERO


def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc ^ 0xFFFF


def record(sync, payload, pause):
    """leader of 2048 one bits, a zero bit, the sync byte, segments + CRC, trailer"""
    out = bytearray([sync])
    for k in range(0, len(payload), 256):
        seg = payload[k:k + 256]
        seg = seg + bytes(256 - len(seg))
        out += seg + struct.pack(">H", crc16(seg))
    out += b"\xff" * 4
    return turbo(FW_ONE, FW_ZERO, FW_ZERO, FW_ZERO, FW_ONE, 4096, out, pause)


def firmware_file(name, data, load, entry):
    out = b""
    blocks = [data[k:k + 2048] for k in range(0, len(data), 2048)]
    for n, blk in enumerate(blocks):
        hdr = bytearray(64)
        hdr[0:len(name)] = name.encode("ascii")
        hdr[16] = n + 1                                     # block number
        hdr[17] = 0xFF if n == len(blocks) - 1 else 0       # last block
        hdr[18] = 2                                         # binary
        struct.pack_into("<HH", hdr, 19, len(blk), load + n * 2048)
        hdr[23] = 0xFF if n == 0 else 0                     # first block
        struct.pack_into("<HH", hdr, 24, len(data), entry)
        out += record(0x2C, bytes(hdr), 100)
        out += record(0x16, blk, 2500 if n == len(blocks) - 1 else 100)
    return out


# ------------------------------------------------------------------ the game's own format
G_PILOT, G_SYNC, G_ZERO, G_ONE = round(600 * T), round(150 * T), round(200 * T), round(400 * T)


def game_block(ident, data):
    body = bytearray([ident]) + struct.pack("<H", len(data)) + data
    x = 0
    for b in body:
        x ^= b
    body.append(x)
    return turbo(G_PILOT, G_SYNC, G_SYNC, G_ZERO, G_ONE, 1500, body, 2000)


def main():
    out = bytearray(b"ZXTape!\x1a\x01\x14")
    for spec in sys.argv[2:]:
        kind, rest = spec.split(":", 1)
        if kind == "fw":
            name, path, load, entry = rest.split(":")
            out += firmware_file(name, open(path, "rb").read(), int(load, 0), int(entry, 0))
        else:
            ident, path = rest.split(":")
            out += game_block(int(ident), bytearray(open(path, "rb").read()))
    open(sys.argv[1], "wb").write(out)
    print("%s: %d bytes" % (sys.argv[1], len(out)))


if __name__ == "__main__":
    main()
