import sys,numpy as np,torch
from PIL import Image
from spandrel import ModelLoader
m=ModelLoader().load_from_file('x4plus.pth').model.eval()
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype('float32')/255
t=torch.from_numpy(im).permute(2,0,1)[None]
with torch.no_grad(): o=m(t)
o=(o[0].permute(1,2,0).clamp(0,1).numpy()*255+0.5).astype('uint8')
Image.fromarray(o).save(sys.argv[2]); print(o.shape)
