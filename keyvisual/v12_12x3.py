"""v12 at 12:3 (3072x768): v11_12x3 re-staging with every element grown 1.2x to match the wider panel
(drawn from the vectors at the larger size, nothing stretched), anchored on the ground so nobody floats.
v12: v11 with clean vector edges (MuPDF premultiplied alpha fixed in compose/objs), clouds and petals
moving on sub-pixel positions, and a much higher bitrate encode.
v11: v10 with the title lock-up held still (no float).
v10 = v9 with livelier but calm surroundings: brighter garland twinkle that travels along the wire,
six clouds drifting on their own, and people rigged per limb (waving arms, nodding heads, a rocking kid).
v9 = v8 with the wheels slowed to one turn per 5 s. v8 was v6.1 plus a living title logo: the two wheels in 고알빙락 spin, the five stars over
the 알 wheel twinkle in a chase, and crisp four-point glints pop along the lettering.
20 s @ 60 fps seamless loop.
usage: [LOGO_FLOAT=1] python3 v12_12x3.py still.png [loop.mp4]"""
import sys, math, subprocess; sys.path.insert(0,'.')
from compose import vec, W, H, SKY, RED, WHITE
W=3072; XS=W/2560; K=1.2           # 12:3 panel at the same 768 px height; elements drawn 1.2x
from objs import D, draw, obj
from logos import logos
from split import split
from rig import rig
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
S=1.1; Y0=880
BAND=58; GY=H-BAND
OFFY=36                            # push the whole scene down a little to balance the slimmer strip
cy=lambda pt: round((pt-Y0)*S)+OFFY
T=20.0; FPS=60                     # loop length (s) and frame rate
TAU=2*math.pi

# ---------- static landscape ----------
# items that belong to a sprite or rigged group are drawn there only (v10 also left a copy in the landscape,
# which showed as a ghost under moving heads and hands and floated free once groups were re-staged)
import pymupdf
_own=set(i for b in ([700,1195,890,1350],[480,1060,720,1290],[490,1310,770,1500],[860,1080,985,1320],[0,1040,460,1420],[980,1075,1460,1420],[405,1250,545,1320])
         for i,x in enumerate(D) if i>=23 and x.get('rect') is not None and x['rect'] in pymupdf.Rect(b) and x['type']!='clip')
bg_items=[x for i,x in enumerate(D) if i not in _own and ((3<=i<=117 and x.get('rect') is not None and x['type']!='clip' and (x['rect'].y1<1232 or x['rect'].width>250)) or i==22 or (117<i<300 and x.get('rect') is not None and x['rect'].width<12 and x['rect'].y1<1232 and x['type']=='f'))]
CL=(62,Y0,1356,1545)
base=Image.new("RGBA",(W,H),SKY+(255,))
land=draw(bg_items, CL, S, sx=W/((CL[2]-CL[0])*S))
base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,OFFY))

# ---------- sprites ----------
cl=[(992,31,1355,168),(129,93,492,230)]
clouds=[]
for rect,h,x,y,flip,amp,ph,op in [(cl[1],95,330,24,False,140,0.0,1),(cl[0],110,1980,8,True,120,1.7,1),(cl[0],70,720,120,False,150,3.1,1),
                                 (cl[1],62,1700,150,True,130,4.4,1),(cl[0],44,1180,150,False,110,5.2,0.85),(cl[1],40,2120,175,True,90,2.4,0.85)]:
    c=vec([0,0,1417,400],round(h*K),rects=[rect])
    if flip: c=c.transpose(Image.FLIP_LEFT_RIGHT)
    if op<1: c.putalpha(c.getchannel('A').point(lambda v,op=op:int(v*op)))
    clouds.append((c,round(x*XS),y,amp*XS,ph))

def sprite(bbox,x,y=None,excl=(),anchor='c'):
    im,(ox,oy)=obj(bbox,S*K,excl=excl); w0,h0=im.width/K,im.height/K
    top0=cy(oy) if y is None else y
    X={'l':x,'c':x-(K-1)*w0/2,'r':x+w0-im.width}[anchor]
    return [im,max(0,round(X)),round(top0+h0-im.height)]
