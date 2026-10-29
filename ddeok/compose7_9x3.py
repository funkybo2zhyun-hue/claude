import sys,numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typo2 import font,tlayer,outlined,pad_img,PLUM,GOLD,CREAM
OUT=sys.argv[1]
W,H=2304,768
coefs=np.load('bgcoef.npy')
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
def bg_at(px,py): return np.stack([F(px,py)@c for c in coefs],-1)
cy,cx=np.mgrid[0:H,0:W].astype(float)
# poster gradient mapped vertically (poster y 150..600), gentle horizontal symmetry
ppx=330+np.abs(cx-1152)/1152*200; ppy=150+cy/H*430
img=bg_at(ppx,ppy)
d=np.clip(np.abs(cx-1152)/1152,0,1)
img*=(1-0.28*d**1.6)[...,None]
img*=(1-0.18*np.clip(1-cy/320,0,1))[...,None]
# warm glows behind the two stages and behind the title
for gx,gy,rx,ry,c in [(400,640,520,300,(40,22,14)),(1950,640,540,320,(40,22,14)),(1152,330,640,300,(26,14,24))]:
    rr=np.sqrt(((cx-gx)/rx)**2+((cy-gy)/ry)**2); img+=np.exp(-rr**2*1.4)[...,None]*np.array(c,float)
im=Image.fromarray(np.clip(img,0,255).astype('uint8')).convert('RGBA')
PU=np.asarray(Image.open('poster_up.png').convert('RGB')).astype(float)
SU=Image.open('scene_up.png').convert('RGB')
def lantern(box,cxp,cyp,size,blur=0,fade_=1.0):
    global im
    x0,y0,x1,y1=[v*4 for v in box]
    patch=PU[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
    r=patch-bg_at(xx/4,yy/4)
    a=np.clip((np.abs(r).max(2)-12)/30,0,1)
    e=np.minimum(np.minimum(xx-x0,x1-1-xx),np.minimum(yy-y0,y1-1-yy))/12; a*=np.clip(e,0,1)
    w=size; h=size*(y1-y0)/(x1-x0)
    L=Image.fromarray(np.dstack([np.clip(patch,0,255),a*255*fade_]).astype('uint8')).resize((max(1,round(w)),max(1,round(h))),Image.LANCZOS)
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G); R=size*0.9
    gd.ellipse((cxp-R,cyp-R*0.6,cxp+R,cyp+R*1.2),fill=(255,150,70,int(70*fade_)))
    im.alpha_composite(G.filter(ImageFilter.GaussianBlur(size*0.45)))
    im.alpha_composite(L,(round(cxp-w/2),round(cyp-h/2)))
YEL=(498,70,552,128); RS=(511,264,537,294); RB=(521,320,558,362); RL=(150,250,206,310)
# moon (from scene crop, poster x 420..500 => crop 342..422, y 5..85)
def moon(cxp,cyp,diam):
    global im
    m=SU.crop((330*4,0,434*4,98*4)); arr=np.asarray(m).astype(float)
    yy,xx=np.mgrid[0:arr.shape[0],0:arr.shape[1]].astype(float)
    ccx,ccy,R=382*4-330*4,45*4,40*4
    rr=np.sqrt((xx-ccx)**2+(yy-ccy)**2)
    a=np.clip((R+3-rr)/4,0,1)
    M=Image.fromarray(np.dstack([arr,a*255]).astype('uint8'))
    sc=diam/(2*R); M=M.resize((round(M.width*sc),round(M.height*sc)),Image.LANCZOS)
    G=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(G).ellipse((cxp-diam*0.75,cyp-diam*0.75,cxp+diam*0.75,cyp+diam*0.75),fill=(255,190,110,90))
    im.alpha_composite(G.filter(ImageFilter.GaussianBlur(diam*0.3)))
    im.alpha_composite(M,(round(cxp-ccx*sc),round(cyp-ccy*sc)))
moon(250,150,175)
rng0=np.random.default_rng(11)
LAN=[(YEL,2224,330,40,0.6,0.85),(RB,700,330,52,0,1),(RB,1644,300,50,0,1),(YEL,1974,330,46,0,1),(RS,880,250,30,0,0.9),(RS,60,420,34,1,0.75),(RS,1464,240,30,0,0.9),(RS,2244,420,30,1,0.7),(RL,872,110,40,1.2,0.7),(RS,1432,110,26,1.5,0.6),(RS,330,330,24,1.5,0.6),(RS,992,300,22,2,0.5),(RS,1322,290,22,2,0.5),(RB,560,200,30,1.2,0.7),(RS,1794,200,26,1.5,0.6),(RS,2144,300,24,1.5,0.6),(RS,1092,40,20,2,0.45),(RS,1232,60,18,2,0.45),(RS,250,120,22,2,0.5),(RS,1864,60,22,2,0.5)]
for b,x,y,sz,bl,fa in LAN:
    lantern(b,x,y,sz,bl,fa)
