#!/usr/bin/env python3
"""Download & cache CC0 character/texture assets and synthesize 1024x1024 UV-aligned
PBR skin, clothing, armor, eye, hellhound, gore, and decal textures for BUNKER 115.

CC0 Sources cached in /tmp/cc0_cache/chars/:
- Poly Haven (1K JPG PBR sets): caban, cotton_jersey, denim_fabric, brown_leather,
  rusty_metal_02, metal_plate_02, dark_rock_02
- MakeHuman CC0 (makehumancommunity/makehuman): low-poly eyes (.mhclo/.obj/brown_eye.png)
- OpenGameArt CC0: Micket's Wolf (wolf.zip), Jerd's Diving Helmet (Diving_Helmet.obj)
"""

import json
import math
import os
import subprocess
import sys
import time
import urllib.request
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_OUT = os.path.join(REPO_ROOT, "assets", "textures", "characters")
CACHE_DIR = "/tmp/cc0_cache/chars"
PH_DIR = os.path.join(CACHE_DIR, "polyhaven")
EYES_DIR = os.path.join(CACHE_DIR, "eyes")
OGA_DIR = os.path.join(CACHE_DIR, "oga")
BLENDER_BIN = os.environ.get("BLENDER_BIN", "/home/antigravity/.local/bin/blender")

POLYHAVEN_IDS = [
    "caban",
    "cotton_jersey",
    "denim_fabric",
    "brown_leather",
    "rusty_metal_02",
    "metal_plate_02",
    "dark_rock_02",
]


def _fetch_bytes(url: str, retries: int = 5, delay: float = 0.6) -> bytes:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Bunker115/2.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except Exception as exc:
            last_err = exc
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"Failed to download {url}: {last_err}")


def _download_if_missing(url: str, dst: str) -> str:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) > 64:
        return dst
    data = _fetch_bytes(url)
    with open(dst, "wb") as f:
        f.write(data)
    return dst


