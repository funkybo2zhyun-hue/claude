import json,math,sys,numpy as np
from PIL import Image
m=json.load(open('L5/manifest.json')); order=['00_background']+m['order']; meta=m['meta']
IM={n:Image.open(f'L5/{n}.png').convert('RGBA') for n in order}
def tf(n,t):
    dx=dy=0; sx=sy=1; rot=0; op=1
    if n.startswith('70_title_'):
        k=int(n[9:11])-1; T=5; tt=t-k*0.08; tt-=math.floor(tt/T)*T
        up=math.sin(math.pi*tt/0.55) if tt<0.55 else 0
        dy=-16*up+3*math.sin(2*math.pi*(t/10+k*0.07))
        s=0
        if 0.5<=tt<0.85: s=math.sin(math.pi*(tt-0.5)/0.35)
        elif tt<0.5: s=-0.35*math.sin(math.pi*tt/0.5)
        sx=1+0.05*s; sy=1-0.06*s
    if n=='51_obj_L1_mallet':
        T=2.5; tt=t-math.floor(t/T)*T; e=lambda x:x*x*(3-2*x)
        if tt<1.5: rot=-16*e(tt/1.5)
        elif tt<1.68: x=(tt-1.5)/0.18; rot=-16+19*x*x
        else: x=min((tt-1.68)/0.6,1); rot=3*(1-e(x))
    return dx,dy,sx,sy,rot,op
def frame(t):
    out=IM['00_background'].copy()
    for n in order[1:]:
        dx,dy,sx,sy,rot,op=tf(n,t)
        L=IM[n]; ax,ay=meta[n].get('anchor',[1280,384])
        if (dx,dy,sx,sy,rot)!=(0,0,1,1,0):
            # inverse affine: output p -> input
            r=math.radians(rot); c,s_=math.cos(r),math.sin(r)
            # forward: q = A*R*S*(p-a) + a + d
            M=np.array([[c*sx,-s_*sy],[s_*sx,c*sy]]); Mi=np.linalg.inv(M)
            off=np.array([ax,ay])-Mi@np.array([ax+dx,ay+dy])
            L=L.transform(L.size,Image.AFFINE,(Mi[0,0],Mi[0,1],off[0],Mi[1,0],Mi[1,1],off[1]),resample=Image.BICUBIC)
        out.alpha_composite(L)
    return out.convert('RGB')
ts=[float(x) for x in sys.argv[1:]]
fr=[frame(t) for t in ts]
sheet=Image.new('RGB',(1280,384*len(fr)))
for i,f in enumerate(fr): sheet.paste(f.resize((1280,384)),(0,384*i))
sheet.save('sim.png')
fr[0].crop((300,250,800,768)).save('sim_mallet.png')
