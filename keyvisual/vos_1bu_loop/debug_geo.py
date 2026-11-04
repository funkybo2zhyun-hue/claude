import sys
import numpy as np, cv2
from PIL import Image
from render import *

def debug(layers, t, out):
    base = np.asarray(Image.open('../base_2560.png').convert('RGB')).astype(np.float32)
    img = (base * 0.45).astype(np.uint8).copy()
    cols = {"far": (90, 140, 255), "mid": (80, 230, 120), "near": (255, 80, 80)}
    for name, brs in layers.items():
        for br in brs:
            lines, polys = branch_geometry(br, t)
            for pts, w in lines:
                cv2.polylines(img, [np.round(pts * 16).astype(np.int32)], False, cols[name], max(1, int(w)), cv2.LINE_AA, 4)
            cv2.fillPoly(img, [np.round(p * 16).astype(np.int32) for p in polys], cols[name], cv2.LINE_AA, 4)
            cv2.circle(img, tuple(int(v) for v in np.clip(br.base, 0, [W - 1, H - 1])), 6, (255, 255, 0), -1)
    Image.fromarray(img).save(out)

if __name__ == '__main__':
    debug(build_scene(), float(sys.argv[2]) if len(sys.argv) > 2 else 0.0, sys.argv[1])
