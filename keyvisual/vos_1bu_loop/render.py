import math, sys, os
import numpy as np
import cv2
from PIL import Image
from scene import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- params (v01)
P = dict(
    amb=0.54,          # skylight (shade) level, relative
    sun=0.46,          # direct sun added on top
    norm_lit=1.08,     # what a fully sunlit pixel becomes (relative to original)
    sun_col=(1.06, 1.00, 0.86),
    amb_col=(0.97, 0.99, 1.04),
    shaft=0.085,       # haze shafts (linear add)
    dust=1.0,
)


def build_scene(seed=8):
    rng = np.random.default_rng(seed)
    layers = {"far": [], "mid": [], "near": []}
    # each spray gets its own RNG (seeded from its anchor) so adding one never reshuffles the others
    B = lambda base, *a, **k: Branch(np.random.default_rng(seed * 1000003 + (int(base[0]) + 5000) * 7919 + (int(base[1]) + 5000) * 104729), base, *a, **k)
    far = dict(maxdepth=2, leaf_density=2.6, sway_amp=0.010, droop=0.03, lines=False)
    # far canopy (blurry): top-left mass, fringe along the top (kept above the heads), top-right mass
    for (bx, by, ang, ln, ll) in [(-90, -30, 12, 420, 30), (130, -120, 70, 250, 30), (330, -110, 96, 215, 28),
                                  (420, -120, 80, 190, 26), (610, -110, 88, 150, 24), (930, -100, 98, 120, 24),
                                  (1370, -115, 90, 170, 26), (1480, -120, 80, 200, 28), (1560, -105, 100, 150, 24),
                                  (1890, -100, 88, 130, 24), (2160, -115, 94, 190, 28), (2400, -120, 88, 200, 28),
                                  (2700, -30, 168, 430, 30), (2580, -140, 118, 300, 30)]:
        layers["far"].append(B((bx, by), ang, ln, leaf_len=ll, **far))
    # mid: spray down the left edge, one over the chalkboard, one in from the right edge
    mid = dict(maxdepth=2, leaf_density=2.2, sway_amp=0.013, droop=0.03)
    layers["mid"].append(B((-50, 30), 78, 380, leaf_len=32, **mid))
    layers["mid"].append(B((480, -70), 90, 165, leaf_len=30, **mid))
    layers["mid"].append(B((900, -90), 92, 250, leaf_len=30, **mid))
    layers["mid"].append(B((2690, 330), 196, 210, leaf_len=32, **mid))
    # near (sharpest): hero spray hanging from the top-right corner into the right margin
    layers["near"].append(B((-30, -40), 52, 300, leaf_len=40, maxdepth=2, leaf_density=1.8, sway_amp=0.016, droop=0.05))
    layers["near"].append(B((2600, -20), 118, 340, leaf_len=46, maxdepth=2, leaf_density=1.25, sway_amp=0.017, droop=0.05))
    for name, w in (("far", 0.4), ("mid", 0.75), ("near", 1.0)):
        for br in layers[name]:
            br.wscale = w
    return layers


def window_mask():
    """static light patch of the classroom window (two panes + mullion), with soft penumbra."""
    m = np.zeros((H, W), np.float32)
    F = 16
    def poly(pts, v):
        cv2.fillPoly(m, [np.round(np.array(pts) * F).astype(np.int32)], v, cv2.LINE_AA, 4)
    poly([(34, 30), (1502, 10), (1468, 736), (-8, 750)], 1.0)       # left pane
    poly([(1562, 9), (2700, -6), (2700, 724), (1530, 736)], 1.0)    # right pane (jamb is off-frame)
    m = cv2.resize(m, (HW, HH), interpolation=cv2.INTER_AREA)
    m = cv2.filter2D(m, -1, sun_kernel(20 / S), borderType=cv2.BORDER_REPLICATE)
    return m


# ---------------------------------------------------------------- curtain
_XG = np.arange(HW, dtype=np.float32)[None, :] * S + S / 2      # full-res x of half-res pixel centres
_YG = np.arange(HH, dtype=np.float32) * S + S / 2
CURT_K = sun_kernel(26 / S)


def curtain_billow(t):
    """billow amount 0..1, follows the gust with a little cloth lag."""
    w = wind(t - 0.9, 0.0)
    return np.clip((w - 0.30) / 0.75, 0, 1) ** 1.2


