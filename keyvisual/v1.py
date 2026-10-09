import sys; sys.path.insert(0,'.')
from compose import *
canvas=Image.new("RGBA",(W,H),SKY+(255,))
dr=ImageDraw.Draw(canvas)
# grass hill band
pts=[(0,H)]
import math
for x in range(0,1700,10): pts.append((x, 500+18*math.sin(x/260)+0.02*x))
pts+= [(1700,H)]
dr.polygon(pts, fill=GRASS+(255,))
# clouds
c1=vec(None and 0 or [0,0,1417,400],170,rects=[(992,31,1355,168)])
c2=vec([0,0,1417,400],130,rects=[(129,93,492,230)])
canvas.alpha_composite(c2,(-60,40)); canvas.alpha_composite(c1,(930,8))
# scene
sc=scene([1010,1740,2700,2880],H)
a=np.asarray(sc.getchannel('A')).astype(float)
ramp=np.clip(np.arange(sc.width)/240,0,1)
sc.putalpha(Image.fromarray((a*ramp[None,:]).astype(np.uint8)))
sx=W-sc.width; canvas.alpha_composite(sc,(sx,0))
# typography
title=vec([250,140,1140,400],268)
sub=vec([300,400,1100,530],118)
d1=vec([120,1430,840,1517],86,keep=is_redwhite)
d2=vec([120,1517,840,1610],86,keep=is_redwhite)
venue=vec([420,540,1000,640],62)
cx=(sx+200)//2
canvas.alpha_composite(title,(cx-title.width//2,52))
canvas.alpha_composite(sub,(cx-sub.width//2,52+268+14))
gap=22; dw=d1.width+gap+d2.width
canvas.alpha_composite(d1,(cx-dw//2,528)); canvas.alpha_composite(d2,(cx-dw//2+d1.width+gap,528))
pw,ph=venue.width+70,venue.height+26
px,py=cx-pw//2,636
dr=ImageDraw.Draw(canvas); dr.rounded_rectangle([px,py,px+pw,py+ph],radius=ph//2,fill=WHITE+(255,))
canvas.alpha_composite(venue,(cx-venue.width//2,py+13))
canvas.convert("RGB").save(sys.argv[1]); print(canvas.size, sx, title.size, sub.size, d1.size,d2.size, venue.size)
