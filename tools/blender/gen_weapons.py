"""Generate high-detail Call of Duty Zombies inspired weapons + first-person hands in Blender (.blend + .glb).

Coordinate convention in Blender:
  +Y = forward toward muzzle (exports to -Z in Godot)
  +Z = up (exports to +Y in Godot)
  +X = right (exports to +X in Godot)
Origin (0, 0, 0) = player right-hand grip center.
"""

import math
import os
import sys
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def weapon_mats():
    wtex = os.path.join(C.TEX_DIR, "weapons")

    gunmetal = C.make_pbr_mat(
        "Gunmetal",
        (0.22, 0.24, 0.27, 1.0),
        metallic=0.88,
        roughness=0.30,
        albedo_tex=os.path.join(wtex, "gun_steel_albedo.png"),
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        roughness_tex=os.path.join(wtex, "gun_steel_roughness.png"),
        tint_tex=(0.95, 0.98, 1.05),
        normal_strength=0.16,
    )
    dark_steel = C.make_pbr_mat(
        "DarkSteel",
        (0.11, 0.12, 0.14, 1.0),
        metallic=0.90,
        roughness=0.26,
        albedo_tex=os.path.join(wtex, "gun_steel_albedo.png"),
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        roughness_tex=os.path.join(wtex, "gun_steel_roughness.png"),
        tint_tex=(0.50, 0.52, 0.56),
        normal_strength=0.16,
    )
    chrome = C.make_pbr_mat(
        "Chrome",
        (0.76, 0.78, 0.82, 1.0),
        metallic=0.95,
        roughness=0.14,
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        normal_strength=0.10,
    )
    bore_dark = C.make_pbr_mat("BoreDark", (0.015, 0.015, 0.018, 1.0), metallic=0.10, roughness=0.92)
    walnut = C.make_pbr_mat(
        "WalnutWood",
        (0.30, 0.14, 0.06, 1.0),
        metallic=0.0,
        roughness=0.48,
        albedo_tex=os.path.join(wtex, "walnut_albedo.png"),
        normal_tex=os.path.join(wtex, "walnut_normal.png"),
        roughness_tex=os.path.join(wtex, "walnut_roughness.png"),
        normal_strength=0.26,
    )
    bakelite = C.make_pbr_mat(
        "Bakelite",
        (0.18, 0.07, 0.04, 1.0),
        metallic=0.03,
        roughness=0.44,
        albedo_tex=os.path.join(wtex, "bakelite_albedo.png"),
        normal_tex=os.path.join(wtex, "bakelite_normal.png"),
        roughness_tex=os.path.join(wtex, "bakelite_roughness.png"),
        normal_strength=0.38,
    )
    brass = C.make_pbr_mat(
        "Brass",
        (0.48, 0.34, 0.14, 1.0),
        metallic=0.88,
        roughness=0.32,
        albedo_tex=os.path.join(wtex, "brass_albedo.png"),
        normal_tex=os.path.join(wtex, "brass_normal.png"),
        roughness_tex=os.path.join(wtex, "brass_roughness.png"),
        tint_tex=(0.72, 0.66, 0.58),
        normal_strength=0.20,
    )
    copper = C.make_pbr_mat(
        "Copper",
        (0.58, 0.25, 0.11, 1.0),
        metallic=0.90,
        roughness=0.28,
        normal_tex=os.path.join(wtex, "brass_normal.png"),
        normal_strength=0.18,
    )
    ray_red = C.make_pbr_mat(
        "RayGunRed",
        (0.46, 0.05, 0.04, 1.0),
        metallic=0.35,
        roughness=0.28,
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        normal_strength=0.14,
    )
    leather = C.make_pbr_mat(
        "TacticalLeather",
        (0.14, 0.12, 0.10, 1.0),
        metallic=0.04,
        roughness=0.62,
        albedo_tex=os.path.join(wtex, "fp_leather_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_leather_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_leather_roughness.png"),
        tint_tex=(0.74, 0.72, 0.70),
        normal_strength=0.24,
    )
    sleeve_wool = C.make_pbr_mat(
        "SleeveWool",
        (0.12, 0.14, 0.10, 1.0),
        metallic=0.0,
        roughness=0.92,
        albedo_tex=os.path.join(wtex, "fp_sleeve_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_sleeve_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_sleeve_roughness.png"),
        tint_tex=(0.56, 0.62, 0.50),
        normal_strength=0.38,
    )
    flesh_fingers = C.make_pbr_mat(
        "HandSkin",
        (0.14, 0.12, 0.11, 1.0),
        metallic=0.05,
        roughness=0.58,
        normal_tex=os.path.join(wtex, "fp_leather_normal.png"),
        normal_strength=0.18,
    )
    cuff_cloth = C.make_pbr_mat(
        "KnitCuff",
        (0.09, 0.10, 0.08, 1.0),
        metallic=0.0,
        roughness=0.90,
        normal_tex=os.path.join(wtex, "fp_sleeve_normal.png"),
        normal_strength=0.35,
    )
    tritium = C.make_pbr_mat(
        "TritiumSight",
        (0.14, 1.0, 0.48, 1.0),
        metallic=0.0,
        roughness=0.16,
        emission=(0.14, 1.0, 0.48),
        emission_strength=2.2,
    )
    optic_lens = C.make_pbr_mat(
        "OpticLens",
        (0.06, 0.24, 0.32, 1.0),
        metallic=0.20,
        roughness=0.05,
        emission=(0.04, 0.16, 0.22),
        emission_strength=0.45,
    )
    plasma_orange = C.make_pbr_mat(
        "PlasmaOrange",
        (1.0, 0.46, 0.06, 1.0),
        metallic=0.08,
        roughness=0.12,
        emission=(1.0, 0.44, 0.05),
        emission_strength=1.75,
    )
    plasma_cyan = C.make_pbr_mat(
        "PlasmaCyan",
        (0.06, 0.92, 1.0, 1.0),
        metallic=0.08,
        roughness=0.12,
        emission=(0.06, 0.92, 1.0),
        emission_strength=1.45,
    )
    gauge_dial = C.make_pbr_mat(
        "RayGaugeDial",
        (0.75, 0.56, 0.18, 1.0),
        metallic=0.05,
        roughness=0.28,
        albedo_tex=os.path.join(C.TEX_DIR, "props", "pap_gauge.png"),
        emission=(0.85, 0.45, 0.10),
        emission_strength=0.18,
    )
    return locals()


