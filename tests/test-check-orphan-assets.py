#!/usr/bin/env python3
"""Verifica scripts/check-orphan-assets.py contra un repo git de fixture
minimo: un asset referenciado (no debe listarse), uno huerfano (debe
listarse), y uno que solo aparece en CAMPAIGN_SOCIAL_ASSETS (debe listarse
por defecto, pero desaparecer con --exclude-campaign-assets).

No usa el repo real -- crea un repositorio git temporal aislado, porque el
propio checker depende de `git ls-files` para excluir lo gitignored.

Uso:
  python tests/test-check-orphan-assets.py
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("coa", ROOT / "scripts" / "check-orphan-assets.py")
coa = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = coa
_spec.loader.exec_module(coa)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def make_fixture_repo(tmp: Path) -> Path:
    (tmp / "assets").mkdir()
    (tmp / "scripts").mkdir()

    # Referenced asset: mentioned in an .html file that gets tracked by git.
    (tmp / "assets" / "used.png").write_bytes(b"\x89PNG fake used")
    (tmp / "index.html").write_text('<img src="/assets/used.png">', encoding="utf-8")

    # Orphan asset: exists on disk, referenced nowhere.
    (tmp / "assets" / "orphan.png").write_bytes(b"\x89PNG fake orphan")

    # Campaign-social asset: exists on disk, referenced nowhere, but is
    # listed in the fixture's own build-public-dist.py as intentional.
    (tmp / "assets" / "campaign.webp").write_bytes(b"RIFF fake campaign")
    (tmp / "scripts" / "build-public-dist.py").write_text(
        'CAMPAIGN_SOCIAL_ASSETS = ("assets/campaign.webp",)\n', encoding="utf-8"
    )

    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "fixture"],
        cwd=tmp, check=True,
    )
    return tmp


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = make_fixture_repo(Path(tmp_str))

        with mock.patch.object(coa, "ROOT", tmp):
            orphans_default = coa.find_orphans(tmp)
            names_default = {p.name for p, _ in orphans_default}
            check("orphan.png" in names_default, "orphan.png detectado por defecto")
            check("used.png" not in names_default, "used.png NO se marca como huerfano")
            check("campaign.webp" in names_default, "campaign.webp se marca por defecto (sin excluir)")

            orphans_excl = coa.find_orphans(tmp, exclude_campaign_assets=True)
            names_excl = {p.name for p, _ in orphans_excl}
            check("campaign.webp" not in names_excl, "campaign.webp desaparece con --exclude-campaign-assets")
            check("orphan.png" in names_excl, "orphan.png sigue detectado con --exclude-campaign-assets")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-orphan-assets: OK")


if __name__ == "__main__":
    run()
