"""Download, import, clean, decimate, normalize, and export Poly Haven CC0 environment props
for BUNKER 115 v2 (Stream A).

Usage:
  flock /tmp/bunker_blender.lock /home/antigravity/.local/bin/blender \
      --background --python-exit-code 1 --python tools/blender/env_cc0_pipeline.py
"""

import json
import math
import os
import urllib.request
import bpy
from mathutils import Vector

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE_MODELS = "/tmp/cc0_cache/env/models"
OUT_BLEND = os.path.join(REPO_ROOT, "assets_src", "blend", "env_cc0")
OUT_GLB = os.path.join(REPO_ROOT, "assets", "models", "env_cc0")
MANIFEST_OUT = "/tmp/cc0_cache/env/models_manifest.json"

for d in (CACHE_MODELS, OUT_BLEND, OUT_GLB):
    os.makedirs(d, exist_ok=True)

USER_AGENT = "Bunker115-BlenderPipeline/2.0"

# Asset specs: (polyhaven_id, origin_mode, max_tris, scale_override, rot_z_deg, tex_max_px)
# origin_mode: "floor" (center XY, min_z=0), "ceiling" (center XY, max_z=0), "wall_back" (center X, max_y=0, center_z)
ASSETS = [
    ("ammo_box", "floor", 1200, 1.4, 0.0, 512),
    ("Barrel_01", "floor", 1500, 1.0, 0.0, 512),
    ("Barrel_02", "floor", 1500, 1.0, 0.0, 512),
    ("barrel_stove", "floor", 2200, 1.0, 0.0, 512),
    ("concrete_road_barrier", "floor", 1800, 1.0, 0.0, 512),
    ("concrete_road_barrier_02", "floor", 1800, 1.0, 0.0, 512),
    ("caged_hanging_light", "ceiling", 1800, 1.0, 0.0, 512),
    ("hanging_industrial_lamp", "ceiling", 1800, 1.0, 0.0, 512),
    ("industrial_wall_lamp", "wall_back", 1700, 1.25, 0.0, 512),
    ("street_lamp_01", "floor", 2800, 1.0, 0.0, 768),
    ("flood_lights", "floor", 3000, 0.45, 0.0, 512),
    ("chemistry_set", "floor", 3200, 1.0, 0.0, 512),
    ("bunsen_burner", "floor", 1200, 1.25, 0.0, 512),
    ("drawer_cabinet", "floor", 3200, 1.0, 0.0, 512),
    ("metal_office_desk", "floor", 2200, 1.0, 0.0, 512),
    ("portable_welding_cart", "floor", 3500, 1.0, 0.0, 512),
    ("industrial_storage_cart", "floor", 2600, 0.92, 0.0, 512),
    ("crowbar_01", "floor", 800, 1.25, 0.0, 512),
    ("cement_bag", "floor", 900, 1.15, 0.0, 512),
    ("covered_car", "floor", 4500, 1.0, 0.0, 1024),
    ("dead_tree_trunk", "floor", 3200, 0.85, 0.0, 512),
    ("boulder_01", "floor", 2400, 1.15, 0.0, 512),
    ("vintage_radio_transceiver", "floor", 2200, 1.0, 0.0, 512),
    ("power_box_01", "wall_back", 1900, 1.15, 0.0, 512),
    ("medical_box", "floor", 1200, 1.2, 0.0, 512),
    ("metal_toolbox", "floor", 1200, 1.2, 0.0, 512),
    ("steel_frame_shelves_01", "floor", 2400, 0.10, 0.0, 512),
    ("old_military_crate", "floor", 2000, 1.0, 0.0, 512),
]

LIGHT_BULB_HINTS = ("bulb", "lamp_glass", "emit", "emissive", "filament", "lens")


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def download_cached(url: str, dst_path: str) -> str:
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 0:
        return dst_path
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tmp = dst_path + ".part"
    data = fetch_bytes(url)
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dst_path)
    return dst_path


