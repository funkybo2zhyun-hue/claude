import sys, os, numpy as np
from multiprocessing import Pool
from PIL import Image
from render import Renderer, N, FPS
R=None
def init():
    global R; R=Renderer()
def job(i): return R.frame(i / FPS).tobytes()
if __name__=='__main__':
    out=sys.argv[1]
    with open(out,'wb') as f, Pool(4,initializer=init) as pool:
        for k,x in enumerate(pool.imap(job, range(N), chunksize=6)):
            f.write(x)
            if k%600==0: print(k,flush=True)
