# 관저동 먹자웨이 야(夜)장축제 — LED 메인 KV 2560x768

Source: 261014관저동_먹자웨이_포스터.ai (PDF-compatible, not committed, 80 MB).
- strip.py: extracts the text-free scene raster Im0 (4392x6217, CMYK→RGB with ICC).
- vec.py: renders all vector art at 400 dpi with Im0 and the orange base rect removed (title, band, lit windows).
- compose1.py `<scene_y0> <out.png>`: full-width scene crop + vector lit windows, deep-green vignette, title stack (Daejeon no.1 / 관저동 / 먹자웨이 / 야(夜)장축제). v1 = y0 3450.
