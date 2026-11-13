#!/usr/bin/env python3
"""Generate synthesized WAV sound effects for Bunker 115 Zombies."""

import os
import wave
import numpy as np

SR = 44100

OUT_WEAPONS = "assets/audio/weapons"
OUT_ZOMBIES = "assets/audio/zombies"
OUT_UI = "assets/audio/ui"
OUT_AMBIENCE = "assets/audio/ambience"

for d in (OUT_WEAPONS, OUT_ZOMBIES, OUT_UI, OUT_AMBIENCE):
    os.makedirs(d, exist_ok=True)


def save_wav(path, samples, gain=0.85):
    peak = np.max(np.abs(samples))
    if peak > 1e-6:
        samples = samples / peak * gain
    pcm = np.clip(samples * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def t_arr(dur):
    return np.linspace(0.0, dur, int(SR * dur), endpoint=False, dtype=np.float32)


def noise_burst(n, seed=1):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, n).astype(np.float32)


def lowpass(sig, cutoff_alpha=0.15):
    out = np.empty_like(sig)
    prev = 0.0
    for i in range(len(sig)):
        prev = prev + cutoff_alpha * (sig[i] - prev)
        out[i] = prev
    return out


def gunshot(dur=0.28, body_freq=140.0, crack_decay=22.0, body_decay=12.0, seed=10, pap=False):
    t = t_arr(dur)
    n = len(t)
    # Sharp transient crack
    crack = noise_burst(n, seed) * np.exp(-t * crack_decay)
    # Low punchy thump
    freq_env = body_freq * np.exp(-t * 18.0) + 42.0
    phase = 2.0 * np.pi * np.cumsum(freq_env) / SR
    thump = np.sin(phase) * np.exp(-t * body_decay)
    # Room tail
    tail = lowpass(noise_burst(n, seed + 1), 0.08) * np.exp(-t * 7.5) * 0.45
    sig = crack * 0.7 + thump * 0.85 + tail
    if pap:
        # Classic CoD Zombies Pack-a-Punch harmonic laser zap overlay!
        zap = np.sin(2.0 * np.pi * (1400.0 * np.exp(-t * 9.0) + 320.0) * t) * np.exp(-t * 14.0)
        sig += zap * 0.55
    return np.tanh(sig * 1.6)


