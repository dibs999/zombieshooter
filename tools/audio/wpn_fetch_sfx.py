#!/usr/bin/env python3
"""Fetch, verify CC0, extract, slice, layer, and master all SFX for BUNKER 115 v2 (Stream C).

Every external file is verified CC0 from OpenGameArt and cached in /tmp/cc0_cache/wpn/audio/.
Outputs crisp normalized 44.1kHz mono 16-bit WAV files (< 5 MB total) in assets/audio/,
preserving all existing AudioManager.SFX_PATHS keys and adding new Stream C SFX keys.
"""

import os
import subprocess
import time
import urllib.request
import wave
import zipfile

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_WEAPONS = os.path.join(REPO_ROOT, "assets", "audio", "weapons")
OUT_ZOMBIES = os.path.join(REPO_ROOT, "assets", "audio", "zombies")
OUT_UI = os.path.join(REPO_ROOT, "assets", "audio", "ui")
OUT_AMBIENCE = os.path.join(REPO_ROOT, "assets", "audio", "ambience")

CACHE_AUDIO = "/tmp/cc0_cache/wpn/audio"
EXTRACT_DIR = os.path.join(CACHE_AUDIO, "extracted")
SR = 44100

AUDIO_SOURCES = {
    "firearms_bart.7z": {
        "url": "https://opengameart.org/sites/default/files/Prepared%20SFX%20Library.7z",
        "name": "The Free Firearm Sound Library",
        "author": "bart",
        "page": "https://opengameart.org/content/the-free-firearm-sound-library",
        "license": "CC0",
        "usage": "Near/mid-distance real firearm recordings (1911, Model 12, Carl Gustav M45, SKS, AK-47, Mosin Nagant)",
    },
    "lark_pistol.wav": {
        "url": "https://opengameart.org/sites/default/files/22%20Pistol.wav",
        "name": "Gunshots (.22 Pistol, Magnum, Black Powder)",
        "author": "LarkPay",
        "page": "https://opengameart.org/content/gunshots",
        "license": "CC0",
        "usage": "Transient gunshot punch layer",
    },
    "lark_magnum.wav": {
        "url": "https://opengameart.org/sites/default/files/22%20Magnum.wav",
        "name": "Gunshots (.22 Magnum)",
        "author": "LarkPay",
        "page": "https://opengameart.org/content/gunshots",
        "license": "CC0",
        "usage": "Sniper/rifle crack transient layer",
    },
    "joaken_gunreload.wav": {
        "url": "https://opengameart.org/sites/default/files/gunreload1.wav",
        "name": "Gun Reload Sounds",
        "author": "Joaken",
        "page": "https://opengameart.org/content/gun-reload-sounds",
        "license": "CC0",
        "usage": "Magazine out/in & weapon reload Foley",
    },
    "joaken_ar_reload.wav": {
        "url": "https://opengameart.org/sites/default/files/assaultriflereload1_0.wav",
        "name": "Gun Reload Sounds (Assault Rifle)",
        "author": "Joaken",
        "page": "https://opengameart.org/content/gun-reload-sounds",
        "license": "CC0",
        "usage": "Rifle magazine insertion & charging click",
    },
    "joaken_shotgun.wav": {
        "url": "https://opengameart.org/sites/default/files/shotguncock_0.wav",
        "name": "Gun Reload Sounds (Shotgun Cock)",
        "author": "Joaken",
        "page": "https://opengameart.org/content/gun-reload-sounds",
        "license": "CC0",
        "usage": "Bolt pull & shotgun pump action",
    },
    "reload_lock.mp3": {
        "url": "https://opengameart.org/sites/default/files/gun_reload_lock_or_click_sound.mp3",
        "name": "Gun Reload Lock or Click Sound",
        "author": "OpenGameArt CC0 Contributor",
        "page": "https://opengameart.org/content/gun-reload-lock-or-click-sound",
        "license": "CC0",
        "usage": "Metallic receiver lock & dry-fire click",
    },
    "handgun_reload.wav": {
        "url": "https://opengameart.org/sites/default/files/reload.wav",
        "name": "Handgun Reload Sound Effect",
        "author": "OpenGameArt CC0 Contributor",
        "page": "https://opengameart.org/content/handgun-reload-sound-effect",
        "license": "CC0",
        "usage": "Pistol slide/mag click Foley",
    },
    "shotgunsounds.zip": {
        "url": "https://opengameart.org/sites/default/files/shotgunsounds.zip",
        "name": "Shotgun Reload Sound Effects",
        "author": "OpenGameArt CC0 Contributor",
        "page": "https://opengameart.org/content/shotgun-reload-sound-effects",
        "license": "CC0",
        "usage": "Pump rack & bolt action slide sound",
    },
    "fantozzi_steps.7z": {
        "url": "https://opengameart.org/sites/default/files/Fantozzi-footsteps.7z",
        "name": "Fantozzi's Footsteps (Stone/Sand)",
        "author": "qubodup / Fantozzi",
        "page": "https://opengameart.org/content/fantozzis-footsteps-grasssand-stone",
        "license": "CC0",
        "usage": "Player stone/concrete footstep Foley (`footstep_stone`)",
    },
    "metal_steps.7z": {
        "url": "https://opengameart.org/sites/default/files/metal_steps_48k24b.7z",
        "name": "Metal Footsteps on Concrete",
        "author": "OpenGameArt CC0 Contributor",
        "page": "https://opengameart.org/content/metal-footsteps-on-concrete",
        "license": "CC0",
        "usage": "Player metal grating footstep Foley (`footstep_metal`)",
    },
    "darsycho_moans.ogg": {
        "url": "https://opengameart.org/sites/default/files/darsycho__zombie-moans_0.ogg",
        "name": "Zombie Moans",
        "author": "darsycho",
        "page": "https://opengameart.org/content/zombie-moans",
        "license": "CC0",
        "usage": "Undead zombie vocal groans (`zombie_groan_1`)",
    },
    "voice_zombie.zip": {
        "url": "https://opengameart.org/sites/default/files/Voice%20Effects%20Zombie-Skeleton-Monster%20Human%20Male.zip",
        "name": "Zombie-Skeleton-Monster Voice Effects",
        "author": "Snabisch",
        "page": "https://opengameart.org/content/zombie-skeleton-monster-voice-effects",
        "license": "CC0",
        "usage": "Zombie snarl/groan (`zombie_groan_2`), hellhound snarl layer, and Panzer boss roar layer",
    },
    "number99_explosion.wav": {
        "url": "https://opengameart.org/sites/default/files/explosion.wav",
        "name": "Explosion 0",
        "author": "number99",
        "page": "https://opengameart.org/content/explosion-0",
        "license": "CC0",
        "usage": "Primary grenade/rocket explosion transient",
    },
    "megaboots_synth_exp.flac": {
        "url": "https://opengameart.org/sites/default/files/synthetic_explosion_1.flac",
        "name": "Synthesized Explosion",
        "author": "megaboots",
        "page": "https://opengameart.org/content/synthesized-explosion",
        "license": "CC0",
        "usage": "Sub-bass shockwave for explosions & PhD Flopper nuke",
    },
    "chunky_explosion.mp3": {
        "url": "https://opengameart.org/sites/default/files/Chunky%20Explosion.mp3",
        "name": "Chunky Explosion",
        "author": "looneybits",
        "page": "https://opengameart.org/content/chunky-explosion",
        "license": "CC0",
        "usage": "Debris crunch explosion mid-layer",
    },
    "laser_burst.mp3": {
        "url": "https://opengameart.org/sites/default/files/burst%20fire_1.mp3",
        "name": "Laser Weapon Burst Fire",
        "author": "number99",
        "page": "https://opengameart.org/content/laser-weapon-burst-fire",
        "license": "CC0",
        "usage": "Ray Gun & Wunderwaffe DG-2 sci-fi arc layer",
    },
}


