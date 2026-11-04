"""decode the mp4 and dump seam strips (frames N-3..N-1, 0..2) at 100% and 200% for visual check."""
import sys, subprocess, numpy as np
from PIL import Image
W,H=2560,768; fs=W*H*3; N=1800
mp4, out = sys.argv[1], sys.argv[2]
p=subprocess.Popen(['ffmpeg','-loglevel','error','-i',mp4,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
fr={}
for i in range(N):
    b=p.stdout.read(fs)
    if i in (0,1,2,N-3,N-2,N-1): fr[i]=np.frombuffer(b,np.uint8).reshape(H,W,3)
p.stdout.close(); p.wait()
order=[N-3,N-2,N-1,0,1,2]
crop=lambda a,x,y,w,h: a[y:y+h,x:x+w]
# 100%: chalkboard + paper region strips
strip=np.vstack([crop(fr[i],100,40,1400,200) for i in order])
Image.fromarray(strip).save(out+'/seam_100pct_board.png')
strip=np.vstack([np.asarray(Image.fromarray(crop(fr[i],200,60,500,110)).resize((1000,220),Image.NEAREST)) for i in order])
Image.fromarray(strip).save(out+'/seam_200pct_board.png')
strip=np.vstack([crop(fr[i],1560,40,1000,200) for i in order])
Image.fromarray(strip).save(out+'/seam_100pct_paper.png')
d=np.abs(fr[N-1].astype(int)-fr[0]).mean(); d2=np.abs(fr[0].astype(int)-fr[1]).mean()
print('decoded |f1799-f0| %.3f  |f0-f1| %.3f'%(d,d2))
