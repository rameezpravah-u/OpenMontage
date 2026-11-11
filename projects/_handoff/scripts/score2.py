import numpy as np, wave, sys
SR=44100; DUR=15.0; N=int(SR*DUR); B=0.5
rng=np.random.default_rng(11)
L=np.zeros(N); R=np.zeros(N); t=np.arange(N)/SR
def hz(m): return 440*2**((m-69)/12)
def add(s,st,pan=0.0,g=1.0):
    i=int(st*SR)
    if i>=N: return
    j=min(N,i+len(s)); s=s[:j-i]*g
    L[i:j]+=s*np.cos((pan+1)*np.pi/4); R[i:j]+=s*np.sin((pan+1)*np.pi/4)
def lp(x,fc):
    from scipy.signal import lfilter
    a=np.exp(-2*np.pi*fc/SR); return lfilter([1-a],[1,-a],x)
def hp(x,fc): return x-lp(x,fc)
def kick(st,g=0.9):
    n=int(0.45*SR); tt=np.arange(n)/SR; f=48+140*np.exp(-tt*38)
    add(np.tanh(1.6*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*6.5)),st,0,g)
def clap(st,g=0.32):
    n=int(0.25*SR); tt=np.arange(n)/SR; s=hp(rng.standard_normal(n),900)
    env=np.exp(-tt*22)+0.6*np.exp(-np.maximum(tt-0.012,0)*30)*(tt>0.012)
    add(lp(s*env,6000),st,0.1,g); add(lp(s*env,6000),st+0.008,-0.1,g*0.7)
def hat(st,g=0.10,dec=40,pan=0.3):
    n=int(0.2*SR); tt=np.arange(n)/SR; add(hp(rng.standard_normal(n),7000)*np.exp(-tt*dec),st,pan,g)
def saw(f,tt):
    return sum(np.sin(2*np.pi*f*h*tt)/h for h in range(1,14))
def stab(notes,st,dur,g=0.16,fc=2600,side=True):
    n=int((dur+0.3)*SR); tt=np.arange(n)/SR; s=np.zeros(n)
    for m in notes:
        for d in (-0.08,0.08): s+=saw(hz(m+d),tt)
    env=np.minimum(1,tt/0.01)*np.where(tt<dur,1,np.exp(-(tt-dur)*12))
    s=lp(s*env,fc)/len(notes)
    if side:  # sidechain pump on quarter notes
        ph=((st+tt)%B)/B; s*=0.35+0.65*np.minimum(1,ph/0.45)
    add(s,st,-0.35,g); add(s,st+0.013,0.35,g)
def bass(m,st,dur,g=0.32):
    n=int(dur*SR); tt=np.arange(n)/SR
    s=np.tanh(2*lp(saw(hz(m),tt),700))*np.minimum(1,tt/0.005)*np.exp(-tt*3)
    add(s,st,0,g)
def pluck(m,st,g=0.12,fc=3000,pan=0.0):
    n=int(0.4*SR); tt=np.arange(n)/SR
    add(lp(saw(hz(m),tt)*np.exp(-tt*9),fc),st,pan,g)
def riser(st,dur,g=0.18):
    n=int(dur*SR); tt=np.arange(n)/SR; s=rng.standard_normal(n)
    out=np.zeros(n); seg=int(0.05*SR)
    for k in range(0,n,seg):
        fc=300+9000*(k/n)**2; out[k:k+seg]=hp(s[k:k+seg],fc*0.3)
    add(lp(out,9000)*(tt/dur)**2,st,0,g)
def switch(st,g=0.35):  # light-switch click + whoosh
    n=int(0.03*SR); tt=np.arange(n)/SR
    add(hp(rng.standard_normal(n),2000)*np.exp(-tt*300),st-0.01,0.2,g)
    n=int(0.35*SR); tt=np.arange(n)/SR; w=hp(lp(rng.standard_normal(n),5000),600)
    add(w*np.sin(np.pi*np.minimum(1,tt/0.35))**2,st-0.15,-0.3,g*0.35)
def impact(st,g=0.7):
    n=int(2.5*SR); tt=np.arange(n)/SR
    add(np.sin(2*np.pi*(32+70*np.exp(-tt*6))*tt)*np.exp(-tt*1.8),st,0,g)
    add(lp(rng.standard_normal(n),3000)*np.exp(-tt*5),st,0,g*0.3)
# progression (A minor): Am F C G, 2 beats each = 1s
prog=[[57,60,64,69],[53,57,60,65],[48,55,60,64],[55,59,62,67]]
roots=[33,29,36,31]
# intro 0-1.5: filtered plucks + ticks + riser, gap before drop
arp=[69,72,76,72,69,72]
for i,m in enumerate(arp): pluck(m,i*0.25,0.10,1200+i*500,(-1)**i*0.3)
for k in range(6): hat(k*0.25,0.05,80,0.0)
riser(0.2,1.2,0.16)
# DROP at 1.5
impact(1.5)
def groove(a,b,kicks=True):
    x=a
    while x<b-1e-6:
        i=int(round((x-1.5)/1.0))%4
        stab(prog[i],x,0.95,0.15)
        for q in range(2):
            bt=x+q*B
            if bt>=b: break
            if kicks: kick(bt)
            hat(bt+0.25,0.11,30)
            bass(roots[i]+12*(q%2),bt+0.25,0.22)
            if kicks and abs(((bt-1.5)/B)%2-1)<1e-6: clap(bt)
        x+=1.0
groove(1.5,6.0)
# twist breakdown 6-8: no kick, half-time, riser into 8
stab([57,60,64,71],6.0,1.9,0.12,1500,False)
for k in range(8): pluck([76,72,69,72][k%4],6.0+k*0.25,0.09,2500,(-1)**k*0.4)
riser(6.6,1.4,0.2); clap(7.0,0.25)
impact(8.0,0.5)
groove(8.0,11.0)
# end card 11-15: resolve, lighter
impact(11.0,0.45)
stab([57,60,64,69,72],11.0,3.4,0.16,1800,False)
for k in range(8):
    bt=11.0+k*B
    if k<6: kick(bt,0.6)
    hat(bt+0.25,0.08,30)
for k,m in enumerate([76,74,72,69]): pluck(m,11.5+k*0.75,0.11,3500)
# colour switch SFX on cuts
for c in [2.5,3.5,4.0,5.0,6.0,9.0,9.5,10.0,10.5]: switch(c)
switch(1.5,0.5)
# space
ir_n=int(1.6*SR); ir=rng.standard_normal(ir_n)*np.exp(-np.arange(ir_n)/SR*4); ir=lp(ir,6000); ir/=np.sqrt((ir**2).sum())*6
def conv(x):
    m=len(x)+ir_n; F=1<<int(np.ceil(np.log2(m)))
    return np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
L=L+0.25*conv(L); R=R+0.25*conv(R)
fade=np.clip((DUR-t)/1.0,0,1); L*=fade; R*=fade
L=np.tanh(L/np.abs(L).max()*1.4); R=np.tanh(R/np.abs(R).max()*1.4)
pk=max(np.abs(L).max(),np.abs(R).max()); L*=0.9/pk; R*=0.9/pk
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L,R],1)*32767).astype(np.int16).tobytes())
print('ok')
