"""v4 key visual (smaller partner band, title lowered) and its seamless looping video.
usage: python3 v4.py still.png [loop.mp4]"""
import sys, math, subprocess; sys.path.insert(0,'.')
from compose import vec, W, H, SKY, RED, WHITE
from objs import D, draw, obj
from logos import logos
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
S=1.1; Y0=880
BAND=96; GY=H-BAND
cy=lambda pt: round((pt-Y0)*S)
T=10.0; FPS=30                     # loop length (s) and frame rate
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

# festoon geometry (drawn per frame so bulbs can twinkle)
def festoon_pts(x0,x1,y0,y1,sag,n):
    line=[(x0+(x1-x0)*t, y0+(y1-y0)*t+sag*4*t*(1-t)) for t in np.linspace(0,1,120)]
    bulbs=[(x0+(x1-x0)*t, y0+(y1-y0)*t+sag*4*t*(1-t)+8) for t in np.linspace(0.03,0.97,n)]
    return line,bulbs
F=[festoon_pts(250,1300,505,488,62,20), festoon_pts(1300,2330,488,505,62,20)]
wire=Image.new("RGBA",(W*2,H*2),(0,0,0,0)); wd=ImageDraw.Draw(wire)
for line,_ in F: wd.line([(x*2,y*2) for x,y in line],fill=(43,42,42,255),width=5)
base.alpha_composite(wire.resize((W,H),Image.LANCZOS))
BULBS=[b for _,bs in F for b in bs]

pr=vec([1120,170,1700,760],300); pl=vec([-300,680,280,1120],230)

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

def frame(t):
    p=t/T                                    # 0..1 loop phase
    f=base.copy()
    for c,x,y,amp,ph in clouds:              # clouds drift back and forth
        f.alpha_composite(c,(round(x+amp*math.sin(TAU*p+ph)),y))
    # balloon dad bobs, dancers bounce to a beat (6 beats per loop)
    im,x,y=balloon; f.alpha_composite(im,(x,round(y+5*math.sin(TAU*p*2))))
    im,x,y=dancers; f.alpha_composite(im,(x,round(y-9*abs(math.sin(TAU*p*6)))))
    # twinkling festoon bulbs
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    for i,(bx,by) in enumerate(BULBS):
        k=0.5+0.5*math.sin(TAU*(p*3)+i*1.3)
        r=7+3*k
        ld.ellipse([bx-r-6,by-r-6,bx+r+6,by+r+6],fill=(255,236,150,int(70*k)))
        ld.ellipse([bx-7,by-7,bx+7,by+7],fill=(255,int(232+20*k),int(170+60*k),255))
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.6)))
    # peach branches sway from the corners
    f.alpha_composite(rot(pl,2.2*math.sin(TAU*p),(0,0)),(0,-24))
    f.alpha_composite(rot(pr,-2.2*math.sin(TAU*p+1.0),(pr.width,0)),(W-pr.width,-36))
    # title floats, with a light sweep across it once per loop
    lk=lock
    sp=(p-0.15)/0.35
    if 0<sp<1:
        xs=np.arange(tw)[None,:]; ys=np.arange(th)[:,None]
        cx=-300+(tw+600)*sp
        band_=np.clip(1-np.abs((xs+0.35*ys)-cx)/90,0,1)**2
        gl=(band_*INK_A*170).astype(np.uint8)
        sh=Image.new("RGBA",(tw,th),(255,255,255,0)); sh.putalpha(Image.fromarray(gl))
        lk=lock.copy(); lk.alpha_composite(sh)
    f.alpha_composite(lk,(LX,round(LY+7*math.sin(TAU*p))))
    f.alpha_composite(band,(0,GY))
    return f.convert("RGB")

frame(0).save(sys.argv[1]); print("still saved")
if len(sys.argv)>2:
    n=int(T*FPS)
    ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-preset","slow","-crf","16","-pix_fmt","yuv420p","-movflags","+faststart",sys.argv[2]],stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i/FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("video", n, "frames")