# sparkles
rng=np.random.default_rng(5)
G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G)
for i in range(220):
    x=rng.uniform(0,W); y=rng.uniform(0,H*0.75); r=rng.uniform(1,3)
    gd.ellipse((x-r,y-r,x+r,y+r),fill=(255,230,205,int(rng.uniform(60,180))))
im.alpha_composite(G.filter(ImageFilter.GaussianBlur(1.2)))

# ---------- skyline (poster's flat buildings with lit windows), two depths
def skyline(seed,base,hmin,hmax,col,win,wa,alpha,blur,dim_center):
    global im
    r=np.random.default_rng(seed)
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    x=-40
    while x<W+40:
        bw=int(r.uniform(70,170)); cxm=x+bw/2
        k=1-dim_center*np.exp(-((cxm-1152)/400)**2)
        bh=int(r.uniform(hmin,hmax)*k)
        y0=base-bh
        d.rectangle((x,y0,x+bw,base+200),fill=col+(255,))
        if r.random()<0.35: d.rectangle((x+bw*0.3,y0-int(r.uniform(20,50)),x+bw*0.42,y0),fill=col+(255,))
        for wy in range(y0+16,base,int(win*2.6)):
            for wx in range(int(x+12),int(x+bw-12),int(win*2.2)):
                if r.random()<0.42:
                    d.rectangle((wx,wy,wx+win,wy+int(win*1.4)),fill=(255,206,110,int(wa*(0.35+0.65*k))))
        x+=bw+int(r.uniform(-10,14))
    a=np.asarray(L.split()[3]).astype(float)*alpha
    L.putalpha(Image.fromarray(a.astype('uint8')))
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    G=Image.new('RGBA',(W,H),(0,0,0,0)); G.alpha_composite(L)
    im.alpha_composite(G)
skyline(3,600,200,330,(92,72,104),6,150,0.55,1.6,0.7)
skyline(7,640,150,260,(58,46,66),7,235,0.92,0,0.8)
# warm haze at the skyline foot so it reads as a lit market street
cy2,cx2=np.mgrid[0:H,0:W].astype(float)
hz=np.exp(-((cy2-600)/70)**2)*0.35
Hz=np.dstack([np.full((H,W),255),np.full((H,W),170),np.full((H,W),120),hz*255]).astype('uint8')
im.alpha_composite(Image.fromarray(Hz))
# ---------- lantern garlands (poster's hanging lanterns)
HL=None
def hl_sprite():
    S=np.asarray(SU).astype(float); p=S[540:665,1560:1625]; R,G_,B=p[...,0],p[...,1],p[...,2]
    a=np.clip(((R-B)-55)/30,0,1)*np.clip((R-150)/40,0,1)
    return Image.fromarray(np.dstack([p,a*255]).astype('uint8'))
