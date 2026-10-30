import numpy as np,cv2
from PIL import Image
TH=Image.open('title_hi.png'); ah=np.asarray(TH.split()[3])
n_,lab,st,cen=cv2.connectedComponentsWithStats((ah>20).astype(np.uint8),8)
n2,lab2,st2,cen2=cv2.connectedComponentsWithStats((ah>100).astype(np.uint8),8)
TOP=[1,5,10,4,8,6,2,7,3,9]
labs=set()
for i in TOP:
    labs.add(int(lab[int(cen2[i][1]),int(cen2[i][0])])); ys,xs=np.where(lab2==i); labs.add(int(lab[ys[0],xs[0]]))
labs.discard(0)
m=cv2.dilate(np.isin(lab,list(labs)).astype(np.uint8)*255,np.ones((5,5),np.uint8)).astype(float)/255
a=np.asarray(TH.split()[3]).astype(float)
top=TH.copy(); top.putalpha(Image.fromarray((a*m).astype('uint8')))
bot=TH.copy(); bot.putalpha(Image.fromarray((a*(1-m)).astype('uint8')))
top=top.crop(top.getbbox()); bot=bot.crop(bot.getbbox())
gap=int(TH.height*0.06)
Wd=max(top.width,bot.width); out=Image.new('RGBA',(Wd,top.height+gap+bot.height),(0,0,0,0))
out.alpha_composite(top,((Wd-top.width)//2,0)); out.alpha_composite(bot,((Wd-bot.width)//2,top.height+gap))
out.save('title_stack.png'); print(top.size,bot.size,out.size)
