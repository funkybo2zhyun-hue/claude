"""v6: v5 with each person animated on their own (occasional slow hops, nods, sways),
a lighter top garland with softer twinkle. 20 s @ 60 fps seamless loop.
usage: python3 v6.py still.png [loop.mp4]"""
import sys, math, subprocess; sys.path.insert(0,'.')
from compose import vec, W, H, SKY, RED, WHITE
from objs import D, draw, obj
from logos import logos
from split import split
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
S=1.1; Y0=880
BAND=58; GY=H-BAND
OFFY=36                            # push the whole scene down a little to balance the slimmer strip
cy=lambda pt: round((pt-Y0)*S)+OFFY
T=20.0; FPS=60                     # loop length (s) and frame rate
TAU=2*math.pi

# ---------- static landscape ----------
bg_items=[x for i,x in enumerate(D) if (3<=i<=117 and x.get('rect') is not None and x['type']!='clip' and (x['rect'].y1<1232 or x['rect'].width>250)) or i==22 or (117<i<300 and x.get('rect') is not None and x['rect'].width<12 and x['rect'].y1<1232 and x['type']=='f')]
CL=(62,Y0,1356,1545)
base=Image.new("RGBA",(W,H),SKY+(255,))
land=draw(bg_items, CL, S, sx=W/((CL[2]-CL[0])*S))
base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,OFFY))

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
            sprite([405,1250,545,1320],640,y=478+OFFY)]

def actors(bbox, parts, x, y=None, wide=60, keep=None):
    # people/parts of one illustration group as separate sprites sharing one origin
    from split import split as _split
    import pymupdf
    sp,(ox,oy)=_split(bbox, parts, S)
    # very wide shapes (shadows, benches, mats) stay in the static 'rest' layer
    u=None
    for im in sp.values():
        bb=im.getchannel('A').getbbox()
        if bb: u=bb if u is None else (min(u[0],bb[0]),min(u[1],bb[1]),max(u[2],bb[2]),max(u[3],bb[3]))
    sp={n:im.crop(u) for n,im in sp.items()}
    X=x; Y=cy(oy+u[1]/S) if y is None else y
    return sp,(X,Y)
for o in still_objs: base.alpha_composite(o[0],(o[1],o[2]))

# top garland: a few shallow swags, bulbs sitting right on the wire
SW=5; anchors=np.linspace(-30,W+30,SW+1)
wire=Image.new("RGBA",(W*2,160*2),(0,0,0,0)); wd=ImageDraw.Draw(wire); BULBS=[]
for a0,a1 in zip(anchors[:-1],anchors[1:]):
    pts=[(a0+(a1-a0)*t, -2+46*4*t*(1-t)) for t in np.linspace(0,1,90)]
    wd.line([(x*2,y*2) for x,y in pts],fill=(60,52,48,255),width=5)
    for t in np.linspace(0.14,0.86,5):
        BULBS.append((a0+(a1-a0)*t, -2+46*4*t*(1-t)+6))
wire=wire.resize((W,160),Image.LANCZOS)
DIM=np.array([214,170,96]); BRIGHT=np.array([255,247,214])
def soft_glow(r):
    g=Image.new("L",(r*6,r*6),0); ImageDraw.Draw(g).ellipse([r*1.6,r*1.6,r*4.4,r*4.4],fill=255)
    return g.filter(ImageFilter.GaussianBlur(r*0.7))
GLOW_A=soft_glow(8)
GLOWS=[]
for l in range(10):
    g=Image.new("RGBA",GLOW_A.size,(255,226,150,0)); g.putalpha(GLOW_A.point(lambda v,l=l:int(v*(0.10+0.35*l/9)))); GLOWS.append(g)
still_objs.pop(3); still_objs.pop(1)          # table couple + picnic are rebuilt below as actors
base=Image.new("RGBA",(W,H),SKY+(255,)); base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,OFFY))
for o in still_objs: base.alpha_composite(o[0],(o[1],o[2]))

