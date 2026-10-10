import sys, math; sys.path.insert(0,'.')
from compose import vec, W, H, SKY, RED, WHITE
from objs import D, draw, obj
from logos import logos
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
S=1.1; Y0=880                      # poster pt -> canvas px: y=(pt-Y0)*S
BAND=150; GY=H-BAND
cy=lambda pt: round((pt-Y0)*S)
canvas=Image.new("RGBA",(W,H),SKY+(255,))

# 1. landscape: the poster's own mountains, river and grass, widened to 10:3
bg_items=[x for i,x in enumerate(D) if (3<=i<=117 and x.get('rect') is not None and x['type']!='clip' and (x['rect'].y1<1232 or x['rect'].width>250)) or i==22 or (117<i<300 and x.get('rect') is not None and x['rect'].width<12 and x['rect'].y1<1232 and x['type']=='f')]
CL=(62,Y0,1356,1440)
bg=draw(bg_items, CL, S, sx=W/((CL[2]-CL[0])*S))
canvas.alpha_composite(bg.resize((W,bg.height),Image.LANCZOS),(0,0))

# 2. clouds
cl=[(992,31,1355,168),(129,93,492,230)]
for rect,h,x,y,flip in [(cl[1],95,330,24,False),(cl[0],110,1980,8,True),(cl[0],70,720,120,False),(cl[1],62,1700,150,True)]:
    c=vec([0,0,1417,400],h,rects=[rect])
    if flip: c=c.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(c,(x,y))

# 3. foreground characters & vehicles from the poster, re-staged across the width
def put(bbox,x,y=None,flip=False,excl=()):
    im,(ox,oy)=obj(bbox,S,excl=excl)
    if flip: im=im.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(im,(x, cy(oy) if y is None else y))
    return im
put([0,1040,460,1420],0,excl=(491,))                        # left RV + blossom tree
put([480,1060,720,1290],520)                    # umbrella picnic
put([1700-1700+980,1075,1460,1420],W-round(480*S)-6)  # right RV + blossom tree
put([860,1080,985,1320],1905)                   # balloon dad
put([700,1195,890,1350],1715)                   # dancers
put([490,1310,770,1500],300)                    # picnic table couple
put([405,1250,545,1320],640,y=478)              # rolled mat

# 4. festoon lights across the lawn
lay=Image.new("RGBA",(W*2,H*2),(0,0,0,0)); fd=ImageDraw.Draw(lay)
def festoon(x0,x1,y0,y1,sag):
    pts=[]
    for t in np.linspace(0,1,120):
        x=x0+(x1-x0)*t; y=y0+(y1-y0)*t+sag*4*t*(1-t); pts.append((x,y))
    fd.line([(x*2,y*2) for x,y in pts],fill=(43,42,42,255),width=5)
    for t in np.linspace(0.03,0.97,int((x1-x0)/52)):
        x=x0+(x1-x0)*t; y=y0+(y1-y0)*t+sag*4*t*(1-t)+8
        fd.ellipse([(x-7)*2,(y-7)*2,(x+7)*2,(y+7)*2],fill=(255,240,190,255))
festoon(250,1300,470,455,70); festoon(1300,2330,455,470,70)
canvas.alpha_composite(lay.resize((W,H),Image.LANCZOS))

LAYERS={}
# 5. peach branches framing the top corners
pr=vec([1120,170,1700,760],300); pl=vec([-300,680,280,1120],230)
canvas.alpha_composite(pl,(0,-24)); canvas.alpha_composite(pr,(W-pr.width,-36))

