exec(open('_headF.py').read())
BG=Image.fromarray(np.clip(img,0,255).astype('uint8')).convert('RGBA')
import os,json,shutil,cv2; LD=os.environ.get('LD','LF10'); shutil.rmtree(LD,ignore_errors=True); os.makedirs(LD)
BG.convert('RGB').save(f'{LD}/00_background.png')
LAYERS=[]; MAN={}
def new():
    global im; im=Image.new('RGBA',(W,H),(0,0,0,0))
def save(name,**meta):
    im.save(f'{LD}/{name}.png'); LAYERS.append(name); MAN[name]=meta; new()
new()
PU=np.asarray(Image.open('poster_up.png').convert('RGB')).astype(float)
SU=Image.open('scene_up.png').convert('RGB')
def lantern(box,cxp,cyp,size,blur=0,fade_=1.0):
    x0,y0,x1,y1=[v*4 for v in box]
    patch=PU[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1].astype(float)
    r=patch-bg_at(xx/4,yy/4)
    a=np.clip((np.abs(r).max(2)-12)/30,0,1)
    e=np.minimum(np.minimum(xx-x0,x1-1-xx),np.minimum(yy-y0,y1-1-yy))/12; a*=np.clip(e,0,1)
    w=size; h=size*(y1-y0)/(x1-x0)
    L=Image.fromarray(np.dstack([np.clip(patch,0,255),a*255*fade_]).astype('uint8')).resize((max(1,round(w)),max(1,round(h))),Image.LANCZOS)
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G); R=size*0.9
    gd.ellipse((cxp-R,cyp-R*0.6,cxp+R,cyp+R*1.2),fill=(255,150,70,int(70*fade_)))
    im.alpha_composite(G.filter(ImageFilter.GaussianBlur(size*0.45)))
    im.alpha_composite(L,(round(cxp-w/2),round(cyp-h/2)))
YEL=(498,70,552,128); RS=(511,264,537,294); RB=(521,320,558,362); RL=(150,250,206,310)
def moon(cxp,cyp,diam):
    m=SU.crop((330*4,0,434*4,98*4)); arr=np.asarray(m).astype(float)
    yy,xx=np.mgrid[0:arr.shape[0],0:arr.shape[1]].astype(float)
    ccx,ccy,R=382*4-330*4,45*4,40*4
    rr=np.sqrt((xx-ccx)**2+(yy-ccy)**2)
    a=np.clip((R+3-rr)/4,0,1)
    M=Image.fromarray(np.dstack([arr,a*255]).astype('uint8'))
    sc=diam/(2*R); M=M.resize((round(M.width*sc),round(M.height*sc)),Image.LANCZOS)
    G=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(G).ellipse((cxp-diam*0.75,cyp-diam*0.75,cxp+diam*0.75,cyp+diam*0.75),fill=(255,190,110,90))
    im.alpha_composite(G.filter(ImageFilter.GaussianBlur(diam*0.3))); save('10_moon_glow',anchor=[cxp,cyp])
    im.alpha_composite(M,(round(cxp-ccx*sc),round(cyp-ccy*sc))); save('11_moon',anchor=[cxp,cyp])
moon(int(os.environ.get('MX','1152')),int(os.environ.get('MY','70')),int(os.environ.get('MD','90')))
LAN=[(YEL,880,210,34,0.6,0.85),(RB,1420,190,34,0,1),(RS,950,420,22,1,0.75),(RS,1380,440,24,1.5,0.6),(RS,1010,120,20,2,0.5),(RS,1300,110,20,2,0.5),(RL,1060,480,26,1.5,0.6),(RS,1250,500,22,2,0.5),(RS,30,640,20,1.5,0.6),(RS,2270,650,20,2,0.5)]
for k,(b,x,y,sz,bl,fa) in enumerate(LAN):
    lantern(b,x,y,sz,bl,fa); save(f'20_lantern_{k+1:02d}',anchor=[x,y],size=sz)
# sparkles in 3 twinkle groups (same 220 dots as the still)
rng=np.random.default_rng(5)
SG=[Image.new('RGBA',(W,H),(0,0,0,0)) for _ in range(3)]
for i in range(220):
    x=rng.uniform(0,W); y=rng.uniform(0,H*0.75); r=rng.uniform(1,3)
    ImageDraw.Draw(SG[i%3]).ellipse((x-r,y-r,x+r,y+r),fill=(255,230,205,int(rng.uniform(60,180))))
for k in range(3):
    im.alpha_composite(SG[k].filter(ImageFilter.GaussianBlur(1.2))); save(f'30_sparkles_{k+1}')
