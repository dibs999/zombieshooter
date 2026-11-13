#!/usr/bin/env python3
"""Generate procedural PBR textures, decals, and HUD icons for Bunker 115."""

import os
import math
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
    gh = max(2, h // scale)
    gw = max(2, w // scale)
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
    # Seamless wrap-around finite differences
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


def make_cobblestone():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    rows = 8
    cols = 8
    row_h = N / rows
    col_w = N / cols

    row_idx = np.floor(y / row_h)
    x_shifted = (x + (row_idx % 2) * (col_w * 0.5)) % N
    fx = (x_shifted % col_w) / col_w
    fy = (y % row_h) / row_h

    # Distance from tile edges to form rounded cobblestone crowns
    dx = np.abs(fx - 0.5) * 2.0
    dy = np.abs(fy - 0.5) * 2.0
    warp = (fbm((N, N), (32, 16, 8), (0.5, 0.35, 0.15), seed=11) - 0.5) * 0.12
    edge = np.maximum(dx, dy) + warp
    stone_mask = np.clip((0.92 - edge) * 6.0, 0.0, 1.0)

    # Per-stone variation
    cell_id = (row_idx * 13 + np.floor(x_shifted / col_w) * 7).astype(np.int32)
    rng = np.random.default_rng(101)
    lut = rng.uniform(0.72, 1.15, size=256).astype(np.float32)
    stone_var = lut[cell_id % 256]

    micro = fbm((N, N), (32, 16, 8, 4), (0.4, 0.3, 0.2, 0.1), seed=21)
    puddle = np.clip((fbm((N, N), (128, 64, 32), (0.6, 0.3, 0.1), seed=33) - 0.56) * 4.5, 0.0, 1.0)

    height = stone_mask * (0.55 + 0.3 * micro + 0.15 * (stone_var - 0.72))
    height = np.maximum(height, puddle * 0.25)

    base = np.zeros((N, N, 3), dtype=np.float32)
    base[..., 0] = 44 + 28 * micro * stone_var
    base[..., 1] = 48 + 30 * micro * stone_var
    base[..., 2] = 56 + 34 * micro * stone_var
    # Dark wet mortar
    mortar = np.array([18.0, 20.0, 24.0], dtype=np.float32)
    albedo = base * stone_mask[..., None] + mortar * (1.0 - stone_mask[..., None])
    # Darken slightly in puddles
    albedo *= (1.0 - 0.32 * puddle[..., None])

    # Wet cobblestones: shiny puddles (low roughness ~0.08), stones ~0.48, mortar ~0.75
    roughness = 0.78 * (1.0 - stone_mask) + (0.42 + 0.22 * micro) * stone_mask
    roughness = roughness * (1.0 - puddle) + 0.08 * puddle

    save_pbr_set(f"{OUT_ENV}/cobblestone", albedo, height, roughness, strength=4.5)


def make_bunker_concrete():
    N = 512
    noise_big = fbm((N, N), (128, 64, 32, 16, 8), (0.35, 0.25, 0.2, 0.12, 0.08), seed=55)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    # Concrete slab seams every 128px
    seam_x = np.exp(-((np.minimum(x % 128, 128 - (x % 128))) ** 2) / 3.5)
    seam_y = np.exp(-((np.minimum(y % 256, 256 - (y % 256))) ** 2) / 3.5)
    seams = np.maximum(seam_x, seam_y)

    # Vertical damp grime streaks
    streak = value_noise((N, N), scale=16, seed=77)
    damp = np.clip((y / N) * 0.5 + streak * 0.5 - 0.35, 0.0, 1.0)

    height = noise_big * 0.7 - seams * 0.45
    albedo = np.zeros((N, N, 3), dtype=np.float32)
    tone = 74 + 44 * noise_big - 26 * seams - 20 * damp
    albedo[..., 0] = tone * 0.96
    albedo[..., 1] = tone * 0.97
    albedo[..., 2] = tone * 0.93
    roughness = np.clip(0.72 + 0.2 * noise_big - 0.25 * damp, 0.25, 0.96)
    save_pbr_set(f"{OUT_ENV}/bunker_concrete", albedo, height, roughness, strength=3.2)


def make_rusted_steel():
    N = 512
    noise = fbm((N, N), (64, 32, 16, 8, 4), (0.3, 0.3, 0.2, 0.12, 0.08), seed=88)
    rust = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=99) - 0.48) * 3.2, 0.0, 1.0)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    # Panel grid + rivets
    seam = np.maximum(
        np.exp(-((np.minimum(x % 128, 128 - (x % 128))) ** 2) / 3.0),
        np.exp(-((np.minimum(y % 128, 128 - (y % 128))) ** 2) / 3.0),
    )
    rx = ((x % 64) - 16) ** 2 + ((y % 64) - 16) ** 2
    rivets = np.clip(1.0 - rx / 20.0, 0.0, 1.0)

    height = 0.5 + 0.18 * noise - 0.3 * seam + 0.35 * rivets
    steel = np.stack([72 + 30 * noise, 78 + 32 * noise, 84 + 34 * noise], axis=-1)
    rust_col = np.stack([115 + 35 * noise, 52 + 20 * noise, 24 + 12 * noise], axis=-1)
    albedo = steel * (1.0 - rust[..., None]) + rust_col * rust[..., None]
    albedo *= (1.0 - 0.45 * seam[..., None])
    roughness = np.clip(0.32 + 0.15 * noise + 0.48 * rust, 0.2, 0.95)
    save_pbr_set(f"{OUT_ENV}/rusted_steel", albedo, height, roughness, strength=3.6)


