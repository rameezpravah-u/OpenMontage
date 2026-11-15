"""Sound design: music bed + beat-locked effects, synthesised locally.

Why synthesise instead of licensing a library:

* It is free and offline, so it scales to 100 videos a month with no per-clip
  licensing question and no API that can 403 on you (Pixabay did, repeatedly).
* The SFX have to land on *detected* beats, which differ per recording. A
  stock whoosh is a fixed file; a synthesised one is generated at the exact
  length the transition needs.
* No copyright claim risk on Reels/TikTok.

The tradeoff is honest: this is clean sound design, not a produced track. For
a hero piece, drop a real track into `music_library/` and the pipeline uses it
instead — see `bed()`.
"""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000


def _env(n: int, attack: float, curve: float = 3.0) -> np.ndarray:
    e = np.ones(n)
    a = max(1, int(attack * SR))
    e[:a] = np.linspace(0, 1, a)
    tail = np.linspace(0, 1, max(1, n - a))
    e[a:] = (1 - tail) ** curve
    return e


def keystroke(seed: int = 0, amp: float = 0.5) -> np.ndarray:
    """Short dry click. Used under typing runs."""
    rng = np.random.default_rng(seed)
    n = int(0.035 * SR)
    noise = np.diff(np.concatenate([[0], rng.standard_normal(n)]))
    body = 0.35 * np.sin(2 * np.pi * 180 * np.arange(n) / SR)
    return amp * (noise * 0.8 + body) * _env(n, 0.0004, 6.0)


def whoosh(dur: float = 0.34, amp: float = 0.42, seed: int = 1) -> np.ndarray:
    """Rising filtered noise for a cut or a zoom push."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # sweep a one-pole high-pass by mixing progressively more differentiated noise
    sweep = np.linspace(0.05, 0.95, n)
    hp = np.diff(np.concatenate([[0], noise]))
    sig = noise * (1 - sweep) + hp * sweep
    return amp * sig * np.sin(np.pi * t / dur) ** 1.4


def ding(freq: float = 880.0, dur: float = 0.55, amp: float = 0.4) -> np.ndarray:
    """Clean two-partial bell for the moment the correction lands."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t)
           + 0.25 * np.sin(2 * np.pi * freq * 3.0 * t))
    return amp * sig * _env(n, 0.002, 2.4)


def thump(dur: float = 0.3, amp: float = 0.6) -> np.ndarray:
    """Low hit for the hook card."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 24)
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 3.0)


def music_bed(duration: float, bpm: float = 120.0, style: str = "punchy") -> np.ndarray:
    """A minimal instrumental bed locked to `bpm`."""
    beat = 60.0 / bpm
    n = int(duration * SR)
    mix = np.zeros(n)

    def place(start_s: float, sig: np.ndarray) -> None:
        i = int(start_s * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        mix[i:j] += sig[: j - i]

    def sub(freq: float, length: float, amp: float) -> np.ndarray:
        m = int(length * SR)
        return amp * np.sin(2 * np.pi * freq * np.arange(m) / SR) * _env(m, 0.02, 1.2)

    scale = [329.63, 392.00, 493.88, 587.33, 659.25]
    quiet = style == "calm"
    for b in range(int(duration / beat) + 1):
        ts = b * beat
        if ts >= duration:
            break
        if quiet:
            if b % 2 == 0:
                place(ts, thump(0.22, 0.26))
            place(ts + beat / 2, keystroke(seed=b, amp=0.12))
            if b % 8 == 0:
                place(ts, sub(82.41, beat * 7.5, 0.15))
        else:
            place(ts, thump(0.26, 0.62))
            place(ts + beat / 2, keystroke(seed=b, amp=0.22))
            if b % 4 == 0:
                place(ts, sub(82.41, beat * 3.6, 0.24))
            if b % 2 == 1:
                m = int(0.13 * SR)
                place(ts, 0.16 * np.sin(2 * np.pi * scale[b % 5] * np.arange(m) / SR) * _env(m, 0.002, 4.0))

    fi, fo = int(0.05 * SR), int(min(0.6, duration * 0.2) * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    if fo:
        mix[-fo:] *= np.linspace(1, 0, fo)
    return np.tanh(mix * 0.9)


def design(
    out: Path,
    duration: float,
    beats_out: list[float],
    typing_runs: list[tuple[float, float]] | None = None,
    hook_hit: float = 0.12,
    bpm: float = 120.0,
    style: str = "punchy",
    music_gain: float = 0.5,
) -> Path:
    """Render the full sound bed: music + a ding on every detected beat."""
    n = int(duration * SR)
    track = music_bed(duration, bpm, style) * music_gain

    def place(start_s: float, sig: np.ndarray) -> None:
        i = int(start_s * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        track[i:j] += sig[: j - i]

    place(hook_hit, thump(0.34, 0.8))
    for i, t in enumerate(beats_out):
        place(max(0.0, t - 0.16), whoosh(0.3, 0.3, seed=i + 7))
        place(t, ding(880 if i % 2 == 0 else 1046.5, 0.5, 0.34))

    for (a, b) in (typing_runs or []):
        k = a
        while k < b:
            place(k, keystroke(seed=int(k * 97) % 9999, amp=0.17))
            k += 0.085

    track = track / (np.max(np.abs(track)) + 1e-9) * 0.85
    pcm = (np.stack([track, track], axis=1) * 32767).astype(np.int16)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".wav")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if out.suffix == ".mp3":
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp), "-b:a", "192k", "-y", str(out)],
                       check=True, capture_output=True)
        tmp.unlink(missing_ok=True)
    return out


def mix_with_voice(voice: Path, bed: Path, out: Path, duration: float, bed_gain: float = 0.33) -> Path:
    """Duck the bed under the narration so the voice always wins."""
    graph = (
        "[0:a]asplit=2[vo_key][vo_mix];"
        f"[1:a]volume={bed_gain}[bed];"
        "[bed][vo_key]sidechaincompress=threshold=0.05:ratio=8:attack=10:release=300[duck];"
        f"[duck][vo_mix]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,apad,atrim=0:{duration}[out]"
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(voice), "-i", str(bed),
         "-filter_complex", graph, "-map", "[out]",
         "-ar", "48000", "-ac", "2", "-b:a", "192k", "-y", str(out)],
        check=True, capture_output=True,
    )
    return out


def bed(duration: float, out: Path, library: Path = Path("music_library")) -> tuple[Path, str]:
    """Prefer a real track the user dropped in; fall back to the synth."""
    if library.is_dir():
        for f in sorted(library.glob("*.mp3")) + sorted(library.glob("*.wav")):
            subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(f), "-t", str(duration),
                 "-af", f"afade=t=out:st={max(0, duration - 1.2):.2f}:d=1.2",
                 "-b:a", "192k", "-y", str(out)],
                check=True, capture_output=True,
            )
            return out, f"library:{f.name}"
    design(out, duration, beats_out=[])
    return out, "synth"
