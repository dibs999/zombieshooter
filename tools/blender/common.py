"""Shared Blender 4.2 modeling, procedural bmesh, material, UV, rigging, and glTF export helpers."""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BLEND_DIR = os.path.join(REPO_ROOT, "assets_src", "blend")
MODELS_DIR = os.path.join(REPO_ROOT, "assets", "models")
TEX_DIR = os.path.join(REPO_ROOT, "assets", "textures")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear_val(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def srgb_to_linear_col(col):
    if len(col) == 4:
        return (srgb_to_linear_val(col[0]), srgb_to_linear_val(col[1]), srgb_to_linear_val(col[2]), col[3])
    return (srgb_to_linear_val(col[0]), srgb_to_linear_val(col[1]), srgb_to_linear_val(col[2]))


def make_pbr_mat(
    name,
    base_color=(0.5, 0.5, 0.5, 1.0),
    metallic=0.0,
    roughness=0.5,
    emission=None,
    emission_strength=0.0,
    albedo_tex=None,
    normal_tex=None,
    roughness_tex=None,
    srgb=True,
    alpha=1.0,
    tint_tex=None,
    normal_strength=0.65,
    specular=None,
    emissive_albedo=False,
):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bc = srgb_to_linear_col(base_color) if srgb else base_color
    bsdf.inputs["Base Color"].default_value = bc
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if specular is not None and "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    if alpha < 0.999:
        mat.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = alpha
    if emission is not None and emission_strength > 0.0:
        ec = srgb_to_linear_col(emission[:3]) if srgb else emission[:3]
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    elif emissive_albedo and emission_strength > 0.0:
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    if albedo_tex and os.path.exists(albedo_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(albedo_tex, check_existing=True)
        if tint_tex is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            tc = srgb_to_linear_col(tint_tex[:3]) if srgb else tint_tex[:3]
            mix.inputs["B"].default_value = (*tc, 1.0)
            nt.links.new(tex.outputs["Color"], mix.inputs["A"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
            if emissive_albedo:
                nt.links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            if emissive_albedo:
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])

    if roughness_tex and os.path.exists(roughness_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(roughness_tex, check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])

    if normal_tex and os.path.exists(normal_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(normal_tex, check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal_strength
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def assign_mat(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def smooth_shade(obj, auto_angle_deg=38.0):
    if obj.type != "MESH":
        return
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    angle = math.radians(auto_angle_deg)
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            if edge.link_faces[0].normal.angle(edge.link_faces[1].normal, 0.0) > angle:
                edge.smooth = False
            else:
                edge.smooth = True
    bm.to_mesh(obj.data)
    bm.free()


def uv_box_project(obj, scale=2.0):
    """Fast metric triplanar box UV projection directly in bmesh without mode switching."""
    if obj.type != "MESH":
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            co = loop.vert.co
            if az >= ax and az >= ay:
                loop[uv_layer].uv = (co.x * scale, co.y * scale)
            elif ay >= ax:
                loop[uv_layer].uv = (co.x * scale, co.z * scale)
            else:
                loop[uv_layer].uv = (co.y * scale, co.z * scale)
    bm.to_mesh(obj.data)
    bm.free()


def add_bevel(obj, width=0.004, segments=2):
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)
    return mod


def _finish_mesh_obj(name, bm, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, smooth_angle=42.0, uv_scale=2.0):
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj, smooth_angle)
    return obj


def add_box(name, size=(0.1, 0.1, 0.1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.003, uv_scale=2.5):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        add_bevel(obj, width=bevel, segments=2)
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj)
    return obj


def add_cyl(name, radius=0.02, depth=0.2, loc=(0, 0, 0), rot=(0, 0, 0), vertices=20, mat=None, bevel=0.0015, uv_scale=3.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if bevel > 0.0:
        add_bevel(obj, width=bevel, segments=1)
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj)
    return obj


def add_sphere(name, radius=0.05, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), segments=18, rings=12, mat=None, uv_scale=2.5):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj, 60.0)
    return obj


def add_cone(name, r1=0.04, r2=0.0, depth=0.1, loc=(0, 0, 0), rot=(0, 0, 0), vertices=14, mat=None, uv_scale=2.5):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj)
    return obj


