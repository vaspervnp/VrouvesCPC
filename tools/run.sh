#!/bin/bash
# Boot build/vrouves.dsk (or with MEDIA=cdt build/vrouves.cdt) in Caprice32 (private
# config) and type an autocmd script.
#   tools/run.sh <autocmd-file> [outdir]
# In the script: x = idle key (ignored by the game) used as delay,
# \(CAP32_SCRNSHOT) = screenshot, \(CAP32_EXIT) = quit, \(CPC_CUR_RIGHT) etc = keys.
set -e
cd "$(dirname "$0")/.."
U=~/snap/caprice32/current/vrouves
OUT=${2:-build/shots}
mkdir -p "$OUT" "$U/shots"
rm -f "$U"/shots/*.png
MEDIA=${MEDIA:-dsk}
cp build/vrouves.$MEDIA "$U/vrouves.$MEDIA"
cp "$1" "$U/autocmd.txt"
cat > "$U/run.sh" <<INNER
#!/bin/bash
exec timeout ${CAP32_TIMEOUT:-180} \$SNAP/usr/bin/cap32 --cfg_file=\$SNAP_USER_DATA/vrouves/cap32.cfg -O system.limit_speed=${LIMIT:-0} -O system.model=${MODEL:-2} ${CAPOPTS} \\
    -a "\$(cat \$SNAP_USER_DATA/vrouves/autocmd.txt)" "\$SNAP_USER_DATA/vrouves/vrouves.$MEDIA"
INNER
chmod +x "$U/run.sh"
snap run --shell caprice32.launcher -c "\$SNAP_USER_DATA/vrouves/run.sh" >/dev/null 2>&1 || true
n=0
for f in $(ls "$U"/shots/*.png 2>/dev/null | sort); do
  n=$((n+1)); mv "$f" "$OUT/$(printf %02d $n).png"; echo "$OUT/$(printf %02d $n).png"
done
