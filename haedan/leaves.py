# walk artboard 1 and collect every drawable leaf (bokeh circle / glitter image) with its blend chain
import pikepdf, sys, json
src,out=sys.argv[1],sys.argv[2]
pdf=pikepdf.open(src); pg=pdf.pages[0]
M=300  # render margin so circles can move in from off-frame
def mul(a,b):  # a then b (PDF row-vector convention): a*b
    return [a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3], a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3],
            a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5]]
leaves=[]
def walk(ops,res,ctm,chain,tag):
    st=[];cur=list(ctm);gs=[]
    for o in ops:
        op=str(o.operator)
        if op=='q': st.append((cur,gs))
        elif op=='Q': cur,gs=st.pop()
        elif op=='cm': cur=mul([float(x) for x in o.operands],cur)
        elif op=='gs':
            g=res.ExtGState[o.operands[0]]
            gs=[(str(g.get('/BM','/Normal')),float(g.get('/ca',1)))]
        elif op=='Do':
            x=res.XObject[o.operands[0]]
            ch=chain+gs
            if x.Subtype=='/Image':
                leaves.append(dict(kind='img',obj=x,ctm=cur,chain=ch,tag=tag))
            else:
                sub=pikepdf.parse_content_stream(x)
                m=[float(v) for v in x.get('/Matrix',[1,0,0,1,0,0])]
                if any(str(s.operator)=='Do' for s in sub):
                    walk(sub,x.Resources,mul(m,cur),ch,tag)
                else:
                    leaves.append(dict(kind='form',obj=x,ctm=mul(m,cur),chain=ch,tag=tag))
ops=pikepdf.parse_content_stream(pg)
groups=[];c=[];depth=0
for o in ops:
    op=str(o.operator); c.append(o)
    if op=='q': depth+=1
    elif op=='Q': depth-=1
    if depth==0 and op in ('Q','f','f*','S','s','B','B*','n','EMC','BDC','sh','Do','ET','EX'): groups.append(c);c=[]
I=[1,0,0,1,0,0]
for i in range(4,144): walk(groups[i],pg.Resources,I,[],'glitter')
walk(groups[145],pg.Resources,I,[],'fx')
print(len(leaves))
# one page per leaf, on an enlarged canvas
W,H=3078,1728
for L in leaves:
    pdf.pages.append(pdf.pages[0]); p=pdf.pages[-1]
    p.obj.MediaBox=[-M,-M,W+M,H+M]
    for k in ('/CropBox','/TrimBox','/ArtBox','/BleedBox'):
        if k in p.obj: del p.obj[k]
    p.obj.Resources=pikepdf.Dictionary(XObject=pikepdf.Dictionary(L0=L['obj']))
    a=L['ctm']
    s='q %f %f %f %f %f %f cm /L0 Do Q'%tuple(a)
    p.obj.Contents=pdf.make_stream(s.encode())
del pdf.pages[0:2]
pdf.save(out+'/leaves.pdf')
json.dump([dict(kind=L['kind'],chain=L['chain'],tag=L['tag']) for L in leaves],open(out+'/leaves.json','w'))
