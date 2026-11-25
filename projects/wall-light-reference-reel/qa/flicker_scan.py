"""Find the steadiest window (no brightness flicker) in each source clip.
Usage: python flicker_scan.py SECONDS clip.mov [clip.mov ...]"""
import subprocess, sys, numpy as np
win_s = float(sys.argv[1])
for path in sys.argv[2:]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout.split()[0]
    a, b = r.split("/"); fps = int(a) / int(b)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=64:64,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.uint8).reshape(-1, 4096).astype(float).mean(1)
    sm = np.convolve(m, np.ones(9) / 9, "same"); j = np.abs(m - sm); j[:4] = 0; j[-4:] = 0
    w = int(fps * win_s)
    if len(m) - 8 < w:
        print(f"{path.split('/')[-1]} fps {fps:.0f} too short ({len(m)/fps:.2f}s)"); continue
    best = min((j[s:s + w].max(), s) for s in range(4, len(m) - w - 4))
    print(f"{path.split('/')[-1]} fps {fps:.0f} dur {len(m)/fps:.2f}s whole-clip max {j.max():.2f} | "
          f"best {win_s}s window max {best[0]:.2f} at t={best[1]/fps:.2f}s")
