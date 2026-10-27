# 관저동 먹자웨이 v4 LED loop: 20 s @ 60 fps, 2560x768, every motion periodic in 20 s.
import sys, os, pickle, math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
A='/root/mk/anim/'; W,H=2560,768; FPS=60; DUR=20.0; NF=int(DUR*FPS)
TAU=2*math.pi; BEAT=0.625
REST=os.environ.get('REST')=='1'
rng=np.random.default_rng(7)
# ---------------- assets
def ld(p):
    im=Image.open(p); im.load(); return im
plate=ld(A+'plate_clean.png').convert('RGB')
win=ld(A+'win.png'); win_np=np.asarray(win).copy(); win_lab=np.load(A+'win_lab.npy')
WY1=int(np.where(win_np[...,3].max(1)>0)[0].max())+3
NWIN=int(win_lab.max())
busker=ld(A+'sp_busker.png').convert('RGBA'); BK=(692,327)
couple=ld(A+'sp_couple.png').convert('RGBA'); CP=(1860,365)
monitor=ld(A+'sp_monitor.png').convert('RGBA'); MON=(721,568)
badge={k:ld(A+f'badge_{k}.png') for k in ('ob','fb')}
moon2=ld(A+'moon2x.png'); star2=ld(A+'star2x.png')
tshadow=ld(A+'title_shadow.png')
TM=pickle.load(open(A+'title1x.pkl','rb'))['pieces']
for i,p in enumerate(TM): p['img']=ld(A+f'p1_{i:02d}.png')
bulbs=np.load(A+'bulbs_final.npy')
# title layer box
TX0=min(p['X'] for p in TM)-90; TY0=min(p['Y'] for p in TM)-90
TX1=max(p['X']+p['img'].width for p in TM)+90; TY1=min(H,max(p['Y']+p['img'].height for p in TM)+60)
TCX=(min(p['x'] for p in TM)+max(p['x']+p['w'] for p in TM))/2; TCY=(min(p['y'] for p in TM)+max(p['y']+p['h'] for p in TM))/2
# ---------------- helpers
def sm(x): x=min(max(x,0.0),1.0); return x*x*(3-2*x)
def cyc(t,a,b,ramp=0.3):
    """envelope 1 inside [a,b] (seconds, may wrap past 20) with smooth ramps, periodic"""
    t=(t-a)%DUR; L=(b-a)%DUR
    if t>L: return 0.0
    return sm(t/ramp)*sm((L-t)/ramp)
def dt(t,t0):
    """signed time since t0 on the loop, in (-10,10]"""
    d=(t-t0)%DUR
    return d-DUR if d>DUR/2 else d
def aff(dx=0,dy=0,rot=0,sx=1,sy=1,ax=0,ay=0):
    """3x3: scale+rotate about (ax,ay) then translate. rot in degrees, positive = counter-clockwise on screen"""
    c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot))
    R=np.array([[c,s,0],[-s,c,0],[0,0,1.0]]); S=np.diag([sx,sy,1.0])
    T1=np.array([[1,0,-ax],[0,1,-ay],[0,0,1.0]]); T2=np.array([[1,0,ax+dx],[0,1,ay+dy],[0,0,1.0]])
    return T2@R@S@T1
I3=np.eye(3)
def place(dst,img,X,Y,M=I3,ox=0,oy=0):
    """composite sprite img whose rest top-left is canvas (X,Y), moved by canvas affine M; dst origin at (ox,oy)"""
    if np.allclose(M,I3,atol=1e-4):
        dst.alpha_composite(img,(X-ox,Y-oy)); return
    w,h=img.size
    cs=np.array([[X,Y,1],[X+w,Y,1],[X,Y+h,1],[X+w,Y+h,1]],float)@M.T
    bx0=int(math.floor(cs[:,0].min()))-1; by0=int(math.floor(cs[:,1].min()))-1
    bx1=int(math.ceil(cs[:,0].max()))+1; by1=int(math.ceil(cs[:,1].max()))+1
    Mi=np.linalg.inv(M)
    # output pixel (x,y) in box -> canvas (bx0+x, by0+y) -> rest canvas -> sprite (minus X,Y)
    a,b,c=Mi[0]; d,e,f=Mi[1]
    data=(a,b,a*bx0+b*by0+c-X, d,e,d*bx0+e*by0+f-Y)
    out=img.convert('RGBa').transform((bx1-bx0,by1-by0),Image.AFFINE,data,resample=Image.BICUBIC).convert('RGBA')
    dst.alpha_composite(out,(bx0-ox,by0-oy))
