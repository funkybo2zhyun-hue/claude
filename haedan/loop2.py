# BG loop v2: every bokeh circle / glitter is its own object, gold lines are redrawn so they can move
import numpy as np, json, sys, math, subprocess
from multiprocessing import Pool
sys.path.insert(0,'/root/hd'); import comp
D='/root/hd/out'; OUT=sys.argv[1]; FPS=60; T=20.0; N=int(T*FPS); W,H=3078,1728; TAU=2*math.pi
L=json.load(open(D+'/leaves.json')); S=np.load(D+'/sprites.npz')
meta=json.load(open(D+'/meta.json')); dz=np.load(D+'/deltas.npz')
base=np.load(D+'/base.npy').astype(np.float32)/255
mult=[(dz[f'd{k}']/255.0,m) for k,m in enumerate(meta) if m and m[0]=='mult'][0]
rng=np.random.default_rng(11)
objs=[]
for i,l in enumerate(L):
    if l['bbox'] is None: continue
    s=S[f's{i}'].astype(np.float32)/255; a=s[...,3:4]
    c=np.where(a>0,s[...,:3]/np.maximum(a,1e-6),0).clip(0,1)
    bm,op=comp.eff(l['chain'],'nested')
    x0,y0,x1,y1=l['bbox']
    objs.append(dict(i=i,tag=l['tag'],c=c,a=a,bm=bm,op=op,x=x0,y=y0,cx=(x0+x1)/2,cy=(y0+y1)/2,size=max(x1-x0,y1-y0)))
# concentric pieces (glitter core + halo) move as one
gid=[];centers=[]
for o in objs:
    for g,(cx,cy,tag) in enumerate(centers):
        if tag==o['tag'] and abs(cx-o['cx'])<8 and abs(cy-o['cy'])<8: o['g']=g;break
    else: o['g']=len(centers);centers.append((o['cx'],o['cy'],o['tag']))
mot=[]
for g,(cx,cy,tag) in enumerate(centers):
    sz=max(o['size'] for o in objs if o['g']==g)
    if tag=='glitter': A=rng.uniform(45,90)
    elif sz<80: A=rng.uniform(55,100)
    elif sz<260: A=rng.uniform(45,85)
    else: A=rng.uniform(25,45)
    mot.append(dict(A=A,ph1=rng.uniform(0,TAU),ph2=rng.uniform(0,TAU),dx=rng.choice([-1,1]),m=int(rng.choice([1,1,2])),
        n=int(rng.choice([1,2,3])),ph3=rng.uniform(0,TAU)))
print('objects',len(objs),'groups',len(centers))
lines=json.load(open(D+'/lines.json'))
for ln in lines:
    (a,b),(c,d)=ln['pts']; v=math.hypot(c-a,d-b); ux,uy=(c-a)/v,(d-b)/v
    ln['pts']=[[a-500*ux,b-500*uy],[c+500*ux,d+500*uy]]  # endpoints never enter the frame while moving
    ln['mo']=[dict(A=rng.uniform(60,120),ph=rng.uniform(0,TAU),ph2=rng.uniform(0,TAU)) for _ in range(2)]
    ln['gph']=rng.uniform(0,1); ln['gk']=int(rng.choice([1,2]))

def shifted(arr,fx,fy):
    # bilinear sub-pixel shift, output 1px larger
    h,w=arr.shape[:2]; o=np.zeros((h+1,w+1,arr.shape[2]),np.float32)
    o[:h,:w]+=arr*((1-fx)*(1-fy)); o[:h,1:]+=arr*(fx*(1-fy)); o[1:,:w]+=arr*((1-fx)*fy); o[1:,1:]+=arr*(fx*fy)
    return o
