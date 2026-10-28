# 대전 선수단 해단식 메인 화면 (3072x1728)

Source: `261023 대전해단식(인천 전국기능경기대회)메인-001완성.ai` (on 재현's PC, Documents\문창떡축제_LED\source).

Background loop (no text):
1. `python3 split2.py <ai> out` — splits artboard 1's content stream into base gradient + 234 ordered elements
   (136 gold glitter sprites, multiply vignette, gold lines, 92 pink bokeh / glow forms) and writes cumulative pages.
2. `python3 deltas.py out` — renders the cumulative pages; each element becomes a signed delta crop (sum == original exactly).
3. `python3 loop.py out bg.mp4 60` — 20 s seamless loop: small bokeh drift + breathe (overlapping ones move together,
   ones under a later big cluster stay put), glitter flashes in place, a light band sweeps the gold lines twice per loop.
   `python3 loop.py out chk 60 0,300` writes still frames instead.

`groups.py` lists the top-level groups; `iso.py`/`isodeltas.py` were a rejected test (isolated deltas lose the blend-mode stacking).

## v2 (every circle is its own object)
4. `python3 leaves.py <ai> out` + `python3 render_leaves.py out` — walks every nested form down to the leaf circles
   (368: glitter images + radial-gradient bokeh circles), renders each as an RGBA sprite on a 300 px margin canvas
   and records its blend chain (ColorDodge/Overlay/Screen/SoftLight + opacity).
5. `comp.py` re-composites the sprites with the PDF blend formulas (nested chains applied inner→outer); static
   result vs the original render: mean error 0.6/255.
6. `python3 loop2.py bg_v2.mp4` — each circle drifts on its own closed path (25–100 px), glitter twinkles,
   the 12 gold lines (`lines.json`, extended 500 px past the frame) swing their endpoints and carry a travelling glint.
