#!/usr/bin/env python3
"""Fetch CC0 night HDRIs & scanned 1K PBR textures (Poly Haven + ambientCG) and
generate crisp RGBA decal / FX textures for BUNKER 115 v2 (Stream A: Environment).

Raw downloads are cached in /tmp/cc0_cache/env/ so re-runs are fast and offline-safe
once cached, while missing files re-download automatically.
"""

import io
import json
import math
import os
import shutil
import urllib.request
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE_DIR = "/tmp/cc0_cache/env"
HDRI_CACHE = os.path.join(CACHE_DIR, "hdri")
TEX_CACHE = os.path.join(CACHE_DIR, "textures")

OUT_HDRI = os.path.join(REPO_ROOT, "assets", "hdri")
OUT_ENV_TEX = os.path.join(REPO_ROOT, "assets", "textures", "env")
OUT_DECALS = os.path.join(REPO_ROOT, "assets", "decals")

for d in (HDRI_CACHE, TEX_CACHE, OUT_HDRI, OUT_ENV_TEX, OUT_DECALS):
    os.makedirs(d, exist_ok=True)

USER_AGENT = "Bunker115-EnvFetcher/2.0"


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def download_cached(url: str, cache_path: str) -> str:
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    tmp_path = cache_path + ".part"
    data = fetch_bytes(url)
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.replace(tmp_path, cache_path)
    return cache_path


