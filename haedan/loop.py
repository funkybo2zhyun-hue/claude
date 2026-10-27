# 20 s seamless background loop (no text) from the split deltas
import numpy as np, json, sys, math, subprocess
from multiprocessing import Pool
D=sys.argv[1]; OUT=sys.argv[2]; FPS=int(sys.argv[3]) if len(sys.argv)>3 else 60
T=20.0; N=int(T*FPS); W,H=3078,1728
base=np.load(D+'/base.npy').astype(np.float32)
dz=np.load(D+'/deltas.npz'); meta=json.load(open(D+'/meta.json'))
rng=np.random.default_rng(7)
static=base.copy(); movers=[]; lines=None
TAU=2*math.pi
# overlapping pink bokeh must move together, else blend-mode residue shows as crescents
fxi=[i for i,m in enumerate(meta) if m and m[0]=='fx' and m[3]-m[1]<=200]
bigs=[m for m in meta if m and m[0]=='fx' and m[3]-m[1]>200]
par={i:i for i in fxi}
def fd(a):
    while par[a]!=a: a=par[a]
    return a
for a in fxi:
    for b in fxi:
        if a<b:
            A,B=meta[a],meta[b]
            if A[1]<B[3] and B[1]<A[3] and A[2]<B[4] and B[2]<A[4]: par[fd(a)]=fd(b)
# a small one is pinned when a later big cluster draws strongly on top of its footprint
pinned=set()
bigi=[i for i,m in enumerate(meta) if m and m[0]=='fx' and m[3]-m[1]>200]
for i in fxi:
    A=meta[i]; da=np.abs(dz[f'd{i}']).max(2)>10
    for j in bigi:
        if j<i: continue
        B=meta[j]
        X0,Y0,X1,Y1=max(A[1],B[1]),max(A[2],B[2]),min(A[3],B[3]),min(A[4],B[4])
        if X1<=X0 or Y1<=Y0: continue
        db=np.abs(dz[f'd{j}'][Y0-B[2]:Y1-B[2],X0-B[1]:X1-B[1]]).max(2)>12
        if (db & da[Y0-A[2]:Y1-A[2],X0-A[1]:X1-A[1]]).any(): pinned.add(i); break
print('pinned',len(pinned))
grp={}
for i in fxi: grp.setdefault(fd(i),[]).append(i)
gx={}
for r,ms in grp.items():
    x0=min(meta[i][1] for i in ms);y0=min(meta[i][2] for i in ms);x1=max(meta[i][3] for i in ms);y1=max(meta[i][4] for i in ms)
    edge= x0<=2 or y0<=2 or x1>=W-2 or y1>=H-2
    ov=any(i in pinned for i in ms)
    gx[r]=dict(amp=0 if (edge or ov or x1-x0>400) else rng.uniform(10,26),ph=rng.uniform(0,TAU),ph2=rng.uniform(0,TAU),dirx=rng.choice([-1,1]))
print('fx groups',len(grp),sum(1 for g in gx.values() if g['amp']>0),'moving')
for i,m in enumerate(meta):
    if m is None: continue
    t,x0,y0,x1,y1=m; d=dz[f'd{i}'].astype(np.float32)
    w,h=x1-x0,y1-y0
    edge = x0<=2 or y0<=2 or x1>=W-2 or y1>=H-2
    if t=='lines': lines=(d,x0,y0); continue
    if t=='mult' or w>1200: static[y0:y1,x0:x1]+=d; continue
    if t=='fx':
        big = w>200
        G=gx[fd(i)] if not big else dict(amp=0,ph=0,ph2=0,dirx=1)
        movers.append(dict(d=d,x=x0,y=y0,amp=G['amp'],ph=G['ph'],ph2=G['ph2'],
            dirx=G['dirx'], n=int(rng.choice([1,2])), lo=0.80 if big else 0.62, ph3=rng.uniform(0,TAU)))
    else:  # glitter
        amp = 0  # glitter stays put: later blend layers were computed on top of it
        movers.append(dict(d=d,x=x0,y=y0,amp=amp,ph=rng.uniform(0,TAU),ph2=rng.uniform(0,TAU),
            dirx=rng.choice([-1,1]), n=int(rng.choice([1,2,3])), lo=0.15, ph3=rng.uniform(0,TAU), tw=True))
ld,lx,ly=lines; lh,lw=ld.shape[:2]
yy,xx=np.mgrid[ly:ly+lh,lx:lx+lw].astype(np.float32)
diag=(xx*0.8+yy*0.6)  # sweep axis
dmin,dmax=float(diag.min())-400,float(diag.max())+400

def add_shift(img,d,x,y,dx,dy,f):
    ix,iy=math.floor(dx),math.floor(dy); fx,fy=dx-ix,dy-iy
    h,w=d.shape[:2]
    for ox,oy,wt in ((ix,iy,(1-fx)*(1-fy)),(ix+1,iy,fx*(1-fy)),(ix,iy+1,(1-fx)*fy),(ix+1,iy+1,fx*fy)):
        if wt<1e-4: continue
        X0,Y0=x+ox,y+oy; a0,b0=max(0,-X0),max(0,-Y0); a1,b1=min(w,W-X0),min(h,H-Y0)
        if a1<=a0 or b1<=b0: continue
        img[Y0+b0:Y0+b1,X0+a0:X0+a1]+=d[b0:b1,a0:a1]*(wt*f)

def frame(k):
    t=k/FPS; p=t/T
    img=static.copy()
    for m in movers:
        dx=m['amp']*m['dirx']*math.sin(TAU*p+m['ph']); dy=m['amp']*0.7*math.sin(TAU*p+m['ph2'])
        c=0.5+0.5*math.cos(TAU*m['n']*p+m['ph3'])
        f = 1+1.6*c**6 if m.get('tw') else m['lo']+(1-m['lo'])*c
        add_shift(img,m['d'],m['x'],m['y'],dx,dy,f)
    # gold lines: steady + a soft light band sweeping across twice per loop
    s=dmin+(dmax-dmin)*((2*p)%1.0)
    g=1.0+1.8*np.exp(-((diag-s)/170.0)**2)
    img[ly:ly+lh,lx:lx+lw]+=ld*g[...,None]
    return np.clip(img[:,3:3+3072]+0.5,0,255).astype(np.uint8).tobytes()

if __name__=='__main__':
    if len(sys.argv)>4:  # still frames for checking
        from PIL import Image
        for k in map(int,sys.argv[4].split(',')):
            Image.frombytes('RGB',(3072,1728),frame(k)).save(f'{OUT}_f{k}.png')
        sys.exit()
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','3072x1728','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','slow','-crf','9','-pix_fmt','yuv420p','-g',str(FPS),'-keyint_min',str(FPS),'-sc_threshold','0',
        '-movflags','+faststart','-tag:v','avc1',OUT],stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(frame,range(N),chunksize=4): ff.stdin.write(b)
    ff.stdin.close(); ff.wait()
