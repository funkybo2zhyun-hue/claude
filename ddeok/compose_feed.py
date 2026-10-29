exec(open('_feedhead.py').read())
E=lambda k,d:float(os.environ.get(k,d))
LS=E('LS',0.5); RS_=E('RS',0.5)
stage(['L1'],150*4,343*4,E('LCX',300),775,LS,0.62,0.46,dx={'L1':int(E('LDX',-110))})
stage(['R1','R2'],292*4,346*4,E('RCX',2020),775,RS_,0.62,0.46,dy={'R1':int(100*RS_/0.68)},dx={'R1':int(215*RS_/0.68),'R2':int(-110*RS_/0.68)})
# ---------- feed frame
def feed_frame(hole):
    global im
    r=22
    Sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(Sh).rounded_rectangle((FX0-6,FY0+6,FX1+6,FY1+18),radius=r+8,fill=(20,4,30,170))
    im.alpha_composite(Sh.filter(ImageFilter.GaussianBlur(22)))
    Gw=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(Gw).rounded_rectangle((FX0-14,FY0-14,FX1+14,FY1+14),radius=r+14,outline=(255,180,110,120),width=14)
    im.alpha_composite(Gw.filter(ImageFilter.GaussianBlur(14)))
    Fr=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(Fr)
    d.rounded_rectangle((FX0-12,FY0-12,FX1+12,FY1+12),radius=r+12,fill=PLUM+(255,))
    d.rounded_rectangle((FX0-9,FY0-9,FX1+9,FY1+9),radius=r+9,outline=GOLD+(255,),width=4)
    d.rounded_rectangle((FX0-3,FY0-3,FX1+3,FY1+3),radius=r+3,outline=(120,60,90,255),width=3)
    im.alpha_composite(Fr)
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).rounded_rectangle((FX0,FY0,FX1-1,FY1-1),radius=r,fill=255)
    if hole:
        a=np.asarray(im.split()[3]).astype(float)*(1-np.asarray(m)/255.); im.putalpha(Image.fromarray(a.astype('uint8')))
    else:
        P=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(P).rectangle((FX0,FY0,FX1,FY1),fill=(28,22,34,255))
        f2=font('BlackHanSans-Regular.ttf',64); t='LIVE  16:9'; tw_=f2.getlength(t)
        ImageDraw.Draw(P).text((FX0+FW/2-tw_/2,FY0+FH/2-60),t,font=f2,fill=(120,110,130,255))
        f3=font('BlackHanSans-Regular.ttf',34); t3=f'{FW} x {FH}'; ImageDraw.Draw(P).text((FX0+FW/2-f3.getlength(t3)/2,FY0+FH/2+20),t3,font=f3,fill=(100,92,110,255))
        P.putalpha(Image.fromarray(np.minimum(np.asarray(P.split()[3]),np.asarray(m))))
        im.alpha_composite(P)
# ---------- logo block (left column)
import title3d
CXT=E('CXT',272); TW=int(E('TW',470))
T=Image.open('title_hi.png'); th=round(T.height*TW/T.width); T=T.resize((TW,th),Image.LANCZOS); T=T.crop(T.getbbox()); tw,th=T.size
T3,pad=title3d.make(T,depth=9,outline=0)
f=font('BlackHanSans-Regular.ttf',int(E('HS',38)))
Lh,w,h,p=tlayer('2026 문창 떡 축제',f,(255,255,255,255),spacing=3)
Hd=Lh.crop(Lh.getbbox()); arr=np.asarray(Hd).copy()
x0=int(f.getlength('2026 문창 ')+3*8)-3; x1=int(f.getlength('2026 문창 떡')+3*9)+3
pk=arr[:,x0:x1]; pk[...,0]=250; pk[...,1]=120; pk[...,2]=155; Hd=Image.fromarray(arr)
H3,hpad=title3d.make(Hd,depth=5,outline=0)
hw,hh=Hd.size; by0=int(E('BY0',58)); gap=20
LOGO=Image.new('RGBA',(W,H),(0,0,0,0))
LOGO.alpha_composite(H3,(int(CXT-hw//2-hpad),by0-hpad)); LOGO.alpha_composite(T3,(int(CXT-tw//2-pad),by0+hh+gap-pad))
base=im.copy()
im.alpha_composite(LOGO); feed_frame(True); im.save(OUT.replace('.png','_alpha.png'))
im=base; im.alpha_composite(LOGO); feed_frame(False); im.convert('RGB').save(OUT)
print('logo bottom',by0+hh+gap+th, 'hdr',hw,'title',tw,th)
