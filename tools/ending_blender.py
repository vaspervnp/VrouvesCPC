"""The ending scene of LET'S GO FOR VROUVES, built in Blender: the victory
feast in front of the school.

Everyone at one long table: the Cretan, the Bride, Yiayia, the Baker, the
priest, more Cretans and Psssst.  In front, cauldrons of gamopilafo on the
fire and a lamb running away from it, scared; bottom right, a tree with a
hollow where a bird looks out with her chicks.

Run inside Blender (tools/ on sys.path, for blender_toon): it builds its own
scene "VrouvesEnding" and renders it to ENDING_OUT.
"""
import math
import os
import tempfile

from blender_toon import R, Toon

ENDING_OUT = os.path.join(tempfile.gettempdir(), "vrouves_ending.png")
t = Toon("VrouvesEnding", line=2.4)

# ------------------------------------------------------------------ land and sky
import bpy  # noqa: E402

bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 20, 0))
t.put(bpy.context.object, "grass").name = "Ground"
for i, (x, y, s) in enumerate([(-16, 44, 14), (-2, 50, 18), (14, 46, 15), (28, 44, 12)]):
    t.cyl("Mount%d" % i, (x, y, s * 0.5), s, s, "mount", verts=7, r2=0)
    t.cyl("Snow%d" % i, (x, y, s * 0.86), s * 0.29, s * 0.28, "snow", verts=7, r2=0)
t.sphere("Sun", (-17, 34, 15), (2.4, 0.5, 2.4), "yellow")
t.torus("Sun_smile", (-17, 33.4, 14.4), 1.0, 0.13, "black", rot=(R(90), 0, 0), half=True)
for sd in (-1, 1):
    t.sphere("Sun_eye%d" % sd, (-17 + sd * 0.8, 33.4, 15.6), (0.25, 0.1, 0.35), "black")

# ------------------------------------------------------------------ the school
sx, sy = 0.0, 9.5
t.box("School", (sx, sy, 2.8), (13, 3, 5.6), "cream")
roof = t.cyl("School_roof", (sx, sy, 5.85), 2.1, 13.6, "roof", verts=3, rot=(0, R(-90), 0))
roof.scale = (0.38, 1.0, 1.0)        # local x is the height
t.box("School_sign", (sx, sy - 1.56, 5.0), (4.6, 0.12, 1.0), "red")
t.text("School_text", "ΣΧΟΛΕΙΟ", (sx, sy - 1.66, 5.0), 0.8, "white", extrude=0.01)
for k in range(6):
    wx = sx - 5.4 + k * 2.16
    if abs(wx - sx) < 1.5:
        t.box("School_door", (sx, sy - 1.52, 1.2), (1.3, 0.06, 2.4), "blue")
        continue
    t.box("School_win%d" % k, (wx, sy - 1.52, 2.4), (1.2, 0.06, 1.5), "blue")
    t.box("School_sill%d" % k, (wx, sy - 1.56, 1.62), (1.4, 0.12, 0.1), "white")
# the flag of Greece on its pole
t.cyl("Flag_pole", (7.6, 7.0, 3.0), 0.07, 6.0, "silver")
t.box("Flag", (8.6, 7.0, 5.1), (1.9, 0.04, 1.35), "blue")
for k in range(4):
    t.box("Flag_s%d" % k, (8.6, 6.97, 5.62 - k * 0.3), (1.9, 0.02, 0.15), "white")
t.box("Flag_canton", (8.0, 6.95, 5.4), (0.75, 0.02, 0.75), "blue")
t.box("Flag_cross_h", (8.0, 6.93, 5.4), (0.75, 0.02, 0.15), "white")
t.box("Flag_cross_v", (8.0, 6.93, 5.4), (0.15, 0.02, 0.75), "white")
for i, (x, y) in enumerate([(-9.5, 8), (-11.5, 12), (11, 12)]):
    t.cyl("Trunk%d" % i, (x, y, 0.8), 0.3, 1.6, "brown")
    t.sphere("Crown%d" % i, (x, y, 2.5), (1.5, 1.5, 1.4), "leaf")

