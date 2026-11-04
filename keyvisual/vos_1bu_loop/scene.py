"""VOS 1부 키비주얼 루프 — 창가 오후 햇살 + 나뭇잎 그림자 + 빛 속 먼지.

원본 PSD 합성본은 픽셀 그대로 고정. 움직이는 것은 빛(그림자 지도)과 먼지뿐.
모든 움직임은 L초 주기의 정수 배 고조파 → 프레임 N == 프레임 0 (진짜 순환 루프).
"""
import math
import numpy as np
import cv2

W, H = 2560, 768
S = 2                      # light map downscale (half res)
HW, HH = W // S, H // S
FPS = 60
L = 30.0
N = int(round(FPS * L))
TAU = 2 * math.pi

# light travels from upper-left to lower-right
LIGHT_ANG = math.radians(32.0)
LDIR = np.array([math.cos(LIGHT_ANG), math.sin(LIGHT_ANG)])


def srgb2lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin2srgb(x):
    x = np.maximum(x, 0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def periodic(t, terms):
    """sum of a*sin(2pi k t/L + p) — exactly periodic in L for integer k."""
    v = 0.0
    for k, a, p in terms:
        v += a * math.sin(TAU * k * t / L + p)
    return v


def bump(t, center, sharp):
    """smooth periodic bump in [0,1] peaking at `center` (seconds)."""
    return ((1 + math.cos(TAU * (t - center) / L)) / 2) ** sharp


def wind(t, x):
    """gust envelope. wind front travels left→right (delay by x)."""
    tt = t - (x / W) * 1.6
    g = 0.30 + 0.70 * bump(tt, 9.0, 3.0) + 0.35 * bump(tt, 24.5, 6.0)
    return g


def sun_strength(t):
    """a thin cloud passes once per cycle (soft dim, not a blackout)."""
    return 1.0 - 0.38 * bump(t, 19.0, 7.0)


# ---------------------------------------------------------------- leaves
def leaf_template(n=14):
    s = np.linspace(0, 1, n)
    hw = 0.5 * 0.46 * np.sin(np.pi * s ** 0.72) ** 0.85
    hw *= (1 - 0.25 * s)  # broader toward base (ovate)
    top = np.stack([s, hw], 1)
    bot = np.stack([s[::-1], -hw[::-1]], 1)
    return np.concatenate([top, bot[1:-1]], 0)


LEAF = leaf_template()


class Leaf:
    __slots__ = ("seg", "side_ang", "length", "pet", "fore", "b0", "fl_terms", "fo_terms")


class Twig:
    pass


def rand_terms(rng, ks, amp, n=3):
    ks = rng.choice(ks, size=n, replace=False)
    return [(int(k), amp * rng.uniform(0.5, 1.0) / (i + 1) ** 0.5, rng.uniform(0, TAU)) for i, k in enumerate(ks)]


def new_leaf(rng, leaf_len, side, taper):
    lf = Leaf()
    lf.side_ang = side * rng.uniform(0.45, 1.0)
    lf.length = leaf_len * rng.uniform(0.8, 1.2) * taper
    lf.pet = rng.uniform(0.10, 0.20)
    lf.fore = rng.uniform(0.78, 1.0)
    lf.b0 = rng.uniform(-0.75, 0.75)                               # 3D tilt → width foreshortening
    lf.fl_terms = rand_terms(rng, list(range(26, 64)), 0.13, 2)    # 0.9–2.1 Hz flutter about petiole
    lf.fo_terms = rand_terms(rng, list(range(20, 50)), 0.40, 2)    # tilt flutter (3D turn)
    return lf


def make_twig(rng, length, angle, depth, leaf_len, maxdepth, leaf_density, sway_amp, droop):
    """sympodial twig: a chain of rigid segments with joints; children & leaves at nodes."""
    tw = Twig()
    nseg = 6 if depth == 0 else 4
    tw.nseg = nseg
    tw.seg = length / nseg
    tw.angle = angle
    tw.depth = depth
    tw.bends = rng.normal(0, 0.10, nseg)
    tw.droop = droop
    tw.width = max(0.8, 3.4 * (0.6 ** depth))
    if depth == 0:
        tw.sway = rand_terms(rng, [1, 2, 3], sway_amp)
    else:
        tw.sway = rand_terms(rng, [2, 3, 4, 5, 6], sway_amp * (1.3 + 0.4 * depth))
    tw.joint = [rand_terms(rng, [3, 4, 5, 6, 7, 8], sway_amp * 0.5, 2) for _ in range(nseg)]
    tw.children = []
    if depth < maxdepth:
        for i in range(1, nseg):
            if rng.random() < (0.85 if depth == 0 else 0.6):
                side = 1 if (i + depth) % 2 == 0 else -1
                ch = make_twig(rng, length * rng.uniform(0.38, 0.62) * (1 - 0.12 * i), side * rng.uniform(0.45, 0.9),
                               depth + 1, leaf_len, maxdepth, leaf_density, sway_amp, droop)
                tw.children.append((i, ch))
    tw.leaves = []
    if depth >= maxdepth - 1:
        for i in range(1, nseg + 1):
            nl = int(leaf_density + rng.random())
            taper = 1 - 0.3 * i / nseg
            for j in range(nl):
                lf = new_leaf(rng, leaf_len, 1 if (i + j) % 2 == 0 else -1, taper)
                lf.seg = i - rng.uniform(0, 0.6)
                tw.leaves.append(lf)
        lf = new_leaf(rng, leaf_len, 0.15, 0.85)
        lf.seg = nseg
        lf.side_ang = rng.uniform(-0.15, 0.15)
        tw.leaves.append(lf)
    return tw


class Branch:
    """a bough entering the light from `base` (full-res px), drawn into one depth layer."""
    def __init__(self, rng, base, angle_deg, length, leaf_len, maxdepth=3, leaf_density=1.4, sway_amp=0.012,
                 droop=0.10, lines=True):
        self.base = np.array(base, float)
        self.lines = lines
        self.root = make_twig(rng, length, math.radians(angle_deg), 0, leaf_len, maxdepth, leaf_density, sway_amp, droop)


def _rot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def _toward_down(a, k):
    # smooth pull toward 'down' (+90deg); continuous everywhere (no wrap flip when pointing up)
    return a + k * math.cos(a)


WS = [1.0]


def branch_geometry(br, t):
    """returns (lines[(pts, width)], leaf polygons) in full-res px at time t. rigid joints only."""
    lines, polys = [], []

    def rec(tw, p0, ang0):
        g = wind(t, p0[0])
        a = ang0 + tw.angle + g * periodic(t, tw.sway)
        pts = [p0]
        angs = []
        p = p0
        for i in range(tw.nseg):
            a = a + tw.bends[i] + g * periodic(t, tw.joint[i])
            a = _toward_down(a, tw.droop)
            angs.append(a)
            p = p + np.array([math.cos(a), math.sin(a)]) * tw.seg
            pts.append(p)
        lines.append((np.array(pts), tw.width))
        for i, ch in tw.children:
            rec(ch, pts[i], angs[i - 1] if i - 1 < len(angs) else angs[-1])
        for lf in tw.leaves:
            si = int(math.ceil(lf.seg - 1e-9))
            fr = lf.seg - (si - 1)
            pc = pts[si - 1] + (pts[si] - pts[si - 1]) * fr
            ac = angs[si - 1]
            la = _toward_down(ac + lf.side_ang + g * periodic(t, lf.fl_terms), 0.22)
            tilt = lf.b0 + g * periodic(t, lf.fo_terms)
            wsc = max(0.12, abs(math.cos(tilt)))
            Pl = LEAF.copy()
            Pl[:, 0] = (Pl[:, 0] + lf.pet) * lf.length * lf.fore
            Pl[:, 1] = Pl[:, 1] * lf.length * wsc
            polys.append(Pl @ _rot(la).T + pc)
            q = np.array([pc, pc + np.array([math.cos(la), math.sin(la)]) * lf.pet * lf.length * lf.fore])
            lines.append((q, 0.8))

    rec(br.root, br.base, 0.0)
    return lines, polys


def draw_branch(canvas, br, t, scale):
    F = 16
    lines, polys = branch_geometry(br, t)
    if br.lines:
        ws = getattr(br, 'wscale', 1.0)
        for pts, w in lines:
            th = max(1, int(round(w * ws / scale)))
            cv2.polylines(canvas, [np.round(pts / scale * F).astype(np.int32)], False, 255, th, cv2.LINE_AA, 4)
    if polys:
        cv2.fillPoly(canvas, [np.round(p / scale * F).astype(np.int32) for p in polys], 255, cv2.LINE_AA, 4)


# ---------------------------------------------------------------- kernels
def sun_kernel(radius, elong=1.3, ang=LIGHT_ANG):
    """projected sun disk (ellipse along the light direction), anti-aliased, normalised."""
    r = max(radius, 0.6)
    ra, rb = r * elong, r
    R = int(math.ceil(ra)) + 1
    ss = 4
    ys, xs = np.mgrid[-R:R + 1:1 / ss, -R:R + 1:1 / ss]
    c, s = math.cos(ang), math.sin(ang)
    u = xs * c + ys * s
    v = -xs * s + ys * c
    inside = ((u / ra) ** 2 + (v / rb) ** 2 <= 1).astype(np.float32)
    n = 2 * R + 1
    k = cv2.resize(inside, (n, n), interpolation=cv2.INTER_AREA)
    return (k / k.sum()).astype(np.float32)


def line_kernel(length, ang=LIGHT_ANG, width=1.0):
    n = int(length) | 1
    k = np.zeros((n, n), np.float32)
    c = n // 2
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(-c * 4, c * 4 + 1):
        x = c + dx * i / 4
        y = c + dy * i / 4
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < n and 0 <= yi < n:
            # one-sided weight: shafts trail behind (upstream toward the window) the lit patch
            w = math.exp(-((i / 4) / (c * 0.55)) ** 2)
            k[yi, xi] += w
    k = cv2.GaussianBlur(k, (0, 0), width)
    return k / k.sum()
