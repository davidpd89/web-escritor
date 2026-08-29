#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "indexnow.py"
spec = importlib.util.spec_from_file_location("indexnow", SCRIPT)
indexnow = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(indexnow)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def registry(entries: list[dict]) -> dict:
    return {
        "defaults": {"status": "public", "searchIndex": True},
        "entries": entries,
    }


def route(url: str, source: str, **extra) -> dict:
    return {"url": url, "sourceFile": source, **extra}


def write_artifact(root: Path, source: str, body: str) -> None:
    path = root / source
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        before_dist = t / "before-dist"
        after_dist = t / "after-dist"
        before_dist.mkdir()
        after_dist.mkdir()
        before_registry = t / "before.json"
        after_registry = t / "after.json"

        before_entries = [
            route("/", "index.html"),
            route("/changed/", "changed/index.html"),
            route("/deleted/", "deleted/index.html"),
            route("/noindex/", "noindex/index.html", searchIndex=False),
            route("/fragment/#x", "fragment/index.html"),
        ]
        after_entries = [
            route("/", "index.html"),
            route("/changed/", "changed/index.html"),
            route("/added/", "added/index.html"),
            route("/noindex/", "noindex/index.html", searchIndex=False),
        ]
        write_json(before_registry, registry(before_entries))
        write_json(after_registry, registry(after_entries))

        write_artifact(before_dist, "index.html", "same")
        write_artifact(after_dist, "index.html", "same")
        write_artifact(before_dist, "changed/index.html", "old")
        write_artifact(after_dist, "changed/index.html", "new")
        write_artifact(before_dist, "deleted/index.html", "gone")
        write_artifact(after_dist, "added/index.html", "new page")
        write_artifact(before_dist, "noindex/index.html", "private")
        write_artifact(after_dist, "noindex/index.html", "private changed")
        write_artifact(before_dist, "fragment/index.html", "fragment")

        urls, counts = indexnow.derive_changed_urls(before_dist, before_registry, after_dist, after_registry)
        check(
            urls
            == [
                "https://davidportodiaz.com/added/",
                "https://davidportodiaz.com/changed/",
                "https://davidportodiaz.com/deleted/",
            ],
            f"unexpected changed URL set: {urls}",
        )
        check(counts == {"added": 1, "modified": 1, "deleted": 1}, f"unexpected counts: {counts}")

        key = "20c025c30536df9ee9bfa38406e7dd72"
        key_file = t / f"{key}.txt"
        key_file.write_text(key + "\n", encoding="utf-8")
        check(indexnow.read_key(key_file) == key, "valid public key rejected")
        payload = indexnow.payload_for(urls, key)
        check(payload["host"] == "davidportodiaz.com", "payload host drift")
        check(payload["keyLocation"] == f"https://davidportodiaz.com/{key}.txt", "keyLocation drift")
        check(payload["urlList"] == urls, "payload URL list drift")

        for bad in (
            "http://davidportodiaz.com/changed/",
            "https://example.com/changed/",
            "https://davidportodiaz.com/changed/#frag",
        ):
            try:
                indexnow.validate_url(bad)
                failures.append(f"invalid URL accepted: {bad}")
            except ValueError:
                pass

        wrong_name = t / "wrong.txt"
        wrong_name.write_text(key, encoding="utf-8")
        try:
            indexnow.read_key(wrong_name)
            failures.append("key file with wrong filename accepted")
        except ValueError:
            pass

        too_short = t / "short.txt"
        too_short.write_text("abc", encoding="utf-8")
        try:
            indexnow.read_key(too_short)
            failures.append("short key accepted")
        except ValueError:
            pass

    if failures:
        print(f"INDEXNOW TESTS: FAILED ({len(failures)})")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("INDEXNOW TESTS: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