def add_torus(name, major=0.05, minor=0.01, loc=(0, 0, 0), rot=(0, 0, 0), major_segments=24, minor_segments=10, mat=None, uv_scale=3.0):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major,
        minor_radius=minor,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_mat(obj, mat)
    uv_box_project(obj, scale=uv_scale)
    smooth_shade(obj, 60.0)
    return obj


def add_ring_loft(name, rings, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, cap_start=True, cap_end=True, smooth_angle=52.0, uv_scale=2.5):
    """Loft a closed surface through a sequence of equal-length 3D vertex loops."""
    bm = bmesh.new()
    loops = []
    for ring in rings:
        loops.append([bm.verts.new(p) for p in ring])
    n = len(loops[0])
    for i in range(len(loops) - 1):
        r0, r1 = loops[i], loops[i + 1]
        for j in range(n):
            jn = (j + 1) % n
            bm.faces.new((r0[j], r0[jn], r1[jn], r1[j]))
    if cap_start and len(loops[0]) >= 3:
        bm.faces.new(list(reversed(loops[0])))
    if cap_end and len(loops[-1]) >= 3:
        bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh_obj(name, bm, loc=loc, rot=rot, mat=mat, smooth_angle=smooth_angle, uv_scale=uv_scale)


def add_extruded_poly(name, poly_2d, depth=0.02, plane="YZ", loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.002, uv_scale=3.0):
    """Extrude a 2D polygon cleanly in YZ (gun side profile), XY, or XZ with optional bevel."""
    bm = bmesh.new()
    half = depth * 0.5
    front = []
    back = []
    for a, b in poly_2d:
        if plane == "YZ":
            front.append(bm.verts.new((half, a, b)))
            back.append(bm.verts.new((-half, a, b)))
        elif plane == "XZ":
            front.append(bm.verts.new((a, half, b)))
            back.append(bm.verts.new((a, -half, b)))
        else:
            front.append(bm.verts.new((a, b, half)))
            back.append(bm.verts.new((a, b, -half)))

    n = len(poly_2d)
    for i in range(n):
        inext = (i + 1) % n
        bm.faces.new((front[i], front[inext], back[inext], back[i]))
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _finish_mesh_obj(name, bm, loc=loc, rot=rot, mat=mat, smooth_angle=35.0, uv_scale=uv_scale)
    if bevel > 0.0:
        add_bevel(obj, width=bevel, segments=2)
    return obj


def add_tube_pipe(name, points, radius=0.01, segments=12, mat=None, cap=True, radii=None, smooth_angle=60.0, uv_scale=3.5):
    """Sweep a smooth circular tube along a 3D point polyline using parallel transport."""
    if len(points) < 2:
        return None
    pts = [Vector(p) for p in points]
    rings = []
    prev_n = None
    for idx, p in enumerate(pts):
        if idx == 0:
            tangent = (pts[1] - pts[0]).normalized()
        elif idx == len(pts) - 1:
            tangent = (pts[-1] - pts[-2]).normalized()
        else:
            t1 = (pts[idx] - pts[idx - 1]).normalized()
            t2 = (pts[idx + 1] - pts[idx]).normalized()
            tangent = (t1 + t2)
            tangent = tangent.normalized() if tangent.length > 1e-5 else t2

        if prev_n is None:
            up = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
            n = tangent.cross(up).normalized()
        else:
            n = (prev_n - tangent * prev_n.dot(tangent))
            if n.length < 1e-5:
                up = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
                n = tangent.cross(up).normalized()
            else:
                n.normalize()
        prev_n = n
        b = tangent.cross(n).normalized()
        r = radii[idx] if radii is not None else radius
        ring = []
        for s in range(segments):
            ang = (s / segments) * 2.0 * math.pi
            ring.append(p + (n * math.cos(ang) + b * math.sin(ang)) * r)
        rings.append(ring)
    return add_ring_loft(name, rings, mat=mat, cap_start=cap, cap_end=cap, smooth_angle=smooth_angle, uv_scale=uv_scale)


