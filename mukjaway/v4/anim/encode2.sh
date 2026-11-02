#!/bin/bash
# loop v2: render once into a lossless RGB master, then the delivery encode from it:
# explicit BT.709 limited-range conversion (accurate rounding, full chroma interpolation), x264 crf 3, closed GOP 60.
set -e
cd /root/mk
python3 anim/render2.py pipe 0 1200 | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s 2560x768 -r 60 -i - \
  -c:v libx264rgb -qp 0 -preset ultrafast vid/loop2_master_rgb.mkv
ffmpeg -y -loglevel error -i vid/loop2_master_rgb.mkv \
  -vf "scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p" \
  -c:v libx264 -preset slow -crf 3 -profile:v high -level:v 5.1 -g 60 -keyint_min 60 -sc_threshold 0 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -movflags +faststart vid/loop2_full.mp4
echo done