def put(img,o,dx,dy,f):
    X=o['x']+dx; Y=o['y']+dy; ix,iy=math.floor(X),math.floor(Y)
    a=shifted(o['a'],X-ix,Y-iy); c=shifted(o['c']*o['a'],X-ix,Y-iy)
    c=np.where(a>1e-6,c/np.maximum(a,1e-6),0)
    h,w=a.shape[:2]; a0,b0=max(0,-ix),max(0,-iy); a1,b1=min(w,W-ix),min(h,H-iy)
    if a1<=a0 or b1<=b0: return
    reg=img[iy+b0:iy+b1,ix+a0:ix+a1]; al=a[b0:b1,a0:a1]*(o['op']*f); cc=c[b0:b1,a0:a1]
    if isinstance(o['bm'],tuple):
        x=cc
        for m in reversed(o['bm']): x=comp.blend(m,reg,x)
    else: x=comp.blend(o['bm'],reg,cc)
    reg[:]=(1-al)*reg+al*x

def draw_lines(img,p):
    for ln in lines:
        (x0,y0),(x1,y1)=ln['pts']; mo=ln['mo']
        x0+=mo[0]['A']*math.sin(TAU*p+mo[0]['ph']); y0+=mo[0]['A']*0.7*math.sin(TAU*p+mo[0]['ph2'])
        x1+=mo[1]['A']*math.sin(TAU*p+mo[1]['ph']); y1+=mo[1]['A']*0.7*math.sin(TAU*p+mo[1]['ph2'])
        pad=40
        bx0,bx1=int(max(0,min(x0,x1)-pad)),int(min(W,max(x0,x1)+pad)); by0,by1=int(max(0,min(y0,y1)-pad)),int(min(H,max(y0,y1)+pad))
        if bx1<=bx0 or by1<=by0: continue
        yy,xx=np.mgrid[by0:by1,bx0:bx1].astype(np.float32)+0.5
        vx,vy=x1-x0,y1-y0; Ls=math.hypot(vx,vy); ux,uy=vx/Ls,vy/Ls
        t=(xx-x0)*ux+(yy-y0)*uy; dist=np.abs((xx-x0)*(-uy)+(yy-y0)*ux)
        cov=np.clip(ln['w']/2+0.5-dist,0,1)
        reg=img[by0:by1,bx0:bx1]; reg*=(1-0.4*np.exp(-(dist/5.0)**2))[...,None]  # soft shadow like the original multiply layer
        # glint travelling along the line
        u=((p*ln['gk']+ln['gph'])%1.0)*Ls
        gl=np.exp(-((t-u)/170.0)**2)
        glow=np.exp(-(dist/9.0)**2)*gl*0.55
        col=np.array(ln['col'],np.float32)
        hot=np.array([1.0,0.95,0.78],np.float32)
        cc=col+(hot-col)*np.clip(gl*1.2,0,1)[...,None]
        a=np.clip(cov*(0.9+0.1*gl)+glow,0,1)[...,None]
        reg=img[by0:by1,bx0:bx1]; reg[:]=reg*(1-a)+cc*a

def frame(k):
    p=k/N; img=base.copy()
    for o in objs:
        if o['tag']!='glitter': continue
        m=mot[o['g']]
        c=0.5+0.5*math.cos(TAU*m['n']*p+m['ph3']); f=0.35+0.65*c*c
        put(img,o,m['dx']*m['A']*math.sin(TAU*p+m['ph1']),0.8*m['A']*math.sin(TAU*m['m']*p+m['ph2']),f)
    draw_lines(img,p)
    for o in objs:
        if o['tag']!='fx': continue
        m=mot[o['g']]
        c=0.5+0.5*math.cos(TAU*m['n']*p+m['ph3']); f=0.7+0.3*c
        put(img,o,m['dx']*m['A']*math.sin(TAU*p+m['ph1']),0.8*m['A']*math.sin(TAU*m['m']*p+m['ph2']),f)
    return (np.clip(img[:,3:3+3072],0,1)*255+0.5).astype(np.uint8).tobytes()

if __name__=='__main__':
    if len(sys.argv)>2:
        from PIL import Image
        for k in map(int,sys.argv[2].split(',')): Image.frombytes('RGB',(3072,1728),frame(k)).save(f'{OUT}_f{k}.png')
        sys.exit()
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','3072x1728','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','slow','-crf','9','-pix_fmt','yuv420p','-g',str(FPS),'-keyint_min',str(FPS),'-sc_threshold','0',
        '-movflags','+faststart','-tag:v','avc1',OUT],stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(frame,range(N),chunksize=2): ff.stdin.write(b)
    ff.stdin.close(); ff.wait()
