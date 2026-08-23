#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("vvta", ROOT / "scripts" / "validate-video-to-article.py")
vvta = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vvta
_spec.loader.exec_module(vvta)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def frontmatter(**overrides) -> str:
    base = {
        "video_candidate_id": "V-2026-001",
        "status": "draft",
        "platform": "youtube",
        "original_url": "https://www.youtube.com/watch?v=abc123xyz09",
        "published_at": "2026-08-20",
        "own_content": "true",
        "selection_basis": "first_hand",
        "search_console_query": "n/a",
        "search_console_impressions": "n/a",
        "search_console_clicks": "n/a",
        "search_console_extracted_at": "n/a",
        "existing_page": "n/a",
        "destination": "source_for_future",
        "first_hand_value": "Notas de proceso del propio autor.",
        "transcript_source": "Transcripción manual revisada.",
        "third_party_rights_review": "n/a",
        "published_url": "n/a",
    }
    base.update(overrides)
    lines = "\n".join(f"{k}: {v}" for k, v in base.items())
    body = "\n\n# Estructura propuesta\n\nResumen estructural listo para revisión.\n"
    return f"---\n{lines}\n---{body}"


def write(tmp: Path, text: str) -> Path:
    p = tmp / "video.md"
    p.write_text(text, encoding="utf-8")
    return p


print("tests/test-validate-video-to-article")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # 1) plantilla draft -> PASS
    errs = vvta.validate(ROOT / "scripts" / "templates" / "video-to-article.template.md")
    check(errs == [], "1. plantilla draft -> PASS", str(errs))

    # 2) review sin fuente original -> FAIL
    p = write(root, frontmatter(status="review", original_url=""))
    errs = vvta.validate(p)
    check(any("original_url" in e for e in errs), "2. review sin fuente original -> FAIL", str(errs))

    # 3) ready completo -> PASS
    p = write(
        root,
        frontmatter(
            status="ready",
            destination="cuaderno_article",
            selection_basis="first_hand,search_demand",
            search_console_query="portal fantasy",
            search_console_impressions="120",
            search_console_clicks="10",
            search_console_extracted_at="2026-08-21",
            existing_page="n/a",
            third_party_rights_review="clear",
        ).replace("Resumen estructural listo para revisión.", "Sección 1\n\nSección 2")
    )
    errs = vvta.validate(p)
    check(errs == [], "3. ready completo -> PASS", str(errs))

print("tests/test-validate-video-to-article: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
