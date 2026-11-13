"""Generate architectural and environmental 3D props in Blender (.blend + .glb):
- barricade_window (frame + 6 destructible planks Plank_0..Plank_5)
- element115_crystal (glowing cyan crystal cluster on rock)
- ruined_tank (atmospheric courtyard Panzer wreck centerpiece)
- sandbag_wall, crate_military, barrel_rusted, light_cage, lab_pod, teleporter_pad
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def build_barricade_window():
    C.reset_scene()
    stone_tex = os.path.join(C.TEX_DIR, "env", "bunker_concrete_albedo.png")
    wood_tex = os.path.join(C.TEX_DIR, "env", "charred_wood_albedo.png")
    stone = C.make_pbr_mat("WindowStone", (0.32, 0.34, 0.36, 1.0), roughness=0.88, albedo_tex=stone_tex)
    wood = C.make_pbr_mat("WindowWood", (0.34, 0.21, 0.12, 1.0), roughness=0.78, albedo_tex=wood_tex)

    # Frame around 2.0m wide x 1.6m tall opening (sill at z=0.85)
    frame = C.join_objects([
        C.add_box("Sill", (2.30, 0.45, 0.85), (0, 0, 0.425), mat=stone, bevel=0.02),
        C.add_box("Lintel", (2.30, 0.45, 0.40), (0, 0, 2.65), mat=stone, bevel=0.02),
        C.add_box("PillarL", (0.28, 0.45, 1.60), (-1.02, 0, 1.65), mat=stone, bevel=0.02),
        C.add_box("PillarR", (0.28, 0.45, 1.60), (1.02, 0, 1.65), mat=stone, bevel=0.02),
    ], "WindowFrame")

    # 6 Individual planks named Plank_0 .. Plank_5 so Godot can break/repair each board!
    planks_cfg = [
        (0, (0, -0.16, 1.05), (0, math.radians(-4), 0)),
        (1, (0, -0.18, 1.32), (0, math.radians(3), 0)),
        (2, (0, -0.15, 1.62), (0, math.radians(-6), 0)),
        (3, (0, -0.18, 1.92), (0, math.radians(5), 0)),
        (4, (0, -0.16, 2.22), (0, math.radians(-2), 0)),
        (5, (0, -0.22, 1.65), (0, math.radians(38), 0)),
    ]
    for idx, loc, rot in planks_cfg:
        p = C.add_box(f"Plank_{idx}", (1.96, 0.05, 0.19), loc, rot, mat=wood, bevel=0.006)
        C.auto_uv_box(p)

    C.export_asset("env", "barricade_window")


def build_element115_crystal():
    C.reset_scene()
    rock = C.make_pbr_mat("DarkRock", (0.08, 0.085, 0.095, 1.0), roughness=0.94)
    crystal = C.make_pbr_mat("Crystal115", (0.08, 0.88, 1.0, 1.0), metallic=0.12, roughness=0.14, emission=(0.06, 0.90, 1.0), emission_strength=2.5)

    parts = [
        C.add_box("RockCore", (0.92, 0.85, 0.32), (0, 0, 0.14), (0, 0, math.radians(18)), mat=rock, bevel=0.06),
        C.add_box("RockSlab1", (0.65, 0.60, 0.24), (-0.22, 0.14, 0.18), (math.radians(12), math.radians(-14), 0.4), mat=rock, bevel=0.05),
        C.add_box("RockSlab2", (0.58, 0.55, 0.22), (0.24, -0.15, 0.16), (math.radians(-15), math.radians(16), -0.5), mat=rock, bevel=0.05),
        C.add_cone("Shard1", 0.15, 0.02, 1.02, (0, 0.02, 0.58), (math.radians(8), math.radians(-10), 0), vertices=6, mat=crystal),
        C.add_cone("Shard2", 0.12, 0.015, 0.78, (0.20, 0.12, 0.46), (math.radians(-18), math.radians(24), 0.5), vertices=6, mat=crystal),
        C.add_cone("Shard3", 0.11, 0.015, 0.70, (-0.18, -0.10, 0.42), (math.radians(22), math.radians(-26), -0.4), vertices=6, mat=crystal),
        C.add_cone("Shard4", 0.08, 0.015, 0.50, (0.06, -0.22, 0.36), (math.radians(-26), math.radians(-12), 0.2), vertices=6, mat=crystal),
        C.add_cone("Shard5", 0.075, 0.01, 0.46, (-0.22, 0.20, 0.35), (math.radians(25), math.radians(18), 0.8), vertices=6, mat=crystal),
    ]
    C.join_objects(parts, "Element115Crystal")
    C.export_asset("env", "element115_crystal")


def build_ruined_tank():
    C.reset_scene()
    p_alb = os.path.join(C.TEX_DIR, "env", "panzer_armor_albedo.png")
    p_nrm = os.path.join(C.TEX_DIR, "env", "panzer_armor_normal.png")
    p_rgh = os.path.join(C.TEX_DIR, "env", "panzer_armor_roughness.png")
    armor = C.make_pbr_mat("TankArmor", (0.16, 0.18, 0.17, 1.0), metallic=0.32, roughness=0.68, albedo_tex=p_alb, normal_tex=p_nrm, roughness_tex=p_rgh)
    dark_steel = C.make_pbr_mat("TankDarkSteel", (0.10, 0.11, 0.11, 1.0), metallic=0.65, roughness=0.58)
    treads = C.make_pbr_mat("TankTreads", (0.08, 0.075, 0.07, 1.0), metallic=0.45, roughness=0.78)

    parts = [
        C.add_box("Hull", (2.5, 4.9, 0.96), (0, 0, 0.72), (0, math.radians(-2.5), 0), mat=armor, bevel=0.05),
        C.add_box("GlacisFront", (2.46, 0.75, 0.55), (0, 2.32, 0.78), (math.radians(32), math.radians(-2.5), 0), mat=armor, bevel=0.03),
        C.add_box("EngineDeck", (2.3, 1.6, 0.22), (0, -1.5, 1.24), (0, math.radians(-2.5), 0), mat=dark_steel, bevel=0.02),
        C.add_box("SkirtL", (0.12, 5.0, 0.52), (-1.62, 0, 0.62), mat=armor, bevel=0.02),
        C.add_box("SkirtR", (0.12, 5.0, 0.52), (1.62, 0, 0.62), mat=armor, bevel=0.02),
        C.add_box("TrackL", (0.56, 5.2, 0.78), (-1.32, 0, 0.40), mat=treads, bevel=0.05),
        C.add_box("TrackR", (0.56, 5.2, 0.78), (1.32, 0, 0.40), mat=treads, bevel=0.05),
        C.add_cyl("Turret", 1.08, 0.72, (0, 0.25, 1.56), (0, 0, math.radians(22)), vertices=8, mat=armor),
        C.add_box("Mantlet", (0.85, 0.36, 0.46), (0.28, 1.20, 1.58), (0, 0, math.radians(-20)), mat=dark_steel, bevel=0.03),
        C.add_cyl("Cannon", 0.10, 3.25, (0.62, 2.05, 1.62), (math.radians(95), 0, math.radians(-20)), mat=dark_steel),
        C.add_cyl("MuzzleBrake", 0.16, 0.34, (1.16, 3.55, 1.76), (math.radians(95), 0, math.radians(-20)), mat=dark_steel),
        C.add_cyl("Cupola", 0.34, 0.26, (-0.25, -0.05, 2.02), mat=dark_steel),
        C.add_cyl("FuelDrumL", 0.24, 0.82, (-0.65, -2.0, 1.46), (0, math.radians(90), 0), mat=treads),
        C.add_cyl("FuelDrumR", 0.24, 0.82, (0.65, -2.0, 1.46), (0, math.radians(90), 0), mat=treads),
    ]
    for wy in (-1.9, -0.95, 0.0, 0.95, 1.9):
        parts.append(C.add_cyl(f"WheelL_{wy}", 0.32, 0.18, (-1.42, wy, 0.34), (0, math.radians(90), 0), mat=dark_steel))
        parts.append(C.add_cyl(f"WheelR_{wy}", 0.32, 0.18, (1.42, wy, 0.34), (0, math.radians(90), 0), mat=dark_steel))

    C.join_objects(parts, "RuinedTank")
    C.export_asset("env", "ruined_tank")


def build_sandbag_wall():
    C.reset_scene()
    b_alb = os.path.join(C.TEX_DIR, "env", "burlap_albedo.png")
    b_nrm = os.path.join(C.TEX_DIR, "env", "burlap_normal.png")
    b_rgh = os.path.join(C.TEX_DIR, "env", "burlap_roughness.png")
    bag = C.make_pbr_mat("SandbagCloth", (0.28, 0.24, 0.17, 1.0), roughness=0.94, albedo_tex=b_alb, normal_tex=b_nrm, roughness_tex=b_rgh)
    wood_tex = os.path.join(C.TEX_DIR, "env", "charred_wood_albedo.png")
    stake = C.make_pbr_mat("SandbagStake", (0.22, 0.14, 0.08, 1.0), roughness=0.86, albedo_tex=wood_tex)
    parts = [
        C.add_box("StakeL", (0.09, 0.09, 0.92), (-1.22, 0.18, 0.45), (math.radians(6), 0, 0), mat=stake, bevel=0.008),
        C.add_box("StakeR", (0.09, 0.09, 0.92), (1.22, 0.18, 0.45), (math.radians(6), 0, 0), mat=stake, bevel=0.008),
    ]
    for row in range(3):
        z = 0.12 + row * 0.21
        count = 4 - (row % 2)
        for i in range(count):
            x = (i - (count - 1) * 0.5) * 0.59
            jitter_z = math.sin(row * 2.3 + i * 1.7) * 0.07
            jitter_y = math.cos(row * 1.9 + i * 2.1) * 0.03
            parts.append(C.add_box(f"Bag_{row}_{i}", (0.58, 0.36, 0.21), (x, jitter_y, z), (0, math.radians((i - 1) * 2.0), jitter_z), mat=bag, bevel=0.045))
    C.join_objects(parts, "SandbagWall")
    C.export_asset("env", "sandbag_wall")


def build_crate_military():
    C.reset_scene()
    wood_tex = os.path.join(C.TEX_DIR, "env", "charred_wood_albedo.png")
    olive = C.make_pbr_mat("CrateOlive", (0.18, 0.22, 0.14, 1.0), roughness=0.82, albedo_tex=wood_tex)
    iron = C.make_pbr_mat("CrateIron", (0.12, 0.13, 0.14, 1.0), metallic=0.72, roughness=0.52)
    C.join_objects([
        C.add_box("Body", (1.10, 0.75, 0.68), (0, 0, 0.34), mat=olive, bevel=0.015),
        C.add_box("Lid", (1.16, 0.80, 0.08), (0, 0, 0.70), mat=olive, bevel=0.01),
        C.add_box("StrapL", (0.08, 0.82, 0.72), (-0.42, 0, 0.36), mat=iron),
        C.add_box("StrapR", (0.08, 0.82, 0.72), (0.42, 0, 0.36), mat=iron),
    ], "CrateMilitary")
    C.export_asset("env", "crate_military")


def build_barrel_rusted():
    C.reset_scene()
    steel_tex = os.path.join(C.TEX_DIR, "env", "rusted_steel_albedo.png")
    steel_nrm = os.path.join(C.TEX_DIR, "env", "rusted_steel_normal.png")
    rust = C.make_pbr_mat("BarrelRust", (0.30, 0.15, 0.09, 1.0), metallic=0.45, roughness=0.72, albedo_tex=steel_tex, normal_tex=steel_nrm)
    C.join_objects([
        C.add_cyl("Drum", 0.31, 0.92, (0, 0, 0.46), mat=rust),
        C.add_torus("Rib1", 0.315, 0.016, (0, 0, 0.30), mat=rust),
        C.add_torus("Rib2", 0.315, 0.016, (0, 0, 0.62), mat=rust),
    ], "BarrelRusted")
    C.export_asset("env", "barrel_rusted")


def build_light_cage():
    C.reset_scene()
    iron = C.make_pbr_mat("CageIron", (0.14, 0.14, 0.16, 1.0), metallic=0.78, roughness=0.48)
    bulb = C.make_pbr_mat("WarmBulb", (1.0, 0.62, 0.22, 1.0), roughness=0.1, emission=(1.0, 0.58, 0.18), emission_strength=3.2)
    C.join_objects([
        C.add_box("BackPlate", (0.24, 0.06, 0.36), (0, 0, 0), mat=iron, bevel=0.008),
        C.add_sphere("Bulb", 0.085, (1.0, 1.2, 1.4), (0, -0.09, 0), mat=bulb),
        C.add_torus("CageRing1", 0.11, 0.01, (0, -0.09, 0.06), mat=iron),
        C.add_torus("CageRing2", 0.11, 0.01, (0, -0.09, -0.06), mat=iron),
    ], "LightCage")
    C.export_asset("env", "light_cage")


def build_lab_pod():
    C.reset_scene()
    steel = C.make_pbr_mat("PodSteel", (0.14, 0.17, 0.20, 1.0), metallic=0.80, roughness=0.40)
    fluid = C.make_pbr_mat("PodFluid", (0.04, 0.36, 0.42, 1.0), roughness=0.10, emission=(0.04, 0.55, 0.62), emission_strength=0.42, alpha=0.30)
    specimen = C.make_pbr_mat("SpecimenDark", (0.34, 0.44, 0.30, 1.0), roughness=0.58)
    specimen_organ = C.make_pbr_mat("SpecimenOrgan", (0.14, 0.92, 0.68, 1.0), roughness=0.25, emission=(0.14, 0.92, 0.68), emission_strength=1.45)

    # Opaco metallic structure & specimen core
    solid_parts = [
        C.add_cyl("Base", 0.64, 0.34, (0, 0, 0.17), mat=steel),
        C.add_cyl("Cap", 0.64, 0.32, (0, 0, 2.34), mat=steel),
        C.add_torus("MidRing1", 0.50, 0.025, (0, 0, 0.72), mat=steel),
        C.add_torus("MidRing2", 0.50, 0.025, (0, 0, 1.80), mat=steel),
        C.add_cyl("Pillar1", 0.052, 2.1, (-0.54, 0, 1.25), mat=steel),
        C.add_cyl("Pillar2", 0.052, 2.1, (0.54, 0, 1.25), mat=steel),
        C.add_cyl("Pillar3", 0.052, 2.1, (0, 0.54, 1.25), mat=steel),
        C.add_cyl("Pillar4", 0.052, 2.1, (0, -0.54, 1.25), mat=steel),
        # Suspended mutated specimen inside tank
        C.add_sphere("SpecHead", 0.16, (0.95, 1.15, 1.15), (0, 0.04, 1.66), mat=specimen),
        C.add_sphere("SpecTorso", 0.18, (1.1, 0.85, 1.5), (0, -0.02, 1.28), mat=specimen),
        C.add_sphere("SpecSpineGlow1", 0.075, (1, 1, 1), (0, 0.08, 1.66), mat=specimen_organ),
        C.add_sphere("SpecSpineGlow2", 0.085, (1, 1, 1), (0, -0.08, 1.32), mat=specimen_organ),
        C.add_cyl("SpecLimbL", 0.055, 0.58, (-0.18, 0.05, 1.05), (math.radians(24), math.radians(15), 0), mat=specimen),
        C.add_cyl("SpecLimbR", 0.055, 0.58, (0.18, 0.05, 1.05), (math.radians(24), math.radians(-15), 0), mat=specimen),
        C.add_torus("CoreRingBot", 0.28, 0.022, (0, 0, 0.38), mat=specimen_organ),
    ]
    C.join_objects(solid_parts, "LabPodCore")

    glass = C.add_cyl("GlassTube", 0.46, 1.92, (0, 0, 1.26), vertices=24, mat=fluid)
    C.auto_uv_box(glass)
    C.export_asset("env", "lab_pod")


def build_teleporter_pad():
    C.reset_scene()
    steel = C.make_pbr_mat("PadSteel", (0.16, 0.18, 0.22, 1.0), metallic=0.78, roughness=0.40)
    glow = C.make_pbr_mat("PadGlow", (0.08, 0.88, 1.0, 1.0), roughness=0.15, emission=(0.08, 0.88, 1.0), emission_strength=2.6)
    C.join_objects([
        C.add_cyl("Platform", 1.85, 0.22, (0, 0, 0.11), vertices=12, mat=steel),
        C.add_torus("GlowRing", 1.45, 0.05, (0, 0, 0.23), mat=glow),
        C.add_cyl("CoilL", 0.14, 1.8, (-1.65, 0, 1.0), mat=steel),
        C.add_cyl("CoilR", 0.14, 1.8, (1.65, 0, 1.0), mat=steel),
        C.add_cyl("CoilB", 0.14, 1.8, (0, 1.65, 1.0), mat=steel),
        C.add_sphere("OrbL", 0.16, (1, 1, 1), (-1.65, 0, 1.95), mat=glow),
        C.add_sphere("OrbR", 0.16, (1, 1, 1), (1.65, 0, 1.95), mat=glow),
        C.add_sphere("OrbB", 0.16, (1, 1, 1), (0, 1.65, 1.95), mat=glow),
    ], "TeleporterPad")
    C.export_asset("env", "teleporter_pad")


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
    print("ALL ENVIRONMENTAL & ARCHITECTURAL PROPS EXPORTED!")
