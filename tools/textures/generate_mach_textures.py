#!/usr/bin/env python3
"""Download/cache Poly Haven CC0 textures & models for Stream D machines, and generate
UI perk icons, Perk-a-Cola / Wunderfizz / Quest marquees, Fire Trap placards & flame sprite.
Does NOT modify any Stream A/B/C textures.
"""

import json
import math
import os
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_PROPS = os.path.join(REPO_ROOT, "assets", "textures", "props")
OUT_UI = os.path.join(REPO_ROOT, "assets", "textures", "ui")
CACHE_ROOT = "/tmp/cc0_cache/mach"
CACHE_TEX = os.path.join(CACHE_ROOT, "tex")
CACHE_MODELS = os.path.join(CACHE_ROOT, "models")
MANIFEST_PATH = os.path.join(CACHE_ROOT, "manifest.json")

for d in (OUT_PROPS, OUT_UI, CACHE_TEX, CACHE_MODELS):
    os.makedirs(d, exist_ok=True)

USER_AGENT = "Bunker115-BlenderPipeline/2.0"

CC0_TEXTURE_IDS = [
    "rusty_painted_metal",
    "metal_plate_02",
    "metal_grate_rusty",
    "rusty_metal_02",
]

CC0_MODEL_IDS = [
    "propane_tank",
    "retro_multimeter",
]


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


def _load_meta(asset_id: str, cache_dir: str) -> tuple[dict, dict]:
    info_p = os.path.join(cache_dir, "_info.json")
    files_p = os.path.join(cache_dir, "_files.json")
    if os.path.exists(info_p):
        with open(info_p, "r", encoding="utf-8") as f:
            info = json.load(f)
    else:
        info = fetch_json(f"https://api.polyhaven.com/info/{asset_id}")
        with open(info_p, "w", encoding="utf-8") as f:
            json.dump(info, f)
    if os.path.exists(files_p):
        with open(files_p, "r", encoding="utf-8") as f:
            files = json.load(f)
    else:
        files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
        with open(files_p, "w", encoding="utf-8") as f:
            json.dump(files, f)
    return info, files


