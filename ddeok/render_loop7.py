import json,math,sys,subprocess,numpy as np
from PIL import Image
from multiprocessing import Pool
LD=sys.argv[3] if len(sys.argv)>3 else 'L7'
m=json.load(open(f'{LD}/manifest.json')); order=['00_background']+m['order']; meta=m['meta']
W,H=m['size']; FPS=60; N=1200
IM=None; BB=None
def init():
    global IM,BB
    IM={n:Image.open(f'{LD}/{n}.png').convert('RGBA') for n in order}
    BB={n:IM[n].getbbox() for n in order}
TAU=2*math.pi
def e(x): return x*x*(3-2*x)
def tf(n,t):
    dx=dy=0.; sx=sy=1.; rot=0.; op=1.
    if n.startswith('70_title_'):
        k=int(n[9:11])-1; T=5; tt=t-k*0.08; tt-=math.floor(tt/T)*T
        up=math.sin(math.pi*tt/0.55) if tt<0.55 else 0
        dy=-16*up+3*math.sin(TAU*(t/10+k*0.07))
        s=0
        if 0.5<=tt<0.85: s=math.sin(math.pi*(tt-0.5)/0.35)
        elif tt<0.5: s=-0.35*math.sin(math.pi*tt/0.5)
        sx=1+0.05*s; sy=1-0.06*s
    elif n.startswith('60_title_header'):
        dy=3*math.sin(TAU*t/10+1.2); s=1+0.012*math.sin(TAU*t/5); sx=sy=s
    elif n.startswith('20_lantern_'):
        k=int(n[-2:]); Ps=[4,5,10,20/3,5,4,10,20/3,5,4,10,5,20/3]; P=Ps[(k-1)%len(Ps)]
        P2={4:10,5:10,10:20}.get(P,10)
        A=6+(k%4)*3; ph=(k*0.137)%1
        dx=A*0.5*math.sin(TAU*(t/P2+ph)); dy=A*math.sin(TAU*(t/P+ph))
        rot=3*math.sin(TAU*(t/P2+ph+0.25))
        op=0.88+0.12*math.sin(TAU*(t*(6+k%5)/20+ph))
    elif n.startswith('26_garland'):
        g=int(n[10]); i=int(n[-2:]); P=4 if g in (1,2) else 5
        A=2.5 if g in (1,2) else 3.5
        rot=A*math.sin(TAU*(t/P-i*0.09+g*0.3))+0.8*math.sin(TAU*(t/(P/2)+i*0.21))
    elif '_win' in n and n.startswith(('15_sky','16_sky')):
        j=int(n[-1]); P=[10,5,4][j-1]; ph=0.3*j+(0.5 if n.startswith('16') else 0)
        op=1-[0.12,0.3,0.45][j-1]*(0.5+0.5*math.sin(TAU*(t/P+ph)))
    elif n=='10_moon_glow':
        op=0.7+0.3*math.sin(TAU*t/5); s=1+0.04*math.sin(TAU*t/5); sx=sy=s
    elif n=='11_moon':
        s=1+0.012*math.sin(TAU*t/10); sx=sy=s
    elif n.startswith('30_sparkles_'):
        k=int(n[-1]); P=[2.5,4,5][k-1]; op=0.25+0.75*(0.5+0.5*math.sin(TAU*(t/P+k/3)))
    elif n=='51_obj_L1_mallet':
        T=2.5; tt=t-math.floor(t/T)*T
        if tt<1.5: rot=-16*e(tt/1.5)
        elif tt<1.68: x=(tt-1.5)/0.18; rot=-16+19*x*x
        else: x=min((tt-1.68)/0.6,1); rot=3*(1-e(x))
    elif n=='50_obj_L1_rabbit_mortar_bowl':
        T=2.5; tt=t-math.floor(t/T)*T; p=math.sin(math.pi*(tt-1.68)/0.42) if 1.68<=tt<2.1 else 0
        sx=1+0.004*p; sy=1-0.008*p
    elif n=='50_obj_R2_ricecake_rabbits':
        s=math.sin(TAU*t/4); sx=1-0.004*s; sy=1+0.008*s
    return dx,dy,sx,sy,rot,op
def frame(i):
    t=i/FPS
    out=IM['00_background'].copy()
    for n in order[1:]:
        dx,dy,sx,sy,rot,op=tf(n,t)
        L=IM[n]; ax,ay=meta[n].get('anchor',[W/2,H/2])
        if (dx,dy,sx,sy,rot)!=(0,0,1,1,0):
            # crop to bbox with margin for speed
            b=BB[n]; mg=60
            x0,y0=max(0,b[0]-mg),max(0,b[1]-mg); x1,y1=min(W,b[2]+mg),min(H,b[3]+mg)
            sub=L.crop((x0,y0,x1,y1))
            r=math.radians(rot); c,s_=math.cos(r),math.sin(r)
            M=np.array([[c*sx,-s_*sy],[s_*sx,c*sy]]); Mi=np.linalg.inv(M)
            # output pixel p (in sub coords +x0) -> input
            a=np.array([ax,ay]); d=np.array([dx,dy]); o=np.array([x0,y0])
            off=a-Mi@(a+d) - o + Mi@o
            sub=sub.transform(sub.size,Image.AFFINE,(Mi[0,0],Mi[0,1],off[0],Mi[1,0],Mi[1,1],off[1]),resample=Image.BICUBIC)
            if op<1: sub.putalpha(sub.split()[3].point(lambda v:int(v*op)))
            out.alpha_composite(sub,(x0,y0))
        else:
            if op<1:
                b=BB[n]; sub=L.crop(b); sub.putalpha(sub.split()[3].point(lambda v:int(v*op))); out.alpha_composite(sub,(b[0],b[1]))
            else:
                b=BB[n]; out.alpha_composite(L.crop(b),(b[0],b[1]))
    return out.convert('RGB').tobytes()
if __name__=='__main__':
    outp=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else N
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-vf','scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:v','libx264','-preset','slow','-crf','12','-g','60','-keyint_min','60','-sc_threshold','0','-maxrate','60M','-bufsize','120M','-movflags','+faststart',outp],stdin=subprocess.PIPE)
    with Pool(4,initializer=init) as p:
        for k,buf in enumerate(p.imap(frame,range(n),chunksize=4)):
            ff.stdin.write(buf)
            if k%120==0: print(k,flush=True)
    ff.stdin.close(); ff.wait(); print('done')