# ------------------------------------------------------------------ bunting over the feast
for sd in (-1, 1):
    t.cyl("Pole%d" % sd, (sd * 7.2, 3.2, 2.6), 0.08, 5.2, "wood")
cols = ["blue", "white", "red", "yellow", "cyan", "pink"]
for k in range(19):
    u = k / 18
    x = -7.2 + u * 14.4
    z = 5.0 - 0.9 * math.sin(math.pi * u)
    t.cyl("Bunting%d" % k, (x, 3.2, z - 0.25), 0.28, 0.5, cols[k % len(cols)], verts=3, r2=0,
          rot=(R(180), 0, R(90)))

# ------------------------------------------------------------------ the long table
ty = 2.0
t.box("Table", (0, ty, 1.0), (13.5, 1.8, 0.12), "white")
t.box("Cloth", (0, ty - 0.92, 0.8), (13.5, 0.04, 0.45), "white")
for k in range(14):     # a checked hem on the cloth
    t.box("Hem%d" % k, (-6.27 + k * 0.965, ty - 0.95, 0.62), (0.45, 0.04, 0.1), "red")
for sd in (-1, 1):
    t.box("Table_leg%d" % sd, (sd * 6.3, ty - 0.6, 0.45), (0.12, 0.12, 0.9), "wood")

# ------------------------------------------------------------------ everyone at the table
SEATS = [   # x, who
    (-5.6, "cretan"), (-3.9, "bride"), (-2.3, "yiayia"), (-0.6, "baker"),
    (1.2, "priest"), (2.9, "cretan2"), (4.6, "cretan3"),
]
z0 = 0.15
for x, who in SEATS:
    p = who.capitalize()
    if who == "cretan":
        t.cretan(p, x, ty + 0.75, z0, look=(0.5, 0), glass=True)
    elif who == "bride":
        t.bride(p, x, ty + 0.75, z0, look=(-0.6, 0.2))
    elif who == "yiayia":
        t.yiayia(p, x, ty + 0.75, z0, look=(0, 0.3))
    elif who == "baker":
        t.baker(p, x, ty + 0.75, z0, look=(0.4, 0))
    elif who == "priest":
        t.priest(p, x, ty + 0.75, z0, look=(-0.4, 0.3))
    elif who == "cretan2":
        t.cretan(p, x, ty + 0.75, z0, look=(-0.5, 0), beard=True, glass=True)
    else:
        t.cretan(p, x, ty + 0.75, z0, look=(-0.7, 0.3), glass=True)
t.psssst("Ps", 2.1, ty + 0.5, 3.6, look=(0, -0.6))     # over the table, in the middle

# what is on the table
for k, (x, _) in enumerate(SEATS):
    t.cyl("Plate%d" % k, (x, ty - 0.35, 1.08), 0.38, 0.04, "white")
    t.sphere("Food%d" % k, (x, ty - 0.35, 1.13), (0.25, 0.25, 0.08), "rice")
for k, x in enumerate((-4.75, -1.45, 2.05, 5.4)):
    t.cyl("Jug%d" % k, (x, ty - 0.1, 1.38), 0.22, 0.6, "wine", r2=0.14)
    t.torus("Jug_handle%d" % k, (x + 0.24, ty - 0.1, 1.42), 0.13, 0.04, "wine", rot=(R(90), 0, 0))
for k, x in enumerate((-3.1, 0.3, 3.75)):
    t.sphere("Bread%d" % k, (x, ty - 0.15, 1.18), (0.45, 0.25, 0.2), "bread")

