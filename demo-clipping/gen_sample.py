"""Buat video contoh 16:9 berbicara (TTS Indonesia + foto wajah) dan transkrip
per-kata dengan timing yang diketahui (pengganti Whisper di sandbox)."""
import json
import os
import subprocess
import sys
import wave

out_dir = os.path.abspath(sys.argv[1])
face_img = sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

SENTENCES = [
    "Halo semuanya, selamat datang kembali di podcast kita hari ini.",
    "Kali ini kita akan membahas cara menghasilkan uang sebagai clipper.",
    "Banyak orang mengira clipper cukup memotong video orang lain lalu mengunggahnya.",
    "Padahal itu justru cara tercepat untuk kena copyright strike.",
    "Rahasia pertama adalah meminta izin kepada kreator aslinya.",
    "Banyak podcaster justru senang kalau kontennya dipotong dan disebarkan.",
    "Rahasia kedua adalah hook di tiga detik pertama.",
    "Kalau tiga detik pertama membosankan, penonton langsung menggeser layar.",
    "Rahasia ketiga adalah subtitle yang besar dan jelas.",
    "Kebanyakan orang menonton video pendek tanpa suara.",
    "Terakhir, jangan lupa tambahkan sudut pandang atau komentar kamu sendiri.",
    "Itulah yang membuat klip kamu lolos monetisasi YouTube dan Facebook.",
]
GAP = 0.35  # jeda antar kalimat (detik)

words, segments, wavs, t = [], [], [], 0.0
for i, s in enumerate(SENTENCES):
    w = os.path.join(out_dir, f"s{i:02d}.wav")
    subprocess.run(["espeak-ng", "-v", "id", "-s", "150", "-w", w, s], check=True)
    with wave.open(w) as f:
        dur = f.getnframes() / f.getframerate()
    # espeak menambah sedikit hening di awal/akhir; bagi durasi efektif per
    # kata secara proporsional dengan panjang hurufnya.
    toks = s.split()
    lead, tail = 0.08, 0.15
    eff = max(dur - lead - tail, 0.1)
    total_chars = sum(len(x) + 1 for x in toks)
    cur = t + lead
    seg_words = []
    for tok in toks:
        d = eff * (len(tok) + 1) / total_chars
        seg_words.append({"word": " " + tok, "start": round(cur, 3), "end": round(cur + d, 3)})
        cur += d
    segments.append({"start": round(t, 3), "end": round(t + dur, 3), "text": " " + s, "words": seg_words})
    wavs.append(w)
    t += dur + GAP

# gabungkan audio dengan jeda
concat = os.path.join(out_dir, "concat.txt")
silence = os.path.join(out_dir, "gap.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                "-t", str(GAP), silence], check=True)
with open(concat, "w") as f:
    for w in wavs:
        f.write(f"file '{w}'\nfile '{silence}'\n")
audio = os.path.join(out_dir, "audio.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat,
                "-c", "copy", audio], check=True)

# video 1920x1080: foto wajah di sisi kiri-tengah (bukan tepat di tengah, supaya
# terlihat apakah face-tracking menggeser crop 9:16 ke arah wajah), zoom pelan.
video = os.path.join(out_dir, "video_sumber.mp4")
total = t
vf = (
    "color=c=0x1b2a3a:s=1920x1080:r=30[bg];"
    "[0:v]scale=-2:900,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=700x900:fps=30[fg];"
    "[bg][fg]overlay=x=380:y=90:shortest=1,"
    "drawtext=text='PODCAST CLIPPER':x=1300:y=480:fontsize=64:fontcolor=white"
)
subprocess.run([
    "ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", face_img, "-i", audio,
    "-filter_complex", vf, "-t", f"{total:.2f}",
    "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k", "-shortest", video,
], check=True)

with open(os.path.join(out_dir, "transkrip.json"), "w", encoding="utf-8") as f:
    json.dump({"duration": total, "segments": segments}, f, ensure_ascii=False, indent=1)
print(f"OK {video} ({total:.1f}s), {len(segments)} kalimat")
for sg in segments:
    print(f"[{sg['start']:6.2f} - {sg['end']:6.2f}]{sg['text']}")
