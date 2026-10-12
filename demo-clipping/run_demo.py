"""Jalankan main.py opensource-clipping di sandbox tanpa akses YouTube/HuggingFace.

Hanya dua hal yang diganti (sisa pipeline = kode asli repo):
  1. engine.download_video  -> menyalin video lokal (YouTube diblokir di sandbox)
  2. engine.WhisperModel    -> mengembalikan transkrip per-kata dari gen_sample.py
                               (model Whisper di HuggingFace diblokir di sandbox)
Langkah AI (Gemini) dilewati dengan opsi bawaan repo: --load-gemini-json.

Pemakaian: python run_demo.py <repo_dir> <video_lokal> <transkrip.json> [argumen main.py...]
"""
import json
import os
import shutil
import sys
from types import SimpleNamespace

repo_dir, src_video, transcript_path = sys.argv[1:4]
sys.argv = ["main.py"] + sys.argv[4:]
sys.path.insert(0, repo_dir)

from clipping import engine  # noqa: E402


def fake_download(url, output_path, *a, **kw):
    print(f"[1/3] (sandbox) Menyalin video lokal {src_video} -> {output_path}")
    shutil.copy(src_video, output_path)


class FakeWhisperModel:
    def __init__(self, *a, **kw):
        print("      (sandbox) Whisper diganti transkrip TTS dengan timing yang diketahui")

    def transcribe(self, path, **kw):
        with open(transcript_path, encoding="utf-8") as f:
            data = json.load(f)
        segs = [
            SimpleNamespace(
                start=s["start"], end=s["end"], text=s["text"],
                words=[SimpleNamespace(**w, probability=1.0) for w in s["words"]],
            )
            for s in data["segments"]
        ]
        return iter(segs), SimpleNamespace(duration=data["duration"], language="id")


engine.download_video = fake_download
engine.WhisperModel = FakeWhisperModel

import main  # noqa: E402

main.main()
