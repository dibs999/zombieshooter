"""Generate detailed, anatomically sculpted, rigged & animated CoD Zombies characters (.blend + .glb):
- zombie_soldier (M40 Stahlhelm w/ flared skirt & chinstrap, tattered PBR Wehrmacht tunic, exposed ribs, pouches, gaunt hands, jackboots)
- zombie_scientist (Group 935 researcher w/ patchy hair, brass goggles, open torn bloodied lab coat tails over dark jumpsuit)
- zombie_brute (Panzer hazmat juggernaut w/ draped hood, slotted glowing visor, gasmask, dual air hoses to back tanks, damaged steel chest & pauldrons)
- hellhound (Charred ember-cracked volcanic hound w/ glowing molten furnace core visible through 3D skeletal ribcage, fangs, spine spikes, bent claws)

Blender convention: +Y = Forward (Godot -Z), +Z = Up (Godot +Y), +X = Right.
Rig & NLA names match zombie_ai.gd / hellhound_ai.gd strictly.
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def char_mats():
    env = os.path.join(C.TEX_DIR, "env")
    wtex = os.path.join(C.TEX_DIR, "weapons")

    flesh_alb = os.path.join(env, "zombie_flesh_albedo.png")
    flesh_nrm = os.path.join(env, "zombie_flesh_normal.png")
    flesh_rgh = os.path.join(env, "zombie_flesh_roughness.png")

    cloth_alb = os.path.join(env, "zombie_cloth_albedo.png")
    cloth_nrm = os.path.join(env, "zombie_cloth_normal.png")
    cloth_rgh = os.path.join(env, "zombie_cloth_roughness.png")

    lab_alb = os.path.join(env, "zombie_labcoat_albedo.png")
    lab_nrm = os.path.join(env, "zombie_labcoat_normal.png")
    lab_rgh = os.path.join(env, "zombie_labcoat_roughness.png")

    panzer_alb = os.path.join(env, "panzer_armor_albedo.png")
    panzer_nrm = os.path.join(env, "panzer_armor_normal.png")
    panzer_rgh = os.path.join(env, "panzer_armor_roughness.png")

    rust_alb = os.path.join(env, "rusted_steel_albedo.png")
    rust_nrm = os.path.join(env, "rusted_steel_normal.png")
    rust_rgh = os.path.join(env, "rusted_steel_roughness.png")

    hound_alb = os.path.join(env, "hellhound_hide_albedo.png")
    hound_nrm = os.path.join(env, "hellhound_hide_normal.png")
    hound_rgh = os.path.join(env, "hellhound_hide_roughness.png")

    leather_alb = os.path.join(wtex, "fp_leather_albedo.png")
    leather_nrm = os.path.join(wtex, "fp_leather_normal.png")
    leather_rgh = os.path.join(wtex, "fp_leather_roughness.png")

    flesh = C.make_pbr_mat(
        "DecayedFlesh", (0.28, 0.31, 0.24, 1.0), roughness=0.70,
        albedo_tex=flesh_alb, normal_tex=flesh_nrm, roughness_tex=flesh_rgh,
        tint_tex=(0.94, 0.96, 0.90), normal_strength=0.38,
    )
    flesh_dark = C.make_pbr_mat(
        "RottedMuscle", (0.20, 0.05, 0.04, 1.0), roughness=0.45,
        albedo_tex=flesh_alb, normal_tex=flesh_nrm, roughness_tex=flesh_rgh,
        tint_tex=(0.72, 0.22, 0.20), normal_strength=0.46,
    )
    blood = C.make_pbr_mat("DriedBlood", (0.16, 0.015, 0.015, 1.0), roughness=0.36)
    bone_rib = C.make_pbr_mat("BoneRib", (0.58, 0.50, 0.40, 1.0), roughness=0.58)
    teeth = C.make_pbr_mat("GrimTeeth", (0.64, 0.58, 0.44, 1.0), roughness=0.44)

    uniform = C.make_pbr_mat(
        "TatteredUniform", (0.18, 0.20, 0.15, 1.0), roughness=0.88,
        albedo_tex=cloth_alb, normal_tex=cloth_nrm, roughness_tex=cloth_rgh,
        tint_tex=(0.95, 0.98, 0.90), normal_strength=0.42,
    )
    pants = C.make_pbr_mat(
        "TatteredPants", (0.12, 0.13, 0.11, 1.0), roughness=0.90,
        albedo_tex=cloth_alb, normal_tex=cloth_nrm, roughness_tex=cloth_rgh,
        tint_tex=(0.64, 0.66, 0.62), normal_strength=0.38,
    )
    lab_coat = C.make_pbr_mat(
        "BloodiedLabCoat", (0.52, 0.50, 0.46, 1.0), roughness=0.84,
        albedo_tex=lab_alb, normal_tex=lab_nrm, roughness_tex=lab_rgh,
        tint_tex=(0.94, 0.94, 0.92), normal_strength=0.36,
    )
    shirt_dark = C.make_pbr_mat(
        "ScientistShirt", (0.15, 0.18, 0.14, 1.0), roughness=0.86,
        albedo_tex=cloth_alb, normal_tex=cloth_nrm, roughness_tex=cloth_rgh,
        tint_tex=(0.74, 0.80, 0.64), normal_strength=0.36,
    )
    hazmat_cloth = C.make_pbr_mat(
        "HazmatCloth", (0.26, 0.23, 0.13, 1.0), roughness=0.86,
        albedo_tex=cloth_alb, normal_tex=cloth_nrm, roughness_tex=cloth_rgh,
        tint_tex=(1.22, 1.12, 0.68), normal_strength=0.42,
    )
    gasmask_rubber = C.make_pbr_mat(
        "GasmaskRubber", (0.07, 0.075, 0.08, 1.0), metallic=0.10, roughness=0.72,
        normal_tex=leather_nrm, normal_strength=0.28,
    )
    helmet_steel = C.make_pbr_mat(
        "HelmetSteel", (0.15, 0.17, 0.15, 1.0), metallic=0.68, roughness=0.46,
        albedo_tex=panzer_alb, normal_tex=panzer_nrm, roughness_tex=panzer_rgh,
        tint_tex=(0.86, 0.92, 0.84), normal_strength=0.36,
    )
    armor_plate = C.make_pbr_mat(
        "BruteArmor", (0.18, 0.19, 0.21, 1.0), metallic=0.80, roughness=0.42,
        albedo_tex=panzer_alb, normal_tex=panzer_nrm, roughness_tex=panzer_rgh,
        tint_tex=(1.08, 1.08, 1.12), normal_strength=0.44,
    )
    tank_metal = C.make_pbr_mat(
        "BruteTankSteel", (0.20, 0.21, 0.18, 1.0), metallic=0.72, roughness=0.48,
        albedo_tex=rust_alb, normal_tex=rust_nrm, roughness_tex=rust_rgh,
        tint_tex=(0.90, 0.94, 0.82), normal_strength=0.38,
    )
    hazard_yellow = C.make_pbr_mat("BruteStripe", (0.64, 0.44, 0.08, 1.0), metallic=0.18, roughness=0.56)
    boots = C.make_pbr_mat(
        "LeatherBoots", (0.08, 0.065, 0.055, 1.0), roughness=0.62,
        albedo_tex=leather_alb, normal_tex=leather_nrm, roughness_tex=leather_rgh,
        tint_tex=(0.70, 0.62, 0.56), normal_strength=0.32,
    )
    chrome = C.make_pbr_mat("TrimChrome", (0.68, 0.70, 0.72, 1.0), metallic=0.88, roughness=0.28)
    brass = C.make_pbr_mat("TrimBrass", (0.56, 0.40, 0.15, 1.0), metallic=0.85, roughness=0.34)
    dark_hair = C.make_pbr_mat("DarkHair", (0.07, 0.06, 0.055, 1.0), roughness=0.92)
    goggle_lens = C.make_pbr_mat(
        "GoggleLens", (0.14, 0.34, 0.40, 1.0), metallic=0.22, roughness=0.14,
        emission=(0.06, 0.22, 0.26), emission_strength=0.45,
    )
    eye_socket = C.make_pbr_mat("EyeSocket", (0.02, 0.015, 0.015, 1.0), roughness=0.95)
    eye_amber = C.make_pbr_mat("ZombieEyeAmber", (1.0, 0.50, 0.05, 1.0), roughness=0.10, emission=(1.0, 0.46, 0.04), emission_strength=3.8)
    eye_red = C.make_pbr_mat("BruteEyeOrange", (1.0, 0.30, 0.02, 1.0), roughness=0.10, emission=(1.0, 0.28, 0.02), emission_strength=4.2)

    hound_char = C.make_pbr_mat(
        "HoundCharcoal", (0.12, 0.10, 0.09, 1.0), roughness=0.74,
        albedo_tex=hound_alb, normal_tex=hound_nrm, roughness_tex=hound_rgh,
        tint_tex=(0.96, 0.94, 0.90), normal_strength=0.52,
    )
    hound_bone = C.make_pbr_mat("HoundCharredBone", (0.34, 0.24, 0.16, 1.0), roughness=0.58)
    magma = C.make_pbr_mat("HoundMagma", (1.0, 0.38, 0.04, 1.0), roughness=0.18, emission=(1.0, 0.36, 0.03), emission_strength=3.2)
    return locals()


# ---------------------------------------------------------------------------
# Organic Cross-Section Loft & Multi-Bone Feather Skinning Helpers
# ---------------------------------------------------------------------------

def _asym_ring(cx, cy, cz, rx, ry_front, ry_back, sides=16, z_ripple=0.0, seed=0.0):
    """Build an elliptical cross-section with distinct front (+Y) / back (-Y) depth and optional cloth tear ripple."""
    pts = []
    for i in range(sides):
        ang = (i / sides) * 2.0 * math.pi
        ca = math.cos(ang)
        sa = math.sin(ang)
        ry = ry_front if sa >= 0.0 else ry_back
        dz = math.sin(ang * 3.0 + seed) * z_ripple + math.cos(ang * 5.0 - seed) * (z_ripple * 0.5) if z_ripple > 0.0 else 0.0
        pts.append((cx + ca * rx, cy + sa * ry, cz + dz))
    return pts


def create_humanoid_rig(name, scale=1.0):
    arm_data = bpy.data.armatures.new(name + "_ArmData")
    arm_obj = bpy.data.objects.new(name + "_Armature", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    def add_bone(bname, head, tail, parent=None):
        b = arm_data.edit_bones.new(bname)
        b.head = (head[0] * scale, head[1] * scale, head[2] * scale)
        b.tail = (tail[0] * scale, tail[1] * scale, tail[2] * scale)
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b

    add_bone("Pelvis", (0, 0, 0.90), (0, 0, 1.04))
    add_bone("Spine", (0, 0, 1.04), (0, 0, 1.44), "Pelvis")
    add_bone("Head", (0, 0, 1.46), (0, 0, 1.74), "Spine")

    add_bone("Arm_L", (-0.22, 0, 1.38), (-0.24, 0, 1.06), "Spine")
    add_bone("Forearm_L", (-0.24, 0, 1.06), (-0.25, 0.04, 0.78), "Arm_L")
    add_bone("Arm_R", (0.22, 0, 1.38), (0.24, 0, 1.06), "Spine")
    add_bone("Forearm_R", (0.24, 0, 1.06), (0.25, 0.04, 0.78), "Arm_R")

    add_bone("Thigh_L", (-0.105, 0, 0.90), (-0.105, 0, 0.46), "Pelvis")
    add_bone("Shin_L", (-0.105, 0, 0.46), (-0.105, 0, 0.04), "Thigh_L")
    add_bone("Thigh_R", (0.105, 0, 0.90), (0.105, 0, 0.46), "Pelvis")
    add_bone("Shin_R", (0.105, 0, 0.46), (0.105, 0, 0.04), "Thigh_R")

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bind_skinned_mesh(mesh_obj, arm_obj, bone_names, weight_fn, scale=1.0, uv_scale=2.2):
    """Apply transforms/modifiers, compute triplanar UVs, and paint multi-bone gradient weights cleanly."""
    if mesh_obj is None:
        return
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    for mod in list(mesh_obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    C.uv_box_project(mesh_obj, scale=uv_scale)

    groups = {bn: mesh_obj.vertex_groups.new(name=bn) for bn in bone_names}
    inv_s = 1.0 / max(1e-5, scale)
    for v in mesh_obj.data.vertices:
        wdict = weight_fn(v.co.x * inv_s, v.co.y * inv_s, v.co.z * inv_s)
        total = sum(max(0.0, w) for w in wdict.values())
        if total <= 1e-6:
            groups[bone_names[0]].add([v.index], 1.0, "REPLACE")
            continue
        for bn, w in wdict.items():
            wn = max(0.0, w) / total
            if wn > 0.001 and bn in groups:
                groups[bn].add([v.index], wn, "REPLACE")

    mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mesh_obj.parent = arm_obj


def add_humanoid_animations(arm_obj, scale=1.0):
    if not arm_obj.animation_data:
        arm_obj.animation_data_create()
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"

    def make_action(name, frame_poses, loop=True):
        act = bpy.data.actions.new(name=name)
        act.use_fake_user = True
        arm_obj.animation_data.action = act
        for frame, poses in frame_poses.items():
            for pb in arm_obj.pose.bones:
                pb.rotation_euler = (0, 0, 0)
                pb.location = (0, 0, 0)
            for bname, vals in poses.items():
                pb = arm_obj.pose.bones[bname]
                if "rot" in vals:
                    pb.rotation_euler = tuple(math.radians(a) for a in vals["rot"])
                if "loc" in vals:
                    pb.location = tuple(v * scale for v in vals["loc"])
            for pb in arm_obj.pose.bones:
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)
                pb.keyframe_insert(data_path="location", frame=frame)
        track = arm_obj.animation_data.nla_tracks.new()
        track.name = name
        end_f = max(frame_poses.keys())
        strip = track.strips.new(name, 1, act)
        strip.action_frame_start = 1
        strip.action_frame_end = end_f
        arm_obj.animation_data.action = None

    make_action("Idle", {
        1: {"Spine": {"rot": (-8, -3, 0)}, "Head": {"rot": (-8, 0, -6)}, "Arm_L": {"rot": (32, 0, -6)}, "Forearm_L": {"rot": (22, 0, 0)}, "Arm_R": {"rot": (26, 0, 6)}, "Forearm_R": {"rot": (18, 0, 0)}},
        25: {"Spine": {"rot": (-12, 3, 2)}, "Head": {"rot": (-10, 5, 6)}, "Arm_L": {"rot": (38, 0, -8)}, "Forearm_L": {"rot": (24, 0, 0)}, "Arm_R": {"rot": (32, 0, 8)}, "Forearm_R": {"rot": (20, 0, 0)}},
        49: {"Spine": {"rot": (-8, -3, 0)}, "Head": {"rot": (-8, 0, -6)}, "Arm_L": {"rot": (32, 0, -6)}, "Forearm_L": {"rot": (22, 0, 0)}, "Arm_R": {"rot": (26, 0, 6)}, "Forearm_R": {"rot": (18, 0, 0)}},
    })

    make_action("Walk", {
        1: {"Pelvis": {"loc": (0, 0, -0.02), "rot": (0, -4, 4)}, "Spine": {"rot": (-15, 0, -6)}, "Head": {"rot": (10, 8, 6)},
            "Arm_L": {"rot": (72, 0, -6)}, "Forearm_L": {"rot": (22, 0, 0)},
            "Arm_R": {"rot": (82, 0, 6)}, "Forearm_R": {"rot": (26, 0, 0)},
            "Thigh_L": {"rot": (22, 0, 0)}, "Shin_L": {"rot": (-22, 0, 0)},
            "Thigh_R": {"rot": (-20, 0, 0)}, "Shin_R": {"rot": (-12, 0, 0)}},
        17: {"Pelvis": {"loc": (0, 0, 0.02), "rot": (0, 4, -4)}, "Spine": {"rot": (-17, 0, 5)}, "Head": {"rot": (8, -8, -5)},
            "Arm_L": {"rot": (84, 0, -4)}, "Forearm_L": {"rot": (24, 0, 0)},
            "Arm_R": {"rot": (70, 0, 4)}, "Forearm_R": {"rot": (20, 0, 0)},
            "Thigh_L": {"rot": (-20, 0, 0)}, "Shin_L": {"rot": (-12, 0, 0)},
            "Thigh_R": {"rot": (22, 0, 0)}, "Shin_R": {"rot": (-24, 0, 0)}},
        33: {"Pelvis": {"loc": (0, 0, -0.02), "rot": (0, -4, 4)}, "Spine": {"rot": (-15, 0, -6)}, "Head": {"rot": (10, 8, 6)},
            "Arm_L": {"rot": (72, 0, -6)}, "Forearm_L": {"rot": (22, 0, 0)},
            "Arm_R": {"rot": (82, 0, 6)}, "Forearm_R": {"rot": (26, 0, 0)},
            "Thigh_L": {"rot": (22, 0, 0)}, "Shin_L": {"rot": (-22, 0, 0)},
            "Thigh_R": {"rot": (-20, 0, 0)}, "Shin_R": {"rot": (-12, 0, 0)}},
    })

    make_action("Run", {
        1: {"Pelvis": {"loc": (0, 0, -0.04)}, "Spine": {"rot": (-24, 0, -8)}, "Head": {"rot": (16, 0, 4)},
            "Arm_L": {"rot": (90, 0, -8)}, "Forearm_L": {"rot": (30, 0, 0)},
            "Arm_R": {"rot": (74, 0, 8)}, "Forearm_R": {"rot": (34, 0, 0)},
            "Thigh_L": {"rot": (42, 0, 0)}, "Shin_L": {"rot": (-42, 0, 0)},
            "Thigh_R": {"rot": (-36, 0, 0)}, "Shin_R": {"rot": (-20, 0, 0)}},
        10: {"Pelvis": {"loc": (0, 0, 0.03)}, "Spine": {"rot": (-26, 0, 8)}, "Head": {"rot": (18, 0, -4)},
            "Arm_L": {"rot": (74, 0, -8)}, "Forearm_L": {"rot": (34, 0, 0)},
            "Arm_R": {"rot": (92, 0, 8)}, "Forearm_R": {"rot": (28, 0, 0)},
            "Thigh_L": {"rot": (-36, 0, 0)}, "Shin_L": {"rot": (-20, 0, 0)},
            "Thigh_R": {"rot": (42, 0, 0)}, "Shin_R": {"rot": (-45, 0, 0)}},
        19: {"Pelvis": {"loc": (0, 0, -0.04)}, "Spine": {"rot": (-24, 0, -8)}, "Head": {"rot": (16, 0, 4)},
            "Arm_L": {"rot": (90, 0, -8)}, "Forearm_L": {"rot": (30, 0, 0)},
            "Arm_R": {"rot": (74, 0, 8)}, "Forearm_R": {"rot": (34, 0, 0)},
            "Thigh_L": {"rot": (42, 0, 0)}, "Shin_L": {"rot": (-42, 0, 0)},
            "Thigh_R": {"rot": (-36, 0, 0)}, "Shin_R": {"rot": (-20, 0, 0)}},
    })

    make_action("Attack", {
        1: {"Spine": {"rot": (6, 0, 0)}, "Arm_L": {"rot": (118, 0, -18)}, "Arm_R": {"rot": (122, 0, 18)}},
        10: {"Spine": {"rot": (-28, 0, 0)}, "Head": {"rot": (12, 0, 0)}, "Arm_L": {"rot": (54, 0, 12)}, "Forearm_L": {"rot": (40, 0, 0)}, "Arm_R": {"rot": (50, 0, -12)}, "Forearm_R": {"rot": (40, 0, 0)}},
        21: {"Spine": {"rot": (-14, 0, 0)}, "Arm_L": {"rot": (82, 0, -6)}, "Arm_R": {"rot": (82, 0, 6)}},
    }, loop=False)

    make_action("Death", {
        1: {"Pelvis": {"loc": (0, 0, 0), "rot": (0, 0, 0)}, "Spine": {"rot": (-10, 0, 0)}},
        12: {"Pelvis": {"loc": (0, -0.25, -0.35), "rot": (45, 0, 6)}, "Spine": {"rot": (20, 0, 0)}, "Arm_L": {"rot": (45, 0, -35)}, "Arm_R": {"rot": (55, 0, 35)}},
        25: {"Pelvis": {"loc": (0, -0.55, -0.82), "rot": (88, 0, 12)}, "Spine": {"rot": (10, 0, 0)}, "Head": {"rot": (-15, 10, 0)}, "Arm_L": {"rot": (15, 0, -55)}, "Arm_R": {"rot": (20, 0, 50)}, "Thigh_L": {"rot": (-10, 0, -8)}, "Thigh_R": {"rot": (-12, 0, 10)}},
    }, loop=False)

    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------------------
# Sculpted Zombie Anatomy Modules
# ---------------------------------------------------------------------------

def _build_zombie_head(m, scale, eye_mat, variant):
    def s(v):
        return tuple(c * scale for c in v)

    # Contoured zombie cranium with narrow cheeks & domed crown
    skull_rings = [
        _asym_ring(0.0, 0.005 * scale, 1.45 * scale, 0.058 * scale, 0.056 * scale, 0.062 * scale, 14),
        _asym_ring(0.0, 0.014 * scale, 1.53 * scale, 0.068 * scale, 0.088 * scale, 0.084 * scale, 14),
        _asym_ring(0.0, 0.010 * scale, 1.59 * scale, 0.082 * scale, 0.098 * scale, 0.104 * scale, 16),
        _asym_ring(0.0, 0.006 * scale, 1.66 * scale, 0.086 * scale, 0.102 * scale, 0.112 * scale, 16),
        _asym_ring(0.0, -0.004 * scale, 1.72 * scale, 0.072 * scale, 0.084 * scale, 0.095 * scale, 16),
        _asym_ring(0.0, -0.010 * scale, 1.755 * scale, 0.036 * scale, 0.042 * scale, 0.048 * scale, 16),
    ]
    parts = [
        C.add_ring_loft("SkullCranium", skull_rings, mat=m["flesh"], smooth_angle=64.0),
        # Supraorbital brow ridge, zygomatic cheekbones & gaunt jawline
        C.add_box("BrowRidge", s((0.128, 0.036, 0.022)), s((0, 0.096, 1.635)), (math.radians(-6), 0, 0), mat=m["flesh"], bevel=0.007 * scale),
        C.add_box("CheekArchL", s((0.042, 0.048, 0.030)), s((-0.052, 0.082, 1.568)), (0, math.radians(-12), math.radians(-16)), mat=m["flesh"], bevel=0.007 * scale),
        C.add_box("CheekArchR", s((0.042, 0.048, 0.030)), s((0.052, 0.082, 1.568)), (0, math.radians(12), math.radians(16)), mat=m["flesh"], bevel=0.007 * scale),
        C.add_box("NoseBridge", s((0.024, 0.032, 0.042)), s((0, 0.104, 1.590)), (math.radians(18), 0, 0), mat=m["flesh"], bevel=0.005 * scale),
        C.add_box("NasalCav", s((0.020, 0.016, 0.028)), s((0, 0.108, 1.572)), mat=m["eye_socket"], bevel=0.002 * scale),
        # Recessed dark orbital sockets & burning zombie pupils
        C.add_sphere("SocketL", 0.023 * scale, (1.08, 0.65, 0.92), s((-0.036, 0.094, 1.608)), mat=m["eye_socket"]),
        C.add_sphere("SocketR", 0.023 * scale, (1.08, 0.65, 0.92), s((0.036, 0.094, 1.608)), mat=m["eye_socket"]),
        C.add_sphere("EyeL", 0.0125 * scale, (1, 0.9, 1), s((-0.036, 0.102, 1.608)), mat=eye_mat),
        C.add_sphere("EyeR", 0.0125 * scale, (1, 0.9, 1), s((0.036, 0.102, 1.608)), mat=eye_mat),
        # Maxilla, open gory mouth interior & hinged jagged mandible
        C.add_box("MouthGore", s((0.068, 0.046, 0.050)), s((0, 0.082, 1.522)), mat=m["flesh_dark"], bevel=0.004 * scale),
        C.add_box("Mandible", s((0.082, 0.092, 0.032)), s((0, 0.048, 1.482)), (math.radians(-16), 0, 0), mat=m["flesh"], bevel=0.007 * scale),
        C.add_box("BloodChin", s((0.062, 0.034, 0.028)), s((0, 0.090, 1.480)), (math.radians(-16), 0, 0), mat=m["blood"], bevel=0.005 * scale),
    ]
    # Individual jagged teeth (upper & lower rows)
    for ti, tx in enumerate((-0.026, -0.015, -0.005, 0.005, 0.015, 0.026)):
        h = 0.016 if ti in (0, 5) else 0.013
        parts.append(C.add_cone(f"TopTooth_{ti}", 0.0042 * scale, 0.0012 * scale, h * scale, s((tx, 0.100, 1.542)), (math.radians(180), 0, 0), vertices=6, mat=m["teeth"]))
        parts.append(C.add_cone(f"BotTooth_{ti}", 0.0040 * scale, 0.0012 * scale, (h * 0.9) * scale, s((tx, 0.098, 1.498)), (0, 0, 0), vertices=6, mat=m["teeth"]))

    # Tendon cords on side of neck/jaw
    for sx in (-1, 1):
        parts.append(C.add_tube_pipe(
            f"NeckTendon_{sx}",
            [s((sx * 0.048, -0.005, 1.55)), s((sx * 0.038, 0.018, 1.49)), s((sx * 0.028, 0.032, 1.43))],
            radius=0.011 * scale, segments=7, mat=m["flesh_dark"],
        ))

    if variant == "soldier":
        # Authentic M40 Wehrmacht Stahlhelm loft with flared neck skirt + leather chinstrap
        helm_rings = [
            _asym_ring(0.0, -0.018 * scale, 1.592 * scale, 0.118 * scale, 0.118 * scale, 0.152 * scale, 18),
            _asym_ring(0.0, -0.010 * scale, 1.622 * scale, 0.114 * scale, 0.128 * scale, 0.144 * scale, 18),
            _asym_ring(0.0, -0.006 * scale, 1.662 * scale, 0.106 * scale, 0.120 * scale, 0.132 * scale, 18),
            _asym_ring(0.0, -0.006 * scale, 1.720 * scale, 0.094 * scale, 0.106 * scale, 0.118 * scale, 18),
            _asym_ring(0.0, -0.008 * scale, 1.768 * scale, 0.056 * scale, 0.064 * scale, 0.072 * scale, 18),
            _asym_ring(0.0, -0.010 * scale, 1.786 * scale, 0.018 * scale, 0.020 * scale, 0.022 * scale, 18),
        ]
        parts.append(C.add_ring_loft("Stahlhelm", helm_rings, mat=m["helmet_steel"], smooth_angle=52.0))
        parts.append(C.add_box("HelmetBadge", s((0.020, 0.008, 0.026)), s((-0.112, 0.030, 1.645)), (0, 0, math.radians(-12)), mat=m["chrome"], bevel=0.002 * scale))
        parts.append(C.add_tube_pipe(
            "ChinStrap",
            [s((-0.098, 0.02, 1.61)), s((-0.084, 0.055, 1.52)), s((0, 0.068, 1.466)), s((0.084, 0.055, 1.52)), s((0.098, 0.02, 1.61))],
            radius=0.008 * scale, segments=6, mat=m["boots"],
        ))
    elif variant == "scientist":
        # Receding disheveled temple hair tufts & strapped brass scientist goggles
        parts.extend([
            C.add_box("HairTuftL", s((0.032, 0.110, 0.060)), s((-0.076, -0.015, 1.68)), (math.radians(-8), math.radians(-16), 0), mat=m["dark_hair"], bevel=0.006 * scale),
            C.add_box("HairTuftR", s((0.032, 0.110, 0.060)), s((0.076, -0.015, 1.68)), (math.radians(-8), math.radians(16), 0), mat=m["dark_hair"], bevel=0.006 * scale),
            C.add_box("HairBack", s((0.125, 0.042, 0.070)), s((0, -0.098, 1.66)), mat=m["dark_hair"], bevel=0.008 * scale),
            C.add_box("ForeheadStrands", s((0.095, 0.050, 0.018)), s((0.015, 0.068, 1.705)), (math.radians(24), math.radians(12), 0), mat=m["dark_hair"], bevel=0.003 * scale),
            C.add_cyl("GoggleCupL", 0.026 * scale, 0.028 * scale, s((-0.037, 0.104, 1.648)), (math.radians(76), 0, math.radians(-8)), vertices=16, mat=m["brass"], bevel=0.002 * scale),
            C.add_cyl("GoggleCupR", 0.026 * scale, 0.028 * scale, s((0.037, 0.104, 1.648)), (math.radians(76), 0, math.radians(8)), vertices=16, mat=m["brass"], bevel=0.002 * scale),
            C.add_cyl("GoggleLensL", 0.020 * scale, 0.008 * scale, s((-0.037, 0.116, 1.651)), (math.radians(76), 0, math.radians(-8)), vertices=14, mat=m["goggle_lens"], bevel=0.001 * scale),
            C.add_cyl("GoggleLensR", 0.020 * scale, 0.008 * scale, s((0.037, 0.116, 1.651)), (math.radians(76), 0, math.radians(8)), vertices=14, mat=m["goggle_lens"], bevel=0.001 * scale),
            C.add_torus("GoggleStrap", 0.102 * scale, 0.009 * scale, s((0, -0.002, 1.652)), (math.radians(8), 0, 0), major_segments=20, minor_segments=7, mat=m["boots"]),
        ])
    elif variant == "brute":
        # Draped hazmat cowl hood + welded visor frame + glowing slit eyes + central respirator canister
        hood_rings = [
            _asym_ring(0.0, -0.008 * scale, 1.44 * scale, 0.125 * scale, 0.110 * scale, 0.130 * scale, 16),
            _asym_ring(0.0, 0.004 * scale, 1.54 * scale, 0.118 * scale, 0.118 * scale, 0.132 * scale, 16),
            _asym_ring(0.0, 0.002 * scale, 1.64 * scale, 0.122 * scale, 0.128 * scale, 0.140 * scale, 16),
            _asym_ring(0.0, -0.006 * scale, 1.73 * scale, 0.108 * scale, 0.112 * scale, 0.126 * scale, 16),
            _asym_ring(0.0, -0.012 * scale, 1.79 * scale, 0.064 * scale, 0.068 * scale, 0.076 * scale, 16),
        ]
        parts.extend([
            C.add_ring_loft("HazmatHood", hood_rings, mat=m["hazmat_cloth"], smooth_angle=60.0),
            C.add_box("MaskFaceplate", s((0.165, 0.095, 0.145)), s((0, 0.088, 1.592)), mat=m["gasmask_rubber"], bevel=0.016 * scale),
            C.add_box("VisorBezel", s((0.156, 0.044, 0.068)), s((0, 0.122, 1.622)), mat=m["armor_plate"], bevel=0.008 * scale),
            C.add_box("VisorNoseBridge", s((0.024, 0.048, 0.056)), s((0, 0.130, 1.616)), mat=m["armor_plate"], bevel=0.004 * scale),
            C.add_box("VisorLensL", s((0.054, 0.022, 0.038)), s((-0.042, 0.134, 1.622)), mat=m["eye_socket"], bevel=0.003 * scale),
            C.add_box("VisorLensR", s((0.054, 0.022, 0.038)), s((0.042, 0.134, 1.622)), mat=m["eye_socket"], bevel=0.003 * scale),
            C.add_sphere("VisorGlowL", 0.014 * scale, (1.2, 0.7, 0.8), s((-0.042, 0.144, 1.622)), mat=eye_mat),
            C.add_sphere("VisorGlowR", 0.014 * scale, (1.2, 0.7, 0.8), s((0.042, 0.144, 1.622)), mat=eye_mat),
            C.add_cyl("RespCanister", 0.040 * scale, 0.068 * scale, s((0, 0.154, 1.535)), (math.radians(98), 0, 0), vertices=16, mat=m["armor_plate"], bevel=0.004 * scale),
            C.add_cyl("RespGrille", 0.030 * scale, 0.014 * scale, s((0, 0.186, 1.530)), (math.radians(98), 0, 0), vertices=14, mat=m["gasmask_rubber"], bevel=0.002 * scale),
            C.add_cyl("SideValveL", 0.026 * scale, 0.042 * scale, s((-0.062, 0.128, 1.542)), (math.radians(82), 0, math.radians(-30)), vertices=12, mat=m["gasmask_rubber"], bevel=0.002 * scale),
            C.add_cyl("SideValveR", 0.026 * scale, 0.042 * scale, s((0.062, 0.128, 1.542)), (math.radians(82), 0, math.radians(30)), vertices=12, mat=m["gasmask_rubber"], bevel=0.002 * scale),
        ])
    return C.join_objects(parts, "HeadMesh", apply_uv=False)


def _build_arm_mesh(side, sx, variant, m, scale):
    coat_mat = m["uniform"] if variant == "soldier" else (m["lab_coat"] if variant == "scientist" else m["hazmat_cloth"])
    fore_mat = m["hazmat_cloth"] if variant == "brute" else m["flesh"]
    hand_mat = m["boots"] if variant == "brute" else m["flesh"]
    arm_w = 1.24 if variant == "brute" else 1.12

    def s(v):
        return tuple(c * scale for c in v)

    # Continuous sleeve loft from inside shoulder into elbow & forearm cuff
    sleeve_rings = [
        _asym_ring(sx * 0.165 * scale, 0.0, 1.375 * scale, 0.056 * scale * arm_w, 0.054 * scale * arm_w, 0.056 * scale * arm_w, 12),
        _asym_ring(sx * 0.215 * scale, 0.0, 1.355 * scale, 0.055 * scale * arm_w, 0.052 * scale * arm_w, 0.054 * scale * arm_w, 12),
        _asym_ring(sx * 0.232 * scale, 0.0, 1.225 * scale, 0.048 * scale * arm_w, 0.048 * scale * arm_w, 0.048 * scale * arm_w, 12),
        _asym_ring(sx * 0.242 * scale, 0.010 * scale, 1.065 * scale, 0.043 * scale * arm_w, 0.044 * scale * arm_w, 0.044 * scale * arm_w, 12),
        _asym_ring(sx * 0.248 * scale, 0.024 * scale, 0.960 * scale, 0.045 * scale * arm_w, 0.045 * scale * arm_w, 0.045 * scale * arm_w, 12, z_ripple=0.008 * scale),
    ]
    parts = [C.add_ring_loft(f"Sleeve_{side}", sleeve_rings, mat=coat_mat, smooth_angle=60.0)]

    # Exposed rotted lower forearm (or armored hazmat gauntlet on brute)
    fore_rings = [
        _asym_ring(sx * 0.246 * scale, 0.022 * scale, 0.985 * scale, 0.036 * scale * arm_w, 0.036 * scale * arm_w, 0.036 * scale * arm_w, 12),
        _asym_ring(sx * 0.252 * scale, 0.034 * scale, 0.880 * scale, 0.034 * scale * arm_w, 0.035 * scale * arm_w, 0.034 * scale * arm_w, 12),
        _asym_ring(sx * 0.256 * scale, 0.042 * scale, 0.785 * scale, 0.026 * scale * arm_w, 0.028 * scale * arm_w, 0.026 * scale * arm_w, 12),
    ]
    parts.append(C.add_ring_loft(f"ForearmSkin_{side}", fore_rings, mat=fore_mat, smooth_angle=60.0))

    if variant == "brute":
        # Rounded contoured steel shoulder pauldron + braced gauntlet vambrace
        parts.extend([
            C.add_sphere(f"PauldronCap_{side}", 0.084 * scale, (0.78, 1.04, 1.02), s((sx * 0.228, 0.0, 1.380)), (0, math.radians(sx * 22), 0), segments=14, rings=10, mat=m["armor_plate"]),
            C.add_box(f"GauntletPlate_{side}", s((0.068, 0.072, 0.165)), s((sx * 0.258, 0.036, 0.875)), mat=m["boots"], bevel=0.010 * scale),
        ])
    elif variant == "scientist" and side == "R":
        parts.append(C.add_box("BloodPatchR", s((0.056, 0.062, 0.12)), s((sx * 0.238, 0.022, 1.15)), mat=m["blood"], bevel=0.008 * scale))

    # Sculpted palm + thumb + 4 jagged claw fingers
    parts.append(C.add_box(f"Palm_{side}", s((0.038 * arm_w, 0.064 * arm_w, 0.072 * arm_w)), s((sx * 0.258, 0.044, 0.742)), mat=hand_mat, bevel=0.009 * scale))
    thumb_pts = [s((sx * 0.242, 0.055, 0.750)), s((sx * 0.222, 0.076, 0.722)), s((sx * 0.225, 0.074, 0.692))]
    parts.append(C.add_tube_pipe(f"Thumb_{side}", thumb_pts, segments=6, radii=[0.010 * scale, 0.008 * scale, 0.005 * scale], mat=m["blood"] if variant != "brute" else m["boots"]))
    for fi, fy in enumerate((0.022, 0.038, 0.054, 0.068)):
        f_pts = [
            s((sx * 0.258, fy, 0.710)),
            s((sx * 0.254, fy + 0.008, 0.678)),
            s((sx * 0.242, fy + 0.006, 0.654)),
        ]
        fmat = m["blood"] if (variant != "brute" and fi % 2 == 0) else hand_mat
        parts.append(C.add_tube_pipe(f"Finger_{side}_{fi}", f_pts, segments=6, radii=[0.0085 * scale, 0.007 * scale, 0.0045 * scale], mat=fmat))

    return C.join_objects(parts, f"ArmMesh_{side}", apply_uv=False)


def _build_leg_mesh(side, sx, variant, m, scale):
    leg_mat = m["hazmat_cloth"] if variant == "brute" else m["pants"]
    lw = 1.22 if variant == "brute" else 1.10

    def s(v):
        return tuple(c * scale for c in v)

    # Trouser leg from pelvis seat down to calf boot top
    pant_rings = [
        _asym_ring(sx * 0.105 * scale, 0.0, 0.945 * scale, 0.088 * scale * lw, 0.084 * scale * lw, 0.088 * scale * lw, 14),
        _asym_ring(sx * 0.106 * scale, 0.004 * scale, 0.720 * scale, 0.078 * scale * lw, 0.078 * scale * lw, 0.080 * scale * lw, 14),
        _asym_ring(sx * 0.108 * scale, 0.008 * scale, 0.500 * scale, 0.060 * scale * lw, 0.062 * scale * lw, 0.058 * scale * lw, 14),
        _asym_ring(sx * 0.108 * scale, 0.0, 0.420 * scale, 0.058 * scale * lw, 0.058 * scale * lw, 0.064 * scale * lw, 14),
        _asym_ring(sx * 0.108 * scale, -0.004 * scale, 0.295 * scale, 0.056 * scale * lw, 0.054 * scale * lw, 0.064 * scale * lw, 14, z_ripple=0.006 * scale),
    ]
    parts = [C.add_ring_loft(f"Trouser_{side}", pant_rings, mat=leg_mat, smooth_angle=58.0)]

    # Rugged jackboot shaft, sculpted foot vamp & lugged sole resting flat at z = 0.0
    boot_rings = [
        _asym_ring(sx * 0.108 * scale, -0.004 * scale, 0.305 * scale, 0.053 * scale * lw, 0.052 * scale * lw, 0.058 * scale * lw, 14),
        _asym_ring(sx * 0.108 * scale, -0.004 * scale, 0.155 * scale, 0.048 * scale * lw, 0.048 * scale * lw, 0.052 * scale * lw, 14),
        _asym_ring(sx * 0.108 * scale, 0.010 * scale, 0.075 * scale, 0.049 * scale * lw, 0.062 * scale * lw, 0.054 * scale * lw, 14),
    ]
    parts.extend([
        C.add_ring_loft(f"BootShaft_{side}", boot_rings, mat=m["boots"], smooth_angle=55.0),
        C.add_box(f"BootFoot_{side}", s((0.098 * lw, 0.215 * lw, 0.065)), s((sx * 0.108, 0.045, 0.040)), mat=m["boots"], bevel=0.016 * scale),
        C.add_box(f"BootSole_{side}", s((0.104 * lw, 0.228 * lw, 0.022)), s((sx * 0.108, 0.045, 0.011)), mat=m["eye_socket"], bevel=0.004 * scale),
    ])

    if variant == "brute":
        parts.append(C.add_box(f"KneePad_{side}", s((0.115, 0.055, 0.125)), s((sx * 0.108, 0.068, 0.470)), mat=m["armor_plate"], bevel=0.016 * scale))
    elif variant == "scientist" and side == "L":
        parts.append(C.add_box("KneeTearL", s((0.068, 0.026, 0.095)), s((sx * 0.108, 0.062, 0.620)), mat=m["flesh_dark"], bevel=0.006 * scale))

    return C.join_objects(parts, f"LegMesh_{side}", apply_uv=False)


def build_zombie_variant(variant):
    C.reset_scene()
    m = char_mats()
    scale = 1.25 if variant == "brute" else 1.0
    arm = create_humanoid_rig(f"Zombie_{variant}", scale=scale)

    coat_mat = m["uniform"] if variant == "soldier" else (m["lab_coat"] if variant == "scientist" else m["hazmat_cloth"])
    pants_mat = m["hazmat_cloth"] if variant == "brute" else m["pants"]
    eye_mat = m["eye_red"] if variant == "brute" else m["eye_amber"]
    bm_w = 1.15 if variant == "brute" else 1.0

    def s(v):
        return tuple(c * scale for c in v)

    # 1. Contiguous Pelvic + Torso + Collar Mesh
    pelvis_rings = [
        _asym_ring(0.0, 0.0, 0.85 * scale, 0.155 * scale * bm_w, 0.096 * scale * bm_w, 0.104 * scale * bm_w, 16),
        _asym_ring(0.0, 0.0, 0.96 * scale, 0.168 * scale * bm_w, 0.104 * scale * bm_w, 0.108 * scale * bm_w, 16),
        _asym_ring(0.0, 0.0, 1.06 * scale, 0.160 * scale * bm_w, 0.102 * scale * bm_w, 0.102 * scale * bm_w, 16),
    ]
    torso_parts = [C.add_ring_loft("PelvisUnder", pelvis_rings, mat=pants_mat, smooth_angle=60.0)]

    if variant == "soldier":
        coat_rings = [
            _asym_ring(0.0, 0.002 * scale, 0.84 * scale, 0.188 * scale, 0.114 * scale, 0.122 * scale, 18, z_ripple=0.018 * scale),
            _asym_ring(0.0, 0.002 * scale, 0.98 * scale, 0.172 * scale, 0.108 * scale, 0.110 * scale, 18),
            _asym_ring(0.0, 0.004 * scale, 1.14 * scale, 0.184 * scale, 0.118 * scale, 0.112 * scale, 18),
            _asym_ring(0.0, 0.006 * scale, 1.32 * scale, 0.214 * scale, 0.130 * scale, 0.116 * scale, 18),
            _asym_ring(0.0, 0.002 * scale, 1.41 * scale, 0.140 * scale, 0.088 * scale, 0.090 * scale, 18),
            _asym_ring(0.0, 0.0, 1.46 * scale, 0.062 * scale, 0.060 * scale, 0.066 * scale, 18),
        ]
        torso_parts.extend([
            C.add_ring_loft("SoldierTunic", coat_rings, mat=coat_mat, smooth_angle=58.0),
            # Folded lapels & neck collar
            C.add_box("CollarL", s((0.065, 0.055, 0.048)), s((-0.042, 0.058, 1.42)), (math.radians(15), math.radians(-18), math.radians(-12)), mat=coat_mat, bevel=0.006 * scale),
            C.add_box("CollarR", s((0.065, 0.055, 0.048)), s((0.042, 0.058, 1.42)), (math.radians(15), math.radians(18), math.radians(12)), mat=coat_mat, bevel=0.006 * scale),
            # Exposed rotten chest cavity & 3 pale sculpted rib bones
            C.add_box("ChestWoundPit", s((0.125, 0.040, 0.155)), s((-0.072, 0.114, 1.25)), (0, math.radians(14), math.radians(-8)), mat=m["flesh_dark"], bevel=0.008 * scale),
            # Field waist belt + silver buckle + dual triple-cell ammo pouches + Y-straps
            C.add_box("WaistBelt", s((0.365, 0.232, 0.054)), s((0, 0.004, 1.03)), mat=m["boots"], bevel=0.006 * scale),
            C.add_box("BeltBuckle", s((0.064, 0.022, 0.058)), s((0, 0.120, 1.03)), mat=m["chrome"], bevel=0.004 * scale),
            C.add_box("AmmoPouchL", s((0.115, 0.065, 0.095)), s((-0.105, 0.128, 1.045)), mat=m["boots"], bevel=0.006 * scale),
            C.add_box("AmmoPouchR", s((0.115, 0.065, 0.095)), s((0.105, 0.128, 1.045)), mat=m["boots"], bevel=0.006 * scale),
            C.add_box("YStrapL", s((0.036, 0.258, 0.36)), s((-0.088, 0.004, 1.24)), mat=m["boots"], bevel=0.003 * scale),
            C.add_box("YStrapR", s((0.036, 0.258, 0.36)), s((0.088, 0.004, 1.24)), mat=m["boots"], bevel=0.003 * scale),
            C.add_cyl("CanteenBack", 0.058 * scale, 0.16 * scale, s((0.11, -0.145, 0.99)), (0, 0, 0), vertices=12, mat=m["helmet_steel"], bevel=0.006 * scale),
        ])
        for ri in range(3):
            rz = 1.205 + ri * 0.044
            torso_parts.append(C.add_tube_pipe(
                f"RibBone_{ri}",
                [s((-0.122, 0.098, rz)), s((-0.072, 0.128, rz + 0.006)), s((-0.024, 0.122, rz - 0.004))],
                radius=0.009 * scale, segments=7, mat=m["bone_rib"],
            ))
    elif variant == "scientist":
        jumpsuit_rings = [
            _asym_ring(0.0, 0.004 * scale, 0.96 * scale, 0.165 * scale, 0.102 * scale, 0.106 * scale, 16),
            _asym_ring(0.0, 0.006 * scale, 1.18 * scale, 0.175 * scale, 0.116 * scale, 0.110 * scale, 16),
            _asym_ring(0.0, 0.006 * scale, 1.35 * scale, 0.200 * scale, 0.122 * scale, 0.112 * scale, 16),
            _asym_ring(0.0, 0.0, 1.45 * scale, 0.062 * scale, 0.058 * scale, 0.064 * scale, 16),
        ]
        # Tailored draped coat back + shoulder cape + tapered open coat flaps (no boxy upper shoulder sticking out!)
        coat_shell_rings = [
            _asym_ring(0.0, -0.028 * scale, 0.74 * scale, 0.205 * scale, 0.095 * scale, 0.115 * scale, 16, z_ripple=0.022 * scale),
            _asym_ring(0.0, -0.022 * scale, 0.94 * scale, 0.192 * scale, 0.092 * scale, 0.112 * scale, 16),
            _asym_ring(0.0, -0.015 * scale, 1.16 * scale, 0.196 * scale, 0.096 * scale, 0.116 * scale, 16),
            _asym_ring(0.0, -0.008 * scale, 1.34 * scale, 0.206 * scale, 0.098 * scale, 0.118 * scale, 16),
            _asym_ring(0.0, -0.004 * scale, 1.42 * scale, 0.128 * scale, 0.072 * scale, 0.088 * scale, 16),
        ]
        torso_parts.extend([
            C.add_ring_loft("ScientistJumpsuit", jumpsuit_rings, mat=m["shirt_dark"], smooth_angle=58.0),
            C.add_ring_loft("LabCoatDrape", coat_shell_rings, mat=coat_mat, smooth_angle=60.0),
            C.add_box("CoatPanelL", s((0.118, 0.055, 0.54)), s((-0.118, 0.086, 1.00)), (0, math.radians(-6), math.radians(-12)), mat=coat_mat, bevel=0.014 * scale),
            C.add_box("CoatPanelR", s((0.118, 0.055, 0.54)), s((0.118, 0.086, 1.00)), (0, math.radians(6), math.radians(12)), mat=coat_mat, bevel=0.014 * scale),
            C.add_box("CoatLapelL", s((0.068, 0.042, 0.20)), s((-0.096, 0.092, 1.32)), (0, math.radians(24), math.radians(-16)), mat=coat_mat, bevel=0.008 * scale),
            C.add_box("CoatLapelR", s((0.068, 0.042, 0.20)), s((0.096, 0.092, 1.32)), (0, math.radians(-24), math.radians(16)), mat=coat_mat, bevel=0.008 * scale),
            C.add_box("BloodLapelL", s((0.078, 0.030, 0.24)), s((-0.105, 0.106, 1.16)), (0, math.radians(-12), 0), mat=m["blood"], bevel=0.006 * scale),
            C.add_box("ChestBloodWound", s((0.105, 0.032, 0.15)), s((0.01, 0.116, 1.23)), mat=m["flesh_dark"], bevel=0.006 * scale),
            C.add_box("CoatPocket", s((0.068, 0.016, 0.075)), s((0.120, 0.108, 1.22)), mat=coat_mat, bevel=0.003 * scale),
            C.add_cyl("PocketPen1", 0.0045 * scale, 0.052 * scale, s((0.110, 0.112, 1.265)), mat=m["chrome"]),
            C.add_cyl("PocketPen2", 0.0045 * scale, 0.052 * scale, s((0.128, 0.112, 1.265)), mat=m["eye_socket"]),
        ])
    elif variant == "brute":
        haz_rings = [
            _asym_ring(0.0, 0.0, 0.96 * scale, 0.195 * scale, 0.125 * scale, 0.128 * scale, 16),
            _asym_ring(0.0, 0.004 * scale, 1.18 * scale, 0.215 * scale, 0.138 * scale, 0.132 * scale, 16),
            _asym_ring(0.0, 0.004 * scale, 1.38 * scale, 0.245 * scale, 0.145 * scale, 0.138 * scale, 16),
            _asym_ring(0.0, 0.0, 1.46 * scale, 0.095 * scale, 0.085 * scale, 0.095 * scale, 16),
        ]
        # Contoured heavy steel cuirass breastplate + dorsal plate
        armor_rings = [
            _asym_ring(0.0, 0.012 * scale, 1.07 * scale, 0.190 * scale, 0.142 * scale, 0.132 * scale, 16),
            _asym_ring(0.0, 0.018 * scale, 1.22 * scale, 0.228 * scale, 0.162 * scale, 0.142 * scale, 16),
            _asym_ring(0.0, 0.012 * scale, 1.36 * scale, 0.238 * scale, 0.156 * scale, 0.144 * scale, 16),
            _asym_ring(0.0, 0.006 * scale, 1.42 * scale, 0.145 * scale, 0.102 * scale, 0.108 * scale, 16),
        ]
        torso_parts.extend([
            C.add_ring_loft("HazmatCore", haz_rings, mat=coat_mat, smooth_angle=60.0),
            C.add_ring_loft("CuirassArmor", armor_rings, mat=m["armor_plate"], smooth_angle=44.0),
            # Codpiece/groin plate + tactical pouches + chest hazard scar
            C.add_box("GroinArmor", s((0.18, 0.14, 0.20)), s((0, 0.075, 0.94)), mat=m["armor_plate"], bevel=0.014 * scale),
            C.add_box("BattleGashChest", s((0.20, 0.032, 0.038)), s((0.02, 0.168, 1.25)), (0, math.radians(-28), 0), mat=m["flesh_dark"], bevel=0.004 * scale),
            C.add_box("HazardBelt", s((0.44, 0.30, 0.055)), s((0, 0.010, 1.05)), mat=m["hazard_yellow"], bevel=0.006 * scale),
            C.add_box("HipPouchL", s((0.13, 0.10, 0.13)), s((-0.18, 0.11, 1.01)), mat=coat_mat, bevel=0.010 * scale),
            C.add_box("HipPouchR", s((0.13, 0.10, 0.13)), s((0.18, 0.11, 1.01)), mat=coat_mat, bevel=0.010 * scale),
            # Dual O2 / Coolant cylinders strapped onto spine + regulator manifold + breathing hoses looping over shoulders!
            C.add_cyl("BackTankL", 0.068 * scale, 0.39 * scale, s((-0.095, -0.185, 1.24)), vertices=16, mat=m["tank_metal"], bevel=0.008 * scale),
            C.add_cyl("BackTankR", 0.068 * scale, 0.39 * scale, s((0.095, -0.185, 1.24)), vertices=16, mat=m["tank_metal"], bevel=0.008 * scale),
            C.add_cyl("TankValveL", 0.024 * scale, 0.06 * scale, s((-0.095, -0.185, 1.45)), vertices=10, mat=m["brass"], bevel=0.002 * scale),
            C.add_cyl("TankValveR", 0.024 * scale, 0.06 * scale, s((0.095, -0.185, 1.45)), vertices=10, mat=m["brass"], bevel=0.002 * scale),
            C.add_box("BackManifold", s((0.28, 0.075, 0.065)), s((0, -0.175, 1.24)), mat=m["armor_plate"], bevel=0.008 * scale),
        ])
        for sx in (-1, 1):
            torso_parts.append(C.add_tube_pipe(
                f"AirHose_{sx}",
                [
                    s((sx * 0.095, -0.175, 1.44)),
                    s((sx * 0.122, -0.095, 1.445)),
                    s((sx * 0.118, 0.020, 1.430)),
                    s((sx * 0.088, 0.110, 1.405)),
                    s((sx * 0.056, 0.138, 1.485)),
                ],
                radius=0.015 * scale, segments=10, mat=m["gasmask_rubber"],
            ))

    torso_mesh = C.join_objects(torso_parts, "TorsoPelvisMesh", apply_uv=False)

    def torso_weights(x, y, z):
        # Smooth waist transition between Pelvis (z<0.95) and Spine (z>1.08), plus smooth neck collar to Head
        if z >= 1.41:
            t_h = max(0.0, min(1.0, (z - 1.41) / 0.07))
            return {"Spine": 1.0 - t_h, "Head": t_h}
        if z <= 0.94:
            if variant == "scientist" and abs(x) > 0.07:
                return {"Pelvis": 0.78, f"Thigh_{'L' if x < 0 else 'R'}": 0.22}
            return {"Pelvis": 1.0}
        if z >= 1.08:
            return {"Spine": 1.0}
        t = (z - 0.94) / 0.14
        return {"Pelvis": 1.0 - t, "Spine": t}

    bind_skinned_mesh(torso_mesh, arm, ["Pelvis", "Spine", "Head", "Thigh_L", "Thigh_R"], torso_weights, scale=scale, uv_scale=2.2)

    # 2. Head Mesh (bound solidly to Head, overlaps neck cleanly at z=1.43..1.50)
    head_mesh = _build_zombie_head(m, scale, eye_mat, variant)
    bind_skinned_mesh(head_mesh, arm, ["Head", "Spine"], lambda x, y, z: {"Head": 1.0}, scale=scale, uv_scale=2.5)

    # 3. Left & Right Contoured Arms (Shoulder blend + Elbow blend -> Wrist/Claws)
    for side, sx in (("L", -1), ("R", 1)):
        arm_mesh = _build_arm_mesh(side, sx, variant, m, scale)

        def make_arm_w(s_side, s_x):
            def w_fn(x, y, z):
                # Feather inner shoulder deltoid into Spine so chest moves smoothly with raised arm
                sh_dist = abs(x) - 0.175
                w_spine = max(0.0, min(0.55, (0.215 - abs(x)) / 0.055)) if z > 1.28 else 0.0
                # Smooth elbow blend across z = 1.06 +/- 0.055
                t_el = max(0.0, min(1.0, (1.115 - z) / 0.11))
                w_arm = (1.0 - w_spine) * (1.0 - t_el)
                w_fore = (1.0 - w_spine) * t_el
                return {"Spine": w_spine, f"Arm_{s_side}": w_arm, f"Forearm_{s_side}": w_fore}
            return w_fn

        bind_skinned_mesh(arm_mesh, arm, ["Spine", f"Arm_{side}", f"Forearm_{side}"], make_arm_w(side, sx), scale=scale, uv_scale=2.4)

    # 4. Left & Right Contoured Legs (Hip Pelvis blend + Knee blend -> Lugged Jackboots)
    for side, sx in (("L", -1), ("R", 1)):
        leg_mesh = _build_leg_mesh(side, sx, variant, m, scale)

        def make_leg_w(s_side):
            def w_fn(x, y, z):
                # Hip blend above z = 0.87 so trousers tuck seamlessly into Pelvis
                w_pelvis = max(0.0, min(0.85, (z - 0.87) / 0.08))
                # Knee blend across z = 0.46 +/- 0.055
                t_kn = max(0.0, min(1.0, (0.515 - z) / 0.11))
                w_thigh = (1.0 - w_pelvis) * (1.0 - t_kn)
                w_shin = (1.0 - w_pelvis) * t_kn
                return {"Pelvis": w_pelvis, f"Thigh_{s_side}": w_thigh, f"Shin_{s_side}": w_shin}
            return w_fn

        bind_skinned_mesh(leg_mesh, arm, ["Pelvis", f"Thigh_{side}", f"Shin_{side}"], make_leg_w(side), scale=scale, uv_scale=2.2)

    add_humanoid_animations(arm, scale=scale)
    C.export_asset("characters", f"zombie_{variant}", export_anims=True)


# ---------------------------------------------------------------------------
# High-Detail Exposed-Rib Molten Hellhound
# ---------------------------------------------------------------------------

def build_hellhound():
    C.reset_scene()
    m = char_mats()

    arm_data = bpy.data.armatures.new("Hellhound_ArmData")
    arm = bpy.data.objects.new("Hellhound_Armature", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")

    def b(n, h, t, p=None):
        eb = arm_data.edit_bones.new(n)
        eb.head = h
        eb.tail = t
        if p:
            eb.parent = arm_data.edit_bones[p]

    b("Body", (0, -0.15, 0.56), (0, 0.28, 0.60))
    b("Head", (0, 0.30, 0.62), (0, 0.58, 0.66), "Body")
    b("Leg_FL", (-0.135, 0.22, 0.52), (-0.135, 0.22, 0.04), "Body")
    b("Leg_FR", (0.135, 0.22, 0.52), (0.135, 0.22, 0.04), "Body")
    b("Leg_BL", (-0.135, -0.24, 0.52), (-0.135, -0.24, 0.04), "Body")
    b("Leg_BR", (0.135, -0.24, 0.52), (0.135, -0.24, 0.04), "Body")
    bpy.ops.object.mode_set(mode="OBJECT")

    # 1. Sculpted Volcanic Body Loft + Inner Glowing Magma Furnace + 5 Pair Curved 3D Skeletal Ribs
    body_rings = [
        [(math.cos(a) * 0.085, -0.36, 0.55 + math.sin(a) * 0.095) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
        [(math.cos(a) * 0.115, -0.24, 0.54 + math.sin(a) * 0.125) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
        [(math.cos(a) * 0.105, -0.10, 0.51 + math.sin(a) * 0.115) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
        [(math.cos(a) * 0.135, 0.05, 0.54 + math.sin(a) * 0.145) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
        [(math.cos(a) * 0.155, 0.20, 0.58 + math.sin(a) * 0.165) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
        [(math.cos(a) * 0.110, 0.34, 0.62 + math.sin(a) * 0.115) for a in [(k / 16) * 2.0 * math.pi for k in range(16)]],
    ]
    core_rings = [
        [(math.cos(a) * 0.102, -0.14, 0.52 + math.sin(a) * 0.108) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
        [(math.cos(a) * 0.140, 0.03, 0.54 + math.sin(a) * 0.135) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
        [(math.cos(a) * 0.144, 0.15, 0.57 + math.sin(a) * 0.145) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
    ]
    body_parts = [
        C.add_ring_loft("HoundBodyShell", body_rings, mat=m["hound_char"], smooth_angle=58.0),
        C.add_ring_loft("MagmaCoreChest", core_rings, mat=m["magma"], smooth_angle=60.0),
        # Shoulder humps & pelvic musculature
        C.add_sphere("ShoulderHumpL", 0.095, (0.8, 1.35, 1.25), (-0.11, 0.22, 0.60), mat=m["hound_char"]),
        C.add_sphere("ShoulderHumpR", 0.095, (0.8, 1.35, 1.25), (0.11, 0.22, 0.60), mat=m["hound_char"]),
        C.add_sphere("HaunchL", 0.088, (0.8, 1.25, 1.18), (-0.10, -0.24, 0.54), mat=m["hound_char"]),
        C.add_sphere("HaunchR", 0.088, (0.8, 1.25, 1.18), (0.10, -0.24, 0.54), mat=m["hound_char"]),
    ]
    # 5 protruding curved skeletal ribs per flank arching OUTSIDE the glowing magma chest!
    for r_i in range(5):
        ry = 0.14 - r_i * 0.062
        arch = 0.162 - r_i * 0.008
        for sx in (-1, 1):
            rib_pts = [
                (sx * 0.035, ry, 0.67),
                (sx * arch * 0.88, ry - 0.01, 0.62),
                (sx * arch, ry - 0.02, 0.52),
                (sx * arch * 0.66, ry - 0.01, 0.41),
                (sx * 0.025, ry + 0.01, 0.39),
            ]
            body_parts.append(C.add_tube_pipe(
                f"HoundRib_{sx}_{r_i}", rib_pts, segments=7,
                radii=[0.013, 0.012, 0.011, 0.010, 0.008], mat=m["hound_bone"],
            ))
    # Jagged dorsal spine spikes from neck to tail base
    for si, (sy, sz, sl) in enumerate([(0.30, 0.72, 0.10), (0.20, 0.74, 0.13), (0.09, 0.71, 0.12), (-0.03, 0.67, 0.11), (-0.16, 0.67, 0.10), (-0.28, 0.66, 0.09)]):
        body_parts.append(C.add_cone(f"SpineSpike_{si}", 0.026, 0.002, sl, (0, sy, sz), (math.radians(-26), 0, 0), vertices=6, mat=m["hound_char"]))
    # Fiery curved segmented tail
    body_parts.append(C.add_tube_pipe(
        "MagmaTail",
        [(0, -0.34, 0.58), (0, -0.46, 0.64), (0, -0.56, 0.72), (0, -0.62, 0.80)],
        segments=7, radii=[0.028, 0.022, 0.015, 0.008], mat=m["magma"],
    ))
    bind_skinned_mesh(C.join_objects(body_parts, "HoundBody", apply_uv=False), arm, ["Body"], lambda x, y, z: {"Body": 1.0}, scale=1.0, uv_scale=2.5)

    # 2. Fierce Sculpted Canine Skull facing +Y
    head_rings = [
        [(math.cos(a) * 0.088, 0.28, 0.63 + math.sin(a) * 0.092) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
        [(math.cos(a) * 0.096, 0.39, 0.65 + math.sin(a) * 0.096) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
        [(math.cos(a) * 0.068, 0.49, 0.64 + math.sin(a) * 0.068) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
        [(math.cos(a) * 0.044, 0.61, 0.61 + math.sin(a) * 0.040) for a in [(k / 14) * 2.0 * math.pi for k in range(14)]],
    ]
    head_parts = [
        C.add_ring_loft("HoundSkull", head_rings, mat=m["hound_char"], smooth_angle=55.0),
        C.add_box("HoundBrowL", (0.045, 0.075, 0.025), (-0.052, 0.465, 0.685), (math.radians(-12), 0, math.radians(-18)), mat=m["hound_char"], bevel=0.006),
        C.add_box("HoundBrowR", (0.045, 0.075, 0.025), (0.052, 0.465, 0.685), (math.radians(-12), 0, math.radians(18)), mat=m["hound_char"], bevel=0.006),
        C.add_sphere("EyeSocketL", 0.025, (1.1, 0.8, 0.9), (-0.056, 0.478, 0.665), mat=m["eye_socket"]),
        C.add_sphere("EyeSocketR", 0.025, (1.1, 0.8, 0.9), (0.056, 0.478, 0.665), mat=m["eye_socket"]),
        C.add_sphere("EyeL", 0.017, (1, 1, 1), (-0.058, 0.490, 0.665), mat=m["magma"]),
        C.add_sphere("EyeR", 0.017, (1, 1, 1), (0.058, 0.490, 0.665), mat=m["magma"]),
        C.add_cone("EarL", 0.036, 0.003, 0.16, (-0.074, 0.35, 0.78), (math.radians(-16), math.radians(-14), 0), vertices=7, mat=m["hound_char"]),
        C.add_cone("EarR", 0.036, 0.003, 0.16, (0.074, 0.35, 0.78), (math.radians(-16), math.radians(14), 0), vertices=7, mat=m["hound_char"]),
        # Open snarling molten inner maw & charred lower mandible
        C.add_box("MoltenMaw", (0.068, 0.145, 0.042), (0, 0.525, 0.585), (math.radians(-16), 0, 0), mat=m["magma"], bevel=0.006),
        C.add_box("LowerJaw", (0.082, 0.175, 0.034), (0, 0.525, 0.545), (math.radians(-22), 0, 0), mat=m["hound_char"], bevel=0.008),
    ]
    # Sharp canine fangs & glowing ember teeth
    for fx, fy, fz, rot_x, h in [
        (-0.030, 0.59, 0.595, 175, 0.042), (0.030, 0.59, 0.595, 175, 0.042),
        (-0.036, 0.53, 0.605, 175, 0.032), (0.036, 0.53, 0.605, 175, 0.032),
        (-0.024, 0.585, 0.550, 12, 0.036), (0.024, 0.585, 0.550, 12, 0.036),
    ]:
        head_parts.append(C.add_cone(f"Fang_{fx}_{fz}", 0.009, 0.001, h, (fx, fy, fz), (math.radians(rot_x), 0, 0), vertices=6, mat=m["teeth"]))
    bind_skinned_mesh(C.join_objects(head_parts, "HoundHead", apply_uv=False), arm, ["Head"], lambda x, y, z: {"Head": 1.0}, scale=1.0, uv_scale=2.8)

    # 3. Articulated Muscular Canine Legs w/ Bent Hock & 3-Claw Ember Paws
    for lname, lx, ly, is_front in (("Leg_FL", -0.135, 0.22, True), ("Leg_FR", 0.135, 0.22, True), ("Leg_BL", -0.135, -0.24, False), ("Leg_BR", 0.135, -0.24, False)):
        if is_front:
            leg_pts = [(lx, ly, 0.54), (lx, ly - 0.03, 0.36), (lx, ly - 0.04, 0.22), (lx, ly + 0.02, 0.06)]
            leg_r = [0.056, 0.042, 0.030, 0.026]
        else:
            leg_pts = [(lx, ly, 0.54), (lx, ly + 0.05, 0.36), (lx, ly - 0.07, 0.22), (lx, ly + 0.01, 0.06)]
            leg_r = [0.064, 0.046, 0.030, 0.026]
        leg_parts = [
            C.add_tube_pipe(f"{lname}_Limb", leg_pts, segments=10, radii=leg_r, mat=m["hound_char"]),
            C.add_box(f"{lname}_Paw", (0.068, 0.095, 0.038), (lx, ly + 0.035, 0.026), mat=m["hound_char"], bevel=0.010),
        ]
        for ci, cx_off in enumerate((-0.022, 0.0, 0.022)):
            leg_parts.append(C.add_cone(
                f"{lname}_Claw_{ci}", 0.009, 0.001, 0.050,
                (lx + cx_off, ly + 0.092, 0.022), (math.radians(82), 0, 0), vertices=6, mat=m["magma"],
            ))
        leg = C.join_objects(leg_parts, f"{lname}_Part", apply_uv=False)
        bind_skinned_mesh(leg, arm, [lname], lambda x, y, z, b=lname: {b: 1.0}, scale=1.0, uv_scale=2.8)

    # Quadruped animations
    arm.animation_data_create()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"

    def h_act(name, frames):
        act = bpy.data.actions.new(name=name)
        act.use_fake_user = True
        arm.animation_data.action = act
        for f, poses in frames.items():
            for pb in arm.pose.bones:
                pb.rotation_euler = (0, 0, 0)
                pb.location = (0, 0, 0)
            for bn, v in poses.items():
                pb = arm.pose.bones[bn]
                if "rot" in v:
                    pb.rotation_euler = tuple(math.radians(a) for a in v["rot"])
                if "loc" in v:
                    pb.location = v["loc"]
            for pb in arm.pose.bones:
                pb.keyframe_insert(data_path="rotation_euler", frame=f)
                pb.keyframe_insert(data_path="location", frame=f)
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        st = tr.strips.new(name, 1, act)
        st.action_frame_start = 1
        st.action_frame_end = max(frames.keys())
        arm.animation_data.action = None

    h_act("Run", {
        1: {"Body": {"rot": (8, 0, 0), "loc": (0, 0, 0.04)}, "Leg_FL": {"rot": (-42, 0, 0)}, "Leg_FR": {"rot": (-35, 0, 0)}, "Leg_BL": {"rot": (42, 0, 0)}, "Leg_BR": {"rot": (35, 0, 0)}},
        8: {"Body": {"rot": (-8, 0, 0), "loc": (0, 0, -0.04)}, "Leg_FL": {"rot": (38, 0, 0)}, "Leg_FR": {"rot": (42, 0, 0)}, "Leg_BL": {"rot": (-38, 0, 0)}, "Leg_BR": {"rot": (-42, 0, 0)}},
        15: {"Body": {"rot": (8, 0, 0), "loc": (0, 0, 0.04)}, "Leg_FL": {"rot": (-42, 0, 0)}, "Leg_FR": {"rot": (-35, 0, 0)}, "Leg_BL": {"rot": (42, 0, 0)}, "Leg_BR": {"rot": (35, 0, 0)}},
    })
    h_act("Attack", {
        1: {"Body": {"rot": (-18, 0, 0), "loc": (0, 0, 0.15)}, "Head": {"rot": (-10, 0, 0)}, "Leg_FL": {"rot": (-55, 0, 0)}, "Leg_FR": {"rot": (-55, 0, 0)}},
        9: {"Body": {"rot": (16, 0, 0), "loc": (0, 0.12, 0.05)}, "Head": {"rot": (15, 0, 0)}, "Leg_FL": {"rot": (20, 0, 0)}, "Leg_FR": {"rot": (20, 0, 0)}},
        17: {"Body": {"rot": (0, 0, 0)}},
    })
    h_act("Death", {
        1: {"Body": {"rot": (0, 0, 0)}},
        15: {"Body": {"rot": (0, 88, 0), "loc": (0, 0, -0.35)}},
    })
    bpy.ops.object.mode_set(mode="OBJECT")
    C.export_asset("characters", "hellhound", export_anims=True)


if __name__ == "__main__":
    build_zombie_variant("soldier")
    build_zombie_variant("scientist")
    build_zombie_variant("brute")
    build_hellhound()
    print("ALL 4 RIGGED & ANIMATED CHARACTER MODELS EXPORTED!")
