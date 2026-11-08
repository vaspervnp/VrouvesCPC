#!/usr/bin/env python3
"""Put the Lyra area (LYRA.BIN, assembled with the game) into the stage files
that have the Lyra player.  build/extra_stages, written by gen_assets.py,
says where in a stage file it goes and which files have it.

    tools/put_extra.py <LYRA.BIN> <stage dir> <extra_stages>
"""
import os
import sys

lyra, stage_dir, listing = sys.argv[1:4]
off, *names = open(listing).read().split()
off = int(off)
data = open(lyra, "rb").read()
for name in names:
    path = os.path.join(stage_dir, name)
    d = bytearray(open(path, "rb").read())
    assert len(d) >= off + len(data), name
    d[off:off + len(data)] = data
    open(path, "wb").write(d)
