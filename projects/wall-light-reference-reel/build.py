"""Concept A — 'Warm Up Your Walls' Aurora reel, structured like the raffia-lamp reference
(hero push-in -> material macro -> detail -> wide glow -> brand card), real footage only.

Usage: python build.py   (cuts/grades shots into hyperframes/assets)
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OM = ROOT.parents[1]
sys.path.insert(0, str(OM))
from lib.checkpoint import init_project  # noqa: E402

SRC = OM / "projects" / "aurora-making-reel" / "assets" / "source"
PREV = OM / "projects" / "aurora-making-reel" / "cine" / "hyperframes" / "assets"
OUT = ROOT / "hyperframes" / "assets"

# warm amber look: shift the white wall to candle-warm, lift saturation a touch, soft vignette
AMBER = ("curves=all='0/0.03 0.22/0.32 0.6/0.66 1/1',colortemperature=temperature=3600:mix=0.9,eq=contrast=1.1:saturation=1.25:gamma=0.96,"
         "colorbalance=rs=0.03:bs=-0.04:rh=0.02:bh=-0.03,unsharp=7:7:0.9,vignette=angle=PI/4.6")
# wood-forward shots: keep the grain legible (less orange cast, more local contrast)
WOOD = ("colortemperature=temperature=4300:mix=0.8,eq=contrast=1.14:saturation=1.3:gamma=0.95,"
        "unsharp=9:9:1.3,vignette=angle=PI/5")

# name, src, in, dur_out, speed, crop (w:h:x:y in source px after autorotate, or None for centre fill)
SHOTS = [  # crops push the bar/grain into the upper half so the product card never covers the product
    ("hero",  "IMG_8284", 0.0, 2.3, 0.66, "640:1138:490:437"),            # lit bar + wall wash, clear of cable/clutter
    ("teak",  "IMG_8289", 1.3, 2.3, 0.5,  "480:853:1150:731"),            # tight teak-grain macro (boldest grain)
    ("beam",  "IMG_8273", 0.2, 2.1, 1.0,  "iw/1.3:ih/1.3:(iw-ow)/2:ih*0.23"),  # up + down wash on the wall
    ("glide", "IMG_8299", 0.6, 2.3, 0.5,  "iw/1.3:ih/1.3:(iw-ow)/2:ih*0.23"),  # long glide along the lit bar
]


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    init_project("wall-light-reference-reel", title="Aurora — Warm Up Your Walls (ref-style reel)",
                 pipeline_type="cinematic")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src, t0, dur, speed, crop in SHOTS:
        grade = WOOD if name == "teak" else AMBER
        pre = f"setpts=PTS/{speed}"
        geo = (f"crop={crop}," if crop else "") + \
              "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"
        vf = f"{pre},{geo},{grade},fps=30,format=yuv420p"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", f"{dur*speed+0.1:.3f}",
             "-i", str(SRC / f"{src}.mov"), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "16",
             "-preset", "medium", "-t", f"{dur:.3f}", str(OUT / f"{name}.mp4")])
        print("cut", name)
    for f in ("gsap.min.js", "Inter-SemiBold.otf", "InterDisplay-Bold.otf",
              "cormorant-garamond-latin-400-italic.woff2", "cormorant-garamond-latin-500-normal.woff2"):
        shutil.copy(PREV / f, OUT / f)
    shutil.copy(ROOT / "brand" / "nixwoods_lockup_cream.png", OUT / "logo.png")


if __name__ == "__main__":
    main()
