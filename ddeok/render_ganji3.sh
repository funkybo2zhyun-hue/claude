set -e
cd /tmp/claude-0/-home-user-claude/7c8779c3-e9cb-59de-a28a-dab942444711/scratchpad/ddeok
for x in 01:국민의례 02:내빈소개 03:개회사 04:축사 05:개막세레모니 06:기념촬영 07:축하공연; do
  c=${x%%:*}; n=${x#*:}
  cp ganji3_$c.png "/mnt/project-files/keyvisual/munchang_ddeok/ganji_v3/문창떡_식순간지_${c}_${n}_2304x768_v3.png"
  python3 render_loop7.py lg3_$c.mp4 1200 LG3/$c > rg3_$c.log 2>&1
  cp lg3_$c.mp4 "/mnt/project-files/keyvisual/munchang_ddeok/ganji_v3/문창떡_식순간지_${c}_${n}_2304x768_v3_loop20s_60fps.mp4"
  ffmpeg -v error -y -i lg3_$c.mp4 -vf scale=1152:384 -r 30 -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -movflags +faststart "/mnt/project-files/keyvisual/munchang_ddeok/ganji_v3/문창떡_식순간지_${c}_${n}_v3_폰미리보기.mp4"
  echo done $c
done
