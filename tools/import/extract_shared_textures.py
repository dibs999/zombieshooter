#!/usr/bin/env python3
"""Deduplicate & resolution-cap embedded textures across all GLB models into assets/models/_shared_tex/.

Generates:
  - assets/models/_shared_tex/* (deduplicated textures capped at <=512px, <=768px for weapons)
  - assets/models/_shared_tex/*.import (if missing, with compress/mode=2 and normal_map=1/0)
  - tools/import/shared_tex_map.json (per-GLB, per-material slot mapping for EditorScenePostImport)
"""

import hashlib
import io
import json
import pathlib
import re
import struct
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "assets" / "models"
SHARED_DIR = MODELS_DIR / "_shared_tex"
OUT_MAP = ROOT / "tools" / "import" / "shared_tex_map.json"


def parse_glb(path: pathlib.Path):
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"Not a GLB binary: {path}")
    clen, ctype = struct.unpack_from("<II", data, 12)
    assert ctype == 0x4E4F534A, f"Expected JSON chunk in {path}"
    gltf = json.loads(data[20 : 20 + clen].decode("utf-8"))
    boff = 20 + clen
    blen, btype = struct.unpack_from("<II", data, boff)
    assert btype == 0x004E4942, f"Expected BIN chunk in {path}"
    blob = data[boff + 8 : boff + 8 + blen]
    return gltf, blob


def sanitize_stem(name: str, fallback: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or fallback).lower()).strip("_")
    s = re.sub(r"_+", "_", s)
    if not s:
        s = fallback
    return s[:48].rstrip("_")


