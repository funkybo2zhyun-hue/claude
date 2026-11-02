# Per-person soft masks + calm motion recipes for the warp pass (every person moves on their own).
import numpy as np, pickle, math
from PIL import Image, ImageFilter
P=pickle.load(open('/root/mk/anim/people.pkl','rb'))
H,W=768,2560
LOGO=(965,1594)
rng=np.random.default_rng(11)
FG={0,1,2,7,29}; COOK={5,25,6,4}
out=[]
for i,d in enumerate(P):
    x0,y0,x1,y1=[float(v) for v in d['box']]
    if x0>=LOGO[0] and x1<=LOGO[1]: continue          # fully behind the logo
    if i in (35,39): continue                          # smudges at the logo edge, not people
    m=Image.fromarray(d['mask'])
    m=m.point(lambda v:255 if v>110 else 0).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(4))
    pad=24
    bx0,by0=max(0,int(x0)-pad),max(0,int(y0)-pad); bx1,by1=min(W,int(x1)+pad),min(H,int(y1)+pad)
    w=np.asarray(m.crop((bx0,by0,bx1,by1))).astype(np.float32)/255
    ph=y1-y0
    if i in FG: yb=y1+0.35*ph; kind='fg'
    elif i in COOK: yb=y0+0.80*ph; kind='cook'
    else: yb=y0+0.72*ph; kind='sit'
    yy=np.arange(by0,by1,dtype=np.float32)[:,None]
    hf=np.clip((yb-yy)/(yb-y0),0,1)**1.3*np.ones((1,bx1-bx0),np.float32)
    cx=(x0+x1)/2
    # calm recipe: two components, periods that divide 20 s, own phase each
    per=lambda:float(rng.choice([2.5,4.0,5.0]))
    if kind=='cook':
        rec=[('rock',1.1,2.0,rng.uniform(0,6.3)),('bob',0.010*ph,1.0,rng.uniform(0,6.3))]
    elif kind=='fg':
        rec={0:[('rock',0.7,5.0,0.4),('nod',0.010*ph,2.5,1.3)],
             1:[('lean',0.012*ph,5.0,2.0),('nod',0.007*ph,4.0,0.2)],
             2:[('laugh',0.008*ph,5.0,0.0),('rock',0.5,4.0,3.1)],
             7:[('nod',0.011*ph,2.5,4.4),('lean',0.008*ph,5.0,1.0)],
             29:[('rock',0.6,4.0,5.0),('breath',0.006,4.0,0.0)]}[i]
    else:
        kinds=['rock','nod','lean','laugh','breath']
        a,b=rng.choice(kinds,2,replace=False)
        amp=lambda k:{'rock':rng.uniform(0.7,1.4),'nod':rng.uniform(0.012,0.02)*ph,'lean':rng.uniform(0.012,0.02)*ph,
                      'laugh':rng.uniform(0.012,0.018)*ph,'breath':rng.uniform(0.006,0.01)}[k]
        rec=[(a,amp(a),per(),rng.uniform(0,6.3)),(b,amp(b),per(),rng.uniform(0,6.3))]
    out.append(dict(i=i,kind=kind,box=(bx0,by0,bx1,by1),w=w,h=hf,cx=cx,yb=yb,rec=[(k,float(a),float(p),float(f)) for k,a,p,f in rec]))
    print(i,kind,[(k,round(a,2),p) for k,a,p,f in out[-1]['rec']])
pickle.dump(out,open('/root/mk/anim/people_motion.pkl','wb'))
print(len(out),'people move')
