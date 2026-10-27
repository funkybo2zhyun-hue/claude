import pymupdf, json, sys, numpy as np
out=sys.argv[1]
d=pymupdf.open(out+'/iso.pdf')
def r(i):
    pm=d[i].get_pixmap(); return np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width,3).astype(np.int16)
P=r(0); np.save(out+'/prefix.npy',P.astype(np.uint8))
meta=[];arrs={}
for i in range(1,len(d)):
    dl=r(i)-P; nz=np.argwhere(np.abs(dl).max(2)>0)
    if len(nz)==0: meta.append(None); continue
    y0,x0=nz.min(0); y1,x1=nz.max(0)+1
    arrs[f'i{i-1}']=dl[y0:y1,x0:x1]; meta.append([int(x0),int(y0),int(x1),int(y1)])
np.savez(out+'/iso.npz',**arrs); json.dump(meta,open(out+'/isometa.json','w'))
S=P.astype(np.int32)
for i,m in enumerate(meta):
    if m: S[m[1]:m[3],m[0]:m[2]]+=arrs[f'i{i}']
F=np.load(out+'/full.npy').astype(np.int32)
e=np.abs(S-F).max(2); print('err max',e.max(),'mean',e.mean(),'p99',np.percentile(e,99))
from PIL import Image
Image.fromarray(np.clip(S,0,255).astype(np.uint8)).save(out+'/isosum.png')
