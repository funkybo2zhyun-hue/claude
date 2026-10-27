import sys,numpy as np
from PIL import Image
from rembg import remove, new_session
S=4
src=Image.open('scene_up.png').convert('RGB')
sess=new_session(sys.argv[1])
G={'L1':(108,138,264,352),'L2':(36,100,150,280),'R1':(138,52,450,262),'R2':(248,240,412,354)}
for k,(a,b,c,d) in [(sys.argv[2],G[sys.argv[2]])]:
    cr=src.crop((a*S,b*S,c*S,d*S))
    m=remove(cr,session=sess,only_mask=True)
    rgba=cr.copy(); rgba.putalpha(m); rgba.save(f'g_{k}_{sys.argv[1]}.png')
    pv=Image.new('RGBA',cr.size,(30,140,60,255)); pv.alpha_composite(rgba); pv.convert('RGB').resize((cr.width//3,cr.height//3)).save(f'gp_{k}.png')
