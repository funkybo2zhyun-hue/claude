import sys,numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typo2 import font,tlayer,outlined,pad_img,PLUM,GOLD,CREAM
OUT=sys.argv[1]
W,H=2304,768
coefs=np.load('bgcoef.npy')
def F(x,y):
    x=x/300.;y=y/300.
    return np.stack([np.ones_like(x),x,y,x*x,y*y,x*y,y**3,x*y*y,x*x*y],-1)
def bg_at(px,py): return np.stack([F(px,py)@c for c in coefs],-1)
cy,cx=np.mgrid[0:H,0:W].astype(float)
# poster gradient mapped vertically (poster y 150..600), gentle horizontal symmetry
ppx=330+np.abs(cx-1152)/1152*200; ppy=150+cy/H*430
img=bg_at(ppx,ppy)
d=np.clip(np.abs(cx-1152)/1152,0,1)
img*=(1-0.28*d**1.6)[...,None]
img*=(1-0.18*np.clip(1-cy/320,0,1))[...,None]
# warm glows behind the two stages and behind the title
for gx,gy,rx,ry,c in [(270,620,420,300,(40,22,14)),(2030,620,420,300,(40,22,14))]:
    rr=np.sqrt(((cx-gx)/rx)**2+((cy-gy)/ry)**2); img+=np.exp(-rr**2*1.4)[...,None]*np.array(c,float)
