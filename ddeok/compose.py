import os,sys,numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT=sys.argv[1] if len(sys.argv)>1 else 'kv.png'
W,H=2560,768
PY0,PY1=138,660
s=H/(PY1-PY0)
SCX=1405            # canvas x of poster x=330
off=SCX/s-330
coefs=np.load('bgcoef.npy')
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
def bg_at(px,py):  # poster coords arrays
    f=F(px,py); return np.stack([f@c for c in coefs],-1)
# ---- background over canvas
cy,cx=np.mgrid[0:H,0:W].astype(float)
ppx=np.clip(cx/s-off,0,596); ppy=np.minimum(cy/s+PY0,630)
bg=bg_at(ppx,ppy)
# ---- scene residual (hi-res)
CX0,CY0,CX1,CY1=78,180,596,625
crop=Image.open('scene_up.png' if os.path.exists('scene_up.png') else 'scene_crop.png').convert('RGB')
tw=round((CX1-CX0)*s); th=round((CY1-CY0)*s)
crop=np.asarray(crop.resize((tw,th),Image.LANCZOS)).astype(float)
ox=round((CX0+off)*s); oy=round((CY0-PY0)*s)
yy,xx=np.mgrid[0:th,0:tw].astype(float)
res=crop-bg_at(xx/s+CX0,yy/s+CY0)
# feather residual at crop borders
fx=np.clip(np.minimum(xx,tw-1-xx)/(70*s),0,1); fy=np.clip(np.minimum(yy/(60*s),(th-1-yy)/(25*s)),0,1)
wide=(fx*fy)
fx2=np.clip(np.minimum(xx,tw-1-xx)/(6*s),0,1); fy2=np.clip(np.minimum(yy/(3*s),(th-1-yy)/(6*s)),0,1)
obj=np.clip((np.abs(res).max(2)-14)/20,0,1)
obj=np.asarray(Image.fromarray((obj*255).astype('uint8')).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))).astype(float)/255
wt=np.maximum(wide,obj*fx2*fy2)
wt=wt*wt*(3-2*wt)
res*= wt[...,None]
# remove the half lantern cut at right edge
img=bg.copy()
hx,hy=1400,470
rr=np.sqrt(((cx-hx)/520)**2+((cy-hy)/330)**2)
halo=np.exp(-rr**2*1.6)
img+= halo[...,None]*np.array([38,22,14.])
y0c,x0c=max(oy,0),ox
sub=res[y0c-oy:H-oy] if oy<0 else res[:H-oy]
img[y0c:y0c+sub.shape[0],x0c:x0c+sub.shape[1]]+=sub[:, :W-x0c]
# ---- side vignette / darkening for text contrast
d=np.clip(np.abs(cx-1400)/1150,0,1)
dark=1-0.42*d**1.6
top=1-0.15*np.clip(1-cy/300,0,1)
img*= (dark*top)[...,None]
im=Image.fromarray(np.clip(img,0,255).astype('uint8')).convert('RGBA')
# ---- extra lanterns transplanted from poster (residual-add with glow)
P=np.asarray(Image.open('poster_up.png').convert('RGB')).astype(float)
def lantern(box,cxp,cyp,scale,blur=0,fade=1.0):
    global im
    x0,y0,x1,y1=[v*4 for v in box]
    patch=P[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
    r=patch-bg_at(xx/4,yy/4)
    a=np.clip((np.abs(r).max(2)-12)/30,0,1)
    ex=np.minimum(np.minimum(xx-x0,x1-1-xx),np.minimum(yy-y0,y1-1-yy))/12
    a*=np.clip(ex,0,1)
    w=(x1-x0)/4*scale*s; h=(y1-y0)/4*scale*s
    L=Image.fromarray(np.dstack([np.clip(patch,0,255),a*255*fade]).astype('uint8')).resize((max(1,round(w)),max(1,round(h))),Image.LANCZOS)
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(L,(round(cxp-w/2),round(cyp-h/2)))
YEL=(498,70,552,128); RS=(511,264,537,294); RB=(521,320,558,362); RL=(150,250,206,310)
EXTRA=[(YEL,2440,95,0.75,0,1),(RS,1985,120,0.9,0,0.95),(RB,1800,690,0.65,0,0.85),(RS,1030,95,0.75,0,0.9),(RL,975,690,0.5,0,0.8),(RS,62,90,0.7,0,0.7),(RB,2505,620,0.55,0,0.7)]
for b,x,y,sc,bl,fa in EXTRA: lantern(b,x,y,sc,bl,fa)
# ---- soft sparkle specks
rng=np.random.default_rng(7)
glow=Image.new('RGBA',(W,H),(0,0,0,0)); g=ImageDraw.Draw(glow)
for i in range(70):
    x=rng.uniform(0,W); y=rng.uniform(0,H*0.75); r=rng.uniform(1.5,4)
    if 1000<x<1850 and y>120: continue
    g.ellipse((x-r,y-r,x+r,y+r),fill=(255,226,200,int(rng.uniform(70,170))))
im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(1.6)))
# ---- typography
FD='fonts/'
def font(n,sz):
    if n.startswith('NotoSansKR-'):
        f=ImageFont.truetype(FD+'NotoSansKR.ttf',sz); f.set_variation_by_axes([{'Bold':700,'Medium':500,'Black':900}[n[11:-4]]]); return f
    return ImageFont.truetype(FD+n,sz)
