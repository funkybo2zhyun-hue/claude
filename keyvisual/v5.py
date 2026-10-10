"""v5: v4 layout with the string lights moved to a top garland, more ambient motion, 20 s @ 60 fps loop.
usage: python3 v5.py still.png [loop.mp4]"""
import sys, math, subprocess; sys.path.insert(0,'.')
from compose import vec, W, H, SKY, RED, WHITE
from objs import D, draw, obj
from logos import logos
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
S=1.1; Y0=880
BAND=96; GY=H-BAND
cy=lambda pt: round((pt-Y0)*S)
T=20.0; FPS=60                     # loop length (s) and frame rate
TAU=2*math.pi

# ---------- static landscape ----------
bg_items=[x for i,x in enumerate(D) if (3<=i<=117 and x.get('rect') is not None and x['type']!='clip' and (x['rect'].y1<1232 or x['rect'].width>250)) or i==22 or (117<i<300 and x.get('rect') is not None and x['rect'].width<12 and x['rect'].y1<1232 and x['type']=='f')]
CL=(62,Y0,1356,1500)
base=Image.new("RGBA",(W,H),SKY+(255,))
land=draw(bg_items, CL, S, sx=W/((CL[2]-CL[0])*S))
base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,0))

# ---------- sprites ----------
cl=[(992,31,1355,168),(129,93,492,230)]
clouds=[]
for rect,h,x,y,flip,amp,ph in [(cl[1],95,330,24,False,60,0.0),(cl[0],110,1980,8,True,50,1.7),(cl[0],70,720,120,False,80,3.1),(cl[1],62,1700,150,True,70,4.4)]:
    c=vec([0,0,1417,400],h,rects=[rect])
    if flip: c=c.transpose(Image.FLIP_LEFT_RIGHT)
    clouds.append((c,x,y,amp,ph))

def sprite(bbox,x,y=None,excl=()):
    im,(ox,oy)=obj(bbox,S,excl=excl); return [im,x,cy(oy) if y is None else y]
still_objs=[sprite([0,1040,460,1420],0,excl=(491,)), sprite([480,1060,720,1290],520),
            sprite([980,1075,1460,1420],W-round(480*S)-6), sprite([490,1310,770,1500],300),
            sprite([405,1250,545,1320],640,y=478)]
balloon=sprite([860,1080,985,1320],1905)
dancers=sprite([700,1195,890,1350],1715)
for o in still_objs: base.alpha_composite(o[0],(o[1],o[2]))

# top garland: scalloped swags of bulbs hanging from the top edge
SW=8; anchors=np.linspace(-40,W+40,SW+1)
wire=Image.new("RGBA",(W*2,260*2),(0,0,0,0)); wd=ImageDraw.Draw(wire); BULBS=[]
for a0,a1 in zip(anchors[:-1],anchors[1:]):
    pts=[(a0+(a1-a0)*t, -4+70*4*t*(1-t)) for t in np.linspace(0,1,90)]
    wd.line([(x*2,y*2) for x,y in pts],fill=(43,42,42,255),width=6)
    for t in np.linspace(0.1,0.9,6):
        x=a0+(a1-a0)*t; y=-4+70*4*t*(1-t)
        wd.line([(x*2,y*2),(x*2,(y+10)*2)],fill=(43,42,42,255),width=4)
        BULBS.append((x,y+20))
wire=wire.resize((W,260),Image.LANCZOS)
BULB_COL=[(255,236,160),(255,214,120),(255,246,214),(255,190,170)]
def glow_sprite(r,col,alpha):
    g=Image.new("RGBA",(r*8,r*8),(0,0,0,0)); gd=ImageDraw.Draw(g)
    gd.ellipse([r*1.5,r*1.5,r*6.5,r*6.5],fill=col+(alpha,))
    return g.filter(ImageFilter.GaussianBlur(r*0.9))
