import sys, numpy as np
from PIL import Image, ImageFilter, ImageChops
W,H=2560,768; K=400/72
V=Image.open('src/vec_400.png'); BG=Image.open('src/bg_rgb.png').convert('RGB')
SX=BG.width/1312.6457; SY=BG.height/1854.2269
SKY=np.array([6,62,41],np.float32)
def el(x0,y0,x1,y1):
    c=V.crop((int(x0*K),int(y0*K),int(x1*K),int(y1*K))); return c.crop(c.getbbox())
def key(img,lo=28,hi=70):
    a=np.asarray(img).astype(np.float32)[...,:3]
    d=np.sqrt(((a-SKY)**2).sum(2)); al=np.clip((d-lo)/(hi-lo),0,1)
    o=img.convert('RGBA'); o.putalpha(Image.fromarray((al*255).astype('uint8'))); return o
# scene raster + lit windows
scene=BG.convert('RGBA')
bx,by,_,_=V.crop((int(420*K),int(955*K),int(1190*K),int(1140*K))).getbbox()
win=el(420,955,1190,1140); win=win.resize((round(win.width/K*SX),round(win.height/K*SY)),Image.LANCZOS)
scene.alpha_composite(win,(round((420+bx/K+63.6755)*SX),round((955+by/K+47.2106)*SY)))
# 1 sky base
s0=W/BG.width
cv=BG.crop((0,1150,BG.width,1150+round(H/s0))).resize((W,H),Image.LANCZOS).convert('RGBA')
# 2 top deco band (garland, maple, stars) keyed
TS=float([a for a in sys.argv if a.startswith('--ts=')][0][5:]) if any(a.startswith('--ts=') for a in sys.argv) else 0.40
top=BG.crop((0,0,BG.width,950)); top=key(top).resize((round(BG.width*TS),round(950*TS)),Image.LANCZOS)
TOP=top
# 3 side panels
ps=float(sys.argv[1]) if len(sys.argv)>1 else 0.40
PY=int(sys.argv[2]) if len(sys.argv)>2 else 3150
ph=round(H/ps)
def panel(x0,x1,side,fe=200):
    p=scene.crop((x0,PY,x1,PY+ph)).resize((round((x1-x0)*ps),H),Image.LANCZOS)
    w=p.width; m=np.ones((H,w),np.float32); xs=np.arange(w)
    if side=='L': f=np.clip((w-1-xs)/fe,0,1)
    else: f=np.clip(xs/fe,0,1)
    m*=f[None,:]**1.3
    ys=np.arange(H); m*=np.clip(ys/70,0,1)[:,None]**1.0 if False else 1
    p.putalpha(Image.fromarray((m*255).astype('uint8'))); return p
pl=panel(0,1750,'L'); pr=panel(2750,4392,'R')
cv.alpha_composite(pl,(0,0)); cv.alpha_composite(pr,(W-pr.width,0))
co=Image.open('cut/couple.png'); co=co.resize((round(co.width*ps),round(co.height*ps)),Image.LANCZOS)
cv.alpha_composite(co,(round(W-pr.width+(2550-2750)*ps),round((4250-PY)*ps)))
cv.alpha_composite(TOP,(round((W-TOP.width)/2),0))
# 4 center deco: busker + couple on warm glow
yy,xx=np.mgrid[0:H,0:W]
g=np.clip(1-(((xx-W/2)/700)**2+((yy-H-40)/260)**2),0,1)**1.5
glow=Image.new('RGBA',(W,H),(255,175,80,0)); glow.putalpha(Image.fromarray((g*70).astype('uint8')))
cv.alpha_composite(glow)
def cut(n,h,x,y):
    o=Image.open(f'cut/{n}.png'); o=o.crop(o.getbbox()); r=h/o.height; o=o.resize((round(o.width*r),h),Image.LANCZOS)
    sh=Image.new('RGBA',(o.width*2,60),(0,0,0,0)); from PIL import ImageDraw; ImageDraw.Draw(sh).ellipse((o.width*0.45,18,o.width*1.55,42),fill=(0,12,5,150))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)),(round(x-o.width),round(y-36)))
    cv.alpha_composite(o,(round(x-o.width/2),round(y-h))); return o.size
if '--people' in sys.argv:
    cut('busker',300,W/2-560,H-6)
# 5 badges
def put(img,h,cx,cy,rot=0,shadow=0.55,blur=10,off=(6,10)):
    r=h/img.height; im=img.resize((round(img.width*r),h),Image.LANCZOS)
    if rot: im=im.rotate(rot,Image.BICUBIC,expand=True)
    x=round(cx-im.width/2); y=round(cy-im.height/2)
    if shadow:
        sh=Image.new('RGBA',im.size,(0,18,8,0)); sh.putalpha(im.getchannel('A').point(lambda v:int(v*shadow)))
        cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)),(x+off[0],y+off[1]))
    cv.alpha_composite(im,(x,y)); return (x,y,im.width,im.height)
def extrude(img,h,cx,cy,depth,col):
    r=h/img.height; im=img.resize((round(img.width*r),h),Image.LANCZOS)
    x=round(cx-im.width/2); y=round(cy-im.height/2)
    a=im.getchannel('A')
    sh=Image.new('RGBA',im.size,(0,15,6,0)); sh.putalpha(a.point(lambda v:int(v*0.6)))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)),(x+depth+8,y+depth+14))
    for i in range(depth,0,-1):
        t=i/depth; c=tuple(int(cc*(0.75+0.25*(1-t))) for cc in col)
        L=Image.new('RGBA',im.size,c+(0,)); L.putalpha(a); cv.alpha_composite(L,(x+i//2,y+i))
    cv.alpha_composite(im,(x,y))
    return (x,y,im.width,im.height)
openb=el(50,945,420,1135); food=el(740,1345,1135,1595)
dj=el(300,88,900,181); gw=el(250,182,950,320); mk=el(250,322,950,523); bd=el(250,550,950,676)
cx=W/2
y=34; r=put(dj,62,cx,y+31,shadow=0.4); y+=62+10
r=extrude(gw,128,cx,y+64,8,(150,105,40)); y+=128+8
r=extrude(mk,300,cx,y+150,16,(200,170,130)); mkbox=r; y+=300+14
r=extrude(bd,138,cx,y+69,7,(170,130,95)); y+=138
print('title bottom',y,'mk',mkbox)
put(openb,190,cx-835,250,rot=6)
put(food,250,cx+830,250,rot=-2)
cv.convert('RGB').save([a for a in sys.argv if a.endswith('.png')][0])
