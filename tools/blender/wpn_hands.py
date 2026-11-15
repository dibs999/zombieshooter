"""Build anatomical CC0 MPFB2 first-person forearms, wool sleeves & stitched leather gloves.

Outputs:
  assets/models/weapons/fp_right_hand.glb (+ assets_src/blend/weapons/fp_right_hand.blend)
  assets/models/weapons/fp_left_hand.glb  (+ assets_src/blend/weapons/fp_left_hand.blend)

Coordinate convention (matches gen_weapons.py & Godot weapon_controller.gd):
  Blender +Y = forward toward muzzle (exports to Godot -Z)
  Blender +Z = up (exports to Godot +Y)
  Blender +X = right (exports to Godot +X)
Origin (0, 0, 0) = grip center (R palm wrapped on pistol/rifle grip; L palm cupped under forend).
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C
import chars_common as CC


def hand_materials():
    wtex = os.path.join(C.TEX_DIR, "weapons")
    skin = C.make_pbr_mat(
        "FPSkin",
        (0.54, 0.38, 0.30, 1.0),
        metallic=0.0,
        roughness=0.56,
        albedo_tex=os.path.join(wtex, "fp_skin_albedo.jpg"),
        normal_tex=os.path.join(wtex, "fp_skin_normal.jpg"),
        roughness_tex=os.path.join(wtex, "fp_skin_roughness.jpg"),
        tint_tex=(0.96, 0.90, 0.85),
        normal_strength=0.45,
    )
    leather = C.make_pbr_mat(
        "TacticalLeather",
        (0.20, 0.16, 0.12, 1.0),
        metallic=0.04,
        roughness=0.58,
        albedo_tex=os.path.join(wtex, "fp_leather_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_leather_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_leather_roughness.png"),
        tint_tex=(0.78, 0.74, 0.70),
        normal_strength=0.45,
    )
    leather_dark = C.make_pbr_mat(
        "GloveReinforceLeather",
        (0.11, 0.09, 0.075, 1.0),
        metallic=0.05,
        roughness=0.50,
        albedo_tex=os.path.join(wtex, "fp_leather_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_leather_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_leather_roughness.png"),
        tint_tex=(0.48, 0.44, 0.42),
        normal_strength=0.52,
    )
    sleeve_wool = C.make_pbr_mat(
        "SleeveWool",
        (0.18, 0.21, 0.15, 1.0),
        metallic=0.0,
        roughness=0.90,
        albedo_tex=os.path.join(wtex, "fp_sleeve_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_sleeve_normal.png"),
        roughness_tex=os.path.join(wtex, "fp_sleeve_roughness.png"),
        tint_tex=(0.68, 0.72, 0.60),
        normal_strength=0.58,
    )
    cuff_cloth = C.make_pbr_mat(
        "KnitCuff",
        (0.12, 0.13, 0.10, 1.0),
        metallic=0.0,
        roughness=0.88,
        albedo_tex=os.path.join(wtex, "fp_sleeve_albedo.png"),
        normal_tex=os.path.join(wtex, "fp_sleeve_normal.png"),
        tint_tex=(0.48, 0.50, 0.44),
        normal_strength=0.52,
    )
    watch_steel = C.make_pbr_mat(
        "WatchSteel",
        (0.28, 0.30, 0.32, 1.0),
        metallic=0.88,
        roughness=0.28,
        albedo_tex=os.path.join(wtex, "gun_steel_albedo.png"),
        normal_tex=os.path.join(wtex, "gun_steel_normal.png"),
        normal_strength=0.25,
    )
    watch_face = C.make_pbr_mat(
        "WatchDial",
        (0.015, 0.022, 0.018, 1.0),
        metallic=0.12,
        roughness=0.26,
        emission=(0.03, 0.12, 0.06),
        emission_strength=0.06,
    )
    watch_tritium = C.make_pbr_mat(
        "WatchTritium",
        (0.24, 0.88, 0.42, 1.0),
        metallic=0.0,
        roughness=0.30,
        emission=(0.24, 0.92, 0.44),
        emission_strength=0.95,
    )
    brass_rivet = C.make_pbr_mat(
        "GloveBrass",
        (0.50, 0.36, 0.15, 1.0),
        metallic=0.86,
        roughness=0.32,
        albedo_tex=os.path.join(wtex, "brass_albedo.png"),
    )
    return locals()


def _create_base_human():
    """Spawn MPFB2 athletic soldier human rotated so +Y is forward and +X is anatomical right."""
    C.reset_scene()
    HumanService, TargetService = CC._ensure_mpfb()
    macro = TargetService.get_default_macro_info_dict()
    macro.update({
        "gender": 1.0,
        "age": 0.42,
        "muscle": 0.62,
        "weight": 0.28,
        "height": 0.56,
        "proportions": 0.54,
    })
    bm_obj = HumanService.create_human(
        mask_helpers=False,
        detailed_helpers=False,
        feet_on_ground=False,
        macro_detail_dict=macro,
    )
    CC.bake_shape_keys(bm_obj)
    rig = HumanService.add_builtin_rig(bm_obj, "game_engine", import_weights=True)

    bm_obj.parent = None
    for mod in list(bm_obj.modifiers):
        bm_obj.modifiers.remove(mod)
    CC._delete_helper_geometry(bm_obj)

    for o in (rig, bm_obj):
        o.rotation_euler = (0.0, 0.0, math.pi)
    bpy.context.view_layer.update()
    CC._apply_xform([rig, bm_obj])

    mod = bm_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    bm_obj.parent = rig
    return rig, bm_obj


def _pose_bone_armature_rot(rig, bone_name, world_rot_mat_3x3):
    pb = rig.pose.bones.get(bone_name)
    if pb is None:
        return
    pb.rotation_mode = "QUATERNION"
    cur_arm = pb.matrix.to_3x3().normalized()
    target_arm = (world_rot_mat_3x3 @ cur_arm).normalized()
    parent_arm = pb.parent.matrix.to_3x3().normalized() if pb.parent else Matrix.Identity(3)
    rest_local = pb.bone.matrix_local.to_3x3()
    parent_rest = pb.parent.bone.matrix_local.to_3x3() if pb.parent else Matrix.Identity(3)
    rel_rest = parent_rest.inverted() @ rest_local
    pb_local = (parent_arm @ rel_rest).inverted() @ target_arm
    pb.rotation_quaternion = pb_local.to_quaternion()


def _aim_bone_vec(rig, bone_name, target_dir):
    pb = rig.pose.bones.get(bone_name)
    if pb is None:
        return
    cur_vec = (pb.tail - pb.head).normalized()
    tgt = Vector(target_dir).normalized()
    if cur_vec.length > 1e-5 and tgt.length > 1e-5:
        q = cur_vec.rotation_difference(tgt)
        _pose_bone_armature_rot(rig, bone_name, q.to_matrix())
        bpy.context.view_layer.update()


def _orthonormal_frame(fwd: Vector, up_hint: Vector, right_hand_axis: bool = True):
    """Build guaranteed det=+1 (X, Y, Z) orthonormal matrix with Y=fwd, Z=up_orth, X=Y x Z (or Z x Y)."""
    y = fwd.normalized()
    z = (up_hint - y * up_hint.dot(y)).normalized()
    x = y.cross(z).normalized()
    # Notice x, y, z satisfies x = y x z => det(x, y, z) == +1!
    return Matrix((x, y, z)).transposed()


def _curl_finger_toward(rig, bones, target_inward: Vector, angles_deg):
    """Curl each phalanx toward target_inward using v_seg x target_inward (zero sign ambiguity!)."""
    tgt = target_inward.normalized()
    for bn, deg in zip(bones, angles_deg):
        pb = rig.pose.bones.get(bn)
        if pb is None:
            continue
        v_seg = (pb.tail - pb.head).normalized()
        ax = v_seg.cross(tgt)
        if ax.length < 1e-4:
            continue
        ax.normalize()
        q = Quaternion(ax, math.radians(deg))
        _pose_bone_armature_rot(rig, bn, q.to_matrix())
        bpy.context.view_layer.update()


def _freeze_and_isolate_arm(rig, bm_obj, side: str):
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = bm_obj.evaluated_get(deps)
    mesh_posed = bpy.data.meshes.new_from_object(eval_obj, preserve_all_data_layers=True, depsgraph=deps)
    posed_obj = bpy.data.objects.new(f"Posed_{side}", mesh_posed)
    bpy.context.collection.objects.link(posed_obj)

    for vg in bm_obj.vertex_groups:
        if vg.name not in posed_obj.vertex_groups:
            posed_obj.vertex_groups.new(name=vg.name)

    arm_bones = {
        "lowerarm_" + side,
        "hand_" + side,
        "thumb_01_" + side, "thumb_02_" + side, "thumb_03_" + side,
        "index_01_" + side, "index_02_" + side, "index_03_" + side,
        "middle_01_" + side, "middle_02_" + side, "middle_03_" + side,
        "ring_01_" + side, "ring_02_" + side, "ring_03_" + side,
        "pinky_01_" + side, "pinky_02_" + side, "pinky_03_" + side,
    }
    upper_arm_b = "upperarm_" + side

    pb_fore = rig.pose.bones["lowerarm_" + side]
    elbow_pos = pb_fore.head.copy()
    wrist_pos = pb_fore.tail.copy()
    fore_axis = (wrist_pos - elbow_pos).normalized()
    fore_len = (wrist_pos - elbow_pos).length

    vg_by_idx = {vg.index: vg.name for vg in bm_obj.vertex_groups}

    bm = bmesh.new()
    bm.from_mesh(posed_obj.data)
    d_lay = bm.verts.layers.deform.active

    del_faces = []
    for f in bm.faces:
        c = f.calc_center_median()
        w_arm = 0.0
        w_upper = 0.0
        if d_lay is not None:
            inv_n = 1.0 / max(1, len(f.verts))
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    bn = vg_by_idx.get(gi, "")
                    if bn in arm_bones:
                        w_arm += gw * inv_n
                    elif bn == upper_arm_b:
                        w_upper += gw * inv_n
        t_along = (c - elbow_pos).dot(fore_axis) / max(1e-5, fore_len)
        keep = (w_arm >= 0.48) or ((w_arm + w_upper) >= 0.68 and t_along >= -0.92)
        if t_along < -0.92:
            keep = False
        if not keep:
            del_faces.append(f)

    if del_faces:
        bmesh.ops.delete(bm, geom=del_faces, context="FACES")

    lv = [v for v in bm.verts if not v.link_faces]
    if lv:
        bmesh.ops.delete(bm, geom=lv, context="VERTS")

    for _ in range(2):
        spikes = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary) >= 2]
        if not spikes or len(spikes) >= len(bm.faces):
            break
        bmesh.ops.delete(bm, geom=spikes, context="FACES")
        lv = [v for v in bm.verts if not v.link_faces]
        if lv:
            bmesh.ops.delete(bm, geom=lv, context="VERTS")

    b_edges = [e for e in bm.edges if e.is_boundary]
    if b_edges:
        bmesh.ops.holes_fill(bm, edges=b_edges, sides=0)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(posed_obj.data)
    bm.free()

    return posed_obj, elbow_pos, wrist_pos, fore_axis, fore_len


def _make_shell_from_arm(base_arm, name, mat, face_keep_fn, offset=0.0020, thickness=0.0018, dec_ratio=1.0):
    mesh_c = base_arm.data.copy()
    obj = bpy.data.objects.new(name, mesh_c)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    vg_by_idx = {vg.index: vg.name for vg in base_arm.vertex_groups}

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    d_lay = bm.verts.layers.deform.active

    del_f = []
    for f in bm.faces:
        c = f.calc_center_median()
        weights = {}
        if d_lay is not None:
            inv_n = 1.0 / max(1, len(f.verts))
            for v in f.verts:
                for gi, gw in v[d_lay].items():
                    bn = vg_by_idx.get(gi, "")
                    if bn:
                        weights[bn] = weights.get(bn, 0.0) + gw * inv_n
        if not face_keep_fn(c, weights):
            del_f.append(f)

    if del_f:
        bmesh.ops.delete(bm, geom=del_f, context="FACES")
    lv = [v for v in bm.verts if not v.link_faces]
    if lv:
        bmesh.ops.delete(bm, geom=lv, context="VERTS")

    for _ in range(2):
        spikes = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary) >= 2]
        if not spikes or len(spikes) >= len(bm.faces):
            break
        bmesh.ops.delete(bm, geom=spikes, context="FACES")
        lv = [v for v in bm.verts if not v.link_faces]
        if lv:
            bmesh.ops.delete(bm, geom=lv, context="VERTS")

    if len(bm.faces) == 0:
        bm.free()
        bpy.data.objects.remove(obj, do_unlink=True)
        return None

    bm.normal_update()
    if abs(offset) > 1e-5:
        for v in bm.verts:
            wr = 0.0007 * math.sin(v.co.y * 55.0 + v.co.x * 38.0) * math.cos(v.co.z * 48.0)
            v.co += v.normal * (offset + wr)

    bm.to_mesh(obj.data)
    bm.free()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if thickness > 0.0004:
        sol = obj.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = thickness
        sol.offset = 1.0
        sol.use_rim = True
        bpy.ops.object.modifier_apply(modifier=sol.name)

    if dec_ratio < 0.99:
        dec = obj.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = dec_ratio
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)

    C.uv_box_project(obj, scale=6.0)
    C.smooth_shade(obj, 54.0)
    return obj


def _count_tris(obj):
    return sum(max(1, len(p.vertices) - 2) for p in obj.data.polygons)


def _print_hand_joints(rig, side: str, origin: Vector):
    for j in [f"lowerarm_{side}", f"hand_{side}", f"thumb_02_{side}", f"thumb_03_{side}",
              f"index_01_{side}", f"index_03_{side}", f"middle_01_{side}", f"middle_03_{side}",
              f"ring_03_{side}", f"pinky_03_{side}"]:
        pb = rig.pose.bones.get(j)
        if pb:
            h = tuple(round(v, 4) for v in (pb.head - origin))
            t = tuple(round(v, 4) for v in (pb.tail - origin))
            print(f"  [{side.upper()}] {j}: head={h} tail={t}")


def _find_surface_spot(arm_obj, elbow_pos: Vector, fore_axis: Vector, fore_len: float,
                       t_min: float, t_max: float, score_fn,
                       fallback_pos: Vector, fallback_n: Vector):
    """Find best surface face center and outward normal inside normalized forearm band [t_min, t_max]."""
    bm = bmesh.new()
    bm.from_mesh(arm_obj.data)
    bm.normal_update()
    best_pos = None
    best_n = None
    best_score = -1e9
    for margin in (0.0, 0.03):
        lo = t_min - margin
        hi = t_max + margin
        for f in bm.faces:
            c = f.calc_center_median()
            t = (c - elbow_pos).dot(fore_axis) / max(1e-5, fore_len)
            if lo <= t <= hi:
                sc = score_fn(c)
                if sc > best_score:
                    best_score = sc
                    best_pos = c.copy()
                    best_n = f.normal.copy()
        if best_pos is not None:
            break
    bm.free()
    if best_pos is None or best_n is None or best_n.length < 1e-4:
        return fallback_pos, fallback_n.normalized()
    return best_pos, best_n.normalized()


def _tangent_euler(fore_axis: Vector, surf_n: Vector):
    """Build right-handed Euler whose local +Z aligns with surf_n and local +Y aligns along fore_axis."""
    bz = surf_n.normalized()
    by = fore_axis - bz * fore_axis.dot(bz)
    if by.length < 1e-4:
        by = Vector((0.0, 1.0, 0.0)) - bz * bz.y
    by.normalize()
    bx = by.cross(bz).normalized()
    return Matrix((bx, by, bz)).transposed().to_euler()


def build_fp_right_hand():
    """Pose MPFB2 right arm/hand cleanly in firing grip around (0,0,0), staying below slide & sights."""
    rig, bm_obj = _create_base_human()
    m = hand_materials()

    # Align upperarm naturally collinear behind elbow so wool sleeve continues cleanly off-screen
    _aim_bone_vec(rig, "upperarm_r", Vector((-0.28, 0.76, 0.58)))
    # Forearm sweeps naturally from bottom-right-rear shoulder up toward grip (kept low behind slide)
    _aim_bone_vec(rig, "lowerarm_r", Vector((-0.34, 0.72, 0.60)))

    pb_hand = rig.pose.bones["hand_r"]
    pb_mid = rig.pose.bones["middle_01_r"]
    pb_idx = rig.pose.bones["index_01_r"]
    pb_pnk = rig.pose.bones["pinky_01_r"]

    cur_fwd = (pb_mid.head - pb_hand.head).normalized()
    cur_up = (pb_idx.head - pb_pnk.head).normalized()
    M_cur = _orthonormal_frame(cur_fwd, cur_up)

    # Fingers sweep forward (+Y) pitched down (-0.34 Z) and wrapped slightly inward (-X),
    # index side UP (+Z), back-of-hand OUT (+X) -> palm faces (-X, gripping frame!).
    M_tgt = _orthonormal_frame(Vector((-0.08, 0.94, -0.34)), Vector((-0.08, 0.34, 0.94)))
    _pose_bone_armature_rot(rig, "hand_r", M_tgt @ M_cur.inverted())
    bpy.context.view_layer.update()

    # Trigger finger curls cleanly around trigger at (0.002, 0.030, -0.016)
    _curl_finger_toward(rig, ["index_01_r", "index_02_r", "index_03_r"], Vector((-0.88, 0.44, -0.14)), [12.0, 34.0, 28.0])
    # Middle, ring, pinky wrap front strap snugly without over-curling behind grip
    palm_in = Vector((-0.96, -0.22, 0.00)).normalized()
    _curl_finger_toward(rig, ["middle_01_r", "middle_02_r", "middle_03_r"], palm_in, [52.0, 74.0, 48.0])
    _curl_finger_toward(rig, ["ring_01_r", "ring_02_r", "ring_03_r"], palm_in, [56.0, 76.0, 50.0])
    _curl_finger_toward(rig, ["pinky_01_r", "pinky_02_r", "pinky_03_r"], palm_in, [58.0, 74.0, 48.0])

    # Thumb stays on LEFT cheek of frame (X < -0.018), tucked cleanly below slide/sights (Z <= +0.016)
    _aim_bone_vec(rig, "thumb_01_r", Vector((-0.80, 0.56, 0.16)))
    _aim_bone_vec(rig, "thumb_02_r", Vector((-0.56, 0.82, 0.04)))
    _aim_bone_vec(rig, "thumb_03_r", Vector((-0.18, 0.98, -0.06)))

    arm_raw, elbow_pos, wrist_pos, fore_axis, fore_len = _freeze_and_isolate_arm(rig, bm_obj, "r")

    # Anchor using index_01_r & middle_01_r so palm hugs +X=+0.025..+0.048, index curls to trigger (0.002, 0.030, -0.016),
    # and thumb rides outside left cheek (-0.022) well below slide!
    pb_idx1 = rig.pose.bones["index_01_r"]
    pb_mid1 = rig.pose.bones["middle_01_r"]
    pb_thm3 = rig.pose.bones["thumb_03_r"]
    knuckle_ref = pb_idx1.head.lerp(pb_mid1.head, 0.42)
    grip_ref = knuckle_ref - Vector((0.030, 0.004, -0.022))
    _print_hand_joints(rig, "r", grip_ref)
    print(f"[HANDS] R index_tip={tuple(round(v,4) for v in (rig.pose.bones['index_03_r'].tail - grip_ref))} thumb_tip={tuple(round(v,4) for v in (pb_thm3.tail - grip_ref))}")

    bpy.data.objects.remove(bm_obj, do_unlink=True)
    bpy.data.objects.remove(rig, do_unlink=True)

    shift = -grip_ref
    for v in arm_raw.data.vertices:
        v.co += shift
    arm_raw.data.update()
    elbow_s = elbow_pos + shift
    wrist_s = wrist_pos + shift

    glove_bones = {
        "hand_r",
        "thumb_01_r", "thumb_02_r", "thumb_03_r",
        "index_01_r", "index_02_r", "index_03_r",
        "middle_01_r", "middle_02_r", "middle_03_r",
        "ring_01_r", "ring_02_r", "ring_03_r",
        "pinky_01_r", "pinky_02_r", "pinky_03_r",
    }

    arm_skin = _make_shell_from_arm(
        arm_raw,
        "R_ArmSkin",
        m["skin"],
        face_keep_fn=lambda c, w: (
            0.74 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.96
            and sum(w.get(b, 0.0) for b in glove_bones) < 0.45
        ),
        offset=0.0,
        thickness=0.0,
        dec_ratio=0.55,
    )

    r_glove = _make_shell_from_arm(
        arm_raw,
        "R_LeatherGlove",
        m["leather"],
        face_keep_fn=lambda c, w: (
            sum(w.get(b, 0.0) for b in glove_bones) >= 0.36
            or (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) >= 0.92
        ),
        offset=0.0012,
        thickness=0.0014,
        dec_ratio=0.55,
    )

    r_knuckle = _make_shell_from_arm(
        arm_raw,
        "R_KnuckleGuard",
        m["leather_dark"],
        face_keep_fn=lambda c, w: (
            w.get("hand_r", 0.0) >= 0.55 and c.x > 0.032 and c.y > -0.055 and c.y < 0.015
        ),
        offset=0.0030,
        thickness=0.0016,
        dec_ratio=0.65,
    )

    r_sleeve = _make_shell_from_arm(
        arm_raw,
        "R_WoolSleeve",
        m["sleeve_wool"],
        face_keep_fn=lambda c, w: -0.88 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.82,
        offset=0.0054,
        thickness=0.0034,
        dec_ratio=0.40,
    )

    r_cuff = _make_shell_from_arm(
        arm_raw,
        "R_KnitCuff",
        m["cuff_cloth"],
        face_keep_fn=lambda c, w: 0.78 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.85,
        offset=0.0068,
        thickness=0.0042,
        dec_ratio=0.55,
    )

    stud_pos, stud_n = _find_surface_spot(
        arm_raw, elbow_s, fore_axis, fore_len,
        0.91, 0.97,
        score_fn=lambda c: c.x * 0.6 + c.z * 0.8,
        fallback_pos=wrist_s + Vector((0.025, -0.004, 0.012)),
        fallback_n=Vector((0.70, -0.13, 0.70)).normalized(),
    )
    stud_rot = _tangent_euler(fore_axis, stud_n)
    r_stud = C.add_cyl(
        "R_GloveSnap", 0.0040, 0.0028,
        stud_pos + stud_n * 0.0030, stud_rot,
        vertices=10, mat=m["brass_rivet"], bevel=0.0004,
    )

    bpy.data.objects.remove(arm_raw, do_unlink=True)

    organic = C.join_objects([p for p in [arm_skin, r_glove, r_knuckle, r_sleeve] if p is not None], "FPRightOrganic", apply_uv=False)
    o_tris = _count_tris(organic)
    if o_tris > 2680:
        dec = organic.modifiers.new("FinalDecimate", "DECIMATE")
        dec.ratio = 2640.0 / float(o_tris)
        dec.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = organic
        bpy.ops.object.modifier_apply(modifier=dec.name)
    parts = [organic, r_cuff, r_stud]
    joined = C.join_objects([p for p in parts if p is not None], "FPRightHand", apply_uv=False)
    C.uv_box_project(joined, scale=6.0)
    C.smooth_shade(joined, 52.0)

    pts = [v.co for v in joined.data.vertices]
    mn = tuple(round(min(p[i] for p in pts), 4) for i in range(3))
    mx = tuple(round(max(p[i] for p in pts), 4) for i in range(3))
    print(f"[HANDS] fp_right_hand tris={_count_tris(joined)} bounds min={mn} max={mx}")
    C.export_asset("weapons", "fp_right_hand")


def build_fp_left_hand():
    """Pose MPFB2 left arm/hand in cupped C-grip cradle under forends & pistol bottom, with wrist watch."""
    rig, bm_obj = _create_base_human()
    m = hand_materials()

    # Align upperarm naturally collinear behind elbow so wool sleeve continues cleanly off-screen
    _aim_bone_vec(rig, "upperarm_l", Vector((0.52, 0.76, 0.40)))
    # Forearm sweeps smoothly from bottom-left-rear up toward gun forend
    _aim_bone_vec(rig, "lowerarm_l", Vector((0.68, 0.62, 0.36)))

    pb_hand = rig.pose.bones["hand_l"]
    pb_mid = rig.pose.bones["middle_01_l"]
    pb_idx = rig.pose.bones["index_01_l"]
    pb_pnk = rig.pose.bones["pinky_01_l"]

    cur_fwd = (pb_mid.head - pb_hand.head).normalized()
    cur_up = (pb_idx.head - pb_pnk.head).normalized()
    M_cur = _orthonormal_frame(cur_fwd, cur_up)

    # Palm faces UP (+Z) with slight tilt (-X), fingers sweep RIGHT (+X) and gently forward (+Y),
    # index side forward (+Y), pinky rear (-Y) -> fingers curl tightly around right forend cheek (Z <= +0.028)!
    M_tgt = _orthonormal_frame(Vector((0.92, 0.36, -0.10)), Vector((-0.34, 0.92, 0.14)))
    _pose_bone_armature_rot(rig, "hand_l", M_tgt @ M_cur.inverted())
    bpy.context.view_layer.update()

    # Curve fingertips cleanly inward over forend cheek so tips end at X~+0.020, Z~+0.022 (never blocking sights!)
    cup_in = Vector((-0.62, 0.08, 0.78)).normalized()
    _curl_finger_toward(rig, ["index_01_l", "index_02_l", "index_03_l"], cup_in, [44.0, 62.0, 48.0])
    _curl_finger_toward(rig, ["middle_01_l", "middle_02_l", "middle_03_l"], cup_in, [46.0, 66.0, 50.0])
    _curl_finger_toward(rig, ["ring_01_l", "ring_02_l", "ring_03_l"], cup_in, [48.0, 68.0, 52.0])
    _curl_finger_toward(rig, ["pinky_01_l", "pinky_02_l", "pinky_03_l"], cup_in, [50.0, 64.0, 48.0])

    # Thumb rides forward along left forend cheek at X ~ -0.024, Z ~ +0.008
    _aim_bone_vec(rig, "thumb_01_l", Vector((-0.10, 0.96, 0.24)))
    _aim_bone_vec(rig, "thumb_02_l", Vector((0.04, 0.99, 0.10)))
    _aim_bone_vec(rig, "thumb_03_l", Vector((0.12, 0.99, 0.02)))

    arm_raw, elbow_pos, wrist_pos, fore_axis, fore_len = _freeze_and_isolate_arm(rig, bm_obj, "l")

    pb_mid = rig.pose.bones["middle_01_l"]
    pb_hand = rig.pose.bones["hand_l"]
    palm_center = pb_hand.head.lerp(pb_mid.head, 0.55)
    cradle_ref = palm_center - Vector((0.004, 0.002, -0.022))

    _print_hand_joints(rig, "l", cradle_ref)
    idx_tip = rig.pose.bones["index_03_l"].tail - cradle_ref
    thm_tip = rig.pose.bones["thumb_03_l"].tail - cradle_ref
    print(f"[HANDS] L index_tip={tuple(round(v,4) for v in idx_tip)} thumb_tip={tuple(round(v,4) for v in thm_tip)}")

    bpy.data.objects.remove(bm_obj, do_unlink=True)
    bpy.data.objects.remove(rig, do_unlink=True)

    shift = -cradle_ref
    for v in arm_raw.data.vertices:
        v.co += shift
    arm_raw.data.update()
    elbow_s = elbow_pos + shift
    wrist_s = wrist_pos + shift

    glove_bones = {
        "hand_l",
        "thumb_01_l", "thumb_02_l", "thumb_03_l",
        "index_01_l", "index_02_l", "index_03_l",
        "middle_01_l", "middle_02_l", "middle_03_l",
        "ring_01_l", "ring_02_l", "ring_03_l",
        "pinky_01_l", "pinky_02_l", "pinky_03_l",
    }

    arm_skin = _make_shell_from_arm(
        arm_raw,
        "L_ArmSkin",
        m["skin"],
        face_keep_fn=lambda c, w: (
            0.74 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.96
            and sum(w.get(b, 0.0) for b in glove_bones) < 0.45
        ),
        offset=0.0,
        thickness=0.0,
        dec_ratio=0.55,
    )

    l_glove = _make_shell_from_arm(
        arm_raw,
        "L_LeatherGlove",
        m["leather"],
        face_keep_fn=lambda c, w: (
            sum(w.get(b, 0.0) for b in glove_bones) >= 0.36
            or (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) >= 0.92
        ),
        offset=0.0012,
        thickness=0.0014,
        dec_ratio=0.55,
    )

    l_palm = _make_shell_from_arm(
        arm_raw,
        "L_PalmPad",
        m["leather_dark"],
        face_keep_fn=lambda c, w: w.get("hand_l", 0.0) >= 0.55 and c.z < -0.008,
        offset=0.0030,
        thickness=0.0016,
        dec_ratio=0.65,
    )

    l_sleeve = _make_shell_from_arm(
        arm_raw,
        "L_WoolSleeve",
        m["sleeve_wool"],
        face_keep_fn=lambda c, w: -0.88 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.82,
        offset=0.0054,
        thickness=0.0034,
        dec_ratio=0.40,
    )

    l_cuff = _make_shell_from_arm(
        arm_raw,
        "L_KnitCuff",
        m["cuff_cloth"],
        face_keep_fn=lambda c, w: 0.78 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.85,
        offset=0.0068,
        thickness=0.0042,
        dec_ratio=0.55,
    )

    l_watch_strap = _make_shell_from_arm(
        arm_raw,
        "L_WatchStrap",
        m["leather_dark"],
        face_keep_fn=lambda c, w: 0.855 <= (c - elbow_s).dot(fore_axis) / max(1e-5, fore_len) <= 0.885,
        offset=0.0022,
        thickness=0.0016,
        dec_ratio=1.0,
    )

    watch_pos, watch_n = _find_surface_spot(
        arm_raw, elbow_s, fore_axis, fore_len,
        0.855, 0.885,
        score_fn=lambda c: -c.x * 0.4 + c.z * 0.9,
        fallback_pos=wrist_s + Vector((-0.020, -0.006, 0.018)),
        fallback_n=Vector((-0.30, 0.16, 0.94)).normalized(),
    )
    watch_rot = _tangent_euler(fore_axis, watch_n)
    watch_m = watch_rot.to_matrix()
    l_watch_case = C.add_cyl(
        "L_WatchCase", 0.0135, 0.0060,
        watch_pos + watch_n * 0.0042, watch_rot,
        vertices=16, mat=m["watch_steel"], bevel=0.0008,
    )
    l_watch_dial = C.add_cyl(
        "L_WatchDial", 0.0102, 0.0022,
        watch_pos + watch_n * 0.0063, watch_rot,
        vertices=14, mat=m["watch_face"], bevel=0.0,
    )
    dial_top = watch_pos + watch_n * 0.0075
    rot_h = watch_m @ Matrix.Rotation(math.radians(-48.0), 3, "Z")
    rot_m = watch_m @ Matrix.Rotation(math.radians(32.0), 3, "Z")
    l_watch_h = C.add_box(
        "L_WatchHandH", (0.0012, 0.0050, 0.0007),
        dial_top + rot_h @ Vector((0.0, 0.0022, 0.0003)), rot_h.to_euler(),
        mat=m["watch_tritium"], bevel=0.0,
    )
    l_watch_m = C.add_box(
        "L_WatchHandM", (0.0010, 0.0070, 0.0007),
        dial_top + rot_m @ Vector((0.0, 0.0032, 0.0005)), rot_m.to_euler(),
        mat=m["watch_tritium"], bevel=0.0,
    )
    l_watch_pip = C.add_box(
        "L_WatchPip", (0.0014, 0.0022, 0.0007),
        dial_top + watch_m @ Vector((0.0, 0.0074, 0.0003)), watch_rot,
        mat=m["watch_tritium"], bevel=0.0,
    )

    bpy.data.objects.remove(arm_raw, do_unlink=True)

    organic = C.join_objects([p for p in [arm_skin, l_glove, l_palm, l_sleeve] if p is not None], "FPLeftOrganic", apply_uv=False)
    o_tris = _count_tris(organic)
    if o_tris > 2580:
        dec = organic.modifiers.new("FinalDecimate", "DECIMATE")
        dec.ratio = 2540.0 / float(o_tris)
        dec.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = organic
        bpy.ops.object.modifier_apply(modifier=dec.name)
    parts = [organic, l_cuff, l_watch_strap, l_watch_case, l_watch_dial, l_watch_h, l_watch_m, l_watch_pip]
    joined = C.join_objects([p for p in parts if p is not None], "FPLeftHand", apply_uv=False)
    C.uv_box_project(joined, scale=6.0)
    C.smooth_shade(joined, 52.0)

    pts = [v.co for v in joined.data.vertices]
    mn = tuple(round(min(p[i] for p in pts), 4) for i in range(3))
    mx = tuple(round(max(p[i] for p in pts), 4) for i in range(3))
    print(f"[HANDS] fp_left_hand tris={_count_tris(joined)} bounds min={mn} max={mx}")
    C.export_asset("weapons", "fp_left_hand")


if __name__ == "__main__":
    build_fp_right_hand()
    build_fp_left_hand()
    print("[HANDS] Anatomical MPFB2 FP hands & sleeves built cleanly!")
