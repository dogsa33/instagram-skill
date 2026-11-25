#!/usr/bin/env python3
"""Generate Kling 3.0 video through the official Higgsfield CLI.

Higgsfield is the only provider. Run `higgsfield auth login` once; no API key.
Never publishes to Instagram. --dry-run makes no network calls or charges.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

MODEL = "kling3_0"
FINISHED = {"completed", "succeeded", "success"}
FAILED = {"failed", "error", "canceled", "cancelled", "aborted"}


class ProviderError(RuntimeError):
    pass


def _cli_json(arguments):
    """Run the installed, already-authenticated official CLI without a shell."""
    cli = shutil.which("higgsfield")
    if not cli:
        raise ProviderError("Higgsfield CLI not found. Run: npm install -g @higgsfield/cli")
    result = subprocess.run([cli, *arguments, "--json"], capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise ProviderError((result.stderr or result.stdout or "Higgsfield CLI failed")[-1200:].strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Unexpected Higgsfield CLI JSON output: {str(exc)}") from exc


def _job_id(payload):
    """Without --wait, `higgsfield generate create --json` returns job IDs."""
    if isinstance(payload, list) and payload:
        return _job_id(payload[0])
    if isinstance(payload, str) and payload.strip():
        return payload.strip()
    if isinstance(payload, dict):
        value = payload.get("id") or payload.get("job_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ProviderError("Higgsfield did not return a job ID; check Assets before retrying to avoid duplicate charges")


def _job_data(payload):
    if isinstance(payload, list) and payload:
        return _job_data(payload[0])
    if isinstance(payload, dict):
        return payload
    raise ProviderError("Higgsfield job result is not a JSON object")


def _result_url(job):
    value = job.get("result_url")
    if isinstance(value, list) and value:
        value = value[0]
    if not isinstance(value, str):
        raise ProviderError("Completed job has no result_url")
    url = urlparse(value)
    if url.scheme != "https" or not url.netloc or url.username or url.password:
        raise ProviderError("Higgsfield returned an invalid result URL")
    return value


def _save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _download_video(url, output):
    url = _result_url({"result_url": url})
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(".part")
    total = 0
    try:
        with urllib.request.urlopen(url, timeout=120) as response, temp.open("wb") as stream:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > 300 * 1024 * 1024:
                    raise ProviderError("Video download exceeds 300 MB")
                stream.write(block)
        if not total:
            raise ProviderError("Downloaded video is empty")
        temp.replace(output)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return output


def _create_args(args, prompt):
    # The official Kling 3.0 CLI schema accepts ONE start image, not multiple references.
    if not 3 <= args.duration <= 15:
        raise ProviderError("Kling 3.0 duration must be 3–15 seconds")
    if len(args.image) > 1:
        raise ProviderError("Kling 3.0 accepts at most one reference image")
    for image in args.image:
        p = Path(image)
        if not p.is_file() or p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ProviderError(f"Image must exist and be JPG/PNG/WebP: {image}")
    # std is the default/low-complexity tier; Kling 3.0 uses mode, not resolution.
    command = ["generate", "create", MODEL, "--prompt", prompt,
               "--duration", str(args.duration), "--aspect_ratio", "9:16",
               "--mode", "std", "--sound", "off" if args.no_audio else "on"]
    if args.image:
        command += ["--start-image", str(args.image[0])]
    return command

def run(args):
    output = Path(args.out)
    job_file = Path(args.job_file) if args.job_file else output.with_suffix(".job.json")
    if args.resume:
        if not job_file.is_file():
            raise ProviderError(f"No saved job to resume: {job_file}")
        state = json.loads(job_file.read_text(encoding="utf-8"))
        job_id = state.get("id")
        if not job_id:
            raise ProviderError("Saved job does not contain an ID")
        if state.get("model") not in (None, MODEL):
            raise ProviderError("Saved job belongs to another model; use its original workflow")
        if args.dry_run:
            print(json.dumps({"dry_run": True, "resume_id": job_id}, ensure_ascii=False))
            return
    else:
        if job_file.exists():
            raise ProviderError(f"Existing job record: {job_file}. Use --resume or a new --out path.")
        prompt = args.prompt or (Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else "")
        if not prompt.strip():
            raise ProviderError("Provide --prompt or --prompt-file")
        command = _create_args(args, prompt)
        if args.dry_run:
            print(json.dumps({"dry_run": True, "provider": "Higgsfield CLI", "model": MODEL,
                              "command": ["higgsfield", *command, "--json"]}, ensure_ascii=False, indent=2))
            return
        # No --wait: persist the job ID before polling, to avoid duplicate paid jobs.
        job_id = _job_id(_cli_json(command))
        state = {"id": job_id, "model": MODEL, "provider": "Higgsfield", "status": "submitted"}
        _save(job_file, state)
        print(f"Submitted Higgsfield job {job_id}; saved {job_file}", flush=True)

    deadline = time.monotonic() + args.timeout_minutes * 60
    while True:
        job = _job_data(_cli_json(["generate", "get", str(job_id)]))
        status = str(job.get("status", "unknown")).lower()
        state["status"] = status
        _save(job_file, state)
        print(f"Higgsfield status: {status}", flush=True)
        if status in FINISHED:
            saved = _download_video(_result_url(job), output)
            state["result_path"] = str(saved)
            _save(job_file, state)
            print(f"Saved video: {saved}")
            return
        if status in FAILED:
            raise ProviderError(f"Higgsfield generation {status}: {str(job.get('error', ''))[:300]}")
        if time.monotonic() >= deadline:
            raise ProviderError(f"Job still running. Resume with --resume --out {output}")
        time.sleep(args.poll_seconds)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Kling 3.0 via Higgsfield CLI (single model, no API key)")
    prompt = parser.add_mutually_exclusive_group()
    prompt.add_argument("--prompt")
    prompt.add_argument("--prompt-file", help="UTF-8 prompt file")
    parser.add_argument("--image", action="append", default=[], help="Optional single JPG/PNG/WebP product photo")
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--out", required=True, help="Generated MP4 destination")
    parser.add_argument("--job-file", help="Job status JSON; defaults to <out>.job.json")
    parser.add_argument("--resume", action="store_true", help="Continue existing job without new charges")
    parser.add_argument("--poll-seconds", type=float, default=20)
    parser.add_argument("--timeout-minutes", type=float, default=30)
    parser.add_argument("--dry-run", action="store_true", help="Show CLI request, do not charge")
    args = parser.parse_args(argv)
    if args.poll_seconds <= 0 or args.timeout_minutes <= 0:
        parser.error("Polling and timeout must be positive")
    return args


if __name__ == "__main__":
    try:
        run(parse_args())
    except (ProviderError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
