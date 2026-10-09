import pymupdf, numpy as np
from PIL import Image
from scipy import ndimage
P=pymupdf.open("src/2026_goalbingrock_sejong_logo.ai")[0]
def logos(region, z=6, out=None):
    R=pymupdf.Rect(region)
    pix=P.get_pixmap(matrix=pymupdf.Matrix(z,z), clip=R)
    im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
    a=np.asarray(im).astype(int)
    bg=(a.min(-1)>228)
    fg=~bg
    lab,n=ndimage.label(ndimage.binary_dilation(fg,iterations=int(7*z)))
    boxes=[]
    for s in ndimage.find_objects(lab):
        y,x=s; 
        if (y.stop-y.start)*(x.stop-x.start)<(20*z)**2: continue
        boxes.append((x.start,y.start,x.stop,y.stop))
    res=[]
    for b in sorted(boxes,key=lambda b:(round(b[1]/(60*z)),b[0])):
        c=im.crop(b); m=Image.fromarray((fg[b[1]:b[3],b[0]:b[2]]*255).astype(np.uint8))
        rgba=c.convert("RGBA"); 
        # soft alpha: distance from white-ish background
        al=np.clip((230-np.asarray(c).astype(int).min(-1))*255/32,0,255).astype(np.uint8)
        rgba.putalpha(Image.fromarray(al))
        bb=rgba.getchannel('A').getbbox(); res.append(rgba.crop(bb))
    return res
if __name__=="__main__":
    L=logos([200,660,1200,880])
    print(len(L),[l.size for l in L])
    for i,l in enumerate(L): l.save(f"/tmp/claude-0/-home-user-claude/9ecfb4e2-c42f-5367-9fe7-b94789437e3e/scratchpad/logo_{i}.png")
