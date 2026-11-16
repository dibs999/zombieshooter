"""Generate 5 high-detail MPFB2 + CC0 Zombies with torn layered clothing, sculpted gore/ribs,
removable dismemberment parts (Mesh_Head, Mesh_Arm_L, Mesh_Arm_R, Mesh_Legs, Mesh_Torso),
severed bloody bone stumps, and full CoD Zombies NLA animation sets:
- zombie_soldier
- zombie_scientist
- zombie_brute
- zombie_worker
- zombie_crawler
"""

import math
import os
import sys
import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as C
import chars_common as CC


def _add_teeth_and_ribs(variant, m, scale, rig, add_ribs=True):
    """Add sculpted upper/lower jagged teeth (Head) and bloody chest wound ribs (spine_02/03)."""
    objs = []
    t_parts = []
    for i, tx in enumerate((-0.021, -0.013, -0.0045, 0.0045, 0.013, 0.021)):
        ty = 0.134 - abs(tx) * 0.35
        h_t = 0.012 if abs(i - 2.5) > 1.8 else 0.0095
        t_parts.append(C.add_cone(
            f"UpTooth_{i}", 0.0032 * scale, 0.0010 * scale, h_t * scale,
            (tx * scale, ty * scale, 1.578 * scale), (math.radians(176), 0, 0),
            vertices=6, mat=m["teeth"],
        ))
        t_parts.append(C.add_cone(
            f"LoTooth_{i}", 0.0030 * scale, 0.0010 * scale, h_t * 0.85 * scale,
            (tx * scale, (ty - 0.003) * scale, 1.545 * scale), (math.radians(-10), 0, 0),
            vertices=6, mat=m["teeth"],
        ))
    teeth_obj = C.join_objects(t_parts, "TeethArc", apply_uv=False)
    CC.bind_accessory_to_bones(teeth_obj, rig, "Head", scale=scale)
    objs.append(teeth_obj)

    if add_ribs:
        wound_bg = C.add_sphere(
            "ChestWoundMeat", 1.0, (0.066 * scale, 0.022 * scale, 0.086 * scale),
            (-0.048 * scale, 0.118 * scale, 1.295 * scale), (0, math.radians(12), math.radians(-10)),
            segments=10, rings=8, mat=m["gore_flesh"],
        )
        CC.bind_accessory_to_bones(wound_bg, rig, {"spine_02": 0.45, "spine_03": 0.55}, scale=scale)
        objs.append(wound_bg)

        rib_parts = []
        for ri in range(4):
            rz = (1.225 + ri * 0.036) * scale
            rib_parts.append(C.add_tube_pipe(
                f"ChestRib_{ri}",
                [
                    (-0.105 * scale, 0.105 * scale, rz),
                    (-0.052 * scale, 0.136 * scale, rz + 0.005 * scale),
                    (0.002 * scale, 0.128 * scale, rz - 0.006 * scale),
                ],
                radius=0.0072 * scale, segments=7, mat=m["bone"],
            ))
        ribs_obj = C.join_objects(rib_parts, "ChestRibs", apply_uv=False)
        CC.bind_accessory_to_bones(ribs_obj, rig, {"spine_02": 0.45, "spine_03": 0.55}, scale=scale)
        objs.append(ribs_obj)

    return objs


