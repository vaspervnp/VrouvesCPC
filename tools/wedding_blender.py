"""The ending scene of LET'S GO FOR VROUVES, built in Blender: the Bride's
wedding, once the last stage is won.

In front of the village church the Bride and the groom dance, the wedding
crowns on their heads and the ribbon between them held up by Psssst; the
Lyra player plays, sitting on his chair; behind them everyone is at the long
table, with plates of vrouves, and the cauldron of gamopilafo is on the fire.

Run inside Blender (tools/ on sys.path, for blender_toon), or in the
background:
    blender -b --python tools/wedding_blender.py -- <out.png>
It builds its own scene "VrouvesWedding" and renders it there (default:
WEDDING_OUT).  tools/make_ending.py turns the render into CPC colours.
"""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_toon import C, R, Toon  # noqa: E402

WEDDING_OUT = (sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv
               else os.path.join(tempfile.gettempdir(), "vrouves_wedding.png"))
C["vrouves"] = (0.1, 0.5, 0.08)
C["ribbon"] = (1, 0.85, 0.9)
t = Toon("VrouvesWedding", line=2.4)

import bpy  # noqa: E402

# ------------------------------------------------------------------ land and sky
bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 20, 0))
t.put(bpy.context.object, "grass").name = "Ground"
for i, (x, y, s) in enumerate([(-18, 44, 14), (-4, 50, 18), (12, 46, 15), (27, 44, 12)]):
    t.cyl("Mount%d" % i, (x, y, s * 0.5), s, s, "mount", verts=7, r2=0)
    t.cyl("Snow%d" % i, (x, y, s * 0.86), s * 0.29, s * 0.28, "snow", verts=7, r2=0)
t.sphere("Sun", (17, 34, 15), (2.4, 0.5, 2.4), "yellow")
t.torus("Sun_smile", (17, 33.4, 14.4), 1.0, 0.13, "black", rot=(R(90), 0, 0), half=True)
for sd in (-1, 1):
    t.sphere("Sun_eye%d" % sd, (17 + sd * 0.8, 33.4, 15.6), (0.25, 0.1, 0.35), "black")

# ------------------------------------------------------------------ the church
cx, cy = 0.5, 11.0
t.box("Nave", (cx, cy, 2.6), (11, 4, 5.2), "white")
t.cyl("Nave_roof", (cx, cy, 5.2), 2.0, 11.0, "white", rot=(0, R(90), 0))
t.cyl("Drum", (cx, cy - 0.5, 6.4), 1.7, 1.6, "white")
t.sphere("Dome", (cx, cy - 0.5, 7.2), (1.75, 1.75, 1.5), "blue")
t.box("Dome_cross_v", (cx, cy - 0.5, 9.2), (0.12, 0.12, 1.1), "yellow")
t.box("Dome_cross_h", (cx, cy - 0.5, 9.35), (0.6, 0.12, 0.12), "yellow")
t.box("Door", (cx, cy - 2.02, 1.4), (1.6, 0.06, 2.8), "brown")
t.cyl("Door_arch", (cx, cy - 2.02, 2.8), 0.8, 0.06, "brown", rot=(R(90), 0, 0))
for k, wx in enumerate((-3.4, -1.6, 2.6, 4.4)):
    t.box("Win%d" % k, (cx + wx, cy - 2.02, 2.9), (0.7, 0.06, 1.3), "blue")
# the bell tower, its bell in the arch
bx = cx - 6.8
t.box("Tower", (bx, cy - 0.5, 3.8), (2.2, 2.2, 7.6), "white")
t.box("Tower_arch", (bx, cy - 1.62, 5.9), (1.2, 0.06, 1.6), "dark")
t.cyl("Bell", (bx, cy - 1.7, 5.85), 0.45, 0.8, "yellow", r2=0.2)
t.cyl("Tower_dome", (bx, cy - 0.5, 7.9), 1.1, 0.6, "blue", r2=0.3)
t.box("Tower_cross", (bx, cy - 0.5, 8.6), (0.1, 0.1, 0.8), "yellow")
# a garland of flowers over the door
for k in range(9):
    a = math.pi * k / 8
    t.sphere("Garland%d" % k, (cx - math.cos(a) * 1.3, cy - 2.1, 3.0 + math.sin(a) * 0.6),
             (0.2, 0.08, 0.2), "pink" if k % 2 else "white")
for i, (x, y) in enumerate([(-10.5, 9), (-12, 13), (11.5, 10), (13, 14)]):
    t.cyl("Cypress%d" % i, (x, y, 3.0), 0.9, 6.0, "leaf", r2=0.1)

# ------------------------------------------------------------------ bunting over the feast
for sd in (-1, 1):
    t.cyl("Pole%d" % sd, (sd * 7.4, 3.6, 2.6), 0.08, 5.2, "wood")
