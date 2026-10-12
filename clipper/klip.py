#!/usr/bin/env python3
"""Clipper mandiri: video panjang 16:9 -> klip vertikal 9:16 siap upload.

Tanpa layanan AI pihak ketiga. Pemilihan momen dilakukan manusia/Claude dengan
membaca transkrip, lalu dituliskan ke file clips.json.

Alur:
  1. transkrip  : buat transkrip per kata (Whisper lokal, atau impor .srt)
  2. (baca transkrip.txt, tulis clips.json berisi momen terbaik)
  3. render     : potong, crop 9:16 mengikuti wajah, hook + flash, subtitle karaoke

Contoh:
  python klip.py transkrip video.mp4 -o kerja/                 # Whisper lokal
  python klip.py transkrip video.mp4 -o kerja/ --srt video.srt # tanpa Whisper
  python klip.py render video.mp4 kerja/transkrip.json clips.json -o hasil/

Format clips.json:
  [{"judul": "Kesalahan Fatal Clipper", "start": 10.9, "end": 26.7,
    "hook": {"start": 16.8, "end": 21.7}}]          # hook opsional
"""
import argparse
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np

OUT_W, OUT_H = 1080, 1920
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_NAME = "Montserrat Black"


# ---------------------------------------------------------------- transkrip
def _fmt(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def _words_from_text(text, start, end):
    """Bagi rentang waktu ke tiap kata, proporsional dengan panjang huruf."""
    toks = text.split()
    total = sum(len(x) + 1 for x in toks) or 1
    cur, out = start, []
    for tok in toks:
        d = (end - start) * (len(tok) + 1) / total
        out.append({"word": tok, "start": round(cur, 3), "end": round(cur + d, 3)})
        cur += d
    return out


def _parse_srt(path):
    ts = r"(\d+):(\d+):(\d+)[,.](\d+)"
    to_s = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    segs = []
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8-sig").read().strip())
    for b in blocks:
        m = re.search(ts + r"\s*-->\s*" + ts, b)
        if not m:
            continue
        start, end = to_s(*m.groups()[:4]), to_s(*m.groups()[4:])
        text = " ".join(l.strip() for l in b[m.end():].splitlines() if l.strip())
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            segs.append({"start": start, "end": end, "text": text,
                         "words": _words_from_text(text, start, end)})
    return segs


def _whisper(video, model, lang):
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device="auto", compute_type="int8")
    segments, _ = m.transcribe(video, language=lang, word_timestamps=True, vad_filter=True)
    out = []
    for s in segments:
        words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                 for w in (s.words or []) if w.word.strip()]
        out.append({"start": s.start, "end": s.end, "text": s.text.strip(), "words": words})
        print(f"[{_fmt(s.start)} - {_fmt(s.end)}] {s.text.strip()}", flush=True)
    return out


def cmd_transkrip(a):
    os.makedirs(a.output, exist_ok=True)
    segs = _parse_srt(a.srt) if a.srt else _whisper(a.video, a.model, a.lang)
    with open(os.path.join(a.output, "transkrip.json"), "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.output, "transkrip.txt"), "w", encoding="utf-8") as f:
        for s in segs:
            f.write(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}\n")
    print(f"OK: {len(segs)} segmen -> {a.output}/transkrip.txt")


# ------------------------------------------------------------- face tracking
MP_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_detector/"
                "blaze_face_full_range/float16/latest/blaze_face_full_range.tflite")
MP_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "blaze_face_full_range.tflite")


def _face_detector():
    """MediaPipe BlazeFace (lebih akurat, berjalan lokal) atau Haar OpenCV sebagai cadangan.

    Mengembalikan fungsi frame_bgr -> list[(x, w)] dalam piksel."""
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        if not os.path.exists(MP_MODEL):
            import urllib.request

            os.makedirs(os.path.dirname(MP_MODEL), exist_ok=True)
            urllib.request.urlretrieve(MP_MODEL_URL, MP_MODEL)
        det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=MP_MODEL), min_detection_confidence=0.5))

        def detect(frame):
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            return [(d.bounding_box.origin_x, d.bounding_box.width) for d in det.detect(img).detections]

        return detect
    except Exception as e:  # mediapipe tidak terpasang / model tidak bisa diunduh
        print(f"      (MediaPipe tidak tersedia: {e}; memakai Haar OpenCV)", flush=True)
        haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        def detect(frame):
            gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            return [(x, w) for x, _, w, _ in haar.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))]

        return detect


_DETECT = None


def track_faces(video, start, end, step=0.5):
    """Posisi-x tengah wajah (0..1) tiap `step` detik; None jika tak ada wajah."""
    global _DETECT
    _DETECT = _DETECT or _face_detector()
    cap = cv2.VideoCapture(video)
    xs, t = [], start
    while t <= end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        x = None
        if ok:
            small = cv2.resize(frame, None, fx=0.5, fy=0.5)
            faces = _DETECT(small)
            if faces:
                fx, fw = max(faces, key=lambda f: f[1])  # wajah terbesar
                x = (fx + fw / 2) / small.shape[1]
        xs.append(x)
        t += step
    cap.release()
    return xs