still_objs=[sprite([0,1040,460,1420],0,excl=(491,),anchor='l'), None,
            sprite([980,1075,1460,1420],W-round(480*S)-6,anchor='r'), None,
            sprite([405,1250,545,1320],745,y=478+OFFY)]
still_objs=[o for o in still_objs if o]          # picnic and table couple are rigged below

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
SW=6; anchors=np.linspace(-30,W+30,SW+1)
wire=Image.new("RGBA",(W*2,160*2),(0,0,0,0)); wd=ImageDraw.Draw(wire); BULBS=[]
for a0,a1 in zip(anchors[:-1],anchors[1:]):
    pts=[(a0+(a1-a0)*t, -2+46*4*t*(1-t)) for t in np.linspace(0,1,90)]
    wd.line([(x*2,y*2) for x,y in pts],fill=(60,52,48,255),width=5)
    for t in np.linspace(0.14,0.86,5):
        BULBS.append((a0+(a1-a0)*t, -2+46*4*t*(1-t)+8))
wire=wire.resize((W,160),Image.LANCZOS)
DIM=np.array([170,128,74]); BRIGHT=np.array([255,247,214])
def soft_glow(r):
    g=Image.new("L",(r*6,r*6),0); ImageDraw.Draw(g).ellipse([r*1.6,r*1.6,r*4.4,r*4.4],fill=255)
    return g.filter(ImageFilter.GaussianBlur(r*0.7))
GLOW_A=soft_glow(12)
GLOWS=[]
for l in range(10):
    g=Image.new("RGBA",GLOW_A.size,(255,226,150,0)); g.putalpha(GLOW_A.point(lambda v,l=l:int(v*(0.04+0.56*l/9)))); GLOWS.append(g)
still_objs=[o for o in still_objs if o]          # table couple + picnic are rebuilt below as actors
base=Image.new("RGBA",(W,H),SKY+(255,)); base.alpha_composite(land.resize((W,land.height),Image.LANCZOS),(0,OFFY))
for o in still_objs: base.alpha_composite(o[0],(o[1],o[2]))

def puppet(bbox, bodies, limbs, x):
    layers,(ox,oy),piv=rig(bbox,bodies,limbs,S*K)
    u=None
    for _,im in layers:
        bb=im.getchannel('A').getbbox()
        if bb: u=bb if u is None else (min(u[0],bb[0]),min(u[1],bb[1]),max(u[2],bb[2]),max(u[3],bb[3]))
    # same screen placement as the v6 sprites: union box's top-left lands at (x, cy(...))
    w,h=u[2]-u[0],u[3]-u[1]; top0=cy(oy+u[1]/(S*K))
    # grown about the feet: same ground line as the 1x layout, widened evenly to both sides
    return dict(layers=layers,piv=piv,u=u,X=round(x-(K-1)*w/K/2)-u[0],Y=round(top0+h/K-h)-u[1],w=w,h=h)
def body_pivot(P,fx,fy): return (P['u'][0]+fx*P['w'], P['u'][1]+fy*P['h'])
def show(f,P,bodies={},limbs={}):
    for o,im in P['layers']:
        if o in P['piv']:
            pv,par=P['piv'][o]; a=limbs.get(o,0.0)
            if a: im=im.rotate(a,resample=Image.BICUBIC,center=pv)
            o=par
        a,pv,dx,dy=bodies.get(o,(0.0,None,0.0,0.0))
        if a: im=im.rotate(a,resample=Image.BICUBIC,center=pv)
        f.alpha_composite(im,(round(P['X']+dx),round(P['Y']+dy)))
DANCE=puppet([700,1195,890,1350],[('d1',[700,1195,762,1350]),('d2',[762,1195,822,1340]),('d3',[822,1195,890,1350])],
    {'d2_armL':({57,54},(771,1262),'d2'),'d2_armR':({56,55},(797,1256),'d2'),'d3_arm':({81,89},(845,1251),'d3')},2110)
PICNIC=puppet([480,1060,720,1290],[('umb',[540,1060,700,1150])],
    {'pm_head':({1269,1270,1271,1276,1288},(588,1171),None),'pk_head':({1250,1251,1252,1253},(622,1187),None),
     'pw_head':({1247,1248,1249,1277,1279},(650,1189),None)},640)
