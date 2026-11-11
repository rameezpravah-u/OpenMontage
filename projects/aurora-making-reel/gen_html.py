"""Generate the HyperFrames index.html for each Aurora making-of reel from timeline.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CSS = """
@font-face { font-family: "IDBlack"; src: url("assets/InterDisplay-Black.otf"); font-weight: 900; }
@font-face { font-family: "IDBold"; src: url("assets/InterDisplay-Bold.otf"); font-weight: 700; }
@font-face { font-family: "ISemi"; src: url("assets/Inter-SemiBold.otf"); font-weight: 600; }
@font-face { font-family: "Corm"; src: url("assets/cormorant-garamond-latin-400-italic.woff2") format("woff2"); font-style: italic; }
:root { --ink: #120d09; --amber: #ffb54a; --glow: #ffd796; --cream: #fff5e6; }
html, body { margin: 0; background: var(--ink); }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--ink); }
.fill { position: absolute; inset: 0; background: var(--ink); }
video.shot { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; transform-origin: 50% 45%; }
.layer { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; box-sizing: border-box; }
.scrim { background: linear-gradient(180deg, rgba(18,13,9,0.65) 0%, rgba(18,13,9,0.35) 22%, rgba(18,13,9,0) 40%, rgba(18,13,9,0) 50%, rgba(18,13,9,0.55) 68%, rgba(18,13,9,0.82) 100%); }
.cap { position: absolute; left: 70px; top: 1000px; width: 940px; text-align: center; display: block; }
.top { position: absolute; left: 20px; top: 330px; width: 1040px; padding: 70px 50px; box-sizing: border-box; text-align: center; display: block; background: radial-gradient(ellipse 60% 55% at 50% 50%, rgba(18,13,9,0.62) 0%, rgba(18,13,9,0.35) 55%, rgba(18,13,9,0) 100%); }
.top .sub { color: #ffe2b0; }
.top .serif { color: #ffc670; text-shadow: 0 0 2px rgba(0,0,0,0.9), 0 4px 24px rgba(0,0,0,0.85); }
.big { display: block; font-family: "IDBlack"; font-weight: 900; font-size: 92px; line-height: 1.02; letter-spacing: -0.022em; color: #fff; text-shadow: 0 6px 30px rgba(0,0,0,0.65); }
.huge { display: block; font-family: "IDBlack"; font-weight: 900; font-size: 150px; line-height: 0.95; letter-spacing: -0.03em; color: #fff; text-shadow: 0 8px 40px rgba(0,0,0,0.65); }
.sub { display: block; margin-top: 18px; font-family: "IDBold"; font-weight: 700; font-size: 46px; color: var(--glow); text-shadow: 0 4px 20px rgba(0,0,0,0.7); }
.serif { font-family: "Corm"; font-style: italic; font-weight: 400; letter-spacing: 0; color: var(--glow); }
.step { position: absolute; left: 50%; top: 1330px; transform: translateX(-50%); padding: 18px 36px; border-radius: 999px; background: rgba(18,13,9,0.7); border: 2px solid rgba(255,215,150,0.55); white-space: nowrap; display: block; font-family: "IDBlack"; font-weight: 900; font-size: 44px; letter-spacing: 0.06em; color: var(--cream); }
.step b { color: var(--amber); margin-right: 14px; }
.bartrack { position: absolute; left: 140px; top: 330px; width: 800px; height: 10px; border-radius: 10px; background: rgba(255,255,255,0.25); display: block; }
.barfill { position: absolute; left: 140px; top: 330px; width: 800px; height: 10px; border-radius: 10px; background: var(--amber); transform-origin: 0% 50%; box-shadow: 0 0 18px rgba(255,181,74,0.7); display: block; }
.barlabel { position: absolute; left: 140px; top: 268px; font-size: 30px; text-shadow: 0 0 10px rgba(0,0,0,0.9), 0 2px 12px rgba(0,0,0,0.8); width: 800px; text-align: center; display: block; font-family: "ISemi"; font-weight: 600; font-size: 30px; letter-spacing: 0.3em; color: #fff; text-shadow: 0 2px 12px rgba(0,0,0,0.7); }
#flash { background: #fff1d6; opacity: 0; }
.e-brand { position: absolute; left: 60px; top: 380px; width: 960px; text-align: center; display: block; font-family: "ISemi"; font-weight: 600; font-size: 34px; letter-spacing: 0.5em; color: var(--glow); text-shadow: 0 2px 14px rgba(0,0,0,0.6); }
.e-panel { position: absolute; left: 60px; top: 760px; width: 960px; height: 700px; border-radius: 40px; background: rgba(18,13,9,0.82); border: 2px solid rgba(255,215,150,0.35); display: block; }
.e-name { position: absolute; left: 60px; top: 800px; width: 960px; text-align: center; display: block; }
.e-name .serif { display: block; font-size: 120px; line-height: 0.9; }
.e-name .nm { display: block; font-family: "IDBlack"; font-weight: 900; font-size: 54px; color: #fff; margin-top: 6px; }
.e-specs { position: absolute; left: 60px; top: 1010px; width: 960px; text-align: center; display: block; font-family: "ISemi"; font-weight: 600; font-size: 30px; letter-spacing: 0.06em; color: var(--glow); }
.e-price { position: absolute; left: 60px; top: 1060px; width: 960px; text-align: center; display: block; white-space: nowrap; }
.from { font-family: "IDBold"; font-weight: 700; font-size: 44px; color: rgba(255,255,255,0.8); margin-right: 14px; }
.now { font-family: "IDBlack"; font-weight: 900; font-size: 112px; color: #fff; letter-spacing: -0.02em; }
.was { font-family: "IDBold"; font-weight: 700; font-size: 50px; color: rgba(255,255,255,0.55); text-decoration: line-through; margin-left: 18px; }
.off { display: inline-block; margin-left: 18px; padding: 8px 18px; border-radius: 14px; background: var(--amber); color: var(--ink); font-family: "IDBlack"; font-weight: 900; font-size: 42px; vertical-align: 20px; }
.e-cta { position: absolute; left: 190px; top: 1225px; width: 700px; height: 116px; border-radius: 999px; background: var(--amber); color: var(--ink); text-align: center; line-height: 116px; font-family: "IDBlack"; font-weight: 900; font-size: 52px; letter-spacing: 0.04em; display: block; box-shadow: 0 0 60px rgba(255,181,74,0.6); }
.e-code { position: absolute; left: 60px; top: 1370px; width: 960px; text-align: center; display: block; font-family: "IDBold"; font-weight: 700; font-size: 34px; color: var(--cream); }
#fadeout { background: var(--ink); opacity: 0; }
"""

END_CARD = """
<div id="eBrand" class="clip e-brand" data-start="{t}" data-duration="{d}" data-track-index="40">NIXWOODS</div>
<div id="ePanel" class="clip e-panel" data-start="{t}" data-duration="{d}" data-track-index="41"></div>
<div id="eName" class="clip e-name" data-start="{t}" data-duration="{d}" data-track-index="42"><span class="serif">Aurora</span><span class="nm">Teak Linear Wall Light</span></div>
<div id="eSpecs" class="clip e-specs" data-start="{t}" data-duration="{d}" data-track-index="43">SOLID TEAK · WARM LED · 30″ &amp; 48″ · UP/DOWN</div>
<div id="ePrice" class="clip e-price" data-start="{t}" data-duration="{d}" data-track-index="44"><span class="from">from</span><span class="now">₹1,999</span><span class="was">₹2,749</span><span class="off">27% OFF</span></div>
<div id="eCta" class="clip e-cta" data-start="{t}" data-duration="{d}" data-track-index="45">SHOP NOW →</div>
<div id="eCode" class="clip e-code" data-start="{t}" data-duration="{d}" data-track-index="46">Extra ₹100 off on prepaid · code FLY100</div>
"""

END_TL = """
tl.fromTo("#eBrand", {{ opacity: 0, y: -16 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: snap }}, {t}+0.05);
tl.fromTo("#ePanel", {{ opacity: 0, y: 60 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: snap }}, {t});
tl.fromTo("#eName", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: snap }}, {t}+0.15);
tl.fromTo("#eSpecs", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power1.out" }}, {t}+0.4);
tl.fromTo("#ePrice", {{ opacity: 0, scale: 1.3 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: snap }}, {t}+0.55);
tl.fromTo("#eCta", {{ opacity: 0, y: 30, scale: 0.9 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: pop }}, {t}+0.95);
tl.fromTo("#eCta", {{ scale: 1 }}, {{ scale: 1.06, duration: 0.25, ease: "sine.inOut", yoyo: true, repeat: 5, immediateRender: false }}, {t}+1.5);
tl.fromTo("#eCode", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power1.out" }}, {t}+1.25);
"""

# captions: (id, start, dur, html, kind)  kind: cap | step | huge
CAPS = {
    "r1": [
        ("c_hook", 0.0, 2.0, '<span class="big">This light started as a plank of teak.</span>', "cap"),
        ("s1", 2.0, 2.0, "<b>01</b>PLANED", "step"),
        ("s2", 4.0, 2.0, "<b>02</b>CUT TO LENGTH", "step"),
        ("s3", 6.0, 1.0, "<b>03</b>SANDED SMOOTH", "step"),
        ("s4", 7.0, 1.5, "<b>04</b>CHANNEL CUT FOR THE LED", "step"),
        ("s5", 8.5, 2.0, "<b>05</b>POLISHED BY HAND", "step"),
        ("s6", 10.5, 2.5, "<b>06</b>FINISHED IN BATCHES", "step"),
        ("s7", 13.0, 1.0, "<b>07</b>BRANDED", "step"),
        ("s8", 14.0, 1.0, "<b>08</b>WARM LED FITTED", "step"),
        ("c_glow", 15.0, 1.5, '<span class="big">And then…</span><span class="big serif" style="font-size:120px">it glows.</span>', "cap"),
        ("c_teak", 16.5, 1.5, '<span class="big">Solid teak.</span><span class="sub">every bar has its own grain</span>', "cap"),
        ("c_hand", 18.0, 1.5, '<span class="big">Real grain. Real knots.</span>', "cap"),
        ("c_ws", 19.5, 2.5, '<span class="big">Made in our workshop.</span><span class="sub">ready for your wall</span>', "cap"),
        ("c_ud", 22.0, 1.5, '<span class="big">Light up + down</span><span class="sub">or downward only</span>', "cap"),
    ],
    "r2": [
        ("c_hook", 0.0, 1.0, '<span class="big">Raw teak in.</span>', "cap"),
        ("c_hook2", 1.0, 0.5, '<span class="big">Raw teak in.</span><span class="big serif" style="font-size:110px">this out.</span>', "cap"),
        ("w1", 1.5, 1.0, "PLANED", "huge"), ("w2", 2.5, 1.0, "CUT", "huge"),
        ("w3", 3.5, 1.0, "SANDED", "huge"), ("w4", 4.5, 0.5, "ROUTED", "huge"),
        ("w5", 5.0, 1.0, "POLISHED", "huge"), ("w6", 6.0, 0.5, "FINISHED", "huge"),
        ("w7", 6.5, 0.5, "BRANDED", "huge"), ("w8", 7.0, 0.5, "WIRED", "huge"),
        ("w9", 7.5, 1.0, "GLOWING", "huge"),
        ("c_p", 8.5, 2.5, '<span class="big">Made in our workshop.</span><span class="sub">solid teak · warm up + down glow</span>', "cap"),
    ],
    "r3": [],
}
END_AT = {"r1": 23.5, "r2": 11.0}
BAR = {"r1": (2.0, 15.0)}


def build(reel):
    tl = json.load(open(ROOT / reel / "timeline.json"))
    D = tl["duration"]
    vids, anim = [], []
    for i, s in enumerate(tl["segments"]):
        track = 1 + (i % 2)
        vids.append(f'<video id="v_{s["id"]}" class="shot" src="assets/{s["id"]}.mp4" data-start="{s["start"]}" '
                    f'data-duration="{s["dur"]}" data-media-start="0" data-track-index="{track}" muted playsinline></video>')
        t0, d = s["start"], s["dur"]
        if s["mode"] == "fit" or d >= 1.5:
            anim.append(f'tl.fromTo("#v_{s["id"]}", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {d}, ease: "none" }}, {t0});')
        else:
            anim.append(f'tl.fromTo("#v_{s["id"]}", {{ scale: 1.14 }}, {{ scale: 1.02, duration: {d}, ease: snap }}, {t0});')
        if i > 0 and reel != "r3":
            anim.append(f'tl.fromTo("#flash", {{ opacity: 0.16 }}, {{ opacity: 0, duration: 0.18, ease: "power2.out", immediateRender: false }}, {t0});')
    over = []
    end = END_AT.get(reel)
    scrim_d = end if end else D
    over.append(f'<div id="scrim" class="clip layer scrim" data-start="0" data-duration="{scrim_d}" data-track-index="10"></div>')
    over.append(f'<div id="flash" class="clip layer" data-start="0" data-duration="{D}" data-track-index="11"></div>')
    # light-on flash at 1.0s (all reels open on or contain the switch-on)
    on_t = 1.0 if reel != "r3" else 5.5
    anim.append(f'tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.05, ease: "none", immediateRender: false }}, {on_t - 0.05});')
    anim.append(f'tl.to("#flash", {{ opacity: 0, duration: 0.45, ease: "power2.out" }}, {on_t});')
    if reel in BAR:
        a, b = BAR[reel]
        over.append(f'<div id="barLabel" class="clip barlabel" data-start="{a}" data-duration="{b-a}" data-track-index="12">HOW IT\'S MADE</div>')
        over.append(f'<div id="barTrack" class="clip bartrack" data-start="{a}" data-duration="{b-a}" data-track-index="13"></div>')
        over.append(f'<div id="barFill" class="clip barfill" data-start="{a}" data-duration="{b-a}" data-track-index="14"></div>')
        anim.append(f'tl.fromTo("#barFill", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {b-a}, ease: "none" }}, {a});')
        anim.append(f'tl.fromTo(["#barLabel","#barTrack"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {a});')
    for j, (cid, t0, d, html, kind) in enumerate(CAPS[reel]):
        tr = 20 + (j % 2)
        if kind == "step":
            over.append(f'<div id="{cid}" class="clip step" data-start="{t0}" data-duration="{d}" data-track-index="{tr}">{html}</div>')
            anim.append(f'tl.fromTo("#{cid}", {{ opacity: 0, y: 30, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.25, ease: pop }}, {t0});')
        elif kind == "huge":
            over.append(f'<div id="{cid}" class="clip cap" data-start="{t0}" data-duration="{d}" data-track-index="{tr}"><span class="huge">{html}</span></div>')
            anim.append(f'tl.fromTo("#{cid}", {{ opacity: 0, scale: 1.4 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: snap }}, {t0});')
        else:
            over.append(f'<div id="{cid}" class="clip top" data-start="{t0}" data-duration="{d}" data-track-index="{tr}">{html}</div>')
            anim.append(f'tl.fromTo("#{cid}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: pop }}, {t0 + (0.1 if t0 == 0 else 0)});')
    if end:
        over.append(END_CARD.format(t=end, d=round(D - end, 3)))
        anim.append(END_TL.format(t=end))
    over.append(f'<div id="fadeout" class="clip layer" data-start="{D-0.4}" data-duration="0.4" data-track-index="50"></div>')
    if reel != "r3":
        anim.append(f'tl.fromTo("#fadeout", {{ opacity: 0 }}, {{ opacity: 0.5, duration: 0.4, ease: "power1.in" }}, {D-0.4});')
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>Aurora — How It's Made ({reel})</title>
<script src="assets/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-duration="{D}" data-fps="30">
<div id="bg" class="clip fill" data-start="0" data-duration="{D}" data-track-index="0"></div>
{chr(10).join(vids)}
{chr(10).join(over)}
<audio id="music" src="assets/mix.wav" data-start="0" data-duration="{D}" data-track-index="60" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
const pop = "back.out(2.2)";
const snap = "power3.out";
{chr(10).join(anim)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
    (ROOT / reel / "hyperframes" / "index.html").write_text(html)
    print(reel, "index.html written", D)


if __name__ == "__main__":
    for r in (["r1", "r2", "r3"] if sys.argv[1] == "all" else [sys.argv[1]]):
        build(r)