def fetch_cc0_texture_set(asset_id: str, max_px: int = 512) -> dict:
    tdir = os.path.join(CACHE_TEX, asset_id)
    os.makedirs(tdir, exist_ok=True)
    info, files = _load_meta(asset_id, tdir)

    map_keys = {
        "albedo": "Diffuse",
        "normal": "nor_gl",
        "roughness": "Rough",
        "metal": "Metal",
    }
    saved = {}
    for slot, ph_key in map_keys.items():
        slot_data = files.get(ph_key, {}).get("1k", {})
        fmt_entry = slot_data.get("jpg") or slot_data.get("png")
        if not fmt_entry or "url" not in fmt_entry:
            continue
        raw_ext = "jpg" if "jpg" in slot_data else "png"
        raw_path = os.path.join(tdir, f"raw_{slot}.{raw_ext}")
        download_cached(fmt_entry["url"], raw_path)

        out_jpg = os.path.join(tdir, f"{slot}.jpg")
        if not os.path.exists(out_jpg):
            with Image.open(raw_path) as im:
                im = im.convert("RGB")
                if max(im.size) > max_px:
                    im = im.resize((max_px, max_px), Image.Resampling.LANCZOS)
                im.save(out_jpg, format="JPEG", quality=88)
        saved[slot] = out_jpg

    authors = ", ".join(info.get("authors", {}).keys()) or "Poly Haven"
    print(f"[CC0 Tex] {asset_id}: {list(saved.keys())} (authors: {authors})")
    return {
        "id": asset_id,
        "type": "texture",
        "name": info.get("name", asset_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{asset_id}",
        "license": "CC0 1.0",
        "files": saved,
    }


def fetch_cc0_model(asset_id: str) -> dict:
    mdir = os.path.join(CACHE_MODELS, asset_id)
    os.makedirs(mdir, exist_ok=True)
    info, files = _load_meta(asset_id, mdir)

    g_entry = files.get("gltf", {}).get("1k", {}).get("gltf", {})
    gltf_url = g_entry.get("url")
    if not gltf_url:
        raise RuntimeError(f"Missing gltf/1k URL for {asset_id}")
    gltf_local = os.path.join(mdir, os.path.basename(gltf_url))
    download_cached(gltf_url, gltf_local)

    for rel_path, meta in g_entry.get("include", {}).items():
        inc_url = meta.get("url")
        if inc_url:
            download_cached(inc_url, os.path.join(mdir, rel_path))

    authors = ", ".join(info.get("authors", {}).keys()) or "Poly Haven"
    print(f"[CC0 Model] {asset_id} -> {gltf_local} (authors: {authors})")
    return {
        "id": asset_id,
        "type": "model",
        "name": info.get("name", asset_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{asset_id}",
        "license": "CC0 1.0",
        "gltf_path": gltf_local,
    }


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def make_new_perk_icons():
    """Generate crisp 128x128 RGBA perk_<id>.png icons for the 4 new Stream D perks."""
    specs = {
        "mulekick": ((24, 134, 58), (245, 239, 224)),
        "deadshot": ((205, 146, 20), (245, 239, 224)),
        "phdflopper": ((118, 36, 178), (245, 239, 224)),
        "electriccherry": ((22, 148, 212), (245, 239, 224)),
    }
    for key, (bg, cream) in specs.items():
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Vintage CoD double-rim rounded badge
        d.rounded_rectangle([6, 6, 122, 122], radius=22, fill=(*cream, 255))
        d.rounded_rectangle([12, 12, 116, 116], radius=17, fill=(*bg, 255), outline=(28, 32, 36, 220), width=3)
        d.rounded_rectangle([16, 16, 112, 112], radius=14, outline=(*cream, 180), width=2)

        if key == "mulekick":
            # 3 Crisp Rifle Cartridges
            for cx in (40, 64, 88):
                d.rounded_rectangle([cx - 6, 52, cx + 6, 94], radius=2, fill=(*cream, 255), outline=(24, 28, 30, 255), width=2)
                d.polygon([(cx - 6, 52), (cx, 32), (cx + 6, 52)], fill=(*cream, 255), outline=(24, 28, 30, 255))
                d.rectangle([cx - 6, 82, cx + 6, 88], fill=(32, 36, 38, 255))
        elif key == "deadshot":
            # Crosshair Scope + Center Target Dot
            d.ellipse([30, 30, 98, 98], outline=(*cream, 255), width=6)
            d.ellipse([48, 48, 80, 80], outline=(*cream, 255), width=4)
            d.rectangle([61, 22, 67, 46], fill=(*cream, 255))
            d.rectangle([61, 82, 67, 106], fill=(*cream, 255))
            d.rectangle([22, 61, 46, 67], fill=(*cream, 255))
            d.rectangle([82, 61, 106, 67], fill=(*cream, 255))
            d.ellipse([56, 56, 72, 72], fill=(208, 36, 32, 255))
        elif key == "phdflopper":
            # Mushroom Cloud Blast + Chevron
            d.chord([28, 26, 100, 74], start=180, end=360, fill=(*cream, 255))
            d.polygon([(50, 52), (78, 52), (84, 86), (44, 86)], fill=(*cream, 255))
            d.rounded_rectangle([30, 82, 98, 98], radius=5, fill=(*cream, 255))
            d.polygon([(64, 38), (52, 60), (76, 60)], fill=(28, 30, 36, 255))
        elif key == "electriccherry":
            # Jagged Lightning Bolt + Twin Cherries
            d.polygon([(70, 24), (44, 66), (62, 66), (54, 104), (86, 56), (66, 56)], fill=(*cream, 255), outline=(22, 28, 34, 240))
            for cx in (40, 88):
                d.ellipse([cx - 12, 76, cx + 12, 100], fill=(*cream, 255))
                d.ellipse([cx - 9, 79, cx + 9, 97], fill=(205, 32, 36, 255))

        out_path = os.path.join(OUT_UI, f"perk_{key}.png")
        img.save(out_path)
        print(f"[UI Icon] Saved {out_path}")


def make_perk_marquees():
    """Generate 512x256 RGB marquees matching Stream A/B vintage Perk-a-Cola marquees."""
    font_lg = _font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 38)
    font_md = _font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 32)
    font_sm = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

    specs = {
        "mulekick": ("MULE KICK", "3RD WEAPON SLOT", (28, 138, 54), font_lg),
        "deadshot": ("DEADSHOT DAIQUIRI", "TIGHT SPREAD + SNAP", (188, 138, 22), font_md),
        "phdflopper": ("PhD FLOPPER", "NO SPLASH + NUKE DIVE", (118, 38, 174), font_lg),
        "electriccherry": ("ELECTRIC CHERRY", "RELOAD SHOCKWAVE", (22, 142, 198), font_md),
    }
    for key, (label, sub, col, fnt) in specs.items():
        sign = Image.new("RGB", (512, 256), (168, 158, 138))
        ds = ImageDraw.Draw(sign)
        mcol = (int(col[0] * 0.78), int(col[1] * 0.78), int(col[2] * 0.78))
        ds.rectangle([8, 8, 504, 248], fill=(172, 162, 142), outline=mcol, width=10)
        ds.rectangle([22, 22, 490, 234], fill=(18, 18, 22), outline=(185, 174, 152), width=4)
        ds.rectangle([28, 28, 484, 148], fill=mcol)
        ds.text((256, 88), label, fill=(244, 236, 218), font=fnt, anchor="mm")
        ds.text((256, 192), sub, fill=(215, 206, 186), font=font_sm, anchor="mm")
        out_path = os.path.join(OUT_PROPS, f"marquee_{key}.png")
        sign.save(out_path)
        print(f"[Marquee] Saved {out_path}")


