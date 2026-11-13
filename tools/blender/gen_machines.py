"""Generate interactive Zombies machines and Power-Up drops in Blender (.blend + .glb).
- perk_juggernog, perk_speedcola, perk_doubletap, perk_quickrevive, perk_staminup
- mystery_box, teddy_bear
- pack_a_punch
- power_switch, electro_trap
- powerup_max_ammo, powerup_insta_kill, powerup_double_points, powerup_nuke, powerup_carpenter, powerup_fire_sale
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def build_perk_machine(key, body_rgb, trim_rgb):
    C.reset_scene()
    body_mat = C.make_pbr_mat(f"PerkBody_{key}", (*body_rgb, 1.0), metallic=0.25, roughness=0.48)
    cream_mat = C.make_pbr_mat("PerkCream", (0.76, 0.72, 0.62, 1.0), metallic=0.05, roughness=0.52)
    chrome_mat = C.make_pbr_mat("PerkChrome", (0.72, 0.75, 0.78, 1.0), metallic=0.88, roughness=0.24)
    dark_mat = C.make_pbr_mat("PerkDark", (0.08, 0.08, 0.09, 1.0), metallic=0.6, roughness=0.5)
    dome_mat = C.make_pbr_mat(f"PerkDome_{key}", (*body_rgb, 1.0), roughness=0.14, emission=body_rgb, emission_strength=2.2)
    marquee_tex = os.path.join(C.TEX_DIR, "props", f"marquee_{key}.png")
    sign_mat = C.make_pbr_mat(f"PerkSign_{key}", (*body_rgb, 1.0), roughness=0.32, emission=body_rgb, emission_strength=0.95, albedo_tex=marquee_tex)

    parts = [
        C.add_box("CabinetLower", (0.90, 0.72, 1.35), (0, 0, 0.675), mat=body_mat, bevel=0.03),
        C.add_box("CabinetUpper", (0.88, 0.70, 0.62), (0, 0, 1.66), mat=cream_mat, bevel=0.04),
        C.add_box("BasePlinth", (0.96, 0.78, 0.12), (0, 0, 0.06), mat=dark_mat, bevel=0.01),
        C.add_box("FrontDoor", (0.58, 0.08, 0.96), (0, -0.35, 0.70), mat=body_mat, bevel=0.015),
        C.add_box("CoinPanel", (0.42, 0.05, 0.42), (0, -0.39, 0.92), mat=chrome_mat, bevel=0.008),
        C.add_box("BottleChute", (0.34, 0.06, 0.24), (0, -0.39, 0.46), mat=dark_mat, bevel=0.008),
        C.add_box("TrimL", (0.06, 0.76, 1.88), (-0.45, 0, 0.96), mat=chrome_mat, bevel=0.01),
        C.add_box("TrimR", (0.06, 0.76, 1.88), (0.45, 0, 0.96), mat=chrome_mat, bevel=0.01),
        C.add_cyl("DomeBase", 0.20, 0.08, (0, -0.05, 2.01), mat=chrome_mat),
        C.add_sphere("GlowDome", 0.18, (1.0, 1.0, 1.25), (0, -0.05, 2.15), mat=dome_mat),
    ]
    C.join_objects(parts, f"PerkCabinet_{key}")

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, -0.365, 1.66), rotation=(math.radians(90), 0, 0))
    sign = bpy.context.active_object
    sign.name = f"Marquee_{key}"
    sign.scale = (0.74, 0.42, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    C.assign_mat(sign, sign_mat)

    C.export_asset("props", f"perk_{key}")


def build_mystery_box():
    C.reset_scene()
    wood_tex = os.path.join(C.TEX_DIR, "env", "charred_wood_albedo.png")
    wood_mat = C.make_pbr_mat("BoxWood", (0.28, 0.16, 0.09, 1.0), roughness=0.68, albedo_tex=wood_tex)
    iron_mat = C.make_pbr_mat("BoxIron", (0.14, 0.15, 0.17, 1.0), metallic=0.82, roughness=0.45)
    rune_mat = C.make_pbr_mat("BoxRune", (0.15, 0.95, 1.0, 1.0), roughness=0.2, emission=(0.2, 0.95, 1.0), emission_strength=2.6)
    gold_glow = C.make_pbr_mat("BoxGoldGlow", (1.0, 0.80, 0.22, 1.0), roughness=0.2, emission=(1.0, 0.78, 0.20), emission_strength=1.8)

    body_parts = [
        C.add_box("BaseChest", (1.80, 0.78, 0.62), (0, 0, 0.31), mat=wood_mat, bevel=0.015),
        C.add_box("InnerGlow", (1.64, 0.62, 0.06), (0, 0, 0.59), mat=gold_glow, bevel=0.005),
        C.add_box("StrapL", (0.10, 0.82, 0.64), (-0.72, 0, 0.32), mat=iron_mat, bevel=0.008),
        C.add_box("StrapR", (0.10, 0.82, 0.64), (0.72, 0, 0.32), mat=iron_mat, bevel=0.008),
        C.add_box("CornerTrim", (1.84, 0.82, 0.08), (0, 0, 0.05), mat=iron_mat, bevel=0.008),
        C.add_box("FrontLock", (0.26, 0.06, 0.26), (0, -0.40, 0.42), mat=iron_mat, bevel=0.008),
        C.add_box("RuneGlyph", (0.14, 0.02, 0.14), (0, -0.43, 0.42), (0, math.radians(45), 0), mat=rune_mat, bevel=0.002),
    ]
    C.join_objects(body_parts, "BoxBody")

    lid_parts = [
        C.add_box("LidPlank", (1.84, 0.82, 0.14), (0, -0.39, 0.07), mat=wood_mat, bevel=0.015),
        C.add_box("LidIronL", (0.11, 0.84, 0.16), (-0.72, -0.39, 0.07), mat=iron_mat, bevel=0.008),
        C.add_box("LidIronR", (0.11, 0.84, 0.16), (0.72, -0.39, 0.07), mat=iron_mat, bevel=0.008),
        C.add_box("LidQues1", (0.12, 0.12, 0.03), (-0.36, -0.39, 0.15), mat=gold_glow, bevel=0.004),
        C.add_box("LidQues2", (0.12, 0.12, 0.03), (0.36, -0.39, 0.15), mat=gold_glow, bevel=0.004),
    ]
    lid = C.join_objects(lid_parts, "BoxLid")
    lid.location = (0, 0.39, 0.62)

    C.export_asset("props", "mystery_box")


def build_teddy_bear():
    C.reset_scene()
    fur = C.make_pbr_mat("TeddyFur", (0.36, 0.22, 0.12, 1.0), roughness=0.92)
    eye = C.make_pbr_mat("TeddyEye", (1.0, 0.12, 0.05, 1.0), roughness=0.2, emission=(1.0, 0.1, 0.02), emission_strength=3.0)
    parts = [
        C.add_sphere("Torso", 0.15, (1.0, 0.85, 1.2), (0, 0, 0.20), mat=fur),
        C.add_sphere("Head", 0.13, (1.05, 1.0, 1.0), (0, 0, 0.42), mat=fur),
        C.add_sphere("EarL", 0.045, (1, 0.6, 1), (-0.11, 0, 0.52), mat=fur),
        C.add_sphere("EarR", 0.045, (1, 0.6, 1), (0.11, 0, 0.52), mat=fur),
        C.add_sphere("Snout", 0.055, (1.0, 1.1, 0.8), (0, -0.11, 0.40), mat=fur),
        C.add_sphere("EyeL", 0.018, (1, 1, 1), (-0.045, -0.115, 0.45), mat=eye),
        C.add_sphere("EyeR", 0.018, (1, 1, 1), (0.045, -0.115, 0.45), mat=eye),
        C.add_cyl("ArmL", 0.045, 0.18, (-0.17, -0.04, 0.26), (math.radians(40), math.radians(35), 0), mat=fur),
        C.add_cyl("ArmR", 0.045, 0.18, (0.17, -0.04, 0.26), (math.radians(40), math.radians(-35), 0), mat=fur),
        C.add_cyl("LegL", 0.052, 0.18, (-0.09, -0.10, 0.07), (math.radians(80), 0, math.radians(-15)), mat=fur),
        C.add_cyl("LegR", 0.052, 0.18, (0.09, -0.10, 0.07), (math.radians(80), 0, math.radians(15)), mat=fur),
    ]
    C.join_objects(parts, "TeddyBear")
    C.export_asset("props", "teddy_bear")


def build_pack_a_punch():
    C.reset_scene()
    steel_tex = os.path.join(C.TEX_DIR, "env", "rusted_steel_albedo.png")
    iron = C.make_pbr_mat("PaPIron", (0.14, 0.16, 0.20, 1.0), metallic=0.72, roughness=0.46, albedo_tex=steel_tex)
    brass = C.make_pbr_mat("PaPBrass", (0.56, 0.38, 0.13, 1.0), metallic=0.84, roughness=0.34)
    cyan_coil = C.make_pbr_mat("PaPCyanCoil", (0.08, 0.90, 1.0, 1.0), roughness=0.15, emission=(0.08, 0.90, 1.0), emission_strength=1.65)
    orange_coil = C.make_pbr_mat("PaPOrangeCoil", (1.0, 0.42, 0.05, 1.0), roughness=0.15, emission=(1.0, 0.40, 0.04), emission_strength=1.75)
    dark = C.make_pbr_mat("PaPDark", (0.05, 0.05, 0.06, 1.0), metallic=0.55, roughness=0.62)

    parts = [
        C.add_box("Pedestal", (1.68, 1.05, 0.92), (0, 0, 0.46), mat=iron, bevel=0.03),
        C.add_box("ColumnL", (0.20, 0.28, 0.95), (-0.64, -0.18, 1.38), mat=iron, bevel=0.015),
        C.add_box("ColumnR", (0.20, 0.28, 0.95), (0.64, -0.18, 1.38), mat=iron, bevel=0.015),
        C.add_box("IntakeBay", (1.10, 0.52, 0.46), (0, -0.32, 0.62), mat=dark, bevel=0.015),
        C.add_cyl("RollerL", 0.08, 0.48, (-0.34, -0.44, 0.62), (math.radians(90), 0, 0), mat=iron),
        C.add_cyl("RollerR", 0.08, 0.48, (0.34, -0.44, 0.62), (math.radians(90), 0, 0), mat=iron),
        C.add_torus("HeatCoil1", 0.11, 0.020, (-0.22, -0.46, 0.62), (0, math.radians(90), 0), mat=orange_coil),
        C.add_torus("HeatCoil2", 0.11, 0.020, (0.0, -0.46, 0.62), (0, math.radians(90), 0), mat=orange_coil),
        C.add_torus("HeatCoil3", 0.11, 0.020, (0.22, -0.46, 0.62), (0, math.radians(90), 0), mat=orange_coil),
        C.add_box("SignFrame", (1.16, 0.22, 0.34), (0, -0.24, 1.18), mat=dark, bevel=0.015),
        C.add_box("SignTrimTop", (1.20, 0.24, 0.05), (0, -0.24, 1.34), mat=brass, bevel=0.008),
        C.add_box("SignTrimBot", (1.20, 0.24, 0.05), (0, -0.24, 1.02), mat=brass, bevel=0.008),
        C.add_box("SignEmblem", (0.76, 0.04, 0.12), (0, -0.34, 1.18), mat=cyan_coil, bevel=0.005),
        C.add_cyl("UpperHub", 0.26, 0.65, (0, 0.05, 1.48), mat=iron),
        C.add_cyl("TeslaBar", 0.10, 1.35, (0, 0.05, 1.72), (0, math.radians(90), 0), mat=brass),
        C.add_cyl("Gear1", 0.22, 0.08, (0.65, 0.15, 1.25), (math.radians(90), 0, 0), vertices=14, mat=brass),
        C.add_cyl("Gear2", 0.16, 0.08, (0.36, 0.15, 1.38), (math.radians(90), 0, 0), vertices=12, mat=brass),
        C.add_torus("PlasmaL1", 0.16, 0.024, (-0.42, 0.05, 1.72), (0, math.radians(90), 0), mat=cyan_coil),
        C.add_torus("PlasmaL2", 0.16, 0.024, (-0.58, 0.05, 1.72), (0, math.radians(90), 0), mat=cyan_coil),
        C.add_torus("PlasmaR1", 0.16, 0.024, (0.42, 0.05, 1.72), (0, math.radians(90), 0), mat=cyan_coil),
        C.add_torus("PlasmaR2", 0.16, 0.024, (0.58, 0.05, 1.72), (0, math.radians(90), 0), mat=cyan_coil),
        C.add_sphere("CenterOrb", 0.13, (1, 1, 1), (0, -0.18, 1.72), mat=cyan_coil),
    ]
    C.join_objects(parts, "PackAPunch")
    C.export_asset("props", "pack_a_punch")


def build_power_switch():
    C.reset_scene()
    steel = C.make_pbr_mat("SwitchBox", (0.20, 0.22, 0.24, 1.0), metallic=0.75, roughness=0.45)
    red = C.make_pbr_mat("SwitchHandle", (0.72, 0.10, 0.08, 1.0), roughness=0.4)
    brass = C.make_pbr_mat("SwitchBrass", (0.70, 0.52, 0.20, 1.0), metallic=0.88, roughness=0.3)
    lamp_red = C.make_pbr_mat("LampRed", (1.0, 0.15, 0.1, 1.0), roughness=0.2, emission=(1.0, 0.15, 0.08), emission_strength=2.5)

    box_parts = [
        C.add_box("Cabinet", (0.48, 0.26, 0.72), (0, 0, 0), mat=steel, bevel=0.015),
        C.add_cyl("ConduitTop", 0.04, 0.80, (-0.12, 0, 0.72), mat=steel),
        C.add_cyl("ConduitTop2", 0.04, 0.80, (0.12, 0, 0.72), mat=steel),
        C.add_sphere("StatusBulb", 0.045, (1, 1, 1), (0, -0.14, 0.24), mat=lamp_red),
    ]
    C.join_objects(box_parts, "PowerBox")

    lever_parts = [
        C.add_cyl("ArmShaft", 0.018, 0.42, (0.28, -0.20, 0), (math.radians(90), 0, 0), mat=brass),
        C.add_cyl("RedGrip", 0.030, 0.16, (0.28, -0.40, 0), (0, math.radians(90), 0), mat=red),
    ]
    lever = C.join_objects(lever_parts, "SwitchLever")
    lever.location = (0, 0, 0)

    C.export_asset("props", "power_switch")


def build_electro_trap():
    C.reset_scene()
    steel = C.make_pbr_mat("TrapSteel", (0.18, 0.20, 0.22, 1.0), metallic=0.80, roughness=0.4)
    copper = C.make_pbr_mat("TrapCopper", (0.76, 0.40, 0.18, 1.0), metallic=0.90, roughness=0.28)
    arc = C.make_pbr_mat("TrapArc", (0.25, 0.85, 1.0, 1.0), roughness=0.1, emission=(0.25, 0.85, 1.0), emission_strength=2.8)
    parts = [
        C.add_box("BasePanel", (0.55, 0.22, 0.90), (0, 0, 0.45), mat=steel, bevel=0.015),
        C.add_cyl("CoilCore", 0.08, 0.45, (0, -0.18, 0.65), mat=copper),
        C.add_torus("CoilRing1", 0.11, 0.016, (0, -0.18, 0.80), mat=arc),
        C.add_torus("CoilRing2", 0.11, 0.016, (0, -0.18, 0.65), mat=arc),
        C.add_sphere("EmitterTop", 0.09, (1, 1, 1), (0, -0.18, 0.94), mat=steel),
    ]
    C.join_objects(parts, "ElectroTrap")
    C.export_asset("props", "electro_trap")


def build_powerups():
    def mats():
        g = C.make_pbr_mat("PowerGold", (0.88, 0.64, 0.14, 1.0), metallic=0.84, roughness=0.24, emission=(0.82, 0.54, 0.08), emission_strength=0.58)
        b = C.make_pbr_mat("PowerBronze", (0.14, 0.09, 0.04, 1.0), metallic=0.65, roughness=0.46)
        s = C.make_pbr_mat("PowerSteel", (0.26, 0.34, 0.24, 1.0), metallic=0.60, roughness=0.38, emission=(0.15, 0.55, 0.18), emission_strength=0.55)
        red = C.make_pbr_mat("SkullEye", (0.98, 0.16, 0.06, 1.0), metallic=0.1, roughness=0.2, emission=(0.98, 0.14, 0.05), emission_strength=2.1)
        return g, b, s, red

    # 1. Max Ammo (Ammo Box)
    C.reset_scene()
    g, b, s, _ = mats()
    C.join_objects([
        C.add_box("Crate", (0.44, 0.26, 0.30), (0, 0, 0.15), mat=s, bevel=0.015),
        C.add_box("Lid", (0.47, 0.29, 0.06), (0, 0, 0.31), mat=g, bevel=0.01),
        C.add_box("Latch", (0.10, 0.31, 0.10), (0, 0, 0.24), mat=b, bevel=0.005),
    ], "MaxAmmo")
    C.export_asset("pickups", "powerup_max_ammo")

    # 2. Insta-Kill (Skull — sculpted sockets, protruding cheekbones, dark nose, bronze jaw seam, fiery red eyes!)
    C.reset_scene()
    g, b, _, red = mats()
    C.join_objects([
        C.add_sphere("Cranium", 0.20, (0.95, 0.92, 1.08), (0, 0.01, 0.27), mat=g),
        C.add_box("BrowRidge", (0.26, 0.08, 0.045), (0, -0.155, 0.315), mat=g, bevel=0.012),
        C.add_box("CheekL", (0.09, 0.09, 0.065), (-0.11, -0.145, 0.185), mat=g, bevel=0.012),
        C.add_box("CheekR", (0.09, 0.09, 0.065), (0.11, -0.145, 0.185), mat=g, bevel=0.012),
        C.add_box("Jaw", (0.19, 0.16, 0.095), (0, -0.08, 0.08), mat=g, bevel=0.014),
        C.add_box("TeethGap", (0.14, 0.06, 0.032), (0, -0.16, 0.125), mat=b, bevel=0.004),
        C.add_box("NoseSlot", (0.045, 0.05, 0.065), (0, -0.185, 0.195), mat=b, bevel=0.006),
        C.add_sphere("SocketL", 0.048, (1.0, 0.65, 0.95), (-0.068, -0.168, 0.258), mat=b),
        C.add_sphere("SocketR", 0.048, (1.0, 0.65, 0.95), (0.068, -0.168, 0.258), mat=b),
        C.add_sphere("EyeL", 0.022, (1, 1, 1), (-0.068, -0.194, 0.258), mat=red),
        C.add_sphere("EyeR", 0.022, (1, 1, 1), (0.068, -0.194, 0.258), mat=red),
    ], "InstaKill")
    C.export_asset("pickups", "powerup_insta_kill")

    # 3. Double Points (2X emblem)
    C.reset_scene()
    g, b, _, _ = mats()
    C.join_objects([
        C.add_box("TwoTop", (0.17, 0.08, 0.05), (-0.13, 0, 0.36), mat=g, bevel=0.006),
        C.add_box("TwoDiag", (0.19, 0.08, 0.05), (-0.13, 0, 0.23), (0, math.radians(45), 0), mat=g, bevel=0.006),
        C.add_box("TwoBot", (0.17, 0.08, 0.05), (-0.13, 0, 0.10), mat=g, bevel=0.006),
        C.add_box("X1", (0.26, 0.08, 0.055), (0.14, 0, 0.23), (0, math.radians(45), 0), mat=g, bevel=0.006),
        C.add_box("X2", (0.26, 0.08, 0.055), (0.14, 0, 0.23), (0, math.radians(-45), 0), mat=g, bevel=0.006),
        C.add_box("BaseTrim", (0.56, 0.04, 0.04), (0, 0, 0.03), mat=b, bevel=0.005),
    ], "DoublePoints")
    C.export_asset("pickups", "powerup_double_points")

    # 4. Nuke (Finned Atomic Bomb)
    C.reset_scene()
    g, b, _, _ = mats()
    C.join_objects([
        C.add_sphere("BombBody", 0.16, (0.9, 0.9, 1.65), (0, 0, 0.25), mat=g),
        C.add_cone("TailCone", 0.16, 0.08, 0.16, (0, 0, 0.05), mat=b),
        C.add_box("Fin1", (0.28, 0.03, 0.12), (0, 0, 0.06), mat=b, bevel=0.004),
        C.add_box("Fin2", (0.03, 0.28, 0.12), (0, 0, 0.06), mat=b, bevel=0.004),
    ], "Nuke")
    C.export_asset("pickups", "powerup_nuke")

    # 5. Carpenter (Hammer)
    C.reset_scene()
    g, b, _, _ = mats()
    C.join_objects([
        C.add_cyl("Handle", 0.035, 0.42, (0, 0, 0.20), (0, math.radians(20), 0), mat=b),
        C.add_box("Head", (0.24, 0.09, 0.09), (-0.06, 0, 0.38), (0, math.radians(20), 0), mat=g, bevel=0.01),
    ], "Carpenter")
    C.export_asset("pickups", "powerup_carpenter")

    # 6. Fire Sale (Tag)
    C.reset_scene()
    g, b, _, _ = mats()
    C.join_objects([
        C.add_box("TagPlate", (0.34, 0.06, 0.22), (0, 0, 0.22), (0, math.radians(-12), 0), mat=g, bevel=0.015),
        C.add_torus("TagRing", 0.06, 0.012, (0.14, 0, 0.32), (math.radians(90), 0, 0), mat=b),
    ], "FireSale")
    C.export_asset("pickups", "powerup_fire_sale")


if __name__ == "__main__":
    build_perk_machine("juggernog", (0.62, 0.05, 0.06), (0.85, 0.80, 0.75))
    build_perk_machine("speedcola", (0.07, 0.48, 0.16), (0.85, 0.90, 0.85))
    build_perk_machine("doubletap", (0.74, 0.44, 0.06), (0.90, 0.85, 0.70))
    build_perk_machine("quickrevive", (0.09, 0.36, 0.76), (0.85, 0.90, 0.95))
    build_perk_machine("staminup", (0.78, 0.28, 0.05), (0.90, 0.85, 0.75))
    build_mystery_box()
    build_teddy_bear()
    build_pack_a_punch()
    build_power_switch()
    build_electro_trap()
    build_powerups()
    print("ALL MACHINES & POWER-UPS EXPORTED!")