DANCE=actors([700,1195,890,1350],[('d1',[700,1195,762,1350]),('d2',[762,1195,822,1340]),('d3',[822,1195,890,1350])],1715)
PICNIC=actors([480,1060,720,1290],[('umb',[540,1060,700,1150])],520)
TABLE=actors([490,1310,770,1500],[('man',[490,1310,580,1420]),('woman',[580,1310,660,1420])],300)
BALLOON=actors([860,1080,985,1320],[('balloons',[880,1080,960,1140]),('dad',[880,1140,960,1300])],1905)
# static leftovers (shadows, mats, table, bench) go into the base
for sp,(x,y) in (DANCE,PICNIC,TABLE,BALLOON): base.alpha_composite(sp['rest'],(x,y))

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
TY=88
tw=max(title.width,sub.width)+160; th=330+12+118+120
lock=Image.new("RGBA",(tw,th),(0,0,0,0)); ink=Image.new("RGBA",(tw,th),(0,0,0,0))
ink.alpha_composite(title,((tw-title.width)//2,60)); ink.alpha_composite(sub,((tw-sub.width)//2,60+330+12))
a=ink.getchannel('A')
halo=Image.new("RGBA",(tw,th),(255,255,255,0)); halo.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(26)).point(lambda v:int(v*0.35)))
drop=Image.new("RGBA",(tw,th),(120,20,20,0)); drop.putalpha(a.filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.45)))
lock.alpha_composite(halo); lock.alpha_composite(drop,(0,8)); lock.alpha_composite(ink)
INK_A=np.asarray(a).astype(np.float32)/255
LX=(W-tw)//2; LY=TY-60

