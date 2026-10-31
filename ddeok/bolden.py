import numpy as np, cv2
from PIL import Image
def bolden(T,r):
    A=np.asarray(T.convert('RGBA')).astype(np.float32); a=A[...,3]/255
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
    a2=cv2.dilate(a,k); a2=cv2.GaussianBlur(a2,(0,0),r*0.25+0.5); a2=np.clip((a2-0.5)*3+0.5,0,1)
    a2=np.maximum(a2,a)
    s=r*1.2+2
    num=cv2.GaussianBlur(A[...,:3]*a[...,None],(0,0),s); den=cv2.GaussianBlur(a,(0,0),s)[...,None]
    fill=num/np.maximum(den,1e-4)
    rgb=np.where(a[...,None]>0.6,A[...,:3],fill)
    return Image.fromarray(np.dstack([np.clip(rgb,0,255),a2*255]).astype('uint8'))
if __name__=='__main__':
    import sys; r=int(sys.argv[1]); bolden(Image.open('title_hi.png'),r).save(f'title_hi_b{r}.png')
