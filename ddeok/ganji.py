import os,sys,json,shutil,numpy as np
from PIL import Image,ImageDraw
from typo2 import font,tlayer
import title3d
W,H=2304,768; CX=1152
ITEMS=[('01','국민의례',None),('02','내빈 소개',None),('03','개회사',None),('04','축사',None),
       ('05','개막 세레모니','시루떡 커팅식'),('06','기념 촬영',None),('07','축하 공연',None)]
E=lambda k,d:float(os.environ.get(k,d))
m=json.load(open('L9/manifest.json'))
base=[n for n in m['order'] if not n.startswith(('60_','70_'))]
# shared small main logo
LTW=int(E('LTW',470))
T=Image.open('title_hi.png'); T=T.resize((LTW,round(T.height*LTW/T.width)),Image.LANCZOS); T=T.crop(T.getbbox()); ltw,lth=T.size
L3,lp=title3d.make(T,depth=10,outline=0)
LY=int(E('LY',96))
def chars_layers(txt,size,y,color,depth,sp):
    f=font('BlackHanSans-Regular.ttf',size)
    full,w,h,p=tlayer(txt,f,(255,255,255,255),spacing=sp); bb=full.getbbox()
    x0=CX-(bb[2]-bb[0])//2; out=[]
    x=p-f.getbbox(txt)[0]
    for i,c in enumerate(txt):
        if c!=' ':
            L=Image.new('RGBA',full.size,(0,0,0,0)); ImageDraw.Draw(L).text((x,p-f.getbbox(txt)[1]),c,font=f,fill=color+(255,))
            L=L.crop(bb); cb=L.getbbox()
            G3,pd=title3d.make(L,depth=depth,outline=0)
            Lc=Image.new('RGBA',(W,H),(0,0,0,0)); Lc.alpha_composite(G3,(x0-pd,y-pd))
            out.append((Lc,[x0+(cb[0]+cb[2])/2,y+cb[3]]))
        x+=f.getlength(c)+sp
    return out,bb[3]-bb[1]
for code,title,sub in ITEMS:
    D=f'LG/{code}'; shutil.rmtree(D,ignore_errors=True); os.makedirs(D)
    for n in ['00_background']+base: os.symlink(os.path.abspath(f'L9/{n}.png'),f'{D}/{n}.png')
    order=list(base); meta={n:m['meta'][n] for n in base}
    Lg=Image.new('RGBA',(W,H),(0,0,0,0)); Lg.alpha_composite(L3,(CX-ltw//2-lp,LY-lp)); Lg.save(f'{D}/60_title_header_logo.png')
    order.append('60_title_header_logo'); meta['60_title_header_logo']={'anchor':[CX,LY+lth/2]}
    ty=LY+lth+int(E('GAP',48))
    size=int(E('TS',150)) if len(title)<=5 else int(E('TS2',132))
    cl,th=chars_layers(title,size,ty,(255,255,255),14,int(size*0.06))
    for k,(Lc,anc) in enumerate(cl):
        nm=f'70_title_{k+1:02d}_c'; Lc.save(f'{D}/{nm}.png'); order.append(nm); meta[nm]={'anchor':anc}
    if sub:
        sl,_=chars_layers(sub,int(E('SS',58)),ty+th+int(E('SG',34)),(250,120,155),6,4)
        S=Image.new('RGBA',(W,H),(0,0,0,0))
        for Lc,_a in sl: S.alpha_composite(Lc)
        S.save(f'{D}/60_title_header_sub.png'); order.append('60_title_header_sub'); bb=S.getbbox(); meta['60_title_header_sub']={'anchor':[CX,(bb[1]+bb[3])/2]}
    json.dump({'order':order,'meta':meta,'size':[W,H]},open(f'{D}/manifest.json','w'),indent=1)
    full=Image.open(f'{D}/00_background.png').convert('RGBA')
    for n in order: full.alpha_composite(Image.open(f'{D}/{n}.png'))
    full.convert('RGB').save(f'ganji_{code}.png'); print(code,title,'title y',ty,ty+th)
