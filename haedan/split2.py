# cumulative split: base + ordered elements, each element stored as a signed delta crop
import pikepdf, sys, json
src, out = sys.argv[1], sys.argv[2]
pdf = pikepdf.open(src)
pg = pdf.pages[0]
ops = pikepdf.parse_content_stream(pg)
groups=[];cur=[];depth=0
for o in ops:
    op=str(o.operator); cur.append(o)
    if op=='q': depth+=1
    elif op=='Q': depth-=1
    if depth==0 and op in ('Q','f','f*','S','s','B','B*','n','EMC','BDC','sh','Do','ET','EX'):
        groups.append(cur);cur=[]
if cur: groups.append(cur)
Q=pikepdf.ContentStreamInstruction([],pikepdf.Operator('Q'))
q=pikepdf.ContentStreamInstruction([],pikepdf.Operator('q'))
EMC=pikepdf.ContentStreamInstruction([],pikepdf.Operator('EMC'))
g144=groups[144]; k=[i for i,o in enumerate(g144) if str(o.operator)=='CS'][0]
elems=[]
for i in range(4,144): elems.append(('glitter',groups[i]))
elems.append(('mult',g144[:k]+[Q]))
elems.append(('lines',[q]+g144[k:]))
g=groups[145]; head=g[:4]; body=g[4:-1]
assert str(g[-1].operator)=='Q' and len(body)%5==0, (len(body))
for j in range(0,len(body),5): elems.append(('fx',head+body[j:j+5]+[Q]))
pre=[groups[2][0]]
pages=[pre+groups[3]+[EMC]]
acc=[]
for t,e in elems:
    acc=acc+e; pages.append(pre+groups[3]+acc+[EMC])
for c in pages:
    pdf.pages.append(pdf.pages[0]); pdf.pages[-1].obj.Contents=pdf.make_stream(pikepdf.unparse_content_stream(c))
del pdf.pages[0:2]
pdf.save(out+'/cum.pdf')
json.dump([t for t,e in elems],open(out+'/elems.json','w'))
print(len(elems))
