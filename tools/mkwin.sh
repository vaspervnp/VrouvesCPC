#!/bin/bash
# Let's Go for Vrouves for Windows (run from WSL, after ./build.sh):
#   build/win/Vrouves.exe          one file: the launcher, with Caprice32 (the emulator),
#                                  its ROMs and the game's disk inside
#   build/win/Vrouves-win64.zip    that exe, the manuals, how to play, the licences
# The launcher (tools/windows/Launcher.cs) is compiled by the .NET Framework's csc.exe on the
# Windows side; Caprice32's Windows release is downloaded once into build/win/ (or copied
# from BuildDangerousCPC, which already has it). From BuildDangerousCPC/tools/mkwin.sh.
set -e
cd "$(dirname "$0")/.."
B=build/win
CAP_URL=https://github.com/ColinPitrat/caprice32/releases/download/latest/cap32-win64.zip
CAP_SIBLING=../BuildDangerousCPC/build/win/cap32-win64.zip
CSC=/mnt/c/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe

mkdir -p $B
if [ ! -f $B/cap32-win64.zip ]; then
    if [ -f $CAP_SIBLING ]; then cp $CAP_SIBLING $B/; else curl -sfL -o $B/cap32-win64.zip $CAP_URL; fi
fi

# The payload: Caprice32 as released, set up for the game, and the disk
rm -rf $B/payload $B/payload.zip
mkdir -p $B/payload
unzip -q $B/cap32-win64.zip -d $B/payload
mv $B/payload/cap32-win64/* $B/payload/
rmdir $B/payload/cap32-win64
rm -rf $B/payload/resources/freedesktop $B/payload/resources/Info.plist
cp build/vrouves.dsk $B/payload/vrouves.dsk
mkdir -p $B/payload/screenshots $B/payload/snap     # where F3 / Shift+F3 save
cp tools/windows/README.txt $B/payload/Vrouves.txt
python3 - $B/payload/cap32.cfg <<'EOF'
import re, sys
p = sys.argv[1]
cfg = open(p, encoding='latin-1').read()
for key, value in {
    'model': 2,                 # CPC6128: disk drive, RUN"VROUVES
    'scr_scale': 3,             # 1152x810 window
    'scr_fps': 0,               # no FPS counter over the game
    'scr_led': 0,
    'auto_pause': 1,            # pause while the window is in the background
}.items():
    cfg, n = re.subn(rf'^{key}=.*$', f'{key}={value}', cfg, flags=re.M)
    assert n == 1, key
open(p, 'w', encoding='latin-1').write(cfg)
EOF
(cd $B/payload && zip -qr ../payload.zip .)

# The icon: Psssst, from the game's own sprite (Mode 0 pixels are twice as wide as tall)
python3 - $B/icon.ico <<'EOF'
import sys
sys.path.insert(0, 'tools')
from PIL import Image
import art
rows = art.PSSSST
im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
for y, r in enumerate(rows):
    for x, ch in enumerate(r):
        if ch != '.':
            c = art.PEN_RGB[0 if ch in 'kn' else art.CH[ch]] + (255,)
            im.putpixel((x * 2, y + 2), c)
            im.putpixel((x * 2 + 1, y + 2), c)
im.resize((256, 256), Image.NEAREST).save(sys.argv[1], sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
EOF

# Compile on the Windows side (csc wants Windows paths, and local ones are safest)
WTMP=$(wslpath "$(cmd.exe /c 'echo %TEMP%' 2>/dev/null | tr -d '\r')")/vrouves-launcher
rm -rf "$WTMP"
mkdir -p "$WTMP"
cp tools/windows/Launcher.cs $B/payload.zip $B/icon.ico "$WTMP/"
(cd "$WTMP" && "$CSC" /nologo /optimize /target:winexe /out:Vrouves.exe \
    /win32icon:icon.ico /resource:payload.zip,payload.zip \
    /r:System.IO.Compression.dll /r:System.IO.Compression.FileSystem.dll \
    /r:System.Windows.Forms.dll Launcher.cs | tr -d '\r')
cp "$WTMP/Vrouves.exe" $B/Vrouves.exe
rm -rf "$WTMP"

# The release zip
rm -rf $B/release $B/Vrouves-win64.zip
mkdir -p $B/release/Vrouves/licences
cp $B/Vrouves.exe tools/windows/README.txt docs/MANUAL.pdf docs/MANUAL_GR.pdf $B/release/Vrouves/
cp $B/payload/COPYING.txt $B/release/Vrouves/licences/Caprice32-GPL.txt
cp $B/payload/licenses/* $B/release/Vrouves/licences/
(cd $B/release && zip -qr ../Vrouves-win64.zip Vrouves)
ls -l $B/Vrouves.exe $B/Vrouves-win64.zip
