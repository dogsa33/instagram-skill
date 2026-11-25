#!/usr/bin/env python3
"""Compose existing AI footage into a Korean-captioned Instagram Reel.

Uses existing Pillow + FFmpeg requirements; preserves generated audio and can
append an unchanged product photograph. Does not publish or generate new footage.

Examples:
  python scripts/compose_reel.py --clip raw.mp4 --out final.mp4
  python scripts/compose_reel.py --clip a.mp4 --clip b.mp4 --photo real-product.jpg \
      --captions captions_ko.json --font /path/to/NotoSansKR.ttf --out final.mp4

Caption JSON: {"captions": [{"start": 0, "end": 3.2, "text": "발효의 차이"}]}
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, FPS = 1080, 1920, 30


class ComposeError(RuntimeError):
    pass


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise ComposeError((result.stderr or result.stdout)[-2200:])


def _ffprobe(path, stream):
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream,
                             "-show_entries", "stream=codec_type,width,height",
                             "-of", "json", str(path)], capture_output=True, text=True)
    if result.returncode:
        raise ComposeError(f"Cannot inspect media: {path}")
    return json.loads(result.stdout or "{}").get("streams", [])


def _font_path(requested):
    candidates = [requested, os.environ.get("INSTAGRAM_KOREAN_FONT"),
                  r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                  "/System/Library/Fonts/AppleSDGothicNeo.ttc"]
    for path in candidates:
        if path and Path(path).is_file():
            return str(Path(path))
    raise ComposeError("Korean font not found. Specify --font /path/to/NotoSansKR.ttf or set INSTAGRAM_KOREAN_FONT")


def _wrap(text, draw, font, max_width=930):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            candidate = current + ch
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current.strip())
                current = ch
            else:
                current = candidate
        lines.append(current.strip())
    return lines


def _caption_png(text, output, font_name):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_name, 66)
    lines = _wrap(text, draw, font)
    if not lines or len(lines) > 4:
        raise ComposeError("Caption must fit within four lines; shorten the Korean copy")
    spacing, line_height = 20, 85
    h = len(lines) * line_height + (len(lines) - 1) * spacing
    # Use the central safe zone; keep away from bottom UI overlays.
    top = min(1120, 1210 - h)
    top = max(350, top)
    draw.rounded_rectangle([62, top - 23, WIDTH - 62, top + h + 18], radius=30,
                           fill=(0, 0, 0, 160))
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        w = bbox[2] - bbox[0]
        if w > 930:
            raise ComposeError("Caption is wider than safe region")
        draw.text(((WIDTH - w) / 2, top + i * (line_height + spacing)), line,
                  font=font, fill=(255, 255, 255, 255), stroke_width=2,
                  stroke_fill=(0, 0, 0, 220))
    canvas.save(output)


def _load_captions(path):
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("captions") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ComposeError("Captions JSON must be a list or a {'captions': [...]} object")
    verified = []
    for c in entries:
        a, b, text = float(c["start"]), float(c["end"]), str(c["text"]).strip()
        if a < 0 or b <= a or not text:
            raise ComposeError("Caption entries need start >= 0, end > start, and nonempty text")
        verified.append((a, b, text))
    return verified


def _normalize(src, dest, *, photo=False, photo_duration=2.0):
    src = Path(src)
    if not src.is_file():
        raise ComposeError(f"Input not found: {src}")
    if not photo and not _ffprobe(src, "v:0"):
        raise ComposeError(f"Video stream missing: {src}")
    has_audio = False if photo else bool(_ffprobe(src, "a:0"))
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if photo:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", str(photo_duration), "-i", str(src)]
    else:
        args += ["-i", str(src)]
    if not has_audio:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    args += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0"]
    # Fit entire image without distorting or blind crop, retaining the true product appearance.
    vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
          f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,fps={FPS},format=yuv420p")
    args += ["-vf", vf, "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "48000",
             "-ac", "2", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(dest)]
    _run(args)


def compose(args):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ComposeError("FFmpeg and FFprobe must be on PATH")
    if not args.clip:
        raise ComposeError("Provide at least one --clip")
    if args.photo_duration <= 0:
        raise ComposeError("--photo-duration must be positive")
    captions = _load_captions(args.captions)
    font = _font_path(args.font) if captions else None
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    inputs = [Path(x) for x in args.clip] + ([Path(args.photo)] if args.photo else [])
    if output.resolve() in [p.resolve() for p in inputs]:
        raise ComposeError("Output path must differ from input media")
    with tempfile.TemporaryDirectory(prefix="ig_reel_") as td:
        work = Path(td)
        norm = []
        for idx, clip in enumerate(args.clip):
            path = work / f"part_{idx:03d}.mp4"
            _normalize(clip, path)
            norm.append(path)
        if args.photo:
            path = work / f"part_{len(norm):03d}.mp4"
            _normalize(args.photo, path, photo=True, photo_duration=args.photo_duration)
            norm.append(path)
        # All segments have identical codecs, dimensions, FPS and audio layout.
        listing = work / "files.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in norm), encoding="utf-8")
        merged = work / "merged.mp4"
        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
              "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(merged)])
        if not captions:
            shutil.copy2(merged, output)
            print(f"Saved reel: {output}")
            return
        overlays = []
        for i, (start, end, caption) in enumerate(captions):
            path = work / f"caption_{i:03d}.png"
            _caption_png(caption, path, font)
            overlays.append((start, end, path))
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(merged)]
        for _, _, p in overlays:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-i", str(p)]
        chain = []
        prior = "[0:v]"
        for i, (start, end, _) in enumerate(overlays, 1):
            next_label = f"[c{i}]"
            chain.append(f"{prior}[{i}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})':eof_action=repeat{next_label}")
            prior = next_label
        cmd += ["-filter_complex", ";".join(chain), "-map", prior, "-map", "0:a:0",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(output)]
        _run(cmd)
    print(f"Saved Korean-captioned reel: {output}")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Compose AI clips and Korean subtitles into a Reel; never publishes")
    p.add_argument("--clip", action="append", required=True, help="Video clip; repeat to join in order")
    p.add_argument("--photo", help="Optional unchanged real product photo appended as final card")
    p.add_argument("--photo-duration", type=float, default=2.0)
    p.add_argument("--captions", help="UTF-8 timed captions JSON")
    p.add_argument("--font", help="Korean TTF/TTC/OTF font path; falls back to system Korean font")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


if __name__ == "__main__":
    try:
        compose(parse_args())
    except (ComposeError, FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