# ------------------------------------------------------------------ the cauldrons of gamopilafo
for k, x in enumerate((-3.6, -0.6)):
    cy = -2.6
    for j, a in enumerate((20, -25, 75)):    # the logs
        t.cyl("Log%d_%d" % (k, j), (x, cy, 0.18), 0.12, 1.6, "brown", rot=(0, R(90), R(a)))
    for j, (dx, h, col) in enumerate([(-0.75, 0.75, "flame"), (-0.4, 1.0, "orange"), (-0.05, 0.6, "red"),
                                      (0.3, 0.95, "flame"), (0.65, 0.7, "orange"), (0.85, 0.5, "red")]):
        t.cyl("Flame%d_%d" % (k, j), (x + dx, cy - 0.45 - 0.1 * (j % 2), 0.15 + h / 2), 0.2, h, col,
              verts=12, r2=0, rot=(0, R((j % 3 - 1) * 8), 0))
    for j, a in enumerate((90, 210, 330)):   # three legs
        t.cyl("Leg%d_%d" % (k, j), (x + math.cos(R(a)) * 0.6, cy + math.sin(R(a)) * 0.5, 0.4), 0.05, 0.8,
              "dark")
    t.cyl("Cauldron%d" % k, (x, cy, 0.95), 0.8, 0.85, "black", r2=0.68)
    t.torus("Rim%d" % k, (x, cy, 1.37), 0.74, 0.07, "dark")
    t.sphere("Pilafi%d" % k, (x, cy, 1.37), (0.7, 0.7, 0.14), "rice")
    for j in range(5):                       # grains of rice, piled up
        a = j * 1.3
        t.sphere("Grain%d_%d" % (k, j), (x + math.cos(a) * 0.33, cy + math.sin(a) * 0.28, 1.48),
                 (0.15, 0.15, 0.09), "rice")
    for j in range(2):                       # a little steam
        t.sphere("Steam%d_%d" % (k, j), (x + 0.25 - j * 0.45, cy + 0.2, 1.85 + j * 0.3), (0.16, 0.1, 0.12),
                 "white")
t.cyl("Ladle", (-3.25, -2.7, 1.75), 0.05, 1.3, "wood", rot=(0, R(25), 0))

# ------------------------------------------------------------------ the lamb, running for its life
lx, ly = 2.0, -3.4
for j, (dx, dz, s) in enumerate([(0, 0.95, 0.45), (-0.35, 0.95, 0.4), (0.35, 0.95, 0.4), (0, 1.25, 0.38),
                                 (-0.3, 1.2, 0.33), (0.3, 1.2, 0.33), (0, 0.75, 0.35)]):
    t.sphere("Lamb_wool%d" % j, (lx + dx, ly, dz), (s, s * 0.9, s * 0.85), "white")
for j, (dx, rot) in enumerate([(-0.4, 35), (-0.2, 20), (0.25, -30), (0.45, -45)]):   # legs flying
    t.cyl("Lamb_leg%d" % j, (lx + dx, ly, 0.4), 0.07, 0.6, "dark", rot=(0, R(rot), 0))
head = ((lx + 0.85, ly - 0.05, 1.35), (0.34, 0.3, 0.36))
t.sphere("Lamb_head", *head, "white")
t.eye("Lamb_eye_l", head, -0.12, 0.08, 0.13, look=(-0.9, 0.3), pupil=0.3)    # looking back at the fire
t.eye("Lamb_eye_r", head, 0.12, 0.08, 0.13, look=(-0.9, 0.3), pupil=0.3)
t.sphere("Lamb_mouth", (lx + 0.85, t.surface_y(head, 0, -0.18), 1.18), (0.1, 0.04, 0.08), "black")
for sd in (-1, 1):
    t.sphere("Lamb_ear%d" % sd, (lx + 0.85 + sd * 0.38, ly, 1.45), (0.2, 0.08, 0.08), "white",
             rot=(0, R(sd * -25), 0))
t.sphere("Lamb_sweat", (lx + 1.15, ly - 0.2, 1.95), (0.07, 0.05, 0.12), "cyan")
t.sphere("Lamb_sweat2", (lx + 0.6, ly - 0.3, 2.0), (0.06, 0.05, 0.1), "cyan")
for k in range(3):      # dust and speed lines behind it
    t.box("Lamb_speed%d" % k, (lx - 1.2 - k * 0.15, ly, 0.75 + k * 0.3), (0.8, 0.04, 0.05), "white")

