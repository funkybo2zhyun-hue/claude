import numpy as np
from PIL import Image, ImageFilter
S=4
A=np.asarray(Image.open('scene_up.png').convert('RGB')).astype(float)
H,W=A.shape[:2]
CX,CY,AX,BY=243,321,223,119
x0,x1=int((CX-AX)*S)-4,int((CX+AX)*S)+4; y0,y1=int((CY-BY)*S)-4,min(H,int((CY+BY)*S)+4)
yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
u=(xx/S-CX)/AX; v=(yy/S-CY)/BY
r=np.sqrt(u*u+v*v)
V0=0.42
ok=(v>=V0)&(v<V0+0.15)&(r<0.88)
def Fe(u,v): u=np.clip(u,-0.9,0.9); return np.stack([np.ones_like(u),u,u*u,u**3,u**4],-1)
fit=np.zeros(u.shape+(3,))
orig=A[y0:y1,x0:x1]
for c in range(3):
    co,*_=np.linalg.lstsq(Fe(u[ok],v[ok]),orig[...,c][ok],rcond=None); fit[...,c]=Fe(u,v)@co
fit+=np.clip((V0-v)/(V0+1),0,1)[...,None]*np.array([12,9,12.])
# blend: original where v>=V0 and r<0.86, fit elsewhere inside
w=np.clip((v-V0)/0.08,0,1)*np.clip((0.9-r)/0.04,0,1)
w=np.where(r>=0.9,np.clip((v-0.0)/0.2,0,1),w)   # keep original front rim
col=orig*w[...,None]+fit*(1-w[...,None])
# back rim highlight
rim=np.exp(-((1-r)*AX*S/6)**2)*(v<0)
col=col+rim[...,None]*np.array([40,36,34.])
alpha=np.clip((1-r)*AX*S/3,0,1)
out=np.dstack([col,alpha*255]).clip(0,255).astype('uint8')
Image.fromarray(out).save('disc_clean.png')
pv=Image.new('RGBA',(out.shape[1],out.shape[0]),(30,30,60,255)); pv.alpha_composite(Image.fromarray(out)); pv.convert('RGB').resize((out.shape[1]//3,out.shape[0]//3)).save('disc_prev.png')