def make_wunderfizz_and_quest_and_trap_textures():
    font_lg = _font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 34)
    font_md = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    font_sm = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    font_mono = _font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 19)

    # 1. Der Wunderfizz Marquee (512x256)
    wf = Image.new("RGB", (512, 256), (20, 28, 42))
    dw = ImageDraw.Draw(wf)
    dw.rectangle([8, 8, 504, 248], fill=(14, 22, 36), outline=(198, 152, 62), width=10)
    dw.rectangle([22, 22, 490, 234], fill=(10, 20, 34), outline=(56, 208, 245), width=4)
    dw.rectangle([28, 28, 484, 146], fill=(18, 54, 96))
    dw.text((256, 86), "DER WUNDERFIZZ", fill=(165, 242, 255), font=font_lg, anchor="mm")
    dw.text((256, 192), "ELEMENT 115 PERK DISPENSER", fill=(235, 215, 165), font=font_sm, anchor="mm")
    wf.save(os.path.join(OUT_PROPS, "marquee_wunderfizz.png"))

    # 2. Quest Terminal CRT Oscilloscope Screen (512x384)
    qt = Image.new("RGB", (512, 384), (8, 22, 18))
    dq = ImageDraw.Draw(qt)
    dq.rectangle([6, 6, 506, 378], fill=(8, 24, 18), outline=(36, 165, 128), width=6)
    # Phosphor oscilloscope grid
    for gx in range(32, 490, 36):
        dq.line([(gx, 70), (gx, 300)], fill=(16, 62, 46), width=1)
    for gy in range(74, 302, 36):
        dq.line([(26, gy), (486, gy)], fill=(16, 62, 46), width=1)
    dq.rectangle([24, 20, 488, 66], fill=(18, 68, 52), outline=(65, 235, 195), width=2)
    dq.text((256, 43), "GROUP 935 // OP. ELEMENT 115", fill=(155, 255, 235), font=font_md, anchor="mm")
    # Glowing dual oscilloscope waveform
    pts1 = []
    pts2 = []
    for px in range(28, 484, 4):
        t = (px - 28) / 456.0
        y1 = 186 + math.sin(t * math.pi * 8.0) * 52.0 * (0.55 + 0.45 * math.sin(t * math.pi))
        y2 = 186 + math.cos(t * math.pi * 5.0) * 28.0
        pts1.append((px, y1))
        pts2.append((px, y2))
    dq.line(pts2, fill=(40, 175, 125), width=3)
    dq.line(pts1, fill=(92, 255, 235), width=5)
    # Schematic target pips
    for idx, sx in enumerate((96, 204, 308, 416)):
        dq.ellipse([sx - 12, 320, sx + 12, 344], outline=(105, 255, 210), width=3)
        dq.ellipse([sx - 5, 327, sx + 5, 337], fill=(105, 255, 210))
    dq.text((256, 360), "RESONATOR SYNC :: LOCK READY", fill=(140, 245, 210), font=font_mono, anchor="mm")
    qt.save(os.path.join(OUT_PROPS, "marquee_quest.png"))

    # 3. Fire Trap Hazard Panel (512x256)
    fp = Image.new("RGB", (512, 256), (34, 30, 26))
    df = ImageDraw.Draw(fp)
    # Yellow/Black hazard stripes along top & bottom edges
    df.rectangle([0, 0, 512, 36], fill=(216, 156, 20))
    df.rectangle([0, 220, 512, 256], fill=(216, 156, 20))
    for sx in range(-40, 560, 44):
        df.polygon([(sx, 0), (sx + 22, 0), (sx + 4, 36), (sx - 18, 36)], fill=(20, 20, 22))
        df.polygon([(sx, 220), (sx + 22, 220), (sx + 4, 256), (sx - 18, 256)], fill=(20, 20, 22))
    df.rectangle([16, 46, 496, 210], fill=(158, 34, 18), outline=(228, 188, 110), width=4)
    df.text((256, 98), "DANGER // FIRE TRAP", fill=(252, 238, 204), font=font_lg, anchor="mm")
    df.text((256, 154), "HIGH-PRESSURE PROPANE MANIFOLD", fill=(248, 212, 132), font=font_sm, anchor="mm")
    df.text((256, 188), "PULL IGNITION LEVER TO ENGAGE", fill=(230, 226, 214), font=font_sm, anchor="mm")
    fp.save(os.path.join(OUT_PROPS, "fire_trap_panel.png"))

    # 4. Fire Trap Fuel Gauge (256x256)
    fg = Image.new("RGB", (256, 256), (228, 220, 198))
    dg = ImageDraw.Draw(fg)
    dg.ellipse([8, 8, 248, 248], fill=(235, 227, 202), outline=(44, 36, 24), width=10)
    dg.arc([28, 28, 228, 228], start=300, end=42, fill=(214, 38, 18), width=14)
    for i in range(13):
        ang = math.radians(135 + i * (270.0 / 12.0))
        x1, y1 = 128 + math.cos(ang) * 80, 128 + math.sin(ang) * 80
        x2, y2 = 128 + math.cos(ang) * 98, 128 + math.sin(ang) * 98
        dg.line([(x1, y1), (x2, y2)], fill=(22, 22, 26), width=4)
    dg.text((128, 174), "PSI", fill=(32, 28, 24), font=font_md, anchor="mm")
    n_ang = math.radians(318)
    dg.line([(128 - math.cos(n_ang) * 16, 128 - math.sin(n_ang) * 16), (128 + math.cos(n_ang) * 84, 128 + math.sin(n_ang) * 84)], fill=(210, 28, 18), width=7)
    dg.ellipse([116, 116, 140, 140], fill=(32, 32, 36))
    fg.save(os.path.join(OUT_PROPS, "fire_trap_gauge.png"))

    # 5. Soft Turbulent Flame Plume Sprite (128x128 RGBA)
    N = 128
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    nx = (xx - (N * 0.5)) / (N * 0.42)
    ny = (yy - (N * 0.56)) / (N * 0.48)
    rng = np.random.default_rng(115)
    grid = rng.random((16, 16), dtype=np.float32)
    wisp = np.asarray(Image.fromarray((grid * 255).astype(np.uint8)).resize((N, N), Image.Resampling.BICUBIC), dtype=np.float32) / 255.0
    # Taper narrower toward top (low y)
    taper = np.clip(0.55 + 0.55 * (yy / N), 0.38, 1.15)
    rad = np.sqrt((nx / taper) ** 2 + ny ** 2)
    alpha = np.clip((1.0 - rad + (wisp - 0.5) * 0.36) * 1.45, 0.0, 1.0) ** 1.4
    core = np.clip(1.0 - rad * 1.25, 0.0, 1.0)
    rgba = np.zeros((N, N, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(225 + 30 * core, 0, 255).astype(np.uint8)
    rgba[..., 1] = np.clip(95 + 145 * core, 0, 255).astype(np.uint8)
    rgba[..., 2] = np.clip(16 + 165 * (core ** 2), 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(os.path.join(OUT_PROPS, "fire_flame_sprite.png"))
    print("[Prop Tex] Saved Wunderfizz, Quest CRT, Fire Trap panels, gauge & flame sprite")


def main():
    manifest = {"textures": [], "models": []}
    for tid in CC0_TEXTURE_IDS:
        manifest["textures"].append(fetch_cc0_texture_set(tid, max_px=512))
    for mid in CC0_MODEL_IDS:
        manifest["models"].append(fetch_cc0_model(mid))
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[Manifest] Saved {MANIFEST_PATH}")

    make_new_perk_icons()
    make_perk_marquees()
    make_wunderfizz_and_quest_and_trap_textures()


if __name__ == "__main__":
    main()
