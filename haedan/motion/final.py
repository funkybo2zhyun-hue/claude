# Final 해단식 loops in one pass, float all the way, static TPDF dither before 8-bit, high-quality bt709 encode
# outputs: BG only, A (sheen + star glints), B (glyph wave) — 3072x1728, 60 fps, 20 s seamless
import sys, subprocess, numpy as np
from multiprocessing import Pool
sys.path.insert(0,'/root/hd'); sys.path.insert(0,'/root/hd/motion')
import loop2, motionlib as M
W,H,FPS,N=3072,1728,60,1200
rng=np.random.default_rng(7)
DITHER=(rng.random((H,W,3),dtype=np.float32)-rng.random((H,W,3),dtype=np.float32))  # TPDF, ±1 LSB, same every frame
def q(img): return np.clip(np.clip(img,0,1)*255+DITHER+0.5,0,255).astype(np.uint8).tobytes()
def screen(img,add): return img if add is None else 1-(1-img)*(1-np.clip(add,0,1))
def make(k):
    t=k/FPS
    bg=loop2.frame_float(k)
    base=M.over(M.over(bg,*M.top),*M.info)
    out=[q(bg)]
    for f in (M.optA,M.optB):
        r=f(t); img=M.over(base,r[0],r[1])
        if len(r)>2: img=screen(img,r[2])
        out.append(q(img))
    return out
def enc(path):
    return subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-vf','scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int',
        '-c:v','libx264','-preset','slow','-tune','grain','-crf','10','-x264-params','aq-mode=3',
        '-g','60','-keyint_min','60','-sc_threshold','0','-pix_fmt','yuv420p',
        '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
        '-movflags','+faststart','-tag:v','avc1',path],stdin=subprocess.PIPE)
if __name__=='__main__':
    outs=sys.argv[1:4]
    if len(sys.argv)>4:   # test frames only
        from PIL import Image
        for k in map(int,sys.argv[4].split(',')):
            for o,b in zip(outs,make(k)): Image.frombytes('RGB',(W,H),b).save(f'{o}_f{k}.png')
        sys.exit()
    E=[enc(o) for o in outs]
    with Pool(4) as pool:
        for i,bs in enumerate(pool.imap(make,range(N),chunksize=2)):
            for e,b in zip(E,bs): e.stdin.write(b)
            if i%60==0: print('frame',i,flush=True)
    for e in E: e.stdin.close(); e.wait()