def shadow_text(layer_pos,draw_fn,blur=10,alpha=150,dy=4):
    pass
def text_layer(txt,fnt,fill,stroke=0,sc=None,spacing=0):
    bb=fnt.getbbox(txt,stroke_width=stroke)
    w=bb[2]-bb[0]+spacing*len(txt); h=bb[3]-bb[1]
    L=Image.new('RGBA',(w+40,h+40),(0,0,0,0)); d=ImageDraw.Draw(L)
    if spacing:
        x=20-bb[0]
        for ch in txt:
            d.text((x,20-bb[1]),ch,font=fnt,fill=fill,stroke_width=stroke,stroke_fill=sc); x+=fnt.getlength(ch)+spacing
    else:
        d.text((20-bb[0],20-bb[1]),txt,font=fnt,fill=fill,stroke_width=stroke,stroke_fill=sc)
    return L
def put(L,x,y,anchor='l',shadow=(0,0,0,150),sblur=12,sdy=5):
    if anchor=='c': x=x-L.width/2
    if anchor=='r': x=x-L.width
    x=round(x-20); y=round(y-20)
    if shadow:
        a=L.split()[3]
        S=Image.new('RGBA',L.size,shadow); S.putalpha(a.point(lambda v:v*shadow[3]//255))
        S=S.filter(ImageFilter.GaussianBlur(sblur))
        im.alpha_composite(S,(x,y+sdy))
    im.alpha_composite(L,(x,y))
    return L.width-40,L.height-40
ML=130
# header
hw,hh=put(text_layer('2026 문창 떡 축제',font('NanumMyeongjo-ExtraBold.ttf',62),(255,244,228,255),spacing=2),ML+8,112)
# title lettering
T=Image.open('title_hi.png')
tw2=900; th2=round(T.height*tw2/T.width)
T=T.resize((tw2,th2),Image.LANCZOS)
a=T.split()[3]; S=Image.new('RGBA',T.size,(40,20,60,0)); S.putalpha(a.point(lambda v:int(v*0.75)))
S=S.filter(ImageFilter.GaussianBlur(14))
ty=200
im.alpha_composite(S,(ML-8,ty+8)); im.alpha_composite(T,(ML-14,ty))
# tagline
put(text_layer('고소한 떡 냄새, 우리 동네 시장 나들이',font('NotoSansKR-Bold.ttf',44),(255,255,255,240)),ML+8,ty+th2+30)
# right column: date / venue
RX=2430
f1=ImageFont.truetype(FD+'NanumMyeongjo-ExtraBold.ttf',132)
put(text_layer('10.30–31',f1,(255,255,255,255)),RX,230,'r',sblur=14)
put(text_layer('금 · 토',font('NanumMyeongjo-ExtraBold.ttf',58),(255,214,140,255),spacing=2),RX,395,'r')
dd=ImageDraw.Draw(im); dd.rounded_rectangle((RX-520,500,RX,503),2,fill=(255,230,200,200))
put(text_layer('대전 문창전통시장 일대',font('NotoSansKR-Bold.ttf',46),(255,255,255,255)),RX,530,'r')
put(text_layer('11월 금·토 주말에도 야시장 진행',font('NotoSansKR-Medium.ttf',32),(255,224,190,235)),RX,602,'r')
im.convert('RGB').save(OUT)
print(OUT,im.size)
