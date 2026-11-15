#!/usr/bin/env python3
"""Download & cache CC0 weapon/hand/texture assets from Poly Haven and synthesize
high-resolution weapon PBR sets, bullet hole decals, and CoD Zombies HUD textures
for BUNKER 115 v2 Stream C.

CC0 Sources cached in /tmp/cc0_cache/wpn/:
- Poly Haven 3D Model (1K glTF): bolt_action_rifle_7_62 (Mateusz Sadek, CC0)
- Poly Haven PBR Sets (1K JPG): fine_grained_wood, dark_wood, blue_metal_plate,
  metal_plate_02, rusty_metal_02, brown_leather, caban, cotton_jersey
"""

import json
import math
import os
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_WPN = os.path.join(REPO_ROOT, "assets", "textures", "weapons")
TEX_UI = os.path.join(REPO_ROOT, "assets", "textures", "ui")
CACHE_DIR = "/tmp/cc0_cache/wpn"
PH_TEX_DIR = os.path.join(CACHE_DIR, "polyhaven")
PH_RIFLE_DIR = os.path.join(CACHE_DIR, "rifle")

POLYHAVEN_TEX_IDS = [
    "fine_grained_wood",
    "dark_wood",
    "blue_metal_plate",
    "metal_plate_02",
    "rusty_metal_02",
    "brown_leather",
    "caban",
    "cotton_jersey",
]