def _add_jackboots(body, rig, m, scale, heavy=False, boot_mat=None, panzer_sabaton=False):
    """Build calf-high tailored leather/armored boots + anatomical lugged soles with zero heel or toe clipping."""
    bmat = boot_mat if boot_mat is not None else m["leather"]
    vg_idx = {vg.name: vg.index for vg in body.vertex_groups}
    bm_v = body.data.vertices
    toe_idx = vg_idx.get("toenails", -1)
    foot_v_idx = {"l": set(), "r": set()}
    for v in bm_v:
        gs = {g.group: g.weight for g in v.groups}
        for sfx in ("l", "r"):
            fw = gs.get(vg_idx.get(f"foot_{sfx}", -1), 0.0) + gs.get(vg_idx.get(f"ball_{sfx}", -1), 0.0)
            if fw > 0.35 or (toe_idx >= 0 and toe_idx in gs and ((sfx == "l" and v.co.x < 0.0) or (sfx == "r" and v.co.x > 0.0))):
                if v.co.z < 0.098 * scale:
                    foot_v_idx[sfx].add(v.index)

    # First tuck bare forefoot & individual toes inward so BootUppers never molds bare 5-toe bumps
    foot_v_y = {"l": [], "r": []}
    for side, sfx in (("L", "l"), ("R", "r")):
        b_foot = rig.data.bones[f"foot_{sfx}"]
        fh = b_foot.head_local
        bx = fh.x
        for vi in foot_v_idx[sfx]:
            v = bm_v[vi]
            if v.co.y > fh.y - 0.02 * scale:
                v.co.x = bx + (v.co.x - bx) * 0.72
                v.co.y = fh.y + (v.co.y - fh.y) * 0.78
                v.co.z = max(v.co.z, 0.036 * scale)
            foot_v_y[sfx].append(v.co.y)
    body.data.update()

    z_lo_upper = 0.12 if panzer_sabaton else -0.50
    uppers = CC.make_tailored_garment(
        body, rig, "BootUppers", bmat,
        lambda x, y, z, w: (w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)) > 0.45 and (z_lo_upper <= z <= 0.315),
        offset=0.0135 if not heavy else 0.0175,
        thickness=0.0045 if not heavy else 0.006,
        uv_scale=2.8,
        wrinkle_amp=0.0008,
        scale=scale,
    )
    out = [uppers] if uppers else []

    w_mult = 1.15 if heavy else 1.0
    for side, sfx in (("L", "l"), ("R", "r")):
        b_foot = rig.data.bones[f"foot_{sfx}"]
        b_ball = rig.data.bones[f"ball_{sfx}"]
        fh = b_foot.head_local
        bt = b_ball.tail_local
        bx = 0.5 * (fh.x + bt.x)
        y_heel = fh.y - 0.068 * scale
        max_fy = max(foot_v_y[sfx]) if foot_v_y[sfx] else bt.y
        y_toe = max(bt.y + 0.018 * scale, max_fy + 0.014 * scale)
        len_y = y_toe - y_heel
        cy = 0.5 * (y_heel + y_toe)
        yaw = math.atan2(-(bt.x - fh.x), max(1e-4, bt.y - fh.y))

        # Rolled boot top cuff collar around shin capping top edge of BootUppers
        cuff_pos, _, _ = CC.bone_frame(rig, f"calf_{sfx}", along_t=0.38)
        cuff_collar = C.add_torus(
            f"BootCuff_{side}", 0.058 * w_mult * scale, 0.015 * scale,
            cuff_pos, (0, 0, yaw), major_segments=14, minor_segments=6, mat=bmat,
        )
        CC.bind_accessory_to_bones(cuff_collar, rig, f"calf_{sfx}", scale=scale, keep_existing_uv=True)
        out.append(cuff_collar)

        sole = C.add_box(
            f"BootSole_{side}", (0.094 * w_mult * scale, len_y, 0.024 * scale),
            (bx, cy, 0.012 * scale), (0, 0, yaw), mat=m["socket_dark"], bevel=0.014 * scale,
        )
        toe_cap = C.add_sphere(
            f"BootToeCap_{side}", 1.0,
            (0.048 * w_mult * scale, (0.088 if panzer_sabaton else 0.068) * scale, (0.052 if panzer_sabaton else 0.040) * scale),
            (bt.x, max_fy - (0.016 if not panzer_sabaton else 0.024) * scale, (0.046 if panzer_sabaton else 0.036) * scale),
            (0, 0, yaw), segments=12, rings=8, mat=bmat,
        )
        heel_blk = C.add_box(
            f"BootHeelCap_{side}", (0.088 * w_mult * scale, 0.082 * scale, (0.062 if panzer_sabaton else 0.040) * scale),
            (fh.x, fh.y - 0.028 * scale, (0.036 if panzer_sabaton else 0.028) * scale),
            (0, 0, yaw), mat=bmat, bevel=0.012 * scale,
        )
        parts_s = [sole, toe_cap, heel_blk]
        if panzer_sabaton:
            arch_armor = C.add_box(
                f"SabatonInstep_{side}", (0.104 * scale, len_y * 0.72, 0.072 * scale),
                (bx, cy - 0.008 * scale, 0.052 * scale), (math.radians(-12), 0, yaw),
                mat=bmat, bevel=0.018 * scale,
            )
            parts_s.append(arch_armor)
        s_obj = C.join_objects(parts_s, f"BootSoleGrp_{side}", apply_uv=False)

        def make_bw(sf, split_y):
            def bw(x, y, z):
                if y > split_y:
                    return {f"ball_{sf}": 0.65, f"foot_{sf}": 0.35}
                return {f"foot_{sf}": 0.85, f"calf_{sf}": 0.15}
            return bw

        CC.bind_accessory_to_bones(s_obj, rig, make_bw(sfx, b_foot.tail_local.y / max(1e-5, scale)), scale=scale, keep_existing_uv=True)
        out.append(s_obj)
    return out


def _add_fitted_belt(body, rig, name, mat, scale, z_lo=0.972, z_hi=1.032, offset=0.0155, thickness=0.006):
    return CC.make_tailored_garment(
        body, rig, name, mat,
        lambda x, y, z, w: (w.get("pelvis", 0) + w.get("spine_01", 0)) > 0.45 and (z_lo <= z <= z_hi),
        offset=offset, thickness=thickness, uv_scale=3.0, wrinkle_amp=0.0005, scale=scale,
    )


