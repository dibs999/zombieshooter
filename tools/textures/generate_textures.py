#!/usr/bin/env python3
"""Generate high-detail procedural PBR texture sets, weapon finishes, chalk silhouettes,
Perk-a-Cola marquees, Pack-a-Punch dials/signs, and HUD icons for BUNKER 115.
"""

import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT_ENV = "assets/textures/env"
OUT_WEAPONS = "assets/textures/weapons"
OUT_PROPS = "assets/textures/props"
OUT_UI = "assets/textures/ui"

for d in (OUT_ENV, OUT_WEAPONS, OUT_PROPS, OUT_UI):
    os.makedirs(d, exist_ok=True)


def value_noise(shape, scale=16, seed=42):
    rng = np.random.default_rng(seed)
    h, w = shape
    gh = max(2, h // max(1, scale))
    gw = max(2, w // max(1, scale))
    grid = rng.random((gh, gw), dtype=np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(shape, octaves=(64, 32, 16, 8, 4), weights=(0.45, 0.25, 0.15, 0.10, 0.05), seed=42):
    acc = np.zeros(shape, dtype=np.float32)
    for idx, (sc, wt) in enumerate(zip(octaves, weights)):
        acc += wt * value_noise(shape, scale=sc, seed=seed + idx * 17)
    acc = (acc - acc.min()) / max(1e-6, acc.max() - acc.min())
    return acc


def height_to_normal(height, strength=3.0):
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


def save_pbr_set(prefix, albedo_rgb, height, roughness, strength=3.5):
    Image.fromarray(np.clip(albedo_rgb, 0, 255).astype(np.uint8), mode="RGB").save(f"{prefix}_albedo.png")
    height_to_normal(height, strength=strength).save(f"{prefix}_normal.png")
    r_img = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(r_img, mode="L").save(f"{prefix}_roughness.png")


# ---------------------------------------------------------------------------
# Environment & Architectural Textures (1024x1024 where it counts!)
# ---------------------------------------------------------------------------

def make_cobblestone():
    N = 1024
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    rows, cols = 10, 10
    row_h, col_w = N / rows, N / cols

    row_idx = np.floor(y / row_h)
    x_shifted = (x + (row_idx % 2) * (col_w * 0.5)) % N
    fx = (x_shifted % col_w) / col_w
    fy = (y % row_h) / row_h

    dx = np.abs(fx - 0.5) * 2.0
    dy = np.abs(fy - 0.5) * 2.0
    warp = (fbm((N, N), (64, 32, 16, 8), (0.45, 0.30, 0.15, 0.10), seed=11) - 0.5) * 0.16
    edge = np.sqrt((dx * 0.96) ** 4 + (dy * 0.96) ** 4) ** 0.25 + warp
    stone_mask = np.clip((0.91 - edge) * 6.5, 0.0, 1.0)
    crown = np.clip(1.0 - edge, 0.0, 1.0) ** 0.55

    cell_id = (row_idx * 17 + np.floor(x_shifted / col_w) * 11).astype(np.int32)
    rng = np.random.default_rng(101)
    lut_v = rng.uniform(0.68, 1.24, size=256).astype(np.float32)
    lut_warm = rng.uniform(-10.0, 12.0, size=256).astype(np.float32)
    stone_var = lut_v[cell_id % 256]
    warm_shift = lut_warm[cell_id % 256]

    micro = fbm((N, N), (64, 32, 16, 8, 4), (0.35, 0.25, 0.20, 0.12, 0.08), seed=21)
    puddle = np.clip((fbm((N, N), (256, 128, 64, 32), (0.55, 0.25, 0.12, 0.08), seed=33) - 0.59) * 5.0, 0.0, 1.0)
    moss = np.clip((1.0 - stone_mask) * (fbm((N, N), (128, 64, 32), (0.5, 0.3, 0.2), seed=44) - 0.45) * 3.0, 0.0, 1.0)

    height = stone_mask * (0.35 + 0.35 * crown + 0.22 * micro + 0.10 * (stone_var - 0.68))
    height = np.maximum(height, puddle * 0.24)

    base = np.zeros((N, N, 3), dtype=np.float32)
    base[..., 0] = 38 + 26 * micro * stone_var + warm_shift * 0.6
    base[..., 1] = 42 + 28 * micro * stone_var + warm_shift * 0.3
    base[..., 2] = 49 + 31 * micro * stone_var - warm_shift * 0.4
    mortar = np.array([15.0, 17.0, 20.0], dtype=np.float32)
    moss_col = np.array([28.0, 42.0, 24.0], dtype=np.float32)

    albedo = base * stone_mask[..., None] + mortar * (1.0 - stone_mask[..., None])
    albedo = albedo * (1.0 - moss[..., None] * 0.7) + moss_col * (moss[..., None] * 0.7)
    albedo *= (1.0 - 0.38 * puddle[..., None])

    roughness = 0.84 * (1.0 - stone_mask) + (0.40 + 0.24 * micro) * stone_mask
    roughness = roughness * (1.0 - puddle) + 0.07 * puddle
    save_pbr_set(f"{OUT_ENV}/cobblestone", albedo, height, roughness, strength=4.8)


def make_bunker_concrete():
    N = 1024
    noise_big = fbm((N, N), (256, 128, 64, 32, 16, 8), (0.30, 0.24, 0.18, 0.14, 0.08, 0.06), seed=55)
    pits = np.clip((fbm((N, N), (32, 16, 8, 4), (0.35, 0.30, 0.20, 0.15), seed=57) - 0.68) * 6.0, 0.0, 1.0)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)

    seam_x = np.exp(-((np.minimum(x % 256, 256 - (x % 256))) ** 2) / 5.0)
    seam_y = np.exp(-((np.minimum(y % 512, 512 - (y % 512))) ** 2) / 5.0)
    seams = np.maximum(seam_x, seam_y)

    # Tie-rod formwork dimples
    tx = ((x % 256) - 128) ** 2 + ((y % 256) - 128) ** 2
    tie_holes = np.clip(1.0 - tx / 64.0, 0.0, 1.0)

    streak = value_noise((N, N), scale=24, seed=77)
    damp = np.clip((y / N) * 0.55 + streak * 0.45 - 0.36, 0.0, 1.0)
    rust_stain = np.clip(tie_holes * 0.5 + (fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=79) - 0.62) * 2.2, 0.0, 1.0)

    height = noise_big * 0.7 - seams * 0.48 - pits * 0.35 - tie_holes * 0.40
    tone = 68 + 40 * noise_big - 24 * seams - 20 * damp - 16 * pits - 18 * tie_holes
    albedo = np.stack([tone * 0.96, tone * 0.97, tone * 0.93], axis=-1)
    rust_rgb = np.stack([72 + 16 * noise_big, 42 + 10 * noise_big, 26 + 6 * noise_big], axis=-1)
    albedo = albedo * (1.0 - 0.45 * rust_stain[..., None]) + rust_rgb * (0.45 * rust_stain[..., None])
    roughness = np.clip(0.74 + 0.18 * noise_big - 0.24 * damp + 0.15 * pits, 0.28, 0.96)
    save_pbr_set(f"{OUT_ENV}/bunker_concrete", albedo, height, roughness, strength=3.6)


def make_rusted_steel():
    N = 1024
    noise = fbm((N, N), (128, 64, 32, 16, 8, 4), (0.28, 0.24, 0.20, 0.14, 0.08, 0.06), seed=88)
    rust = np.clip((fbm((N, N), (128, 64, 32, 16), (0.45, 0.28, 0.17, 0.10), seed=99) - 0.46) * 3.4, 0.0, 1.0)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)

    seam = np.maximum(
        np.exp(-((np.minimum(x % 256, 256 - (x % 256))) ** 2) / 5.0),
        np.exp(-((np.minimum(y % 256, 256 - (y % 256))) ** 2) / 5.0),
    )
    rx = ((x % 128) - 24) ** 2 + ((y % 128) - 24) ** 2
    rivets = np.clip(1.0 - rx / 36.0, 0.0, 1.0)

    # Scratches
    scr = np.clip((value_noise((N, N), scale=6, seed=91) - 0.78) * 5.0, 0.0, 1.0)

    height = 0.5 + 0.16 * noise - 0.34 * seam + 0.38 * rivets - 0.08 * scr
    steel = np.stack([62 + 28 * noise + 38 * scr, 68 + 30 * noise + 38 * scr, 74 + 32 * noise + 40 * scr], axis=-1)
    rust_col = np.stack([108 + 34 * noise, 46 + 18 * noise, 20 + 10 * noise], axis=-1)
    albedo = steel * (1.0 - rust[..., None]) + rust_col * rust[..., None]
    albedo *= (1.0 - 0.48 * seam[..., None])
    albedo = np.clip(albedo + rivets[..., None] * 18.0, 0, 255)
    roughness = np.clip(0.30 + 0.16 * noise + 0.52 * rust - 0.18 * scr, 0.16, 0.96)
    save_pbr_set(f"{OUT_ENV}/rusted_steel", albedo, height, roughness, strength=3.8)


