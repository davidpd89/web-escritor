#!/usr/bin/env python3
"""Offline, read-only reconciliation: manuscript directory vs bibliographic imprints.

Never merges entities, writes to datasets, crawls sources or guesses contact details.
Review candidates only; publication of a book proves NOTHING about manuscript intake.

Run after obtaining an authorized snapshot of PR #687's pending data:
  python scripts/research/gpt_editoriales_reconcile.py \
    --directory data/editoriales.json \
    --catalogue-publishers /path/to/reading-publishers.json \
    --books /path/to/reading-catalogue.json --as-of 2026-10-22

This research script is intentionally not imported by the daily publication pipeline.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
GENERIC_PREFIXES = ("editorial ", "ediciones ")
ALLOWED_STATUS = {"open", "closed", "unknown", "indirect", "award_only"}


def name_key(value: object) -> str:
    if not isinstance(value, str):
        return ""
    plain = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", plain))


def possible_alias_key(value: object) -> str:
    """Suggest, never approve, an alias after common editorial prefix removal."""
    text = name_key(value)
    for prefix in GENERIC_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def date_age(raw: object, reference: date) -> int | None:
    if not isinstance(raw, str):
        return None
    try:
        when = date.fromisoformat(raw)
    except ValueError:
        return None
    return (reference - when).days


def valid_source(raw: object, *, permitted_host: str | None = None) -> bool:
    if not isinstance(raw, str):
        return False
    try:
        url = urlsplit(raw)
        return (url.scheme == "https" and bool(url.hostname) and not url.username
                and not url.password and url.port is None
                and (permitted_host is None or url.hostname == permitted_host)
                and not url.fragment)
    except ValueError:
        return False


def _unique_rows(rows: list[dict], dataset: str) -> dict:
    by_slug: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{dataset}: registro no es objeto")
        slug = row.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"{dataset}: identificador inválido: {slug!r}")
        if slug in by_slug:
            raise ValueError(f"{dataset}: slug duplicado: {slug}")
        by_slug[slug] = row
    return by_slug


def reconcile(directory: dict, catalogue_publishers: dict, books: dict,
              *, as_of: date, stale_days: int = 90) -> dict:
    """Deterministic public-safe report: no emails, contact paths or private notes."""
    if not isinstance(directory.get("publishers"), list):
        raise ValueError("Directory requires publishers array")
    if not isinstance(catalogue_publishers.get("editoriales"), list):
        raise ValueError("Catalogue publishers requires editoriales array")
    if not isinstance(books.get("libros"), list):
        raise ValueError("Books require libros array")
    if stale_days < 1:
        raise ValueError("stale_days must be positive")
    manual = _unique_rows(directory["publishers"], "directory")
    imprints = _unique_rows(catalogue_publishers["editoriales"], "catalogue")
    if any(not isinstance(b, dict) for b in books["libros"]):
        raise ValueError("Malformed book")
    book_ids = [b.get("id") for b in books["libros"]]
    if any(not isinstance(ident, str) or not ident for ident in book_ids):
        raise ValueError("Missing book ID")
    if len(set(book_ids)) != len(book_ids):
        raise ValueError("Duplicate book ID")
    exact_names: dict[str, list[dict]] = defaultdict(list)
    alias_names: dict[str, list[dict]] = defaultdict(list)
    for row in manual.values():
        exact_names[name_key(row.get("name"))].append(row)
        alias_names[possible_alias_key(row.get("name"))].append(row)
    reused_names = {key: sorted(r["slug"] for r in rows)
                    for key, rows in exact_names.items()
                    if key and len(rows) > 1}
    status_counts = Counter(row.get("status", "unrecognized") for row in manual.values())
    stale = []
    invalid_checks = []
    no_primary_source = []
    with_submission_email = 0
    for row in manual.values():
        slug = row["slug"]
        age = date_age(row.get("verified_at"), as_of)
        if age is None or age < 0:
            invalid_checks.append(slug)
        elif age > stale_days:
            stale.append(slug)
        if row.get("submission_email"):
            with_submission_email += 1
        if not any(isinstance(src, dict) and src.get("primary") is True
                   and valid_source(src.get("url")) for src in row.get("sources", [])):
            no_primary_source.append(slug)
    links_manual = Counter()
    links_imprints = Counter()
    book_errors = []
    for book in books["libros"]:
        if book.get("estado") != "publicado":
            continue
        slug = book.get("editorial_slug")
        imprint_slug = book.get("editorial_catalogo_slug")
        ident = book.get("id", "(sin id)")
        if slug and imprint_slug:
            book_errors.append({"book": ident, "problem": "two_publisher_targets"})
        elif slug:
            links_manual[slug] += 1
            if slug not in manual:
                book_errors.append({"book": ident, "problem": "missing_directory_slug", "slug": slug})
        elif imprint_slug:
            links_imprints[imprint_slug] += 1
            if imprint_slug not in imprints:
                book_errors.append({"book": ident, "problem": "missing_catalogue_slug", "slug": imprint_slug})
        else:
            book_errors.append({"book": ident, "problem": "no_publisher_reference"})

    candidates = []
    for slug, row in sorted(imprints.items()):
        name = row.get("nombre")
        exact = exact_names.get(name_key(name), [])
        alias = alias_names.get(possible_alias_key(name), [])
        slug_conflict = slug in manual
        source_urls = [src.get("url") for src in row.get("fuentes", [])
                       if isinstance(src, dict)]
        valid_evidence = bool(source_urls) and all(valid_source(url, permitted_host="www.penguinlibros.com")
                                                   for url in source_urls)
        if slug_conflict:
            decision = "review_slug_collision"
        elif len(exact) == 1:
            decision = "review_exact_name"
        elif len(exact) > 1:
            decision = "review_ambiguous_name"
        elif alias:
            decision = "review_alias"
        elif not valid_evidence:
            decision = "quarantine_source"
        else:
            decision = "catalogue_only"
        candidates.append({
            "catalogue_slug": slug,
            "catalogue_name": name,
            "decision": decision,
            "possible_directory_slugs": sorted({r["slug"] for r in exact + alias}
                                                | ({slug} if slug_conflict else set())),
            "linked_books": links_imprints[slug],
            "orphan": links_imprints[slug] == 0,
            "bibliographic_source_valid": valid_evidence,
            "group_claim": row.get("grupo") or None,
            "manuscript_status": "not_inferred",
        })

    directory_linked_statuses = Counter()
    for slug, count in links_manual.items():
        if slug in manual:
            directory_linked_statuses[manual[slug].get("status", "unrecognized")] += count

    return {
        "as_of": as_of.isoformat(),
        "note": "Offline candidates only. ISBN/bibliographic status != manuscript intake status.",
        "counts": {
            "directory_publishers": len(manual),
            "catalogue_imprints": len(imprints),
            "published_books": sum(b.get("estado") == "publicado" for b in books["libros"]),
            "linked_to_directory": sum(links_manual.values()),
            "linked_to_catalogue_imprint": sum(links_imprints.values()),
            "imprints_without_published_books": sum(x["orphan"] for x in candidates),
            "directory_submission_email_records": with_submission_email,
            "directory_primary_source_missing": len(no_primary_source),
            "directory_verification_old": len(stale),
            "directory_verification_invalid": len(invalid_checks),
        },
        "manuscript_status_counts": dict(sorted(status_counts.items())),
        "linked_book_status_counts": dict(sorted(directory_linked_statuses.items())),
        "duplicate_normalized_directory_names": reused_names,
        "stale_directory_slugs": sorted(stale),
        "invalid_verification_slugs": sorted(invalid_checks),
        "without_primary_source_slugs": sorted(no_primary_source),
        "integrity_errors": sorted(book_errors, key=lambda e: (str(e["book"]), e["problem"])),
        "imprint_candidates": candidates,
        "publish_changes": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--catalogue-publishers", type=Path, required=True)
    p.add_argument("--books", type=Path, required=True)
    p.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    p.add_argument("--stale-days", type=int, default=90)
    args = p.parse_args(argv)
    try:
        with args.directory.open(encoding="utf-8") as handle:
            directory = json.load(handle)
        with args.catalogue_publishers.open(encoding="utf-8") as handle:
            publishers = json.load(handle)
        with args.books.open(encoding="utf-8") as handle:
            books = json.load(handle)
        result = reconcile(directory, publishers, books, as_of=args.as_of, stale_days=args.stale_days)
    except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Error: datos incompatibles o fichero no disponible: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
