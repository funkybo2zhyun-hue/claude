#!/bin/bash
# full 20 s loop: frames piped from the renderer into x264 (closed GOP every second so the loop restarts cleanly)
set -e
cd /root/mk
python3 anim/render.py pipe 0 1200 | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s 2560x768 -r 60 -i - \
  -c:v libx264 -preset slow -crf 14 -tune animation -g 60 -keyint_min 60 -sc_threshold 0 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart vid/loop_full.mp4
echo done
