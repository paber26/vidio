# Clipper mandiri (`klip.py`)

Mengubah video panjang 16:9 menjadi klip vertikal 9:16 siap upload **tanpa
layanan AI / aplikasi clipping pihak ketiga**. Yang dipakai hanya ffmpeg dan
library lokal (OpenCV, MediaPipe, Whisper) — semuanya berjalan di komputer sendiri.

Pemilihan momen (bagian yang di tool lain dikerjakan Gemini/GPT) dilakukan
dengan **membaca transkrip**, oleh Anda sendiri atau oleh Claude.

## Fitur
- Potong klip sesuai timestamp
- Crop 9:16 yang **mengikuti wajah** (MediaPipe BlazeFace; cadangan: Haar OpenCV), kamera bergerak halus
- **Hook** di awal klip + flash putih sebelum klip utama
- **Subtitle karaoke**: huruf besar, kata yang diucapkan berwarna kuning
- **Judul** di bagian atas selama klip utama
- Output 1080×1920, 30 fps, H.264 + AAC

## Instalasi
```bash
sudo apt install ffmpeg            # atau: brew install ffmpeg / winget install ffmpeg
pip install opencv-python numpy mediapipe faster-whisper
```
`mediapipe` dan `faster-whisper` opsional: tanpa mediapipe dipakai Haar OpenCV;
tanpa faster-whisper pakai file `.srt`.

## Alur kerja
```bash
# 1. Transkrip per kata
python klip.py transkrip podcast.mp4 -o kerja/                    # Whisper lokal (model 'small')
python klip.py transkrip podcast.mp4 -o kerja/ --srt podcast.srt  # atau dari subtitle .srt

# 2. Baca kerja/transkrip.txt, pilih momen terbaik, tulis clips.json

# 3. Render
python klip.py render podcast.mp4 kerja/transkrip.json clips.json -o hasil/
```

`clips.json`:
```json
[
  {"judul": "Kesalahan Fatal Clipper Pemula", "start": 10.93, "end": 32.48,
   "hook": {"start": 16.79, "end": 21.73}}
]
```
- `start`/`end`: bagian utama klip (detik). Ideal 20–60 detik.
- `hook` (opsional): kalimat paling "menjual" dari dalam klip, diputar di awal.

## Tips memilih momen
- Kalimat pembuka harus bisa dipahami **tanpa konteks** sebelumnya.
- Cari: pernyataan kontroversial/kontras, angka & fakta mengejutkan, cerita
  dengan punchline, tips praktis berurutan ("rahasia pertama…").
- Akhiri di kalimat yang tuntas, jangan terpotong di tengah ide.

## Sumber `.srt` tanpa Whisper
- YouTube Studio (video milik sendiri) → Subtitle → unduh `.srt`
- Ekspor caption otomatis dari CapCut
- Transkrip dari kreator yang memberi izin clipping

Timing kata dari `.srt` diperkirakan (dibagi rata per huruf), jadi highlight
karaoke sedikit kurang presisi dibanding Whisper.

## Contoh hasil
`contoh-hasil/` berisi 2 klip dari video contoh di `../demo-clipping/sumber/`
(suara TTS + wajah ilustrasi), dibuat dengan `--srt`.
