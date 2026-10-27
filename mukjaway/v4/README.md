# 관저동 먹자웨이 야(夜)장축제 — LED KV v4 (2560x768)

Re-staging of the poster .ai's own elements (no enlargement, no new art). Inputs live in project files
`keyvisual/gwanjeo_mukjaway/src/` (bg_rgb.png = text-free scene raster, vec_400.png = vector art, cut/ = cutouts)
and are expected under /root/mk/src and /root/mk/cut; LaMa weights `big-lama.pt` (Sanster/models release) in /root/mk/src.

- `stage1.py` — scene plate: poster market at s=0.38 split around the centre logo. Left copy (src x 0-2900) keeps the
  busker; right copy (src x 1836-4392) has the busker, his stands and the front diner's shoulder inpainted on a wide
  context window (two LaMa passes). The strip behind the logo is filled with mirrored neighbours and its seams inpainted.
- `stage2.py <plate> <out> [json]` — vector lit windows (mirrored into the hidden strip), poster moon and sparkle star,
  OPEN and 먹거리/체험부스 badges in the top corners, centred title stack (600 px tall) with shallow depth and a tight shadow.
  v4 params: `{"fb_xy":[2150,70],"fb_h":215,"fb_r":4,"ob_xy":[55,70],"ob_r":-4}`.
- `common.py`, `lama.py` — helpers (vector crops by pt bbox, LaMa inference on CPU torch).