# ------------------------------------------------------------------ the tree with the hollow, bottom right
hx, hy = 3.2, -5.2
t.cyl("Hollow_trunk", (hx, hy, 3.5), 0.7, 7.0, "brown", r2=0.55)
t.sphere("Hollow_crown", (hx - 0.2, hy + 0.3, 7.6), (2.6, 2.0, 1.8), "leaf")
t.cyl("Hollow_branch", (hx - 0.9, hy, 4.3), 0.16, 1.6, "brown", rot=(0, R(-55), 0))
t.sphere("Hollow_leaves", (hx - 1.6, hy, 4.9), (0.8, 0.6, 0.55), "leaf")
for j, a in enumerate((-40, 40, 0)):
    t.cyl("Root%d" % j, (hx + math.sin(R(a)) * 0.8, hy - 0.2, 0.2), 0.2, 0.9, "brown",
          rot=(0, R(a + 90 * (1 if a > 0 else -1) * 0.7), 0))
t.sphere("Hole", (hx - 0.3, hy - 0.62, 2.3), (0.42, 0.2, 0.52), "hole")
t.torus("Hole_rim", (hx - 0.3, hy - 0.64, 2.3), 0.42, 0.08, "wood", rot=(R(90), 0, 0), scale=(1, 1, 1.22))
# the mother bird on the rim
bh = ((hx - 0.3, hy - 0.85, 2.95), (0.24, 0.22, 0.24))
t.sphere("Bird_body", (hx - 0.3, hy - 0.75, 2.72), (0.32, 0.28, 0.26), "bird")
t.sphere("Bird_head", *bh, "bird")
t.eye("Bird_eye_l", bh, -0.08, 0.05, 0.07, look=(-0.5, -0.3))
t.eye("Bird_eye_r", bh, 0.08, 0.05, 0.07, look=(-0.5, -0.3))
t.cyl("Bird_beak", (hx - 0.3, hy - 1.08, 2.9), 0.07, 0.2, "orange", r2=0, rot=(R(90), 0, 0))
t.sphere("Bird_belly", (hx - 0.3, hy - 0.95, 2.68), (0.18, 0.08, 0.16), "orange")
for sd in (-1, 1):
    t.sphere("Bird_wing%d" % sd, (hx - 0.3 + sd * 0.3, hy - 0.75, 2.72), (0.12, 0.2, 0.2), "bird",
             rot=(0, R(sd * 20), 0))
# her chicks, beaks open, in the hollow
for j, dx in enumerate((-0.22, 0.0, 0.22)):
    ch = ((hx - 0.3 + dx, hy - 0.75, 2.2 + (0.06 if j == 1 else 0)), (0.13, 0.12, 0.13))
    t.sphere("Chick%d" % j, *ch, "chick")
    t.eye("Chick%d_eye_l" % j, ch, -0.05, 0.04, 0.035, pupil=0.5)
    t.eye("Chick%d_eye_r" % j, ch, 0.05, 0.04, 0.035, pupil=0.5)
    cx_, cy_, cz_ = ch[0]
    t.cyl("Chick%d_beak_u" % j, (cx_, cy_ - 0.15, cz_ + 0.12), 0.04, 0.1, "orange", r2=0,
          rot=(R(60), 0, 0))
    t.cyl("Chick%d_beak_d" % j, (cx_, cy_ - 0.15, cz_ + 0.03), 0.04, 0.1, "orange", r2=0,
          rot=(R(120), 0, 0))

# ------------------------------------------------------------------ camera
t.camera((0.2, -10.5, 3.0), (R(84), 0, 0), lens=24, shift_y=0.04)
t.render(ENDING_OUT)
result = {"out": ENDING_OUT, "objects": len(t.col.objects)}
