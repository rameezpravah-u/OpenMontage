#!/bin/bash
# Render, export and QA every hook variant.  Usage: bash render_variants.sh
cd "$(dirname "$0")/../.." || exit 1
for ws in projects/aurora-transformation-hook/variants/v*/; do
  v=$(basename "$ws"); out=projects/aurora-transformation-hook/renders/variants
  mkdir -p "$out"
  python3 -c "
from tools.video.hyperframes_compose import HyperFramesCompose
r=HyperFramesCompose().execute({'operation':'render_existing','workspace_path':'${ws}hyperframes','output_path':'$out/${v}_raw.mp4'})
print('$v', r.success, getattr(r,'error',None))"
  ffmpeg -v error -y -i "$out/${v}_raw.mp4" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.5 -c:a aac -b:a 192k -movflags +faststart "$out/aurora_hook-${v}_15s_9x16.mp4"
  ffmpeg -v error -y -i "$out/aurora_hook-${v}_15s_9x16.mp4" -vf crop=1080:1350:0:285 -c:v libx264 -crf 18 -preset slow -c:a copy -movflags +faststart "$out/aurora_hook-${v}_15s_4x5.mp4"
  rm -f "$out/${v}_raw.mp4"
done
echo ALL_RENDERED
