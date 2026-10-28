import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__)); from data import S
W,H=3072,1728
F='/mnt/project-files/keyvisual/daejeon_haedan/AE/fonts/'
def font(w,s): return ImageFont.truetype(F+f'GmarketSans{w}.otf', s)
bg=Image.open(os.path.join(os.path.dirname(__file__),'bg0.png')).convert('RGB')
# header: original gold title lettering + 대회명, small at the top
g=Image.open('/root/hd/out/text_gold@2x.png').convert('RGBA'); g=g.crop(g.getbbox())
top=Image.open('/root/hd/out/text_top@2x.png').convert('RGBA'); top=top.crop(top.getbbox())
A=np.array(top); A[...,:3]=255; top=Image.fromarray(A)
def gold_fill(mask, x0, x1):
    # same ramp as the AE gold: #A98C57 -> #EFE3BF left to right
    w,h=mask.size; t=np.clip((np.arange(w)[None,:]+x0-x0)/(max(x1-x0,1)),0,1)
    c0=np.array([0xA9,0x8C,0x57],np.float32); c1=np.array([0xEF,0xE3,0xBF],np.float32)
    rgb=(c0+(c1-c0)*t[...,None]).repeat(h,0)
    out=np.dstack([rgb,np.array(mask,np.float32)]).astype(np.uint8); return Image.fromarray(out,'RGBA')
def text_mask(s, f, track=0):
    # draw with tracking (em/1000) into an L mask
    em=f.size; adv=[f.getlength(ch)+track*em/1000 for ch in s]
    w=int(sum(adv)-track*em/1000)+40; asc,desc=f.getmetrics(); h=asc+desc+40
    m=Image.new('L',(w,h),0); d=ImageDraw.Draw(m); x=20
    for ch,a in zip(s,adv): d.text((x,20),ch,font=f,fill=255); x+=a
    return m.crop(m.getbbox())
def segs_mask(segs, size, track=-20):
    parts=[text_mask(t.strip() if t.strip() else t, font('Bold' if b else 'Medium', size), track) if t.strip() else None for t,b in segs]
    # recompose with spaces
    fM=font('Medium',size); sp=fM.getlength(' ')
    asc=fM.getmetrics()[0]
    tot=0; items=[]
    for (t,b) in segs:
        f=font('Bold' if b else 'Medium', size)
        lead=sp if t.startswith(' ') else 0; trail=sp if t.endswith(' ') else 0
        m=Image.new('L',(int(f.getlength(t.strip())*1.2)+60, int(size*1.6)),0)
        ImageDraw.Draw(m).text((10,10),t.strip(),font=f,fill=255)
        bb=m.getbbox(); items.append((m,bb,lead,trail)); tot+=lead+(bb[2]-bb[0])+trail
    out=Image.new('L',(int(tot)+4,int(size*1.6)),0); x=0
    for m,bb,lead,trail in items:
        x+=lead; out.paste(m.crop((bb[0],0,bb[2],m.height)),(int(x),0)); x+=bb[2]-bb[0]+trail
    return out.crop(out.getbbox()) if out.getbbox() else out
def shadow(canvas, mask, xy, blur=14, op=110):
    sh=Image.new('RGBA',canvas.size,(0,0,0,0)); a=Image.new('L',canvas.size,0); a.paste(mask,(xy[0]+6,xy[1]+8))
    a=a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v:v*op//255); sh.putalpha(a); canvas.alpha_composite(sh)
def place(canvas, mask, cy, color=None, goldfill=False, maxw=2700, sh=True):
    if mask.width>maxw: mask=mask.resize((maxw,int(mask.height*maxw/mask.width)),Image.LANCZOS)
    x=(W-mask.width)//2; y=int(cy-mask.height/2)
    if sh: shadow(canvas,mask,(x,y))
    if goldfill: lay=gold_fill(mask,0,mask.width)
    else: lay=Image.new('RGBA',mask.size,color+(255,)); lay.putalpha(mask)
    canvas.alpha_composite(lay,(x,y)); return y, y+mask.height
LA='/mnt/project-files/keyvisual/daejeon_haedan/AE/assets/'
L1=Image.open(LA+'logo_daejeon@2x.png').convert('RGBA'); L1=L1.crop(L1.getbbox())
L2=Image.open(LA+'logo_worldskills_committee@2x.png').convert('RGBA'); L2=L2.crop(L2.getbbox())
LS=0.55
L1=L1.resize((int(L1.width*LS),int(L1.height*LS)),Image.LANCZOS); L2=L2.resize((int(L2.width*LS),int(L2.height*LS)),Image.LANCZOS)
def logos(c, cy=1600, gap=130):
    tw=L1.width+gap+L2.width; x=(W-tw)//2
    c.alpha_composite(L1,(x,int(cy-L1.height/2))); c.alpha_composite(L2,(x+L1.width+gap,int(cy-L2.height/2)))
def slide(e):
    c=bg.convert('RGBA')
    # header
    th=top.resize((int(top.width*0.30),int(top.height*0.30)),Image.LANCZOS)
    gh=g.resize((int(g.width*0.30),int(g.height*0.30)),Image.LANCZOS)
    HY=70
    c.alpha_composite(th,((W-th.width)//2,HY)); c.alpha_composite(gh,((W-gh.width)//2,HY+th.height+26))
    # thin gold rule under header
    ry=HY+th.height+26+gh.height+50
    rule=Image.new('RGBA',(900,4),(0xD8,0xC6,0x96,170)); c.alpha_composite(rule,((W-900)//2,ry))
    lines=e['title'].split('\n'); fs=270  # one size for every slide
    ms=[text_mask(l, font('Bold',fs), -35) for l in lines]
    if len(ms)==1: TM=ms[0]
    else:
        gap=int(fs*0.28); TM=Image.new('L',(max(m.width for m in ms), sum(m.height for m in ms)+gap*(len(ms)-1)),0); yy=0
        for m in ms: TM.paste(m,((TM.width-m.width)//2,yy)); yy+=m.height+gap
    logos(c)
    has_body=e['sub'] or e['plain'] or e['org']
    if not has_body:
        place(c,TM,790,goldfill=True); return c.convert('RGB')
    y0,y1=place(c,TM,700,goldfill=True)
    if e['plain']:
        place(c,segs_mask(e['plain'],130),y1+200,(255,255,255)); return c.convert('RGB')
    cy=y1+140
    if e['sub']:
        sm=text_mask(e['sub'],font('Medium',112),-10); a,b=place(c,sm,cy,(0xF0,0xE2,0xBC)); cy=b+140
    nm=segs_mask([(e['org']+' ',0),(e['name'],1)],128) if e['org']!='개인' else segs_mask([('개인 ',0),(e['name'],1)],128)
    place(c,nm,cy,(255,255,255))
    return c.convert('RGB')
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
names=[]
for i,e in enumerate(S,1):
    lab=e['title'].replace(' ','').replace('\n','')+('_'+e['sub'].replace('/','·').replace(' ','') if e['sub'] else '')+('_'+e['name'].split()[0] if e['name'] else '')
    fn=f"{i:02d}_{lab}.png"; slide(e).save(os.path.join(out,fn)); names.append(fn)
open(os.path.join(out,'list.txt'),'w').write('\n'.join(names))
print(len(names))
