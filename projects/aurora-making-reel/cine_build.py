"""Cinematic Aurora Meta ad: slow-motion selects with a filmic grade and a real-sound bed."""
import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "assets" / "source", ROOT / "cine" / "hyperframes" / "assets"
FILM = ("eq=contrast=1.08:saturation=0.9:gamma=0.97,"
        "curves=master='0/0.035 0.5/0.48 1/0.95',"
        "colorbalance=rs=-0.02:bs=0.035:rh=0.05:gh=0.01:bh=-0.05,"
        "vignette=angle=PI/5,noise=alls=7:allf=t")
WARM = "colortemperature=temperature=4200:mix=0.55,"
# id, src, in, out_dur, speed, mode(crop|letter), crop-centre-x (0..1), warm, sfx_gain
SEG = [
    ("router", "IMG_8255", 0.8, 3.4, 0.5,  "crop",   0.50, False, 0.0),
    ("polish", "IMG_8254", 0.2, 3.4, 0.5,  "crop",   0.50, False, 0.0),
    ("sun",    "IMG_8263", 0.3, 3.4, 0.5,  "crop",   0.50, False, 0.0),
    ("rows",   "IMG_8249", 0.0, 2.4, 0.5,  "crop",   0.50, False, 0.0),
    ("on",     "IMG_8271", 3.55, 2.4, 1.0, "crop",   0.50, True,  1.0),
    ("glide",  "IMG_8289", 0.8, 3.4, 0.5,  "crop",   0.50, False, 0.0),
    ("reach",  "IMG_8285", 3.0, 2.4, 0.5,  "crop",   0.56, False, 0.0),
    ("end",    "IMG_8299", 0.5, 5.4, 0.5,  "crop",   0.50, True,  0.0),
]
STARTS = [0.0, 3.0, 6.0, 9.0, 11.0, 13.0, 16.0, 18.0]

def run(c): subprocess.run(c, check=True)

def vf(mode, cx, warm, speed):
    col = (WARM if warm else "") + FILM
    pre = f"setpts=PTS/{speed}"
    if mode == "crop":
        return (f"{pre},scale=-2:1920:flags=lanczos,"
                f"crop=1080:1920:'max(0,min(iw-1080,iw*{cx}-540))':0,{col},fps=30,format=yuv420p")
    return (f"{pre},scale=1080:-2:flags=lanczos,{col},pad=1080:1920:0:(oh-ih)/2:black,fps=30,format=yuv420p")

OUT.mkdir(parents=True, exist_ok=True)
plan = []
for (sid, src, t_in, dur, speed, mode, cx, warm, g), st in zip(SEG, STARTS):
    f = SRC / f"{src}.mov"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(t_in), "-t", f"{dur*speed+0.05:.3f}", "-i", str(f), "-vf", vf(mode, cx, warm, speed),
         "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-t", f"{dur:.3f}", str(OUT / f"{sid}.mp4")])
    plan.append({"id": sid, "src": src, "src_in": t_in, "start": st, "dur": dur, "speed": speed, "mode": mode})
D = round(STARTS[-1] + SEG[-1][3], 3)
# ambient bed: the real slow-motion room tone isn't usable (slowed), so take real-time workshop/room audio
# from the same takes, very low, plus the actual switch-on clip sound.
parts = []
tmp = ROOT / "cine" / "sfx"; tmp.mkdir(exist_ok=True)
for (sid, src, t_in, dur, speed, mode, cx, warm, g), st in zip(SEG, STARTS):
    p = tmp / f"{sid}.wav"
    if g > 0:
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(t_in), "-t", f"{dur:.3f}", "-i", str(SRC / f"{src}.mov"), "-vn",
             "-af", "aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:%.3f" % dur, str(p)])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(t_in), "-t", f"{dur:.3f}", "-i", str(SRC / f"{src}.mov"), "-vn",
             "-af", "aresample=44100,aformat=channel_layouts=stereo,lowpass=f=2500,volume=0.35,apad,atrim=0:%.3f" % dur, str(p)])
    parts.append((p, st))
inputs, filt = [], []
for i, (p, st) in enumerate(parts):
    inputs += ["-i", str(p)]
    filt.append(f"[{i}]afade=t=in:d=0.3,afade=t=out:st={max(0,SEG[i][3]-0.4):.2f}:d=0.4,adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
filt.append("".join(f"[a{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,atrim=0:{D},loudnorm=I=-24:TP=-4[o]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[o]", str(ROOT / "cine" / "sfx_bed.wav")])
(ROOT / "cine" / "timeline.json").write_text(json.dumps({"duration": D, "segments": plan}, indent=2))
print("duration", D)
