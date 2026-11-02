# Loop prep 2: per-window layer + labels, badges (shadow baked), moon/star sprites, title pieces
# re-sampled to 1x on the canvas grid, static title shadow, cleaned bulb list.
import sys, pickle; sys.path.insert(0,'/root/mk/lib')
import numpy as np
from PIL import Image, ImageFilter, ImageChops
from scipy import ndimage as ndi
from common import *
A='/root/mk/anim/'
s=0.38; Y0=3290; Y1=Y0+H/s; LX1=2900; RX0=1836
LW=round(LX1*s); RW=round((4392-RX0)*s); RX=W-RW
SX=4392/1312.6457; SY=6217/1854.2269
def ty(y): return (y-Y0)*H/(Y1-Y0)
def tL(x): return x*LW/LX1
def tR(x): return RX+(x-RX0)*RW/(4392-RX0)
# --- windows layer (same as v4 stage2)
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
g0,g1=LW,RX; mid=(g0+g1)//2
wl.alpha_composite(wl.crop((2*g0-mid,0,g0,H)).transpose(Image.FLIP_LEFT_RIGHT),(g0,0))
wl.alpha_composite(wl.crop((g1,0,2*g1-mid,H)).transpose(Image.FLIP_LEFT_RIGHT),(mid,0))
wl.save(A+'win.png')
al=np.asarray(wl.getchannel('A'))
lab,n=ndi.label(al>20)
lab=ndi.grey_dilation(lab,size=(3,3))  # cover soft edges
np.save(A+'win_lab.npy',lab.astype(np.int32)); print('windows',n)
# --- badges at 1x, unrotated, shadow baked (as v4 put(): alpha .5, blur 8, offset 5,9)
def fit(img,h): return rs(img,h/img.height)
for nm,box,h in [('ob',(50,945,420,1135),170),('fb',(740,1345,1135,1595),215)]:
    b=fit(el(*box),h); P=30
    out=Image.new('RGBA',(b.width+2*P,b.height+2*P),(0,0,0,0))
    sh=Image.new('RGBA',b.size,(2,20,10,0)); sh.putalpha(b.getchannel('A').point(lambda v:int(v*0.5)))
    shl=Image.new('RGBA',out.size,(0,0,0,0)); shl.alpha_composite(sh,(P+5,P+9))
    out.alpha_composite(shl.filter(ImageFilter.GaussianBlur(8))); out.alpha_composite(b,(P,P))
    out.save(A+f'badge_{nm}.png'); print(nm,b.size)
# --- moon / big star (keyed from the poster sky) at 2x of their v4 size
SKYC=np.array([6,62,41],np.float32)
def keyed(box):
    c=BG().crop(box); a=np.asarray(c).astype(np.float32)
    al=np.clip((np.sqrt(((a-SKYC)**2).sum(2))-28)/42,0,1)
    o=c.convert('RGBA'); o.putalpha(Image.fromarray((al*255).astype('uint8'))); return o.crop(o.getbbox())
fit(keyed((3780,1480,4060,1760)),156).save(A+'moon2x.png')
fit(keyed((280,1170,520,1400)),140).save(A+'star2x.png')
# --- title pieces -> 1x sprites on the integer canvas grid (premultiplied resample)
M=pickle.load(open(A+'title_meta.pkl','rb')); SS=2
import glob
files=sorted(glob.glob(A+'t_*.png'))
T=[]
for fn,p in zip(files,M['pieces']):
    im=Image.open(fn).convert('RGBa'); pad=8
    big=Image.new('RGBa',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.paste(im,(pad,pad))
    X0=int(np.floor(p['x']))-1; Y0_=int(np.floor(p['y']))-1
    w=int(np.ceil(im.width/SS))+3; h=int(np.ceil(im.height/SS))+3
    bx=(X0-p['x'])*SS+pad; by=(Y0_-p['y'])*SS+pad
    one=big.resize((w,h),Image.LANCZOS,box=(bx,by,bx+w*SS,by+h*SS)).convert('RGBA')
    T.append(dict(name=p['name'],img=one,X=X0,Y=Y0_,w=p['w'],h=p['h'],x=p['x'],y=p['y']))
order=[t for t in T if t['name']=='bd_band']+[t for t in T if t['name']!='bd_band']
# rest composite -> check vs v4 + static shadow
rest=Image.new('RGBA',(W,H),(0,0,0,0))
for t in order: rest.alpha_composite(t['img'],(t['X'],t['Y']))
D=5; Aa=rest.getchannel('A')
sh=Image.new('RGBA',(W,H),(0,14,6,0)); sh.putalpha(Aa.point(lambda v:int(v*0.5)))
sh=sh.filter(ImageFilter.GaussianBlur(7)); sh=ImageChops.offset(sh,D//2+3,D+7)
sh.save(A+'title_shadow.png')
pickle.dump(dict(pieces=[dict(t,img=None) for t in order]),open(A+'title1x.pkl','wb'))
for i,t in enumerate(order): t['img'].save(A+f'p1_{i:02d}.png')
rest.save(A+'title_rest.png')
# --- bulbs: drop the false hits (awning, cook's face, the star at the top)
b=np.load(A+'bulbs2.npy')
bad=[(133,104),(73,363)]
keep=[x for x in b if x[1]>15 and all(np.hypot(x[0]-bx,x[1]-by)>12 for bx,by in bad)]
np.save(A+'bulbs_final.npy',np.array(keep)); print('bulbs',len(keep))