def _fetch_bytes(url: str, retries: int = 5, delay: float = 0.6) -> bytes:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Bunker115/2.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
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
    for d in (CACHE_DIR, PH_TEX_DIR, PH_RIFLE_DIR, TEX_WPN, TEX_UI):
        os.makedirs(d, exist_ok=True)

    meta = {"polyhaven_models": {}, "polyhaven_textures": {}}

    # 1. Poly Haven scanned CC0 Bolt-Action Rifle 7.62 (1K glTF + bin + textures)
    rifle_gltf = os.path.join(PH_RIFLE_DIR, "bolt_action_rifle_7_62_1k.gltf")
    rifle_info_p = os.path.join(PH_RIFLE_DIR, "info.json")
    rifle_files_p = os.path.join(PH_RIFLE_DIR, "files.json")
    if not (os.path.exists(rifle_gltf) and os.path.exists(rifle_info_p) and os.path.exists(rifle_files_p)):
        files_json = json.loads(_fetch_bytes("https://api.polyhaven.com/files/bolt_action_rifle_7_62").decode("utf-8"))
        info_json = json.loads(_fetch_bytes("https://api.polyhaven.com/info/bolt_action_rifle_7_62").decode("utf-8"))
        with open(rifle_files_p, "w", encoding="utf-8") as f:
            json.dump(files_json, f, indent=2)
        with open(rifle_info_p, "w", encoding="utf-8") as f:
            json.dump(info_json, f, indent=2)
    else:
        with open(rifle_files_p, "r", encoding="utf-8") as f:
            files_json = json.load(f)
        with open(rifle_info_p, "r", encoding="utf-8") as f:
            info_json = json.load(f)

    g1k = files_json["gltf"]["1k"]["gltf"]
    _download_if_missing(g1k["url"], rifle_gltf)
    for rel, spec in g1k.get("include", {}).items():
        _download_if_missing(spec["url"], os.path.join(PH_RIFLE_DIR, rel))

    meta["polyhaven_models"]["bolt_action_rifle_7_62"] = {
        "name": info_json.get("name", "Bolt Action Rifle 7.62"),
        "author": ", ".join(info_json.get("authors", {}).keys()) or "Mateusz Sadek",
        "url": "https://polyhaven.com/a/bolt_action_rifle_7_62",
        "license": "CC0",
    }

    # 2. Poly Haven 1K PBR texture sets
    for aid in POLYHAVEN_TEX_IDS:
        ad = os.path.join(PH_TEX_DIR, aid)
        os.makedirs(ad, exist_ok=True)
        diff_p = os.path.join(ad, f"{aid}_diff_1k.jpg")
        nor_p = os.path.join(ad, f"{aid}_nor_gl_1k.jpg")
        rgh_p = os.path.join(ad, f"{aid}_rough_1k.jpg")
        info_p = os.path.join(ad, "info.json")
        if not (os.path.exists(diff_p) and os.path.exists(nor_p) and os.path.exists(rgh_p) and os.path.exists(info_p)):
            time.sleep(0.25)
            fj = json.loads(_fetch_bytes(f"https://api.polyhaven.com/files/{aid}").decode("utf-8"))
            time.sleep(0.15)
            ij = json.loads(_fetch_bytes(f"https://api.polyhaven.com/info/{aid}").decode("utf-8"))
            with open(info_p, "w", encoding="utf-8") as f:
                json.dump(ij, f, indent=2)
            for key, out_p in [("Diffuse", diff_p), ("nor_gl", nor_p), ("Rough", rgh_p)]:
                url = fj[key]["1k"]["jpg"]["url"]
                _download_if_missing(url, out_p)
        else:
            with open(info_p, "r", encoding="utf-8") as f:
                ij = json.load(f)
        meta["polyhaven_textures"][aid] = {
            "name": ij.get("name", aid),
            "author": ", ".join(ij.get("authors", {}).keys()) or "Poly Haven",
            "url": f"https://polyhaven.com/a/{aid}",
            "license": "CC0",
        }

    with open(os.path.join(CACHE_DIR, "wpn_cc0_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[WPN-CC0] Cached Poly Haven rifle + {len(POLYHAVEN_TEX_IDS)} PBR sets in {CACHE_DIR}")
    return meta


# ---------------------------------------------------------------------------
# Noise & Image Utilities
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
        acc += wt * value_noise(shape, scale=sc, seed=seed + idx * 17)
    lo, hi = acc.min(), acc.max()
    return (acc - lo) / max(1e-6, hi - lo)


def height_to_normal(height: np.ndarray, strength: float = 3.0) -> Image.Image:
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(height)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    rgb = np.stack([nx / norm * 0.5 + 0.5, ny / norm * 0.5 + 0.5, nz / norm * 0.5 + 0.5], axis=-1)
    return Image.fromarray(np.clip(rgb * 255.0, 0, 255).astype(np.uint8), mode="RGB")


def _load_ph(aid: str, size: int = 512):
    ad = os.path.join(PH_TEX_DIR, aid)
    diff = np.asarray(Image.open(os.path.join(ad, f"{aid}_diff_1k.jpg")).convert("RGB").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
    nor = np.asarray(Image.open(os.path.join(ad, f"{aid}_nor_gl_1k.jpg")).convert("RGB").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
    rgh = np.asarray(Image.open(os.path.join(ad, f"{aid}_rough_1k.jpg")).convert("L").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    return diff, nor, rgh


def _blend_normal(nor_rgb: np.ndarray, extra_height: np.ndarray, extra_strength: float = 2.0) -> Image.Image:
    n_base = (nor_rgb / 255.0) * 2.0 - 1.0
    dx = np.roll(extra_height, -1, axis=1) - np.roll(extra_height, 1, axis=1)
    dy = np.roll(extra_height, -1, axis=0) - np.roll(extra_height, 1, axis=0)
    nx = n_base[..., 0] - dx * extra_strength
    ny = n_base[..., 1] - dy * extra_strength
    nz = np.maximum(0.25, n_base[..., 2])
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    rgb = np.stack([nx / norm * 0.5 + 0.5, ny / norm * 0.5 + 0.5, nz / norm * 0.5 + 0.5], axis=-1)
    return Image.fromarray(np.clip(rgb * 255.0, 0, 255).astype(np.uint8), mode="RGB")


def _neutralize_gain(rgb: np.ndarray, contrast: float = 1.25) -> np.ndarray:
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    mean = float(np.mean(lum))
    return (np.clip((lum - mean) * contrast + 128.0, 36.0, 240.0) / 145.0)[..., None]


def _save_wpn_pbr(name: str, alb: np.ndarray, nor_img: Image.Image, rgh: np.ndarray, ext: str = "png"):
    fmt = "JPEG" if ext == "jpg" else "PNG"
    kw = {"format": fmt, "optimize": True}
    if fmt == "JPEG":
        kw["quality"] = 90
    Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(TEX_WPN, f"{name}_albedo.{ext}"), **kw
    )
    nor_img.save(os.path.join(TEX_WPN, f"{name}_normal.{ext}"), **kw)
    Image.fromarray(np.clip(rgh * 255.0, 0, 255).astype(np.uint8), mode="L").save(
        os.path.join(TEX_WPN, f"{name}_roughness.{ext}"), **kw
    )


# ---------------------------------------------------------------------------
# 1. Weapon, Glove & Sleeve PBR Maps (512x512 crisp CC0-derived)
# ---------------------------------------------------------------------------

def build_weapon_pbr_sets():
    N = 512
    scratches = np.clip(1.0 - np.abs(fbm((N, N), (64, 32, 16, 4), (0.4, 0.3, 0.2, 0.1), seed=21) - 0.5) * 14.0, 0.0, 1.0)
    brush_h = value_noise((N, N), scale=2, seed=29)
    brush_streak = np.mean(brush_h.reshape(N, N // 8, 8), axis=2, keepdims=True)
    brush = np.repeat(brush_streak, 8, axis=2).reshape(N, N)
    grime = fbm((N, N), (64, 32, 16, 8), (0.45, 0.28, 0.17, 0.10), seed=37)

    # A) Gun Steel (blued gunmetal with fine lathe brush + micro edge scratches)
    blu_d, blu_n, blu_r = _load_ph("blue_metal_plate", N)
    blu_gain = _neutralize_gain(blu_d, 1.2)
    steel_alb = blu_gain * np.array([62.0, 68.0, 76.0], dtype=np.float32)[None, None, :]
    steel_alb = steel_alb * (0.88 + 0.18 * brush[..., None]) + np.array([135.0, 142.0, 150.0], dtype=np.float32)[None, None, :] * (scratches[..., None] * 0.22)
    steel_rgh = np.clip(blu_r * 0.55 + 0.22 - scratches * 0.12 + grime * 0.10, 0.16, 0.72)
    _save_wpn_pbr("gun_steel", steel_alb, _blend_normal(blu_n, brush * 0.4 + scratches * 0.6, 1.4), steel_rgh, ext="png")

    # Dark Parkarized Receiver Steel (from metal_plate_02)
    plt_d, plt_n, plt_r = _load_ph("metal_plate_02", N)
    plt_gain = _neutralize_gain(plt_d, 1.25)
    dark_alb = plt_gain * np.array([34.0, 36.0, 40.0], dtype=np.float32)[None, None, :] * (0.85 + 0.22 * grime[..., None])
    dark_alb += np.array([96.0, 100.0, 108.0], dtype=np.float32)[None, None, :] * (scratches[..., None] * 0.18)
    _save_wpn_pbr("dark_steel", dark_alb, _blend_normal(plt_n, scratches, 1.2), np.clip(plt_r * 0.6 + 0.24, 0.20, 0.76), ext="jpg")

    # B) Walnut Wood (rich oiled WWII rifle stock grain from fine_grained_wood)
    wd_d, wd_n, wd_r = _load_ph("fine_grained_wood", N)
    wal_alb = wd_d * np.array([0.82, 0.66, 0.54], dtype=np.float32)[None, None, :] * (0.82 + 0.24 * (1.0 - grime[..., None] * 0.4))
    wal_rgh = np.clip(wd_r * 0.72 + 0.18, 0.22, 0.75)
    _save_wpn_pbr("walnut", wal_alb, _blend_normal(wd_n, grime, 0.8), wal_rgh, ext="png")

    # Dark Walnut for Wunderwaffe stock
    dw_d, dw_n, dw_r = _load_ph("dark_wood", N)
    wund_w = dw_d * np.array([0.92, 0.80, 0.72], dtype=np.float32)[None, None, :]
    _save_wpn_pbr("wunderwaffe_wood", wund_w, Image.fromarray(dw_n.astype(np.uint8)), np.clip(dw_r * 0.78 + 0.14, 0.22, 0.72), ext="jpg")

    # C) Checkered Bakelite Grip (sharp crosshatch diamond knurling + phenolic resin)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    d1 = np.abs(np.sin((xx + yy) * (math.pi / 12.0)))
    d2 = np.abs(np.sin((xx - yy) * (math.pi / 12.0)))
    knurl = np.minimum(d1, d2) ** 0.75
    bak_base = np.array([62.0, 24.0, 14.0], dtype=np.float32)[None, None, :] * (0.65 + 0.45 * knurl[..., None])
    bak_base *= (0.84 + 0.22 * grime[..., None])
    _save_wpn_pbr("bakelite", bak_base, height_to_normal(knurl * 0.75 + grime * 0.15, 3.8), np.clip(0.32 + 0.28 * (1.0 - knurl), 0.24, 0.78), ext="png")

    # D) Aged Brass & Oxidized Copper (for Ray Gun & Wunderwaffe Tesla coils!)
    rst_d, rst_n, rst_r = _load_ph("rusty_metal_02", N)
    rst_gain = _neutralize_gain(rst_d, 1.15)
    brass_alb = rst_gain * np.array([175.0, 128.0, 52.0], dtype=np.float32)[None, None, :] * (0.85 + 0.22 * brush[..., None])
    brass_alb = brass_alb * (1.0 - grime[..., None] * 0.35) + np.array([68.0, 56.0, 32.0], dtype=np.float32)[None, None, :] * (grime[..., None] * 0.35)
    _save_wpn_pbr("brass", brass_alb, _blend_normal(rst_n, brush, 1.1), np.clip(rst_r * 0.48 + 0.20, 0.16, 0.68), ext="png")

    cop_alb = rst_gain * np.array([186.0, 92.0, 48.0], dtype=np.float32)[None, None, :] * (0.86 + 0.20 * brush[..., None])
    patina = np.clip((grime - 0.56) * 3.0, 0.0, 0.45)
    cop_alb = cop_alb * (1.0 - patina[..., None]) + np.array([58.0, 118.0, 102.0], dtype=np.float32)[None, None, :] * patina[..., None]
    _save_wpn_pbr("copper", cop_alb, _blend_normal(rst_n, scratches, 1.2), np.clip(rst_r * 0.45 + 0.22 + patina * 0.35, 0.16, 0.78), ext="jpg")

    # E) First-Person Combat Leather Gloves (from Poly Haven brown_leather)
    lth_d, lth_n, lth_r = _load_ph("brown_leather", N)
    lth_alb = lth_d * np.array([0.42, 0.36, 0.32], dtype=np.float32)[None, None, :] * (0.80 + 0.28 * (1.0 - grime[..., None] * 0.4))
    _save_wpn_pbr("fp_leather", lth_alb, _blend_normal(lth_n, scratches, 1.0), np.clip(lth_r * 0.85 + 0.10, 0.28, 0.86), ext="png")

    # F) First-Person WWII Olive Wool Sleeve (luminance-neutralized Poly Haven caban weave)
    cab_d, cab_n, cab_r = _load_ph("caban", N)
    cab_gain = _neutralize_gain(cab_d, 1.35)
    slv_alb = cab_gain * np.array([72.0, 82.0, 62.0], dtype=np.float32)[None, None, :] * (0.76 + 0.30 * grime[..., None])
    _save_wpn_pbr("fp_sleeve", slv_alb, _blend_normal(cab_n, grime, 1.3), np.clip(cab_r * 0.85 + 0.16, 0.45, 0.96), ext="png")

    # G) First-Person Anatomical Hand/Wrist Skin (natural weathered soldier skin w/ pores & dirt)
    pores = value_noise((N, N), scale=3, seed=55)
    veins = np.clip(1.0 - np.abs(fbm((N, N), (32, 16, 8), (0.5, 0.3, 0.2), seed=59) - 0.5) * 18.0, 0.0, 1.0)
    skin_base = np.array([182.0, 136.0, 110.0], dtype=np.float32)[None, None, :]
    skin_alb = skin_base * (0.88 + 0.18 * fbm((N, N), (48, 24, 12), (0.5, 0.3, 0.2), seed=61)[..., None]) * (0.94 + 0.10 * pores[..., None])
    skin_alb = skin_alb * (1.0 - veins[..., None] * 0.18) + np.array([96.0, 92.0, 108.0], dtype=np.float32)[None, None, :] * (veins[..., None] * 0.18)
    skin_alb = skin_alb * (1.0 - grime[..., None] * 0.22) + np.array([62.0, 50.0, 42.0], dtype=np.float32)[None, None, :] * (grime[..., None] * 0.22)
    _save_wpn_pbr("fp_skin", skin_alb, height_to_normal(pores * 0.5 + grime * 0.3, 2.4), np.clip(0.46 + 0.22 * grime, 0.34, 0.78), ext="jpg")

    # H) Pack-a-Punch Element-115 Engraved Runic Camo (crisp silver/cyan circuit filigree)
    P = 512
    img_a = Image.new("RGB", (P, P), (22, 30, 44))
    img_e = Image.new("RGB", (P, P), (0, 0, 0))
    da = ImageDraw.Draw(img_a)
    de = ImageDraw.Draw(img_e)
    rng = np.random.default_rng(115)
    # Brushed cobalt-gunmetal background
    bg = np.asarray(img_a, dtype=np.float32) + (brush - 0.5)[..., None] * 18.0
    img_a = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), mode="RGB")
    da = ImageDraw.Draw(img_a)
    # Geometric Element-115 circuit traces & arcane rings
    for _ in range(42):
        x0, y0 = int(rng.integers(0, P)), int(rng.integers(0, P))
        for _seg in range(4):
            ang = int(rng.integers(0, 8)) * (math.pi * 0.25)
            ln = int(rng.integers(24, 92))
            x1 = x0 + int(round(math.cos(ang) * ln))
            y1 = y0 + int(round(math.sin(ang) * ln))
            da.line([(x0, y0), (x1, y1)], fill=(120, 200, 235), width=3)
            de.line([(x0, y0), (x1, y1)], fill=(35, 215, 255), width=3)
            da.ellipse((x1 - 4, y1 - 4, x1 + 4, y1 + 4), fill=(195, 240, 255))
            de.ellipse((x1 - 4, y1 - 4, x1 + 4, y1 + 4), fill=(90, 245, 255))
            x0, y0 = x1 % P, y1 % P
    for cx, cy, r in [(128, 128, 46), (384, 384, 46), (384, 128, 32), (128, 384, 32)]:
        da.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(145, 210, 240), width=3)
        de.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(45, 220, 255), width=3)
        da.ellipse((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), outline=(85, 165, 210), width=2)
        de.ellipse((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), outline=(25, 160, 230), width=2)
    img_a.save(os.path.join(TEX_WPN, "pap_albedo.png"), format="PNG", optimize=True)
    img_e.filter(ImageFilter.GaussianBlur(radius=0.8)).save(os.path.join(TEX_WPN, "pap_emission.png"), format="PNG", optimize=True)


# ---------------------------------------------------------------------------
# 2. Bullet Hole Decals & Muzzle Sprite
# ---------------------------------------------------------------------------

def build_decal_and_fx_textures():
    S = 256
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    nx = (xx - S * 0.5) / (S * 0.44)
    ny = (yy - S * 0.5) / (S * 0.44)
    rad = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)
    noise = fbm((S, S), (32, 16, 8, 4), (0.45, 0.28, 0.17, 0.10), seed=313)
    cracks = np.clip(np.cos(ang * 9.0 + noise * 6.0) * 0.5 + 0.5, 0.0, 1.0) ** 4.0

    # Concrete bullet impact decal (deep black hole + chipped grey concrete rim + radial cracks)
    hole = np.clip((0.26 + (noise - 0.5) * 0.09 - rad) * 18.0, 0.0, 1.0)
    chip_ring = np.clip((0.52 + cracks * 0.28 + (noise - 0.5) * 0.16 - rad) * 8.0, 0.0, 1.0)
    alpha = np.clip(np.maximum(hole, chip_ring * 0.85) * np.clip((1.0 - rad) * 3.0, 0.0, 1.0), 0.0, 0.96)
    rgba = np.zeros((S, S, 4), dtype=np.float32)
    base_dust = 72.0 + 36.0 * noise
    rgba[..., 0] = base_dust * (1.0 - hole) + 8.0 * hole
    rgba[..., 1] = base_dust * (1.0 - hole) + 8.0 * hole
    rgba[..., 2] = (base_dust + 4.0) * (1.0 - hole) + 10.0 * hole
    rgba[..., 3] = alpha * 255.0
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_WPN, "bullet_hole_concrete.png"), format="PNG", optimize=True
    )

    # Metallic bullet hole decal (charred core + bright steel torn rim)
    rim = np.clip(1.0 - np.abs(rad - 0.30 - (noise - 0.5) * 0.06) * 12.0, 0.0, 1.0)
    m_rgba = np.zeros((S, S, 4), dtype=np.float32)
    m_rgba[..., 0] = 18.0 * hole + 175.0 * rim
    m_rgba[..., 1] = 16.0 * hole + 170.0 * rim
    m_rgba[..., 2] = 18.0 * hole + 165.0 * rim
    m_rgba[..., 3] = np.clip(np.maximum(hole * 0.96, rim * 0.85), 0.0, 0.96) * 255.0
    Image.fromarray(np.clip(m_rgba, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_WPN, "bullet_hole_metal.png"), format="PNG", optimize=True
    )

    # Additive Muzzle Star Sprite
    M = 256
    my, mx = np.mgrid[0:M, 0:M].astype(np.float32)
    mdx = (mx - M * 0.5) / (M * 0.46)
    mdy = (my - M * 0.5) / (M * 0.46)
    mr = np.sqrt(mdx * mdx + mdy * mdy)
    mang = np.arctan2(mdy, mdx)
    rays = (np.abs(np.cos(mang * 3.0)) ** 5.0) * 0.65 + (np.abs(np.sin(mang * 6.0)) ** 7.0) * 0.45
    core = np.clip(1.0 - mr * 1.15, 0.0, 1.0) ** 1.8
    spike = np.clip(1.0 - mr * (1.25 - 0.55 * rays), 0.0, 1.0) ** 2.2
    val = np.clip(np.maximum(core, spike), 0.0, 1.0)
    mtex = np.zeros((M, M, 4), dtype=np.float32)
    mtex[..., 0] = 255.0
    mtex[..., 1] = 185.0 + 70.0 * core
    mtex[..., 2] = 80.0 + 175.0 * (core ** 2.2)
    mtex[..., 3] = val * 255.0
    Image.fromarray(np.clip(mtex, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_WPN, "muzzle_star_tex.png"), format="PNG", optimize=True
    )