def curtain(t):
    """sheer classroom curtain at the left jamb; its soft shadow sweeps in with the breeze."""
    b = curtain_billow(t)
    yy = _YG
    shape = np.clip((yy + 60) / (H + 60), 0, 1) ** 0.85            # pinned at the rail, free at the hem
    ripple = (18 + 22 * b) * np.sin(TAU * (yy / 330.0 - 3 * t / L)) * shape
    xe = 50 + 470 * b * shape + ripple + 10 * math.sin(TAU * 2 * t / L)
    d = xe[:, None] - _XG                                          # >0 inside the curtain
    cov = np.clip(d / 6.0 + 0.5, 0, 1)
    pleat = 0.38 + 0.13 * np.sin(TAU * d / 58.0 + 1.3 * np.sin(TAU * (yy[:, None] / 280.0 - 2 * t / L)))
    hem = 0.14 * np.exp(-np.maximum(d, 0) / 9.0)
    Tf = np.clip(pleat - hem, 0.25, 1)
    T = 1 - cov * (1 - Tf)
    return cv2.filter2D(T.astype(np.float32), -1, CURT_K, borderType=cv2.BORDER_REPLICATE)


KER = {"far": (sun_kernel(16 / S), 0.90), "mid": (sun_kernel(7.5 / S), 0.93), "near": (sun_kernel(3.5 / S), 0.95)}
SHAFT_K = None


def sun_map(layers, wm, t):
    T = np.ones((HH, HW), np.float32)
    for name, brs in layers.items():
        c = np.zeros((HH, HW), np.uint8)
        for br in brs:
            draw_branch(c, br, t, S)
        k, op = KER[name]
        cov = cv2.filter2D(c.astype(np.float32) / 255, -1, k, borderType=cv2.BORDER_REPLICATE)
        T *= (1 - op * cov)
    T *= curtain(t)
    return wm * T * sun_strength(t)


# ---------------------------------------------------------------- god rays
_RY, _RX = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32) * 4 + 2
_RS = -_RX * LDIR[1] + _RY * LDIR[0]       # across-beam coordinate (full-res px)
_RU = _RX * LDIR[0] + _RY * LDIR[1]        # along-beam coordinate
_rr = np.random.default_rng(5)
RAY_BUNDLES = [(-420, 190, 1.0), (-150, 120, 0.8), (60, 170, 0.95), (300, 110, 0.6), (520, 150, 0.5)]
RAY_STRIA = [(1 / _rr.uniform(14, 40), _rr.uniform(0.15, 0.35), _rr.uniform(0, TAU), int(_rr.integers(1, 4))) for _ in range(7)]
RAY_LEAF = [(_rr.uniform(-520, 640), _rr.uniform(18, 50), _rr.uniform(0.3, 0.7),
             [(k, _rr.uniform(12, 30) / k, _rr.uniform(0, TAU)) for k in (1, 2, 3)]) for _ in range(9)]


def god_rays(t):
    s = _RS
    A = np.zeros_like(s)
    for c, w, a in RAY_BUNDLES:
        A += a * np.exp(-((s - c) / w) ** 4)
    st = np.ones_like(s)
    for f, a, p, k in RAY_STRIA:
        st += a * np.sin(TAU * s * f / 4 * 4 / 4 + p + 0.6 * math.sin(TAU * k * t / L + p))
    A *= np.clip(st / (1 + sum(x[1] for x in RAY_STRIA) * 0.6), 0, None)
    for c, w, a, sw in RAY_LEAF:
        A *= 1 - a * wind(t, 300) * 0 - a * np.exp(-((s - c - periodic(t, sw) * (0.5 + wind(t, 300))) / w) ** 2)
    u = _RU
    fall = np.clip((u + 150) / 250, 0, 1) * np.exp(-np.maximum(u - 100, 0) / 900.0)
    A *= fall * (sun_strength(t) ** 1.5)
    A = cv2.GaussianBlur(A, (0, 0), 2.0)
    return cv2.resize(A, (W, H), interpolation=cv2.INTER_CUBIC)


