"""Faceless moody Aurora reel (style of the '50 hooks' reference: dim ambient footage + one gold serif line).
Slow dissolving shots of the real light, darker exposure, light kept warm-WHITE (not orange), soft grain.
Usage: python build.py
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OM = ROOT.parents[1]
sys.path.insert(0, str(OM))
from lib.checkpoint import init_project  # noqa: E402

SRC = OM / "projects" / "aurora-making-reel" / "assets" / "source"
SIB = OM / "projects" / "wall-light-reference-reel" / "hyperframes" / "assets"
OUT = ROOT / "hyperframes" / "assets"
FILL = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"
SLOW = "framerate=fps=30:interp_start=0:interp_end=255"
# moody: lower exposure, deeper shadows, light stays warm-white; fine film grain
MOOD = ("colortemperature=temperature=4700:mix=0.55,curves=all='0/0.02 0.2/0.11 0.45/0.27 0.7/0.52 0.88/0.76 1/0.97',unsharp=13:13:0.9,"
        "eq=contrast=1.05:saturation=0.95")
FINISH = "vignette=angle=PI/3.4,noise=alls=5:allf=t"      # applied after framing (not on the landscape source)
MOOD_FULL = MOOD.replace("temperature=4700:mix=0.55", "temperature=7600:mix=0.8")

# name, src, in, out_dur, speed, geometry   (windows from qa/flicker_scan.py; all 60fps sources)
SHOTS = [
    ("end_glow", "IMG_8298", 0.07, 3.0, 0.4, f"crop=iw/1.3:ih/1.3:(iw-ow)/2:ih*0.15,{FILL}"),  # bar kept below the text block
    ("glide",    "IMG_8299", 1.35, 3.0, 0.4, f"crop=iw/1.3:ih/1.3:(iw-ow)/2:ih*0.23,{FILL}"),
    ("wash",     "IMG_8295", 1.17, 3.0, 0.4, FILL),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    init_project("aurora-faceless-moody", title="Aurora — faceless moody reel", pipeline_type="cinematic")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src, t0, dur, speed, geo in SHOTS:
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", f"{dur*speed+0.1:.3f}", "-i", str(SRC / f"{src}.mov"),
             "-vf", f"setpts=PTS/{speed},{SLOW},{geo},{MOOD},{FINISH},fps=30,format=yuv420p", "-an", "-c:v", "libx264",
             "-crf", "16", "-preset", "medium", "-t", f"{dur:.3f}", str(OUT / f"{name}.mp4")])
        print("cut", name)
    # whole Aurora: feathered wide panel over a smooth dim wall tone
    run(["ffmpeg", "-v", "error", "-y", "-ss", "0.10", "-t", "1.15", "-i", str(SRC / "IMG_8284.mov"), "-filter_complex",
         f"[0:v]deflicker=size=9:mode=am,setpts=PTS/0.33,{SLOW},deflicker=size=15:mode=am,{MOOD_FULL},split[a][b];"
         "[a]crop=1600:400:600:400,scale=12:12:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80[bg];"
         "[b]crop=2500:760:120:420,scale=1080:-2:flags=lanczos,format=yuva420p,"
         "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/40)'[fg];"
         f"[bg][fg]overlay=0:640,{FINISH},fps=30,format=yuv420p[v]", "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16",
         "-preset", "medium", "-t", "3.4", str(OUT / "full.mp4")])
    print("cut full")
    for f in ("gsap.min.js", "cormorant-garamond-latin-400-italic.woff2", "cormorant-garamond-latin-500-normal.woff2"):
        shutil.copy(SIB / f, OUT / f)


if __name__ == "__main__":
    main()
