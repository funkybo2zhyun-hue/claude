import numpy as np
from PIL import Image
im=np.asarray(Image.open('poster.jpg').convert('RGB')).astype(float)
def fill(a,x0,y0,x1,y1,pad=14):
    X0,Y0,X1,Y1=max(x0-pad,0),max(y0-pad,0),min(x1+pad,a.shape[1]),min(y1+pad,a.shape[0])
    ys,xs=np.mgrid[Y0:Y1,X0:X1]
    ring=~((xs>=x0)&(xs<x1)&(ys>=y0)&(ys<y1))
    # exclude bright/saturated text pixels from ring
    px=a[Y0:Y1,X0:X1]
    lum=px.mean(2); sat=px.max(2)-px.min(2)
    ok=ring&(lum<170)&(sat<90)
    def feats(x,y):
        x=(x-x0)/100.;y=(y-y0)/100.
        return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y],-1)
    F=feats(xs[ok],ys[ok]);
    for c in range(3):
        coef,*_=np.linalg.lstsq(F,px[...,c][ok],rcond=None)
        yy,xx=np.mgrid[y0:y1,x0:x1]
        a[y0:y1,x0:x1,c]=feats(xx,yy)@coef
    return a
im=fill(im,40,158,128,258)
im=fill(im,128,155,358,222)
rng=np.random.default_rng(1)
out=Image.fromarray(np.clip(im,0,255).astype('uint8'))
out.crop((78,180,596,625)).save('scene_crop.png')
out.crop((40,140,400,280)).resize((1080,420),Image.LANCZOS).save('check.png')
