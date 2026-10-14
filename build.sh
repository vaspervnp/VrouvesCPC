#!/bin/bash
# Build LET'S GO FOR VROUVES: assets -> rasm -> build/vrouves.dsk (+ .sna)
# The disk holds the stage files and the title overlay, read by the game's
# own loader from fixed positions, and the main program VROUVES.BIN.
set -e
cd "$(dirname "$0")"
mkdir -p build
python3 tools/gen_assets.py
STAGES=$(cd build && ls STAGE*.BIN | sort -V)
rm -f build/vrouves.dsk
iDSK build/vrouves.dsk -n >/dev/null 2>&1
for f in $STAGES; do
    iDSK build/vrouves.dsk -i build/$f -t 0 >/dev/null 2>&1
done
python3 tools/diskmap.py build/vrouves.dsk asm src/gen/diskmap.asm $STAGES
cd src
rm -f VROUVES.BIN TITLE.BIN
rasm main.asm -o ../build/vrouves -s -sq -v2 ${RASMFLAGS} 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -Ei "error|warning|code\+data|overlay" || true
[ -f VROUVES.BIN ] && [ -f TITLE.BIN ] || { echo "assembly failed"; exit 1; }
mv VROUVES.BIN TITLE.BIN ../build/
cd ..
iDSK build/vrouves.dsk -i build/TITLE.BIN -t 0 >/dev/null 2>&1
iDSK build/vrouves.dsk -i build/VROUVES.BIN -t 1 -c 0040 -e 0040 >/dev/null 2>&1
python3 tools/diskmap.py build/vrouves.dsk verify src/gen/diskmap.asm \
    $(for f in $STAGES; do echo "$f=build/$f"; done) TITLE.BIN=build/TITLE.BIN
iDSK build/vrouves.dsk -l 2>/dev/null | grep -i "\.BIN"