def _build_soldier(m):
    scale = 1.0
    rig, body, eyes = CC.create_mpfb_zombie_base(
        "soldier", scale=scale, age=0.68, muscle=0.52, weight=0.22, height=0.50,
        skin_mat=m["skin_soldier"], eye_mat=m["eye_amber"], boot_sole=0.024, decimate_ratio=0.33,
    )
    skinned = [body, eyes]

    # Torn Wehrmacht Feldgrau Tunic (upper torso + torn chest hole + torn sleeves)
    def keep_tunic(x, y, z, w):
        arm = w.get("upperarm_l", 0) + w.get("upperarm_r", 0) + w.get("lowerarm_l", 0) + w.get("lowerarm_r", 0)
        torso = w.get("spine_01", 0) + w.get("spine_02", 0) + w.get("spine_03", 0) + w.get("clavicle_l", 0) + w.get("clavicle_r", 0) + w.get("pelvis", 0)
        if arm > 0.35:
            return z > (1.19 if x < 0 else 1.11)
        return (torso > 0.45) and (0.76 <= z <= 1.45)

    def tunic_hole(x, y, z, _w):
        if y > 0.04 and (-0.125 <= x <= 0.025) and (1.19 <= z <= 1.38):
            rip = math.sin(x * 16.0 + z * 12.0) * 0.14
            return ((x + 0.048) ** 2 / 0.0052 + (z - 1.285) ** 2 / 0.0082 + rip) < 1.0
        return False

    tunic = CC.make_tailored_garment(body, rig, "SoldierTunic", m["uniform_soldier"], keep_tunic, hole_fn=tunic_hole, offset=0.011, thickness=0.005, uv_scale=2.2, scale=scale)
    if tunic:
        skinned.append(tunic)

    # Tattered Trousers (pelvis down to boot tops with knee tear)
    def keep_pants(x, y, z, w):
        leg = w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("pelvis", 0)
        return leg > 0.45 and (0.18 <= z <= 0.99)

    def pants_hole(x, y, z, _w):
        return y > 0.03 and x > 0.05 and (0.48 <= z <= 0.62)

    pants = CC.make_tailored_garment(body, rig, "SoldierPants", m["pants_soldier"], keep_pants, hole_fn=pants_hole, offset=0.0085, thickness=0.0, uv_scale=2.4, scale=scale)
    if pants:
        skinned.append(pants)

    skinned.extend(_add_jackboots(body, rig, m, scale, heavy=False))
    skinned.extend(_add_teeth_and_ribs("soldier", m, scale, rig, add_ribs=True))

    # M40 Wehrmacht Stahlhelm centered tightly on skull cranium (y=+0.028) & pivoted around head center
    yc = 0.028
    helm_rings = [
        [(math.cos(a) * 0.114, yc + math.sin(a) * (0.118 if math.sin(a) >= 0 else 0.134), 1.608) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
        [(math.cos(a) * 0.106, yc + math.sin(a) * (0.112 if math.sin(a) >= 0 else 0.122), 1.644) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
        [(math.cos(a) * 0.098, yc + math.sin(a) * 0.110, 1.696) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
        [(math.cos(a) * 0.084, yc + math.sin(a) * 0.094, 1.742) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
        [(math.cos(a) * 0.050, yc + math.sin(a) * 0.056, 1.772) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
        [(math.cos(a) * 0.014, yc + math.sin(a) * 0.016, 1.784) for a in [(i / 20) * 2.0 * math.pi for i in range(20)]],
    ]
    helm = C.add_ring_loft("Stahlhelm", helm_rings, mat=m["stahlhelm"], smooth_angle=52.0)
    strap = C.add_tube_pipe("ChinStrap", [(-0.088, 0.055, 1.612), (-0.072, 0.085, 1.522), (0.0, 0.092, 1.482), (0.072, 0.085, 1.522), (0.088, 0.055, 1.612)], radius=0.006, segments=6, mat=m["leather"])
    helm_grp = C.join_objects([helm, strap], "StahlhelmFull", apply_uv=False)
    # Rotate around actual head center (never world origin!) so helmet sits flush on skull
    CC.rotate_verts_around(helm_grp, (0.0, yc, 1.655), (-4.0, 2.5, 0.0))
    CC.bind_accessory_to_bones(helm_grp, rig, "Head", scale=scale, keep_existing_uv=True)
    skinned.append(helm_grp)

    # Fitted Leather Belt + Snug Y-Strap Harness + Chest/Waist Pouches + Rear Canteen
    sbelt = _add_fitted_belt(body, rig, "SoldierBelt", m["leather"], scale)
    if sbelt:
        skinned.append(sbelt)
    ystraps = CC.make_tailored_garment(
        body, rig, "SoldierYStraps", m["leather"],
        lambda x, y, z, w: (w.get("spine_01", 0) + w.get("spine_02", 0) + w.get("spine_03", 0)) > 0.45 and (1.03 <= z <= 1.43) and (0.048 <= abs(x) <= 0.088) and (y > 0.02 or y < -0.02),
        offset=0.0145, thickness=0.004, uv_scale=3.0, scale=scale,
    )
    if ystraps:
        skinned.append(ystraps)

    gear = C.join_objects([
        C.add_box("Buckle", (0.054, 0.022, 0.048), (0.0, 0.130, 1.002), mat=m["chrome"], bevel=0.004),
        C.add_box("PouchL", (0.082, 0.042, 0.080), (-0.078, 0.128, 1.012), (0, 0, math.radians(-14)), mat=m["leather"], bevel=0.006),
        C.add_box("PouchR", (0.082, 0.042, 0.080), (0.078, 0.128, 1.012), (0, 0, math.radians(14)), mat=m["leather"], bevel=0.006),
        C.add_cyl("Canteen", 0.046, 0.135, (0.082, -0.118, 0.965), vertices=12, mat=m["stahlhelm"], bevel=0.005),
    ], "SoldierWebbing", apply_uv=False)
    CC.bind_accessory_to_bones(gear, rig, lambda x, y, z: {"pelvis": 0.65, "spine_01": 0.35}, scale=scale, keep_existing_uv=True)
    skinned.append(gear)

    CC.cull_body_faces(
        body,
        scale,
        lambda x, y, z, w: (
            (
                (w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)) > 0.50
                and z < 0.24
            )
            or (
                (w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0)) > 0.55
                and (0.24 <= z <= 0.92)
                and not (y > 0.00 and x > 0.01 and 0.42 <= z <= 0.68)
                and not (w.get("pelvis", 0) >= 0.35 and 0.80 <= z <= 0.90)
            )
            or (
                sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES)) < 0.15
                and sum(w.get(b, 0) for b in CC.HEAD_BONES) < 0.12
                and (0.90 <= z <= 1.37)
                and not (y > 0.00 and -0.18 <= x <= 0.07 and 1.13 <= z <= 1.43)
            )
        ),
    )

    parts = CC.split_dismemberment_parts(rig, skinned, m["gore_flesh"], m["bone"], scale=scale, z_neck_cut=1.45)
    CC.add_zombie_nla_animations(rig, scale=scale)
    tris = sum(len(p.vertices) - 2 for obj in parts.values() if obj for p in obj.data.polygons)
    print(f"[CHARS] zombie_soldier tris={tris}, parts={sorted(parts.keys())}")
    C.export_asset("characters", "zombie_soldier", export_anims=True)


def _build_scientist(m):
    scale = 1.0
    rig, body, eyes = CC.create_mpfb_zombie_base(
        "scientist", scale=scale, age=0.76, muscle=0.35, weight=0.18, height=0.50,
        skin_mat=m["skin_scientist"], eye_mat=m["eye_amber"], boot_sole=0.022, decimate_ratio=0.27,
    )
    skinned = [body, eyes]

    # Jumpsuit / dark shirt & trousers underneath coat
    def keep_jump(x, y, z, w):
        arm = w.get("upperarm_l", 0) + w.get("upperarm_r", 0)
        torso = w.get("spine_01", 0) + w.get("spine_02", 0) + w.get("spine_03", 0) + w.get("pelvis", 0)
        leg = w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0)
        if arm > 0.35:
            return z > 1.15
        return (torso > 0.4 or leg > 0.4) and (0.18 <= z <= 1.44)

    jump = CC.make_tailored_garment(body, rig, "SciJumpsuit", m["jumpsuit_scientist"], keep_jump, offset=0.006, thickness=0.0, uv_scale=2.4, scale=scale)
    if jump:
        skinned.append(jump)

    # Bloodied Unbuttoned Lab Coat (clean open V-neck front placket without single-tri sawteeth)
    def keep_coat(x, y, z, w):
        arm = w.get("upperarm_l", 0) + w.get("upperarm_r", 0) + w.get("lowerarm_l", 0) + w.get("lowerarm_r", 0)
        if arm > 0.35:
            return z > 1.06
        gap_w = 0.044 + max(0.0, 1.38 - z) * 0.06
        if y > 0.04 and abs(x) < gap_w and z < 1.41:
            return False
        return 0.88 <= z <= 1.45

    coat = CC.make_tailored_garment(body, rig, "SciLabCoat", m["labcoat_scientist"], keep_coat, offset=0.012, thickness=0.0045, uv_scale=2.2, scale=scale)
    if coat:
        skinned.append(coat)

    # Draped open lab coat tails + chest pocket + pens + Group 935 laminated ID tag hugging chest
    skirt_parts = [
        C.add_box("CoatTailL", (0.100, 0.036, 0.38), (-0.108, 0.048, 0.74), (0, math.radians(-4), math.radians(-8)), mat=m["labcoat_scientist"], bevel=0.014),
        C.add_box("CoatTailR", (0.100, 0.036, 0.38), (0.108, 0.048, 0.74), (0, math.radians(4), math.radians(8)), mat=m["labcoat_scientist"], bevel=0.014),
        C.add_box("CoatTailBack", (0.280, 0.046, 0.40), (0.0, -0.098, 0.74), (math.radians(-4), 0, 0), mat=m["labcoat_scientist"], bevel=0.014),
        C.add_box("CoatPocket", (0.056, 0.014, 0.064), (0.088, 0.116, 1.285), (0, 0, math.radians(12)), mat=m["labcoat_scientist"], bevel=0.003),
        C.add_cyl("Pen1", 0.0035, 0.044, (0.080, 0.120, 1.326), mat=m["chrome"]),
        C.add_cyl("Pen2", 0.0035, 0.044, (0.095, 0.118, 1.326), mat=m["socket_dark"]),
        C.add_box("IDBadge", (0.040, 0.007, 0.054), (-0.082, 0.124, 1.298), (0, math.radians(-8), math.radians(-10)), mat=m["chrome"], bevel=0.002),
    ]
    coat_extras = C.join_objects(skirt_parts, "SciCoatExtras", apply_uv=False)
    def coat_bw(x, y, z):
        if z > 1.05:
            return {"spine_03": 0.60, "spine_02": 0.40}
        if abs(x) > 0.055 and y > -0.02:
            return {"pelvis": 0.62, f"thigh_{'l' if x < 0 else 'r'}": 0.38}
        return {"pelvis": 0.75, "spine_01": 0.25}
    CC.bind_accessory_to_bones(coat_extras, rig, coat_bw, scale=scale, keep_existing_uv=True)
    skinned.append(coat_extras)

    skinned.extend(_add_jackboots(body, rig, m, scale, heavy=False))
    skinned.extend(_add_teeth_and_ribs("scientist", m, scale, rig, add_ribs=False))

    # Skull-hugging disheveled mad-scientist fibrous matted hair
    sci_hair = CC.make_tailored_garment(
        body, rig, "SciHair", m["zombie_hair"],
        lambda x, y, z, w: w.get("Head", 0) > 0.55 and ((z > 1.688 and y < 0.090) or (y < 0.018 and z > 1.592)),
        offset=0.007, thickness=0.008, uv_scale=3.2, wrinkle_amp=0.005, scale=scale,
    )
    if sci_hair:
        skinned.append(sci_hair)

    # Snug Broken Brass Lab Goggles aligned to actual EYE center + skull-hugging oval strap
    eye_vs = [v.co for v in eyes.data.vertices]
    ey_c = sum(eye_vs, Vector((0, 0, 0))) / max(1, len(eye_vs))
    ey_x = max(abs(v.co.x) for v in eyes.data.vertices) * 0.72
    ey_y = max(v.co.y for v in eyes.data.vertices) + 0.011 * scale
    ey_z = ey_c.z

    gog_strap = C.add_torus("GogStrap", 0.095, 0.0055, (0.0, 0.030, ey_z + 0.004), (math.radians(6), 0, 0), major_segments=20, minor_segments=6, mat=m["leather"])
    for v in gog_strap.data.vertices:
        v.co.x *= 0.80
        v.co.y = (v.co.y - 0.030) * 0.96 + 0.030
    gog_strap.data.update()

    head_acc = C.join_objects([
        C.add_cyl("GogRimL", 0.020, 0.016, (-ey_x, ey_y + 0.004, ey_z + 0.005), (math.radians(82), 0, math.radians(-14)), vertices=14, mat=m["brass"], bevel=0.002),
        C.add_cyl("GogRimR", 0.020, 0.016, (ey_x, ey_y + 0.002, ey_z - 0.003), (math.radians(88), 0, math.radians(10)), vertices=14, mat=m["brass"], bevel=0.002),
        C.add_cyl("GogLensR", 0.0155, 0.006, (ey_x + 0.001, ey_y + 0.010, ey_z - 0.003), (math.radians(88), 0, math.radians(10)), vertices=14, mat=m["goggle_lens"], bevel=0.001),
        C.add_box("GogBridge", (0.028, 0.010, 0.007), (0.0, ey_y + 0.008, ey_z + 0.002), (0, math.radians(-8), 0), mat=m["brass"], bevel=0.0015),
        gog_strap,
    ], "SciHeadgear", apply_uv=False)
    CC.bind_accessory_to_bones(head_acc, rig, "Head", scale=scale, keep_existing_uv=True)
    skinned.append(head_acc)

    CC.cull_body_faces(
        body,
        scale,
        lambda x, y, z, w: (
            (
                (w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)) > 0.50
                and z < 0.24
            )
            or (
                (w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0)) > 0.55
                and (0.24 <= z <= 0.92)
                and not (w.get("pelvis", 0) >= 0.35 and 0.80 <= z <= 0.90)
            )
            or (
                sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES)) < 0.15
                and sum(w.get(b, 0) for b in CC.HEAD_BONES) < 0.12
                and (0.90 <= z <= 1.36)
            )
        ),
    )

    parts = CC.split_dismemberment_parts(rig, skinned, m["gore_flesh"], m["bone"], scale=scale, z_neck_cut=1.45)
    CC.add_zombie_nla_animations(rig, scale=scale)
    tris = sum(len(p.vertices) - 2 for obj in parts.values() if obj for p in obj.data.polygons)
    print(f"[CHARS] zombie_scientist tris={tris}, parts={sorted(parts.keys())}")
    C.export_asset("characters", "zombie_scientist", export_anims=True)


