import sys, subprocess, numpy as np, os, cv2
W,H=2560,768; fs=W*H*3; N=1800
src, out, crf, params = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','60','-i',src,
     '-c:v','libx264','-preset','slower',*(['-qp',crf[2:]] if crf.startswith('qp') else ['-crf',crf]),'-x264-params',params,'-profile:v','high','-pix_fmt','yuv420p',
     '-vf','scale=out_color_matrix=bt709:out_range=tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
     '-color_range','tv','-movflags','+faststart',out]
subprocess.run(cmd,check=True)
p=subprocess.Popen(['ffmpeg','-loglevel','error','-i',out,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
s=open(src,'rb'); first=prev=None; steps=[]; lo=[]; errs=[]; n=0
while True:
    b=p.stdout.read(fs)
    if len(b)<fs: break
    a=np.frombuffer(b,np.uint8).reshape(H,W,3).astype(np.float32)
    o=np.frombuffer(s.read(fs),np.uint8).reshape(H,W,3).astype(np.float32)
    errs.append(np.abs(a-o).mean())
    if first is None: first=a
    if prev is not None:
        d=(a-prev).mean(2); steps.append(np.abs(d).mean()); lo.append(np.abs(cv2.GaussianBlur(d,(0,0),6)).mean())
    prev=a; n+=1
d=(first-prev).mean(2); seam=np.abs(d).mean(); seamlo=np.abs(cv2.GaussianBlur(d,(0,0),6)).mean()
steps=np.array(steps); lo=np.array(lo)
print(f'{out}: {os.path.getsize(out)/1e6:.1f}MB frames {n}')
print(f'  step median {np.median(steps):.3f} p99 {np.percentile(steps,99):.3f} max {steps.max():.3f} (frame {steps.argmax()+1})')
print(f'  lowfreq step median {np.median(lo):.3f} max {lo.max():.3f}')
print(f'  seam 1799->0: {seam:.3f} (ratio {seam/np.median(steps):.2f}), lowfreq {seamlo:.3f}')
print(f'  error vs lossless: mean {np.mean(errs):.3f}  max {np.max(errs):.3f}  first {errs[0]:.3f} last {errs[-1]:.3f}')
np.save(out+'.steps.npy', steps)
