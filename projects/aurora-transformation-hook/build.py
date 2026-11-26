"""Aurora 'Transformation hook' Meta ad (hook #1 from the 4-hooks reference reel):
'We turned THIS (raw teak) into THIS (Aurora)' -> how it's made in 5 steps -> switch on -> full product + offer.
Real footage only. Windows chosen with ../wall-light-reference-reel/qa/flicker_scan.py.
Usage: python build.py
"""
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OM = ROOT.parents[1]
sys.path.insert(0, str(OM))
from lib.checkpoint import init_project  # noqa: E402

SRC = OM / "projects" / "aurora-making-reel" / "assets" / "source"
SIB = OM / "projects" / "wall-light-reference-reel" / "hyperframes" / "assets"
OUT = ROOT / "hyperframes" / "assets"
TMP = ROOT / "work"

NATURAL = "eq=contrast=1.06:saturation=1.08,unsharp=5:5:0.6"
FULL_WB = "deflicker=size=9:mode=am,colortemperature=temperature=7600:mix=0.8,eq=contrast=1.06:saturation=1.05,unsharp=7:7:0.8"
FILL = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"

# name, src, in, dur, speed, mode, sfx(keep real audio)
STEPS = [
    ("cut",   "IMG_8246", 1.73, 1.2, 1.0, True),
    ("plane", "IMG_8239", 0.97, 1.2, 1.0, True),
    ("route", "IMG_8255", 1.87, 1.2, 1.0, True),
    ("sand",  "IMG_8235", 0.13, 1.2, 1.0, True),
    ("wire",  "IMG_8250", 0.73, 1.2, 1.0, True),   # LED diffusers fitted in the slots (8277 was 24fps -> judder)
]
TIMELINE = []  # (name, start, dur, keep_audio, src, in)


def run(cmd):
    subprocess.run(cmd, check=True)


def enc(args, out):
    run(["ffmpeg", "-v", "error", "-y", *args, "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-r", "30", str(out)])


def wide_panel(src, t0, dur, speed, fgc, top, bgc, extra_out_h=1920):
    """Full-product landscape clip as a feathered wide panel over a smooth wall-tone gradient."""
    return ["-ss", str(t0), "-t", f"{dur*speed+0.1:.3f}", "-i", str(SRC / f"{src}.mov"), "-filter_complex",
            f"[0:v]{FULL_WB},setpts=PTS/{speed},framerate=fps=30:interp_start=0:interp_end=255,deflicker=size=15:mode=am,split[a][b];"
            f"[a]crop={bgc},scale=12:12:flags=area,scale=1080:{extra_out_h}:flags=bicubic,gblur=sigma=80,eq=brightness=0.05[bg];"
            f"[b]crop={fgc},scale=1080:-2:flags=lanczos,format=yuva420p,"
            "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/36)'[fg];"
            f"[bg][fg]overlay=0:{top},fps=30,format=yuv420p[v]", "-map", "[v]", "-t", f"{dur:.3f}"]


def main():
    init_project("aurora-transformation-hook", title="Aurora — Transformation hook ad", pipeline_type="cinematic")
    OUT.mkdir(parents=True, exist_ok=True); TMP.mkdir(exist_ok=True)

    # 1) split-screen hook 0-2.4s: top = raw teak stack (8263), bottom = whole lit Aurora (8284 wide panel)
    enc(["-ss", "0.75", "-t", "2.5", "-i", str(SRC / "IMG_8263.mov"), "-vf",
         f"scale=1080:960:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:960,{NATURAL},fps=30", "-t", "2.4"],
        TMP / "top.mp4")
    enc(wide_panel("IMG_8284", 0.15, 2.4, 0.6, "2500:760:120:420", 300, "1600:400:600:400", 960), TMP / "bot.mp4")
    enc(["-i", str(TMP / "top.mp4"), "-i", str(TMP / "bot.mp4"), "-filter_complex",
         "[0:v][1:v]vstack=2,format=yuv420p[v]", "-map", "[v]", "-t", "2.4"], OUT / "hook.mp4")
    TIMELINE.append(("hook", 0.0, 2.4, False, "IMG_8263", 0.75))

    # 2) how it's made, 5 x 1.2s, real speed with real workshop sound
    t = 2.4
    for name, src, t0, dur, speed, keep in STEPS:
        enc(["-ss", str(t0), "-t", f"{dur+0.1:.3f}", "-i", str(SRC / f"{src}.mov"), "-vf",
             f"{FILL},{NATURAL},fps=30", "-t", f"{dur:.3f}"], OUT / f"{name}.mp4")
        TIMELINE.append((name, round(t, 3), dur, keep, src, t0)); t += dur

    # 3) switch on. 8271 strobes on camera from src 4.93s, so only the clean 4.43-4.90 stretch is used
    #    (bar off -> bloom at src 4.60 -> settling glow), slowed 0.26x with blended in-betweens.
    #    Bloom lands at 8.4 + (4.60-4.43)/0.26 = 9.05s.
    enc(["-ss", "4.43", "-t", "0.47", "-i", str(SRC / "IMG_8271.mov"), "-vf",
         f"setpts=PTS/0.26,framerate=fps=30:interp_start=0:interp_end=255,{FILL},"
         "colortemperature=temperature=5200:mix=0.6,eq=contrast=1.05:saturation=1.08,fps=30,tpad=stop_mode=clone:stop_duration=0.3",
         "-t", "1.8"], OUT / "lighton.mp4")
    TIMELINE.append(("lighton", round(t, 3), 1.8, False, "IMG_8271", 4.43)); t += 1.8

    # 4) end: whole Aurora, slow (0.33x), panel y 540-851 between name and price
    enc(wide_panel("IMG_8284", 0.10, 4.4, 0.33, "2500:760:120:420", 540, "1600:400:600:400"), OUT / "end.mp4")
    TIMELINE.append(("end", round(t, 3), 4.4, False, "IMG_8284", 0.10)); t += 4.4

    # real workshop audio bed, placed on the timeline (silence elsewhere)
    parts = []
    for i, (name, st, dur, keep, src, t0) in enumerate(TIMELINE):
        part = TMP / f"a{i:02d}.wav"
        if keep:
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", f"{dur:.3f}", "-i", str(SRC / f"{src}.mov"), "-vn",
                 "-af", f"aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{dur:.3f},"
                        f"afade=t=in:d=0.03,afade=t=out:st={dur-0.06:.3f}:d=0.06", str(part)])
        else:
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}", str(part)])
        parts.append(part)
    (TMP / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(TMP / "list.txt"),
         "-af", "loudnorm=I=-22:TP=-4", str(ROOT / "assets" / "audio" / "sfx_bed.wav")])
    (ROOT / "timeline.json").write_text(json.dumps({"duration": round(t, 3), "shots": [
        {"id": n, "start": s, "dur": d, "src": src, "src_in": t0} for n, s, d, _, src, t0 in TIMELINE]}, indent=2))
    for f in ("gsap.min.js", "Inter-SemiBold.otf", "InterDisplay-Bold.otf", "cormorant-garamond-latin-400-italic.woff2",
              "cormorant-garamond-latin-500-normal.woff2", "logo.png"):
        shutil.copy(SIB / f, OUT / f)
    print("duration", round(t, 3))


if __name__ == "__main__":
    main()