TABLE=puppet([490,1310,770,1500],[('man',[490,1310,580,1420]),('woman',[580,1310,660,1420])],
    {'m_head':({420,421,422,426,435},(548,1357),'man'),'w_head':({399,401,402,403,408},(603,1346),'woman')},428)
BALLOON=puppet([860,1080,985,1320],[('balloons',[880,1080,960,1140]),('dad',[880,1140,960,1300])],
    {'kid':({266,271,267,272,273,274,279,281,282,283,287,288},(905,1192),'dad')},2335)

# drifting peach-blossom petals (each falls 1-2 full screen heights per loop, so the loop is seamless)
rng=np.random.default_rng(7)
def petal(h):
    p=Image.new("RGBA",(h*4,h*4),(0,0,0,0)); pd=ImageDraw.Draw(p)
    pd.ellipse([h*0.6,h*1.4,h*3.4,h*2.6],fill=(248,170,160,235)); pd.ellipse([h*1.2,h*1.7,h*2.6,h*2.2],fill=(255,205,196,235))
    return p.resize((h*2,h*2),Image.LANCZOS)
PETALS=[]
for i in range(18):
    h=int(rng.integers(14,24)); sp=petal(h)
    PETALS.append(dict(rots=[sp.rotate(a,resample=Image.BICUBIC,expand=True) for a in range(0,360,15)],
        x0=float(rng.uniform(0,W)), y0=float(rng.uniform(0,GY)), fall=int(rng.integers(1,3)),
        sway=float(rng.uniform(30,90)), sw=int(rng.integers(1,4)), ph=float(rng.uniform(0,TAU)), spin=int(rng.choice([-2,-1,1,2]))))

pr=vec([1120,170,1700,760],round(300*K)); pl=vec([-300,680,280,1120],round(230*K))
base_still=None

# title lock-up as one sprite (title + subtitle + halo + drop shadow)
title=vec([250,140,1140,400],round(330*K)); sub=vec([300,400,1100,530],round(118*K))
TY=66
tw=max(title.width,sub.width)+160; th=round((330+12+118+120)*K)
lock=Image.new("RGBA",(tw,th),(0,0,0,0)); ink=Image.new("RGBA",(tw,th),(0,0,0,0))
ink.alpha_composite(title,((tw-title.width)//2,round(60*K))); ink.alpha_composite(sub,((tw-sub.width)//2,round((60+330+12)*K)))
a=ink.getchannel('A')
halo=Image.new("RGBA",(tw,th),(255,255,255,0)); halo.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(26)).point(lambda v:int(v*0.35)))
drop=Image.new("RGBA",(tw,th),(120,20,20,0)); drop.putalpha(a.filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.45)))
lock.alpha_composite(halo); lock.alpha_composite(drop,(0,8)); lock.alpha_composite(ink)
INK_A=np.asarray(a).astype(np.float32)/255

# ---------- living logo ----------
# wheels: hub/rim centres fitted on the rendered ink; the disc inside the white tyre is rotated
_ia0=np.asarray(ink).astype(np.float32)
def _fit_wheel(cx,cy):
    # centre of the thin red rim ring, refitted on the 1.2x ink so the spinning disc sits exactly
    ys,xs=np.mgrid[0:_ia0.shape[0],0:_ia0.shape[1]]; d=np.hypot(xs-cx,ys-cy)
    m=(_ia0[...,3]>200)&(_ia0[...,0]>200)&(_ia0[...,1]<120)&(d>33*K)&(d<47*K)
    x,y=xs[m].astype(float),ys[m].astype(float)
    c=np.linalg.lstsq(np.c_[2*x,2*y,np.ones(len(x))],x**2+y**2,rcond=None)[0]; return (float(c[0]),float(c[1]))
WHEELS=[_fit_wheel(_c[0]*K-(K-1)*80,_c[1]*K) for _c in [(454.62,187.17),(678.72,316.48)]]
WR=60                                       # tyre band is white from r=42..57, so the cut is invisible
WREV=4                                      # turns per loop (5 spokes -> any whole turn loops cleanly)
def disc_mask(r,pad):
    m=Image.new("L",((r+pad)*16,(r+pad)*16),0); ImageDraw.Draw(m).ellipse([pad*8,pad*8,(2*r+pad)*8,(2*r+pad)*8],fill=255)
    return m.resize(((r+pad)*2,(r+pad)*2),Image.LANCZOS)