cols = ["white", "blue", "pink", "white", "yellow", "cyan"]
for k in range(19):
    u = k / 18
    x = -7.4 + u * 14.8
    z = 5.0 - 0.9 * math.sin(math.pi * u)
    t.cyl("Bunting%d" % k, (x, 3.6, z - 0.25), 0.28, 0.5, cols[k % len(cols)], verts=3, r2=0,
          rot=(R(180), 0, R(90)))

# ------------------------------------------------------------------ the long table
ty = 3.2
t.box("Table", (0, ty, 1.0), (13.5, 1.8, 0.12), "white")
t.box("Cloth", (0, ty - 0.92, 0.8), (13.5, 0.04, 0.45), "white")
for k in range(14):     # a hem of little hearts... of red squares
    t.box("Hem%d" % k, (-6.27 + k * 0.965, ty - 0.95, 0.62), (0.45, 0.04, 0.1), "pink")
SEATS = [(-5.4, "cretan"), (-3.6, "yiayia"), (-1.8, "priest"), (0.0, "baker"),
         (1.8, "cretan2"), (3.6, "yiayia2"), (5.4, "cretan3")]
z0 = 0.15
for x, who in SEATS:
    p = who.capitalize()
    if who == "cretan":
        t.cretan(p, x, ty + 0.75, z0, look=(0.5, -0.3), glass=True)
    elif who == "yiayia":
        t.yiayia(p, x, ty + 0.75, z0, look=(0.4, -0.3))
    elif who == "priest":
        t.priest(p, x, ty + 0.75, z0, look=(0.3, -0.4))
    elif who == "baker":
        t.baker(p, x, ty + 0.75, z0, look=(0, -0.4))
    elif who == "cretan2":
        t.cretan(p, x, ty + 0.75, z0, look=(-0.4, -0.3), beard=True, glass=True)
    elif who == "yiayia2":
        t.yiayia(p, x, ty + 0.75, z0, look=(-0.5, -0.3))
    else:
        t.cretan(p, x, ty + 0.75, z0, look=(-0.7, -0.2), glass=True)
for k, (x, _) in enumerate(SEATS):      # plates heaped with vrouves
    t.cyl("Plate%d" % k, (x, ty - 0.35, 1.08), 0.38, 0.04, "white")
    for j in range(4):
        a = j * 1.6 + k
        t.sphere("Vrouves%d_%d" % (k, j), (x + math.cos(a) * 0.13, ty - 0.35 + math.sin(a) * 0.1, 1.15),
                 (0.17, 0.14, 0.07), "vrouves" if j % 2 else "leaf")
for k, x in enumerate((-4.5, -0.9, 2.7)):
    t.cyl("Jug%d" % k, (x, ty - 0.1, 1.38), 0.22, 0.6, "wine", r2=0.14)
for k, x in enumerate((-2.7, 0.9, 4.5)):   # the wedding breads, round and decorated
    t.cyl("Bread%d" % k, (x, ty - 0.2, 1.15), 0.42, 0.2, "bread")
    t.torus("Bread_deco%d" % k, (x, ty - 0.2, 1.26), 0.26, 0.05, "cream")

# ------------------------------------------------------------------ the couple, dancing


def crown(p, x, y, z):
    """the wedding crown: a ring of little white flowers"""
    t.torus(p + "_crown", (x, y, z), 0.42, 0.06, "white")
    for k in range(8):
        a = k * math.pi / 4
        t.sphere(p + "_bud%d" % k, (x + math.cos(a) * 0.42, y + math.sin(a) * 0.4, z + 0.05),
                 (0.09, 0.09, 0.09), "pink" if k % 2 else "white")


dy = -1.0
bxl, gxr = -1.0, 1.0
t.bride("Bride", bxl, dy, 0.0, look=(0.6, 0.1))
crown("Bride", bxl, dy - 0.02, 2.72)
# the groom: a Cretan in his best, with his crown instead of the sariki
t.cretan("Groom", gxr, dy, 0.0, look=(-0.6, 0.1), sariki=False)
t.sphere("Groom_hair", (gxr, dy + 0.05, 2.62), (0.62, 0.56, 0.28), "black")
t.box("Groom_shirt", (gxr, dy - 0.52, 1.35), (0.45, 0.06, 0.6), "white")
crown("Groom", gxr, dy - 0.02, 2.82)
# hand in hand, arms up in the dance
for k, (x, rot) in enumerate([(bxl + 0.55, -40), (gxr - 0.55, 40)]):
    t.cyl("Arm%d" % k, (x, dy - 0.25, 1.95), 0.11, 0.9, "white" if k == 0 else "black", rot=(0, R(rot), 0))
