import sys; sys.argv=[sys.argv[0]]+sys.argv[1:]
from multiprocessing import Pool
sys.path.insert(0,'/root/mk/anim')
import render as R
from PIL import Image
def f(t): return R.frame(round(t*R.FPS)).crop(BOX).resize((int((BOX[2]-BOX[0])*SC),int((BOX[3]-BOX[1])*SC)),Image.LANCZOS)
if __name__=='__main__':
    out=sys.argv[1]; t0,t1,st=map(float,sys.argv[2:5]); BOX=tuple(map(int,sys.argv[5].split(','))); SC=float(sys.argv[6]); cols=int(sys.argv[7])
    ts=[t0+i*st for i in range(int(round((t1-t0)/st))+1)]
    import builtins; builtins.BOX=BOX; builtins.SC=SC
    with Pool(4) as p: ims=p.map(f,ts)
    w,h=ims[0].size; rows=(len(ims)+cols-1)//cols
    sh=Image.new('RGB',(w*cols,h*rows))
    for i,im in enumerate(ims): sh.paste(im,((i%cols)*w,(i//cols)*h))
    sh.save(out); print(len(ims),sh.size)