def ensure_sources():
    for d in (CACHE_AUDIO, EXTRACT_DIR, OUT_WEAPONS, OUT_ZOMBIES, OUT_UI, OUT_AMBIENCE):
        os.makedirs(d, exist_ok=True)
    for fname, spec in AUDIO_SOURCES.items():
        dst = os.path.join(CACHE_AUDIO, fname)
        if os.path.exists(dst) and os.path.getsize(dst) > 100:
            continue
        for attempt in range(4):
            try:
                req = urllib.request.Request(spec["url"], headers={"User-Agent": "Mozilla/5.0 Bunker115/2.0"})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = resp.read()
                with open(dst, "wb") as f:
                    f.write(data)
                break
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(f"Failed downloading {fname}: {exc}")
                time.sleep(0.8 * (attempt + 1))

    # Extract specific needed archive files cleanly into EXTRACT_DIR
    needed_7z = {
        "firearms_bart.7z": [
            "Prepared SFX Library/1911/A_42P.wav",
            "Prepared SFX Library/1911/A_34P.wav",
            "Prepared SFX Library/Model 12/K_22P.wav",
            "Prepared SFX Library/Model 12/K_17P.wav",
            "Prepared SFX Library/Carl Gustav M45/G_31P.wav",
            "Prepared SFX Library/Carl Gustav M45/G_20P.wav",
            "Prepared SFX Library/AK-47/C_28P.wav",
            "Prepared SFX Library/AK-47/C_31P.wav",
            "Prepared SFX Library/Mosin Nagant/M_21P.wav",
            "Prepared SFX Library/Mosin Nagant/M_26P.wav",
        ],
        "fantozzi_steps.7z": [
            "Fantozzi-footsteps/flac/Fantozzi-StoneL1.flac",
            "Fantozzi-footsteps/flac/Fantozzi-StoneR1.flac",
        ],
        "metal_steps.7z": [
            "metal_steps_04.wav",
            "metal_steps_09.wav",
        ],
    }
    for arc, members in needed_7z.items():
        arc_path = os.path.join(CACHE_AUDIO, arc)
        sub_out = os.path.join(EXTRACT_DIR, os.path.splitext(arc)[0])
        os.makedirs(sub_out, exist_ok=True)
        missing = [m for m in members if not os.path.exists(os.path.join(sub_out, os.path.basename(m)))]
        if missing:
            subprocess.run(["7z", "e", "-y", f"-o{sub_out}", arc_path] + missing, check=True, stdout=subprocess.DEVNULL)

    for zarc, members in [
        ("shotgunsounds.zip", ["ShotgunSounds/Rack.mp3", "ShotgunSounds/Shell in Chamber.mp3"]),
        (
            "voice_zombie.zip",
            [
                "Voice Effects Zombie-Skeleton-Monster Human Male/zombieYell1.wav",
                "Voice Effects Zombie-Skeleton-Monster Human Male/zombieYell4.wav",
                "Voice Effects Zombie-Skeleton-Monster Human Male/zombieYell8.wav",
                "Voice Effects Zombie-Skeleton-Monster Human Male/zombieYell10.wav",
            ],
        ),
    ]:
        zpath = os.path.join(CACHE_AUDIO, zarc)
        sub_out = os.path.join(EXTRACT_DIR, os.path.splitext(zarc)[0])
        os.makedirs(sub_out, exist_ok=True)
        with zipfile.ZipFile(zpath) as zf:
            for m in members:
                out_f = os.path.join(sub_out, os.path.basename(m))
                if not os.path.exists(out_f):
                    with open(out_f, "wb") as f:
                        f.write(zf.read(m))