def _build_brute(m):
    scale = 1.22
    def s(v):
        return (v[0] * scale, v[1] * scale, v[2] * scale)

    rig, body, eyes = CC.create_mpfb_zombie_base(
        "brute", scale=scale, age=0.62, muscle=0.92, weight=0.45, height=0.58,
        skin_mat=m["skin_brute"], eye_mat=m["eye_orange"], boot_sole=0.026, decimate_ratio=0.22,
    )
    skinned = [body, eyes]

    # Measure exact scaled eye coordinates so Brute gasmask & brow goggles sit flush on his actual face
    b_eye_vs = [v.co for v in eyes.data.vertices]
    b_ec = sum(b_eye_vs, Vector((0, 0, 0))) / max(1, len(b_eye_vs))
    b_ey = max(v.y for v in b_eye_vs)
    b_ex = max(abs(v.x) for v in b_eye_vs) * 0.72
    b_ez = b_ec.z
    ez_u = b_ez / scale

    # Full Heavy Hazmat Canvas Undersuit + Enclosed Hood over upper cranium/neck
    def keep_hazmat(x, y, z, w):
        hand_w = sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES) if "upperarm" not in b and "lowerarm" not in b and "clavicle" not in b)
        foot = w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)
        head = w.get("Head", 0)
        if hand_w >= 0.40 or foot >= 0.45:
            return False
        if head >= 0.50:
            return (z > ez_u + 0.028) or (y < 0.085)
        return z >= 0.18

    haz = CC.make_tailored_garment(body, rig, "BruteHazmat", m["hazmat_brute"], keep_hazmat, offset=0.0125, thickness=0.0045, uv_scale=2.2, scale=scale)
    if haz:
        skinned.append(haz)

    skinned.extend(_add_jackboots(body, rig, m, scale, heavy=True))

    # Contoured Steel Chest Breastplate & Groin Plate
    cuirass = CC.make_tailored_garment(
        body, rig, "BruteCuirass", m["panzer_armor"],
        lambda x, y, z, w: (w.get("spine_02", 0) + w.get("spine_03", 0) + w.get("spine_01", 0)) > 0.45 and (1.12 <= z <= 1.40) and abs(x) < 0.195,
        offset=0.019, thickness=0.014, uv_scale=2.6, wrinkle_amp=0.0005, scale=scale,
    )
    if cuirass:
        skinned.append(cuirass)

    groin = CC.make_tailored_garment(
        body, rig, "BruteGroin", m["panzer_armor"],
        lambda x, y, z, w: (w.get("pelvis", 0) + w.get("spine_01", 0)) > 0.45 and (0.87 <= z <= 1.00) and y > -0.04 and abs(x) < 0.145,
        offset=0.019, thickness=0.012, uv_scale=2.6, wrinkle_amp=0.0004, scale=scale,
    )
    if groin:
        skinned.append(groin)

    hbelt = _add_fitted_belt(body, rig, "BruteBelt", m["hazard_metal"], scale, z_lo=0.99, z_hi=1.065, offset=0.023, thickness=0.010)
    if hbelt:
        skinned.append(hbelt)

    kneepads = CC.make_tailored_garment(
        body, rig, "BruteKneeArmor", m["panzer_armor"],
        lambda x, y, z, w: (w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0)) > 0.45 and (0.45 <= z <= 0.56) and y > 0.02,
        offset=0.018, thickness=0.010, uv_scale=2.8, wrinkle_amp=0.0004, scale=scale,
    )
    if kneepads:
        skinned.append(kneepads)

    # Shoulder Pauldrons & Snug Tailored Forearm Vambraces
    for side, sfx, sx in (("L", "l", -1), ("R", "r", 1)):
        sh_orig, _, _ = CC.bone_frame(rig, f"upperarm_{sfx}", along_t=0.18)
        pauld = C.add_sphere(f"BrutePauld_{side}", 0.092 * scale, (0.95, 1.08, 1.04), sh_orig + Vector((sx * 0.02 * scale, 0.0, 0.02 * scale)), (0, math.radians(sx * 24), 0), segments=12, rings=8, mat=m["panzer_armor"])
        CC.bind_accessory_to_bones(pauld, rig, {f"upperarm_{sfx}": 0.75, f"clavicle_{sfx}": 0.25}, scale=scale, keep_existing_uv=True)
        skinned.append(pauld)

        vamb = CC.make_tailored_garment(
            body, rig, f"BruteVamb_{side}", m["panzer_armor"],
            lambda x, y, z, w, bn=f"lowerarm_{sfx}": w.get(bn, 0) > 0.45,
            offset=0.015, thickness=0.009, uv_scale=3.0, wrinkle_amp=0.0005, scale=scale,
        )
        if vamb:
            skinned.append(vamb)

    # Back Dual O2 Coolant Tanks + Manifold + Air Hoses + Chest Slash Wound
    chest_objs = [
        C.add_box("BruteChestSlash", s((0.15, 0.024, 0.028)), s((0.0, 0.145, 1.26)), (0, math.radians(-24), 0), mat=m["gore_flesh"], bevel=0.004 * scale),
        C.add_cyl("BruteTankL", 0.060 * scale, 0.36 * scale, s((-0.088, -0.165, 1.26)), vertices=14, mat=m["tank_metal"], bevel=0.008 * scale),
        C.add_cyl("BruteTankR", 0.060 * scale, 0.36 * scale, s((0.088, -0.165, 1.26)), vertices=14, mat=m["tank_metal"], bevel=0.008 * scale),
        C.add_cyl("BruteValveL", 0.020 * scale, 0.05 * scale, s((-0.088, -0.165, 1.455)), vertices=10, mat=m["brass"]),
        C.add_cyl("BruteValveR", 0.020 * scale, 0.05 * scale, s((0.088, -0.165, 1.455)), vertices=10, mat=m["brass"]),
        C.add_box("BruteManifold", s((0.24, 0.058, 0.055)), s((0.0, -0.155, 1.26)), mat=m["panzer_armor"], bevel=0.008 * scale),
    ]
    for sx in (-1, 1):
        chest_objs.append(C.add_tube_pipe(
            f"BruteHose_{sx}",
            [s((sx * 0.088, -0.155, 1.45)), s((sx * 0.112, -0.065, 1.48)), s((sx * 0.105, 0.045, 1.48)), (sx * 0.070 * scale, b_ey - 0.02 * scale, b_ez - 0.08 * scale)],
            radius=0.013 * scale, segments=8, mat=m["rubber"],
        ))
    brute_torso = C.join_objects(chest_objs, "BruteArmorRigged", apply_uv=False)
    CC.bind_accessory_to_bones(brute_torso, rig, lambda x, y, z: {"spine_03": 0.55, "spine_02": 0.45} if z > 1.12 else {"pelvis": 0.55, "spine_01": 0.45}, scale=scale, keep_existing_uv=True)
    skinned.append(brute_torso)

    # Full Tactical Gasmask Faceplate & Tactical Brow Helmet aligned directly from actual Brute eye bounds!
    head_objs = [
        C.add_sphere("BruteMaskSeal", 1.0, s((0.086, 0.068, 0.084)), (0.0, b_ey - 0.018 * scale, b_ez - 0.055 * scale), segments=12, rings=8, mat=m["rubber"]),
        C.add_box("BruteNoseBridge", s((0.026, 0.036, 0.050)), (0.0, b_ey + 0.014 * scale, b_ez - 0.010 * scale), mat=m["rubber"], bevel=0.004 * scale),
        C.add_cyl("BruteGogRimL", 0.026 * scale, 0.022 * scale, (-b_ex, b_ey + 0.008 * scale, b_ez), (math.radians(86), 0, math.radians(-14)), vertices=14, mat=m["panzer_armor"], bevel=0.003 * scale),
        C.add_cyl("BruteGogRimR", 0.026 * scale, 0.022 * scale, (b_ex, b_ey + 0.008 * scale, b_ez), (math.radians(86), 0, math.radians(14)), vertices=14, mat=m["panzer_armor"], bevel=0.003 * scale),
        C.add_cyl("BruteVisorL", 0.019 * scale, 0.008 * scale, (-b_ex - 0.002 * scale, b_ey + 0.018 * scale, b_ez), (math.radians(86), 0, math.radians(-14)), vertices=14, mat=m["visor_glow"]),
        C.add_cyl("BruteVisorR", 0.019 * scale, 0.008 * scale, (b_ex + 0.002 * scale, b_ey + 0.018 * scale, b_ez), (math.radians(86), 0, math.radians(14)), vertices=14, mat=m["visor_glow"]),
        C.add_cyl("BruteSnout", 0.034 * scale, 0.062 * scale, (0.0, b_ey + 0.022 * scale, b_ez - 0.068 * scale), (math.radians(104), 0, 0), vertices=14, mat=m["panzer_armor"], bevel=0.004 * scale),
        C.add_cyl("BruteRespGrille", 0.026 * scale, 0.014 * scale, (0.0, b_ey + 0.055 * scale, b_ez - 0.076 * scale), (math.radians(104), 0, 0), vertices=12, mat=m["rubber"]),
        C.add_cyl("BruteFilterL", 0.024 * scale, 0.044 * scale, (-0.054 * scale, b_ey + 0.010 * scale, b_ez - 0.072 * scale), (math.radians(94), 0, math.radians(-26)), vertices=12, mat=m["hazard_metal"], bevel=0.003 * scale),
        C.add_sphere("BruteCraniumCap", 1.0, s((0.102, 0.118, 0.088)), (0.0, b_ey - 0.115 * scale, b_ez + 0.052 * scale), (math.radians(-8), 0, 0), segments=14, rings=8, mat=m["panzer_armor"]),
        C.add_box("BruteBrowGuard", s((0.155, 0.062, 0.032)), (0.0, b_ey - 0.012 * scale, b_ez + 0.048 * scale), (math.radians(12), 0, 0), mat=m["panzer_trim"], bevel=0.006 * scale),
    ]
    brute_head = C.join_objects(head_objs, "BruteHeadgear", apply_uv=False)
    CC.bind_accessory_to_bones(brute_head, rig, "Head", scale=scale, keep_existing_uv=True)
    skinned.append(brute_head)

    CC.cull_body_faces(
        body,
        scale,
        lambda x, y, z, w: (
            (
                (w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)) > 0.50
                and z < 0.24
            )
            or (
                sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES) if "upperarm" not in b and "clavicle" not in b) < 0.15
                and sum(w.get(b, 0) for b in CC.HEAD_BONES) < 0.12
                and (0.24 <= z <= 1.38)
                and not (w.get("pelvis", 0) >= 0.35 and 0.80 <= z <= 0.90)
            )
        ),
    )

    parts = CC.split_dismemberment_parts(rig, skinned, m["gore_flesh"], m["bone"], scale=scale, z_neck_cut=1.45)
    CC.add_zombie_nla_animations(rig, scale=scale)
    tris = sum(len(p.vertices) - 2 for obj in parts.values() if obj for p in obj.data.polygons)
    print(f"[CHARS] zombie_brute tris={tris}, parts={sorted(parts.keys())}")
    C.export_asset("characters", "zombie_brute", export_anims=True)