LAYERS['scene']=canvas.copy()
# 6. title lock-up with a soft halo for long-distance legibility
title=vec([250,140,1140,400],330)
sub=vec([300,400,1100,530],118)
ty=46
block=Image.new("RGBA",(W,H),(0,0,0,0))
for im,(x,y) in [(title,((W-title.width)//2,ty)),(sub,((W-sub.width)//2,ty+330+12))]:
    block.alpha_composite(im,(x,y))
halo=block.getchannel('A').filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(26))
shadow=Image.new("RGBA",(W,H),(255,255,255,0)); shadow.putalpha(halo.point(lambda v:int(v*0.35)))
drop=Image.new("RGBA",(W,H),(120,20,20,0)); drop.putalpha(block.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.45)))
canvas.alpha_composite(shadow); canvas.alpha_composite(drop,(0,8))
LAYERS['backdrop']=canvas.copy()
canvas.alpha_composite(block)
LAYERS['title']=(title,((W-title.width)//2,ty)); LAYERS['sub']=(sub,((W-sub.width)//2,ty+330+12))

# 7. partner logo band
dr=ImageDraw.Draw(canvas)
dr.rectangle([0,GY,W,H],fill=WHITE+(255,)); dr.rectangle([0,GY,W,GY+8],fill=RED+(255,))
lg=logos([200,660,1200,880])
cmd=Image.new("RGBA",(max(lg[6].width,lg[9].width),lg[6].height+40+lg[9].height),(0,0,0,0))
cmd.alpha_composite(lg[6],((cmd.width-lg[6].width)//2,0)); cmd.alpha_composite(lg[9],((cmd.width-lg[9].width)//2,lg[6].height+40))
order=[lg[0],lg[1],lg[3],lg[2],lg[4],lg[5],cmd,lg[7],lg[8]]
A=13500; MAXH=92; sized=[]
for im in order:
    h=min(MAXH, math.sqrt(A*im.height/im.width)); sized.append(im.resize((round(im.width*h/im.height),round(h)),Image.LANCZOS))
margin=110; total=sum(s.width for s in sized); gap=(W-2*margin-total)/(len(sized)-1)
x=margin; my=GY+8+(BAND-8)//2; LAYERS['logos']=[]
for s in sized:
    canvas.alpha_composite(s,(round(x),my-s.height//2)); LAYERS['logos'].append((s,(round(x),my-s.height//2))); x+=s.width+gap
canvas.convert("RGB").save(sys.argv[1]); print("ok", canvas.size)
if len(sys.argv)>2:
    import base64, io
    def b64(im):
        b=io.BytesIO(); im.save(b,"PNG",optimize=True); return base64.b64encode(b.getvalue()).decode()
    # the backdrop (scene, peaches, halo) as one layer; title, subtitle and each logo as separate movable layers
    bd=LAYERS['backdrop'].crop((0,0,W,GY)).convert("RGB")
    b=io.BytesIO(); bd.save(b,"JPEG",quality=90); bdj=base64.b64encode(b.getvalue()).decode()
    els=[f'<img src="data:image/jpeg;base64,{bdj}" alt="Festival scene" style="position:absolute;left:0;top:0;width:{W}px;height:{GY}px">',
         f'<div style="position:absolute;left:0;top:{GY}px;width:{W}px;height:{BAND}px;background:#FFFFFF"></div>',
         f'<div style="position:absolute;left:0;top:{GY}px;width:{W}px;height:8px;background:#EF4642"></div>']
    for k,alt in (('title','고알빙락'),('sub','페스티벌 in 세종')):
        im,(x,y)=LAYERS[k]; els.append(f'<img src="data:image/png;base64,{b64(im)}" alt="{alt}" style="position:absolute;left:{x}px;top:{y}px;width:{im.width}px;height:{im.height}px">')
    for i,(im,(x,y)) in enumerate(LAYERS['logos']):
        els.append(f'<img src="data:image/png;base64,{b64(im)}" alt="Partner logo {i+1}" style="position:absolute;left:{x}px;top:{y}px;width:{im.width}px;height:{im.height}px">')
    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="hz:slide-selector" content=".slide"><title>고알빙락 LED 키비주얼 v3</title>
<style>html,body{{margin:0;padding:0}} .slide{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#33C6F4}}</style></head>
<body><section class="slide" data-canvas-width="{W}" data-canvas-height="{H}">{''.join(els)}</section></body></html>"""
    open(sys.argv[2],"w").write(html); print("html bytes",len(html))
