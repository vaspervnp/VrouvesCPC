"""Cartoon building blocks for the Blender scenes of LET'S GO FOR VROUVES
(tools/ending_blender.py): a scene with flat two-tone materials and black
Freestyle outlines, primitives, faces, and the villagers.

Imported inside Blender, with tools/ on sys.path.
"""
import math

import bmesh
import bpy

R = math.radians

C = {
    "black": (0.03, 0.03, 0.04), "skin": (1.0, 0.62, 0.42), "white": (1, 1, 1),
    "blue": (0.05, 0.25, 0.9), "grass": (0.2, 0.7, 0.12), "road": (0.95, 0.5, 0.12),
    "brown": (0.45, 0.22, 0.07), "wood": (0.65, 0.38, 0.15), "leaf": (0.25, 0.85, 0.15),
    "grey": (0.55, 0.57, 0.6), "dark": (0.2, 0.2, 0.24), "red": (1, 0.08, 0.05),
    "yellow": (1, 0.9, 0.1), "mount": (0.45, 0.4, 0.6), "snow": (0.95, 0.97, 1),
    "pink": (1, 0.45, 0.6), "cyan": (0.2, 0.9, 1), "cream": (1, 0.93, 0.75),
    "orange": (1, 0.45, 0.0), "flame": (1, 0.75, 0.05), "rice": (1, 0.95, 0.7),
    "wine": (0.5, 0.0, 0.1), "hair": (0.3, 0.15, 0.05), "silver": (0.8, 0.82, 0.86),
    "roof": (0.85, 0.25, 0.1), "glass": (0.75, 0.95, 1), "bird": (0.1, 0.45, 1),
    "chick": (1, 0.85, 0.2), "hole": (0.12, 0.06, 0.02), "bread": (0.85, 0.55, 0.2),
}


