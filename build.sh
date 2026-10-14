#!/bin/bash
# Build LET'S GO FOR VROUVES: assets -> rasm -> build/vrouves.dsk (+ .sna)
set -e
cd "$(dirname "$0")"
mkdir -p build
python3 tools/gen_assets.py
cd src
rasm main.asm -o ../build/vrouves -s -v2 ${RASMFLAGS} 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -Ei "error|warning|code\+data" || true
[ -f VROUVES.BIN ] || { echo "assembly failed"; exit 1; }
mv VROUVES.BIN ../build/VROUVES.BIN
cd ..
rm -f build/vrouves.dsk
iDSK build/vrouves.dsk -n >/dev/null
iDSK build/vrouves.dsk -i build/VROUVES.BIN -t 1 -c 0040 -e 0040 >/dev/null
iDSK build/vrouves.dsk -l | grep -i vrouves
