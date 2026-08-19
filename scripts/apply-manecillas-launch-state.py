#!/usr/bin/env python3
"""Launch-day transition helper for Las manecillas del recuerdo.

This does NOT blindly find/replace prose. Every previous attempt at
mechanical "prevista -> publicada" substitution on this project has needed a
human pass anyway (tense errors, phrases that don't fit their sentence,
CTAs that need a real purchaseUrl before they can honestly change). Instead
this script:

  1. Tells you whether today is prelaunch or launch, deterministically
     (never guesses from a browser clock - see --date for testing).
  2. In prelaunch mode, lists every tracked file+line containing one of the
     known prelaunch marker phrases about Las manecillas del recuerdo, as an
     explicit checklist of exactly what needs a human look on launch day.
  3. In launch mode (today >= publicationDate), the same listing becomes the
     "these still say prelaunch after the launch date" alarm - which is
     also exactly what check-editorial-facts.py's LAUNCH_STALE patterns
     already catch, so --check here defers to that script rather than
     duplicating the definition of "stale".

Usage:
    python scripts/apply-manecillas-launch-state.py            # list markers
    python scripts/apply-manecillas-launch-state.py --check    # exit 1 if
                                                                 # launch mode
                                                                 # AND markers
                                                                 # remain
    python scripts/apply-manecillas-launch-state.py --date 2026-09-03
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MADRID = ZoneInfo("Europe/Madrid")

# Same source of truth the rest of the toolchain uses.
import json
FACTS = json.loads((ROOT / "editorial-facts.json").read_text(encoding="utf-8"))
BOOK = FACTS["books"]["lasManecillasDelRecuerdo"]
PUBLICATION_DATE = date.fromisoformat(BOOK["publicationDate"])

SCAN_SUFFIXES = {".html", ".txt", ".json"}

# Markers that only make sense while Las manecillas del recuerdo hasn't
# published yet. Each is scoped near the title so unrelated uses of common
# words like "próxima" elsewhere on the page don't get flagged.
MARKERS = [
    (re.compile(r"Las manecillas del recuerdo.{0,120}\bprevista\b", re.I | re.S), "prevista"),
    (re.compile(r"\bprevista\b.{0,120}Las manecillas del recuerdo", re.I | re.S), "prevista"),
    (re.compile(r"Las manecillas del recuerdo.{0,120}\bpróxima novela\b", re.I | re.S), "próxima novela"),
    (re.compile(r"\bpróxima novela\b.{0,60}Las manecillas del recuerdo", re.I | re.S), "próxima novela"),
    (re.compile(r"\bSale el 3 de septiembre de 2026\b", re.I), "sale el ..."),
    (re.compile(r"\bRecu[eé]rdamelo el d[ií]a del lanzamiento\b", re.I), "recuérdamelo"),
    (re.compile(r"\bRecibir aviso de lanzamiento\b", re.I), "avísame / recibir aviso"),
    (re.compile(r"\bTe avisar[eé] cuando Las manecillas del recuerdo est[eé] disponible\b", re.I), "avísame (newsletter)"),
    (re.compile(r'"statusBeforePublication"\s*:\s*"scheduled"', re.I), "editorial-facts.json: statusBeforePublication"),
]


def git_tracked_files() -> set[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        return {line.strip() for line in out.splitlines() if line.strip()}
    except (OSError, subprocess.CalledProcessError):
        return set()


def resolve_today(raw: str | None) -> date:
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(MADRID).date()


def find_markers() -> list[tuple[str, int, str]]:
    tracked = git_tracked_files()
    hits: list[tuple[str, int, str]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if tracked and rel not in tracked:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        for pattern, label in MARKERS:
            for m in pattern.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                snippet = lines[line_no - 1].strip()[:140] if line_no <= len(lines) else ""
                hits.append((rel, line_no, f"[{label}] {snippet}"))
    # de-duplicate identical (file, line) hits from overlapping patterns
    seen = set()
    deduped = []
    for rel, line_no, snippet in hits:
        key = (rel, line_no)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((rel, line_no, snippet))
    return sorted(deduped)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                     help="exit 1 only if today >= publicationDate AND prelaunch markers remain")
    ap.add_argument("--date", help="YYYY-MM-DD, for testing/simulation")
    args = ap.parse_args()

    today = resolve_today(args.date)
    mode = "launch" if today >= PUBLICATION_DATE else "prelaunch"
    hits = find_markers()

    print(f"Today: {today.isoformat()} | Publication date: {PUBLICATION_DATE.isoformat()} | Mode: {mode}")
    print(f"Prelaunch markers found: {len(hits)}\n")
    for rel, line_no, snippet in hits:
        print(f"  {rel}:{line_no}: {snippet}")

    if not hits:
        print("\nNo prelaunch markers found - nothing left that assumes the book isn't out yet.")

    print(
        "\nThis script does not edit anything. Each marker above is a surface to "
        "review by hand on/after launch day: 'prevista para' -> 'publicada el', "
        "'recibir aviso de lanzamiento' -> a real purchase/where-to-buy CTA once "
        "purchaseUrl exists in editorial-facts.json, etc. Update "
        "editorial-facts.json's samuelEntreMundos-style fields for Las manecillas "
        "(statusBeforePublication/statusFromPublicationDate, purchaseUrl) as the "
        "canonical source, then propagate."
    )

    if args.check and mode == "launch" and hits:
        print(f"\nERROR: {len(hits)} prelaunch marker(s) remain after the publication date.", file=sys.stderr)
        return 1
    if args.check:
        print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
