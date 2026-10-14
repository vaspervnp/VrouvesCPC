# LET'S GO FOR VROUVES / ΠΑΜΕ ΓΙΑ ΒΡΟΥΒΕΣ

A top-down tower defence game for the **Amstrad CPC 64K** (Mode 0, 160×200, 16 colours),
written in Z80 assembly.

Armed with EU Directive 8647/2026, Frankenstein & Moreau CO. send bio-drones, compliance
squads and weed-destroying tanks to wipe out the wild, "copyrighted" *vrouves* of Crete.
In Zoniana, the villagers have to protect the Kafenio and its sacks of bitter greens.
The rebel corporate drone **Psssst** has defected to their side.

![Screenshots from Caprice32](docs/screenshots.png)

## Running

```bash
./build.sh
```

This writes `build/vrouves.dsk` (and `build/vrouves.sna`, a snapshot for quick loading; the
game still reads its title screen and stages from the disk, so keep the disk inserted).
Insert the disk in any CPC emulator or a real 464/664/6128 with a disc drive and type:

```
RUN"VROUVES
```

## Controls

| Key | Action |
| --- | --- |
| Cursor keys / Q A O P / joystick | Move the build cursor |
| 1 – 6 | Choose a defender |
| SPACE / RETURN / ENTER / COPY / FIRE | Build on the cursor tile |
| S / DEL | Sell the defender under the cursor (half price back) |
| N | Call the next wave now (half the seconds left on the countdown are paid as a bonus) |
| H | Pause / continue (ESC while paused quits to the title) |
| L | Switch English / Greek at any time |
| M | Music on / off |

On the title screen, → (or joystick right) flips between the story, defenders and invaders pages.

## Defenders

| # | Defender | Cost | From stage | Notes |
| --- | --- | --- | --- | --- |
| 1 | Cretan | 35 | 1 | Hunting rifle, hits drones and walkers |
| 4 | Psssst | 80 | 1 | The defected drone. Laser that also strips armour. Hovers, so it can sit on walls, trees and other blocked tiles |
| 2 | Yiayia | 50 | 2 | Staff of chastisement and a pot of bitter leaves: slows everything near her, heavy close bash |
| 3 | Bride | 70 | 3 | Rapid pistol, 1 in 4 shots is a triple-damage critical |
| 6 | Baker | 60 | 4 | Hurls dakos (barley rusks) with splash damage |
| 5 | Cauldron | 110 | 5 | Toxic "unlicensed lipids and ascorbic acids": area damage that ignores armour, slows walkers |

The village joins the fight bit by bit: the Kafenio is held by the Cretan and Psssst, and every
following stage brings one more defender, announced when the stage begins.

## Invaders

* **Bio-drones** – fast and fragile; they fly a shortcut straight over the walls. Yiayia and the cauldron cannot reach them.
* **F&M compliance guards** – armoured walkers with weed-whackers and herbicide.
* **Weed destroyers** – treaded tanks with lots of health; they dent cauldrons next to the road, putting them out of action for a few seconds.

## Stages

1. **The Kafenio** – the road winds down from the hills to the village café, its porch stacked
   with sacks of vrouves.
2. **The village church** – the greens are hidden in the church courtyard, with the priest and
   the candle stand. The road is shorter and every wave a little bigger.
3. **The town hall** – on the plaza under the old plane tree, by the fountain and the mayor;
   the Greek and the EU flag fly over the portico. The invaders here are tougher: they come
   with the health they would have two waves later.
4. **The bakery** – in the yard of the village bakery by its wood-fired oven, among the
   woodpile and the racks of drying dakos. The road crosses the map in three close lanes.
5. **The school** – in the schoolyard with its basketball court, the flag and the teacher.
   The waves are the biggest of all.
6. **The village pitch** – the greens wait on the touchline by the coach and the team bench,
   below stands full of villagers. The road runs around the pitch, which is buildable grass;
   the drones fly straight across it.
7. **The cemetery church** – the last stand, at the little stone chapel among the graves and
   cypresses, with the priest and a yiayia in black by the oil lamps. The road winds between
   the graves, where nothing can be built.

Each stage has ten waves and starts with fresh funds. Every invader that reaches the building
steals greens; the sacks disappear as its HP drops. Survive all ten waves to move on to the
next stage; lose, and it is back to the title screen.

## Building

