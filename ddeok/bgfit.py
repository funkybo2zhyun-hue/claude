# fit smooth background model on poster bg pixels (objects/text excluded)
import numpy as np
from PIL import Image
P=np.asarray(Image.open('poster.jpg').convert('RGB')).astype(float)
H,W,_=P.shape
ys,xs=np.mgrid[0:H,0:W]
mask=np.ones((H,W),bool)
for (x0,y0,x1,y1) in [(30,20,330,105),(36,110,360,260),(36,250,80,610),(95,235,596,620),(400,170,515,275),(490,60,560,130),(0,0,70,110),(0,630,596,843),(150,220,250,320)]:
    mask[y0:y1,x0:x1]=False
sat=P.max(2)-P.min(2); mask&=sat<80
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
coefs=[]
for c in range(3):
    co,*_=np.linalg.lstsq(F(xs[mask].astype(float),ys[mask].astype(float)),P[...,c][mask],rcond=None); coefs.append(co)
np.save('bgcoef.npy',np.array(coefs))
pred=np.stack([F(xs.astype(float),ys.astype(float))@co for co in coefs],-1)
err=np.abs(pred-P)[mask].mean(); print('mean err',err)
for y in range(0,843,100): print(y,pred[y,300].round())
