import pymupdf, json, sys, numpy as np
out=sys.argv[1]; M=300
d=pymupdf.open(out+'/leaves.pdf'); L=json.load(open(out+'/leaves.json'))
arrs={}
for i in range(len(d)):
    pm=d[i].get_pixmap(alpha=True)
    a=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width,4)
    nz=np.argwhere(a[...,3]>0)
    if len(nz)==0: L[i]['bbox']=None; continue
    y0,x0=nz.min(0); y1,x1=nz.max(0)+1
    arrs[f's{i}']=a[y0:y1,x0:x1].copy()
    L[i]['bbox']=[int(x0)-M,int(y0)-M,int(x1)-M,int(y1)-M]   # in artboard px
np.savez(out+'/sprites.npz',**arrs); json.dump(L,open(out+'/leaves.json','w'))
print(len(arrs), pm.width, pm.height)
