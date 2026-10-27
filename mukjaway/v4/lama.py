import numpy as np, torch
from PIL import Image
_m=None
def inpaint(img, mask):
    """img: PIL RGB, mask: PIL L (255=hole). returns PIL RGB"""
    global _m
    if _m is None:
        torch.set_num_threads(4)
        _m=torch.jit.load('/root/mk/src/big-lama.pt',map_location='cpu'); _m.eval()
    a=np.asarray(img.convert('RGB')).astype(np.float32)/255.
    m=(np.asarray(mask.convert('L'))>127).astype(np.float32)
    h,w=m.shape; ph=(8-h%8)%8; pw=(8-w%8)%8
    a2=np.pad(a,((0,ph),(0,pw),(0,0)),mode='reflect'); m2=np.pad(m,((0,ph),(0,pw)),mode='reflect')
    t=torch.from_numpy(a2).permute(2,0,1)[None]; mt=torch.from_numpy(m2)[None,None]
    with torch.no_grad(): o=_m(t,mt)[0].permute(1,2,0).numpy()
    o=o[:h,:w]; o=np.clip(o*255,0,255).astype(np.uint8)
    res=np.where(m[...,None]>0.5,o,(a*255).astype(np.uint8))
    return Image.fromarray(res)
