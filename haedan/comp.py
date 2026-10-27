import numpy as np, json
D='/root/hd/out'
L=json.load(open(D+'/leaves.json')); S=np.load(D+'/sprites.npz')
meta=json.load(open(D+'/meta.json')); dz=np.load(D+'/deltas.npz')
W,H=3078,1728
def blend(bm,b,s):
    if bm=='/Normal': return s
    if bm=='/Multiply': return b*s
    if bm=='/Screen': return b+s-b*s
    if bm=='/Overlay': return np.where(b<=0.5,2*b*s,1-2*(1-b)*(1-s))
    if bm=='/SoftLight':
        Dd=np.where(b<=0.25,((16*b-12)*b+4)*b,np.sqrt(np.maximum(b,0)))
        return np.where(s<=0.5,b-(1-2*s)*b*(1-b),b+(2*s-1)*(Dd-b))
    if bm=='/ColorDodge': return np.where(s>=1,1.0,np.minimum(1.0,b/np.maximum(1e-6,1-s)))
    raise Exception(bm)
def eff(chain,mode):
    bms=[b for b,a in chain if b!='/Normal']
    if not bms: bm='/Normal'
    elif mode=='nested': bm=tuple(bms) if len(bms)>1 else bms[0]
    else: bm=bms[-1] if mode=='inner' else bms[0]
    op=1.0
    for b,a in chain: op*=a
    return bm,op
def place(img,spr,x0,y0,bm,op,premul):
    h,w=spr.shape[:2]
    a0,b0=max(0,-x0),max(0,-y0); a1,b1=min(w,W-x0),min(h,H-y0)
    if a1<=a0 or b1<=b0: return
    s=spr[b0:b1,a0:a1].astype(np.float32)/255
    al=s[...,3:4]*op; c=s[...,:3]
    if premul: c=np.where(s[...,3:4]>0,c/np.maximum(s[...,3:4],1e-6),0).clip(0,1)
    reg=img[y0+b0:y0+b1,x0+a0:x0+a1]
    if isinstance(bm,tuple):
        x=c
        for m in reversed(bm): x=blend(m,reg,x)
        reg[:]=(1-al)*reg+al*x
    else: reg[:]=(1-al)*reg+al*blend(bm,reg,c)
def compose(mode='inner',premul=False,offs=None):
    img=np.load(D+'/base.npy').astype(np.float32)/255
    for i,l in enumerate(L):
        if l['tag']!='glitter' or l['bbox'] is None: continue
        bm,op=eff(l['chain'],mode); x0,y0=l['bbox'][:2]
        if offs: x0+=offs[i][0]; y0+=offs[i][1]
        place(img,S[f's{i}'],x0,y0,bm,op,premul)
    for k,m in enumerate(meta):
        if m and m[0] in ('mult','lines'): img[m[2]:m[4],m[1]:m[3]]+=dz[f'd{k}']/255.0
    for i,l in enumerate(L):
        if l['tag']!='fx' or l['bbox'] is None: continue
        bm,op=eff(l['chain'],mode); x0,y0=l['bbox'][:2]
        if offs: x0+=offs[i][0]; y0+=offs[i][1]
        place(img,S[f's{i}'],x0,y0,bm,op,premul)
    return img
if __name__=='__main__':
    F=np.load(D+'/full.npy').astype(np.float32)/255
    from PIL import Image
    for mode in ('nested',):
        for pm in (True,):
            im=compose(mode,pm); e=np.abs(im.clip(0,1)-F).max(2)*255
            print(mode,pm,'mean',e.mean(),'p99',np.percentile(e,99))
            Image.fromarray((im.clip(0,1)*255+.5).astype(np.uint8)).crop((1300,0,2500,700)).save(f'{D}/sim_{mode}_{int(pm)}.png')
