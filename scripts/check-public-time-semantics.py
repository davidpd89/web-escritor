#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today()
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

def parse_temporal(value: str):
    value = value.strip()
    if not value:
        raise ValueError("empty temporal value")
    if re.fullmatch(r"P(?:\d+[YMWD])?(?:T(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?", value):
        return ("duration", value)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return ("date", date.fromisoformat(value))
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return ("datetime", datetime.fromisoformat(normalized))
    except ValueError as exc:
        raise ValueError(f"invalid ISO date/datetime {value!r}") from exc

def as_date(parsed):
    kind, value = parsed
    if kind == "date":
        return value
    if kind == "datetime":
        return value.date()
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
            parse_temporal(value)
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
                    d = as_date(parsed[key])
                    if d and d > TODAY:
                        errors.append(f"{rel}:{line}: {key} is in the future ({d.isoformat()})")

            if "datePublished" in parsed and "dateModified" in parsed:
                a, b = as_date(parsed["datePublished"]), as_date(parsed["dateModified"])
                if a and b and b < a:
                    errors.append(f"{rel}:{line}: dateModified {b} precedes datePublished {a}")

            if "startDate" in parsed and "endDate" in parsed:
                a, b = parsed["startDate"], parsed["endDate"]
                if a[0] != "duration" and b[0] != "duration":
                    av, bv = a[1], b[1]
                    if isinstance(av, date) and not isinstance(av, datetime):
                        av = datetime.combine(av, datetime.min.time())
                    if isinstance(bv, date) and not isinstance(bv, datetime):
                        bv = datetime.combine(bv, datetime.min.time())
                    if isinstance(av, datetime) and isinstance(bv, datetime):
                        if av.tzinfo is not None and bv.tzinfo is None:
                            bv = bv.replace(tzinfo=av.tzinfo)
                        elif bv.tzinfo is not None and av.tzinfo is None:
                            av = av.replace(tzinfo=bv.tzinfo)
                        if bv < av:
                            errors.append(f"{rel}:{line}: endDate precedes startDate")

if errors:
    print(f"PUBLIC TIME SEMANTICS: FAIL ({len(errors)} issue(s))")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"PUBLIC TIME SEMANTICS: PASS ({files} files, {time_count} <time> values, {jsonld_count} JSON-LD blocks)")
