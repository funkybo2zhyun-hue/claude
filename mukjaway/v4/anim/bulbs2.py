import numpy as np
from PIL import Image
from scipy import ndimage as ndi
im=np.asarray(Image.open('anim/plate_clean.png').convert('RGB')).astype(np.float32)
L=im.mean(2); B=im[...,2]
old=np.load('anim/bulbs.npy')
# keep old ones in the upper part only (lower ones were shirts / dishes)
keep=[b for b in old if b[1]<=415]
# relaxed pass in the sky band: bright blobs surrounded by dark
m=(L>195)&(B>120)
lab,n=ndi.label(m)
objs=ndi.find_objects(lab)
add=[]
for i,sl in enumerate(objs,1):
    ys,xs=sl
    comp=(lab[sl]==i); a=comp.sum()
    if a<6 or a>1200: continue
    cy,cx=ndi.center_of_mass(comp); cy+=ys.start; cx+=xs.start
    if cy>415: continue
    h=ys.stop-ys.start; w=xs.stop-xs.start
    if not (0.45<w/h<2.2): continue
    r=np.sqrt(a/np.pi)
    if comp.sum()/(h*w)<0.4: continue
    # ring darker than core
    yy,xx=np.ogrid[:L.shape[0],:L.shape[1]]
    y0,y1=int(max(0,cy-3*r-6)),int(min(L.shape[0],cy+3*r+7)); x0,x1=int(max(0,cx-3*r-6)),int(min(L.shape[1],cx+3*r+7))
    sub=L[y0:y1,x0:x1]; d=np.hypot(yy[y0:y1]-cy,xx[:,x0:x1]-cx)
    ring=sub[(d>1.7*r+2)&(d<2.8*r+5)]
    core=sub[d<max(1,0.7*r)]
    if ring.size==0 or core.size==0: continue
    if ring.mean()>core.mean()-45: continue
    if min(np.hypot(*(np.array(keep)[:,:2]-[cx,cy]).T))<max(6,r): continue
    add.append([cx,cy,r])
print(len(keep),'kept',len(add),'added')
allb=np.array(keep+add)
np.save('anim/bulbs2.npy',allb)
from PIL import ImageDraw
v=Image.open('anim/plate_clean.png').convert('RGB'); d=ImageDraw.Draw(v)
for cx,cy,r in keep: d.ellipse((cx-r-3,cy-r-3,cx+r+3,cy+r+3),outline=(0,255,255),width=2)
for cx,cy,r in add: d.ellipse((cx-r-3,cy-r-3,cx+r+3,cy+r+3),outline=(255,0,255),width=2)
v.crop((0,0,1280,500)).save('out/b2_L.png'); v.crop((1280,0,2560,500)).save('out/b2_R.png')
