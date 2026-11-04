"""VOS 1부 키비주얼 루프 v03 — 배경 톤 그레이딩 + 실제 질감의 먼지.

먼지는 동그란 점이 아니라 실제 공기 중 먼지처럼:
  speck  : 불규칙한 알갱이(작은 조각 2~4개가 붙은 모양, 내부 농도 얼룩)
  flake  : 얇은 조각 — 가장자리가 너덜너덜하고 반투명, 테두리가 빛을 받음. 공중에서 뒤집히며 정면일 때 반짝
  fluff  : 섬유가 엉킨 솜먼지(가는 털 가닥 + 성긴 심)
  fiber  : 굵기·농도가 들쭉날쭉한 섬유 가닥, 꺾임과 잔털
  far    : 멀리 있는 아주 작은 알갱이(느리게 움직임 = 원근)
각 입자의 질감은 한 번 만든 뒤 고정(강체). 매 프레임 회전·3D 뒤집힘(단축)·이동만 함.
모든 움직임은 L초 주기의 정수배 고조파 → 프레임 N == 프레임 0.
"""
import math, os, sys
import numpy as np
import cv2
from PIL import Image

W, H = 2560, 768
FPS = 60
L = 30.0
N = int(round(FPS * L))
TAU = 2 * math.pi
SS = 6                      # supersampling of textures and of the per-particle raster
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get('VOS_BASE', os.path.join(ROOT, 'grade', 'base_B_웜빈티지딥.png'))


def srgb2lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin2srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def periodic(t, terms):
    return sum(a * math.sin(TAU * k * t / L + p) for k, a, p in terms)


