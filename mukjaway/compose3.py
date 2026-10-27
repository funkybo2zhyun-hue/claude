import sys, numpy as np
from PIL import Image, ImageFilter
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
scene=BG.convert('RGBA')
bx,by,_,_=V.crop((int(420*K),int(955*K),int(1190*K),int(1140*K))).getbbox()
win=el(420,955,1190,1140); win=win.resize((round(win.width/K*SX),round(win.height/K*SY)),Image.LANCZOS)
scene.alpha_composite(win,(round((420+bx/K+63.6755)*SX),round((955+by/K+47.2106)*SY)))
# sky base: poster's own plain sky, downscaled (not enlarged)
s0=W/BG.width
cv=BG.crop((0,1150,BG.width,1150+round(H/s0))).resize((W,H),Image.LANCZOS).convert('RGBA')
# whole market scene, full width of the illustration kept, scaled to canvas height
SY0=3250; ss=H/(BG.height-SY0)
sc=scene.crop((0,SY0,BG.width,BG.height)).resize((round(BG.width*ss),H),Image.LANCZOS)
fe=110; m=np.ones((H,sc.width),np.float32); m*=np.clip(np.arange(sc.width)/fe,0,1)[None,:]
sc.putalpha(Image.fromarray((m*255).astype('uint8')))
SCX=W-sc.width; cv.alpha_composite(sc,(SCX,0))
# maple branch from poster top-left + stars, keyed, at the scene's scale
tl=key(BG.crop((0,0,1400,1300))); ts=0.33
tl=tl.resize((round(tl.width*ts),round(tl.height*ts)),Image.LANCZOS); cv.alpha_composite(tl,(0,0))
def put(img,h,cx,cy,rot=0,shadow=0.5,blur=8,off=(5,8)):
    r=h/img.height; im=img.resize((round(img.width*r),h),Image.LANCZOS)
    if rot: im=im.rotate(rot,Image.BICUBIC,expand=True)
    x=round(cx-im.width/2); y=round(cy-im.height/2)
    if shadow:
        sh=Image.new('RGBA',im.size,(0,18,8,0)); sh.putalpha(im.getchannel('A').point(lambda v:int(v*shadow)))
        cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)),(x+off[0],y+off[1]))
    cv.alpha_composite(im,(x,y)); return (x,y,im.width,im.height)
def extrude(img,h,cx,cy,depth,col):
    r=h/img.height; im=img.resize((round(img.width*r),h),Image.LANCZOS)
    x=round(cx-im.width/2); y=round(cy-im.height/2); a=im.getchannel('A')
    sh=Image.new('RGBA',im.size,(0,15,6,0)); sh.putalpha(a.point(lambda v:int(v*0.6)))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)),(x+depth+6,y+depth+12))
    for i in range(depth,0,-1):
        c=tuple(int(cc*(0.75+0.25*(1-i/depth))) for cc in col)
        L=Image.new('RGBA',im.size,c+(0,)); L.putalpha(a); cv.alpha_composite(L,(x+i//2,y+i))
    cv.alpha_composite(im,(x,y)); return (x,y,im.width,im.height)
dj=el(300,88,900,181); gw=el(250,182,950,320); mk=el(250,322,950,523); bd=el(250,550,950,676)
inv=el(250,690,950,725); dt=el(100,738,1100,835); vn=el(250,860,950,905); ad=el(250,915,960,952)
openb=el(50,945,420,1135); food=el(740,1345,1135,1595)
cx=SCX/2+20
rows=[('dj',dj,46),('gw',gw,96),('mk',mk,238),('bd',bd,100),('inv',inv,28),('dt',dt,74),('vn',vn,36),('ad',ad,26)]
gaps=[8,4,12,14,10,12,6]
tot=sum(h for *_,h in rows)+sum(gaps); y=(H-tot)/2
for i,(n,im,h) in enumerate(rows):
    if n=='gw': extrude(im,h,cx,y+h/2,7,(150,105,40))
    elif n=='mk': extrude(im,h,cx,y+h/2,13,(200,170,130))
    elif n=='bd': extrude(im,h,cx,y+h/2,6,(170,130,95))
    else: put(im,h,cx,y+h/2,shadow=0.45)
    y+=h+(gaps[i] if i<len(gaps) else 0)
print('scene x',SCX,sc.width,'stack',tot)
put(openb,150,SCX+175,175,rot=4)
put(food,190,W-215,575,rot=-2)
cv.convert('RGB').save(sys.argv[1])