# ---------------------------------------------------------------------------
# 3. CoD Zombies HUD Textures (Vignette, Hitmarker, Damage Arc, Icons)
# ---------------------------------------------------------------------------

def build_hud_textures():
    # A) Sharp Arterial Blood Vignette (1280x720 transparent center, bloody veins & splatters at border)
    W, H = 1280, 720
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.5) / (H * 0.5)
    edge = np.sqrt((nx * 0.92) ** 2 + (ny * 1.02) ** 2)
    splat_n = fbm((H, W), (64, 32, 16, 8), (0.45, 0.28, 0.17, 0.10), seed=511)
    veins = np.clip(1.0 - np.abs(fbm((H, W), (48, 24, 12, 6), (0.45, 0.28, 0.17, 0.10), seed=517) - 0.5) * 16.0, 0.0, 1.0)
    mask = np.clip((edge - 0.52 + (splat_n - 0.45) * 0.32 + veins * 0.14) * 2.2, 0.0, 1.0)
    alpha = (mask ** 1.35) * np.clip((edge - 0.38) * 2.0, 0.0, 1.0)
    vig = np.zeros((H, W, 4), dtype=np.float32)
    vig[..., 0] = 128.0 + 48.0 * veins - 42.0 * mask
    vig[..., 1] = 6.0 + 10.0 * veins
    vig[..., 2] = 8.0 + 10.0 * veins
    vig[..., 3] = np.clip(alpha, 0.0, 0.95) * 255.0
    Image.fromarray(np.clip(vig, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_UI, "blood_vignette.png"), format="PNG", optimize=True
    )

    # B) Crisp Diagonal Hitmarker (128x128)
    hm = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(hm)
    arms = [
        ((24, 24), (50, 50)),
        ((104, 24), (78, 50)),
        ((24, 104), (50, 78)),
        ((104, 104), (78, 78)),
    ]
    for p0, p1 in arms:
        d.line([p0, p1], fill=(10, 10, 10, 220), width=11)
    for p0, p1 in arms:
        d.line([p0, p1], fill=(255, 255, 255, 255), width=6)
    hm.save(os.path.join(TEX_UI, "hitmarker.png"), format="PNG", optimize=True)

    # C) Directional Damage Indicator Arc (256x256, centered top arc pointing UP = 0 deg)
    A = 256
    ay, ax = np.mgrid[0:A, 0:A].astype(np.float32)
    adx = (ax - A * 0.5) / (A * 0.5)
    ady = (ay - A * 0.5) / (A * 0.5)
    ar = np.sqrt(adx * adx + ady * ady)
    # Angle 0 is UP (-Y)
    ang = np.arctan2(adx, -ady)
    arc_band = np.exp(-((ar - 0.72) / 0.11) ** 2)
    ang_band = np.clip(1.0 - np.abs(ang) / math.radians(38.0), 0.0, 1.0) ** 1.4
    sharp_tip = np.exp(-((ar - 0.76) / 0.045) ** 2) * (np.clip(1.0 - np.abs(ang) / math.radians(16.0), 0.0, 1.0))
    d_alpha = np.clip(arc_band * ang_band * 0.92 + sharp_tip * 0.4, 0.0, 1.0)
    arc_img = np.zeros((A, A, 4), dtype=np.float32)
    arc_img[..., 0] = 225.0 + 30.0 * sharp_tip
    arc_img[..., 1] = 18.0 + 35.0 * sharp_tip
    arc_img[..., 2] = 14.0
    arc_img[..., 3] = d_alpha * 245.0
    Image.fromarray(np.clip(arc_img, 0, 255).astype(np.uint8), mode="RGBA").save(
        os.path.join(TEX_UI, "hud_dmg_arc.png"), format="PNG", optimize=True
    )

    # D) Grenade Silhouette Icon (64x64)
    gimg = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gimg)
    gd.rounded_rectangle((20, 22, 44, 54), radius=10, fill=(235, 240, 232, 255), outline=(25, 28, 25, 255), width=2)
    for yline in (31, 39, 47):
        gd.line([(21, yline), (43, yline)], fill=(45, 52, 46, 220), width=2)
    gd.line([(32, 23), (32, 53)], fill=(45, 52, 46, 220), width=2)
    gd.rectangle((27, 13, 37, 23), fill=(215, 210, 190, 255), outline=(25, 25, 25, 255), width=2)
    gd.line([(37, 15), (47, 19), (49, 36)], fill=(235, 240, 232, 255), width=3)
    gd.ellipse((15, 11, 26, 22), outline=(235, 240, 232, 255), width=2)
    gimg.save(os.path.join(TEX_UI, "hud_grenade_icon.png"), format="PNG", optimize=True)

    # E) Pack-a-Punch Badge (96x48)
    pimg = Image.new("RGBA", (96, 48), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pimg)
    pd.rounded_rectangle((2, 4, 93, 43), radius=8, fill=(10, 28, 44, 225), outline=(55, 225, 255, 255), width=2)
    pd.polygon([(18, 12), (24, 24), (18, 36), (12, 24)], fill=(85, 245, 255, 255))
    pd.polygon([(78, 12), (84, 24), (78, 36), (72, 24)], fill=(85, 245, 255, 255))
    pd.text((31, 16), "PaP", fill=(210, 250, 255, 255))
    pimg.save(os.path.join(TEX_UI, "hud_pap_badge.png"), format="PNG", optimize=True)

    # F) Fallback Stream-C HUD Perk Badges for the 4 new perks (named hud_perk_*.png so Stream D's perk_*.png are untouched)
    perk_specs = [
        ("mulekick", (38, 168, 72), "MK"),
        ("deadshot", (235, 185, 42), "DS"),
        ("phdflopper", (152, 54, 198), "PHD"),
        ("electriccherry", (55, 195, 255), "EC"),
    ]
    for pid, col, tag in perk_specs:
        im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.polygon([(32, 3), (61, 32), (32, 61), (3, 32)], fill=(14, 16, 20, 235), outline=col + (255,), width=4)
        dr.polygon([(32, 9), (55, 32), (32, 55), (9, 32)], fill=col + (215,))
        tx = 20 if len(tag) == 2 else 14
        dr.text((tx, 25), tag, fill=(255, 252, 242, 255))
        im.save(os.path.join(TEX_UI, f"hud_perk_{pid}.png"), format="PNG", optimize=True)


