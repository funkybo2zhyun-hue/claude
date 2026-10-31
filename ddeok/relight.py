import numpy as np, cv2
from PIL import Image
g=Image.open('g_R1v8_birefnet-general.png').convert('RGBA'); A=np.asarray(g).astype(np.float32)
rgb=A[...,:3]; a=A[...,3]
R,G,B=rgb[...,0],rgb[...,1],rgb[...,2]
win=((R>225)&(G>170)&(B<190)&(R-B>60)).astype(np.float32)
win=cv2.morphologyEx(win,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
win=cv2.GaussianBlur(win,(0,0),1.0)
warm=np.clip((R-B-40)/60,0,1)               # only warm-lit surfaces get graded
lum=0.299*R+0.587*G+0.114*B
# neutralise the orange flood: pull toward a cooler, dimmer night palette, keep hue of the paint
k=warm*(1-win)
gray=lum[...,None]
desat=gray+(rgb-gray)*0.86
night=desat*np.array([0.80,0.74,0.86],np.float32)+np.array([2,0,10],np.float32)
out=rgb*(1-k[...,None])+night*k[...,None]
# light that actually comes from the windows: soft warm pool spreading over the wall
src=cv2.GaussianBlur(win,(0,0),3)
spill=cv2.GaussianBlur(win,(0,0),22)*1.6+cv2.GaussianBlur(win,(0,0),8)*0.6
spill=np.clip(spill,0,1)*(1-win)*(a/255)
out=out+spill[...,None]*np.array([95,55,10],np.float32)*(0.4+0.6*warm[...,None])
# windows a touch brighter/warmer so they read as the light source
out=out*(1-win[...,None])+np.minimum(rgb*np.array([1.03,1.0,0.9]),255)*win[...,None]
Image.fromarray(np.dstack([np.clip(out,0,255),a]).astype('uint8')).save('g_R1v9_birefnet-general.png')
bg=Image.new('RGBA',g.size,(90,70,100,255)); bg.alpha_composite(Image.open('g_R1v9_birefnet-general.png'))
bg2=Image.new('RGBA',g.size,(90,70,100,255)); bg2.alpha_composite(g)
o=Image.new('RGB',(848*2,640)); o.paste(bg2.crop((400,200,1248,840)),(0,0)); o.paste(bg.crop((400,200,1248,840)),(848,0)); o.save('z_relight.png')
