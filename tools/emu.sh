#!/bin/bash
# Run a snapshot/disk in Caprice32 with an autocmd script and collect screenshots.
# usage: tools/emu.sh <file.sna|file.dsk> "<autocmd>" [outdir]
# In the autocmd: x = idle keypress (ignored by the game), \(CAP32_SCRNSHOT) = screenshot,
# \(CAP32_EXIT) = quit, \(CPC_CUR_UP) etc = keys.
FILE=$(readlink -f "$1")
CMD="$2"
OUT=${3:-build/shots}
mkdir -p "$OUT"
SHOTS=$HOME/snap/caprice32/4/screenshots
before=$(ls "$SHOTS" | wc -l)
timeout ${EMU_TIMEOUT:-120} snap run --shell caprice32.launcher -c "\$SNAP/usr/bin/cap32 --cfg_file=\$SNAP_USER_DATA/etc/cap32.cfg -O system.model=${MODEL:-2} -a '$CMD' '$FILE'" >/dev/null 2>&1
ls -t "$SHOTS" | head -n $(( $(ls "$SHOTS" | wc -l) - before )) | tac | while read f; do mv "$SHOTS/$f" "$OUT/"; echo "$OUT/$f"; done
