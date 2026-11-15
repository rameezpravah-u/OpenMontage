#!/usr/bin/env python3
"""TypeBetter viral video pipeline.

    python viral/pipeline.py --recording raw/type-fix.mov --concept mistake-reveal

Takes a raw screen recording and a concept file, produces a finished vertical
video. No manual editing in between.

    recording ─┬─> beats.analyse ──> speed plan + beat times
               └─> ffmpeg ─────────> normalised, ramped footage
    concept ───┬─> Piper TTS ──────> narration per line
               └─> Whisper ────────> word-level captions
    beats ─────────> sound.design ─> music + ding/whoosh on each beat
    all ───────────> props.json ───> Remotion ──> final.mp4

Everything that varies per video lives in the concept JSON. Everything that is
a craft decision (speed policy, zoom shape, caption rhythm, mix levels) lives
in code and applies to every video identically.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from viral.steps import beats as beats_mod  # noqa: E402
from viral.steps import sound as sound_mod  # noqa: E402
from viral.steps import voice as voice_mod  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "projects" / "viral-engine"
FPS = 30
W, H = 1080, 1920


def sh(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def normalise(src: Path, out: Path, segs: list[beats_mod.Segment], crop: str | None) -> float:
    """Apply the speed plan and conform to 1080x1920 in a single ffmpeg pass."""
    vf_tail = crop or "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'"
    graph = beats_mod.build_filter(segs)
    graph += f";[outv]{vf_tail},scale={W}:{H},fps={FPS}[final]"
    out.parent.mkdir(parents=True, exist_ok=True)
    sh(["ffmpeg", "-v", "error", "-i", str(src), "-filter_complex", graph,
        "-map", "[final]", "-an", "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-y", str(out)])
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True, check=True)
    return float(probe.stdout.strip())


def distribute_vo(lines: list[dict], beat_times: list[float], total: float) -> list[float]:
    """Pin narration lines to detected beats where possible.

    Line 0 always starts at 0.25s (the hook needs voice immediately). The rest
    aim to land just *before* a beat, so the sentence finishes as the on-screen
    payoff arrives rather than trailing after it.
    """
    offsets = [0.25]
    usable = [t for t in beat_times if t > 1.0]
    cursor = 0.25 + lines[0]["duration"] + 0.18
    for ln in lines[1:]:
        target = next((t - ln["duration"] * 0.72 for t in usable if t - ln["duration"] * 0.72 >= cursor), None)
        start = target if target is not None else cursor
        start = min(start, max(0.0, total - ln["duration"] - 0.1))
        offsets.append(round(start, 3))
        cursor = start + ln["duration"] + 0.18
    return offsets


def run(recording: Path, concept_path: Path, out_dir: Path, scale: float, keep_draft: bool) -> Path:
    concept = json.loads(concept_path.read_text())
    slug = concept.get("slug", concept_path.stem)
    work = out_dir / slug
    work.mkdir(parents=True, exist_ok=True)
    pub = ENGINE / "public"
    pub.mkdir(parents=True, exist_ok=True)

    print(f"\n  concept   {concept['name']}")
    print(f"  recording {recording.name}")

    # 1 ── read the recording -------------------------------------------------
    analysis = beats_mod.analyse(recording)
    segs = beats_mod.plan_segments(recording)
    print(f"\n  [1/6] analysed: {analysis['source_duration']}s -> "
          f"{analysis['output_duration']}s ({analysis['compression']}x), "
          f"{len(analysis['beats'])} beats")

    # 2 ── conform ------------------------------------------------------------
    footage = pub / f"{slug}_footage.mp4"
    body = normalise(recording, footage, segs, concept.get("crop"))
    print(f"  [2/6] footage conformed: {body:.2f}s @ {W}x{H}/{FPS}fps")

    beat_times = [b["t_out"] for b in analysis["beats"] if b["t_out"] < body - 0.3]

    # 3 ── narration ----------------------------------------------------------
    lines = concept["script"]
    vo_segs = voice_mod.narrate(lines, work / "vo")
    offsets = distribute_vo(vo_segs, beat_times, body)
    vo = voice_mod.assemble_vo(vo_segs, offsets, body, work / "narration.wav")
    print(f"  [3/6] narration: {len(lines)} lines placed at "
          f"{', '.join(f'{o:.1f}s' for o in offsets)}")

    # 4 ── captions -----------------------------------------------------------
    captions = voice_mod.captions_for(vo_segs, offsets, work)
    print(f"  [4/6] captions: {len(captions)} words with timings")

    # 5 ── sound --------------------------------------------------------------
    typing_runs = [(s["start"], s["end"]) for s in analysis["segments"]
                   if s["speed"] > 1.5 and s["out_duration"] > 0.25][:6]
    bed = sound_mod.design(work / "bed.wav", body, beat_times,
                           typing_runs=None, bpm=concept.get("bpm", 120),
                           style=concept.get("music_style", "punchy"),
                           music_gain=0.45)
    track = pub / f"{slug}_audio.mp3"
    sound_mod.mix_with_voice(vo, bed, track, body)
    print(f"  [5/6] sound: bed + {len(beat_times)} beat hits, ducked under VO")

    # 6 ── render -------------------------------------------------------------
    cta_frames = int(concept.get("cta_seconds", 4.0) * FPS)
    props = {
        "video": footage.name,
        "videoDurationInFrames": int(math.floor(body * FPS)),
        "hook": {"text": concept["hook"], "sub": concept.get("hook_sub"),
                 "durationInFrames": int(concept.get("hook_seconds", 2.2) * FPS)},
        "captions": captions,
        "zooms": [{"t": t, "scale": concept.get("zoom", 1.12)} for t in beat_times],
        "audio": track.name,
        "cta": {"durationInFrames": cta_frames,
                "wordmark": concept.get("wordmark", "Type Better"),
                "line": concept.get("cta_line", "Start free — 2,000 AI words."),
                "store": concept.get("store_line", "on the App Store"),
                "icon": "app_icon_1024.png"},
        "fps": FPS,
    }
    (ENGINE / "artifacts").mkdir(parents=True, exist_ok=True)
    (ENGINE / "artifacts" / "props.json").write_text(json.dumps(props, indent=1))

    out = out_dir / f"{slug}.mp4"
    staged = ROOT / "remotion-composer" / "projects" / "viral-engine"
    if staged.exists():
        subprocess.run(["rm", "-rf", str(staged)], check=True)

    from tools.video.video_compose import VideoCompose
    res = VideoCompose().execute({
        "operation": "render",
        "output_path": str(out),
        "edit_decisions": {
            "render_runtime": "remotion",
            "composition_mode": "atelier",
            "bespoke": {
                "entry": str(ENGINE / "index.tsx"),
                "composition_id": "ViralEngine",
                "props_path": str(ENGINE / "artifacts" / "props.json"),
                "public_dir": str(pub),
                "art_direction": str(ENGINE / "art-direction.md"),
                "scale": scale, "crf": 18, "concurrency": 4,
            },
        },
    })
    if not res.success:
        raise SystemExit(f"render failed: {res.error}")
    total = (props["videoDurationInFrames"] + cta_frames) / FPS
    print(f"  [6/6] rendered: {out}  ({total:.1f}s)\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Raw screen recording -> publishable vertical video.")
    ap.add_argument("--recording", required=True, type=Path)
    ap.add_argument("--concept", required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "out")
    ap.add_argument("--scale", type=float, default=1.0, help="0.5 for a fast draft")
    ap.add_argument("--keep-draft", action="store_true")
    a = ap.parse_args()

    cp = Path(a.concept)
    if not cp.exists():
        cp = ROOT / "viral" / "concepts" / f"{a.concept}.json"
    if not cp.exists():
        raise SystemExit(f"concept not found: {a.concept}")

    run(a.recording, cp, a.out, a.scale, a.keep_draft)


if __name__ == "__main__":
    main()