# skyline: body + windows split into 3 twinkle groups
def skyline(tag,seed,base,hmin,hmax,col,win,wa,alpha,blur,dim_center):
    r=np.random.default_rng(seed)
    B=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(B)
    WG=[Image.new('RGBA',(W,H),(0,0,0,0)) for _ in range(3)]
    x=-40; wi=0
    while x<W+40:
        bw=int(r.uniform(70,170)); cxm=x+bw/2
        k=1-dim_center*np.exp(-((cxm-1152)/400)**2)
        bh=int(r.uniform(hmin,hmax)*k)
        y0=base-bh
        d.rectangle((x,y0,x+bw,base+200),fill=col+(255,))
        if r.random()<0.35: d.rectangle((x+bw*0.3,y0-int(r.uniform(20,50)),x+bw*0.42,y0),fill=col+(255,))
        for wy in range(y0+16,base,int(win*2.6)):
            for wx in range(int(x+12),int(x+bw-12),int(win*2.2)):
                if r.random()<0.42:
                    g=WG[[0,1,2,0,0,1][wi%6]]; wi+=1   # most windows steady-ish, a few groups twinkle
                    ImageDraw.Draw(g).rectangle((wx,wy,wx+win,wy+int(win*1.4)),fill=(255,206,110,int(wa*(0.35+0.65*k))))
        x+=bw+int(r.uniform(-10,14))
    # windows were drawn over the body in the still, so body alpha*alpha and windows alpha*alpha
    for L,name in [(B,f'{tag}_body')]+[(WG[j],f'{tag}_win{j+1}') for j in range(3)]:
        a=np.asarray(L.split()[3]).astype(float)*alpha; L.putalpha(Image.fromarray(a.astype('uint8')))
        if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
        im.alpha_composite(L); save(name)
skyline('15_sky_far',3,600,200,330,(92,72,104),6,150,0.55,1.6,0.0)
skyline('16_sky_near',7,640,150,260,(58,46,66),7,235,0.92,0,0.0)
hz=np.exp(-((cy-600)/70)**2)*0.35
im.alpha_composite(Image.fromarray(np.dstack([np.full((H,W),255),np.full((H,W),170),np.full((H,W),120),hz*255]).astype('uint8'))); save('17_haze')
# garlands: static string + one layer per hanging lantern (drop cord + sprite + glow), pivots at the hook
S=np.asarray(SU).astype(float); p=S[540:665,1560:1625]; R_,G_,B_=p[...,0],p[...,1],p[...,2]
HL=Image.fromarray(np.dstack([p,np.clip(((R_-B_)-55)/30,0,1)*np.clip((R_-150)/40,0,1)*255]).astype('uint8'))
def garland(gi,p0,p1,sag,n,size,blur=0,fade_=1.0,swing=0):
    def pt(t): return (p0[0]+(p1[0]-p0[0])*t, p0[1]+(p1[1]-p0[1])*t+sag*4*t*(1-t))
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    d.line([pt(t) for t in np.linspace(0,1,200)],fill=(70,40,60,int(230*fade_)),width=max(2,int(size/16)))
    if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(L); save(f'25_garland{gi}_string')
    for i in range(n):
        t=(i+0.5)/n; x,y=pt(t); drop=size*0.35; h=size*HL.height/HL.width
        Gl=Image.new('RGBA',(W,H),(0,0,0,0)); R=size*1.1
        ImageDraw.Draw(Gl).ellipse((x-R,y+drop+h*0.5-R,x+R,y+drop+h*0.5+R),fill=(255,190,100,int(95*fade_)))
        im.alpha_composite(Gl.filter(ImageFilter.GaussianBlur(size*0.6)))
        L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
        d.line([(x,y),(x,y+drop)],fill=(70,40,60,int(230*fade_)),width=2)
        s=HL.resize((round(size),round(h)),Image.LANCZOS)
        ang=np.sin(i*1.7)*swing
        if ang: s=s.rotate(ang,resample=Image.BICUBIC,expand=True)
        if fade_<1: s.putalpha(Image.fromarray((np.asarray(s.split()[3]).astype(float)*fade_).astype('uint8')))
        L.alpha_composite(s,(round(x-s.width/2),round(y+drop-2)))
        if blur: L=L.filter(ImageFilter.GaussianBlur(blur))
        im.alpha_composite(L); save(f'26_garland{gi}_lamp{i+1:02d}',anchor=[x,y],size=size)


if os.environ.get('GARL','1')=='1':
    garland(3,(-40,10),(900,60),70,9,30,swing=4)
    garland(4,(1404,60),(2344,10),70,9,30,swing=4)
if os.environ.get('GARLC')=='1':
    garland(5,(700,-6),(1604,-6),60,8,30,swing=4)
# stages
disc=Image.open('disc_clean.png')
DCX,DCY=243*4,321*4
DOX,DOY=int((243-223)*4)-4,int((321-119)*4)-4
G4={'L1':(108,138),'L2':(36,100),'R1':(138,52),'R2':(248,240)}
OBJN={'L1':'rabbit_mortar_bowl','R1':'hanok_pine','R2':'ricecake_rabbits'}
def shadowed(one,name,**meta):
    a1=one.split()[3]; sh1=Image.new('RGBA',(W,H),(120,60,50,0)); sh1.putalpha(a1.point(lambda v:int(v*0.45))); sh1=sh1.filter(ImageFilter.GaussianBlur(10))
    im.alpha_composite(sh1,(6,10)); im.alpha_composite(one); save(name,**meta)
