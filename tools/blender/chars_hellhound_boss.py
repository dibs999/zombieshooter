"""Generate Overhauled CC0 Hellhound & Panzersoldat Boss in Blender 4.2:
- hellhound: CC0 Wolf (Micket) refined with Subsurf, charred fur/magma-vein PBR+emission,
  molten furnace chest core, protruding charred ribs, dorsal spikes, fangs & ember claws,
  full quadruped NLA animations (Idle, Run, Attack, Death).
- panzer_boss: CoD Origins Panzersoldat juggernaut (1.42x MPFB2 + CC0 Diving_Helmet by Jerd),
  fuel thruster backpack & hoses, left hydraulic pincer claw arm, right vented flamethrower arm,
  separate breakable armor plate nodes (ArmorPlate_Chest, ArmorPlate_Shoulder_L,
  ArmorPlate_Shoulder_R, Helmet_VisorPlate), and full boss NLA animations
  (Idle, Walk, Run, Attack, FlameAttack, Hit, Death).
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C
import chars_common as CC
import chars_zombies as CZ

WOLF_BLEND = os.path.join(CC.CACHE_DIR, "oga", "wolf", "wolf.blend")
HELMET_OBJ = os.path.join(CC.CACHE_DIR, "oga", "Diving_Helmet.obj")


# ---------------------------------------------------------------------------
# 1. Overhauled Hellhound (Micket CC0 Wolf + Molten Demonic Sculpt)
# ---------------------------------------------------------------------------

def _make_hound_anim(rig_obj, name, frame_poses, scale=1.0):
    act = bpy.data.actions.new(name=name)
    act.use_fake_user = True
    rig_obj.animation_data.action = act
    for frame, poses in frame_poses.items():
        for pb in rig_obj.pose.bones:
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
        for bname, vals in poses.items():
            if "rot" in vals:
                CC._pose_bone_world_rot(rig_obj, bname, vals["rot"])
            if "loc" in vals:
                CC._pose_bone_world_loc(rig_obj, bname, vals["loc"], scale=scale)
        for pb in rig_obj.pose.bones:
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
            pb.keyframe_insert(data_path="location", frame=frame)
    track = rig_obj.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, 1, act)
    strip.action_frame_start = 1
    strip.action_frame_end = max(frame_poses.keys())
    rig_obj.animation_data.action = None


def build_hellhound(m):
    C.reset_scene()
    m = CC.build_char_materials()

    with bpy.data.libraries.load(WOLF_BLEND, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n in ("Armature", "Wolf")]
    for obj in dt.objects:
        bpy.context.collection.objects.link(obj)

    rig = bpy.data.objects["Armature"]
    wolf = bpy.data.objects["Wolf"]
    rig.data.use_mirror_x = False

    wolf.parent = None
    for mod in list(wolf.modifiers):
        if mod.type == "ARMATURE":
            wolf.modifiers.remove(mod)

    # Rotate +Y forward and shift paws flush to Z=0 at uniform hound scale
    rot_z = Matrix.Rotation(math.pi, 4, "Z")
    wolf.data.transform(rot_z)

    bpy.context.view_layer.objects.active = wolf
    bpy.ops.object.select_all(action="DESELECT")
    wolf.select_set(True)
    for mod in list(wolf.modifiers):
        if mod.type == "MIRROR":
            bpy.ops.object.modifier_apply(modifier=mod.name)

    min_z = min(v.co.z for v in wolf.data.vertices)
    hound_scale = 0.245
    xf = Matrix.Scale(hound_scale, 4) @ Matrix.Translation((0.0, 0.0, -min_z))
    wolf.data.transform(xf)

    # Subdivide smoothly then decimate into ~3.6k tris keeping canine anatomy crisp
    sub = wolf.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    bpy.ops.object.modifier_apply(modifier=sub.name)

    dec = wolf.modifiers.new("Decimate", "DECIMATE")
    dec.decimate_type = "COLLAPSE"
    dec.ratio = 0.58
    dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=dec.name)

    C.uv_box_project(wolf, scale=2.8)
    C.smooth_shade(wolf, 64.0)
    C.assign_mat(wolf, m["hellhound_hide"])
    wolf.name = "Hellhound_Body"

    # Transform bones identically in Edit Mode & connect Tail1 -> Bone
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    orig_connect = {eb.name: eb.use_connect for eb in rig.data.edit_bones}
    for eb in rig.data.edit_bones:
        eb.use_connect = False
    for eb in rig.data.edit_bones:
        eb.head = xf @ (rot_z @ eb.head)
        eb.tail = xf @ (rot_z @ eb.tail)
    for eb in rig.data.edit_bones:
        if orig_connect.get(eb.name, False):
            eb.use_connect = True
    if "Tail1" in rig.data.edit_bones and "Bone" in rig.data.edit_bones:
        rig.data.edit_bones["Tail1"].parent = rig.data.edit_bones["Bone"]
    bpy.ops.object.mode_set(mode="OBJECT")

    rig.name = "Hellhound_Armature"
    rig.data.name = "Hellhound_ArmData"

    # Re-attach Armature modifier to main Wolf body
    mod = wolf.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    wolf.parent = rig

    # --- Sculpted Demonic Hellhound Features ---
    # 1) Glowing Molten Magma Core inside chest/ribcage
    magma_core = C.add_sphere(
        "HoundMagmaCore", 1.0, (0.132, 0.168, 0.102),
        (0.0, 0.055, 0.568), (math.radians(-6), 0, 0),
        segments=12, rings=8, mat=m["magma"],
    )
    CC.bind_accessory_to_bones(magma_core, rig, {"Bone.005": 0.55, "Bone.001": 0.45}, scale=1.0, keep_existing_uv=True)

    # 2) Curved Anatomical Charred Ribcage hugging torso flanks & framing the molten chest core
    rib_parts = []
    for ri in range(5):
        ry = -0.095 + ri * 0.068
        spread = 0.126 + math.sin((ri / 4.0) * math.pi) * 0.014
        z_top = 0.735 - ri * 0.008
        z_bot = 0.445 + ri * 0.012
        z_mid = 0.5 * (z_top + z_bot) + 0.014
        for sx in (-1, 1):
            rib_parts.append(C.add_tube_pipe(
                f"HoundRib_{ri}_{sx}",
                [
                    (sx * 0.025, ry - 0.014, z_top),
                    (sx * (spread * 0.74), ry - 0.004, z_top - 0.036),
                    (sx * spread, ry + 0.006, z_mid),
                    (sx * (spread * 0.80), ry + 0.013, z_bot + 0.044),
                    (sx * 0.052, ry + 0.016, z_bot),
                ],
                radius=0.0085, segments=5,
                radii=[0.008, 0.0095, 0.010, 0.0085, 0.006],
                mat=m["hound_bone"],
            ))
    ribs = C.join_objects(rib_parts, "Hellhound_Ribs", apply_uv=False)
    CC.bind_accessory_to_bones(ribs, rig, lambda x, y, z: {"Bone.001": 0.70, "Bone.005": 0.30} if y > 0.0 else {"Bone.005": 0.75, "Bone": 0.25}, scale=1.0, keep_existing_uv=True)

    # 3) Dorsal Volcanic Spine Spikes running down back + neck
    spike_specs = [
        ((0.0, 0.35, 0.855), 0.024, 0.090, -28, "Neck3"),
        ((0.0, 0.23, 0.840), 0.026, 0.105, -26, "Neck2"),
        ((0.0, 0.10, 0.822), 0.030, 0.125, -25, "Bone.001"),
        ((0.0, -0.04, 0.820), 0.032, 0.138, -28, "Bone.001"),
        ((0.0, -0.18, 0.825), 0.030, 0.128, -30, "Bone.005"),
        ((0.0, -0.32, 0.835), 0.026, 0.108, -32, "Bone.005"),
        ((0.0, -0.46, 0.820), 0.022, 0.090, -34, "Bone"),
    ]
    for idx, (loc, rad, dep, pitch, bn) in enumerate(spike_specs):
        sp = C.add_cone(f"HoundSpike_{idx}", rad, 0.003, dep, loc, (math.radians(pitch), 0, 0), vertices=6, mat=m["hound_bone"])
        CC.bind_accessory_to_bones(sp, rig, bn, scale=1.0, keep_existing_uv=True)

    # 4) Dark Sunken Eye Sockets + Piercing Ember Eyes + Snarling Upper Fangs (Head) & Lower Fangs + Tongue (Jaw2)
    eye_parts = []
    for sx in (-1, 1):
        eye_parts.append(C.add_sphere(
            f"HoundEyeSocket_{sx}", 1.0, (0.016, 0.020, 0.017),
            (sx * 0.043, 0.506, 0.784), (math.radians(-12), 0, math.radians(sx * -22)),
            segments=10, rings=8, mat=m["socket_dark"],
        ))
        eye_parts.append(C.add_sphere(
            f"HoundEye_{sx}", 1.0, (0.0095, 0.015, 0.010),
            (sx * 0.045, 0.517, 0.785), (math.radians(-12), 0, math.radians(sx * -22)),
            segments=10, rings=8, mat=m["hound_eye"],
        ))
    # Upper fangs seated strictly beneath upper palate (Z_top <= 0.665 < snout Z=0.688)
    for sx in (-1, 1):
        eye_parts.append(C.add_cone(f"UpperCanine_{sx}", 0.0068, 0.0010, 0.028, (sx * 0.019, 0.570, 0.650), (math.radians(170), 0, 0), vertices=6, mat=m["bone"]))
        eye_parts.append(C.add_cone(f"UpperIncisor_{sx}", 0.0042, 0.0010, 0.017, (sx * 0.007, 0.588, 0.648), (math.radians(172), 0, 0), vertices=5, mat=m["bone"]))
    head_feat = C.join_objects(eye_parts, "Hellhound_HeadFeatures", apply_uv=False)
    CC.bind_accessory_to_bones(head_feat, rig, "Head", scale=1.0, keep_existing_uv=True)

    jaw_parts = [
        C.add_cone("LowerCanine_L", 0.0055, 0.0010, 0.022, (-0.014, 0.538, 0.634), (math.radians(12), 0, 0), vertices=6, mat=m["bone"]),
        C.add_cone("LowerCanine_R", 0.0055, 0.0010, 0.022, (0.014, 0.538, 0.634), (math.radians(12), 0, 0), vertices=6, mat=m["bone"]),
        C.add_sphere("MoltenTongue", 1.0, (0.013, 0.036, 0.006), (0.0, 0.512, 0.632), (math.radians(-12), 0, 0), segments=8, rings=6, mat=m["magma"]),
    ]
    jaw_feat = C.join_objects(jaw_parts, "Hellhound_JawFeatures", apply_uv=False)
    CC.bind_accessory_to_bones(jaw_feat, rig, "Jaw2", scale=1.0, keep_existing_uv=True)

    # 5) Glowing Ember Claws on all 4 paws
    paw_specs = [
        ("FrontToe_L", -0.082, 0.338, 0.018),
        ("FrontToe_R", 0.082, 0.338, 0.018),
        ("BackToe_L", -0.080, -0.415, 0.018),
        ("BackToe_R", 0.080, -0.415, 0.018),
    ]
    for bn, px, py, pz in paw_specs:
        claws = []
        for ci, dx in enumerate((-0.022, 0.0, 0.022)):
            claws.append(C.add_cone(
                f"{bn}_Claw{ci}", 0.007, 0.001, 0.038,
                (px + dx, py, pz), (math.radians(80), 0, 0), vertices=5, mat=m["magma"],
            ))
        c_obj = C.join_objects(claws, f"Hellhound_Claws_{bn}", apply_uv=False)
        CC.bind_accessory_to_bones(c_obj, rig, bn, scale=1.0, keep_existing_uv=True)

    # --- Quadruped Animations ---
    if not rig.animation_data:
        rig.animation_data_create()
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"

    _make_hound_anim(rig, "Idle", {
        1: {
            "Bone": {"rot": (4, 0, 0)},
            "Bone.005": {"rot": (-4, 0, 0)},
            "Neck2": {"rot": (6, 0, 0)},
            "Head": {"rot": (-8, 0, 0)},
            "Jaw1": {"rot": (-14, 0, 0)},
            "Tail1": {"rot": (16, 0, -10)}, "Tail2": {"rot": (12, 0, -12)},
        },
        16: {
            "Bone": {"loc": (0, 0, -0.018), "rot": (2, 0, 0)},
            "Bone.005": {"rot": (-6, 0, 0)},
            "Neck2": {"rot": (10, 0, 4)},
            "Head": {"rot": (-12, 0, -4)},
            "Jaw1": {"rot": (-26, 0, 0)},
            "Tail1": {"rot": (22, 0, 12)}, "Tail2": {"rot": (16, 0, 14)},
        },
        32: {
            "Bone": {"rot": (4, 0, 0)},
            "Bone.005": {"rot": (-4, 0, 0)},
            "Neck2": {"rot": (6, 0, 0)},
            "Head": {"rot": (-8, 0, 0)},
            "Jaw1": {"rot": (-14, 0, 0)},
            "Tail1": {"rot": (16, 0, -10)}, "Tail2": {"rot": (12, 0, -12)},
        },
    })

    # Bounding predator gallop (extended leap -> tucked gather -> push off)
    _make_hound_anim(rig, "Run", {
        1: { # Extended stretch phase: front legs forward, back legs kicking backward
            "Bone": {"loc": (0, 0, 0.04), "rot": (-14, 0, 0)},
            "Bone.005": {"rot": (12, 0, 0)}, "Bone.001": {"rot": (8, 0, 0)},
            "Neck2": {"rot": (-10, 0, 0)}, "Head": {"rot": (-14, 0, 0)},
            "Jaw1": {"rot": (-24, 0, 0)},
            "FrontShoulder_L": {"rot": (34, 0, 0)}, "FrontLeg1_L": {"rot": (24, 0, 0)}, "FrontLeg2_L": {"rot": (14, 0, 0)},
            "FrontShoulder_R": {"rot": (22, 0, 0)}, "FrontLeg1_R": {"rot": (28, 0, 0)}, "FrontLeg2_R": {"rot": (10, 0, 0)},
            "BackLeg1_L": {"rot": (-44, 0, 0)}, "BackLeg2_L": {"rot": (-22, 0, 0)},
            "BackLeg1_R": {"rot": (-34, 0, 0)}, "BackLeg2_R": {"rot": (-28, 0, 0)},
            "Tail1": {"rot": (-12, 0, 0)}, "Tail2": {"rot": (-14, 0, 0)},
        },
        8: { # Gather / coiled spring phase
            "Bone": {"loc": (0, 0, -0.05), "rot": (18, 0, 0)},
            "Bone.005": {"rot": (-16, 0, 0)}, "Bone.001": {"rot": (-12, 0, 0)},
            "Neck2": {"rot": (12, 0, 0)}, "Head": {"rot": (-4, 0, 0)},
            "Jaw1": {"rot": (-16, 0, 0)},
            "FrontShoulder_L": {"rot": (-28, 0, 0)}, "FrontLeg1_L": {"rot": (-28, 0, 0)}, "FrontLeg2_L": {"rot": (22, 0, 0)},
            "FrontShoulder_R": {"rot": (-36, 0, 0)}, "FrontLeg1_R": {"rot": (-20, 0, 0)}, "FrontLeg2_R": {"rot": (26, 0, 0)},
            "BackLeg1_L": {"rot": (46, 0, 0)}, "BackLeg2_L": {"rot": (-32, 0, 0)},
            "BackLeg1_R": {"rot": (38, 0, 0)}, "BackLeg2_R": {"rot": (-26, 0, 0)},
            "Tail1": {"rot": (16, 0, 0)}, "Tail2": {"rot": (14, 0, 0)},
        },
        15: {
            "Bone": {"loc": (0, 0, 0.04), "rot": (-14, 0, 0)},
            "Bone.005": {"rot": (12, 0, 0)}, "Bone.001": {"rot": (8, 0, 0)},
            "Neck2": {"rot": (-10, 0, 0)}, "Head": {"rot": (-14, 0, 0)},
            "Jaw1": {"rot": (-24, 0, 0)},
            "FrontShoulder_L": {"rot": (34, 0, 0)}, "FrontLeg1_L": {"rot": (24, 0, 0)}, "FrontLeg2_L": {"rot": (14, 0, 0)},
            "FrontShoulder_R": {"rot": (22, 0, 0)}, "FrontLeg1_R": {"rot": (28, 0, 0)}, "FrontLeg2_R": {"rot": (10, 0, 0)},
            "BackLeg1_L": {"rot": (-44, 0, 0)}, "BackLeg2_L": {"rot": (-22, 0, 0)},
            "BackLeg1_R": {"rot": (-34, 0, 0)}, "BackLeg2_R": {"rot": (-28, 0, 0)},
            "Tail1": {"rot": (-12, 0, 0)}, "Tail2": {"rot": (-14, 0, 0)},
        },
    })

    _make_hound_anim(rig, "Attack", {
        1: {
            "Bone": {"loc": (0, -0.05, -0.08), "rot": (18, 0, 0)},
            "Neck2": {"rot": (16, 0, 0)}, "Head": {"rot": (12, 0, 0)}, "Jaw1": {"rot": (-42, 0, 0)},
            "FrontShoulder_L": {"rot": (-20, 0, 0)}, "FrontShoulder_R": {"rot": (-20, 0, 0)},
        },
        7: {
            "Bone": {"loc": (0, 0.14, 0.12), "rot": (-22, 0, 0)},
            "Bone.005": {"rot": (-10, 0, 0)},
            "Neck2": {"rot": (-14, 0, 0)}, "Head": {"rot": (-18, 0, 0)}, "Jaw1": {"rot": (-46, 0, 0)},
            "FrontShoulder_L": {"rot": (52, 0, -10)}, "FrontLeg1_L": {"rot": (25, 0, 0)},
            "FrontShoulder_R": {"rot": (48, 0, 10)}, "FrontLeg1_R": {"rot": (25, 0, 0)},
            "BackLeg1_L": {"rot": (-48, 0, 0)}, "BackLeg1_R": {"rot": (-48, 0, 0)},
        },
        14: {
            "Bone": {"loc": (0, 0, 0), "rot": (0, 0, 0)},
            "Jaw1": {"rot": (-12, 0, 0)},
        },
    })

    _make_hound_anim(rig, "Death", {
        1: {"Bone": {"loc": (0, 0, 0), "rot": (0, 0, 0)}},
        9: {
            "Bone": {"loc": (0, 0, -0.26), "rot": (8, 42, 0)},
            "Neck2": {"rot": (-20, 15, 0)}, "Jaw1": {"rot": (-28, 0, 0)},
            "FrontShoulder_L": {"rot": (-25, 0, 22)}, "BackLeg1_L": {"rot": (25, 0, 18)},
        },
        18: {
            "Bone": {"loc": (0, 0, -0.52), "rot": (12, 82, 0)},
            "Neck2": {"rot": (-26, 20, 0)}, "Head": {"rot": (-15, 18, 0)}, "Jaw1": {"rot": (-20, 0, 0)},
            "FrontShoulder_L": {"rot": (-38, 0, 32)}, "FrontShoulder_R": {"rot": (24, 0, -18)},
            "BackLeg1_L": {"rot": (35, 0, 28)}, "BackLeg1_R": {"rot": (-22, 0, -16)},
        },
    })

    bpy.ops.object.mode_set(mode="OBJECT")
    mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = sum(len(p.vertices) - 2 for obj in mesh_objs for p in obj.data.polygons)
    print(f"[CHARS] hellhound tris={tris}, parts={[o.name for o in mesh_objs]}")
    C.export_asset("characters", "hellhound", export_anims=True)


# ---------------------------------------------------------------------------
# 2. Panzersoldat Boss (MPFB2 Juggernaut + Jerd CC0 Diving Helmet + Mech Weapons)
# ---------------------------------------------------------------------------

def _import_cc0_diving_helmet(m, rig, scale):
    """Import CC0 Diving_Helmet.obj (Jerd), align front viewport +Y, decimate, attach to Head."""
    before = set(bpy.data.objects.keys())
    bpy.ops.wm.obj_import(filepath=HELMET_OBJ)
    new_objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == "MESH"]
    helm = C.join_objects(new_objs, "PanzerDivingHelmet", apply_uv=False)

    # Rotate +90° around Z so original +X barred front viewport aims cleanly +Y Forward!
    helm.rotation_euler = (0.0, 0.0, math.pi * 0.5)
    bpy.context.view_layer.update()
    CC._apply_xform([helm])

    # Center XY on origin and scale cleanly to fit 1.42x scale juggernaut shoulders
    xs = [v.co.x for v in helm.data.vertices]
    ys = [v.co.y for v in helm.data.vertices]
    zs = [v.co.z for v in helm.data.vertices]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    min_z = min(zs)
    helm_scale = 0.168 * scale
    for v in helm.data.vertices:
        v.co = Vector(((v.co.x - cx) * helm_scale, (v.co.y - cy) * helm_scale + 0.015 * scale, (v.co.z - min_z) * helm_scale + 1.445 * scale))

    # Decimate helmet cleanly to ~1.7k-2.0k tris while preserving silhouette & viewport grill
    bpy.ops.object.select_all(action="DESELECT")
    helm.select_set(True)
    bpy.context.view_layer.objects.active = helm
    dec = helm.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = 0.16
    dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=dec.name)

    C.uv_box_project(helm, scale=2.5)
    C.smooth_shade(helm, 48.0)
    C.assign_mat(helm, m["panzer_armor"])
    CC.bind_accessory_to_bones(helm, rig, "Head", scale=scale, keep_existing_uv=True)
    return helm


def _add_panzer_animations(rig_obj, scale=1.42):
    if not rig_obj.animation_data:
        rig_obj.animation_data_create()
    bpy.ops.object.select_all(action="DESELECT")
    rig_obj.select_set(True)
    bpy.context.view_layer.objects.active = rig_obj
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig_obj.pose.bones:
        pb.rotation_mode = "XYZ"

    def make_act(name, frame_poses):
        act = bpy.data.actions.new(name=name)
        act.use_fake_user = True
        rig_obj.animation_data.action = act
        for frame, poses in frame_poses.items():
            for pb in rig_obj.pose.bones:
                pb.rotation_euler = (0.0, 0.0, 0.0)
                pb.location = (0.0, 0.0, 0.0)
            for bname, vals in poses.items():
                if "rot" in vals:
                    CC._pose_bone_world_rot(rig_obj, bname, vals["rot"])
                if "loc" in vals:
                    CC._pose_bone_world_loc(rig_obj, bname, vals["loc"], scale=scale)
            for pb in rig_obj.pose.bones:
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)
                pb.keyframe_insert(data_path="location", frame=frame)
        track = rig_obj.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, act)
        strip.action_frame_start = 1
        strip.action_frame_end = max(frame_poses.keys())
        rig_obj.animation_data.action = None

    make_act("Idle", {
        1: {
            "pelvis": {"loc": (0, 0, -0.02), "rot": (-2, 0, 0)},
            "spine_01": {"rot": (-4, 0, 0)}, "spine_02": {"rot": (-6, 0, 0)}, "Head": {"rot": (8, 0, 0)},
            "upperarm_l": {"rot": (22, 12, -10)}, "lowerarm_l": {"rot": (24, 0, 8)},
            "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (26, 0, -8)},
            "thigh_l": {"rot": (6, 0, -4)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-4, 0, 4)}, "calf_r": {"rot": (-8, 0, 0)},
        },
        24: {
            "pelvis": {"loc": (0, 0, 0.01), "rot": (-4, 0, 0)},
            "spine_01": {"rot": (-6, 0, 0)}, "spine_02": {"rot": (-8, 0, 0)}, "Head": {"rot": (12, 4, 0)},
            "upperarm_l": {"rot": (28, 14, -8)}, "lowerarm_l": {"rot": (28, 0, 8)},
            "upperarm_r": {"rot": (34, -14, 8)}, "lowerarm_r": {"rot": (30, 0, -8)},
        },
        48: {
            "pelvis": {"loc": (0, 0, -0.02), "rot": (-2, 0, 0)},
            "spine_01": {"rot": (-4, 0, 0)}, "spine_02": {"rot": (-6, 0, 0)}, "Head": {"rot": (8, 0, 0)},
            "upperarm_l": {"rot": (22, 12, -10)}, "lowerarm_l": {"rot": (24, 0, 8)},
            "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (26, 0, -8)},
        },
    })

    # Heavy mechanical stomp walk
    w1 = {
        "pelvis": {"loc": (0, 0, -0.03), "rot": (-4, -4, 6)},
        "spine_02": {"rot": (-8, 3, -6)}, "Head": {"rot": (10, 0, 4)},
        "upperarm_l": {"rot": (32, 12, -10)}, "lowerarm_l": {"rot": (26, 0, 8)},
        "upperarm_r": {"rot": (40, -12, 8)}, "lowerarm_r": {"rot": (24, 0, -6)},
        "thigh_l": {"rot": (28, 0, -3)}, "calf_l": {"rot": (-30, 0, 0)},
        "thigh_r": {"rot": (-20, 0, 3)}, "calf_r": {"rot": (-14, 0, 0)},
    }
    w2 = {
        "pelvis": {"loc": (0, 0, -0.03), "rot": (-4, 4, -6)},
        "spine_02": {"rot": (-8, -3, 6)}, "Head": {"rot": (10, 0, -4)},
        "upperarm_l": {"rot": (42, 12, -8)}, "lowerarm_l": {"rot": (22, 0, 8)},
        "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (28, 0, -6)},
        "thigh_l": {"rot": (-20, 0, -3)}, "calf_l": {"rot": (-14, 0, 0)},
        "thigh_r": {"rot": (28, 0, 3)}, "calf_r": {"rot": (-30, 0, 0)},
    }
    make_act("Walk", {1: w1, 18: w2, 35: w1})
    make_act("Run", {1: w1, 12: w2, 23: w1})

    # Left Claw Heavy Smash / Sweep
    make_act("Attack", {
        1: {"spine_02": {"rot": (6, 0, -14)}, "upperarm_l": {"rot": (104, 24, -20)}, "lowerarm_l": {"rot": (20, 0, 0)}, "upperarm_r": {"rot": (22, -12, 12)}, "lowerarm_r": {"rot": (26, 0, -8)}},
        10: {"pelvis": {"loc": (0, 0.06, -0.04), "rot": (-12, 0, 16)}, "spine_02": {"rot": (-18, 0, 18)}, "Head": {"rot": (18, 0, 0)},
             "upperarm_l": {"rot": (54, -20, 22)}, "lowerarm_l": {"rot": (18, 0, -10)}, "upperarm_r": {"rot": (18, -10, 14)}, "lowerarm_r": {"rot": (24, 0, -8)}},
        22: {"spine_02": {"rot": (-6, 0, 0)}, "upperarm_l": {"rot": (26, 12, -10)}, "lowerarm_l": {"rot": (24, 0, 8)}, "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (26, 0, -8)}},
    })

    # Right Arm Flamethrower Sweep (levels forearm & barrel horizontally forward +Y at chest height!)
    make_act("FlameAttack", {
        1: {
            "pelvis": {"loc": (0, 0, -0.04), "rot": (-6, 0, -8)},
            "spine_01": {"rot": (-4, 0, -4)}, "spine_02": {"rot": (-6, 0, -8)}, "Head": {"rot": (10, 0, 8)},
            "upperarm_r": {"rot": (12, -6, 20)}, "lowerarm_r": {"rot": (24, 0, 0)}, "hand_r": {"rot": (0, 0, 0)},
            "upperarm_l": {"rot": (24, 16, -12)}, "lowerarm_l": {"rot": (26, 0, 8)},
            "thigh_l": {"rot": (8, 0, -4)}, "calf_l": {"rot": (-12, 0, 0)},
            "thigh_r": {"rot": (-6, 0, 4)}, "calf_r": {"rot": (-10, 0, 0)},
        },
        14: {
            "pelvis": {"loc": (0, 0, -0.04), "rot": (-6, 0, 8)},
            "spine_01": {"rot": (-4, 0, 4)}, "spine_02": {"rot": (-6, 0, 8)}, "Head": {"rot": (10, 0, -8)},
            "upperarm_r": {"rot": (10, -6, 34)}, "lowerarm_r": {"rot": (24, 0, 4)}, "hand_r": {"rot": (0, 0, 0)},
            "upperarm_l": {"rot": (24, 16, -12)}, "lowerarm_l": {"rot": (26, 0, 8)},
            "thigh_l": {"rot": (8, 0, -4)}, "calf_l": {"rot": (-12, 0, 0)},
            "thigh_r": {"rot": (-6, 0, 4)}, "calf_r": {"rot": (-10, 0, 0)},
        },
        27: {
            "pelvis": {"loc": (0, 0, -0.04), "rot": (-6, 0, -8)},
            "spine_01": {"rot": (-4, 0, -4)}, "spine_02": {"rot": (-6, 0, -8)}, "Head": {"rot": (10, 0, 8)},
            "upperarm_r": {"rot": (12, -6, 20)}, "lowerarm_r": {"rot": (24, 0, 0)}, "hand_r": {"rot": (0, 0, 0)},
            "upperarm_l": {"rot": (24, 16, -12)}, "lowerarm_l": {"rot": (26, 0, 8)},
            "thigh_l": {"rot": (8, 0, -4)}, "calf_l": {"rot": (-12, 0, 0)},
            "thigh_r": {"rot": (-6, 0, 4)}, "calf_r": {"rot": (-10, 0, 0)},
        },
    })

    # Stagger Hit preserves full upperarm/lowerarm/leg pose so arms never pop back to A-pose!
    make_act("Hit", {
        1: {
            "pelvis": {"loc": (0, 0, -0.02), "rot": (-2, 0, 0)},
            "spine_02": {"rot": (-6, 0, 0)}, "Head": {"rot": (8, 0, 0)},
            "upperarm_l": {"rot": (24, 12, -10)}, "lowerarm_l": {"rot": (24, 0, 8)},
            "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (26, 0, -8)},
            "thigh_l": {"rot": (6, 0, -4)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-4, 0, 4)}, "calf_r": {"rot": (-8, 0, 0)},
        },
        7: {
            "pelvis": {"loc": (0, -0.04, -0.03), "rot": (12, 0, -8)},
            "spine_02": {"rot": (16, 6, -8)}, "Head": {"rot": (18, -8, 0)},
            "upperarm_l": {"rot": (38, 18, -18)}, "lowerarm_l": {"rot": (30, 0, 10)},
            "upperarm_r": {"rot": (22, -18, 18)}, "lowerarm_r": {"rot": (30, 0, -10)},
            "thigh_l": {"rot": (10, 0, -4)}, "calf_l": {"rot": (-14, 0, 0)},
            "thigh_r": {"rot": (-6, 0, 4)}, "calf_r": {"rot": (-10, 0, 0)},
        },
        16: {
            "pelvis": {"loc": (0, 0, -0.02), "rot": (-2, 0, 0)},
            "spine_02": {"rot": (-6, 0, 0)}, "Head": {"rot": (8, 0, 0)},
            "upperarm_l": {"rot": (24, 12, -10)}, "lowerarm_l": {"rot": (24, 0, 8)},
            "upperarm_r": {"rot": (28, -12, 10)}, "lowerarm_r": {"rot": (26, 0, -8)},
            "thigh_l": {"rot": (6, 0, -4)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-4, 0, 4)}, "calf_r": {"rot": (-8, 0, 0)},
        },
    })

    make_act("Death", {
        1: {
            "pelvis": {"loc": (0, 0, -0.02), "rot": (-2, 0, 0)},
            "spine_02": {"rot": (-6, 0, 0)},
            "upperarm_l": {"rot": (30, 12, -10)}, "lowerarm_l": {"rot": (44, 0, 8)},
            "upperarm_r": {"rot": (38, -12, 10)}, "lowerarm_r": {"rot": (48, 0, -8)},
        },
        12: {
            "pelvis": {"loc": (0, 0.14, -0.35), "rot": (-38, 0, -6)},
            "spine_02": {"rot": (-18, 0, 0)},
            "upperarm_l": {"rot": (58, 18, -18)}, "lowerarm_l": {"rot": (36, 0, 6)},
            "upperarm_r": {"rot": (62, -18, 18)}, "lowerarm_r": {"rot": (38, 0, -6)},
            "thigh_l": {"rot": (30, 0, 0)}, "calf_l": {"rot": (-78, 0, 0)},
            "thigh_r": {"rot": (25, 0, 0)}, "calf_r": {"rot": (-74, 0, 0)},
        },
        28: {
            "pelvis": {"loc": (0, 0.42, -0.78), "rot": (-86, 0, -8)},
            "spine_02": {"rot": (-8, 0, 0)},
            "upperarm_l": {"rot": (125, 25, -30)}, "lowerarm_l": {"rot": (22, 0, 0)},
            "upperarm_r": {"rot": (118, -25, 28)}, "lowerarm_r": {"rot": (22, 0, 0)},
            "thigh_l": {"rot": (-6, 0, -6)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-6, 0, 6)}, "calf_r": {"rot": (-10, 0, 0)},
        },
    })

    bpy.ops.object.mode_set(mode="OBJECT")


def build_panzer_boss(m):
    C.reset_scene()
    m = CC.build_char_materials()

    scale = 1.42
    def s(v):
        return (v[0] * scale, v[1] * scale, v[2] * scale)

    rig, body, eyes = CC.create_mpfb_zombie_base(
        "panzer", scale=scale, age=0.72, muscle=0.95, weight=0.55, height=0.60,
        skin_mat=m["panzer_suit"], eye_mat=m["eye_orange"], boot_sole=0.030, decimate_ratio=0.11,
        bake_claw=False,
    )
    rig.name = "Panzer_boss_Armature"
    rig.data.name = "Panzer_boss_ArmData"

    # Full Armored Diving Pressure Undersuit (covers upper torso/hips/shoulders ONLY; zero bare fingers or leg clipping!)
    skip_suit_bones = (CC.ARM_L_BONES - {"upperarm_l"}) | (CC.ARM_R_BONES - {"upperarm_r"}) | {"calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"}
    suit = CC.make_tailored_garment(
        body, rig, "PanzerUndersuit", m["panzer_suit"],
        lambda x, y, z, w: (
            w.get("Head", 0) < 0.6
            and sum(w.get(b, 0.0) for b in skip_suit_bones) < 0.25
            and (0.58 <= z <= 1.48)
        ),
        offset=0.004, thickness=0.003, uv_scale=2.4, wrinkle_amp=0.0005, scale=scale,
    )

    # Bone-Aligned Heavy Mechanical Leg Greaves, Knee Cops & Solid Mech Sabaton Boots (ZERO bare human toes!)
    leg_objs = CZ._add_jackboots(body, rig, m, scale, heavy=True, boot_mat=m["panzer_armor"], panzer_sabaton=True)

    # Strip ALL bare limb/hand/foot faces from inner MPFB body + remove eyes so zero exposed flesh ever renders on mech Panzer
    bpy.data.objects.remove(eyes, do_unlink=True)
    strip_bones = CC.ARM_L_BONES | CC.ARM_R_BONES | CC.LEG_BONES
    vg_by_idx = {vg.index: vg.name for vg in body.vertex_groups}
    bm_b = bmesh.new()
    bm_b.from_mesh(body.data)
    d_lay = bm_b.verts.layers.deform.active
    if d_lay is not None:
        del_faces = []
        for f in bm_b.faces:
            c = f.calc_center_median()
            w_limb = 0.0
            inv_n = 1.0 / max(1, len(f.verts))
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    if vg_by_idx.get(gi, "") in strip_bones:
                        w_limb += gw * inv_n
            if w_limb > 0.20 or (c.z / scale) < 1.08:
                del_faces.append(f)
        if del_faces:
            bmesh.ops.delete(bm_b, geom=del_faces, context="FACES")
            lv = [v for v in bm_b.verts if not v.link_faces]
            if lv:
                bmesh.ops.delete(bm_b, geom=lv, context="VERTS")
    bm_b.to_mesh(body.data)
    bm_b.free()

    for side, sfx, sx in (("L", "l", -1), ("R", "r", 1)):
        _, _, th_len = CC.bone_frame(rig, f"thigh_{sfx}", along_t=0.5)
        thigh_g = C.add_cyl(f"PanzerThigh_{side}", 0.122 * scale, th_len * 0.84, (0, 0, 0), vertices=12, mat=m["panzer_trim"], bevel=0.0)
        CC.transform_along_bone(thigh_g, rig, f"thigh_{sfx}", along_t=0.50)
        CC.bind_accessory_to_bones(thigh_g, rig, f"thigh_{sfx}", scale=scale, keep_existing_uv=True)

        hip_orig, _, _ = CC.bone_frame(rig, f"thigh_{sfx}", along_t=0.14)
        hip_plate = C.add_box(f"PanzerHipPlate_{side}", (0.068 * scale, 0.19 * scale, 0.21 * scale), hip_orig + Vector((sx * 0.094 * scale, 0.0, 0.015 * scale)), (0, math.radians(sx * 10), 0), mat=m["panzer_armor"], bevel=0.014 * scale)
        CC.bind_accessory_to_bones(hip_plate, rig, {"pelvis": 0.50, f"thigh_{sfx}": 0.50}, scale=scale, keep_existing_uv=True)

        _, _, cf_len = CC.bone_frame(rig, f"calf_{sfx}", along_t=0.5)
        shin_g = C.add_cyl(f"PanzerShin_{side}", 0.092 * scale, cf_len * 0.72, (0, 0, 0), vertices=12, mat=m["panzer_trim"], bevel=0.0)
        CC.transform_along_bone(shin_g, rig, f"calf_{sfx}", along_t=0.40)
        CC.bind_accessory_to_bones(shin_g, rig, f"calf_{sfx}", scale=scale, keep_existing_uv=True)

        knee_orig, _, _ = CC.bone_frame(rig, f"calf_{sfx}", along_t=0.02)
        knee_cop = C.add_sphere(f"PanzerKnee_{side}", 0.096 * scale, (1.02, 1.15, 0.98), knee_orig + Vector((0.0, 0.028 * scale, 0.0)), segments=12, rings=8, mat=m["panzer_armor"])
        CC.bind_accessory_to_bones(knee_cop, rig, {f"calf_{sfx}": 0.55, f"thigh_{sfx}": 0.45}, scale=scale, keep_existing_uv=True)
        leg_objs.extend([thigh_g, hip_plate, shin_g, knee_cop])

    # Contoured Torso Chassis + Radial Armored Furnace Turbine Core + Fuel Thruster Backpack
    torso_parts = [
        C.add_box("PanzerPelvisBlock", s((0.36, 0.23, 0.15)), s((0.0, 0.012, 0.96)), mat=m["panzer_trim"], bevel=0.035 * scale),
        C.add_box("PanzerGroinTasset", s((0.18, 0.12, 0.16)), s((0.0, 0.105, 0.92)), (math.radians(8), 0, 0), mat=m["panzer_armor"], bevel=0.018 * scale),
        C.add_box("PanzerHazardBelt", s((0.38, 0.25, 0.048)), s((0.0, 0.014, 1.045)), mat=m["hazard_metal"], bevel=0.010 * scale),
        C.add_box("PanzerChassis", s((0.36, 0.24, 0.34)), s((0.0, 0.010, 1.25)), mat=m["panzer_trim"], bevel=0.036 * scale),
        C.add_cyl("PanzerChestCollar", 0.145 * scale, 0.068 * scale, s((0.0, 0.008, 1.43)), vertices=12, mat=m["panzer_armor"], bevel=0.0),
        # Multi-layered radial furnace turbine behind ArmorPlate_Chest
        C.add_cyl("PanzerCoreOuterFlange", 0.084 * scale, 0.036 * scale, s((0.0, 0.146, 1.27)), (math.radians(90), 0, 0), vertices=12, mat=m["panzer_armor"], bevel=0.0),
        C.add_cyl("PanzerChestCoreRing", 0.068 * scale, 0.044 * scale, s((0.0, 0.148, 1.27)), (math.radians(90), 0, 0), vertices=12, mat=m["brass"], bevel=0.0),
        C.add_cyl("PanzerChestCoreGlow", 0.054 * scale, 0.038 * scale, s((0.0, 0.146, 1.27)), (math.radians(90), 0, 0), vertices=12, mat=m["magma"], bevel=0.0),
        C.add_cyl("PanzerCoreHub", 0.020 * scale, 0.048 * scale, s((0.0, 0.158, 1.27)), (math.radians(90), 0, 0), vertices=10, mat=m["panzer_armor"], bevel=0.0),
        # Twin Back Fuel/Thruster Tanks + Weathered Hazard Bands + Exhaust Nozzles
        C.add_cyl("FuelTankL", 0.088 * scale, 0.44 * scale, s((-0.115, -0.215, 1.24)), vertices=12, mat=m["tank_metal"], bevel=0.0),
        C.add_cyl("FuelTankR", 0.088 * scale, 0.44 * scale, s((0.115, -0.215, 1.24)), vertices=12, mat=m["tank_metal"], bevel=0.0),
        C.add_cyl("FuelBandL", 0.092 * scale, 0.045 * scale, s((-0.115, -0.215, 1.32)), vertices=12, mat=m["hazard_metal"], bevel=0.0),
        C.add_cyl("FuelBandR", 0.092 * scale, 0.045 * scale, s((0.115, -0.215, 1.32)), vertices=12, mat=m["hazard_metal"], bevel=0.0),
        C.add_cone("ThrusterBellL", 0.072 * scale, 0.042 * scale, 0.10 * scale, s((-0.115, -0.220, 0.97)), (math.radians(168), 0, 0), vertices=12, mat=m["panzer_armor"]),
        C.add_cone("ThrusterBellR", 0.072 * scale, 0.042 * scale, 0.10 * scale, s((0.115, -0.220, 0.97)), (math.radians(168), 0, 0), vertices=12, mat=m["panzer_armor"]),
        C.add_box("BackManifold", s((0.28, 0.10, 0.14)), s((0.0, -0.195, 1.26)), mat=m["panzer_armor"], bevel=0.012 * scale),
        C.add_box("BackVentGlow", s((0.10, 0.03, 0.06)), s((0.0, -0.245, 1.26)), mat=m["magma"], bevel=0.0),
    ]
    for vi in range(3):
        ang = math.radians(vi * 60.0 + 30.0)
        torso_parts.append(C.add_box(f"PanzerTurbineVane_{vi}", s((0.013, 0.022, 0.112)), s((0.0, 0.162, 1.27)), (0, ang, 0), mat=m["panzer_armor"], bevel=0.0))
    for rx in (-0.062, 0.062):
        for rz in (1.208, 1.332):
            torso_parts.append(C.add_cyl(f"CoreRivet_{rx:.2f}_{rz:.2f}", 0.008 * scale, 0.018 * scale, s((rx, 0.168, rz)), (math.radians(90), 0, 0), vertices=6, mat=m["brass"], bevel=0.0))

    torso_acc = C.join_objects(torso_parts, "PanzerTorsoPack", apply_uv=False)
    CC.bind_accessory_to_bones(torso_acc, rig, lambda x, y, z: {"spine_03": 0.55, "spine_02": 0.45} if z > 1.12 else {"pelvis": 0.65, "spine_01": 0.35}, scale=scale, keep_existing_uv=True)

    # --- Articulated Armored Upper Arm Sleeves & Elbows (continuous mech arms!) ---
    arm_bridge_objs = []
    for side, sfx in (("L", "l"), ("R", "r")):
        _, _, ua_len = CC.bone_frame(rig, f"upperarm_{sfx}", along_t=0.5)
        ua_sleeve = C.add_cyl(f"PanzerUpperArm_{side}", 0.068 * scale, ua_len * 0.78, (0, 0, 0), vertices=12, mat=m["panzer_trim"], bevel=0.0)
        CC.transform_along_bone(ua_sleeve, rig, f"upperarm_{sfx}", along_t=0.54)
        CC.bind_accessory_to_bones(ua_sleeve, rig, f"upperarm_{sfx}", scale=scale, keep_existing_uv=True)

        elb_pos, _, _ = CC.bone_frame(rig, f"lowerarm_{sfx}", along_t=0.0)
        elb_joint = C.add_sphere(f"PanzerElbow_{side}", 0.066 * scale, (1.0, 1.0, 1.0), elb_pos, segments=10, rings=8, mat=m["brass"])
        CC.bind_accessory_to_bones(elb_joint, rig, {f"upperarm_{sfx}": 0.48, f"lowerarm_{sfx}": 0.52}, scale=scale, keep_existing_uv=True)
        arm_bridge_objs.extend([ua_sleeve, elb_joint])

    # --- Left Arm: Coaxial Bone-Aligned Hydraulic Pincer Claw ---
    _, _, la_l_len = CC.bone_frame(rig, "lowerarm_l", along_t=0.5)
    claw_housing = C.add_cyl("ClawHousing", 0.066 * scale, la_l_len * 0.88, (0, 0, 0), vertices=12, mat=m["panzer_armor"], bevel=0.0)
    CC.transform_along_bone(claw_housing, rig, "lowerarm_l", along_t=0.52)
    claw_band = C.add_cyl("ClawBand", 0.072 * scale, 0.036 * scale, (0, 0, 0), vertices=12, mat=m["hazard_metal"], bevel=0.0)
    CC.transform_along_bone(claw_band, rig, "lowerarm_l", along_t=0.72)
    claw_forearm = C.join_objects([claw_housing, claw_band], "PanzerClawForearm", apply_uv=False)
    CC.bind_accessory_to_bones(claw_forearm, rig, {"lowerarm_l": 0.90, "upperarm_l": 0.10}, scale=scale, keep_existing_uv=True)

    hand_l_parts = []
    claw_wrist = C.add_cyl("ClawWrist", 0.056 * scale, 0.088 * scale, (0, 0, 0), vertices=12, mat=m["brass"], bevel=0.0)
    CC.transform_along_bone(claw_wrist, rig, "hand_l", along_t=0.25)
    claw_hub = C.add_box("ClawHub", (0.105 * scale, 0.088 * scale, 0.074 * scale), (0, 0, 0), mat=m["panzer_trim"], bevel=0.008 * scale)
    CC.transform_along_bone(claw_hub, rig, "hand_l", along_t=1.0, local_offset=(0.0, 0.0, 0.025 * scale))
    hand_l_parts.extend([claw_wrist, claw_hub])
    for ci, (ox, oy) in enumerate(((-0.044, 0.024), (0.044, 0.024), (0.0, -0.040))):
        p0 = Vector((ox * scale, oy * scale, 0.03 * scale))
        p1 = Vector((ox * 1.32 * scale, oy * 1.25 * scale, 0.145 * scale))
        p2 = Vector((ox * 0.28 * scale, oy * 0.25 * scale, 0.255 * scale))
        blade = C.add_tube_pipe(
            f"PincerBlade_{ci}", [p0, p1, p2],
            radius=0.014 * scale, segments=6,
            radii=[0.017 * scale, 0.013 * scale, 0.0035 * scale],
            mat=m["chrome"],
        )
        CC.transform_along_bone(blade, rig, "hand_l", along_t=1.0)
        hand_l_parts.append(blade)
    claw_hand = C.join_objects(hand_l_parts, "PanzerClawHand", apply_uv=False)
    CC.bind_accessory_to_bones(claw_hand, rig, {"hand_l": 0.88, "lowerarm_l": 0.12}, scale=scale, keep_existing_uv=True)

    # --- Right Arm: Coaxial Bone-Aligned Armored Flamethrower + Vented Shroud + Hollow Barrel + Hose ---
    _, _, la_r_len = CC.bone_frame(rig, "lowerarm_r", along_t=0.5)
    flame_gauntlet = C.add_box("FlameGauntlet", (0.116 * scale, 0.120 * scale, la_r_len * 0.86), (0, 0, 0), mat=m["panzer_armor"], bevel=0.012 * scale)
    CC.transform_along_bone(flame_gauntlet, rig, "lowerarm_r", along_t=0.50)
    flame_tank_u = C.add_cyl("FlameTankUnder", 0.045 * scale, 0.25 * scale, (0, 0, 0), vertices=12, mat=m["tank_metal"], bevel=0.0)
    CC.transform_along_bone(flame_tank_u, rig, "lowerarm_r", along_t=0.72, local_offset=(0.0, -0.068 * scale, 0.04 * scale))
    flame_forearm = C.join_objects([flame_gauntlet, flame_tank_u], "PanzerFlameForearm", apply_uv=False)
    CC.bind_accessory_to_bones(flame_forearm, rig, {"lowerarm_r": 0.88, "hand_r": 0.12}, scale=scale, keep_existing_uv=True)

    # Note add_vented_shroud & add_hollow_barrel orient along local +Y -> local_rot_deg=(90, 0, 0) maps +Y onto +Z (arm axis!)
    flame_shroud = C.add_vented_shroud("FlameShroud", r_outer=0.042 * scale, thickness=0.007 * scale, length=0.30 * scale, bands=6, struts=6, mat=m["panzer_trim"], segs=12)
    CC.transform_along_bone(flame_shroud, rig, "hand_r", along_t=1.0, local_offset=(0.0, 0.012 * scale, 0.12 * scale), local_rot_deg=(90, 0, 0))
    flame_nozzle = C.add_hollow_barrel("FlameNozzle", r_outer=0.030 * scale, r_inner=0.019 * scale, length=0.36 * scale, segments=10, mat=m["brass"], bore_mat=m["magma"])
    CC.transform_along_bone(flame_nozzle, rig, "hand_r", along_t=1.0, local_offset=(0.0, 0.012 * scale, 0.15 * scale), local_rot_deg=(90, 0, 0))
    flame_pilot = C.add_sphere("FlamePilotGlow", 0.019 * scale, (1.0, 1.0, 1.3), (0, 0, 0), segments=8, rings=6, mat=m["visor_glow"])
    CC.transform_along_bone(flame_pilot, rig, "hand_r", along_t=1.0, local_offset=(0.0, -0.022 * scale, 0.315 * scale))
    flame_barrel = C.join_objects([flame_shroud, flame_nozzle, flame_pilot], "PanzerFlameBarrel", apply_uv=False)
    CC.bind_accessory_to_bones(flame_barrel, rig, {"hand_r": 0.88, "lowerarm_r": 0.12}, scale=scale, keep_existing_uv=True)

    # Fuel hose connecting back manifold -> right elbow -> under-barrel fuel tank
    uarm_mid, _, _ = CC.bone_frame(rig, "upperarm_r", along_t=0.65)
    elb_pos_r, m_larm_r, _ = CC.bone_frame(rig, "lowerarm_r", along_t=0.0)
    tank_inlet, _, _ = CC.bone_frame(rig, "lowerarm_r", along_t=0.45)
    hose_p0 = Vector(s((0.12, -0.20, 1.16)))
    hose_p1 = uarm_mid + Vector((0.02 * scale, -0.08 * scale, -0.02 * scale))
    hose_p2 = elb_pos_r + Vector((0.03 * scale, -0.06 * scale, -0.03 * scale))
    hose_p3 = tank_inlet + (m_larm_r.to_3x3() @ Vector((0.0, -0.072 * scale, 0.0)))
    flame_hose = C.add_tube_pipe("FlameFuelHose", [hose_p0, hose_p1, hose_p2, hose_p3], radius=0.017 * scale, segments=8, mat=m["rubber"])
    def hose_bw(x, y, z):
        if y < -0.06:
            return {"spine_02": 0.80, "upperarm_r": 0.20}
        if y < 0.04:
            return {"upperarm_r": 0.55, "lowerarm_r": 0.45}
        return {"lowerarm_r": 0.90, "hand_r": 0.10}
    CC.bind_accessory_to_bones(flame_hose, rig, hose_bw, scale=scale, keep_existing_uv=True)

    # --- Diving Helmet + Dark Recessed Inner Faceplate + Twin Fiery Glowing Eyes ---
    diving_helm = _import_cc0_diving_helmet(m, rig, scale)
    visor_cowl = C.add_sphere("Helmet_InnerCowl", 1.0, s((0.095, 0.088, 0.095)), s((0.0, 0.105, 1.635)), segments=12, rings=8, mat=m["socket_dark"])
    visor_eye_l = C.add_sphere("Helmet_EyeL", 1.0, s((0.024, 0.018, 0.015)), s((-0.042, 0.172, 1.646)), (0, 0, math.radians(-14)), segments=10, rings=8, mat=m["visor_glow"])
    visor_eye_r = C.add_sphere("Helmet_EyeR", 1.0, s((0.024, 0.018, 0.015)), s((0.042, 0.172, 1.646)), (0, 0, math.radians(14)), segments=10, rings=8, mat=m["visor_glow"])
    visor_slit = C.add_box("Helmet_VisorSlit", s((0.105, 0.018, 0.014)), s((0.0, 0.168, 1.646)), mat=m["magma"], bevel=0.003 * scale)
    visor_core = C.join_objects([visor_cowl, visor_eye_l, visor_eye_r, visor_slit], "Helmet_VisorGlow", apply_uv=False)
    CC.bind_accessory_to_bones(visor_core, rig, "Head", scale=scale, keep_existing_uv=True)

    # Join core non-breakable body/armature parts into Panzer_Body so hierarchy stays clean
    core_objs = [o for o in [
        body, suit, torso_acc,
        claw_forearm, claw_hand, flame_forearm, flame_barrel, flame_hose,
        diving_helm, visor_core,
    ] + arm_bridge_objs + leg_objs if o is not None]
    for o in core_objs:
        o.parent = None
        for mod in list(o.modifiers):
            if mod.type == "ARMATURE":
                o.modifiers.remove(mod)
    bpy.ops.object.select_all(action="DESELECT")
    for o in core_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = core_objs[0]
    bpy.ops.object.join()
    panzer_body = bpy.context.active_object
    panzer_body.name = "Panzer_Body"
    C.smooth_shade(panzer_body, 54.0)
    mod = panzer_body.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    panzer_body.parent = rig

    # --- 4 SEPARATE Breakable Armor Plate Nodes (skinned to same Armature!) ---
    plate_chest = C.join_objects([
        C.add_box("PlateChestMain", s((0.34, 0.088, 0.21)), s((0.0, 0.156, 1.305)), (math.radians(-10), 0, 0), mat=m["panzer_armor"], bevel=0.020 * scale),
        C.add_box("PlateChestLower", s((0.30, 0.082, 0.125)), s((0.0, 0.146, 1.155)), (math.radians(14), 0, 0), mat=m["panzer_armor"], bevel=0.016 * scale),
        C.add_box("PlateChestCollar", s((0.28, 0.068, 0.054)), s((0.0, 0.142, 1.418)), (math.radians(-24), 0, 0), mat=m["panzer_trim"], bevel=0.010 * scale),
        C.add_box("PlateChestTrim", s((0.27, 0.026, 0.044)), s((0.0, 0.196, 1.365)), (math.radians(-10), 0, 0), mat=m["hazard_metal"], bevel=0.004 * scale),
        C.add_box("PlateChestRibL", s((0.036, 0.034, 0.23)), s((-0.105, 0.192, 1.245)), (math.radians(-6), 0, math.radians(-8)), mat=m["brass"], bevel=0.004 * scale),
        C.add_box("PlateChestRibR", s((0.036, 0.034, 0.23)), s((0.105, 0.192, 1.245)), (math.radians(-6), 0, math.radians(8)), mat=m["brass"], bevel=0.004 * scale),
    ], "ArmorPlate_Chest", apply_uv=False)
    CC.bind_accessory_to_bones(plate_chest, rig, {"spine_03": 0.55, "spine_02": 0.45}, scale=scale, keep_existing_uv=True)

    sh_l_orig, _, _ = CC.bone_frame(rig, "upperarm_l", along_t=0.14)
    plate_sh_l = C.join_objects([
        C.add_sphere("PauldL", 0.118 * scale, (0.95, 1.15, 1.06), sh_l_orig + Vector((-0.028 * scale, 0.0, 0.035 * scale)), (0, math.radians(-26), 0), segments=14, rings=8, mat=m["panzer_armor"]),
        C.add_cone("SpikeL", 0.022 * scale, 0.004 * scale, 0.08 * scale, sh_l_orig + Vector((-0.120 * scale, 0.0, 0.110 * scale)), (0, math.radians(-52), 0), vertices=8, mat=m["brass"]),
    ], "ArmorPlate_Shoulder_L", apply_uv=False)
    CC.bind_accessory_to_bones(plate_sh_l, rig, {"upperarm_l": 0.72, "clavicle_l": 0.28}, scale=scale, keep_existing_uv=True)

    sh_r_orig, _, _ = CC.bone_frame(rig, "upperarm_r", along_t=0.14)
    plate_sh_r = C.join_objects([
        C.add_sphere("PauldR", 0.118 * scale, (0.95, 1.15, 1.06), sh_r_orig + Vector((0.028 * scale, 0.0, 0.035 * scale)), (0, math.radians(26), 0), segments=14, rings=8, mat=m["panzer_armor"]),
        C.add_cone("SpikeR", 0.022 * scale, 0.004 * scale, 0.08 * scale, sh_r_orig + Vector((0.120 * scale, 0.0, 0.110 * scale)), (0, math.radians(52), 0), vertices=8, mat=m["brass"]),
    ], "ArmorPlate_Shoulder_R", apply_uv=False)
    CC.bind_accessory_to_bones(plate_sh_r, rig, {"upperarm_r": 0.72, "clavicle_r": 0.28}, scale=scale, keep_existing_uv=True)

    # Helmet Visor Grille Shield (hugs viewport with narrow glowing slit; shatters off to expose blazing visor eyes!)
    visor_plate = C.join_objects([
        C.add_box("VisorTop", s((0.17, 0.042, 0.052)), s((0.0, 0.198, 1.695)), (math.radians(-12), 0, 0), mat=m["panzer_armor"], bevel=0.008 * scale),
        C.add_box("VisorBot", s((0.17, 0.042, 0.052)), s((0.0, 0.198, 1.600)), (math.radians(12), 0, 0), mat=m["panzer_armor"], bevel=0.008 * scale),
        C.add_box("VisorBarL", s((0.026, 0.044, 0.145)), s((-0.072, 0.196, 1.648)), (0, 0, math.radians(-14)), mat=m["brass"], bevel=0.004 * scale),
        C.add_box("VisorBarC", s((0.020, 0.044, 0.145)), s((0.0, 0.204, 1.648)), mat=m["brass"], bevel=0.004 * scale),
        C.add_box("VisorBarR", s((0.026, 0.044, 0.145)), s((0.072, 0.196, 1.648)), (0, 0, math.radians(14)), mat=m["brass"], bevel=0.004 * scale),
    ], "Helmet_VisorPlate", apply_uv=False)
    CC.bind_accessory_to_bones(visor_plate, rig, "Head", scale=scale, keep_existing_uv=True)

    _add_panzer_animations(rig, scale=scale)
    mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = sum(len(p.vertices) - 2 for obj in mesh_objs for p in obj.data.polygons)
    print(f"[CHARS] panzer_boss tris={tris}, parts={[o.name for o in mesh_objs]}")
    C.export_asset("characters", "panzer_boss", export_anims=True)


def build_all():
    m = CC.build_char_materials()
    build_hellhound(m)
    build_panzer_boss(m)


if __name__ == "__main__":
    build_all()
