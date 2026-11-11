"""Cut, grade and time the Aurora making-of footage for three reels.

Each reel gets: hyperframes/assets/<seg>.mp4 (1080x1920, 30fps, silent) plus
assets/sfx_bed.wav — the clips' own workshop audio laid on the same timeline.
Usage: python build_clips.py r1|r2|r3|all
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "assets" / "source"
WARM = "colortemperature=temperature=3600:mix=0.9,eq=brightness=0.04"      # cool-looking lit clips → match "warm LED"
GRADE = "eq=contrast=1.06:saturation=1.1"

# name: (src, start, dur_out, speed, mode, flags)
#   mode: crop = fill 9:16; fit = landscape full-width over blurred fill
#   flags: w = warm-correct, f = rotate 180 (upside-down logo), q = mute (no sfx)
R1 = [
    ("hook",   "IMG_8271", 3.55, 2.0, 1.0, "crop", "q"),
    ("plane1", "IMG_8239", 1.5,  1.0, 1.0, "crop", ""),
    ("plane2", "IMG_8243", 0.3,  0.5, 1.0, "crop", ""),
    ("plane3", "IMG_8241", 1.5,  0.5, 1.0, "crop", ""),
    ("cut1",   "IMG_8246", 2.0,  1.0, 1.0, "crop", ""),
    ("cut2",   "IMG_8248", 0.3,  0.5, 1.0, "crop", ""),
    ("cut3",   "IMG_8247", 0.5,  0.5, 1.0, "crop", ""),
    ("sand1",  "IMG_8235", 0.6,  0.5, 1.0, "crop", ""),
    ("sand2",  "IMG_8237", 0.4,  0.5, 1.0, "crop", ""),
    ("route",  "IMG_8255", 1.5,  1.5, 0.5, "crop", ""),
    ("pol1",   "IMG_8252", 1.0,  1.0, 1.0, "crop", ""),
    ("pol2",   "IMG_8254", 0.5,  1.0, 1.0, "crop", ""),
    ("rows1",  "IMG_8250", 2.0,  0.5, 1.0, "crop", ""),
    ("rows2",  "IMG_8249", 0.3,  0.5, 1.0, "crop", ""),
    ("sun1",   "IMG_8263", 0.5,  1.0, 1.0, "crop", ""),
    ("sun2",   "IMG_8267", 0.8,  0.5, 1.0, "crop", ""),
    ("brand",  "IMG_8269", 1.0,  1.0, 1.0, "crop", "f"),
    ("wire",   "IMG_8277", 0.3,  1.0, 1.0, "crop", ""),
    ("beam",   "IMG_8280", 0.3,  1.5, 1.0, "crop", "w"),
    ("grain",  "IMG_8289", 1.0,  1.5, 1.0, "crop", ""),
    ("hand",   "IMG_8303", 0.2,  1.5, 1.0, "crop", ""),
    ("person", "IMG_8285", 3.0,  2.5, 1.0, "fit",  ""),
    ("updown", "IMG_8273", 0.3,  1.5, 1.0, "crop", "w"),
    ("end",    "IMG_8284", 0.0,  4.5, 0.33, "fit", "q"),
]
R2 = [
    ("hook",   "IMG_8271", 3.55, 1.5, 1.0, "crop", "q"),
    ("plane1", "IMG_8239", 1.8,  0.5, 1.0, "crop", ""),
    ("plane3", "IMG_8241", 1.5,  0.5, 1.0, "crop", ""),
    ("cut1",   "IMG_8246", 2.4,  0.5, 1.0, "crop", ""),
    ("cut2",   "IMG_8248", 0.3,  0.5, 1.0, "crop", ""),
    ("sand1",  "IMG_8235", 0.6,  0.5, 1.0, "crop", ""),
    ("sand2",  "IMG_8237", 0.4,  0.5, 1.0, "crop", ""),
    ("route",  "IMG_8255", 2.0,  0.5, 0.5, "crop", ""),
    ("pol1",   "IMG_8252", 1.2,  0.5, 1.0, "crop", ""),
    ("rows1",  "IMG_8250", 2.0,  0.5, 1.0, "crop", ""),
    ("sun1",   "IMG_8263", 0.8,  0.5, 1.0, "crop", ""),
    ("brand",  "IMG_8269", 1.0,  0.5, 1.0, "crop", "f"),
    ("wire",   "IMG_8277", 0.5,  0.5, 1.0, "crop", ""),
    ("beam",   "IMG_8280", 0.3,  0.5, 1.0, "crop", "w"),
    ("grain",  "IMG_8289", 1.5,  0.5, 1.0, "crop", ""),
    ("person", "IMG_8285", 3.0,  2.5, 1.0, "fit",  ""),
    ("end",    "IMG_8284", 0.0,  4.0, 0.375, "fit", "q"),
]
R3 = [  # satisfying loop, no text
    ("sand1",  "IMG_8235", 0.2,  1.5, 1.0, "crop", ""),
    ("route",  "IMG_8255", 1.2,  1.5, 0.5, "crop", ""),
    ("pol1",   "IMG_8252", 0.5,  1.5, 1.0, "crop", ""),
    ("hook",   "IMG_8271", 3.55, 1.5, 1.0, "crop", "q"),
    ("grain",  "IMG_8289", 0.5,  2.0, 1.0, "crop", ""),
]
REELS = {"r1": R1, "r2": R2, "r3": R3}


def run(cmd):
    subprocess.run(cmd, check=True)


def vf_for(mode, flags, speed):
    pre = f"setpts=PTS/{speed}"
    if "f" in flags:
        pre += ",hflip,vflip"
    color = GRADE + ("," + WARM if "w" in flags else "")
    if mode == "crop":
        return None, f"{pre},scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,{color},fps=30,format=yuv420p"
    fc = (f"[0:v]{pre},{color},split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=45,eq=brightness=-0.12[bg];"
          f"[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=0:(H-h)/2,fps=30,format=yuv420p[v]")
    return fc, None


def build(reel):
    out = ROOT / reel / "hyperframes" / "assets"
    out.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / reel / "sfx_parts"
    tmp.mkdir(parents=True, exist_ok=True)
    plan, t, parts = [], 0.0, []
    for name, src, start, dur, speed, mode, flags in REELS[reel]:
        f = SRC / f"{src}.mov"
        src_dur = dur * speed
        fc, vf = vf_for(mode, flags, speed)
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{src_dur:.3f}", "-i", str(f)]
        cmd += (["-filter_complex", fc, "-map", "[v]"] if fc else ["-vf", vf])
        cmd += ["-an", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-t", f"{dur:.3f}", str(out / f"{name}.mp4")]
        run(cmd)
        # matching slice of real workshop audio (silence when muted or slow-motion)
        part = tmp / f"{len(parts):02d}.wav"
        if "q" in flags or speed != 1.0:
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}", str(part)])
        else:
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{dur:.3f}", "-i", str(f), "-vn",
                 "-af", f"aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{dur:.3f},afade=t=in:d=0.03,afade=t=out:st={max(dur-0.06,0):.3f}:d=0.06",
                 str(part)])
        parts.append(part)
        plan.append({"id": name, "src": src, "src_in": start, "start": round(t, 3), "dur": dur, "speed": speed, "mode": mode, "flags": flags})
        t += dur
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-af", "loudnorm=I=-20:TP=-3", str(ROOT / reel / "sfx_bed.wav")])
    (ROOT / reel / "timeline.json").write_text(json.dumps({"duration": round(t, 3), "segments": plan}, indent=2))
    print(reel, "duration", round(t, 3), "segments", len(plan))


if __name__ == "__main__":
    for r in (REELS if sys.argv[1] == "all" else [sys.argv[1]]):
        build(r)
