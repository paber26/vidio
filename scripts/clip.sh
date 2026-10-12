#!/usr/bin/env bash
# Potong video lokal lalu ubah ke format vertikal 9:16 (1080x1920) untuk
# Shorts / Reels / TikTok. Video asli ditaruh di tengah, latar belakang
# memakai versi blur dari video yang sama.
#
# Pemakaian:
#   clip.sh <input> <mulai HH:MM:SS> <durasi detik> <output.mp4> [subtitle.srt]
#
# Gunakan hanya untuk konten yang Anda miliki atau sudah diizinkan pemiliknya.
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Pemakaian: $0 <input> <mulai HH:MM:SS> <durasi detik> <output.mp4> [subtitle.srt]" >&2
  exit 1
fi

input=$1
start=$2
duration=$3
output=$4
subs=${5:-}

command -v ffmpeg >/dev/null || { echo "ffmpeg belum terpasang" >&2; exit 1; }

filter="[0:v]split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];\
[fg]scale=1080:-2[fg];\
[bg][fg]overlay=(W-w)/2:(H-h)/2"

if [ -n "$subs" ]; then
  # Subtitle besar di sepertiga bawah layar.
  # Timestamp .srt harus relatif terhadap awal klip (mulai dari 00:00:00).
  filter="$filter,subtitles='${subs}':force_style='FontSize=14,Bold=1,Outline=2,MarginV=60'"
fi
filter="$filter[v]"

ffmpeg -hide_banner -y -ss "$start" -t "$duration" -i "$input" \
  -filter_complex "$filter" -map "[v]" -map 0:a? \
  -c:v libx264 -preset medium -crf 20 -r 30 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart \
  "$output"

echo "Selesai: $output"
