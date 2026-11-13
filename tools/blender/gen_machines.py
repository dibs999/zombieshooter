"""Generate intricate Call of Duty Zombies machines & power-up collectibles in Blender (.blend + .glb).
- perk_juggernog, perk_speedcola, perk_doubletap, perk_quickrevive, perk_staminup
- mystery_box (charred timber slats, interlocking 3D chains, iron lock & rune, hinged BoxLid w/ 3D '?')
- teddy_bear (burlap plush, stitches, crimson CoD eye)
- pack_a_punch (claw feet, twin helical heater coils, feed rollers, pap_marquee, 3 pap_gauges, brass gears & cyan Tesla coils)
- power_switch (knife-blade breaker box + pivoting SwitchLever)
- electro_trap (ribbed ceramic insulators, copper electromagnet & corona dome)
- powerup_max_ammo, powerup_insta_kill, powerup_double_points, powerup_nuke, powerup_carpenter, powerup_fire_sale
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def _tex_env(name):
    return (
        os.path.join(C.TEX_DIR, "env", f"{name}_albedo.png"),
        os.path.join(C.TEX_DIR, "env", f"{name}_normal.png"),
        os.path.join(C.TEX_DIR, "env", f"{name}_roughness.png"),
    )


def _tex_wpn(name):
    return (
        os.path.join(C.TEX_DIR, "weapons", f"{name}_albedo.png"),
        os.path.join(C.TEX_DIR, "weapons", f"{name}_normal.png"),
        os.path.join(C.TEX_DIR, "weapons", f"{name}_roughness.png"),
    )


def build_perk_machine(key, body_rgb, bottle_rgb):
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("rusted_steel")
    br_a, br_n, br_r = _tex_wpn("brass")

    # Tinted enameled worn sheetmetal body & cream 1950s fridge hood
    body_mat = C.make_pbr_mat(
        f"PerkBody_{key}",
        (*body_rgb, 1.0),
        metallic=0.34,
        roughness=0.44,
        albedo_tex=st_a,
        normal_tex=st_n,
        roughness_tex=st_r,
        tint_tex=tuple(min(1.0, c * 1.45 + 0.14) for c in body_rgb),
        normal_strength=0.45,
    )
    cream_mat = C.make_pbr_mat(
        "PerkCream",
        (0.78, 0.74, 0.64, 1.0),
        metallic=0.08,
        roughness=0.48,
        albedo_tex=st_a,
        normal_tex=st_n,
        tint_tex=(0.94, 0.89, 0.78),
        normal_strength=0.25,
    )
    chrome_mat = C.make_pbr_mat("PerkChrome", (0.74, 0.77, 0.80, 1.0), metallic=0.90, roughness=0.22)
    brass_mat = C.make_pbr_mat("PerkBrass", (0.64, 0.45, 0.16, 1.0), metallic=0.86, roughness=0.30, albedo_tex=br_a, normal_tex=br_n)
    dark_mat = C.make_pbr_mat("PerkDark", (0.07, 0.075, 0.085, 1.0), metallic=0.68, roughness=0.46)
    bay_dark = C.make_pbr_mat("PerkBayDark", (0.03, 0.035, 0.04, 1.0), metallic=0.40, roughness=0.72)
    dome_mat = C.make_pbr_mat(
        f"PerkDome_{key}",
        (*body_rgb, 1.0),
        roughness=0.14,
        emission=body_rgb,
        emission_strength=1.95,
    )
    bottle_mat = C.make_pbr_mat(
        f"PerkBottle_{key}",
        (*bottle_rgb, 1.0),
        roughness=0.10,
        emission=bottle_rgb,
        emission_strength=1.25,
    )
    glass_mat = C.make_pbr_mat(
        "PerkShowcaseGlass",
        (0.78, 0.90, 0.95, 1.0),
        roughness=0.06,
        alpha=0.24,
    )
    marquee_tex = os.path.join(C.TEX_DIR, "props", f"marquee_{key}.png")
    sign_mat = C.make_pbr_mat(
        f"PerkSign_{key}",
        (1.0, 1.0, 1.0, 1.0),
        roughness=0.98,
        specular=0.0,
        emission_strength=0.25,
        emissive_albedo=True,
        albedo_tex=marquee_tex,
    )

    parts = []

    # 1. Footed Plinth & Rounded Streamline 1950s Enamel Cabinet
    parts.append(C.add_box("BasePlinth", (0.94, 0.74, 0.11), (0, 0, 0.055), mat=dark_mat, bevel=0.015, uv_scale=1.8))
    for cx in (-0.42, 0.42):
        for cy in (-0.31, 0.31):
            parts.append(C.add_cyl(f"Foot_{cx}_{cy}", 0.055, 0.06, (cx, cy, 0.03), vertices=12, mat=chrome_mat))

    # Lower Enameled Body (Z=0.10 .. 1.32)
    parts.append(C.add_box("CabinetLower", (0.90, 0.68, 1.22), (0, 0.01, 0.71), mat=body_mat, bevel=0.045, uv_scale=1.6))

    # Lofted Cream Vintage Fridge Hood with crowned arch shoulder (Z=1.32 .. 2.02)
    hood_rings = []
    for hw, hd, z in (
        (0.45, 0.34, 1.32),
        (0.45, 0.34, 1.84),
        (0.43, 0.32, 1.94),
        (0.38, 0.27, 2.00),
        (0.32, 0.22, 2.03),
    ):
        hood_rings.append([
            (-hw, -hd, z), (hw, -hd, z), (hw, hd, z), (-hw, hd, z)
        ])
    parts.append(C.add_ring_loft("CabinetHood", hood_rings, mat=cream_mat, smooth_angle=35.0, uv_scale=1.6))

    # Chrome Wrap-Around Belt & Side Bumpers
    parts.append(C.add_box("ChromeBelt", (0.94, 0.73, 0.055), (0, 0.01, 1.33), mat=chrome_mat, bevel=0.014))
    parts.append(C.add_box("ChromeCrown", (0.86, 0.66, 0.045), (0, 0.01, 1.94), mat=chrome_mat, bevel=0.012))
    for sx in (-0.46, 0.46):
        parts.append(C.add_box(f"SideRib_{sx}", (0.045, 0.72, 1.80), (sx, 0.01, 1.00), mat=chrome_mat, bevel=0.012))
        for lz in range(6):
            parts.append(C.add_box(
                f"SideLouver_{sx}_{lz}",
                (0.024, 0.42, 0.022),
                (sx * 0.99, 0.02, 0.32 + lz * 0.055),
                (0, math.radians(-22 if sx > 0 else 22), 0),
                mat=dark_mat,
                bevel=0.003,
            ))

    # 2. Front Embossed Vending Door, Recessed Selector Panel & Chute
    parts.append(C.add_box("FrontDoorFrame", (0.64, 0.045, 0.98), (0, -0.34, 0.71), mat=chrome_mat, bevel=0.014))
    parts.append(C.add_box("FrontDoorInset", (0.58, 0.045, 0.92), (0, -0.35, 0.71), mat=body_mat, bevel=0.012, uv_scale=1.8))

    parts.append(C.add_box("CoinBezel", (0.40, 0.055, 0.38), (0, -0.375, 0.93), mat=chrome_mat, bevel=0.01))
    parts.append(C.add_box("CoinFace", (0.34, 0.03, 0.32), (0, -0.395, 0.93), mat=dark_mat, bevel=0.005))
    parts.append(C.add_box("CoinSlot", (0.04, 0.035, 0.09), (-0.09, -0.41, 1.00), mat=chrome_mat, bevel=0.004))
    parts.append(C.add_box("CoinReturn", (0.06, 0.035, 0.07), (-0.09, -0.41, 0.87), mat=chrome_mat, bevel=0.005))
    parts.append(C.add_cyl("LatchLever", 0.016, 0.07, (-0.18, -0.395, 0.93), (0, 0, math.radians(20)), mat=chrome_mat))
    for b_idx in range(3):
        parts.append(C.add_box(f"SelBtn_{b_idx}", (0.14, 0.035, 0.045), (0.06, -0.405, 1.01 - b_idx * 0.075), mat=dome_mat, bevel=0.006))

    parts.append(C.add_box("ChuteHousing", (0.38, 0.06, 0.23), (0, -0.375, 0.49), mat=chrome_mat, bevel=0.01))
    parts.append(C.add_box("ChuteCavity", (0.32, 0.05, 0.17), (0, -0.39, 0.49), mat=bay_dark, bevel=0.005))
    parts.append(C.add_box("ChuteFlap", (0.30, 0.018, 0.14), (0, -0.398, 0.50), (math.radians(-10), 0, 0), mat=chrome_mat, bevel=0.004))

    for gz in range(4):
        parts.append(C.add_box(f"FrontGrill_{gz}", (0.48, 0.03, 0.02), (0, -0.37, 0.25 + gz * 0.035), (math.radians(28), 0, 0), mat=dark_mat, bevel=0.002))

    # 3. Proud Illuminated Bottle Showcase Bay (fully in front of CabinetHood Y=-0.34!)
    parts.append(C.add_box("ShowcaseBack", (0.72, 0.018, 0.21), (0, -0.342, 1.49), mat=bay_dark, bevel=0.004))
    parts.append(C.add_box("ShowcaseRimT", (0.76, 0.10, 0.03), (0, -0.382, 1.60), mat=chrome_mat, bevel=0.008))
    parts.append(C.add_box("ShowcaseRimB", (0.76, 0.10, 0.03), (0, -0.382, 1.38), mat=chrome_mat, bevel=0.008))
    parts.append(C.add_box("ShowcaseRimL", (0.035, 0.10, 0.25), (-0.365, -0.382, 1.49), mat=chrome_mat, bevel=0.008))
    parts.append(C.add_box("ShowcaseRimR", (0.035, 0.10, 0.25), (0.365, -0.382, 1.49), mat=chrome_mat, bevel=0.008))

    bottle_prof = [
        (0.002, 0.0), (0.034, 0.004), (0.036, 0.075), (0.030, 0.095),
        (0.014, 0.120), (0.013, 0.155), (0.016, 0.162), (0.013, 0.168), (0.002, 0.169)
    ]
    for bx in (-0.18, 0.0, 0.18):
        parts.append(C.add_lathe(f"Bottle_{bx}", bottle_prof, segments=14, loc=(bx, -0.380, 1.402), mat=bottle_mat))
        parts.append(C.add_cyl(f"BottleCap_{bx}", 0.015, 0.012, (bx, -0.380, 1.573), mat=brass_mat))

    # 4. Hollow Chrome Frame Trim around Marquee & Top Caged Siren Beacon
    parts.append(C.add_box("MarqueeBarT", (0.78, 0.04, 0.025), (0, -0.352, 1.945), mat=chrome_mat, bevel=0.006))
    parts.append(C.add_box("MarqueeBarB", (0.78, 0.04, 0.025), (0, -0.352, 1.625), mat=chrome_mat, bevel=0.006))
    parts.append(C.add_box("MarqueeBarL", (0.03, 0.04, 0.34), (-0.375, -0.352, 1.785), mat=chrome_mat, bevel=0.006))
    parts.append(C.add_box("MarqueeBarR", (0.03, 0.04, 0.34), (0.375, -0.352, 1.785), mat=chrome_mat, bevel=0.006))

    # Beacon Base + Dome + Protective Wire Cage
    parts.append(C.add_lathe(
        "DomeCollar",
        [(0.20, 2.02), (0.19, 2.08), (0.165, 2.11), (0.02, 2.11)],
        segments=20,
        loc=(0, -0.02, 0.0),
        mat=chrome_mat,
    ))
    parts.append(C.add_lathe(
        "GlowDome",
        [(0.145, 2.10), (0.15, 2.18), (0.14, 2.27), (0.105, 2.34), (0.055, 2.38), (0.005, 2.39)],
        segments=20,
        loc=(0, -0.02, 0.0),
        mat=dome_mat,
    ))
    parts.append(C.add_cyl("FinialCap", 0.042, 0.03, (0, -0.02, 2.39), mat=brass_mat))

    # Crossed protective wireframe cage rings & vertical ribs around Beacon
    for rz in (2.17, 2.28):
        parts.append(C.add_torus(f"CageBand_{rz}", 0.168 if rz < 2.22 else 0.152, 0.007, (0, -0.02, rz), major_segments=20, mat=chrome_mat))
    for rib in range(6):
        ang = (rib / 6.0) * 2.0 * math.pi
        cx = math.cos(ang)
        cy = math.sin(ang)
        pts = [
            (cx * 0.175, -0.02 + cy * 0.175, 2.09),
            (cx * 0.172, -0.02 + cy * 0.172, 2.20),
            (cx * 0.148, -0.02 + cy * 0.148, 2.33),
            (cx * 0.050, -0.02 + cy * 0.050, 2.405),
        ]
        parts.append(C.add_tube_pipe(f"CageRib_{rib}", pts, radius=0.0065, segments=6, mat=chrome_mat))

    # Rear Junction Box & Power Conduit
    parts.append(C.add_box("RearBreaker", (0.28, 0.08, 0.34), (0.20, 0.36, 0.65), mat=dark_mat, bevel=0.01))
    parts.append(C.add_tube_pipe("RearCable", [(0.20, 0.36, 0.48), (0.20, 0.39, 0.25), (0.24, 0.38, 0.03)], radius=0.018, segments=8, mat=dark_mat))

    C.join_objects(parts, f"PerkCabinet_{key}")

    # Separate glass pane IN FRONT of the bottles (-0.422) and UV-intact Marquee plane
    C.add_box(f"ShowcaseGlass_{key}", (0.68, 0.008, 0.19), (0, -0.422, 1.49), mat=glass_mat, bevel=0.0)
    C.add_textured_plane(f"Marquee_{key}", 0.72, 0.32, loc=(0, -0.369, 1.78), mat=sign_mat)

    C.export_asset("props", f"perk_{key}")


def build_mystery_box():
    C.reset_scene()
    cw_a, cw_n, cw_r = _tex_env("charred_wood")
    st_a, st_n, st_r = _tex_env("rusted_steel")
    br_a, br_n, br_r = _tex_wpn("brass")

    wood_mat = C.make_pbr_mat(
        "BoxCharredWood",
        (0.46, 0.36, 0.26, 1.0),
        roughness=0.72,
        albedo_tex=cw_a,
        normal_tex=cw_n,
        roughness_tex=cw_r,
        normal_strength=0.80,
    )
    iron_mat = C.make_pbr_mat(
        "BoxForgedIron",
        (0.18, 0.20, 0.22, 1.0),
        metallic=0.80,
        roughness=0.46,
        albedo_tex=st_a,
        normal_tex=st_n,
        roughness_tex=st_r,
        normal_strength=0.55,
    )
    brass_mat = C.make_pbr_mat("BoxBrass", (0.72, 0.50, 0.18, 1.0), metallic=0.86, roughness=0.28, albedo_tex=br_a, normal_tex=br_n)
    dark_mat = C.make_pbr_mat("BoxDarkCavity", (0.04, 0.03, 0.025, 1.0), metallic=0.2, roughness=0.85)
    rune_mat = C.make_pbr_mat("BoxRune", (0.14, 0.94, 1.0, 1.0), roughness=0.18, emission=(0.18, 0.94, 1.0), emission_strength=2.2)
    gold_glow = C.make_pbr_mat("BoxGoldGlow", (1.0, 0.76, 0.18, 1.0), roughness=0.22, emission=(1.0, 0.72, 0.16), emission_strength=1.55)

    body_parts = []
    # Base floor & 4 horizontal timber courses along walls (individual slightly beveled plank strips)
    body_parts.append(C.add_box("ChestFloor", (1.78, 0.76, 0.08), (0, 0, 0.04), mat=wood_mat, bevel=0.01, uv_scale=1.6))
    body_parts.append(C.add_box("InnerCavern", (1.66, 0.64, 0.44), (0, 0, 0.30), mat=dark_mat, bevel=0.005))
    body_parts.append(C.add_box("InnerGoldGlow", (1.58, 0.56, 0.05), (0, 0, 0.52), mat=gold_glow, bevel=0.006))

    for pz_idx, zc in enumerate((0.12, 0.27, 0.42, 0.56)):
        bow = math.sin(pz_idx * 1.4) * 0.008
        # Front & Back Planks
        for sy in (-0.37, 0.37):
            body_parts.append(C.add_box(f"PlankFB_{pz_idx}_{sy}", (1.82, 0.065, 0.132), (0, sy + bow * (-1 if sy < 0 else 1), zc), mat=wood_mat, bevel=0.012, uv_scale=1.6))
        # Side Planks
        for sx in (-0.88, 0.88):
            body_parts.append(C.add_box(f"PlankLR_{pz_idx}_{sx}", (0.065, 0.76, 0.132), (sx, 0, zc), mat=wood_mat, bevel=0.012, uv_scale=1.6))

    # Iron Corner Straps, Mid Straps, Rivets & Rim Trim
    for sx in (-0.90, 0.90):
        for sy in (-0.39, 0.39):
            body_parts.append(C.add_box(f"CornerPost_{sx}_{sy}", (0.09, 0.09, 0.64), (sx, sy, 0.31), mat=iron_mat, bevel=0.01))
    for rx in (-0.64, 0.0, 0.64):
        body_parts.append(C.add_box(f"BandWrap_{rx}", (0.09, 0.84, 0.61), (rx, 0, 0.305), mat=iron_mat, bevel=0.008))
    body_parts.append(C.add_box("BaseIronSkirt", (1.86, 0.84, 0.08), (0, 0, 0.045), mat=iron_mat, bevel=0.01))

    # Side Carry Ring Handles & Rear Brass Hinges
    for sx in (-0.93, 0.93):
        body_parts.append(C.add_box(f"HandlePlate_{sx}", (0.04, 0.22, 0.18), (sx, 0, 0.34), mat=iron_mat, bevel=0.006))
        body_parts.append(C.add_torus(f"HandleRing_{sx}", 0.075, 0.015, (sx * 1.03, 0, 0.28), (0, math.radians(90), 0), mat=iron_mat))
    for hx in (-0.64, 0.64):
        body_parts.append(C.add_cyl(f"HingePin_{hx}", 0.026, 0.16, (hx, 0.40, 0.62), (0, math.radians(90), 0), mat=brass_mat))

    # Front Heavy Lock Hasp & Glowing Cyan Group 935 Diamond Rune
    body_parts.append(C.add_box("FrontHaspPlate", (0.28, 0.07, 0.28), (0, -0.415, 0.42), mat=iron_mat, bevel=0.01))
    body_parts.append(C.add_cyl("PadlockLoop", 0.042, 0.04, (0, -0.455, 0.34), (math.radians(90), 0, 0), mat=brass_mat))
    body_parts.append(C.add_box("RuneDiamond", (0.14, 0.03, 0.14), (0, -0.45, 0.44), (0, math.radians(45), 0), mat=rune_mat, bevel=0.004))
    body_parts.append(C.add_torus("RuneFrame", 0.10, 0.012, (0, -0.442, 0.44), (math.radians(90), 0, 0), mat=brass_mat))

    # Interlocking 3D Metal Chains draped around corners of the chest (iconically CoD Zombies!)
    chain_pts_front = [(-0.89, -0.42, 0.54), (-0.42, -0.43, 0.32), (0.0, -0.44, 0.24), (0.42, -0.43, 0.32), (0.89, -0.42, 0.54)]
    chain_l = [(-0.92, -0.39, 0.54), (-0.93, 0.0, 0.26), (-0.92, 0.39, 0.54)]
    chain_r = [(0.92, -0.39, 0.54), (0.93, 0.0, 0.26), (0.92, 0.39, 0.54)]
    body_parts.append(C.add_chain("FrontChain", chain_pts_front, link_len=0.072, link_w=0.038, wire_r=0.008, mat=iron_mat))
    body_parts.append(C.add_chain("SideChainL", chain_l, link_len=0.072, link_w=0.038, wire_r=0.008, mat=iron_mat))
    body_parts.append(C.add_chain("SideChainR", chain_r, link_len=0.072, link_w=0.038, wire_r=0.008, mat=iron_mat))

    C.join_objects(body_parts, "BoxBody")

    # Hinged BoxLid MUST have pivot origin at (0, 0.39, 0.62) in Blender -> Godot BoxLid rotation_degrees:x = 82 lifts front (-Y) up!
    lid_parts = []
    # Arch-crowned planks spanning Y in [-0.79 .. 0.01] relative to hinge
    for ly_idx, yc in enumerate((-0.72, -0.52, -0.32, -0.12)):
        z_arch = 0.08 + (0.045 if ly_idx in (1, 2) else 0.0)
        lid_parts.append(C.add_box(f"LidPlank_{ly_idx}", (1.84, 0.19, 0.11), (0, yc, z_arch), mat=wood_mat, bevel=0.012, uv_scale=1.6))
    for rx in (-0.74, 0.0, 0.74):
        lid_parts.append(C.add_box(f"LidIron_{rx}", (0.10, 0.84, 0.155), (rx, -0.39, 0.095), mat=iron_mat, bevel=0.01))
    lid_parts.append(C.add_box("LidRimF", (1.88, 0.07, 0.14), (0, -0.80, 0.07), mat=iron_mat, bevel=0.008))
    lid_parts.append(C.add_box("LidRimB", (1.88, 0.07, 0.14), (0, 0.01, 0.07), mat=iron_mat, bevel=0.008))

    # Sculpted 3D Golden Question Marks (?) protruding on top of lid
    for qx in (-0.40, 0.40):
        q_curve = [
            (qx - 0.055, -0.31, 0.165),
            (qx - 0.045, -0.25, 0.172),
            (qx + 0.005, -0.23, 0.172),
            (qx + 0.055, -0.26, 0.172),
            (qx + 0.055, -0.33, 0.172),
            (qx + 0.005, -0.39, 0.172),
            (qx + 0.000, -0.45, 0.170),
        ]
        lid_parts.append(C.add_tube_pipe(f"QuestionHook_{qx}", q_curve, radius=0.022, segments=10, mat=gold_glow))
        lid_parts.append(C.add_sphere(f"QuestionDot_{qx}", 0.026, (1.0, 1.0, 0.7), (qx + 0.000, -0.525, 0.165), mat=gold_glow))

    lid = C.join_objects(lid_parts, "BoxLid")
    lid.location = (0, 0.39, 0.62)

    C.export_asset("props", "mystery_box")


def build_teddy_bear():
    C.reset_scene()
    bu_a, bu_n, bu_r = _tex_env("burlap")
    fur = C.make_pbr_mat(
        "TeddyBurlap",
        (0.46, 0.30, 0.18, 1.0),
        roughness=0.92,
        albedo_tex=bu_a,
        normal_tex=bu_n,
        roughness_tex=bu_r,
        tint_tex=(0.68, 0.46, 0.28),
        normal_strength=0.75,
    )
    muzzle = C.make_pbr_mat("TeddyMuzzle", (0.58, 0.42, 0.28, 1.0), roughness=0.88, albedo_tex=bu_a, normal_tex=bu_n, tint_tex=(0.82, 0.64, 0.44))
    stitch = C.make_pbr_mat("TeddyStitch", (0.06, 0.05, 0.05, 1.0), roughness=0.7)
    eye_glow = C.make_pbr_mat("TeddyEyeGlow", (1.0, 0.12, 0.04, 1.0), roughness=0.18, emission=(1.0, 0.10, 0.03), emission_strength=2.4)
    button = C.make_pbr_mat("TeddyButton", (0.08, 0.08, 0.09, 1.0), metallic=0.15, roughness=0.35)

    parts = [
        C.add_sphere("Torso", 0.16, (1.0, 0.86, 1.18), (0, 0, 0.20), mat=fur, uv_scale=4.0),
        C.add_sphere("BellyPatch", 0.115, (0.95, 0.55, 1.05), (0, -0.095, 0.20), mat=muzzle, uv_scale=4.0),
        C.add_sphere("Head", 0.135, (1.06, 1.00, 0.98), (0, -0.01, 0.43), mat=fur, uv_scale=4.0),
        C.add_sphere("EarL", 0.048, (1.0, 0.55, 1.0), (-0.115, 0.0, 0.535), mat=fur),
        C.add_sphere("EarR", 0.048, (1.0, 0.55, 1.0), (0.115, 0.0, 0.535), mat=fur),
        C.add_sphere("Snout", 0.058, (1.05, 1.10, 0.85), (0, -0.115, 0.405), mat=muzzle),
        C.add_sphere("Nose", 0.022, (1.2, 0.9, 0.8), (0, -0.172, 0.425), mat=button),
        # Left button eye w/ thread cross + right demonic glowing red CoD eye
        C.add_cyl("EyeBtnL", 0.020, 0.014, (-0.048, -0.128, 0.462), (math.radians(80), 0, math.radians(-16)), mat=button),
        C.add_sphere("EyeGlowR", 0.019, (1, 1, 1), (0.048, -0.126, 0.462), mat=eye_glow),
    ]
    # Crossed stitches along forehead & chest
    for sx, sz, ang in ((-0.02, 0.23, 32), (0.02, 0.23, -32), (-0.02, 0.17, -28), (0.02, 0.17, 28)):
        parts.append(C.add_box(f"Stitch_{sx}_{sz}", (0.032, 0.008, 0.008), (sx, -0.155, sz), (0, math.radians(ang), 0), mat=stitch, bevel=0.001))

    # Rounded Limbs w/ Paw Pads
    parts.append(C.add_tube_pipe("ArmL", [(-0.12, -0.02, 0.30), (-0.19, -0.08, 0.23), (-0.20, -0.15, 0.18)], radius=0.044, radii=[0.040, 0.044, 0.048], mat=fur))
    parts.append(C.add_tube_pipe("ArmR", [(0.12, -0.02, 0.30), (0.19, -0.08, 0.23), (0.20, -0.15, 0.18)], radius=0.044, radii=[0.040, 0.044, 0.048], mat=fur))
    parts.append(C.add_tube_pipe("LegL", [(-0.08, -0.02, 0.09), (-0.11, -0.12, 0.06), (-0.12, -0.22, 0.06)], radius=0.052, radii=[0.048, 0.054, 0.058], mat=fur))
    parts.append(C.add_tube_pipe("LegR", [(0.08, -0.02, 0.09), (0.11, -0.12, 0.06), (0.12, -0.22, 0.06)], radius=0.052, radii=[0.048, 0.054, 0.058], mat=fur))

    C.join_objects(parts, "TeddyBear")
    C.export_asset("props", "teddy_bear")


def build_pack_a_punch():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("rusted_steel")
    pa_a, pa_n, pa_r = _tex_env("panzer_armor")
    br_a, br_n, br_r = _tex_wpn("brass")

    iron = C.make_pbr_mat(
        "PaPIron",
        (0.24, 0.27, 0.31, 1.0),
        metallic=0.72,
        roughness=0.44,
        albedo_tex=st_a,
        normal_tex=st_n,
        roughness_tex=st_r,
        normal_strength=0.65,
    )
    armor = C.make_pbr_mat(
        "PaPArmor",
        (0.20, 0.23, 0.25, 1.0),
        metallic=0.58,
        roughness=0.52,
        albedo_tex=pa_a,
        normal_tex=pa_n,
        roughness_tex=pa_r,
        normal_strength=0.60,
    )
    brass = C.make_pbr_mat(
        "PaPBrass",
        (0.76, 0.56, 0.22, 1.0),
        metallic=0.88,
        roughness=0.28,
        albedo_tex=br_a,
        normal_tex=br_n,
        roughness_tex=br_r,
    )
    copper = C.make_pbr_mat("PaPCopper", (0.78, 0.42, 0.18, 1.0), metallic=0.88, roughness=0.30)
    dark = C.make_pbr_mat("PaPDarkBay", (0.035, 0.04, 0.045, 1.0), metallic=0.55, roughness=0.68)
    cyan_coil = C.make_pbr_mat("PaPCyanCoil", (0.12, 0.92, 1.0, 1.0), roughness=0.14, emission=(0.12, 0.92, 1.0), emission_strength=1.95)
    orange_coil = C.make_pbr_mat("PaPOrangeCoil", (1.0, 0.44, 0.06, 1.0), roughness=0.16, emission=(1.0, 0.42, 0.05), emission_strength=2.15)
    led_red = C.make_pbr_mat("PaPLedRed", (1.0, 0.18, 0.10, 1.0), roughness=0.2, emission=(1.0, 0.16, 0.08), emission_strength=1.5)
    led_grn = C.make_pbr_mat("PaPLedGreen", (0.18, 1.0, 0.35, 1.0), roughness=0.2, emission=(0.18, 1.0, 0.35), emission_strength=1.5)

    pap_marquee_tex = os.path.join(C.TEX_DIR, "props", "pap_marquee.png")
    marquee_mat = C.make_pbr_mat(
        "PaPMarquee",
        (1.0, 1.0, 1.0, 1.0),
        roughness=0.92,
        specular=0.04,
        emission_strength=0.42,
        emissive_albedo=True,
        albedo_tex=pap_marquee_tex,
    )
    pap_gauge_tex = os.path.join(C.TEX_DIR, "props", "pap_gauge.png")
    gauge_mat = C.make_pbr_mat(
        "PaPGaugeFace",
        (0.95, 0.92, 0.84, 1.0),
        roughness=0.75,
        specular=0.06,
        emission_strength=0.18,
        emissive_albedo=True,
        albedo_tex=pap_gauge_tex,
    )

    parts = []

    # 1. 4 Splayed Cast-Iron Claw Feet + Sub-Chassis Skid
    for fx in (-0.72, 0.72):
        for fy in (-0.42, 0.42):
            sx_s = 1.0 if fx > 0 else -1.0
            sy_s = 1.0 if fy > 0 else -1.0
            parts.append(C.add_box(f"FootPad_{fx}_{fy}", (0.18, 0.18, 0.045), (fx + sx_s * 0.09, fy + sy_s * 0.06, 0.022), mat=iron, bevel=0.01))
            parts.append(C.add_box(
                f"FootStrut_{fx}_{fy}",
                (0.14, 0.14, 0.24),
                (fx + sx_s * 0.05, fy + sy_s * 0.03, 0.12),
                (math.radians(-18 * sy_s), math.radians(18 * sx_s), 0),
                mat=armor,
                bevel=0.012,
            ))

    # 2. Tapered Lower Boiler Chassis & Brass Trim Belt (Z=0.18 .. 0.96)
    chassis_rings = [
        [(-0.78, -0.46, 0.18), (0.78, -0.46, 0.18), (0.78, 0.46, 0.18), (-0.78, 0.46, 0.18)],
        [(-0.82, -0.48, 0.56), (0.82, -0.48, 0.56), (0.82, 0.48, 0.56), (-0.82, 0.48, 0.56)],
        [(-0.74, -0.44, 0.96), (0.74, -0.44, 0.96), (0.74, 0.44, 0.96), (-0.74, 0.44, 0.96)],
    ]
    parts.append(C.add_ring_loft("MainBoiler", chassis_rings, mat=armor, smooth_angle=35.0, uv_scale=1.2))
    parts.append(C.add_box("UpperDeckTrim", (1.54, 0.92, 0.055), (0, 0, 0.96), mat=brass, bevel=0.012))

    # 3. Recessed Weapon Intake Forge Bay + Helical Orange Coils + Feed Rollers
    parts.append(C.add_box("ForgeCavity", (1.06, 0.42, 0.40), (0, -0.31, 0.65), mat=dark, bevel=0.015))
    parts.append(C.add_box("ForgeBezelTop", (1.16, 0.12, 0.06), (0, -0.47, 0.85), mat=brass, bevel=0.012))
    parts.append(C.add_box("ForgeBezelBot", (1.16, 0.14, 0.06), (0, -0.47, 0.43), mat=brass, bevel=0.012))
    for rx in (-0.54, 0.54):
        parts.append(C.add_box(f"ForgeBezelSide_{rx}", (0.07, 0.12, 0.44), (rx, -0.47, 0.64), mat=brass, bevel=0.01))
    # Feed Rollers
    for rz in (0.48, 0.80):
        parts.append(C.add_cyl(f"FeedRoller_{rz}", 0.042, 0.98, (0, -0.46, rz), (0, math.radians(90), 0), vertices=16, mat=brass))
    # 3 Vertical Helical Orange Heating Elements glowing inside intake bay!
    for hx in (-0.28, 0.0, 0.28):
        parts.append(C.add_coil_spring(
            f"HeatHelix_{hx}",
            major_r=0.072,
            wire_r=0.016,
            length=0.25,
            turns=4.5,
            steps_per_turn=14,
            loc=(hx, -0.41, 0.64),
            rot=(math.radians(90), 0, 0),
            mat=orange_coil,
        ))
        parts.append(C.add_cyl(f"HeatCore_{hx}", 0.025, 0.29, (hx, -0.41, 0.64), mat=iron))

    # Lower Control Apron (toggles + brass indicators)
    parts.append(C.add_box("ControlApron", (0.96, 0.06, 0.14), (0, -0.48, 0.31), mat=iron, bevel=0.01))
    for i, tx in enumerate((-0.30, -0.12, 0.12, 0.30)):
        parts.append(C.add_cyl(f"Switch_{i}", 0.014, 0.06, (tx, -0.52, 0.31), (math.radians(70), 0, 0), mat=brass))
    parts.append(C.add_sphere("PilotGreen", 0.022, (1, 1, 1), (-0.40, -0.51, 0.31), mat=led_grn))
    parts.append(C.add_sphere("PilotRed", 0.022, (1, 1, 1), (0.40, -0.51, 0.31), mat=led_red))

    # 4. External Side Copper Conduits, Crank Flywheel & Cleanout Doors
    parts.append(C.add_tube_pipe("PipeLeft", [(-0.82, -0.18, 0.42), (-0.94, -0.18, 0.48), (-0.94, 0.12, 1.04), (-0.64, 0.12, 1.15)], radius=0.036, segments=10, mat=copper))
    parts.append(C.add_tube_pipe("PipeRight", [(0.82, -0.18, 0.42), (0.94, -0.18, 0.48), (0.94, 0.12, 1.04), (0.64, 0.12, 1.15)], radius=0.036, segments=10, mat=copper))
    # Right Flywheel Hand-Crank
    parts.append(C.add_torus("FlywheelRim", 0.16, 0.024, (0.88, -0.05, 0.62), (0, math.radians(90), 0), mat=brass))
    parts.append(C.add_cyl("FlywheelHub", 0.045, 0.08, (0.85, -0.05, 0.62), (0, math.radians(90), 0), mat=iron))
    for s in range(4):
        ang = s * math.pi * 0.5
        parts.append(C.add_cyl(f"WheelSpoke_{s}", 0.014, 0.30, (0.88, -0.05, 0.62), (ang, 0, 0), mat=brass))
    parts.append(C.add_cyl("CrankGrip", 0.022, 0.12, (0.95, -0.05, 0.76), (0, math.radians(90), 0), mat=copper))

    # 5. Upper Support Stanchions, Marquee Frame & 3 Analog Gauges
    for cx in (-0.64, 0.64):
        parts.append(C.add_cyl(f"UpperCol_{cx}", 0.075, 0.82, (cx, -0.16, 1.37), mat=iron))
        parts.append(C.add_torus(f"ColCollarB_{cx}", 0.095, 0.02, (cx, -0.16, 1.02), mat=brass))
        parts.append(C.add_torus(f"ColCollarT_{cx}", 0.095, 0.02, (cx, -0.16, 1.72), mat=brass))

    # Marquee Lightbox Housing
    parts.append(C.add_box("MarqueeBox", (1.20, 0.24, 0.40), (0, -0.26, 1.32), mat=iron, bevel=0.016))
    parts.append(C.add_box("MarqueeTrimTop", (1.26, 0.28, 0.05), (0, -0.26, 1.52), mat=brass, bevel=0.01))
    parts.append(C.add_box("MarqueeTrimBot", (1.26, 0.28, 0.05), (0, -0.26, 1.12), mat=brass, bevel=0.01))

    # 3 Brass Gauge Bezels at Z=1.06 front & side
    gauge_specs = [
        (0.0, -0.40, 1.04, 0.095),
        (-0.34, -0.39, 1.02, 0.078),
        (0.34, -0.39, 1.02, 0.078),
    ]
    for idx, (gx, gy, gz, gr) in enumerate(gauge_specs):
        parts.append(C.add_cyl(f"GaugeCup_{idx}", gr * 1.12, 0.07, (gx, gy, gz), (math.radians(90), 0, 0), vertices=24, mat=brass))
        parts.append(C.add_torus(f"GaugeRim_{idx}", gr * 1.06, 0.014, (gx, gy - 0.032, gz), (math.radians(90), 0, 0), mat=brass))

    # 6. 4 Interlocking Toothed 3D Brass Gears along upper mechanism rear
    parts.append(C.add_gear("GearMainR", teeth=16, r_outer=0.26, r_root=0.22, r_bore=0.04, thickness=0.04, spokes=5, loc=(0.48, 0.12, 1.44), mat=brass))
    parts.append(C.add_gear("GearMidL", teeth=12, r_outer=0.18, r_root=0.15, r_bore=0.03, thickness=0.04, spokes=4, loc=(-0.44, 0.14, 1.48), mat=brass))
    parts.append(C.add_gear("GearTopC", teeth=14, r_outer=0.21, r_root=0.175, r_bore=0.035, thickness=0.04, spokes=5, loc=(0.12, 0.16, 1.62), mat=copper))
    parts.append(C.add_gear("GearSmall", teeth=10, r_outer=0.13, r_root=0.105, r_bore=0.025, thickness=0.04, spokes=4, loc=(-0.18, 0.16, 1.62), mat=brass))

    # 7. Crown Gyroscope Dynamo Dome + Twin Helical Glowing Cyan Tesla Coils
    parts.append(C.add_cyl("TurretColumn", 0.20, 0.44, (0, 0.0, 1.68), mat=iron))
    parts.append(C.add_sphere("GyroCore", 0.21, (1.0, 1.0, 1.0), (0, 0.0, 1.94), mat=iron))
    parts.append(C.add_torus("GyroGimbalA", 0.26, 0.022, (0, 0.0, 1.94), (math.radians(25), 0, math.radians(15)), mat=brass))
    parts.append(C.add_torus("GyroGimbalB", 0.26, 0.022, (0, 0.0, 1.94), (math.radians(-65), math.radians(30), 0), mat=brass))
    # Front Emitter Eye Lens
    parts.append(C.add_cyl("EmitterHood", 0.13, 0.16, (0, -0.18, 1.94), (math.radians(90), 0, 0), mat=brass))
    parts.append(C.add_sphere("EmitterCore", 0.095, (1.0, 0.7, 1.0), (0, -0.24, 1.94), mat=cyan_coil))

    # Crossarm & Twin Helical Cyan Tesla Coils
    parts.append(C.add_cyl("TeslaBar", 0.068, 1.48, (0, 0.0, 1.94), (0, math.radians(90), 0), mat=copper))
    for sx in (-1.0, 1.0):
        parts.append(C.add_coil_spring(
            f"TeslaHelix_{sx}",
            major_r=0.145,
            wire_r=0.022,
            length=0.42,
            turns=4.5,
            steps_per_turn=14,
            loc=(sx * 0.48, 0.0, 1.94),
            rot=(0, 0, math.radians(90)),
            mat=cyan_coil,
        ))
        # Finned End Insulator + Corona Cap
        parts.append(C.add_cyl(f"InsulatorRod_{sx}", 0.09, 0.14, (sx * 0.74, 0.0, 1.94), (0, math.radians(90), 0), mat=brass))
        parts.append(C.add_sphere(f"CoronaBall_{sx}", 0.085, (1.0, 1.0, 1.0), (sx * 0.84, 0.0, 1.94), mat=cyan_coil))

    C.join_objects(parts, "PackAPunch")

    # Separate textured plane & round analog dials so their [0..1] planar UVs stay crisp
    C.add_textured_plane("PaPMarqueePlane", 1.12, 0.34, loc=(0, -0.388, 1.32), mat=marquee_mat)
    for idx, (gx, gy, gz, gr) in enumerate(gauge_specs):
        C.add_textured_disc(f"PaPGaugeDial_{idx}", gr, vertices=24, loc=(gx, gy - 0.036, gz), mat=gauge_mat)

    C.export_asset("props", "pack_a_punch")


def build_power_switch():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("rusted_steel")
    br_a, br_n, br_r = _tex_wpn("brass")

    steel = C.make_pbr_mat("SwitchSteel", (0.20, 0.23, 0.26, 1.0), metallic=0.76, roughness=0.45, albedo_tex=st_a, normal_tex=st_n, roughness_tex=st_r)
    dark = C.make_pbr_mat("SwitchDark", (0.06, 0.065, 0.07, 1.0), metallic=0.5, roughness=0.65)
    brass = C.make_pbr_mat("SwitchBrass", (0.72, 0.54, 0.20, 1.0), metallic=0.88, roughness=0.28, albedo_tex=br_a, normal_tex=br_n)
    copper = C.make_pbr_mat("SwitchCopper", (0.82, 0.44, 0.18, 1.0), metallic=0.90, roughness=0.26)
    red_bakelite = C.make_pbr_mat("SwitchHandle", (0.68, 0.08, 0.06, 1.0), roughness=0.35)
    hazard = C.make_pbr_mat("SwitchHazard", (0.85, 0.58, 0.08, 1.0), roughness=0.42)
    ceramic = C.make_pbr_mat("SwitchCeramic", (0.78, 0.75, 0.70, 1.0), roughness=0.26)
    lamp_red = C.make_pbr_mat("LampRed", (1.0, 0.18, 0.10, 1.0), roughness=0.18, emission=(1.0, 0.16, 0.08), emission_strength=2.2)

    box_parts = [
        C.add_box("Cabinet", (0.50, 0.26, 0.76), (0, 0, 0), mat=steel, bevel=0.018),
        C.add_box("DoorFrame", (0.46, 0.04, 0.70), (0, -0.135, 0), mat=dark, bevel=0.008),
        C.add_box("HazardTag", (0.34, 0.025, 0.11), (0, -0.15, -0.22), mat=hazard, bevel=0.004),
        # Twin Overhead Steel Conduit Pipes & Collars
        C.add_cyl("ConduitL", 0.038, 0.85, (-0.13, 0, 0.78), mat=steel),
        C.add_cyl("ConduitR", 0.038, 0.85, (0.13, 0, 0.78), mat=steel),
        C.add_torus("ConduitColL", 0.052, 0.015, (-0.13, 0, 0.41), mat=brass),
        C.add_torus("ConduitColR", 0.052, 0.015, (0.13, 0, 0.41), mat=brass),
        # Exposed Copper Knife-Switch Contacts on porcelain blocks inside cabinet front
        C.add_box("CeramicBaseT", (0.30, 0.05, 0.09), (0, -0.155, 0.14), mat=ceramic, bevel=0.006),
        C.add_box("CeramicBaseB", (0.30, 0.05, 0.09), (0, -0.155, -0.06), mat=ceramic, bevel=0.006),
        C.add_box("KnifeJawL", (0.04, 0.06, 0.12), (-0.09, -0.175, 0.14), mat=copper, bevel=0.004),
        C.add_box("KnifeJawR", (0.04, 0.06, 0.12), (0.09, -0.175, 0.14), mat=copper, bevel=0.004),
        C.add_cyl("PivotBossR", 0.045, 0.08, (0.27, 0, 0), (0, math.radians(90), 0), mat=brass),
        # Armored Pilot Lamp at Top
        C.add_cyl("LampGuard", 0.062, 0.05, (0, -0.15, 0.28), (math.radians(90), 0, 0), mat=brass),
        C.add_sphere("StatusBulb", 0.048, (1, 1, 1.1), (0, -0.175, 0.28), mat=lamp_red),
    ]
    C.join_objects(box_parts, "PowerBox")

    # Pivoting Knife Lever Yoke (origin MUST remain at (0, 0, 0) for power_switch.gd X-rotation!)
    lever_parts = [
        C.add_box("BladeL", (0.022, 0.24, 0.042), (-0.09, -0.22, 0), mat=copper, bevel=0.003),
        C.add_box("BladeR", (0.022, 0.24, 0.042), (0.09, -0.22, 0), mat=copper, bevel=0.003),
        C.add_box("InsulCrossbar", (0.24, 0.036, 0.036), (0.02, -0.32, 0), mat=dark, bevel=0.006),
        C.add_cyl("SideShaft", 0.018, 0.44, (0.29, -0.21, 0), (math.radians(90), 0, 0), mat=brass),
        C.add_cyl("CrossJoin", 0.016, 0.20, (0.20, -0.32, 0), (0, math.radians(90), 0), mat=brass),
        C.add_cyl("RedGrip", 0.034, 0.18, (0.29, -0.43, 0), (0, math.radians(90), 0), mat=red_bakelite),
    ]
    lever = C.join_objects(lever_parts, "SwitchLever")
    lever.location = (0, 0, 0)

    C.export_asset("props", "power_switch")


def build_electro_trap():
    C.reset_scene()
    st_a, st_n, st_r = _tex_env("rusted_steel")
    steel = C.make_pbr_mat("TrapSteel", (0.18, 0.21, 0.24, 1.0), metallic=0.80, roughness=0.40, albedo_tex=st_a, normal_tex=st_n)
    copper = C.make_pbr_mat("TrapCopper", (0.78, 0.42, 0.18, 1.0), metallic=0.90, roughness=0.28)
    ceramic = C.make_pbr_mat("TrapCeramic", (0.72, 0.70, 0.65, 1.0), roughness=0.25)
    arc = C.make_pbr_mat("TrapArc", (0.22, 0.88, 1.0, 1.0), roughness=0.12, emission=(0.22, 0.88, 1.0), emission_strength=2.2)

    parts = [
        C.add_box("BasePanel", (0.58, 0.22, 0.94), (0, 0, 0.47), mat=steel, bevel=0.018),
        C.add_box("PanelTrim", (0.62, 0.06, 0.98), (0, -0.09, 0.47), mat=steel, bevel=0.01),
        C.add_box("ConduitSide", (0.07, 0.07, 0.92), (-0.31, 0, 0.46), mat=steel, bevel=0.008),
    ]
    # Ribbed Ceramic Insulator Stack + Wound Copper Coil + Top Corona Emitter
    insul_prof = [
        (0.08, 0.35), (0.12, 0.38), (0.12, 0.42), (0.07, 0.45),
        (0.115, 0.48), (0.115, 0.52), (0.065, 0.55), (0.08, 0.90),
    ]
    parts.append(C.add_lathe("InsulatorStack", insul_prof, segments=18, loc=(0, -0.20, 0.0), mat=ceramic))
    parts.append(C.add_coil_spring(
        "CopperWinding",
        major_r=0.095,
        wire_r=0.015,
        length=0.32,
        turns=7.0,
        steps_per_turn=12,
        loc=(0, -0.20, 0.72),
        rot=(math.radians(90), 0, 0),
        mat=copper,
    ))
    parts.append(C.add_torus("CoronaRingT", 0.145, 0.018, (0, -0.20, 0.92), mat=arc))
    parts.append(C.add_torus("CoronaRingB", 0.125, 0.015, (0, -0.20, 0.54), mat=arc))
    parts.append(C.add_sphere("EmitterTop", 0.095, (1, 1, 1), (0, -0.20, 0.98), mat=steel))

    C.join_objects(parts, "ElectroTrap")
    C.export_asset("props", "electro_trap")


def build_powerups():
    br_a, br_n, br_r = _tex_wpn("brass")
    gs_a, gs_n, gs_r = _tex_wpn("gun_steel")
    wl_a, wl_n, wl_r = _tex_wpn("walnut")

    def mats():
        # Rich metallic antique gold w/ very subtle emission (0.05) so shadows & metallic speculars sculpt form!
        gold = C.make_pbr_mat(
            "PowerGold",
            (0.88, 0.64, 0.16, 1.0),
            metallic=0.90,
            roughness=0.28,
            emission=(0.75, 0.50, 0.10),
            emission_strength=0.05,
            albedo_tex=br_a,
            normal_tex=br_n,
            roughness_tex=br_r,
            tint_tex=(0.98, 0.88, 0.62),
            normal_strength=0.35,
        )
        bronze = C.make_pbr_mat(
            "PowerBronze",
            (0.18, 0.12, 0.06, 1.0),
            metallic=0.72,
            roughness=0.40,
            albedo_tex=gs_a,
            normal_tex=gs_n,
            tint_tex=(0.55, 0.36, 0.18),
            normal_strength=0.35,
        )
        olive_steel = C.make_pbr_mat(
            "PowerOliveSteel",
            (0.32, 0.42, 0.26, 1.0),
            metallic=0.58,
            roughness=0.38,
            emission=(0.20, 0.55, 0.20),
            emission_strength=0.06,
            albedo_tex=gs_a,
            normal_tex=gs_n,
            tint_tex=(0.52, 0.72, 0.40),
        )
        walnut = C.make_pbr_mat(
            "PowerWalnut",
            (0.38, 0.20, 0.10, 1.0),
            roughness=0.56,
            albedo_tex=wl_a,
            normal_tex=wl_n,
            roughness_tex=wl_r,
        )
        crimson = C.make_pbr_mat(
            "SkullCrimson",
            (0.98, 0.14, 0.04, 1.0),
            roughness=0.16,
            emission=(1.0, 0.12, 0.03),
            emission_strength=2.2,
        )
        socket_dark = C.make_pbr_mat(
            "SocketCavity",
            (0.025, 0.015, 0.010, 1.0),
            metallic=0.25,
            roughness=0.82,
        )
        return gold, bronze, olive_steel, walnut, crimson, socket_dark

    # 1. Max Ammo (Stamped WWII Ammo Crate + Carry Handle + Brass Bullet Belt)
    C.reset_scene()
    g, b, s, _, _, _ = mats()
    parts = [
        C.add_box("AmmoBody", (0.44, 0.25, 0.29), (0, 0, 0.145), mat=s, bevel=0.014),
        C.add_box("AmmoLid", (0.47, 0.28, 0.055), (0, 0, 0.305), mat=g, bevel=0.012),
        C.add_box("AmmoLatch", (0.10, 0.30, 0.10), (0, 0, 0.235), mat=b, bevel=0.006),
        C.add_box("AmmoRib1", (0.455, 0.04, 0.18), (0, -0.125, 0.14), mat=b, bevel=0.004),
        C.add_box("AmmoRib2", (0.455, 0.04, 0.18), (0, 0.125, 0.14), mat=b, bevel=0.004),
        C.add_tube_pipe("TopHandle", [(-0.10, 0, 0.33), (-0.09, 0, 0.39), (0.09, 0, 0.39), (0.10, 0, 0.33)], radius=0.014, segments=8, mat=b),
    ]
    for c_i in range(6):
        cx = -0.125 + c_i * 0.050
        parts.append(C.add_cyl(f"Shell_{c_i}", 0.015, 0.09, (cx, -0.155, 0.24), (math.radians(15), 0, 0), vertices=10, mat=g))
        parts.append(C.add_cone(f"Tip_{c_i}", 0.015, 0.002, 0.04, (cx, -0.165, 0.295), (math.radians(15), 0, 0), vertices=10, mat=b))
    C.join_objects(parts, "MaxAmmo")
    C.export_asset("pickups", "powerup_max_ammo")

    # 2. Insta-Kill (Sculpted Anatomical Skull — Broad Parietal Cranium, Deep Sockets, Zygomatic Arches & Tapered Jaw)
    C.reset_scene()
    g, b, _, _, red, cavity = mats()
    parts = []

    segs = 20
    # Each slice: (z, cy, rx, ry, brow_pinch, temple_tuck)
    skull_slices = [
        (0.145, -0.042, 0.078, 0.098, 0.012, 0.018),   # Upper maxilla / gum ridge
        (0.185, -0.025, 0.118, 0.122, 0.018, 0.022),   # Cheekbone flare
        (0.238, -0.008, 0.156, 0.155, 0.012, 0.032),   # Mid socket level (deep recessed orbits/temples)
        (0.292,  0.000, 0.186, 0.182, 0.032, 0.015),   # Prominent supraorbital brow ridge!
        (0.355,  0.016, 0.196, 0.194, 0.008, 0.0),     # Broad rounded parietal cranium
        (0.415,  0.026, 0.164, 0.172, 0.0,   0.0),     # Crown dome
        (0.452,  0.028, 0.102, 0.114, 0.0,   0.0),     # Vertex cap
        (0.468,  0.028, 0.026, 0.030, 0.0,   0.0),
    ]
    rings = []
    for z, cy, rx, ry, brow, tuck in skull_slices:
        r = []
        for s in range(segs):
            ang = (s / segs) * 2.0 * math.pi
            ca, sa = math.cos(ang), math.sin(ang)
            x = ca * rx
            y = cy + sa * ry
            if sa < -0.15:
                if abs(ca) > 0.45:
                    x *= (1.0 - tuck * abs(sa))
                if abs(ca) < 0.65:
                    if abs(z - 0.238) < 0.03:
                        y += 0.032 * (1.0 - abs(ca) * 0.45)  # Deep eye socket depression!
                    elif abs(z - 0.292) < 0.025:
                        y -= brow * (1.0 - abs(ca) * 0.35)  # Fierce brow overhang!
                    elif abs(z - 0.185) < 0.025 and abs(ca) > 0.26:
                        y -= 0.020  # Forward cheekbones
            r.append((x, y, z))
        rings.append(r)
    parts.append(C.add_ring_loft("SkullCranium", rings, mat=g, smooth_angle=52.0, uv_scale=3.0))

    # Zygomatic arches spanning cheek to mastoid temple
    for side in (-1.0, 1.0):
        zyg = [
            (side * 0.105, -0.095, 0.205),
            (side * 0.148, -0.035, 0.212),
            (side * 0.146,  0.035, 0.215),
        ]
        parts.append(C.add_tube_pipe(f"Zygomatic_{side}", zyg, radius=0.015, segments=8, mat=g))

    # Nose bridge & recessed nasal pyriform cavity
    parts.append(C.add_box("NoseBridge", (0.022, 0.045, 0.048), (0, -0.150, 0.242), (math.radians(-18), 0, 0), mat=g, bevel=0.007))
    parts.append(C.add_cone("NoseCavity", 0.028, 0.006, 0.036, (0, -0.132, 0.188), (math.radians(90), 0, 0), vertices=3, mat=cavity))

    # Slender Tapered Lower Jawbone (Mandible loft)
    jaw_pts = [
        (-0.088, -0.022, 0.148),
        (-0.082, -0.068, 0.086),
        (-0.044, -0.118, 0.054),
        ( 0.000, -0.134, 0.050),
        ( 0.044, -0.118, 0.054),
        ( 0.082, -0.068, 0.086),
        ( 0.088, -0.022, 0.148),
    ]
    jaw_radii = [0.020, 0.024, 0.025, 0.026, 0.025, 0.024, 0.020]
    parts.append(C.add_tube_pipe("MandibleArch", jaw_pts, radii=jaw_radii, segments=10, mat=g))
    parts.append(C.add_box("DarkMouthCavity", (0.11, 0.075, 0.048), (0, -0.095, 0.116), mat=cavity, bevel=0.004))

    # 12 Crisp Carved Teeth along tight dental arcade
    for ti in range(6):
        ang = -0.56 + (ti / 5.0) * 1.12
        tx = math.sin(ang) * 0.066
        ty = -0.082 - math.cos(ang) * 0.048
        parts.append(C.add_box(f"ToothUp_{ti}", (0.015, 0.016, 0.020), (tx, ty, 0.128), (0, 0, -ang), mat=g, bevel=0.003))
        parts.append(C.add_box(f"ToothLo_{ti}", (0.014, 0.015, 0.018), (tx, ty, 0.098), (0, 0, -ang), mat=g, bevel=0.003))

    # Deep Dark Eye Sockets + Glowing Crimson Pupils recessed inside!
    for ex, erot in ((-0.054, 14), (0.054, -14)):
        parts.append(C.add_sphere(f"OrbSocket_{ex}", 0.042, (1.0, 0.68, 0.88), (ex, -0.124, 0.238), (0, 0, math.radians(erot)), mat=cavity))
        parts.append(C.add_sphere(f"CrimsonIris_{ex}", 0.014, (1, 1, 1), (ex, -0.136, 0.238), mat=red))

    C.join_objects(parts, "InstaKill")
    C.export_asset("pickups", "powerup_insta_kill")

    # 3. Double Points (Sleek Molded 2X on Bronze Pedestal Ring)
    C.reset_scene()
    g, b, _, _, _, _ = mats()
    two_pts = [
        (-0.22, 0.34), (-0.17, 0.39), (-0.06, 0.39), (-0.02, 0.34),
        (-0.02, 0.27), (-0.15, 0.17), (-0.02, 0.17), (-0.02, 0.11),
        (-0.23, 0.11), (-0.23, 0.17), (-0.09, 0.28), (-0.09, 0.33),
        (-0.16, 0.33), (-0.22, 0.29),
    ]
    parts = [
        C.add_extruded_poly("DigitTwo", two_pts, depth=0.085, plane="XZ", mat=g, bevel=0.009),
        C.add_box("XStroke1", (0.28, 0.085, 0.064), (0.14, 0, 0.25), (0, math.radians(48), 0), mat=g, bevel=0.009),
        C.add_box("XStroke2", (0.28, 0.085, 0.064), (0.14, 0, 0.25), (0, math.radians(-48), 0), mat=g, bevel=0.009),
        C.add_torus("BaseMedalRing", 0.24, 0.024, (0, 0, 0.045), mat=b),
    ]
    C.join_objects(parts, "DoublePoints")
    C.export_asset("pickups", "powerup_double_points")

    # 4. Nuke (Streamlined Ogive Fat-Man Warhead + Cruciform Tail Box Fins)
    C.reset_scene()
    g, b, _, _, _, _ = mats()
    nuke_prof = [
        (0.04, 0.02), (0.09, 0.09), (0.14, 0.18), (0.155, 0.28),
        (0.145, 0.37), (0.105, 0.44), (0.045, 0.49), (0.005, 0.51),
    ]
    parts = [
        C.add_lathe("Warhead", nuke_prof, segments=20, loc=(0, 0, 0.03), mat=g),
        C.add_torus("WeldBand", 0.158, 0.015, (0, 0, 0.30), mat=b),
        C.add_box("ShroudH", (0.26, 0.025, 0.14), (0, 0, 0.09), mat=b, bevel=0.005),
        C.add_box("ShroudV", (0.025, 0.26, 0.14), (0, 0, 0.09), mat=b, bevel=0.005),
        C.add_box("ShroudRim1", (0.26, 0.26, 0.024), (0, 0, 0.03), mat=g, bevel=0.004),
    ]
    C.join_objects(parts, "Nuke")
    C.export_asset("pickups", "powerup_nuke")

    # 5. Carpenter (Ergonomic Hickory Hammer Handle + Brass Ferrule + Curved Claw Head)
    C.reset_scene()
    g, b, _, wl, _, _ = mats()
    claw_head = [
        (-0.12, 0.35), (-0.08, 0.42), (0.03, 0.42), (0.12, 0.38),
        (0.14, 0.34), (0.07, 0.36), (-0.03, 0.36), (-0.12, 0.35),
    ]
    parts = [
        C.add_tube_pipe("HickoryHandle", [(0.05, 0, 0.02), (0.01, 0, 0.20), (-0.03, 0, 0.38)], radii=[0.030, 0.025, 0.028], segments=12, mat=wl),
        C.add_cyl("SteelFerrule", 0.034, 0.06, (-0.03, 0, 0.36), (0, math.radians(14), 0), mat=b),
        C.add_extruded_poly("ClawHead", claw_head, depth=0.068, plane="XZ", loc=(0, 0, 0.0), rot=(0, math.radians(14), 0), mat=g, bevel=0.008),
        C.add_cyl("StrikeFace", 0.038, 0.055, (-0.11, 0, 0.41), (0, math.radians(104), 0), mat=b),
    ]
    C.join_objects(parts, "Carpenter")
    C.export_asset("pickups", "powerup_carpenter")

    # 6. Fire Sale (Embossed Luggage Price Tag + Brass Grommet + 3-Link Interlocking Chain)
    C.reset_scene()
    g, b, _, _, _, _ = mats()
    tag_poly = [(-0.18, 0.14), (0.10, 0.14), (0.20, 0.22), (0.20, 0.30), (0.10, 0.38), (-0.18, 0.38)]
    parts = [
        C.add_extruded_poly("TagBody", tag_poly, depth=0.048, plane="XZ", rot=(0, math.radians(-10), 0), mat=g, bevel=0.009),
        C.add_torus("Grommet", 0.028, 0.010, (0.15, 0, 0.28), (math.radians(90), math.radians(-10), 0), mat=b),
        C.add_box("BarTop", (0.20, 0.06, 0.024), (-0.05, 0, 0.30), (0, math.radians(-10), 0), mat=b, bevel=0.004),
        C.add_box("BarBot", (0.20, 0.06, 0.024), (-0.05, 0, 0.22), (0, math.radians(-10), 0), mat=b, bevel=0.004),
        C.add_chain("KeyChain", [(0.16, 0, 0.29), (0.21, 0, 0.37), (0.17, 0, 0.44)], link_len=0.055, link_w=0.032, wire_r=0.007, mat=b),
    ]
    C.join_objects(parts, "FireSale")
    C.export_asset("pickups", "powerup_fire_sale")


if __name__ == "__main__":
    build_perk_machine("juggernog", (0.64, 0.06, 0.06), (0.95, 0.14, 0.12))
    build_perk_machine("speedcola", (0.07, 0.48, 0.16), (0.14, 0.92, 0.34))
    build_perk_machine("doubletap", (0.76, 0.46, 0.06), (0.96, 0.72, 0.14))
    build_perk_machine("quickrevive", (0.08, 0.38, 0.78), (0.18, 0.68, 1.0))
    build_perk_machine("staminup", (0.80, 0.30, 0.05), (1.0, 0.45, 0.10))
    build_mystery_box()
    build_teddy_bear()
    build_pack_a_punch()
    build_power_switch()
    build_electro_trap()
    build_powerups()
    print("ALL INTRICATE MACHINES & POWER-UPS EXPORTED!")
