import pymupdf
from objs import D, draw
def split(bbox, parts, scale, excl=()):
    """Render each person/part of a group as its own sprite on the group's shared origin.
    parts: list of (name, rect) - an item goes to the first part whose rect contains its center;
    leftovers and very wide shapes (shadows, benches, mats) go to 'rest'."""
    R=pymupdf.Rect(bbox)
    its=[(i,x) for i,x in enumerate(D) if i>=23 and i not in excl and x.get('rect') is not None and x['rect'] in R and x['type']!='clip']
    groups={n:[] for n,_ in parts}; groups['rest']=[]
    for i,x in its:
        c=(x['rect'].tl+x['rect'].br)/2
        if x['rect'].width>60: groups['rest'].append(x); continue
        for n,pr in parts:
            if pymupdf.Rect(pr).contains(c): groups[n].append(x); break
        else: groups['rest'].append(x)
    clip=R+(-2,-2,2,2)
    return {n:draw(v,clip,scale) for n,v in groups.items()}, (clip.x0,clip.y0)
