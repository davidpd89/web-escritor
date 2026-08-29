#!/usr/bin/env python3
"""Validate article dates and optional editorial review lifecycle.

Two different clocks are intentionally kept separate:

- ``datePublished`` / ``dateModified`` describe publication and substantive
  page changes and must stay in parity with the visible article dates.
- ``lastVerified`` / ``reviewBy`` are optional editorial lifecycle fields in
  ``data/content-registry.json``. They track factual verification/review debt
  without pretending that a verification-only pass modified the article.

Run from the repository root:
    python scripts/check-article-dates.py --check

For deterministic tests/audits:
    python scripts/check-article-dates.py --check --as-of 2026-08-29
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLE_GLOB = "cuaderno/**/index.html"
DEFAULT_REGISTRY = "data/content-registry.json"

JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
ARTICLE_HEADER_RE = re.compile(r"<header\s+class=\"article-header\"", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PUBLISHED_VISIBLE_RE = re.compile(
    r"Publicado el\s*<time[^>]*datetime=[\"'](?P<date>\d{4}-\d{2}-\d{2})[\"']",
    re.I,
)
UPDATED_VISIBLE_RE = re.compile(
    r"Actualizado el\s*<time[^>]*datetime=[\"'](?P<date>\d{4}-\d{2}-\d{2})[\"']",
    re.I,
)


def iter_nodes(node):
    if isinstance(node, dict):
        yield node
        if isinstance(node.get("@graph"), list):
            for child in node["@graph"]:
                yield from iter_nodes(child)
        for value in node.values():
            yield from iter_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_nodes(item)


def parse_iso_date(value: object, label: str, errors: list[str]) -> date | None:
    """Parse a strict YYYY-MM-DD calendar date and append a useful error."""
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        errors.append(f"{label}: expected YYYY-MM-DD, got {value!r}")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: invalid calendar date {value!r}")
        return None


def extract_article_dates(html: str) -> tuple[str | None, str | None]:
    published = None
    modified = None
    for match in JSONLD_RE.finditer(html):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in iter_nodes(data):
            if not isinstance(node, dict):
                continue
            type_value = node.get("@type")
            types = type_value if isinstance(type_value, list) else [type_value]
            if not any(t in {"Article", "BlogPosting"} for t in types if isinstance(t, str)):
                continue
            p = node.get("datePublished")
            m = node.get("dateModified")
            if isinstance(p, str) and DATE_RE.match(p[:10]):
                published = p[:10]
            if isinstance(m, str) and DATE_RE.match(m[:10]):
                modified = m[:10]
            if published and modified:
                return published, modified
    return published, modified


def load_review_lifecycle(
    registry_path: Path,
    root: Path,
    as_of: date,
) -> tuple[dict[str, dict[str, date]], list[str]]:
    """Load optional lastVerified/reviewBy fields from the canonical registry.

    The pair is all-or-nothing. ``lastVerified`` may be newer than the page's
    ``dateModified``: checking facts without substantively changing the page
    must not manufacture freshness. ``reviewBy`` is an editorial deadline and
    an overdue entry fails CI until it is actually reviewed/rescheduled.
    """
    errors: list[str] = []
    lifecycle: dict[str, dict[str, date]] = {}

    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{registry_path}: cannot read lifecycle registry: {exc}"]

    entries = raw.get("entries")
    if not isinstance(entries, list):
        return {}, [f"{registry_path}: content-registry must contain an entries array"]

    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            continue
        source = item.get("sourceFile")
        item_id = item.get("id", f"entry-{index + 1}")
        last_raw = item.get("lastVerified")
        review_raw = item.get("reviewBy")
        has_last = last_raw not in (None, "")
        has_review = review_raw not in (None, "")

        if not has_last and not has_review:
            continue
        if not has_last or not has_review:
            errors.append(
                f"{item_id}: lastVerified and reviewBy must be declared together"
            )
            continue
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{item_id}: lifecycle entry requires sourceFile")
            continue

        last_verified = parse_iso_date(last_raw, f"{item_id}.lastVerified", errors)
        review_by = parse_iso_date(review_raw, f"{item_id}.reviewBy", errors)
        if not last_verified or not review_by:
            continue

        if last_verified > as_of:
            errors.append(
                f"{item_id}: lastVerified {last_verified.isoformat()} is in the future "
                f"relative to {as_of.isoformat()}"
            )
        if review_by < last_verified:
            errors.append(
                f"{item_id}: reviewBy {review_by.isoformat()} predates "
                f"lastVerified {last_verified.isoformat()}"
            )
        if review_by < as_of:
            errors.append(
                f"{item_id}: editorial review overdue since {review_by.isoformat()} "
                f"(as-of {as_of.isoformat()})"
            )

        source_path = root / source
        if not source_path.is_file():
            errors.append(f"{item_id}: lifecycle sourceFile does not exist: {source}")

        if source in lifecycle:
            errors.append(f"{item_id}: duplicate lifecycle declaration for sourceFile {source}")
            continue
        lifecycle[source] = {
            "lastVerified": last_verified,
            "reviewBy": review_by,
        }

    return lifecycle, errors


def check_file(
    path: Path,
    root: Path,
    lifecycle: dict[str, dict[str, date]],
) -> tuple[list[str], bool]:
    errors: list[str] = []
    rel = path.relative_to(root).as_posix()
    html = path.read_text(encoding="utf-8", errors="replace")

    if not ARTICLE_HEADER_RE.search(html):
        return errors, False

    published, modified = extract_article_dates(html)
    if not published or not modified:
        errors.append(f"{rel}: missing datePublished/dateModified in JSON-LD Article")
        return errors, True

    published_date = parse_iso_date(published, f"{rel}.datePublished", errors)
    modified_date = parse_iso_date(modified, f"{rel}.dateModified", errors)
    if published_date and modified_date and modified_date < published_date:
        errors.append(
            f"{rel}: dateModified {modified} predates datePublished {published}"
        )

    visible_published = PUBLISHED_VISIBLE_RE.search(html)
    if not visible_published:
        errors.append(f"{rel}: missing visible published date block")
    elif visible_published.group("date") != published:
        errors.append(f"{rel}: missing visible published date matching JSON-LD ({published})")

    visible_updated = UPDATED_VISIBLE_RE.search(html)
    has_updated = visible_updated is not None
    if modified == published:
        if has_updated:
            errors.append(
                f"{rel}: has visible updated date even though "
                f"dateModified == datePublished ({modified})"
            )
    else:
        if not visible_updated:
            errors.append(f"{rel}: missing visible updated date block ({modified})")
        elif visible_updated.group("date") != modified:
            errors.append(f"{rel}: missing visible updated date matching JSON-LD ({modified})")

    review = lifecycle.get(rel)
    if review and modified_date:
        # A substantive page change after the last factual verification makes
        # that verification stale. The opposite is intentionally allowed:
        # lastVerified > dateModified means facts were rechecked without
        # manufacturing a new public modification date.
        if review["lastVerified"] < modified_date:
            errors.append(
                f"{rel}: lastVerified {review['lastVerified'].isoformat()} predates "
                f"dateModified {modified_date.isoformat()}; reverify facts after the change"
            )

    return errors, True


def run_checks(
    root: Path,
    registry_path: Path,
    as_of: date,
) -> tuple[list[str], int, int]:
    lifecycle, errors = load_review_lifecycle(registry_path, root, as_of)
    checked = 0
    checked_sources: set[str] = set()

    for file_path in sorted(root.glob(ARTICLE_GLOB)):
        file_errors, is_article = check_file(file_path, root, lifecycle)
        if is_article:
            checked += 1
            checked_sources.add(file_path.relative_to(root).as_posix())
        errors.extend(file_errors)

    # A lifecycle declaration that does not point at a Cuaderno article would
    # silently create unowned review debt. Fail closed instead.
    for source in sorted(lifecycle):
        if source not in checked_sources:
            errors.append(
                f"{source}: lifecycle declared but source is not a checked Cuaderno article"
            )

    return errors, checked, len(lifecycle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check visible article dates and editorial review lifecycle"
    )
    parser.add_argument("--check", action="store_true", help="Run in check mode (default behavior)")
    parser.add_argument("--root", default=str(ROOT), help="Repository/site root")
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY,
        help="Lifecycle authority (relative to --root unless absolute)",
    )
    parser.add_argument(
        "--as-of",
        help="Deterministic review date YYYY-MM-DD (defaults to today)",
    )
    args = parser.parse_args()

    as_of_errors: list[str] = []
    as_of = (
        parse_iso_date(args.as_of, "--as-of", as_of_errors)
        if args.as_of
        else date.today()
    )
    if as_of_errors or as_of is None:
        print("FAIL: invalid --as-of date", file=sys.stderr)
        for err in as_of_errors:
            print(f" - {err}", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    registry_path = Path(args.registry)
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    errors, checked, lifecycle_count = run_checks(root, registry_path, as_of)

    if errors:
        print("FAIL: article date/review lifecycle mismatch", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    print(
        "PASS: article date/review lifecycle "
        f"({checked} articles, {lifecycle_count} scheduled reviews, "
        f"as-of {as_of.isoformat()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