# credit strip: thin, low-weight row with organizers (left) and partner brands (right)
band=Image.new("RGBA",(W,BAND),WHITE+(255,)); bd=ImageDraw.Draw(band); bd.rectangle([0,0,W,2],fill=RED+(255,))
lg=logos([200,660,1200,880]); org=logos([100,1840,1320,1960])
cmd=Image.new("RGBA",(max(lg[6].width,lg[9].width),lg[6].height+40+lg[9].height),(0,0,0,0))
cmd.alpha_composite(lg[6],((cmd.width-lg[6].width)//2,0)); cmd.alpha_composite(lg[9],((cmd.width-lg[9].width)//2,lg[6].height+40))
partners=[lg[0],lg[1],lg[3],lg[2],lg[4],lg[5],cmd,lg[7],lg[8]]
organizers=[org[1],org[0],org[2],org[3],org[4]]
def fit(ims,A,MAXH):
    out=[]
    for im in ims:
        h=min(MAXH, math.sqrt(A*im.height/im.width)); out.append(im.resize((round(im.width*h/im.height),round(h)),Image.LANCZOS))
    return out
P=fit(partners,1700,32); O=fit(organizers,1700,32)
margin=240; gapP=46; gapO=46; div=70
total=sum(s.width for s in O)+gapO*(len(O)-1)+div*2+sum(s.width for s in P)+gapP*(len(P)-1)
x=(W-total)/2; my=2+(BAND-2)//2
for s in O: band.alpha_composite(s,(round(x),my-s.height//2)); x+=s.width+gapO
x+=div-gapO; bd.line([(round(x),my-14),(round(x),my+14)],fill=(200,200,200,255),width=2); x+=div
for s in P: band.alpha_composite(s,(round(x),my-s.height//2)); x+=s.width+gapP

def rot(im, deg, pivot):
    return im.rotate(deg, resample=Image.BICUBIC, center=pivot)

def ease_hop(p, at, dur, h):
    """single slow hop centred at loop phase `at` lasting `dur` seconds"""
    u=((p-at+0.5)%1.0-0.5)*T/dur+0.5
    return -h*math.sin(math.pi*u)**1.5 if 0<u<1 else 0.0

def place(f, sp, name, origin, angle=0.0, pivot=None, dx=0.0, dy=0.0):
    im=sp[name]
    if angle: im=im.rotate(angle, resample=Image.BICUBIC, center=pivot)
    f.alpha_composite(im,(round(origin[0]+dx),round(origin[1]+dy)))

def frame(t, still=False):
    p=t/T
    f=base.copy()
    for c,x,y,amp,ph in clouds:
        f.alpha_composite(c,(round(x+amp*math.sin(TAU*p+ph)),y))
    # picnic: only the umbrella canopy rocks in the breeze
    sp,o=PICNIC; w,h=sp['umb'].size
    place(f,sp,'umb',o,angle=2.2*math.sin(TAU*p*3),pivot=(w*0.45,h*0.75))
    # table couple: he leans in to chat now and then, she laughs back
    sp,o=TABLE; w,h=sp['man'].size
    lean=2.5*max(0,math.sin(TAU*p*2))**2
    place(f,sp,'man',o,angle=-lean,pivot=(w*0.25,h*0.62))
    place(f,sp,'woman',o,angle=1.8*max(0,math.sin(TAU*p*2-1.2))**2,pivot=(w*0.45,h*0.62),dy=-2*max(0,math.sin(TAU*p*4-0.6)))
    # dancers: gentle sway, each takes one slow hop at their own moment
    sp,o=DANCE; w,h=sp['d1'].size
    for n,ph,at in (('d1',0.0,0.18),('d2',1.9,0.52),('d3',3.7,0.83)):
        place(f,sp,n,o,angle=1.6*math.sin(TAU*p*4+ph),pivot=({'d1':0.2,'d2':0.5,'d3':0.8}[n]*w,h*0.95),dy=ease_hop(p,at,1.1,16))
    # balloon dad: balloons drift on their strings, dad shifts his weight
    sp,o=BALLOON; w,h=sp['dad'].size
    place(f,sp,'dad',o,angle=0.8*math.sin(TAU*p*2),pivot=(w*0.5,h*0.98))
    place(f,sp,'balloons',o,angle=5*math.sin(TAU*p*3),pivot=(w*0.45,h*0.32),dy=3*math.sin(TAU*p*5))
    if not still:
        for d in PETALS:
            yy=(d["y0"]+(GY+80)*d["fall"]*p)%(GY+80)-40
            xx=(d["x0"]+d["sway"]*math.sin(TAU*p*d["sw"]+d["ph"]))%W
            r=d["rots"][int((p*24*d["spin"]+d["ph"]*4))%24]
            f.alpha_composite(r,(int(xx-r.width/2),int(yy-r.height/2)))
    # garland: soft, slow twinkle (no flares)
    f.alpha_composite(wire,(0,0))
    dr=ImageDraw.Draw(f)
    for i,(bx,by) in enumerate(BULBS):
        k=0.5+0.5*math.sin(TAU*p*2-i*0.9)*0.6+0.5*0.4*math.sin(TAU*p*5+i*2.3)
        k=max(0.0,min(1.0,k))
        g=GLOWS[int(k*9)]; f.alpha_composite(g,(int(bx-g.width/2),int(by-g.height/2)))
        c=tuple(int(v) for v in DIM+(BRIGHT-DIM)*k)
        dr.ellipse([bx-7,by-7,bx+7,by+7],fill=c+(255,),outline=(90,70,50,255),width=1)
        dr.ellipse([bx-3.5,by-4.5,bx-0.5,by-1.5],fill=(255,255,255,int(120+120*k)))
    f.alpha_composite(rot(pl,2.5*math.sin(TAU*p*2),(0,0)),(0,-24))
    f.alpha_composite(rot(pr,-2.5*math.sin(TAU*p*2+1.0),(pr.width,0)),(W-pr.width,-36))
    lk=lock
    for st in (0.08,0.58):
        sp_=(p-st)/0.22
        if 0<sp_<1:
            xs=np.arange(tw)[None,:]; ys=np.arange(th)[:,None]
            cx=-300+(tw+600)*sp_
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
