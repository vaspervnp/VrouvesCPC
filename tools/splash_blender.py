"""The cartoon splash scene for LET'S GO FOR VROUVES, built in Blender.

Run inside Blender (Text editor, or the Blender MCP): it builds its own scene
"VrouvesSplash" (other scenes are left alone) and renders it to SPLASH_OUT.
"""
import math
import os
import tempfile

import bpy

SPLASH_OUT = os.path.join(tempfile.gettempdir(), "vrouves_splash.png")
SCENE = "VrouvesSplash"

# ------------------------------------------------------------------ scene
if SCENE in bpy.data.scenes:
    old = bpy.data.scenes[SCENE]
    for ob in list(old.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.scenes.remove(old)
sc = bpy.data.scenes.new(SCENE)
bpy.context.window.scene = sc
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
sc.render.use_freestyle = True
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = 3.2
ls = sc.view_layers[0].freestyle_settings.linesets
lset = ls[0] if len(ls) else ls.new("Lines")
lset.linestyle.color = (0, 0, 0)
lset.select_by_visibility = True
lset.select_silhouette = lset.select_border = lset.select_crease = True

world = bpy.data.worlds.new("SplashSky")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.35, 0.65, 1.0, 1)
bg.inputs[1].default_value = 0.6
sc.world = world

MATS = {}