# ---------------------------------------------------------------- texture helpers (hi-res, SS px per final px)
def fbm(rng, h, w, cell, octaves=4):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for _ in range(octaves):
        gh, gw = max(2, int(h / cell) + 2), max(2, int(w / cell) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.55
        cell = max(1.0, cell / 2)
    out /= tot
    return (out - out.min()) / (np.ptp(out) + 1e-6)


def jagged_poly(rng, n, r, aspect, jit):
    a = np.sort(rng.uniform(0, TAU, n))
    rad = r * rng.uniform(1 - jit, 1, n)
    pts = np.stack([np.cos(a) * rad, np.sin(a) * rad * aspect], 1)
    for i in rng.choice(n, max(1, n // 4), replace=False):
        pts[i] *= rng.uniform(0.35, 0.65)            # concave nicks — outline is never an oval
    return pts


def canvas_for(extent):
    n = int(math.ceil(extent * SS)) + 12
    n += n % 2
    return np.zeros((n, n), np.float32), np.array([n / 2, n / 2])


def fill(can, c, pts_px, val=1.0):
    q = np.round((pts_px * SS + c) * 16).astype(np.int32)
    tmp = np.zeros(can.shape, np.uint8)
    cv2.fillPoly(tmp, [q], 255, cv2.LINE_AA, 4)
    np.maximum(can, tmp.astype(np.float32) / 255 * val, out=can)


def stroke(can, c, p0, p1, width_px, val):
    q = np.round((np.array([p0, p1]) * SS + c) * 16).astype(np.int32)
    tmp = np.zeros(can.shape, np.uint8)
    cv2.polylines(tmp, [q], False, 255, max(1, int(round(width_px * SS))), cv2.LINE_AA, 4)
    np.maximum(can, tmp.astype(np.float32) / 255 * val, out=can)


def curl_path(rng, length, seg, curl_sd=0.12, kinks=0, curl0=0.3):
    n = max(3, int(length / seg))
    ang = rng.uniform(0, TAU); curl = rng.uniform(-curl0, curl0)
    kink_at = set(rng.choice(range(1, n), min(kinks, n - 1), replace=False).tolist()) if kinks else set()
    p = [np.zeros(2)]
    for i in range(n):
        curl += rng.normal(0, curl_sd)
        ang += curl * 0.35
        if i in kink_at:
            ang += rng.choice([-1, 1]) * rng.uniform(0.6, 1.3)
        p.append(p[-1] + seg * np.array([math.cos(ang), math.sin(ang)]))
    return np.array(p)


def noise1d(rng, n, cells=5):
    g = rng.random(cells + 2).astype(np.float32)
    return np.interp(np.linspace(0, cells + 1, n), np.arange(cells + 2), g)


# ---------------------------------------------------------------- particle textures
def tex_speck(rng, D):
    can, c = canvas_for(D * 1.8)
    for _ in range(int(rng.integers(2, 5))):
        off = rng.normal(0, D * 0.18, 2)
        fill(can, c, jagged_poly(rng, int(rng.integers(5, 8)), D * 0.5 * rng.uniform(0.45, 0.85),
                                 rng.uniform(0.5, 1.0), 0.45) + off, rng.uniform(0.7, 1.0))
    can *= 0.6 + 0.4 * fbm(rng, *can.shape, cell=SS * 0.8)
    return cv2.GaussianBlur(can, (0, 0), SS * rng.uniform(0.12, 0.3)), c


def chip_outline(rng, D, aspect):
    """angular chip with torn edges: few corners of very different radius, then fractal edge displacement."""
    n = int(rng.integers(5, 9))
    gaps = rng.uniform(0.5, 1.5, n); a = np.cumsum(gaps / gaps.sum() * TAU) + rng.uniform(0, TAU)
    rad = D * 0.5 * rng.uniform(0.45, 1.0, n)
    P = np.stack([np.cos(a) * rad, np.sin(a) * rad * aspect], 1)
    for lvl in range(4):                                   # midpoint displacement → ragged, torn edge
        Q = []
        for i in range(len(P)):
            p0, p1 = P[i], P[(i + 1) % len(P)]
            e = p1 - p0; ln = np.hypot(*e) + 1e-9
            nrm = np.array([-e[1], e[0]]) / ln
            Q += [p0, (p0 + p1) / 2 + nrm * rng.normal(0, 0.16 * ln)]
        P = np.array(Q)
    return P


def tex_flake(rng, D, soft=0.3):
    can, c = canvas_for(D * 1.6)
    fill(can, c, chip_outline(rng, D, rng.uniform(0.5, 0.9)))
    m = (can > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    rim = np.exp(-dist / (SS * 0.55))                      # thin edge catches the light
    body = 0.28 + 0.4 * fbm(rng, *can.shape, cell=SS * 1.3)
    a = m * np.clip(body + 0.6 * rim, 0, 1)
    if rng.random() < 0.55:                                # a fold/crease across the flake
        ang = rng.uniform(0, TAU); off = rng.normal(0, D * 0.12, 2)
        crease = np.zeros_like(can)
        stroke(crease, c, off - D * np.array([math.cos(ang), math.sin(ang)]), off + D * np.array([math.cos(ang), math.sin(ang)]), 0.3, 0.35)
        a = np.clip(a + m * crease, 0, 1)
    return cv2.GaussianBlur(a.astype(np.float32), (0, 0), SS * soft), c


def tex_fluff(rng, D):
    """loose tangle of hairs (lint): strands start anywhere in an irregular blob and cross each other."""
    can, c = canvas_for(D * 1.35)
    asp = rng.uniform(0.55, 0.9); ang = rng.uniform(0, TAU)
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    strands = np.zeros_like(can)
    for _ in range(int(D * 0.75) + 4):
        st = R @ (rng.normal(0, 1, 2) * [D * 0.16, D * 0.16 * asp])
        p = curl_path(rng, D * rng.uniform(0.3, 0.8), 0.45, 0.07, curl0=0.2)
        p = p - p[int(len(p) * rng.uniform(0.3, 0.7))] + st
        wid, val = rng.uniform(0.17, 0.33), rng.uniform(0.4, 0.85)
        av = 0.45 + 0.55 * noise1d(rng, len(p))
        for i in range(len(p) - 1):
            stroke(strands, c, p[i], p[i + 1], wid, val * av[i])
    core = np.zeros_like(can)
    for _ in range(int(rng.integers(2, 5))):               # a couple of denser matted bits, not a disc
        off = R @ (rng.normal(0, 1, 2) * [D * 0.08, D * 0.08 * asp])
        fill(core, c, jagged_poly(rng, 7, D * rng.uniform(0.04, 0.09), rng.uniform(0.4, 0.9), 0.5) + off, rng.uniform(0.35, 0.6))
    a = np.clip(strands + core, 0, 1)
    a *= 0.7 + 0.3 * fbm(rng, *can.shape, cell=SS * 1.0)
    return cv2.GaussianBlur(a, (0, 0), SS * 0.2), c


def tex_fiber(rng, Lf):
    can, c = canvas_for(Lf * 1.15)
    for _ in range(50):                                     # gentle curve or S, never a closed loop
        p = curl_path(rng, Lf, 0.5, 0.035, kinks=int(rng.integers(0, 3)), curl0=0.12)
        if np.hypot(*(p[-1] - p[0])) > 0.6 * Lf:
            break
    p -= p.mean(0)
    n = len(p)
    s = np.linspace(0, 1, n)
    w0 = rng.uniform(0.28, 0.55)
    wid = w0 * np.sin(np.pi * np.clip(s, 0.02, 0.98)) ** 0.35 * (0.65 + 0.7 * noise1d(rng, n, 6))
    av = 0.45 + 0.55 * noise1d(rng, n, 7)
    for i in range(n - 1):
        stroke(can, c, p[i], p[i + 1], wid[i], av[i])
    for _ in range(int(rng.integers(0, 4))):                  # stray hairs
        j = int(rng.integers(2, n - 2))
        h = curl_path(rng, rng.uniform(1.0, 3.0), 0.4, 0.25) + p[j]
        for i in range(len(h) - 1):
            stroke(can, c, h[i], h[i + 1], 0.17, 0.5)
    return cv2.GaussianBlur(can, (0, 0), SS * 0.15), c


# ---------------------------------------------------------------- particles
def build_dust(seed=37):
    rng = np.random.default_rng(seed)
    parts = []

    def base(kind, zone, drift, tex, amp, spin, tumble):
        d = dict(kind=kind, x0=rng.uniform(*zone[0]), y0=rng.uniform(*zone[1]))
        d['mx'] = [(k, drift * rng.uniform(0.5, 1.0) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
        d['my'] = [(k, drift * rng.uniform(0.4, 0.9) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
        jit = 0.5 + drift / 60
        d['jx'] = [(int(k), jit * rng.uniform(0.8, 1.6), rng.uniform(0, TAU)) for k in rng.choice(range(4, 9), 2, replace=False)]
        d['jy'] = [(int(k), jit * rng.uniform(0.8, 1.6), rng.uniform(0, TAU)) for k in rng.choice(range(4, 9), 2, replace=False)]
        d['rot0'] = rng.uniform(0, TAU)
        d['spin'] = int(rng.choice(spin))
        d['tumble'] = int(rng.integers(*tumble))
        d['tex'], d['c'] = tex
        d['amp'] = amp
        d['col'] = np.array((1.0, rng.uniform(0.92, 0.97), rng.uniform(0.80, 0.90)), np.float32)
        parts.append(d)

    left, full, paper = ((0, 1520), (6, 762)), ((0, 2560), (6, 762)), ((1520, 2554), (6, 762))
    for zone, n in ((left, 50), (paper, 20)):          # far: tiny, slow (parallax)
        for _ in range(n):
            base('far', zone, 22, tex_speck(rng, rng.uniform(1.6, 2.6)), rng.uniform(0.9, 1.3), [-1, 1], (2, 6))
    for zone, n in ((left, 60), (paper, 24)):
        for _ in range(n):
            base('speck', zone, 40, tex_speck(rng, rng.uniform(3.0, 5.2)), rng.uniform(1.1, 1.6), [-2, -1, 1, 2], (2, 7))
    for zone, n in ((left, 28), (paper, 12)):
        for _ in range(n):
            base('flake', zone, 48, tex_flake(rng, rng.uniform(3.5, 8.0)), rng.uniform(0.85, 1.3), [-3, -2, -1, 1, 2, 3], (3, 9))
    for zone, n in ((left, 4), (paper, 2)):                 # nearer flakes: bigger, a little soft, still torn-edged
        for _ in range(n):
            base('flake', zone, 80, tex_flake(rng, rng.uniform(10, 15), soft=rng.uniform(0.6, 0.9)), rng.uniform(0.35, 0.5), [-2, -1, 1, 2], (2, 5))
    for zone, n in ((left, 6), (paper, 3)):
        for _ in range(n):
            base('fluff', zone, 58, tex_fluff(rng, rng.uniform(10, 20)), rng.uniform(0.75, 1.05), [-1, 1], (1, 3))
    for zone, n in ((left, 10), (paper, 4)):
        for _ in range(n):
            base('fiber', zone, 55, tex_fiber(rng, rng.uniform(8, 22)), rng.uniform(0.7, 1.0), [-1, 1], (1, 4))
    return parts


def pose(d, t):
    x = d['x0'] + periodic(t, d['mx']) + periodic(t, d['jx'])
    y = d['y0'] + periodic(t, d['my']) + periodic(t, d['jy'])
    th = d['rot0'] + TAU * d['spin'] * t / L + 0.25 * math.sin(TAU * 3 * t / L + d['rot0'])
    tilt = TAU * d['tumble'] * t / L + d['rot0'] * 1.7
    ct = math.cos(tilt)
    k = d['kind']
    if k in ('speck', 'far'):
        sx, sy, g = 1.0, max(0.35, abs(ct)), 0.55 + 0.45 * (0.5 + 0.5 * ct) ** 2
    elif k == 'flake':                      # thin plate: foreshortens to its edge, flashes when face-on
        sx, sy, g = 1.0, max(0.12, abs(ct)), 0.22 + 0.78 * max(0.0, ct) ** 4
    elif k == 'fluff':                      # loose 3D clump: only mild change in silhouette
        sx, sy, g = 1.0, 0.78 + 0.22 * abs(ct), 0.82 + 0.18 * ct
    else:                                   # fibre turning in depth: apparent length changes
        sx, sy, g = 0.55 + 0.45 * abs(ct), 1.0, 0.65 + 0.35 * (0.5 + 0.5 * ct)
    return x, y, th, sx, sy, g


def sprite(d, t):
    x, y, th, sx, sy, g = pose(d, t)
    tex, c = d['tex'], d['c']
    half = tex.shape[0] / 2 / SS
    bx0, by0 = int(math.floor(x - half)) - 1, int(math.floor(y - half)) - 1
    bx1, by1 = int(math.ceil(x + half)) + 1, int(math.ceil(y + half)) + 1
    if bx1 <= 0 or by1 <= 0 or bx0 >= W or by0 >= H:
        return None
    w, h = bx1 - bx0, by1 - by0
    cs, sn = math.cos(th), math.sin(th)
    A = np.array([[cs, -sn], [sn, cs]]) @ np.diag([sx, sy])
    off = SS * (np.array([x, y]) - [bx0, by0]) - A @ c
    M = np.hstack([A, off[:, None]]).astype(np.float32)
    hi = cv2.warpAffine(tex, M, (w * SS, h * SS), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = cv2.resize(hi, (w, h), interpolation=cv2.INTER_AREA)
    return a * (d['amp'] * g), bx0, by0


def render_dust(parts, t):
    acc = np.zeros((H, W, 3), np.float32)
    for d in parts:
        r = sprite(d, t)
        if r is None:
            continue
        a, bx0, by0 = r
        h, w = a.shape
        x0, y0 = max(bx0, 0), max(by0, 0)
        x1, y1 = min(bx0 + w, W), min(by0 + h, H)
        acc[y0:y1, x0:x1] += a[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0, None] * d['col'][None, None, :]
    return acc


class Renderer:
    def __init__(self):
        self.base = np.asarray(Image.open(BASE).convert('RGB')).copy()
        self.base_lin = srgb2lin(self.base.astype(np.float32) / 255)
        self.dust = build_dust()

    def frame(self, t):
        dust = render_dust(self.dust, t)
        img = self.base.copy()
        m = dust.max(-1) > 1e-3
        if m.any():
            img[m] = np.clip(np.round(lin2srgb(self.base_lin[m] + dust[m]) * 255), 0, 255).astype(np.uint8)
        return img


if __name__ == '__main__':
    r = Renderer()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for t in [float(x) for x in sys.argv[2:]]:
        Image.fromarray(r.frame(t)).save(f'{out}/still_t{t:05.2f}.png')