def add_hollow_barrel(name, r_outer=0.012, r_inner=0.0085, length=0.35, loc=(0, 0, 0), rot=(0, 0, 0), segments=22, mat=None, bore_mat=None):
    """Build a thick-walled open cylindrical barrel (outer jacket + chamfered crown + deep inner bore) along local +Y."""
    bm = bmesh.new()
    hy = length * 0.5
    crown_y = hy - min(0.006, length * 0.08)
    bore_back_y = -hy + min(0.02, length * 0.2)

    ro_b, ro_m, ro_f = [], [], []
    ri_f, ri_b = [], []
    for s in range(segments):
        ang = (s / segments) * 2.0 * math.pi
        cx, cz = math.cos(ang), math.sin(ang)
        ro_b.append(bm.verts.new((cx * r_outer, -hy, cz * r_outer)))
        ro_m.append(bm.verts.new((cx * r_outer, crown_y, cz * r_outer)))
        rm = (r_outer + r_inner) * 0.5
        ro_f.append(bm.verts.new((cx * (r_outer * 0.88 + r_inner * 0.12), hy, cz * (r_outer * 0.88 + r_inner * 0.12))))
        ri_f.append(bm.verts.new((cx * r_inner, hy - 0.002, cz * r_inner)))
        ri_b.append(bm.verts.new((cx * r_inner, bore_back_y, cz * r_inner)))

    for s in range(segments):
        sn = (s + 1) % segments
        f1 = bm.faces.new((ro_b[s], ro_b[sn], ro_m[sn], ro_m[s]))
        f2 = bm.faces.new((ro_m[s], ro_m[sn], ro_f[sn], ro_f[s]))
        f3 = bm.faces.new((ro_f[s], ro_f[sn], ri_f[sn], ri_f[s]))
        f4 = bm.faces.new((ri_f[s], ri_f[sn], ri_b[sn], ri_b[s]))
        if bore_mat is not None:
            f4.material_index = 1
    bm.faces.new(list(reversed(ro_b)))
    fcap = bm.faces.new(ri_b)
    if bore_mat is not None:
        fcap.material_index = 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _finish_mesh_obj(name, bm, loc=loc, rot=rot, mat=mat, smooth_angle=48.0, uv_scale=4.0)
    if bore_mat is not None:
        obj.data.materials.append(bore_mat)
    return obj


