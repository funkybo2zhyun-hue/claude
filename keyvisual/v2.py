import sys; sys.path.insert(0,'.')
from compose import *
from logos import logos
import math
canvas=Image.new("RGBA",(W,H),SKY+(255,))
BAND=150; GY=H-BAND   # top of the partner-logo band

def fade_x(im, left=0, right=0):
    a=np.asarray(im.getchannel('A')).astype(float); w=im.width; x=np.arange(w)
    r=np.ones(w)
    if left: r=np.minimum(r,np.clip(x/left,0,1))
    if right: r=np.minimum(r,np.clip((w-1-x)/right,0,1))
    im=im.copy(); im.putalpha(Image.fromarray((a*r[None,:]).astype(np.uint8))); return im

# clouds
cl=[(992,31,1355,168),(129,93,492,230)]
C1=vec([0,0,1417,400],1,rects=[cl[0]]) if False else None
for rect,h,x,y,flip in [(cl[0],120,560,18,False),(cl[1],100,1880,40,True),(cl[0],80,1210,150,True),(cl[1],70,820,330,False),(cl[0],70,1640,300,False)]:
    c=vec([0,0,1417,400],h,rects=[rect])
    if flip: c=c.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(c,(x,y))

# center landscape: flat hills in the poster palette, matching the wings' horizon
ORANGE=(0xF3,0x6C,0x29); YELLOW=(0xFC,0xB3,0x26); TEAL=(0x2F,0x6F,0x61); RIVER=(0x00,0xA3,0xCF)
S2=2; land=Image.new("RGBA",(W*S2,H*S2),(0,0,0,0)); ld=ImageDraw.Draw(land)
def hill(base, peaks, color):
    pts=[(0,H*S2)]
    for x in range(0,W+1,4):
        y=base-sum(h*math.exp(-((x-c)/w)**2) for c,w,h in peaks)
        pts.append((x*S2,y*S2))
    pts.append((W*S2,H*S2)); ld.polygon(pts,fill=color+(255,))
hill(300,[(1450,380,95),(2250,380,260),(850,300,55)],YELLOW)
hill(305,[(380,300,185),(1100,300,80),(1700,260,50)],ORANGE)
hill(310,[(1900,300,70),(2350,260,100),(250,220,60)],TEAL)
ld.rectangle([0,292*S2,W*S2,H*S2],fill=RIVER+(255,))
pts=[(0,H*S2)]+[(x*S2,(338+12*math.sin(x/170)+6*math.sin(x/53))*S2) for x in range(0,W+1,4)]+[(W*S2,H*S2)]
ld.polygon(pts,fill=GRASS+(255,))
land=land.resize((W,H),Image.LANCZOS); canvas.alpha_composite(land)
# wings
WH=GY+40
L=scene([125,1740,1180,2880],WH); L=fade_x(L,0,130)
R=scene([1640,1740,2712,2880],WH); R=fade_x(R,130,0)
canvas.alpha_composite(L,(0,GY-WH+40)); canvas.alpha_composite(R,(W-R.width,GY-WH+40))

# festoon lights strung between the wings
x0,x1,yb,sag=560,2000,560,30
lay=Image.new("RGBA",(W*2,H*2),(0,0,0,0)); fd=ImageDraw.Draw(lay)
cur=lambda x: yb+sag*(1-((x-(x0+x1)/2)/((x1-x0)/2))**2)
fd.line([(x*2,cur(x)*2) for x in range(x0,x1+1,4)],fill=(43,42,42,255),width=6)
for x in range(x0+30,x1,58):
    y=cur(x)+9; fd.ellipse([(x-8)*2,(y-8)*2,(x+8)*2,(y+8)*2],fill=(255,243,196,255))
canvas.alpha_composite(lay.resize((W,H),Image.LANCZOS))
# peach branches in the top corners
pr=vec([1120,170,1700,760],330); pl=vec([-300,680,280,1120],250)
canvas.alpha_composite(pl,(0,-30)); canvas.alpha_composite(pr,(W-pr.width,-40))

# title block, centered
title=vec([250,140,1140,400],350)
sub=vec([300,400,1100,530],122)
ty=30
canvas.alpha_composite(title,((W-title.width)//2,ty))
canvas.alpha_composite(sub,((W-sub.width)//2,ty+350+14))

# partner logo band
dr=ImageDraw.Draw(canvas)
dr.rectangle([0,GY,W,H],fill=WHITE+(255,))
dr.rectangle([0,GY,W,GY+8],fill=RED+(255,))
lg=logos([200,660,1200,880])
cmd=Image.new("RGBA",(max(lg[6].width,lg[9].width),lg[6].height+40+lg[9].height),(0,0,0,0))
cmd.alpha_composite(lg[6],((cmd.width-lg[6].width)//2,0)); cmd.alpha_composite(lg[9],((cmd.width-lg[9].width)//2,lg[6].height+40))
order=[lg[0],lg[1],lg[3],lg[2],lg[4],lg[5],cmd,lg[7],lg[8]]
# size by equal visual area, capped by height
A=13500; MAXH=92; sized=[]
for im in order:
    h=min(MAXH, math.sqrt(A*im.height/im.width)); sized.append(im.resize((round(im.width*h/im.height),round(h)),Image.LANCZOS))
margin=110; total=sum(s.width for s in sized); gap=(W-2*margin-total)/(len(sized)-1)
x=margin; cy=GY+8+(BAND-8)//2
for s in sized:
    canvas.alpha_composite(s,(round(x),cy-s.height//2)); x+=s.width+gap
canvas.convert("RGB").save(sys.argv[1]); print("gap",round(gap),[s.size for s in sized])
