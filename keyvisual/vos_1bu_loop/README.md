# VOS 1부 키비주얼 루프 v01

Source: `2026_vos_영상용 3.psd` (5000x1500). Output: 2560x768, 60 fps, one exact 30 s cycle.

The PSD composite is never resampled or warped; only light moves on top of it:
classroom window light with a mullion shadow, leaf shadows at three depths (rigid jointed
twigs, sun-disk penumbra blur), a sheer curtain shadow that billows in on the gust, parallel
god rays over the chalkboard, sparse dust motes, and a thin cloud dimming the sun once.
All motion uses integer harmonics of the loop length, so frame 1800 == frame 0.

- `scene.py` — twig/leaf model, wind, sun kernels
- `render.py` — layout, light map, curtain, rays, dust, compositing (`python3 render.py outdir t1 t2 ...` for stills)
- `final2.py` — renders the lossless raw master
- `encode_qc.py` — H.264 encode + per-frame/seam QC against the master
- `x264_zones_used.txt` — final encode settings (one keyframe per loop, quality ramp before the seam)

Inputs expected next to `src/`: `base_2560.png` (PSD composite, Lanczos to 2560x768).

## v02 (2026-11-04)

재현: added light, trees and shadows looked wrong — keep the artwork as it is and keep only the dust.
`render_v02.py` leaves every original pixel bit-identical except where a dust mote passes (≈0.8 % of pixels per frame);
119 motes drift on closed periodic paths with a slow glint. `final_v02.py` renders the raw master; encode settings in `x264_settings_v02.txt`.

## v03 (2026-11-04)

재현: the dust was too round and should look like real dust; the background was too bright, so grade colour and levels, not just brightness.

- `grade.py` grades the merged PSD composite with levels, gamma, per-channel output levels, saturation, clarity and an elliptical vignette.
  - The painting is weighted by its layer alpha, so its edges don't halo against the paper.
  - Three presets: A 웜빈티지, B 웜빈티지딥 (used for v03), C 무드다크. Run `python3 grade.py ../grade` to write `grade/base_*.png`.
- `render_v03.py` adds 223 dust particles on the graded base, in linear light. Each particle is a fixed texture that only rotates, tumbles (foreshortens) and drifts. There are no gaussian dots and no defocus discs.
  - torn-edge flakes with a lit rim and a crease, which glint when face-on
  - lint tangles
  - tapered fibres with stray hairs
  - irregular specks, plus tiny far specks that move slower (parallax)
- `final_v03.py` renders the raw master. `encode_qc.py` encodes and checks it with the settings in `x264_settings_v03.txt`. `seam_qc.py` dumps decoded seam strips.

## v04 (2026-11-04)

재현 picked tone A. v04 uses the v03 dust unchanged (`render_v03.py`) on `grade/base_A_웜빈티지.png`, set via `VOS_BASE=.../base_A_웜빈티지.png python3 final_v03.py raw.rgb`. The encode is the same as v03.
