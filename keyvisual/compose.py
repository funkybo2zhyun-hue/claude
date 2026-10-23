import pymupdf, numpy as np, sys
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
SRC="src/2026_goalbingrock_sejong_logo.ai"
doc=pymupdf.open(SRC); P=doc[0]; D=P.get_drawings()
W,H=2560,768
SKY=(51,198,244); GRASS=(113,188,112); RED=(239,70,66); WHITE=(255,255,255)

def vec(region, height, keep=lambda x:True, rects=None, pad=6):
    """Redraw the vector paths inside region onto a transparent layer, scaled to the given height."""
    R=pymupdf.Rect(region)
    nd=pymupdf.open(); pg=nd.new_page(width=P.rect.width,height=P.rect.height)
    for x in D:
        r=x['rect']
        if rects is not None:
            if not any(abs(r.x0-a)<1 and abs(r.y0-b)<1 and abs(r.x1-c)<1 and abs(r.y1-d)<1 for a,b,c,d in rects): continue
        elif not (r in R) or not keep(x): continue
        sh=pg.new_shape()
        for it in x['items']:
            k=it[0]
            if k=='l': sh.draw_line(it[1],it[2])
            elif k=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
            elif k=='re':
                # keep the rectangle's winding: same-direction rects are holes (e.g. the camper windows on 고)
                r=it[1]; o=it[2] if len(it)>2 else 1
                pts=[r.tl,r.tr,r.br,r.bl] if o==1 else [r.tl,r.bl,r.br,r.tr]; sh.draw_polyline(pts+[pts[0]])
            elif k=='qu': sh.draw_quad(it[1])
        lc=x.get('lineCap'); lc=max(lc) if isinstance(lc,(list,tuple)) else (lc or 0)
        sh.finish(fill=x.get('fill'), color=x.get('color') if x['type']!='f' else None,
                  width=x.get('width') or 0, even_odd=x.get('even_odd',False),
                  closePath=x.get('closePath',False), lineCap=lc, lineJoin=x.get('lineJoin') or 0)
        sh.commit()
    clip=R+(-pad,-pad,pad,pad)
    z=height*2/clip.height
    pix=pg.get_pixmap(matrix=pymupdf.Matrix(z,z), clip=clip, alpha=True)
    im=Image.frombytes("RGBa",(pix.width,pix.height),pix.samples).convert("RGBA")  # MuPDF pixmaps are premultiplied
    bb=im.getchannel('A').getbbox(); im=im.crop(bb)
    s=height/im.height
    return im.resize((round(im.width*s),height),Image.LANCZOS)

def is_redwhite(x):
    f=x.get('fill'); c=x.get('color')
    ok=lambda v: v and (min(v)>0.97 or (v[0]>0.9 and v[1]<0.3))
    return (x['type']=='s' and ok(c)) or (x['type']!='s' and ok(f))

def scene(box2x, height):
    """Raster crop of the illustration (2x render coords); pale sky connected to the top edge becomes transparent."""
    z=4
    x0,y0,x1,y1=[v/2 for v in box2x]
    pix=P.get_pixmap(matrix=pymupdf.Matrix(z,z), clip=pymupdf.Rect(x0,y0,x1,y1))
    im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
    a=np.asarray(im).astype(int)
    pale=(np.abs(a-np.array([238,248,252])).sum(-1)<18)|(a.min(-1)>250)
    lab,_=ndimage.label(pale)
    top=set(np.unique(lab[0]))-{0}
    sky=np.isin(lab,list(top))
    alpha=np.where(sky,0,255).astype(np.uint8)
    out=im.convert("RGBA"); out.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2)))
    s=height/out.height
    return out.resize((round(out.width*s),height),Image.LANCZOS)

if __name__=="__main__":
    import json; cfg=json.load(open(sys.argv[1])); out=sys.argv[2]
    exec(open(cfg["layout"]).read())
