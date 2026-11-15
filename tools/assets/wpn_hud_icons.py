#!/usr/bin/env python3
"""Generate crisp, anti-aliased CoD Zombies HUD icons matching the existing rounded badge style."""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

UI_DIR = Path(__file__).resolve().parents[2] / "assets" / "textures" / "ui"


def _rounded_badge(bg_rgb, accent_rgb, draw_emblem_fn, size=128):
    # Supersample 4x for razor-sharp anti-aliasing
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)

    pad = int(s * 0.06)
    rad = int(s * 0.20)
    cream = (246, 240, 224, 255)
    dark = (32, 34, 38, 255)
    dr.rounded_rectangle((pad, pad, s - pad, s - pad), radius=rad, fill=cream)
    p2 = pad + int(s * 0.045)
    dr.rounded_rectangle((p2, p2, s - p2, s - p2), radius=int(rad * 0.85), fill=bg_rgb + (255,))
    p3 = p2 + int(s * 0.032)
    dr.rounded_rectangle((p3, p3, s - p3, s - p3), radius=int(rad * 0.72), outline=dark, width=max(4, int(s * 0.030)))
    # Subtle inner highlight gradient top edge
    dr.rounded_rectangle(
        (p3 + 6, p3 + 6, s - p3 - 6, s - p3 - 6),
        radius=int(rad * 0.65),
        outline=accent_rgb + (120,),
        width=max(2, int(s * 0.012)),
    )

    draw_emblem_fn(dr, s, cream, dark)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def _emblem_mulekick(dr, s, cream, dark):
    # Three crisp upright cartridges / rifle silhouettes side by side
    cx, cy = s * 0.50, s * 0.52
    for dx in (-0.18, 0.0, 0.18):
        x = cx + dx * s
        w = s * 0.055
        # Casing body
        dr.rounded_rectangle((x - w, cy - s * 0.10, x + w, cy + s * 0.22), radius=int(w * 0.35), fill=cream, outline=dark, width=6)
        # Bullet ogive tip
        tip = [(x - w * 0.85, cy - s * 0.10), (x, cy - s * 0.26), (x + w * 0.85, cy - s * 0.10)]
        dr.polygon(tip, fill=cream, outline=dark)
        # Extractor groove
        dr.rectangle((x - w * 0.9, cy + s * 0.14, x + w * 0.9, cy + s * 0.18), fill=dark)