def make_charred_wood():
    N = 1024
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    warp = fbm((N, N), (128, 64, 32, 16), (0.45, 0.30, 0.15, 0.10), seed=123)
    grain = np.sin(y * 0.18 + warp * 18.0) * 0.5 + 0.5
    plank_seam = np.exp(-((np.minimum(y % 128, 128 - (y % 128))) ** 2) / 5.0)
    burn = fbm((N, N), (128, 64, 32), (0.55, 0.30, 0.15), seed=145)
    splinter = value_noise((N, N), scale=8, seed=149)

    height = grain * 0.38 + 0.15 * splinter - plank_seam * 0.60
    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (66 + 44 * grain + 18 * splinter) * (0.62 + 0.38 * burn) * (1.0 - 0.62 * plank_seam)
    albedo[..., 1] = (42 + 30 * grain + 12 * splinter) * (0.62 + 0.38 * burn) * (1.0 - 0.62 * plank_seam)
    albedo[..., 2] = (25 + 18 * grain + 8 * splinter) * (0.62 + 0.38 * burn) * (1.0 - 0.62 * plank_seam)
    roughness = np.clip(0.64 + 0.24 * (1.0 - grain) + 0.10 * plank_seam, 0.35, 0.96)
    save_pbr_set(f"{OUT_ENV}/charred_wood", albedo, height, roughness, strength=3.8)