GLOWS=[[glow_sprite(10,c,int(40+215*l/7)) for l in range(8)] for c in BULB_COL]
def flare(size,alpha):
    f=Image.new("RGBA",(size,size),(0,0,0,0)); fd=ImageDraw.Draw(f); c=size//2
    fd.polygon([(c,0),(c+3,c-3),(size,c),(c+3,c+3),(c,size),(c-3,c+3),(0,c),(c-3,c-3)],fill=(255,255,240,alpha))
    return f.filter(ImageFilter.GaussianBlur(0.8))
FLARE=flare(54,255)
table=still_objs.pop(3)                       # picnic table couple bobs gently
picnic=still_objs.pop(1)                      # umbrella picnic sways a touch
base=Image.new("RGBA",(W,H),SKY+(255,)); base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,0))
for o in still_objs: base.alpha_composite(o[0],(o[1],o[2]))

# drifting peach-blossom petals (each falls 1-2 full screen heights per loop, so the loop is seamless)
rng=np.random.default_rng(7)
def petal(h):
    p=Image.new("RGBA",(h*4,h*4),(0,0,0,0)); pd=ImageDraw.Draw(p)
    pd.ellipse([h*0.6,h*1.4,h*3.4,h*2.6],fill=(248,170,160,235)); pd.ellipse([h*1.2,h*1.7,h*2.6,h*2.2],fill=(255,205,196,235))
    return p.resize((h*2,h*2),Image.LANCZOS)
PETALS=[]
for i in range(18):
    h=int(rng.integers(12,20)); sp=petal(h)
    PETALS.append(dict(rots=[sp.rotate(a,resample=Image.BICUBIC,expand=True) for a in range(0,360,15)],
        x0=float(rng.uniform(0,W)), y0=float(rng.uniform(0,GY)), fall=int(rng.integers(1,3)),
        sway=float(rng.uniform(30,90)), sw=int(rng.integers(1,4)), ph=float(rng.uniform(0,TAU)), spin=int(rng.choice([-2,-1,1,2]))))

pr=vec([1120,170,1700,760],300); pl=vec([-300,680,280,1120],230)
base_still=None

# title lock-up as one sprite (title + subtitle + halo + drop shadow)
title=vec([250,140,1140,400],330); sub=vec([300,400,1100,530],118)
TY=74
tw=max(title.width,sub.width)+160; th=330+12+118+120
lock=Image.new("RGBA",(tw,th),(0,0,0,0)); ink=Image.new("RGBA",(tw,th),(0,0,0,0))
ink.alpha_composite(title,((tw-title.width)//2,60)); ink.alpha_composite(sub,((tw-sub.width)//2,60+330+12))
a=ink.getchannel('A')
halo=Image.new("RGBA",(tw,th),(255,255,255,0)); halo.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(26)).point(lambda v:int(v*0.35)))
drop=Image.new("RGBA",(tw,th),(120,20,20,0)); drop.putalpha(a.filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.45)))
lock.alpha_composite(halo); lock.alpha_composite(drop,(0,8)); lock.alpha_composite(ink)
INK_A=np.asarray(a).astype(np.float32)/255
LX=(W-tw)//2; LY=TY-60