def _emblem_deadshot(dr, s, cream, dark):
    # Crisp sniper crosshair reticle + bullseye center
    cx, cy = s * 0.50, s * 0.50
    r1 = s * 0.24
    r2 = s * 0.11
    lw = max(8, int(s * 0.042))
    dr.ellipse((cx - r1, cy - r1, cx + r1, cy + r1), outline=cream, width=lw)
    dr.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), outline=cream, width=max(5, lw // 2))
    dr.ellipse((cx - s * 0.04, cy - s * 0.04, cx + s * 0.04, cy + s * 0.04), fill=(215, 42, 36, 255))
    # 4 crosshair ticks
    gap = s * 0.09
    ext = s * 0.31
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dr.line((cx + dx * gap, cy + dy * gap, cx + dx * ext, cy + dy * ext), fill=cream, width=lw)


def _emblem_phd(dr, s, cream, dark):
    # Tactical dive bomb / mushroom blast emblem
    cx, cy = s * 0.50, s * 0.52
    # Explosion mushroom cap
    dr.pieslice((cx - s * 0.26, cy - s * 0.28, cx + s * 0.26, cy + s * 0.04), start=180, end=360, fill=cream)
    # Stem & base blast cloud
    dr.polygon(
        [
            (cx - s * 0.08, cy - s * 0.10),
            (cx + s * 0.08, cy - s * 0.10),
            (cx + s * 0.14, cy + s * 0.18),
            (cx - s * 0.14, cy + s * 0.18),
        ],
        fill=cream,
    )
    dr.rounded_rectangle((cx - s * 0.26, cy + s * 0.14, cx + s * 0.26, cy + s * 0.24), radius=14, fill=cream)
    # Shockwave chevron accent inside stem
    dr.polygon([(cx, cy - s * 0.20), (cx + s * 0.08, cy - s * 0.06), (cx - s * 0.08, cy - s * 0.06)], fill=dark)


def _emblem_cherry(dr, s, cream, dark):
    # Electric lightning bolt flanked by twin energy arcs / cherry stems
    cx, cy = s * 0.50, s * 0.50
    bolt = [
        (cx + s * 0.06, cy - s * 0.28),
        (cx - s * 0.14, cy + s * 0.02),
        (cx + s * 0.01, cy + s * 0.02),
        (cx - s * 0.07, cy + s * 0.28),
        (cx + s * 0.16, cy - s * 0.04),
        (cx + s * 0.00, cy - s * 0.04),
    ]
    dr.polygon(bolt, fill=cream, outline=dark)
    # Twin glowing cherry spheres at lower left/right
    r = s * 0.075
    for sx in (-0.19, 0.19):
        bx = cx + sx * s
        by = cy + s * 0.17
        dr.ellipse((bx - r, by - r, bx + r, by + r), fill=(225, 48, 56, 255), outline=cream, width=6)


def make_pap_badge(width=128, height=56):
    s = 4
    w, h = width * s, height * s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    pad = 12
    cyan = (62, 232, 255, 255)
    dark = (14, 24, 34, 235)
    dr.rounded_rectangle((pad, pad, w - pad, h - pad), radius=36, fill=dark, outline=cyan, width=10)
    # Runic twin diamonds left & right + chevron bars
    cy = h // 2
    for dx in (int(w * 0.18), int(w * 0.82)):
        dr.polygon([(dx, cy - 44), (dx + 28, cy), (dx, cy + 44), (dx - 28, cy)], fill=cyan)
    # Center triple PaP bars / glyph (clean crisp vector mark, no tiny font mismatch)
    cx = w // 2
    dr.polygon([(cx, cy - 52), (cx + 42, cy), (cx, cy + 52), (cx - 42, cy)], outline=cyan, width=10)
    dr.polygon([(cx, cy - 26), (cx + 21, cy), (cx, cy + 26), (cx - 21, cy)], fill=(210, 252, 255, 255))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def make_grenade_icon(size=96):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx, cy = s * 0.48, s * 0.56
    olive = (232, 236, 224, 240)
    dark = (22, 24, 22, 255)
    # Pineapple body
    dr.rounded_rectangle((cx - s * 0.20, cy - s * 0.22, cx + s * 0.20, cy + s * 0.28), radius=int(s * 0.16), fill=olive, outline=dark, width=10)
    # Waffle grooves
    for gx in (-0.07, 0.07):
        dr.line((cx + gx * s, cy - s * 0.19, cx + gx * s, cy + s * 0.25), fill=dark, width=7)
    for gy in (-0.06, 0.08):
        dr.line((cx - s * 0.18, cy + gy * s, cx + s * 0.18, cy + gy * s), fill=dark, width=7)
    # Fuze head
    dr.rounded_rectangle((cx - s * 0.08, cy - s * 0.36, cx + s * 0.08, cy - s * 0.20), radius=8, fill=olive, outline=dark, width=9)
    # Spoon lever
    dr.line([(cx + s * 0.08, cy - s * 0.34), (cx + s * 0.24, cy - s * 0.25), (cx + s * 0.27, cy + s * 0.08)], fill=olive, width=14)
    # Pin ring
    dr.ellipse((cx - s * 0.24, cy - s * 0.38, cx - s * 0.06, cy - s * 0.20), outline=olive, width=10)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main():
    UI_DIR.mkdir(parents=True, exist_ok=True)
    _rounded_badge((34, 148, 66), (110, 245, 140), _emblem_mulekick).save(UI_DIR / "hud_perk_mulekick.png")
    _rounded_badge((214, 152, 28), (255, 220, 95), _emblem_deadshot).save(UI_DIR / "hud_perk_deadshot.png")
    _rounded_badge((126, 48, 178), (210, 110, 255), _emblem_phd).save(UI_DIR / "hud_perk_phdflopper.png")
    _rounded_badge((28, 162, 224), (110, 240, 255), _emblem_cherry).save(UI_DIR / "hud_perk_electriccherry.png")
    make_pap_badge().save(UI_DIR / "hud_pap_badge.png")
    make_grenade_icon().save(UI_DIR / "hud_grenade_icon.png")
    print("[HUD_ICONS] Regenerated 6 crisp anti-aliased HUD icons in", UI_DIR)


if __name__ == "__main__":
    main()
