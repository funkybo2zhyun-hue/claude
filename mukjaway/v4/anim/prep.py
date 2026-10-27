# Loop prep: clean plate without the busker (left copy) and the walking couple (right copy),
# plus their sprites at canvas scale, so they can move without leaving holes.
import sys; sys.path.insert(0,'/root/mk/lib')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from lama import inpaint
s=0.38; Y0=3290; Y1=Y0+H/s; LX1=2900; RX0=1836
LW=round(LX1*s); RW=round((4392-RX0)*s); RX=W-RW
def ty(y): return (y-Y0)*H/(Y1-Y0)
def tL(x): return x*LW/LX1
def tRl(x): return (x-RX0)*RW/(4392-RX0)
bg=BG()
L=Image.open('/root/mk/v4/L.png'); R=Image.open('/root/mk/v4/R.png')
def clean_window(copy, tx, box, masks, CS=0.6, passes=2):
    """inpaint person(s) on a wide source window, paste the cleaned window into the copy"""
    X0,Yt,X1,Yb=box
    ctx=bg.crop(box); ctx=ctx.resize((round(ctx.width*CS),round(ctx.height*CS)),Image.LANCZOS)
    m=Image.new('L',ctx.size,0)
    for name,ox,oy in masks:
        a=Image.open(name).getchannel('A')
        a=a.resize((round(a.width*CS),round(a.height*CS)),Image.LANCZOS).point(lambda v:255 if v>20 else 0)
        m.paste(a,(round((ox-X0)*CS),round((oy-Yt)*CS)),a)
    m=m.filter(ImageFilter.MaxFilter(9))
    ctx=inpaint(ctx,m)
    for _ in range(passes-1): ctx=inpaint(ctx,m.filter(ImageFilter.MaxFilter(21)))
    pw=ctx.resize((round((X1-X0)*s),round((Yb-Yt)*s)),Image.LANCZOS)
    # paste only the repaired person area (not the whole window, which the 0.6x round trip softens)
    pm=m.filter(ImageFilter.MaxFilter(15)).resize(pw.size,Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    copy.paste(pw,(round(tx(X0)),round(ty(Yt))),pm)
    return copy
L=clean_window(L,tL,(1600,3950,2700,5200),[('/root/mk/cut2/busker.png',1820,4150)])
# keep the original monitor speaker in front of the busker's feet
R=clean_window(R,tRl,(2300,4050,3700,5400),[('/root/mk/cut/couple.png',2550,4250)])
L.save('/root/mk/anim/Lc.png'); R.save('/root/mk/anim/Rc.png')
cv=Image.new('RGB',(W,H)); cv.paste(R,(RX,0)); cv.paste(L,(0,0))
g0,g1=LW,RX; mid=(g0+g1)//2
cv.paste(L.crop((2*g0-mid,0,g0,H)).transpose(Image.FLIP_LEFT_RIGHT),(g0,0))
cv.paste(R.crop((0,0,g1-mid,H)).transpose(Image.FLIP_LEFT_RIGHT),(mid,0))
M=Image.new('L',(W,H),0); d=ImageDraw.Draw(M)
d.rectangle([g0-6,0,g0+30,H],fill=255); d.rectangle([mid-40,0,mid+40,H],fill=255)
inpaint(cv,M).save('/root/mk/anim/plate_clean.png')
# sprites at canvas scale (+ canvas position)
def sprite(path,ox,oy,tx,name,xoff=0):
    im=Image.open(path); sp=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    x,y=tx(ox)+xoff,ty(oy); sp.save(f'/root/mk/anim/{name}.png'); print(name,round(x),round(y),sp.size)
sprite('/root/mk/cut2/busker.png',1820,4150,tL,'sp_busker')
sprite('/root/mk/cut/couple.png',2550,4250,tRl,'sp_couple',xoff=RX)
# monitor speaker patch (static, drawn over the busker's feet)
mon=L.crop((round(tL(1897)),round(ty(4786)),round(tL(2073)),round(ty(4900))))
mon.save('/root/mk/anim/sp_monitor.png'); print('monitor',round(tL(1897)),round(ty(4786)))
