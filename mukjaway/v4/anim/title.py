# Split the centred title stack into animatable pieces straight from the .ai vectors:
# Daejeon no.1 letters + its two stars, 관/저/동 + dashes, 먹/자/웨/이 (cream outline and red fill as
# separate layers), the brush band and its 7 live-text characters. Pieces keep the v4 placement.
import sys, pickle; sys.path.insert(0,'/root/mk/lib')
import numpy as np, pymupdf as fitz
from PIL import Image, ImageFilter
from common import *
from vecsplit import drawings, render
CL=(250,80,950,680)
crop=V().crop((int(CL[0]*K),int(CL[1]*K),int(CL[2]*K),int(CL[3]*K)))
bx0,by0,bx1,by1=crop.getbbox(); stack=crop.crop((bx0,by0,bx1,by1))
LH=600; f=LH/stack.height; OX=(W-round(stack.width*f))//2; OY=(H-LH)//2
SS=2  # sprites kept at 2x canvas scale
arr=np.asarray(crop).astype(np.float32)
def vmask(sel):
    m=render(sel,CL,K); a=np.asarray(m.getchannel('A')).astype(np.float32)/255
    h,w=arr.shape[:2]; a=a[:h,:w]
    if a.shape!=(h,w): a=np.pad(a,((0,h-a.shape[0]),(0,w-a.shape[1])))
    return a
def mkpiece(rgb,alpha,name,depth=5):
    """rgb HxWx3 float, alpha HxW 0-1 at vec res -> sprite at SS*canvas scale with baked shallow depth"""
    ys,xs=np.where(alpha>0.01)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    rgba=np.dstack([rgb[y0:y1,x0:x1],alpha[y0:y1,x0:x1,None]*255]).clip(0,255).astype('uint8')
    im=Image.fromarray(rgba,'RGBA')
    im=im.resize((max(1,round(im.width*f*SS)),max(1,round(im.height*f*SS))),Image.LANCZOS)
    # baked extrusion (same look as v4 stage2: D=5 px at canvas scale)
    D=depth*SS; a=np.asarray(im).astype(np.float32)
    out=Image.new('RGBA',(im.width+D,im.height+D),(0,0,0,0))
    for i in range(D,0,-1):
        k=0.30+0.22*(1-i/D); lay=a.copy(); lay[...,:3]=np.minimum(lay[...,:3]*k+np.array([8,4,2])*(1-i/D),255)
        out.alpha_composite(Image.fromarray(lay.astype('uint8')),(round(i*0.3),i))
    out.alpha_composite(im,(0,0))
    cx=OX+(x0-bx0)*f; cy=OY+(y0-by0)*f
    return dict(name=name,img=out,x=cx,y=cy,w=im.width/SS,h=im.height/SS)
dr=drawings()
def sel(rect,pred=lambda x:True):
    r=fitz.Rect(rect)
    return [x for x in dr if fitz.Rect(x['rect']).intersects(r) and fitz.Rect(x['rect']).width<760
            and x.get('fill') and max(x['fill'])>0.05 and pred(x)]
def cxr(x): r=x['rect']; return (r[0]+r[2])/2
P=[]
A0=arr[...,3]/255; RGB=arr[...,:3]
# Daejeon no.1 — one piece per glyph (stars separate)
djs=sel((300,88,900,181))
seen=set()
for x in sorted(djs,key=cxr):
    key=tuple(round(v) for v in x['rect'])
    if key in seen: continue
    seen.add(key)
    m=np.minimum(A0,np.asarray(Image.fromarray((vmask([x])*255).astype('uint8')).filter(ImageFilter.MaxFilter(5))).astype(np.float32)/255)
    nm='dj_star' if (x['rect'][2]-x['rect'][0])>20 and abs((x['rect'][3]+x['rect'][1])/2-164)<6 else 'dj'
    P.append(mkpiece(RGB,m,nm))
