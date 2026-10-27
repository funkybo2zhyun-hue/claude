import pymupdf as fitz, re
fitz.TOOLS.set_icc(True)
d=fitz.open('src/poster.ai'); p=d[0]
s=d.xref_stream(8)
s=s.replace(b'/Im0 Do',b'',1)
s=s.replace(b'0 0 1190.552 1683.779 re\nf\n',b'',1)
d.update_stream(8,s)
pm=p.get_pixmap(dpi=400,alpha=True); pm.save('src/vec_400.png'); print(pm.width,pm.height)