def make_weapons_sfx():
    save_wav(f"{OUT_WEAPONS}/shot_pistol.wav", gunshot(0.24, 175.0, 26.0, 16.0, 1))
    save_wav(f"{OUT_WEAPONS}/shot_pistol_pap.wav", gunshot(0.30, 185.0, 22.0, 13.0, 2, pap=True))
    save_wav(f"{OUT_WEAPONS}/shot_shotgun.wav", gunshot(0.45, 95.0, 14.0, 7.0, 3))
    save_wav(f"{OUT_WEAPONS}/shot_shotgun_pap.wav", gunshot(0.48, 100.0, 14.0, 7.0, 4, pap=True))
    save_wav(f"{OUT_WEAPONS}/shot_smg.wav", gunshot(0.18, 195.0, 32.0, 18.0, 5))
    save_wav(f"{OUT_WEAPONS}/shot_smg_pap.wav", gunshot(0.22, 210.0, 28.0, 15.0, 6, pap=True))
    save_wav(f"{OUT_WEAPONS}/shot_rifle.wav", gunshot(0.28, 145.0, 20.0, 11.0, 7))
    save_wav(f"{OUT_WEAPONS}/shot_rifle_pap.wav", gunshot(0.32, 155.0, 19.0, 10.0, 8, pap=True))
    save_wav(f"{OUT_WEAPONS}/shot_sniper.wav", gunshot(0.55, 110.0, 12.0, 6.0, 9))
    save_wav(f"{OUT_WEAPONS}/shot_sniper_pap.wav", gunshot(0.58, 115.0, 12.0, 6.0, 10, pap=True))

    # Ray Gun signature sci-fi zap!
    t = t_arr(0.36)
    f = 980.0 * np.exp(-t * 10.0) + 190.0
    ray = (np.sin(2.0 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4.0 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 8.5)
    ray += noise_burst(len(t), 33) * np.exp(-t * 25.0) * 0.25
    save_wav(f"{OUT_WEAPONS}/shot_raygun.wav", np.tanh(ray * 1.4))

    # Reload click
    t = t_arr(0.18)
    clk1 = noise_burst(len(t), 40) * np.exp(-t * 55.0)
    clk2 = np.roll(noise_burst(len(t), 41) * np.exp(-t * 60.0), int(0.08 * SR))
    clk2[:int(0.08 * SR)] = 0
    save_wav(f"{OUT_WEAPONS}/reload_click.wav", lowpass(clk1 + clk2, 0.35))

    # Empty click
    t = t_arr(0.07)
    save_wav(f"{OUT_WEAPONS}/empty_click.wav", np.sin(2.0 * np.pi * 1250.0 * t) * np.exp(-t * 80.0))

    # Knife slash
    t = t_arr(0.22)
    swish = lowpass(noise_burst(len(t), 50), 0.22) * np.sin(np.pi * t / 0.22) ** 1.5
    save_wav(f"{OUT_WEAPONS}/knife_slash.wav", swish)

    # Headshot crunch
    t = t_arr(0.16)
    crunch = noise_burst(len(t), 55) * np.exp(-t * 28.0) + np.sin(2.0 * np.pi * 520.0 * t) * np.exp(-t * 35.0) * 0.5
    save_wav(f"{OUT_WEAPONS}/headshot_crunch.wav", np.tanh(crunch * 1.5))

    # Explosion (grenade / nuke / raygun)
    t = t_arr(1.1)
    boom = lowpass(noise_burst(len(t), 60), 0.04) * np.exp(-t * 2.8)
    sub = np.sin(2.0 * np.pi * (80.0 * np.exp(-t * 4.0) + 28.0) * t) * np.exp(-t * 3.5)
    save_wav(f"{OUT_WEAPONS}/explosion.wav", np.tanh((boom * 1.3 + sub * 0.9) * 1.5))


def make_zombie_sfx():
    # Zombie groan 1 & 2
    for idx, base_f in enumerate((115.0, 145.0), start=1):
        t = t_arr(0.9)
        vib = 1.0 + 0.08 * np.sin(2.0 * np.pi * 6.0 * t)
        f = (base_f - 25.0 * t) * vib
        saw = ((np.cumsum(f) / SR) % 1.0) * 2.0 - 1.0
        formant = np.sin(2.0 * np.pi * (base_f * 2.6) * t) * 0.4
        env = np.sin(np.pi * t / 0.9) ** 0.7
        sig = lowpass(saw * 0.6 + formant + noise_burst(len(t), 70 + idx) * 0.2, 0.14) * env
        save_wav(f"{OUT_ZOMBIES}/zombie_groan_{idx}.wav", sig, gain=0.75)

    # Hellhound howl/snarl
    t = t_arr(1.0)
    f = 340.0 * np.exp(-t * 0.8) + 120.0 + 30.0 * np.sin(2.0 * np.pi * 12.0 * t)
    growl = np.tanh((((np.cumsum(f) / SR) % 1.0) * 2.0 - 1.0) * 2.0) * np.sin(np.pi * t / 1.0)
    save_wav(f"{OUT_ZOMBIES}/hellhound_howl.wav", lowpass(growl, 0.22), gain=0.8)

    # Wood plank break & repair hammer
    t = t_arr(0.24)
    snap = noise_burst(len(t), 80) * np.exp(-t * 26.0) + np.sin(2.0 * np.pi * 190.0 * t) * np.exp(-t * 22.0)
    save_wav(f"{OUT_ZOMBIES}/plank_break.wav", snap)

    t = t_arr(0.18)
    ham = np.sin(2.0 * np.pi * 240.0 * np.exp(-t * 15.0) * t) * np.exp(-t * 28.0) + noise_burst(len(t), 81) * np.exp(-t * 45.0) * 0.5
    save_wav(f"{OUT_ZOMBIES}/plank_repair.wav", ham)


def make_ui_and_machine_sfx():
    # Round Start eerie brass/bell chord
    t = t_arr(2.6)
    freqs = (110.0, 130.81, 164.81, 220.0) # A2, C3, E3, A3 eerie minor chord
    chord = sum(np.sin(2.0 * np.pi * f * t) * np.exp(-t * (0.9 + 0.15 * i)) for i, f in enumerate(freqs))
    bell = np.sin(2.0 * np.pi * 440.0 * t) * np.exp(-t * 2.2) * 0.35
    save_wav(f"{OUT_UI}/round_start.wav", np.tanh((chord * 0.3 + bell) * 1.2), gain=0.85)

    # Round End hopeful-dark chime
    t = t_arr(2.0)
    notes = [(220.0, 0.0), (261.63, 0.28), (329.63, 0.56), (440.0, 0.85)]
    sig = np.zeros_like(t)
    for freq, start in notes:
        mask = t >= start
        dt = np.maximum(0.0, t - start)
        sig[mask] += np.sin(2.0 * np.pi * freq * dt[mask]) * np.exp(-dt[mask] * 2.5)
    save_wav(f"{OUT_UI}/round_end.wav", sig * 0.45, gain=0.8)

    # Buy / Cash register cha-ching
    t = t_arr(0.35)
    c1 = np.sin(2.0 * np.pi * 1046.5 * t) * np.exp(-t * 16.0)
    c2 = np.sin(2.0 * np.pi * 1567.98 * np.maximum(0.0, t - 0.07)) * np.exp(-np.maximum(0.0, t - 0.07) * 12.0) * (t >= 0.07)
    save_wav(f"{OUT_UI}/buy_confirm.wav", c1 + c2, gain=0.8)

    # Error / Denied buzz
    t = t_arr(0.25)
    err = np.sign(np.sin(2.0 * np.pi * 110.0 * t)) * np.exp(-t * 8.0)
    save_wav(f"{OUT_UI}/buy_denied.wav", lowpass(err, 0.18), gain=0.65)

    # Mystery Box jingle
    t = t_arr(2.8)
    melody = [(523.25, 0.0), (659.25, 0.22), (783.99, 0.44), (659.25, 0.66), (880.0, 0.90), (783.99, 1.20), (1046.5, 1.50)]
    box = np.zeros_like(t)
    for freq, st in melody:
        m = t >= st
        dt = np.maximum(0.0, t - st)
        box[m] += (np.sin(2.0 * np.pi * freq * dt[m]) + 0.3 * np.sin(4.0 * np.pi * freq * dt[m])) * np.exp(-dt[m] * 3.8)
    save_wav(f"{OUT_UI}/mystery_box_jingle.wav", box * 0.5, gain=0.8)

    # Power Switch activation + generator spool up
    t = t_arr(2.2)
    clunk = noise_burst(len(t), 91) * np.exp(-t * 35.0)
    spool_f = 45.0 + 180.0 * (t / 2.2) ** 1.3
    spool = np.sin(2.0 * np.pi * np.cumsum(spool_f) / SR) * np.minimum(1.0, t * 2.0) * np.exp(-np.maximum(0.0, t - 1.5) * 2.5)
    save_wav(f"{OUT_UI}/power_on.wav", np.tanh((clunk + spool * 0.7) * 1.3), gain=0.85)

    # Powerup pickup chime
    t = t_arr(0.75)
    pu = (np.sin(2.0 * np.pi * 587.33 * t) + np.sin(2.0 * np.pi * 880.0 * t) * 0.7) * np.exp(-t * 4.5)
    save_wav(f"{OUT_UI}/powerup_collect.wav", pu, gain=0.8)

    # Perk drink jingle
    t = t_arr(1.2)
    pnotes = [(392.0, 0.0), (493.88, 0.16), (587.33, 0.32), (783.99, 0.52)]
    pj = np.zeros_like(t)
    for freq, st in pnotes:
        m = t >= st
        dt = np.maximum(0.0, t - st)
        pj[m] += np.sin(2.0 * np.pi * freq * dt[m]) * np.exp(-dt[m] * 3.2)
    save_wav(f"{OUT_UI}/perk_drink.wav", pj * 0.5, gain=0.8)

    # Hitmarker tick
    t = t_arr(0.05)
    hm = np.sin(2.0 * np.pi * 2200.0 * t) * np.exp(-t * 90.0)
    save_wav(f"{OUT_UI}/hitmarker.wav", hm, gain=0.6)

    # Player hurt thud
    t = t_arr(0.28)
    hurt = np.sin(2.0 * np.pi * (110.0 * np.exp(-t * 10.0) + 40.0) * t) * np.exp(-t * 11.0) + noise_burst(len(t), 95) * np.exp(-t * 18.0) * 0.4
    save_wav(f"{OUT_UI}/player_hurt.wav", np.tanh(hurt * 1.4), gain=0.85)

    # Ambient eerie wind & electrical hum loop (4s seamless)
    t = t_arr(4.0)
    rng = np.random.default_rng(100)
    white = rng.uniform(-1.0, 1.0, len(t)).astype(np.float32)
    # Seamless circular smoothing
    wind = np.fft.irfft(np.fft.rfft(white) * np.exp(-np.linspace(0, 12, len(t) // 2 + 1)))
    hum = 0.15 * np.sin(2.0 * np.pi * 55.0 * t) + 0.08 * np.sin(2.0 * np.pi * 110.0 * t)
    save_wav(f"{OUT_AMBIENCE}/bunker_ambience.wav", wind / (np.max(np.abs(wind)) + 1e-6) * 0.55 + hum, gain=0.5)


if __name__ == "__main__":
    make_weapons_sfx()
    make_zombie_sfx()
    make_ui_and_machine_sfx()
    print("All synthesized WAV audio files generated!")
