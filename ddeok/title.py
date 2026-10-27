import numpy as np
from PIL import Image, ImageFilter
src=np.asarray(Image.open('poster.jpg').convert('RGB')).astype(float)
x0,y0,x1,y1=38,116,360,260
P=src[y0:y1,x0:x1]
# background: fit quadratic from pixels that look like bg
lum=P.mean(2); sat=P.max(2)-P.min(2)
ys,xs=np.mgrid[0:P.shape[0],0:P.shape[1]]
bgmask=(lum<150)&(P[...,0]<175)
F=np.stack([np.ones_like(xs),xs/100,ys/100,(xs/100)**2,(ys/100)**2,xs*ys/1e4],-1).astype(float)
B=np.zeros_like(P)
for c in range(3):
    coef,*_=np.linalg.lstsq(F[bgmask],P[...,c][bgmask],rcond=None); B[...,c]=F@coef
D=P-B
W=np.array([250,250,250.]); K=np.array([240,105,140.])
def proj(Fc):
    v=Fc[None,None]-B; return np.clip((D*v).sum(2)/(v*v).sum(2),0,1)
aw=proj(W); ak=proj(K)
# classify pink vs white by redness relative to blue
pinkness=(P[...,0]-P[...,2])
is_pink=(pinkness>60)&(xs<130)
from PIL import ImageFilter as IF
is_pink=(np.asarray(Image.fromarray(is_pink.astype("uint8")*255).filter(IF.MaxFilter(7)))>0)&(xs<130)&(ys>48)
a=np.where(is_pink,ak,aw)
a[139:]=0
a[105:,160:200]=0
Image.fromarray((a*255).astype('uint8')).save('title_alpha_raw.png')
Image.fromarray(is_pink.astype('uint8')*255).save('title_pink.png')
# upscale 8x, threshold-smooth
S=8
A=Image.fromarray((a*255).astype('uint8')).resize((a.shape[1]*S,a.shape[0]*S),Image.BICUBIC).filter(ImageFilter.GaussianBlur(S*0.6))
A=np.asarray(A).astype(float)/255
A=np.clip((A-0.42)/0.16,0,1)   # crisp edge, AA width ~ few px
pk=np.asarray(Image.fromarray(is_pink.astype('uint8')*255).resize(A.shape[::-1],Image.BICUBIC).filter(ImageFilter.GaussianBlur(S*0.5)))/255.
rgb=np.zeros(A.shape+(3,))
rgb[:]=W; rgb=rgb*(1-pk[...,None])+np.array([243,106,142.])*pk[...,None]
out=np.dstack([rgb,A*255]).astype('uint8')
Image.fromarray(out).save('title_hi.png')
prev=Image.new('RGBA',(out.shape[1],out.shape[0]),(70,55,100,255)); prev.alpha_composite(Image.fromarray(out)); prev.convert('RGB').resize((out.shape[1]//2,out.shape[0]//2)).save('title_prev.png')
print(out.shape)
