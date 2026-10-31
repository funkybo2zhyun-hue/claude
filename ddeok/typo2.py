import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD='fonts/'
def font(n,sz):
    if n.startswith('NotoSansKR-'):
        f=ImageFont.truetype(FD+'NotoSansKR.ttf',sz); f.set_variation_by_axes([{'Bold':700,'Medium':500,'Black':900,'ExtraBold':800}[n[11:-4]]]); return f
    return ImageFont.truetype(FD+n,sz)
def tlayer(txt,fnt,fill,spacing=0,pad=40):
    bb=fnt.getbbox(txt); w=int(sum(fnt.getlength(c) for c in txt)+spacing*(len(txt)-1)) if spacing else bb[2]-bb[0]; h=bb[3]-bb[1]
    L=Image.new('RGBA',(w+2*pad,h+2*pad),(0,0,0,0)); d=ImageDraw.Draw(L)
    if spacing:
        x=pad-bb[0]
        for c in txt: d.text((x,pad-bb[1]),c,font=fnt,fill=fill); x+=fnt.getlength(c)+spacing
    else: d.text((pad-bb[0],pad-bb[1]),txt,font=fnt,fill=fill)
    return L,w,h,pad
def outlined(L,ow,ocol,glow=None,gblur=18,shadow=(20,5,30,170),sdy=8,sblur=14):
    a=L.split()[3]
    out=Image.new('RGBA',L.size,(0,0,0,0))
    if shadow:
        S=Image.new('RGBA',L.size,shadow[:3]+(0,)); S.putalpha(a.filter(ImageFilter.MaxFilter(ow*2+1)).point(lambda v:v*shadow[3]//255) if ow else a.point(lambda v:v*shadow[3]//255))
        S=S.filter(ImageFilter.GaussianBlur(sblur)); out.alpha_composite(S,(0,sdy))
    if glow:
        G=Image.new('RGBA',L.size,glow[:3]+(0,)); G.putalpha(a.filter(ImageFilter.MaxFilter(ow*2+1 if ow else 3)).point(lambda v:v*glow[3]//255)); out.alpha_composite(G.filter(ImageFilter.GaussianBlur(gblur)))
    if ow:
        # round outline via repeated max filter + slight blur for AA
        m=a
        for _ in range(ow//3): m=m.filter(ImageFilter.MaxFilter(7))
        m=m.filter(ImageFilter.GaussianBlur(1.2))
        O=Image.new('RGBA',L.size,ocol[:3]+(0,)); O.putalpha(m.point(lambda v:v*ocol[3]//255)); out.alpha_composite(O)
    out.alpha_composite(L); return out
def pad_img(L,p):
    N=Image.new('RGBA',(L.width+2*p,L.height+2*p),(0,0,0,0)); N.alpha_composite(L,(p,p)); return N
GOLD=(255,214,140); CREAM=(255,244,226); PLUM=(58,24,66)
def draw(im, ML=120, RX=2440, title_w=900, ty=196):
    d=ImageDraw.Draw(im)
    # header ribbon
    f=font('NanumMyeongjo-ExtraBold.ttf',52)
    L,w,h,p=tlayer('2026 문창 떡 축제',f,CREAM+(255,),spacing=3)
    bx0,by0=ML,92; bx1,by1=bx0+w+64,by0+h+34
    R=Image.new('RGBA',im.size,(0,0,0,0)); rd=ImageDraw.Draw(R)
    rd.rounded_rectangle((bx0,by0,bx1,by1),radius=(by1-by0)//2,fill=PLUM+(205,),outline=GOLD+(255,),width=3)
    im.alpha_composite(R.filter(ImageFilter.GaussianBlur(0.6)))
    im.alpha_composite(L,(bx0+32-p,by0+17-p))
    # title lettering, outlined
    T=Image.open('title_hi.png'); th=round(T.height*title_w/T.width); T=T.resize((title_w,th),Image.LANCZOS)
    T=pad_img(T,60)
    T=outlined(T,12,PLUM+(255,),glow=(255,190,150,150),gblur=26,shadow=(15,0,25,200),sdy=12,sblur=16)
    im.alpha_composite(T,(ML-20-60,ty-60))
    # tagline
    f=font('NotoSansKR-Bold.ttf',44)
    L,w,h,p=tlayer('고소한 떡 냄새, 우리 동네 시장 나들이',f,(255,255,255,255))
    L=outlined(L,0,None,shadow=(15,0,25,220),sdy=4,sblur=8)
    im.alpha_composite(L,(ML+10-p,ty+th+34-p))
    # right info panel
    PW=560; PX0=RX-PW; PY0=150; PY1=620
    P=Image.new('RGBA',im.size,(0,0,0,0)); pd=ImageDraw.Draw(P)
    pd.rounded_rectangle((PX0,PY0,RX,PY1),radius=36,fill=(40,18,50,150),outline=GOLD+(230,),width=3)
    pd.rounded_rectangle((PX0+12,PY0+12,RX-12,PY1-12),radius=28,outline=GOLD+(90,),width=1)
    sh=P.split()[3].point(lambda v:min(255,v)); 
    im.alpha_composite(P)
    cx=(PX0+RX)//2
    def ctext(txt,fn,col,y,spacing=0,sh=True):
        L,w,h,p=tlayer(txt,fn,col,spacing=spacing)
        if sh: L=outlined(L,0,None,shadow=(10,0,20,200),sdy=4,sblur=8)
        im.alpha_composite(L,(cx-w//2-p,y-p)); return h
    # label chips
    def chip(txt,y):
        fn=font('NotoSansKR-Bold.ttf',28); L,w,h,p=tlayer(txt,fn,PLUM+(255,))
        C=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(C).rounded_rectangle((cx-w//2-22,y,cx+w//2+22,y+h+18),radius=(h+18)//2,fill=GOLD+(255,))
        im.alpha_composite(C); im.alpha_composite(L,(cx-w//2-p,y+9-p))
    chip('일 시',PY0+40)
    ctext('10.30 – 10.31',font('NanumMyeongjo-ExtraBold.ttf',96),(255,255,255,255),PY0+104)
    ctext('금요일 · 토요일',font('NotoSansKR-Bold.ttf',38),GOLD+(255,),PY0+222)
    chip('장 소',PY0+292)
    ctext('대전 문창전통시장 일대',font('NotoSansKR-Bold.ttf',46),(255,255,255,255),PY0+356)
    ctext('11월 금·토 주말에도 야시장 진행',font('NotoSansKR-Medium.ttf',28),CREAM+(225,),PY1+28)
    return im
if __name__=='__main__':
    import sys
    im=Image.open(sys.argv[1]).convert('RGBA'); draw(im).convert('RGB').save(sys.argv[2])
