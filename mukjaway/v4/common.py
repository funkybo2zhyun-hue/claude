import numpy as np
from PIL import Image, ImageFilter
K=400/72  # vec_400 px per pt
W,H=2560,768
_V=None; _BG=None
def V():
    global _V
    if _V is None: _V=Image.open('/root/mk/src/vec_400.png')
    return _V
def BG():
    global _BG
    if _BG is None: _BG=Image.open('/root/mk/src/bg_rgb.png').convert('RGB')
    return _BG
def el(x0,y0,x1,y1):
    c=V().crop((int(x0*K),int(y0*K),int(x1*K),int(y1*K))); return c.crop(c.getbbox())
def rs(img,s):
    return img.resize((max(1,round(img.width*s)),max(1,round(img.height*s))),Image.LANCZOS)