def _build_worker_or_crawler(m, variant="worker", skip_legs=False):
    scale = 1.02 if not skip_legs else 1.0
    rig, body, eyes = CC.create_mpfb_zombie_base(
        variant, scale=scale, age=0.65, muscle=0.62, weight=0.30, height=0.52,
        skin_mat=m["skin_worker"], eye_mat=m["eye_amber"], boot_sole=0.022, decimate_ratio=0.30 if not skip_legs else 0.34,
    )
    skinned = [body, eyes]

    arm_all = CC.ARM_L_BONES | CC.ARM_R_BONES
    def keep_overalls(x, y, z, w):
        if sum(w.get(b, 0) for b in arm_all) > 0.30:
            return False
        if z > 1.18:
            return (y < 0.02 or x > 0.01) and z <= 1.40
        if skip_legs and z < 0.85:
            return False
        return 0.18 <= z <= 1.40

    overalls = CC.make_tailored_garment(body, rig, "WorkerOveralls", m["overalls_worker"], keep_overalls, offset=0.0095, thickness=0.0045, uv_scale=2.2, scale=scale)
    if overalls:
        skinned.append(overalls)

    if not skip_legs:
        skinned.extend(_add_jackboots(body, rig, m, scale, heavy=True))
    skinned.extend(_add_teeth_and_ribs(variant, m, scale, rig, add_ribs=True))

    # Fitted leather utility belt + snug right chest bib strap + wrench pouch
    wbelt = _add_fitted_belt(body, rig, "WorkerBelt", m["leather"], scale)
    if wbelt:
        skinned.append(wbelt)
    wstrap = CC.make_tailored_garment(
        body, rig, "WorkerBibStrap", m["overalls_worker"],
        lambda x, y, z, w: (w.get("spine_02", 0) + w.get("spine_03", 0)) > 0.45 and (1.18 <= z <= 1.42) and (0.045 <= x <= 0.095),
        offset=0.0135, thickness=0.004, uv_scale=2.8, scale=scale,
    )
    if wstrap:
        skinned.append(wstrap)
    wpouch = C.add_box("ToolPouch", (0.075 * scale, 0.055 * scale, 0.10 * scale), (-0.145 * scale, 0.045 * scale, 0.98 * scale), mat=m["leather"], bevel=0.006 * scale)
    CC.bind_accessory_to_bones(wpouch, rig, {"pelvis": 0.70, "spine_01": 0.30}, scale=scale, keep_existing_uv=True)
    skinned.append(wpouch)

    if not skip_legs:
        # Contoured Ribbed Miner Hard-Hat centered accurately on skull (0, 0.026, 1.668)
        yc = 0.026
        cap_rings = [
            [(math.cos(a) * 0.108 * scale, (yc + math.sin(a) * 0.124) * scale, 1.635 * scale) for a in [(i / 18) * 2.0 * math.pi for i in range(18)]],
            [(math.cos(a) * 0.104 * scale, (yc + math.sin(a) * 0.118) * scale, 1.678 * scale) for a in [(i / 18) * 2.0 * math.pi for i in range(18)]],
            [(math.cos(a) * 0.088 * scale, (yc + math.sin(a) * 0.100) * scale, 1.724 * scale) for a in [(i / 18) * 2.0 * math.pi for i in range(18)]],
            [(math.cos(a) * 0.048 * scale, (yc + math.sin(a) * 0.056) * scale, 1.754 * scale) for a in [(i / 18) * 2.0 * math.pi for i in range(18)]],
            [(math.cos(a) * 0.014 * scale, (yc + math.sin(a) * 0.016) * scale, 1.766 * scale) for a in [(i / 18) * 2.0 * math.pi for i in range(18)]],
        ]
        head_cap = C.join_objects([
            C.add_ring_loft("HardHatDome", cap_rings, mat=m["hazard_yellow"], smooth_angle=52.0),
            C.add_box("HatBrim", (0.140 * scale, 0.068 * scale, 0.011 * scale), (0.0, 0.145 * scale, 1.644 * scale), (math.radians(8), 0, 0), mat=m["hazard_yellow"], bevel=0.004 * scale),
            C.add_cyl("HeadLamp", 0.022 * scale, 0.032 * scale, (0.0, 0.148 * scale, 1.682 * scale), (math.radians(84), 0, 0), vertices=12, mat=m["chrome"], bevel=0.002 * scale),
            C.add_cyl("HeadLampLens", 0.016 * scale, 0.006 * scale, (0.0, 0.165 * scale, 1.684 * scale), (math.radians(84), 0, 0), vertices=12, mat=m["brass"]),
        ], "WorkerHeadGear", apply_uv=False)
        CC.bind_accessory_to_bones(head_cap, rig, "Head", scale=scale, keep_existing_uv=True)
        skinned.append(head_cap)
    else:
        cr_hair = CC.make_tailored_garment(
            body, rig, "CrawlerHair", m["zombie_hair"],
            lambda x, y, z, w: w.get("Head", 0) > 0.55 and ((z > 1.685 and y < 0.095) or (y < 0.015 and z > 1.595)),
            offset=0.008, thickness=0.008, uv_scale=3.2, wrinkle_amp=0.005, scale=scale,
        )
        if cr_hair:
            skinned.append(cr_hair)

    CC.cull_body_faces(
        body,
        scale,
        (
            (lambda x, y, z, w: (
                sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES)) < 0.15
                and sum(w.get(b, 0) for b in CC.HEAD_BONES) < 0.12
                and (0.91 <= z <= 1.12)
            ))
            if skip_legs
            else (lambda x, y, z, w: (
                (
                    (w.get("calf_l", 0) + w.get("calf_r", 0) + w.get("foot_l", 0) + w.get("foot_r", 0) + w.get("ball_l", 0) + w.get("ball_r", 0)) > 0.50
                    and z < 0.24
                )
                or (
                    (w.get("thigh_l", 0) + w.get("thigh_r", 0) + w.get("calf_l", 0) + w.get("calf_r", 0)) > 0.55
                    and (0.24 <= z <= 0.92)
                    and not (w.get("pelvis", 0) >= 0.35 and 0.80 <= z <= 0.90)
                )
                or (
                    sum(w.get(b, 0) for b in (CC.ARM_L_BONES | CC.ARM_R_BONES)) < 0.15
                    and sum(w.get(b, 0) for b in CC.HEAD_BONES) < 0.12
                    and (0.90 <= z <= 1.12)
                )
            ))
        ),
    )

    parts = CC.split_dismemberment_parts(rig, skinned, m["gore_flesh"], m["bone"], scale=scale, z_neck_cut=1.45, skip_legs=skip_legs)
    CC.add_zombie_nla_animations(rig, scale=scale, is_crawler=skip_legs)
    tris = sum(len(p.vertices) - 2 for obj in parts.values() if obj for p in obj.data.polygons)
    print(f"[CHARS] zombie_{variant} tris={tris}, parts={sorted(parts.keys())}")
    C.export_asset("characters", f"zombie_{variant}", export_anims=True)


def build_all_zombies():
    for variant, fn in [
        ("soldier", _build_soldier),
        ("scientist", _build_scientist),
        ("brute", _build_brute),
        ("worker", lambda m: _build_worker_or_crawler(m, "worker", skip_legs=False)),
        ("crawler", lambda m: _build_worker_or_crawler(m, "crawler", skip_legs=True)),
    ]:
        C.reset_scene()
        m = CC.build_char_materials()
        fn(m)


if __name__ == "__main__":
    build_all_zombies()
