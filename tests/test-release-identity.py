#!/usr/bin/env python3
"""Regression tests for the generated release identity marker."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "stamp-release-identity.py"
spec = importlib.util.spec_from_file_location("release_identity", SCRIPT)
assert spec and spec.loader
release_identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_identity)


def main() -> None:
    sha = "0123456789abcdef0123456789abcdef01234567"
    other_sha = "89abcdef0123456789abcdef0123456789abcdef"

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "dist"
        out.mkdir()

        path = release_identity.stamp(out, sha)
        assert path == out / "_release" / f"{sha}.json"
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload == {"schemaVersion": 1, "sha": sha}
        assert release_identity.verify(out, sha) == path

        # An old/different release cannot satisfy the marker for another SHA.
        try:
            release_identity.verify(out, other_sha)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("different SHA unexpectedly verified against existing marker")

        for invalid in ("", "abc", "g" * 40, "a" * 39, "a" * 41, "../" + "a" * 40):
            try:
                release_identity.validate_sha(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid SHA accepted: {invalid!r}")

    print("OK: exact per-SHA release identity contract passed.")


if __name__ == "__main__":
    main()