def make_lab_tile():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    gx = np.minimum(x % 64, 64 - (x % 64))
    gy = np.minimum(y % 64, 64 - (y % 64))
    grout = np.maximum(np.exp(-(gx ** 2) / 3.2), np.exp(-(gy ** 2) / 3.2))
    grime = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=211)
    stain = np.clip((fbm((N, N), (128, 64, 32), (0.5, 0.3, 0.2), seed=219) - 0.62) * 3.5, 0.0, 1.0)
    height = 0.6 - 0.45 * grout + 0.08 * grime
    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (74 - 30 * grime) * (1.0 - 0.58 * grout) * (1.0 - 0.25 * stain)
    albedo[..., 1] = (86 - 32 * grime) * (1.0 - 0.58 * grout) * (1.0 - 0.30 * stain)
    albedo[..., 2] = (82 - 28 * grime) * (1.0 - 0.58 * grout) * (1.0 - 0.32 * stain)
    roughness = np.clip(0.32 + 0.44 * grime + 0.28 * grout, 0.18, 0.96)
    save_pbr_set(f"{OUT_ENV}/lab_tile", albedo, height, roughness, strength=2.8)


def make_panzer_armor():
    N = 1024
    noise = fbm((N, N), (128, 64, 32, 16, 8), (0.36, 0.26, 0.20, 0.12, 0.06), seed=303)
    rust = np.clip((fbm((N, N), (128, 64, 32, 16), (0.45, 0.30, 0.15, 0.10), seed=317) - 0.54) * 3.2, 0.0, 1.0)
    scorch = np.clip((fbm((N, N), (256, 128, 64), (0.5, 0.3, 0.2), seed=319) - 0.64) * 3.8, 0.0, 1.0)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    seam = np.maximum(
        np.exp(-((np.minimum(x % 256, 256 - (x % 256))) ** 2) / 5.5),
        np.exp(-((np.minimum(y % 256, 256 - (y % 256))) ** 2) / 5.5),
    )
    rx = ((x % 64) - 16) ** 2 + ((y % 64) - 16) ** 2
    rivets = np.clip(1.0 - rx / 20.0, 0.0, 1.0)
    height = 0.5 + 0.16 * noise - 0.34 * seam + 0.36 * rivets

    base = np.stack([42 + 18 * noise, 46 + 18 * noise, 43 + 16 * noise], axis=-1)
    rust_col = np.stack([78 + 20 * noise, 36 + 12 * noise, 20 + 8 * noise], axis=-1)
    albedo = base * (1.0 - 0.62 * rust[..., None]) + rust_col * (0.62 * rust[..., None])
    albedo *= (1.0 - 0.45 * seam[..., None])
    albedo *= (1.0 - 0.42 * scorch[..., None])
    albedo = np.clip(albedo + rivets[..., None] * 14.0, 0, 255)
    roughness = np.clip(0.52 + 0.18 * noise + 0.28 * rust + 0.12 * scorch, 0.30, 0.94)
    save_pbr_set(f"{OUT_ENV}/panzer_armor", albedo, height, roughness, strength=3.8)


def make_burlap():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    weave_x = np.sin(x * 1.1) * 0.5 + 0.5
    weave_y = np.sin(y * 1.1) * 0.5 + 0.5
    weave = 0.5 * weave_x + 0.5 * weave_y
    dirt = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=409)
    height = 0.45 * weave + 0.35 * dirt

    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (82 + 28 * weave) * (0.58 + 0.42 * dirt)
    albedo[..., 1] = (70 + 24 * weave) * (0.58 + 0.42 * dirt)
    albedo[..., 2] = (48 + 18 * weave) * (0.58 + 0.42 * dirt)
    roughness = np.clip(0.84 + 0.12 * (1.0 - weave), 0.72, 0.98)
    save_pbr_set(f"{OUT_ENV}/burlap", albedo, height, roughness, strength=4.2)


def make_wood_crate():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    grain = np.sin(x * 0.22 + fbm((N, N), (64, 32, 16), (0.55, 0.3, 0.15), seed=450) * 12.0) * 0.5 + 0.5
    seam = np.exp(-((np.minimum(y % 128, 128 - (y % 128))) ** 2) / 4.0)
    dirt = fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=451)
    height = 0.4 * grain + 0.2 * dirt - 0.5 * seam

    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (42 + 22 * grain) * (0.7 + 0.3 * dirt) * (1.0 - 0.55 * seam)
    albedo[..., 1] = (50 + 24 * grain) * (0.7 + 0.3 * dirt) * (1.0 - 0.55 * seam)
    albedo[..., 2] = (30 + 14 * grain) * (0.7 + 0.3 * dirt) * (1.0 - 0.55 * seam)
    roughness = np.clip(0.72 + 0.18 * (1.0 - grain), 0.45, 0.95)
    save_pbr_set(f"{OUT_ENV}/wood_crate", albedo, height, roughness, strength=3.4)