def fetch_cc0_sources() -> dict:
    """Download & cache Poly Haven textures, MakeHuman eyes, and OpenGameArt CC0 meshes."""
    for d in (CACHE_DIR, PH_DIR, EYES_DIR, OGA_DIR, TEX_OUT):
        os.makedirs(d, exist_ok=True)

    meta = {"polyhaven": {}, "oga": {}, "makehuman": {}}

    # 1. MakeHuman CC0 low-poly eyes
    mh_base = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/eyes"
    for rel, dst_name in [
        ("low-poly/low-poly.mhclo", "low-poly.mhclo"),
        ("low-poly/low-poly.obj", "low-poly.obj"),
        ("materials/brown.mhmat", "brown.mhmat"),
        ("materials/brown_eye.png", "brown_eye.png"),
    ]:
        _download_if_missing(f"{mh_base}/{rel}", os.path.join(EYES_DIR, dst_name))
    meta["makehuman"]["eyes"] = {
        "name": "MakeHuman Low-Poly Eyes & Brown Eye Texture",
        "author": "MakeHuman Community (Joel Palmius, Jonas Hauquier, Data Collection AB)",
        "url": "https://github.com/makehumancommunity/makehuman/tree/master/makehuman/data/eyes",
        "license": "CC0 1.0",
    }

    # 2. OpenGameArt CC0 base models (Wolf & Diving Helmet)
    oga_items = [
        ("wolf.zip", "https://opengameart.org/sites/default/files/wolf.zip",
         "Wolf", "Micket", "https://opengameart.org/content/wolf-1"),
        ("Diving_Helmet.obj", "https://opengameart.org/sites/default/files/Diving_Helmet.obj",
         "Diver's Helmet", "Jerd", "https://opengameart.org/content/divers-helmet"),
    ]
    for fname, url, title, author, page_url in oga_items:
        dst = os.path.join(OGA_DIR, fname)
        _download_if_missing(url, dst)
        if fname.endswith(".zip"):
            ex_dir = os.path.join(OGA_DIR, fname[:-4])
            if not os.path.exists(ex_dir):
                os.makedirs(ex_dir, exist_ok=True)
                with zipfile.ZipFile(dst) as zf:
                    zf.extractall(ex_dir)
        meta["oga"][fname] = {"name": title, "author": author, "url": page_url, "license": "CC0"}

    # 3. Poly Haven CC0 1K textures (Diffuse, nor_gl, Rough)
    for aid in POLYHAVEN_IDS:
        ad = os.path.join(PH_DIR, aid)
        os.makedirs(ad, exist_ok=True)
        diff_p = os.path.join(ad, f"{aid}_diff_1k.jpg")
        nor_p = os.path.join(ad, f"{aid}_nor_gl_1k.jpg")
        rgh_p = os.path.join(ad, f"{aid}_rough_1k.jpg")
        info_p = os.path.join(ad, "info.json")
        if not (os.path.exists(diff_p) and os.path.exists(nor_p) and os.path.exists(rgh_p) and os.path.exists(info_p)):
            time.sleep(0.35)
            files_json = json.loads(_fetch_bytes(f"https://api.polyhaven.com/files/{aid}").decode("utf-8"))
            time.sleep(0.25)
            info_json = json.loads(_fetch_bytes(f"https://api.polyhaven.com/info/{aid}").decode("utf-8"))
            with open(info_p, "w", encoding="utf-8") as f:
                json.dump(info_json, f, indent=2)
            for key, out_p in [("Diffuse", diff_p), ("nor_gl", nor_p), ("Rough", rgh_p)]:
                url = files_json[key]["1k"]["jpg"]["url"]
                _download_if_missing(url, out_p)
        else:
            with open(info_p, "r", encoding="utf-8") as f:
                info_json = json.load(f)
        authors = ", ".join(info_json.get("authors", {}).keys()) or "Poly Haven"
        meta["polyhaven"][aid] = {
            "name": info_json.get("name", aid),
            "author": authors,
            "url": f"https://polyhaven.com/a/{aid}",
            "license": "CC0",
        }

    with open(os.path.join(CACHE_DIR, "cc0_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[CC0] Cached {len(POLYHAVEN_IDS)} Poly Haven sets + MakeHuman eyes + OGA models in {CACHE_DIR}")
    return meta


# ---------------------------------------------------------------------------
# MPFB2 Exact UV-to-3D Atlas Extraction (runs once in Blender)
# ---------------------------------------------------------------------------

def ensure_mpfb_uv_atlas(size: int = 1024) -> dict:
    """Rasterize MPFB2's canonical UVMap into 1024x1024 3D coordinate & anatomical region buffers."""
    atlas_path = os.path.join(CACHE_DIR, f"mpfb_uv_atlas_{size}.npz")
    if os.path.exists(atlas_path):
        data = dict(np.load(atlas_path))
        if "eye_l" in data and "mouth" in data:
            return data

    py_expr = f"""
import bpy, addon_utils, bmesh, math, numpy as np
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

macro = TargetService.get_default_macro_info_dict()
macro.update({{'gender': 1.0, 'age': 0.65, 'muscle': 0.50, 'weight': 0.25, 'height': 0.50, 'proportions': 0.52}})
bm_obj = HumanService.create_human(mask_helpers=True, detailed_helpers=False, feet_on_ground=False, macro_detail_dict=macro)
sk = bm_obj.shape_key_add(name='__baked__', from_mix=True)
for kb in list(bm_obj.data.shape_keys.key_blocks):
    if kb != sk:
        bm_obj.shape_key_remove(kb)
bm_obj.shape_key_remove(sk)

rig = HumanService.add_builtin_rig(bm_obj, 'game_engine', import_weights=True)
eyes = HumanService.add_mhclo_asset('{EYES_DIR}/low-poly.mhclo', bm_obj, asset_type='Eyes')

# Unparent and remove Armature mod temporarily before applying transform for clean UV coordinate bake
bpy.ops.object.select_all(action='DESELECT')
for obj in (eyes, bm_obj):
    if obj.parent is not None:
        mw = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = mw
for mod in list(bm_obj.modifiers):
    if mod.type == 'ARMATURE':
        bm_obj.modifiers.remove(mod)

bm_obj.location = (0.0, 0.0, 0.845)
bm_obj.rotation_euler = (0.0, 0.0, math.pi)
eyes.location = (0.0, 0.0, 0.845)
eyes.rotation_euler = (0.0, 0.0, math.pi)
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
bm_obj.select_set(True)
eyes.select_set(True)
bpy.context.view_layer.objects.active = bm_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

ew = [v.co.copy() for v in eyes.data.vertices]
l_pts = [p for p in ew if p.x < 0.0]
r_pts = [p for p in ew if p.x > 0.0]
eye_l = np.array(sum(l_pts, Vector()) / max(1, len(l_pts)), dtype=np.float32)
eye_r = np.array(sum(r_pts, Vector()) / max(1, len(r_pts)), dtype=np.float32)

bm = bmesh.new()
bm.from_mesh(bm_obj.data)
uv_lay = bm.loops.layers.uv.active
d_lay = bm.verts.layers.deform.active
vg_h = bm_obj.vertex_groups['HelperGeometry'].index
vg_j = bm_obj.vertex_groups['JointCubes'].index
vg_lips = bm_obj.vertex_groups['lips'].index
vg_head = bm_obj.vertex_groups['head'].index
vg_hand_l = bm_obj.vertex_groups['hand_l'].index
vg_hand_r = bm_obj.vertex_groups['hand_r'].index
vg_nails = bm_obj.vertex_groups['fingernails'].index

mouth_pts = [v.co.copy() for v in bm.verts if vg_lips in v[d_lay]]
mouth_c = np.array(sum(mouth_pts, Vector()) / max(1, len(mouth_pts)), dtype=np.float32)

N = {size}
pos_map = np.zeros((N, N, 3), dtype=np.float32)
mask_map = np.zeros((N, N, 5), dtype=np.float32) # 0:body, 1:lips, 2:head, 3:hands, 4:nails

def raster_tri(u0, v0, u1, v1, u2, v2, a0, a1, a2, m0, m1, m2):
    px0, py0 = u0 * (N - 1), (1.0 - v0) * (N - 1)
    px1, py1 = u1 * (N - 1), (1.0 - v1) * (N - 1)
    px2, py2 = u2 * (N - 1), (1.0 - v2) * (N - 1)
    xmin = max(0, int(math.floor(min(px0, px1, px2))) - 1)
    xmax = min(N - 1, int(math.ceil(max(px0, px1, px2))) + 1)
    ymin = max(0, int(math.floor(min(py0, py1, py2))) - 1)
    ymax = min(N - 1, int(math.ceil(max(py0, py1, py2))) + 1)
    denom = (py1 - py2) * (px0 - px2) + (px2 - px1) * (py0 - py2)
    if abs(denom) < 1e-8:
        return
    inv_d = 1.0 / denom
    xs = np.arange(xmin, xmax + 1, dtype=np.float32)[None, :]
    ys = np.arange(ymin, ymax + 1, dtype=np.float32)[:, None]
    w0 = ((py1 - py2) * (xs - px2) + (px2 - px1) * (ys - py2)) * inv_d
    w1 = ((py2 - py0) * (xs - px2) + (px0 - px2) * (ys - py2)) * inv_d
    w2 = 1.0 - w0 - w1
    inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
    if not np.any(inside):
        return
    yy, xx = np.where(inside)
    gy = ymin + yy
    gx = xmin + xx
    bw0, bw1, bw2 = w0[yy, xx][:, None], w1[yy, xx][:, None], w2[yy, xx][:, None]
    pos_map[gy, gx] = bw0 * a0 + bw1 * a1 + bw2 * a2
    mask_map[gy, gx] = bw0 * m0 + bw1 * m1 + bw2 * m2

for f in bm.faces:
    if any(vg_h in v[d_lay] or vg_j in v[d_lay] for v in f.verts):
        continue
    pts = []
    uvs = []
    ms = []
    for lp in f.loops:
        v = lp.vert
        d = v[d_lay]
        pts.append(np.array([v.co.x, v.co.y, v.co.z], dtype=np.float32))
        uvs.append(lp[uv_lay].uv)
        ms.append(np.array([
            1.0,
            1.0 if vg_lips in d else 0.0,
            1.0 if vg_head in d else 0.0,
            1.0 if (vg_hand_l in d or vg_hand_r in d) else 0.0,
            1.0 if vg_nails in d else 0.0,
        ], dtype=np.float32))
    for k in range(1, len(pts) - 1):
        raster_tri(uvs[0].x, uvs[0].y, uvs[k].x, uvs[k].y, uvs[k+1].x, uvs[k+1].y,
                   pts[0], pts[k], pts[k+1], ms[0], ms[k], ms[k+1])

# Dilate UV island edges by 6 pixels to eliminate decimation/mipmap black seams
valid = mask_map[..., 0] > 0.1
for _ in range(6):
    inv = ~valid
    if not np.any(inv):
        break
    for dy, dx in ((-1,0),(1,0),(0,-1),(0,1)):
        sv = np.roll(valid, shift=(dy, dx), axis=(0, 1))
        take = inv & sv
        if np.any(take):
            pos_map[take] = np.roll(pos_map, shift=(dy, dx), axis=(0, 1))[take]
            mask_map[take] = np.roll(mask_map, shift=(dy, dx), axis=(0, 1))[take]
            valid[take] = True
            inv = ~valid

np.savez_compressed('{atlas_path}', pos=pos_map, mask=mask_map, eye_l=eye_l, eye_r=eye_r, mouth=mouth_c)
print('Saved UV atlas:', '{atlas_path}', 'eye_l:', eye_l, 'mouth:', mouth_c)
"""
    cmd = [
        "flock", "/tmp/bunker_blender.lock",
        BLENDER_BIN, "--background", "--python-exit-code", "1", "--python-expr", py_expr,
    ]
    subprocess.run(cmd, check=True)
    return dict(np.load(atlas_path))


# ---------------------------------------------------------------------------
# Procedural Noise & PBR Utilities
# ---------------------------------------------------------------------------

def value_noise(shape, scale=16, seed=42):
    rng = np.random.default_rng(seed)
    h, w = shape
    gh = max(2, h // max(1, scale))
    gw = max(2, w // max(1, scale))
    grid = rng.random((gh, gw), dtype=np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(shape, octaves=(64, 32, 16, 8, 4), weights=(0.40, 0.25, 0.18, 0.11, 0.06), seed=42):
    acc = np.zeros(shape, dtype=np.float32)
    for idx, (sc, wt) in enumerate(zip(octaves, weights)):
        acc += wt * value_noise(shape, scale=sc, seed=seed + idx * 19)
    lo, hi = acc.min(), acc.max()
    return (acc - lo) / max(1e-6, hi - lo)


def height_to_normal(height: np.ndarray, strength: float = 3.0) -> Image.Image:
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(height)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    r = np.clip((nx / norm * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g = np.clip((ny / norm * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b = np.clip((nz / norm * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")


def _load_ph(aid: str, size: int = 1024):
    ad = os.path.join(PH_DIR, aid)
    diff = np.asarray(Image.open(os.path.join(ad, f"{aid}_diff_1k.jpg")).convert("RGB").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
    nor = np.asarray(Image.open(os.path.join(ad, f"{aid}_nor_gl_1k.jpg")).convert("RGB").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
    rgh = np.asarray(Image.open(os.path.join(ad, f"{aid}_rough_1k.jpg")).convert("L").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    return diff, nor, rgh


def _blend_normal(nor_rgb: np.ndarray, extra_height: np.ndarray, extra_strength: float = 2.6) -> Image.Image:
    n_base = (nor_rgb / 255.0) * 2.0 - 1.0
    dx = np.roll(extra_height, -1, axis=1) - np.roll(extra_height, 1, axis=1)
    dy = np.roll(extra_height, -1, axis=0) - np.roll(extra_height, 1, axis=0)
    nx = n_base[..., 0] - dx * extra_strength
    ny = n_base[..., 1] - dy * extra_strength
    nz = np.maximum(0.25, n_base[..., 2])
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    rgb = np.stack([nx / norm * 0.5 + 0.5, ny / norm * 0.5 + 0.5, nz / norm * 0.5 + 0.5], axis=-1)
    return Image.fromarray(np.clip(rgb * 255.0, 0, 255).astype(np.uint8), mode="RGB")


def _save_pbr(name: str, alb: np.ndarray, nor_img: Image.Image, rgh: np.ndarray, emi: np.ndarray = None):
    Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(TEX_OUT, f"{name}_albedo.jpg"), format="JPEG", quality=89, optimize=True
    )
    nor_img.save(os.path.join(TEX_OUT, f"{name}_normal.jpg"), format="JPEG", quality=93, optimize=True)
    Image.fromarray(np.clip(rgh * 255.0, 0, 255).astype(np.uint8), mode="L").save(
        os.path.join(TEX_OUT, f"{name}_roughness.jpg"), format="JPEG", quality=88, optimize=True
    )
    if emi is not None:
        Image.fromarray(np.clip(emi, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(TEX_OUT, f"{name}_emission.jpg"), format="JPEG", quality=89, optimize=True
        )


def _neutralize_weave(rgb: np.ndarray, contrast: float = 1.35) -> np.ndarray:
    """Convert colored Poly Haven fabric RGB to centered monochrome weave gain so tints never shift orange."""
    lum = (rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114)
    mean = float(np.mean(lum))
    norm = np.clip((lum - mean) * contrast + 128.0, 32.0, 240.0) / 160.0
    return norm[..., None]


# ---------------------------------------------------------------------------
# 1. UV-Aligned Anatomical Zombie Skin Maps (1024x1024)
# ---------------------------------------------------------------------------

def build_zombie_skin_sets(atlas: dict):
    N = 1024
    pos = atlas["pos"]
    msk = atlas["mask"]
    eye_l = atlas["eye_l"]
    eye_r = atlas["eye_r"]
    mouth_c = atlas["mouth"]

    px, py, pz = pos[..., 0], pos[..., 1], pos[..., 2]
    m_body = msk[..., 0] > 0.05
    m_lips = np.clip(msk[..., 1], 0.0, 1.0)
    m_hands = np.clip(msk[..., 3], 0.0, 1.0)
    m_nails = np.clip(msk[..., 4], 0.0, 1.0)

    mottle = fbm((N, N), (64, 32, 16, 8, 4), (0.34, 0.26, 0.20, 0.12, 0.08), seed=701)
    pores = value_noise((N, N), scale=3, seed=709)
    veins_a = np.clip(1.0 - np.abs(fbm((N, N), (48, 24, 12, 6), (0.45, 0.28, 0.17, 0.10), seed=715) - 0.5) * 16.0, 0.0, 1.0)
    veins_b = np.clip(1.0 - np.abs(fbm((N, N), (32, 16, 8), (0.50, 0.30, 0.20), seed=721) - 0.5) * 18.0, 0.0, 1.0)
    veins = np.maximum(veins_a, veins_b * 0.7) * (0.55 + 0.45 * mottle)

    # Exact 3D anatomical eye sockets from loaded MakeHuman eye centers
    d_eye_l = np.sqrt((px - eye_l[0]) ** 2 + ((pz - eye_l[2]) * 1.35) ** 2 + np.maximum(0.0, eye_l[1] - 0.045 - py) ** 2 * 3.5)
    d_eye_r = np.sqrt((px - eye_r[0]) ** 2 + ((pz - eye_r[2]) * 1.35) ** 2 + np.maximum(0.0, eye_r[1] - 0.045 - py) ** 2 * 3.5)
    eye_bruise = np.clip(1.0 - np.minimum(d_eye_l, d_eye_r) / 0.036, 0.0, 1.0) * m_body
    eye_deep = np.clip(1.0 - np.minimum(d_eye_l, d_eye_r) / 0.020, 0.0, 1.0) * m_body

    # Cheek hollow shading & zygomatic contour relative to mouth_c / eye_l
    cheek_z = 0.5 * (eye_l[2] + mouth_c[2]) - 0.01
    cheek_hollow = (
        np.exp(-((np.abs(px) - 0.046) ** 2) / 0.0005 - ((pz - cheek_z) ** 2) / 0.0005)
        * np.clip((py - 0.05) * 20.0, 0.0, 1.0)
        * m_body
    )

    # Mouth, chin & neck arterial blood trails anchored at exact mouth_c
    d_mouth = np.sqrt((px * 0.85) ** 2 + ((pz - mouth_c[2]) * 1.25) ** 2 + np.maximum(0.0, mouth_c[1] - 0.05 - py) ** 2 * 3.0)
    chin_drip = np.exp(-((px / 0.045) ** 2)) * np.clip((mouth_c[2] + 0.01 - pz) / 0.14, 0.0, 1.0) * np.clip((pz - (mouth_c[2] - 0.28)) / 0.14, 0.0, 1.0)
    chin_drip *= np.clip((py - 0.03) * 18.0, 0.0, 1.0) * m_body
    blood_noise = fbm((N, N), (32, 16, 8, 4), (0.4, 0.3, 0.2, 0.1), seed=740)
    mouth_gore = np.clip(m_lips * 0.95 + np.clip(1.0 - d_mouth / 0.042, 0.0, 1.0) * 0.82 + chin_drip * (0.45 + 0.85 * blood_noise) - 0.20, 0.0, 1.0) * m_body

    # Exposed necrotic chest/rib laceration (chest height Z ~ mouth_c[2] - 0.25)
    chest_z = mouth_c[2] - 0.26
    chest_wound_d = np.sqrt(((px + 0.045) / 0.095) ** 2 + ((pz - chest_z) / 0.115) ** 2)
    chest_wound = np.clip((1.0 - chest_wound_d + (blood_noise - 0.45) * 0.45) * 2.2, 0.0, 1.0) * np.clip((py - 0.04) * 16.0, 0.0, 1.0) * m_body
    rib_stripes = np.clip(np.sin(pz * 145.0) * 0.5 + 0.5, 0.0, 1.0) ** 2.2
    exposed_ribs = chest_wound * rib_stripes * np.clip(1.0 - chest_wound_d * 1.15, 0.0, 1.0)

    # Dark soaked blood & battlefield grime on hands (darker & grittier instead of pale white)
    grime = fbm((N, N), (128, 64, 32, 16), (0.45, 0.28, 0.17, 0.10), seed=760)
    hand_grime = m_hands * (0.55 + 0.45 * grime)
    hand_blood = np.clip(m_hands * (0.52 + 0.82 * blood_noise - 0.22) * 1.75, 0.0, 1.0)

    variants = {
        "soldier":   {"skin": (114, 118, 102), "blood_amt": 0.95, "chest_rib": 1.0, "soot": 0.42, "seed": 1},
        "scientist": {"skin": (124, 124, 118), "blood_amt": 1.00, "chest_rib": 0.35, "soot": 0.26, "seed": 2},
        "brute":     {"skin": (104, 108, 92),  "blood_amt": 0.85, "chest_rib": 0.0, "soot": 0.56, "seed": 3},
        "worker":    {"skin": (120, 116, 100), "blood_amt": 0.98, "chest_rib": 1.0, "soot": 0.48, "seed": 4},
    }

    for vname, cfg in variants.items():
        base_rgb = np.array(cfg["skin"], dtype=np.float32)[None, None, :]
        alb = base_rgb * (0.78 + 0.36 * mottle[..., None]) * (0.94 + 0.12 * pores[..., None])

        # Purple-brown necrotic veins & mottled bruising (reduced on hands so hands stay flesh-toned!)
        vein_c = np.array([48.0, 38.0, 44.0], dtype=np.float32)[None, None, :]
        vein_w = 0.54 * veins * (1.0 - 0.55 * m_hands)
        alb = alb * (1.0 - vein_w[..., None]) + vein_c * vein_w[..., None]

        # Sunken dark orbital rings, hollow cheeks & warm soot grime on hands
        bruise_c = np.array([22.0, 17.0, 20.0], dtype=np.float32)[None, None, :]
        dark_mask = np.clip(eye_bruise * 0.86 + cheek_hollow * 0.52, 0.0, 0.90)
        alb = alb * (1.0 - dark_mask[..., None]) + bruise_c * dark_mask[..., None]
        hand_soot_c = np.array([42.0, 34.0, 28.0], dtype=np.float32)[None, None, :]
        alb = alb * (1.0 - hand_grime[..., None] * 0.42) + hand_soot_c * (hand_grime[..., None] * 0.42)
        alb *= (1.0 - 0.74 * eye_deep[..., None])

        # Soot & battlefield dirt
        soot_mask = np.clip((grime - 0.34) * cfg["soot"] * 2.0, 0.0, 0.62)
        alb *= (1.0 - soot_mask[..., None])

        # Deep wet & dried arterial blood on mouth/chin/hands/chest
        gore_mask = np.clip((mouth_gore + hand_blood * 0.94) * cfg["blood_amt"], 0.0, 1.0)
        wet_blood = np.array([84.0, 6.0, 6.0], dtype=np.float32)[None, None, :]
        dry_blood = np.array([34.0, 5.0, 5.0], dtype=np.float32)[None, None, :]
        blood_col = wet_blood * (0.40 + 0.60 * blood_noise[..., None]) + dry_blood * (0.60 - 0.60 * blood_noise[..., None])
        alb = alb * (1.0 - gore_mask[..., None] * 0.92) + blood_col * (gore_mask[..., None] * 0.92)

        # Exposed chest muscle & bone ribs
        if cfg["chest_rib"] > 0.05:
            cw = chest_wound * cfg["chest_rib"]
            er = exposed_ribs * cfg["chest_rib"]
            muscle_c = np.array([72.0, 9.0, 9.0], dtype=np.float32)[None, None, :]
            bone_c = np.array([170.0, 150.0, 120.0], dtype=np.float32)[None, None, :]
            alb = alb * (1.0 - cw[..., None]) + muscle_c * cw[..., None]
            alb = alb * (1.0 - er[..., None]) + bone_c * er[..., None]

        # Bloodied fingernails
        alb = alb * (1.0 - m_nails[..., None] * 0.72) + np.array([32.0, 6.0, 6.0], dtype=np.float32)[None, None, :] * (m_nails[..., None] * 0.72)

        h = 0.5 + 0.14 * mottle + 0.06 * pores + 0.10 * veins - 0.26 * chest_wound * cfg["chest_rib"] + 0.34 * exposed_ribs * cfg["chest_rib"]
        rgh = np.clip(0.62 + 0.18 * mottle - 0.42 * gore_mask - 0.32 * chest_wound * cfg["chest_rib"], 0.16, 0.92)
        _save_pbr(f"zombie_skin_{vname}", alb, height_to_normal(h, strength=3.5), rgh)


# ---------------------------------------------------------------------------
# 2. CoD Zombies Glowing Eyes (from CC0 MakeHuman brown_eye.png)
# ---------------------------------------------------------------------------

def build_zombie_eyes():
    eye_src = Image.open(os.path.join(EYES_DIR, "brown_eye.png")).convert("RGB").resize((512, 512), Image.Resampling.BILINEAR)
    arr = np.asarray(eye_src, dtype=np.float32)

    lum = (arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11) / 255.0
    r_minus_b = (arr[..., 0] - arr[..., 2]) / 255.0
    iris_mask = np.clip((r_minus_b - 0.06) * 6.0, 0.0, 1.0) * np.clip((0.45 - lum) * 3.5, 0.0, 1.0)
    pupil_mask = np.clip((0.06 - lum) * 20.0, 0.0, 1.0)

    veins = np.clip(1.0 - np.abs(fbm((512, 512), (32, 16, 8), (0.5, 0.3, 0.2), seed=801) - 0.5) * 14.0, 0.0, 1.0)
    sclera = arr * np.array([0.42, 0.30, 0.26], dtype=np.float32)[None, None, :]
    sclera = sclera * (1.0 - 0.55 * veins[..., None]) + np.array([105.0, 12.0, 10.0], dtype=np.float32)[None, None, :] * (0.55 * veins[..., None])

    for cname, iris_col, emi_col in [
        ("amber", (255.0, 168.0, 24.0), (255.0, 136.0, 14.0)),
        ("orange", (255.0, 82.0, 12.0), (255.0, 62.0, 6.0)),
    ]:
        iris_tex = np.array(iris_col, dtype=np.float32)[None, None, :] * (0.65 + 0.55 * lum[..., None])
        alb = sclera * (1.0 - iris_mask[..., None]) + iris_tex * iris_mask[..., None]
        alb *= (1.0 - pupil_mask[..., None] * 0.92)
        emi = np.array(emi_col, dtype=np.float32)[None, None, :] * np.clip(iris_mask[..., None] * (1.0 - pupil_mask[..., None] * 0.85), 0.0, 1.0)
        Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(TEX_OUT, f"zombie_eye_{cname}_albedo.jpg"), format="JPEG", quality=90, optimize=True
        )
        Image.fromarray(np.clip(emi, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(TEX_OUT, f"zombie_eye_{cname}_emission.jpg"), format="JPEG", quality=90, optimize=True
        )


# ---------------------------------------------------------------------------
# 3. Clothing, Armor, Hellhound & Gore Textures (from Poly Haven CC0 1K)
# ---------------------------------------------------------------------------

def build_clothing_armor_and_hound():
    N = 1024
    dirt = fbm((N, N), (128, 64, 32, 16), (0.42, 0.28, 0.18, 0.12), seed=820)
    blood_p = np.clip((fbm((N, N), (64, 32, 16, 8), (0.45, 0.30, 0.15, 0.10), seed=825) - 0.57) * 4.2, 0.0, 1.0)
    blood_rgb = np.array([72.0, 7.0, 7.0], dtype=np.float32)[None, None, :]

    # A) Soldier Feldgrau Wool Uniform (luminance-neutralized 'caban' weave -> authentic Feldgrau olive-grey!)
    cab_d, cab_n, cab_r = _load_ph("caban", N)
    cab_gain = _neutralize_weave(cab_d, contrast=1.35)
    sol = cab_gain * np.array([82.0, 90.0, 72.0], dtype=np.float32)[None, None, :]
    sol *= (0.72 + 0.38 * dirt[..., None])
    sol = sol * (1.0 - blood_p[..., None] * 0.82) + blood_rgb * (blood_p[..., None] * 0.82)
    _save_pbr("uniform_soldier", sol, _blend_normal(cab_n, dirt, 1.5), np.clip(cab_r * 0.85 + 0.18 - 0.35 * blood_p, 0.24, 0.96))

    # B) Scientist Blood-Stained Lab Coat (from Poly Haven 'cotton_jersey', aged dingy ivory)
    cot_d, cot_n, cot_r = _load_ph("cotton_jersey", N)
    sci_blood = np.clip((fbm((N, N), (96, 48, 24, 12), (0.45, 0.28, 0.17, 0.10), seed=833) - 0.52) * 3.6, 0.0, 1.0)
    cot_gain = _neutralize_weave(cot_d, contrast=1.25)
    lab = cot_gain * np.array([136.0, 132.0, 122.0], dtype=np.float32)[None, None, :]
    lab *= (0.74 + 0.32 * dirt[..., None])
    lab = lab * (1.0 - sci_blood[..., None] * 0.86) + blood_rgb * (sci_blood[..., None] * 0.86)
    _save_pbr("labcoat_scientist", lab, _blend_normal(cot_n, dirt, 1.2), np.clip(cot_r * 0.82 + 0.18 - 0.42 * sci_blood, 0.22, 0.96))

    # C) Worker Tattered Coveralls (from Poly Haven 'denim_fabric')
    den_d, den_n, den_r = _load_ph("denim_fabric", N)
    den_gain = _neutralize_weave(den_d, contrast=1.35)
    wrk = den_gain * np.array([62.0, 76.0, 96.0], dtype=np.float32)[None, None, :]
    wrk *= (0.64 + 0.44 * dirt[..., None])
    wrk = wrk * (1.0 - blood_p[..., None] * 0.78) + blood_rgb * (blood_p[..., None] * 0.78)
    _save_pbr("overalls_worker", wrk, _blend_normal(den_n, dirt, 1.4), np.clip(den_r * 0.85 + 0.15 - 0.35 * blood_p, 0.25, 0.96))

    # D) Brute Heavy Hazmat Canvas (luminance-neutralized weave -> grim weathered charcoal-olive)
    scorch = np.clip((fbm((N, N), (128, 64, 32), (0.5, 0.3, 0.2), seed=844) - 0.54) * 2.8, 0.0, 1.0)
    haz = cab_gain * np.array([72.0, 74.0, 56.0], dtype=np.float32)[None, None, :]
    haz *= (1.0 - 0.52 * scorch[..., None]) * (0.74 + 0.34 * dirt[..., None])
    haz = haz * (1.0 - blood_p[..., None] * 0.55) + blood_rgb * (blood_p[..., None] * 0.55)
    _save_pbr("hazmat_brute", haz, _blend_normal(cab_n, scorch, 1.8), np.clip(cab_r * 0.85 + 0.15, 0.35, 0.96))

    # D2) Panzer Boss Ballistic Kevlar / Pressure Diving Suit (dark charcoal steel-slate, zero orange spots!)
    panz_suit = den_gain * np.array([50.0, 54.0, 56.0], dtype=np.float32)[None, None, :]
    panz_suit *= (1.0 - 0.46 * scorch[..., None]) * (0.76 + 0.32 * dirt[..., None])
    _save_pbr("panzer_suit", panz_suit, _blend_normal(den_n, scorch, 1.6), np.clip(den_r * 0.75 + 0.22, 0.30, 0.92))

    # E) Leather Gear / Boots / Belts / Pouches (from Poly Haven 'brown_leather')
    lth_d, lth_n, lth_r = _load_ph("brown_leather", N)
    lth = lth_d * np.array([0.46, 0.40, 0.36], dtype=np.float32)[None, None, :] * (0.78 + 0.30 * dirt[..., None])
    _save_pbr("leather_gear", lth, _blend_normal(lth_n, dirt, 1.0), np.clip(lth_r * 0.9 + 0.08, 0.28, 0.88))

    # F) Stahlhelm Steel (neutralized dark matte weathered gunmetal olive-slate + subtle rust dust)
    rst_d, rst_n, rst_r = _load_ph("rusty_metal_02", N)
    rst_gain = _neutralize_weave(rst_d, contrast=1.15)
    helm = rst_gain * np.array([62.0, 68.0, 60.0], dtype=np.float32)[None, None, :]
    rust_speck = np.clip((scorch - 0.35) * 1.4, 0.0, 0.35)
    helm = helm * (1.0 - rust_speck[..., None]) + rst_d * np.array([0.42, 0.32, 0.24], dtype=np.float32)[None, None, :] * rust_speck[..., None]
    _save_pbr("stahlhelm_steel", helm, _blend_normal(rst_n, dirt, 1.0), np.clip(rst_r * 0.85 + 0.14, 0.38, 0.92))

    # G) Panzer Boss Armor (from Poly Haven 'metal_plate_02' + weathered rust)
    plt_d, plt_n, plt_r = _load_ph("metal_plate_02", N)
    rust_m = np.clip((fbm((N, N), (128, 64, 32, 16), (0.45, 0.28, 0.17, 0.10), seed=855) - 0.52) * 2.8, 0.0, 1.0)
    panz = plt_d * (1.0 - 0.48 * rust_m[..., None]) + rst_d * (0.48 * rust_m[..., None])
    panz *= np.array([0.56, 0.58, 0.56], dtype=np.float32)[None, None, :] * (1.0 - 0.40 * scorch[..., None])
    _save_pbr("panzer_armor", panz, _blend_normal(plt_n, rust_m, 2.2), np.clip(plt_r * 0.65 + 0.32 * rust_m, 0.24, 0.92))

    # G2) Weathered Industrial Hazard Metal (chipped dark mustard-amber stripes over scratched dark iron)
    yy_m, xx_m = np.mgrid[0:N, 0:N].astype(np.float32)
    stripe = ((np.sin((xx_m + yy_m) * 0.048) > 0.0)).astype(np.float32)
    chip = np.clip((fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=861) - 0.38) * 3.5, 0.0, 1.0)
    paint_col = np.array([138.0, 88.0, 18.0], dtype=np.float32)[None, None, :] * stripe[..., None] + np.array([26.0, 26.0, 28.0], dtype=np.float32)[None, None, :] * (1.0 - stripe[..., None])
    bare_iron = plt_d * np.array([0.45, 0.44, 0.42], dtype=np.float32)[None, None, :]
    haz_m = bare_iron * (1.0 - chip[..., None] * 0.85) + paint_col * (chip[..., None] * 0.85)
    haz_m *= (0.72 + 0.36 * (1.0 - scorch[..., None]))
    _save_pbr("hazard_metal", haz_m, _blend_normal(plt_n, chip, 1.8), np.clip(plt_r * 0.65 + 0.28 * (1.0 - chip), 0.26, 0.90))

    # H) Hellhound Charred Soot Wolf Fur + Sharp Sparse Crimson-Ember Fissures (~4% fissure density!)
    rk_d, rk_n, rk_r = _load_ph("dark_rock_02", N)
    rk_gain = _neutralize_weave(rk_d, contrast=1.30)
    fur_streak = fbm((N, N), (64, 32, 16, 4), (0.35, 0.30, 0.20, 0.15), seed=871)
    cracks_raw = np.clip(1.0 - np.abs(fbm((N, N), (96, 48, 24, 12), (0.45, 0.28, 0.17, 0.10), seed=877) - 0.5) * 38.0, 0.0, 1.0)
    cracks = (cracks_raw ** 4.0) * np.clip((fbm((N, N), (128, 64), (0.6, 0.4), seed=879) - 0.36) * 2.8, 0.0, 1.0)
    char_base = rk_gain * np.array([12.0, 10.0, 10.0], dtype=np.float32)[None, None, :] * (0.52 + 0.55 * fur_streak[..., None])
    lava_edge = np.array([190.0, 34.0, 4.0], dtype=np.float32)[None, None, :]
    lava_core = np.array([255.0, 124.0, 16.0], dtype=np.float32)[None, None, :]
    hound_alb = char_base * (1.0 - cracks[..., None]) + lava_edge * cracks[..., None]
    hound_emi = lava_edge * (cracks[..., None] * 0.78) + lava_core * (cracks[..., None] ** 3.0)
    _save_pbr("hellhound_hide", hound_alb, _blend_normal(rk_n, fur_streak - cracks * 1.1, 3.4), np.clip(rk_r * 0.86 + 0.12 - 0.45 * cracks, 0.22, 0.96), emi=hound_emi)

    # H2) Coarse Matted Dark Hair (512x512 fibrous strands so hair never looks like smooth plastic!)
    G = 512
    strand_x = value_noise((G, G), scale=3, seed=883)
    strand_y = fbm((G, G), (32, 16, 8, 4), (0.4, 0.3, 0.2, 0.1), seed=887)
    hair_h = 0.65 * strand_x + 0.35 * strand_y
    hair_alb = (np.array([28.0, 24.0, 21.0], dtype=np.float32)[None, None, :] * (0.55 + 0.85 * hair_h[..., None]))
    hair_alb *= (0.78 + 0.32 * dirt[:G, :G, None])
    _save_pbr("zombie_hair", hair_alb, height_to_normal(hair_h, strength=4.5), np.clip(0.84 + 0.14 * (1.0 - hair_h), 0.72, 0.98))

    # I) Gore / Severed Stump Flesh (512x512 deep arterial dark crimson)
    g_n = fbm((G, G), (32, 16, 8, 4), (0.4, 0.3, 0.2, 0.1), seed=890)
    gore_alb = np.zeros((G, G, 3), dtype=np.float32)
    gore_alb[..., 0] = 46 + 42 * g_n
    gore_alb[..., 1] = 5 + 6 * g_n
    gore_alb[..., 2] = 5 + 5 * g_n
    gore_rgh = np.clip(0.20 + 0.22 * (1.0 - g_n), 0.14, 0.58)
    _save_pbr("gore_flesh", gore_alb, height_to_normal(g_n, strength=4.2), gore_rgh)

    # J) Floor Blood Pool Decal (512x512 RGBA transparent splatter)
    yy, xx = np.mgrid[0:G, 0:G].astype(np.float32)
    nx_c = (xx - G * 0.5) / (G * 0.42)
    ny_c = (yy - G * 0.5) / (G * 0.42)
    rad = np.sqrt(nx_c ** 2 + ny_c ** 2)
    warp = (fbm((G, G), (64, 32, 16, 8), (0.45, 0.28, 0.17, 0.10), seed=901) - 0.5) * 0.65
    pool_mask = np.clip((0.72 - (rad + warp)) * 7.5, 0.0, 1.0)
    drops = np.clip((fbm((G, G), (16, 8, 4), (0.5, 0.3, 0.2), seed=907) - 0.66) * 12.0, 0.0, 1.0) * np.clip(1.05 - rad, 0.0, 1.0)
    alpha = np.clip(np.maximum(pool_mask, drops * 0.85), 0.0, 0.94)
    inner = np.clip((0.45 - rad) * 2.0, 0.0, 1.0)
    rgba = np.zeros((G, G, 4), dtype=np.float32)
    rgba[..., 0] = 68 - 22 * inner + 18 * g_n
    rgba[..., 1] = 5 + 3 * g_n
    rgba[..., 2] = 5 + 3 * g_n
    rgba[..., 3] = alpha * 255.0
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(os.path.join(TEX_OUT, "blood_pool_decal.png"))


def build_particle_sprites():
    """Generate soft radial RGBA sprites for Panzer's flamethrower jet & Hellhound embers."""
    # 1) 128x128 Turbulent Fire/Smoke Puff Sprite (white-core alpha mask tinted by vertex color_ramp)
    F = 128
    yy, xx = np.mgrid[0:F, 0:F].astype(np.float32)
    dx = (xx - F * 0.5) / (F * 0.44)
    dy = (yy - F * 0.5) / (F * 0.44)
    rad = np.sqrt(dx * dx + dy * dy)
    turb = fbm((F, F), (32, 16, 8, 4), (0.45, 0.28, 0.17, 0.10), seed=941)
    r_warp = rad + (turb - 0.5) * 0.48
    alpha = np.clip((1.0 - r_warp) * 1.65, 0.0, 1.0) ** 1.55
    core = np.clip((0.68 - r_warp) * 1.8, 0.0, 1.0)
    rgba = np.zeros((F, F, 4), dtype=np.float32)
    rgba[..., 0] = 255.0
    rgba[..., 1] = 175.0 + 80.0 * core
    rgba[..., 2] = 95.0 + 150.0 * (core ** 1.6)
    rgba[..., 3] = alpha * 245.0
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_OUT, "panzer_flame_puff.png")
    )

    # 2) 64x64 Soft Radial Ember Spark
    E = 64
    yy, xx = np.mgrid[0:E, 0:E].astype(np.float32)
    edx = (xx - E * 0.5) / (E * 0.45)
    edy = (yy - E * 0.5) / (E * 0.45)
    erad = np.sqrt(edx * edx + edy * edy)
    ea = np.clip(1.0 - erad, 0.0, 1.0) ** 2.2
    ergba = np.zeros((E, E, 4), dtype=np.float32)
    ergba[..., 0] = 255.0
    ergba[..., 1] = 140.0 + 110.0 * ea
    ergba[..., 2] = 25.0 + 140.0 * (ea ** 2.0)
    ergba[..., 3] = ea * 255.0
    Image.fromarray(np.clip(ergba, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_OUT, "char_ember_puff.png")
    )


def _prune_legacy_opaque_pngs():
    """Remove Pass 1 opaque PNGs replaced by JPGs while keeping RGBA decal & sprites."""
    keep = {"blood_pool_decal.png", "panzer_flame_puff.png", "char_ember_puff.png"}
    if not os.path.isdir(TEX_OUT):
        return
    for fn in os.listdir(TEX_OUT):
        if fn in keep or fn in {k + ".import" for k in keep}:
            continue
        if fn.endswith(".png") or fn.endswith(".png.import"):
            try:
                os.remove(os.path.join(TEX_OUT, fn))
            except OSError:
                pass


def write_credits(meta: dict):
    credits_path = os.path.join(REPO_ROOT, "docs", "credits_chars.md")
    os.makedirs(os.path.dirname(credits_path), exist_ok=True)
    lines = [
        "# Character, Hellhound & Boss CC0 Credits (Stream B)",
        "",
        "| Asset / Source | Author(s) | Source URL | License | Usage |",
        "| :--- | :--- | :--- | :--- | :--- |",
        "| MPFB2 / MakeHuman Base Mesh & Game Engine Rig | MakeHuman Community / Joel Palmius | https://github.com/makehumancommunity/mpfb2 | CC0 (mesh/targets/weights); GPL-3.0-or-later addon | Base anatomical zombie & boss meshes, morph targets, and 53-bone game rig |",
    ]
    mh = meta.get("makehuman", {}).get("eyes")
    if mh:
        lines.append(f"| {mh['name']} | {mh['author']} | {mh['url']} | {mh['license']} | Fitted zombie eyeballs & iris UV layout |")
    for _, item in sorted(meta.get("oga", {}).items()):
        lines.append(f"| {item['name']} | {item['author']} | {item['url']} | {item['license']} | Refined in Blender for Hellhound / Panzersoldat Boss |")
    for aid, item in sorted(meta.get("polyhaven", {}).items()):
        lines.append(f"| {item['name']} (`{aid}`) | {item['author']} | {item['url']} | {item['license']} | 1K PBR albedo/normal/roughness maps for uniforms, coats, leather, armor & hide |")
    lines.append("")
    with open(credits_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[CC0] Wrote {credits_path}")


def main():
    meta = fetch_cc0_sources()
    atlas = ensure_mpfb_uv_atlas(1024)
    build_zombie_skin_sets(atlas)
    build_zombie_eyes()
    build_clothing_armor_and_hound()
    build_particle_sprites()
    _prune_legacy_opaque_pngs()
    write_credits(meta)
    print("[CC0] Generated all character textures in", TEX_OUT)


if __name__ == "__main__":
    main()