def add_coil_spring(name, major_r=0.04, wire_r=0.007, length=0.18, turns=5.5, steps_per_turn=14, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    """Create a 3D helical heating/tesla coil oriented along local +Y."""
    pts = []
    total = int(turns * steps_per_turn) + 1
    for i in range(total):
        t = i / max(1, total - 1)
        ang = t * turns * 2.0 * math.pi
        pts.append((math.cos(ang) * major_r, -length * 0.5 + t * length, math.sin(ang) * major_r))
    obj = add_tube_pipe(name, pts, radius=wire_r, segments=8, mat=mat, cap=True)
    if obj:
        obj.location = loc
        obj.rotation_euler = rot
    return obj


def add_gear(name, teeth=16, r_outer=0.14, r_root=0.116, r_bore=0.028, thickness=0.024, spokes=5, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    """Build a detailed mechanical spur gear aligned along local Y axis."""
    parts = []
    bm = bmesh.new()
    ht = thickness * 0.5
    front_ring = []
    back_ring = []
    pts_per_tooth = 4
    total_pts = teeth * pts_per_tooth
    for i in range(teeth):
        a0 = (i / teeth) * 2.0 * math.pi
        da = (2.0 * math.pi / teeth)
        angles = [a0, a0 + da * 0.16, a0 + da * 0.34, a0 + da * 0.50]
        radii = [r_root, r_outer, r_outer, r_root]
        for ang, rr in zip(angles, radii):
            front_ring.append(bm.verts.new((math.cos(ang) * rr, ht, math.sin(ang) * rr)))
            back_ring.append(bm.verts.new((math.cos(ang) * rr, -ht, math.sin(ang) * rr)))

    inner_f = []
    inner_b = []
    r_inner_rim = max(r_bore + 0.012, r_root * 0.72)
    for k in range(total_pts):
        ang = (k / total_pts) * 2.0 * math.pi
        inner_f.append(bm.verts.new((math.cos(ang) * r_inner_rim, ht, math.sin(ang) * r_inner_rim)))
        inner_b.append(bm.verts.new((math.cos(ang) * r_inner_rim, -ht, math.sin(ang) * r_inner_rim)))

    for k in range(total_pts):
        kn = (k + 1) % total_pts
        bm.faces.new((front_ring[k], front_ring[kn], back_ring[kn], back_ring[k]))
        bm.faces.new((inner_f[k], front_ring[k], front_ring[kn], inner_f[kn]))
        bm.faces.new((inner_b[kn], back_ring[kn], back_ring[k], inner_b[k]))
        bm.faces.new((inner_b[k], inner_b[kn], inner_f[kn], inner_f[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rim = _finish_mesh_obj(f"{name}_Rim", bm, mat=mat, smooth_angle=35.0, uv_scale=3.0)
    parts.append(rim)

    hub = add_cyl(f"{name}_Hub", r_bore * 1.45, thickness * 1.4, (0, 0, 0), (math.radians(90), 0, 0), vertices=14, mat=mat)
    parts.append(hub)
    spoke_len = r_inner_rim - r_bore * 0.6
    for s in range(spokes):
        ang = (s / spokes) * 2.0 * math.pi
        mid_r = r_bore * 0.8 + spoke_len * 0.5
        sp = add_box(
            f"{name}_Spoke{s}",
            (spoke_len, thickness * 0.55, max(0.014, r_outer * 0.14)),
            (math.cos(ang) * mid_r, 0, math.sin(ang) * mid_r),
            (0, -ang, 0),
            mat=mat,
            bevel=0.001,
        )
        parts.append(sp)
    joined = join_objects(parts, name, apply_uv=False)
    joined.location = loc
    joined.rotation_euler = rot
    return joined


def add_chain(name, points, link_len=0.068, link_w=0.036, wire_r=0.007, mat=None):
    """Build interlocking 3D metal chain links along a polyline."""
    if len(points) < 2:
        return None
    links = []
    idx = 0
    for i in range(len(points) - 1):
        p0 = Vector(points[i])
        p1 = Vector(points[i + 1])
        seg = p1 - p0
        d = seg.length
        if d < 1e-4:
            continue
        tangent = seg.normalized()
        step = link_len * 0.68
        count = max(1, int(d / step))
        q_rot = tangent.to_track_quat("Y", "Z").to_euler()
        for k in range(count):
            t = (k + 0.5) / count
            pos = p0.lerp(p1, t)
            lk = add_torus(f"{name}_L{idx}", link_w * 0.5, wire_r, major_segments=14, minor_segments=7, mat=mat)
            lk.scale = (0.72, 1.38, 1.0)
            bpy.context.view_layer.objects.active = lk
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            lk.location = pos
            lk.rotation_euler = q_rot
            if idx % 2 == 1:
                m_rot = Matrix.Rotation(math.pi * 0.5, 4, tangent)
                lk.matrix_world = Matrix.Translation(pos) @ m_rot @ q_rot.to_matrix().to_4x4()
            links.append(lk)
            idx += 1
    return join_objects(links, name, apply_uv=False) if links else None


def add_vented_shroud(name, r_outer=0.020, thickness=0.0035, length=0.22, bands=7, struts=6, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    """Build a genuine see-through perforated heatshield along local +Y using axial ribs and band rings."""
    parts = []
    ring_w = (length / bands) * 0.42
    for i in range(bands):
        y = -length * 0.5 + (i + 0.5) * (length / bands)
        bm = bmesh.new()
        segs = 20
        r_in = r_outer - thickness
        vo_f, vo_b, vi_f, vi_b = [], [], [], []
        for s in range(segs):
            ang = (s / segs) * 2.0 * math.pi
            cx, cz = math.cos(ang), math.sin(ang)
            vo_f.append(bm.verts.new((cx * r_outer, y + ring_w * 0.5, cz * r_outer)))
            vo_b.append(bm.verts.new((cx * r_outer, y - ring_w * 0.5, cz * r_outer)))
            vi_f.append(bm.verts.new((cx * r_in, y + ring_w * 0.5, cz * r_in)))
            vi_b.append(bm.verts.new((cx * r_in, y - ring_w * 0.5, cz * r_in)))
        for s in range(segs):
            sn = (s + 1) % segs
            bm.faces.new((vo_b[s], vo_b[sn], vo_f[sn], vo_f[s]))
            bm.faces.new((vi_f[s], vi_f[sn], vi_b[sn], vi_b[s]))
            bm.faces.new((vo_f[s], vo_f[sn], vi_f[sn], vi_f[s]))
            bm.faces.new((vi_b[s], vi_b[sn], vo_b[sn], vo_b[s]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(_finish_mesh_obj(f"{name}_R{i}", bm, mat=mat, smooth_angle=45.0, uv_scale=4.0))

    r_mid = r_outer - thickness * 0.5
    strut_t = thickness * 1.15
    strut_w = max(0.004, (2.0 * math.pi * r_outer / struts) * 0.28)
    for s in range(struts):
        ang = (s / struts) * 2.0 * math.pi
        st = add_box(
            f"{name}_S{s}",
            (strut_t, length, strut_w),
            (math.cos(ang) * r_mid, 0, math.sin(ang) * r_mid),
            (0, -ang, 0),
            mat=mat,
            bevel=0.0,
            uv_scale=4.0,
        )
        parts.append(st)
    joined = join_objects(parts, name, apply_uv=False)
    joined.location = loc
    joined.rotation_euler = rot
    return joined


def add_lathe(name, profile_rz, segments=22, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, smooth_angle=52.0, uv_scale=3.0):
    """Revolve a 2D (radius, z) profile cleanly around local +Z."""
    rings = []
    for r, z in profile_rz:
        rr = max(0.001, r)
        ring = []
        for s in range(segments):
            ang = (s / segments) * 2.0 * math.pi
            ring.append((math.cos(ang) * rr, math.sin(ang) * rr, z))
        rings.append(ring)
    return add_ring_loft(name, rings, loc=loc, rot=rot, mat=mat, smooth_angle=smooth_angle, uv_scale=uv_scale)


def add_textured_plane(name, width, height, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    """Create a Quad facing -Y with exact [0, 1] UV mapping (do NOT apply box UV projection)."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=(math.radians(90) + rot[0], rot[1], rot[2]))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (width, height, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        assign_mat(obj, mat)
    return obj


def add_textured_disc(name, radius, vertices=28, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    """Create a circular disc facing -Y with exact planar [0..1] UV coordinates."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    center = bm.verts.new((0.0, 0.0, 0.0))
    rim = []
    coords = []
    for i in range(vertices):
        ang = (i / vertices) * 2.0 * math.pi
        cx, cz = math.cos(ang), math.sin(ang)
        rim.append(bm.verts.new((cx * radius, 0.0, cz * radius)))
        coords.append((0.5 + 0.5 * cx, 0.5 + 0.5 * cz))
    for i in range(vertices):
        inext = (i + 1) % vertices
        f = bm.faces.new((center, rim[inext], rim[i]))
        f.loops[0][uv_layer].uv = (0.5, 0.5)
        f.loops[1][uv_layer].uv = coords[inext]
        f.loops[2][uv_layer].uv = coords[i]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj, 45.0)
    return obj


def auto_uv_box(obj):
    if obj.type != "MESH":
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def join_objects(objs, final_name, apply_uv=False):
    bpy.ops.object.select_all(action="DESELECT")
    valid = [o for o in objs if o is not None and o.type == "MESH"]
    if not valid:
        return None
    for o in valid:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    if len(valid) > 1:
        bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = final_name
    if apply_uv:
        auto_uv_box(joined)
    return joined


def export_asset(sub_folder, asset_name, export_anims=False):
    blend_folder = os.path.join(BLEND_DIR, sub_folder)
    model_folder = os.path.join(MODELS_DIR, sub_folder)
    os.makedirs(blend_folder, exist_ok=True)
    os.makedirs(model_folder, exist_ok=True)

    blend_path = os.path.join(blend_folder, f"{asset_name}.blend")
    glb_path = os.path.join(model_folder, f"{asset_name}.glb")

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_animations=export_anims,
        export_nla_strips=export_anims,
        export_draco_mesh_compression_enable=False,
    )
    print(f"[BLENDER] Exported {asset_name} -> {glb_path}")