# ---------------------------------------------------------------------------
# Enemy Organic PBR Texture Sets
# ---------------------------------------------------------------------------

def make_zombie_cloth():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    weave = 0.5 * (np.sin(x * 0.95) * 0.5 + 0.5) + 0.5 * (np.sin(y * 0.95) * 0.5 + 0.5)
    grime = fbm((N, N), (64, 32, 16, 8), (0.45, 0.25, 0.2, 0.1), seed=521)
    blood = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=613) - 0.58) * 4.0, 0.0, 1.0)
    height = 0.35 * weave + 0.45 * grime - 0.12 * blood

    olive = np.stack([46 + 22 * grime, 50 + 22 * grime, 40 + 18 * grime], axis=-1)
    blood_c = np.stack([68 + 14 * grime, 10 + 4 * grime, 10 + 4 * grime], axis=-1)
    albedo = olive * (1.0 - blood[..., None]) + blood_c * blood[..., None]
    albedo *= (0.85 + 0.2 * weave[..., None])
    roughness = np.clip(0.82 + 0.14 * grime - 0.36 * blood, 0.30, 0.96)
    save_pbr_set(f"{OUT_ENV}/zombie_cloth", albedo, height, roughness, strength=3.4)


def make_zombie_flesh():
    N = 512
    mottle = fbm((N, N), (64, 32, 16, 8), (0.40, 0.28, 0.20, 0.12), seed=630)
    veins = np.clip(1.0 - np.abs(fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=633) - 0.5) * 14.0, 0.0, 1.0)
    rot = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=637) - 0.60) * 3.8, 0.0, 1.0)
    height = 0.45 * mottle + 0.25 * veins - 0.30 * rot

    skin = np.stack([64 + 28 * mottle, 72 + 26 * mottle, 56 + 20 * mottle], axis=-1)
    vein_col = np.array([36.0, 26.0, 32.0], dtype=np.float32)
    rot_col = np.stack([78 + 12 * mottle, 14 + 4 * mottle, 12 + 3 * mottle], axis=-1)
    albedo = skin * (1.0 - 0.45 * veins[..., None]) + vein_col * (0.45 * veins[..., None])
    albedo = albedo * (1.0 - rot[..., None]) + rot_col * rot[..., None]
    roughness = np.clip(0.68 + 0.16 * mottle - 0.36 * rot, 0.24, 0.90)
    save_pbr_set(f"{OUT_ENV}/zombie_flesh", albedo, height, roughness, strength=3.8)


def make_zombie_labcoat():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    weave = 0.5 * (np.sin(x * 1.15) * 0.5 + 0.5) + 0.5 * (np.sin(y * 1.15) * 0.5 + 0.5)
    grime = fbm((N, N), (64, 32, 16, 8), (0.45, 0.25, 0.2, 0.1), seed=650)
    blood = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=655) - 0.56) * 4.2, 0.0, 1.0)
    height = 0.30 * weave + 0.35 * grime
    cloth = np.stack([128 + 30 * grime, 126 + 28 * grime, 114 + 24 * grime], axis=-1)
    blood_c = np.stack([82 + 16 * grime, 10 + 4 * grime, 10 + 4 * grime], axis=-1)
    albedo = cloth * (1.0 - blood[..., None]) + blood_c * blood[..., None]
    albedo *= (0.88 + 0.16 * weave[..., None])
    roughness = np.clip(0.84 + 0.10 * grime - 0.40 * blood, 0.28, 0.96)
    save_pbr_set(f"{OUT_ENV}/zombie_labcoat", albedo, height, roughness, strength=3.0)


def make_hellhound_hide():
    N = 512
    crust = fbm((N, N), (64, 32, 16, 8, 4), (0.35, 0.28, 0.20, 0.11, 0.06), seed=670)
    cracks = np.clip(1.0 - np.abs(fbm((N, N), (64, 32, 16), (0.55, 0.30, 0.15), seed=673) - 0.5) * 10.0, 0.0, 1.0)
    height = crust * 0.7 - cracks * 0.65

    char_col = np.stack([22 + 16 * crust, 18 + 12 * crust, 16 + 10 * crust], axis=-1)
    ember = np.array([255.0, 92.0, 12.0], dtype=np.float32)
    albedo = char_col * (1.0 - cracks[..., None]) + ember * cracks[..., None]
    roughness = np.clip(0.74 + 0.18 * crust - 0.45 * cracks, 0.22, 0.95)
    save_pbr_set(f"{OUT_ENV}/hellhound_hide", albedo, height, roughness, strength=4.5)


