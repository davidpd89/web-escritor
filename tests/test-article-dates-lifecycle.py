#!/usr/bin/env python3
"""Regression tests for A.4 public dates and editorial review lifecycle."""

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


def article_html(
    published: str,
    modified: str,
    *,
    visible_updated: bool | None = None,
    structured_type: str = "Article",
    article_header: bool = True,
) -> str:
    if visible_updated is None:
        visible_updated = modified != published
    updated = (
        f' · Actualizado el <time datetime="{modified}">{modified}</time>'
        if visible_updated
        else ""
    )
    header_class = ' class="article-header"' if article_header else ""
    return f'''<!doctype html>
<html><head>
<script type="application/ld+json">{{
  "@context":"https://schema.org",
  "@type":"{structured_type}",
  "headline":"Prueba",
  "datePublished":"{published}",
  "dateModified":"{modified}"
}}</script>
</head><body>
<header{header_class}>
<p>Publicado el <time datetime="{published}">{published}</time>{updated}</p>
</header>
</body></html>'''


def make_fixture(
    root: Path,
    *,
    rel: str = "cuaderno/prueba/index.html",
    published: str = "2026-01-10",
    modified: str = "2026-02-10",
    verified_at: str | None = None,
    review_by: str | None = None,
    visible_updated: bool | None = None,
    structured_type: str = "Article",
    article_header: bool = True,
) -> tuple[Path, Path]:
    relative = Path(rel)
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        article_html(
            published,
            modified,
            visible_updated=visible_updated,
            structured_type=structured_type,
            article_header=article_header,
        ),
        encoding="utf-8",
    )
    entry = {
        "id": "article-test",
        "sourceFile": relative.as_posix(),
    }
    if verified_at is not None:
        entry["verifiedAt"] = verified_at
    if review_by is not None:
        entry["reviewBy"] = review_by
    registry = root / "data/content-registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"entries": [entry]}), encoding="utf-8")
    return target, registry


print("tests/test-article-dates-lifecycle")
as_of = date(2026, 8, 29)

# 1. Existing public-date parity remains valid without lifecycle metadata.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root)
    errors, warnings, infos, checked, lifecycle_count = mod.run_checks(
        root, registry, as_of
    )
    check(not errors, "existing article date contract still passes", str(errors))
    check(not warnings and not infos, "no review debt exists without lifecycle")
    check(checked == 1 and lifecycle_count == 0, "lifecycle remains opt-in")

# 2. A factual verification may be newer than dateModified without fake freshness.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        modified="2026-02-10",
        verified_at="2026-08-20",
        review_by="2026-11-20",
    )
    errors, warnings, infos, _, lifecycle_count = mod.run_checks(
        root, registry, as_of
    )
    check(
        not errors,
        "verifiedAt may exceed dateModified without changing public freshness",
        str(errors),
    )
    check(not warnings and not infos, "future review outside 30 days is quiet")
    check(lifecycle_count == 1, "one scheduled review is counted")

# 3. Overdue review debt is visible but does not manufacture a build failure.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        verified_at="2026-03-01",
        review_by="2026-08-28",
    )
    errors, warnings, _, _, _ = mod.run_checks(root, registry, as_of)
    check(not errors, "overdue review is not a build-integrity error", str(errors))
    check(
        any("overdue" in warning for warning in warnings),
        "overdue review is reported as warning",
        str(warnings),
    )

# 4. A substantive modification after factual verification invalidates verification.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        modified="2026-08-20",
        verified_at="2026-08-19",
        review_by="2026-11-19",
    )
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("verifiedAt" in err and "predates dateModified" in err for err in errors),
        "modification after verification requires reverification",
        str(errors),
    )

# 5. Lifecycle fields are an all-or-nothing pair.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root, verified_at="2026-08-20")
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("must be declared together" in err for err in errors),
        "verifiedAt/reviewBy pair is enforced",
        str(errors),
    )

# 6. Calendar validity is checked, not just YYYY-MM-DD shape.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        verified_at="2026-02-30",
        review_by="2026-12-01",
    )
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("invalid calendar date" in err for err in errors),
        "impossible lifecycle date is rejected",
        str(errors),
    )

# 7. reviewBy cannot predate verifiedAt.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        verified_at="2026-08-20",
        review_by="2026-08-19",
    )
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("reviewBy" in err and "predates" in err for err in errors),
        "reviewBy before verifiedAt is rejected",
        str(errors),
    )

# 8. Public dateModified cannot predate datePublished.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        published="2026-06-01",
        modified="2026-05-01",
    )
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("dateModified" in err and "predates datePublished" in err for err in errors),
        "dateModified before datePublished is rejected",
        str(errors),
    )

# 9. Lifecycle applies outside cuaderno/** (for example recommendations).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        rel="recomendaciones/prueba/index.html",
        modified="2026-08-20",
        verified_at="2026-08-21",
        review_by="2026-11-21",
        structured_type="WebPage",
        article_header=False,
    )
    errors, warnings, infos, checked, lifecycle_count = mod.run_checks(
        root, registry, as_of
    )
    check(not errors, "non-Cuaderno lifecycle source is valid", str(errors))
    check(not warnings and not infos, "non-Cuaderno lifecycle respects same debt policy")
    check(
        checked == 0 and lifecycle_count == 1,
        "lifecycle scope is independent of Cuaderno visible-date scope",
    )

# 10. A review due within 30 days is informational, not a failure.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(
        root,
        verified_at="2026-08-20",
        review_by="2026-09-15",
    )
    errors, warnings, infos, _, _ = mod.run_checks(root, registry, as_of)
    check(not errors and not warnings, "near-term review does not fail or warn")
    check(
        any("within 30 days" in info for info in infos),
        "near-term review is reported as info",
        str(infos),
    )

# 11. The checker is read-only.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    target, registry = make_fixture(
        root,
        verified_at="2026-08-20",
        review_by="2026-09-15",
    )
    before_page = target.read_bytes()
    before_registry = registry.read_bytes()
    mod.run_checks(root, registry, as_of)
    check(target.read_bytes() == before_page, "checker does not mutate article HTML")
    check(
        registry.read_bytes() == before_registry,
        "checker does not mutate lifecycle registry",
    )

# 12. Lifecycle dates cannot be hidden in registry defaults.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root)
    payload = json.loads(registry.read_text(encoding="utf-8"))
    payload["defaults"] = {
        "verifiedAt": "2026-08-20",
        "reviewBy": "2026-11-20",
    }
    registry.write_text(json.dumps(payload), encoding="utf-8")
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("lifecycle fields must be per-entry" in err for err in errors),
        "lifecycle defaults are rejected",
        str(errors),
    )

# 13. Historical experimental field names are rejected to prevent schema drift.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    _, registry = make_fixture(root)
    payload = json.loads(registry.read_text(encoding="utf-8"))
    payload["entries"][0]["lastVerified"] = "2026-08-20"
    payload["entries"][0]["reviewAt"] = "2026-11-20"
    registry.write_text(json.dumps(payload), encoding="utf-8")
    errors, _, _, _, _ = mod.run_checks(root, registry, as_of)
    check(
        any("unsupported legacy lifecycle field" in err for err in errors),
        "legacy lifecycle aliases are rejected",
        str(errors),
    )

print(
    "tests/test-article-dates-lifecycle: "
    + ("OK" if not failures else f"{len(failures)} FALLO(S)")
)
raise SystemExit(1 if failures else 0)