def download_polyhaven_gltf(asset_id: str) -> tuple[str, dict]:
    info_cache = os.path.join(CACHE_MODELS, asset_id, "_info.json")
    files_cache = os.path.join(CACHE_MODELS, asset_id, "_files.json")
    os.makedirs(os.path.join(CACHE_MODELS, asset_id), exist_ok=True)

    if os.path.exists(info_cache):
        with open(info_cache, "r", encoding="utf-8") as f:
            info = json.load(f)
    else:
        info = fetch_json(f"https://api.polyhaven.com/info/{asset_id}")
        with open(info_cache, "w", encoding="utf-8") as f:
            json.dump(info, f)

    if os.path.exists(files_cache):
        with open(files_cache, "r", encoding="utf-8") as f:
            files = json.load(f)
    else:
        files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
        with open(files_cache, "w", encoding="utf-8") as f:
            json.dump(files, f)

    g_entry = files.get("gltf", {}).get("1k", {}).get("gltf", {})
    gltf_url = g_entry.get("url")
    if not gltf_url:
        raise RuntimeError(f"No gltf/1k URL for {asset_id}")

    asset_dir = os.path.join(CACHE_MODELS, asset_id)
    gltf_local = os.path.join(asset_dir, os.path.basename(gltf_url))
    download_cached(gltf_url, gltf_local)

    for rel_path, meta in g_entry.get("include", {}).items():
        inc_url = meta.get("url")
        if inc_url:
            download_cached(inc_url, os.path.join(asset_dir, rel_path))

    authors = ", ".join(info.get("authors", {}).keys()) or "Poly Haven"
    credit = {
        "id": asset_id,
        "name": info.get("name", asset_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{asset_id}",
        "license": "CC0 1.0",
    }
    return gltf_local, credit


def count_tris(obj: bpy.types.Object) -> int:
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    if obj.data.polygons:
        used = {vi for p in obj.data.polygons for vi in p.vertices}
        verts = [obj.matrix_world @ obj.data.vertices[vi].co for vi in used]
    else:
        verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not verts:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    mn = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    mx = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    return mn, mx


def process_asset(
    asset_id: str,
    origin_mode: str,
    max_tris: int,
    scale_override: float,
    rot_z_deg: float,
    tex_max_px: int,
) -> dict:
    gltf_path, credit = download_polyhaven_gltf(asset_id)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=gltf_path)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No meshes imported for {asset_id}")

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.make_single_user(object=True, obdata=True, material=False)

    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()

    obj = bpy.context.active_object
    clean_name = asset_id.lower()
    obj.name = f"CC0_{asset_id}"

    if abs(scale_override - 1.0) > 1e-4 or abs(rot_z_deg) > 1e-4:
        obj.scale = (scale_override, scale_override, scale_override)
        obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    raw_tris = count_tris(obj)
    if raw_tris > max_tris:
        ratio = max(0.015, (max_tris / float(raw_tris)) * 0.95)
        mod = obj.modifiers.new(name="DecimateEnv", type="DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)

    final_tris = count_tris(obj)
    # Second pass if split edges prevented decimation from reaching target budget
    if final_tris > int(max_tris * 1.35):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        weld_thresh = 0.05 if final_tris > max_tris * 3 else 0.002
        bpy.ops.mesh.remove_doubles(threshold=weld_thresh)
        bpy.ops.object.mode_set(mode="OBJECT")
        cur_tris = max(1, count_tris(obj))
        if cur_tris > max_tris:
            ratio2 = max(0.015, (max_tris / float(cur_tris)) * 0.94)
            mod2 = obj.modifiers.new(name="DecimateEnv2", type="DECIMATE")
            mod2.decimate_type = "COLLAPSE"
            mod2.ratio = ratio2
            mod2.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=mod2.name)
        final_tris = count_tris(obj)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Normalize origin cleanly using only rendered polygon vertices
    mn, mx = world_bounds(obj)
    cx = (mn.x + mx.x) * 0.5
    cy = (mn.y + mx.y) * 0.5
    cz = (mn.z + mx.z) * 0.5
    if origin_mode == "floor":
        shift = Vector((-cx, -cy, -mn.z))
    elif origin_mode == "ceiling":
        shift = Vector((-cx, -cy, -mx.z))
    elif origin_mode == "wall_back":
        # Back plate at Blender +Y=0 (Godot -Z), protruding toward Godot +Z
        shift = Vector((-cx, -mx.y, -cz))
    else:
        shift = Vector((-cx, -cy, -mn.z))

    for v in obj.data.vertices:
        v.co += shift
    obj.data.update()

    mn2, mx2 = world_bounds(obj)
    dims = mx2 - mn2

    # Resize images and re-pack as compact JPEGs in /tmp cache so .blend stays compact (~15 MB total)
    tex_cache_dir = os.path.join(CACHE_MODELS, "_scaled_tex", clean_name)
    os.makedirs(tex_cache_dir, exist_ok=True)
    for img_idx, img in enumerate(bpy.data.images):
        if img.type != "IMAGE" or img.size[0] == 0 or img.size[1] == 0:
            continue
        w, h = img.size[0], img.size[1]
        if max(w, h) > tex_max_px:
            scale_px = tex_max_px / float(max(w, h))
            img.scale(max(64, int(round(w * scale_px))), max(64, int(round(h * scale_px))))
        if img.packed_file:
            img.unpack(method="REMOVE")
        jpg_tmp = os.path.join(tex_cache_dir, f"tex_{img_idx}.jpg")
        img.filepath_raw = jpg_tmp
        img.file_format = "JPEG"
        img.save()
        img.filepath = jpg_tmp
        img.reload()
        img.pack()

    mat_names = []
    for mat in obj.data.materials:
        if not mat or not mat.use_nodes:
            continue
        mat_names.append(mat.name)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            mlow = mat.name.lower()
            if any(h in mlow for h in LIGHT_BULB_HINTS) and "metal" not in mlow and "iron" not in mlow:
                if "Emission Strength" in bsdf.inputs and bsdf.inputs["Emission Strength"].default_value < 0.5:
                    bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.35, 1.0)
                    bsdf.inputs["Emission Strength"].default_value = 2.4

    blend_path = os.path.join(OUT_BLEND, f"{clean_name}.blend")
    glb_path = os.path.join(OUT_GLB, f"{clean_name}.glb")

    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_animations=False,
        export_draco_mesh_compression_enable=False,
        export_image_format="JPEG",
        export_jpeg_quality=82,
    )
    glb_kb = os.path.getsize(glb_path) // 1024
    print(
        f"[CC0] {asset_id:26s} -> {clean_name}.glb ({glb_kb:4d} KB) | "
        f"tris {raw_tris:6d} -> {final_tris:5d} | "
        f"size=({dims.x:.2f}, {dims.y:.2f}, {dims.z:.2f})m | mats={mat_names}"
    )

    credit.update({
        "output_glb": f"assets/models/env_cc0/{clean_name}.glb",
        "output_blend": f"assets_src/blend/env_cc0/{clean_name}.blend",
        "tris": final_tris,
        "dimensions_m": [round(dims.x, 3), round(dims.y, 3), round(dims.z, 3)],
        "glb_kb": glb_kb,
    })
    return credit


def main() -> None:
    credits = []
    for spec in ASSETS:
        credits.append(process_asset(*spec))
    with open(MANIFEST_OUT, "w", encoding="utf-8") as f:
        json.dump(credits, f, indent=2)
    print(f"[CC0 PIPELINE DONE] Exported {len(credits)} CC0 assets -> {OUT_GLB}")


if __name__ == "__main__":
    main()
