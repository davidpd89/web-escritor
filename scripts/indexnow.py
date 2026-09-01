#!/usr/bin/env python3
"""Derive and submit IndexNow notifications for public indexable routes.

The release contract is intentionally split in two phases:

1. ``derive`` compares two already-built public artifacts plus their content
   registries and writes only added/modified/deleted public indexable URLs.
2. ``submit`` runs after production has been verified at the exact release SHA.

A successful 200/202 response means RECEIVED/PENDING KEY VALIDATION, never
"indexed" or "ranked".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ORIGIN = "https://davidportodiaz.com"
HOST = "davidportodiaz.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
MAX_URLS = 10_000
GATED_STATUS = {"noindex", "internal", "gated", "deprecated"}
KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,128}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_routes(path: Path) -> dict[str, str]:
    data = load_json(path)
    defaults = data.get("defaults", {})
    routes: dict[str, str] = {}
    for entry in data.get("entries", []):
        status = entry.get("status", defaults.get("status", "public"))
        search_index = entry.get("searchIndex", defaults.get("searchIndex", True))
        url = entry.get("url")
        source = entry.get("sourceFile")
        if status in GATED_STATUS or not search_index or not url or not source:
            continue
        if not isinstance(url, str) or not isinstance(source, str):
            continue
        if "#" in url or not url.startswith("/"):
            continue
        routes[url] = source.replace("\\", "/")
    return routes


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_digest(dist: Path, source: str) -> str:
    path = dist / source
    if not path.is_file():
        raise FileNotFoundError(f"public registry source missing from artifact: {path}")
    return digest(path)


def derive_changed_urls(
    before_dist: Path,
    before_registry: Path,
    after_dist: Path,
    after_registry: Path,
) -> tuple[list[str], dict[str, int]]:
    before = registry_routes(before_registry)
    after = registry_routes(after_registry)
    changed: set[str] = set()
    counts = {"added": 0, "modified": 0, "deleted": 0}

    for route in sorted(set(before) | set(after)):
        if route not in before:
            artifact_digest(after_dist, after[route])
            changed.add(ORIGIN + route)
            counts["added"] += 1
            continue
        if route not in after:
            artifact_digest(before_dist, before[route])
            changed.add(ORIGIN + route)
            counts["deleted"] += 1
            continue
        if artifact_digest(before_dist, before[route]) != artifact_digest(after_dist, after[route]):
            changed.add(ORIGIN + route)
            counts["modified"] += 1

    urls = sorted(changed)
    if len(urls) > MAX_URLS:
        raise ValueError(f"refusing to emit {len(urls)} URLs; IndexNow maximum is {MAX_URLS}")
    return urls, counts


def validate_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST:
        raise ValueError(f"IndexNow URL must be HTTPS on {HOST}: {url}")
    if parts.fragment:
        raise ValueError(f"IndexNow URL must not contain fragments: {url}")


def load_url_file(path: Path) -> list[str]:
    data = load_json(path)
    urls = data.get("urls", [])
    if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
        raise ValueError("URL file must contain a JSON array field named 'urls'")
    urls = sorted(set(urls))
    if len(urls) > MAX_URLS:
        raise ValueError(f"too many URLs: {len(urls)} > {MAX_URLS}")
    for url in urls:
        validate_url(url)
    return urls


def read_key(path: Path) -> str:
    key = path.read_text(encoding="utf-8").strip()
    if not KEY_RE.fullmatch(key):
        raise ValueError("IndexNow key must be 8-128 letters, numbers, or hyphens")
    if path.name != f"{key}.txt":
        raise ValueError(f"root key filename must be {key}.txt, got {path.name}")
    return key


def payload_for(urls: list[str], key: str) -> dict:
    return {
        "host": HOST,
        "key": key,
        "keyLocation": f"{ORIGIN}/{key}.txt",
        "urlList": urls,
    }


def submit_payload(payload: dict, endpoint: str, retries: int, timeout: float) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "davidportodiaz.com-indexnow/1.0"},
        method="POST",
    )
    attempts = retries + 1
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
                continue
            raise RuntimeError(f"IndexNow network failure after {attempts} attempt(s): {exc}") from exc

        if status in {200, 202}:
            return status, text
        if status == 429 or 500 <= status <= 599:
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
                continue
        return status, text
    raise AssertionError("unreachable")


def cmd_derive(args: argparse.Namespace) -> int:
    urls, counts = derive_changed_urls(
        Path(args.before_dist),
        Path(args.before_registry),
        Path(args.after_dist),
        Path(args.after_registry),
    )
    output = {
        "schemaVersion": 1,
        "origin": ORIGIN,
        "counts": counts,
        "urls": urls,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"INDEXNOW DERIVE: {len(urls)} URL(s) — {counts}")
    for url in urls:
        print(f"- {url}")
    return 0


def cmd_empty(args: argparse.Namespace) -> int:
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"schemaVersion": 1, "origin": ORIGIN, "counts": {"added": 0, "modified": 0, "deleted": 0}, "urls": []},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("INDEXNOW DERIVE: workflow_dispatch/no comparable previous release — 0 URLs")
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    urls = load_url_file(Path(args.url_file))
    if not urls:
        print("INDEXNOW SUBMIT: no changed public indexable URLs; nothing to send")
        return 0
    key = read_key(Path(args.key_file))
    payload = payload_for(urls, key)
    if args.dry_run:
        safe = {**payload, "key": "<public-key-redacted-from-log>"}
        print(json.dumps(safe, ensure_ascii=False, indent=2))
        print("INDEXNOW SUBMIT: dry-run; no network request sent")
        return 0

    status, text = submit_payload(payload, args.endpoint, args.retries, args.timeout)
    if status == 200:
        print(f"INDEXNOW SUBMIT: RECEIVED ({status}) — {len(urls)} URL(s)")
        return 0
    if status == 202:
        print(f"INDEXNOW SUBMIT: RECEIVED_KEY_VALIDATION_PENDING ({status}) — {len(urls)} URL(s)")
        return 0
    print(f"INDEXNOW SUBMIT: FAILED HTTP {status}: {text[:500]}")
    return 1


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    derive = sub.add_parser("derive")
    derive.add_argument("--before-dist", required=True)
    derive.add_argument("--before-registry", required=True)
    derive.add_argument("--after-dist", required=True)
    derive.add_argument("--after-registry", required=True)
    derive.add_argument("--output", required=True)
    derive.set_defaults(func=cmd_derive)

    empty = sub.add_parser("empty")
    empty.add_argument("--output", required=True)
    empty.set_defaults(func=cmd_empty)

    submit = sub.add_parser("submit")
    submit.add_argument("--url-file", required=True)
    submit.add_argument("--key-file", required=True)
    submit.add_argument("--endpoint", default=ENDPOINT)
    submit.add_argument("--retries", type=int, default=2)
    submit.add_argument("--timeout", type=float, default=15.0)
    submit.add_argument("--dry-run", action="store_true")
    submit.set_defaults(func=cmd_submit)
    return ap


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
