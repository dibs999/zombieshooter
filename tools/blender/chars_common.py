"""Shared MPFB2, CC0 texture, clothing shell, dismemberment split, and animation helpers
for BUNKER 115 Stream B characters.

Coordinate convention:
- Blender: +Y Forward, +X Right (anatomical left of character is -X? Wait: let's match MPFB rotated 180° around Z:
  upperarm_l at X = -0.17, upperarm_r at X = +0.17, face looking toward +Y, +Z Up).
- Exported glTF (export_yup=True): -Z Forward, +Y Up.
- Bone rotation helper converts Armature-space XYZ Euler deltas cleanly into each MPFB2 bone's rest frame.
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C

TEX_CHARS = os.path.join(C.TEX_DIR, "characters")
CACHE_DIR = "/tmp/cc0_cache/chars"
EYES_MHCLO = os.path.join(CACHE_DIR, "eyes", "low-poly.mhclo")
MPFB_TARGETS = "/home/antigravity/.config/blender/4.2/extensions/user_default/mpfb/data/targets"

ARM_L_BONES = {
    "upperarm_l", "lowerarm_l", "hand_l",
    "index_01_l", "index_02_l", "index_03_l",
    "middle_01_l", "middle_02_l", "middle_03_l",
    "pinky_01_l", "pinky_02_l", "pinky_03_l",
    "ring_01_l", "ring_02_l", "ring_03_l",
    "thumb_01_l", "thumb_02_l", "thumb_03_l",
}
ARM_R_BONES = {b[:-2] + "_r" for b in ARM_L_BONES}
LEG_BONES = {"thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"}
HEAD_BONES = {"Head", "head", "neck_01"}
FINGER_BONE_PREFIXES = ("index", "middle", "ring", "pinky", "thumb")
FINGER_BONES = {
    f"{p}_0{i}_{sfx}"
    for p in FINGER_BONE_PREFIXES
    for i in (1, 2, 3)
    for sfx in ("l", "r")
}
CLAW_HAND_POSES = {
    "index_01_l": (28, 0, 0), "index_02_l": (35, 0, 0),
    "middle_01_l": (32, 0, 0), "middle_02_l": (38, 0, 0),
    "ring_01_l": (36, 0, 0), "ring_02_l": (42, 0, 0),
    "pinky_01_l": (40, 0, 0), "pinky_02_l": (45, 0, 0),
    "index_01_r": (28, 0, 0), "index_02_r": (35, 0, 0),
    "middle_01_r": (32, 0, 0), "middle_02_r": (38, 0, 0),
    "ring_01_r": (36, 0, 0), "ring_02_r": (42, 0, 0),
    "pinky_01_r": (40, 0, 0), "pinky_02_r": (45, 0, 0),
}


def _ensure_mpfb():
    import addon_utils
    addon_utils.enable("bl_ext.user_default.mpfb", default_set=True)
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    return HumanService, TargetService


def make_char_pbr_mat(
    name,
    base_color=(0.5, 0.5, 0.5, 1.0),
    metallic=0.0,
    roughness=0.55,
    emission=None,
    emission_strength=0.0,
    albedo_tex=None,
    normal_tex=None,
    roughness_tex=None,
    emission_tex=None,
    tint_tex=None,
    normal_strength=0.72,
    alpha=1.0,
):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bc = C.srgb_to_linear_col(base_color)
    bsdf.inputs["Base Color"].default_value = bc
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 0.999:
        mat.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = alpha

    if albedo_tex and os.path.exists(albedo_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(albedo_tex, check_existing=True)
        if tint_tex is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            tc = C.srgb_to_linear_col(tint_tex[:3])
            mix.inputs["B"].default_value = (*tc, 1.0)
            nt.links.new(tex.outputs["Color"], mix.inputs["A"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if roughness_tex and os.path.exists(roughness_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(roughness_tex, check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])

    if normal_tex and os.path.exists(normal_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(normal_tex, check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal_strength
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if emission_tex and os.path.exists(emission_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(emission_tex, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = max(0.01, emission_strength)
    elif emission is not None and emission_strength > 0.0:
        ec = C.srgb_to_linear_col(emission[:3])
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def _pbr_set(name, prefix, metallic=0.0, roughness=0.6, normal_strength=0.72, emission_strength=0.0, tint_tex=None, has_emission=False):
    def _tex(suffix):
        jp = os.path.join(TEX_CHARS, f"{prefix}_{suffix}.jpg")
        return jp if os.path.exists(jp) else os.path.join(TEX_CHARS, f"{prefix}_{suffix}.png")

    return make_char_pbr_mat(
        name,
        metallic=metallic,
        roughness=roughness,
        albedo_tex=_tex("albedo"),
        normal_tex=_tex("normal"),
        roughness_tex=_tex("roughness"),
        emission_tex=_tex("emission") if has_emission else None,
        emission_strength=emission_strength,
        normal_strength=normal_strength,
        tint_tex=tint_tex,
    )


def build_char_materials():
    def _eye_tex(cname, kind):
        jp = os.path.join(TEX_CHARS, f"zombie_eye_{cname}_{kind}.jpg")
        return jp if os.path.exists(jp) else os.path.join(TEX_CHARS, f"zombie_eye_{cname}_{kind}.png")

    return {
        "skin_soldier": _pbr_set("SkinSoldier", "zombie_skin_soldier", roughness=0.62, normal_strength=0.85),
        "skin_scientist": _pbr_set("SkinScientist", "zombie_skin_scientist", roughness=0.58, normal_strength=0.82),
        "skin_brute": _pbr_set("SkinBrute", "zombie_skin_brute", roughness=0.64, normal_strength=0.88),
        "skin_worker": _pbr_set("SkinWorker", "zombie_skin_worker", roughness=0.64, normal_strength=0.85),

        "eye_amber": make_char_pbr_mat(
            "ZombieEyeAmber", roughness=0.08,
            albedo_tex=_eye_tex("amber", "albedo"),
            emission_tex=_eye_tex("amber", "emission"),
            emission_strength=3.0,
        ),
        "eye_orange": make_char_pbr_mat(
            "ZombieEyeOrange", roughness=0.08,
            albedo_tex=_eye_tex("orange", "albedo"),
            emission_tex=_eye_tex("orange", "emission"),
            emission_strength=3.4,
        ),

        "uniform_soldier": _pbr_set("UniformSoldier", "uniform_soldier", roughness=0.90, normal_strength=0.78),
        "pants_soldier": _pbr_set("PantsSoldier", "uniform_soldier", roughness=0.92, normal_strength=0.72, tint_tex=(0.76, 0.78, 0.74)),
        "labcoat_scientist": _pbr_set("LabcoatScientist", "labcoat_scientist", roughness=0.86, normal_strength=0.72),
        "jumpsuit_scientist": _pbr_set("JumpsuitScientist", "uniform_soldier", roughness=0.90, normal_strength=0.65, tint_tex=(0.54, 0.58, 0.54)),
        "overalls_worker": _pbr_set("OverallsWorker", "overalls_worker", roughness=0.88, normal_strength=0.76),
        "hazmat_brute": _pbr_set("HazmatBrute", "hazmat_brute", roughness=0.88, normal_strength=0.78),
        "panzer_suit": _pbr_set("PanzerSuit", "panzer_suit", roughness=0.80, normal_strength=0.76),

        "leather": _pbr_set("CharLeather", "leather_gear", roughness=0.64, normal_strength=0.68),
        "stahlhelm": _pbr_set("StahlhelmSteel", "stahlhelm_steel", metallic=0.44, roughness=0.58, normal_strength=0.72),
        "panzer_armor": _pbr_set("PanzerArmor", "panzer_armor", metallic=0.76, roughness=0.44, normal_strength=0.82),
        "panzer_trim": _pbr_set("PanzerTrim", "stahlhelm_steel", metallic=0.72, roughness=0.48, normal_strength=0.70, tint_tex=(0.76, 0.78, 0.80)),
        "tank_metal": _pbr_set("TankMetal", "panzer_armor", metallic=0.70, roughness=0.50, normal_strength=0.75, tint_tex=(0.70, 0.76, 0.66)),
        "hazard_metal": _pbr_set("HazardMetal", "hazard_metal", metallic=0.68, roughness=0.46, normal_strength=0.80),
        "hazard_yellow": make_char_pbr_mat("HazardYellow", (0.30, 0.20, 0.04, 1.0), metallic=0.22, roughness=0.58),

        "hellhound_hide": _pbr_set("HellhoundHide", "hellhound_hide", roughness=0.76, normal_strength=0.92, emission_strength=2.15, has_emission=True),
        "zombie_hair": _pbr_set("ZombieHair", "zombie_hair", roughness=0.92, normal_strength=0.95),
        "gore_flesh": _pbr_set("GoreFlesh", "gore_flesh", roughness=0.22, normal_strength=0.85),
        "bone": make_char_pbr_mat("ExposedBone", (0.54, 0.44, 0.32, 1.0), roughness=0.58),
        "teeth": make_char_pbr_mat("ZombieTeeth", (0.36, 0.30, 0.20, 1.0), roughness=0.58),
        "dark_hair": make_char_pbr_mat("DarkHair", (0.05, 0.045, 0.04, 1.0), roughness=0.92),
        "rubber": make_char_pbr_mat("DarkRubber", (0.05, 0.055, 0.06, 1.0), metallic=0.06, roughness=0.78),
        "brass": make_char_pbr_mat("WeatheredBrass", (0.46, 0.32, 0.12, 1.0), metallic=0.82, roughness=0.38),
        "chrome": make_char_pbr_mat("DullSteel", (0.54, 0.56, 0.58, 1.0), metallic=0.84, roughness=0.34),
        "goggle_lens": make_char_pbr_mat("GoggleLens", (0.07, 0.14, 0.18, 1.0), metallic=0.35, roughness=0.10, emission=(0.03, 0.09, 0.12), emission_strength=0.22),
        "visor_glow": make_char_pbr_mat("VisorGlowOrange", (1.0, 0.36, 0.04, 1.0), roughness=0.10, emission=(1.0, 0.34, 0.03), emission_strength=3.0),
        "hound_eye": make_char_pbr_mat("HoundEyeCore", (1.0, 0.28, 0.02, 1.0), roughness=0.06, emission=(1.0, 0.26, 0.02), emission_strength=2.3),
        "magma": make_char_pbr_mat("MoltenMagma", (1.0, 0.30, 0.02, 1.0), roughness=0.18, emission=(1.0, 0.28, 0.02), emission_strength=2.5),
        "hound_bone": make_char_pbr_mat("HoundCharredBone", (0.24, 0.16, 0.12, 1.0), roughness=0.68),
        "socket_dark": make_char_pbr_mat("SocketDark", (0.02, 0.015, 0.015, 1.0), roughness=0.95),
    }


def rotate_verts_around(obj, pivot, deg_xyz):
    """Rotate mesh vertices in-place around an explicit pivot point (never world origin)."""
    piv = Vector(pivot)
    rot_m = Euler(tuple(math.radians(a) for a in deg_xyz), "XYZ").to_matrix()
    for v in obj.data.vertices:
        v.co = piv + rot_m @ (v.co - piv)
    obj.data.update()


def bone_frame(rig_obj, bone_name, along_t=0.5):
    """Return (origin_pos, Matrix4x4 mapping local +Z along bone head->tail and +Y forward, length)."""
    b = rig_obj.data.bones[bone_name]
    h = b.head_local.copy()
    t = b.tail_local.copy()
    d = t - h
    length = max(1e-5, d.length)
    z_ax = d.normalized()
    ref = Vector((0.0, 1.0, 0.0)) if abs(z_ax.y) < 0.92 else Vector((0.0, 0.0, 1.0))
    x_ax = ref.cross(z_ax).normalized()
    y_ax = z_ax.cross(x_ax).normalized()
    if y_ax.y < 0.0 and abs(z_ax.y) < 0.90:
        x_ax = -x_ax
        y_ax = -y_ax
    origin = h.lerp(t, along_t)
    m = Matrix((
        (x_ax.x, y_ax.x, z_ax.x, origin.x),
        (x_ax.y, y_ax.y, z_ax.y, origin.y),
        (x_ax.z, y_ax.z, z_ax.z, origin.z),
        (0.0, 0.0, 0.0, 1.0),
    ))
    return origin, m, length


def transform_along_bone(obj, rig_obj, bone_name, along_t=0.5, local_offset=(0.0, 0.0, 0.0), local_rot_deg=(0.0, 0.0, 0.0)):
    """Apply pending modifiers/xforms and place canonical object into bone's exact head->tail frame."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        if mod.type != "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    _, m_frame, _ = bone_frame(rig_obj, bone_name, along_t=along_t)
    m_off = Matrix.Translation(Vector(local_offset)) @ Euler(tuple(math.radians(a) for a in local_rot_deg), "XYZ").to_matrix().to_4x4()
    obj.data.transform(m_frame @ m_off)
    obj.data.update()
    return obj