# ---------------- motion primitives (return dict of dx,dy,rot,sx,sy)
def hop(t,t0,dur,h,sq=0.12,tilt=0.0):
    u=dt(t,t0)/dur
    if -0.25<=u<0:
        v=(u+0.25)/0.25; k=math.sin(math.pi*v); return dict(sy=1-sq*k,sx=1+0.7*sq*k)
    if 0<=u<1:
        k=math.sin(math.pi*u); return dict(dy=-h*4*u*(1-u),sy=1+0.6*sq*k,sx=1-0.4*sq*k,rot=tilt*k)
    if 1<=u<1.35:
        v=(u-1)/0.35; k=math.sin(math.pi*v)*(1-0.4*v); return dict(sy=1-sq*k,sx=1+0.7*sq*k)
    return {}
def spring(t,t0,dur,amp,n=1.5):
    u=dt(t,t0)/dur
    if 0<=u<1: return amp*math.exp(-3*u)*math.sin(TAU*n*u)/0.64
    return 0.0
def add(*ds):
    o=dict(dx=0.0,dy=0.0,rot=0.0,sx=1.0,sy=1.0)
    for d in ds:
        o['dx']+=d.get('dx',0); o['dy']+=d.get('dy',0); o['rot']+=d.get('rot',0)
        o['sx']*=d.get('sx',1); o['sy']*=d.get('sy',1)
    return o
# ---------------- title choreography
G=dict(dj=[i for i,p in enumerate(TM) if p['name'] in('dj','dj_star')],
       gw=[i for i,p in enumerate(TM) if p['name'] in('gw_1','gw_2','gw_3')],
       dash=[i for i,p in enumerate(TM) if p['name'].startswith('gw_dash')],
       band=[i for i,p in enumerate(TM) if p['name']=='bd_band'],
       bc=[i for i,p in enumerate(TM) if p['name'].startswith('bd_c')])
MK=[[i for i,p in enumerate(TM) if p['name'] in (f'mk_{k}_o',f'mk_{k}_f')] for k in range(1,5)]
for k in G: G[k].sort(key=lambda i:TM[i]['x'])
def bottom_center(idx):
    xs=[TM[i]['x'] for i in idx]; xe=[TM[i]['x']+TM[i]['w'] for i in idx]; ye=[TM[i]['y']+TM[i]['h'] for i in idx]
    return (min(xs)+max(xe))/2, max(ye)
def center(idx):
    xs=[TM[i]['x'] for i in idx]; xe=[TM[i]['x']+TM[i]['w'] for i in idx]
    ys=[TM[i]['y'] for i in idx]; ye=[TM[i]['y']+TM[i]['h'] for i in idx]
    return (min(xs)+max(xe))/2,(min(ys)+max(ye))/2