# 관/저/동 and the two dashes
gws=sel((250,182,950,330),lambda x:x['rect'][1]>180 and x['rect'][3]<330)
groups={'gw_dashL':lambda c:c<380,'gw_1':lambda c:380<=c<537,'gw_2':lambda c:537<=c<667,'gw_3':lambda c:667<=c<800,'gw_dashR':lambda c:c>=800}
for nm,fn in groups.items():
    g=[x for x in gws if fn(cxr(x))]
    m=np.minimum(A0,np.asarray(Image.fromarray((vmask(g)*255).astype('uint8')).filter(ImageFilter.MaxFilter(5))).astype(np.float32)/255)
    P.append(mkpiece(RGB,m,nm))
# 먹/자/웨/이: cream outline layer + red fill layer per syllable
mks=sel((250,322,950,523),lambda x:x['rect'][1]>320)
cream=lambda x:x['fill'][0]>0.9 and x['fill'][1]>0.9
red=lambda x:x['fill'][0]<0.8
syl={'mk_1':lambda c:c<445,'mk_2':lambda c:445<=c<600,'mk_3':lambda c:600<=c<752,'mk_4':lambda c:c>=752}
redall=vmask([x for x in mks if red(x)])
CREAM=np.array([250,237,212],np.float32)
outl,fill=[],[]
for nm,fn in syl.items():
    mo=vmask([x for x in mks if cream(x) and fn(cxr(x))]); mr=vmask([x for x in mks if red(x) and fn(cxr(x))])
    # outline: original where it's not someone else's red, flat cream there
    others=np.clip(redall-mr,0,1)
    rgb_o=RGB*(1-others[...,None])+CREAM*others[...,None]
    outl.append(mkpiece(rgb_o,np.minimum(mo,np.maximum(A0,others)),nm+'_o'))
    fill.append(mkpiece(RGB,np.minimum(mr,A0),nm+'_f',depth=0))
P+=outl+fill
# band + 7 characters (live text, keyed off the cream band)
d=fitz.open('/root/mk/src/poster.ai'); pg=d[0]
chars=[]
for b in pg.get_text('rawdict',clip=fitz.Rect(250,540,950,690))['blocks']:
    for l in b.get('lines',[]):
        for sp in l['spans']:
            for c in sp['chars']: chars.append(c['bbox'])
chars.sort(key=lambda b:b[0])
BC=np.array([247,219,184],np.float32)
dist=np.sqrt(((RGB-BC)**2).sum(2))
band_rect=(int((305-CL[0])*K),int((553-CL[1])*K),int((881-CL[0])*K),int((674-CL[1])*K))
inband=np.zeros_like(A0); inband[band_rect[1]:band_rect[3],band_rect[0]:band_rect[2]]=1
txt=np.clip((dist-30)/90,0,1)*inband*(A0>0.9)
# band without text: text pixels replaced by band cream
tm=np.asarray(Image.fromarray((txt*255).astype('uint8')).filter(ImageFilter.MaxFilter(5))).astype(np.float32)/255
rgb_b=RGB*(1-tm[...,None])+BC*tm[...,None]
bm=np.zeros_like(A0); bm[band_rect[1]-40:band_rect[3]+40,band_rect[0]-60:band_rect[2]+60]=1
P.append(mkpiece(rgb_b,A0*bm,'bd_band'))
xs=[(c[0]+c[2])/2 for c in chars]
cuts=[CL[0]-1]+[(chars[i][2]+chars[i+1][0])/2 for i in range(len(chars)-1)]+[CL[2]+1]
for i in range(len(chars)):
    cm=np.zeros_like(A0); c0=int((cuts[i]-CL[0])*K); c1=int((cuts[i+1]-CL[0])*K)
    cm[:,max(c0,0):max(c1,0)]=1
    a=txt*cm
    if a.max()<0.5: continue
    P.append(mkpiece(RGB,a,f'bd_c{i}',depth=0))
for p in P: print(p['name'],round(p['x']),round(p['y']),round(p['w']),round(p['h']))
# static stack shadow (as in v4)
st=rs(stack,f); A=st.getchannel('A')
pickle.dump(dict(pieces=[dict(p,img=None) for p in P],OX=OX,OY=OY,f=f,W=st.width,H=st.height),open('/root/mk/anim/title_meta.pkl','wb'))
for i,p in enumerate(P): p['img'].save(f'/root/mk/anim/t_{i:02d}_{p["name"]}.png')