HL=hl_sprite()
def garland(p0,p1,sag,n,size,blur=0,fade_=1.0,swing=0):
    global im
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    ts=np.linspace(0,1,200)
    def pt(t): return (p0[0]+(p1[0]-p0[0])*t, p0[1]+(p1[1]-p0[1])*t+sag*4*t*(1-t))
    pts=[pt(t) for t in ts]
    d.line(pts,fill=(70,40,60,int(230*fade_)),width=max(2,int(size/16)))
    Gl=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(Gl)
    sprites=[]
    for i in range(n):
        t=(i+0.5)/n; x,y=pt(t)
        drop=size*0.35
        d.line([(x,y),(x,y+drop)],fill=(70,40,60,int(230*fade_)),width=2)
        h=size*HL.height/HL.width
        s=HL.resize((round(size),round(h)),Image.LANCZOS)
        ang=np.sin(i*1.7)*swing
        if ang: s=s.rotate(ang,resample=Image.BICUBIC,expand=True)
        if fade_<1:
            a=np.asarray(s.split()[3]).astype(float)*fade_; s.putalpha(Image.fromarray(a.astype('uint8')))
        sprites.append((s,x,y+drop))
        R=size*1.1; gd.ellipse((x-R,y+drop+h*0.5-R,x+R,y+drop+h*0.5+R),fill=(255,190,100,int(95*fade_)))
    im.alpha_composite(Gl.filter(ImageFilter.GaussianBlur(size*0.6)))
    for s,x,y in sprites: L.alpha_composite(s,(round(x-s.width/2),round(y-2)))
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(L)
garland((-40,150),(640,95),70,7,26,blur=1.0,fade_=0.75,swing=4)
garland((1664,95),(2344,150),70,7,26,blur=1.0,fade_=0.75,swing=4)
garland((-40,10),(880,40),150,8,40,swing=5)
garland((1424,40),(2344,10),150,8,40,swing=5)
# ---------- stages
disc=Image.open('disc_clean.png')
DCX,DCY=243*4,321*4  # disc centre in scene_up px; disc_clean origin offset:
DOX,DOY=int((243-223)*4)-4,int((321-119)*4)-4
G4={'L1':(108,138),'L2':(36,100),'R1':(138,52),'R2':(248,240)}
def stage(names,ocx,ocy,canvas_cx,canvas_cy,sc,dsx,dsy,dy={},dx={},pre=[]):
    """ocx,ocy: scene_up px of the point that should sit on disc centre"""
    global im
    dw=round(disc.width*dsx); dh=round(disc.height*dsy)
    D=disc.resize((dw,dh),Image.LANCZOS)
    im.alpha_composite(D,(round(canvas_cx-(DCX-DOX)*dsx),round(canvas_cy-(DCY-DOY)*dsy)))
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    for pim,px,py in pre: layer.alpha_composite(pim,(px,py))
    for n in names:
        g=Image.open(f'g_{n}_birefnet-general.png')
        if n=='L2':  # drop the duplicated rabbit ear at the right edge
            a=np.asarray(g.split()[3]).copy(); a[:, (119-36)*4+20:]=0; g.putalpha(Image.fromarray(a))
        gx,gy=G4[n][0]*4,G4[n][1]*4
        g=g.resize((round(g.width*sc),round(g.height*sc)),Image.LANCZOS)
        layer.alpha_composite(g,(round(canvas_cx+(gx-ocx)*sc)+dx.get(n,0),round(canvas_cy+(gy-ocy)*sc)+dy.get(n,0)))
    # contact shadow
    a=layer.split()[3]
    sh=Image.new('RGBA',(W,H),(120,60,50,0)); sh.putalpha(a.point(lambda v:int(v*0.45)))
    sh=sh.filter(ImageFilter.GaussianBlur(10))
    im.alpha_composite(sh,(6,10)); im.alpha_composite(layer)
SC=0.5
# left: cluster centre x≈150 crop, base row ≈ 340 crop placed slightly behind disc centre
stage([],0,0,1152,790,1,1.5,0.42)
from PIL import ImageOps
_g=Image.open('g_L2_birefnet-general.png'); _a=np.asarray(_g.split()[3]).copy(); _a[:, (119-36)*4:]=0; _g.putalpha(Image.fromarray(_a))
_g=ImageOps.mirror(_g); _s=0.8; _g=_g.resize((round(_g.width*_s),round(_g.height*_s)),Image.LANCZOS)
_cut=round((456-(119-36)*4)*_s)
stage(['L1'],150*4,343*4,520,760,0.74,0.82,0.5,dx={'L1':-180},pre=[(_g,-_cut-10,640-_g.height)])
stage(['R1','R2'],292*4,346*4,1800,760,0.68,0.82,0.5,dy={'R1':100},dx={'R1':215,'R2':-110})
# ---------- centred title block (v4: 3D lettering, no tagline)
import title3d
CXT=1152
T=Image.open('title_hi.png'); tw=960; th=round(T.height*tw/T.width); T=T.resize((tw,th),Image.LANCZOS)
T=T.crop(T.getbbox()); tw,th=T.size
T3,pad=title3d.make(T,depth=14,outline=0)
import os
HF=os.environ.get('HF','BlackHanSans-Regular.ttf'); HS=int(os.environ.get('HS','70')); HP=os.environ.get('HP','0')=='1'
f=font(HF,HS)
L,w,h,p=tlayer('2026 문창 떡 축제',f,(255,255,255,255),spacing=4)
Hd=L.crop(L.getbbox())
if HP:  # pink 떡 like the main logo accents
    arr=np.asarray(Hd).copy()
    x0=int(f.getlength('2026 문창 ')+4*8)-4; x1=int(f.getlength('2026 문창 떡')+4*9)+4
    pk=arr[:,x0:x1]; pk[...,0]=250; pk[...,1]=120; pk[...,2]=155
    Hd=Image.fromarray(arr)
H3,hpad=title3d.make(Hd,depth=8,outline=0)
hw,hh=Hd.size; gap=34
total=hh+gap+th+14
by0=(H-total)//2-4
im.alpha_composite(H3,(CXT-hw//2-hpad,by0-hpad))
ty=by0+hh+gap
im.alpha_composite(T3,(CXT-tw//2-pad,ty-pad))
im.convert('RGB').save(OUT); print('ok',by0,ty+th)
