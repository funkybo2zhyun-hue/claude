import sys,numpy as np
from PIL import Image, ImageDraw, ImageFilter
import typo2
OUT=sys.argv[1]
W,H=2560,768
coefs=np.load('bgcoef.npy')
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
def bg_at(px,py):
    return np.stack([F(px,py)@c for c in coefs],-1)
PU=np.asarray(Image.open('poster_up.png').convert('RGB')).astype(float)
s=1.80            # canvas px per poster px for the hero
SCX=1400          # canvas x of poster x=330
PY_TOP=172        # poster y at canvas y=0
cy,cx=np.mgrid[0:H,0:W].astype(float)
# background: gradient evaluated with gentle horizontal clamp
ppx=np.clip((cx-SCX)/s*0.55+330,0,596); ppy=np.minimum(cy/s+PY_TOP,630)
img=bg_at(ppx,ppy)
# deepen top & sides into night sky
d=np.clip(np.abs(cx-SCX)/1250,0,1)
img*=(1-0.45*d**1.4)[...,None]
img*=(1-0.25*np.clip(1-cy/380,0,1))[...,None]
# moon-side warm halo behind hero
rr=np.sqrt(((cx-SCX)/600)**2+((cy-520)/360)**2)
img+=np.exp(-rr**2*1.5)[...,None]*np.array([46,26,16.])
im=Image.fromarray(np.clip(img,0,255).astype('uint8')).convert('RGBA')
# ---------- distant skyline silhouettes (flat, poster style)
rng=np.random.default_rng(3)
def skyline(y_base,hmin,hmax,col,win,alpha,seed,blur=0):
    r=np.random.default_rng(seed)
    L=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L)
    x=-20
    while x<W:
        bw=int(r.uniform(60,150)); bh=int(r.uniform(hmin,hmax))
        x0,y0=x,y_base-bh
        dr.rectangle((x0,y0,x0+bw,H),fill=col+(alpha,))
        if r.random()<0.3: dr.rectangle((x0+bw*0.35,y0-r.uniform(12,30),x0+bw*0.45,y0),fill=col+(alpha,))
        for wy in range(int(y0+16),H,26):
            for wx in range(int(x0+12),int(x0+bw-12),22):
                if r.random()<0.16: dr.rectangle((wx,wy,wx+5,wy+8),fill=win+(int(alpha*r.uniform(0.35,0.8)),))
        x+=bw+int(r.uniform(-10,8))
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    return L
far=skyline(590,40,150,(74,60,106),(255,214,150),120,1,blur=1.5)
near=skyline(690,60,190,(34,26,56),(255,200,120),225,2)
# fade skylines under text zones a little & keep hero clear
def fade(L,keep):
    a=np.asarray(L.split()[3]).astype(float)*keep
    L.putalpha(Image.fromarray(a.astype('uint8'))); return L
keep=np.clip(np.abs(cx-SCX)/520,0,1)**1.5
import os
if not os.environ.get('NOSKY'):
    im.alpha_composite(fade(far,0.55+0.45*keep))
    im.alpha_composite(fade(near,keep))
# ground haze over skyline bottom
haze=np.clip((cy-560)/200,0,1)**1.2
Hz=Image.fromarray(np.dstack([np.full((H,W),150),np.full((H,W),85),np.full((H,W),95),(haze*170)]).astype('uint8'))
im.alpha_composite(Hz)
# ---------- hero scene residual from upscaled poster
CX0,CY0,CX1,CY1=78,180,596,600
crop=Image.open('scene_up.png').convert('RGB')     # covers poster 78..596 x 180..625
cw=round((596-78)*s); chh=round((625-180)*s)
crop=np.asarray(crop.resize((cw,chh),Image.LANCZOS)).astype(float)
ox=round(SCX+(78-330)*s); oy=round((180-PY_TOP)*s)
yy,xx=np.mgrid[0:chh,0:cw].astype(float)
px=xx/s+78; py=yy/s+180
res=crop-bg_at(px,py)
obj=np.clip((np.abs(res).max(2)-14)/20,0,1)
obj=np.asarray(Image.fromarray((obj*255).astype('uint8')).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(5))).astype(float)/255
edge=np.clip(np.minimum.reduce([xx/(8*s),(cw-1-xx)/(8*s),yy/(3*s)]),0,1)
wt=obj*edge; wt=wt*wt*(3-2*wt)
# composite: alpha blend crop over current canvas using wt
base=np.asarray(im).astype(float)
y0=oy; y1=min(H,oy+chh); x0=ox; x1=ox+cw
sub=base[y0:y1,x0:x1,:3]
a=wt[:y1-y0,:,None]
base[y0:y1,x0:x1,:3]=sub*(1-a)+crop[:y1-y0]*a
im=Image.fromarray(np.clip(base,0,255).astype('uint8'))
# ---------- sky lanterns from upscaled poster
def lantern(box,cxp,cyp,size,blur=0,fade_=1.0,glow=True):
    global im
    x0,y0,x1,y1=[v*4 for v in box]
    patch=PU[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
    r=patch-bg_at(xx/4,yy/4)
    a=np.clip((np.abs(r).max(2)-12)/30,0,1)
    e=np.minimum(np.minimum(xx-x0,x1-1-xx),np.minimum(yy-y0,y1-1-yy))/12; a*=np.clip(e,0,1)
    w=size; h=size*(y1-y0)/(x1-x0)
    L=Image.fromarray(np.dstack([np.clip(patch,0,255),a*255*fade_]).astype('uint8')).resize((max(1,round(w)),max(1,round(h))),Image.LANCZOS)
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    if glow:
        G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G); R=size*0.9
        gd.ellipse((cxp-R,cyp-R*0.6,cxp+R,cyp+R*1.2),fill=(255,150,70,int(70*fade_)))
        im.alpha_composite(G.filter(ImageFilter.GaussianBlur(size*0.45)))
    im.alpha_composite(L,(round(cxp-w/2),round(cyp-h/2)))
YEL=(498,70,552,128); RS=(511,264,537,294); RB=(521,320,558,362); RL=(150,250,206,310)
L_=[ # (src, x, y, size, blur, fade)
 (YEL,2470,70,58,0,1),(RB,1990,95,52,0,1),(RS,2180,300,34,0,0.95),(RS,1880,640,40,0,0.9),(RL,2505,560,70,2,0.75),
 (RS,2330,700,26,1,0.7),(RS,1745,40,26,0,0.85),(RB,960,70,46,0,1),(RS,1050,250,30,0,0.9),(RS,880,690,34,0,0.85),
 (RS,700,40,24,1,0.7),(RL,70,620,80,3,0.7),(RS,40,95,30,1,0.7),(RS,1640,250,30,0,0.9),
 (RS,2400,420,22,1.5,0.6),(RS,620,700,22,1.5,0.6),(RB,1500,25,30,1,0.8),
]
for b,x,y,sz,bl,fa in L_: lantern(b,x,y,sz,bl,fa)
# fine sparkle dust
G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G)
for i in range(140):
    x=rng.uniform(0,W); y=rng.uniform(0,H*0.8); r=rng.uniform(1,3.2)
    if abs(x-SCX)<430 and y>110: continue
    gd.ellipse((x-r,y-r,x+r,y+r),fill=(255,230,205,int(rng.uniform(60,190))))
im.alpha_composite(G.filter(ImageFilter.GaussianBlur(1.2)))
im.convert('RGB').save(OUT.replace('.png','_bg.png'))
im=typo2.draw(im)
im.convert('RGB').save(OUT); print('ok')
