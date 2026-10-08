#!/usr/bin/env python3
"""Validate temporal semantics across public HTML and JSON-LD.

The checker deliberately preserves reduced precision: a known publication year
such as "2025" is valid information and must not be expanded to an invented
month/day. Ordering checks fail only when two temporal ranges are definitely
contradictory.
"""
from __future__ import annotations

import calendar
import json
import re
import sys
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today()
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

DURATION_RE = re.compile(r"P(?:\d+[YMWD])?(?:T(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?")
YEAR_RE = re.compile(r"\d{4,}")
MONTH_RE = re.compile(r"(\d{4,})-(\d{2})")
DATE_RE = re.compile(r"\d{4,}-\d{2}-\d{2}")
WEEK_RE = re.compile(r"(\d{4,})-W(\d{2})")
YEARLESS_RE = re.compile(r"(?:--)?\d{2}-\d{2}")
TIME_RE = re.compile(r"\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?")
OFFSET_RE = re.compile(r"(?:Z|[+-]\d{2}:?\d{2})")


def parse_temporal(value: str, *, html_time: bool = False):
    value = value.strip()
    if not value:
        raise ValueError("empty temporal value")
    if DURATION_RE.fullmatch(value):
        return ("duration", value)

    if YEAR_RE.fullmatch(value):
        year = int(value)
        if year < 1:
            raise ValueError(f"invalid year {value!r}")
        return ("year", year)

    m = MONTH_RE.fullmatch(value)
    if m:
        year, month = map(int, m.groups())
        if year < 1 or not 1 <= month <= 12:
            raise ValueError(f"invalid month {value!r}")
        return ("month", (year, month))

    if DATE_RE.fullmatch(value):
        try:
            return ("date", date.fromisoformat(value))
        except ValueError as exc:
            raise ValueError(f"invalid ISO date {value!r}") from exc

    # WHATWG <time> accepts additional machine-readable forms that are not
    # Schema.org Date/DateTime values (yearless dates, weeks, bare times and
    # timezone offsets). Validate those syntactically without pretending they
    # denote a calendar date.
    if html_time:
        if YEARLESS_RE.fullmatch(value):
            month, day = map(int, value.removeprefix("--").split("-"))
            # The yearless microsyntax uses a leap year so 02-29 is valid,
            # but impossible month/day combinations must still fail.
            if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(2000, month)[1]:
                raise ValueError(f"invalid yearless date {value!r}")
            return ("html-only", value)
        m = WEEK_RE.fullmatch(value)
        if m:
            year, week = map(int, m.groups())
            if year >= 1:
                jan1 = calendar.weekday(year, 1, 1)
                last_week = 53 if (jan1 == 3 or (jan1 == 2 and calendar.isleap(year))) else 52
                if 1 <= week <= last_week:
                    return ("html-only", value)
            raise ValueError(f"invalid week {value!r}")
        if TIME_RE.fullmatch(value):
            parts = value.split(":")
            hour, minute = int(parts[0]), int(parts[1])
            second = int(parts[2].split(".")[0]) if len(parts) == 3 else 0
            if hour <= 23 and minute <= 59 and second <= 59:
                return ("html-only", value)
            raise ValueError(f"invalid time {value!r}")
        if OFFSET_RE.fullmatch(value):
            if value == "Z":
                return ("html-only", value)
            digits = value[1:].replace(":", "")
            hours, minutes = int(digits[:2]), int(digits[2:])
            # WHATWG permits +00:00 but forbids the negative sign for zero.
            if hours <= 23 and minutes <= 59 and not (value.startswith("-") and hours == minutes == 0):
                return ("html-only", value)
            raise ValueError(f"invalid timezone offset {value!r}")

    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        return ("datetime", parsed)
    except ValueError as exc:
        raise ValueError(f"invalid ISO temporal value {value!r}") from exc


def bounds(parsed):
    """Return inclusive date bounds when a value denotes a calendar period."""
    kind, value = parsed
    if kind == "date":
        return value, value
    if kind == "datetime":
        d = value.date()
        return d, d
    if kind == "year":
        return date(value, 1, 1), date(value, 12, 31)
    if kind == "month":
        year, month = value
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    return None


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.times: list[tuple[int, str]] = []
        self.jsonld: list[tuple[int, str]] = []
        self._json_line = 0
        self._in_json = False
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "time" and "datetime" in data:
            self.times.append((self.getpos()[0], data["datetime"]))
        if tag.lower() == "script" and data.get("type", "").lower() == "application/ld+json":
            self._in_json = True
            self._json_line = self.getpos()[0]
            self._parts = []

    def handle_data(self, data):
        if self._in_json:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._in_json:
            self.jsonld.append((self._json_line, "".join(self._parts)))
            self._in_json = False
            self._parts = []


def public_html():
    seen = set()
    for raw in REGISTRY.get("entries", []):
        item = {**DEFAULTS, **raw}
        source = str(item.get("sourceFile") or "")
        if item.get("status") == "public" and source.endswith(".html"):
            path = ROOT / source
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def walk_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_nodes(child)


errors = []
files = 0
time_count = 0
jsonld_count = 0

for path in sorted(public_html()):
    files += 1
    rel = path.relative_to(ROOT).as_posix()
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8"))

    for line, value in parser.times:
        time_count += 1
        try:
            parse_temporal(value, html_time=True)
        except ValueError as exc:
            errors.append(f"{rel}:{line}: <time datetime={value!r}> {exc}")

    for line, raw in parser.jsonld:
        jsonld_count += 1
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}:{line}: invalid JSON-LD: {exc}")
            continue

        for node in walk_nodes(doc):
            parsed = {}
            for key in ("datePublished", "dateModified", "uploadDate", "startDate", "endDate"):
                if key not in node or not isinstance(node[key], str):
                    continue
                try:
                    parsed[key] = parse_temporal(node[key])
                except ValueError as exc:
                    errors.append(f"{rel}:{line}: {key} {exc}")

            for key in ("datePublished", "dateModified", "uploadDate"):
                if key in parsed:
                    span = bounds(parsed[key])
                    if span and span[0] > TODAY:
                        errors.append(f"{rel}:{line}: {key} is in the future ({node[key]})")

            if "datePublished" in parsed and "dateModified" in parsed:
                published = bounds(parsed["datePublished"])
                modified = bounds(parsed["dateModified"])
                # Fail only when the entire modification period is before the
                # entire publication period. Overlapping reduced-precision
                # ranges are ambiguous and therefore not fabricated.
                if published and modified and modified[1] < published[0]:
                    errors.append(
                        f"{rel}:{line}: dateModified {node['dateModified']} "
                        f"precedes datePublished {node['datePublished']}"
                    )

            if "startDate" in parsed and "endDate" in parsed:
                start = bounds(parsed["startDate"])
                end = bounds(parsed["endDate"])
                if start and end and end[1] < start[0]:
                    errors.append(f"{rel}:{line}: endDate precedes startDate")

if errors:
    print(f"PUBLIC TIME SEMANTICS: FAIL ({len(errors)} issue(s))")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(
    f"PUBLIC TIME SEMANTICS: PASS "
    f"({files} files, {time_count} <time> values, {jsonld_count} JSON-LD blocks)"
)
