#!/usr/bin/env python3
"""Offline sampler for Open Library monthly WORKS dump.

The output is an INTERNAL research queue, not verified narrative locations.
Accepts gzipped OL TSV (type, key, revision, modified, JSON) or uncompressed TSV.
No network, no LLM, no publication. Downloads remain outside Git and CI.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

WORK = re.compile(r"^/works/(OL[0-9]+W)$")
AUTH = re.compile(r"^/authors/OL[0-9]+A$")


def work_candidate(tsv_line: str, place_terms: tuple[str, ...] = ()) -> dict | None:
    fields = tsv_line.rstrip("\r\n").split("\t", 4)
    if len(fields) != 5 or fields[0] != "/type/work":
        return None
    work_match = WORK.fullmatch(fields[1])
    if work_match is None:
        return None
    try:
        obj = json.loads(fields[4])
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(obj, dict):
        return None
    places = obj.get("subject_places") or []
    if not isinstance(places, list):
        return None
    places = sorted({p.strip() for p in places if isinstance(p, str) and p.strip()}, key=str.casefold)
    if not places:
        return None
    if place_terms and not any(t in p.casefold() for t in place_terms for p in places):
        return None
    title = obj.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    authors = obj.get("authors") or []
    author_keys: set[str] = set()
    for a in authors if isinstance(authors, list) else []:
        key = a.get("author", {}).get("key") if isinstance(a, dict) and isinstance(a.get("author"), dict) else None
        if isinstance(key, str) and AUTH.fullmatch(key):
            author_keys.add(key)
    return {
        "status": "candidate",
        "source": "openlibrary_works_dump",
        "source_url": f"https://openlibrary.org/works/{work_match.group(1)}",
        "work_id": work_match.group(1),
        "title": title.strip(),
        "authors_openlibrary": sorted(author_keys),
        "subject_place_candidates": places,
        "relationship_type": "unverified_subject_place",
        "rights_status": "metadata_license_review_pending",
        "evidence_warning": "Open Library subject_places NO acredita un escenario narrativo ni una calle",
    }


def scan(stream, *, place_terms: tuple[str, ...] = (), max_rows: int = 100000,
         max_candidates: int = 100):
    """Return bounded candidates and counters; never read or process the full planet by default."""
    stats = {"scanned": 0, "candidates": 0, "stopped_by_limit": False}
    output = []
    for line in stream:
        if stats["scanned"] >= max_rows or len(output) >= max_candidates:
            stats["stopped_by_limit"] = True
            break
        stats["scanned"] += 1
        item = work_candidate(line, place_terms)
        if item:
            output.append(item)
    stats["candidates"] = len(output)
    return output, stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dump", type=Path, help="Fichero .txt/.txt.gz local, NO se descarga")
    p.add_argument("--place", action="append", default=[], help="Filtro opcional por topónimo en subject_places")
    p.add_argument("--max-rows", type=int, default=100000)
    p.add_argument("--max-candidates", type=int, default=100)
    p.add_argument("--output", type=Path, help="Guardar cola JSONL de candidatos; sin esto solo resumen")
    args = p.parse_args()
    if args.max_rows < 1 or not 1 <= args.max_candidates <= 10000:
        p.error("max-rows >= 1 y 1 <= max-candidates <= 10000")
    if args.output and args.output.exists():
        p.error("La salida ya existe: conservar snapshot; usar ruta nueva")
    if args.output and args.dump.resolve() == args.output.resolve():
        p.error("Salida y entrada no pueden ser el mismo fichero")
    opener = gzip.open if args.dump.suffix.casefold() == ".gz" else open
    with opener(args.dump, "rt", encoding="utf-8", errors="replace") as f:
        rows, stats = scan(f, place_terms=tuple(s.strip().casefold() for s in args.place if s.strip()),
                           max_rows=args.max_rows, max_candidates=args.max_candidates)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as dst:
            for row in rows:
                dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"input": str(args.dump), "output": str(args.output) if args.output else None,
                      **stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
