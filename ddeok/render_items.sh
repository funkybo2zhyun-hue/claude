set -e
cd /tmp/claude-0/-home-user-claude/7c8779c3-e9cb-59de-a28a-dab942444711/scratchpad/ddeok
G=/mnt/project-files/keyvisual/munchang_ddeok/ganji_v3; F=/mnt/project-files/keyvisual/munchang_ddeok/feed
declare -A NM=([01]=국민의례 [02]=내빈소개 [03]=개회사 [04]=축사 [05]=개막세레모니 [06]=기념촬영 [07]=축하공연)
for c in "$@"; do
  if [ "$c" = feed ]; then
    python3 render_loop9.py lf8.mp4 1200 LF7 > rf8.log 2>&1
    cp lf7check.png "$F/munchang_ddeok_중계폼_2304x768_v8.png"
    cp lf8.mp4 "$F/munchang_ddeok_중계폼_2304x768_v8_loop20s_60fps.mp4"
    ffmpeg -v error -y -i lf8.mp4 -vf scale=1152:384 -r 30 -c:v libx264 -crf 24 -preset fast -pix_fmt yuv420p -movflags +faststart "$F/munchang_ddeok_중계폼_2304x768_v8_폰미리보기.mp4"
  else
    n=${NM[$c]}
    cp ganji3_$c.png "$G/문창떡_식순간지_${c}_${n}_2304x768_v3.png"
    python3 render_loop9.py lg3_$c.mp4 1200 LG3/$c > rg3_$c.log 2>&1
    cp lg3_$c.mp4 "$G/문창떡_식순간지_${c}_${n}_2304x768_v3_loop20s_60fps.mp4"
    ffmpeg -v error -y -i lg3_$c.mp4 -vf scale=1152:384 -r 30 -c:v libx264 -crf 24 -preset fast -pix_fmt yuv420p -movflags +faststart "$G/문창떡_식순간지_${c}_${n}_v3_폰미리보기.mp4"
  fi
  echo done $c
done
