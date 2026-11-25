#!/usr/bin/env python3
"""Optional Replicate Seedance adapter for instagram-skill.

Requires only Python 3.9+ and REPLICATE_API_TOKEN for paid API calls.
Does not publish content. Dry run is safe and free.

Examples:
  python scripts/seedance_video.py --prompt '...' --image product.jpg --out reel/raw.mp4 --dry-run
  python scripts/seedance_video.py --prompt-file prompt.txt --image product.jpg --out reel/raw.mp4
  python scripts/seedance_video.py --resume --job-file reel/raw.job.json --out reel/raw.mp4
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlparse

API = "https://api.replicate.com/v1"
DEFAULT_MODEL = "bytedance/seedance-2.5"
TERMINAL = {"succeeded", "failed", "canceled", "aborted"}


class ProviderError(RuntimeError):
    pass


def _api_request(url, token, payload=None, headers=None, method=None):
    hdr = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    hdr.update(headers or {})
    body = payload
    if isinstance(payload, dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdr, method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        message = exc.read(2048).decode("utf-8", "replace")
        raise ProviderError(f"Replicate HTTP {exc.code}: {message}") from None
    except urllib.error.URLError as exc:
        raise ProviderError(f"Replicate connection error: {exc.reason}") from None


def _https_url(url):
    p = urlparse(str(url))
    if p.scheme != "https" or not p.netloc or p.username or p.password:
        raise ProviderError("Provider returned an invalid or non-HTTPS URL")
    return str(url)


def _upload_image(path, token):
    path = Path(path)
    if not path.is_file():
        raise ProviderError(f"Reference photo not found: {path}")
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ProviderError("Use JPG, PNG or WebP reference photos")
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ProviderError(f"Photo exceeds the 20 MB safety cap: {path}")
    boundary = uuid.uuid4().hex
    name = path.name.replace('"', "_")
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"content\"; "
            f"filename=\"{name}\"\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8")
    body = head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    result = _api_request(f"{API}/files", token, payload=body,
                          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    link = (result.get("urls") or {}).get("get") or result.get("url")
    if not link:
        raise ProviderError(f"Image upload response missing file URL: {list(result)}")
    return _https_url(link)


def _video_output_url(prediction):
    value = prediction.get("output")
    if isinstance(value, list):
        value = next((x for x in value if x), None)
    if isinstance(value, dict):
        value = value.get("url") or value.get("video")
    if not isinstance(value, str) or not value:
        raise ProviderError("Generation succeeded but no video URL was returned")
    return _https_url(value)


def _save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _download_video(url, output_path):
    url = _https_url(url)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    if tmp.exists():
        tmp.unlink()
    limit = 300 * 1024 * 1024
    count = 0
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "instagram-skill"}), timeout=120) as resp, tmp.open("wb") as f:
            while True:
                data = resp.read(1024 * 1024)
                if not data:
                    break
                count += len(data)
                if count > limit:
                    raise ProviderError("Video download exceeds the 300 MB safety cap")
                f.write(data)
        if count == 0:
            raise ProviderError("Downloaded video is empty")
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return path


def _model_name(model):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", model):
        raise ProviderError("Model must be in owner/name form")
    return model


def run(args):
    output = Path(args.out)
    job_file = Path(args.job_file) if args.job_file else output.with_suffix(".job.json")
    if args.resume:
        if not job_file.is_file():
            raise ProviderError(f"Cannot resume; missing job file: {job_file}")
        state = json.loads(job_file.read_text(encoding="utf-8"))
        if not state.get("id"):
            raise ProviderError("Job file does not contain a prediction ID")
        if args.dry_run:
            print(json.dumps({"dry_run": True, "resume_id": state["id"]}, ensure_ascii=False))
            return
    else:
        if job_file.exists():
            raise ProviderError(f"Existing job record: {job_file}. Use --resume to avoid duplicate paid generation, or explicitly remove the record.")
        prompt = args.prompt or (Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else "")
        if not prompt.strip():
            raise ProviderError("Provide --prompt or --prompt-file (UTF-8)")
        if len(args.image) > 4:
            raise ProviderError("This adapter supports up to four reference images")
        for p in args.image:
            if not Path(p).is_file():
                raise ProviderError(f"Reference photo not found: {p}")
        if args.duration < 3 or args.duration > 60:
            raise ProviderError("Duration must be between 3 and 60 seconds; provider/model may impose tighter limits")
        model = _model_name(args.model)
        spec = {"prompt": prompt, "duration": args.duration,
                "resolution": args.resolution, "aspect_ratio": "9:16",
                "generate_audio": not args.no_audio, "watermark": False}
        if args.dry_run:
            print(json.dumps({"dry_run": True, "model": model,
                              "input": {**spec, "reference_images": [str(x) for x in args.image]},
                              "note": "No network request or charge was made"}, ensure_ascii=False, indent=2))
            return
    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not token:
        raise ProviderError("REPLICATE_API_TOKEN is required for real generation. Do not commit it to Git.")
    if not args.resume:
        urls = [_upload_image(p, token) for p in args.image]
        if urls:
            spec["reference_images"] = urls
        prediction = _api_request(f"{API}/models/{model}/predictions", token, {"input": spec})
        if not prediction.get("id"):
            raise ProviderError("Replicate did not return a prediction ID")
        state = {"id": prediction["id"], "model": model, "status": prediction.get("status"),
                 "image_count": len(urls), "created_at": prediction.get("created_at")}
        _save_json(job_file, state)
        print(f"Prediction submitted: {state['id']}. State saved: {job_file}")
    else:
        prediction = None
    deadline = time.monotonic() + args.timeout_minutes * 60
    while True:
        prediction = _api_request(f"{API}/predictions/{state['id']}", token)
        status = prediction.get("status", "unknown")
        state["status"] = status
        _save_json(job_file, state)
        print(f"Seedance status: {status}", flush=True)
        if status == "succeeded":
            url = _video_output_url(prediction)
            final = _download_video(url, output)
            state["result_path"] = str(final)
            _save_json(job_file, state)
            print(f"Saved video: {final}")
            return
        if status in TERMINAL:
            raise ProviderError(f"Video generation ended with status={status}: {str(prediction.get('error') or '')[:500]}")
        if time.monotonic() >= deadline:
            raise ProviderError(f"Still running; saved job {state['id']}. Resume with --resume --job-file {job_file}")
        time.sleep(args.poll_seconds)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Generate a Seedance Reel via Replicate. Never posts automatically.")
    text = p.add_mutually_exclusive_group()
    text.add_argument("--prompt", help="Video prompt in Korean or English")
    text.add_argument("--prompt-file", help="UTF-8 prompt file")
    p.add_argument("--image", action="append", default=[], help="Reference photo (repeat up to four times)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Replicate model owner/name")
    p.add_argument("--duration", type=int, default=15)
    p.add_argument("--resolution", default="720p")
    p.add_argument("--no-audio", action="store_true")
    p.add_argument("--out", required=True, help="MP4 output path")
    p.add_argument("--job-file", help="Resume-safe state JSON (default: <out>.job.json)")
    p.add_argument("--resume", action="store_true", help="Resume an existing prediction without a new paid job")
    p.add_argument("--poll-seconds", type=float, default=20)
    p.add_argument("--timeout-minutes", type=float, default=30)
    p.add_argument("--dry-run", action="store_true", help="Print request without network, credentials or charges")
    a = p.parse_args(argv)
    if a.poll_seconds <= 0 or a.timeout_minutes <= 0:
        p.error("Polling and timeout must be positive")
    return a


if __name__ == "__main__":
    try:
        run(parse_args())
    except (ProviderError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