def bake_shape_keys(obj):
    if obj.data.shape_keys is None:
        return
    sk = obj.shape_key_add(name="__baked__", from_mix=True)
    for kb in list(obj.data.shape_keys.key_blocks):
        if kb != sk:
            obj.shape_key_remove(kb)
    obj.shape_key_remove(sk)


def _delete_helper_geometry(bm_obj):
    vg_names = {vg.name: vg.index for vg in bm_obj.vertex_groups}
    bad_idxs = {vg_names[n] for n in ("HelperGeometry", "JointCubes") if n in vg_names}
    if not bad_idxs:
        return
    bm = bmesh.new()
    bm.from_mesh(bm_obj.data)
    d_lay = bm.verts.layers.deform.active
    if d_lay is not None:
        del_verts = [v for v in bm.verts if any(idx in v[d_lay] for idx in bad_idxs)]
        bmesh.ops.delete(bm, geom=del_verts, context="VERTS")
    bm.to_mesh(bm_obj.data)
    bm.free()
    for n in ("HelperGeometry", "JointCubes"):
        if n in bm_obj.vertex_groups:
            bm_obj.vertex_groups.remove(bm_obj.vertex_groups[n])


def _apply_xform(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def _merge_finger_weights_and_strip_bones(bm_obj, rig_obj, bake_claw=True):
    """Optionally bake CLAW_HAND_POSES into rest mesh, merge all finger weights into hand_l/hand_r, and strip 30 finger bones (53 -> 23)."""
    if bake_claw:
        arm_bake = bm_obj.modifiers.new("ArmatureBake", "ARMATURE")
        arm_bake.object = rig_obj

        bpy.ops.object.select_all(action="DESELECT")
        rig_obj.select_set(True)
        bpy.context.view_layer.objects.active = rig_obj
        bpy.ops.object.mode_set(mode="POSE")
        for pb in rig_obj.pose.bones:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
        for bn, degs in CLAW_HAND_POSES.items():
            _pose_bone_world_rot(rig_obj, bn, degs)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()

        bpy.ops.object.select_all(action="DESELECT")
        bm_obj.select_set(True)
        bpy.context.view_layer.objects.active = bm_obj
        bpy.ops.object.modifier_apply(modifier=arm_bake.name)

        bpy.ops.object.select_all(action="DESELECT")
        rig_obj.select_set(True)
        bpy.context.view_layer.objects.active = rig_obj
        bpy.ops.object.mode_set(mode="POSE")
        for pb in rig_obj.pose.bones:
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()

    if "hand_l" not in bm_obj.vertex_groups:
        bm_obj.vertex_groups.new(name="hand_l")
    if "hand_r" not in bm_obj.vertex_groups:
        bm_obj.vertex_groups.new(name="hand_r")

    hand_l_idx = bm_obj.vertex_groups["hand_l"].index
    hand_r_idx = bm_obj.vertex_groups["hand_r"].index
    finger_l_idxs = {bm_obj.vertex_groups[bn].index for bn in FINGER_BONES if bn.endswith("_l") and bn in bm_obj.vertex_groups}
    finger_r_idxs = {bm_obj.vertex_groups[bn].index for bn in FINGER_BONES if bn.endswith("_r") and bn in bm_obj.vertex_groups}

    if finger_l_idxs or finger_r_idxs:
        bm = bmesh.new()
        bm.from_mesh(bm_obj.data)
        d_lay = bm.verts.layers.deform.active
        if d_lay is not None:
            for v in bm.verts:
                deform = v[d_lay]
                add_l = 0.0
                for idx in finger_l_idxs:
                    if idx in deform:
                        add_l += deform[idx]
                        del deform[idx]
                if add_l > 0.0:
                    deform[hand_l_idx] = deform.get(hand_l_idx, 0.0) + add_l

                add_r = 0.0
                for idx in finger_r_idxs:
                    if idx in deform:
                        add_r += deform[idx]
                        del deform[idx]
                if add_r > 0.0:
                    deform[hand_r_idx] = deform.get(hand_r_idx, 0.0) + add_r
        bm.to_mesh(bm_obj.data)
        bm.free()
        bm_obj.data.update()

    for bn in FINGER_BONES:
        if bn in bm_obj.vertex_groups:
            bm_obj.vertex_groups.remove(bm_obj.vertex_groups[bn])

    bpy.ops.object.select_all(action="DESELECT")
    rig_obj.select_set(True)
    bpy.context.view_layer.objects.active = rig_obj
    bpy.ops.object.mode_set(mode="EDIT")
    for bn in list(FINGER_BONES):
        eb = rig_obj.data.edit_bones.get(bn)
        if eb is not None:
            rig_obj.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode="OBJECT")


