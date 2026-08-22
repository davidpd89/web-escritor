#!/usr/bin/env python3
"""Offline contract for premios.html evidence and award attribution."""
from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "premios.html"

failures: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def text_content(fragment: str) -> str:
    fragment = re.sub(r"<script\b.*?</script>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<style\b.*?</style>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_module.unescape(fragment)).strip()


source = PAGE.read_text(encoding="utf-8")
check(source.startswith("<!DOCTYPE html>"), "premios.html: missing HTML doctype")
check(len(re.findall(r"<h1(?:\s|>)", source, flags=re.I)) == 1, "premios.html: expected exactly one H1")
check("id-card" not in source, "premios.html: card treatment reintroduced")

jsonld_blocks = re.findall(
    r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
    source,
    flags=re.I | re.S,
)
check(bool(jsonld_blocks), "premios.html: missing JSON-LD")
documents = []
for index, block in enumerate(jsonld_blocks):
    try:
        documents.append(json.loads(block))
    except json.JSONDecodeError as exc:
        failures.append(f"premios.html: invalid JSON-LD block {index}: {exc}")

nodes = []
for document in documents:
    if isinstance(document, dict):
        graph = document.get("@graph")
        nodes.extend(graph if isinstance(graph, list) else [document])
persons = [node for node in nodes if isinstance(node, dict) and node.get("@type") == "Person"]
check(len(persons) == 1, f"premios.html: expected one Person node, got {len(persons)}")
person_awards = persons[0].get("award", []) if persons else []
check(isinstance(person_awards, list), "premios.html: Person.award must be an array")

section_match = re.search(
    r'<section\b[^>]*id="reconocimientos"[^>]*>(.*?)</section>',
    source,
    flags=re.I | re.S,
)
check(bool(section_match), "premios.html: missing #reconocimientos")
recognition_html = section_match.group(1) if section_match else ""
records = re.findall(r'<li\b[^>]*data-award-record[^>]*>(.*?)</li>', recognition_html, flags=re.I | re.S)
check(len(records) == 2, f"premios.html: expected exactly 2 visible recognition records, got {len(records)}")

visible_awards: list[str] = []
source_links: list[dict[str, str]] = []
for index, record in enumerate(records, start=1):
    year_match = re.search(r'<span\b[^>]*data-award-year[^>]*>(.*?)</span>', record, flags=re.I | re.S)
    result_match = re.search(r'<h3\b[^>]*data-award-result[^>]*>(.*?)</h3>', record, flags=re.I | re.S)
    name_match = re.search(r'<span\b[^>]*data-award-name[^>]*>(.*?)</span>', record, flags=re.I | re.S)
    organizer_match = re.search(r'<span\b[^>]*data-award-organizer[^>]*>(.*?)</span>', record, flags=re.I | re.S)
    check(all((year_match, result_match, name_match, organizer_match)), f"recognition {index}: incomplete visible award identity")
    if all((year_match, result_match, name_match, organizer_match)):
        year = text_content(year_match.group(1))
        result = text_content(result_match.group(1))
        name = text_content(name_match.group(1))
        organizer = text_content(organizer_match.group(1))
        visible_awards.append(f"{result} — {name} · {organizer} ({year})")

    for anchor_match in re.finditer(r'<a\b([^>]*\bdata-award-source\b[^>]*)>', record, flags=re.I | re.S):
        raw_attrs = anchor_match.group(1)
        attrs = dict(re.findall(r'([:\w-]+)="([^"]*)"', raw_attrs))
        source_links.append(attrs)

check(len(person_awards) == 2, f"premios.html: Person.award must contain exactly 2 recognitions, got {len(person_awards) if isinstance(person_awards, list) else 'non-list'}")
check(person_awards == visible_awards, f"premios.html: Person.award does not exactly match visible recognitions: schema={person_awards!r}, visible={visible_awards!r}")
check(len(set(visible_awards)) == len(visible_awards), "premios.html: duplicated visible recognition")
check(len(set(person_awards)) == len(person_awards) if isinstance(person_awards, list) else False, "premios.html: duplicated Person.award value")

for forbidden in ("Debut novelístico publicado", "Antología colaborativa", "Segunda novela", "Reseñas de lectores"):
    check(forbidden not in " ".join(person_awards), f"premios.html: trajectory/reception item leaked into Person.award: {forbidden}")

check("No es un premio de <em>Samuel entre mundos</em>" in records[0] if records else False, "premios.html: first award does not explicitly disambiguate Samuel entre mundos")
check("no lo atribuye a <em>Samuel entre mundos</em>" in records[1] if len(records) > 1 else False, "premios.html: finalist record incorrectly attributes the submitted work to Samuel entre mundos")
check("manuscritos inéditos" in records[1] if len(records) > 1 else False, "premios.html: finalist evidence limitation omits the official unpublished-work requirement")
check(bool(source_links), "premios.html: recognition records lack evidence links")
for index, attrs in enumerate(source_links, start=1):
    href = attrs.get("href", "")
    rel_tokens = set(attrs.get("rel", "").split())
    check(href.startswith("https://"), f"source link {index}: must use HTTPS: {href}")
    check(attrs.get("target") == "_blank", f"source link {index}: external source must use target=_blank")
    check({"noopener", "noreferrer"}.issubset(rel_tokens), f"source link {index}: missing safe rel tokens")
    check(not re.search(r"[?&](utm_|fbclid|gclid)", href, flags=re.I), f"source link {index}: tracking parameter found")

source_hrefs = [attrs.get("href", "") for attrs in source_links]
check("https://www.instagram.com/davidportodiaz/" not in source_hrefs, "premios.html: author social network used as award evidence")
check("https://www.letrascomoespada.com/concursos/memoria_concursos/memoria2026.php" in source_hrefs, "premios.html: official Letras Como Espada results source missing")
check("https://www.babidibulibros.com/premio-literatura-juan-andres-teno-2026/" in source_hrefs, "premios.html: official BABIDI-BÚ call source missing")

if failures:
    print("Awards evidence contract FAILED:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print(f"PASS — awards evidence contract ({checks} checks).")