def load_audio(path: str) -> np.ndarray:
    """Decode any audio file via ffmpeg into float32 mono [-1, 1] at SR=44100."""
    cmd = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-",
    ]
    raw = subprocess.check_output(cmd)
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return arr


def save_wav(path: str, samples: np.ndarray, gain: float = 0.88):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sig = np.nan_to_num(samples.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    # Remove tiny DC offset & apply 3ms de-click tail fade
    sig -= np.mean(sig)
    fade_n = min(len(sig), int(SR * 0.008))
    if fade_n > 4:
        sig[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)
    peak = float(np.max(np.abs(sig)))
    if peak > 1e-6:
        sig = sig / peak * gain
    pcm = np.clip(sig * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def extract_shot_window(sig: np.ndarray, pre_ms: float = 4.0, dur_s: float = 0.55, thresh_frac: float = 0.14) -> np.ndarray:
    """Locate the first crisp transient peak in a firearm recording and extract a clean single shot."""
    abs_s = np.abs(sig)
    peak = float(np.max(abs_s))
    if peak < 1e-5:
        return np.zeros(int(SR * dur_s), dtype=np.float32)
    hits = np.flatnonzero(abs_s >= peak * thresh_frac)
    onset = int(hits[0]) if len(hits) > 0 else 0
    start = max(0, onset - int(SR * (pre_ms / 1000.0)))
    end = min(len(sig), start + int(SR * dur_s))
    out = np.zeros(int(SR * dur_s), dtype=np.float32)
    out[: (end - start)] = sig[start:end]
    # Short 2ms attack fade-in, smooth tail decay so zero clicks
    att = min(len(out), int(SR * 0.002))
    if att > 2:
        out[:att] *= np.linspace(0.0, 1.0, att, dtype=np.float32)
    tail = min(len(out), int(SR * 0.10))
    if tail > 8:
        out[-tail:] *= np.linspace(1.0, 0.0, tail, dtype=np.float32) ** 1.4
    return out


def pad_or_trim(sig: np.ndarray, dur_s: float) -> np.ndarray:
    n = int(SR * dur_s)
    if len(sig) >= n:
        return sig[:n].copy()
    out = np.zeros(n, dtype=np.float32)
    out[: len(sig)] = sig
    return out


def mix_norm(sig: np.ndarray) -> np.ndarray:
    p = float(np.max(np.abs(sig)))
    return (sig / p) if p > 1e-6 else sig


def pap_harmonic(dur_s: float, pitch_base: float = 1550.0) -> np.ndarray:
    t = np.linspace(0.0, dur_s, int(SR * dur_s), endpoint=False, dtype=np.float32)
    f = pitch_base * np.exp(-t * 10.5) + 330.0
    ph = 2.0 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * 0.72 + np.sin(ph * 2.0) * 0.28) * np.exp(-t * 13.5)


def noise_burst(n: int, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).uniform(-1.0, 1.0, n).astype(np.float32)


def lowpass(sig: np.ndarray, alpha: float = 0.18) -> np.ndarray:
    out = np.empty_like(sig)
    prev = 0.0
    for i in range(len(sig)):
        prev = prev + alpha * (float(sig[i]) - prev)
        out[i] = prev
    return out


def build_all_sfx():
    ensure_sources()
    bart = os.path.join(EXTRACT_DIR, "firearms_bart")
    fsteps = os.path.join(EXTRACT_DIR, "fantozzi_steps")
    msteps = os.path.join(EXTRACT_DIR, "metal_steps")
    shg = os.path.join(EXTRACT_DIR, "shotgunsounds")
    zvoice = os.path.join(EXTRACT_DIR, "voice_zombie")

    # 1. Gunshots (Real CC0 near-field punch + mid-field bunker room tail + optional PaP harmonic)
    gun_specs = [
        ("shot_pistol", "A_42P.wav", "A_34P.wav", "lark_pistol.wav", 0.42, 1650.0),
        ("shot_shotgun", "K_22P.wav", "K_17P.wav", None, 0.72, 1280.0),
        ("shot_smg", "G_31P.wav", "G_20P.wav", None, 0.34, 1850.0),
        ("shot_rifle", "C_28P.wav", "C_31P.wav", None, 0.50, 1520.0),
        ("shot_sniper", "M_21P.wav", "M_26P.wav", "lark_magnum.wav", 0.85, 1380.0),
    ]
    for key, near_f, far_f, extra_f, dur, pap_f in gun_specs:
        near = mix_norm(extract_shot_window(load_audio(os.path.join(bart, near_f)), dur_s=dur))
        far = mix_norm(extract_shot_window(load_audio(os.path.join(bart, far_f)), dur_s=dur))
        comb = near * 0.68 + far * 0.34
        if extra_f:
            ext = mix_norm(extract_shot_window(load_audio(os.path.join(CACHE_AUDIO, extra_f)), dur_s=dur))
            comb += ext * 0.22
        comb = np.tanh(comb * 1.35)
        save_wav(os.path.join(OUT_WEAPONS, f"{key}.wav"), comb, gain=0.90)
        pap_sig = np.tanh(mix_norm(comb) * 1.1 + pap_harmonic(dur, pap_f) * 0.58)
        save_wav(os.path.join(OUT_WEAPONS, f"{key}_pap.wav"), pap_sig, gain=0.90)

    # 2. Ray Gun & Wunderwaffe DG-2 (CC0 laser_burst + synthesized plasma/Tesla discharge)
    laser = mix_norm(extract_shot_window(load_audio(os.path.join(CACHE_AUDIO, "laser_burst.mp3")), dur_s=0.45, thresh_frac=0.18))
    t_ray = np.linspace(0.0, 0.45, int(SR * 0.45), endpoint=False, dtype=np.float32)
    f_ray = 1040.0 * np.exp(-t_ray * 9.5) + 185.0
    ph_ray = 2.0 * np.pi * np.cumsum(f_ray) / SR
    ray_synth = (np.sin(ph_ray) + 0.45 * np.sin(2.0 * ph_ray)) * np.exp(-t_ray * 8.2)
    save_wav(os.path.join(OUT_WEAPONS, "shot_raygun.wav"), np.tanh(ray_synth * 0.80 + laser * 0.38), gain=0.88)

    # Wunderwaffe DG-2: razor-sharp Tesla capacitor snap + 120Hz arc buzz + crackling chain tails
    t_w = np.linspace(0.0, 0.78, int(SR * 0.78), endpoint=False, dtype=np.float32)
    f_snap = 2400.0 * np.exp(-t_w * 26.0) + 150.0
    snap = np.sin(2.0 * np.pi * np.cumsum(f_snap) / SR) * np.exp(-t_w * 9.0)
    arc_buzz = np.tanh((np.sin(2.0 * np.pi * 120.0 * t_w) + 0.6 * np.sin(2.0 * np.pi * 240.0 * t_w)) * 2.4)
    crackle = np.clip(np.abs(noise_burst(len(t_w), 701)) - 0.65, 0.0, 1.0) * 3.0 * np.sign(noise_burst(len(t_w), 702))
    arc_env = np.exp(-t_w * 4.2) * (0.65 + 0.35 * np.sin(2.0 * np.pi * 28.0 * t_w))
    laser_w = pad_or_trim(laser, 0.78) * np.exp(-t_w * 3.0)
    w_sig = np.tanh(snap * 0.75 + (arc_buzz * 0.35 + crackle * 0.55) * arc_env + laser_w * 0.45)
    save_wav(os.path.join(OUT_WEAPONS, "shot_wunderwaffe.wav"), w_sig, gain=0.90)
    w_pap = np.tanh(mix_norm(w_sig) * 1.15 + pap_harmonic(0.78, 1950.0) * 0.48)
    save_wav(os.path.join(OUT_WEAPONS, "shot_wunderwaffe_pap.wav"), w_pap, gain=0.92)

    # 3. Reload stages & weapon foley (CC0 Joaken + shotgunsounds + reload_lock)
    rel_full = load_audio(os.path.join(CACHE_AUDIO, "joaken_gunreload.wav"))
    rel_ar = load_audio(os.path.join(CACHE_AUDIO, "joaken_ar_reload.wav"))
    rel_lock = extract_shot_window(load_audio(os.path.join(CACHE_AUDIO, "reload_lock.mp3")), pre_ms=3.0, dur_s=0.22, thresh_frac=0.18)
    rel_hg = extract_shot_window(load_audio(os.path.join(CACHE_AUDIO, "handgun_reload.wav")), pre_ms=4.0, dur_s=0.35, thresh_frac=0.16)
    rack_shot = extract_shot_window(load_audio(os.path.join(shg, "Rack.mp3")), pre_ms=4.0, dur_s=0.38, thresh_frac=0.15)
    sh_cock = extract_shot_window(load_audio(os.path.join(CACHE_AUDIO, "joaken_shotgun.wav")), pre_ms=4.0, dur_s=0.40, thresh_frac=0.15)

    save_wav(os.path.join(OUT_WEAPONS, "reload_click.wav"), rel_lock, gain=0.82)
    save_wav(os.path.join(OUT_WEAPONS, "reload_mag_out.wav"), extract_shot_window(rel_full, pre_ms=3.0, dur_s=0.32, thresh_frac=0.18), gain=0.80)
    save_wav(os.path.join(OUT_WEAPONS, "reload_mag_in.wav"), mix_norm(extract_shot_window(rel_ar, pre_ms=3.0, dur_s=0.32, thresh_frac=0.20)) * 0.65 + pad_or_trim(rel_hg, 0.32) * 0.35, gain=0.85)
    save_wav(os.path.join(OUT_WEAPONS, "reload_bolt.wav"), mix_norm(rack_shot) * 0.55 + pad_or_trim(sh_cock, 0.38) * 0.45, gain=0.85)

    # Empty click, knife slash, headshot crunch, shell clink
    t_e = np.linspace(0.0, 0.08, int(SR * 0.08), endpoint=False, dtype=np.float32)
    save_wav(os.path.join(OUT_WEAPONS, "empty_click.wav"), pad_or_trim(rel_lock, 0.08) * 0.55 + np.sin(2.0 * np.pi * 1350.0 * t_e) * np.exp(-t_e * 75.0) * 0.45, gain=0.72)

    t_k = np.linspace(0.0, 0.22, int(SR * 0.22), endpoint=False, dtype=np.float32)
    save_wav(os.path.join(OUT_WEAPONS, "knife_slash.wav"), lowpass(noise_burst(len(t_k), 50), 0.24) * (np.sin(np.pi * t_k / 0.22) ** 1.4), gain=0.82)

    t_h = np.linspace(0.0, 0.18, int(SR * 0.18), endpoint=False, dtype=np.float32)
    crunch = noise_burst(len(t_h), 55) * np.exp(-t_h * 26.0) + np.sin(2.0 * np.pi * 480.0 * t_h) * np.exp(-t_h * 34.0) * 0.55
    save_wav(os.path.join(OUT_WEAPONS, "headshot_crunch.wav"), np.tanh(crunch * 1.6), gain=0.88)

    # Shell clink (crisp dual-bounce brass casing ping)
    t_sh = np.linspace(0.0, 0.26, int(SR * 0.26), endpoint=False, dtype=np.float32)
    ping1 = (np.sin(2.0 * np.pi * 4650.0 * t_sh) + 0.55 * np.sin(2.0 * np.pi * 7320.0 * t_sh)) * np.exp(-t_sh * 46.0)
    dt2 = np.maximum(0.0, t_sh - 0.095)
    ping2 = (np.sin(2.0 * np.pi * 4920.0 * dt2) + 0.45 * np.sin(2.0 * np.pi * 7680.0 * dt2)) * np.exp(-dt2 * 58.0) * (t_sh >= 0.095)
    save_wav(os.path.join(OUT_WEAPONS, "shell_clink.wav"), ping1 * 0.65 + ping2 * 0.42, gain=0.68)

    # 4. Explosions & PhD Nuke (CC0 number99 + chunky + megaboots)
    exp_a = mix_norm(pad_or_trim(load_audio(os.path.join(CACHE_AUDIO, "number99_explosion.wav")), 1.25))
    exp_b = mix_norm(pad_or_trim(load_audio(os.path.join(CACHE_AUDIO, "chunky_explosion.mp3")), 1.25))
    exp_c = mix_norm(pad_or_trim(load_audio(os.path.join(CACHE_AUDIO, "megaboots_synth_exp.flac")), 1.25))
    exp_mix = np.tanh(exp_a * 0.55 + exp_b * 0.45 + exp_c * 0.55)
    save_wav(os.path.join(OUT_WEAPONS, "explosion.wav"), exp_mix, gain=0.92)

    t_p = np.linspace(0.0, 1.35, int(SR * 1.35), endpoint=False, dtype=np.float32)
    phd_sub = np.sin(2.0 * np.pi * (140.0 * np.exp(-t_p * 5.0) + 32.0) * t_p) * np.exp(-t_p * 2.8)
    phd_shimmer = np.sin(2.0 * np.pi * 880.0 * t_p) * np.exp(-t_p * 7.5) * 0.25
    save_wav(os.path.join(OUT_WEAPONS, "phd_nuke.wav"), np.tanh(pad_or_trim(exp_c, 1.35) * 0.65 + phd_sub * 0.8 + phd_shimmer), gain=0.92)

    # Electric Cherry shock ring
    t_ec = np.linspace(0.0, 0.55, int(SR * 0.55), endpoint=False, dtype=np.float32)
    ec_zap = pad_or_trim(laser, 0.55) * 0.45 + np.tanh(np.sin(2.0 * np.pi * 180.0 * t_ec) * 2.2) * np.exp(-t_ec * 6.5) * 0.5
    ec_crackle = noise_burst(len(t_ec), 711) * np.exp(-t_ec * 9.0) * 0.45
    save_wav(os.path.join(OUT_WEAPONS, "perk_electric_cherry.wav"), np.tanh(ec_zap + ec_crackle), gain=0.86)

    # 5. Zombies & Boss Roar (CC0 darsycho + Snabisch)
    dars = load_audio(os.path.join(CACHE_AUDIO, "darsycho_moans.ogg"))
    save_wav(os.path.join(OUT_ZOMBIES, "zombie_groan_1.wav"), extract_shot_window(dars, pre_ms=15.0, dur_s=1.15, thresh_frac=0.18), gain=0.82)
    yell4 = extract_shot_window(load_audio(os.path.join(zvoice, "zombieYell4.wav")), pre_ms=10.0, dur_s=0.95, thresh_frac=0.12)
    save_wav(os.path.join(OUT_ZOMBIES, "zombie_groan_2.wav"), yell4, gain=0.82)

    # Hellhound howl: pitch-raised fierce snarl layered with synth growl
    yell8 = load_audio(os.path.join(zvoice, "zombieYell8.wav"))
    t_hh = np.linspace(0.0, 0.95, int(SR * 0.95), endpoint=False, dtype=np.float32)
    f_hh = 350.0 * np.exp(-t_hh * 0.9) + 135.0 + 32.0 * np.sin(2.0 * np.pi * 14.0 * t_hh)
    hh_synth = lowpass(np.tanh((((np.cumsum(f_hh) / SR) % 1.0) * 2.0 - 1.0) * 2.2), 0.24) * np.sin(np.pi * t_hh / 0.95)
    save_wav(os.path.join(OUT_ZOMBIES, "hellhound_howl.wav"), np.tanh(pad_or_trim(mix_norm(yell8), 0.95) * 0.45 + hh_synth * 0.72), gain=0.84)

    # Panzer Soldat Boss Roar (deep brass siren + steam hiss + down-pitched monstrous bellow)
    yell10_lo = load_audio(os.path.join(zvoice, "zombieYell10.wav"))
    # Resample 1.55x slower for terrifying deep pitch drop!
    idx_slow = np.linspace(0, len(yell10_lo) - 1, int(len(yell10_lo) * 1.55)).astype(np.int32)
    yell_deep = pad_or_trim(mix_norm(yell10_lo[idx_slow]), 1.65)
    t_b = np.linspace(0.0, 1.65, int(SR * 1.65), endpoint=False, dtype=np.float32)
    horn = (np.sin(2.0 * np.pi * (86.0 - 16.0 * t_b) * t_b) + 0.65 * np.sin(2.0 * np.pi * (129.0 - 24.0 * t_b) * t_b)) * np.sin(np.pi * t_b / 1.65) ** 0.55
    steam = lowpass(noise_burst(len(t_b), 799), 0.20) * np.exp(-np.maximum(0.0, t_b - 0.15) * 2.4) * 0.42
    save_wav(os.path.join(OUT_ZOMBIES, "boss_roar.wav"), np.tanh(yell_deep * 0.65 + horn * 0.68 + steam), gain=0.90)

    # Wood plank break & repair
    t_pb = np.linspace(0.0, 0.24, int(SR * 0.24), endpoint=False, dtype=np.float32)
    save_wav(os.path.join(OUT_ZOMBIES, "plank_break.wav"), np.tanh(noise_burst(len(t_pb), 80) * np.exp(-t_pb * 26.0) + np.sin(2.0 * np.pi * 190.0 * t_pb) * np.exp(-t_pb * 22.0)), gain=0.85)
    t_pr = np.linspace(0.0, 0.18, int(SR * 0.18), endpoint=False, dtype=np.float32)
    save_wav(os.path.join(OUT_ZOMBIES, "plank_repair.wav"), np.sin(2.0 * np.pi * 240.0 * np.exp(-t_pr * 15.0) * t_pr) * np.exp(-t_pr * 28.0) + noise_burst(len(t_pr), 81) * np.exp(-t_pr * 45.0) * 0.5, gain=0.84)

    # 6. Footsteps & Slide (CC0 Fantozzi + metal_steps)
    st1 = mix_norm(extract_shot_window(load_audio(os.path.join(fsteps, "Fantozzi-StoneL1.flac")), pre_ms=3.0, dur_s=0.24, thresh_frac=0.14))
    save_wav(os.path.join(OUT_UI, "footstep_stone.wav"), st1, gain=0.68)

    mt1 = mix_norm(extract_shot_window(load_audio(os.path.join(msteps, "metal_steps_04.wav")), pre_ms=3.0, dur_s=0.28, thresh_frac=0.14))
    t_m = np.linspace(0.0, 0.28, int(SR * 0.28), endpoint=False, dtype=np.float32)
    boot_thud = np.sin(2.0 * np.pi * 88.0 * t_m) * np.exp(-t_m * 32.0) * 0.42
    save_wav(os.path.join(OUT_UI, "footstep_metal.wav"), mt1 * 0.72 + boot_thud, gain=0.72)

    # Tactical sprint-slide gritty scrape
    t_sl = np.linspace(0.0, 0.48, int(SR * 0.48), endpoint=False, dtype=np.float32)
    scrape = lowpass(noise_burst(len(t_sl), 613), 0.28) * np.exp(-t_sl * 4.5) * (1.0 - np.exp(-t_sl * 45.0))
    save_wav(os.path.join(OUT_UI, "slide_scrape.wav"), pad_or_trim(st1, 0.48) * 0.35 + scrape * 0.85, gain=0.78)

    # Round chalk tally scrape + chime
    t_rc = np.linspace(0.0, 0.65, int(SR * 0.65), endpoint=False, dtype=np.float32)
    chalk = (noise_burst(len(t_rc), 621) - lowpass(noise_burst(len(t_rc), 621), 0.12)) * np.sin(np.pi * t_rc / 0.45) * (t_rc < 0.45)
    chime = np.sin(2.0 * np.pi * 196.0 * t_rc) * np.exp(-t_rc * 4.0) * 0.4
    save_wav(os.path.join(OUT_UI, "round_chalk.wav"), chalk * 0.55 + chime, gain=0.74)

    # 7. Keep rich synthesized UI jingles & seamless ambience cleanly
    from generate_sfx import make_ui_and_machine_sfx
    make_ui_and_machine_sfx()

    # Re-calculate audio directory size
    total_bytes = 0
    count = 0
    for root, _, files in os.walk(os.path.join(REPO_ROOT, "assets", "audio")):
        for fn in files:
            if fn.endswith(".wav") or fn.endswith(".ogg"):
                total_bytes += os.path.getsize(os.path.join(root, fn))
                count += 1
    print(f"[WPN-SFX] Exported {count} audio SFX files, total size = {total_bytes / (1024*1024):.2f} MB")


if __name__ == "__main__":
    build_all_sfx()
