# v4 stage 2: lit windows, decor, badges and the centred title with depth on top of the scene plate.
import sys, json; sys.path.insert(0,'/root/mk/lib'); sys.path.insert(0,'/root/mk/v4')
import numpy as np
from PIL import Image, ImageFilter, ImageChops
from common import *
P=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
s=0.38; Y0=3290; Y1=Y0+H/s; LX1=2900; RX0=1836
LW=round(LX1*s); RW=round((4392-RX0)*s); RX=W-RW
SX=4392/1312.6457; SY=6217/1854.2269
def ty(y): return (y-Y0)*H/(Y1-Y0)
def tL(x): return x*LW/LX1
def tR(x): return RX+(x-RX0)*RW/(4392-RX0)
cv=Image.open(sys.argv[1]).convert('RGBA')
# --- lit windows (vector) on the skyline of both copies
wc=V().crop((int(360*K),int(985*K),int(1010*K),int(1110*K)))
a=np.asarray(wc).astype(np.int16)
key=(a[...,0]>140)&(a[...,1]>100)&(a[...,2]<110)&((a[...,0]-a[...,1])<80)&(a[...,3]>0)
wa=wc.copy(); wa.putalpha(Image.fromarray((key*a[...,3]).astype('uint8')))
sx0=(360+63.6755)*SX; sy0=(985+47.2106)*SY; f=SX/K*s
wr=rs(wa,f)
wl=Image.new('RGBA',(W,H),(0,0,0,0))
for tx,lo,hi in [(tL,0,LW),(tR,RX,W)]:
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); lay.alpha_composite(wr,(round(tx(sx0)),round(ty(sy0))))
    m=Image.new('L',(W,H),0); m.paste(255,(lo,0,hi,H))
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'),m)); wl.alpha_composite(lay)
# the strip behind the logo is mirrored neighbours in the plate — mirror their windows too
g0,g1=LW,RX; mid=(g0+g1)//2
wl.alpha_composite(wl.crop((2*g0-mid,0,g0,H)).transpose(Image.FLIP_LEFT_RIGHT),(g0,0))
wl.alpha_composite(wl.crop((g1,0,2*g1-mid,H)).transpose(Image.FLIP_LEFT_RIGHT),(mid,0))
cv.alpha_composite(wl)
def put(img,x,y,shadow=0.5,blur=8,off=(5,9)):
    if shadow:
        sh=Image.new('RGBA',img.size,(2,20,10,0)); sh.putalpha(img.getchannel('A').point(lambda v:int(v*shadow)))
        cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)),(x+off[0],y+off[1]))
    cv.alpha_composite(img,(x,y))
def fit(img,h=None,w=None,rot=0):
    r=(h/img.height) if h else (w/img.width); im=rs(img,r)
    return im.rotate(rot,Image.BICUBIC,expand=True) if rot else im
# --- badges (poster's own)
if P.get('badges',1):
    ob=fit(el(50,945,420,1135),h=P.get('ob_h',170),rot=P.get('ob_r',4))
    put(ob,*P.get('ob_xy',[60,70]))
    fb=fit(el(740,1345,1135,1595),h=P.get('fb_h',215),rot=P.get('fb_r',-3))
    put(fb,*P.get('fb_xy',[1640,330]))
# --- crescent moon and sparkle star from the poster sky
if P.get('sky',1):
    SKYC=np.array([6,62,41],np.float32)
    def keyed(box):
        c=BG().crop(box); a=np.asarray(c).astype(np.float32)
        al=np.clip((np.sqrt(((a-SKYC)**2).sum(2))-28)/42,0,1)
        o=c.convert('RGBA'); o.putalpha(Image.fromarray((al*255).astype('uint8'))); return o.crop(o.getbbox())
    mo=fit(keyed((3780,1480,4060,1760)),h=P.get('moon_h',78)); cv.alpha_composite(mo,tuple(P.get('moon_xy',[1890,22])))
    stx=fit(keyed((280,1170,520,1400)),h=P.get('star_h',70)); cv.alpha_composite(stx,tuple(P.get('star_xy',[700,18])))
# --- title stack with depth
st=el(250,80,950,680); LH=P.get('LH',600); st=rs(st,LH/st.height)
x=(W-st.width)//2; y=(H-st.height)//2+P.get('ly',0)
A=st.getchannel('A'); D=P.get('depth',5)
sh=Image.new('RGBA',st.size,(0,14,6,0)); sh.putalpha(A.point(lambda v:int(v*P.get('sh_a',0.5))))
cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(P.get('sh_b',7))),(x+D//2+3,y+D+7))
arr=np.asarray(st).astype(np.float32)
for i in range(D,0,-1):
    k=0.30+0.22*(1-i/D)
    lay=arr.copy(); lay[...,:3]*=k; lay[...,:3]=np.minimum(lay[...,:3]+np.array([8,4,2])*(1-i/D),255)
    cv.alpha_composite(Image.fromarray(lay.astype('uint8')),(x+round(i*0.3),y+i))
cv.alpha_composite(st,(x,y))
print('logo',x,y,x+st.width,y+st.height)
cv.convert('RGB').save(sys.argv[2])
