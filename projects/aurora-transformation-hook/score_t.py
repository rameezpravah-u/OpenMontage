"""Original bed for the Aurora transformation-hook ad: 100 bpm (beat 0.6s). Hook 0-2.4 (soft), how-it's-made
2.4-8.4 (groove, workshop SFX on top), riser, 9.05 light-on bloom, 10.2 end resolve. Usage: python score_t.py out.wav"""
import numpy as np, wave, sys
SR = 44100; DUR = 14.6; N = int(SR * DUR); B = 0.6
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

# hook: Dmaj9 pad + question-y plucks
pad([50, 54, 57, 61, 64], 0.0, 2.4, g=0.055, att=0.4)
keys(38, 0.0, 0.16, 0, 1.6)
for st, m in [(0.0, 69), (0.6, 73), (1.2, 76), (1.8, 78)]: keys(m, st, 0.09, 0.2, 1.0)
# how it's made: Bm9 | Gmaj7 | A(add9), groove on
for st, ch, bass in [(2.4, [47, 50, 54, 57, 61], 35), (4.8, [43, 50, 54, 59, 62], 31), (7.2, [45, 52, 57, 59, 64], 33)]:
    pad(ch, st, 2.4 if st < 7.2 else 1.4, g=0.05, att=0.2)
    keys(bass, st, 0.16, 0, 1.4); keys(bass, st + 1.2, 0.12, 0, 1.2)
for k in range(20):
    tb = 2.4 + k * B
    if tb > 8.5: break
    if k % 2 == 0: kick(tb, 0.36)
    shaker(tb + B / 2, 0.035)
for st, m in [(2.4, 74), (3.0, 73), (3.6, 69), (4.8, 71), (5.4, 74), (6.0, 78), (7.2, 76), (7.8, 78)]:
    keys(m, st, 0.08, 0.25 if m % 2 else -0.25, 0.9)
swell(7.9, 1.15, 0.09)               # riser into the switch
# 9.05 light-on bloom: wide open Dmaj9 + shimmer
kick(9.05, 0.55)
pad([38, 50, 57, 61, 64, 69, 73], 9.05, 5.0, g=0.09, att=0.05, rel=2.0)
for st, m in [(9.05, 74), (9.07, 78), (9.09, 81), (9.1, 86), (9.6, 85), (10.2, 81), (10.8, 78), (11.4, 81), (12.0, 74)]:
    keys(m, st, 0.1, 0.1, 2.0)
keys(38, 10.2, 0.16, 0, 2.5)

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
