# v4 stage 1: scene plate — the poster's market split around the centre logo (no enlargement).
# Left copy keeps the busker; right copy starts where the logo ends, with the busker and the
# front diner's shoulder removed so nobody appears twice. The strip behind the logo is
# pre-filled with mirrored neighbours and only its seams are inpainted (all hidden by the logo).
import sys; sys.path.insert(0,'/root/mk/lib')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from lama import inpaint
s=0.38; Y0=3290; Y1=Y0+H/s
LX1=2900; RX0=1836
LW=round(LX1*s); RW=round((4392-RX0)*s); RX=W-RW
def ty(y): return (y-Y0)*H/(Y1-Y0)
def tL(x): return x*LW/LX1
def tR(x): return x*RW/(4392-RX0)-RX0*RW/(4392-RX0)   # local x inside the right copy
bg=BG()
L=bg.crop((0,Y0,LX1,round(Y1))).resize((LW,H),Image.LANCZOS)
R=bg.crop((RX0,Y0,4392,round(Y1))).resize((RW,H),Image.LANCZOS)
def cutmask(size,name,ox,oy,tx,dil):
    a=Image.open(f'/root/mk/cut/{name}.png').getchannel('A')
    a2=a.resize((round(a.width*s),round(a.height*s)),Image.LANCZOS).point(lambda v:255 if v>20 else 0)
    m=Image.new('L',size,0); m.paste(a2,(round(tx(ox)),round(ty(oy))))
    return m.filter(ImageFilter.MaxFilter(dil))
# left copy: walking couple's man bleeding in at the right edge
mL=cutmask(L.size,'couple',2550,4250,tL,9)
L=inpaint(L,mL)
# right copy: busker (+guitar, mic, stands) and the guest cut by the copy edge are inpainted on a
# wider source window (context on both sides), then the cleaned window is pasted into the copy.
CX0,CY0,CX1,CY1,CS=1560,3950,2760,5200,0.6
ctx=bg.crop((CX0,CY0,CX1,CY1)); ctx=ctx.resize((round(ctx.width*CS),round(ctx.height*CS)),Image.LANCZOS)
def cx(x): return (x-CX0)*CS
def cy(y): return (y-CY0)*CS
mC=Image.new('L',ctx.size,0)
a=Image.open('/root/mk/cut/busker.png').getchannel('A')
a=a.resize((round(a.width*CS),round(a.height*CS)),Image.LANCZOS).point(lambda v:255 if v>20 else 0)
mC.paste(a,(round(cx(1850)),round(cy(4000))),a)
dC=ImageDraw.Draw(mC)
dC.polygon([(cx(2140),cy(4465)),(cx(2345),cy(4355)),(cx(2360),cy(4425)),(cx(2150),cy(4535))],fill=255)
dC.rectangle([cx(2115),cy(4430),cx(2245),cy(4610)],fill=255)
dC.rectangle([cx(2105),cy(4265),cx(2215),cy(4350)],fill=255)
dC.rectangle([cx(2155),cy(4265),cx(2212),cy(4975)],fill=255)
dC.rectangle([cx(2100),cy(4870),cx(2270),cy(4995)],fill=255)
dC.rectangle([cx(1945),cy(4430),cx(2008),cy(4930)],fill=255)
dl=Image.open('/root/mk/cut/dinL.png').getchannel('A')
dl=dl.resize((round(dl.width*CS),round(dl.height*CS)),Image.LANCZOS).point(lambda v:255 if v>20 else 0)
mC.paste(dl,(round(cx(0)),round(cy(4500))),dl)   # front diner's head/shoulder (ground and wall behind)
dC.rectangle([cx(1832),cy(4385),cx(1965),cy(4810)],fill=255)
mC=mC.filter(ImageFilter.MaxFilter(7))
ctx=inpaint(ctx,mC)
# second pass over a wider ring removes the lighter ghost LaMa leaves on the plain wall
ctx=inpaint(ctx,mC.filter(ImageFilter.MaxFilter(25)))
ctx.save('/root/mk/v4/R_ctx.png')
# paste the cleaned window (only the part right of RX0) into the right copy
pw=ctx.crop((round(cx(RX0)),0,ctx.width,ctx.height))
pw=pw.resize((round((CX1-RX0)*s),round((CY1-CY0)*s)),Image.LANCZOS)
pm=Image.new('L',pw.size,0); ImageDraw.Draw(pm).rectangle([0,6,pw.width-8,pw.height-8],fill=255)
pm=pm.filter(ImageFilter.GaussianBlur(4))
R.paste(pw,(0,round(ty(CY0))),pm)
# front diner's shoulder at the copy edge (ground behind) — small, inpaint in place
mR=cutmask(R.size,'dinL',0,4500,tR,9)
R=inpaint(R,mR)
L.save('/root/mk/v4/L.png'); R.save('/root/mk/v4/R.png')
# assemble; strip behind the logo = mirrored neighbours, seams inpainted
cv=Image.new('RGB',(W,H)); cv.paste(R,(RX,0)); cv.paste(L,(0,0))
g0,g1=LW,RX; mid=(g0+g1)//2
cv.paste(L.crop((2*g0-mid,0,g0,H)).transpose(Image.FLIP_LEFT_RIGHT),(g0,0))
cv.paste(R.crop((0,0,g1-mid,H)).transpose(Image.FLIP_LEFT_RIGHT),(mid,0))
M=Image.new('L',(W,H),0); d=ImageDraw.Draw(M)
d.rectangle([g0-6,0,g0+30,H],fill=255); d.rectangle([mid-40,0,mid+40,H],fill=255)
cv.save('/root/mk/v4/plate_raw.png'); M.save('/root/mk/v4/plate_mask.png')
inpaint(cv,M).save('/root/mk/v4/plate.png')
print('LW',LW,'RX',RX,'gap',g0,g1)
