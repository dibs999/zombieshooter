"""Generate environmental props & modular architectural kit pieces in Blender (.blend + .glb):
Props:
- barricade_window (brick/stone frame + 6 bolt-studded planks Plank_0..Plank_5, clear shoot aperture)
- element115_crystal (layered meteorite base + 9 translucent glowing hexagonal crystal spires)
- ruined_tank (detailed battle-damaged Panzer IV Ausf. H w/ Schuerzen skirts, 16 roadwheels, track cleats & hollow cannon)
- sandbag_wall (pinched pillowy burlap bags stacked in offset courses + staked timbers)
- crate_military, barrel_rusted, light_cage, teleporter_pad
- lab_pod (fluted bio-containment pod w/ external gauge & suspended skeletal mutant corpse — no snowman!)
Architectural Kit Pieces (used in game_world.gd, buyable_door.tscn & main_menu.tscn):
- blast_door (3.4x3.2m vaulted bulkhead door w/ handwheel, hinge lugs & cross-ribs, centered at origin)
- steel_gantry (10.0m perforated truss catwalk bridge w/ safety handrails)
- wall_pipes (4.0m industrial 3-pipe manifold + spoked red valve + pap_gauge dial)
- barbed_wire (2.2m cheval-de-frise timber X-frames + helical razor wire coils)
- rubble_pile (bombed masonry chunks, shattered beam & bent protruding rebar)
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def _tex_env(name):
    ext = "jpg" if name.startswith("cc0_") else "png"
    return (
        os.path.join(C.TEX_DIR, "env", f"{name}_albedo.{ext}"),
        os.path.join(C.TEX_DIR, "env", f"{name}_normal.{ext}"),
        os.path.join(C.TEX_DIR, "env", f"{name}_roughness.{ext}"),
    )


def _tex_wpn(name):
    return (
        os.path.join(C.TEX_DIR, "weapons", f"{name}_albedo.png"),
        os.path.join(C.TEX_DIR, "weapons", f"{name}_normal.png"),
        os.path.join(C.TEX_DIR, "weapons", f"{name}_roughness.png"),
    )


def build_barricade_window():
    C.reset_scene()
    bc_a, bc_n, bc_r = _tex_env("cc0_concrete_wall")
    rb_a, rb_n, rb_r = _tex_env("cc0_brick")
    cw_a, cw_n, cw_r = _tex_env("cc0_planks")
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")

    stone = C.make_pbr_mat("WindowStone", (0.42, 0.44, 0.46, 1.0), roughness=0.88, albedo_tex=bc_a, normal_tex=bc_n, roughness_tex=bc_r, tint_tex=(0.72, 0.74, 0.76), normal_strength=0.9)
    brick = C.make_pbr_mat("WindowBrick", (0.50, 0.42, 0.36, 1.0), roughness=0.90, albedo_tex=rb_a, normal_tex=rb_n, roughness_tex=rb_r, tint_tex=(0.78, 0.72, 0.68), normal_strength=0.95)
    wood = C.make_pbr_mat("WindowWood", (0.46, 0.32, 0.20, 1.0), roughness=0.82, albedo_tex=cw_a, normal_tex=cw_n, roughness_tex=cw_r, tint_tex=(0.82, 0.74, 0.66), normal_strength=0.85)
    iron = C.make_pbr_mat("WindowIron", (0.16, 0.17, 0.18, 1.0), metallic=0.82, roughness=0.45, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.45, 0.46, 0.48))

    # Opening remains strictly clear: X in [-0.88..+0.88], Z in [0.85..2.45] for ballistic & zombie climb
    frame_parts = [
        C.add_box("SillBase", (2.34, 0.46, 0.75), (0, 0, 0.375), mat=brick, bevel=0.02, uv_scale=0.55),
        C.add_box("SillLedge", (2.42, 0.56, 0.10), (0, 0, 0.80), mat=stone, bevel=0.015, uv_scale=0.65),
        C.add_box("LintelBeam", (2.40, 0.54, 0.38), (0, 0, 2.66), mat=stone, bevel=0.02, uv_scale=0.55),
        C.add_box("PillarL", (0.30, 0.48, 1.62), (-1.03, 0, 1.66), mat=brick, bevel=0.018, uv_scale=0.55),
        C.add_box("PillarR", (0.30, 0.48, 1.62), (1.03, 0, 1.66), mat=brick, bevel=0.018, uv_scale=0.55),
    ]
    for ix in (-0.90, 0.90):
        for iz in (1.05, 1.45, 1.85, 2.25):
            frame_parts.append(C.add_box(f"Bracket_{ix}_{iz}", (0.06, 0.52, 0.08), (ix, 0, iz), mat=iron, bevel=0.005))
    C.join_objects(frame_parts, "WindowFrame")

    # Exact contract: 6 individually named destructible objects Plank_0..Plank_5
    planks_cfg = [
        (0, (0, -0.17, 1.03), (0, math.radians(-3.5), 0)),
        (1, (0, -0.19, 1.32), (0, math.radians(2.8), 0)),
        (2, (0, -0.16, 1.62), (0, math.radians(-5.2), 0)),
        (3, (0, -0.19, 1.93), (0, math.radians(4.5), 0)),
        (4, (0, -0.17, 2.23), (0, math.radians(-2.2), 0)),
        (5, (0, -0.23, 1.65), (0, math.radians(36.0), 0)),
    ]
    for idx, loc, rot in planks_cfg:
        b = C.add_box(f"PlankBoard_{idx}", (1.98, 0.048, 0.185), (0, 0, 0), mat=wood, bevel=0.008, uv_scale=1.1)
        n1 = C.add_cyl(f"BoltL_{idx}", 0.016, 0.068, (-0.86, 0, 0), (math.radians(90), 0, 0), vertices=6, mat=iron)
        n2 = C.add_cyl(f"BoltR_{idx}", 0.016, 0.068, (0.86, 0, 0), (math.radians(90), 0, 0), vertices=6, mat=iron)
        plank = C.join_objects([b, n1, n2], f"Plank_{idx}")
        plank.location = loc
        plank.rotation_euler = rot

    C.export_asset("env", "barricade_window")


def build_element115_crystal():
    C.reset_scene()
    pa_a, pa_n, pa_r = _tex_env("cc0_concrete_wall")
    rock = C.make_pbr_mat(
        "MeteorRock",
        (0.09, 0.095, 0.105, 1.0),
        roughness=0.92,
        albedo_tex=pa_a,
        normal_tex=pa_n,
        roughness_tex=pa_r,
        tint_tex=(0.24, 0.26, 0.32),
        normal_strength=1.05,
    )
    crystal = C.make_pbr_mat(
        "Crystal115",
        (0.04, 0.72, 0.94, 1.0),
        metallic=0.22,
        roughness=0.10,
        emission=(0.04, 0.76, 0.96),
        emission_strength=0.92,
    )

    parts = [
        C.add_box("RockCore", (1.02, 0.92, 0.28), (0, 0, 0.12), (0, 0, math.radians(16)), mat=rock, bevel=0.06),
        C.add_box("RockSlabA", (0.72, 0.64, 0.24), (-0.24, 0.14, 0.17), (math.radians(14), math.radians(-16), 0.4), mat=rock, bevel=0.05),
        C.add_box("RockSlabB", (0.64, 0.58, 0.22), (0.24, -0.14, 0.15), (math.radians(-16), math.radians(18), -0.5), mat=rock, bevel=0.05),
        C.add_box("RockRim", (0.48, 0.45, 0.20), (0.05, 0.22, 0.19), (math.radians(22), 0, 0.2), mat=rock, bevel=0.045),
    ]

    shards = [
        ((0.0, 0.02, 0.22), 0.145, 0.88, (8, -9, 0)),
        ((0.20, 0.12, 0.20), 0.115, 0.66, (-18, 22, 28)),
        ((-0.18, -0.10, 0.19), 0.105, 0.58, (22, -24, -22)),
        ((0.08, -0.22, 0.18), 0.082, 0.44, (-25, -14, 14)),
        ((-0.24, 0.18, 0.18), 0.075, 0.42, (26, 20, 42)),
        ((0.26, -0.16, 0.15), 0.065, 0.34, (-30, 28, -32)),
        ((-0.05, 0.25, 0.17), 0.070, 0.36, (30, -8, 18)),
    ]
    for idx, (pos, r, h, rot) in enumerate(shards):
        prof = [
            (r * 0.85, 0.0),
            (r * 1.0, h * 0.25),
            (r * 0.92, h * 0.72),
            (0.003, h),
        ]
        parts.append(C.add_lathe(
            f"Crystal_{idx}",
            prof,
            segments=6,
            loc=pos,
            rot=tuple(math.radians(a) for a in rot),
            mat=crystal,
            smooth_angle=12.0,
        ))

    C.join_objects(parts, "Element115Crystal")
    C.export_asset("env", "element115_crystal")


def build_ruined_tank():
    C.reset_scene()
    pa_a, pa_n, pa_r = _tex_env("panzer_armor")
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")

    armor = C.make_pbr_mat(
        "TankPanzerArmor",
        (0.30, 0.33, 0.31, 1.0),
        metallic=0.38,
        roughness=0.60,
        albedo_tex=pa_a,
        normal_tex=pa_n,
        roughness_tex=pa_r,
        tint_tex=(0.92, 0.96, 0.94),
        normal_strength=0.72,
    )
    armor_scorch = C.make_pbr_mat(
        "TankScorchedArmor",
        (0.16, 0.165, 0.16, 1.0),
        metallic=0.48,
        roughness=0.72,
        albedo_tex=st_a,
        normal_tex=st_n,
        roughness_tex=st_r,
        tint_tex=(0.45, 0.42, 0.40),
        normal_strength=0.85,
    )
    dark_steel = C.make_pbr_mat("TankDarkSteel", (0.10, 0.11, 0.11, 1.0), metallic=0.72, roughness=0.50, albedo_tex=st_a, normal_tex=st_n, tint_tex=(0.30, 0.32, 0.34))
    treads = C.make_pbr_mat("TankTreads", (0.08, 0.075, 0.07, 1.0), metallic=0.52, roughness=0.78, albedo_tex=st_a, normal_tex=st_n, tint_tex=(0.35, 0.30, 0.26))
    rubber = C.make_pbr_mat("TankWheelRubber", (0.045, 0.045, 0.048, 1.0), metallic=0.05, roughness=0.88)

    parts = []
    tilt_y = math.radians(-2.2)

    # 1. Lofted Panzer IV Armor Hull + Sloped Upper/Lower Glacis + Overhanging Sponsons
    hull_slices = [
        (-2.45, 0.72, 0.92, 0.36, 1.04),
        (-2.20, 0.74, 1.18, 0.32, 1.18),
        (-0.85, 0.74, 1.24, 0.32, 1.22),
        ( 1.20, 0.74, 1.24, 0.32, 1.22),
        ( 1.95, 0.72, 1.18, 0.34, 1.16),
        ( 2.48, 0.68, 1.08, 0.56, 0.92),
    ]
    hull_rings = []
    for y, bw, tw, zb, zt in hull_slices:
        hull_rings.append([
            (-bw, y, zb), (bw, y, zb), (tw, y, (zb + zt) * 0.52),
            (tw * 0.96, y, zt), (-tw * 0.96, y, zt), (-tw, y, (zb + zt) * 0.52),
        ])
    parts.append(C.add_ring_loft("MainHull", hull_rings, rot=(0, tilt_y, 0), mat=armor, smooth_angle=25.0, uv_scale=0.65))

    parts.append(C.add_box("GlacisPlate", (2.16, 0.64, 0.36), (0, 2.04, 0.98), (math.radians(-16), tilt_y, 0), mat=armor, bevel=0.025, uv_scale=0.65))
    parts.append(C.add_box("DriverVisor", (0.48, 0.24, 0.22), (-0.42, 1.88, 1.16), (0, tilt_y, 0), mat=dark_steel, bevel=0.015))
    parts.append(C.add_sphere("HullMGBall", 0.14, (1, 1, 1), (0.46, 2.02, 1.10), mat=dark_steel))
    parts.append(C.add_hollow_barrel("HullMGBbl", r_outer=0.022, r_inner=0.012, length=0.45, loc=(0.46, 2.25, 1.10), rot=(0, 0, math.radians(-8)), mat=dark_steel))
    for st_i in range(4):
        parts.append(C.add_box(f"SpareTrack_{st_i}", (0.36, 0.08, 0.22), (-0.42 + st_i * 0.38, 2.38, 0.72), (math.radians(24), tilt_y, 0), mat=treads, bevel=0.0))

    parts.append(C.add_box("EngineDeck", (2.06, 1.38, 0.14), (0, -1.52, 1.24), (0, tilt_y, 0), mat=armor_scorch, bevel=0.02, uv_scale=0.75))
    for li in range(7):
        parts.append(C.add_box(f"Louver_{li}", (1.56, 0.08, 0.05), (0, -2.02 + li * 0.16, 1.32), (math.radians(22), tilt_y, 0), mat=dark_steel, bevel=0.0))
    parts.append(C.add_cyl("ExhaustMuffler", 0.13, 1.02, (0, -2.52, 0.68), (0, math.radians(90), 0), vertices=12, mat=armor_scorch, bevel=0.0))
    parts.append(C.add_cyl("FuelDrumL", 0.22, 0.78, (-0.58, -1.96, 1.46), (0, math.radians(90), 0), vertices=12, mat=treads, bevel=0.0))
    parts.append(C.add_cyl("FuelDrumR", 0.22, 0.78, (0.58, -1.96, 1.46), (0, math.radians(90), 0), vertices=12, mat=treads, bevel=0.0))

    # 2. Track Running Gear (16 Dished Roadwheels + Drive Sprockets + Idlers + Return Rollers + Wrapped Track Cleat Belt)
    wheel_prof = [
        (0.28, -0.09), (0.28, 0.09), (0.23, 0.095), (0.21, 0.05),
        (0.11, 0.05), (0.09, 0.105), (0.01, 0.105)
    ]
    for side_idx, sx in enumerate((-1.18, 1.18)):
        parts.append(C.add_box(f"Fender_{side_idx}", (0.54, 4.95, 0.07), (sx, 0.02, 0.96), (0, tilt_y, 0), mat=armor, bevel=0.015, uv_scale=0.65))
        for wi in range(8):
            wy = -1.78 + wi * 0.51
            parts.append(C.add_lathe(f"RoadWheel_{side_idx}_{wi}", wheel_prof, segments=10, loc=(sx, wy, 0.30), rot=(0, math.radians(90 if sx > 0 else -90), 0), mat=armor))
            parts.append(C.add_cyl(f"Tire_{side_idx}_{wi}", 0.295, 0.14, (sx, wy, 0.30), (0, math.radians(90), 0), vertices=10, mat=rubber, bevel=0.0))
        parts.append(C.add_gear(f"Sprocket_{side_idx}", teeth=10, r_outer=0.38, r_root=0.31, r_bore=0.08, thickness=0.22, spokes=4, loc=(sx, 2.24, 0.56), rot=(0, 0, math.radians(90)), mat=dark_steel))
        parts.append(C.add_cyl(f"Idler_{side_idx}", 0.31, 0.22, (sx, -2.26, 0.54), (0, math.radians(90), 0), vertices=10, mat=dark_steel, bevel=0.0))
        for ri in range(4):
            parts.append(C.add_cyl(f"Return_{side_idx}_{ri}", 0.095, 0.18, (sx, -1.5 + ri * 1.0, 0.78), (0, math.radians(90), 0), vertices=10, mat=treads, bevel=0.0))

        track_loop = [
            (sx, -1.85, 0.03), (sx, 0.0, 0.03), (sx, 1.85, 0.03),
            (sx, 2.48, 0.38), (sx, 2.42, 0.84),
            (sx, 1.50, 0.88), (sx, 0.0, 0.88), (sx, -1.50, 0.88),
            (sx, -2.42, 0.80), (sx, -2.48, 0.36), (sx, -1.85, 0.03),
        ]
        for ti in range(len(track_loop) - 1):
            p0 = track_loop[ti]
            p1 = track_loop[ti + 1]
            dy = p1[1] - p0[1]
            dz = p1[2] - p0[2]
            seg_len = math.hypot(dy, dz)
            mid_y = (p0[1] + p1[1]) * 0.5
            mid_z = (p0[2] + p1[2]) * 0.5
            ang = math.atan2(dz, dy)
            parts.append(C.add_box(f"TrackSeg_{side_idx}_{ti}", (0.44, seg_len + 0.06, 0.06), (sx, mid_y, mid_z), (ang, 0, 0), mat=treads, bevel=0.0))
            steps = max(1, int(seg_len / 0.34))
            for gi in range(steps):
                t = (gi + 0.5) / steps
                parts.append(C.add_box(
                    f"Grouser_{side_idx}_{ti}_{gi}",
                    (0.46, 0.09, 0.035),
                    (sx, p0[1] + dy * t, p0[2] + dz * t),
                    (ang, 0, 0),
                    mat=dark_steel,
                    bevel=0.0,
                ))

    skirt_cfg = [
        (-1.46, -1.65, 0.68, (0, math.radians(-4), 0)),
        (-1.47, -0.55, 0.66, (math.radians(3), math.radians(5), math.radians(-2))),
        (-1.46,  0.55, 0.68, (0, math.radians(-2), 0)),
        ( 1.46, -1.65, 0.68, (0, math.radians(3), 0)),
        ( 1.47, -0.55, 0.66, (math.radians(-4), math.radians(-6), math.radians(3))),
        ( 1.46,  0.55, 0.68, (0, math.radians(2), 0)),
        ( 1.46,  1.62, 0.67, (math.radians(6), math.radians(8), math.radians(-4))),
    ]
    for idx, (skx, sky, skz, skrot) in enumerate(skirt_cfg):
        parts.append(C.add_box(f"Schuerzen_{idx}", (0.045, 1.02, 0.60), (skx, sky, skz), skrot, mat=armor, bevel=0.008, uv_scale=0.65))

    # 3. Sloped Octagonal Panzer IV Turret + Turret Schuerzen + Stowage Bin + Saukopf Mantlet + 75mm Hollow Cannon
    t_yaw = math.radians(-18.0)
    cy, sx_off = math.cos(t_yaw), math.sin(t_yaw)
    turret_pts = []
    for scale_r, zt in ((1.04, 1.24), (1.00, 1.44), (0.86, 1.82)):
        pts_8 = [
            (-0.62 * scale_r,  1.02 * scale_r, zt),
            ( 0.62 * scale_r,  1.02 * scale_r, zt),
            ( 1.04 * scale_r,  0.34 * scale_r, zt),
            ( 0.94 * scale_r, -0.78 * scale_r, zt),
            ( 0.52 * scale_r, -1.16 * scale_r, zt),
            (-0.52 * scale_r, -1.16 * scale_r, zt),
            (-0.94 * scale_r, -0.78 * scale_r, zt),
            (-1.04 * scale_r,  0.34 * scale_r, zt),
        ]
        rot_ring = []
        for px, py, pz in pts_8:
            rx = px * cy - py * sx_off
            ry = px * sx_off + py * cy + 0.15
            rot_ring.append((rx, ry, pz))
        turret_pts.append(rot_ring)
    parts.append(C.add_ring_loft("PanzerTurret", turret_pts, mat=armor, smooth_angle=25.0, uv_scale=0.65))

    def _tur_pt(lx, ly, lz):
        return (lx * cy - ly * sx_off, lx * sx_off + ly * cy + 0.15, lz)

    parts.append(C.add_box("Rommelkiste", (1.02, 0.42, 0.42), _tur_pt(0, -1.32, 1.54), (0, 0, t_yaw), mat=armor_scorch, bevel=0.015))
    cup_pos = _tur_pt(-0.26, -0.25, 1.94)
    parts.append(C.add_cyl("CupolaBase", 0.34, 0.24, cup_pos, vertices=12, mat=dark_steel))
    parts.append(C.add_cyl("CupolaHatch", 0.30, 0.06, (cup_pos[0] + 0.18, cup_pos[1], cup_pos[2] + 0.18), (0, math.radians(-42), t_yaw), vertices=12, mat=armor))

    for ts_idx, (lx, ly, yaw_off) in enumerate((
        (-1.14,  0.22, -6),
        (-1.06, -0.76,  24),
        ( 1.14,  0.22,  6),
        ( 1.06, -0.76, -24),
    )):
        parts.append(C.add_box(f"TurretSkirt_{ts_idx}", (0.04, 0.96, 0.62), _tur_pt(lx, ly, 1.54), (0, 0, t_yaw + math.radians(yaw_off)), mat=armor, bevel=0.008, uv_scale=0.65))

    mantlet_pos = _tur_pt(0, 1.06, 1.54)
    parts.append(C.add_box("SaukopfMantlet", (0.74, 0.42, 0.44), mantlet_pos, (math.radians(-6), 0, t_yaw), mat=armor_scorch, bevel=0.06))
    parts.append(C.add_cyl("RecoilSleeve", 0.15, 0.72, _tur_pt(0, 1.38, 1.56), (math.radians(84), 0, t_yaw), vertices=12, mat=dark_steel, bevel=0.0))
    parts.append(C.add_hollow_barrel(
        "MainCannon75mm",
        r_outer=0.095,
        r_inner=0.056,
        length=2.85,
        loc=_tur_pt(0, 2.75, 1.70),
        rot=(math.radians(-6), 0, t_yaw),
        segments=12,
        mat=dark_steel,
    ))
    mb_prof = [
        (0.11, -0.18), (0.165, -0.14), (0.165, -0.04), (0.125, -0.02),
        (0.125,  0.04), (0.165,  0.06), (0.165,  0.16), (0.105,  0.20), (0.062, 0.20),
    ]
    parts.append(C.add_lathe("MuzzleBrake", mb_prof, segments=12, loc=_tur_pt(0, 4.24, 1.86), rot=(math.radians(-84), 0, t_yaw), mat=armor_scorch))

    C.join_objects(parts, "RuinedTank")
    C.export_asset("env", "ruined_tank")


def build_sandbag_wall():
    C.reset_scene()
    bu_a, bu_n, bu_r = _tex_env("burlap")
    cw_a, cw_n, cw_r = _tex_env("cc0_planks")

    bag = C.make_pbr_mat("SandbagCloth", (0.38, 0.32, 0.22, 1.0), roughness=0.95, albedo_tex=bu_a, normal_tex=bu_n, roughness_tex=bu_r, tint_tex=(0.76, 0.68, 0.56), normal_strength=0.90)
    stake = C.make_pbr_mat("SandbagStake", (0.34, 0.24, 0.16, 1.0), roughness=0.86, albedo_tex=cw_a, normal_tex=cw_n, roughness_tex=cw_r, tint_tex=(0.72, 0.64, 0.56))

    def _add_pinched_bag(name, loc, rot_deg):
        rings = []
        for t in (-1.0, -0.78, -0.45, 0.0, 0.45, 0.78, 1.0):
            x = t * 0.305
            bulge = math.cos(t * math.pi * 0.46) ** 0.7
            ry = 0.075 + 0.115 * bulge
            rz = 0.036 + 0.075 * bulge
            ring = []
            for s in range(10):
                ang = (s / 10) * 2.0 * math.pi
                z_val = math.sin(ang) * rz
                if z_val < 0:
                    z_val *= 0.75
                ring.append((x, math.cos(ang) * ry, z_val))
            rings.append(ring)
        return C.add_ring_loft(name, rings, loc=loc, rot=tuple(math.radians(a) for a in rot_deg), mat=bag, smooth_angle=55.0, uv_scale=6.0)

    parts = [
        C.add_box("StakeL", (0.09, 0.09, 0.96), (-1.22, 0.22, 0.46), (math.radians(8), 0, 0), mat=stake, bevel=0.01),
        C.add_box("StakeR", (0.09, 0.09, 0.96), (1.22, 0.22, 0.46), (math.radians(8), 0, 0), mat=stake, bevel=0.01),
        C.add_box("CrossBrace", (2.52, 0.05, 0.08), (0, 0.25, 0.56), (0, 0, 0), mat=stake, bevel=0.008),
    ]
    for row in range(3):
        z = 0.10 + row * 0.185
        count = 4 - (row % 2)
        for i in range(count):
            x = (i - (count - 1) * 0.5) * 0.57
            jy = math.cos(row * 2.1 + i * 1.9) * 0.025
            jrot = ((i - 1) * 2.5, math.sin(row * 1.7 + i) * 3.5, math.sin(row * 2.3 + i * 1.7) * 5.0)
            parts.append(_add_pinched_bag(f"Bag_{row}_{i}", (x, jy, z), jrot))

    C.join_objects(parts, "SandbagWall")
    C.export_asset("env", "sandbag_wall")


def build_crate_military():
    C.reset_scene()
    wc_a, wc_n, wc_r = _tex_env("wood_crate")
    cw_a, cw_n, cw_r = _tex_env("cc0_planks")
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")
    olive = C.make_pbr_mat("CrateOlive", (0.28, 0.34, 0.22, 1.0), roughness=0.80, albedo_tex=wc_a, normal_tex=wc_n, roughness_tex=wc_r)
    trim = C.make_pbr_mat("CrateTrim", (0.24, 0.28, 0.18, 1.0), roughness=0.82, albedo_tex=cw_a, normal_tex=cw_n, roughness_tex=cw_r, tint_tex=(0.68, 0.74, 0.56))
    iron = C.make_pbr_mat("CrateIron", (0.16, 0.17, 0.18, 1.0), metallic=0.75, roughness=0.50, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.45, 0.46, 0.48))

    parts = [
        C.add_box("CoreBox", (1.06, 0.72, 0.64), (0, 0, 0.32), mat=olive, bevel=0.01),
        C.add_box("LidSlab", (1.14, 0.78, 0.075), (0, 0, 0.68), mat=trim, bevel=0.012),
    ]
    for sz in (0.04, 0.61):
        parts.append(C.add_box(f"Rail_{sz}", (1.12, 0.76, 0.07), (0, 0, sz), mat=trim, bevel=0.008))
    for sx in (-0.52, 0.52):
        for sy in (-0.34, 0.34):
            parts.append(C.add_box(f"Corner_{sx}_{sy}", (0.08, 0.08, 0.64), (sx, sy, 0.32), mat=trim, bevel=0.006))
        parts.append(C.add_torus(f"Handle_{sx}", 0.06, 0.012, (sx * 1.11, 0, 0.34), (0, math.radians(90), 0), mat=iron))
    for sy in (-0.365, 0.365):
        parts.append(C.add_box(f"DiagF_{sy}", (0.98, 0.03, 0.075), (0, sy, 0.32), (0, math.radians(28), 0), mat=trim, bevel=0.005))
    for rx in (-0.40, 0.40):
        parts.append(C.add_box(f"IronStrap_{rx}", (0.06, 0.80, 0.73), (rx, 0, 0.365), mat=iron, bevel=0.005))

    C.join_objects(parts, "CrateMilitary")
    C.export_asset("env", "crate_military")


def build_barrel_rusted():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")
    rust = C.make_pbr_mat(
        "BarrelRust",
        (0.42, 0.24, 0.16, 1.0),
        metallic=0.45,
        roughness=0.68,
        albedo_tex=st_a,
        normal_tex=st_n,
        roughness_tex=st_r,
        tint_tex=(0.74, 0.52, 0.40),
        normal_strength=0.85,
    )
    cap = C.make_pbr_mat("BarrelBung", (0.14, 0.14, 0.15, 1.0), metallic=0.80, roughness=0.42)

    drum_prof = [
        (0.02, 0.015), (0.31, 0.015), (0.315, 0.035), (0.30, 0.05),
        (0.305, 0.29), (0.328, 0.31), (0.305, 0.33),
        (0.305, 0.58), (0.328, 0.60), (0.305, 0.62),
        (0.305, 0.88), (0.315, 0.90), (0.30, 0.92), (0.285, 0.895), (0.02, 0.895),
    ]
    parts = [
        C.add_lathe("SwagedDrum", drum_prof, segments=22, mat=rust),
        C.add_cyl("BungLarge", 0.038, 0.022, (0.16, 0.0, 0.905), mat=cap),
        C.add_cyl("BungSmall", 0.022, 0.022, (-0.18, 0.08, 0.905), mat=cap),
    ]
    C.join_objects(parts, "BarrelRusted")
    C.export_asset("env", "barrel_rusted")


def build_light_cage():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")
    iron = C.make_pbr_mat("CageIron", (0.16, 0.17, 0.19, 1.0), metallic=0.82, roughness=0.45, albedo_tex=st_a, normal_tex=st_n, tint_tex=(0.45, 0.46, 0.48))
    bulb = C.make_pbr_mat("WarmBulb", (1.0, 0.66, 0.25, 1.0), roughness=0.12, emission=(1.0, 0.60, 0.20), emission_strength=2.8)
    parts = [
        C.add_cyl("MountPlate", 0.15, 0.05, (0, 0, 0), (math.radians(90), 0, 0), mat=iron),
        C.add_cyl("SocketNeck", 0.065, 0.08, (0, -0.05, 0), (math.radians(90), 0, 0), mat=iron),
        C.add_sphere("BulbGlass", 0.085, (1.0, 1.25, 1.0), (0, -0.14, 0), mat=bulb),
        C.add_torus("CageBandA", 0.115, 0.008, (0, -0.13, 0), (math.radians(90), 0, 0), mat=iron),
        C.add_torus("CageBandB", 0.088, 0.007, (0, -0.22, 0), (math.radians(90), 0, 0), mat=iron),
    ]
    for r_i in range(4):
        ang = (r_i / 4.0) * math.pi
        cx, cz = math.cos(ang), math.sin(ang)
        pts = [
            (cx * 0.118, -0.04, cz * 0.118),
            (cx * 0.118, -0.16, cz * 0.118),
            (cx * 0.065, -0.25, cz * 0.065),
            (-cx * 0.065, -0.25, -cz * 0.065),
            (-cx * 0.118, -0.16, -cz * 0.118),
            (-cx * 0.118, -0.04, -cz * 0.118),
        ]
        parts.append(C.add_tube_pipe(f"GuardWire_{r_i}", pts, radius=0.007, segments=6, mat=iron))

    C.join_objects(parts, "LightCage")
    C.export_asset("env", "light_cage")


def build_lab_pod():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_metal_plate")
    zf_a, zf_n, zf_r = _tex_env("zombie_flesh")
    br_a, br_n, br_r = _tex_wpn("brass")

    steel = C.make_pbr_mat("PodSteel", (0.24, 0.27, 0.30, 1.0), metallic=0.80, roughness=0.40, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.50, 0.54, 0.58))
    brass = C.make_pbr_mat("PodBrass", (0.70, 0.50, 0.18, 1.0), metallic=0.86, roughness=0.30, albedo_tex=br_a, normal_tex=br_n)
    copper = C.make_pbr_mat("PodCopper", (0.78, 0.42, 0.18, 1.0), metallic=0.88, roughness=0.30)
    valve_red = C.make_pbr_mat("PodValveRed", (0.68, 0.10, 0.08, 1.0), metallic=0.3, roughness=0.45)

    specimen = C.make_pbr_mat("SpecimenFlesh", (0.38, 0.48, 0.34, 1.0), roughness=0.62, albedo_tex=zf_a, normal_tex=zf_n)
    bone_mat = C.make_pbr_mat("SpecimenBone", (0.68, 0.66, 0.56, 1.0), roughness=0.62)
    organ_glow = C.make_pbr_mat("SpecimenGlow", (0.12, 0.94, 0.72, 1.0), roughness=0.22, emission=(0.12, 0.94, 0.72), emission_strength=1.35)
    fluid = C.make_pbr_mat("PodFluid", (0.04, 0.42, 0.48, 1.0), roughness=0.08, emission=(0.04, 0.58, 0.64), emission_strength=0.32, alpha=0.26)
    gauge_mat = C.make_pbr_mat("PodGaugeFace", (0.95, 0.92, 0.84, 1.0), roughness=0.35, albedo_tex=os.path.join(C.TEX_DIR, "props", "pap_gauge.png"))

    solid = [
        C.add_lathe("PodBase", [(0.68, 0.0), (0.68, 0.14), (0.62, 0.24), (0.52, 0.34), (0.04, 0.34)], segments=12, mat=steel),
        C.add_lathe("PodCap", [(0.04, 2.18), (0.54, 2.18), (0.64, 2.28), (0.66, 2.46), (0.48, 2.52), (0.04, 2.52)], segments=12, mat=steel),
        C.add_torus("RingBot", 0.52, 0.025, (0, 0, 0.68), mat=brass),
        C.add_torus("RingTop", 0.52, 0.025, (0, 0, 1.88), mat=brass),
        C.add_torus("CoreEmitter", 0.26, 0.020, (0, 0, 0.37), mat=organ_glow),
    ]
    for pi in range(4):
        ang = pi * math.pi * 0.5 + math.radians(45)
        px, py = math.cos(ang) * 0.55, math.sin(ang) * 0.55
        solid.append(C.add_cyl(f"Buttress_{pi}", 0.052, 2.16, (px, py, 1.26), vertices=12, mat=steel))
        solid.append(C.add_cyl(f"CollarB_{pi}", 0.072, 0.08, (px, py, 0.38), vertices=12, mat=brass))
        solid.append(C.add_cyl(f"CollarT_{pi}", 0.072, 0.08, (px, py, 2.14), vertices=12, mat=brass))

    solid.append(C.add_tube_pipe("LabPipe", [(0.56, -0.10, 0.22), (0.64, -0.10, 0.42), (0.64, -0.10, 1.18), (0.56, -0.10, 1.32)], radius=0.028, segments=8, mat=copper))
    solid.append(C.add_box("ControlBox", (0.14, 0.24, 0.32), (0.58, -0.04, 0.92), mat=steel, bevel=0.01))
    solid.append(C.add_cyl("GaugeBezel", 0.085, 0.05, (0.58, -0.14, 1.00), (math.radians(90), 0, 0), mat=brass))
    solid.append(C.add_torus("ValveWheel", 0.085, 0.014, (0.68, -0.02, 0.78), (0, math.radians(90), 0), mat=valve_red))

    body_rings = [
        [(math.cos(a) * 0.075, math.sin(a) * 0.055, 0.92) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.095, -0.01 + math.sin(a) * 0.072, 1.12) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.155, -0.02 + math.sin(a) * 0.110, 1.36) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.175, -0.01 + math.sin(a) * 0.115, 1.54) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.068,  0.01 + math.sin(a) * 0.065, 1.66) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.112, -0.04 + math.sin(a) * 0.135, 1.82) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.120, -0.01 + math.sin(a) * 0.125, 1.94) for a in [i * math.pi / 6 for i in range(12)]],
        [(math.cos(a) * 0.045,  0.00 + math.sin(a) * 0.050, 2.02) for a in [i * math.pi / 6 for i in range(12)]],
    ]
    solid.append(C.add_ring_loft("SpecimenBody", body_rings, mat=specimen, smooth_angle=52.0))
    solid.append(C.add_sphere("SpecEyeL", 0.018, (1, 1, 1), (-0.042, -0.155, 1.86), mat=organ_glow))
    solid.append(C.add_sphere("SpecEyeR", 0.018, (1, 1, 1), (0.042, -0.155, 1.86), mat=organ_glow))
    for r_i in range(5):
        rz = 1.24 + r_i * 0.068
        for side in (-1.0, 1.0):
            pts = [
                (side * 0.02, 0.06, rz),
                (side * 0.14, 0.01, rz - 0.015),
                (side * 0.13, -0.10, rz - 0.03),
                (side * 0.04, -0.125, rz - 0.035),
            ]
            solid.append(C.add_tube_pipe(f"SpecRib_{side}_{r_i}", pts, radius=0.012, segments=6, mat=bone_mat))
        solid.append(C.add_sphere(f"VertebraGlow_{r_i}", 0.026, (1, 1, 1), (0, 0.075, rz), mat=organ_glow))
    solid.append(C.add_sphere("SpecHeart", 0.048, (1, 1, 1), (0.02, -0.09, 1.44), mat=organ_glow))
    solid.append(C.add_tube_pipe("SpecArmL", [(-0.17, 0.0, 1.50), (-0.25, -0.12, 1.24), (-0.18, -0.22, 1.02)], radii=[0.042, 0.034, 0.026], mat=specimen))
    solid.append(C.add_tube_pipe("SpecArmR", [(0.17, 0.0, 1.50), (0.25, -0.12, 1.24), (0.18, -0.22, 1.02)], radii=[0.042, 0.034, 0.026], mat=specimen))
    solid.append(C.add_tube_pipe("SpecLegL", [(-0.06, 0.0, 0.94), (-0.11, -0.06, 0.72), (-0.08, 0.04, 0.48)], radii=[0.052, 0.040, 0.030], mat=specimen))
    solid.append(C.add_tube_pipe("SpecLegR", [(0.06, 0.0, 0.94), (0.11, -0.06, 0.72), (0.08, 0.04, 0.48)], radii=[0.052, 0.040, 0.030], mat=specimen))

    C.join_objects(solid, "LabPodCore")

    C.add_textured_disc("PodGaugeDial", 0.072, vertices=24, loc=(0.58, -0.168, 1.00), mat=gauge_mat)
    glass = C.add_cyl("GlassTube", 0.45, 1.88, (0, 0, 1.26), vertices=24, mat=fluid)
    C.auto_uv_box(glass)
    C.export_asset("env", "lab_pod")


def build_teleporter_pad():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_metal_plate")
    steel = C.make_pbr_mat("PadSteel", (0.22, 0.25, 0.28, 1.0), metallic=0.80, roughness=0.40, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.50, 0.54, 0.58))
    copper = C.make_pbr_mat("PadCopper", (0.76, 0.40, 0.16, 1.0), metallic=0.88, roughness=0.28)
    ceramic = C.make_pbr_mat("PadCeramic", (0.72, 0.72, 0.68, 1.0), roughness=0.25)
    glow = C.make_pbr_mat("PadGlow", (0.10, 0.90, 1.0, 1.0), roughness=0.14, emission=(0.10, 0.90, 1.0), emission_strength=2.2)

    parts = [
        C.add_lathe("StepDeck", [(1.95, 0.0), (1.92, 0.12), (1.68, 0.16), (1.62, 0.24), (0.05, 0.24)], segments=12, mat=steel),
        C.add_torus("GlowRingOuter", 1.44, 0.045, (0, 0, 0.25), mat=glow),
        C.add_torus("GlowRingInner", 0.92, 0.025, (0, 0, 0.25), mat=copper),
    ]
    insul_prof = [
        (0.14, 0.22), (0.12, 1.15), (0.18, 1.22), (0.18, 1.30), (0.10, 1.36),
        (0.17, 1.42), (0.17, 1.50), (0.10, 1.56), (0.14, 1.82),
    ]
    for p_idx, (px, py) in enumerate(((-1.62, 0.0), (1.62, 0.0), (0.0, 1.62))):
        parts.append(C.add_lathe(f"Pylon_{p_idx}", insul_prof, segments=14, loc=(px, py, 0.0), mat=ceramic))
        parts.append(C.add_coil_spring(
            f"PylonWinding_{p_idx}",
            major_r=0.155,
            wire_r=0.018,
            length=0.55,
            turns=5.0,
            steps_per_turn=12,
            loc=(px, py, 0.72),
            rot=(math.radians(90), 0, 0),
            mat=copper,
        ))
        parts.append(C.add_torus(f"PylonArc_{p_idx}", 0.22, 0.022, (px, py, 1.84), mat=glow))
        parts.append(C.add_sphere(f"PylonOrb_{p_idx}", 0.16, (1, 1, 1), (px, py, 1.98), mat=glow))
        parts.append(C.add_tube_pipe(f"FeedCable_{p_idx}", [(px * 0.90, py * 0.90, 0.26), (px * 0.78, py * 0.78, 0.26)], radius=0.036, mat=copper))

    C.join_objects(parts, "TeleporterPad")
    C.export_asset("env", "teleporter_pad")


def build_blast_door():
    """3.4m x 3.2m Vaulted Bunker Blast Door centered at (0, 0, 0) for buyable_door.tscn."""
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_metal_plate")
    pa_a, pa_n, pa_r = _tex_env("cc0_rust_steel")

    steel = C.make_pbr_mat("DoorSteel", (0.28, 0.30, 0.32, 1.0), metallic=0.72, roughness=0.46, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.56, 0.58, 0.62), normal_strength=0.9)
    armor = C.make_pbr_mat("DoorArmor", (0.22, 0.24, 0.26, 1.0), metallic=0.65, roughness=0.52, albedo_tex=pa_a, normal_tex=pa_n, roughness_tex=pa_r, tint_tex=(0.45, 0.44, 0.42), normal_strength=0.85)
    brass = C.make_pbr_mat("DoorBrass", (0.68, 0.48, 0.18, 1.0), metallic=0.86, roughness=0.30)
    hazard = C.make_pbr_mat("DoorHazard", (0.78, 0.54, 0.08, 1.0), roughness=0.45)

    parts = [
        C.add_box("CoreSlab", (3.36, 0.22, 3.16), (0, 0, 0), mat=steel, bevel=0.015, uv_scale=0.65),
        C.add_box("FrameTop", (3.44, 0.30, 0.22), (0, 0, 1.50), mat=armor, bevel=0.015, uv_scale=0.65),
        C.add_box("FrameBot", (3.44, 0.30, 0.24), (0, 0, -1.48), mat=armor, bevel=0.015, uv_scale=0.65),
        C.add_box("FrameL", (0.24, 0.30, 3.20), (-1.60, 0, 0), mat=armor, bevel=0.015, uv_scale=0.65),
        C.add_box("FrameR", (0.24, 0.30, 3.20), (1.60, 0, 0), mat=armor, bevel=0.015, uv_scale=0.65),
        C.add_box("MidBelt", (3.16, 0.28, 0.16), (0, 0, 0.24), mat=armor, bevel=0.012),
        C.add_box("HazardStrip", (3.08, 0.25, 0.07), (0, 0, -1.32), mat=hazard, bevel=0.006),
        C.add_box("PlacardPlate", (1.65, 0.26, 0.46), (0, 0, 0.78), mat=armor, bevel=0.01),
    ]
    for rx in (-0.82, 0.82):
        parts.append(C.add_box(f"VertStiff_{rx}", (0.14, 0.26, 2.75), (rx, 0, 0), mat=armor, bevel=0.008))
    for diag_ang in (32, -32):
        parts.append(C.add_box(f"DiagLower_{diag_ang}", (2.40, 0.25, 0.11), (0, 0, -0.58), (0, math.radians(diag_ang), 0), mat=armor, bevel=0.008))
    for hz in (-1.05, 0.0, 1.05):
        parts.append(C.add_cyl(f"HingeL_{hz}", 0.065, 0.36, (-1.62, 0, hz), vertices=12, mat=brass))
        parts.append(C.add_cyl(f"HingeR_{hz}", 0.065, 0.36, (1.62, 0, hz), vertices=12, mat=brass))

    for sy in (-0.15, 0.15):
        parts.append(C.add_torus(f"WheelRim_{sy}", 0.26, 0.028, (0, sy, -0.18), (math.radians(90), 0, 0), mat=brass))
        parts.append(C.add_cyl(f"WheelHub_{sy}", 0.065, 0.09, (0, sy, -0.18), (math.radians(90), 0, 0), mat=brass))
        for sp in range(5):
            ang = (sp / 5.0) * 2.0 * math.pi
            parts.append(C.add_box(
                f"Spoke_{sy}_{sp}",
                (0.24, 0.025, 0.025),
                (math.cos(ang) * 0.13, sy, -0.18 + math.sin(ang) * 0.13),
                (0, -ang, 0),
                mat=brass,
                bevel=0.003,
            ))

    C.join_objects(parts, "BlastDoor")
    C.export_asset("env", "blast_door")


def build_steel_gantry():
    """10.0m modular industrial overhead catwalk bridge along X (deck at Z=0, guardrails to +1.05)."""
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")
    gr_a, gr_n, gr_r = _tex_env("cc0_metal_plate")
    steel = C.make_pbr_mat("GantrySteel", (0.22, 0.24, 0.26, 1.0), metallic=0.76, roughness=0.46, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.50, 0.48, 0.46))
    grate = C.make_pbr_mat("GantryGrate", (0.16, 0.17, 0.18, 1.0), metallic=0.80, roughness=0.52, albedo_tex=gr_a, normal_tex=gr_n, roughness_tex=gr_r, tint_tex=(0.45, 0.48, 0.50))

    parts = []
    for sy in (-0.98, 0.98):
        parts.append(C.add_box(f"MainGirder_{sy}", (10.0, 0.12, 0.36), (0, sy, -0.18), mat=steel, bevel=0.01, uv_scale=0.6))
        parts.append(C.add_box(f"TopRail_{sy}", (10.0, 0.048, 0.048), (0, sy, 1.02), mat=steel, bevel=0.008))
        parts.append(C.add_box(f"MidRail_{sy}", (10.0, 0.040, 0.040), (0, sy, 0.54), mat=steel, bevel=0.006))
        parts.append(C.add_box(f"KickPlate_{sy}", (10.0, 0.035, 0.14), (0, sy, 0.07), mat=steel, bevel=0.005))

    for idx in range(9):
        px = -4.9 + idx * 1.225
        parts.append(C.add_box(f"CrossJoist_{idx}", (0.10, 2.04, 0.18), (px, 0, -0.14), mat=steel, bevel=0.006))
        for sy in (-0.98, 0.98):
            parts.append(C.add_box(f"Post_{idx}_{sy}", (0.055, 0.055, 1.06), (px, sy, 0.50), mat=steel, bevel=0.006))
        if idx < 8:
            mid_x = px + 0.612
            parts.append(C.add_box(f"DiagTruss_{idx}", (1.35, 1.72, 0.06), (mid_x, 0, -0.16), (0, 0, math.radians(22 if idx % 2 == 0 else -22)), mat=steel, bevel=0.005))

    for d_idx in range(28):
        dx = -4.82 + d_idx * 0.355
        parts.append(C.add_box(f"DeckStrip_{d_idx}", (0.28, 1.84, 0.045), (dx, 0, -0.02), mat=grate, bevel=0.005))

    C.join_objects(parts, "SteelGantry")
    C.export_asset("env", "steel_gantry")


def build_wall_pipes():
    """4.0m wide flush-backed industrial 3-pipe manifold + spoked red valve + gauge dial (mounts flush at Y=0 facing -Y)."""
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("cc0_rust_steel")
    steel = C.make_pbr_mat("PipeSteel", (0.22, 0.24, 0.27, 1.0), metallic=0.78, roughness=0.42, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r, tint_tex=(0.56, 0.54, 0.52))
    copper = C.make_pbr_mat("PipeCopper", (0.72, 0.38, 0.16, 1.0), metallic=0.88, roughness=0.30)
    valve_red = C.make_pbr_mat("ValveRed", (0.72, 0.10, 0.08, 1.0), metallic=0.35, roughness=0.45)
    gauge_mat = C.make_pbr_mat("WallGaugeFace", (0.95, 0.92, 0.84, 1.0), roughness=0.32, albedo_tex=os.path.join(C.TEX_DIR, "props", "pap_gauge.png"))

    parts = []
    pipe_specs = [
        (0.085, 0.34, -0.14, steel),
        (0.060, 0.04, -0.12, copper),
        (0.042, -0.22, -0.10, steel),
    ]
    for idx, (pr, pz, py, pmat) in enumerate(pipe_specs):
        parts.append(C.add_cyl(f"PipeMain_{idx}", pr, 4.0, (0, py, pz), (0, math.radians(90), 0), vertices=14, mat=pmat))
        for fx in (-1.35, 0.0, 1.35):
            parts.append(C.add_cyl(f"Flange_{idx}_{fx}", pr * 1.45, 0.06, (fx, py, pz), (0, math.radians(90), 0), vertices=14, mat=steel))

    for bx in (-1.65, -0.55, 0.55, 1.65):
        parts.append(C.add_box(f"Clamp_{bx}", (0.09, 0.26, 0.86), (bx, -0.12, 0.06), mat=steel, bevel=0.008))

    parts.append(C.add_cyl("BypassPipe", 0.048, 0.72, (-0.35, -0.14, 0.06), mat=copper))
    parts.append(C.add_torus("ValveWheel", 0.135, 0.018, (-0.35, -0.28, 0.06), (math.radians(90), 0, 0), mat=valve_red))
    for s in range(4):
        ang = s * math.pi * 0.25
        parts.append(C.add_box(f"ValveSpoke_{s}", (0.24, 0.018, 0.022), (-0.35, -0.28, 0.06), (0, ang, 0), mat=valve_red, bevel=0.002))
    parts.append(C.add_cyl("WallGaugeCup", 0.11, 0.06, (0.38, -0.18, 0.20), (math.radians(90), 0, 0), mat=copper))

    C.join_objects(parts, "WallPipes")
    C.add_textured_disc("WallGaugeDial", 0.095, vertices=24, loc=(0.38, -0.215, 0.20), mat=gauge_mat)
    C.export_asset("env", "wall_pipes")


def build_barbed_wire():
    """2.2m cheval-de-frise timber X-frames + coiled helical barbed wire."""
    C.reset_scene()
    cw_a, cw_n, cw_r = _tex_env("cc0_planks")
    wood = C.make_pbr_mat("WireWood", (0.34, 0.22, 0.14, 1.0), roughness=0.86, albedo_tex=cw_a, normal_tex=cw_n, roughness_tex=cw_r, tint_tex=(0.72, 0.64, 0.56))
    wire = C.make_pbr_mat("RazorWire", (0.16, 0.17, 0.18, 1.0), metallic=0.82, roughness=0.48)

    parts = [
        C.add_box("CenterSpine", (2.20, 0.08, 0.08), (0, 0, 0.44), mat=wood, bevel=0.008),
    ]
    for fx in (-0.95, 0.0, 0.95):
        parts.append(C.add_box(f"LegA_{fx}", (0.075, 0.075, 1.06), (fx, 0, 0.42), (math.radians(38), 0, 0), mat=wood, bevel=0.006))
        parts.append(C.add_box(f"LegB_{fx}", (0.075, 0.075, 1.06), (fx, 0, 0.42), (math.radians(-38), 0, 0), mat=wood, bevel=0.006))

    parts.append(C.add_coil_spring("ConcertinaWire1", major_r=0.22, wire_r=0.011, length=2.15, turns=9.0, steps_per_turn=12, loc=(0, 0, 0.46), rot=(0, 0, math.radians(90)), mat=wire))
    parts.append(C.add_coil_spring("ConcertinaWire2", major_r=0.14, wire_r=0.009, length=2.05, turns=11.0, steps_per_turn=10, loc=(0, 0.06, 0.34), rot=(0, 0, math.radians(90)), mat=wire))

    C.join_objects(parts, "BarbedWire")
    C.export_asset("env", "barbed_wire")


def build_rubble_pile():
    """2.4m x 1.5m x 0.72m bombed masonry debris mound with jagged bent protruding rebar."""
    C.reset_scene()
    rb_a, rb_n, rb_r = _tex_env("cc0_brick")
    bc_a, bc_n, bc_r = _tex_env("cc0_concrete_wall")
    brick = C.make_pbr_mat("RubbleBrick", (0.48, 0.38, 0.32, 1.0), roughness=0.92, albedo_tex=rb_a, normal_tex=rb_n, roughness_tex=rb_r, tint_tex=(0.76, 0.70, 0.66), normal_strength=0.95)
    conc = C.make_pbr_mat("RubbleConcrete", (0.38, 0.40, 0.42, 1.0), roughness=0.90, albedo_tex=bc_a, normal_tex=bc_n, roughness_tex=bc_r, tint_tex=(0.70, 0.72, 0.74), normal_strength=0.95)
    rebar = C.make_pbr_mat("RubbleRebar", (0.24, 0.14, 0.10, 1.0), metallic=0.65, roughness=0.66)

    slabs = [
        ("BaseMound", (2.15, 1.32, 0.26), (0, 0, 0.11), (0, 0, 8), conc),
        ("SlabTiltA", (1.28, 0.78, 0.22), (-0.42, 0.14, 0.26), (14, -22, 18), conc),
        ("SlabTiltB", (1.12, 0.72, 0.24), (0.48, -0.12, 0.28), (-16, 20, -24), brick),
        ("ChunkC",    (0.62, 0.54, 0.34), (-0.08, -0.08, 0.34), (22, 14, 35), brick),
        ("ChunkD",    (0.54, 0.48, 0.26), (0.68, 0.28, 0.18), (12, -16, -40), conc),
        ("ChunkE",    (0.46, 0.42, 0.22), (-0.75, -0.26, 0.15), (-18, 12, 22), brick),
    ]
    parts = [C.add_box(n, sz, loc, tuple(math.radians(a) for a in rot), mat=m, bevel=0.04, uv_scale=0.55) for n, sz, loc, rot, m in slabs]

    rebar_paths = [
        [(-0.22, 0.05, 0.22), (-0.12, -0.02, 0.52), (-0.24, -0.18, 0.74)],
        [( 0.06, 0.12, 0.20), ( 0.18,  0.04, 0.58), ( 0.08, -0.10, 0.78)],
        [( 0.36,-0.08, 0.20), ( 0.52, -0.22, 0.48), ( 0.62, -0.35, 0.62)],
        [(-0.48, 0.18, 0.18), (-0.64,  0.26, 0.44), (-0.72,  0.18, 0.58)],
    ]
    for idx, pts in enumerate(rebar_paths):
        parts.append(C.add_tube_pipe(f"Rebar_{idx}", pts, radius=0.015, segments=6, mat=rebar))

    C.join_objects(parts, "RubblePile")
    C.export_asset("env", "rubble_pile")


if __name__ == "__main__":
    build_barricade_window()
    build_element115_crystal()
    build_ruined_tank()
    build_sandbag_wall()
    build_crate_military()
    build_barrel_rusted()
    build_light_cage()
    build_lab_pod()
    build_teleporter_pad()
    build_blast_door()
    build_steel_gantry()
    build_wall_pipes()
    build_barbed_wire()
    build_rubble_pile()
    print("ALL HIGH-DETAIL PROPS & ARCHITECTURAL KIT PIECES EXPORTED!")
