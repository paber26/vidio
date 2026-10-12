# Repo GitHub Open Source untuk Clipper

> Dicek 12 Oktober 2026: semua repo di bawah ada dan bisa di-clone. Tanggal
> "update terakhir" diambil dari commit terakhir di branch utama. Jumlah star
> tidak bisa diverifikasi dari sesi ini, jadi tidak dicantumkan.

Hampir semua tool ini memakai alur yang sama:
**Whisper** (transkrip) → **LLM** (memilih momen viral) → **ffmpeg** (potong) →
**face tracking** (ubah 16:9 ke 9:16) → **subtitle burn-in**.

## Ringkasan

| Repo | Jenis | Lisensi | Update terakhir | Cocok untuk |
|---|---|---|---|---|
| [NaufalRizqullah/opensource-clipping](https://github.com/NaufalRizqullah/opensource-clipping) | Python, Docker | MIT | 2026-09-26 | **Dibuat developer Indonesia, ada README bahasa Indonesia.** Hook teaser, subtitle karaoke, thumbnail otomatis, mode split-screen podcast |
| [FujiwaraChoki/supoclip](https://github.com/FujiwaraChoki/supoclip) | Web app, Docker Compose | AGPL-3.0 | 2026-10-11 | Alternatif OpusClip paling lengkap: skor viral, crop wajah 9:16. LLM bisa Gemini/GPT/Claude/**Ollama (lokal, gratis)** |
| [mutonby/openshorts](https://github.com/mutonby/openshorts) | Web app, Docker | MIT | 2026-10-09 | Podcast 2 orang: wajah ditumpuk atas–bawah, subtitle di tengah. Butuh RAM 8 GB+, API key Gemini |
| [zhouxiaoka/autoclip](https://github.com/zhouxiaoka/autoclip) | Aplikasi desktop + CLI + MCP | MIT | 2026-10-12 | Paling mudah: **ada installer desktop**, tempel link → video + cover + caption. Model AI cloud bayar per pemakaian |
| [SamurAIGPT/AI-Youtube-Shorts-Generator](https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator) | Python CLI | MIT | 2026-10-11 | Proses banyak video sekaligus (batch), output JSON. Butuh API key LLM |
| [nmbrthirteen/podcli](https://github.com/nmbrthirteen/podcli) | CLI + web studio + MCP | AGPL-3.0 | 2026-10-04 | Khusus podcast. Satu perintah `podcli process episode.mp4`, transkrip & render di komputer sendiri |
| [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) | Skill Claude Code | MIT | 2026-08-24 | Tanpa API cloud, cocok untuk talking-head. Dioptimalkan untuk macOS |
| [ClipsAI/clipsai](https://github.com/ClipsAI/clipsai) | Library Python | MIT | **2024-01-17 (tidak aktif)** | Bahan belajar/membangun tool sendiri. Sudah tidak di-update |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | CLI | Public domain | 2026-10-12 | **Bukan** pencari momen viral, tapi otomatis membuang bagian hening. Pelengkap yang berguna |

## Rekomendasi sesuai kondisi

- **Tidak mau ribet / tidak paham coding** → `autoclip` (versi desktop), atau
  versi hosted dari SupoClip/OpenShorts (ada paket gratis tapi terbatas).
- **Mau gratis penuh dan punya PC lumayan (GPU lebih baik)** → `supoclip` + Ollama,
  semuanya jalan lokal tanpa biaya API.
- **Konten berbahasa Indonesia** → mulai dari `opensource-clipping`
  (dokumentasi Indonesia; Faster-Whisper large-v3 mendukung bahasa Indonesia).
- **Fokus podcast 2 orang** → `openshorts` atau `podcli`.
- **Developer yang mau membangun pipeline sendiri** → pelajari
  `opensource-clipping` / `SamurAIGPT`, atau kembangkan `scripts/clip.sh` di repo ini.

## Hal yang perlu diperhatikan

1. **Lisensi AGPL-3.0** (SupoClip, podcli): bebas dipakai untuk diri sendiri.
   Kalau Anda memodifikasi lalu menjual atau menyediakannya sebagai layanan online,
   kode modifikasinya wajib dibuka. MIT tidak punya kewajiban ini.
2. **"Gratis" ≠ tanpa biaya**: banyak repo butuh API key (Gemini, OpenAI, dll.)
   yang dibayar per pemakaian, kecuali memakai model lokal (Ollama/Whisper lokal).
3. **Hardware**: Whisper large-v3 dan face tracking berat di CPU
   (OpenShorts: ±5–8 menit untuk video 8 menit di CPU).
4. **Fitur download dari link YouTube** (yt-dlp) secara teknis ada, tapi itu
   **tidak menyelesaikan masalah izin & hak cipta**. Pakai hanya untuk video yang
   Anda punya izinnya (lihat [README.md](README.md)).
5. **Hasil AI tetap perlu diedit manual.** Klip mentah hasil template yang
   diunggah massal adalah persis jenis konten yang tidak dimonetisasi oleh
   YouTube ("inauthentic content") dan Facebook ("unoriginal content").
6. Ini kode pihak ketiga: baca README/kode dan jalankan di lingkungan terpisah
   (Docker/virtualenv) sebelum memakainya. Hati-hati juga dengan repo tiruan
   yang menjanjikan "OpusClip Pro gratis" (bisa berisi malware).

## Sumber pencarian
- GitHub topics: [viral-clips](https://github.com/topics/viral-clips),
  [opus-clip](https://github.com/topics/opus-clip),
  [youtube-shorts](https://github.com/topics/youtube-shorts),
  [shorts-maker](https://github.com/topics/shorts-maker)
- https://openapps.pro/alternatives/opusclip
- https://www.opensourcealternatives.to/item/autoclip
- https://www.sourcepulse.org/projects/26291748
- https://mcpservers.org/id/servers/nmbrthirteen/podcli
