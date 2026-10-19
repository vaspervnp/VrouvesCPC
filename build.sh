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
rm -f VROUVES.BIN TITLE.BIN ENDCODE.BIN
rasm main.asm -o ../build/vrouves -s -sq -v2 ${RASMFLAGS} 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -Ei "error|warning|code\+data|overlay" || true
[ -f VROUVES.BIN ] && [ -f TITLE.BIN ] && [ -f ENDCODE.BIN ] || { echo "assembly failed"; exit 1; }
mv VROUVES.BIN TITLE.BIN ENDCODE.BIN ../build/
cd ..
# the ending screen, with its inks and code in the screen's hidden tails, right after TITLE.BIN
python3 tools/png_to_scr.py assets/ending_sceneFinal.png build/ENDING.SCR 0x7D0 build/ENDCODE.BIN@0xFD0 >/dev/null
iDSK build/vrouves.dsk -i build/TITLE.BIN -t 0 >/dev/null 2>&1
iDSK build/vrouves.dsk -i build/ENDING.SCR -t 0 >/dev/null 2>&1
iDSK build/vrouves.dsk -i build/VROUVES.BIN -t 1 -c 0040 -e 0040 >/dev/null 2>&1
# RUN"VROUVES finds the BASIC loader first: the REVIVE8BIT and splash
# screens, then VROUVES.BIN
python3 tools/make_splash.py >/dev/null
python3 tools/make_boot.py
cp assets/revive8b.scr build/REVIVE8B.SCR
iDSK build/vrouves.dsk -i build/REVIVE8B.SCR -t 1 -c C000 -e 0 >/dev/null 2>&1
iDSK build/vrouves.dsk -i build/SPLASH.SCR -t 1 -c C000 -e 0 >/dev/null 2>&1
iDSK build/vrouves.dsk -i build/VROUVES.BAS -t 0 >/dev/null 2>&1
python3 tools/diskmap.py build/vrouves.dsk verify src/gen/diskmap.asm \
    $(for f in $STAGES; do echo "$f=build/$f"; done) TITLE.BIN=build/TITLE.BIN ENDING.SCR=build/ENDING.SCR
iDSK build/vrouves.dsk -l 2>/dev/null | grep -Ei "\.(BIN|BAS|SCR)"