WMASK=disc_mask(WR,2)
def spin_wheels(lk,ang):
    for k,(cx,cy) in enumerate(WHEELS):
        x0,y0=math.floor(cx)-WR-2,math.floor(cy)-WR-2
        box=(x0,y0,x0+WMASK.width,y0+WMASK.height)
        d=lock.crop(box).rotate(ang*(1 if k==0 else 1.0),resample=Image.BICUBIC,center=(cx-x0,cy-y0))
        lk.paste(d,box[:2],WMASK)
# stars over the 알 wheel: chase twinkle (each grows, flashes white-hot, settles)
from scipy import ndimage
def _fit_star(sx,sy):
    r=int(16*K); y0,x0=int(sy-r),int(sx-r); w=(_ia0[y0:y0+2*r,x0:x0+2*r,1]>200)&(_ia0[y0:y0+2*r,x0:x0+2*r,3]>200)
    lab,_=ndimage.label(w); l=lab[r,r] if lab[r,r] else np.bincount(lab.ravel())[1:].argmax()+1
    yy,xx=np.nonzero(lab==l); return (x0+xx.mean()+0.5-0.5, y0+yy.mean())
STARS=[_fit_star(x*K-(K-1)*80,y*K) for x,y in [(390,155.5),(416,127.5),(457,115.5),(497.5,127.5),(521,155.5)]]
def star_poly(cx,cy,R,r,rot=-90):
    return [(cx+(R if i%2==0 else r)*math.cos(math.radians(rot+36*i)),cy+(R if i%2==0 else r)*math.sin(math.radians(rot+36*i))) for i in range(10)]
def glint(size):
    # four-point sparkle: thin crossed spikes + a small soft core, drawn 4x and downsampled
    n=size*4; g=Image.new("L",(n,n),0); gd=ImageDraw.Draw(g); c=n/2
    for a in (0,90,45,135):
        L=c*(1.0 if a%90==0 else 0.42); w=n*(0.085 if a%90==0 else 0.05)
        ca,sa=math.cos(math.radians(a)),math.sin(math.radians(a))
        gd.polygon([(c+L*ca,c+L*sa),(c-w*sa,c+w*ca),(c-L*ca,c-L*sa),(c+w*sa,c-w*ca)],fill=255)
    gd.ellipse([c-n*0.09,c-n*0.09,c+n*0.09,c+n*0.09],fill=255)
    g=g.resize((size,size),Image.LANCZOS)
    halo=g.filter(ImageFilter.GaussianBlur(size*0.08)).point(lambda v:int(v*0.55))
    return ImageChops.lighter(g,halo)
GL=[glint(s) for s in range(8,171)]
# glint spots: white outline pixels of the title lettering, spread over the logo, staggered in time
_rng=np.random.default_rng(11)
_ia=np.asarray(ink).astype(np.int16)
_edge=(_ia[...,3]>230)&(_ia[...,1]>235)&(np.asarray(a.filter(ImageFilter.MinFilter(5)))<250)
_ys,_xs=np.nonzero(_edge)
SPOTS=[]
for i in range(26):
    for _ in range(200):
        j=_rng.integers(len(_xs)); x,y=int(_xs[j]),int(_ys[j])
        if all(math.hypot(x-sx,y-sy)>150*K for sx,sy,_,_ in SPOTS[-6:]): break
    SPOTS.append((x,y,i/26+float(_rng.uniform(-0.01,0.01)),int(_rng.integers(108,163))))
# a couple of extra glints that land right on the wheel rims while they turn
SPOTS+=[(round(WHEELS[0][0]+40*K),round(WHEELS[0][1]-36*K),0.30,144),(round(WHEELS[1][0]-42*K),round(WHEELS[1][1]+30*K),0.73,144)]
def pulse(p,at,dur):
    u=((p-at+0.5)%1.0-0.5)*T/dur+0.5
    return math.sin(math.pi*u)**2 if 0<u<1 else 0.0
