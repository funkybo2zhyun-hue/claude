import sys,numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typo2 import font,tlayer,outlined,pad_img,PLUM,GOLD,CREAM
OUT=sys.argv[1]
W,H=2560,768
coefs=np.load('bgcoef.npy')
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
def bg_at(px,py): return np.stack([F(px,py)@c for c in coefs],-1)
cy,cx=np.mgrid[0:H,0:W].astype(float)
# poster gradient mapped vertically (poster y 150..600), gentle horizontal symmetry
ppx=330+np.abs(cx-1280)/1280*200; ppy=150+cy/H*430
img=bg_at(ppx,ppy)
d=np.clip(np.abs(cx-1280)/1280,0,1)
img*=(1-0.28*d**1.6)[...,None]
img*=(1-0.18*np.clip(1-cy/320,0,1))[...,None]
# warm glows behind the two stages and behind the title
for gx,gy,rx,ry,c in [(400,640,520,300,(40,22,14)),(2185,640,560,320,(40,22,14)),(1280,330,700,300,(26,14,24))]:
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
moon(2440,120,150)
for b,x,y,sz,bl,fa in [
 (YEL,120,110,62,0,1),(RB,640,90,50,0,1),(RS,760,300,30,0,0.9),(RS,40,380,34,1,0.75),(RS,330,40,26,1,0.7),
 (RB,1880,120,46,0,1),(RS,2250,60,28,1,0.8),(RS,1820,330,28,0,0.9),(RS,2530,330,30,1,0.7),(RS,1000,700,28,1,0.6),(RS,1560,705,28,1,0.6),(RL,960,60,40,1.5,0.6),(RS,1600,40,24,1.5,0.6)]:
    lantern(b,x,y,sz,bl,fa)
# sparkles
rng=np.random.default_rng(5)
G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G)
for i in range(130):
    x=rng.uniform(0,W); y=rng.uniform(0,H*0.75); r=rng.uniform(1,3)
    gd.ellipse((x-r,y-r,x+r,y+r),fill=(255,230,205,int(rng.uniform(60,180))))
im.alpha_composite(G.filter(ImageFilter.GaussianBlur(1.2)))
# ---------- stages
disc=Image.open('disc_clean.png')
DCX,DCY=243*4,321*4  # disc centre in scene_up px; disc_clean origin offset:
DOX,DOY=int((243-223)*4)-4,int((321-119)*4)-4
G4={'L1':(108,138),'L2':(36,100),'R1':(138,52),'R2':(248,240)}
def stage(names,ocx,ocy,canvas_cx,canvas_cy,sc,dsx,dsy,dy={},dx={}):
    """ocx,ocy: scene_up px of the point that should sit on disc centre"""
    global im
    dw=round(disc.width*dsx); dh=round(disc.height*dsy)
    D=disc.resize((dw,dh),Image.LANCZOS)
    im.alpha_composite(D,(round(canvas_cx-(DCX-DOX)*dsx),round(canvas_cy-(DCY-DOY)*dsy)))
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    for n in names:
        g=Image.open(f'g_{n}_birefnet-general.png')
        if n=='L2':  # drop the duplicated rabbit ear at the right edge
            a=np.asarray(g.split()[3]).copy(); a[:, (119-36)*4:]=0; g.putalpha(Image.fromarray(a))
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
stage(['L2','L1'],150*4,343*4,420,738,0.68,0.46,0.42,dy={'L2':85},dx={'L2':50,'L1':50})
stage(['R1','R2'],292*4,346*4,2185,738,0.58,0.46,0.42,dy={'R1':95},dx={'R1':70,'R2':-250})
# ---------- centred title block (v4: 3D lettering, no tagline)
import title3d
CXT=1280
T=Image.open('title_hi.png'); tw=1110; th=round(T.height*tw/T.width); T=T.resize((tw,th),Image.LANCZOS)
T=T.crop(T.getbbox()); tw,th=T.size
T3,pad=title3d.make(T,depth=14,outline=4)
f=font('NanumMyeongjo-ExtraBold.ttf',56)
L,w,h,p=tlayer('2026 문창 떡 축제',f,CREAM+(255,),spacing=3)
ph=h+34; gap=30
total=ph+gap+th+14
by0=(H-total)//2-6; bx0=CXT-(w+64)//2; bx1=bx0+w+64; by1=by0+ph
R=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(R).rounded_rectangle((bx0,by0,bx1,by1),radius=ph//2,fill=PLUM+(205,),outline=GOLD+(255,),width=3)
im.alpha_composite(R); im.alpha_composite(L,(bx0+32-p,by0+17-p))
ty=by1+gap
im.alpha_composite(T3,(CXT-tw//2-pad,ty-pad))
im.convert('RGB').save(OUT); print('ok',by0,ty+th)