def stage(tag,names,ocx,ocy,canvas_cx,canvas_cy,sc,dsx,dsy,dy={},dx={},pre=[]):
    if dsx>0.01:
      D=disc.resize((round(disc.width*dsx),round(disc.height*dsy)),Image.LANCZOS)
      im.alpha_composite(D,(round(canvas_cx-(DCX-DOX)*dsx),round(canvas_cy-(DCY-DOY)*dsy))); save(f'40_disc_{tag}',anchor=[canvas_cx,canvas_cy])
    for pim,px,py,nm in pre:
        one=Image.new('RGBA',(W,H),(0,0,0,0)); one.alpha_composite(pim,(px,py)); bb=one.getbbox()
        shadowed(one,nm,anchor=[(bb[0]+bb[2])/2,bb[3]])
    for n in names:
        g=Image.open(f'g_{n}'+('v9' if n=='R1' else '')+'_birefnet-general.png')
        gx,gy=G4[n][0]*4,G4[n][1]*4
        g=g.resize((round(g.width*sc),round(g.height*sc)),Image.LANCZOS)
        X0=round(canvas_cx+(gx-ocx)*sc)+dx.get(n,0); Y0=round(canvas_cy+(gy-ocy)*sc)+dy.get(n,0)
        def tocan(px,py): return [X0+(px*4-gx)*sc, Y0+(py*4-gy)*sc]
        one=Image.new('RGBA',(W,H),(0,0,0,0)); one.alpha_composite(g,(X0,Y0))
        mal=None
        if n=='L1':
            poly=[tocan(x,y) for x,y in [(171,195),(205,195),(205,237),(186,235),(173,256),(161,253),(168,233),(173,226)]]
            m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon([tuple(q) for q in poly],fill=255)
            keep=Image.new('L',(W,H),0); k0=tocan(160,244); ImageDraw.Draw(keep).rectangle((k0[0],k0[1],W,H),fill=255)
            m=Image.fromarray(np.minimum(np.asarray(m),255-np.asarray(keep))).filter(ImageFilter.GaussianBlur(0.8))
            oa=np.asarray(one.split()[3]).astype(float); ma=np.asarray(m).astype(float)/255
            mal=one.copy(); mal.putalpha(Image.fromarray((oa*ma).astype('uint8')))
            one.putalpha(Image.fromarray((oa*(1-ma)).astype('uint8')))
            pivot=tocan(167,250)
        bb=one.getbbox()
        shadowed(one,'50_obj_'+n+'_'+OBJN[n],anchor=[(bb[0]+bb[2])/2,bb[3]])
        if mal is not None:
            im.alpha_composite(mal); save('51_obj_L1_mallet',anchor=pivot)
FWD=int(os.environ.get('FW','752')); FHT=int(os.environ.get('FH',str(FWD*9//16))); EDGE=int(os.environ.get('EDGE','40')); FYT=int(os.environ.get('FY',str((H-FHT)//2)))
BOXES=[(EDGE,FYT),(W-EDGE-FWD,FYT)]
stage('C',[],0,0,1152,810,1,1.2,0.42)
stage('L',['L1'],150*4,343*4,int(os.environ.get('LCX','1060')),775,float(os.environ.get('LS','0.36')),0.0001,0.0001,dx={'L1':int(os.environ.get('LDX','-60'))})
stage('R',['R2'],292*4,346*4,int(os.environ.get('RCX','1240')),775,float(os.environ.get('RS','0.36')),0.0001,0.0001,dx={'R2':int(os.environ.get('RDX','-40'))})
import title3d
T=Image.open('title_stack.png'); TW=int(os.environ.get('TW','520')); T=T.resize((TW,round(T.height*TW/T.width)),Image.LANCZOS); T=T.crop(T.getbbox()); tw,th=T.size
T3,pad=title3d.make(T,depth=12,outline=0)
ty=int(os.environ.get('TY','300'))-th//2
im.alpha_composite(T3,(1152-tw//2-pad,ty-pad)); save('61_title_logo',anchor=[1152,ty+th/2])
HD=Image.open('L9/60_title_header.png'); HD=HD.crop(HD.getbbox()); HW=int(os.environ.get('HW','520')); HD=HD.resize((HW,round(HD.height*HW/HD.width)),Image.LANCZOS)
hy=int(os.environ.get('HY','90')); im.alpha_composite(HD,(1152-HW//2,hy-HD.height//2)); save('60_title_header',anchor=[1152,hy])
d=ImageDraw.Draw(im)
for bx,by in BOXES:
    d.rectangle((bx-6,by-6,bx+FWD+5,by+FHT+5),outline=GOLD+(255,),width=6)
    d.rectangle((bx,by,bx+FWD-1,by+FHT-1),fill=(0,0,0,255))
save('80_feed_frame')
full=BG.copy()
for nme in LAYERS: full.alpha_composite(Image.open(f'{LD}/{nme}.png'))
full.convert('RGB').save(OUT)
json.dump({'order':LAYERS,'meta':MAN,'size':[W,H]},open(f'{LD}/manifest.json','w'),indent=1)
print('ok',len(LAYERS),BOXES,FWD,FHT,'logo y',ty,ty+th)