def make_ruin_brick_and_gear():
    # Weathered war-torn masonry brick for multi-story courtyard ruins
    N = 1024
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    row_h, col_w = 48.0, 96.0
    row_idx = np.floor(y / row_h)
    xs = (x + (row_idx % 2) * (col_w * 0.5)) % N
    fx = (xs % col_w) / col_w
    fy = (y % row_h) / row_h
    edge = np.maximum(np.abs(fx - 0.5) * 2.0, np.abs(fy - 0.5) * 2.0)
    mask = np.clip((0.91 - edge) * 9.0, 0.0, 1.0)
    bvar = ((row_idx * 13 + np.floor(xs / col_w) * 7) % 19) / 19.0
    soot = fbm((N, N), (256, 128, 64, 32), (0.45, 0.28, 0.17, 0.10), seed=691)
    micro = fbm((N, N), (32, 16, 8, 4), (0.4, 0.3, 0.2, 0.1), seed=695)
    height = mask * (0.45 + 0.30 * micro) + soot * 0.15
    brick = np.stack([72 + 24 * bvar - 28 * soot, 44 + 16 * bvar - 18 * soot, 36 + 14 * bvar - 14 * soot], axis=-1)
    mortar = np.stack([46 + 18 * micro, 46 + 18 * micro, 44 + 16 * micro], axis=-1)
    albedo = brick * mask[..., None] + mortar * (1.0 - mask[..., None])
    albedo *= (0.78 + 0.34 * micro[..., None])
    roughness = np.clip(0.84 - 0.12 * micro + 0.08 * soot, 0.50, 0.96)
    save_pbr_set(f"{OUT_ENV}/ruin_brick", albedo, height, roughness, strength=4.0)

    # First-person tactical leather glove (fine pebble grain, subtle seams)
    G = 512
    g_n = fbm((G, G), (16, 8, 4), (0.35, 0.35, 0.30), seed=698)
    crease = np.clip(1.0 - np.abs(fbm((G, G), (32, 16, 8), (0.5, 0.3, 0.2), seed=699) - 0.5) * 18.0, 0.0, 1.0)
    h_g = 0.45 + 0.16 * g_n - 0.08 * crease
    alb_g = np.stack([34 + 14 * g_n - 6 * crease, 30 + 12 * g_n - 5 * crease, 28 + 11 * g_n - 4 * crease], axis=-1)
    rgh_g = np.clip(0.50 + 0.16 * (1.0 - g_n) + 0.12 * crease, 0.30, 0.84)
    save_pbr_set(f"{OUT_WEAPONS}/fp_leather", alb_g, h_g, rgh_g, strength=1.5)

    # First-person field jacket wool sleeve (deep olive-drab twill, clean from zombie blood)
    y_s, x_s = np.mgrid[0:G, 0:G].astype(np.float32)
    twill = 0.5 * (np.sin((x_s + y_s) * 1.6) * 0.5 + 0.5) + 0.5 * (np.sin((x_s - y_s) * 0.8) * 0.5 + 0.5)
    weath = fbm((G, G), (64, 32, 16), (0.5, 0.3, 0.2), seed=700)
    h_s = 0.35 * twill + 0.25 * weath
    alb_s = np.stack([22 + 10 * weath + 4 * twill, 26 + 11 * weath + 5 * twill, 19 + 8 * weath + 3 * twill], axis=-1)
    rgh_s = np.clip(0.86 + 0.08 * weath, 0.74, 0.97)
    save_pbr_set(f"{OUT_WEAPONS}/fp_sleeve", alb_s, h_s, rgh_s, strength=1.5)


# ---------------------------------------------------------------------------
# Weapon Metal, Hardwood, Bakelite, Brass, Gauge & Pack-a-Punch Camo
# ---------------------------------------------------------------------------