def _finalize_weapon(parts, mesh_name, sub_folder, asset_name, uv_scale=10.0):
    joined = C.join_objects(parts, mesh_name, apply_uv=False)
    if joined is not None:
        C.uv_box_project(joined, scale=uv_scale)
    C.export_asset(sub_folder, asset_name)


def _oval_ring(cx, cy, cz, rx, ry, rz=0.0, tilt_x=0.0, sides=12):
    """Build an elliptical cross-section vertex loop centered at (cx, cy, cz)."""
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
    """12-vertex chamfered rectangle loop along Y or Z."""
    bx = hx * bevel_f
    bz = hz * bevel_f
    dx = hx - bx
    dz = hz - bz
    pts_2d = [
        (dx, hz),
        (hx, dz),
        (hx, -dz),
        (dx, -hz),
        (-dx, -hz),
        (-hx, -dz),
        (-hx, dz),
        (-dx, hz),
    ]
    if axis == "Y":
        return [(cx + a, cy, cz + b) for a, b in pts_2d]
    return [(cx + a, cy + b, cz) for a, b in pts_2d]


def _wood_stock_loft(name, y_end=-0.27, z_butt=-0.048, y_neck=-0.035, z_neck=-0.012, w_butt=0.022, h_butt=0.062, w_neck=0.018, h_neck=0.028, mat=None):
    """Build an ergonomically swept walnut shoulder stock with comb & belly curves."""
    rings = [
        _rect_bevel_ring(0.0, y_end, z_butt, w_butt, h_butt, 0.32),
        _rect_bevel_ring(0.0, y_end * 0.72 + y_neck * 0.28, z_butt * 0.78 + z_neck * 0.22 + 0.008, w_butt * 0.96, h_butt * 0.88, 0.34),
        _rect_bevel_ring(0.0, y_end * 0.38 + y_neck * 0.62, z_butt * 0.35 + z_neck * 0.65 + 0.006, w_butt * 0.88, h_butt * 0.68, 0.36),
        _rect_bevel_ring(0.0, y_neck, z_neck, w_neck, h_neck, 0.38),
    ]
    return C.add_ring_loft(name, rings, mat=mat, smooth_angle=48.0, uv_scale=8.0)


# ---------------------------------------------------------------------------
# First-Person Gloved Hands & Wool Sleeves
# ---------------------------------------------------------------------------

def build_fp_right_hand():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Sculpted palm overlapping smoothly into forearm cuff
    palm_rings = [
        _rect_bevel_ring(0.024, -0.095, -0.058, 0.024, 0.022, 0.45),
        _rect_bevel_ring(0.016, -0.052, -0.038, 0.027, 0.027, 0.42),
        _rect_bevel_ring(0.010, -0.018, -0.024, 0.028, 0.028, 0.40),
        _rect_bevel_ring(0.016, 0.008, -0.022, 0.023, 0.024, 0.45),
    ]
    parts.append(C.add_ring_loft("R_Palm", palm_rings, mat=m["leather"], smooth_angle=60.0))
    parts.append(C.add_box("R_KnuckleGuard", (0.014, 0.016, 0.056), (0.028, 0.004, -0.024), (math.radians(-14), 0, 0), mat=m["leather"], bevel=0.005))

    # Thumb wrapped cleanly over frame below sights
    thumb_pts = [
        (0.006, -0.030, -0.012),
        (-0.014, -0.018, 0.000),
        (-0.022, 0.000, 0.008),
        (-0.020, 0.020, 0.009),
    ]
    parts.append(C.add_tube_pipe("R_Thumb", thumb_pts, segments=10, radii=[0.0115, 0.010, 0.0088, 0.0072], mat=m["leather"]))
    parts.append(C.add_sphere("R_ThumbTip", 0.0070, (0.9, 1.15, 0.9), (-0.020, 0.025, 0.009), mat=m["flesh_fingers"]))

    # Index finger poised naturally on trigger
    idx_pts = [
        (0.024, 0.006, -0.010),
        (0.024, 0.025, -0.014),
        (0.014, 0.038, -0.016),
        (0.002, 0.036, -0.016),
    ]
    parts.append(C.add_tube_pipe("R_Index", idx_pts, segments=9, radii=[0.0085, 0.0078, 0.0070, 0.0062], mat=m["leather"]))

    # Middle, ring & pinky fingers wrapping front strap tightly
    for f_i, (fz, off) in enumerate([(-0.028, 0.0), (-0.043, -0.002), (-0.058, -0.004)]):
        f_pts = [
            (0.024, 0.004 + off, fz + 0.004),
            (0.023, 0.016 + off, fz),
            (0.008, 0.022 + off, fz - 0.002),
            (-0.013, 0.014 + off, fz - 0.003),
            (-0.019, 0.000 + off, fz - 0.003),
        ]
        r_base = 0.0082 - f_i * 0.0007
        parts.append(C.add_tube_pipe(f"R_Finger{f_i}", f_pts, segments=9, radii=[r_base, r_base * 0.95, r_base * 0.90, r_base * 0.84, r_base * 0.78], mat=m["leather"]))

    # Folded dark wool knit cuff + continuous tapered olive field-jacket sleeve
    parts.append(C.add_torus("R_KnitCuff", 0.031, 0.007, (0.028, -0.094, -0.059), (math.radians(62), 0, math.radians(-26)), major_segments=18, minor_segments=8, mat=m["cuff_cloth"]))
    sleeve_pts = [
        (0.021, -0.078, -0.050),
        (0.038, -0.110, -0.068),
        (0.088, -0.185, -0.112),
        (0.165, -0.295, -0.172),
    ]
    parts.append(C.add_tube_pipe("R_Sleeve", sleeve_pts, segments=16, radii=[0.026, 0.035, 0.044, 0.050], mat=m["sleeve_wool"]))

    _finalize_weapon(parts, "FPRightHand", "weapons", "fp_right_hand", uv_scale=6.0)


