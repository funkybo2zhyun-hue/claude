import sys, numpy as np
from PIL import Image, ImageFilter
W,H=2560,768; K=400/72
V=Image.open('src/vec_400.png'); BG=Image.open('src/bg_rgb.png').convert('RGB')
def el(x0,y0,x1,y1):
    c=V.crop((int(x0*K),int(y0*K),int(x1*K),int(y1*K))); return c.crop(c.getbbox())
y0=int(sys.argv[1]) if len(sys.argv)>1 else 3450
s=W/BG.width
# scene + lit building windows (vector) aligned to raster
SX=BG.width/1312.6457; SY=BG.height/1854.2269
scene=BG.copy().convert('RGBA')
win=el(420,955,1190,1140); wx=(422.9+63.6755)*SX
bx,by=V.crop((int(420*K),int(955*K),int(1190*K),int(1140*K))).getbbox()[:2]
wpt=(420+bx/K,955+by/K)
win=win.resize((round(win.width/K*SX),round(win.height/K*SY)),Image.LANCZOS)
scene.alpha_composite(win,(round((wpt[0]+63.6755)*SX),round((wpt[1]+47.2106)*SY)))
hh=round(H/s)
scene=scene.crop((0,y0,BG.width,y0+hh)).resize((W,H),Image.LANCZOS)
cv=scene
# soft deep-green vignette behind the title stack
g=np.zeros((H,W),np.float32); yy,xx=np.mgrid[0:H,0:W]
cx,cy,rx,ry=W/2,300,760,430
d=((xx-cx)/rx)**2+((yy-cy)/ry)**2
a=np.clip(1-d,0,1)**0.9*0.86
top=np.clip(1-yy/520,0,1)**1.6*0.35
a=np.maximum(a,top)
dark=Image.new('RGBA',(W,H),(4,44,29,255)); dark.putalpha(Image.fromarray((a*255).astype('uint8')))
cv=cv.copy(); cv.alpha_composite(dark)
def put(img,h,cy,shadow=True):
    r=h/img.height; im=img.resize((round(img.width*r),h),Image.LANCZOS)
    x=(W-im.width)//2; y=round(cy-h/2)
    if shadow:
        sh=Image.new('RGBA',im.size,(0,20,10,0)); sh.putalpha(im.getchannel('A').point(lambda v:int(v*0.55)))
        sh=sh.filter(ImageFilter.GaussianBlur(10)); cv.alpha_composite(sh,(x+6,y+10))
    cv.alpha_composite(im,(x,y)); return im.size
dj=el(300,88,900,181); gw=el(250,182,950,320); mk=el(250,322,950,523); bd=el(250,550,950,676)
L=[(dj,58),(gw,118),(mk,262),(bd,124)]; gap=[12,8,14]
tot=sum(h for _,h in L)+sum(gap); y=(600-tot)/2+22
for i,(im,h) in enumerate(L):
    sz=put(im,h,y+h/2,shadow=(i>0)); print(sz); y+=h+(gap[i] if i<3 else 0)
print('stack bottom',y)
cv.convert('RGB').save(sys.argv[2] if len(sys.argv)>2 else 'out.png')
