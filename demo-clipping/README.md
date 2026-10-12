# Demo: opensource-clipping dijalankan dengan video contoh

Repo yang diuji: [NaufalRizqullah/opensource-clipping](https://github.com/NaufalRizqullah/opensource-clipping)
(versi 1.15.0, commit 2026-09-26).

## Hasil

| File | Isi |
|---|---|
| `sumber/video_sumber.mp4` | Video sumber 16:9, 63 detik (input) |
| `hasil/highlight_rank_1_ready.mp4` | Klip 1 — 9:16, 21,8 detik, "Kesalahan Fatal Clipper Pemula" |
| `hasil/highlight_rank_2_ready.mp4` | Klip 2 — 9:16, 25,2 detik, "3 Detik Penentu Video Viral" |
| `hasil/thumbnail_rank_*.jpg` | Thumbnail otomatis |
| `hasil/metadata_preview.json` | Judul, deskripsi, hashtag, caption TikTok |

Fitur repo yang terlihat bekerja di hasil:
- **Hook teaser**: klip dibuka dengan kalimat paling "menjual" (hook), lalu transisi glitch, lalu klip utama.
- **Face tracking + crop 9:16** (MediaPipe BlazeFace): wajah yang berada di kiri frame 16:9 otomatis jadi pusat frame vertikal.
- **Subtitle karaoke** per kata (kata yang sedang diucapkan berwarna kuning).
- **Thumbnail + metadata** siap upload.

## Batasan sandbox (penting dibaca)

Sandbox cloud tempat demo ini dibuat **memblokir YouTube, HuggingFace, dan jsDelivr**,
dan tidak ada API key Gemini. Karena itu:

| Langkah | Normalnya | Di demo ini |
|---|---|---|
| 1. Download | yt-dlp dari URL YouTube | video lokal disalin (`run_demo.py`) |
| 2. Transkrip | Faster-Whisper large-v3 | transkrip per kata dari timing TTS (`gen_sample.py`) |
| 3. Pilih momen viral | Gemini membaca transkrip | `gemini_response.json` ditulis manual, dimuat via opsi bawaan `--load-gemini-json` |
| 4–7. Hook, face tracking, subtitle, render, thumbnail | — | **kode asli repo, tanpa diubah** |

Video sumbernya buatan sendiri: suara TTS bahasa Indonesia (espeak-ng, terdengar robotik)
+ wajah ilustrasi (`draw_face.py`, bukan orang sungguhan), supaya bebas hak cipta.

## Cara menjalankan sendiri dengan benar (di PC atau Google Colab)

Di PC/Colab yang aksesnya normal, tidak perlu skrip pengganti di folder ini:

```bash
git clone https://github.com/NaufalRizqullah/opensource-clipping
cd opensource-clipping
pip install -r requirements.txt          # butuh ffmpeg terpasang
cp .env.sample .env                      # isi GOOGLE_API_KEY (gratis di aistudio.google.com/apikey)
python main.py --url "https://youtube.com/watch?v=VIDEO_ID" --clips 3 --ratio 9:16
```

- Tanpa GPU: tambahkan `--whisper-device cpu --whisper-compute-type int8`
  (pertimbangkan `--whisper-model small` agar lebih cepat).
- Colab (GPU T4 gratis) adalah cara yang direkomendasikan README repo-nya.
- Gunakan hanya video yang Anda punya izin untuk dipotong (lihat `../README.md`).

## Reproduksi demo ini

```bash
python draw_face.py wajah.png
python gen_sample.py sumber wajah.png            # butuh espeak-ng + ffmpeg
mkdir -p run/outputs && cp gemini_response.json run/outputs/
cd run && GOOGLE_API_KEY=dummy python ../run_demo.py <path-repo-opensource-clipping> \
  ../sumber/video_sumber.mp4 ../sumber/transkrip.json \
  --url https://example.com/sample --clips 2 --ratio 9:16 --load-gemini-json \
  --no-broll --no-bgm --whisper-device cpu --whisper-compute-type int8
```
