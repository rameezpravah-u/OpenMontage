"""Hook A/B variants of the transformation ad (hooks from the '50 hooks' reference reel).
Body 2.4-14.6s is identical to the main ad; only the first 2.4s (shot + two hook cards) changes.
Every hook shot keeps the product inside PANEL[v] and the cards inside CARD_TOP/CARD_BOT, which never overlap.
Usage: python variants.py            (builds hook clips + variants/<v>/hyperframes/index.html)
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parents[1] / "projects" / "aurora-making-reel" / "assets" / "source"
MAIN = ROOT / "hyperframes"
FULL_WB = "colortemperature=temperature=7600:mix=0.8,eq=contrast=1.06:saturation=1.05,unsharp=7:7:0.8"
CARD_TOP = (330, 520)    # y range the top card may occupy (2 lines max)
CARD_BOT = (1170, 1300)  # y range of the bottom card (1 line)

VARIANTS = {
    "v1_tube-light-upgrade": dict(
        hook="#50", top='Still using a <b>tube light?</b>', bot="Here's the upgrade.", panel=(600, 980),
        clip=["-ss", "0.15", "-t", "1.5", "-i", "IMG_8284.mov"],
        fc=f"[0:v]deflicker=size=9:mode=am,{FULL_WB},setpts=PTS/0.6,framerate=fps=30:interp_start=0:interp_end=255,split[a][b];"
           "[a]crop=1600:400:600:400,scale=12:12:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80,eq=brightness=0.05[bg];"
           "[b]crop=2500:760:120:420,scale=1080:-2:flags=lanczos,format=yuva420p,"
           "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/36)'[fg];[bg][fg]overlay=0:620"),
    "v2_stop-buying": dict(
        hook="#2", top='<b>Stop buying</b> wall lights', bot="until you watch this.", panel=(600, 1110),
        clip=["-ss", "4.23", "-t", "1.3", "-i", "IMG_8289.mov"],
        fc="[0:v]colortemperature=temperature=4700:mix=0.65,eq=contrast=1.1:saturation=1.15:gamma=0.97,unsharp=9:9:1.2,"
           "setpts=PTS/0.5,split[a][b];"
           "[a]crop=iw:200:0:1380,scale=12:12:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80[bg];"
           "[b]crop=1450:1450:1366:0,scale=1080:1080:flags=lanczos,format=yuva420p,"
           "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/40)'[fg];[bg][fg]overlay=0:240"),
    "v3_what-1999-gets-you": dict(
        hook="#15", top='Here\'s what <b>₹1,999</b>', bot="actually gets you ↓", panel=(600, 1000),
        clip=["-ss", "1.18", "-t", "1.3", "-i", "IMG_8285.mov"],
        fc="[0:v]deflicker=size=9:mode=am,colortemperature=temperature=6600:mix=0.8,eq=contrast=1.06:saturation=1.05,"
           "unsharp=7:7:0.8,setpts=PTS/0.5,framerate=fps=30:interp_start=0:interp_end=255,split[a][b];"
           "[a]crop=1400:400:900:300,scale=12:12:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80,eq=brightness=0.05[bg];"
           "[b]crop=2500:840:0:500,scale=1080:-2:flags=lanczos,format=yuva420p,"
           "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/36)'[fg];[bg][fg]overlay=0:610"),
    "v4_whats-inside": dict(
        hook="#30", top='What\'s actually <b>inside</b>', bot="a NixWoods wall light?", panel=(560, 1150),
        clip=["-ss", "0.1", "-t", "1.3", "-i", "IMG_8249.mov"],
        fc="[0:v]deflicker=size=11:mode=am,eq=contrast=1.06:saturation=1.08,unsharp=5:5:0.6,setpts=PTS/0.5,split[a][b];"
           "[a]scale=1:2:flags=area,scale=1080:1920:flags=bicubic,gblur=sigma=80,eq=brightness=0.06[bg];"
           "[b]crop=iw:ih*0.32:0:ih*0.34,scale=1080:-2:flags=lanczos,format=yuva420p,"
           "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='255*min(1,min(Y,H-1-Y)/36)'[fg];[bg][fg]overlay=0:560"),
}

CSS = """
.hc { position: absolute; left: 80px; width: 920px; text-align: center; display: block; font-family: "IBold"; font-weight: 700;
      font-size: 66px; line-height: 1.32; color: #000; }
.hc span { background: #fff; padding: 4px 24px; border-radius: 18px; -webkit-box-decoration-break: clone; box-decoration-break: clone;
           box-shadow: 0 12px 34px rgba(0,0,0,0.3); }
.hc b { background: #000; color: #fff; padding: 0 14px; border-radius: 12px; }
/* override the main ad's #hTop/#hBot (id rules: 740px wide, 80px, fixed height) */
#hTop.hc, #hBot.hc { left: 60px; width: 960px; height: auto; line-height: 1.32; font-size: 62px; text-align: center; background: none; box-shadow: none; border-radius: 0; }
#hTop.hc { top: 330px; } #hBot.hc { top: 1180px; }
.hc b { white-space: nowrap; }
"""


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    base = (MAIN / "index.html").read_text()
    manifest = {}
    for v, cfg in VARIANTS.items():
        ws = ROOT / "variants" / v / "hyperframes"
        if ws.exists():
            shutil.rmtree(ws)
        (ws / "assets").mkdir(parents=True)
        for f in (MAIN / "assets").iterdir():          # hard-link the shared body assets
            (ws / "assets" / f.name).hardlink_to(f)
        hook_out = ws / "assets" / "hook_v.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y"] + [str(SRC / a) if a.endswith(".mov") else a for a in cfg["clip"]] + \
              ["-filter_complex", cfg["fc"] + ",fps=30,format=yuv420p[v]", "-map", "[v]", "-t", "2.4", "-an",
               "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(hook_out)]
        run(cmd)
        html = base.replace('src="assets/hook.mp4"', 'src="assets/hook_v.mp4"')
        html = re.sub(r'<div id="divider"[^>]*></div>\n', "", html)
        html = re.sub(r'<div id="hTop"[^>]*>.*?</div>',
                      f'<div id="hTop" class="clip hc" style="z-index:30" data-start="0.15" data-duration="2.2" data-track-index="4"><span>{cfg["top"]}</span></div>', html)
        html = re.sub(r'<div id="hBot"[^>]*>.*?</div>',
                      f'<div id="hBot" class="clip hc" style="z-index:30" data-start="0.75" data-duration="1.6" data-track-index="5"><span>{cfg["bot"]}</span></div>', html)
        html = html.replace("</style>", CSS + "</style>")
        html = re.sub(r"<title>.*?</title>", f"<title>Aurora hook {v}</title>", html)
        (ws / "index.html").write_text(html)
        manifest[v] = {"hook_ref": cfg["hook"], "top": re.sub("<.*?>", "", cfg["top"]), "bottom": cfg["bot"],
                       "panel_y": cfg["panel"], "card_top_y": CARD_TOP, "card_bot_y": CARD_BOT}
        print("built", v)
    (ROOT / "variants" / "variants.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
