"""Narration + word-level caption timings.

The key architectural point, and the thing most "auto-caption" tutorials get
wrong for this use case: **the screen recordings are silent.** There is no
speech in them to transcribe. So captions cannot come from the recording.

Instead:

    script line -> Piper TTS -> narration.wav -> Whisper -> word timestamps

We transcribe our *own generated narration*. That gives word-level timings
that are exact against the audio we are actually going to play, which is what
`@remotion/captions` needs to drive karaoke-style captions.

TTS provider is pluggable. Piper runs locally and free, which is what makes
100 videos/month viable; swap in ElevenLabs for hero pieces by setting
TB_TTS=elevenlabs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import wave
from pathlib import Path

PIPER_MODEL = Path.home() / ".piper" / "models" / "en_US-ryan-high.onnx"


def _wav_duration(p: Path) -> float:
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / w.getframerate()


def speak_piper(text: str, out: Path, model: Path = PIPER_MODEL) -> float:
    """Local, free, offline TTS. Returns duration in seconds."""
    if not model.exists():
        raise FileNotFoundError(
            f"Piper voice model missing: {model}\n"
            "  pip install piper-tts\n"
            "  curl -sL -o ~/.piper/models/en_US-ryan-high.onnx "
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx\n"
            "  (and the matching .onnx.json)"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["python", "-m", "piper", "--model", str(model), "--output-file", str(out)],
        input=text.encode(), check=True, capture_output=True,
    )
    return _wav_duration(out)


def speak(text: str, out: Path) -> float:
    """Dispatch on TB_TTS. Piper by default."""
    provider = os.environ.get("TB_TTS", "piper").lower()
    if provider == "piper":
        return speak_piper(text, out)
    raise ValueError(
        f"TTS provider {provider!r} not wired in this build. "
        "Piper is the local default; add an ElevenLabs branch here when a key is configured."
    )


def narrate(lines: list[str], workdir: Path) -> list[dict]:
    """One wav per script line, so each line can be pinned to its own beat."""
    workdir.mkdir(parents=True, exist_ok=True)
    out = []
    for i, line in enumerate(lines):
        p = workdir / f"vo_{i:02d}.wav"
        dur = speak(line, p)
        out.append({"index": i, "text": line, "path": str(p), "duration": round(dur, 3)})
    return out


def assemble_vo(segments: list[dict], offsets: list[float], total: float, out: Path) -> Path:
    """Place each narration line at its assigned time on one timeline."""
    inputs, filters, labels = [], [], []
    for i, (seg, off) in enumerate(zip(segments, offsets)):
        inputs += ["-i", seg["path"]]
        ms = int(off * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    graph = ";".join(filters) + ";" + "".join(labels) + \
        f"amix=inputs={len(segments)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{total}[out]"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", *inputs, "-filter_complex", graph,
         "-map", "[out]", "-ar", "48000", "-ac", "2", "-y", str(out)],
        check=True, capture_output=True,
    )
    return out


# --------------------------------------------------------------------------
# Word-level captions
# --------------------------------------------------------------------------

def word_timings(audio: Path, offset_s: float = 0.0, model_size: str = "base.en") -> list[dict]:
    """Transcribe with word timestamps -> @remotion/captions `Caption[]` shape.

    faster-whisper (CTranslate2) rather than openai-whisper: 4x quicker on CPU
    for the same model, which matters when this runs per video. whisper.cpp via
    @remotion/install-whisper-cpp is the alternative if you want the toolchain
    entirely inside Node.
    """
    import numpy as np
    from faster_whisper import WhisperModel

    # Decode to 16 kHz mono float32 ourselves and hand Whisper the array.
    # faster-whisper's own loader goes through PyAV, whose `metadata_errors`
    # kwarg was dropped in recent versions — decoding here sidesteps that
    # version coupling entirely.
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(audio),
         "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True,
    ).stdout
    samples = np.frombuffer(pcm, dtype=np.float32)

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(samples, word_timestamps=True, vad_filter=False)

    captions: list[dict] = []
    for seg in segments:
        for w in (seg.words or []):
            captions.append({
                "text": w.word,
                "startMs": round((w.start + offset_s) * 1000),
                "endMs": round((w.end + offset_s) * 1000),
                "timestampMs": round(((w.start + w.end) / 2 + offset_s) * 1000),
                "confidence": round(float(w.probability), 3),
            })
    return captions


def captions_for(vo_segments: list[dict], offsets: list[float], workdir: Path) -> list[dict]:
    """Word timings across every narration line, shifted onto the final timeline."""
    all_caps: list[dict] = []
    for seg, off in zip(vo_segments, offsets):
        all_caps.extend(word_timings(Path(seg["path"]), offset_s=off))
    all_caps.sort(key=lambda c: c["startMs"])
    (workdir / "captions.json").write_text(json.dumps(all_caps, indent=1))
    return all_caps


if __name__ == "__main__":
    import sys
    wd = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/vo_test")
    segs = narrate(["This is Type Better. Type it wrong, and one tap fixes it."], wd)
    print(json.dumps(segs, indent=2))
    caps = captions_for(segs, [0.0], wd)
    print(f"{len(caps)} words")
    print(json.dumps(caps[:8], indent=1))
