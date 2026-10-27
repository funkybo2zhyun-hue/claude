import numpy as np
from PIL import Image, ImageFilter
def blur(a,s): return np.asarray(Image.fromarray(np.clip(a*255,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(s))).astype(float)/255
def make(T, depth=16, outline=4, plum=(58,24,66)):
    """T: RGBA lettering (white + pink). returns RGBA with extrusion, bevel, thin outline, shadow"""
    pad=depth+60
    N=Image.new('RGBA',(T.width+2*pad,T.height+2*pad),(0,0,0,0)); N.alpha_composite(T,(pad,pad)); T=N
    arr=np.asarray(T).astype(float); rgb=arr[...,:3]; a=arr[...,3]/255
    pink=np.clip((rgb[...,0]-rgb[...,2]-30)/60,0,1)   # 1 on pink letters
    H,W=a.shape
    # face colours with vertical gradient per glyph height (global y)
    yy=np.linspace(0,1,H)[:,None]
    white_face=np.stack([255-14*yy,252-22*yy,246-30*yy],-1)*np.ones((1,W,1))
    pink_face=np.stack([250-10*yy,120-25*yy,155-25*yy],-1)*np.ones((1,W,1))
    face=white_face*(1-pink[...,None])+pink_face*pink[...,None]
    # bevel: light from top-left
    h=blur(a,5)
    gy,gx=np.gradient(h)
    shade=-(gx*0.6+gy*0.8)   # positive where surface faces up-left
    shade=np.clip(shade*14,-1,1)
    inner=np.clip(blur(a,2.5)*1.0,0,1)
    edge=np.clip(1-blur(a,6)/np.maximum(a,1e-3),0,1)*a   # near edges
    face=face*(1+0.22*shade[...,None]*np.clip(edge*3,0,1)[...,None])
    spec=np.clip(shade,0,1)*np.clip(edge*3,0,1)
    face=face+spec[...,None]*40
    # side (extrusion) colours
    side_white=np.array([196,160,200.]); side_pink=np.array([176,52,96.])
    side=side_white*(1-pink[...,None])+side_pink*pink[...,None]
    out=np.zeros((H,W,4))
    def over(dst,col,al):
        da=dst[...,3:4]; aa=al[...,None]
        o=aa+da*(1-aa)
        c=(col*aa+dst[...,:3]*da*(1-aa))/np.maximum(o,1e-6)
        return np.concatenate([c,o],-1)
    # extrusion: from deepest to front, offset down-right
    for i in range(depth,0,-1):
        dx=int(round(i*0.35)); dy=i
        sa=np.zeros_like(a); sa[dy:,dx:]=a[:H-dy,:W-dx]
        sc=np.zeros_like(side); sc[dy:,dx:]=side[:H-dy,:W-dx]
        dark=0.62+0.38*(1-i/depth)
        out=over(out,sc*dark,sa)
    out=over(out,np.clip(face,0,255),a)
    # thin outline around everything
    A=out[...,3]
    m=Image.fromarray((A*255).astype('uint8')).filter(ImageFilter.MaxFilter(outline*2+1)).filter(ImageFilter.GaussianBlur(1))
    ol=np.asarray(m).astype(float)/255
    base=np.zeros((H,W,4)); base=over(base,np.array(plum,float)*np.ones((H,W,1)),ol)
    # drop shadow
    sh=blur(ol,14)*0.6
    sh_s=np.zeros_like(sh); sh_s[10:,4:]=sh[:-10,:-4]
    fin=np.zeros((H,W,4)); fin=over(fin,np.array([15,0,25.])*np.ones((H,W,1)),sh_s)
    fin=over(fin,base[...,:3],base[...,3]); fin=over(fin,out[...,:3],out[...,3])
    img=np.dstack([fin[...,:3],fin[...,3]*255]).clip(0,255).astype('uint8')
    return Image.fromarray(img), pad
