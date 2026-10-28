# Title motion option previews (1536x864, 30fps, 8 s) over BG v2 + original text layers
import sys, subprocess, numpy as np
from PIL import Image
from scipy import ndimage as nd
W,H,FPS,DUR=3072,1728,60,20.0
K=2.0  # scale factor vs preview
O='/root/hd/out/'
def load(f, two=False):
    im=Image.open(O+f).convert('RGBA')
    c=6 if two else 3
    im=im.crop((c,0,im.width-c,im.height)).resize((W,H),Image.LANCZOS)
    a=np.asarray(im).astype(np.float32)/255
    return a[...,:3]*a[...,3:], a[...,3:]          # premultiplied rgb, alpha
top=load('text_top@2x.png',True); top=(np.repeat(top[1],3,2),top[1]); info=load('text_info@2x.png',True)
gold_full=Image.open(O+'text_gold@2x.png').convert('RGBA')
grgb,ga=load('text_gold@2x.png',True)
# glyph groups from artboard x-ranges (3078 px space) -> preview x
R=[(477,646),(660,827),(846,1031),(1043,1202),(1214,1378),(1444,1612),(1628,1799),(1818,1995),(2057,2230),(2253,2430),(2435,2599)]
sx=W/3072.0
gl=[]
for (a,b) in R:
    m=np.zeros((H,W),np.float32); x0=int((a-3)*sx)-2; x1=int((b-3)*sx)+3
    m[:,x0:x1]=1; gl.append((m, (x0+x1)/2))
ys,xs=np.where(ga[...,0]>0.3); Y0,Y1=ys.min(),ys.max(); X0,X1=xs.min(),xs.max()
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
def over(dst,rgb,a): return rgb+dst*(1-a)
def smooth(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def bump(t,w): return np.where(np.abs(t)<w, 0.5+0.5*np.cos(np.pi*t/w),0.0)
WARM=np.array([1.0,0.95,0.82],np.float32)

def title_static(t): return grgb, ga

def optA(t):
    # soft diagonal sheen + star glints at glyph corners
    rgb,a=grgb.copy(),ga
    ang=np.deg2rad(20); u=xx*np.cos(ang)+yy*np.sin(ang)
    for t0 in (0.8,10.8):
        p=(t-t0)/1.8
        if 0<=p<=1:
            c=(X0-150*K)+(X1-X0+300*K)*smooth(p)
            band=np.exp(-((u-c-np.sin(ang)*(Y0+Y1)/2)/(75.0*K))**2)*0.55
            rgb=rgb+ (band[...,None]*WARM)*a
    add=np.zeros((H,W,3),np.float32)
    stars=[(ts+r,x,y) for r in (0,10) for (ts,x,y) in [(2.4,gl[2][1]+30*K,Y0+8*K),(3.3,gl[6][1]+28*K,Y0+10*K),(6.6,gl[9][1]-25*K,Y0+12*K),(7.4,gl[0][1]-20*K,Y1-10*K)]]
    for (ts,sx_,sy) in stars:
        e=bump(t-ts,0.45)
        if e<=0: continue
        L=150*K*e; dx=xx-sx_; dy=yy-sy
        rot=0.6*(t-ts)
        cx=dx*np.cos(rot)+dy*np.sin(rot); cy=-dx*np.sin(rot)+dy*np.cos(rot)
        ray=np.exp(-(cy/(2.2*K))**2)*np.exp(-np.abs(cx)/max(L*0.45,1))+np.exp(-(cx/(2.2*K))**2)*np.exp(-np.abs(cy)/max(L*0.45,1))
        core=np.exp(-(dx*dx+dy*dy)/(2*(9*K*e+0.5)**2))+0.35*np.exp(-(dx*dx+dy*dy)/(2*(30*K*e+0.5)**2))
        add+=((ray*0.9+core)*e)[...,None]*WARM
    return rgb, a, add

def optB(t):
    # slow left->right wave: each glyph lifts and brightens in turn (every 4 s)
    rgb=np.zeros((H,W,3),np.float32); a=np.zeros((H,W,1),np.float32)
    ph=t%4.0
    for i,(m,cx) in enumerate(gl):
        e=float(bump(ph-0.8-i*0.13,0.55))
        dy=-12*K*e
        gm=m[...,None]
        rs=nd.shift(grgb*gm,(dy,0,0),order=1,prefilter=False) if e>0 else grgb*gm; as_=nd.shift(ga*gm,(dy,0,0),order=1,prefilter=False) if e>0 else ga*gm
        rs=rs*(1+0.35*e)
        rgb+=rs; a+=as_
    return np.clip(rgb,0,None), np.clip(a,0,1), None

edge=None
def optC(t):
    # light running along the letter outlines + inner lift where it passes
    global edge
    if edge is None:
        al=ga[...,0]; er=nd.grey_erosion(al,size=(3,3)); edge=np.clip(al-er,0,1)
        edge=nd.gaussian_filter(edge,0.6)
    rgb,a=grgb.copy(),ga
    ph=(t%4.0)/4.0
    c=X0-200+(X1-X0+400)*ph
    g=np.exp(-((xx-c)/110.0)**2)
    line=edge*g*1.6
    glow=nd.gaussian_filter(line,6)*2.2
    rgb=rgb+(g*0.18)[...,None]*WARM*a
    add=(line+glow)[...,None]*WARM
    return rgb,a,add

