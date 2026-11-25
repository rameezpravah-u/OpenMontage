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

# natural look: true-to-product 3000K warm-white light, cream wall, real teak brown.
# (v1 used a heavy amber grade; it read orange and hid the grain — replaced after review.)
NATURAL = "colortemperature=temperature=4700:mix=0.65,eq=contrast=1.06:saturation=1.1:gamma=0.98,unsharp=7:7:0.8"
WOOD = "colortemperature=temperature=4700:mix=0.65,eq=contrast=1.1:saturation=1.15:gamma=0.97,unsharp=9:9:1.2"

# name, src, in, dur_out, speed, crop.  Every window was picked with qa/flicker_scan.py (steadiest
# stretch of each clip — the 8272/8273/8280/8293 up-down clips strobe and are not used).
# Crops push the bar/grain into the upper half so the product card never covers the product.
SHOTS = [
    ("hero",  "IMG_8298", 0.07, 2.3, 0.5, "iw/1.3:ih/1.3:(iw-ow)/2:ih*0.23"),   # bar end, grain + wall glow
    ("teak",  "IMG_8289", 4.23, 2.3, 0.5, "panel"),                             # flame-figure grain, square panel high in frame
    ("beam",  "IMG_8295", 1.17, 2.3, 0.5, "iw/1.45:ih/1.45:(iw-ow)/2:ih*0.31"),  # up + down wash on the wall
    ("glide", "IMG_8299", 1.35, 2.5, 0.5, "iw/1.3:ih/1.3:(iw-ow)/2:ih*0.23"),   # long glide along the lit bar
]


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    init_project("wall-light-reference-reel", title="Aurora — Warm Up Your Walls (ref-style reel)",
                 pipeline_type="cinematic")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src, t0, dur, speed, crop in SHOTS:
        grade = WOOD if name == "teak" else NATURAL
        pre = f"setpts=PTS/{speed}"
        geo = (f"crop={crop}," if crop else "") + \
              "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"
        vf = f"{pre},{geo},{grade},fps=30,format=yuv420p"
        if crop == "panel":  # landscape macro: square crop (bar drift kept inside y 380-976) over blurred wall
            vf = None
            fc = (f"[0:v]{pre},{grade},split[a][b];"
                  "[a]crop=iw:200:0:1380,scale=1080:1920,gblur=sigma=30[bg];"  # plain wall strip below the bar → no ghost bar
                  ""
                  "[b]crop=1450:1450:1366:0,scale=1080:1080:flags=lanczos[fg];"
                  "[bg][fg]overlay=0:82,fps=30,format=yuv420p[v]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", f"{dur*speed+0.1:.3f}",
             "-i", str(SRC / f"{src}.mov"), *(["-vf", vf] if vf else ["-filter_complex", fc, "-map", "[v]"]), "-an", "-c:v", "libx264", "-crf", "16",
             "-preset", "medium", "-t", f"{dur:.3f}", str(OUT / f"{name}.mp4")])
        print("cut", name)
    for f in ("gsap.min.js", "Inter-SemiBold.otf", "InterDisplay-Bold.otf",
              "cormorant-garamond-latin-400-italic.woff2", "cormorant-garamond-latin-500-normal.woff2"):
        shutil.copy(PREV / f, OUT / f)
    shutil.copy(ROOT / "brand" / "nixwoods_lockup_cream.png", OUT / "logo.png")


if __name__ == "__main__":
    main()