t.sphere("Hands", (0, dy - 0.3, 2.3), (0.18, 0.15, 0.15), "skin")
for k, (x, rot) in enumerate([(bxl - 0.6, 30), (gxr + 0.6, -30)]):
    t.cyl("Arm_out%d" % k, (x, dy - 0.2, 1.4), 0.11, 0.8, "white" if k == 0 else "black",
          rot=(0, R(rot), 0))
# the ribbon between the crowns, held up in the middle by Psssst
for k, (x0, x1) in enumerate([(bxl, -0.05), (0.05, gxr)]):
    for j in range(6):
        u = (j + 0.5) / 6
        x = x0 + (x1 - x0) * u
        z = 2.85 + 1.2 * (u if k == 0 else 1 - u)
        t.sphere("Ribbon%d_%d" % (k, j), (x, dy - 0.05, z), (0.16, 0.05, 0.09), "pink")
t.psssst("Ps", 0.0, dy - 0.1, 4.45, look=(0, -0.6))

# ------------------------------------------------------------------ the Lyra player
lx, ly = -4.6, -1.3
t.box("Chair_seat", (lx, ly + 0.2, 0.75), (0.9, 0.8, 0.1), "wood")
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        t.cyl("Chair_leg%d%d" % (sx_, sy_), (lx + sx_ * 0.38, ly + 0.2 + sy_ * 0.33, 0.37), 0.05, 0.75, "wood")
t.box("Chair_back", (lx, ly + 0.6, 1.4), (0.9, 0.08, 1.2), "wood")
t.cretan("Lyra", lx, ly + 0.1, 0.2, look=(0.7, -0.3), beard=True)
# the lyra, upright on his left knee, and the bow across it
t.sphere("Lyra_body", (lx + 0.3, ly - 0.6, 1.3), (0.28, 0.12, 0.45), "brown")
t.cyl("Lyra_neck", (lx + 0.3, ly - 0.62, 1.95), 0.08, 0.6, "brown")
t.sphere("Lyra_head", (lx + 0.3, ly - 0.62, 2.28), (0.12, 0.08, 0.1), "wood")
t.cyl("Lyra_bow", (lx + 0.3, ly - 0.78, 1.55), 0.03, 1.5, "wood", rot=(0, R(80), 0))
for k in range(3):
    t.sphere("Bow_bell%d" % k, (lx - 0.35 + k * 0.12, ly - 0.8, 1.45), (0.06, 0.06, 0.06), "yellow")
for k, (x, z) in enumerate([(-3.4, 3.0), (-3.0, 3.5), (-3.6, 3.8)]):   # the tune in the air
    t.sphere("Note%d" % k, (x, ly - 0.9, z), (0.13, 0.06, 0.1), "black")
    t.box("Note_stem%d" % k, (x + 0.12, ly - 0.9, z + 0.25), (0.03, 0.03, 0.45), "black")

# ------------------------------------------------------------------ the cauldron of gamopilafo
gx, gy = 4.6, -1.8
for j, a in enumerate((20, -25, 75)):
    t.cyl("Log%d" % j, (gx, gy, 0.18), 0.12, 1.6, "brown", rot=(0, R(90), R(a)))
for j, (dx, h, col) in enumerate([(-0.7, 0.75, "flame"), (-0.35, 1.0, "orange"), (0.0, 0.6, "red"),
                                  (0.35, 0.95, "flame"), (0.7, 0.7, "orange")]):
    t.cyl("Flame%d" % j, (gx + dx, gy - 0.45 - 0.1 * (j % 2), 0.15 + h / 2), 0.2, h, col,
          verts=12, r2=0, rot=(0, R((j % 3 - 1) * 8), 0))
for j, a in enumerate((90, 210, 330)):
    t.cyl("Leg%d" % j, (gx + math.cos(R(a)) * 0.6, gy + math.sin(R(a)) * 0.5, 0.4), 0.05, 0.8, "dark")
t.cyl("Cauldron", (gx, gy, 0.95), 0.8, 0.85, "black", r2=0.68)
t.torus("Rim", (gx, gy, 1.37), 0.74, 0.07, "dark")
t.sphere("Pilafi", (gx, gy, 1.37), (0.7, 0.7, 0.14), "rice")
for j in range(2):
    t.sphere("Steam%d" % j, (gx + 0.25 - j * 0.45, gy + 0.2, 1.85 + j * 0.3), (0.16, 0.1, 0.12), "white")

# ------------------------------------------------------------------ camera
t.camera((0.2, -10.5, 3.2), (R(84), 0, 0), lens=24, shift_y=0.06)
t.render(WEDDING_OUT)
print("wedding:", WEDDING_OUT, len(t.col.objects), "objects")
