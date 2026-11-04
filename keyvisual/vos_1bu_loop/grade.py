"""배경(종이+타이틀) 그레이딩: 레벨·감마·채널별 화이트(색 밸런스)·채도·로컬 대비·비네팅.
원본 합성본(Photoshop merged)에 직접 적용, 그림(인물) 그룹 알파로 영역을 나눠 그림은 약하게만.
"""
import sys, os, json
import numpy as np, cv2
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRESETS = {
  # out_white: per-channel output white (sRGB 0-1) → sets paper colour; gamma <1 darkens mids
  'A_웜빈티지': dict(in_black=0.03, in_white=0.97, gamma=0.92, out_black=(0.02, 0.015, 0.01), out_white=(0.80, 0.71, 0.60),
                    sat=1.18, clarity=0.22, vig=0.16, img_strength=0.35),
  'B_웜빈티지딥': dict(in_black=0.04, in_white=0.965, gamma=0.88, out_black=(0.022, 0.015, 0.012), out_white=(0.74, 0.635, 0.515),
                    sat=1.16, clarity=0.26, vig=0.22, img_strength=0.42),
  'C_무드다크': dict(in_black=0.05, in_white=0.95, gamma=0.84, out_black=(0.02, 0.025, 0.03), out_white=(0.66, 0.60, 0.54),
                    sat=0.95, clarity=0.30, vig=0.26, img_strength=0.5),
}


def grade(x, p, H, W):
    # 1) levels with per-channel output range (colour balance lives in out_black/out_white)
    y = np.clip((x - p['in_black']) / (p['in_white'] - p['in_black']), 0, 1) ** (1 / p['gamma'])
    ob = np.array(p['out_black'], np.float32); ow = np.array(p['out_white'], np.float32)
    y = ob + (ow - ob) * y
    # 2) saturation around luma
    l = (y * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    y = l + (y - l) * p['sat']
    # 3) clarity: large-radius local contrast so crumples / ruled lines stay readable after compression
    lb = cv2.GaussianBlur(l[..., 0], (0, 0), 18 * W / 5000)
    y = y + (p['clarity'] * (l[..., 0] - lb))[..., None]
    return np.clip(y, 0, 1)


def vignette(H, W, strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx / W - 0.5) * 2; ny = (yy / H - 0.5) * 2
    r = np.sqrt((nx * 0.92) ** 2 + (ny * 0.62) ** 2)
    return (1 - strength * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6).astype(np.float32)


def make(name, p, out_w=2560):
    M = np.asarray(Image.open(os.path.join(ROOT, 'merged_full.png')).convert('RGB')).astype(np.float32) / 255
    H, W = M.shape[:2]
    ai = np.asarray(Image.open(os.path.join(ROOT, 'grp_img.png')))[..., 3].astype(np.float32) / 255
    # inside the painting: full grade on paper-like watercolour washes (bright + unsaturated), lighter on the people
    lum = (M * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1)
    sat = M.max(-1) - M.min(-1)
    sm = lambda e0, e1, v: np.clip((v - e0) / (e1 - e0), 0, 1) ** 2 * (3 - 2 * np.clip((v - e0) / (e1 - e0), 0, 1))
    paperlike = sm(0.55, 0.78, lum) * (1 - sm(0.10, 0.22, sat))
    paperlike = cv2.GaussianBlur(paperlike, (0, 0), 3)
    s_img = p['img_strength'] + (1 - p['img_strength']) * paperlike
    w = ((1 - ai) + ai * s_img)[..., None]
    G = grade(M, p, H, W)
    out = M * (1 - w) + G * w
    out *= vignette(H, W, p['vig'])[..., None]
    im = Image.fromarray(np.clip(np.round(out * 255), 0, 255).astype(np.uint8))
    return im.resize((out_w, out_w * H // W), Image.LANCZOS)


if __name__ == '__main__':
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    names = sys.argv[2:] or list(PRESETS)
    for n in names:
        make(n, PRESETS[n]).save(f'{od}/base_{n}.png')
        print('saved', n)
