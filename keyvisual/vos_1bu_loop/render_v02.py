"""VOS 1부 키비주얼 루프 v02 — 원본 그대로 + 먼지만.

원본 합성본 픽셀은 그대로(먼지가 지나가는 자리 외에는 비트 단위로 동일).
먼지 입자만 L초 주기의 정수배 고조파로 떠다님 → 프레임 N == 프레임 0.
"""
import math, os, sys
import numpy as np
from PIL import Image

W, H = 2560, 768
FPS = 60
L = 30.0
N = int(round(FPS * L))
TAU = 2 * math.pi
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def srgb2lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin2srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def periodic(t, terms):
    return sum(a * math.sin(TAU * k * t / L + p) for k, a, p in terms)


DUST_COL = np.array((1.0, 0.95, 0.86), np.float32)   # warm white, like motes in afternoon air


def build_dust(seed=21):
    rng = np.random.default_rng(seed)
    parts = []

    def add(n, sig, amp, zone, drift):
        for _ in range(n):
            d = dict(x0=rng.uniform(*zone[0]), y0=rng.uniform(*zone[1]), sig=rng.uniform(*sig), amp=rng.uniform(*amp))
            # lazy closed meander (k=1..3) — larger for nearer motes (parallax) — plus a tiny brownian wobble (k=4..8)
            d['mx'] = [(k, drift * rng.uniform(0.5, 1.0) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
            d['my'] = [(k, drift * rng.uniform(0.4, 0.9) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
            d['jx'] = [(int(k), rng.uniform(1.0, 2.5), rng.uniform(0, TAU)) for k in rng.choice(range(4, 9), 2, replace=False)]
            d['jy'] = [(int(k), rng.uniform(1.0, 2.5), rng.uniform(0, TAU)) for k in rng.choice(range(4, 9), 2, replace=False)]
            # slow glint as the flake tumbles (0.2–0.9 Hz), never fully off
            d['tw'] = (int(rng.integers(6, 28)), rng.uniform(0, TAU), rng.uniform(0.25, 0.45))
            parts.append(d)

    add(70, (1.2, 1.9), (0.30, 0.55), ((0, 1520), (8, 760)), 40)      # fine motes over the classroom painting
    add(30, (2.0, 3.0), (0.16, 0.30), ((0, 1520), (0, 768)), 60)      # a little nearer, softer
    add(14, (1.3, 2.2), (0.25, 0.45), ((1520, 2552), (8, 760)), 40)   # sparse in front of the paper
    add(5, (5.5, 8.0), (0.045, 0.070), ((0, 2560), (0, 768)), 90)     # very few near, defocused
    return parts


def render_dust(parts, t):
    acc = np.zeros((H, W), np.float32)
    for d in parts:
        x = d['x0'] + periodic(t, d['mx']) + periodic(t, d['jx'])
        y = d['y0'] + periodic(t, d['my']) + periodic(t, d['jy'])
        k, ph, depth = d['tw']
        tw = 1 - depth + depth * (0.5 + 0.5 * math.sin(TAU * k * t / L + ph))
        a = d['amp'] * tw
        sg = d['sig']
        R = int(math.ceil(sg * 3.5)) + 1
        xi, yi = int(math.floor(x)), int(math.floor(y))
        x0, x1 = max(xi - R, 0), min(xi + R + 1, W)
        y0, y1 = max(yi - R, 0), min(yi + R + 1, H)
        if x0 >= x1 or y0 >= y1:
            continue
        xs = np.arange(x0, x1) + 0.5 - x
        ys = np.arange(y0, y1) + 0.5 - y
        acc[y0:y1, x0:x1] += a * np.exp(-(ys[:, None] ** 2 + xs[None, :] ** 2) / (2 * sg * sg))
    return acc


class Renderer:
    def __init__(self):
        self.base = np.asarray(Image.open(os.path.join(ROOT, 'base_2560.png')).convert('RGB')).copy()
        self.base_lin = srgb2lin(self.base.astype(np.float32) / 255)
        self.dust = build_dust()

    def frame(self, t):
        dust = render_dust(self.dust, t)
        img = self.base.copy()
        m = dust > 1e-3                       # only touch pixels a mote actually covers
        if m.any():
            lin = self.base_lin[m] + dust[m][:, None] * DUST_COL[None, :]
            img[m] = np.clip(np.round(lin2srgb(lin) * 255), 0, 255).astype(np.uint8)
        return img


if __name__ == '__main__':
    r = Renderer()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for t in [float(x) for x in sys.argv[2:]]:
        Image.fromarray(r.frame(t)).save(f'{out}/still_t{t:05.2f}.png')
