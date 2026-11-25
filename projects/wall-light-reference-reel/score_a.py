"""Original warm bed for concept A: 109 bpm (beat 0.55s), cuts land on bar lines 2.2/4.4/6.6/8.8s.
Soft kick + shaker, Rhodes-ish plucks, pad; a lift into the brand card. Usage: python score_a.py out.wav"""
import numpy as np, wave, sys
SR = 44100; DUR = 12.4; N = int(SR * DUR); B = 0.55
rng = np.random.default_rng(11)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    if j <= i: return
    s = sig[:j - i] * gain
    L[i:j] += s * np.cos((pan + 1) * np.pi / 4); R[i:j] += s * np.sin((pan + 1) * np.pi / 4)

def lp(x, fc):
    # one-pole low-pass via FFT-free recursion (vectorised with lfilter-like cumulative trick is overkill here)
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); p = 0.0
    for k in range(len(x)): p = (1 - a) * x[k] + a * p; y[k] = p
    return y

def pad(notes, start, dur, g=0.05, att=0.6, rel=1.2):
    n = int((dur + rel) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        for d in (-0.06, 0.0, 0.05):
            f = hz(m + d)
            for h in range(1, 5): s += np.sin(2 * np.pi * f * h * tt + rng.random() * 6) / h ** 1.8
    env = np.minimum(1, tt / att) * np.where(tt < dur, 1, np.exp(-(tt - dur) / (rel / 3)))
    s = lp(s * env, 1200) / len(notes)
    add(s, start, -0.35, g); add(s, start + 0.013, 0.35, g)

def keys(m, start, g=0.12, pan=0.0, dec=1.4):
    n = int(2.5 * SR); tt = np.arange(n) / SR; f = hz(m)
    s = (np.sin(2 * np.pi * f * tt + 0.8 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 6)) * np.exp(-tt / dec)
         + 0.25 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 3))
    add(s * np.minimum(1, tt / 0.003), start, pan, g)

def kick(start, g=0.45):
    n = int(0.4 * SR); tt = np.arange(n) / SR; f = 48 + 80 * np.exp(-tt * 28)
    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), start, 0, g)

def shaker(start, g=0.035, pan=0.3):
    n = int(0.09 * SR); tt = np.arange(n) / SR; s = rng.standard_normal(n); s = s - lp(s, 5000)
    add(s * np.minimum(1, tt / 0.01) * np.exp(-tt * 45), start, pan, g)

def swell(start, dur, g=0.08):
    n = int(dur * SR); tt = np.arange(n) / SR; s = lp(rng.standard_normal(n), 3000) * (tt / dur) ** 3
    add(s, start, 0, g)

# chords per bar (2.2s): Dmaj9 | Bm9 | Gmaj7 | A(add9) | Dmaj9 (card)
CH = [[50, 54, 57, 61, 64], [47, 50, 54, 57, 61], [43, 50, 54, 59, 62], [45, 52, 57, 59, 64], [50, 54, 57, 61, 64, 69]]
BASS = [38, 35, 31, 33, 38]
for i, ch in enumerate(CH):
    st = i * 4 * B
    pad(ch, st, 4 * B if i < 4 else 3.4, g=0.06 if i < 4 else 0.075, att=0.5 if i else 1.0)
    keys(BASS[i], st, 0.16, 0, 1.6)
# groove enters bar 2 (teak), breathes out on the card
for k in range(int(8.8 / B)):
    tb = k * B
    if tb >= 2.2 and k % 2 == 0: kick(tb, 0.38)
    if tb >= 1.1: shaker(tb + B / 2, 0.03 if k % 2 else 0.04)
# melody plucks (eighths-ish), lifting toward the card
MEL = [(0.55, 73), (1.1, 76), (1.65, 78), (2.75, 74), (3.3, 73), (3.85, 69), (4.95, 71), (5.5, 74), (6.05, 78),
       (7.15, 76), (7.7, 78), (8.25, 81)]
for st, m in MEL: keys(m, st, 0.09, 0.25 if m % 2 else -0.25, 1.1)
swell(7.7, 1.1, 0.06)
kick(8.8, 0.5)
for st, m in [(8.8, 74), (8.82, 78), (8.84, 81), (9.35, 85), (9.9, 81), (10.45, 78), (11.0, 74)]: keys(m, st, 0.1, 0.1, 1.8)

# small room reverb
irn = int(1.6 * SR); ir = rng.standard_normal(irn) * np.exp(-np.arange(irn) / SR * 3.2); ir /= np.abs(ir).sum() ** 0.5 * 9
def conv(x):
    m = len(x) + irn; F = 1 << int(np.ceil(np.log2(m)))
    return np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[:len(x)]
L = L + 0.3 * conv(L); R = R + 0.3 * conv(R)
env = np.clip((DUR - t) / 1.6, 0, 1) * np.clip(t / 0.05, 0, 1)
L *= env; R *= env
pk = max(np.abs(L).max(), np.abs(R).max()); L /= pk / 0.89; R /= pk / 0.89
out = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print("wrote", sys.argv[1])
