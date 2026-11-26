"""Automated QA for the Aurora transformation-hook ad (same method as wall-light-reference-reel/qa/test_reel.py).
  flicker   - per-shot frame-to-frame brightness jitter in the FINAL render (the light-on shot is checked
              only after the switch, since the switch itself is a deliberate brightness jump)
  colour    - lit wall in the end shot reads warm-white, not orange (R/B 1.0-1.3)
  occlusion - no text box sits over the product (dark wood) in the hook's 'after' half or the end shot
  hook      - both halves of the split are present in the first second (raw wood on top, lit wall below)
  format    - h264 1080x1920, 14.6s, audio, ~-14 LUFS; 4:5 export 1080x1350 keeps the product
  hyperframes check passes
Usage: python qa/test_ad.py
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OM = ROOT.parents[1]
import os
VARIANT = os.environ.get("VARIANT")          # e.g. v1_tube-light-upgrade -> test that hook variant instead of the main ad
if VARIANT:
    FINAL = ROOT / "renders" / "variants" / f"aurora_hook-{VARIANT}_15s_9x16.mp4"
    FINAL45 = ROOT / "renders" / "variants" / f"aurora_hook-{VARIANT}_15s_4x5.mp4"
    WS = ROOT / "variants" / VARIANT / "hyperframes"
else:
    FINAL = ROOT / "renders" / "aurora_transformation-hook_15s_9x16.mp4"
    FINAL45 = ROOT / "renders" / "aurora_transformation-hook_15s_4x5.mp4"
    WS = ROOT / "hyperframes"
SHOTS = {"hook": (0.0, 2.4), "cut": (2.4, 3.6), "plane": (3.6, 4.8), "route": (4.8, 6.0), "sand": (6.0, 7.2),
         "wire": (7.2, 8.4), "lighton": (9.25, 10.2), "end": (12.0, 14.6)}  # end measured after its text has animated in
results = []


def check(name, ok, detail):
    results.append((name, ok, detail)); print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def grab(path, t, w=1080, h=1920, fmt="gray"):
    c = 3 if fmt == "rgb24" else 1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-vf",
                          f"scale={w}:{h},format={fmt}", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).astype(float)
    return a.reshape(h, w, c) if c == 3 else a.reshape(h, w)


# flicker (handheld workshop shots move a lot, so this measures brightness *jumps*, not motion)
for name, (a, b) in SHOTS.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a + 0.1), "-t", str(b - a - 0.2), "-i", str(FINAL),
                          "-vf", "scale=96:96,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    m = np.frombuffer(raw, np.uint8).reshape(-1, 9216).astype(float).mean(1)
    j = np.abs(m - np.convolve(m, np.ones(7) / 7, "same"))[3:-3]
    check(f"flicker/{name}", j.max() < 2.5, f"max jitter {j.max():.2f} (limit 2.5)")

# colour of the end shot's lit wall
f = grab(FINAL, 13.5, 270, 480, "rgb24"); lum = f.mean(2); px = f[lum >= np.percentile(lum, 85)]
rb = px[:, 0].mean() / px[:, 2].mean()
check("colour/end", 1.0 <= rb <= 1.3, f"wall R/B {rb:.2f} (warm-white 1.0-1.3)")

# occlusion: product pixels (dark wood on the lit wall) vs text boxes, measured on the rendered frame
def wood_frac(img, y0, y1, x0, x1, wall_ref):
    box = img[y0:y1, x0:x1]
    return (box < 0.45 * wall_ref).mean()

if not VARIANT:
    g = grab(FINAL, 1.8)                       # hook: bottom half (after) — product panel ~y 1260-1570
    wall = np.percentile(g[960:], 80)
    prod_rows = np.where((g[960:] < 0.45 * wall).mean(1) > 0.3)[0] + 960
    check("occlusion/hook-after", len(prod_rows) > 0 and prod_rows.min() > 1140,
          f"product rows y≈{prod_rows.min() if len(prod_rows) else '-'}-{prod_rows.max() if len(prod_rows) else '-'}; 'into THIS' card ends at 1140")
else:
    # variant hook: product (dark/contrasty pixels) must sit inside its panel band, cards outside it
    cfg = json.loads((ROOT / "variants" / "variants.json").read_text())[VARIANT]
    p0, p1 = cfg["panel_y"]; ct, cb = cfg["card_top_y"], cfg["card_bot_y"]
    hv = grab(WS / "assets" / "hook_v.mp4", 1.2)
    edge = np.abs(np.diff(hv, axis=1)).mean(1) + np.abs(np.diff(hv, axis=0, append=hv[-1:])).mean(1)  # x+y edges per row: product busy, wall flat
    busy = np.where(edge > 4 * np.median(edge))[0]
    inside = ((busy >= p0) & (busy <= p1)).mean() if len(busy) else 0
    geom_ok = ct[1] <= p0 and p1 <= cb[0]
    check("occlusion/hook", len(busy) > 0 and inside > 0.9 and geom_ok,
          f"product rows y≈{busy.min() if len(busy) else '-'}-{busy.max() if len(busy) else '-'} ({inside:.0%} inside panel {p0}-{p1}); cards {ct} / {cb}")
# locate the product on the clean end clip (no text), then compare with the text positions in index.html
g = grab(ROOT / "hyperframes" / "assets" / "end.mp4", 2.0)
wall = np.percentile(g, 80)
rows = np.where((g < 0.45 * wall).mean(1) > 0.3)[0]
text_boxes = {"logo/name": (250, 510), "hand/price/cta/small": (880, 1225)}
hits = {k: int(((rows >= y0) & (rows <= y1)).sum()) for k, (y0, y1) in text_boxes.items()}
check("occlusion/end", len(rows) > 0 and max(hits.values()) == 0,
      f"product rows y≈{rows.min() if len(rows) else '-'}-{rows.max() if len(rows) else '-'}; overlap with text {hits}")

# hook: top = raw wood (warm, textured), bottom = lit wall (bright) in the first second
f = grab(FINAL, 0.5, 270, 480, "rgb24")
top, bot = f[:240], f[240:]
if not VARIANT: check("hook/split", top.mean() < bot.mean() and top.std() > 25,
      f"top mean {top.mean():.0f} std {top.std():.0f} (raw wood), bottom mean {bot.mean():.0f} (lit wall)")

# format
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
                               "-of", "json", str(FINAL)], capture_output=True, text=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video")
check("format/9x16", (v["codec_name"], v["width"], v["height"]) == ("h264", 1080, 1920) and abs(float(p["format"]["duration"]) - 14.6) < 0.15,
      f'{v["codec_name"]} {v["width"]}x{v["height"]} {float(p["format"]["duration"]):.2f}s')
check("format/audio", any(s["codec_type"] == "audio" for s in p["streams"]), "audio stream present")
ln = subprocess.run(["ffmpeg", "-i", str(FINAL), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float(json.loads(ln[ln.rindex("{"):ln.rindex("}") + 1])["input_i"])
check("format/loudness", -15.5 <= lufs <= -12.5, f"{lufs:.1f} LUFS (target -14)")
g45 = grab(FINAL45, 13.5, 1080, 1350)
r45 = np.where((g45 < 0.45 * np.percentile(g45, 80)).mean(1) > 0.3)[0]
check("format/4x5", len(r45) > 0, f"1080x1350 export; product visible at y≈{r45.min() if len(r45) else '-'}-{r45.max() if len(r45) else '-'}")

sys.path.insert(0, str(OM))
from tools.video.hyperframes_compose import HyperFramesCompose  # noqa: E402
r = HyperFramesCompose().execute({"operation": "check", "workspace_path": str(WS)})
errs = [f["code"] for v in (r.data or {}).get("report", {}).values() if isinstance(v, dict) and "findings" in v
        for f in v["findings"] if f["severity"] == "error"]
check("hyperframes/check", not errs, "no errors" if not errs else ", ".join(errs))

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f" — FAILED: {', '.join(failed)}" if failed else ""))
(ROOT / "qa" / (f"report_{VARIANT}.txt" if VARIANT else "report.txt")).write_text("\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}: {d}" for n, ok, d in results) + "\n")
sys.exit(1 if failed else 0)