# partner band: slimmer strip, smaller logos
band=Image.new("RGBA",(W,BAND),WHITE+(255,)); bd=ImageDraw.Draw(band); bd.rectangle([0,0,W,4],fill=RED+(255,))
lg=logos([200,660,1200,880])
cmd=Image.new("RGBA",(max(lg[6].width,lg[9].width),lg[6].height+40+lg[9].height),(0,0,0,0))
cmd.alpha_composite(lg[6],((cmd.width-lg[6].width)//2,0)); cmd.alpha_composite(lg[9],((cmd.width-lg[9].width)//2,lg[6].height+40))
order=[lg[0],lg[1],lg[3],lg[2],lg[4],lg[5],cmd,lg[7],lg[8]]
A=4600; MAXH=56; sized=[]
for im in order:
    h=min(MAXH, math.sqrt(A*im.height/im.width)); sized.append(im.resize((round(im.width*h/im.height),round(h)),Image.LANCZOS))
margin=260; total=sum(s.width for s in sized); gap=(W-2*margin-total)/(len(sized)-1)
x=margin; my=4+(BAND-4)//2
for s in sized: band.alpha_composite(s,(round(x),my-s.height//2)); x+=s.width+gap

def rot(im, deg, pivot):
    return im.rotate(deg, resample=Image.BICUBIC, center=pivot)

def frame(t, still=False):
    p=t/T
    f=base.copy()
    for c,x,y,amp,ph in clouds:
        f.alpha_composite(c,(round(x+amp*math.sin(TAU*p+ph)),y))
    im,x,y=picnic; f.alpha_composite(im,(x,round(y+2*math.sin(TAU*p*4))))
    im,x,y=table;  f.alpha_composite(im,(x,round(y+3*math.sin(TAU*p*5+1.0))))
    im,x,y=balloon; f.alpha_composite(im,(x,round(y+6*math.sin(TAU*p*3))))
    im,x,y=dancers; f.alpha_composite(im,(x,round(y-10*abs(math.sin(TAU*p*20)))))
    if not still:
        for d in PETALS:
            yy=(d["y0"]+(GY+80)*d["fall"]*p)%(GY+80)-40
            xx=(d["x0"]+d["sway"]*math.sin(TAU*p*d["sw"]+d["ph"]))%W
            r=d["rots"][int((p*24*d["spin"]+d["ph"]*4))%24]
            f.alpha_composite(r,(int(xx-r.width/2),int(yy-r.height/2)))
    # garland: wire, then bulbs that glow and twinkle in waves, with a star flare at their peak
    f.alpha_composite(wire,(0,0))
    for i,(bx,by) in enumerate(BULBS):
        k=0.5+0.5*math.sin(TAU*(p*8)-i*0.55)            # chasing wave along the garland
        k=k*0.75+0.25*(0.5+0.5*math.sin(TAU*p*13+i*2.1)) # plus individual flicker
        col=i%4; g=GLOWS[col][min(7,int(k*8))]
        f.alpha_composite(g,(int(bx-g.width/2),int(by-g.height/2)))
        dr=ImageDraw.Draw(f); r=8+2*k
        dr.ellipse([bx-r,by-r,bx+r,by+r],fill=BULB_COL[col]+(255,))
        if k>0.9 and not still:
            fl=FLARE; sc=int(30+60*(k-0.9)/0.1)
            fl=fl.resize((sc,sc),Image.LANCZOS)
            f.alpha_composite(fl,(int(bx-sc/2),int(by-sc/2)))
    f.alpha_composite(rot(pl,2.5*math.sin(TAU*p*2),(0,0)),(0,-24))
    f.alpha_composite(rot(pr,-2.5*math.sin(TAU*p*2+1.0),(pr.width,0)),(W-pr.width,-36))
    lk=lock
    for st in (0.08,0.58):
        sp=(p-st)/0.22
        if 0<sp<1:
            xs=np.arange(tw)[None,:]; ys=np.arange(th)[:,None]
            cx=-300+(tw+600)*sp
            band_=np.clip(1-np.abs((xs+0.35*ys)-cx)/90,0,1)**2
            sh=Image.new("RGBA",(tw,th),(255,255,255,0)); sh.putalpha(Image.fromarray((band_*INK_A*170).astype(np.uint8)))
            lk=lock.copy(); lk.alpha_composite(sh)
    f.alpha_composite(lk,(LX,round(LY+7*math.sin(TAU*p*2))))
    f.alpha_composite(band,(0,GY))
    return f.convert("RGB")

frame(0,still=True).save(sys.argv[1]); print("still saved")
if len(sys.argv)>2:
    n=int(T*FPS)
    ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-preset","slow","-crf","17","-g","120","-pix_fmt","yuv420p","-movflags","+faststart",sys.argv[2]],stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i/FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("video", n, "frames")
