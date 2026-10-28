import pymupdf, json, sys, numpy as np
out=sys.argv[1]
d=pymupdf.open(out+'/cum.pdf'); types=json.load(open(out+'/elems.json'))
def r(i):
    pm=d[i].get_pixmap(); return np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width,3).astype(np.int16)
prev=r(0); np.save(out+'/base.npy',prev.astype(np.uint8))
meta=[]; arrs={}
for i,t in enumerate(types):
    cur=r(i+1); dl=cur-prev; prev=cur
    nz=np.argwhere(np.abs(dl).max(2)>0)
    if len(nz)==0: meta.append(None); continue
    y0,x0=nz.min(0); y1,x1=nz.max(0)+1
    arrs[f'd{i}']=dl[y0:y1,x0:x1]; meta.append([t,int(x0),int(y0),int(x1),int(y1)])
np.save(out+'/full.npy',prev.astype(np.uint8))
np.savez(out+'/deltas.npz',**arrs); json.dump(meta,open(out+'/meta.json','w'))
print(sum(m is not None for m in meta))