def create_mpfb_zombie_base(
    variant,
    scale=1.0,
    age=0.68,
    muscle=0.52,
    weight=0.22,
    height=0.50,
    skin_mat=None,
    eye_mat=None,
    boot_sole=0.022,
    decimate_ratio=0.50,
    target_overrides=None,
    bake_claw=True,
):
    HumanService, TargetService = _ensure_mpfb()
    macro = TargetService.get_default_macro_info_dict()
    macro.update({
        "gender": 1.0,
        "age": age,
        "muscle": muscle,
        "weight": weight,
        "height": height,
        "proportions": 0.52,
    })
    bm_obj = HumanService.create_human(
        mask_helpers=False,
        detailed_helpers=True,
        feet_on_ground=False,
        macro_detail_dict=macro,
    )

    targets = {
        "chin/chin-jaw-drop-incr.target.gz": 0.62,
        "eyebrows/eyebrows-angle-down.target.gz": 0.85,
        "cheek/l-cheek-volume-decr.target.gz": 0.85,
        "cheek/r-cheek-volume-decr.target.gz": 0.85,
        "expression/units/caucasian/mouth-open.target.gz": 0.72,
        "expression/units/caucasian/eye-left-opened-up.target.gz": 0.75,
        "expression/units/caucasian/eye-right-opened-up.target.gz": 0.75,
        "expression/units/caucasian/neck-platysma.target.gz": 0.80,
        "expression/units/caucasian/nose-left-elevation.target.gz": 0.45,
        "expression/units/caucasian/nose-right-elevation.target.gz": 0.45,
    }
    if target_overrides:
        targets.update(target_overrides)

    for rel, wt in targets.items():
        tp = os.path.join(MPFB_TARGETS, rel)
        if os.path.exists(tp):
            TargetService.load_target(bm_obj, tp, weight=wt)

    bake_shape_keys(bm_obj)

    rig = HumanService.add_builtin_rig(bm_obj, "game_engine", import_weights=True)
    eyes = HumanService.add_mhclo_asset(EYES_MHCLO, bm_obj, asset_type="Eyes")
    bake_shape_keys(eyes)

    # Unparent and clear temporary Armature modifier before transforming and deleting helpers
    for o in (bm_obj, eyes):
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
        for mod in list(o.modifiers):
            if mod.type == "ARMATURE":
                o.modifiers.remove(mod)

    _delete_helper_geometry(bm_obj)
    for mod in list(bm_obj.modifiers):
        bm_obj.modifiers.remove(mod)
    min_z = min(v.co.z for v in bm_obj.data.vertices)
    dz = -min_z + boot_sole

    # Step 1: Rotate +Y forward and shift feet cleanly to Z = boot_sole at scale=1
    for o in (rig, bm_obj, eyes):
        o.location = (0.0, 0.0, dz)
        o.rotation_euler = (0.0, 0.0, math.pi)
    bpy.context.view_layer.update()
    _apply_xform([rig, bm_obj, eyes])

    # Step 2: Uniform scale around world origin (0, 0, 0)
    if abs(scale - 1.0) > 1e-5:
        for o in (rig, bm_obj, eyes):
            o.scale = (scale, scale, scale)
        bpy.context.view_layer.update()
        _apply_xform([rig, bm_obj, eyes])

    # Step 3: Rename head -> Head cleanly for zombie_ai.gd / test_runner.gd contract
    if "head" in rig.data.bones:
        rig.data.bones["head"].name = "Head"
    if "head" in bm_obj.vertex_groups:
        bm_obj.vertex_groups["head"].name = "Head"
    rig.name = f"Zombie_{variant}_Armature"
    rig.data.name = f"Zombie_{variant}_ArmData"

    # Step 4: Decimate body (after helpers removed and before baking claw/stripping finger bones)
    if decimate_ratio < 0.99:
        bpy.ops.object.select_all(action="DESELECT")
        bm_obj.select_set(True)
        bpy.context.view_layer.objects.active = bm_obj
        dec = bm_obj.modifiers.new("Decimate", "DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.ratio = decimate_ratio
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)

    _merge_finger_weights_and_strip_bones(bm_obj, rig, bake_claw=bake_claw)

    if skin_mat:
        C.assign_mat(bm_obj, skin_mat)
    C.smooth_shade(bm_obj, 62.0)

    # Step 5: Configure eyeballs to follow Head bone cleanly
    eyes.vertex_groups.clear()
    vg_e = eyes.vertex_groups.new(name="Head")
    vg_e.add([v.index for v in eyes.data.vertices], 1.0, "REPLACE")
    if eye_mat:
        C.assign_mat(eyes, eye_mat)
    C.smooth_shade(eyes, 65.0)

    for o in (bm_obj, eyes):
        mod = o.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        o.parent = rig

    return rig, bm_obj, eyes