class Toon:
    def __init__(self, scene_name, size=(1280, 800), line=3.2, sky=(0.35, 0.65, 1.0)):
        if scene_name in bpy.data.scenes:
            old = bpy.data.scenes[scene_name]
            for ob in list(old.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.scenes.remove(old)
        sc = self.sc = bpy.data.scenes.new(scene_name)
        bpy.context.window.scene = sc
        for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                sc.render.engine = eng
                break
            except TypeError:
                pass
        sc.render.resolution_x, sc.render.resolution_y = size
        sc.render.resolution_percentage = 100
        sc.view_settings.view_transform = "Standard"
        sc.render.use_freestyle = True
        sc.render.line_thickness_mode = "ABSOLUTE"
        sc.render.line_thickness = line
        ls = sc.view_layers[0].freestyle_settings.linesets
        lset = ls[0] if len(ls) else ls.new("Lines")
        lset.linestyle.color = (0, 0, 0)
        lset.select_by_visibility = True
        lset.select_silhouette = lset.select_border = lset.select_crease = True
        world = bpy.data.worlds.new(scene_name + "Sky")
        world.use_nodes = True
        bg = world.node_tree.nodes["Background"]
        bg.inputs[0].default_value = sky + (1,)
        bg.inputs[1].default_value = 0.6
        sc.world = world
        self.col = bpy.data.collections.new(scene_name)
        sc.collection.children.link(self.col)
        self.mats = {}

    # -------------------------------------------------------------- materials
    def toon(self, name):
        """flat cartoon shading: two tones, lit and shadow"""
        if name in self.mats:
            return self.mats[name]
        rgb = C[name]
        m = bpy.data.materials.new("toon_" + name)
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
        m.diffuse_color = rgb + (1,)
        self.mats[name] = m
        return m

    # -------------------------------------------------------------- primitives
    def put(self, ob, mat=None, smooth=True):
        for c in ob.users_collection:
            c.objects.unlink(ob)
        self.col.objects.link(ob)
        if mat:
            ob.data.materials.clear()
            ob.data.materials.append(self.toon(mat))
        if smooth and ob.type == "MESH":
            for p in ob.data.polygons:
                p.use_smooth = True
        return ob

    def sphere(self, name, loc, scale, mat, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc, rotation=rot)
        ob = bpy.context.object
        ob.name = name
        ob.scale = scale
        return self.put(ob, mat)

    def cyl(self, name, loc, r, depth, mat, rot=(0, 0, 0), verts=32, r2=None):
        if r2 is None:
            bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                                location=loc, rotation=rot)
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth,
                                            location=loc, rotation=rot)
        ob = bpy.context.object
        ob.name = name
        return self.put(ob, mat, smooth=verts > 8)

    def box(self, name, loc, size, mat, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
        ob = bpy.context.object
        ob.name = name
        ob.scale = size
        return self.put(ob, mat, smooth=False)

    def torus(self, name, loc, R_, r, mat, rot=(0, 0, 0), scale=(1, 1, 1), half=False):
        """a ring; half=True keeps only its lower half (a smile, facing -y)"""
        bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=r, location=loc, rotation=rot,
                                         major_segments=40, minor_segments=12)
        ob = bpy.context.object
        ob.name = name
        if half:
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            # local y becomes world z after the 90 degree turn about x
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > 0.02], context="VERTS")
            bm.to_mesh(ob.data)
            bm.free()
        ob.scale = scale
        return self.put(ob, mat)

    def text(self, name, s, loc, size, mat, rot=(R(90), 0, 0), extrude=0.05):
        bpy.ops.object.text_add(location=loc, rotation=rot)
        ob = bpy.context.object
        ob.name = name
        ob.data.body = s
        ob.data.size = size
        ob.data.extrude = extrude
        ob.data.align_x = "CENTER"
        ob.data.align_y = "CENTER"
        return self.put(ob, mat, smooth=False)

    # -------------------------------------------------------------- faces
    @staticmethod
    def surface_y(head, dx, dz):
        """front of the ellipsoid head = (centre, scale) at offsets dx, dz"""
        (hx, hy, hz), (a, b, c) = head
        return hy - b * math.sqrt(max(0.05, 1 - (dx / a) ** 2 - (dz / c) ** 2))

    def eye(self, name, head, dx, dz, r, look=(0, 0), pupil=0.45):
        """a googly eye on the front of the head; look = (x, z) of the pupil"""
        (hx, hy, hz), _ = head
        x, z = hx + dx, hz + dz
        y = self.surface_y(head, dx, dz) + r * 0.15
        self.sphere(name, (x, y, z), (r, r * 0.55, r * 1.15), "white")
        self.sphere(name + "_p", (x + look[0] * r * 0.45, y - r * 0.45, z + look[1] * r * 0.45),
                    (r * pupil, r * 0.25, r * pupil * 1.1), "black")

    def face(self, p, head, eye_r=0.16, look=(0, 0), smile=0.2, nose=True, open_mouth=False):
        (hx, hy, hz), (a, b, c) = head
        self.eye(p + "_eye_l", head, -a * 0.33, c * 0.22, eye_r, look)
        self.eye(p + "_eye_r", head, a * 0.33, c * 0.22, eye_r, look)
        if nose:
            self.sphere(p + "_nose", (hx, self.surface_y(head, 0, -0.05) - 0.06, hz - c * 0.05),
                        (a * 0.22, a * 0.22, a * 0.24), "skin")
        my = self.surface_y(head, 0, -c * 0.45)
        if open_mouth:
            self.sphere(p + "_mouth", (hx, my, hz - c * 0.45), (a * 0.22, 0.06, c * 0.18), "red")
        elif smile:
            self.torus(p + "_smile", (hx, my - 0.02, hz - c * 0.38), smile, 0.035, "black",
                       rot=(R(90), 0, 0), half=True)

    # -------------------------------------------------------------- villagers
    def cretan(self, p, x, y, z0=0.0, look=(0, 0), beard=False, glass=False, sariki=True):
        """black shirt, red sash, handlebar moustache, the sariki with its fringe"""
        self.cyl(p + "_body", (x, y, z0 + 1.1), 0.55, 1.2, "black", r2=0.62)
        self.cyl(p + "_sash", (x, y, z0 + 0.65), 0.58, 0.2, "red")
        head = ((x, y - 0.05, z0 + 2.25), (0.66, 0.6, 0.68))
        self.sphere(p + "_head", *head, "skin")
        self.face(p, head, 0.2, look, smile=0)
        for sd in (-1, 1):
            self.box(p + "_brow%d" % sd, (x + sd * 0.23, self.surface_y(head, sd * 0.23, 0.36) - 0.07,
                                          z0 + 2.62), (0.3, 0.07, 0.08), "black", rot=(0, R(sd * 12), 0))
        my = self.surface_y(head, 0, -0.27) - 0.06
        for sd in (-1, 1):
            self.sphere(p + "_mous%d" % sd, (x + sd * 0.26, my, z0 + 2.0), (0.3, 0.1, 0.1), "black",
                        rot=(0, R(sd * 18), 0))
            self.sphere(p + "_curl%d" % sd, (x + sd * 0.54, my + 0.05, z0 + 2.12), (0.09, 0.09, 0.14),
                        "black")
        if beard:
            self.sphere(p + "_beard", (x, my + 0.1, z0 + 1.72), (0.42, 0.25, 0.32), "black")
        else:
            self.torus(p + "_smile", (x, self.surface_y(head, 0, -0.42) - 0.02, z0 + 1.92), 0.16,
                       0.035, "black", rot=(R(90), 0, 0), half=True)
        if sariki:
            self.sphere(p + "_sariki", (x, y - 0.02, z0 + 2.62), (0.7, 0.64, 0.38), "black")
            for k in range(14):
                a = math.pi + k * math.pi / 13
                self.sphere(p + "_fr%d" % k, (x + math.cos(a) * 0.68, y - math.sin(a) * 0.6 - 0.05,
                                              z0 + 2.5), (0.06, 0.06, 0.06), "black")
        if glass:
            self.raised_glass(p, x + 0.55, y - 0.45, z0 + 1.6)
        return head

    def raised_glass(self, p, x, y, z):
        """an arm up, holding a glass of red wine: a toast"""
        self.cyl(p + "_arm", (x, y + 0.2, z + 0.1), 0.12, 0.9, "black", rot=(R(-20), R(-25), 0))
        self.sphere(p + "_hand", (x + 0.15, y - 0.05, z + 0.55), (0.13, 0.13, 0.13), "skin")
        self.cyl(p + "_glass", (x + 0.15, y - 0.12, z + 0.8), 0.11, 0.32, "glass", r2=0.13)
        self.cyl(p + "_wine", (x + 0.15, y - 0.12, z + 0.75), 0.1, 0.18, "wine")

    def yiayia(self, p, x, y, z0=0.0, look=(0, 0)):
        self.cyl(p + "_body", (x, y + 0.1, z0 + 1.0), 0.62, 1.3, "black", r2=0.42)
        head = ((x, y - 0.05, z0 + 2.05), (0.56, 0.52, 0.58))
        self.sphere(p + "_head", *head, "skin")
        self.sphere(p + "_scarf", (x, y + 0.2, z0 + 2.25), (0.66, 0.58, 0.62), "black")
        self.face(p, head, 0.12, look, smile=0.17)
        for sd in (-1, 1):
            self.torus(p + "_glass%d" % sd, (x + sd * 0.19, self.surface_y(head, sd * 0.19, 0.13) - 0.1,
                                              z0 + 2.18), 0.15, 0.022, "dark", rot=(R(90), 0, 0))
        for sd in (-1, 1):     # rosy cheeks
            self.sphere(p + "_cheek%d" % sd, (x + sd * 0.3, self.surface_y(head, sd * 0.3, -0.12) - 0.01,
                                               z0 + 1.93), (0.1, 0.03, 0.07), "pink")
        return head

    def bride(self, p, x, y, z0=0.0, look=(0, 0)):
        self.cyl(p + "_body", (x, y, z0 + 1.05), 0.6, 1.2, "white", r2=0.4)
        head = ((x, y - 0.05, z0 + 2.1), (0.56, 0.52, 0.6))
        self.sphere(p + "_hair", (x, y + 0.12, z0 + 2.25), (0.62, 0.55, 0.62), "hair")
        self.sphere(p + "_head", *head, "skin")
        self.face(p, head, 0.14, look, smile=0.16)
        self.sphere(p + "_lips", (x, self.surface_y(head, 0, -0.3) - 0.01, z0 + 1.82), (0.09, 0.03, 0.05),
                    "red")
        self.cyl(p + "_veil", (x, y + 0.35, z0 + 1.6), 0.25, 1.6, "white", r2=0.85,
                 rot=(R(180 - 12), 0, 0))
        for k in range(7):     # a crown of little flowers
            a = math.pi + k * math.pi / 6
            self.sphere(p + "_fl%d" % k, (x + math.cos(a) * 0.5, y - math.sin(a) * 0.45 + 0.02,
                                          z0 + 2.55), (0.09, 0.09, 0.09), "pink" if k % 2 else "white")
        return head

    def baker(self, p, x, y, z0=0.0, look=(0, 0)):
        self.cyl(p + "_body", (x, y, z0 + 1.1), 0.6, 1.2, "white", r2=0.6)
        self.box(p + "_apron", (x, y - 0.58, z0 + 0.9), (0.7, 0.04, 0.8), "cream")
        head = ((x, y - 0.05, z0 + 2.2), (0.64, 0.58, 0.64))
        self.sphere(p + "_head", *head, "skin")
        self.face(p, head, 0.15, look, smile=0.18)
        for sd in (-1, 1):
            self.sphere(p + "_mous%d" % sd, (x + sd * 0.17, self.surface_y(head, sd * 0.17, -0.22) - 0.05,
                                              z0 + 1.98), (0.18, 0.08, 0.07), "hair")
        self.cyl(p + "_hat", (x, y, z0 + 2.85), 0.42, 0.55, "white")
        self.sphere(p + "_puff", (x, y, z0 + 3.2), (0.6, 0.55, 0.32), "white")
        # holding up a ring of bread
        self.torus(p + "_koulouri", (x + 0.7, y - 0.5, z0 + 1.75), 0.24, 0.09, "bread",
                   rot=(R(90), 0, 0))
        self.sphere(p + "_hand", (x + 0.7, y - 0.45, z0 + 1.5), (0.13, 0.13, 0.13), "skin")
        return head

    def priest(self, p, x, y, z0=0.0, look=(0, 0)):
        self.cyl(p + "_body", (x, y, z0 + 1.1), 0.62, 1.2, "black", r2=0.55)
        head = ((x, y - 0.05, z0 + 2.2), (0.6, 0.56, 0.62))
        self.sphere(p + "_head", *head, "skin")
        self.face(p, head, 0.14, look, smile=0)
        self.cyl(p + "_beard", (x, self.surface_y(head, 0, -0.3) + 0.05, z0 + 1.55), 0.42, 0.95, "silver",
                 r2=0.08, rot=(R(180 + 8), 0, 0))
        for sd in (-1, 1):
            self.sphere(p + "_mous%d" % sd, (x + sd * 0.16, self.surface_y(head, sd * 0.16, -0.2) - 0.06,
                                              z0 + 2.0), (0.2, 0.08, 0.08), "silver")
        self.torus(p + "_smile", (x, self.surface_y(head, 0, -0.36) - 0.09, z0 + 1.9), 0.12, 0.03,
                   "black", rot=(R(90), 0, 0), half=True)
        self.cyl(p + "_hat", (x, y, z0 + 2.95), 0.5, 0.75, "black", r2=0.56)    # the kalimafki
        self.cyl(p + "_brim", (x, y, z0 + 3.33), 0.62, 0.06, "black")
        # a cross held up in blessing
        self.box(p + "_cross_v", (x - 0.75, y - 0.5, z0 + 2.0), (0.07, 0.07, 0.5), "yellow")
        self.box(p + "_cross_h", (x - 0.75, y - 0.5, z0 + 2.08), (0.3, 0.07, 0.07), "yellow")
        self.sphere(p + "_hand", (x - 0.75, y - 0.45, z0 + 1.72), (0.13, 0.13, 0.13), "skin")
        return head

    def psssst(self, p, x, y, z, look=(0, 0), sariki=True):
        head = ((x, y, z), (0.62, 0.55, 0.45))
        self.sphere(p + "_body", *head, "yellow")
        self.eye(p + "_eye_l", head, -0.2, 0.05, 0.16, look)
        self.eye(p + "_eye_r", head, 0.2, 0.05, 0.16, look)
        self.torus(p + "_smile", (x, self.surface_y(head, 0, -0.15) - 0.02, z - 0.12), 0.18, 0.04,
                   "black", rot=(R(90), 0, 0), half=True)
        if sariki:
            self.sphere(p + "_sariki", (x, y, z + 0.35), (0.6, 0.52, 0.25), "black")
        for s in (-1, 1):
            self.box(p + "_arm%d" % s, (x + s * 0.75, y, z + 0.2), (0.6, 0.1, 0.08), "dark")
            self.cyl(p + "_rotor%d" % s, (x + s * 1.05, y, z + 0.32), 0.4, 0.04, "cyan")
        return head

    # -------------------------------------------------------------- light, camera, render
    def camera(self, loc, rot, lens=28, shift_y=0.0, sun_rot=(R(50), R(10), R(-25))):
        bpy.ops.object.light_add(type="SUN", location=(0, -10, 10), rotation=sun_rot)
        self.put(bpy.context.object).data.energy = 3
        bpy.ops.object.camera_add(location=loc, rotation=rot)
        cam = self.put(bpy.context.object)
        cam.data.lens = lens
        cam.data.shift_y = shift_y
        self.sc.camera = cam
        return cam

    def render(self, path):
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
