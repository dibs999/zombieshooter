"""Generate rigged and animated Blender characters (.blend + .glb):
- zombie_soldier (Wehrmacht helmet + tattered bloodied uniform + glowing amber eyes)
- zombie_scientist (Torn bloodied lab coat + decayed flesh + glowing amber eyes)
- zombie_brute (Armored hazmat juggernaut + steel chestplate + glowing orange visor)
- hellhound (Demonic magma-ribbed hound + glowing embers & eyes)

Blender convention: +Y = Forward (Godot -Z), +Z = Up (Godot +Y).
"""

import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def char_mats():
    cloth_tex = os.path.join(C.TEX_DIR, "env", "zombie_cloth_albedo.png")
    cloth_nrm = os.path.join(C.TEX_DIR, "env", "zombie_cloth_normal.png")
    cloth_rgh = os.path.join(C.TEX_DIR, "env", "zombie_cloth_roughness.png")

    flesh = C.make_pbr_mat("DecayedFlesh", (0.28, 0.32, 0.24, 1.0), roughness=0.78)
    flesh_dark = C.make_pbr_mat("RottedMuscle", (0.19, 0.08, 0.07, 1.0), roughness=0.62)
    blood = C.make_pbr_mat("DriedBlood", (0.22, 0.02, 0.02, 1.0), roughness=0.42)
    uniform = C.make_pbr_mat("TatteredUniform", (0.18, 0.20, 0.15, 1.0), roughness=0.88, albedo_tex=cloth_tex, normal_tex=cloth_nrm, roughness_tex=cloth_rgh)
    pants = C.make_pbr_mat("TatteredPants", (0.12, 0.13, 0.11, 1.0), roughness=0.90)
    lab_coat = C.make_pbr_mat("BloodiedLabCoat", (0.50, 0.49, 0.44, 1.0), roughness=0.84)
    shirt_dark = C.make_pbr_mat("ScientistShirt", (0.14, 0.16, 0.18, 1.0), roughness=0.82)
    helmet_steel = C.make_pbr_mat("HelmetSteel", (0.15, 0.17, 0.15, 1.0), metallic=0.65, roughness=0.52)
    armor_plate = C.make_pbr_mat("BruteArmor", (0.16, 0.17, 0.19, 1.0), metallic=0.78, roughness=0.42)
    hazard_yellow = C.make_pbr_mat("BruteStripe", (0.72, 0.52, 0.08, 1.0), metallic=0.15, roughness=0.58)
    hazmat_cloth = C.make_pbr_mat("HazmatCloth", (0.24, 0.22, 0.12, 1.0), roughness=0.86)
    boots = C.make_pbr_mat("LeatherBoots", (0.08, 0.06, 0.05, 1.0), roughness=0.65)
    teeth = C.make_pbr_mat("GrimTeeth", (0.62, 0.58, 0.46, 1.0), roughness=0.48)
    eye_socket = C.make_pbr_mat("EyeSocket", (0.04, 0.03, 0.03, 1.0), roughness=0.90)
    eye_amber = C.make_pbr_mat("ZombieEyeAmber", (1.0, 0.48, 0.04, 1.0), roughness=0.12, emission=(1.0, 0.44, 0.03), emission_strength=3.6)
    eye_red = C.make_pbr_mat("BruteEyeOrange", (1.0, 0.28, 0.02, 1.0), roughness=0.12, emission=(1.0, 0.26, 0.02), emission_strength=4.0)
    hound_char = C.make_pbr_mat("HoundCharcoal", (0.14, 0.11, 0.10, 1.0), roughness=0.72)
    magma = C.make_pbr_mat("HoundMagma", (1.0, 0.34, 0.03, 1.0), roughness=0.22, emission=(1.0, 0.30, 0.02), emission_strength=2.5)
    return locals()


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

    add_bone("Arm_L", (-0.23, 0, 1.38), (-0.25, 0, 1.06), "Spine")
    add_bone("Forearm_L", (-0.25, 0, 1.06), (-0.26, 0.04, 0.78), "Arm_L")
    add_bone("Arm_R", (0.23, 0, 1.38), (0.25, 0, 1.06), "Spine")
    add_bone("Forearm_R", (0.25, 0, 1.06), (0.26, 0.04, 0.78), "Arm_R")

    add_bone("Thigh_L", (-0.11, 0, 0.90), (-0.11, 0, 0.46), "Pelvis")
    add_bone("Shin_L", (-0.11, 0, 0.46), (-0.11, 0, 0.04), "Thigh_L")
    add_bone("Thigh_R", (0.11, 0, 0.90), (0.11, 0, 0.46), "Pelvis")
    add_bone("Shin_R", (0.11, 0, 0.46), (0.11, 0, 0.04), "Thigh_R")

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bind_part_to_bone(mesh_obj, arm_obj, bone_name):
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    for mod in list(mesh_obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vg = mesh_obj.vertex_groups.new(name=bone_name)
    vg.add([v.index for v in mesh_obj.data.vertices], 1.0, "REPLACE")
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

    # 1. Idle (1..49) - hunched head, arms hung forward
    make_action("Idle", {
        1: {"Spine": {"rot": (-8, -3, 0)}, "Head": {"rot": (-8, 0, -6)}, "Arm_L": {"rot": (34, 0, -5)}, "Forearm_L": {"rot": (22, 0, 0)}, "Arm_R": {"rot": (28, 0, 5)}, "Forearm_R": {"rot": (18, 0, 0)}},
        25: {"Spine": {"rot": (-12, 3, 2)}, "Head": {"rot": (-10, 5, 6)}, "Arm_L": {"rot": (40, 0, -8)}, "Forearm_L": {"rot": (24, 0, 0)}, "Arm_R": {"rot": (34, 0, 8)}, "Forearm_R": {"rot": (20, 0, 0)}},
        49: {"Spine": {"rot": (-8, -3, 0)}, "Head": {"rot": (-8, 0, -6)}, "Arm_L": {"rot": (34, 0, -5)}, "Forearm_L": {"rot": (22, 0, 0)}, "Arm_R": {"rot": (28, 0, 5)}, "Forearm_R": {"rot": (18, 0, 0)}},
    })

    # 2. Walk (Shambling limp, hunched torso, outstretched reaching arms! 1..33)
    make_action("Walk", {
        1: {"Pelvis": {"loc": (0, 0, -0.02), "rot": (0, -4, 4)}, "Spine": {"rot": (-16, 0, -6)}, "Head": {"rot": (10, 8, 6)},
            "Arm_L": {"rot": (74, 0, -6)}, "Forearm_L": {"rot": (20, 0, 0)},
            "Arm_R": {"rot": (84, 0, 6)}, "Forearm_R": {"rot": (24, 0, 0)},
            "Thigh_L": {"rot": (24, 0, 0)}, "Shin_L": {"rot": (-24, 0, 0)},
            "Thigh_R": {"rot": (-22, 0, 0)}, "Shin_R": {"rot": (-12, 0, 0)}},
        17: {"Pelvis": {"loc": (0, 0, 0.02), "rot": (0, 4, -4)}, "Spine": {"rot": (-18, 0, 5)}, "Head": {"rot": (8, -8, -5)},
            "Arm_L": {"rot": (86, 0, -4)}, "Forearm_L": {"rot": (22, 0, 0)},
            "Arm_R": {"rot": (72, 0, 4)}, "Forearm_R": {"rot": (18, 0, 0)},
            "Thigh_L": {"rot": (-22, 0, 0)}, "Shin_L": {"rot": (-12, 0, 0)},
            "Thigh_R": {"rot": (24, 0, 0)}, "Shin_R": {"rot": (-26, 0, 0)}},
        33: {"Pelvis": {"loc": (0, 0, -0.02), "rot": (0, -4, 4)}, "Spine": {"rot": (-16, 0, -6)}, "Head": {"rot": (10, 8, 6)},
            "Arm_L": {"rot": (74, 0, -6)}, "Forearm_L": {"rot": (20, 0, 0)},
            "Arm_R": {"rot": (84, 0, 6)}, "Forearm_R": {"rot": (24, 0, 0)},
            "Thigh_L": {"rot": (24, 0, 0)}, "Shin_L": {"rot": (-24, 0, 0)},
            "Thigh_R": {"rot": (-22, 0, 0)}, "Shin_R": {"rot": (-12, 0, 0)}},
    })

    # 3. Run (Aggressive Sprinter! 1..19)
    make_action("Run", {
        1: {"Pelvis": {"loc": (0, 0, -0.04)}, "Spine": {"rot": (-26, 0, -8)}, "Head": {"rot": (16, 0, 4)},
            "Arm_L": {"rot": (92, 0, -8)}, "Forearm_L": {"rot": (30, 0, 0)},
            "Arm_R": {"rot": (76, 0, 8)}, "Forearm_R": {"rot": (35, 0, 0)},
            "Thigh_L": {"rot": (45, 0, 0)}, "Shin_L": {"rot": (-45, 0, 0)},
            "Thigh_R": {"rot": (-38, 0, 0)}, "Shin_R": {"rot": (-20, 0, 0)}},
        10: {"Pelvis": {"loc": (0, 0, 0.03)}, "Spine": {"rot": (-28, 0, 8)}, "Head": {"rot": (18, 0, -4)},
            "Arm_L": {"rot": (76, 0, -8)}, "Forearm_L": {"rot": (35, 0, 0)},
            "Arm_R": {"rot": (94, 0, 8)}, "Forearm_R": {"rot": (28, 0, 0)},
            "Thigh_L": {"rot": (-38, 0, 0)}, "Shin_L": {"rot": (-20, 0, 0)},
            "Thigh_R": {"rot": (45, 0, 0)}, "Shin_R": {"rot": (-48, 0, 0)}},
        19: {"Pelvis": {"loc": (0, 0, -0.04)}, "Spine": {"rot": (-26, 0, -8)}, "Head": {"rot": (16, 0, 4)},
            "Arm_L": {"rot": (92, 0, -8)}, "Forearm_L": {"rot": (30, 0, 0)},
            "Arm_R": {"rot": (76, 0, 8)}, "Forearm_R": {"rot": (35, 0, 0)},
            "Thigh_L": {"rot": (45, 0, 0)}, "Shin_L": {"rot": (-45, 0, 0)},
            "Thigh_R": {"rot": (-38, 0, 0)}, "Shin_R": {"rot": (-20, 0, 0)}},
    })

    # 4. Attack (Savage lunge & swipe! 1..21)
    make_action("Attack", {
        1: {"Spine": {"rot": (6, 0, 0)}, "Arm_L": {"rot": (120, 0, -18)}, "Arm_R": {"rot": (125, 0, 18)}},
        10: {"Spine": {"rot": (-28, 0, 0)}, "Head": {"rot": (12, 0, 0)}, "Arm_L": {"rot": (55, 0, 12)}, "Forearm_L": {"rot": (40, 0, 0)}, "Arm_R": {"rot": (50, 0, -12)}, "Forearm_R": {"rot": (40, 0, 0)}},
        21: {"Spine": {"rot": (-14, 0, 0)}, "Arm_L": {"rot": (82, 0, -6)}, "Arm_R": {"rot": (82, 0, 6)}},
    }, loop=False)

    # 5. Death (Collapse backward 1..25)
    make_action("Death", {
        1: {"Pelvis": {"loc": (0, 0, 0), "rot": (0, 0, 0)}, "Spine": {"rot": (-10, 0, 0)}},
        12: {"Pelvis": {"loc": (0, -0.25, -0.35), "rot": (45, 0, 6)}, "Spine": {"rot": (20, 0, 0)}, "Arm_L": {"rot": (45, 0, -35)}, "Arm_R": {"rot": (55, 0, 35)}},
        25: {"Pelvis": {"loc": (0, -0.55, -0.82), "rot": (88, 0, 12)}, "Spine": {"rot": (10, 0, 0)}, "Head": {"rot": (-15, 10, 0)}, "Arm_L": {"rot": (15, 0, -55)}, "Arm_R": {"rot": (20, 0, 50)}, "Thigh_L": {"rot": (-10, 0, -8)}, "Thigh_R": {"rot": (-12, 0, 10)}},
    }, loop=False)

    bpy.ops.object.mode_set(mode="OBJECT")


def build_zombie_variant(variant):
    C.reset_scene()
    m = char_mats()
    scale = 1.25 if variant == "brute" else 1.0
    arm = create_humanoid_rig(f"Zombie_{variant}", scale=scale)

    coat_mat = m["uniform"] if variant == "soldier" else (m["lab_coat"] if variant == "scientist" else m["hazmat_cloth"])
    eye_mat = m["eye_red"] if variant == "brute" else m["eye_amber"]

    def s(v):
        return tuple(c * scale for c in v)

    # Pelvis & waist gear
    pelvis_parts = [C.add_box("PelvisMesh", s((0.31, 0.19, 0.18)), s((0, 0, 0.91)), mat=m["pants"], bevel=0.015)]
    bind_part_to_bone(C.join_objects(pelvis_parts, "PelvisPart"), arm, "Pelvis")

    # Torso / Spine
    torso_parts = [
        C.add_box("Chest", s((0.38, 0.22, 0.38)), s((0, 0, 1.24)), mat=coat_mat, bevel=0.02),
        C.add_box("Shoulders", s((0.46, 0.20, 0.12)), s((0, 0, 1.38)), mat=coat_mat, bevel=0.02),
        C.add_box("RibWound", s((0.13, 0.04, 0.16)), s((-0.07, 0.105, 1.24)), (0, math.radians(15), 0), mat=m["flesh_dark"], bevel=0.006),
        C.add_box("NeckStump", s((0.12, 0.12, 0.10)), s((0, 0, 1.45)), mat=m["flesh"], bevel=0.01),
    ]
    if variant == "soldier":
        torso_parts.extend([
            C.add_box("AmmoBelt", s((0.40, 0.24, 0.06)), s((0, 0, 1.05)), mat=m["boots"], bevel=0.005),
            C.add_box("PouchL", s((0.10, 0.07, 0.11)), s((-0.11, 0.12, 1.06)), mat=m["boots"], bevel=0.006),
            C.add_box("PouchR", s((0.10, 0.07, 0.11)), s((0.11, 0.12, 1.06)), mat=m["boots"], bevel=0.006),
            C.add_box("ChestStrapL", s((0.05, 0.24, 0.34)), s((-0.10, 0.0, 1.25)), mat=m["boots"], bevel=0.004),
            C.add_box("ChestStrapR", s((0.05, 0.24, 0.34)), s((0.10, 0.0, 1.25)), mat=m["boots"], bevel=0.004),
        ])
    elif variant == "scientist":
        torso_parts.extend([
            C.add_box("InnerShirt", s((0.16, 0.225, 0.32)), s((0, 0.01, 1.23)), mat=m["shirt_dark"], bevel=0.005),
            C.add_box("CoatTailL", s((0.17, 0.23, 0.32)), s((-0.11, -0.01, 0.89)), mat=m["lab_coat"], bevel=0.008),
            C.add_box("CoatTailR", s((0.17, 0.23, 0.32)), s((0.11, -0.01, 0.89)), mat=m["lab_coat"], bevel=0.008),
            C.add_box("BloodLapel", s((0.16, 0.04, 0.28)), s((0.08, 0.105, 1.18)), (0, math.radians(-18), 0), mat=m["blood"], bevel=0.005),
        ])
    elif variant == "brute":
        torso_parts.extend([
            C.add_box("ChestPlate", s((0.44, 0.27, 0.36)), s((0, 0.02, 1.26)), mat=m["armor_plate"], bevel=0.018),
            C.add_box("HazardStripe", s((0.42, 0.28, 0.05)), s((0, 0.02, 1.15)), mat=m["hazard_yellow"], bevel=0.004),
            C.add_box("PauldronL", s((0.18, 0.22, 0.16)), s((-0.27, 0, 1.40)), (0, math.radians(-18), 0), mat=m["armor_plate"], bevel=0.014),
            C.add_box("PauldronR", s((0.18, 0.22, 0.16)), s((0.27, 0, 1.40)), (0, math.radians(18), 0), mat=m["armor_plate"], bevel=0.014),
            C.add_cyl("BackTankL", 0.065 * scale, 0.36 * scale, s((-0.09, -0.17, 1.24)), mat=m["helmet_steel"]),
            C.add_cyl("BackTankR", 0.065 * scale, 0.36 * scale, s((0.09, -0.17, 1.24)), mat=m["helmet_steel"]),
        ])
    bind_part_to_bone(C.join_objects(torso_parts, "TorsoPart"), arm, "Spine")

    # Head (+Y forward!)
    head_parts = [
        C.add_sphere("Skull", 0.11 * scale, (0.88, 1.04, 1.14), s((0, 0.01, 1.60)), mat=m["flesh"]),
        C.add_box("Jaw", s((0.10, 0.11, 0.065)), s((0, 0.04, 1.48)), (math.radians(-12), 0, 0), mat=m["flesh"], bevel=0.006),
        C.add_box("MouthCavity", s((0.075, 0.05, 0.045)), s((0, 0.09, 1.51)), mat=m["blood"], bevel=0.002),
        C.add_box("TeethTop", s((0.070, 0.02, 0.018)), s((0, 0.108, 1.525)), mat=m["teeth"], bevel=0.001),
        C.add_sphere("SocketL", 0.025 * scale, (1, 0.8, 1), s((-0.038, 0.092, 1.60)), mat=m["eye_socket"]),
        C.add_sphere("SocketR", 0.025 * scale, (1, 0.8, 1), s((0.038, 0.092, 1.60)), mat=m["eye_socket"]),
        C.add_sphere("EyeL", 0.015 * scale, (1, 1, 1), s((-0.038, 0.106, 1.60)), mat=eye_mat),
        C.add_sphere("EyeR", 0.015 * scale, (1, 1, 1), s((0.038, 0.106, 1.60)), mat=eye_mat),
    ]
    if variant == "soldier":
        head_parts.extend([
            C.add_sphere("Helmet", 0.132 * scale, (1.02, 1.12, 0.85), s((0, -0.005, 1.66)), mat=m["helmet_steel"]),
            C.add_box("HelmetRim", s((0.25, 0.28, 0.035)), s((0, -0.01, 1.62)), mat=m["helmet_steel"], bevel=0.008),
        ])
    elif variant == "scientist":
        head_parts.extend([
            C.add_box("GoggleRimL", s((0.048, 0.024, 0.038)), s((-0.038, 0.104, 1.60)), mat=m["armor_plate"], bevel=0.004),
            C.add_box("GoggleRimR", s((0.048, 0.024, 0.038)), s((0.038, 0.104, 1.60)), mat=m["armor_plate"], bevel=0.004),
            C.add_box("GoggleBand", s((0.21, 0.21, 0.022)), s((0, 0.0, 1.60)), mat=m["boots"], bevel=0.003),
        ])
    elif variant == "brute":
        head_parts.extend([
            C.add_sphere("HazmatHood", 0.145 * scale, (1.05, 1.12, 1.12), s((0, 0, 1.62)), mat=m["hazmat_cloth"]),
            C.add_box("VisorFrame", s((0.16, 0.06, 0.075)), s((0, 0.10, 1.60)), mat=m["armor_plate"], bevel=0.006),
            C.add_box("Visor", s((0.125, 0.05, 0.042)), s((0, 0.115, 1.60)), mat=eye_mat, bevel=0.004),
            C.add_cyl("MaskFilterL", 0.036 * scale, 0.07 * scale, s((-0.048, 0.13, 1.52)), (math.radians(90), 0, math.radians(-18)), mat=m["armor_plate"]),
            C.add_cyl("MaskFilterR", 0.036 * scale, 0.07 * scale, s((0.048, 0.13, 1.52)), (math.radians(90), 0, math.radians(18)), mat=m["armor_plate"]),
        ])
    bind_part_to_bone(C.join_objects(head_parts, "HeadPart"), arm, "Head")

    # Arms & Legs
    for side, sx in (("L", -1), ("R", 1)):
        upper_w = 0.115 if variant == "brute" else 0.088
        arm_u = C.add_cyl(f"UpperArm_{side}", upper_w * 0.5 * scale, 0.30 * scale, s((0.23 * sx, 0, 1.23)), mat=coat_mat)
        bind_part_to_bone(arm_u, arm, f"Arm_{side}")

        fore_parts = [
            C.add_cyl(f"Forearm_{side}", upper_w * 0.42 * scale, 0.28 * scale, s((0.25 * sx, 0.02, 0.92)), mat=m["flesh"]),
            C.add_box(f"BloodyHand_{side}", s((0.06, 0.08, 0.095)), s((0.26 * sx, 0.04, 0.77)), mat=m["blood"], bevel=0.008),
        ]
        bind_part_to_bone(C.join_objects(fore_parts, f"ForearmPart_{side}"), arm, f"Forearm_{side}")

        thigh = C.add_cyl(f"Thigh_{side}", upper_w * 0.65 * scale, 0.42 * scale, s((0.11 * sx, 0, 0.68)), mat=m["pants"])
        bind_part_to_bone(thigh, arm, f"Thigh_{side}")

        shin_parts = [
            C.add_cyl(f"Shin_{side}", upper_w * 0.52 * scale, 0.34 * scale, s((0.11 * sx, 0, 0.27)), mat=m["pants"]),
            C.add_box(f"Boot_{side}", s((0.105, 0.22, 0.11)), s((0.11 * sx, 0.04, 0.06)), mat=m["boots"], bevel=0.01),
        ]
        bind_part_to_bone(C.join_objects(shin_parts, f"ShinPart_{side}"), arm, f"Shin_{side}")

    add_humanoid_animations(arm, scale=scale)
    C.export_asset("characters", f"zombie_{variant}", export_anims=True)


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
    b("Leg_FL", (-0.14, 0.22, 0.52), (-0.14, 0.22, 0.05), "Body")
    b("Leg_FR", (0.14, 0.22, 0.52), (0.14, 0.22, 0.05), "Body")
    b("Leg_BL", (-0.14, -0.24, 0.52), (-0.14, -0.24, 0.05), "Body")
    b("Leg_BR", (0.14, -0.24, 0.52), (0.14, -0.24, 0.05), "Body")
    bpy.ops.object.mode_set(mode="OBJECT")

    # Body with glowing magma ribs
    body_parts = [
        C.add_box("Torso", (0.28, 0.68, 0.26), (0, 0.02, 0.56), mat=m["hound_char"], bevel=0.03),
        C.add_box("ShoulderHump", (0.34, 0.26, 0.28), (0, 0.22, 0.60), mat=m["hound_char"], bevel=0.03),
        C.add_box("MagmaCore", (0.295, 0.40, 0.10), (0, 0.04, 0.53), mat=m["magma"], bevel=0.01),
        C.add_cone("SpineSpike1", 0.035, 0.0, 0.15, (0, 0.18, 0.74), (math.radians(-22), 0, 0), mat=m["hound_char"]),
        C.add_cone("SpineSpike2", 0.032, 0.0, 0.14, (0, 0.0, 0.73), (math.radians(-22), 0, 0), mat=m["hound_char"]),
        C.add_cone("SpineSpike3", 0.028, 0.0, 0.12, (0, -0.18, 0.72), (math.radians(-22), 0, 0), mat=m["hound_char"]),
        C.add_box("Tail", (0.04, 0.30, 0.04), (0, -0.44, 0.65), (math.radians(34), 0, 0), mat=m["magma"]),
    ]
    bind_part_to_bone(C.join_objects(body_parts, "HoundBody", apply_uv=False), arm, "Body")

    # Head facing +Y
    head_parts = [
        C.add_box("Skull", (0.21, 0.24, 0.21), (0, 0.38, 0.64), mat=m["hound_char"], bevel=0.025),
        C.add_box("Snout", (0.12, 0.22, 0.10), (0, 0.53, 0.62), mat=m["hound_char"], bevel=0.015),
        C.add_box("MagmaJaw", (0.11, 0.18, 0.055), (0, 0.52, 0.54), (math.radians(-20), 0, 0), mat=m["magma"], bevel=0.008),
        C.add_cone("EarL", 0.035, 0.0, 0.15, (-0.075, 0.34, 0.79), (math.radians(-18), 0, 0), mat=m["hound_char"]),
        C.add_cone("EarR", 0.035, 0.0, 0.15, (0.075, 0.34, 0.79), (math.radians(-18), 0, 0), mat=m["hound_char"]),
        C.add_sphere("EyeL", 0.022, (1, 1, 1), (-0.06, 0.48, 0.68), mat=m["magma"]),
        C.add_sphere("EyeR", 0.022, (1, 1, 1), (0.06, 0.48, 0.68), mat=m["magma"]),
    ]
    bind_part_to_bone(C.join_objects(head_parts, "HoundHead", apply_uv=False), arm, "Head")

    for lname, lx, ly in (("Leg_FL", -0.14, 0.22), ("Leg_FR", 0.14, 0.22), ("Leg_BL", -0.14, -0.24), ("Leg_BR", 0.14, -0.24)):
        leg = C.join_objects([
            C.add_cyl(f"{lname}_mesh", 0.042, 0.46, (lx, ly, 0.28), mat=m["hound_char"]),
            C.add_box(f"{lname}_claw", (0.07, 0.11, 0.05), (lx, ly + 0.03, 0.04), mat=m["magma"], bevel=0.008),
        ], f"{lname}_Part", apply_uv=False)
        bind_part_to_bone(leg, arm, lname)

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