def write_import_if_needed(img_path: pathlib.Path, is_normal: bool, cap: int) -> bool:
    imp_path = pathlib.Path(str(img_path) + ".import")
    nmap_val = 1 if is_normal else 0
    if imp_path.exists():
        text = imp_path.read_text(encoding="utf-8")
        new_text = re.sub(r"^compress/normal_map=\d+", f"compress/normal_map={nmap_val}", text, flags=re.MULTILINE)
        new_text = re.sub(r"^compress/mode=\d+", "compress/mode=2", new_text, flags=re.MULTILINE)
        new_text = re.sub(r"^process/size_limit=\d+", f"process/size_limit={cap}", new_text, flags=re.MULTILINE)
        if new_text != text:
            imp_path.write_text(new_text, encoding="utf-8")
            return True
        return False

    res_path = "res://" + img_path.relative_to(ROOT).as_posix()
    content = f"""[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="{res_path}"

[params]

compress/mode=2
compress/high_quality=false
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map={nmap_val}
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit={cap}
detect_3d/compress_to=1
"""
    imp_path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)

    glbs = sorted(MODELS_DIR.rglob("*.glb"))
    assert len(glbs) > 0, f"No GLBs found under {MODELS_DIR}"

    unique_records = {}  # (sha256, cap) -> dict
    tex_map = {}

    for glb_path in glbs:
        rel_glb = glb_path.relative_to(ROOT).as_posix()
        res_glb = "res://" + rel_glb
        cap = 768 if "/weapons/" in ("/" + rel_glb) else 512
        gltf, blob = parse_glb(glb_path)

        textures = gltf.get("textures", [])
        images = gltf.get("images", [])
        materials = gltf.get("materials", [])

        normal_img_indices = set()
        for mat in materials:
            if "normalTexture" in mat:
                ti = mat["normalTexture"]["index"]
                if ti < len(textures) and "source" in textures[ti]:
                    normal_img_indices.add(textures[ti]["source"])

        img_idx_to_res = {}
        for ii, im in enumerate(images):
            bv = gltf["bufferViews"][im["bufferView"]]
            raw = blob[bv.get("byteOffset", 0) : bv.get("byteOffset", 0) + bv["byteLength"]]
            sha = hashlib.sha256(raw).hexdigest()
            is_normal = ii in normal_img_indices
            key = (sha, cap)
            if key not in unique_records:
                stem = sanitize_stem(im.get("name", ""), f"tex_{ii}")
                # Prefer semantic name even if first encounter was generic img_7
                mime = im.get("mimeType", "")
                pil_img = Image.open(io.BytesIO(raw))
                w, h = pil_img.size
                needs_resize = max(w, h) > cap
                has_alpha = pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info)

                if needs_resize:
                    scale = cap / float(max(w, h))
                    nw = max(1, int(round(w * scale)))
                    nh = max(1, int(round(h * scale)))
                    out_img = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
                    if is_normal or has_alpha or "png" in mime:
                        ext = ".png"
                        buf = io.BytesIO()
                        out_img.save(buf, format="PNG", optimize=True)
                        out_bytes = buf.getvalue()
                    else:
                        ext = ".jpg"
                        if out_img.mode != "RGB":
                            out_img = out_img.convert("RGB")
                        buf = io.BytesIO()
                        out_img.save(buf, format="JPEG", quality=92, optimize=True)
                        out_bytes = buf.getvalue()
                else:
                    ext = ".jpg" if ("jpeg" in mime or "jpg" in mime) else ".png"
                    out_bytes = raw

                fname = f"{stem}_{cap}_{sha[:8]}{ext}"
                unique_records[key] = {
                    "fname": fname,
                    "bytes": out_bytes,
                    "is_normal": is_normal,
                    "cap": cap,
                    "orig_size": (w, h),
                    "resized": needs_resize,
                    "best_stem_score": 0 if re.match(r"^(img|tex)_\d+$", stem) else 1,
                }
            else:
                rec = unique_records[key]
                rec["is_normal"] = rec["is_normal"] or is_normal
                stem = sanitize_stem(im.get("name", ""), f"tex_{ii}")
                score = 0 if re.match(r"^(img|tex)_\d+$", stem) else 1
                if score > rec["best_stem_score"]:
                    ext = pathlib.Path(rec["fname"]).suffix
                    rec["fname"] = f"{stem}_{cap}_{sha[:8]}{ext}"
                    rec["best_stem_score"] = score

            img_idx_to_res[ii] = key

        glb_entry = {}
        for mat in materials:
            mname = mat.get("name", "")
            if not mname:
                continue
            spec = {}
            pbr = mat.get("pbrMetallicRoughness", {})
            if "baseColorTexture" in pbr:
                ti = pbr["baseColorTexture"]["index"]
                src = textures[ti]["source"]
                spec["albedo_key"] = img_idx_to_res[src]
            if "normalTexture" in mat:
                ti = mat["normalTexture"]["index"]
                src = textures[ti]["source"]
                spec["normal_key"] = img_idx_to_res[src]
                spec["normal_scale"] = float(mat["normalTexture"].get("scale", 1.0))
            if "metallicRoughnessTexture" in pbr:
                ti = pbr["metallicRoughnessTexture"]["index"]
                src = textures[ti]["source"]
                spec["orm_key"] = img_idx_to_res[src]
            if "emissiveTexture" in mat:
                ti = mat["emissiveTexture"]["index"]
                src = textures[ti]["source"]
                spec["emissive_key"] = img_idx_to_res[src]
            if spec:
                glb_entry[mname] = spec

        if glb_entry:
            tex_map[res_glb] = glb_entry

    # Write shared textures cleanly, removing any stale unreferenced files inside _shared_tex
    expected_fnames = {rec["fname"] for rec in unique_records.values()}
    removed_stale = 0
    for existing in list(SHARED_DIR.iterdir()):
        if existing.name.endswith(".import"):
            target_name = existing.name[:-7]
            if target_name not in expected_fnames:
                existing.unlink()
                removed_stale += 1
        elif existing.name not in expected_fnames:
            existing.unlink()
            removed_stale += 1

    written = 0
    resized_cnt = 0
    imp_touched = 0
    for key, rec in unique_records.items():
        out_file = SHARED_DIR / rec["fname"]
        if (not out_file.exists()) or out_file.read_bytes() != rec["bytes"]:
            out_file.write_bytes(rec["bytes"])
            written += 1
        if rec["resized"]:
            resized_cnt += 1
        if write_import_if_needed(out_file, rec["is_normal"], rec["cap"]):
            imp_touched += 1

    # Convert keys in tex_map to final res:// paths
    final_map = {}
    for res_glb, mats in tex_map.items():
        final_mats = {}
        for mname, spec in mats.items():
            out_spec = {}
            for slot in ("albedo", "normal", "orm", "emissive"):
                kname = slot + "_key"
                if kname in spec:
                    rec = unique_records[spec[kname]]
                    out_spec[slot] = f"res://assets/models/_shared_tex/{rec['fname']}"
            if "normal_scale" in spec:
                out_spec["normal_scale"] = spec["normal_scale"]
            final_mats[mname] = out_spec
        final_map[res_glb] = final_mats

    OUT_MAP.write_text(json.dumps(final_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    total_mb = sum(len(r["bytes"]) for r in unique_records.values()) / (1024 * 1024)
    print(f"GLBs scanned: {len(glbs)} (with textures: {len(final_map)})")
    print(f"Unique shared textures: {len(unique_records)} (resized >cap: {resized_cnt}, written: {written}, .import touched: {imp_touched}, stale removed: {removed_stale})")
    print(f"Total shared texture disk size: {total_mb:.2f} MB")
    print(f"Wrote map: {OUT_MAP}")


if __name__ == "__main__":
    main()
