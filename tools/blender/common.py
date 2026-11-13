"""Shared Blender 4.2 modeling, material, rigging, and glTF export helpers."""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BLEND_DIR = os.path.join(REPO_ROOT, "assets_src", "blend")
MODELS_DIR = os.path.join(REPO_ROOT, "assets", "models")
TEX_DIR = os.path.join(REPO_ROOT, "assets", "textures")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear_val(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def srgb_to_linear_col(col):
    if len(col) == 4:
        return (srgb_to_linear_val(col[0]), srgb_to_linear_val(col[1]), srgb_to_linear_val(col[2]), col[3])
    return (srgb_to_linear_val(col[0]), srgb_to_linear_val(col[1]), srgb_to_linear_val(col[2]))


def make_pbr_mat(
    name,
    base_color=(0.5, 0.5, 0.5, 1.0),
    metallic=0.0,
    roughness=0.5,
    emission=None,
    emission_strength=0.0,
    albedo_tex=None,
    normal_tex=None,
    roughness_tex=None,
    srgb=True,
    alpha=1.0,
):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bc = srgb_to_linear_col(base_color) if srgb else base_color
    bsdf.inputs["Base Color"].default_value = bc
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 0.999:
        mat.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = alpha
    if emission is not None and emission_strength > 0.0:
        ec = srgb_to_linear_col(emission[:3]) if srgb else emission[:3]
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    if albedo_tex and os.path.exists(albedo_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(albedo_tex)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if roughness_tex and os.path.exists(roughness_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(roughness_tex)
        tex.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])

    if normal_tex and os.path.exists(normal_tex):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(normal_tex)
        tex.image.colorspace_settings.name = "Non-Color"
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 0.85
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def assign_mat(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def smooth_shade(obj, auto_angle_deg=38.0):
    if obj.type != "MESH":
        return
    for poly in obj.data.polygons:
        poly.use_smooth = True
    # Add WeightedNormal / EdgeSplit modifier or sharp edges by angle
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    angle = math.radians(auto_angle_deg)
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            if edge.link_faces[0].normal.angle(edge.link_faces[1].normal, 0.0) > angle:
                edge.smooth = False
            else:
                edge.smooth = True
    bm.to_mesh(obj.data)
    bm.free()


def add_bevel(obj, width=0.004, segments=2):
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)
    return mod


def add_box(name, size=(0.1, 0.1, 0.1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        add_bevel(obj, width=bevel, segments=2)
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj)
    return obj


def add_cyl(name, radius=0.02, depth=0.2, loc=(0, 0, 0), rot=(0, 0, 0), vertices=20, mat=None, bevel=0.0015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if bevel > 0.0:
        add_bevel(obj, width=bevel, segments=1)
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj)
    return obj


def add_sphere(name, radius=0.05, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), segments=18, rings=12, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj, 60.0)
    return obj


def add_cone(name, r1=0.04, r2=0.0, depth=0.1, loc=(0, 0, 0), rot=(0, 0, 0), vertices=12, mat=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj)
    return obj


def add_torus(name, major=0.05, minor=0.01, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=24, minor_segments=10, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_mat(obj, mat)
    smooth_shade(obj, 60.0)
    return obj


def auto_uv_box(obj):
    if obj.type != "MESH":
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def join_objects(objs, final_name, apply_uv=True):
    bpy.ops.object.select_all(action="DESELECT")
    valid = [o for o in objs if o is not None and o.type == "MESH"]
    if not valid:
        return None
    for o in valid:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    if len(valid) > 1:
        bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = final_name
    if apply_uv:
        auto_uv_box(joined)
    return joined


def export_asset(sub_folder, asset_name, export_anims=False):
    blend_folder = os.path.join(BLEND_DIR, sub_folder)
    model_folder = os.path.join(MODELS_DIR, sub_folder)
    os.makedirs(blend_folder, exist_ok=True)
    os.makedirs(model_folder, exist_ok=True)

    blend_path = os.path.join(blend_folder, f"{asset_name}.blend")
    glb_path = os.path.join(model_folder, f"{asset_name}.glb")

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_animations=export_anims,
        export_nla_strips=export_anims,
        export_draco_mesh_compression_enable=False,
    )
    print(f"[BLENDER] Exported {asset_name} -> {glb_path}")
