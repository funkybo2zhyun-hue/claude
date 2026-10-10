import pymupdf, numpy as np
from PIL import Image
P=pymupdf.open("src/2026_goalbingrock_sejong_logo.ai")[0]
D=P.get_drawings()
def draw(items, clip, scale, sx=1.0):
    """Redraw drawing items onto a transparent layer; clip in pt; scale px/pt; sx extra horizontal stretch."""
    nd=pymupdf.open(); pg=nd.new_page(width=P.rect.width+600,height=P.rect.height)
    for x in items:
        sh=pg.new_shape()
        for it in x['items']:
            k=it[0]
            if k=='l': sh.draw_line(it[1],it[2])
            elif k=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
            elif k=='re': sh.draw_rect(it[1])
            elif k=='qu': sh.draw_quad(it[1])
        lc=x.get('lineCap'); lc=max(lc) if isinstance(lc,(list,tuple)) else (lc or 0)
        sh.finish(fill=x.get('fill'), color=x.get('color') if x['type']!='f' else None,
                  width=x.get('width') or 0, even_odd=x.get('even_odd',False),
                  closePath=x.get('closePath',False), lineCap=lc, lineJoin=x.get('lineJoin') or 0,
                  fill_opacity=x.get('fill_opacity') or 1)
        sh.commit()
    z=scale*2
    pix=pg.get_pixmap(matrix=pymupdf.Matrix(z,z), clip=pymupdf.Rect(clip), alpha=True)
    im=Image.frombytes("RGBA",(pix.width,pix.height),pix.samples)
    return im.resize((round(im.width/2*sx), round(im.height/2)), Image.LANCZOS)
def obj(bbox, scale=1.0, imin=23, imax=10**9, excl=()):
    R=pymupdf.Rect(bbox)
    its=[x for i,x in enumerate(D) if imin<=i<=imax and i not in excl and x.get('rect') is not None and x['rect'] in R and x['type']!='clip']
    im=draw(its, R+(-2,-2,2,2), scale)
    bb=im.getchannel('A').getbbox(); return im.crop(bb), (R.x0-2+bb[0]/scale, R.y0-2+bb[1]/scale)