def make_tailored_garment(
    body_obj,
    rig_obj,
    name,
    mat,
    keep_face_fn,
    hole_fn=None,
    offset=0.0085,
    thickness=0.0045,
    uv_scale=2.4,
    wrinkle_amp=0.0028,
    scale=1.0,
):
    """Clone decimated MPFB body with exact 53-bone weights into a layered torn cloth shell."""
    mesh_copy = body_obj.data.copy()
    mesh_copy.name = name + "_Mesh"
    obj = bpy.data.objects.new(name, mesh_copy)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # Copy vertex group definitions matching body_obj
    for vg in body_obj.vertex_groups:
        if vg.name not in obj.vertex_groups:
            obj.vertex_groups.new(name=vg.name)

    vg_by_idx = {vg.index: vg.name for vg in obj.vertex_groups}
    inv_s = 1.0 / max(1e-5, scale)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    d_lay = bm.verts.layers.deform.active

    del_faces = []
    for f in bm.faces:
        c = f.calc_center_median()
        cx, cy, cz = c.x * inv_s, c.y * inv_s, c.z * inv_s
        weights = {}
        if d_lay is not None:
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    gn = vg_by_idx.get(gi, "")
                    if gn:
                        weights[gn] = weights.get(gn, 0.0) + gw * 0.3333
        if not keep_face_fn(cx, cy, cz, weights):
            del_faces.append(f)
        elif hole_fn is not None and hole_fn(cx, cy, cz, weights):
            del_faces.append(f)

    if del_faces:
        bmesh.ops.delete(bm, geom=del_faces, context="FACES")

    loose_verts = [v for v in bm.verts if not v.link_faces]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

    # Prune isolated protruding boundary triangle spikes and relax jagged sawtooth edges
    for _ in range(2):
        spikes = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary) >= 2]
        if not spikes or len(spikes) >= len(bm.faces):
            break
        bmesh.ops.delete(bm, geom=spikes, context="FACES")
        lv = [v for v in bm.verts if not v.link_faces]
        if lv:
            bmesh.ops.delete(bm, geom=lv, context="VERTS")

    for _ in range(2):
        deltas = {}
        for v in bm.verts:
            if v.is_boundary:
                nb = [e.other_vert(v).co for e in v.link_edges if e.is_boundary]
                if len(nb) >= 2:
                    avg = sum(nb, Vector((0.0, 0.0, 0.0))) / float(len(nb))
                    deltas[v] = (avg - v.co) * 0.42
        for v, d in deltas.items():
            v.co += d

    if len(bm.faces) == 0:
        bm.free()
        bpy.data.objects.remove(obj, do_unlink=True)
        return None

    bm.normal_update()
    for v in bm.verts:
        vx, vy, vz = v.co.x * inv_s, v.co.y * inv_s, v.co.z * inv_s
        wr = wrinkle_amp * (math.sin(vx * 36.0 + vz * 24.0) * math.cos(vy * 31.0 - vz * 19.0))
        v.co += v.normal * ((offset + wr) * scale)

    bm.to_mesh(obj.data)
    bm.free()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if thickness > 0.0005:
        sol = obj.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = thickness * scale
        sol.offset = 1.0
        sol.use_rim = True
        bpy.ops.object.modifier_apply(modifier=sol.name)

    C.uv_box_project(obj, scale=uv_scale)
    C.smooth_shade(obj, 52.0)

    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig_obj
    obj.parent = rig_obj
    return obj


def cull_body_faces(body_obj, scale, cull_fn):
    """Remove strictly occluded inner human body triangles using face center + bone weights."""
    vg_by_idx = {vg.index: vg.name for vg in body_obj.vertex_groups}
    inv_s = 1.0 / max(1e-5, scale)

    bm = bmesh.new()
    bm.from_mesh(body_obj.data)
    d_lay = bm.verts.layers.deform.active

    del_faces = []
    for f in bm.faces:
        c = f.calc_center_median()
        cx, cy, cz = c.x * inv_s, c.y * inv_s, c.z * inv_s
        weights = {}
        if d_lay is not None:
            inv_n = 1.0 / max(1, len(f.verts))
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    gn = vg_by_idx.get(gi, "")
                    if gn:
                        weights[gn] = weights.get(gn, 0.0) + gw * inv_n
        if cull_fn(cx, cy, cz, weights):
            del_faces.append(f)

    if del_faces and len(del_faces) < len(bm.faces):
        bmesh.ops.delete(bm, geom=del_faces, context="FACES")
        lv = [v for v in bm.verts if not v.link_faces]
        if lv:
            bmesh.ops.delete(bm, geom=lv, context="VERTS")
        bm.to_mesh(body_obj.data)
        body_obj.data.update()
    bm.free()


