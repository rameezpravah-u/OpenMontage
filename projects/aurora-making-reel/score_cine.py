import numpy as np, wave, sys
SR=44100; DUR=23.4; N=int(SR*DUR); BEAT=0.6
rng=np.random.default_rng(7)
t=np.arange(N)/SR
L=np.zeros(N); R=np.zeros(N)
def hz(m): return 440*2**((m-69)/12)
def add(sig,start,pan=0.0,gain=1.0):
    i=int(start*SR); j=min(N,i+len(sig)); s=sig[:j-i]*gain
    L[i:j]+=s*np.cos((pan+1)*np.pi/4); R[i:j]+=s*np.sin((pan+1)*np.pi/4)
def onepole(x,fc):
    a=np.exp(-2*np.pi*fc/SR); y=np.zeros_like(x); p=0.0
    for k in range(len(x)): p=(1-a)*x[k]+a*p; y[k]=p
    return y
def pad(notes,start,dur,att=1.2,rel=1.5,g=0.06):
    n=int((dur+rel)*SR); tt=np.arange(n)/SR; s=np.zeros(n)
    for m in notes:
        for det in (-0.07,0.0,0.06):
            f=hz(m+det)
            for h in range(1,6): s+=np.sin(2*np.pi*f*h*tt+rng.random()*6)/h**1.6
    env=np.minimum(1,tt/att)*np.where(tt<dur,1,np.exp(-(tt-dur)/ (rel/3)))
    s=onepole(s*env,1400)
    add(s,start,-0.3,g/len(notes)); add(s,start+0.011,0.3,g/len(notes))
def piano(m,start,g=0.22,pan=0.0,dec=2.2):
    n=int(4*SR); tt=np.arange(n)/SR; f=hz(m)
    s=sum(np.sin(2*np.pi*f*h*tt*(1+0.0004*h*h))*np.exp(-tt*(1.0+h*0.9)/dec)/h**1.3 for h in range(1,8))
    s*=np.minimum(1,tt/0.004)
    add(s,start,pan,g)
def kick(start,g=0.5):
    n=int(0.5*SR); tt=np.arange(n)/SR; f=45+90*np.exp(-tt*30)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*7),start,0,g)
def tick(start,g=0.05):
    n=int(0.08*SR); tt=np.arange(n)/SR; s=rng.standard_normal(n); s=s-onepole(s,6000)
    add(s*np.exp(-tt*60),start,0.4,g)
def boom(start,g=0.6):
    n=int(3*SR); tt=np.arange(n)/SR
    add(np.sin(2*np.pi*(38+30*np.exp(-tt*4))*tt)*np.exp(-tt*1.6),start,0,g)
def riser(start,dur,g=0.12):
    n=int(dur*SR); tt=np.arange(n)/SR; s=rng.standard_normal(n)
    s=onepole(s,2500)*(tt/dur)**2.5
    add(s,start,-0.2,g); add(s[::-1]*0,start,0.2,0)
# harmony (MIDI), cinematic: chords move on the cuts
pad([38,54,57,61,64],0.0,3.0,att=1.6)        # Dmaj9
pad([35,50,54,57,61],3.0,3.0,att=0.9)        # Bm9
pad([43,54,59,62,66],6.0,3.0,att=0.9)        # Gmaj7
pad([45,52,57,61,64],9.0,3.0,att=0.9,g=0.05) # A(add9) — held, waiting
pad([38,50,57,61,64,69],12.0,4.0,att=0.2,rel=2.0,g=0.085)   # light on: open Dmaj9
pad([43,55,59,62,66],16.0,2.0,att=0.6)       # Gmaj7
pad([38,50,57,62,66,69],18.0,4.6,att=0.5,rel=2.5,g=0.075)   # home
for st,m,p in [(0.7,74,0),(1.9,69,-.2),(3.1,73,.2),(4.3,66,0),(6.1,71,-.2),(7.3,74,.1),(9.1,76,.2),(10.3,73,0)]:
    piano(m,st,0.18,p)
riser(10.6,1.4,0.07)
boom(12.0,0.32)
for m,st in [(74,12.0),(78,12.02),(81,12.04),(86,12.5),(85,13.3),(81,14.2),(78,15.1)]: piano(m,st,0.16,0.1,3.2)
for st,m in [(16.1,79),(16.9,78),(18.0,74),(18.05,78),(18.1,81),(19.5,85),(21.0,81)]: piano(m,st,0.15,0,3.5)
# reverb
ir_n=int(2.6*SR); ir=rng.standard_normal(ir_n)*np.exp(-np.arange(ir_n)/SR*2.4); ir=onepole(ir,5000); ir/=np.abs(ir).sum()**0.5*8
def conv(x):
    m=len(x)+ir_n; F=1<<int(np.ceil(np.log2(m)))
    return np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
L=L+0.35*conv(L); R=R+0.35*conv(np.roll(R,0))
fade=np.clip((DUR-t)/2.2,0,1); fin=np.clip(t/0.08,0,1)
L*=fade*fin; R*=fade*fin
pk=max(np.abs(L).max(),np.abs(R).max()); L/=pk/0.89; R/=pk/0.89
out=(np.stack([L,R],1)*32767).astype(np.int16)
with wave.open(sys.argv[1],'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('wrote',sys.argv[1])