def smooth_path(xs, dead_zone=0.06):
    """Isi celah, haluskan, dan tahan kamera agar tidak goyang (dead zone)."""
    known = [x for x in xs if x is not None]
    if not known:
        return [0.5] * len(xs)
    filled, last = [], known[0]
    for x in xs:
        last = x if x is not None else last
        filled.append(last)
    k = 5
    padded = np.pad(np.array(filled), (k // 2, k // 2), mode="edge")
    med = [float(np.median(padded[i:i + k])) for i in range(len(filled))]
    out, cur = [], med[0]
    for x in med:
        if abs(x - cur) > dead_zone:
            cur = x
        out.append(cur)
    return out


# ------------------------------------------------------------------ subtitle
def _ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _clean(w):
    return w.replace("{", "(").replace("}", ")").upper()


def build_ass(words, offset, dur, judul=None, words_per_line=3):
    """Subtitle karaoke: kata yang sedang diucapkan berwarna kuning."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT_NAME},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,480,1
Style: Judul,{FONT_NAME},68,&H00000000,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if judul:
        lines.append(f"Dialogue: 1,{_ass_time(0)},{_ass_time(dur)},Judul,,0,0,0,,{_clean(judul)}")
    # kelompokkan kata: maks N kata, putus juga bila ada jeda > 0.6 detik
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= words_per_line or w["seg"] != cur[-1]["seg"]
                    or w["start"] - cur[-1]["end"] > 0.6):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    for g in groups:
        for i, w in enumerate(g):
            s = w["start"] - offset
            e = (g[i + 1]["start"] if i + 1 < len(g) else w["end"]) - offset
            if e <= 0 or s >= dur:
                continue
            text = " ".join(
                ("{\\c&H00E5FF&\\fscx110\\fscy110}" + _clean(x["word"]) + "{\\r}") if j == i
                else _clean(x["word"]) for j, x in enumerate(g))
            lines.append(f"Dialogue: 0,{_ass_time(s)},{_ass_time(min(e, dur))},Sub,,0,0,0,,{text}")
    return head + "\n".join(lines) + "\n"


# -------------------------------------------------------------------- render
def render_segment(video, start, end, words, out_path, judul=None):
    """Satu segmen: crop 9:16 mengikuti wajah + subtitle karaoke + audio."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    crop_w = min(W, int(round(H * 9 / 16)))
    crop_h = min(H, int(round(crop_w * 16 / 9)))

    step = 0.5
    path = smooth_path(track_faces(video, start, end, step))
    dur = end - start
    ass_path = out_path + ".ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(words, start, dur, judul))

    vf = f"subtitles='{ass_path}':fontsdir='{FONT_DIR}'"
    enc = subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OUT_W}x{OUT_H}", "-r", f"{fps}", "-i", "-",
        "-ss", f"{start}", "-t", f"{dur}", "-i", video,
        "-map", "0:v", "-map", "1:a?", "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-shortest", out_path,
    ], stdin=subprocess.PIPE)

    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    n_frames = int(round(dur * fps))
    x_prev = None
    for i in range(n_frames):
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        k = min(int(t / step), len(path) - 1)
        k2 = min(k + 1, len(path) - 1)
        frac = (t - k * step) / step
        cx = path[k] * (1 - frac) + path[k2] * frac
        target = cx * W - crop_w / 2
        # gerakan kamera halus (ease) menuju target
        x_prev = target if x_prev is None else x_prev + (target - x_prev) * 0.15
        x0 = int(np.clip(x_prev, 0, W - crop_w))
        y0 = (H - crop_h) // 2
        crop = frame[y0:y0 + crop_h, x0:x0 + crop_w]
        enc.stdin.write(cv2.resize(crop, (OUT_W, OUT_H), interpolation=cv2.INTER_LANCZOS4).tobytes())
    cap.release()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"ffmpeg gagal untuk {out_path}")
    os.remove(ass_path)


def flash(out_path, dur=0.25):
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"color=white:s={OUT_W}x{OUT_H}:r=30:d={dur}",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out_path,
    ], check=True)


def concat(parts, out_path):
    inputs = sum((["-i", p] for p in parts), [])
    streams = "".join(f"[{i}:v][{i}:a]" for i in range(len(parts)))
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", *inputs,
        "-filter_complex", f"{streams}concat=n={len(parts)}:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_path,
    ], check=True)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "klip"


def cmd_render(a):
    os.makedirs(a.output, exist_ok=True)
    segs = json.load(open(a.transkrip, encoding="utf-8"))
    words = [dict(w, seg=i) for i, s in enumerate(segs) for w in s["words"]]
    clips = json.load(open(a.clips, encoding="utf-8"))
    for n, c in enumerate(clips, 1):
        judul = c.get("judul", f"Klip {n}")
        name = f"{n:02d}-{_slug(judul)}"
        tmp = os.path.join(a.output, f".{name}")
        print(f"[{n}/{len(clips)}] {judul}  ({c['start']:.1f}s - {c['end']:.1f}s)", flush=True)
        parts = []
        hook = c.get("hook")
        if hook:
            render_segment(a.video, hook["start"], hook["end"], words, tmp + "-hook.mp4")
            flash(tmp + "-flash.mp4")
            parts += [tmp + "-hook.mp4", tmp + "-flash.mp4"]
        render_segment(a.video, c["start"], c["end"], words, tmp + "-main.mp4", judul=judul)
        parts.append(tmp + "-main.mp4")
        final = os.path.join(a.output, name + ".mp4")
        concat(parts, final)
        for p in parts:
            os.remove(p)
        print(f"      -> {final}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transkrip", help="buat transkrip per kata")
    t.add_argument("video")
    t.add_argument("-o", "--output", default="kerja")
    t.add_argument("--srt", help="pakai file .srt (tanpa Whisper)")
    t.add_argument("--model", default="small", help="model Whisper lokal (tiny/base/small/medium/large-v3)")
    t.add_argument("--lang", default="id")
    t.set_defaults(func=cmd_transkrip)
    r = sub.add_parser("render", help="render klip dari clips.json")
    r.add_argument("video")
    r.add_argument("transkrip")
    r.add_argument("clips")
    r.add_argument("-o", "--output", default="hasil")
    r.set_defaults(func=cmd_render)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    sys.exit(main())
