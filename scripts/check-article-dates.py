#!/usr/bin/env python3
"""Validate public article dates and optional editorial review lifecycle.

Two clocks are intentionally separate:

- ``datePublished`` / ``dateModified`` describe publication and substantive
  page changes and must stay in parity with visible dates on Cuaderno articles.
- ``verifiedAt`` / ``reviewBy`` are optional internal lifecycle fields in
  ``data/content-registry.json``. They track factual verification and review
  debt without pretending that a verification-only pass modified the page.

Lifecycle metadata is source-agnostic: any registry entry with a real
``sourceFile`` may opt in. Lifecycle dates must be declared per entry, never in
registry defaults. Legacy experimental field names are rejected so the repo has
one authoritative schema.

An overdue review is editorial debt (warning), not a build-integrity failure.
Invalid dates, impossible ordering, missing sources, schema drift, or a
substantive page modification newer than ``verifiedAt`` are errors.

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
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLE_GLOB = "cuaderno/**/index.html"
DEFAULT_REGISTRY = "data/content-registry.json"
REVIEW_DUE_SOON_DAYS = 30
LIFECYCLE_FIELDS = {"verifiedAt", "reviewBy"}
LEGACY_LIFECYCLE_FIELDS = {
    "lastVerified",
    "lastVerifiedAt",
    "lastReviewed",
    "lastReviewedAt",
    "reviewAt",
    "reviewCadence",
}

JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
ARTICLE_HEADER_RE = re.compile(r'<header\s+class=["\']article-header["\']', re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PUBLISHED_VISIBLE_RE = re.compile(
    r'Publicado el\s*<time[^>]*datetime=["\'](?P<date>\d{4}-\d{2}-\d{2})["\']',
    re.I,
)
UPDATED_VISIBLE_RE = re.compile(
    r'Actualizado el\s*<time[^>]*datetime=["\'](?P<date>\d{4}-\d{2}-\d{2})["\']',
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


def jsonld_nodes(html: str):
    """Yield parsed JSON-LD nodes, ignoring malformed blocks as the old checker did."""
    for match in JSONLD_RE.finditer(html):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        yield from iter_nodes(data)


def extract_article_dates(html: str) -> tuple[str | None, str | None]:
    """Return Article/BlogPosting publication and modification dates."""
    published = None
    modified = None
    for node in jsonld_nodes(html):
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


def extract_structured_modified_date(html: str) -> str | None:
    """Return a page-like JSON-LD dateModified when available.

    Lifecycle metadata can apply outside ``cuaderno/**`` (for example a
    recommendation page). This helper lets the internal verification clock be
    checked against a substantive public modification without broadening the
    visible-date contract of Cuaderno articles.
    """
    candidates: list[str] = []
    for node in jsonld_nodes(html):
        if not isinstance(node, dict):
            continue
        type_value = node.get("@type")
        types = type_value if isinstance(type_value, list) else [type_value]
        if not any(
            t in {"Article", "BlogPosting", "NewsArticle", "WebPage"}
            for t in types
            if isinstance(t, str)
        ):
            continue
        modified = node.get("dateModified")
        if isinstance(modified, str) and DATE_RE.match(modified[:10]):
            candidates.append(modified[:10])
    return max(candidates) if candidates else None


def load_review_lifecycle(
    registry_path: Path,
    root: Path,
    as_of: date,
) -> tuple[
    dict[str, dict[str, date]],
    list[str],
    list[str],
    list[str],
]:
    """Load optional ``verifiedAt`` / ``reviewBy`` lifecycle metadata.

    The pair is all-or-nothing and must be declared on individual entries.
    Registry defaults are forbidden for lifecycle dates because verification
    and review targets describe an actual editorial act on a specific source.

    ``verifiedAt`` may be newer than a page's ``dateModified``: checking facts
    without substantively changing the page must not manufacture freshness.

    Review debt is deliberately non-blocking:
    - due within 30 days -> INFO;
    - overdue -> WARNING;
    - malformed/impossible metadata or schema drift -> ERROR.

    A future blocking policy would require an explicit release-critical
    contract; A.4 does not invent one.
    """
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []
    lifecycle: dict[str, dict[str, date]] = {}

    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{registry_path}: cannot read lifecycle registry: {exc}"], [], []

    defaults = raw.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        errors.append(f"{registry_path}: content-registry defaults must be an object")
    else:
        default_lifecycle = sorted(
            set(defaults) & (LIFECYCLE_FIELDS | LEGACY_LIFECYCLE_FIELDS)
        )
        if default_lifecycle:
            errors.append(
                "content-registry defaults: lifecycle fields must be per-entry, "
                "not defaults: " + ", ".join(default_lifecycle)
            )

    entries = raw.get("entries")
    if not isinstance(entries, list):
        errors.append(f"{registry_path}: content-registry must contain an entries array")
        return {}, errors, warnings, infos

    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            continue

        source = item.get("sourceFile")
        item_id = item.get("id", f"entry-{index + 1}")
        legacy_fields = sorted(set(item) & LEGACY_LIFECYCLE_FIELDS)
        if legacy_fields:
            errors.append(
                f"{item_id}: unsupported legacy lifecycle field(s) "
                f"{', '.join(legacy_fields)}; use verifiedAt + reviewBy"
            )

        verified_raw = item.get("verifiedAt")
        review_raw = item.get("reviewBy")
        has_verified = verified_raw not in (None, "")
        has_review = review_raw not in (None, "")

        if not has_verified and not has_review:
            continue
        if not has_verified or not has_review:
            errors.append(
                f"{item_id}: verifiedAt and reviewBy must be declared together"
            )
            continue
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{item_id}: lifecycle entry requires sourceFile")
            continue

        verified_at = parse_iso_date(
            verified_raw, f"{item_id}.verifiedAt", errors
        )
        review_by = parse_iso_date(review_raw, f"{item_id}.reviewBy", errors)
        if not verified_at or not review_by:
            continue

        if verified_at > as_of:
            errors.append(
                f"{item_id}: verifiedAt {verified_at.isoformat()} is in the future "
                f"relative to {as_of.isoformat()}"
            )
        if review_by < verified_at:
            errors.append(
                f"{item_id}: reviewBy {review_by.isoformat()} predates "
                f"verifiedAt {verified_at.isoformat()}"
            )

        source_path = root / source
        if not source_path.is_file():
            errors.append(f"{item_id}: lifecycle sourceFile does not exist: {source}")
        else:
            html = source_path.read_text(encoding="utf-8", errors="replace")
            modified_raw = extract_structured_modified_date(html)
            if modified_raw:
                modified_date = parse_iso_date(
                    modified_raw, f"{source}.dateModified", errors
                )
                if modified_date and verified_at < modified_date:
                    errors.append(
                        f"{source}: verifiedAt {verified_at.isoformat()} predates "
                        f"dateModified {modified_date.isoformat()}; reverify facts "
                        "after the substantive change"
                    )

        if source in lifecycle:
            errors.append(
                f"{item_id}: duplicate lifecycle declaration for sourceFile {source}"
            )
            continue

        lifecycle[source] = {
            "verifiedAt": verified_at,
            "reviewBy": review_by,
        }

        if review_by < as_of:
            warnings.append(
                f"{item_id}: editorial review overdue since {review_by.isoformat()} "
                f"(as-of {as_of.isoformat()})"
            )
        elif review_by <= as_of + timedelta(days=REVIEW_DUE_SOON_DAYS):
            infos.append(
                f"{item_id}: editorial review due by {review_by.isoformat()} "
                f"(within {REVIEW_DUE_SOON_DAYS} days)"
            )

    return lifecycle, errors, warnings, infos


def check_file(path: Path, root: Path) -> tuple[list[str], bool]:
    """Validate the existing visible-date contract for Cuaderno articles."""
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
        errors.append(
            f"{rel}: missing visible published date matching JSON-LD ({published})"
        )

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
            errors.append(
                f"{rel}: missing visible updated date matching JSON-LD ({modified})"
            )

    return errors, True


def run_checks(
    root: Path,
    registry_path: Path,
    as_of: date,
) -> tuple[list[str], list[str], list[str], int, int]:
    lifecycle, errors, warnings, infos = load_review_lifecycle(
        registry_path, root, as_of
    )
    checked = 0

    for file_path in sorted(root.glob(ARTICLE_GLOB)):
        file_errors, is_article = check_file(file_path, root)
        if is_article:
            checked += 1
        errors.extend(file_errors)

    return errors, warnings, infos, checked, len(lifecycle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check visible article dates and editorial review lifecycle"
    )
    parser.add_argument(
        "--check", action="store_true", help="Run in check mode (default behavior)"
    )
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

    errors, warnings, infos, checked, lifecycle_count = run_checks(
        root, registry_path, as_of
    )

    for info in infos:
        print(f"INFO: {info}")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print("FAIL: article date/review lifecycle mismatch", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    print(
        "PASS: article date/review lifecycle "
        f"({checked} Cuaderno articles, {lifecycle_count} scheduled reviews, "
        f"{len(warnings)} overdue, as-of {as_of.isoformat()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