def make_weapon_finishes():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)

    # 1. Blued/Parkerized Gun Steel (subtle ultra-fine directional brushing + crisp edge scratches)
    brush = value_noise((N, N), scale=2, seed=701) * 0.6 + value_noise((N, N), scale=6, seed=702) * 0.4
    brush_dir = np.sin(x * 1.2 + brush * 5.0) * 0.5 + 0.5
    mottle = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=703)
    scratch = np.clip((value_noise((N, N), scale=4, seed=705) - 0.84) * 7.0, 0.0, 1.0)
    height_s = 0.5 + 0.05 * brush_dir + 0.06 * mottle - 0.06 * scratch
    albedo_s = np.zeros((N, N, 3), dtype=np.float32)
    tone = 42 + 16 * mottle + 6 * brush_dir + 34 * scratch
    albedo_s[..., 0] = tone * 0.94
    albedo_s[..., 1] = tone * 0.98
    albedo_s[..., 2] = tone * 1.06
    rough_s = np.clip(0.28 + 0.14 * mottle - 0.10 * scratch, 0.14, 0.52)
    save_pbr_set(f"{OUT_WEAPONS}/gun_steel", albedo_s, height_s, rough_s, strength=1.1)

    # 2. Figured Oiled Walnut Wood
    w_warp = fbm((N, N), (64, 32, 16, 8), (0.45, 0.30, 0.15, 0.10), seed=710)
    rings = np.sin(y * 0.22 + w_warp * 12.0) * 0.5 + 0.5
    pores = value_noise((N, N), scale=4, seed=713)
    height_w = 0.28 * rings + 0.12 * pores
    albedo_w = np.zeros((N, N, 3), dtype=np.float32)
    albedo_w[..., 0] = 60 + 36 * rings + 12 * w_warp
    albedo_w[..., 1] = 28 + 18 * rings + 6 * w_warp
    albedo_w[..., 2] = 13 + 9 * rings + 3 * w_warp
    rough_w = np.clip(0.42 + 0.20 * (1.0 - rings) + 0.06 * pores, 0.28, 0.70)
    save_pbr_set(f"{OUT_WEAPONS}/walnut", albedo_w, height_w, rough_w, strength=1.4)

    # 3. Micro-Checkered Dark Bakelite / Grip (fine 8px diamonds!)
    diag1 = np.abs(((x + y) % 8) - 4.0) / 4.0
    diag2 = np.abs(((x - y) % 8) - 4.0) / 4.0
    diamond = np.minimum(diag1, diag2)
    mottle_b = fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=720)
    height_b = 0.38 * diamond + 0.08 * mottle_b
    albedo_b = np.zeros((N, N, 3), dtype=np.float32)
    albedo_b[..., 0] = 36 + 18 * diamond + 10 * mottle_b
    albedo_b[..., 1] = 16 + 8 * diamond + 5 * mottle_b
    albedo_b[..., 2] = 12 + 5 * diamond + 3 * mottle_b
    rough_b = np.clip(0.44 + 0.24 * (1.0 - diamond), 0.30, 0.78)
    save_pbr_set(f"{OUT_WEAPONS}/bakelite", albedo_b, height_b, rough_b, strength=2.0)

    # 4. Aged Antique Bronze / Brass
    b_mottle = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=730)
    patina = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=734) - 0.56) * 3.2, 0.0, 1.0)
    height_br = 0.5 + 0.08 * b_mottle - 0.08 * patina
    brass_c = np.stack([146 + 26 * b_mottle, 106 + 20 * b_mottle, 44 + 12 * b_mottle], axis=-1)
    pat_c = np.array([46.0, 56.0, 44.0], dtype=np.float32)
    albedo_br = brass_c * (1.0 - 0.52 * patina[..., None]) + pat_c * (0.52 * patina[..., None])
    rough_br = np.clip(0.28 + 0.14 * b_mottle + 0.42 * patina, 0.20, 0.85)
    save_pbr_set(f"{OUT_WEAPONS}/brass", albedo_br, height_br, rough_br, strength=1.3)


def make_pap_runes():
    N = 512
    # Machined silver/chrome base with crisp engraved ancient runes (cyan + magenta)
    noise = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=770)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    brush = 0.5 * np.sin(x * 0.45 + noise * 5.0) + 0.5
    base_val = 148 + 34 * noise + 12 * brush
    img_arr = np.stack([base_val * 0.94, base_val * 0.98, base_val * 1.06], axis=-1).astype(np.uint8)
    img = Image.fromarray(img_arr, mode="RGB")
    em = Image.new("RGB", (N, N), (0, 0, 0))
    d_img = ImageDraw.Draw(img)
    d_em = ImageDraw.Draw(em)

    rng = np.random.default_rng(777)
    # Ornate repeating geometric filigree borders + rune circuits
    for gy in range(64, N, 128):
        d_img.line([(0, gy), (N, gy)], fill=(36, 40, 48), width=5)
        col = (0, 225, 255) if (gy // 128) % 2 == 0 else (245, 55, 205)
        d_em.line([(0, gy), (N, gy)], fill=col, width=2)
        for gx in range(32, N, 64):
            d_img.polygon([(gx, gy - 14), (gx + 14, gy), (gx, gy + 14), (gx - 14, gy)], outline=(32, 36, 44), width=3)
            d_em.polygon([(gx, gy - 14), (gx + 14, gy), (gx, gy + 14), (gx - 14, gy)], outline=col, width=2)

    for i in range(44):
        x0 = int(rng.integers(0, N))
        y0 = int(rng.integers(0, N))
        col = (0, 235, 255) if i % 3 != 0 else (250, 55, 210)
        pts = [(x0, y0)]
        cx, cy = x0, y0
        for _ in range(rng.integers(3, 6)):
            ang = int(rng.integers(0, 8)) * (math.pi / 4.0)
            dist = int(rng.integers(24, 58))
            cx = (cx + int(math.cos(ang) * dist)) % N
            cy = (cy + int(math.sin(ang) * dist)) % N
            pts.append((cx, cy))
        for a, b in zip(pts[:-1], pts[1:]):
            if abs(a[0] - b[0]) < N // 2 and abs(a[1] - b[1]) < N // 2:
                d_img.line([a, b], fill=(28, 32, 40), width=5)
                d_em.line([a, b], fill=col, width=2)
                d_img.line([a, b], fill=(175, 235, 255), width=2)
        r = int(rng.integers(7, 13))
        d_em.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], outline=col, width=2)
        d_img.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], outline=(205, 240, 255), width=2)

    em_glow = em.filter(ImageFilter.GaussianBlur(radius=1.4))
    em_arr = np.clip(np.asarray(em, dtype=np.float32) * 0.90 + np.asarray(em_glow, dtype=np.float32) * 0.45, 0, 255).astype(np.uint8)
    img.save(f"{OUT_WEAPONS}/pap_albedo.png")
    Image.fromarray(em_arr, mode="RGB").save(f"{OUT_WEAPONS}/pap_emission.png")