def live_lock(p):
    lk=lock.copy()
    spin_wheels(lk,-360*WREV*p)             # clockwise
    ld=ImageDraw.Draw(lk)
    for i,(sx,sy) in enumerate(STARS):
        k=max(pulse(p,(q+i*0.15)/5,0.9) for q in range(5))  # chase across the 5 stars, every 4 s
        if k>0.01:
            R=8.5*K*(1+0.55*k); ld.polygon(star_poly(sx,sy,R+3,(R+3)*0.45),fill=RED+(255,))
            ld.polygon(star_poly(sx,sy,R,R*0.45),fill=(255,255,int(255-40*k),255))
        if k>0.35:
            g=GL[min(len(GL)-1,int(36+60*k)-8)]
            gl=Image.new("RGBA",g.size,(255,255,240,0)); gl.putalpha(g.point(lambda v,k=k:int(v*min(1,(k-0.35)/0.4))))
            lk.alpha_composite(gl,(int(sx-g.width/2),int(sy-g.height/2)))
    return lk
def add_glints(f,p,ox,oy):
    for x,y,at,sz in SPOTS:
        k=pulse(p,at,0.7)
        if k<0.02: continue
        g=GL[max(0,min(len(GL)-1,round(sz*(0.35+0.65*k))-8))]
        rot=g.rotate(30*k-15,resample=Image.BICUBIC)
        gl=Image.new("RGBA",g.size,(255,252,235,0)); gl.putalpha(rot.point(lambda v,k=k:int(v*k)))
        f.alpha_composite(gl,(int(ox+x-g.width/2),int(oy+y-g.height/2)))
LX=(W-tw)//2; LY=TY-round(60*K)

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

import os
FLOAT=os.environ.get("LOGO_FLOAT")=="1"; FP=80   # LOGO_FLOAT=1 renders the smooth-float variant
def sub_paste(f, im, x, y):
    # composite at a fractional position (whole-pixel steps make slow drifts judder)
    ix,iy=math.floor(x),math.floor(y); fx,fy=x-ix,y-iy
    if fx>1e-3 or fy>1e-3:
        im=im.transform((im.width+1,im.height+1),Image.AFFINE,(1,0,-fx,0,1,-fy),resample=Image.BICUBIC)
    if ix>=0 and iy>=0: f.alpha_composite(im,(ix,iy))
    else: f.alpha_composite(im,dest=(max(0,ix),max(0,iy)),source=(max(0,-ix),max(0,-iy)))
