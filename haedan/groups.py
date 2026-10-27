import pikepdf,sys,collections,pickle
pdf=pikepdf.open(sys.argv[1]); pgi=int(sys.argv[2])
pg=pdf.pages[pgi]
ops=pikepdf.parse_content_stream(pg)
groups=[];cur=[];depth=0
for o in ops:
    op=str(o.operator)
    cur.append(o)
    if op=='q': depth+=1
    elif op=='Q': depth-=1
    if depth==0 and op in ('Q','f','f*','S','s','B','B*','n','EMC','BDC','sh','Do','ET','EX'):
        groups.append(cur);cur=[]
if cur: groups.append(cur)
print(len(groups))
for i,g in enumerate(groups):
    c=collections.Counter(str(o.operator) for o in g)
    dos=[str(o.operands[0]) for o in g if str(o.operator)=='Do']
    cols=[ [float(x) for x in o.operands] for o in g if str(o.operator) in ('scn','sc','g','rg','k','SCN','RG','K','G')][:2]
    print(i,len(g),dict(c.most_common(6)),dos[:4],cols)
