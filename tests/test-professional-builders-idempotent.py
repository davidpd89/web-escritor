#!/usr/bin/env python3
"""Integration regression: professional-scope builders must be idempotent.

Each builder runs twice against the same temporary destination.  The complete
set of generated files and their bytes must be identical after the second run.
This is deliberately separate from source/output parity: a builder can match
committed output once and still be non-idempotent.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
TODAY = "2026-08-22"


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def run(label: str, command: list[str], output_root: Path) -> None:
    subprocess.run(command, cwd=ROOT, check=True)
    first = snapshot(output_root)
    assert first, f"{label}: first generation produced no files"
    subprocess.run(command, cwd=ROOT, check=True)
    second = snapshot(output_root)
    assert second == first, f"{label}: second generation drifted\nfirst={first}\nsecond={second}"
    print(f"ok {label}: {len(first)} output(s), second generation byte-identical")


with tempfile.TemporaryDirectory() as tmp_dir:
    tmp = Path(tmp_dir)

    tools_dir = tmp / "tools-hub"
    tools_dir.mkdir()
    run(
        "tools hub",
        [PYTHON, "scripts/build-tools-hub.py", "data/tools-hub.json", str(tools_dir / "index.html")],
        tools_dir,
    )

    writer_dir = tmp / "writer-tools"
    writer_dir.mkdir()
    run(
        "writer tools directory",
        [PYTHON, "scripts/build-writer-tools.py", "data/writer-tools.json", "--output", str(writer_dir / "index.html")],
        writer_dir,
    )

    editorial_dir = tmp / "editoriales-build"
    editorial_dir.mkdir()
    run(
        "editoriales",
        [
            PYTHON,
            "scripts/build-editoriales.py",
            "--data",
            "data/editoriales.json",
            "--output",
            str(editorial_dir),
            "--today",
            TODAY,
        ],
        editorial_dir,
    )

    radar_dir = tmp / "radar-build"
    radar_dir.mkdir()
    run(
        "convocatorias",
        [
            PYTHON,
            "scripts/build-radar-opportunities.py",
            "--data",
            "data/radar-opportunities.json",
            "--out",
            str(radar_dir),
            "--today",
            TODAY,
        ],
        radar_dir,
    )

print("test-professional-builders-idempotent: OK")
