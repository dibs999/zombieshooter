"""Build all 11 high-detail CC0-textured & animatable-part weapons for BUNKER 115 v2.

Features:
- Uses CC0 Poly Haven scanned bolt-action rifle (bolt_action_rifle_7_62) cleaned, aligned,
  split with animatable Bolt & Trigger, scope lens enhanced, and decimated <= 12k tris for kar98k.glb.
- Rebuilds all 9 procedural+CC0 PBR weapons (m1911, m14, trench_shotgun, mp40, stg44, mg42,
  raygun, combat_knife, frag_grenade) <= 15k tris each with refined ergonomics & hollow bores.
- Adds NEW Wonder Weapon: wunderwaffe.glb (Wunderwaffe DG-2) <= 15k tris with brass/copper Tesla
  coils, 3 glowing cyan glass VacuumTubes, detachable glowing Magazine bulb, 3-prong emitter muzzle!
- Keeps movable child parts (Slide, Bolt, Magazine, Pump, Drum, FeedCover, PlasmaCells,
  VacuumTubes, Trigger) as separate child Mesh objects inside each .glb so weapon_controller.gd
  can animate blowback, bolt lift/pull, pump action, mag drop/insert, and glowing cells/tubes!

Coordinate convention:
  Blender +Y = forward toward muzzle (exports to Godot -Z)
  Blender +Z = up (exports to Godot +Y)
  Blender +X = right (exports to Godot +X)
Origin (0, 0, 0) = player right-hand grip center.
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C

KAR98K_CC0_GLTF = "/tmp/cc0_cache/wpn/rifle/bolt_action_rifle_7_62_1k.gltf"


def count_scene_tris():
    total = 0
    for o in bpy.data.objects:
        if o.type == "MESH":
            total += sum(max(1, len(p.vertices) - 2) for p in o.data.polygons)
    return total


def _apply_mods_and_freeze(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def _join_named(parts, name, uv_scale=10.0, pivot=(0.0, 0.0, 0.0), apply_uv=True):
    valid = [p for p in parts if p is not None and p.type == "MESH"]
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
    joined.name = name
    if any(abs(v) > 1e-6 for v in pivot):
        px, py, pz = pivot
        for v in joined.data.vertices:
            v.co.x -= px
            v.co.y -= py
            v.co.z -= pz
        joined.data.update()
        joined.location = pivot
    else:
        joined.location = (0.0, 0.0, 0.0)
    if apply_uv:
        C.uv_box_project(joined, scale=uv_scale)
    return joined


def _export_weapon_scene(sub_folder, asset_name, max_tris=15000):
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(bpy.data.objects):
        if o.type == "MESH" and len(o.data.polygons) == 0:
            bpy.data.objects.remove(o, do_unlink=True)
    tris = count_scene_tris()
    names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
    print(f"[WPN] {asset_name}: total_tris={tris} nodes={names}")
    if tris > max_tris:
        raise RuntimeError(f"{asset_name} exceeded tri limit: {tris} > {max_tris}")
    C.export_asset(sub_folder, asset_name)


def weapon_mats():
    wtex = os.path.join(C.TEX_DIR, "weapons")

    gunmetal = C.make_pbr_mat(
        "Gunmetal",
        (0.20, 0.22, 0.26, 1.0),
        metallic=0.88,
        roughness=0.28,
        albedo_tex=os.path.join(wtex, "gun_steel_albedo.png"),
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        roughness_tex=os.path.join(wtex, "gun_steel_roughness.png"),
        tint_tex=(0.88, 0.92, 1.00),
        normal_strength=0.22,
    )
    dark_steel = C.make_pbr_mat(
        "DarkSteel",
        (0.10, 0.11, 0.13, 1.0),
        metallic=0.90,
        roughness=0.25,
        albedo_tex=os.path.join(wtex, "dark_steel_albedo.jpg"),
        normal_tex=os.path.join(wtex, "dark_steel_normal.jpg"),
        roughness_tex=os.path.join(wtex, "dark_steel_roughness.jpg"),
        tint_tex=(0.56, 0.58, 0.64),
        normal_strength=0.24,
    )
    chrome = C.make_pbr_mat(
        "Chrome",
        (0.76, 0.78, 0.82, 1.0),
        metallic=0.95,
        roughness=0.14,
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        normal_strength=0.12,
    )
    bore_dark = C.make_pbr_mat("BoreDark", (0.015, 0.015, 0.018, 1.0), metallic=0.10, roughness=0.92)
    walnut = C.make_pbr_mat(
        "WalnutWood",
        (0.28, 0.13, 0.06, 1.0),
        metallic=0.0,
        roughness=0.46,
        albedo_tex=os.path.join(wtex, "walnut_albedo.png"),
        normal_tex=os.path.join(wtex, "walnut_normal.png"),
        roughness_tex=os.path.join(wtex, "walnut_roughness.png"),
        normal_strength=0.30,
    )
    wunder_wood = C.make_pbr_mat(
        "WunderWalnut",
        (0.22, 0.10, 0.05, 1.0),
        metallic=0.0,
        roughness=0.44,
        albedo_tex=os.path.join(wtex, "wunderwaffe_wood_albedo.jpg"),
        normal_tex=os.path.join(wtex, "wunderwaffe_wood_normal.jpg"),
        roughness_tex=os.path.join(wtex, "wunderwaffe_wood_roughness.jpg"),
        tint_tex=(0.76, 0.66, 0.58),
        normal_strength=0.36,
    )
    bakelite = C.make_pbr_mat(
        "Bakelite",
        (0.18, 0.07, 0.04, 1.0),
        metallic=0.03,
        roughness=0.42,
        albedo_tex=os.path.join(wtex, "bakelite_albedo.png"),
        normal_tex=os.path.join(wtex, "bakelite_normal.png"),
        roughness_tex=os.path.join(wtex, "bakelite_roughness.png"),
        normal_strength=0.40,
    )
    brass = C.make_pbr_mat(
        "Brass",
        (0.52, 0.36, 0.14, 1.0),
        metallic=0.88,
        roughness=0.30,
        albedo_tex=os.path.join(wtex, "brass_albedo.png"),
        normal_tex=os.path.join(wtex, "brass_normal.png"),
        roughness_tex=os.path.join(wtex, "brass_roughness.png"),
        tint_tex=(0.78, 0.70, 0.60),
        normal_strength=0.22,
    )
    copper = C.make_pbr_mat(
        "Copper",
        (0.60, 0.25, 0.11, 1.0),
        metallic=0.90,
        roughness=0.26,
        albedo_tex=os.path.join(wtex, "copper_albedo.jpg"),
        normal_tex=os.path.join(wtex, "copper_normal.jpg"),
        roughness_tex=os.path.join(wtex, "copper_roughness.jpg"),
        tint_tex=(0.88, 0.68, 0.54),
        normal_strength=0.24,
    )
    ray_red = C.make_pbr_mat(
        "RayGunRed",
        (0.48, 0.045, 0.038, 1.0),
        metallic=0.38,
        roughness=0.26,
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        normal_strength=0.16,
    )
    leather = C.make_pbr_mat(
        "KnifeLeather",
        (0.16, 0.12, 0.09, 1.0),
        metallic=0.04,
        roughness=0.60,
        albedo_tex=os.path.join(wtex, "fp_leather_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_leather_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_leather_roughness.png"),
        normal_strength=0.28,
    )
    tritium = C.make_pbr_mat(
        "TritiumSight",
        (0.14, 1.0, 0.48, 1.0),
        metallic=0.0,
        roughness=0.15,
        emission=(0.14, 1.0, 0.48),
        emission_strength=2.3,
    )
    optic_lens = C.make_pbr_mat(
        "OpticLens",
        (0.05, 0.22, 0.30, 1.0),
        metallic=0.20,
        roughness=0.06,
        emission=(0.05, 0.22, 0.30),
        emission_strength=0.55,
    )
    plasma_orange = C.make_pbr_mat(
        "PlasmaOrange",
        (1.0, 0.48, 0.06, 1.0),
        metallic=0.06,
        roughness=0.12,
        emission=(1.0, 0.46, 0.05),
        emission_strength=2.1,
    )
    plasma_cyan = C.make_pbr_mat(
        "PlasmaCyan",
        (0.08, 0.94, 1.0, 1.0),
        metallic=0.05,
        roughness=0.10,
        emission=(0.08, 0.94, 1.0),
        emission_strength=2.4,
    )
    tesla_glass = C.make_pbr_mat(
        "TeslaGlass",
        (0.55, 0.92, 1.0, 1.0),
        metallic=0.08,
        roughness=0.08,
        alpha=0.52,
        emission=(0.06, 0.60, 0.85),
        emission_strength=0.65,
    )
    gauge_dial = C.make_pbr_mat(
        "RayGaugeDial",
        (0.75, 0.56, 0.18, 1.0),
        metallic=0.05,
        roughness=0.28,
        albedo_tex=os.path.join(C.TEX_DIR, "props", "pap_gauge.png"),
        emission=(0.85, 0.45, 0.10),
        emission_strength=0.22,
    )
    return locals()


def _oval_ring(cx, cy, cz, rx, ry, rz=0.0, tilt_x=0.0, sides=12):
    pts = []
    ct, st = math.cos(tilt_x), math.sin(tilt_x)
    for i in range(sides):
        ang = (i / sides) * 2.0 * math.pi
        lx = math.cos(ang) * rx
        ly = math.sin(ang) * ry
        lz = math.sin(ang) * rz
        ry_r = ly * ct - lz * st
        rz_r = ly * st + lz * ct
        pts.append((cx + lx, cy + ry_r, cz + rz_r))
    return pts


def _rect_bevel_ring(cx, cy, cz, hx, hz, bevel_f=0.25, axis="Y"):
    bx = hx * bevel_f
    bz = hz * bevel_f
    dx = hx - bx
    dz = hz - bz
    pts_2d = [
        (dx, hz), (hx, dz), (hx, -dz), (dx, -hz),
        (-dx, -hz), (-hx, -dz), (-hx, dz), (-dx, hz),
    ]
    if axis == "Y":
        return [(cx + a, cy, cz + b) for a, b in pts_2d]
    return [(cx + a, cy + b, cz) for a, b in pts_2d]


def _wood_stock_loft(name, y_end=-0.27, z_butt=-0.048, y_neck=-0.035, z_neck=-0.012, w_butt=0.022, h_butt=0.062, w_neck=0.018, h_neck=0.028, mat=None):
    rings = [
        _rect_bevel_ring(0.0, y_end, z_butt, w_butt, h_butt, 0.32),
        _rect_bevel_ring(0.0, y_end * 0.72 + y_neck * 0.28, z_butt * 0.78 + z_neck * 0.22 + 0.008, w_butt * 0.96, h_butt * 0.88, 0.34),
        _rect_bevel_ring(0.0, y_end * 0.38 + y_neck * 0.62, z_butt * 0.35 + z_neck * 0.65 + 0.006, w_butt * 0.88, h_butt * 0.68, 0.36),
        _rect_bevel_ring(0.0, y_neck, z_neck, w_neck, h_neck, 0.38),
    ]
    return C.add_ring_loft(name, rings, mat=mat, smooth_angle=48.0, uv_scale=8.0)


# ---------------------------------------------------------------------------
# 1. M1911 (Receiver + Slide + Magazine + Trigger)
# ---------------------------------------------------------------------------

def build_m1911():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    frame_profile = [
        (-0.040, -0.095), (0.006, -0.082), (0.022, -0.018),
        (0.054, -0.002), (0.136, -0.002), (0.138, 0.018),
        (-0.038, 0.018), (-0.056, 0.024), (-0.046, 0.012),
        (-0.028, -0.002), (-0.032, -0.045),
    ]
    static_parts.append(C.add_extruded_poly("FrameBody", frame_profile, depth=0.025, plane="YZ", mat=m["dark_steel"], bevel=0.0025))

    for sx in (-1, 1):
        static_parts.append(C.add_box(f"GripPanel_{sx}", (0.006, 0.042, 0.096), (sx * 0.014, -0.013, -0.043), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.002))
        for sz in (-0.018, -0.072):
            static_parts.append(C.add_cyl(f"GripScrew_{sx}_{sz}", 0.0032, 0.004, (sx * 0.0165, -0.013 - (sz + 0.043) * 0.28, sz), (0, math.radians(90), 0), vertices=10, mat=m["brass"], bevel=0.0004))

    guard_pts = [(0, 0.012, -0.002), (0, 0.016, -0.032), (0, 0.048, -0.032), (0, 0.052, -0.002)]
    static_parts.append(C.add_tube_pipe("TriggerGuard", guard_pts, radius=0.0038, segments=8, mat=m["dark_steel"]))
    static_parts.append(C.add_box("SpurHammer", (0.007, 0.018, 0.017), (0, -0.044, 0.030), (math.radians(-28), 0, 0), mat=m["chrome"], bevel=0.0015))
    static_parts.append(C.add_cyl("ThumbSafety", 0.0035, 0.022, (-0.016, -0.028, 0.020), (math.radians(90), 0, 0), vertices=8, mat=m["dark_steel"]))
    static_parts.append(C.add_box("SlideStop", (0.004, 0.028, 0.006), (-0.015, 0.025, 0.015), (0, 0, 0), mat=m["dark_steel"], bevel=0.0008))
    static_parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0086, r_inner=0.0058, length=0.195, loc=(0, 0.088, 0.036), mat=m["chrome"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cyl("RecoilPlug", 0.0068, 0.032, (0, 0.152, 0.022), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"]))
    _join_named(static_parts, "Receiver", uv_scale=12.0)

    # Separate animatable Slide (origin 0,0,0 -> translates along Godot +Z)
    slide_parts = []
    slide_rings = [
        _rect_bevel_ring(0.0, -0.042, 0.035, 0.0165, 0.0165, 0.30),
        _rect_bevel_ring(0.0, 0.165, 0.035, 0.0160, 0.0160, 0.30),
    ]
    slide_parts.append(C.add_ring_loft("SlideBody", slide_rings, mat=m["gunmetal"], smooth_angle=35.0, uv_scale=4.0))
    for i in range(9):
        slide_parts.append(C.add_box(f"RearSerr_{i}", (0.0345, 0.0022, 0.022), (0, -0.030 + i * 0.0045, 0.035), (math.radians(-12), 0, 0), mat=m["dark_steel"], bevel=0.0003))
    for i in range(5):
        slide_parts.append(C.add_box(f"FrontSerr_{i}", (0.0340, 0.0020, 0.020), (0, 0.125 + i * 0.0045, 0.035), (math.radians(-12), 0, 0), mat=m["dark_steel"], bevel=0.0003))
    slide_parts.append(C.add_box("ChamberHood", (0.020, 0.038, 0.014), (0.002, 0.048, 0.045), (0, 0, 0), mat=m["chrome"], bevel=0.0015))
    slide_parts.append(C.add_cyl("MuzzleCollar", 0.0102, 0.012, (0, 0.178, 0.036), (math.radians(90), 0, 0), vertices=18, mat=m["dark_steel"], bevel=0.001))
    slide_parts.append(C.add_box("RearSightBase", (0.026, 0.014, 0.006), (0, -0.032, 0.052), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    slide_parts.append(C.add_box("RearSightL", (0.007, 0.012, 0.010), (-0.009, -0.032, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    slide_parts.append(C.add_box("RearSightR", (0.007, 0.012, 0.010), (0.009, -0.032, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    slide_parts.append(C.add_box("FrontSightBlade", (0.0045, 0.013, 0.011), (0, 0.154, 0.055), (0, 0, 0), mat=m["dark_steel"], bevel=0.0008))
    slide_parts.append(C.add_sphere("FrontTritium", 0.0022, (1, 1, 1), (0, 0.150, 0.058), mat=m["tritium"]))
    slide_parts.append(C.add_sphere("RearTritL", 0.0018, (1, 1, 1), (-0.009, -0.037, 0.058), mat=m["tritium"]))
    slide_parts.append(C.add_sphere("RearTritR", 0.0018, (1, 1, 1), (0.009, -0.037, 0.058), mat=m["tritium"]))
    _join_named(slide_parts, "Slide", uv_scale=12.0)

    # Separate Magazine (drops out along grip angle during reload)
    mag_parts = [
        C.add_box("MagTube", (0.017, 0.034, 0.095), (0, -0.014, -0.048), (math.radians(-16), 0, 0), mat=m["dark_steel"], bevel=0.0015),
        C.add_box("MagBase", (0.022, 0.044, 0.012), (0, -0.026, -0.096), (math.radians(-16), 0, 0), mat=m["gunmetal"], bevel=0.002),
    ]
    _join_named(mag_parts, "Magazine", uv_scale=12.0, pivot=(0.0, -0.014, -0.045))

    # Separate Trigger (pivot near top pin)
    trig = C.add_box("Trigger", (0.006, 0.010, 0.019), (0, 0.030, -0.015), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=12.0, pivot=(0.0, 0.030, -0.006))

    _export_weapon_scene("weapons", "m1911", max_tris=15000)


# ---------------------------------------------------------------------------
# 2. Kar98k Scoped (Cleaned & Split CC0 Poly Haven Rifle <= 12k tris)
# ---------------------------------------------------------------------------

def build_kar98k():
    C.reset_scene()
    m = weapon_mats()

    if not os.path.exists(KAR98K_CC0_GLTF):
        raise FileNotFoundError(f"Missing CC0 rifle at {KAR98K_CC0_GLTF}")

    bpy.ops.import_scene.gltf(filepath=KAR98K_CC0_GLTF)
    bpy.context.view_layer.update()

    # Discard loose cartridge prop to save tris & avoid floating part
    bullet = bpy.data.objects.get("bolt_action_rifle_7_62_bullet_54mm")
    if bullet is not None:
        bpy.data.objects.remove(bullet, do_unlink=True)

    # Transform entire imported hierarchy:
    # +X forward -> +90 deg Z rotates +X to +Y forward; scale 0.90; trigger sits at (0, +0.022, -0.016)
    rot_m = Euler((0.0, 0.0, math.radians(90.0)), "XYZ").to_matrix().to_4x4()
    scl_m = Matrix.Scale(0.90, 4)
    # Trigger raw center was (-0.2885, 0.0, -0.0104). After rot+scl: (0.0, -0.2597, -0.0094).
    # Target trigger position: (0.0, +0.022, -0.016) -> translation (0.0, +0.2817, -0.0066).
    xform = Matrix.Translation(Vector((0.0, 0.2817, -0.0066))) @ scl_m @ rot_m

    for o in list(bpy.data.objects):
        if o.type == "MESH":
            # Bake current parent matrix cleanly into mesh vertices
            mw = xform @ o.matrix_world
            o.parent = None
            o.matrix_world = Matrix.Identity(4)
            o.data.transform(mw)
            o.data.update()
        elif o.type == "EMPTY":
            bpy.data.objects.remove(o, do_unlink=True)

    # Center Scope smoothly onto X=0 so ADS crosshair aligns through the ocular tube cleanly!
    scope_obj = bpy.data.objects.get("bolt_action_rifle_7_62_scope")
    if scope_obj is not None:
        xs = [v.co.x for v in scope_obj.data.vertices]
        ys = [v.co.y for v in scope_obj.data.vertices]
        zs = [v.co.z for v in scope_obj.data.vertices]
        scx = 0.5 * (min(xs) + max(xs))
        scz = 0.5 * (min(zs) + max(zs))
        # Recenter scope X onto 0.0 (receiver centerline) cleanly
        for v in scope_obj.data.vertices:
            v.co.x -= scx
        scope_obj.data.update()
        print(f"[KAR98K] Scope bounds Y=[{min(ys):.4f}..{max(ys):.4f}] Z=[{min(zs):.4f}..{max(zs):.4f}] (center_z={scz:.4f}, X shifted by {-scx:.4f})")

        # Enhance glass material slots with crisp OpticLens emission + slight sheen
        for i, mat in enumerate(scope_obj.data.materials):
            if mat and "glass" in mat.name.lower():
                scope_obj.data.materials[i] = m["optic_lens"]

    # Join static parts: rifle body + leather wrap + scope -> Receiver
    body = bpy.data.objects.get("bolt_action_rifle_7_62")
    wrap = bpy.data.objects.get("bolt_action_rifle_7_62_wrap")
    static_list = [o for o in (body, wrap, scope_obj) if o is not None]
    receiver = _join_named(static_list, "Receiver", uv_scale=1.0, apply_uv=False)

    # Decimate Receiver carefully (preserving UVs) to ~7,600 tris so total stays <= 10,800 (< 12k!)
    rec_tris = sum(max(1, len(p.vertices) - 2) for p in receiver.data.polygons)
    if rec_tris > 7600:
        dec = receiver.modifiers.new("DecimateStatic", "DECIMATE")
        dec.ratio = 7400.0 / float(rec_tris)
        dec.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = receiver
        bpy.ops.object.modifier_apply(modifier=dec.name)
    C.smooth_shade(receiver, 48.0)

    # Join bolt_a + bolt_b into animatable Bolt node centered on bolt shaft axis (0, 0.085, 0.029)
    bolt_a = bpy.data.objects.get("bolt_action_rifle_7_62_bolt_a")
    bolt_b = bpy.data.objects.get("bolt_action_rifle_7_62_bolt_b")
    bolt_objs = [o for o in (bolt_a, bolt_b) if o is not None]
    if bolt_objs:
        # Find exact centerline Z of bolt shaft in transformed mesh
        bz_all = [v.co.z for o in bolt_objs for v in o.data.vertices]
        by_all = [v.co.y for o in bolt_objs for v in o.data.vertices]
        bolt_pivot = (0.0, 0.5 * (min(by_all) + max(by_all)), 0.029)
        bolt = _join_named(bolt_objs, "Bolt", uv_scale=1.0, pivot=bolt_pivot, apply_uv=False)
        bt = sum(max(1, len(p.vertices) - 2) for p in bolt.data.polygons)
        if bt > 1800:
            dec = bolt.modifiers.new("DecimateBolt", "DECIMATE")
            dec.ratio = 1750.0 / float(bt)
            dec.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = bolt
            bpy.ops.object.modifier_apply(modifier=dec.name)
        C.smooth_shade(bolt, 46.0)

    trig = bpy.data.objects.get("bolt_action_rifle_7_62_trigger")
    if trig is not None:
        trig.name = "Trigger"
        txs = [v.co.x for v in trig.data.vertices]
        tys = [v.co.y for v in trig.data.vertices]
        tzs = [v.co.z for v in trig.data.vertices]
        piv = (0.5 * (min(txs) + max(txs)), 0.5 * (min(tys) + max(tys)), max(tzs))
        _join_named([trig], "Trigger", uv_scale=1.0, pivot=piv, apply_uv=False)

    # Print muzzle & bounds for WeaponDB exact calibration
    pts = [v.co for v in receiver.data.vertices]
    print(f"[KAR98K] Receiver bounds Y=[{min(p.y for p in pts):.4f}..{max(p.y for p in pts):.4f}] Z=[{min(p.z for p in pts):.4f}..{max(p.z for p in pts):.4f}]")
    _export_weapon_scene("weapons", "kar98k", max_tris=12000)


# ---------------------------------------------------------------------------
# 3. Trench Shotgun (Receiver + Pump + Bolt + Trigger)
# ---------------------------------------------------------------------------

def build_trench_shotgun():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(_wood_stock_loft("Stock", y_end=-0.27, z_butt=-0.052, y_neck=-0.045, z_neck=-0.006, w_butt=0.022, h_butt=0.062, w_neck=0.017, h_neck=0.028, mat=m["walnut"]))
    static_parts.append(C.add_box("ButtPlate", (0.046, 0.010, 0.126), (0, -0.275, -0.052), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    static_parts.append(C.add_box("GripNeck", (0.034, 0.052, 0.068), (0, -0.022, -0.032), (math.radians(-30), 0, 0), mat=m["walnut"], bevel=0.005))
    rec_rings = [
        _rect_bevel_ring(0.0, -0.068, 0.020, 0.022, 0.032, 0.28),
        _rect_bevel_ring(0.0, 0.135, 0.022, 0.022, 0.033, 0.28),
    ]
    static_parts.append(C.add_ring_loft("ReceiverBody", rec_rings, mat=m["gunmetal"], smooth_angle=38.0))
    static_parts.append(C.add_box("Hammer", (0.010, 0.022, 0.018), (0, -0.068, 0.046), (math.radians(-35), 0, 0), mat=m["dark_steel"], bevel=0.002))
    static_parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.015, -0.010), (0, -0.012, -0.038), (0, 0.026, -0.038), (0, 0.030, -0.010)], radius=0.004, segments=8, mat=m["dark_steel"]))
    static_parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0145, r_inner=0.0108, length=0.55, loc=(0, 0.37, 0.038), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cyl("MagTube", 0.0125, 0.49, (0, 0.34, 0.008), (math.radians(90), 0, 0), vertices=18, mat=m["gunmetal"], bevel=0.0015))
    static_parts.append(C.add_vented_shroud("HeatShield", r_outer=0.0205, thickness=0.003, length=0.25, bands=9, struts=6, loc=(0, 0.34, 0.038), mat=m["dark_steel"]))
    static_parts.append(C.add_box("BayonetLug", (0.028, 0.044, 0.054), (0, 0.56, 0.022), (0, 0, 0), mat=m["dark_steel"], bevel=0.0025))
    static_parts.append(C.add_cyl("LugBolt", 0.0045, 0.036, (0, 0.56, 0.012), (0, math.radians(90), 0), vertices=10, mat=m["chrome"]))
    static_parts.append(C.add_box("SightBase", (0.008, 0.014, 0.008), (0, 0.625, 0.053), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    static_parts.append(C.add_sphere("BrassBead", 0.0038, (1, 1, 1), (0, 0.627, 0.058), mat=m["brass"]))
    _join_named(static_parts, "Receiver", uv_scale=10.0)

    # Separate sliding Pump (ribbed walnut forend + action bar)
    pump_rings = []
    for k in range(22):
        py = 0.19 + (k / 21.0) * 0.165
        rr = 0.0255 if k % 2 == 0 else 0.0215
        pump_rings.append(_oval_ring(0.0, py, 0.008, rr, 0.0, rr, math.radians(90), sides=16))
    pump_parts = [
        C.add_ring_loft("PumpForend", pump_rings, mat=m["walnut"], smooth_angle=52.0),
        C.add_cyl("ActionBar", 0.0045, 0.24, (-0.017, 0.19, 0.008), (math.radians(90), 0, 0), vertices=10, mat=m["chrome"]),
    ]
    _join_named(pump_parts, "Pump", uv_scale=10.0)

    # Separate Bolt & Trigger
    bolt = C.add_box("Bolt", (0.008, 0.068, 0.020), (0.019, 0.042, 0.030), (0, 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([bolt], "Bolt", uv_scale=10.0)
    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.008, -0.022), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=10.0, pivot=(0.0, 0.008, -0.012))

    _export_weapon_scene("weapons", "trench_shotgun", max_tris=15000)


# ---------------------------------------------------------------------------
# 4. MP40 (Receiver + Magazine + Bolt + Trigger)
# ---------------------------------------------------------------------------

def build_mp40():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(C.add_box("Grip", (0.032, 0.045, 0.112), (0, -0.012, -0.048), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.004))
    static_parts.append(C.add_box("LowerChassis", (0.038, 0.22, 0.042), (0, 0.065, 0.006), (0, 0, 0), mat=m["bakelite"], bevel=0.005))
    static_parts.append(C.add_tube_pipe("TriggerGuard", [(0, 0.008, -0.008), (0, 0.012, -0.035), (0, 0.048, -0.035), (0, 0.052, -0.008)], radius=0.0035, segments=8, mat=m["dark_steel"]))
    static_parts.append(C.add_cyl("UpperTube", 0.0215, 0.31, (0, 0.085, 0.036), (math.radians(90), 0, 0), vertices=22, mat=m["gunmetal"], bevel=0.002))
    for rx in (-0.020, 0.020):
        static_parts.append(C.add_box(f"RecRib_{rx}", (0.005, 0.22, 0.008), (rx, 0.08, 0.036), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    static_parts.append(C.add_cyl("BoltSlot", 0.006, 0.095, (-0.019, 0.04, 0.044), (math.radians(90), 0, 0), vertices=10, mat=m["bore_dark"]))
    static_parts.append(C.add_box("EjectionPort", (0.006, 0.048, 0.016), (0.019, 0.06, 0.042), (0, 0, 0), mat=m["bore_dark"]))
    static_parts.append(C.add_box("MagWell", (0.034, 0.050, 0.068), (0, 0.185, -0.010), (math.radians(4), 0, 0), mat=m["gunmetal"], bevel=0.003))
    static_parts.append(C.add_cyl("MagCollar", 0.024, 0.030, (0, 0.22, 0.036), (math.radians(90), 0, 0), vertices=18, mat=m["dark_steel"], bevel=0.002))
    static_parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0105, r_inner=0.0072, length=0.25, loc=(0, 0.335, 0.036), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cyl("BarrelNut", 0.016, 0.042, (0, 0.245, 0.036), (math.radians(90), 0, 0), vertices=16, mat=m["dark_steel"], bevel=0.002))
    static_parts.append(C.add_box("RestingBar", (0.012, 0.145, 0.018), (0, 0.34, 0.014), (0, 0, 0), mat=m["bakelite"], bevel=0.003))
    static_parts.append(C.add_cyl("RestingLug", 0.013, 0.018, (0, 0.405, 0.025), (math.radians(90), 0, 0), vertices=12, mat=m["dark_steel"]))
    for sx in (-1, 1):
        static_parts.append(C.add_cyl(f"StockPivot_{sx}", 0.012, 0.014, (sx * 0.023, -0.028, 0.010), (0, math.radians(90), 0), vertices=14, mat=m["dark_steel"], bevel=0.0015))
        static_parts.append(C.add_cyl(f"FoldStrut_{sx}", 0.0065, 0.22, (sx * 0.024, -0.135, -0.002), (math.radians(84), 0, 0), vertices=12, mat=m["gunmetal"], bevel=0.001))
    static_parts.append(C.add_box("ButtPlate", (0.056, 0.014, 0.092), (0, -0.244, -0.018), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    static_parts.append(C.add_box("FrontSightBase", (0.016, 0.022, 0.016), (0, 0.44, 0.046), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    static_parts.append(C.add_torus("FrontSightHood", 0.011, 0.0024, (0, 0.44, 0.056), (math.radians(90), 0, 0), major_segments=16, minor_segments=6, mat=m["dark_steel"]))
    static_parts.append(C.add_box("FrontPost", (0.003, 0.004, 0.010), (0, 0.44, 0.056), (0, 0, 0), mat=m["tritium"], bevel=0.0005))
    static_parts.append(C.add_box("RearSight", (0.022, 0.022, 0.014), (0, -0.032, 0.057), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    _join_named(static_parts, "Receiver", uv_scale=14.0)

    mag_parts = [
        C.add_box("MagBody", (0.023, 0.036, 0.195), (0, 0.185, -0.118), (math.radians(5), 0, 0), mat=m["dark_steel"], bevel=0.002),
        C.add_box("MagFloorPlate", (0.027, 0.040, 0.008), (0, 0.194, -0.214), (math.radians(5), 0, 0), mat=m["gunmetal"], bevel=0.0015),
    ]
    _join_named(mag_parts, "Magazine", uv_scale=14.0, pivot=(0.0, 0.185, -0.035))

    bolt_parts = [
        C.add_tube_pipe("CockingHandle", [(-0.018, 0.01, 0.044), (-0.040, 0.005, 0.042), (-0.044, -0.004, 0.034)], radius=0.0055, segments=10, mat=m["chrome"]),
        C.add_cyl("BoltCarrier", 0.014, 0.055, (0, 0.045, 0.036), (math.radians(90), 0, 0), vertices=14, mat=m["chrome"]),
    ]
    _join_named(bolt_parts, "Bolt", uv_scale=14.0)

    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.030, -0.019), (math.radians(18), 0, 0), mat=m["gunmetal"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=14.0, pivot=(0.0, 0.030, -0.010))

    _export_weapon_scene("weapons", "mp40", max_tris=15000)


# ---------------------------------------------------------------------------
# 5. STG-44 (Receiver + Magazine + Bolt + Trigger)
# ---------------------------------------------------------------------------

def build_stg44():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(_wood_stock_loft("WoodStock", y_end=-0.27, z_butt=-0.042, y_neck=-0.042, z_neck=0.010, w_butt=0.020, h_butt=0.058, w_neck=0.019, h_neck=0.032, mat=m["walnut"]))
    static_parts.append(C.add_box("ButtPlate", (0.042, 0.012, 0.118), (0, -0.274, -0.042), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    static_parts.append(C.add_box("SlingCutout", (0.043, 0.036, 0.018), (0, -0.18, -0.045), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))
    static_parts.append(C.add_box("Grip", (0.032, 0.046, 0.11), (0, -0.015, -0.045), (math.radians(-18), 0, 0), mat=m["bakelite"], bevel=0.004))
    static_parts.append(C.add_tube_pipe("TriggerGuard", [(0, 0.006, -0.006), (0, 0.012, -0.035), (0, 0.048, -0.035), (0, 0.054, -0.006)], radius=0.0036, segments=8, mat=m["dark_steel"]))
    rec_rings = [
        _rect_bevel_ring(0.0, -0.050, 0.024, 0.022, 0.032, 0.30),
        _rect_bevel_ring(0.0, 0.205, 0.024, 0.021, 0.031, 0.30),
    ]
    static_parts.append(C.add_ring_loft("ReceiverBody", rec_rings, mat=m["gunmetal"], smooth_angle=35.0))
    static_parts.append(C.add_vented_shroud("PerforatedShroud", r_outer=0.021, thickness=0.0032, length=0.22, bands=8, struts=6, loc=(0, 0.30, 0.028), mat=m["dark_steel"]))
    static_parts.append(C.add_box("LowerWoodGrip", (0.030, 0.18, 0.020), (0, 0.29, 0.010), (0, 0, 0), mat=m["walnut"], bevel=0.004))
    static_parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0105, r_inner=0.0072, length=0.35, loc=(0, 0.43, 0.028), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cyl("GasTube", 0.0085, 0.25, (0, 0.36, 0.046), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"], bevel=0.0015))
    static_parts.append(C.add_box("GasBlock", (0.020, 0.028, 0.036), (0, 0.475, 0.036), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))
    static_parts.append(C.add_box("FrontSightBase", (0.016, 0.022, 0.030), (0, 0.56, 0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    static_parts.append(C.add_torus("FrontHood", 0.010, 0.0022, (0, 0.56, 0.064), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["dark_steel"]))
    static_parts.append(C.add_box("FrontPost", (0.003, 0.004, 0.012), (0, 0.56, 0.063), (0, 0, 0), mat=m["tritium"], bevel=0.0004))
    static_parts.append(C.add_box("RearSightPedestal", (0.024, 0.036, 0.020), (0, 0.06, 0.060), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    _join_named(static_parts, "Receiver", uv_scale=11.0)

    mag_parts = []
    for seg_i, (sy, sz, rot_x) in enumerate([(0.135, -0.048, 8), (0.156, -0.118, 19), (0.194, -0.182, 31)]):
        mag_parts.append(C.add_box(f"MagSeg_{seg_i}", (0.024, 0.056, 0.076), (0, sy, sz), (math.radians(rot_x), 0, 0), mat=m["dark_steel"], bevel=0.002))
        for rx in (-0.0125, 0.0125):
            mag_parts.append(C.add_box(f"MagRib_{seg_i}_{rx}", (0.003, 0.012, 0.070), (rx, sy, sz), (math.radians(rot_x), 0, 0), mat=m["gunmetal"], bevel=0.0005))
    _join_named(mag_parts, "Magazine", uv_scale=11.0, pivot=(0.0, 0.135, -0.015))

    bolt_parts = [
        C.add_box("DustCover", (0.006, 0.064, 0.020), (0.020, 0.075, 0.034), (0, 0, 0), mat=m["chrome"], bevel=0.001),
        C.add_tube_pipe("ChargingHandle", [(-0.021, 0.125, 0.034), (-0.042, 0.120, 0.034)], radius=0.0055, segments=10, mat=m["dark_steel"]),
    ]
    _join_named(bolt_parts, "Bolt", uv_scale=11.0)

    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.030, -0.020), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=11.0, pivot=(0.0, 0.030, -0.010))

    _export_weapon_scene("weapons", "stg44", max_tris=15000)


# ---------------------------------------------------------------------------
# 6. M14 (Receiver + Magazine + Bolt + Trigger)
# ---------------------------------------------------------------------------

def build_m14():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(_wood_stock_loft("ButtStock", y_end=-0.30, z_butt=-0.048, y_neck=-0.04, z_neck=-0.008, w_butt=0.022, h_butt=0.058, w_neck=0.020, h_neck=0.032, mat=m["walnut"]))
    static_parts.append(C.add_box("ButtPlate", (0.044, 0.012, 0.118), (0, -0.304, -0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    forend_rings = [
        _rect_bevel_ring(0.0, -0.04, -0.002, 0.022, 0.032, 0.34),
        _rect_bevel_ring(0.0, 0.14, 0.002, 0.023, 0.034, 0.34),
        _rect_bevel_ring(0.0, 0.36, 0.012, 0.020, 0.024, 0.38),
    ]
    static_parts.append(C.add_ring_loft("WoodForend", forend_rings, mat=m["walnut"], smooth_angle=45.0))
    static_parts.append(C.add_box("UpperHandguard", (0.034, 0.22, 0.024), (0, 0.25, 0.036), (0, 0, 0), mat=m["bakelite"], bevel=0.004))
    static_parts.append(C.add_box("ReceiverBody", (0.042, 0.175, 0.042), (0, 0.055, 0.034), (0, 0, 0), mat=m["gunmetal"], bevel=0.003))
    static_parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.02, -0.012), (0, -0.015, -0.040), (0, 0.028, -0.040), (0, 0.032, -0.012)], radius=0.0035, segments=8, mat=m["dark_steel"]))
    static_parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0108, r_inner=0.0074, length=0.40, loc=(0, 0.45, 0.036), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cyl("GasCyl", 0.0115, 0.14, (0, 0.43, 0.014), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"], bevel=0.0015))
    static_parts.append(C.add_vented_shroud("FlashHider", r_outer=0.013, thickness=0.0028, length=0.072, bands=2, struts=5, loc=(0, 0.65, 0.036), mat=m["dark_steel"]))
    static_parts.append(C.add_box("FrontSightBase", (0.016, 0.018, 0.024), (0, 0.60, 0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    static_parts.append(C.add_box("FrontPost", (0.004, 0.005, 0.014), (0, 0.60, 0.056), (0, 0, 0), mat=m["tritium"], bevel=0.0005))
    static_parts.append(C.add_box("RearAperture", (0.026, 0.022, 0.016), (0, -0.022, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    _join_named(static_parts, "Receiver", uv_scale=8.0)

    mag_parts = [
        C.add_box("MagBody", (0.028, 0.068, 0.108), (0, 0.115, -0.068), (math.radians(6), 0, 0), mat=m["dark_steel"], bevel=0.002),
        C.add_box("MagFloor", (0.031, 0.072, 0.008), (0, 0.120, -0.122), (math.radians(6), 0, 0), mat=m["gunmetal"], bevel=0.0015),
    ]
    _join_named(mag_parts, "Magazine", uv_scale=8.0, pivot=(0.0, 0.115, -0.020))

    bolt_parts = [
        C.add_box("BoltTop", (0.024, 0.068, 0.014), (0, 0.06, 0.048), (0, 0, 0), mat=m["chrome"], bevel=0.0015),
        C.add_cyl("OpRod", 0.006, 0.28, (0.023, 0.18, 0.026), (math.radians(90), 0, 0), vertices=10, mat=m["dark_steel"]),
        C.add_box("OpRodHandle", (0.022, 0.012, 0.012), (0.032, 0.065, 0.028), (0, 0, 0), mat=m["gunmetal"], bevel=0.0015),
    ]
    _join_named(bolt_parts, "Bolt", uv_scale=8.0)

    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.010, -0.024), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=8.0, pivot=(0.0, 0.010, -0.014))

    _export_weapon_scene("weapons", "m14", max_tris=15000)


# ---------------------------------------------------------------------------
# 7. MG42 (Receiver + Drum + FeedCover + Bolt + Trigger)
# ---------------------------------------------------------------------------

def build_mg42():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(_wood_stock_loft("Butt", y_end=-0.24, z_butt=-0.028, y_neck=-0.055, z_neck=0.006, w_butt=0.025, h_butt=0.058, w_neck=0.024, h_neck=0.036, mat=m["walnut"]))
    static_parts.append(C.add_box("Grip", (0.034, 0.048, 0.114), (0, -0.015, -0.048), (math.radians(-14), 0, 0), mat=m["bakelite"], bevel=0.004))
    static_parts.append(C.add_box("ReceiverBody", (0.068, 0.28, 0.086), (0, 0.09, 0.024), (0, 0, 0), mat=m["dark_steel"], bevel=0.004))
    for idx in range(7):
        static_parts.append(C.add_box(f"ShroudRib_{idx}", (0.056, 0.016, 0.068), (0, 0.245 + idx * 0.052, 0.028), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    static_parts.append(C.add_box("ShroudTopRail", (0.054, 0.36, 0.012), (0, 0.40, 0.058), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    static_parts.append(C.add_box("ShroudBotRail", (0.054, 0.36, 0.012), (0, 0.40, -0.002), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    static_parts.append(C.add_hollow_barrel("InnerBarrel", r_outer=0.014, r_inner=0.0095, length=0.48, loc=(0, 0.45, 0.028), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    static_parts.append(C.add_cone("FlashBooster", r1=0.018, r2=0.023, depth=0.075, loc=(0, 0.68, 0.028), rot=(math.radians(90), 0, 0), mat=m["dark_steel"]))
    for sx in (-1, 1):
        static_parts.append(C.add_cyl(f"BipodLeg_{sx}", 0.007, 0.24, (sx * 0.028, 0.44, -0.014), (math.radians(90), 0, 0), vertices=10, mat=m["dark_steel"]))
    static_parts.append(C.add_torus("AAFrontSight", 0.015, 0.0025, (0, 0.56, 0.074), (math.radians(90), 0, 0), major_segments=16, minor_segments=6, mat=m["dark_steel"]))
    static_parts.append(C.add_box("RearSightPost", (0.020, 0.018, 0.018), (0, 0.02, 0.078), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    _join_named(static_parts, "Receiver", uv_scale=8.0)

    drum_parts = [
        C.add_cyl("DrumMag", 0.076, 0.074, (-0.068, 0.145, -0.022), (0, math.radians(90), 0), vertices=22, mat=m["gunmetal"], bevel=0.003),
        C.add_cyl("DrumHub", 0.026, 0.082, (-0.068, 0.145, -0.022), (0, math.radians(90), 0), vertices=14, mat=m["dark_steel"], bevel=0.002),
    ]
    for b_i in range(6):
        by = 0.115 + b_i * 0.012
        drum_parts.append(C.add_cyl(f"BeltBullet_{b_i}", 0.0055, 0.044, (-0.044, by, 0.046), (0, math.radians(90), math.radians(-18)), vertices=8, mat=m["brass"]))
    _join_named(drum_parts, "Drum", uv_scale=8.0, pivot=(-0.036, 0.145, -0.010))

    cover_parts = [
        C.add_box("FeedCoverBody", (0.064, 0.145, 0.020), (0, 0.14, 0.072), (0, 0, 0), mat=m["gunmetal"], bevel=0.0025),
        C.add_box("FeedLatch", (0.032, 0.022, 0.014), (0, 0.06, 0.076), (0, 0, 0), mat=m["chrome"], bevel=0.0015),
    ]
    _join_named(cover_parts, "FeedCover", uv_scale=8.0, pivot=(0.0, 0.21, 0.070))

    bolt = C.add_cyl("Bolt", 0.011, 0.044, (0.046, 0.06, 0.026), (0, math.radians(90), 0), vertices=14, mat=m["gunmetal"], bevel=0.0015)
    _join_named([bolt], "Bolt", uv_scale=8.0)
    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.014, -0.020), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=8.0, pivot=(0.0, 0.014, -0.010))

    _export_weapon_scene("weapons", "mg42", max_tris=15000)


# ---------------------------------------------------------------------------
# 8. Ray Gun (Receiver + PlasmaCells + Trigger)
# ---------------------------------------------------------------------------

def build_raygun():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    static_parts.append(C.add_box("Grip", (0.030, 0.050, 0.115), (0, -0.012, -0.048), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.004))
    bow_pts = [(0, -0.024, -0.104), (0, 0.042, -0.098), (0, 0.076, -0.052), (0, 0.068, 0.002)]
    static_parts.append(C.add_tube_pipe("KnuckleGuard", bow_pts, radius=0.011, segments=12, mat=m["brass"]))

    chassis_rings = [
        _rect_bevel_ring(0.0, -0.065, 0.022, 0.024, 0.036, 0.42),
        _rect_bevel_ring(0.0, 0.020, 0.028, 0.032, 0.042, 0.42),
        _rect_bevel_ring(0.0, 0.110, 0.032, 0.028, 0.038, 0.42),
    ]
    static_parts.append(C.add_ring_loft("MainHousing", chassis_rings, mat=m["brass"], smooth_angle=52.0))
    static_parts.append(C.add_box("RedTopSpine", (0.026, 0.125, 0.014), (0, -0.010, 0.058), (0, 0, 0), mat=m["ray_red"], bevel=0.004))
    for sx in (-1, 1):
        for lv in range(5):
            static_parts.append(C.add_box(f"Louver_{sx}_{lv}", (0.007, 0.054, 0.006), (sx * 0.032, -0.008 + lv * 0.008, 0.012 + lv * 0.008), (math.radians(-28), 0, 0), mat=m["dark_steel"], bevel=0.001))

    static_parts.append(C.add_cyl("DialBezel", 0.031, 0.020, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=24, mat=m["copper"], bevel=0.002))
    static_parts.append(C.add_cyl("DialFaceL", 0.025, 0.023, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=22, mat=m["ray_red"]))
    static_parts.append(C.add_cyl("DialCenterGlow", 0.015, 0.025, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=18, mat=m["gauge_dial"]))
    for s_ang in (-145, -110, -75, 165):
        ra = math.radians(s_ang)
        static_parts.append(C.add_cone(f"DialSpike_{s_ang}", r1=0.0045, r2=0.001, depth=0.022, loc=(0, -0.048 + math.cos(ra) * 0.038, -0.024 + math.sin(ra) * 0.038), rot=(math.radians(90) - ra, 0, 0), vertices=8, mat=m["brass"]))

    static_parts.append(C.add_box("CellTopBar", (0.016, 0.12, 0.010), (0, 0.105, 0.056), (0, 0, 0), mat=m["ray_red"], bevel=0.002))
    static_parts.append(C.add_box("CellLatch", (0.036, 0.016, 0.026), (0, 0.055, 0.048), (0, 0, 0), mat=m["brass"], bevel=0.002))
    static_parts.append(C.add_cyl("EmitterBase", 0.030, 0.055, (0, 0.175, 0.038), (math.radians(90), 0, 0), vertices=22, mat=m["ray_red"], bevel=0.002))
    static_parts.append(C.add_cone("EmitterShaft", r1=0.026, r2=0.016, depth=0.14, loc=(0, 0.255, 0.038), rot=(math.radians(90), 0, 0), vertices=22, mat=m["copper"]))
    for ry, r_ring in [(0.205, 0.038), (0.255, 0.033), (0.302, 0.028)]:
        static_parts.append(C.add_torus(f"CyanCoil_{ry}", r_ring, 0.0055, (0, ry, 0.038), (math.radians(90), 0, 0), major_segments=22, minor_segments=8, mat=m["plasma_cyan"]))

    fin_poly = [(0.11, 0.052), (0.24, 0.052), (0.20, 0.095), (0.14, 0.072)]
    static_parts.append(C.add_extruded_poly("DorsalFin", fin_poly, depth=0.007, plane="YZ", mat=m["ray_red"], bevel=0.0015))
    static_parts.append(C.add_cyl("RearAntenna", 0.0025, 0.068, (0, 0.18, 0.088), (math.radians(90), 0, 0), vertices=8, mat=m["chrome"]))
    static_parts.append(C.add_torus("TopSightRing", 0.010, 0.0025, (0, -0.02, 0.070), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["tritium"]))
    static_parts.append(C.add_cone("MuzzleBell", r1=0.016, r2=0.031, depth=0.052, loc=(0, 0.348, 0.038), rot=(math.radians(90), 0, 0), vertices=22, mat=m["brass"]))
    static_parts.append(C.add_cyl("MuzzleCore", 0.022, 0.014, (0, 0.369, 0.038), (math.radians(90), 0, 0), vertices=18, mat=m["plasma_orange"]))
    _join_named(static_parts, "Receiver", uv_scale=12.0)

    cells = [
        C.add_cyl("PlasmaCellL", 0.013, 0.115, (-0.014, 0.105, 0.040), (math.radians(90), 0, 0), vertices=16, mat=m["plasma_orange"]),
        C.add_cyl("PlasmaCellR", 0.013, 0.115, (0.014, 0.105, 0.040), (math.radians(90), 0, 0), vertices=16, mat=m["plasma_orange"]),
    ]
    _join_named(cells, "PlasmaCells", uv_scale=12.0, pivot=(0.0, 0.105, 0.040))

    trig = C.add_box("Trigger", (0.006, 0.012, 0.020), (0, 0.026, -0.016), (math.radians(15), 0, 0), mat=m["copper"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=12.0, pivot=(0.0, 0.026, -0.006))

    _export_weapon_scene("weapons", "raygun", max_tris=15000)


# ---------------------------------------------------------------------------
# 9. NEW Wonder Weapon: Wunderwaffe DG-2 (Receiver + VacuumTubes + Magazine + Trigger)
# ---------------------------------------------------------------------------

def build_wunderwaffe():
    C.reset_scene()
    m = weapon_mats()

    static_parts = []
    # Rich dark walnut WWII carbine buttstock + steel buttplate & pistol grip neck
    static_parts.append(_wood_stock_loft("ButtStock", y_end=-0.28, z_butt=-0.044, y_neck=-0.045, z_neck=-0.006, w_butt=0.023, h_butt=0.060, w_neck=0.019, h_neck=0.032, mat=m["wunder_wood"]))
    static_parts.append(C.add_box("ButtPlate", (0.048, 0.012, 0.122), (0, -0.284, -0.044), (0, 0, 0), mat=m["brass"], bevel=0.003))
    static_parts.append(C.add_box("GripNeck", (0.032, 0.050, 0.072), (0, -0.018, -0.032), (math.radians(-26), 0, 0), mat=m["wunder_wood"], bevel=0.005))
    static_parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.010, -0.010), (0, -0.005, -0.038), (0, 0.030, -0.038), (0, 0.034, -0.010)], radius=0.0040, segments=8, mat=m["brass"]))

    # Heavy riveted dark gunmetal generator chassis + copper side plates + walnut lower forend
    chassis_rings = [
        _rect_bevel_ring(0.0, -0.058, 0.024, 0.028, 0.036, 0.34),
        _rect_bevel_ring(0.0, 0.085, 0.026, 0.034, 0.040, 0.34),
        _rect_bevel_ring(0.0, 0.250, 0.028, 0.030, 0.036, 0.36),
    ]
    static_parts.append(C.add_ring_loft("MainChassis", chassis_rings, mat=m["dark_steel"], smooth_angle=38.0))
    for sx in (-1, 1):
        static_parts.append(C.add_box(f"SidePlate_{sx}", (0.008, 0.21, 0.044), (sx * 0.034, 0.095, 0.028), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
        for ry in (0.01, 0.07, 0.13, 0.19):
            static_parts.append(C.add_cyl(f"SideRivet_{sx}_{ry}", 0.0038, 0.005, (sx * 0.038, ry, 0.044), (0, math.radians(90), 0), vertices=8, mat=m["brass"]))
    static_parts.append(C.add_box("ForendWood", (0.038, 0.24, 0.026), (0, 0.26, -0.006), (0, 0, 0), mat=m["wunder_wood"], bevel=0.005))

    # Central high-voltage conduit barrel + helical copper Tesla induction coil + brass collar rings!
    static_parts.append(C.add_hollow_barrel("CoreTube", r_outer=0.017, r_inner=0.010, length=0.40, loc=(0, 0.42, 0.034), mat=m["gunmetal"], bore_mat=m["plasma_cyan"]))
    static_parts.append(C.add_coil_spring("TeslaCoil", major_r=0.024, wire_r=0.0044, length=0.22, turns=6.5, steps_per_turn=14, loc=(0, 0.365, 0.034), mat=m["copper"]))
    for ry in (0.250, 0.325, 0.405, 0.485):
        static_parts.append(C.add_cyl(f"BrassCollar_{ry}", 0.029, 0.015, (0, ry, 0.034), (math.radians(90), 0, 0), vertices=18, mat=m["brass"], bevel=0.002))

    # Signature Wunderwaffe DG-2 3-prong forward lightning arc emitter fork!
    static_parts.append(C.add_cyl("EmitterBlock", 0.026, 0.042, (0, 0.51, 0.034), (math.radians(90), 0, 0), vertices=18, mat=m["dark_steel"], bevel=0.002))
    prong_dirs = [
        (0.0, 0.026),     # top prong
        (-0.023, -0.015), # lower left prong
        (0.023, -0.015),  # lower right prong
    ]
    for idx, (px, pz) in enumerate(prong_dirs):
        pts = [
            (px * 0.85, 0.505, 0.034 + pz * 0.85),
            (px * 1.15, 0.565, 0.034 + pz * 1.15),
            (px * 0.68, 0.625, 0.034 + pz * 0.68),
        ]
        static_parts.append(C.add_tube_pipe(f"Prong_{idx}", pts, radius=0.0052, segments=10, mat=m["copper"]))
        static_parts.append(C.add_sphere(f"ProngTip_{idx}", 0.0068, (1, 1, 1), pts[-1], mat=m["chrome"], segments=12, rings=8))
    static_parts.append(C.add_sphere("EmitterSparkCore", 0.011, (1, 1, 1), (0, 0.58, 0.034), mat=m["plasma_cyan"], segments=12, rings=8))

    # Iron sights aligned along X=0, Z=0.070
    static_parts.append(C.add_box("RearSightBase", (0.026, 0.022, 0.014), (0, -0.035, 0.064), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    static_parts.append(C.add_box("RearSightL", (0.006, 0.014, 0.012), (-0.009, -0.035, 0.072), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    static_parts.append(C.add_box("RearSightR", (0.006, 0.014, 0.012), (0.009, -0.035, 0.072), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    static_parts.append(C.add_torus("FrontSightRing", 0.011, 0.0022, (0, 0.50, 0.072), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["brass"]))
    static_parts.append(C.add_box("FrontSightPost", (0.003, 0.005, 0.010), (0, 0.50, 0.068), (0, 0, 0), mat=m["plasma_cyan"], bevel=0.0004))

    # Upper curved brass manifold rail holding the 3 vacuum tubes
    static_parts.append(C.add_box("TubeRack", (0.032, 0.16, 0.014), (0.016, 0.10, 0.062), (0, 0, math.radians(-12)), mat=m["brass"], bevel=0.002))
    static_parts.append(C.add_box("BulbCageClamp", (0.044, 0.056, 0.016), (0, 0.135, -0.026), (0, 0, 0), mat=m["brass"], bevel=0.002))
    _join_named(static_parts, "Receiver", uv_scale=8.0)

    # Separate glowing VacuumTubes (3 iconic angled cyan glass tubes on top-right rail!)
    tube_parts = []
    for i, ty in enumerate((0.048, 0.100, 0.152)):
        tx = 0.018
        tz = 0.090
        rot_t = (0, math.radians(16), 0)
        tube_parts.append(C.add_cyl(f"TubeSocket_{i}", 0.013, 0.018, (tx - 0.003, ty, tz - 0.020), rot_t, vertices=14, mat=m["brass"], bevel=0.001))
        tube_parts.append(C.add_cyl(f"TubeGlass_{i}", 0.0115, 0.046, (tx + 0.004, ty, tz + 0.008), rot_t, vertices=14, mat=m["tesla_glass"]))
        tube_parts.append(C.add_cyl(f"TubeFilament_{i}", 0.0068, 0.036, (tx + 0.004, ty, tz + 0.008), rot_t, vertices=10, mat=m["plasma_cyan"]))
        tube_parts.append(C.add_cyl(f"TubeCap_{i}", 0.008, 0.009, (tx + 0.011, ty, tz + 0.032), rot_t, vertices=12, mat=m["copper"]))
    _join_named(tube_parts, "VacuumTubes", uv_scale=10.0, pivot=(0.018, 0.100, 0.075))

    # Separate detachable Magazine (glowing Element-115 power bulb beneath receiver!)
    mag_parts = [
        C.add_cyl("BulbBrassCap", 0.020, 0.018, (0, 0.135, -0.035), (0, 0, 0), vertices=16, mat=m["brass"], bevel=0.002),
        C.add_sphere("BulbGlass", 0.023, (0.92, 0.92, 1.35), (0, 0.135, -0.068), segments=16, rings=10, mat=m["tesla_glass"]),
        C.add_sphere("BulbCoreGlow", 0.015, (0.85, 0.85, 1.30), (0, 0.135, -0.068), segments=12, rings=8, mat=m["plasma_cyan"]),
        C.add_cyl("BulbBottomCap", 0.012, 0.012, (0, 0.135, -0.100), (0, 0, 0), vertices=12, mat=m["copper"]),
    ]
    _join_named(mag_parts, "Magazine", uv_scale=10.0, pivot=(0.0, 0.135, -0.035))

    trig = C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.012, -0.022), (math.radians(15), 0, 0), mat=m["brass"], bevel=0.001)
    _join_named([trig], "Trigger", uv_scale=10.0, pivot=(0.0, 0.012, -0.012))

    _export_weapon_scene("weapons", "wunderwaffe", max_tris=15000)


# ---------------------------------------------------------------------------
# 10 & 11. Combat Knife & Frag Grenade
# ---------------------------------------------------------------------------

def build_combat_knife():
    C.reset_scene()
    m = weapon_mats()
    parts = []
    for k in range(7):
        parts.append(C.add_cyl(f"GripRing_{k}", 0.017 if k % 2 == 0 else 0.0145, 0.016, (0, 0, -0.048 + k * 0.016), (0, 0, 0), vertices=14, mat=m["leather"], bevel=0.002))
    parts.append(C.add_cyl("Pommel", 0.019, 0.014, (0, 0, -0.060), (0, 0, 0), vertices=14, mat=m["brass"], bevel=0.002))
    parts.append(C.add_box("Crossguard", (0.018, 0.060, 0.011), (0, 0, 0.062), (0, 0, 0), mat=m["dark_steel"], bevel=0.0025))
    blade_poly = [
        (-0.014, 0.067), (0.014, 0.067),
        (0.016, 0.175), (0.006, 0.232),
        (-0.014, 0.190),
    ]
    parts.append(C.add_extruded_poly("Blade", blade_poly, depth=0.005, plane="YZ", mat=m["chrome"], bevel=0.0018))
    parts.append(C.add_box("BloodFuller", (0.0062, 0.007, 0.092), (0, 0.002, 0.130), (0, 0, 0), mat=m["dark_steel"], bevel=0.0008))
    _join_named(parts, "CombatKnife", uv_scale=12.0)
    _export_weapon_scene("weapons", "combat_knife", max_tris=5000)


def build_frag_grenade():
    C.reset_scene()
    m = weapon_mats()
    parts = []
    rings = []
    for k in range(11):
        t = k / 10.0
        z = -0.044 + t * 0.088
        r_base = math.sin(t * math.pi) * 0.036 + 0.012
        ring = []
        for s in range(16):
            ang = (s / 16.0) * 2.0 * math.pi
            rr = r_base * (1.08 if (s % 2 == 0 and k % 2 == 0) else 0.94)
            ring.append((math.cos(ang) * rr, math.sin(ang) * rr, z))
        rings.append(ring)
    parts.append(C.add_ring_loft("Body", rings, mat=m["gunmetal"], smooth_angle=35.0))
    parts.append(C.add_cyl("FuzeNeck", 0.014, 0.028, (0, 0, 0.052), (0, 0, 0), vertices=14, mat=m["brass"], bevel=0.002))
    parts.append(C.add_tube_pipe("Spoon", [(0, 0.012, 0.062), (0, 0.032, 0.058), (0, 0.044, 0.022), (0, 0.040, -0.015)], radius=0.0045, segments=8, mat=m["dark_steel"]))
    parts.append(C.add_torus("PinRing", 0.016, 0.0028, (0.018, -0.006, 0.058), (0, math.radians(90), 0), major_segments=16, minor_segments=6, mat=m["chrome"]))
    _join_named(parts, "FragGrenade", uv_scale=12.0)
    _export_weapon_scene("weapons", "frag_grenade", max_tris=5000)


def build_all_weapons():
    build_m1911()
    build_kar98k()
    build_trench_shotgun()
    build_mp40()
    build_stg44()
    build_m14()
    build_mg42()
    build_raygun()
    build_wunderwaffe()
    build_combat_knife()
    build_frag_grenade()
    print("[WPN] ALL 11 HIGH-DETAIL ANIMATABLE WEAPONS BUILT & EXPORTED!")


if __name__ == "__main__":
    build_all_weapons()
