#!/usr/bin/env python3
"""Generate synthesized Stream D Easter Egg tribute rock/synth track:
assets/audio/ui/ee_song_115.wav (~30s, 158 BPM D minor).
"""

import os
import wave
import numpy as np

SR = 44100
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_PATH = os.path.join(REPO_ROOT, "assets", "audio", "ui", "ee_song_115.wav")


def save_wav(path: str, samples: np.ndarray, gain: float = 0.85) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    peak = float(np.max(np.abs(samples)))
    if peak > 1e-6:
        samples = samples / peak * gain
    pcm = np.clip(samples * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def midi_to_hz(m: float) -> float:
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))


def make_115_song() -> np.ndarray:
    bpm = 158.0
    beat_dur = 60.0 / bpm
    step_dur = beat_dur * 0.5  # 8th note grid
    total_bars = 19  # ~28.8s
    total_steps = total_bars * 8
    dur = total_steps * step_dur
    n_samples = int(round(dur * SR))
    mix = np.zeros(n_samples, dtype=np.float32)

    rng = np.random.default_rng(115)

    # Bar harmonic progression in D minor: Dm -> F -> Bb -> A -> Dm -> Gm -> C -> A7 (repeats + climax)
    chord_roots = [
        38, 38, 41, 41, 46, 46, 45, 44,
        38, 38, 43, 43, 48, 48, 45, 45,
        38, 46, 45,
    ]

    def add_slice(start_idx: int, sig: np.ndarray) -> None:
        end_idx = min(n_samples, start_idx + len(sig))
        if end_idx > start_idx:
            mix[start_idx:end_idx] += sig[: end_idx - start_idx]

    # 1. Driving Palm-Muted Industrial Guitar Power Chords + Sub Bass
    for step in range(total_steps):
        bar = step // 8
        beat_step = step % 8
        root = chord_roots[bar]
        t0 = step * step_dur
        idx0 = int(round(t0 * SR))

        # Accent pattern: 1, 2, 3&, 4, 4&
        is_accent = beat_step in (0, 2, 5, 6, 7)
        note_dur = step_dur * (1.25 if is_accent else 0.72)
        t = np.linspace(0.0, note_dur, int(round(note_dur * SR)), endpoint=False, dtype=np.float32)
        env = np.minimum(t / 0.008, 1.0) * np.exp(-t * (7.5 if is_accent else 14.0))

        # Saw-like distorted power chord (root + 5th + octave)
        chord_sig = np.zeros_like(t)
        for semitone, wt in ((0, 1.0), (7, 0.75), (12, 0.60)):
            f = midi_to_hz(root + semitone)
            w = np.sin(2.0 * np.pi * f * t) + 0.55 * np.sin(4.0 * np.pi * f * t) + 0.30 * np.sin(6.0 * np.pi * f * t)
            chord_sig += w * wt
        chord_sig = np.tanh(chord_sig * (2.6 if bar >= 4 else 1.7)) * env * (0.34 if bar >= 4 else 0.22)
        add_slice(idx0, chord_sig)

        # Driving sub-bass on downbeats & 8ths
        f_bass = midi_to_hz(root - 12)
        bass = np.sin(2.0 * np.pi * f_bass * t) * env * 0.24
        add_slice(idx0, bass)

    # 2. Kick, Snare & Industrial Hi-Hat Groove (kicks in hard on bar 2)
    for step in range(8, total_steps):
        bar = step // 8
        sub = step % 8
        t0 = step * step_dur
        idx0 = int(round(t0 * SR))

        # Kick on 1, 1&, 3, 4&
        if sub in (0, 1, 4, 7):
            tk = np.linspace(0.0, 0.16, int(0.16 * SR), endpoint=False, dtype=np.float32)
            fk = 128.0 * np.exp(-tk * 34.0) + 46.0
            ph = 2.0 * np.pi * np.cumsum(fk) / SR
            kick = np.tanh(np.sin(ph) * 1.9) * np.exp(-tk * 16.0) * 0.48
            add_slice(idx0, kick)

        # Heavy Snare on 2 & 4 (steps 2, 6)
        if sub in (2, 6):
            ts = np.linspace(0.0, 0.19, int(0.19 * SR), endpoint=False, dtype=np.float32)
            noise = rng.uniform(-1.0, 1.0, len(ts)).astype(np.float32)
            tone = np.sin(2.0 * np.pi * (195.0 * np.exp(-ts * 18.0) + 120.0) * ts)
            snare = np.tanh((noise * 0.72 + tone * 0.55) * 1.6) * np.exp(-ts * 18.0) * 0.40
            add_slice(idx0, snare)

        # Crisp 8th-note hi-hat
        th = np.linspace(0.0, 0.055, int(0.055 * SR), endpoint=False, dtype=np.float32)
        hat_n = rng.uniform(-1.0, 1.0, len(th)).astype(np.float32)
        hat = (hat_n - np.roll(hat_n, 1)) * 0.5 * np.exp(-th * 55.0) * (0.20 if bar >= 4 else 0.12)
        add_slice(idx0, hat)

    # 3. Haunting Element-115 Minor Lead Riff (bars 4..18)
    melody_notes = [
        # (step_offset, midi_note, dur_steps)
        (0, 74, 1.5), (1.5, 77, 1.5), (3, 81, 2.0), (5, 79, 1.5), (6.5, 77, 1.5),
        (8, 76, 2.0), (10, 74, 1.5), (11.5, 72, 1.5), (13, 74, 3.0),
        (16, 74, 1.5), (17.5, 77, 1.5), (19, 82, 2.0), (21, 81, 1.5), (22.5, 79, 1.5),
        (24, 77, 2.0), (26, 76, 2.0), (28, 73, 2.0), (30, 76, 2.0),
    ]
    for phrase_bar in (4, 8, 12, 16):
        phrase_step0 = phrase_bar * 8
        for s_off, m_note, d_steps in melody_notes:
            abs_step = phrase_step0 + s_off
            if abs_step >= total_steps - 2:
                continue
            nd = d_steps * step_dur
            tl = np.linspace(0.0, nd, int(round(nd * SR)), endpoint=False, dtype=np.float32)
            idx0 = int(round(abs_step * step_dur * SR))
            f0 = midi_to_hz(m_note)
            vib = 1.0 + 0.004 * np.sin(2.0 * np.pi * 5.8 * tl)
            ph = 2.0 * np.pi * np.cumsum(f0 * vib) / SR
            lead = (np.sin(ph) * 0.70 + np.sin(ph * 2.0) * 0.35 + np.sin(ph * 3.0) * 0.18)
            lead = np.tanh(lead * 1.65)
            l_env = np.minimum(tl / 0.015, 1.0) * np.minimum((nd - tl) / 0.035, 1.0)
            add_slice(idx0, lead * l_env * 0.25)

    # 4. Eerie High E-115 Choir/Pad Swell over full track
    t_all = np.linspace(0.0, dur, n_samples, endpoint=False, dtype=np.float32)
    pad = (
        0.5 * np.sin(2.0 * np.pi * midi_to_hz(62) * t_all)
        + 0.4 * np.sin(2.0 * np.pi * midi_to_hz(69) * t_all)
        + 0.3 * np.sin(2.0 * np.pi * midi_to_hz(77) * t_all)
    ) * (0.065 + 0.025 * np.sin(2.0 * np.pi * 0.35 * t_all))
    mix += pad

    # Smooth fade in (0.4s) & fade out (1.8s)
    fade_in = min(n_samples, int(0.4 * SR))
    fade_out = min(n_samples, int(1.8 * SR))
    mix[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    mix[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)
    return np.tanh(mix * 1.15)


if __name__ == "__main__":
    song = make_115_song()
    save_wav(OUT_PATH, song, gain=0.84)
    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"[Audio] Saved {OUT_PATH} ({size_kb} KB, {len(song)/SR:.2f}s)")
