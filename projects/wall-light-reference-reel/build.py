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
    ("full",  "IMG_8284", 0.20, 2.3, 0.5, ("wide", "2500:760:120:420", 535, "1600:400:600:400")),   # WHOLE Aurora on the wall
    ("teak",  "IMG_8289", 4.23, 2.3, 0.5, "panel"),                             # flame-figure grain, square panel high in frame
    ("beam",  "IMG_8295", 1.17, 2.3, 0.5, "iw/1.45:ih/1.45:(iw-ow)/2:ih*0.31"),  # up + down wash on the wall
    ("arm",   "IMG_8285", 1.18, 2.5, 0.5, ("wide", "2500:840:0:500", 520, "1400:400:900:300")),     # whole bar + arm for scale (30"/48")
]
# kept for reference, no longer in the cut: ("hero","IMG_8298",...), ("glide","IMG_8299",...)
DEFLICKER = "deflicker=size=9:mode=am"
# 8284/8285 were shot with a warmer camera white balance; neutralise them to match the other shots (wall R/B ~1.2)
WB = {"full": 7600, "arm": 6600}   # 8284/8285 have mild LED shimmer (jitter ~3.5-4.5) -> smoothed


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    init_project("wall-light-reference-reel", title="Aurora — Warm Up Your Walls (ref-style reel)",
                 pipeline_type="cinematic")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src, t0, dur, speed, crop in SHOTS:
        grade = WOOD if name == "teak" else NATURAL
        if name in WB:
            grade = f"colortemperature=temperature={WB[name]}:mix=0.8,eq=contrast=1.06:saturation=1.05,unsharp=7:7:0.8"
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
        if isinstance(crop, tuple) and crop[0] == "wide":
            # full-product landscape shot: wide panel (feathered top/bottom) over a blurred strip of the same wall
            _, fgc, top, bgc = crop
            vf = None
            fc = (f"[0:v]{DEFLICKER},{pre},{grade},split[a][b];"
                  f"[a]crop={bgc},scale=12:12:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80,eq=brightness=0.05[bg];"  # smooth wall-tone gradient (no streaks)
                  f"[b]crop={fgc},scale=1080:-2:flags=lanczos,format=yuva420p,"
                  "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/36)'[fg];"
                  f"[bg][fg]overlay=0:{top},fps=30,format=yuv420p[v]")
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