# ---------------------------------------------------------------------------
# UI, Perk Marquees, Pack-a-Punch Sign/Gauge, Chalk Weapon Silhouettes
# ---------------------------------------------------------------------------

def make_blood_vignette():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    nx = (x - N / 2) / (N / 2)
    ny = (y - N / 2) / (N / 2)
    rad = np.sqrt(nx * nx + ny * ny)
    noise = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=666)
    alpha = np.clip((rad - 0.58 + (noise - 0.5) * 0.45) * 1.9, 0.0, 1.0)
    rgba = np.zeros((N, N, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(115 + 65 * noise, 0, 255).astype(np.uint8)
    rgba[..., 1] = 8
    rgba[..., 2] = 10
    rgba[..., 3] = np.clip(alpha * 235, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(f"{OUT_UI}/blood_vignette.png")


def make_pap_props():
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 44)
    except Exception:
        font_lg = ImageFont.load_default()

    # Pack-a-Punch Illuminated Marquee (512x160)
    sign = Image.new("RGB", (512, 160), (26, 22, 16))
    d = ImageDraw.Draw(sign)
    d.rectangle([6, 6, 506, 154], fill=(42, 32, 18), outline=(218, 174, 82), width=6)
    d.rectangle([16, 16, 496, 144], fill=(20, 26, 30), outline=(145, 112, 48), width=3)
    d.text((256, 80), "PACK-A-PUNCH", fill=(255, 224, 145), font=font_lg, anchor="mm")
    sign.save(f"{OUT_PROPS}/pap_marquee.png")

    # Analog Pressure Gauge Dial (256x256)
    g = Image.new("RGB", (256, 256), (232, 224, 200))
    dg = ImageDraw.Draw(g)
    dg.ellipse([8, 8, 248, 248], fill=(238, 230, 206), outline=(52, 42, 24), width=10)
    dg.arc([28, 28, 228, 228], start=310, end=40, fill=(205, 32, 24), width=12)
    for i in range(13):
        ang = math.radians(135 + i * (270 / 12))
        x1 = 128 + math.cos(ang) * 82
        y1 = 128 + math.sin(ang) * 82
        x2 = 128 + math.cos(ang) * 98
        y2 = 128 + math.sin(ang) * 98
        dg.line([(x1, y1), (x2, y2)], fill=(25, 25, 28), width=4)
    # Needle
    n_ang = math.radians(345)
    dg.line([(128 - math.cos(n_ang) * 18, 128 - math.sin(n_ang) * 18), (128 + math.cos(n_ang) * 84, 128 + math.sin(n_ang) * 84)], fill=(195, 28, 24), width=6)
    dg.ellipse([116, 116, 140, 140], fill=(35, 35, 38))
    g.save(f"{OUT_PROPS}/pap_gauge.png")


def make_perk_badges_and_marquees():
    perks = {
        "juggernog": ("JUGGER-NOG", "ARMOR + MAX HP", (195, 28, 34), "SHIELD"),
        "speedcola": ("SPEED COLA", "FAST RELOAD", (28, 175, 68), "BOLT"),
        "doubletap": ("DOUBLE TAP II", "2X DAMAGE & ROF", (225, 165, 25), "BULLETS"),
        "quickrevive": ("QUICK REVIVE", "SELF REVIVE", (35, 130, 235), "CROSS"),
        "staminup": ("STAMIN-UP", "SPRINT BOOST", (235, 105, 25), "WING"),
    }
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 40)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    for key, (label, sub, col, glyph) in perks.items():
        badge = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(badge)
        d.rounded_rectangle([6, 6, 122, 122], radius=20, fill=(col[0], col[1], col[2], 235), outline=(255, 245, 220, 255), width=5)
        d.rounded_rectangle([14, 14, 114, 114], radius=14, outline=(20, 20, 24, 180), width=3)
        if glyph == "SHIELD":
            d.polygon([(64, 26), (96, 38), (90, 78), (64, 102), (38, 78), (32, 38)], fill=(255, 245, 235, 255))
            d.rectangle([58, 44, 70, 82], fill=col)
            d.rectangle([45, 57, 83, 69], fill=col)
        elif glyph == "BOLT":
            d.polygon([(72, 24), (42, 68), (64, 68), (54, 104), (88, 56), (66, 56)], fill=(255, 250, 235, 255))
        elif glyph == "BULLETS":
            for ox in (-16, 16):
                cx = 64 + ox
                d.rectangle([cx - 8, 52, cx + 8, 96], fill=(255, 245, 220, 255))
                d.polygon([(cx - 8, 52), (cx, 26), (cx + 8, 52)], fill=(255, 245, 220, 255))
        elif glyph == "CROSS":
            d.rectangle([54, 28, 74, 100], fill=(255, 250, 255, 255))
            d.rectangle([28, 54, 100, 74], fill=(255, 250, 255, 255))
        elif glyph == "WING":
            d.polygon([(26, 78), (54, 42), (98, 34), (82, 60), (96, 66), (72, 84), (36, 94)], fill=(255, 245, 230, 255))
        badge.save(f"{OUT_UI}/perk_{key}.png")

        # Rich weathered retro marquee with aged paper border (balanced luminance avoids light blow-out)
        sign = Image.new("RGB", (512, 256), (168, 158, 138))
        ds = ImageDraw.Draw(sign)
        mcol = (int(col[0] * 0.72), int(col[1] * 0.72), int(col[2] * 0.72))
        ds.rectangle([8, 8, 504, 248], fill=(172, 162, 142), outline=mcol, width=10)
        ds.rectangle([22, 22, 490, 234], fill=(18, 18, 22), outline=(185, 174, 152), width=4)
        ds.rectangle([28, 28, 484, 148], fill=mcol)
        ds.text((256, 88), label, fill=(242, 234, 218), font=font_lg, anchor="mm")
        ds.text((256, 192), sub, fill=(215, 205, 186), font=font_sm, anchor="mm")
        sign.save(f"{OUT_PROPS}/marquee_{key}.png")


def make_chalk_wallbuys():
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    buys = {
        "m14": ("M14", "500 PTS"),
        "shotgun": ("M1897 TRENCH", "1000 PTS"),
        "mp40": ("MP40", "1000 PTS"),
        "stg44": ("STG-44", "1200 PTS"),
        "kar98k": ("KAR98K", "800 PTS"),
    }
    for key, (name, price) in buys.items():
        img = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        chalk = (228, 238, 248, 225)
        d.rounded_rectangle([14, 14, 498, 242], radius=16, outline=chalk, width=3)
        # Authentic distinct weapon chalk silhouettes
        if key == "m14":
            d.polygon([(54, 126), (138, 122), (168, 114), (360, 114), (360, 128), (185, 134), (132, 148), (54, 166)], outline=chalk, width=4)
            d.line([(360, 118), (448, 118)], fill=chalk, width=7)
            d.polygon([(228, 132), (248, 132), (244, 174), (224, 174)], outline=chalk, width=4)
        elif key == "shotgun":
            d.polygon([(54, 132), (146, 124), (175, 112), (265, 112), (265, 132), (180, 138), (125, 152), (54, 168)], outline=chalk, width=4)
            d.line([(265, 116), (452, 116)], fill=chalk, width=7)
            d.line([(265, 128), (432, 128)], fill=chalk, width=5)
            d.rectangle([285, 122, 365, 140], outline=chalk, width=4)
        elif key == "mp40":
            d.rectangle([156, 108, 326, 130], outline=chalk, width=4)
            d.line([(326, 116), (438, 116)], fill=chalk, width=6)
            d.polygon([(165, 130), (185, 130), (170, 174), (150, 174)], outline=chalk, width=4)
            d.polygon([(280, 130), (298, 130), (292, 198), (274, 198)], outline=chalk, width=4)
            d.line([(156, 126), (72, 138)], fill=chalk, width=5)
            d.line([(72, 116), (72, 160)], fill=chalk, width=6)
        elif key == "stg44":
            d.polygon([(56, 128), (142, 118), (345, 110), (345, 134), (150, 142), (56, 166)], outline=chalk, width=4)
            d.line([(345, 118), (446, 118)], fill=chalk, width=6)
            d.polygon([(176, 138), (196, 138), (182, 176), (162, 176)], outline=chalk, width=4)
            d.polygon([(246, 134), (268, 134), (284, 186), (260, 190)], outline=chalk, width=4)
        elif key == "kar98k":
            d.polygon([(50, 132), (148, 122), (370, 116), (370, 128), (152, 142), (50, 168)], outline=chalk, width=4)
            d.line([(370, 120), (458, 120)], fill=chalk, width=6)
            d.rectangle([188, 94, 304, 110], outline=chalk, width=4)
            d.line([(210, 110), (210, 118)], fill=chalk, width=4)
            d.line([(280, 110), (280, 118)], fill=chalk, width=4)

        d.text((256, 48), name, fill=chalk, font=font, anchor="mm")
        d.text((256, 212), price, fill=(135, 232, 255, 235), font=font_sm, anchor="mm")
        img.filter(ImageFilter.GaussianBlur(radius=0.5)).save(f"{OUT_PROPS}/chalk_{key}.png")


def make_crosshair_and_hitmarker():
    hm = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(hm)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.line([(32 + sx * 9, 32 + sy * 9), (32 + sx * 24, 32 + sy * 24)], fill=(255, 255, 255, 245), width=4)
    hm.save(f"{OUT_UI}/hitmarker.png")


if __name__ == "__main__":
    make_cobblestone()
    make_bunker_concrete()
    make_rusted_steel()
    make_charred_wood()
    make_lab_tile()
    make_panzer_armor()
    make_burlap()
    make_wood_crate()
    make_zombie_cloth()
    make_zombie_flesh()
    make_zombie_labcoat()
    make_hellhound_hide()
    make_ruin_brick_and_gear()
    make_weapon_finishes()
    make_pap_runes()
    make_pap_props()
    make_blood_vignette()
    make_perk_badges_and_marquees()
    make_chalk_wallbuys()
    make_crosshair_and_hitmarker()
    print("All 1024px/512px procedural PBR texture sets & decals generated!")
