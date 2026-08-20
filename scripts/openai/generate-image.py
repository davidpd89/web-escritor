#!/usr/bin/env python3
"""Generate an image with the OpenAI Images API (default model: gpt-image-2,
overridable with --model).

This script reads OPENAI_API_KEY from the environment ONLY. It never
accepts a key via CLI argument, never prints it, never writes it to any
output file/log, and never embeds it in the saved image or a JSON sidecar.

Environment loading: if OPENAI_API_KEY is not already set in the process
environment, this script will look for a local, git-ignored `.env.local`
file at the repo root (one KEY=VALUE per line, '#' comments allowed) and
read the key from there. `.env.local` is covered by `.env.*` in
.gitignore — verified before this script was written. No third-party
dependency (e.g. python-dotenv) is required, to keep this stdlib-only
like every other script in scripts/.

Usage:
  # Dry run (default): prints what WOULD be requested, makes no network
  # call, spends no money. Always do this first for a new prompt.
  python scripts/openai/generate-image.py --prompt "..." --out assets/x.png

  # Real generation (spends money). Only after reviewing the dry run.
  python scripts/openai/generate-image.py --prompt "..." --out assets/x.png --live

  # Optional size/quality (supported sizes: 1024x1024, 1024x1536,
  # 1536x1024, auto; quality: low, medium, high, auto).
  python scripts/openai/generate-image.py --prompt "..." --out assets/x.png \
      --size 1536x1024 --quality medium --live

  # Older model, if gpt-image-2 isn't available on this account/API version:
  python scripts/openai/generate-image.py --prompt "..." --out assets/x.png \
      --model gpt-image-1 --live

Cost control: this script makes exactly ONE API request per invocation
(n=1, hardcoded). There is no batch/loop mode. Run it once per variant
you actually want, not in a loop "to see what comes out" — every --live
call costs real money.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_URL = "https://api.openai.com/v1/images/generations"


def load_env_local() -> None:
    """Populate os.environ from .env.local if OPENAI_API_KEY isn't already set.

    Never prints, logs, or returns the key value. Silently does nothing if
    the file is absent or the key is already set some other way.
    """
    if os.environ.get("OPENAI_API_KEY"):
        return
    env_path = REPO_ROOT / ".env.local"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", required=True)
    p.add_argument("--out", required=True, help="Output image path (.png or .webp)")
    p.add_argument("--size", default="1024x1024", choices=["1024x1024", "1024x1536", "1536x1024", "auto"])
    p.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"])
    p.add_argument(
        "--model",
        default="gpt-image-2",
        help="OpenAI image model (default: gpt-image-2, current per OpenAI's docs as of this "
        "session; pass e.g. --model gpt-image-1 for the older model if needed).",
    )
    p.add_argument("--live", action="store_true", help="Perform a real, billed API call")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    load_env_local()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY not configured in environment or .env.local. Aborting.")
        return 1

    print("Prompt:", args.prompt)
    print("Output:", args.out)
    print("Model:", args.model)
    print("Size:", args.size, "| Quality:", args.quality)

    if not args.live:
        print("\nDry run complete (no API call made, no cost). Re-run with --live to actually generate and pay for this image.")
        return 0

    print("\nLive generation requested — this is a BILLED API call.")

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": 1,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            resp_body = resp.read()
    except urllib.error.HTTPError as e:
        # Deliberately do not include request headers (which would contain
        # the Authorization bearer token) in any error output.
        err_text = e.read().decode("utf-8", errors="replace")
        print(f"API error: HTTP {e.code}", file=sys.stderr)
        print(err_text, file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Network error contacting OpenAI: {e.reason}", file=sys.stderr)
        return 1

    data = json.loads(resp_body)
    items = data.get("data") or []
    if not items or "b64_json" not in items[0]:
        print("Unexpected API response shape (no b64_json data).", file=sys.stderr)
        return 1

    import base64

    image_bytes = base64.b64decode(items[0]["b64_json"])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    print(f"\nSaved {len(image_bytes)} bytes to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
