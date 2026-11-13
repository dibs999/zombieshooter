"""Generate all 10 high-detail first-person weapon models in Blender (.blend + .glb).
Coordinate convention in Blender:
  +Y = forward toward muzzle (exports to -Z in Godot)
  +Z = up (exports to +Y in Godot)
  +X = right (exports to +X in Godot)
Origin (0,0,0) = player right-hand grip center.
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def weapon_mats():
    gunmetal = C.make_pbr_mat("Gunmetal", (0.20, 0.22, 0.25, 1.0), metallic=0.84, roughness=0.34)
    dark_steel = C.make_pbr_mat("DarkSteel", (0.11, 0.12, 0.14, 1.0), metallic=0.88, roughness=0.28)
    chrome = C.make_pbr_mat("Chrome", (0.74, 0.77, 0.80, 1.0), metallic=0.95, roughness=0.16)
    walnut = C.make_pbr_mat("WalnutWood", (0.28, 0.14, 0.07, 1.0), metallic=0.0, roughness=0.55)
    bakelite = C.make_pbr_mat("Bakelite", (0.20, 0.07, 0.04, 1.0), metallic=0.05, roughness=0.45)
    brass = C.make_pbr_mat("Brass", (0.76, 0.56, 0.22, 1.0), metallic=0.88, roughness=0.24)
    tritium = C.make_pbr_mat("TritiumSight", (0.12, 1.0, 0.45, 1.0), metallic=0.0, roughness=0.18, emission=(0.12, 1.0, 0.45), emission_strength=2.2)
    plasma_orange = C.make_pbr_mat("PlasmaOrange", (1.0, 0.44, 0.06, 1.0), metallic=0.1, roughness=0.14, emission=(1.0, 0.42, 0.05), emission_strength=2.6)
    plasma_cyan = C.make_pbr_mat("PlasmaCyan", (0.06, 0.90, 1.0, 1.0), metallic=0.1, roughness=0.14, emission=(0.06, 0.90, 1.0), emission_strength=2.8)
    return locals()


def build_m1911():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("Grip", (0.030, 0.052, 0.110), (0, -0.015, -0.045), (math.radians(-14), 0, 0), m["bakelite"]),
        C.add_box("Frame", (0.032, 0.155, 0.032), (0, 0.048, 0.008), (0, 0, 0), m["dark_steel"]),
        C.add_box("Slide", (0.033, 0.205, 0.034), (0, 0.062, 0.034), (0, 0, 0), m["gunmetal"], bevel=0.004),
        C.add_cyl("Barrel", 0.0085, 0.21, (0, 0.068, 0.032), (math.radians(90), 0, 0), mat=m["chrome"], bevel=0.001),
        C.add_box("TriggerGuard", (0.014, 0.044, 0.032), (0, 0.032, -0.018), (0, 0, 0), m["dark_steel"]),
        C.add_box("Hammer", (0.010, 0.018, 0.020), (0, -0.042, 0.035), (math.radians(-25), 0, 0), m["chrome"]),
        C.add_box("RearSightL", (0.006, 0.012, 0.010), (-0.009, -0.030, 0.055), (0, 0, 0), m["dark_steel"]),
        C.add_box("RearSightR", (0.006, 0.012, 0.010), (0.009, -0.030, 0.055), (0, 0, 0), m["dark_steel"]),
        C.add_box("FrontSight", (0.005, 0.012, 0.012), (0, 0.154, 0.056), (0, 0, 0), m["tritium"], bevel=0.001),
        C.add_box("RearDotL", (0.003, 0.004, 0.004), (-0.009, -0.035, 0.056), (0, 0, 0), m["tritium"], bevel=0.0005),
        C.add_box("RearDotR", (0.003, 0.004, 0.004), (0.009, -0.035, 0.056), (0, 0, 0), m["tritium"], bevel=0.0005),
    ]
    C.join_objects(parts, "M1911")
    C.export_asset("weapons", "m1911")


def build_trench_shotgun():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("Stock", (0.040, 0.24, 0.095), (0, -0.15, -0.032), (math.radians(-10), 0, 0), m["walnut"], bevel=0.006),
        C.add_box("Receiver", (0.044, 0.20, 0.068), (0, 0.03, 0.018), (0, 0, 0), m["gunmetal"], bevel=0.004),
        C.add_cyl("Barrel", 0.015, 0.56, (0, 0.36, 0.038), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_cyl("MagTube", 0.013, 0.48, (0, 0.32, 0.008), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_cyl("PumpForend", 0.024, 0.17, (0, 0.27, 0.008), (math.radians(90), 0, 0), mat=m["walnut"], bevel=0.003),
        C.add_box("HeatShield", (0.034, 0.26, 0.012), (0, 0.30, 0.052), (0, 0, 0), m["dark_steel"]),
        C.add_box("BayonetLug", (0.022, 0.036, 0.036), (0, 0.56, 0.018), (0, 0, 0), m["dark_steel"]),
        C.add_box("BeadSight", (0.005, 0.006, 0.009), (0, 0.625, 0.056), (0, 0, 0), m["brass"], bevel=0.001),
    ]
    C.join_objects(parts, "TrenchShotgun")
    C.export_asset("weapons", "trench_shotgun")


def build_mp40():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("Grip", (0.032, 0.045, 0.115), (0, -0.012, -0.048), (math.radians(-16), 0, 0), m["bakelite"]),
        C.add_box("LowerReceiver", (0.038, 0.22, 0.044), (0, 0.06, 0.008), (0, 0, 0), m["bakelite"], bevel=0.004),
        C.add_cyl("UpperTube", 0.022, 0.30, (0, 0.08, 0.036), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_cyl("Barrel", 0.010, 0.26, (0, 0.33, 0.036), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_box("MagWell", (0.030, 0.046, 0.050), (0, 0.175, -0.012), (0, 0, 0), m["gunmetal"]),
        C.add_box("Magazine", (0.024, 0.034, 0.19), (0, 0.175, -0.115), (math.radians(4), 0, 0), m["dark_steel"]),
        C.add_cyl("FoldStockL", 0.006, 0.22, (-0.024, -0.13, 0.010), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_cyl("FoldStockR", 0.006, 0.22, (0.024, -0.13, 0.010), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_box("ButtPlate", (0.056, 0.012, 0.095), (0, -0.24, -0.015), (0, 0, 0), m["dark_steel"]),
        C.add_box("FrontSight", (0.014, 0.016, 0.022), (0, 0.44, 0.054), (0, 0, 0), m["dark_steel"]),
        C.add_box("RearSight", (0.018, 0.016, 0.014), (0, -0.04, 0.062), (0, 0, 0), m["dark_steel"]),
    ]
    C.join_objects(parts, "MP40")
    C.export_asset("weapons", "mp40")


def build_stg44():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("WoodStock", (0.040, 0.23, 0.105), (0, -0.16, -0.024), (math.radians(-6), 0, 0), m["walnut"], bevel=0.006),
        C.add_box("Grip", (0.032, 0.046, 0.11), (0, -0.015, -0.045), (math.radians(-18), 0, 0), m["bakelite"]),
        C.add_box("Receiver", (0.044, 0.28, 0.068), (0, 0.08, 0.022), (0, 0, 0), m["gunmetal"], bevel=0.004),
        C.add_box("Handguard", (0.038, 0.21, 0.048), (0, 0.30, 0.026), (0, 0, 0), m["dark_steel"], bevel=0.003),
        C.add_cyl("Barrel", 0.011, 0.32, (0, 0.44, 0.028), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_cyl("GasTube", 0.009, 0.22, (0, 0.35, 0.052), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        # Curved banana magazine in 2 segments
        C.add_box("MagUpper", (0.026, 0.056, 0.105), (0, 0.15, -0.055), (math.radians(8), 0, 0), m["dark_steel"]),
        C.add_box("MagLower", (0.025, 0.054, 0.105), (0, 0.175, -0.145), (math.radians(24), 0, 0), m["dark_steel"]),
        C.add_box("FrontSightPost", (0.014, 0.016, 0.034), (0, 0.56, 0.054), (0, 0, 0), m["dark_steel"]),
        C.add_box("RearSight", (0.022, 0.026, 0.018), (0, 0.08, 0.064), (0, 0, 0), m["dark_steel"]),
    ]
    C.join_objects(parts, "STG44")
    C.export_asset("weapons", "stg44")


def build_m14():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("WoodBody", (0.044, 0.52, 0.068), (0, 0.06, -0.005), (0, 0, 0), m["walnut"], bevel=0.006),
        C.add_box("ButtStock", (0.042, 0.22, 0.105), (0, -0.22, -0.028), (math.radians(-6), 0, 0), m["walnut"], bevel=0.006),
        C.add_box("Receiver", (0.042, 0.18, 0.046), (0, 0.06, 0.036), (0, 0, 0), m["gunmetal"]),
        C.add_cyl("Barrel", 0.011, 0.42, (0, 0.44, 0.036), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_box("FlashHider", (0.020, 0.060, 0.020), (0, 0.65, 0.036), (0, 0, 0), m["dark_steel"]),
        C.add_box("Magazine", (0.028, 0.068, 0.105), (0, 0.11, -0.068), (math.radians(6), 0, 0), m["dark_steel"]),
        C.add_box("FrontSight", (0.014, 0.016, 0.028), (0, 0.60, 0.056), (0, 0, 0), m["dark_steel"]),
    ]
    C.join_objects(parts, "M14")
    C.export_asset("weapons", "m14")


def build_kar98k():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("WoodStock", (0.042, 0.68, 0.062), (0, 0.12, -0.004), (0, 0, 0), m["walnut"], bevel=0.006),
        C.add_box("Butt", (0.040, 0.22, 0.102), (0, -0.24, -0.028), (math.radians(-7), 0, 0), m["walnut"], bevel=0.006),
        C.add_cyl("Receiver", 0.019, 0.22, (0, 0.06, 0.034), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_cyl("Barrel", 0.010, 0.48, (0, 0.46, 0.034), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_cyl("BoltHandle", 0.006, 0.065, (0.028, 0.02, 0.034), (0, math.radians(90), 0), mat=m["chrome"]),
        # Optic sniper scope!
        C.add_cyl("ScopeTube", 0.017, 0.28, (0, 0.08, 0.078), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_cyl("ScopeBell", 0.023, 0.06, (0, 0.21, 0.078), (math.radians(90), 0, 0), mat=m["gunmetal"]),
        C.add_box("ScopeMount1", (0.018, 0.024, 0.035), (0, 0.01, 0.056), (0, 0, 0), m["dark_steel"]),
        C.add_box("ScopeMount2", (0.018, 0.024, 0.035), (0, 0.14, 0.056), (0, 0, 0), m["dark_steel"]),
    ]
    C.join_objects(parts, "Kar98k")
    C.export_asset("weapons", "kar98k")


def build_mg42():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_box("Butt", (0.048, 0.20, 0.105), (0, -0.20, -0.018), (0, 0, 0), m["walnut"], bevel=0.005),
        C.add_box("Grip", (0.034, 0.048, 0.115), (0, -0.015, -0.048), (math.radians(-14), 0, 0), m["bakelite"]),
        C.add_box("Receiver", (0.068, 0.28, 0.088), (0, 0.09, 0.025), (0, 0, 0), m["dark_steel"], bevel=0.004),
        C.add_box("BarrelShroud", (0.054, 0.38, 0.066), (0, 0.40, 0.028), (0, 0, 0), m["gunmetal"], bevel=0.004),
        C.add_cyl("Barrel", 0.014, 0.20, (0, 0.62, 0.028), (math.radians(90), 0, 0), mat=m["dark_steel"]),
        C.add_cyl("DrumMag", 0.075, 0.075, (-0.065, 0.14, -0.025), (0, math.radians(90), 0), mat=m["gunmetal"]),
        C.add_box("FeedCover", (0.066, 0.14, 0.018), (0, 0.14, 0.075), (0, 0, 0), m["gunmetal"]),
        C.add_box("FrontSight", (0.016, 0.016, 0.034), (0, 0.56, 0.072), (0, 0, 0), m["dark_steel"]),
    ]
    C.join_objects(parts, "MG42")
    C.export_asset("weapons", "mg42")


def build_raygun():
    C.reset_scene()
    m = weapon_mats()
    # Inspired directly by concept_weapons_packapunch Ray Cannon!
    parts = [
        C.add_box("Grip", (0.032, 0.052, 0.118), (0, -0.01, -0.045), (math.radians(-16), 0, 0), m["dark_steel"]),
        C.add_box("HandGuardLoop", (0.024, 0.095, 0.095), (0, 0.04, -0.045), (0, 0, 0), m["brass"]),
        C.add_sphere("RearCore", 0.055, (0.72, 1.35, 1.05), (0, 0.01, 0.022), mat=m["brass"]),
        C.add_cyl("ChamberGlass", 0.032, 0.13, (0, 0.12, 0.036), (math.radians(90), 0, 0), mat=m["plasma_orange"]),
        C.add_cyl("EmitterCone", 0.028, 0.16, (0, 0.25, 0.036), (math.radians(90), 0, 0), mat=m["brass"]),
        C.add_torus("Ring1", 0.042, 0.008, (0, 0.19, 0.036), (math.radians(90), 0, 0), mat=m["plasma_cyan"]),
        C.add_torus("Ring2", 0.036, 0.007, (0, 0.26, 0.036), (math.radians(90), 0, 0), mat=m["plasma_cyan"]),
        C.add_torus("Ring3", 0.030, 0.006, (0, 0.32, 0.036), (math.radians(90), 0, 0), mat=m["plasma_cyan"]),
        C.add_box("TopFin", (0.008, 0.14, 0.038), (0, 0.12, 0.085), (0, 0, 0), m["brass"]),
        C.add_cyl("MuzzleCup", 0.026, 0.045, (0, 0.35, 0.036), (math.radians(90), 0, 0), mat=m["plasma_orange"]),
    ]
    C.join_objects(parts, "RayGun")
    C.export_asset("weapons", "raygun")


def build_combat_knife():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_cyl("Handle", 0.016, 0.115, (0, 0, 0), (0, 0, 0), mat=m["bakelite"]),
        C.add_box("Crossguard", (0.018, 0.056, 0.010), (0, 0, 0.060), (0, 0, 0), m["dark_steel"]),
        C.add_box("Blade", (0.005, 0.028, 0.165), (0, 0.004, 0.145), (0, 0, 0), m["chrome"], bevel=0.002),
    ]
    C.join_objects(parts, "CombatKnife")
    C.export_asset("weapons", "combat_knife")


def build_frag_grenade():
    C.reset_scene()
    m = weapon_mats()
    parts = [
        C.add_sphere("Body", 0.042, (0.88, 0.88, 1.15), (0, 0, 0), mat=m["gunmetal"]),
        C.add_cyl("Neck", 0.016, 0.032, (0, 0, 0.052), (0, 0, 0), mat=m["brass"]),
        C.add_box("Spoon", (0.012, 0.028, 0.068), (0, 0.028, 0.028), (math.radians(18), 0, 0), m["dark_steel"]),
        C.add_torus("PinRing", 0.016, 0.003, (0.018, -0.01, 0.058), (0, math.radians(90), 0), mat=m["chrome"]),
    ]
    C.join_objects(parts, "FragGrenade")
    C.export_asset("weapons", "frag_grenade")


if __name__ == "__main__":
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
    print("ALL 10 WEAPON MODELS EXPORTED!")