def fetch_polyhaven_hdri(hdri_id: str, out_filename: str) -> dict:
    info = fetch_json(f"https://api.polyhaven.com/info/{hdri_id}")
    files = fetch_json(f"https://api.polyhaven.com/files/{hdri_id}")
    hdr_entry = files.get("hdri", {}).get("2k", {}).get("hdr", {})
    url = hdr_entry.get("url")
    if not url:
        raise RuntimeError(f"Missing 2k hdr URL for {hdri_id}")
    cache_path = download_cached(url, os.path.join(HDRI_CACHE, f"{hdri_id}_2k.hdr"))
    dst_path = os.path.join(OUT_HDRI, out_filename)
    shutil.copyfile(cache_path, dst_path)
    authors = ", ".join(info.get("authors", {}).keys()) or "Poly Haven"
    print(f"[HDRI] {hdri_id} -> {dst_path} ({os.path.getsize(dst_path)//1024} KB)")
    return {
        "id": hdri_id,
        "name": info.get("name", hdri_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{hdri_id}",
        "license": "CC0 1.0",
        "output": f"assets/hdri/{out_filename}",
    }


def _pick_ph_map_url(files_dict: dict, keys: list[str], res: str = "1k") -> tuple[str | None, str]:
    for key in keys:
        node = files_dict.get(key, {}).get(res, {})
        for fmt in ("jpg", "png"):
            if fmt in node and "url" in node[fmt]:
                return node[fmt]["url"], key
    return None, ""


def _save_resized_jpg(src_img: Image.Image, dst_path: str, max_dim: int = 1024, quality: int = 88) -> None:
    if src_img.width > max_dim or src_img.height > max_dim:
        src_img = src_img.resize((max_dim, max_dim), Image.Resampling.LANCZOS)
    src_img.save(dst_path, format="JPEG", quality=quality, optimize=True)


def fetch_polyhaven_texture(tex_id: str, out_prefix: str) -> dict:
    info = fetch_json(f"https://api.polyhaven.com/info/{tex_id}")
    files = fetch_json(f"https://api.polyhaven.com/files/{tex_id}")

    alb_url, _ = _pick_ph_map_url(files, ["Diffuse", "albedo", "col"])
    nrm_url, _ = _pick_ph_map_url(files, ["nor_gl"])
    rgh_url, rgh_key = _pick_ph_map_url(files, ["Rough", "rough", "arm", "rough_ao"])

    if not alb_url or not nrm_url or not rgh_url:
        raise RuntimeError(f"Missing required maps for Poly Haven texture {tex_id}: {list(files.keys())}")

    tdir = os.path.join(TEX_CACHE, tex_id)
    alb_src = download_cached(alb_url, os.path.join(tdir, os.path.basename(alb_url)))
    nrm_src = download_cached(nrm_url, os.path.join(tdir, os.path.basename(nrm_url)))
    rgh_src = download_cached(rgh_url, os.path.join(tdir, os.path.basename(rgh_url)))

    with Image.open(alb_src) as im:
        _save_resized_jpg(im.convert("RGB"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_albedo.jpg"))
    with Image.open(nrm_src) as im:
        _save_resized_jpg(im.convert("RGB"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_normal.jpg"), quality=92)
    with Image.open(rgh_src) as im:
        if rgh_key == "arm":
            # Poly Haven ARM packs AO=R, Roughness=G, Metallic=B
            _, g_chan, _ = im.convert("RGB").split()
            _save_resized_jpg(g_chan.convert("L"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_roughness.jpg"))
        else:
            _save_resized_jpg(im.convert("L"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_roughness.jpg"))

    authors = ", ".join(info.get("authors", {}).keys()) or "Poly Haven"
    print(f"[TEX/PH] {tex_id} -> {out_prefix}_{{albedo,normal,roughness}}.jpg")
    return {
        "id": tex_id,
        "name": info.get("name", tex_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{tex_id}",
        "license": "CC0 1.0",
        "output": f"assets/textures/env/{out_prefix}_*.jpg",
    }


def fetch_ambientcg_texture(asset_id: str, out_prefix: str) -> dict:
    url = f"https://ambientcg.com/get?file={asset_id}_1K-JPG.zip"
    zip_path = download_cached(url, os.path.join(TEX_CACHE, f"{asset_id}_1K-JPG.zip"))
    tdir = os.path.join(TEX_CACHE, asset_id)
    os.makedirs(tdir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tdir)

    candidates = os.listdir(tdir)
    alb_file = next((f for f in candidates if "_Color." in f), None)
    nrm_file = next((f for f in candidates if "_NormalGL." in f), None)
    rgh_file = next((f for f in candidates if "_Roughness." in f), None)
    met_file = next((f for f in candidates if "_Metalness." in f), None)
    if not alb_file or not nrm_file or not rgh_file:
        raise RuntimeError(f"Missing maps in ambientCG {asset_id}: {candidates}")

    with Image.open(os.path.join(tdir, alb_file)) as im:
        _save_resized_jpg(im.convert("RGB"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_albedo.jpg"))
    with Image.open(os.path.join(tdir, nrm_file)) as im:
        _save_resized_jpg(im.convert("RGB"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_normal.jpg"), quality=92)
    with Image.open(os.path.join(tdir, rgh_file)) as im:
        _save_resized_jpg(im.convert("L"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_roughness.jpg"))
    if met_file:
        with Image.open(os.path.join(tdir, met_file)) as im:
            _save_resized_jpg(im.convert("L"), os.path.join(OUT_ENV_TEX, f"{out_prefix}_metallic.jpg"))

    print(f"[TEX/ACG] {asset_id} -> {out_prefix}_{{albedo,normal,roughness}}.jpg")
    return {
        "id": asset_id,
        "name": asset_id,
        "authors": "Lennart Demes (ambientCG)",
        "url": f"https://ambientcg.com/view?id={asset_id}",
        "license": "CC0 1.0",
        "output": f"assets/textures/env/{out_prefix}_*.jpg",
    }


# ---------------------------------------------------------------------------
# Procedural RGBA Decal & FX Texture Generation (sharp 512x512 / 256x256 PNG)
# ---------------------------------------------------------------------------

def _fbm(shape: tuple[int, int], octaves=(64, 32, 16, 8, 4), weights=(0.42, 0.26, 0.16, 0.10, 0.06), seed=42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = shape
    acc = np.zeros(shape, dtype=np.float32)
    for idx, (sc, wt) in enumerate(zip(octaves, weights)):
        gh = max(2, h // max(1, sc))
        gw = max(2, w // max(1, sc))
        grid = np.random.default_rng(seed + idx * 31).random((gh, gw), dtype=np.float32)
        im = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
        acc += wt * (np.asarray(im, dtype=np.float32) / 255.0)
    lo, hi = float(acc.min()), float(acc.max())
    return (acc - lo) / max(1e-6, hi - lo)


def _height_to_normal_png(height: np.ndarray, path: str, strength: float = 3.5) -> None:
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(height)
    n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    rgb = np.stack([
        np.clip((nx / n * 0.5 + 0.5) * 255.0, 0, 255),
        np.clip((ny / n * 0.5 + 0.5) * 255.0, 0, 255),
        np.clip((nz / n * 0.5 + 0.5) * 255.0, 0, 255),
    ], axis=-1).astype(np.uint8)
    Image.fromarray(rgb, mode="RGB").save(path)


def generate_decals_and_fx() -> None:
    N = 512
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    u = (xx / (N - 1)) * 2.0 - 1.0
    v = (yy / (N - 1)) * 2.0 - 1.0
    r = np.sqrt(u * u + v * v)

    # 1. Grime / water leakage streaks (top-down vertical runoff)
    n1 = _fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=101)
    streak_x = _fbm((1, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=102)
    streak = np.repeat(streak_x, N, axis=0)
    v_top = np.clip(1.0 - (yy / N), 0.0, 1.0) ** 0.75
    x_edge = np.clip(1.0 - np.abs(u) ** 2.2, 0.0, 1.0)
    alpha = np.clip((streak * 0.65 + n1 * 0.45 - 0.22) * v_top * x_edge * 2.2, 0.0, 0.92)
    rgba = np.zeros((N, N, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(28 + 26 * n1, 0, 255).astype(np.uint8)
    rgba[..., 1] = np.clip(24 + 20 * n1, 0, 255).astype(np.uint8)
    rgba[..., 2] = np.clip(20 + 14 * n1, 0, 255).astype(np.uint8)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_grime_leak.png"))

    # 2. Rainwater Puddle (Albedo + ORM with R=AO, G=Roughness, B=Metal)
    pn = _fbm((N, N), (128, 64, 32, 16), (0.5, 0.28, 0.14, 0.08), seed=205)
    p_dist = r + (pn - 0.5) * 0.55
    p_mask = np.clip((0.72 - p_dist) * 5.2, 0.0, 1.0)
    p_albedo = np.zeros((N, N, 4), dtype=np.uint8)
    p_albedo[..., 0] = 16
    p_albedo[..., 1] = 20
    p_albedo[..., 2] = 24
    p_albedo[..., 3] = (p_mask * 0.58 * 255).astype(np.uint8)
    Image.fromarray(p_albedo, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_puddle_albedo.png"))

    p_orm = np.zeros((N, N, 3), dtype=np.uint8)
    p_orm[..., 0] = np.clip(255 - p_mask * 55, 0, 255).astype(np.uint8)  # AO
    p_orm[..., 1] = np.clip((0.85 * (1.0 - p_mask) + 0.06 * p_mask) * 255, 0, 255).astype(np.uint8)  # Roughness
    p_orm[..., 2] = np.clip(p_mask * 35, 0, 255).astype(np.uint8)
    Image.fromarray(p_orm, mode="RGB").save(os.path.join(OUT_DECALS, "decal_puddle_orm.png"))

    # 3. Blood splatter + smear
    im_blood = Image.new("L", (N, N), 0)
    dr = ImageDraw.Draw(im_blood)
    rng = np.random.default_rng(303)
    dr.ellipse((150, 165, 345, 330), fill=235)
    for _ in range(42):
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(45, 200)
        cx = int(256 + math.cos(ang) * dist)
        cy = int(256 + math.sin(ang) * dist)
        rad = int(rng.uniform(4, 28) * max(0.3, 1.15 - dist / 220.0))
        dr.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=int(rng.uniform(170, 250)))
        if dist < 140:
            ex = int(256 + math.cos(ang) * (dist + rng.uniform(18, 48)))
            ey = int(256 + math.sin(ang) * (dist + rng.uniform(18, 48)))
            dr.line((cx, cy, ex, ey), fill=210, width=max(2, rad // 2))
    im_blood = im_blood.filter(ImageFilter.GaussianBlur(radius=1.5))
    bn = _fbm((N, N), (64, 32, 16, 8), (0.4, 0.3, 0.2, 0.1), seed=304)
    b_alpha = np.clip((np.asarray(im_blood, dtype=np.float32) / 255.0) * (0.7 + 0.45 * bn) - 0.1 * (r > 0.9), 0.0, 0.94)
    b_rgba = np.zeros((N, N, 4), dtype=np.uint8)
    b_rgba[..., 0] = np.clip(62 + 44 * bn, 0, 255).astype(np.uint8)
    b_rgba[..., 1] = np.clip(6 + 8 * bn, 0, 255).astype(np.uint8)
    b_rgba[..., 2] = np.clip(7 + 6 * bn, 0, 255).astype(np.uint8)
    b_rgba[..., 3] = (b_alpha * 255).astype(np.uint8)
    Image.fromarray(b_rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_blood_splatter.png"))

    # 4. Scorch / blast burn mark
    sn = _fbm((N, N), (64, 32, 16, 8), (0.45, 0.25, 0.18, 0.12), seed=404)
    ang = np.arctan2(v, u)
    rays = 0.78 + 0.22 * np.sin(ang * 11.0 + sn * 6.0) * np.cos(ang * 5.0)
    scorch_alpha = np.clip((1.0 - (r / (0.85 * rays))) * 1.45 * (0.65 + 0.5 * sn), 0.0, 0.92)
    s_rgba = np.zeros((N, N, 4), dtype=np.uint8)
    s_rgba[..., 0] = np.clip(18 + 20 * sn, 0, 255).astype(np.uint8)
    s_rgba[..., 1] = np.clip(16 + 18 * sn, 0, 255).astype(np.uint8)
    s_rgba[..., 2] = np.clip(15 + 16 * sn, 0, 255).astype(np.uint8)
    s_rgba[..., 3] = (scorch_alpha * 255).astype(np.uint8)
    Image.fromarray(s_rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_scorch_mark.png"))

    # 5. Chipped industrial yellow-black warning stripe
    wn = _fbm((N, N), (64, 32, 16, 8, 4), (0.35, 0.25, 0.2, 0.12, 0.08), seed=505)
    stripe = ((xx * 0.14 + yy * 0.14) % 48.0) < 24.0
    box_mask = (np.abs(u) < 0.92) & (np.abs(v) < 0.36)
    chip = wn > 0.28
    w_alpha = np.where(box_mask & chip, 0.86 * (0.6 + 0.4 * wn), 0.0)
    w_rgba = np.zeros((N, N, 4), dtype=np.uint8)
    w_rgba[..., 0] = np.where(stripe, 196, 24)
    w_rgba[..., 1] = np.where(stripe, 142, 22)
    w_rgba[..., 2] = np.where(stripe, 22, 20)
    w_rgba[..., 3] = np.clip(w_alpha * 255, 0, 255).astype(np.uint8)
    Image.fromarray(w_rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_warning_stripe.png"))

    # 6. Branching structural wall cracks (albedo + normal)
    im_cr = Image.new("L", (N, N), 0)
    drc = ImageDraw.Draw(im_cr)
    rng_c = np.random.default_rng(606)
    for _ in range(7):
        px, py = 256.0 + rng_c.uniform(-24, 24), 256.0 + rng_c.uniform(-24, 24)
        theta = rng_c.uniform(0, 2 * math.pi)
        for step in range(18):
            step_len = rng_c.uniform(8, 16)
            nx = px + math.cos(theta) * step_len
            ny = py + math.sin(theta) * step_len
            w_px = max(1, int(4.5 - step * 0.2))
            drc.line((px, py, nx, ny), fill=235, width=w_px)
            if rng_c.random() < 0.25 and step > 2:
                b_th = theta + rng_c.choice([-1, 1]) * rng_c.uniform(0.4, 0.9)
                bx, by = nx, ny
                for bs in range(7):
                    bnx = bx + math.cos(b_th) * rng_c.uniform(6, 12)
                    bny = by + math.sin(b_th) * rng_c.uniform(6, 12)
                    drc.line((bx, by, bnx, bny), fill=185, width=max(1, 3 - bs // 2))
                    bx, by = bnx, bny
                    b_th += rng_c.uniform(-0.35, 0.35)
            px, py = nx, ny
            theta += rng_c.uniform(-0.42, 0.42)
    cr_arr = np.asarray(im_cr.filter(ImageFilter.GaussianBlur(radius=0.8)), dtype=np.float32) / 255.0
    cr_arr *= np.clip((0.92 - r) * 3.0, 0.0, 1.0)
    c_rgba = np.zeros((N, N, 4), dtype=np.uint8)
    c_rgba[..., 0] = 20
    c_rgba[..., 1] = 20
    c_rgba[..., 2] = 22
    c_rgba[..., 3] = np.clip(cr_arr * 240, 0, 255).astype(np.uint8)
    Image.fromarray(c_rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_wall_crack.png"))
    _height_to_normal_png(1.0 - cr_arr, os.path.join(OUT_DECALS, "decal_wall_crack_normal.png"), strength=4.5)

    # 7. Motorpool oil slick
    on = _fbm((N, N), (64, 32, 16, 8), (0.45, 0.3, 0.15, 0.1), seed=707)
    o_mask = np.clip((0.68 - (r + (on - 0.5) * 0.45)) * 4.5, 0.0, 1.0)
    o_rgba = np.zeros((N, N, 4), dtype=np.uint8)
    o_rgba[..., 0] = np.clip(14 + 14 * np.sin(on * 9.0), 0, 255).astype(np.uint8)
    o_rgba[..., 1] = np.clip(12 + 10 * np.cos(on * 7.0), 0, 255).astype(np.uint8)
    o_rgba[..., 2] = np.clip(18 + 18 * np.sin(on * 11.0 + 1.2), 0, 255).astype(np.uint8)
    o_rgba[..., 3] = (o_mask * 0.85 * 255).astype(np.uint8)
    Image.fromarray(o_rgba, mode="RGBA").save(os.path.join(OUT_DECALS, "decal_oil_slick.png"))

    # 8. Industrial floor drain grate (albedo + normal)
    im_gr = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    drg = ImageDraw.Draw(im_gr)
    drg.rectangle((24, 96, 488, 416), fill=(32, 34, 36, 248), outline=(58, 52, 46, 255), width=10)
    drg.rectangle((42, 114, 470, 398), fill=(10, 12, 14, 250))
    for gx in range(56, 466, 26):
        drg.rectangle((gx, 116, gx + 10, 396), fill=(48, 44, 40, 255))
    for gy in (180, 256, 332):
        drg.rectangle((42, gy - 6, 470, gy + 6), fill=(56, 52, 46, 255))
    im_gr.save(os.path.join(OUT_DECALS, "decal_floor_grate.png"))
    gr_h = np.asarray(im_gr.convert("L"), dtype=np.float32) / 255.0
    _height_to_normal_png(gr_h, os.path.join(OUT_DECALS, "decal_floor_grate_normal.png"), strength=4.0)

    # 9. Mist puff sprite (256x256 RGBA)
    M = 256
    my, mx = np.mgrid[0:M, 0:M].astype(np.float32)
    mr = np.sqrt(((mx / (M - 1)) * 2 - 1) ** 2 + ((my / (M - 1)) * 2 - 1) ** 2)
    mn = _fbm((M, M), (64, 32, 16), (0.55, 0.30, 0.15), seed=808)
    m_alpha = np.clip((np.maximum(0.0, 1.0 - mr) ** 1.7) * (0.55 + 0.6 * mn), 0.0, 1.0)
    m_rgba = np.zeros((M, M, 4), dtype=np.uint8)
    m_rgba[..., 0] = 210
    m_rgba[..., 1] = 225
    m_rgba[..., 2] = 240
    m_rgba[..., 3] = (m_alpha * 255).astype(np.uint8)
    Image.fromarray(m_rgba, mode="RGBA").save(os.path.join(OUT_ENV_TEX, "fx_mist_puff.png"))

    # 10. Ember glow sprite (128x128 RGBA)
    E = 128
    ey, ex = np.mgrid[0:E, 0:E].astype(np.float32)
    er = np.sqrt(((ex / (E - 1)) * 2 - 1) ** 2 + ((ey / (E - 1)) * 2 - 1) ** 2)
    e_alpha = np.clip(np.maximum(0.0, 1.0 - er) ** 2.6, 0.0, 1.0)
    e_rgba = np.zeros((E, E, 4), dtype=np.uint8)
    e_rgba[..., 0] = 255
    e_rgba[..., 1] = np.clip(235 - 120 * er, 90, 255).astype(np.uint8)
    e_rgba[..., 2] = np.clip(160 - 150 * er, 15, 255).astype(np.uint8)
    e_rgba[..., 3] = (e_alpha * 255).astype(np.uint8)
    Image.fromarray(e_rgba, mode="RGBA").save(os.path.join(OUT_ENV_TEX, "fx_ember_glow.png"))
    print(f"[DECALS & FX] Generated 8 decals + 2 FX sprites.")


def main() -> None:
    credits = []
    credits.append(fetch_polyhaven_hdri("moonlit_golf", "moonlit_golf_2k.hdr"))
    credits.append(fetch_polyhaven_hdri("blaubeuren_night", "blaubeuren_night_2k.hdr"))

    ph_textures = [
        ("cobblestone_04", "cc0_cobble"),
        ("brushed_concrete_03", "cc0_concrete_wall"),
        ("concrete_floor_worn_001", "cc0_concrete_floor"),
        ("brick_moss_001", "cc0_brick"),
        ("blue_floor_tiles_01", "cc0_lab_tile"),
        ("rust_coarse_01", "cc0_rust_steel"),
        ("rusty_corrugated_iron", "cc0_corrugated"),
        ("dark_wooden_planks", "cc0_planks"),
        ("asphalt_02", "cc0_asphalt"),
        ("brown_mud_02", "cc0_mud"),
    ]
    for tid, prefix in ph_textures:
        credits.append(fetch_polyhaven_texture(tid, prefix))

    credits.append(fetch_ambientcg_texture("DiamondPlate008C", "cc0_metal_plate"))
    generate_decals_and_fx()

    manifest_path = os.path.join(CACHE_DIR, "textures_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(credits, f, indent=2)
    print(f"[DONE] Saved {len(credits)} CC0 texture/HDRI entries -> {manifest_path}")


if __name__ == "__main__":
    main()
