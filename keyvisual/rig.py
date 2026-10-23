import pymupdf
from PIL import Image
from objs import D, draw
def rig(bbox, bodies, limbs, scale):
    """Layered puppet of one illustration group, keeping the artwork's own stacking order.
    bodies: [(name, rect)] - items whose centre falls in rect move with that body.
    limbs:  {name: (item indices, pivot pt, parent body or None)} - rotate about pivot, then follow the parent.
    Consecutive items with the same owner become one layer. Returns layers [(owner, image)], origin pt, pivots px."""
    R=pymupdf.Rect(bbox)
    its=[(i,x) for i,x in enumerate(D) if i>=23 and x.get('rect') is not None and x['rect'] in R and x['type']!='clip']
    own={i:n for n,(ids,_,_) in limbs.items() for i in ids}
    def owner(i,x):
        if i in own: return own[i]
        if x['rect'].width>60: return 'rest'
        c=(x['rect'].tl+x['rect'].br)/2
        for n,r in bodies:
            if pymupdf.Rect(r).contains(c): return n
        return 'rest'
    runs=[]
    for i,x in its:
        o=owner(i,x)
        if runs and runs[-1][0]==o: runs[-1][1].append(x)
        else: runs.append((o,[x]))
    clip=R+(-2,-2,2,2)
    layers=[(o,draw(v,clip,scale)) for o,v in runs]
    px=lambda pt:((pt[0]-clip.x0)*scale,(pt[1]-clip.y0)*scale)
    return layers,(clip.x0,clip.y0),{n:(px(pv),par) for n,(_,pv,par) in limbs.items()}
