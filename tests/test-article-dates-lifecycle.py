#!/usr/bin/env python3
"""Regression tests for A.4 article freshness/review lifecycle."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_article_dates",
    ROOT / "scripts" / "check-article-dates.py",
)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def article_html(published: str, modified: str, *, visible_updated: bool | None = None) -> str:
    if visible_updated is None:
        visible_updated = modified != published
    updated = (
        f' · Actualizado el <time datetime="{modified}">{modified}</time>'
        if visible_updated
        else ""
    )
    return f'''<!doctype html>
<html><head>
<script type="application/ld+json">{{
  "@context":"https://schema.org",
  "@type":"Article",
  "headline":"Prueba",
  "datePublished":"{published}",
  "dateModified":"{modified}"
}}</script>
</head><body>
<header class="article-header">
<p>Publicado el <time datetime="{published}">{published}</time>{updated}</p>
</header>
</body></html>'''


def make_fixture(
    root: Path,
    *,
    published: str = "2026-01-10",
    modified: str = "2026-02-10",
    last_verified: str | None = None,
    review_by: str | None = None,
    visible_updated: bool | None = None,
) -> tuple[Path, Path]:
    rel = Path("cuaderno/prueba/index.html")
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        article_html(published, modified, visible_updated=visible_updated),
        encoding="utf-8",
    )
    entry = {
        "id": "article-test",
        "sourceFile": rel.as_posix(),
    }
    if last_verified is not None:
        entry["lastVerified"] = last_verified
    if review_by is not None:
        entry["reviewBy"] = review_by
    registry = root / "data/content-registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"entries": [entry]}), encoding="utf-8")
    return target, registry


print("tests/test-article-dates-lifecycle")
as_of = date(2026, 8, 29)

# 1. Existing date parity remains valid without lifecycle metadata.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root)
    errors, checked, lifecycle_count = mod.run_checks(root, registry, as_of)
    check(not errors, "existing article date contract still passes", str(errors))
    check(checked == 1 and lifecycle_count == 0, "no lifecycle is required by default")

# 2. Reverification may be newer than dateModified without fake freshness.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        modified="2026-02-10",
        last_verified="2026-08-20",
        review_by="2026-11-20",
    )
    errors, _, lifecycle_count = mod.run_checks(root, registry, as_of)
    check(not errors, "lastVerified may exceed dateModified without changing public freshness", str(errors))
    check(lifecycle_count == 1, "one scheduled review is counted")

# 3. Overdue reviewBy must fail deterministically.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        last_verified="2026-03-01",
        review_by="2026-08-28",
    )
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(any("overdue" in err for err in errors), "overdue reviewBy fails CI", str(errors))

# 4. A substantive modification after factual verification invalidates the verification.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        modified="2026-08-20",
        last_verified="2026-08-19",
        review_by="2026-11-19",
    )
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("lastVerified" in err and "predates dateModified" in err for err in errors),
        "modification after verification requires reverification",
        str(errors),
    )

# 5. Lifecycle fields are an all-or-nothing pair.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root, last_verified="2026-08-20")
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("must be declared together" in err for err in errors),
        "lastVerified/reviewBy pair is enforced",
        str(errors),
    )

# 6. Calendar validity is checked, not just the YYYY-MM-DD shape.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        last_verified="2026-02-30",
        review_by="2026-12-01",
    )
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("invalid calendar date" in err for err in errors),
        "impossible lifecycle date is rejected",
        str(errors),
    )

# 7. reviewBy cannot predate lastVerified.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        last_verified="2026-08-20",
        review_by="2026-08-19",
    )
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("reviewBy" in err and "predates" in err for err in errors),
        "reviewBy before lastVerified is rejected",
        str(errors),
    )

# 8. JSON-LD dateModified cannot predate datePublished.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        published="2026-06-01",
        modified="2026-05-01",
    )
    errors, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("dateModified" in err and "predates datePublished" in err for err in errors),
        "dateModified before datePublished is rejected",
        str(errors),
    )

print("tests/test-article-dates-lifecycle: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 1 if failures else 0)
