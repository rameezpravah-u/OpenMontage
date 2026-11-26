"""Automated QA for the faceless moody Aurora reel.
  flicker   - per-shot brightness jitter in the final render (dissolve windows skipped)
  colour    - the light reads warm-WHITE, not orange (R/B of brightest pixels 1.0-1.35)
  moody     - frames are genuinely dim (mean luma well under the daylight ads)
  grain     - the teak still shows texture after the dark grade (not crushed to flat black)
  occlusion - text blocks never sit over the product (checked on the clean shot clips)
  format    - h264 1080x1920 11s, audio, ~-14 LUFS, 4:5 export; hyperframes check
Usage: python qa/test_moody.py
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OM = ROOT.parents[1]
A = ROOT / "hyperframes" / "assets"
FINAL = ROOT / "renders" / "aurora_faceless-moody_11s_9x16.mp4"
FINAL45 = ROOT / "renders" / "aurora_faceless-moody_11s_4x5.mp4"
SHOTS = {"end_glow": (0.9, 2.5), "glide": (3.1, 5.1), "wash": (5.7, 7.7), "full": (8.3, 10.8)}
TEXT_A = (300, 530)   # "Still using a tube light?" block, shots 1-3
TEXT_B = [(290, 490), (995, 1130)]   # end text (name above, price below the bar), shot 4
results = []


def check(n, ok, d):
    results.append((n, ok, d)); print(f"[{'PASS' if ok else 'FAIL'}] {n}: {d}")


def grab(path, t, w=1080, h=1920, fmt="gray"):
    c = 3 if fmt == "rgb24" else 1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-vf",
                          f"scale={w}:{h},format={fmt}", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).astype(float)
    return a.reshape(h, w, c) if c == 3 else a.reshape(h, w)


def product_rows(g):
    """Rows of the bar: a solid band >=24px tall, clearly darker than the lit wall, measured on the centre
    columns only (v1 used full-width rows and mistook the vignette's dark edges for the product)."""
    c = g[:, 270:810].mean(1)
    dark = c < 0.6 * np.median(c)
    rows, y = [], 0
    while y < len(dark):
        if dark[y]:
            e = y
            while e < len(dark) and dark[e]: e += 1
            if e - y >= 24 and 80 < y and e < 1840: rows.extend(range(y, e))
            y = e
        else:
            y += 1
    return np.array(rows, dtype=int)


for n, (a, b) in SHOTS.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", str(FINAL), "-vf",
                          "scale=96:96,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    m = np.frombuffer(raw, np.uint8).reshape(-1, 9216).astype(float).mean(1)
    j = np.abs(m - np.convolve(m, np.ones(7) / 7, "same"))[3:-3]
    check(f"flicker/{n}", j.max() < 2.5, f"max jitter {j.max():.2f} (limit 2.5)")

for n in SHOTS:
    f = grab(A / f"{n}.mp4", 1.5, 270, 480, "rgb24"); lum = f.mean(2); px = f[lum >= np.percentile(lum, 97)]
    rb = px[:, 0].mean() / px[:, 2].mean()
    check(f"colour/{n}", 1.0 <= rb <= 1.35, f"light R/B {rb:.2f} (warm-white 1.0-1.35; orange >1.4)")

lumas = [grab(FINAL, t, 270, 480).mean() for t in (1.5, 4.0, 6.5, 9.5)]
check("moody/dim", max(lumas) < 120, f"mean luma per shot {[round(x) for x in lumas]} (limit 120; daylight ads ~150-190)")

for n in ("end_glow", "glide", "wash"):
    g = grab(A / f"{n}.mp4", 1.5)
    rows = product_rows(g)
    if not len(rows):
        check(f"grain/{n}", False, "bar not found"); continue
    band = g[rows.min():rows.max() + 1, 100:980]
    tex = np.abs(np.diff(band, axis=0)).mean()
    check(f"grain/{n}", tex > 1.2 and band.mean() > 18, f"bar mean {band.mean():.0f}, texture {tex:.2f} (needs >18 and >1.2: not crushed)")

for n, zones in (("end_glow", [TEXT_A]), ("glide", [TEXT_A]), ("wash", [TEXT_A]), ("full", TEXT_B)):
    worst = 0; rr = None
    for t in (0.2, 1.5, 2.8):
        g = grab(A / f"{n}.mp4", t)
        rows = product_rows(g)
        if len(rows): rr = (int(rows.min()), int(rows.max()))
        worst = max(worst, max(int(((rows >= z0) & (rows <= z1)).sum()) for z0, z1 in zones))
    check(f"occlusion/{n}", rr is not None and worst < 20, f"bar rows y≈{rr}; {worst}px rows under text {zones}")

p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
                               "-of", "json", str(FINAL)], capture_output=True, text=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video")
check("format/9x16", (v["codec_name"], v["width"], v["height"]) == ("h264", 1080, 1920) and abs(float(p["format"]["duration"]) - 11) < 0.15,
      f'{v["codec_name"]} {v["width"]}x{v["height"]} {float(p["format"]["duration"]):.2f}s')
check("format/audio", any(s["codec_type"] == "audio" for s in p["streams"]), "audio stream present")
ln = subprocess.run(["ffmpeg", "-i", str(FINAL), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float(json.loads(ln[ln.rindex("{"):ln.rindex("}") + 1])["input_i"])
check("format/loudness", -15.5 <= lufs <= -12.5, f"{lufs:.1f} LUFS (target -14)")
w45 = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "json",
                                 str(FINAL45)], capture_output=True, text=True).stdout)["streams"][0]
check("format/4x5", (w45["width"], w45["height"]) == (1080, 1350), f'{w45["width"]}x{w45["height"]}')

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