def make_charred_wood():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    grain = np.sin(y * 0.24 + fbm((N, N), (64, 32, 16), (0.6, 0.3, 0.1), seed=123) * 14.0) * 0.5 + 0.5
    plank_seam = np.exp(-((np.minimum(y % 64, 64 - (y % 64))) ** 2) / 3.0)
    burn = fbm((N, N), (64, 32), (0.65, 0.35), seed=145)

    height = grain * 0.4 - plank_seam * 0.55
    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (72 + 48 * grain) * (0.65 + 0.35 * burn) * (1.0 - 0.6 * plank_seam)
    albedo[..., 1] = (48 + 34 * grain) * (0.65 + 0.35 * burn) * (1.0 - 0.6 * plank_seam)
    albedo[..., 2] = (30 + 22 * grain) * (0.65 + 0.35 * burn) * (1.0 - 0.6 * plank_seam)
    roughness = np.clip(0.65 + 0.25 * (1.0 - grain), 0.35, 0.95)
    save_pbr_set(f"{OUT_ENV}/charred_wood", albedo, height, roughness, strength=3.5)


def make_lab_tile():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    gx = np.minimum(x % 64, 64 - (x % 64))
    gy = np.minimum(y % 64, 64 - (y % 64))
    grout = np.maximum(np.exp(-(gx ** 2) / 3.0), np.exp(-(gy ** 2) / 3.0))
    grime = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=211)
    height = 0.6 - 0.45 * grout + 0.08 * grime
    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (92 - 38 * grime) * (1.0 - 0.55 * grout)
    albedo[..., 1] = (104 - 40 * grime) * (1.0 - 0.55 * grout)
    albedo[..., 2] = (98 - 34 * grime) * (1.0 - 0.55 * grout)
    roughness = np.clip(0.28 + 0.45 * grime + 0.3 * grout, 0.15, 0.95)
    save_pbr_set(f"{OUT_ENV}/lab_tile", albedo, height, roughness, strength=2.6)