def build_fp_left_hand():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Support palm overlapping cleanly into wrist & arm angled down-left out of center sightline
    palm_rings = [
        _rect_bevel_ring(-0.028, -0.056, -0.036, 0.024, 0.018, 0.45),
        _rect_bevel_ring(-0.012, -0.020, -0.024, 0.027, 0.019, 0.42),
        _rect_bevel_ring(0.002, 0.016, -0.018, 0.025, 0.016, 0.42),
    ]
    parts.append(C.add_ring_loft("L_Palm", palm_rings, mat=m["leather"], smooth_angle=60.0))

    thumb_pts = [
        (-0.024, -0.028, -0.015),
        (-0.028, -0.004, 0.000),
        (-0.024, 0.020, 0.008),
        (-0.018, 0.040, 0.008),
    ]
    parts.append(C.add_tube_pipe("L_Thumb", thumb_pts, segments=9, radii=[0.0112, 0.0098, 0.0084, 0.0070], mat=m["leather"]))
    parts.append(C.add_sphere("L_ThumbTip", 0.0066, (0.9, 1.15, 0.9), (-0.017, 0.044, 0.008), mat=m["flesh_fingers"]))

    for f_i, fy in enumerate([0.024, 0.009, -0.005, -0.019]):
        f_pts = [
            (0.015, fy, -0.020),
            (0.026, fy + 0.002, -0.008),
            (0.026, fy + 0.003, 0.008),
            (0.017, fy + 0.003, 0.018),
        ]
        r = 0.0080 - f_i * 0.0005
        parts.append(C.add_tube_pipe(f"L_Finger{f_i}", f_pts, segments=8, radii=[r, r * 0.94, r * 0.88, r * 0.80], mat=m["leather"]))

    # Wrist watch dial bezel + folded dark wool cuff overlapping glove heel cleanly!
    parts.append(C.add_cyl("L_WatchCase", 0.011, 0.008, (-0.046, -0.054, -0.024), (0, math.radians(-26), math.radians(32)), vertices=14, mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_torus("L_KnitCuff", 0.029, 0.007, (-0.044, -0.058, -0.042), (math.radians(56), 0, math.radians(54)), major_segments=18, minor_segments=8, mat=m["cuff_cloth"]))
    sleeve_pts = [
        (-0.026, -0.042, -0.032),
        (-0.068, -0.066, -0.050),
        (-0.138, -0.105, -0.086),
        (-0.205, -0.140, -0.120),
        (-0.275, -0.175, -0.152),
        (-0.355, -0.215, -0.188),
    ]
    parts.append(C.add_tube_pipe("L_Sleeve", sleeve_pts, segments=16, radii=[0.022, 0.028, 0.034, 0.032, 0.038, 0.042], mat=m["sleeve_wool"]))

    _finalize_weapon(parts, "FPLeftHand", "weapons", "fp_left_hand", uv_scale=6.0)


# ---------------------------------------------------------------------------
# High-Detail Firearms (10 Weapons)
# ---------------------------------------------------------------------------

def build_m1911():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Sculpted steel grip frame with swept beavertail
    frame_profile = [
        (-0.040, -0.095), (0.006, -0.082), (0.022, -0.018),
        (0.054, -0.002), (0.136, -0.002), (0.138, 0.018),
        (-0.038, 0.018), (-0.056, 0.024), (-0.046, 0.012),
        (-0.028, -0.002), (-0.032, -0.045),
    ]
    parts.append(C.add_extruded_poly("FrameBody", frame_profile, depth=0.025, plane="YZ", mat=m["dark_steel"], bevel=0.0025))

    # Twin checkered Bakelite side grip panels + 4 brass grip screws
    for sx in (-1, 1):
        parts.append(C.add_box(f"GripPanel_{sx}", (0.006, 0.042, 0.096), (sx * 0.014, -0.013, -0.043), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.002))
        for sz in (-0.018, -0.072):
            parts.append(C.add_cyl(f"GripScrew_{sx}_{sz}", 0.0032, 0.004, (sx * 0.0165, -0.013 - (sz + 0.043) * 0.28, sz), (0, math.radians(90), 0), vertices=10, mat=m["brass"], bevel=0.0004))

    # Magazine basepad, arched trigger guard, skeletonized trigger, spur hammer, controls
    parts.append(C.add_box("MagBase", (0.022, 0.044, 0.012), (0, -0.026, -0.096), (math.radians(-16), 0, 0), mat=m["gunmetal"], bevel=0.002))
    guard_pts = [(0, 0.012, -0.002), (0, 0.016, -0.032), (0, 0.048, -0.032), (0, 0.052, -0.002)]
    parts.append(C.add_tube_pipe("TriggerGuard", guard_pts, radius=0.0038, segments=8, mat=m["dark_steel"]))
    parts.append(C.add_box("Trigger", (0.006, 0.010, 0.019), (0, 0.030, -0.015), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001))
    parts.append(C.add_box("SpurHammer", (0.007, 0.018, 0.017), (0, -0.044, 0.030), (math.radians(-28), 0, 0), mat=m["chrome"], bevel=0.0015))
    parts.append(C.add_cyl("ThumbSafety", 0.0035, 0.022, (-0.016, -0.028, 0.020), (math.radians(90), 0, 0), vertices=8, mat=m["dark_steel"]))
    parts.append(C.add_box("SlideStop", (0.004, 0.028, 0.006), (-0.015, 0.025, 0.015), (0, 0, 0), mat=m["dark_steel"], bevel=0.0008))

    # Beveled Slide + ejection port recess + front/rear serrations
    slide_rings = [
        _rect_bevel_ring(0.0, -0.042, 0.035, 0.0165, 0.0165, 0.30),
        _rect_bevel_ring(0.0, 0.165, 0.035, 0.0160, 0.0160, 0.30),
    ]
    parts.append(C.add_ring_loft("Slide", slide_rings, mat=m["gunmetal"], smooth_angle=35.0, uv_scale=4.0))
    for i in range(9):
        parts.append(C.add_box(f"RearSerr_{i}", (0.0345, 0.0022, 0.022), (0, -0.030 + i * 0.0045, 0.035), (math.radians(-12), 0, 0), mat=m["dark_steel"], bevel=0.0003))
    for i in range(5):
        parts.append(C.add_box(f"FrontSerr_{i}", (0.0340, 0.0020, 0.020), (0, 0.125 + i * 0.0045, 0.035), (math.radians(-12), 0, 0), mat=m["dark_steel"], bevel=0.0003))

    # Chrome barrel hood at ejection port + open hollow threaded barrel + recoil spring plug
    parts.append(C.add_box("ChamberHood", (0.020, 0.038, 0.014), (0.002, 0.048, 0.045), (0, 0, 0), mat=m["chrome"], bevel=0.0015))
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0086, r_inner=0.0058, length=0.195, loc=(0, 0.088, 0.036), mat=m["chrome"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cyl("MuzzleCollar", 0.0102, 0.012, (0, 0.178, 0.036), (math.radians(90), 0, 0), vertices=18, mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_cyl("RecoilPlug", 0.0068, 0.032, (0, 0.152, 0.022), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"]))

    # Novak 3-dot glowing tritium combat sights
    parts.append(C.add_box("RearSightBase", (0.026, 0.014, 0.006), (0, -0.032, 0.052), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_box("RearSightL", (0.007, 0.012, 0.010), (-0.009, -0.032, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_box("RearSightR", (0.007, 0.012, 0.010), (0.009, -0.032, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_box("FrontSightBlade", (0.0045, 0.013, 0.011), (0, 0.154, 0.055), (0, 0, 0), mat=m["dark_steel"], bevel=0.0008))
    parts.append(C.add_sphere("FrontTritium", 0.0022, (1, 1, 1), (0, 0.150, 0.058), mat=m["tritium"]))
    parts.append(C.add_sphere("RearTritL", 0.0018, (1, 1, 1), (-0.009, -0.037, 0.058), mat=m["tritium"]))
    parts.append(C.add_sphere("RearTritR", 0.0018, (1, 1, 1), (0.009, -0.037, 0.058), mat=m["tritium"]))

    _finalize_weapon(parts, "M1911", "weapons", "m1911", uv_scale=12.0)


def build_trench_shotgun():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Ergonomic Walnut pistol-grip buttstock + curved steel buttplate
    parts.append(_wood_stock_loft("Stock", y_end=-0.27, z_butt=-0.052, y_neck=-0.045, z_neck=-0.006, w_butt=0.022, h_butt=0.062, w_neck=0.017, h_neck=0.028, mat=m["walnut"]))
    parts.append(C.add_box("ButtPlate", (0.046, 0.010, 0.126), (0, -0.275, -0.052), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    parts.append(C.add_box("GripNeck", (0.034, 0.052, 0.068), (0, -0.022, -0.032), (math.radians(-30), 0, 0), mat=m["walnut"], bevel=0.005))

    # Solid steel Receiver + chrome bolt inside ejection port + external hammer & guard
    rec_rings = [
        _rect_bevel_ring(0.0, -0.068, 0.020, 0.022, 0.032, 0.28),
        _rect_bevel_ring(0.0, 0.135, 0.022, 0.022, 0.033, 0.28),
    ]
    parts.append(C.add_ring_loft("Receiver", rec_rings, mat=m["gunmetal"], smooth_angle=38.0))
    parts.append(C.add_box("ChromeBolt", (0.008, 0.068, 0.020), (0.019, 0.042, 0.030), (0, 0, 0), mat=m["chrome"], bevel=0.001))
    parts.append(C.add_box("Hammer", (0.010, 0.022, 0.018), (0, -0.068, 0.046), (math.radians(-35), 0, 0), mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.015, -0.010), (0, -0.012, -0.038), (0, 0.026, -0.038), (0, 0.030, -0.010)], radius=0.004, segments=8, mat=m["dark_steel"]))
    parts.append(C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.008, -0.022), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001))

    # Heavy open hollow barrel + under-barrel tubular magazine + slide action bar
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0145, r_inner=0.0108, length=0.55, loc=(0, 0.37, 0.038), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cyl("MagTube", 0.0125, 0.49, (0, 0.34, 0.008), (math.radians(90), 0, 0), vertices=18, mat=m["gunmetal"], bevel=0.0015))
    parts.append(C.add_cyl("ActionBar", 0.0045, 0.24, (-0.017, 0.19, 0.008), (math.radians(90), 0, 0), vertices=10, mat=m["chrome"]))

    # Iconic M1897 perforated steel barrel heatshield!
    parts.append(C.add_vented_shroud("HeatShield", r_outer=0.0205, thickness=0.003, length=0.25, bands=9, struts=6, loc=(0, 0.34, 0.038), mat=m["dark_steel"]))

    # Ribbed turned Walnut pump forend (11 sculpted finger grooves!)
    pump_rings = []
    for k in range(22):
        py = 0.19 + (k / 21.0) * 0.165
        rr = 0.0255 if k % 2 == 0 else 0.0215
        pump_rings.append(_oval_ring(0.0, py, 0.008, rr, 0.0, rr, math.radians(90), sides=16))
    parts.append(C.add_ring_loft("PumpForend", pump_rings, mat=m["walnut"], smooth_angle=52.0))

    # Twin-bolt bayonet lug collar & brass bead front sight
    parts.append(C.add_box("BayonetLug", (0.028, 0.044, 0.054), (0, 0.56, 0.022), (0, 0, 0), mat=m["dark_steel"], bevel=0.0025))
    parts.append(C.add_cyl("LugBolt", 0.0045, 0.036, (0, 0.56, 0.012), (0, math.radians(90), 0), vertices=10, mat=m["chrome"]))
    parts.append(C.add_box("SightBase", (0.008, 0.014, 0.008), (0, 0.625, 0.053), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_sphere("BrassBead", 0.0038, (1, 1, 1), (0, 0.627, 0.058), mat=m["brass"]))

    _finalize_weapon(parts, "TrenchShotgun", "weapons", "trench_shotgun", uv_scale=10.0)


def build_mp40():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Ergonomic dark-brown ribbed Bakelite grip + sculpted lower chassis
    parts.append(C.add_box("Grip", (0.032, 0.045, 0.112), (0, -0.012, -0.048), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.004))
    parts.append(C.add_box("LowerChassis", (0.038, 0.22, 0.042), (0, 0.065, 0.006), (0, 0, 0), mat=m["bakelite"], bevel=0.005))
    parts.append(C.add_tube_pipe("TriggerGuard", [(0, 0.008, -0.008), (0, 0.012, -0.035), (0, 0.048, -0.035), (0, 0.052, -0.008)], radius=0.0035, segments=8, mat=m["dark_steel"]))
    parts.append(C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.030, -0.019), (math.radians(18), 0, 0), mat=m["gunmetal"], bevel=0.001))

    # Stamped tubular Upper Receiver with longitudinal ribs, bolt track & cocking handle
    parts.append(C.add_cyl("UpperTube", 0.0215, 0.31, (0, 0.085, 0.036), (math.radians(90), 0, 0), vertices=22, mat=m["gunmetal"], bevel=0.002))
    for rx in (-0.020, 0.020):
        parts.append(C.add_box(f"RecRib_{rx}", (0.005, 0.22, 0.008), (rx, 0.08, 0.036), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_cyl("BoltSlot", 0.006, 0.095, (-0.019, 0.04, 0.044), (math.radians(90), 0, 0), vertices=10, mat=m["bore_dark"]))
    parts.append(C.add_tube_pipe("CockingHandle", [(-0.018, 0.01, 0.044), (-0.040, 0.005, 0.042), (-0.044, -0.004, 0.034)], radius=0.0055, segments=10, mat=m["chrome"]))
    parts.append(C.add_box("EjectionPort", (0.006, 0.048, 0.016), (0.019, 0.06, 0.042), (0, 0, 0), mat=m["bore_dark"]))

    # Iconic slotted magazine housing + vertical 32-round box magazine
    parts.append(C.add_box("MagWell", (0.034, 0.050, 0.068), (0, 0.185, -0.010), (math.radians(4), 0, 0), mat=m["gunmetal"], bevel=0.003))
    parts.append(C.add_cyl("MagCollar", 0.024, 0.030, (0, 0.22, 0.036), (math.radians(90), 0, 0), vertices=18, mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_box("Magazine", (0.023, 0.036, 0.195), (0, 0.185, -0.118), (math.radians(5), 0, 0), mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_box("MagFloorPlate", (0.027, 0.040, 0.008), (0, 0.194, -0.214), (math.radians(5), 0, 0), mat=m["gunmetal"], bevel=0.0015))

    # Open hollow barrel + corrugated barrel nut + under-barrel Bakelite resting bar!
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0105, r_inner=0.0072, length=0.25, loc=(0, 0.335, 0.036), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cyl("BarrelNut", 0.016, 0.042, (0, 0.245, 0.036), (math.radians(90), 0, 0), vertices=16, mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_box("RestingBar", (0.012, 0.145, 0.018), (0, 0.34, 0.014), (0, 0, 0), mat=m["bakelite"], bevel=0.003))
    parts.append(C.add_cyl("RestingLug", 0.013, 0.018, (0, 0.405, 0.025), (math.radians(90), 0, 0), vertices=12, mat=m["dark_steel"]))

    # Underfolding skeletal stock struts + hinge knobs + T-shaped pivoting buttplate
    for sx in (-1, 1):
        parts.append(C.add_cyl(f"StockPivot_{sx}", 0.012, 0.014, (sx * 0.023, -0.028, 0.010), (0, math.radians(90), 0), vertices=14, mat=m["dark_steel"], bevel=0.0015))
        parts.append(C.add_cyl(f"FoldStrut_{sx}", 0.0065, 0.22, (sx * 0.024, -0.135, -0.002), (math.radians(84), 0, 0), vertices=12, mat=m["gunmetal"], bevel=0.001))
    parts.append(C.add_box("ButtPlate", (0.056, 0.014, 0.092), (0, -0.244, -0.018), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))

    # Hooded front sight ring & V-notch rear sight
    parts.append(C.add_box("FrontSightBase", (0.016, 0.022, 0.016), (0, 0.44, 0.046), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    parts.append(C.add_torus("FrontSightHood", 0.011, 0.0024, (0, 0.44, 0.056), (math.radians(90), 0, 0), major_segments=16, minor_segments=6, mat=m["dark_steel"]))
    parts.append(C.add_box("FrontPost", (0.003, 0.004, 0.010), (0, 0.44, 0.056), (0, 0, 0), mat=m["tritium"], bevel=0.0005))
    parts.append(C.add_box("RearSight", (0.022, 0.022, 0.014), (0, -0.032, 0.057), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))

    _finalize_weapon(parts, "MP40", "weapons", "mp40", uv_scale=14.0)


def build_stg44():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Iconic slanted walnut stock with recessed sling window & cupped steel buttplate
    parts.append(_wood_stock_loft("WoodStock", y_end=-0.27, z_butt=-0.042, y_neck=-0.042, z_neck=0.010, w_butt=0.020, h_butt=0.058, w_neck=0.019, h_neck=0.032, mat=m["walnut"]))
    parts.append(C.add_box("ButtPlate", (0.042, 0.012, 0.118), (0, -0.274, -0.042), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    parts.append(C.add_box("SlingCutout", (0.043, 0.036, 0.018), (0, -0.18, -0.045), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))

    # Grip, stamped lower & contoured upper receiver + dust cover + charging handle
    parts.append(C.add_box("Grip", (0.032, 0.046, 0.11), (0, -0.015, -0.045), (math.radians(-18), 0, 0), mat=m["bakelite"], bevel=0.004))
    parts.append(C.add_tube_pipe("TriggerGuard", [(0, 0.006, -0.006), (0, 0.012, -0.035), (0, 0.048, -0.035), (0, 0.054, -0.006)], radius=0.0036, segments=8, mat=m["dark_steel"]))
    parts.append(C.add_box("Trigger", (0.006, 0.008, 0.018), (0, 0.030, -0.020), (math.radians(15), 0, 0), mat=m["chrome"], bevel=0.001))

    rec_rings = [
        _rect_bevel_ring(0.0, -0.050, 0.024, 0.022, 0.032, 0.30),
        _rect_bevel_ring(0.0, 0.205, 0.024, 0.021, 0.031, 0.30),
    ]
    parts.append(C.add_ring_loft("Receiver", rec_rings, mat=m["gunmetal"], smooth_angle=35.0))
    parts.append(C.add_box("DustCover", (0.006, 0.064, 0.020), (0.020, 0.075, 0.034), (0, 0, 0), mat=m["chrome"], bevel=0.001))
    parts.append(C.add_tube_pipe("ChargingHandle", [(-0.021, 0.125, 0.034), (-0.042, 0.120, 0.034)], radius=0.0055, segments=10, mat=m["dark_steel"]))

    # Iconic ventilated/perforated stamped handguard + wood lower insert + gas block + open barrel!
    parts.append(C.add_vented_shroud("PerforatedShroud", r_outer=0.021, thickness=0.0032, length=0.22, bands=8, struts=6, loc=(0, 0.30, 0.028), mat=m["dark_steel"]))
    parts.append(C.add_box("LowerWoodGrip", (0.030, 0.18, 0.020), (0, 0.29, 0.010), (0, 0, 0), mat=m["walnut"], bevel=0.004))
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0105, r_inner=0.0072, length=0.35, loc=(0, 0.43, 0.028), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cyl("GasTube", 0.0085, 0.25, (0, 0.36, 0.046), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"], bevel=0.0015))
    parts.append(C.add_box("GasBlock", (0.020, 0.028, 0.036), (0, 0.475, 0.036), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))

    # Curved 3-segment stamped banana magazine with stiffening ribs!
    for seg_i, (sy, sz, rot_x) in enumerate([(0.135, -0.048, 8), (0.156, -0.118, 19), (0.194, -0.182, 31)]):
        parts.append(C.add_box(f"MagSeg_{seg_i}", (0.024, 0.056, 0.076), (0, sy, sz), (math.radians(rot_x), 0, 0), mat=m["dark_steel"], bevel=0.002))
        for rx in (-0.0125, 0.0125):
            parts.append(C.add_box(f"MagRib_{seg_i}_{rx}", (0.003, 0.012, 0.070), (rx, sy, sz), (math.radians(rot_x), 0, 0), mat=m["gunmetal"], bevel=0.0005))

    # Hooded front post & tall tangent rear sight
    parts.append(C.add_box("FrontSightBase", (0.016, 0.022, 0.030), (0, 0.56, 0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))
    parts.append(C.add_torus("FrontHood", 0.010, 0.0022, (0, 0.56, 0.064), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["dark_steel"]))
    parts.append(C.add_box("RearSightPedestal", (0.024, 0.036, 0.020), (0, 0.06, 0.060), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))

    _finalize_weapon(parts, "STG44", "weapons", "stg44", uv_scale=11.0)


def build_m14():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Sculpted full-length Walnut rifle body + swept buttstock + pistol-grip contour
    parts.append(_wood_stock_loft("ButtStock", y_end=-0.30, z_butt=-0.048, y_neck=-0.04, z_neck=-0.008, w_butt=0.022, h_butt=0.058, w_neck=0.020, h_neck=0.032, mat=m["walnut"]))
    parts.append(C.add_box("ButtPlate", (0.044, 0.012, 0.118), (0, -0.304, -0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    forend_rings = [
        _rect_bevel_ring(0.0, -0.04, -0.002, 0.022, 0.032, 0.34),
        _rect_bevel_ring(0.0, 0.14, 0.002, 0.023, 0.034, 0.34),
        _rect_bevel_ring(0.0, 0.36, 0.012, 0.020, 0.024, 0.38),
    ]
    parts.append(C.add_ring_loft("WoodForend", forend_rings, mat=m["walnut"], smooth_angle=45.0))
    parts.append(C.add_box("UpperHandguard", (0.034, 0.22, 0.024), (0, 0.25, 0.036), (0, 0, 0), mat=m["bakelite"], bevel=0.004))

    # Receiver, Chrome bolt + Op-rod charging handle on right side, trigger guard
    parts.append(C.add_box("Receiver", (0.042, 0.175, 0.042), (0, 0.055, 0.034), (0, 0, 0), mat=m["gunmetal"], bevel=0.003))
    parts.append(C.add_box("BoltTop", (0.024, 0.068, 0.014), (0, 0.06, 0.048), (0, 0, 0), mat=m["chrome"], bevel=0.0015))
    parts.append(C.add_cyl("OpRod", 0.006, 0.28, (0.023, 0.18, 0.026), (math.radians(90), 0, 0), vertices=10, mat=m["dark_steel"]))
    parts.append(C.add_box("OpRodHandle", (0.022, 0.012, 0.012), (0.032, 0.065, 0.028), (0, 0, 0), mat=m["gunmetal"], bevel=0.0015))
    parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.02, -0.012), (0, -0.015, -0.040), (0, 0.028, -0.040), (0, 0.032, -0.012)], radius=0.0035, segments=8, mat=m["dark_steel"]))

    # Detachable 20-rd steel box magazine
    parts.append(C.add_box("Magazine", (0.028, 0.068, 0.108), (0, 0.115, -0.068), (math.radians(6), 0, 0), mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_box("MagFloor", (0.031, 0.072, 0.008), (0, 0.120, -0.122), (math.radians(6), 0, 0), mat=m["gunmetal"], bevel=0.0015))

    # Open hollow barrel + Gas cylinder + pronged Flash Hider + winged sights!
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0108, r_inner=0.0074, length=0.40, loc=(0, 0.45, 0.036), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cyl("GasCyl", 0.0115, 0.14, (0, 0.43, 0.014), (math.radians(90), 0, 0), vertices=14, mat=m["gunmetal"], bevel=0.0015))
    parts.append(C.add_vented_shroud("FlashHider", r_outer=0.013, thickness=0.0028, length=0.072, bands=2, struts=5, loc=(0, 0.65, 0.036), mat=m["dark_steel"]))
    parts.append(C.add_box("FrontSightBase", (0.016, 0.018, 0.024), (0, 0.60, 0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.001))
    parts.append(C.add_box("FrontPost", (0.004, 0.005, 0.014), (0, 0.60, 0.056), (0, 0, 0), mat=m["tritium"], bevel=0.0005))
    parts.append(C.add_box("RearAperture", (0.026, 0.022, 0.016), (0, -0.022, 0.056), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))

    _finalize_weapon(parts, "M14", "weapons", "m14", uv_scale=8.0)


def build_kar98k():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Sculpted full-length Mauser walnut stock + sling slot + steel barrel bands & bayonet lug
    parts.append(_wood_stock_loft("ButtStock", y_end=-0.30, z_butt=-0.048, y_neck=-0.038, z_neck=-0.008, w_butt=0.021, h_butt=0.056, w_neck=0.018, h_neck=0.028, mat=m["walnut"]))
    parts.append(C.add_box("ButtPlate", (0.042, 0.012, 0.114), (0, -0.304, -0.048), (0, 0, 0), mat=m["dark_steel"], bevel=0.003))
    forend_rings = [
        _rect_bevel_ring(0.0, -0.038, -0.004, 0.021, 0.029, 0.36),
        _rect_bevel_ring(0.0, 0.18, 0.008, 0.020, 0.026, 0.38),
        _rect_bevel_ring(0.0, 0.44, 0.016, 0.017, 0.020, 0.42),
    ]
    parts.append(C.add_ring_loft("WoodForend", forend_rings, mat=m["walnut"], smooth_angle=45.0))
    for by in (0.28, 0.44):
        parts.append(C.add_box(f"BarrelBand_{by}", (0.039, 0.018, 0.046), (0, by, 0.022), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_cyl("CleaningRod", 0.0035, 0.34, (0, 0.44, 0.004), (math.radians(90), 0, 0), vertices=10, mat=m["gunmetal"]))

    # Cylindrical Mauser Receiver + turned-down chrome Bolt Handle & spherical knob + trigger guard
    parts.append(C.add_cyl("Receiver", 0.0195, 0.23, (0, 0.06, 0.034), (math.radians(90), 0, 0), vertices=20, mat=m["dark_steel"], bevel=0.002))
    bolt_pts = [(0.014, 0.005, 0.034), (0.034, 0.002, 0.026), (0.040, -0.004, 0.006)]
    parts.append(C.add_tube_pipe("BoltHandleArm", bolt_pts, radius=0.005, segments=10, mat=m["chrome"]))
    parts.append(C.add_sphere("BoltKnob", 0.011, (1, 1, 1), (0.041, -0.005, 0.001), mat=m["chrome"]))
    parts.append(C.add_tube_pipe("TriggerGuard", [(0, -0.012, -0.012), (0, -0.008, -0.036), (0, 0.032, -0.036), (0, 0.036, -0.012)], radius=0.0035, segments=8, mat=m["dark_steel"]))

    # Stepped open hollow barrel + hooded front sight
    parts.append(C.add_hollow_barrel("Barrel", r_outer=0.0102, r_inner=0.0070, length=0.47, loc=(0, 0.46, 0.034), mat=m["gunmetal"], bore_mat=m["bore_dark"]))
    parts.append(C.add_torus("FrontHood", 0.009, 0.002, (0, 0.67, 0.048), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["dark_steel"]))

    # Detailed ZF39 Sniper Scope (centerline at z=0.078 matching ADS height!)
    parts.append(C.add_cyl("ScopeTube", 0.016, 0.25, (0, 0.08, 0.078), (math.radians(90), 0, 0), vertices=20, mat=m["dark_steel"], bevel=0.002))
    parts.append(C.add_cyl("ObjectiveBell", 0.023, 0.062, (0, 0.225, 0.078), (math.radians(90), 0, 0), vertices=22, mat=m["gunmetal"], bevel=0.002))
    parts.append(C.add_cyl("OcularBell", 0.020, 0.052, (0, -0.065, 0.078), (math.radians(90), 0, 0), vertices=20, mat=m["gunmetal"], bevel=0.002))
    parts.append(C.add_cyl("ObjectiveLens", 0.019, 0.006, (0, 0.255, 0.078), (math.radians(90), 0, 0), vertices=20, mat=m["optic_lens"]))
    parts.append(C.add_cyl("OcularLens", 0.016, 0.006, (0, -0.089, 0.078), (math.radians(90), 0, 0), vertices=18, mat=m["optic_lens"]))
    parts.append(C.add_cyl("ElevTurret", 0.010, 0.022, (0, 0.08, 0.098), (0, 0, 0), vertices=14, mat=m["brass"], bevel=0.0015))
    parts.append(C.add_cyl("WindTurret", 0.009, 0.022, (0.020, 0.08, 0.078), (0, math.radians(90), 0), vertices=14, mat=m["brass"], bevel=0.0015))
    for sy in (0.005, 0.145):
        parts.append(C.add_box(f"ScopeRing_{sy}", (0.024, 0.022, 0.038), (0, sy, 0.058), (0, 0, 0), mat=m["dark_steel"], bevel=0.002))

    _finalize_weapon(parts, "Kar98k", "weapons", "kar98k", uv_scale=8.0)


def build_mg42():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Wide curved walnut buttstock + buffer block + grip
    parts.append(_wood_stock_loft("Butt", y_end=-0.24, z_butt=-0.028, y_neck=-0.055, z_neck=0.006, w_butt=0.025, h_butt=0.058, w_neck=0.024, h_neck=0.036, mat=m["walnut"]))
    parts.append(C.add_box("Grip", (0.034, 0.048, 0.114), (0, -0.015, -0.048), (math.radians(-14), 0, 0), mat=m["bakelite"], bevel=0.004))

    # Heavy stamped Receiver + top hinged feed tray + cocking knob on right side
    parts.append(C.add_box("Receiver", (0.068, 0.28, 0.086), (0, 0.09, 0.024), (0, 0, 0), mat=m["dark_steel"], bevel=0.004))
    parts.append(C.add_box("FeedCover", (0.064, 0.145, 0.020), (0, 0.14, 0.072), (0, 0, 0), mat=m["gunmetal"], bevel=0.0025))
    parts.append(C.add_box("FeedLatch", (0.032, 0.022, 0.014), (0, 0.06, 0.076), (0, 0, 0), mat=m["chrome"], bevel=0.0015))
    parts.append(C.add_cyl("CockingKnob", 0.011, 0.044, (0.046, 0.06, 0.026), (0, math.radians(90), 0), vertices=14, mat=m["gunmetal"], bevel=0.0015))

    # Signature ventilated rectangular MG42 Barrel Shroud over hollow Barrel + Conical Flash Booster!
    for idx in range(7):
        parts.append(C.add_box(f"ShroudRib_{idx}", (0.056, 0.016, 0.068), (0, 0.245 + idx * 0.052, 0.028), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    parts.append(C.add_box("ShroudTopRail", (0.054, 0.36, 0.012), (0, 0.40, 0.058), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    parts.append(C.add_box("ShroudBotRail", (0.054, 0.36, 0.012), (0, 0.40, -0.002), (0, 0, 0), mat=m["gunmetal"], bevel=0.002))
    parts.append(C.add_hollow_barrel("InnerBarrel", r_outer=0.014, r_inner=0.0095, length=0.48, loc=(0, 0.45, 0.028), mat=m["dark_steel"], bore_mat=m["bore_dark"]))
    parts.append(C.add_cone("FlashBooster", r1=0.018, r2=0.023, depth=0.075, loc=(0, 0.68, 0.028), rot=(math.radians(90), 0, 0), mat=m["dark_steel"]))

    # Side Gurttrommel assault drum + visible brass ammo belt feeding into tray!
    parts.append(C.add_cyl("DrumMag", 0.076, 0.074, (-0.068, 0.145, -0.022), (0, math.radians(90), 0), vertices=22, mat=m["gunmetal"], bevel=0.003))
    parts.append(C.add_cyl("DrumHub", 0.026, 0.082, (-0.068, 0.145, -0.022), (0, math.radians(90), 0), vertices=14, mat=m["dark_steel"], bevel=0.002))
    for b_i in range(6):
        by = 0.115 + b_i * 0.012
        parts.append(C.add_cyl(f"BeltBullet_{b_i}", 0.0055, 0.044, (-0.044, by, 0.046), (0, math.radians(90), math.radians(-18)), vertices=8, mat=m["brass"]))

    # Folded bipod legs + flip-up AA front ring sight & tall rear tangent sight
    for sx in (-1, 1):
        parts.append(C.add_cyl(f"BipodLeg_{sx}", 0.007, 0.24, (sx * 0.028, 0.44, -0.014), (math.radians(90), 0, 0), vertices=10, mat=m["dark_steel"]))
    parts.append(C.add_torus("AAFrontSight", 0.015, 0.0025, (0, 0.56, 0.074), (math.radians(90), 0, 0), major_segments=16, minor_segments=6, mat=m["dark_steel"]))
    parts.append(C.add_box("RearSightPost", (0.020, 0.018, 0.018), (0, 0.02, 0.078), (0, 0, 0), mat=m["dark_steel"], bevel=0.0015))

    _finalize_weapon(parts, "MG42", "weapons", "mg42", uv_scale=8.0)


def build_raygun():
    C.reset_scene()
    m = weapon_mats()
    parts = []

    # Checkered pistol grip + swept brass knuckle handguard bow
    parts.append(C.add_box("Grip", (0.030, 0.050, 0.115), (0, -0.012, -0.048), (math.radians(-16), 0, 0), mat=m["bakelite"], bevel=0.004))
    bow_pts = [
        (0, -0.024, -0.104),
        (0, 0.042, -0.098),
        (0, 0.076, -0.052),
        (0, 0.068, 0.002),
    ]
    parts.append(C.add_tube_pipe("KnuckleGuard", bow_pts, radius=0.011, segments=12, mat=m["brass"]))
    parts.append(C.add_box("Trigger", (0.006, 0.012, 0.020), (0, 0.026, -0.016), (math.radians(15), 0, 0), mat=m["copper"], bevel=0.001))

    # Central atom-punk chassis + enamel crimson top cowl & diagonal cooling louvers
    chassis_rings = [
        _rect_bevel_ring(0.0, -0.065, 0.022, 0.024, 0.036, 0.42),
        _rect_bevel_ring(0.0, 0.020, 0.028, 0.032, 0.042, 0.42),
        _rect_bevel_ring(0.0, 0.110, 0.032, 0.028, 0.038, 0.42),
    ]
    parts.append(C.add_ring_loft("MainHousing", chassis_rings, mat=m["brass"], smooth_angle=52.0))
    parts.append(C.add_box("RedTopSpine", (0.026, 0.125, 0.014), (0, -0.010, 0.058), (0, 0, 0), mat=m["ray_red"], bevel=0.004))
    for sx in (-1, 1):
        for lv in range(5):
            parts.append(C.add_box(f"Louver_{sx}_{lv}", (0.007, 0.054, 0.006), (sx * 0.032, -0.008 + lv * 0.008, 0.012 + lv * 0.008), (math.radians(-28), 0, 0), mat=m["dark_steel"], bevel=0.001))

    # Bottom circular Charge Dial Gauge + radial stabilizing spikes!
    parts.append(C.add_cyl("DialBezel", 0.031, 0.020, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=24, mat=m["copper"], bevel=0.002))
    parts.append(C.add_cyl("DialFaceL", 0.025, 0.023, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=22, mat=m["ray_red"]))
    parts.append(C.add_cyl("DialCenterGlow", 0.015, 0.025, (0, -0.048, -0.024), (0, math.radians(90), 0), vertices=18, mat=m["gauge_dial"]))
    for s_ang in (-145, -110, -75, 165):
        ra = math.radians(s_ang)
        parts.append(C.add_cone(f"DialSpike_{s_ang}", r1=0.0045, r2=0.001, depth=0.022, loc=(0, -0.048 + math.cos(ra) * 0.038, -0.024 + math.sin(ra) * 0.038), rot=(math.radians(90) - ra, 0, 0), vertices=8, mat=m["brass"]))

    # Dual exposed glowing Amber Plasma Battery Cells inside cutaway upper cage
    for sx in (-0.014, 0.014):
        parts.append(C.add_cyl(f"PlasmaCell_{sx}", 0.013, 0.115, (sx, 0.105, 0.040), (math.radians(90), 0, 0), vertices=16, mat=m["plasma_orange"]))
    parts.append(C.add_box("CellTopBar", (0.016, 0.12, 0.010), (0, 0.105, 0.056), (0, 0, 0), mat=m["ray_red"], bevel=0.002))
    parts.append(C.add_box("CellLatch", (0.036, 0.016, 0.026), (0, 0.055, 0.048), (0, 0, 0), mat=m["brass"], bevel=0.002))

    # Stepped Tapered Emitter Barrel + 3 Glowing Cyan Containment Rings + Dorsal Wing Fin + Flared Nozzle!
    parts.append(C.add_cyl("EmitterBase", 0.030, 0.055, (0, 0.175, 0.038), (math.radians(90), 0, 0), vertices=22, mat=m["ray_red"], bevel=0.002))
    parts.append(C.add_cone("EmitterShaft", r1=0.026, r2=0.016, depth=0.14, loc=(0, 0.255, 0.038), rot=(math.radians(90), 0, 0), vertices=22, mat=m["copper"]))
    for ry, r_ring in [(0.205, 0.038), (0.255, 0.033), (0.302, 0.028)]:
        parts.append(C.add_torus(f"CyanCoil_{ry}", r_ring, 0.0055, (0, ry, 0.038), (math.radians(90), 0, 0), major_segments=22, minor_segments=8, mat=m["plasma_cyan"]))

    fin_poly = [(0.11, 0.052), (0.24, 0.052), (0.20, 0.095), (0.14, 0.072)]
    parts.append(C.add_extruded_poly("DorsalFin", fin_poly, depth=0.007, plane="YZ", mat=m["ray_red"], bevel=0.0015))
    parts.append(C.add_cyl("RearAntenna", 0.0025, 0.068, (0, 0.18, 0.088), (math.radians(90), 0, 0), vertices=8, mat=m["chrome"]))
    parts.append(C.add_torus("TopSightRing", 0.010, 0.0025, (0, -0.02, 0.070), (math.radians(90), 0, 0), major_segments=14, minor_segments=6, mat=m["tritium"]))

    parts.append(C.add_cone("MuzzleBell", r1=0.016, r2=0.031, depth=0.052, loc=(0, 0.348, 0.038), rot=(math.radians(90), 0, 0), vertices=22, mat=m["brass"]))
    parts.append(C.add_cyl("MuzzleCore", 0.022, 0.014, (0, 0.369, 0.038), (math.radians(90), 0, 0), vertices=18, mat=m["plasma_orange"]))

    _finalize_weapon(parts, "RayGun", "weapons", "raygun", uv_scale=12.0)


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
    _finalize_weapon(parts, "CombatKnife", "weapons", "combat_knife", uv_scale=12.0)


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
    _finalize_weapon(parts, "FragGrenade", "weapons", "frag_grenade", uv_scale=12.0)


if __name__ == "__main__":
    build_fp_right_hand()
    build_fp_left_hand()
    build_m1911()
    build_trench_shotgun()
    build_mp40()
    build_stg44()
    build_m14()
    build_kar98k()
    build_mg42()
    build_raygun()
    build_combat_knife()
    build_frag_grenade()
    print("ALL 10 HIGH-DETAIL WEAPONS + FIRST-PERSON HANDS EXPORTED!")
