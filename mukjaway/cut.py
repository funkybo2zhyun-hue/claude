import sys
from PIL import Image
from rembg import remove, new_session
name,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6])
b=Image.open('src/bg_rgb.png').convert('RGB').crop((x0,y0,x1,y1))
s=new_session('birefnet-general')
o=remove(b,session=s); o.save(f'cut/{name}.png'); print(name,o.size)