def frame(t, still=False):
    p=t/T
    f=base.copy()
    for c,x,y,amp,ph in clouds:
        sub_paste(f,c,x+amp*math.sin(TAU*p+ph),y)
    # picnic: only the umbrella canopy rocks in the breeze
    # (picnic: the umbrella rocks; the three of them turn their heads as they chat)
    P=PICNIC
    show(f,P,{'umb':(2.2*math.sin(TAU*p*3),body_pivot(P,0.45,0.75),0,0)},
         {'pm_head':4*math.sin(TAU*p*2),'pk_head':5*math.sin(TAU*p*3+1.0),'pw_head':-4*math.sin(TAU*p*2+2.0)})
    # table couple: he leans in to chat now and then, she laughs back; both nod while talking
    P=TABLE
    show(f,P,{'man':(-2.5*max(0,math.sin(TAU*p*2))**2,body_pivot(P,0.25,0.62),0,0),
              'woman':(1.8*max(0,math.sin(TAU*p*2-1.2))**2,body_pivot(P,0.45,0.62),0,-2*max(0,math.sin(TAU*p*4-0.6)))},
         {'m_head':3*math.sin(TAU*p*4+0.5),'w_head':-3.5*math.sin(TAU*p*3+2.0)})
    # dancers: gentle sway, one slow hop each; the middle one sways his raised arms, the right one waves
    P=DANCE
    show(f,P,{n:(1.6*math.sin(TAU*p*4+ph),body_pivot(P,fx,0.95),0,ease_hop(p,at,1.1,16)) for n,ph,at,fx in
              (('d1',0.0,0.18,0.2),('d2',1.9,0.52,0.5),('d3',3.7,0.83,0.8))},
         {'d2_armL':9*math.sin(TAU*p*6),'d2_armR':9*math.sin(TAU*p*6+0.7),'d3_arm':10*math.sin(TAU*p*8+1.0)})
    # balloon dad: balloons drift on their strings, dad shifts his weight, the kid on his shoulders rocks
    P=BALLOON
    show(f,P,{'dad':(0.8*math.sin(TAU*p*2),body_pivot(P,0.5,0.98),0,0),
              'balloons':(5*math.sin(TAU*p*3),body_pivot(P,0.45,0.32),0,3*math.sin(TAU*p*5))},
         {'kid':4*math.sin(TAU*p*4)})
    if not still:
        for d in PETALS:
            yy=(d["y0"]+(GY+80)*d["fall"]*p)%(GY+80)-40
            xx=(d["x0"]+d["sway"]*math.sin(TAU*p*d["sw"]+d["ph"]))%W
            r=d["rots"][math.floor(p*24*d["spin"]+d["ph"]*4)%24]
            px,py=xx-r.width/2,yy-r.height/2
            for ox in (0,-W,W):                 # draw wrap-around copies so petals never pop at the edges
                if -r.width<px+ox<W and -r.height<py<H: sub_paste(f,r,px+ox,py)
    # garland: soft, slow twinkle (no flares)
    f.alpha_composite(wire,(0,0))
    dr=ImageDraw.Draw(f)
    for i,(bx,by) in enumerate(BULBS):
        # a slow wave of light runs along the wire every 10 s, each bulb also breathes on its own
        wave=0.5+0.5*math.sin(TAU*p*2-i*0.45)
        own=0.5+0.5*math.sin(TAU*p*(3+i%3)+i*2.3)
        k=max(0.0,min(1.0,0.1+0.9*(0.6*wave+0.4*own)**1.4))
        g=GLOWS[int(k*9)]; f.alpha_composite(g,(int(bx-g.width/2),int(by-g.height/2)))
        c=tuple(int(v) for v in DIM+(BRIGHT-DIM)*k)
        dr.ellipse([bx-11,by-11,bx+11,by+11],fill=c+(255,),outline=(90,70,50,255),width=1)
        dr.ellipse([bx-5.5,by-6.5,bx-0.5,by-1.5],fill=(255,255,255,int(110+140*k)))
    f.alpha_composite(rot(pl,2.5*math.sin(TAU*p*2),(0,0)),(0,-24))
    f.alpha_composite(rot(pr,-2.5*math.sin(TAU*p*2+1.0),(pr.width,0)),(W-pr.width,-36))
    lk=live_lock(p)
    for st in (0.08,0.58):
        sp_=(p-st)/0.22
        if 0<sp_<1:
            xs=np.arange(tw)[None,:]; ys=np.arange(th)[:,None]
            cx=-300+(tw+600)*sp_
            band_=np.clip(1-np.abs((xs+0.35*ys)-cx)/90,0,1)**2
            sh=Image.new("RGBA",(tw,th),(255,255,255,0)); sh.putalpha(Image.fromarray((band_*INK_A*170).astype(np.uint8)))
            lk.alpha_composite(sh)
    if FLOAT:
        # smooth float: whole-pixel steps looked choppy, so the logo (and its glints) is shifted by the sub-pixel remainder
        y=LY+7*math.sin(TAU*p*2); iy=math.floor(y); fr=y-iy
        L=Image.new("RGBA",(tw+2*FP,th+2*FP),(0,0,0,0)); L.alpha_composite(lk,(FP,FP)); add_glints(L,p,FP,FP)
        if fr>1e-3: L=L.transform(L.size,Image.AFFINE,(1,0,0,0,1,-fr),resample=Image.BICUBIC)
        f.alpha_composite(L,dest=(LX-FP,max(0,iy-FP)),source=(0,max(0,FP-iy)))
    else:
        f.alpha_composite(lk,(LX,LY))           # logo held still (v11)
        add_glints(f,p,LX,LY)
    f.alpha_composite(band,(0,GY))
    return f.convert("RGB")

frame(0,still=True).save(sys.argv[1]); print("still saved")
if len(sys.argv)>2:
    n=int(T*FPS)
    ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-preset","slow","-crf","4","-x264-params","aq-mode=3:deblock=-1,-1","-g","60","-keyint_min","60","-sc_threshold","0","-pix_fmt","yuv420p","-movflags","+faststart",sys.argv[2]],stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i/FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("video", n, "frames")