def write_credits(meta: dict):
    credits_path = os.path.join(REPO_ROOT, "docs", "credits_wpn.md")
    os.makedirs(os.path.dirname(credits_path), exist_ok=True)
    lines = [
        "# Weapons, Viewmodel, HUD & Audio CC0 Credits (Stream C)",
        "",
        "## 3D Models & Textures",
        "| Asset / Source | Author(s) | Source URL | License | Usage |",
        "| :--- | :--- | :--- | :--- | :--- |",
        "| MPFB2 / MakeHuman Base Mesh | MakeHuman Community / Joel Palmius | https://github.com/makehumancommunity/mpfb2 | CC0 (mesh/targets/weights); GPL-3.0-or-later addon | Anatomical first-person forearms, articulated hands, and fingers (`fp_right_hand.glb`, `fp_left_hand.glb`) |",
    ]
    for mid, item in sorted(meta.get("polyhaven_models", {}).items()):
        lines.append(f"| {item['name']} (`{mid}`) | {item['author']} | {item['url']} | {item['license']} | Refined & split in Blender for `kar98k.glb` (bolt action rifle base + ZF39 scope) |")
    for aid, item in sorted(meta.get("polyhaven_textures", {}).items()):
        lines.append(f"| {item['name']} (`{aid}`) | {item['author']} | {item['url']} | {item['license']} | 1K PBR albedo/normal/roughness maps for weapons, leather gloves, and wool sleeves |")
    lines.append("")
    with open(credits_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[WPN-CC0] Wrote base credits to {credits_path}")


def main():
    meta = fetch_cc0_sources()
    build_weapon_pbr_sets()
    build_decal_and_fx_textures()
    build_hud_textures()
    write_credits(meta)
    print("[WPN-CC0] All weapon PBR, decal & HUD textures ready!")


if __name__ == "__main__":
    main()
