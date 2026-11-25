"""Automated QA for the Aurora 'Warm Up Your Walls' reel.

Tests (all measured, not eyeballed):
  1. flicker      - frame-to-frame brightness jitter inside every shot of the FINAL render
  2. colour       - lit wall reads warm-white (not orange): R/B ratio of the brightest pixels
  3. occlusion    - the product (dark wood band) never sits under a label or the product card,
                    including at the end of each push-in
  4. 4:5 safety   - product + card both survive the 1080x1350 centre crop
  5. format       - duration, resolution, codec, audio present, loudness near -14 LUFS
  6. hyperframes  - the composition passes `hyperframes check`
Usage: python qa/test_reel.py
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OM = ROOT.parents[1]
FINAL = ROOT / "renders" / "aurora_warm-up-your-walls_12s_9x16.mp4"
FINAL45 = ROOT / "renders" / "aurora_warm-up-your-walls_12s_4x5.mp4"
ASSETS = ROOT / "hyperframes" / "assets"
# shot: (start, end, asset, push-in scales)  — must match index.html
SHOTS = {"hero": (0.0, 2.2, (1.0, 1.09)), "teak": (2.2, 4.4, (1.08, 1.0)),
         "beam": (4.4, 6.6, (1.0, 1.06)), "glide": (6.6, 8.8, (1.06, 1.0))}
LABEL = (270, 354)       # .tag top..bottom
CARD = (1108, 1355)      # badge top (1108) .. #card bottom (1355)
ORIGIN_Y = 0.45 * 1920   # transform-origin of video.shot
results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def frames(path, vf, w, h, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + \
          (["-t", str(t)] if t is not None else []) + ["-i", str(path), "-vf", vf, "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    c = 3 if "rgb24" in vf else 1
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, c) if c == 3 else np.frombuffer(raw, np.uint8).reshape(-1, h, w)


# 1. flicker, per shot of the final render (skip 3 frames each side of a cut)
for name, (a, b, _) in SHOTS.items():
    f = frames(FINAL, "scale=96:96,format=gray", 96, 96, ss=a + 0.1, t=b - a - 0.2).astype(float)
    m = f.reshape(len(f), -1).mean(1)
    sm = np.convolve(m, np.ones(7) / 7, "same"); j = np.abs(m - sm)[3:-3]
    check(f"flicker/{name}", j.max() < 2.5, f"max jitter {j.max():.2f} (limit 2.5)")

# 2. colour of the lit wall (brightest 15% of pixels per shot asset)
for name in SHOTS:
    f = frames(ASSETS / f"{name}.mp4", "select=eq(n\\,30),scale=270:480,format=rgb24", 270, 480)[0].astype(float)
    lum = f.mean(2); px = f[lum >= np.percentile(lum, 85)]
    rb = px[:, 0].mean() / max(px[:, 2].mean(), 1)
    check(f"colour/{name}", 1.0 <= rb <= 1.3, f"wall R/B {rb:.2f} (warm-white 1.0-1.3; orange >1.4)")

# 3. product occlusion — locate the dark wood band in each shot asset (first + last frame), map through push-in
def wood_rows(img):
    """Rows belonging to the product: clearly dark bands (< 0.6 x lit wall) at least 40px tall.
    (v1 used 0.72 and no run-length filter; it mistook the naturally dimmer lower wall for wood.)"""
    lum = img.mean(1)
    dark = lum < 0.6 * np.percentile(lum, 80)
    rows, y = [], 0
    while y < len(dark):
        if dark[y]:
            e = y
            while e < len(dark) and dark[e]: e += 1
            if e - y >= 40: rows.extend(range(y, e))
            y = e
        else:
            y += 1
    return np.array(rows)

def through_scale(y, s):
    return ORIGIN_Y + (y - ORIGIN_Y) * s

def dark_px_in(img, s, z0, z1, x0=60, x1=1020):
    """Fraction of a zone's area covered by clearly-dark (wood) pixels, after the push-in scale."""
    wall = np.percentile(img, 80)
    ys = np.arange(img.shape[0]); yy = through_scale(ys, s)
    band = img[(yy >= z0) & (yy <= z1), x0:x1]
    return (band < 0.6 * wall).mean() if band.size else 0.0

for name, (a, b, scales) in SHOTS.items():
    worst = []
    n = int(round((b - a) * 30)) - 2
    for idx, s in ((0, scales[0]), (n, scales[1])):
        g = frames(ASSETS / f"{name}.mp4", f"select=eq(n\\,{idx}),format=gray", 1080, 1920)[0].astype(float)
        for zname, (z0, z1) in (("label", LABEL), ("card", CARD)):
            worst.append((dark_px_in(g, s, z0, z1), zname))
        rows = wood_rows(g)
        if len(rows): band = (int(through_scale(rows.min(), s)), int(through_scale(rows.max(), s)))
    frac, zone = max(worst)
    check(f"occlusion/{name}", frac < 0.03, f"wood band y≈{band[0]}-{band[1]}; {frac:.1%} of the {zone} area is over wood (limit 3%)")

# 4. 4:5 crop keeps product + card (crop window y 285..1635)
for name in SHOTS:
    g = frames(ASSETS / f"{name}.mp4", "select=eq(n\\,30),format=gray", 1080, 1920)[0].astype(float)
    rows = wood_rows(g)
    inside = ((rows >= 285) & (rows <= 1635)).mean() if len(rows) else 0
    check(f"4x5/{name}", inside > 0.8 and CARD[1] <= 1635, f"{inside:.0%} of product rows inside 4:5 window")

# 5. format
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
                               "-of", "json", str(FINAL)], capture_output=True, text=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video")
check("format/9x16", (v["codec_name"], v["width"], v["height"]) == ("h264", 1080, 1920) and abs(float(p["format"]["duration"]) - 12.4) < 0.1,
      f'{v["codec_name"]} {v["width"]}x{v["height"]} {float(p["format"]["duration"]):.2f}s')
check("format/audio", any(s["codec_type"] == "audio" for s in p["streams"]), "audio stream present")
ln = subprocess.run(["ffmpeg", "-i", str(FINAL), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float(json.loads(ln[ln.rindex("{"):ln.rindex("}") + 1])["input_i"])
check("format/loudness", -15.5 <= lufs <= -12.5, f"{lufs:.1f} LUFS (target -14)")
p45 = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-select_streams", "v",
                                 "-of", "json", str(FINAL45)], capture_output=True, text=True).stdout)["streams"][0]
check("format/4x5", (p45["width"], p45["height"]) == (1080, 1350), f'{p45["width"]}x{p45["height"]}')

# 6. hyperframes check
sys.path.insert(0, str(OM))
from tools.video.hyperframes_compose import HyperFramesCompose  # noqa: E402
r = HyperFramesCompose().execute({"operation": "check", "workspace_path": str(ROOT / "hyperframes")})
errs = [f["code"] for v in (r.data or {}).get("report", {}).values() if isinstance(v, dict) and "findings" in v
        for f in v["findings"] if f["severity"] == "error"]
check("hyperframes/check", not errs, "no errors" if not errs else ", ".join(errs))

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f" — FAILED: {', '.join(failed)}" if failed else ""))
(ROOT / "qa" / "report.txt").write_text("\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}: {d}" for n, ok, d in results) + "\n")
sys.exit(1 if failed else 0)
