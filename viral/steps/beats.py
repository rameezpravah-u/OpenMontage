"""Find the moments that matter inside a raw TypeBetter screen recording.

The whole system hangs off this file. A raw recording is mostly dead time:
someone thinking, a cursor blinking, a spinner spinning. The interesting
frames are the ones where the screen *changes a lot* — a panel opening, a
result landing, text being replaced.

We measure per-frame change cheaply (mean absolute difference of a downscaled
greyscale frame against the previous one) and read the resulting signal:

    low, flat          -> dead air            (cut it, or speed it up)
    low, periodic      -> caret blink / spinner (speed it up hard)
    sustained medium   -> typing               (speed up ~2x)
    single large spike -> a state change       (KEEP at 1x, put a zoom here)

No ML, no API, no per-video tuning. It runs in a couple of seconds on a
30-second clip and it is deterministic, which matters when you are rendering
100 videos a month and cannot eyeball each one.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

# Downscale hard before diffing: we want structural change, not pixel noise.
PROBE_W, PROBE_H = 96, 171  # keeps 9:16


@dataclass
class Beat:
    """One detected state change."""

    t: float  # seconds into the source
    strength: float  # 0..1, how big the change was
    kind: str  # "change" | "settle"


@dataclass
class Segment:
    """A stretch of the source with a playback speed attached."""

    start: float
    end: float
    speed: float
    reason: str

    @property
    def out_duration(self) -> float:
        return (self.end - self.start) / self.speed


def _luma_series(video: Path, fps: int = 15) -> tuple[np.ndarray, float]:
    """Decode a tiny greyscale version of the video into memory."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(video),
        "-vf", f"fps={fps},scale={PROBE_W}:{PROBE_H},format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    frame_size = PROBE_W * PROBE_H
    n = len(raw) // frame_size
    arr = np.frombuffer(raw[: n * frame_size], dtype=np.uint8)
    return arr.reshape(n, PROBE_H, PROBE_W).astype(np.float32), float(fps)


def change_signal(video: Path, fps: int = 15) -> tuple[np.ndarray, float]:
    """Per-frame change, normalised 0..1."""
    frames, fps_f = _luma_series(video, fps)
    if len(frames) < 2:
        return np.zeros(1), fps_f
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    peak = float(diff.max()) or 1.0
    return diff / peak, fps_f


def find_beats(
    video: Path,
    fps: int = 15,
    spike_threshold: float = 0.22,
    min_gap_s: float = 0.45,
) -> list[Beat]:
    """Return the state-change moments, strongest first in time order.

    `min_gap_s` stops a single transition (which spans several frames) from
    registering as four separate beats.
    """
    sig, fps_f = change_signal(video, fps)
    beats: list[Beat] = []
    last_t = -999.0
    for i, v in enumerate(sig):
        if v < spike_threshold:
            continue
        t = (i + 1) / fps_f
        if t - last_t < min_gap_s:
            # same transition still unfolding — keep the strongest frame
            if beats and v > beats[-1].strength:
                beats[-1] = Beat(t=t, strength=float(v), kind="change")
            continue
        beats.append(Beat(t=t, strength=float(v), kind="change"))
        last_t = t
    return beats


def plan_segments(
    video: Path,
    fps: int = 15,
    dead_threshold: float = 0.012,
    typing_threshold: float = 0.10,
    dead_speed: float = 6.0,
    typing_speed: float = 2.0,
    hold_after_beat_s: float = 1.1,
    min_segment_s: float = 0.2,
) -> list[Segment]:
    """Turn the change signal into a speed-ramp plan.

    Every decision moment plays at 1x. Everything else is compressed. This is
    what removes the manual editing: you never trim by hand, you declare the
    policy once and it applies to every recording you ever drop in.
    """
    sig, fps_f = change_signal(video, fps)
    beats = find_beats(video, fps)
    beat_times = [b.t for b in beats]

    duration = len(sig) / fps_f
    labels: list[str] = []
    for i, v in enumerate(sig):
        t = (i + 1) / fps_f
        # protect a window after each state change so the payoff is readable
        if any(0 <= t - bt <= hold_after_beat_s for bt in beat_times):
            labels.append("hold")
        elif v >= typing_threshold:
            labels.append("hold")       # big motion: leave it alone
        elif v >= dead_threshold:
            labels.append("typing")
        else:
            labels.append("dead")

    speeds = {"hold": 1.0, "typing": typing_speed, "dead": dead_speed}
    reasons = {
        "hold": "decision moment - plays at 1x",
        "typing": "typing / low motion - compressed",
        "dead": "no change on screen - compressed hard",
    }

    segments: list[Segment] = []
    run_label = labels[0]
    run_start = 0.0
    for i in range(1, len(labels)):
        if labels[i] != run_label:
            end = (i + 1) / fps_f
            if end - run_start >= min_segment_s:
                segments.append(
                    Segment(run_start, end, speeds[run_label], reasons[run_label])
                )
                run_start = end
            run_label = labels[i]
    segments.append(Segment(run_start, duration, speeds[run_label], reasons[run_label]))

    # merge neighbours that ended up with the same speed
    merged: list[Segment] = []
    for s in segments:
        if merged and abs(merged[-1].speed - s.speed) < 1e-6:
            merged[-1] = Segment(merged[-1].start, s.end, s.speed, merged[-1].reason)
        else:
            merged.append(s)
    return merged


def analyse(video: Path) -> dict:
    """Everything the rest of the pipeline needs to know about a recording."""
    segs = plan_segments(video)
    beats = find_beats(video)
    src_dur = sum(s.end - s.start for s in segs)
    out_dur = sum(s.out_duration for s in segs)

    # map each source beat onto its position in the sped-up output
    def to_output_time(t: float) -> float:
        acc = 0.0
        for s in segs:
            if t <= s.start:
                break
            acc += (min(t, s.end) - s.start) / s.speed
        return round(acc, 3)

    return {
        "source": str(video),
        "source_duration": round(src_dur, 2),
        "output_duration": round(out_dur, 2),
        "compression": round(src_dur / out_dur, 2) if out_dur else 1.0,
        "beats": [
            {**asdict(b), "t_out": to_output_time(b.t)} for b in beats
        ],
        "segments": [asdict(s) | {"out_duration": round(s.out_duration, 3)} for s in segs],
    }


def build_filter(segs: list[Segment]) -> str:
    """ffmpeg filter_complex that applies the speed plan in one pass."""
    parts, labels = [], []
    for i, s in enumerate(segs):
        parts.append(
            f"[0:v]trim=start={s.start:.3f}:end={s.end:.3f},"
            f"setpts=(PTS-STARTPTS)/{s.speed}[v{i}]"
        )
        labels.append(f"[v{i}]")
    parts.append("".join(labels) + f"concat=n={len(segs)}:v=1:a=0[outv]")
    return ";".join(parts)


if __name__ == "__main__":
    import sys

    print(json.dumps(analyse(Path(sys.argv[1])), indent=2))