Requirements: `python3` with Pillow, [rasm](https://github.com/EdouardBERGE/rasm) and
[iDSK](https://github.com/cpcsdk/idsk).

* `tools/gen_assets.py` generates `src/gen/assets.asm`: the 3×6 font (Latin and Greek), the
  sprites (`tools/art.py`), all English/Greek text (`tools/texts.py`, byte-pair compressed),
  the music and sound effects; `src/gen/title_text.asm`, the texts only the title screen needs;
  and one file per stage, `build/STAGE1.BIN` to `STAGE7.BIN`: the map rendered to 8×12
  tiles, the cell types, the enemy paths, the sacks, the flag position, the waves and the
  stage's own texts, the defenders it has and how tough its invaders are, in a fixed layout. Preview PNGs go to `build/preview/`.
* `build.sh` puts the stage files on a fresh disk first, asks `tools/diskmap.py` where they
  landed (`src/gen/diskmap.asm`), assembles, adds the title overlay `TITLE.BIN` and
  `VROUVES.BIN`, and checks that every file is where the loader will look for it.
* `src/main.asm` is the entry point and memory map; `hw.asm` (interrupts, keyboard, AY
  sound), `gfx.asm` (double buffering, sprites, dirty rectangles, text), `game.asm`,
  `disk.asm` (the disk loader) and `title.asm` (assembled into the title overlay).
* `RASMFLAGS="-DDEBUG=9" ./build.sh` builds a debug version that starts with plenty of money
  at wave 9 and every defender; `-DSTART_STAGE=n` starts at stage n; add `-DMETER=1` to show how many 50 Hz
  frames each drawn frame took (top right).

### Headless testing

`tools/cpcsim.py` is a small headless CPC (Z80 core from the `z80` Python package, keyboard
through the PPI/AY, gate array palette, CRTC base, 300 Hz interrupts, and the disc
controller reading `build/vrouves.dsk`) that renders the shown
screen to PNG and stops on a crash (PC or SP out of range). On top of it,
`tools/scenario.py stress` builds two dozen defenders and runs a late wave,
`tools/bench.py` (on a `-DDEBUG=9` build) reports the frame rate in that fight and
`tools/profile.py` where the CPU time goes (set `CPC_SPEED=0.8` to approximate the CPC's
memory wait states), `tools/costs.py <wave>` the time per game activity,
`tools/ghosts.py` checks that no sprite leftovers remain on either screen between waves,
`tools/enemycheck.py [stress]` checks at every flip that every enemy is fully drawn, and
`tools/scenario.py full` plays a whole game, all stages, with a build order per stage,
printing progress per wave — handy for balancing. The tools work on whichever stage the build
starts at.

### Testing in Caprice32

`tools/run.sh <autocmd-file>` boots the disk in the Caprice32 snap with a private config and
screenshot folder, typing the given autocmd script. `tools/script.py` composes such scripts
(`W<n>` idles, `S` takes a screenshot, `R L U D` move the cursor, `_` is space) and
`tools/place.py` produces cursor moves to build towers at given cells.

## Technical notes

* The firmware is switched off; the game owns all 64K. Memory map: code and data from `#0040`,
  the current stage just below `#4000`, screen buffers at `#4000` and `#C000`, a copy of the
  playfield background at `#8000`, line tables, sprite mask table, dirty-rectangle lists and
  entity tables up to `#BEFF`. The title screen's code and texts are an overlay that is loaded
  into the background buffer whenever the title is shown.
* With the firmware off, `disk.asm` drives the µPD765 disc controller itself: motor on,
  recalibrate, seek, and read data sector by sector (interrupts held off during each sector,
  retries on errors) straight to the destination; the music is held meanwhile. Files are
  stored without an AMSDOS header, and their tracks and sectors are fixed at build time.
* The playfield is double buffered. Every sprite drawn on a buffer leaves a rectangle in that
  buffer's list, which is restored from the background copy before the next frame is drawn there.
* Sprites use pen 0 as transparent and a 256-byte mask table, so they are stored at one byte
  per two pixels; black inside sprites uses pen 15.
* The screen is drawn at a fixed 12.5 frames per second (every fourth 50 Hz frame), with the
  game logic running two ticks per drawn frame (25 Hz), so the pace never changes however busy
  the battle gets. `FRAMES_PER_DRAW equ 2` in `src/hw.asm` draws at up to 25 fps instead:
  about 24–25 fps in waves 1–7 and 19–23 fps in the busiest late waves, where sixteen walkers
  on screen alone take most of two frames to draw. The logic then runs as many 25 Hz ticks as
  frames passed (at most two), so the pace stays the same.
* Enemies are only redrawn when they change: per screen buffer the game remembers where and
  with which sprite each enemy was last drawn; restored rectangles stamp a 16×16 cell map and
  an unchanged enemy is redrawn only if one of its cells was restored. There are no health bars.
* Per 25 Hz tick at most four towers look for a target; input handling is skipped when no key
  is down; a cauldron draws at most two clouds per throw; up to eight effects at a time. Music and effects on the AY are driven from the 50 Hz interrupt.
* Rendering: sprites step down screen lines arithmetically and use an unrolled, width-indexed
  inner loop; background restores copy rows of up to 8 bytes with unrolled `LDI` (C = 255 so
  `LDI` never touches the row counter in B, line steps patched in, wider rectangles in 8-byte
  strips), and stamping the cell map is a short page-local loop; row counters live in a shadow register;
  HUD text changes are written to the back screen only, spreading the cost over two frames.
* Enemies have their own 8×12 routine: each row is drawn by a handler for its kind (all
  opaque, middle opaque, middle opaque with empty edges, masked), opaque bytes are copied with
  `LDI`, and for every pattern of rows the game writes a list of 12 `CALL`s into the hidden tail
  of a `#4000` screen block, so nothing is decoded while drawing. Left-facing frames are
  mirrored at start-up into the hidden tails of the `#C000` screen. A guard takes about 2900 T
  states instead of 4080, a tank 2050–2300.