def make_pap_runes():
    N = 512
    img = Image.new("RGB", (N, N), (14, 16, 26))
    em = Image.new("RGB", (N, N), (0, 0, 0))
    d_img = ImageDraw.Draw(img)
    d_em = ImageDraw.Draw(em)

    rng = np.random.default_rng(777)
    # Intricate circuit + glyph runes inspired by Pack-a-Punch concept art
    for i in range(48):
        x0 = int(rng.integers(0, N))
        y0 = int(rng.integers(0, N))
        col = (0, 235, 255) if i % 2 == 0 else (255, 50, 210)
        pts = [(x0, y0)]
        cx, cy = x0, y0
        for _ in range(rng.integers(3, 7)):
            ang = int(rng.integers(0, 8)) * (math.pi / 4.0)
            dist = int(rng.integers(24, 72))
            cx = (cx + int(math.cos(ang) * dist)) % N
            cy = (cy + int(math.sin(ang) * dist)) % N
            pts.append((cx, cy))
        for a, b in zip(pts[:-1], pts[1:]):
            if abs(a[0] - b[0]) < N // 2 and abs(a[1] - b[1]) < N // 2:
                d_em.line([a, b], fill=col, width=3)
                d_img.line([a, b], fill=(170, 230, 255), width=3)
        # Rune ring nodes
        r = int(rng.integers(6, 15))
        d_em.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], outline=col, width=2)
        d_img.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], outline=(210, 230, 255), width=2)

    em_glow = em.filter(ImageFilter.GaussianBlur(radius=3))
    em_arr = np.clip(np.asarray(em, dtype=np.float32) + np.asarray(em_glow, dtype=np.float32) * 0.85, 0, 255).astype(np.uint8)
    img.save(f"{OUT_WEAPONS}/pap_albedo.png")
    Image.fromarray(em_arr, mode="RGB").save(f"{OUT_WEAPONS}/pap_emission.png")


def make_blood_vignette():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    nx = (x - N / 2) / (N / 2)
    ny = (y - N / 2) / (N / 2)
    rad = np.sqrt(nx * nx + ny * ny)
    noise = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=666)
    alpha = np.clip((rad - 0.58 + (noise - 0.5) * 0.45) * 1.9, 0.0, 1.0)
    # Add organic splatter droplets near edges
    rgba = np.zeros((N, N, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(115 + 65 * noise, 0, 255).astype(np.uint8)
    rgba[..., 1] = 8
    rgba[..., 2] = 10
    rgba[..., 3] = np.clip(alpha * 235, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(f"{OUT_UI}/blood_vignette.png")


def make_perk_badges_and_marquees():
    perks = {
        "juggernog": ("JUGGERNOG", (195, 28, 34), "SHIELD"),
        "speedcola": ("SPEED COLA", (28, 175, 68), "BOLT"),
        "doubletap": ("DOUBLE TAP", (225, 165, 25), "BULLETS"),
        "quickrevive": ("QUICK REVIVE", (35, 130, 235), "CROSS"),
        "staminup": ("STAMIN-UP", (235, 105, 25), "WING"),
    }
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    for key, (label, col, glyph) in perks.items():
        # HUD Badge 128x128
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

        # Machine Marquee Sign 512x256
        sign = Image.new("RGB", (512, 256), (18, 18, 22))
        ds = ImageDraw.Draw(sign)
        ds.rectangle([8, 8, 504, 248], fill=col, outline=(245, 235, 210), width=8)
        ds.rectangle([22, 22, 490, 234], fill=(20, 20, 24), outline=col, width=4)
        ds.text((256, 105), label, fill=(255, 248, 235), font=font_lg, anchor="mm")
        ds.text((256, 178), "PERK-A-COLA", fill=col, font=font_sm, anchor="mm")
        sign.save(f"{OUT_PROPS}/marquee_{key}.png")


def make_chalk_wallbuys():
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    buys = {
        "m14": ("M14", "500 PTS"),
        "shotgun": ("TRENCH GUN", "1000 PTS"),
        "mp40": ("MP40", "1000 PTS"),
        "stg44": ("STG-44", "1200 PTS"),
        "kar98k": ("KAR98K", "800 PTS"),
    }
    for key, (name, price) in buys.items():
        img = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        chalk = (225, 235, 245, 220)
        # Chalk rectangle & stylized silhouette bar
        d.rounded_rectangle([18, 18, 494, 238], radius=16, outline=chalk, width=4)
        d.line([(60, 122), (430, 122)], fill=chalk, width=14)
        d.line([(60, 122), (35, 165)], fill=chalk, width=18)
        d.line([(210, 122), (200, 178)], fill=chalk, width=12)
        d.line([(320, 122), (332, 168)], fill=chalk, width=10)
        d.text((256, 56), name, fill=chalk, font=font, anchor="mm")
        d.text((256, 204), price, fill=(140, 235, 255, 230), font=font_sm, anchor="mm")
        img.filter(ImageFilter.GaussianBlur(radius=0.6)).save(f"{OUT_PROPS}/chalk_{key}.png")


def make_crosshair_and_hitmarker():
    # Hitmarker 64x64
    hm = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(hm)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.line([(32 + sx * 9, 32 + sy * 9), (32 + sx * 24, 32 + sy * 24)], fill=(255, 255, 255, 245), width=4)
    hm.save(f"{OUT_UI}/hitmarker.png")


def make_panzer_armor():
    N = 512
    noise = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=303)
    rust = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=317) - 0.58) * 3.0, 0.0, 1.0)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    seam = np.maximum(
        np.exp(-((np.minimum(x % 256, 256 - (x % 256))) ** 2) / 4.0),
        np.exp(-((np.minimum(y % 256, 256 - (y % 256))) ** 2) / 4.0),
    )
    rx = ((x % 64) - 12) ** 2 + ((y % 64) - 12) ** 2
    rivets = np.clip(1.0 - rx / 14.0, 0.0, 1.0)
    height = 0.5 + 0.16 * noise - 0.32 * seam + 0.32 * rivets

    # Dark Wehrmacht Feldgrau / charcoal steel + subtle muted dark oxide rust
    base = np.stack([42 + 18 * noise, 46 + 18 * noise, 43 + 16 * noise], axis=-1)
    rust_col = np.stack([64 + 18 * noise, 36 + 12 * noise, 24 + 8 * noise], axis=-1)
    albedo = base * (1.0 - 0.55 * rust[..., None]) + rust_col * (0.55 * rust[..., None])
    albedo *= (1.0 - 0.42 * seam[..., None])
    roughness = np.clip(0.56 + 0.18 * noise + 0.22 * rust, 0.35, 0.92)
    save_pbr_set(f"{OUT_ENV}/panzer_armor", albedo, height, roughness, strength=3.4)


