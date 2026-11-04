import sys, numpy as np
from multiprocessing import Pool
from render_v03 import Renderer, N, FPS
R=None
def init():
    global R; R=Renderer()
def job(i): return R.frame(i / FPS).tobytes()
if __name__=='__main__':
    with open(sys.argv[1],'wb') as f, Pool(4,initializer=init) as pool:
        for x in pool.imap(job, range(N), chunksize=10): f.write(x)