def toon(name, rgb):
    """flat cartoon shading: two tones, lit and shadow"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new("sp_" + name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    em = nt.nodes.new("ShaderNodeEmission")
    ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (rgb[0] * .55, rgb[1] * .55, rgb[2] * .6, 1)
    e[1].position, e[1].color = 0.12, (rgb[0], rgb[1], rgb[2], 1)
    nt.links.new(dif.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1)
    MATS[name] = m
    return m


C = {
    "black": (0.03, 0.03, 0.04), "skin": (1.0, 0.62, 0.42), "white": (1, 1, 1),
    "blue": (0.05, 0.25, 0.9), "grass": (0.2, 0.7, 0.12), "road": (0.95, 0.5, 0.12),
    "brown": (0.45, 0.22, 0.07), "sack": (0.8, 0.6, 0.3), "leaf": (0.25, 0.85, 0.15),
    "grey": (0.55, 0.57, 0.6), "dark": (0.2, 0.2, 0.24), "red": (1, 0.08, 0.05),
    "yellow": (1, 0.9, 0.1), "mount": (0.45, 0.4, 0.6), "snow": (0.95, 0.97, 1),
    "khaki": (0.5, 0.5, 0.25), "pink": (1, 0.45, 0.6), "cyan": (0.2, 0.9, 1),
}
COL = bpy.data.collections.new("Splash")
sc.collection.children.link(COL)


def put(ob, mat=None, smooth=True):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    COL.objects.link(ob)
    if mat:
        ob.data.materials.clear()
        ob.data.materials.append(toon(mat, C[mat]))
    if smooth and ob.type == "MESH":
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def sphere(name, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    return put(ob, mat)


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=32, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth,
                                        location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    return put(ob, mat, smooth=verts > 8)


def box(name, loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    return put(ob, mat, smooth=False)


def torus(name, loc, R, r, mat, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=40, minor_segments=12)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    return put(ob, mat)


def text(name, s, loc, size, mat, rot=(math.radians(90), 0, 0), extrude=0.12):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.data.body = s
    ob.data.size = size
    ob.data.extrude = extrude
    ob.data.align_x = "CENTER"
    ob.data.align_y = "CENTER"
    return put(ob, mat, smooth=False)


def surface_y(head, dx, dz):
    """front of the ellipsoid head = (centre, scale) at offsets dx, dz"""
    (hx, hy, hz), (a, b, c) = head
    return hy - b * math.sqrt(max(0.05, 1 - (dx / a) ** 2 - (dz / c) ** 2))


def eye(name, head, dx, dz, r, look=(0, 0), pupil=0.45):
    """a googly eye sitting on the front of the head; look = (x, z) of the pupil"""
    (hx, hy, hz), _ = head
    x, z = hx + dx, hz + dz
    y = surface_y(head, dx, dz) + r * 0.15
    sphere(name, (x, y, z), (r, r * 0.55, r * 1.15), "white")
    sphere(name + "_p", (x + look[0] * r * 0.45, y - r * 0.45, z + look[1] * r * 0.45),
           (r * pupil, r * 0.25, r * pupil * 1.1), "black")


R = math.radians

# ------------------------------------------------------------------ land
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 20, 0))
put(bpy.context.object, "grass").name = "Ground"
road = box("Road", (1.0, 1.5, 0.01), (30, 2.2, 0.02), "road", rot=(0, 0, R(-8)))
for i, (x, y, s) in enumerate([(-14, 40, 14), (2, 46, 18), (16, 40, 13), (-26, 38, 10), (28, 42, 12)]):
    m = cyl("Mount%d" % i, (x, y, s * 0.5), s, s, "mount", verts=7, r2=0)
    cyl("Snow%d" % i, (x, y, s * 0.86), s * 0.29, s * 0.28, "snow", verts=7, r2=0)
# the sun, wearing shades
sphere("Sun", (17, 30, 15), (2.6, 0.5, 2.6), "yellow")
box("Shade_l", (16.2, 29.3, 15.4), (1.1, 0.1, 0.65), "black")
box("Shade_r", (17.9, 29.3, 15.4), (1.1, 0.1, 0.65), "black")
box("Shade_b", (17.05, 29.3, 15.65), (0.6, 0.1, 0.12), "black")
torus("Sun_smile", (17, 29.3, 14.2), 1.0, 0.12, "black", rot=(R(90), 0, 0), scale=(1, 1, 0.55))
for i in range(4):     # trees
    x = (-9.5, -4.2, 6.5, 12)[i]
    y = (10, 14, 12, 9)[i]
    cyl("Trunk%d" % i, (x, y, 0.7), 0.25, 1.4, "brown")
    sphere("Crown%d" % i, (x, y, 2.1), (1.3, 1.3, 1.2), "leaf")

# ------------------------------------------------------------------ the kafenio
box("Kaf", (-6.6, 3.5, 2.0), (4.4, 3.0, 4.0), "white")
box("Kaf_roof", (-6.6, 3.5, 4.1), (4.7, 3.3, 0.25), "blue")
box("Kaf_door", (-5.6, 1.98, 1.1), (1.1, 0.06, 2.1), "blue")
box("Kaf_win", (-7.7, 1.98, 2.3), (1.0, 0.06, 1.0), "blue")
box("Kaf_sign", (-6.3, 1.9, 3.4), (4.0, 0.12, 0.95), "blue")
text("Kaf_text", "ΚΑΦΕΝΕΙΟ", (-6.3, 1.8, 3.4), 0.75, "white", extrude=0.01)
box("Table", (-4.0, 0.4, 0.75), (0.9, 0.9, 0.08), "white")
cyl("Table_leg", (-4.0, 0.4, 0.37), 0.06, 0.75, "dark")
cyl("Cup", (-4.15, 0.3, 0.92), 0.12, 0.25, "white")
cyl("Coffee", (-4.15, 0.3, 1.05), 0.1, 0.02, "brown")

# ------------------------------------------------------------------ sacks of vrouves
for i, (x, y) in enumerate([(-4.3, -1.6), (-3.2, -2.1), (-2.4, -1.4)]):
    sphere("Sack%d" % i, (x, y, 0.55), (0.6, 0.5, 0.65), "sack")
    for j in range(5):
        a = j * 1.25
        sphere("Leaf%d_%d" % (i, j), (x + math.cos(a) * 0.22, y + math.sin(a) * 0.18, 1.2),
               (0.12, 0.08, 0.38), "leaf", rot=(math.sin(a) * 0.6, math.cos(a) * 0.6, 0))

# ------------------------------------------------------------------ the Cretan
cx = -1.1
cyl("Cr_boot_l", (cx - 0.3, 0, 0.45), 0.24, 0.9, "black")
cyl("Cr_boot_r", (cx + 0.3, 0, 0.45), 0.24, 0.9, "black")
sphere("Cr_vraka", (cx, 0, 1.15), (0.62, 0.5, 0.5), "black")    # baggy breeches
cyl("Cr_body", (cx, 0, 1.75), 0.55, 1.1, "black", r2=0.62)
cyl("Cr_sash", (cx, 0, 1.3), 0.6, 0.18, "red")
CR_HEAD = ((cx, -0.05, 2.9), (0.78, 0.72, 0.8))
sphere("Cr_head", *CR_HEAD, "skin")
sphere("Cr_nose", (cx, surface_y(CR_HEAD, 0, -0.05) - 0.05, 2.85), (0.2, 0.2, 0.22), "skin")
eye("Cr_eye_l", CR_HEAD, -0.26, 0.2, 0.2, look=(0.7, 0))
eye("Cr_eye_r", CR_HEAD, 0.26, 0.2, 0.2, look=(0.7, 0))
box("Cr_brow_l", (cx - 0.28, surface_y(CR_HEAD, -0.28, 0.42) - 0.08, 3.34), (0.36, 0.08, 0.09),
    "black", rot=(0, R(-20), 0))
box("Cr_brow_r", (cx + 0.28, surface_y(CR_HEAD, 0.28, 0.42) - 0.08, 3.34), (0.36, 0.08, 0.09),
    "black", rot=(0, R(20), 0))
# the handlebar moustache, ends curled up
my = surface_y(CR_HEAD, 0, -0.32) - 0.06
for sd in (-1, 1):
    sphere("Cr_mous%d" % sd, (cx + sd * 0.3, my, 2.6), (0.36, 0.12, 0.12), "black",
           rot=(0, R(sd * 18), 0))
    sphere("Cr_curl%d" % sd, (cx + sd * 0.64, my + 0.06, 2.74), (0.1, 0.1, 0.16), "black")
# the sariki: black headscarf with a fringe
sphere("Cr_sariki", (cx, -0.02, 3.35), (0.82, 0.76, 0.45), "black")
for k in range(16):
    a = math.pi + k * math.pi / 15
    sphere("Cr_fringe%d" % k, (cx + math.cos(a) * 0.8, -math.sin(a) * 0.72 - 0.05 + 0.0, 3.2),
           (0.07, 0.07, 0.07), "black")
# the rifle, held across
cyl("Cr_barrel", (cx + 0.55, -0.55, 2.2), 0.06, 2.2, "dark", rot=(0, R(55), 0))
box("Cr_stock", (cx - 0.15, -0.55, 1.6), (0.7, 0.14, 0.22), "brown", rot=(0, R(55), 0))
sphere("Cr_hand", (cx + 0.35, -0.6, 2.0), (0.17, 0.17, 0.17), "skin")

# ------------------------------------------------------------------ Yiayia, throwing her slipper
yx = 1.6
cyl("Yi_dress", (yx, 0.2, 0.9), 0.75, 1.8, "black", r2=0.42)
YI_HEAD = ((yx, 0.0, 2.25), (0.6, 0.56, 0.62))
sphere("Yi_head", *YI_HEAD, "skin")
sphere("Yi_scarf", (yx, 0.25, 2.45), (0.72, 0.62, 0.66), "black")
eye("Yi_eye_l", YI_HEAD, -0.2, 0.05, 0.13, look=(0.7, 0.6))
eye("Yi_eye_r", YI_HEAD, 0.2, 0.05, 0.13, look=(0.7, 0.6))
for s_ in (-1, 1):
    torus("Yi_glass%d" % s_, (yx + s_ * 0.2, surface_y(YI_HEAD, s_ * 0.2, 0.05) - 0.1, 2.3),
          0.17, 0.025, "dark", rot=(R(90), 0, 0))
sphere("Yi_mouth", (yx, surface_y(YI_HEAD, 0, -0.27), 1.98), (0.16, 0.08, 0.13), "red")   # shouting
cyl("Yi_arm", (yx + 0.55, 0.1, 2.3), 0.12, 1.1, "black", rot=(0, R(-40), 0))
sphere("Yi_hand", (yx + 0.9, 0.05, 2.75), (0.14, 0.14, 0.14), "skin")
cyl("Yi_staff", (yx - 0.75, -0.1, 1.2), 0.07, 2.5, "brown", rot=(0, R(10), 0))
torus("Yi_staff_hook", (yx - 0.6, -0.1, 2.5), 0.18, 0.07, "brown", rot=(R(90), 0, 0))
# the flying slipper (pantofla) and its speed lines
box("Slipper", (3.65, -0.9, 3.55), (0.9, 0.4, 0.14), "pink", rot=(R(70), R(-25), R(10)))
sphere("Slipper_pom", (3.95, -1.05, 3.7), (0.2, 0.2, 0.2), "red")
for k in range(3):
    box("Speed%d" % k, (2.75 - k * 0.1, -0.9, 3.05 + k * 0.32), (0.8, 0.04, 0.05), "white",
        rot=(0, R(-28), 0))

# ------------------------------------------------------------------ the F&M drone, panicking
dx, dz = 4.7, 3.9
sphere("Dr_body", (dx, 0, dz), (0.8, 0.7, 0.55), "grey")
DR_HEAD = ((dx, 0, dz), (0.8, 0.7, 0.55))
eye("Dr_eye_l", DR_HEAD, -0.25, 0.1, 0.24, look=(-0.8, 0.2), pupil=0.25)
eye("Dr_eye_r", DR_HEAD, 0.25, 0.1, 0.24, look=(-0.8, 0.2), pupil=0.25)
sphere("Dr_mouth", (dx, surface_y(DR_HEAD, 0, -0.25), dz - 0.25), (0.22, 0.06, 0.14), "black")
for s in (-1, 1):
    box("Dr_arm%d" % s, (dx + s * 0.95, 0, dz + 0.3), (0.9, 0.12, 0.1), "dark")
    cyl("Dr_rotor%d" % s, (dx + s * 1.35, 0, dz + 0.45), 0.55, 0.04, "cyan")
sphere("Dr_sweat", (dx + 0.75, -0.4, dz + 0.55), (0.1, 0.06, 0.16), "cyan")

# ------------------------------------------------------------------ Psssst, the defected drone, in a sariki
px, pz = -3.2, 4.7
sphere("Ps_body", (px, 0, pz), (0.62, 0.55, 0.45), "yellow")
PS_HEAD = ((px, 0, pz), (0.62, 0.55, 0.45))
eye("Ps_eye_l", PS_HEAD, -0.2, 0.05, 0.16, look=(0.8, 0))
eye("Ps_eye_r", PS_HEAD, 0.2, 0.05, 0.16, look=(0.8, 0))
torus("Ps_smile", (px, surface_y(PS_HEAD, 0, -0.15) - 0.02, pz - 0.15), 0.18, 0.04, "black", rot=(R(90), 0, 0), scale=(1, 1, 0.5))
sphere("Ps_sariki", (px, 0, pz + 0.35), (0.6, 0.52, 0.25), "black")
for s in (-1, 1):
    box("Ps_arm%d" % s, (px + s * 0.75, 0, pz + 0.2), (0.6, 0.1, 0.08), "dark")
    cyl("Ps_rotor%d" % s, (px + s * 1.05, 0, pz + 0.32), 0.4, 0.04, "cyan")

# ------------------------------------------------------------------ the weed destroyer, dented
tx = 6.0
box("Tk_tread", (tx, 1.8, 0.45), (2.6, 1.6, 0.8), "dark")
box("Tk_hull", (tx, 1.8, 1.1), (2.2, 1.4, 0.7), "khaki")
sphere("Tk_turret", (tx - 0.1, 1.8, 1.55), (0.75, 0.65, 0.5), "khaki")
cyl("Tk_whacker", (tx - 1.4, 1.2, 0.9), 0.08, 1.4, "grey", rot=(0, R(65), R(20)))
cyl("Tk_blade", (tx - 2.0, 0.9, 0.35), 0.4, 0.04, "red")
for k in range(4):
    cyl("Tk_wheel%d" % k, (tx - 0.9 + k * 0.6, 0.95, 0.45), 0.3, 0.1, "grey", rot=(R(90), 0, 0))
for k, ex in enumerate((tx - 0.45, tx - 0.05)):
    sphere("Tk_eye%d" % k, (ex, 1.08, 1.2), (0.17, 0.05, 0.2), "white")
    sphere("Tk_pupil%d" % k, (ex - 0.06, 1.03, 1.17), (0.07, 0.03, 0.07), "black")
text("Tk_logo", "F&M", (tx + 0.6, 1.08, 1.2), 0.35, "red", extrude=0.02)
for k in range(3):     # bump: little stars
    sphere("Tk_star%d" % k, (tx - 0.1 + (k - 1) * 0.5, 1.8, 2.3 + (k % 2) * 0.2),
           (0.12, 0.12, 0.12), "yellow")

# ------------------------------------------------------------------ a goat, stealing a leaf
gx, gy = -1.3, -3.2
sphere("Gt_body", (gx, gy, 0.75), (0.75, 0.42, 0.42), "white")
for k, (lx, ly) in enumerate([(-0.45, -0.2), (0.45, -0.2), (-0.45, 0.2), (0.45, 0.2)]):
    cyl("Gt_leg%d" % k, (gx + lx, gy + ly, 0.3), 0.08, 0.6, "white")
GT_HEAD = ((gx - 0.85, gy - 0.1, 1.05), (0.32, 0.28, 0.3))
sphere("Gt_head", *GT_HEAD, "white")
sphere("Gt_snout", (gx - 1.1, gy - 0.18, 0.95), (0.18, 0.16, 0.14), "white")
eye("Gt_eye_l", GT_HEAD, -0.12, 0.08, 0.1, look=(-0.6, 0))
eye("Gt_eye_r", GT_HEAD, 0.1, 0.08, 0.1, look=(-0.6, 0))
for sd in (-1, 1):
    cyl("Gt_horn%d" % sd, (gx - 0.8 + sd * 0.12, gy - 0.05, 1.42), 0.06, 0.35, "grey", r2=0.01,
        rot=(0, R(sd * 25 + 15), 0))
cyl("Gt_beard", (gx - 1.12, gy - 0.2, 0.72), 0.07, 0.25, "grey", r2=0.0, rot=(R(180), 0, 0))
sphere("Gt_leaf", (gx - 1.35, gy - 0.25, 0.92), (0.22, 0.05, 0.08), "leaf", rot=(0, R(-20), 0))
cyl("Gt_tail", (gx + 0.8, gy, 1.05), 0.06, 0.25, "white", rot=(0, R(-40), 0))

# ------------------------------------------------------------------ light, camera
bpy.ops.object.light_add(type="SUN", location=(0, -10, 10), rotation=(R(50), R(10), R(-25)))
put(bpy.context.object).data.energy = 3
bpy.ops.object.camera_add(location=(-0.3, -11.5, 2.9), rotation=(R(84), 0, 0))
cam = put(bpy.context.object)
cam.data.lens = 28
cam.data.shift_y = 0.08
sc.camera = cam

sc.render.filepath = SPLASH_OUT
bpy.ops.render.render(write_still=True)
result = {"out": SPLASH_OUT, "objects": len(COL.objects)}