def make_burlap():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    weave_x = np.sin(x * 0.85) * 0.5 + 0.5
    weave_y = np.sin(y * 0.85) * 0.5 + 0.5
    weave = 0.5 * weave_x + 0.5 * weave_y
    dirt = fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=409)
    height = 0.45 * weave + 0.35 * dirt

    albedo = np.zeros((N, N, 3), dtype=np.float32)
    albedo[..., 0] = (78 + 26 * weave) * (0.62 + 0.38 * dirt)
    albedo[..., 1] = (68 + 22 * weave) * (0.62 + 0.38 * dirt)
    albedo[..., 2] = (48 + 16 * weave) * (0.62 + 0.38 * dirt)
    roughness = np.clip(0.84 + 0.12 * (1.0 - weave), 0.72, 0.98)
    save_pbr_set(f"{OUT_ENV}/burlap", albedo, height, roughness, strength=4.0)


def make_zombie_cloth():
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    weave = 0.5 * (np.sin(x * 0.9) * 0.5 + 0.5) + 0.5 * (np.sin(y * 0.9) * 0.5 + 0.5)
    grime = fbm((N, N), (64, 32, 16, 8), (0.45, 0.25, 0.2, 0.1), seed=521)
    blood = np.clip((fbm((N, N), (64, 32, 16), (0.5, 0.3, 0.2), seed=613) - 0.62) * 3.8, 0.0, 1.0)
    height = 0.35 * weave + 0.45 * grime

    olive = np.stack([46 + 22 * grime, 50 + 22 * grime, 40 + 18 * grime], axis=-1)
    blood_c = np.stack([68 + 14 * grime, 14 + 4 * grime, 14 + 4 * grime], axis=-1)
    albedo = olive * (1.0 - blood[..., None]) + blood_c * blood[..., None]
    albedo *= (0.85 + 0.2 * weave[..., None])
    roughness = np.clip(0.80 + 0.14 * grime - 0.30 * blood, 0.38, 0.96)
    save_pbr_set(f"{OUT_ENV}/zombie_cloth", albedo, height, roughness, strength=3.2)


if __name__ == "__main__":
    make_cobblestone()
    make_bunker_concrete()
    make_rusted_steel()
    make_charred_wood()
    make_lab_tile()
    make_panzer_armor()
    make_burlap()
    make_zombie_cloth()
    make_pap_runes()
    make_blood_vignette()
    make_perk_badges_and_marquees()
    make_chalk_wallbuys()
    make_crosshair_and_hitmarker()
    print("All procedural PBR textures & HUD icons generated!")