def title_mats(t):
    mats={}
    def put(idx,m,anchor):
        ax,ay=anchor
        M=aff(m['dx'],m['dy'],m['rot'],m['sx'],m['sy'],ax,ay)
        for i in idx: mats[i]=M
    # Daejeon no.1 — letter waves (L->R at 0.2, R->L at 10.2) + continuous ripple in dance parts
    n=len(G['dj'])
    for k,i in enumerate(G['dj']):
        nm=TM[i]['name']
        m=add(hop(t,0.20+0.05*k,0.42,15,0.10),hop(t,10.20+0.05*(n-1-k),0.42,15,0.10))
        env=cyc(t,5.6,9.7)+cyc(t,16.2,19.6)
        m=add(m,dict(dy=-6*env*max(0,math.sin(TAU*(t/1.25-k/n)))))
        if nm=='dj_star':
            spin=0.0
            for t0 in (0.2,5.0,10.2,15.0):
                u=dt(t,t0)/1.1
                if 0<=u<1: spin+=360*sm(u)
            m=add(m,dict(rot=spin*(1 if k==0 else -1),sx=1+0.35*abs(spring(t,0.2,1.1,1)),sy=1+0.35*abs(spring(t,0.2,1.1,1))))
            put([i],m,center([i]))
        else: put([i],m,bottom_center([i]))
    # 관 저 동
    for k,i in enumerate(G['gw']):
        m=add(hop(t,0.95+0.17*k,0.48,28,0.14),hop(t,12.0+0.17*(2-k),0.48,28,0.14))
        env=cyc(t,5.6,9.7)
        m=add(m,dict(dy=-8*env*max(0,math.sin(TAU*(t/1.25)+math.pi*k))))
        env2=cyc(t,16.2,19.6)
        m=add(m,dict(rot=5*env2*math.sin(TAU*t/1.25+math.pi*k)))
        m=add(m,dict(sy=1+spring(t,14.1,0.9,-0.10),sx=1+spring(t,14.1,0.9,0.07)))
        put([i],m,bottom_center([i]))
    for k,i in enumerate(G['dash']):
        s=1+spring(t,0.95+0.51*k,0.6,0.45)+spring(t,12.0+0.51*(1-k),0.6,0.45)
        put([i],dict(dx=0,dy=0,rot=0,sx=s,sy=1),center([i]))
    # 먹 자 웨 이 (outline+fill move together)
    for k,idx in enumerate(MK):
        sgn=1 if k%2==0 else -1
        m=add(hop(t,1.90+0.20*k,0.56,42,0.16,tilt=6*sgn),hop(t,10.95+0.20*(3-k),0.56,46,0.16,tilt=-7*sgn))
        env=cyc(t,5.6,9.7)
        m=add(m,dict(rot=6*env*math.sin(TAU*t/1.25)*sgn))
        m=add(m,dict(sy=1+spring(t,14.0,0.9,-0.13),sx=1+spring(t,14.0,0.9,0.09)))
        # dance B: alternate bounces on the beat
        env2=cyc(t,16.2,19.6)
        if env2>0:
            ph=((t/BEAT)+(0 if k%2==0 else 1))%2
            if ph<1:
                kk=math.sin(math.pi*ph); m=add(m,dict(dy=-18*env2*kk,sy=1+0.05*env2*kk,sx=1-0.03*env2*kk))
        put(idx,m,bottom_center(idx))
    # band + 야(夜)장축제
    bm=dict(rot=spring(t,3.05,1.3,2.6,2)+spring(t,12.85,1.3,-2.6,2))
    put(G['band'],add(bm),center(G['band']))
    cb=center(G['band']); Mb=aff(0,0,bm['rot'],1,1,*cb)
    nb=len(G['bc'])
    for k,i in enumerate(G['bc']):
        s=1+spring(t,3.05+0.09*k,0.5,0.34)+spring(t,12.85+0.09*(nb-1-k),0.5,0.34)
        env=cyc(t,5.6,9.7)+cyc(t,16.2,19.6)
        dy=-5*env*math.sin(TAU*(t/1.25-k/nb))
        cx,cy=center([i]); mats[i]=Mb@aff(0,dy,0,s,s,cx,cy)
    # whole-logo pop
    gs=1+spring(t,4.3,0.8,0.08)+spring(t,15.0,0.8,0.08)
    Mg=aff(0,0,0,gs,gs,TCX,TCY)
    for i in mats: mats[i]=Mg@mats[i]
    return mats
