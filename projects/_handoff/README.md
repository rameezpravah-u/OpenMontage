# NixWoods reels — handoff

Produced with OpenMontage (cinematic pipeline, HyperFrames runtime, hand-built "atelier" compositions).
`projects/` is normally gitignored; these folders were force-added on this branch.

## Finished deliverables (upload-ready H.264, 1080 wide)
| Project | Files |
|---|---|
| Wood pendant light (18s) | `projects/lumen-wood-pendant-reel/renders/one-line-of-light_reel.mp4` |
| Rubik's Cube table lamp (15s) | `projects/rubiks-cube-lamp-reel/renders/rubiks-cube-lamp_reel.mp4` (+ `cover_red.jpg`, `cover_endcard.jpg`) |
| Wall lights collection (16s) | `projects/wall-lights-viral-reel/renders/wall-lights_reel.mp4` (+ `cover_8pm.jpg`) |
| Compact Wooden Wall Light Meta ad (15s) | `projects/compact-wall-light-ad/renders/compact-wall-light_meta-ad_9x16.mp4`, `..._4x5.mp4` (+ `cover.jpg`) |
| Aurora Teak Linear Wall Light ad (17s) | `projects/aurora-wall-light-ad/renders/aurora-wall-light_ad_9x16.mp4`, `..._4x5.mp4` (+ `cover.jpg`) |

## How to edit / re-render one
Each project has `hyperframes/index.html` (the composition: timing, text, prices, GSAP animation) with all
graded clips, stills, fonts, GSAP and the music in `hyperframes/assets/`.
1. Edit text/prices/timing in `hyperframes/index.html`.
2. Render: `python -c "from tools.tool_registry import registry; registry.discover(); print(registry._tools['hyperframes_compose'].execute({'operation':'render_existing','workspace_path':'projects/<project>/hyperframes','output_path':'projects/<project>/renders/final.mp4'}))"`
3. Convert the HEVC master to H.264 for upload: `ffmpeg -i renders/final.mp4 -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -movflags +faststart -c:a aac -b:a 192k renders/<name>_9x16.mp4`; 4:5 feed version: add `-vf crop=1080:1350:0:285`.
Needs Node >= 22 + ffmpeg (HyperFrames runs via npx) and `pip install -r requirements.txt scipy`.

`artifacts/` holds the pipeline records (research, proposal, script, scene plan, edit decisions, decision log).

## Music
All tracks are original, synthesized with numpy (royalty-free; Pixabay download was blocked with 403).
Generators: `projects/_handoff/scripts/score.py` (pendant), `score2.py` (cube), `score3.py` (wall lights),
`score4.py` (compact), `score5.py` (aurora). Run: `python score5.py out.wav` then
`ffmpeg -i out.wav -af loudnorm=I=-13:TP=-1.2:LRA=9 score.wav`. Not auditioned by ear — listen before posting.

## Known facts / cautions
- Prices taken from nixwoods.com on 2026-11-05: Aurora 30" ₹1,999 (was ₹2,749), 30" up+down ₹2,499, 48" ₹2,999 / ₹3,499; Compact from ₹4,999 (was ₹6,999); collection from ₹1,599; code FLY100 = ₹100 off prepaid.
- Drive files named `aurora_share_*` and `NW-CREATIVE-IMG-...aurora...AC4I*` actually show the twin-tube **Compact** light — don't use them for Aurora.
- Aurora room shots (sideboard/art/mirror/bed) are the store's listing renders; hook/close use real Aurora clips (`aurora_needs-edit_000018/20/64`).
- Wall-lights reel uses Veo AI room clips (with ✦ watermark) + crops of the existing "5 Wall Lights" montage.
- Compact "remote dimmable" beat simulates dimming with an overlay (no real dimming footage existed).
- Not included here: raw source downloads (`assets/source`) and HEVC masters, to keep the branch small. Sources are in the user's Google Drive.