# ---------------------------------------------------------------- dust
def build_dust(seed=11):
    rng = np.random.default_rng(seed)
    parts = []
    def add(n, sig, amp, zone):
        for _ in range(n):
            x0 = rng.uniform(*zone[0]); y0 = rng.uniform(*zone[1])
            d = dict(x0=x0, y0=y0, sig=rng.uniform(*sig), amp=rng.uniform(*amp))
            # lazy meander (k=1..3) + small brownian jitter (k=5..9), all integer harmonics of L
            d['mx'] = [(k, rng.uniform(15, 55) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
            d['my'] = [(k, rng.uniform(10, 40) / k, rng.uniform(0, TAU)) for k in (1, 2, 3)]
            d['jx'] = [(int(k), rng.uniform(1.5, 4), rng.uniform(0, TAU)) for k in rng.choice(range(5, 10), 2, replace=False)]
            d['jy'] = [(int(k), rng.uniform(1.5, 4), rng.uniform(0, TAU)) for k in rng.choice(range(5, 10), 2, replace=False)]
            d['tw'] = [(int(rng.integers(18, 70)), 1.0, rng.uniform(0, TAU))]
            parts.append(d)
    add(60, (1.4, 2.4), (0.10, 0.24), ((0, 1500), (10, 740)))     # motes over the painting (dark → they read)
    add(16, (1.2, 2.0), (0.06, 0.12), ((1560, 2520), (10, 740)))   # sparse over the paper
    add(16, (2.8, 4.0), (0.05, 0.09), ((0, 1800), (0, 768)))       # closer, softer
    add(5, (8, 12), (0.016, 0.026), ((0, 2560), (0, 768)))         # near, defocused
    return parts


def render_dust(parts, sunm, t, rays=None):
    acc = np.zeros((H, W), np.float32)
    for d in parts:
        x = d['x0'] + periodic(t, d['mx']) + periodic(t, d['jx'])
        y = d['y0'] + periodic(t, d['my']) + periodic(t, d['jy'])
        hx, hy = int(np.clip(x / S, 0, HW - 1)), int(np.clip(y / S, 0, HH - 1))
        lit = float(sunm[hy, hx])
        if rays is not None:
            lit = lit * 0.6 + 0.9 * float(rays[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))])
        if lit < 0.02:
            continue
        tw = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(TAU * d['tw'][0][0] * t / L + d['tw'][0][2])) ** 2
        a = d['amp'] * lit * tw * P['dust']
        sg = d['sig']
        R = int(math.ceil(sg * 3.5)) + 1
        xi, yi = int(math.floor(x)), int(math.floor(y))
        x0, x1 = max(xi - R, 0), min(xi + R + 1, W)
        y0, y1 = max(yi - R, 0), min(yi + R + 1, H)
        if x0 >= x1 or y0 >= y1:
            continue
        xs = np.arange(x0, x1) + 0.5 - x
        ys = np.arange(y0, y1) + 0.5 - y
        g = np.exp(-(ys[:, None] ** 2 + xs[None, :] ** 2) / (2 * sg * sg))
        acc[y0:y1, x0:x1] += a * g
    return acc


# ---------------------------------------------------------------- compose
DITHER = [True]


class Renderer:
    def __init__(self):
        base = np.asarray(Image.open(os.path.join(ROOT, 'base_2560.png')).convert('RGB')).astype(np.float32) / 255
        self.base_lin = srgb2lin(base)
        self.layers = build_scene()
        self.wm = window_mask()
        self.dust = build_dust()
        self.shk = line_kernel(int(240 / 4)) # quarter res
        rng = np.random.default_rng(3)
        self.dither = (rng.random((H, W, 3)).astype(np.float32) + rng.random((H, W, 3)).astype(np.float32) - 1.0) / 255.0
        # shaft spatial falloff: strongest near the window (upper-left), fading toward lower-right
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        proj = (xx / W) * 0.75 + (yy / H) * 0.45
        self.shaft_fall = np.clip(1.15 - proj, 0, 1) ** 1.6
        sc = np.array(P['sun_col'], np.float32); ac = np.array(P['amb_col'], np.float32)
        # normalise so a fully lit pixel = norm_lit, overall hue kept
        self.sun_rgb = sc * P['sun'] / (P['amb'] + P['sun']) * P['norm_lit']
        self.amb_rgb = ac * P['amb'] / (P['amb'] + P['sun']) * P['norm_lit']

    def frame(self, t, parts=False):
        sm = sun_map(self.layers, self.wm, t)                  # half res, 0..1
        sm_full = cv2.resize(sm, (W, H), interpolation=cv2.INTER_CUBIC)
        G = self.amb_rgb[None, None, :] + sm_full[..., None] * self.sun_rgb[None, None, :]
        out = self.base_lin * G
        # haze shafts
        sh = god_rays(t)
        out += (P['shaft'] * sh)[..., None] * np.array(P['sun_col'], np.float32)[None, None, :]
        dust = render_dust(self.dust, sm, t, sh)
        out += dust[..., None] * np.array((1.0, 0.93, 0.80), np.float32)[None, None, :]
        # soft shoulder (no hard clipping on white shirts / paper)
        knee = 0.82
        over = np.maximum(out - knee, 0)
        out = np.minimum(out, knee) + (1 - knee) * (1 - np.exp(-over / (1 - knee)))
        srgb = lin2srgb(out) + (self.dither if DITHER[0] else 0)
        img = np.clip(np.round(srgb * 255), 0, 255).astype(np.uint8)
        if parts:
            return img, sm, sh, dust
        return img


if __name__ == '__main__':
    r = Renderer()
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for t in [float(x) for x in sys.argv[2:]]:
        img, sm, sh, dust = r.frame(t, parts=True)
        Image.fromarray(img).save(f'{outdir}/still_t{t:05.2f}.png')
        Image.fromarray((np.clip(sm, 0, 1) * 255).astype(np.uint8)).save(f'{outdir}/sun_t{t:05.2f}.png')