# ---------------- bulbs
bx,by,br=bulbs[:,0],bulbs[:,1],bulbs[:,2]
bph=rng.uniform(0,1,len(bulbs)); bpar=np.array([(int(x//55))%2 for x in bx])
def bulb_level(t):
    A_=0.5+0.5*np.cos(TAU*(t/1.25-bx/520)); A_=A_**1.6
    B_=0.5+0.5*np.tanh(3.2*np.cos(TAU*t/1.25+math.pi*bpar))
    C_=0.5+0.5*np.cos(TAU*(t/1.25+bx/520)); C_=C_**1.6
    D_=0.5+0.5*np.cos(TAU*(t/(2.5)+bph)); D_=D_**2
    w=np.array([cyc(t,19.8,5.2,0.4),cyc(t,4.8,10.2,0.4),cyc(t,9.8,15.2,0.4),cyc(t,14.8,20.2,0.4)])
    w=w/w.sum()
    return w[0]*A_+w[1]*B_+w[2]*C_+w[3]*D_
GLOW={}
def glow_sprite(r):
    k=round(r*2)/2
    if k not in GLOW:
        R=int(math.ceil(k*4.2+4)); yy,xx=np.mgrid[-R:R+1,-R:R+1]; d=np.hypot(xx,yy)
        g=0.65*np.exp(-(d/(1.25*k+1))**2)+0.35*np.exp(-(d/(2.8*k+3))**2)
        core=np.clip((k+1.2-d)/1.6,0,1)
        GLOW[k]=(g.astype(np.float32),core.astype(np.float32),R)
    return GLOW[k]
WARM=np.array([255,214,140],np.float32)
DIMK=np.array([0.30,0.42,0.62],np.float32)  # off = deeper amber, not grey
def bulbs_fx(fr,t):
    lv=bulb_level(t)
    for (x,y,r),b in zip(bulbs,lv):
        g,core,R=glow_sprite(r); xi,yi=int(round(x)),int(round(y))
        y0,y1,x0,x1=yi-R,yi+R+1,xi-R,xi+R+1
        gy0,gx0=max(0,-y0),max(0,-x0); y0c,x0c=max(0,y0),max(0,x0); y1c,x1c=min(H,y1),min(W,x1)
        gs=g[gy0:gy0+y1c-y0c,gx0:gx0+x1c-x0c]; cs=core[gy0:gy0+y1c-y0c,gx0:gx0+x1c-x0c]
        reg=fr[y0c:y1c,x0c:x1c]
        reg*=1-((1-b)*cs)[...,None]*DIMK
        reg+=(gs*(150*b))[...,None]*WARM/255
# ---------------- windows
wph=rng.uniform(0,DUR,NWIN+1); wdur=rng.choice([1.25,2.5,3.75,5.0],NWIN+1); woff=rng.random(NWIN+1)<0.55
wph2=rng.uniform(0,DUR,NWIN+1); wtw=rng.random(NWIN+1)<0.15
def win_alpha(t):
    lut=np.ones(NWIN+1,np.float32)
    for i in range(1,NWIN+1):
        v=1.0
        if woff[i]:
            d=(t-wph[i])%DUR
            if d<wdur[i]: v=1-sm(d/0.06)*sm((wdur[i]-d)/0.06)
        if woff[i] and wdur[i]<=2.5:
            d=(t-wph2[i])%DUR
            if d<wdur[i]: v*=1-sm(d/0.06)*sm((wdur[i]-d)/0.06)
        if wtw[i]: v*=0.75+0.25*math.cos(TAU*t/0.625*2+wph[i])
        lut[i]=v
    lut[0]=1
    return lut
# ---------------- sky sparkles
SKYC=np.array([6,62,41]); pa=np.asarray(plate).astype(int)
cand=[]; tries=0
while len(cand)<22 and tries<20000:
    tries+=1
    x=rng.uniform(30,W-30); y=rng.uniform(16,175)
    if 900<x<1660 and y>40: continue
    if (x<420 and y<260) or (x>2120 and y<300): continue   # badges
    if abs(x-1918)<70 and y<120: continue                  # moon
    if abs(x-735)<70 and y<110: continue                   # big star
    reg=pa[int(y)-14:int(y)+14,int(x)-14:int(x)+14]
    if np.abs(reg-SKYC).sum(2).max()>110: continue
    if any(math.hypot(x-a,y-b)<110 for a,b,*_ in cand): continue
    cand.append((x,y,rng.uniform(14,30),rng.choice([2.5,5.0]),rng.uniform(0,5),rng.choice([-1,1])))
def sparkle(dst,x,y,size,rot,alpha=1.0):
    if size<1.5: return
    im=star2.resize((max(2,round(size*star2.width/star2.height)),max(2,round(size))),Image.LANCZOS)
    if rot: im=im.rotate(rot,Image.BICUBIC,expand=True)
    if alpha<1: im.putalpha(im.getchannel('A').point(lambda v:int(v*alpha)))
    dst.alpha_composite(im,(int(round(x-im.width/2)),int(round(y-im.height/2))))
# glow sprite for sky elements
def soft_glow(r,col,a):
    R=int(r*2.2); yy,xx=np.mgrid[-R:R+1,-R:R+1]; d=np.hypot(xx,yy)
    g=np.exp(-(d/r)**2)*a
    im=np.zeros((2*R+1,2*R+1,4),np.uint8); im[...,:3]=col; im[...,3]=np.clip(g*255,0,255)
    return Image.fromarray(im,'RGBA')
MOONGLOW=soft_glow(70,(250,226,160),0.45)
# burst sparkles (logo pops at 4.3 and 15.0)
bursts=[]
for t0 in (4.3,15.0):
    for j in range(20):
        ang=TAU*j/20+rng.uniform(-0.15,0.15)
        ex,ey=abs(math.cos(ang))*330,abs(math.sin(ang))*310
        sx_=TCX+math.cos(ang)*330; sy_=TCY+math.sin(ang)*300
        bursts.append((t0+rng.uniform(0,0.12),sx_,sy_,ang,rng.uniform(100,200),rng.uniform(26,46)))
# ---------------- music notes from the guitar
try: NF_=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',64)
except Exception: NF_=None
NOTES={}
def note_img(ch):
    if ch not in NOTES:
        im=Image.new('RGBA',(110,110),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.text((55,58),ch,font=NF_,fill=(250,236,206,255),anchor='mm',stroke_width=5,stroke_fill=(16,58,40,255))
        NOTES[ch]=im.crop(im.getbbox())
    return NOTES[ch]
NOTE_SRC=(BK[0]+176,BK[1]+88)  # guitar headstock, clear of his face
# ---------------- frame
def frame(i):
    t=i/FPS
    if REST: t=-1  # sentinel
    fr=plate.copy().convert('RGBA')
    # windows
    if REST: fr.alpha_composite(win)
    else:
        lut=win_alpha(t); sub=win_np[:WY1].copy()
        sub[...,3]=(sub[...,3]*lut[win_lab[:WY1]]).astype(np.uint8)
        fr.alpha_composite(Image.fromarray(sub,'RGBA'),(0,0))
    # sky: moon, big star, sparkles
    if REST:
        mo=moon2.resize((round(moon2.width/2),78),Image.LANCZOS); fr.alpha_composite(mo,(1890,22))
        st=star2.resize((round(star2.width/2),70),Image.LANCZOS); fr.alpha_composite(st,(700,18))
    else:
        mw,mh=round(moon2.width/2),78; mcx,mcy=1890+mw/2,22+mh/2
        ga=0.75+0.25*math.cos(TAU*t/2.5)
        g=MOONGLOW.copy(); g.putalpha(g.getchannel('A').point(lambda v:int(v*ga)))
        fr.alpha_composite(g,(int(mcx-g.width/2),int(mcy-g.height/2)))
        mo=moon2.resize((mw,mh),Image.LANCZOS)
        place(fr,mo,1890,22,aff(0,3*math.sin(TAU*t/5),9*math.sin(TAU*t/5+0.6),1,1,mcx,mcy))
        sw,sh_=round(star2.width/2),70; scx,scy=700+sw/2,18+sh_/2
        ps=1+0.22*(0.5+0.5*math.cos(TAU*t/1.25))
        g=soft_glow(26,(255,240,190),0.35*ps); fr.alpha_composite(g,(int(scx-g.width/2),int(scy-g.height/2)))
        st=star2.resize((sw,sh_),Image.LANCZOS)
        place(fr,st,700,18,aff(0,0,-360*t/10,ps,ps,scx,scy))
        for (x,y,sz,per,ph,dr) in cand:
            u=((t+ph)%per)/1.1
            if u<1:
                k=math.sin(math.pi*u)**1.4; sparkle(fr,x,y,sz*k,dr*90*u,1.0)
    # bulbs (dim + glow) in float
    if not REST:
        a=np.asarray(fr.convert('RGB')).astype(np.float32)
        bulbs_fx(a,t)
        fr=Image.fromarray(np.clip(a,0,255).astype(np.uint8)).convert('RGBA')
    # busker groove + notes
    if REST: fr.alpha_composite(busker,BK)
    else:
        fx,fy=BK[0]+117,BK[1]+278
        sq=1-0.022*(0.5+0.5*math.cos(TAU*t/BEAT))
        place(fr,busker,*BK,aff(0,0,2.4*math.sin(TAU*t/1.25),1+0.4*(1-sq),sq,fx,fy))
    fr.alpha_composite(monitor,MON)
    if not REST:
        for k in range(32):
            age=(t-k*BEAT)%DUR
            if age<2.5 and k%2==0 or age<2.2 and k%4==1:
                u=age/2.5; ch='♪' if k%3 else '♫'
                im=note_img(ch); sc=0.62+0.5*sm(u/0.3)
                sway=14*math.sin(TAU*(u*1.6)+k)
                x=NOTE_SRC[0]+28*u+sway+(k%5)*5-10; y=NOTE_SRC[1]-200*u-(k%3)*8
                al=sm(u/0.12)*sm((1-u)/0.35)
                im=im.resize((max(2,round(im.width*sc)),max(2,round(im.height*sc))),Image.LANCZOS)
                im=im.rotate(16*math.sin(TAU*u*1.3+k),Image.BICUBIC,expand=True)
                im.putalpha(im.getchannel('A').point(lambda v,al=al:int(v*al)))
                fr.alpha_composite(im,(int(x-im.width/2),int(y-im.height/2)))
    # couple strolling
    if REST: fr.alpha_composite(couple,CP)
    else:
        fx,fy=CP[0]+170,CP[1]+515
        step=abs(math.sin(math.pi*t/BEAT))
        place(fr,couple,*CP,aff(3.5*math.sin(TAU*t/1.25),-5*step,1.3*math.sin(TAU*t/1.25),1,1,fx,fy))
    # title
    fr.alpha_composite(tshadow)
    tl=Image.new('RGBA',(TX1-TX0,TY1-TY0),(0,0,0,0))
    mats={} if REST else title_mats(t)
    for idx,p in enumerate(TM):
        place(tl,p['img'],p['X'],p['Y'],mats.get(idx,I3),TX0,TY0)
    if not REST:
        for t0 in (4.45,15.15):
            u=dt(t,t0)/1.0
            if 0<=u<1:
                ta=np.asarray(tl).astype(np.float32)
                yy,xx=np.mgrid[0:tl.height,0:tl.width]
                xs=(TX0-40)+u*(TX1-TX0+80)
                d=(xx+TX0)-xs+(yy+TY0-TCY)*0.38
                band=np.exp(-(d/40)**2)*0.75+np.exp(-(d/120)**2)*0.18
                ta[...,:3]+=band[...,None]*np.array([255,246,225])*(ta[...,3:]/255)
                tl=Image.fromarray(np.clip(ta,0,255).astype(np.uint8),'RGBA')
    fr.alpha_composite(tl,(TX0,TY0))
    # burst sparkles
    if not REST:
        for (t0,x0,y0,ang,dist,sz) in bursts:
            u=dt(t,t0)/0.95
            if 0<=u<1:
                e=1-(1-u)**3
                sparkle(fr,x0+math.cos(ang)*dist*e,y0+math.sin(ang)*dist*e,sz*math.sin(math.pi*min(1,u*1.3))**0.8,200*u,1.0)
    # badges: hang from top-centre and swing, opposite phases, pop now and then
    for nm,xy,base,ph,pops in (('ob',(55,71),-4,0.0,(2.5,12.5)),('fb',(2151,70),4,math.pi,(7.5,17.5))):
        b=badge[nm]; P=30; bw,bh=b.width-2*P,b.height-2*P
        # v4 placed the rotated(expand) badge at xy: its centre is xy + rotated size/2
        c,s=math.cos(math.radians(base)),math.sin(math.radians(base))
        rw=abs(bw*c)+abs(bh*s); rh=abs(bw*s)+abs(bh*c)
        cx,cy=xy[0]+rw/2,xy[1]+rh/2
        X,Y=round(cx-b.width/2),round(cy-b.height/2)
        if REST:
            place(fr,b,X,Y,aff(0,0,base,1,1,cx,cy)); continue
        sw=8*math.sin(TAU*t/2.5+ph)
        sp=1+sum(spring(t,p0,0.7,0.16) for p0 in pops)
        # pivot = top centre of the badge in its rest pose
        px,py=cx-s*(-bh/2)*0+(-math.sin(math.radians(base))*(-bh/2)), cy+(-bh/2)*c
        M=aff(0,0,sw,sp,sp,px,py)@aff(0,0,base,1,1,cx,cy)
        place(fr,b,X,Y,M)
    return fr.convert('RGB')
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='still':
        for a in sys.argv[3:]:
            t=float(a); frame(round(t*FPS)).save(f'{sys.argv[2]}_{a}.png')
    elif mode=='rest':
        frame(0).save(sys.argv[2])
    elif mode=='pipe':
        # frames [a,b) as raw rgb24 to stdout, parallel
        from multiprocessing import Pool
        a,b=int(sys.argv[2]),int(sys.argv[3]); nw=int(os.environ.get('NW','4'))
        out=sys.stdout.buffer
        with Pool(nw) as pool:
            for im in pool.imap(frame,range(a,b),chunksize=2):
                out.write(im.tobytes())
