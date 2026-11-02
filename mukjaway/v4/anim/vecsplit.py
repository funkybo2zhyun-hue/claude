import pymupdf as fitz
from PIL import Image
_d=None
def drawings():
    global _d
    if _d is None:
        doc=fitz.open('/root/mk/src/poster.ai'); _d=doc[0].get_drawings()
    return _d
def render(sel, clip, zoom):
    """Redraw the selected vector drawings (list of dicts) on a blank page, return RGBA crop of clip (pt rect)."""
    doc=fitz.open(); pg=doc.new_page(width=1190.55,height=1683.78)
    for x in sel:
        sh=pg.new_shape()
        for it in x['items']:
            k=it[0]
            if k=='l': sh.draw_line(it[1],it[2])
            elif k=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
            elif k=='re': sh.draw_rect(it[1])
            elif k=='qu': sh.draw_quad(it[1])
        sh.finish(fill=x.get('fill'),color=None,even_odd=x.get('even_odd',False),closePath=x.get('closePath',True),fill_opacity=x.get('fill_opacity',1) or 1)
        sh.commit()
    pm=pg.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=fitz.Rect(clip),alpha=True)
    return Image.frombytes('RGBA',(pm.width,pm.height),pm.samples)