def bind_accessory_to_bones(obj, rig_obj, weight_spec, scale=1.0, keep_existing_uv=False):
    """Apply non-armature mods + transforms, project UVs if desired, paint weights, bind to rig."""
    if obj is None:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        if mod.type != "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if not keep_existing_uv:
        C.uv_box_project(obj, scale=2.5)

    obj.vertex_groups.clear()
    if isinstance(weight_spec, str):
        vg = obj.vertex_groups.new(name=weight_spec)
        vg.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")
    elif isinstance(weight_spec, dict):
        tot = sum(max(0.0, w) for w in weight_spec.values())
        all_v = [v.index for v in obj.data.vertices]
        for bn, w in weight_spec.items():
            wn = max(0.0, w) / max(1e-6, tot)
            if wn > 0.005:
                vg = obj.vertex_groups.new(name=bn)
                vg.add(all_v, wn, "REPLACE")
    else:
        inv_s = 1.0 / max(1e-5, scale)
        groups = {}
        for v in obj.data.vertices:
            wd = weight_spec(v.co.x * inv_s, v.co.y * inv_s, v.co.z * inv_s)
            tot = sum(max(0.0, w) for w in wd.values())
            if tot <= 1e-6:
                continue
            for bn, w in wd.items():
                wn = max(0.0, w) / tot
                if wn > 0.005:
                    if bn not in groups:
                        groups[bn] = obj.vertex_groups.new(name=bn)
                    groups[bn].add([v.index], wn, "REPLACE")

    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig_obj
    obj.parent = rig_obj
    return obj


def _make_stump_cap(name, loc, rot_deg, radii, bone_name, gore_mat, bone_mat, rig_obj, scale=1.0):
    rx, ry = radii[0] * scale, radii[1] * scale
    loc_s = (loc[0] * scale, loc[1] * scale, loc[2] * scale)
    rot_r = tuple(math.radians(a) for a in rot_deg)
    flesh = C.add_sphere(name + "_Flesh", 1.0, (rx, ry, rx * 0.72), loc_s, rot_r, segments=12, rings=8, mat=gore_mat)
    # Protruding severed bone tip inside bloody meat
    bone_tip = C.add_cyl(name + "_Bone", rx * 0.34, rx * 1.45, loc_s, rot_r, vertices=10, mat=bone_mat, bevel=0.002 * scale)
    # Offset bone tip slightly outward along cap's local Z
    rot_m = Euler(rot_r, "XYZ").to_matrix()
    bone_tip.location = Vector(loc_s) + rot_m @ Vector((0.0, 0.0, rx * 0.36))
    stump = C.join_objects([flesh, bone_tip], name, apply_uv=False)
    bind_accessory_to_bones(stump, rig_obj, bone_name, scale=scale)
    return stump


def split_dismemberment_parts(
    rig_obj,
    skinned_objs,
    gore_mat,
    bone_mat,
    scale=1.0,
    z_neck_cut=1.45,
    skip_legs=False,
    include_stumps=True,
):
    """Join skinned objects safely and split into removable dismemberment parts:
    Mesh_Head, Mesh_Arm_L, Mesh_Arm_R, Mesh_Legs (unless skip_legs), Mesh_Torso,
    plus Stump_Head, Stump_Arm_L, Stump_Arm_R, Stump_Legs bound to the same Armature.
    """
    valid = [o for o in skinned_objs if o is not None and o.type == "MESH"]
    # Temporarily remove Armature modifiers before joining, then extract parts by face region
    for o in valid:
        o.parent = None
        for mod in list(o.modifiers):
            if mod.type == "ARMATURE":
                o.modifiers.remove(mod)

    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    if len(valid) > 1:
        bpy.ops.object.join()
    master = bpy.context.active_object
    master.name = "MasterJoined"

    vg_names = {vg.index: vg.name for vg in master.vertex_groups}
    inv_s = 1.0 / max(1e-5, scale)

    bm = bmesh.new()
    bm.from_mesh(master.data)
    d_lay = bm.verts.layers.deform.active

    face_region = {}
    for f in bm.faces:
        c = f.calc_center_median()
        cz = c.z * inv_s
        w_head = w_al = w_ar = w_leg = 0.0
        if d_lay is not None:
            inv_n = 1.0 / max(1, len(f.verts))
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    bn = vg_names.get(gi, "")
                    if bn in HEAD_BONES:
                        w_head += gw * inv_n
                    elif bn in ARM_L_BONES:
                        w_al += gw * inv_n
                    elif bn in ARM_R_BONES:
                        w_ar += gw * inv_n
                    elif bn in LEG_BONES:
                        w_leg += gw * inv_n
        if w_head >= 0.42 and cz >= z_neck_cut - 0.06:
            face_region[f.index] = "Head"
        elif w_al >= 0.42:
            face_region[f.index] = "Arm_L"
        elif w_ar >= 0.42:
            face_region[f.index] = "Arm_R"
        elif w_leg >= 0.45:
            face_region[f.index] = "Legs"
        else:
            face_region[f.index] = "Torso"
    bm.free()

    target_regions = ["Head", "Arm_L", "Arm_R", "Torso"] + ([] if skip_legs else ["Legs"])
    out_parts = {}

    for reg in target_regions:
        keep_idxs = {fi for fi, r in face_region.items() if r == reg}
        if not keep_idxs:
            continue
        mesh_c = master.data.copy()
        obj_r = bpy.data.objects.new(f"Mesh_{reg}", mesh_c)
        bpy.context.collection.objects.link(obj_r)
        for vg in master.vertex_groups:
            if vg.name not in obj_r.vertex_groups:
                obj_r.vertex_groups.new(name=vg.name)

        bm_r = bmesh.new()
        bm_r.from_mesh(obj_r.data)
        del_f = [f for f in bm_r.faces if f.index not in keep_idxs]
        if del_f:
            bmesh.ops.delete(bm_r, geom=del_f, context="FACES")
        lv = [v for v in bm_r.verts if not v.link_faces]
        if lv:
            bmesh.ops.delete(bm_r, geom=lv, context="VERTS")
        bm_r.to_mesh(obj_r.data)
        bm_r.free()

        C.smooth_shade(obj_r, 56.0)
        mod = obj_r.modifiers.new("Armature", "ARMATURE")
        mod.object = rig_obj
        obj_r.parent = rig_obj
        out_parts[reg] = obj_r

    bpy.data.objects.remove(master, do_unlink=True)

    if include_stumps:
        out_parts["Stump_Head"] = _make_stump_cap("Stump_Head", (0.0, 0.015, 1.45), (0, 0, 0), (0.056, 0.058), "neck_01", gore_mat, bone_mat, rig_obj, scale=scale)
        out_parts["Stump_Arm_L"] = _make_stump_cap("Stump_Arm_L", (-0.175, 0.015, 1.35), (0, -78, 0), (0.052, 0.052), "clavicle_l", gore_mat, bone_mat, rig_obj, scale=scale)
        out_parts["Stump_Arm_R"] = _make_stump_cap("Stump_Arm_R", (0.175, 0.015, 1.35), (0, 78, 0), (0.052, 0.052), "clavicle_r", gore_mat, bone_mat, rig_obj, scale=scale)
        out_parts["Stump_Legs"] = C.join_objects([
            _make_stump_cap("Stump_Leg_TmpL", (-0.102, 0.005, 0.865), (180, 0, 0), (0.064, 0.064), "pelvis", gore_mat, bone_mat, rig_obj, scale=scale),
            _make_stump_cap("Stump_Leg_TmpR", (0.102, 0.005, 0.865), (180, 0, 0), (0.064, 0.064), "pelvis", gore_mat, bone_mat, rig_obj, scale=scale),
        ], "Stump_Legs", apply_uv=False)
        bind_accessory_to_bones(out_parts["Stump_Legs"], rig_obj, "pelvis", scale=scale)

    return out_parts


