# isolated fx deltas: render(prefix + one fx form) - render(prefix)
import pikepdf, sys, json
src,out=sys.argv[1],sys.argv[2]
exec(open(sys.argv[3]).read().split("pre=[groups[2][0]]")[0])  # reuse element building from split2.py
pre=[groups[2][0]]
prefix=pre+groups[3]+[o for t,e in elems if t!='fx' for o in e]
pages=[prefix+[EMC]]+[prefix+e+[EMC] for t,e in elems if t=='fx']
for c in pages:
    pdf.pages.append(pdf.pages[0]); pdf.pages[-1].obj.Contents=pdf.make_stream(pikepdf.unparse_content_stream(c))
del pdf.pages[0:2]
pdf.save(out+'/iso.pdf'); print(len(pages))
