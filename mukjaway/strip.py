import pymupdf as fitz, re, sys
fitz.TOOLS.set_icc(True)
d=fitz.open('src/poster.ai'); p=d[0]
pix=fitz.Pixmap(d,36); pix=fitz.Pixmap(fitz.csRGB,pix); pix.save('src/bg_rgb.png')
for x in p.get_contents():
    s=d.xref_stream(x)
    n=len(re.findall(rb'/Im0 Do',s)); print(x,len(s),n)
    s=re.sub(rb'/Im0 Do',b'',s); d.update_stream(x,s)
pm=p.get_pixmap(dpi=300,alpha=True); pm.save('src/vec_300.png'); print(pm.width,pm.height)