# ---------------------------------------------------------------------------
# World-Space -> MPFB Bone-Local NLA Animation Authoring
# ---------------------------------------------------------------------------

def _pose_bone_world_rot(rig_obj, bone_name, deg_xyz):
    if bone_name not in rig_obj.pose.bones:
        return
    pb = rig_obj.pose.bones[bone_name]
    pb.rotation_mode = "XYZ"
    m_rest = rig_obj.data.bones[bone_name].matrix_local.to_3x3()
    r_world = Euler(tuple(math.radians(a) for a in deg_xyz), "XYZ").to_matrix()
    r_local = m_rest.inverted() @ r_world @ m_rest
    pb.rotation_euler = r_local.to_euler("XYZ")


def _pose_bone_world_loc(rig_obj, bone_name, world_delta, scale=1.0):
    if bone_name not in rig_obj.pose.bones:
        return
    pb = rig_obj.pose.bones[bone_name]
    m_rest = rig_obj.data.bones[bone_name].matrix_local.to_3x3()
    pb.location = m_rest.inverted() @ (Vector(world_delta) * scale)


def add_zombie_nla_animations(rig_obj, scale=1.0, is_crawler=False):
    if not rig_obj.animation_data:
        rig_obj.animation_data_create()
    bpy.ops.object.select_all(action="DESELECT")
    rig_obj.select_set(True)
    bpy.context.view_layer.objects.active = rig_obj
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig_obj.pose.bones:
        pb.rotation_mode = "XYZ"

    def make_action(name, frame_poses):
        act = bpy.data.actions.new(name=name)
        act.use_fake_user = True
        rig_obj.animation_data.action = act
        for frame, poses in frame_poses.items():
            for pb in rig_obj.pose.bones:
                pb.rotation_euler = (0.0, 0.0, 0.0)
                pb.location = (0.0, 0.0, 0.0)
            for bname, vals in poses.items():
                if "rot" in vals:
                    _pose_bone_world_rot(rig_obj, bname, vals["rot"])
                if "loc" in vals:
                    _pose_bone_world_loc(rig_obj, bname, vals["loc"], scale=scale)
            for pb in rig_obj.pose.bones:
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)
                pb.keyframe_insert(data_path="location", frame=frame)
        track = rig_obj.animation_data.nla_tracks.new()
        track.name = name
        end_f = max(frame_poses.keys())
        strip = track.strips.new(name, 1, act)
        strip.action_frame_start = 1
        strip.action_frame_end = end_f
        rig_obj.animation_data.action = None

    make_action("Idle", {
        1: {
            "pelvis": {"rot": (-4, 0, 2)},
            "spine_01": {"rot": (-6, 0, -2)}, "spine_02": {"rot": (-8, -3, 2)}, "spine_03": {"rot": (-6, 2, 0)},
            "neck_01": {"rot": (-4, 4, -8)}, "Head": {"rot": (12, -10, 6)},
            "upperarm_l": {"rot": (44, 6, -6)}, "lowerarm_l": {"rot": (34, 0, 4)},
            "upperarm_r": {"rot": (32, -6, 6)}, "lowerarm_r": {"rot": (28, 0, -4)},
            "thigh_l": {"rot": (6, 0, -2)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-4, 0, 2)}, "calf_r": {"rot": (-8, 0, 0)},
        },
        25: {
            "pelvis": {"rot": (-2, 0, -2)},
            "spine_01": {"rot": (-8, 0, 3)}, "spine_02": {"rot": (-10, 3, -2)}, "spine_03": {"rot": (-8, -2, 0)},
            "neck_01": {"rot": (-6, -4, 8)}, "Head": {"rot": (16, 12, -8)},
            "upperarm_l": {"rot": (52, 8, -4)}, "lowerarm_l": {"rot": (38, 0, 4)},
            "upperarm_r": {"rot": (42, -8, 4)}, "lowerarm_r": {"rot": (34, 0, -4)},
            "thigh_l": {"rot": (8, 0, -2)}, "calf_l": {"rot": (-12, 0, 0)},
            "thigh_r": {"rot": (-2, 0, 2)}, "calf_r": {"rot": (-10, 0, 0)},
        },
        49: {
            "pelvis": {"rot": (-4, 0, 2)},
            "spine_01": {"rot": (-6, 0, -2)}, "spine_02": {"rot": (-8, -3, 2)}, "spine_03": {"rot": (-6, 2, 0)},
            "neck_01": {"rot": (-4, 4, -8)}, "Head": {"rot": (12, -10, 6)},
            "upperarm_l": {"rot": (44, 6, -6)}, "lowerarm_l": {"rot": (34, 0, 4)},
            "upperarm_r": {"rot": (32, -6, 6)}, "lowerarm_r": {"rot": (28, 0, -4)},
            "thigh_l": {"rot": (6, 0, -2)}, "calf_l": {"rot": (-10, 0, 0)},
            "thigh_r": {"rot": (-4, 0, 2)}, "calf_r": {"rot": (-8, 0, 0)},
        },
    })

    # Classic CoD Zombies shambling gait: hunched torso, twisted broken-neck stare, reaching arms, heavy limp stride
    walk_f1 = {
        "pelvis": {"loc": (0.0, 0.0, -0.025), "rot": (-6, -5, 6)},
        "spine_01": {"rot": (-8, 2, -4)}, "spine_02": {"rot": (-9, 4, -4)}, "spine_03": {"rot": (-6, 0, 4)},
        "neck_01": {"rot": (-4, 8, -10)}, "Head": {"rot": (14, -14, 10)},
        "upperarm_l": {"rot": (76, 8, -4)}, "lowerarm_l": {"rot": (26, 0, 8)},
        "upperarm_r": {"rot": (90, -10, 4)}, "lowerarm_r": {"rot": (22, 0, -8)},
        "thigh_l": {"rot": (26, 0, 0)}, "calf_l": {"rot": (-26, 0, 0)}, "foot_l": {"rot": (8, 0, 0)},
        "thigh_r": {"rot": (-22, 0, 0)}, "calf_r": {"rot": (-14, 0, 0)}, "foot_r": {"rot": (-6, 0, 0)},
    }
    walk_f17 = {
        "pelvis": {"loc": (0.0, 0.0, 0.015), "rot": (-4, 5, -6)},
        "spine_01": {"rot": (-10, -2, 4)}, "spine_02": {"rot": (-10, -4, 4)}, "spine_03": {"rot": (-6, 0, -4)},
        "neck_01": {"rot": (-4, -8, 10)}, "Head": {"rot": (16, 10, -10)},
        "upperarm_l": {"rot": (92, 10, -4)}, "lowerarm_l": {"rot": (24, 0, 6)},
        "upperarm_r": {"rot": (72, -8, 4)}, "lowerarm_r": {"rot": (28, 0, -6)},
        "thigh_l": {"rot": (-20, 0, 0)}, "calf_l": {"rot": (-14, 0, 0)}, "foot_l": {"rot": (-6, 0, 0)},
        "thigh_r": {"rot": (24, 0, 0)}, "calf_r": {"rot": (-28, 0, 0)}, "foot_r": {"rot": (10, 0, 0)},
    }
    make_action("Walk", {1: walk_f1, 17: walk_f17, 33: walk_f1})

    # Aggressive CoD sprinter: deep forward lean, pumping claw hands
    run_f1 = {
        "pelvis": {"loc": (0.0, 0.0, -0.055), "rot": (-12, -6, 8)},
        "spine_01": {"rot": (-10, 0, -5)}, "spine_02": {"rot": (-10, 0, -5)}, "spine_03": {"rot": (-6, 0, 4)},
        "neck_01": {"rot": (4, 0, 0)}, "Head": {"rot": (22, -6, 6)},
        "upperarm_l": {"rot": (98, 12, -8)}, "lowerarm_l": {"rot": (38, 0, 6)},
        "upperarm_r": {"rot": (66, -12, 8)}, "lowerarm_r": {"rot": (42, 0, -6)},
        "thigh_l": {"rot": (46, 0, 0)}, "calf_l": {"rot": (-48, 0, 0)}, "foot_l": {"rot": (12, 0, 0)},
        "thigh_r": {"rot": (-38, 0, 0)}, "calf_r": {"rot": (-22, 0, 0)}, "foot_r": {"rot": (-12, 0, 0)},
    }
    run_f10 = {
        "pelvis": {"loc": (0.0, 0.0, 0.02), "rot": (-12, 6, -8)},
        "spine_01": {"rot": (-10, 0, 5)}, "spine_02": {"rot": (-10, 0, 5)}, "spine_03": {"rot": (-6, 0, -4)},
        "neck_01": {"rot": (4, 0, 0)}, "Head": {"rot": (22, 6, -6)},
        "upperarm_l": {"rot": (66, 12, -8)}, "lowerarm_l": {"rot": (42, 0, 6)},
        "upperarm_r": {"rot": (98, -12, 8)}, "lowerarm_r": {"rot": (38, 0, -6)},
        "thigh_l": {"rot": (-38, 0, 0)}, "calf_l": {"rot": (-22, 0, 0)}, "foot_l": {"rot": (-12, 0, 0)},
        "thigh_r": {"rot": (46, 0, 0)}, "calf_r": {"rot": (-48, 0, 0)}, "foot_r": {"rot": (12, 0, 0)},
    }
    make_action("Run", {1: run_f1, 10: run_f10, 19: run_f1})

    # Aggressive two-handed / right-claw swipe lunge
    make_action("Attack", {
        1: {"spine_02": {"rot": (6, 0, -8)}, "spine_03": {"rot": (4, 0, -6)}, "upperarm_l": {"rot": (118, 18, -12)}, "lowerarm_l": {"rot": (26, 0, 0)}, "upperarm_r": {"rot": (124, -18, 12)}, "lowerarm_r": {"rot": (24, 0, 0)}},
        9: {"pelvis": {"loc": (0, 0.05, -0.03), "rot": (-10, 0, 10)}, "spine_02": {"rot": (-18, 0, 10)}, "spine_03": {"rot": (-12, 0, 8)}, "Head": {"rot": (22, 0, 0)},
            "upperarm_l": {"rot": (52, -16, 12)}, "lowerarm_l": {"rot": (42, 0, -10)},
            "upperarm_r": {"rot": (46, 16, -12)}, "lowerarm_r": {"rot": (46, 0, 10)}},
        19: {"spine_02": {"rot": (-10, 0, 0)}, "upperarm_l": {"rot": (82, 6, -4)}, "upperarm_r": {"rot": (82, -6, 4)}},
    })

    # Window plank ripping animation
    make_action("Tear", {
        1: {"spine_02": {"rot": (-12, 0, 0)}, "upperarm_l": {"rot": (118, 14, -10)}, "lowerarm_l": {"rot": (20, 0, 0)}, "upperarm_r": {"rot": (122, -14, 10)}, "lowerarm_r": {"rot": (22, 0, 0)}},
        10: {"pelvis": {"rot": (8, 0, -8)}, "spine_02": {"rot": (10, 0, -6)}, "Head": {"rot": (-10, 8, 0)}, "upperarm_l": {"rot": (62, 18, -16)}, "lowerarm_l": {"rot": (58, 0, 0)}, "upperarm_r": {"rot": (92, -8, 6)}, "lowerarm_r": {"rot": (42, 0, 0)}},
        20: {"spine_02": {"rot": (-10, 0, 4)}, "upperarm_l": {"rot": (108, 12, -8)}, "upperarm_r": {"rot": (110, -12, 8)}},
    })

    # Climbing over window sill
    make_action("Vault", {
        1: {"pelvis": {"loc": (0, 0, 0.08), "rot": (-16, 0, 0)}, "spine_02": {"rot": (-16, 0, 0)}, "upperarm_l": {"rot": (105, 10, 0)}, "upperarm_r": {"rot": (105, -10, 0)}, "thigh_l": {"rot": (68, 0, 0)}, "calf_l": {"rot": (-82, 0, 0)}, "thigh_r": {"rot": (20, 0, 0)}, "calf_r": {"rot": (-28, 0, 0)}},
        11: {"pelvis": {"loc": (0, 0.05, 0.16), "rot": (-28, 0, 0)}, "spine_02": {"rot": (-14, 0, 0)}, "Head": {"rot": (24, 0, 0)}, "upperarm_l": {"rot": (74, 8, -8)}, "upperarm_r": {"rot": (74, -8, 8)}, "thigh_l": {"rot": (35, 0, 0)}, "calf_l": {"rot": (-45, 0, 0)}, "thigh_r": {"rot": (62, 0, 0)}, "calf_r": {"rot": (-78, 0, 0)}},
        21: {"pelvis": {"loc": (0, 0, 0), "rot": (-8, 0, 0)}, "spine_02": {"rot": (-12, 0, 0)}, "upperarm_l": {"rot": (78, 6, -6)}, "upperarm_r": {"rot": (78, -6, 6)}},
    })

    # Stagger Hit flinch
    make_action("Hit", {
        1: {"spine_02": {"rot": (-10, 0, 0)}},
        6: {"pelvis": {"loc": (0, -0.05, -0.02), "rot": (14, 0, -10)}, "spine_02": {"rot": (22, 8, -10)}, "neck_01": {"rot": (12, 0, 0)}, "Head": {"rot": (20, -14, 0)}, "upperarm_l": {"rot": (52, 22, -28)}, "upperarm_r": {"rot": (44, -22, 28)}},
        16: {"spine_02": {"rot": (-10, 0, 0)}, "upperarm_l": {"rot": (76, 6, -6)}, "upperarm_r": {"rot": (76, -6, 6)}},
    })

    # Prone Belly Crawl (flat horizontal torso hovering cleanly at Z=0.14..0.28, alternating hands dragging along ground!)
    crawl_f1 = {
        "pelvis": {"loc": (0.0, 0.0, -0.715), "rot": (-86, 0, -6)},
        "spine_01": {"rot": (2, 0, 3)}, "spine_02": {"rot": (2, 0, 5)}, "spine_03": {"rot": (4, 0, 4)},
        "neck_01": {"rot": (28, 0, 0)}, "Head": {"rot": (34, -8, 6)},
        "upperarm_l": {"rot": (156, 18, -14)}, "lowerarm_l": {"rot": (24, 0, 8)},
        "upperarm_r": {"rot": (128, -20, 16)}, "lowerarm_r": {"rot": (46, 0, -10)},
    }
    crawl_f15 = {
        "pelvis": {"loc": (0.0, 0.0, -0.715), "rot": (-86, 0, 6)},
        "spine_01": {"rot": (2, 0, -3)}, "spine_02": {"rot": (2, 0, -5)}, "spine_03": {"rot": (4, 0, -4)},
        "neck_01": {"rot": (28, 0, 0)}, "Head": {"rot": (34, 8, -6)},
        "upperarm_l": {"rot": (128, 20, -16)}, "lowerarm_l": {"rot": (46, 0, 10)},
        "upperarm_r": {"rot": (156, -18, 14)}, "lowerarm_r": {"rot": (24, 0, -8)},
    }
    make_action("Crawl", {1: crawl_f1, 15: crawl_f15, 29: crawl_f1})

    # Collapse Backwards + Death alias
    death_back = {
        1: {"pelvis": {"loc": (0, 0, 0), "rot": (0, 0, 0)}, "spine_02": {"rot": (-8, 0, 0)}},
        11: {"pelvis": {"loc": (0, -0.22, -0.34), "rot": (44, 0, 8)}, "spine_02": {"rot": (16, 0, 0)}, "Head": {"rot": (18, 10, 0)}, "upperarm_l": {"rot": (48, 22, -32)}, "upperarm_r": {"rot": (54, -22, 32)}, "thigh_l": {"rot": (18, 0, 0)}, "calf_l": {"rot": (-32, 0, 0)}, "thigh_r": {"rot": (14, 0, 0)}, "calf_r": {"rot": (-25, 0, 0)}},
        24: {"pelvis": {"loc": (0, -0.52, -0.78), "rot": (88, 0, 12)}, "spine_02": {"rot": (6, 0, 0)}, "Head": {"rot": (8, 14, 0)}, "upperarm_l": {"rot": (18, 42, -55)}, "upperarm_r": {"rot": (22, -42, 50)}, "thigh_l": {"rot": (-8, 0, -8)}, "calf_l": {"rot": (-6, 0, 0)}, "thigh_r": {"rot": (-10, 0, 10)}, "calf_r": {"rot": (-6, 0, 0)}},
    }
    make_action("DeathBack", death_back)
    make_action("Death", death_back)

    # Collapse Forward (headshot / chest collapse)
    make_action("DeathFwd", {
        1: {"pelvis": {"loc": (0, 0, 0), "rot": (0, 0, 0)}, "spine_02": {"rot": (-10, 0, 0)}},
        11: {"pelvis": {"loc": (0, 0.18, -0.38), "rot": (-46, 0, -6)}, "spine_02": {"rot": (-18, 0, 0)}, "Head": {"rot": (-12, -10, 0)}, "upperarm_l": {"rot": (32, 24, -22)}, "upperarm_r": {"rot": (38, -24, 24)}, "thigh_l": {"rot": (-14, 0, 0)}, "calf_l": {"rot": (-62, 0, 0)}, "thigh_r": {"rot": (-10, 0, 0)}, "calf_r": {"rot": (-54, 0, 0)}},
        24: {"pelvis": {"loc": (0, 0.46, -0.78), "rot": (-86, 0, -8)}, "spine_02": {"rot": (-6, 0, 0)}, "Head": {"rot": (12, -16, 0)}, "upperarm_l": {"rot": (142, 30, -35)}, "upperarm_r": {"rot": (132, -30, 35)}, "thigh_l": {"rot": (-4, 0, -6)}, "calf_l": {"rot": (-10, 0, 0)}, "thigh_r": {"rot": (-4, 0, 6)}, "calf_r": {"rot": (-8, 0, 0)}},
    })

    bpy.ops.object.mode_set(mode="OBJECT")
