# Find every person in the clean plate (YOLO11x-seg), keep masks for the per-person warp motion.
import numpy as np, pickle
from PIL import Image, ImageDraw
from ultralytics import YOLO
m=YOLO('/root/mk/models/yolo11x-seg.pt')
im=Image.open('/root/mk/anim/plate_clean.png').convert('RGB'); W,H=im.size
dets=[]
def run(img,ox,oy,sc,imgsz):
    r=m.predict(np.asarray(img)[...,::-1],imgsz=imgsz,conf=0.12,classes=[0],retina_masks=True,verbose=False)[0]
    if r.masks is None: return
    for b,c,mk in zip(r.boxes.xyxy.cpu().numpy(),r.boxes.conf.cpu().numpy(),r.masks.data.cpu().numpy()):
        mm=Image.fromarray((mk*255).astype('uint8')).resize((round(img.width/sc),round(img.height/sc)),Image.BILINEAR)
        full=np.zeros((H,W),np.uint8); full[oy:oy+mm.height,ox:ox+mm.width]=np.asarray(mm)[:H-oy,:W-ox]
        dets.append(dict(box=b/sc+[ox,oy,ox,oy],conf=float(c),mask=full))
run(im,0,0,1,2560)
# 2x tiles for the small people at the stalls
for x0 in range(0,W,640):
    x1=min(W,x0+960); tile=im.crop((x0,0,x1,H)).resize(((x1-x0)*2,H*2),Image.LANCZOS)
    run(tile,x0,0,2,1920)
print(len(dets),'raw')
# merge duplicates by mask IoU
dets.sort(key=lambda d:-d['conf']); keep=[]
for d in dets:
    a=d['mask']>127
    if a.sum()<60: continue
    dup=False
    for k in keep:
        b=k['mask']>127; inter=(a&b).sum(); 
        if inter/min(a.sum(),b.sum())>0.5: dup=True; break
    if not dup: keep.append(d)
print(len(keep),'people')
pickle.dump(keep,open('/root/mk/anim/people.pkl','wb'))
v=im.copy().convert('RGBA'); ov=Image.new('RGBA',v.size,(0,0,0,0)); rng=np.random.default_rng(1)
for i,d in enumerate(keep):
    col=tuple(int(c) for c in rng.integers(60,255,3))
    a=Image.fromarray(((d['mask']>127)*120).astype('uint8')); lay=Image.new('RGBA',v.size,col+(0,)); lay.putalpha(a); ov.alpha_composite(lay)
v.alpha_composite(ov); dr=ImageDraw.Draw(v)
for i,d in enumerate(keep):
    x0,y0,x1,y1=d['box']; dr.rectangle((x0,y0,x1,y1),outline=(255,255,255,255),width=1); dr.text((x0+2,y0+1),str(i),fill=(255,255,255,255))
v.convert('RGB').save('/root/mk/out/people_det.png')
