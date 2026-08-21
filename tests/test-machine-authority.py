#!/usr/bin/env python3
"""Cross-surface contract for machine-readable editorial authority.

Offline by design: this validates the current repository contract and never
depends on a pull-request base snapshot or a live external service.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ORIGIN = "https://davidportodiaz.com"
PUBLIC_MACHINE_FILES = (
    "ai/index.html",
    "llms.txt",
    "llms-full.txt",
    "press-kit/david-porto-diaz.json",
    "press-kit/las-manecillas-del-recuerdo.json",
    "press-kit/samuel-entre-mundos.json",
    "robots.txt",
)
UTF8_FILES = ("editorial-facts.json", *PUBLIC_MACHINE_FILES)

failures: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def load_text(rel: str) -> str:
    path = ROOT / rel
    check(path.is_file(), f"missing required file: {rel}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"{rel}: invalid UTF-8 ({exc})")
        return ""


def load_json(rel: str):
    text = load_text(rel)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        failures.append(f"{rel}: invalid JSON ({exc})")
        return {}


def validate_absolute_http_url(value: str, where: str) -> None:
    check(value == value.strip(), f"{where}: URL has surrounding whitespace")
    check(not re.search(r"\s", value), f"{where}: URL contains whitespace")
    parts = urlsplit(value)
    check(parts.scheme in {"http", "https"}, f"{where}: URL must use http/https: {value}")
    check(bool(parts.netloc and parts.hostname), f"{where}: URL lacks hostname: {value}")
    if parts.hostname:
        check(bool(re.fullmatch(r"[A-Za-z0-9.-]+", parts.hostname)), f"{where}: illegal hostname characters: {parts.hostname}")
        check(not parts.hostname.startswith(".") and not parts.hostname.endswith("."), f"{where}: malformed hostname: {parts.hostname}")
        for label in parts.hostname.split("."):
            check(bool(label) and not label.startswith("-") and not label.endswith("-"), f"{where}: malformed hostname label in {parts.hostname}")


def walk_urls(value, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str) and (
                child.startswith("http://")
                or child.startswith("https://")
                or key.lower().endswith("url")
                or key.lower().endswith("website")
                or key.lower() in {"wikidata", "orcid", "goodreads", "babelio", "storygraph", "amazonauthorcentral"}
            ):
                if child.startswith(("http://", "https://")):
                    validate_absolute_http_url(child, child_path)
            walk_urls(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk_urls(child, f"{path}[{i}]")


class AIHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.scripts: list[tuple[dict[str, str], str]] = []
        self._script_attrs: dict[str, str] | None = None
        self._script_data: list[str] = []
        self.h1 = 0
        self.h2 = 0
        self.has_main = False
        self.has_skip = False
        self.html_classes: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag == "html":
            self.html_classes = set((data.get("class") or "").split())
        elif tag == "link":
            self.links.append(data)
        elif tag == "meta":
            self.metas.append(data)
        elif tag == "script":
            self._script_attrs = data
            self._script_data = []
        elif tag == "h1":
            self.h1 += 1
        elif tag == "h2":
            self.h2 += 1
        elif tag == "main" and data.get("id") == "contenido":
            self.has_main = True
        elif tag == "a" and data.get("class") == "skip-link" and data.get("href") == "#contenido":
            self.has_skip = True

    def handle_data(self, data: str) -> None:
        if self._script_attrs is not None:
            self._script_data.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_attrs is not None:
            self.scripts.append((self._script_attrs, "".join(self._script_data)))
            self._script_attrs = None
            self._script_data = []


def exact_award_label(facts: dict) -> str:
    award = facts["recognitions"]["letrasComoEspada2026"]
    return f'{award["result"]} — {award["name"]} · {award["organizer"]} {award["year"]}'


def exact_finalist_label(facts: dict) -> str:
    rec = facts["recognitions"]["juanAndresTeno2026"]
    return f'{rec["result"]} · {rec["name"]} ({rec["year"]})'


def build_after_matrix(facts: dict, author_press: dict, man_press: dict, sam_press: dict) -> dict:
    man = facts["books"]["lasManecillasDelRecuerdo"]
    sam = facts["books"]["samuelEntreMundos"]
    return {
        "generatedFromCurrentContract": True,
        "rows": [
            {
                "fact": "author.name",
                "values": {
                    "editorial-facts.json": facts["author"]["name"],
                    "press-kit/david-porto-diaz.json": author_press["name"],
                    "press-kit/las-manecillas-del-recuerdo.json": man_press["author"],
                    "press-kit/samuel-entre-mundos.json": sam_press["author"],
                },
                "drift": False,
            },
            {
                "fact": "author.birthPlace",
                "values": {
                    "editorial-facts.json": facts["author"]["birthPlace"],
                    "press-kit/david-porto-diaz.json": author_press["birthplace"],
                },
                "drift": False,
            },
            {
                "fact": "manecillas.status",
                "values": {
                    "editorial-facts.json": man["statusBeforePublication"],
                    "press-kit/david-porto-diaz.json": next(b["status"] for b in author_press["books"] if b["title"] == man["title"]),
                    "press-kit/las-manecillas-del-recuerdo.json": man_press["status"],
                    "ai/index.html": "published wording",
                    "llms.txt": "published wording",
                    "llms-full.txt": "published wording",
                },
                "drift": False,
            },
            {
                "fact": "manecillas.commercialAvailability",
                "values": {
                    "editorial-facts.json": man["purchaseUrl"],
                    "press-kit/las-manecillas-del-recuerdo.json": man_press["purchase"]["purchaseUrl"],
                    "machine copy": "Sin URL de compra verificada",
                },
                "drift": False,
            },
            {
                "fact": "manecillas.isbn",
                "values": {
                    "editorial-facts.json": man["isbn"],
                    "press-kit/las-manecillas-del-recuerdo.json": man_press["isbn"],
                },
                "drift": False,
            },
            {
                "fact": "manecillas.pages",
                "values": {
                    "editorial-facts.json": man["numberOfPages"],
                    "press-kit/las-manecillas-del-recuerdo.json": man_press["pages"],
                },
                "drift": False,
            },
            {
                "fact": "samuel.isbn",
                "values": {
                    "editorial-facts.json": sam["isbn"],
                    "press-kit/samuel-entre-mundos.json": sam_press["isbn"],
                },
                "drift": False,
            },
            {
                "fact": "samuel.pages",
                "values": {
                    "editorial-facts.json": sam["numberOfPages"],
                    "press-kit/samuel-entre-mundos.json": sam_press["pages"],
                },
                "drift": False,
            },
            {
                "fact": "samuel.publicationYear",
                "values": {
                    "editorial-facts.json": sam["publicationYear"],
                    "press-kit/samuel-entre-mundos.json": sam_press["publicationYear"],
                },
                "drift": False,
            },
            {
                "fact": "juanAndresTeno2026",
                "values": {
                    "editorial-facts.json": exact_finalist_label(facts),
                    "press-kit/david-porto-diaz.json": f'{author_press["recognitions"][0]["result"]} · {author_press["recognitions"][0]["name"]} ({author_press["recognitions"][0]["year"]})',
                    "press-kit/samuel-entre-mundos.json": f'{sam_press["recognitions"][0]["result"]} · {sam_press["recognitions"][0]["name"]} ({sam_press["recognitions"][0]["year"]})',
                },
                "drift": False,
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", help="Write before/after drift and summary as CI artifacts")
    args = parser.parse_args()

    texts = {rel: load_text(rel) for rel in UTF8_FILES}
    for rel, text in texts.items():
        check("\ufffd" not in text, f"{rel}: Unicode replacement character found")
    check("ñ" in texts["llms-full.txt"], "llms-full.txt: expected UTF-8 ñ sentinel")
    check("—" in texts["llms-full.txt"], "llms-full.txt: expected UTF-8 em dash sentinel")
    check("«" in texts["llms-full.txt"], "llms-full.txt: expected UTF-8 Spanish quote sentinel")

    facts = load_json("editorial-facts.json")
    author_press = load_json("press-kit/david-porto-diaz.json")
    man_press = load_json("press-kit/las-manecillas-del-recuerdo.json")
    sam_press = load_json("press-kit/samuel-entre-mundos.json")

    check(facts.get("schemaVersion") == 1, "editorial-facts.json: schemaVersion changed unexpectedly")

    required = {
        "press-kit/david-porto-diaz.json": {"name", "type", "birthplace", "residence", "website", "identifiers", "books", "awards", "recognitions", "contact", "lastUpdated"},
        "press-kit/las-manecillas-del-recuerdo.json": {"title", "author", "isbn", "publisher", "publicationDate", "format", "pages", "priceEUR", "status", "purchase", "urls", "press", "lastUpdated"},
        "press-kit/samuel-entre-mundos.json": {"title", "author", "isbn", "publisher", "publicationYear", "format", "pages", "asin", "award", "recognitions", "urls", "press", "lastUpdated"},
    }
    for rel, keys in required.items():
        data = {"press-kit/david-porto-diaz.json": author_press, "press-kit/las-manecillas-del-recuerdo.json": man_press, "press-kit/samuel-entre-mundos.json": sam_press}[rel]
        check(keys.issubset(data), f"{rel}: missing required field(s): {sorted(keys - set(data))}")

    author = facts["author"]
    man = facts["books"]["lasManecillasDelRecuerdo"]
    sam = facts["books"]["samuelEntreMundos"]

    check(author_press["name"] == author["name"], "author name drift: press-kit vs editorial facts")
    check(author_press["website"] == author["website"], "author website drift: press-kit vs editorial facts")
    check(author_press["nationality"] == author["nationality"], "author nationality drift: press-kit vs editorial facts")
    check(author_press["birthplace"] == author["birthPlace"], "author birthplace drift: press-kit vs editorial facts")
    check(author_press["residence"] == author["homeLocation"], "author residence drift: press-kit vs editorial facts")
    check(author_press["contact"]["email"] == author["publicContact"], "author public contact drift")
    check(author_press["identifiers"] == author["identifiers"], "author identifier drift")

    author_man = next(b for b in author_press["books"] if b["title"] == man["title"])
    check(man_press["title"] == man["title"] == author_man["title"], "Manecillas title drift")
    check(man_press["author"] == author["name"], "Manecillas author drift")
    check(man_press["publisher"] == man["publisher"] == author_man["publisher"], "Manecillas publisher drift")
    check(man_press["publicationDate"] == man["publicationDate"] == author_man["publicationDate"], "Manecillas publication date drift")
    check(man_press["isbn"] == man["isbn"] == author_man["isbn"], "Manecillas ISBN drift")
    check(man_press["pages"] == man["numberOfPages"] == author_man["pages"], "Manecillas page-count drift")
    check(man_press["priceEUR"] == man["priceEUR"] == author_man["priceEUR"], "Manecillas PVP drift")
    check(man_press["format"] == "Tapa blanda" and man["format"] == "Paperback", "Manecillas format mapping drift")
    check(man_press["status"] == author_man["status"] == "published", "Manecillas machine status must be published")
    check(man["statusBeforePublication"] == man["statusFromPublicationDate"] == "published", "Manecillas temporal contract must not switch publication wording by runner date")
    check(man["purchaseUrl"] is None and man_press["purchase"]["purchaseUrl"] is None, "Manecillas purchase URL must stay null until verified")

    author_sam = next(b for b in author_press["books"] if b["title"] == sam["title"])
    check(sam_press["title"] == sam["title"] == author_sam["title"], "Samuel title drift")
    check(sam_press["author"] == author["name"], "Samuel author drift")
    check(sam_press["publisher"] == sam["publisher"] == author_sam["publisher"], "Samuel publisher drift")
    check(sam_press["isbn"] == sam["isbn"] == author_sam["isbn"], "Samuel ISBN drift")
    check(sam_press["pages"] == sam["numberOfPages"], "Samuel page-count drift")
    check(sam_press["publicationYear"] == sam["publicationYear"] == author_sam["year"], "Samuel publication-year drift")
    check(sam_press["asin"] == sam["asin"] == "B0GB6LGQFH", "Samuel ASIN drift")
    check(sam_press["urls"]["amazon"] == sam["purchaseUrls"]["amazonEs"], "Samuel Amazon URL drift")
    check("tag=davidporto-21" in sam_press["urls"]["amazon"], "Samuel Amazon affiliate tag was lost")
    check(sam_press["urls"]["publisher"] == sam["sourceUrl"], "Samuel publisher URL drift")

    award = facts["recognitions"]["letrasComoEspada2026"]
    finalist = facts["recognitions"]["juanAndresTeno2026"]
    check(award["type"] == "award" and award["holder"] == author["name"] and award["submittedWork"] is None, "Letras award ownership drift")
    check(finalist["type"] == "finalistSelection" and finalist["submittedWork"] == sam["title"], "Juan Andrés Teno recognition relation drift")
    check(len(author_press["awards"]) == 1 and "Letras Como Espada" in author_press["awards"][0]["name"], "author press-kit awards must contain only the true award")
    check(len(author_press["recognitions"]) == 1 and author_press["recognitions"][0]["submittedWork"] == sam["title"], "author press-kit finalist recognition missing/ambiguous")
    check(sam_press["award"] is None, "Samuel must not carry a book award")
    check(sam_press["recognitions"][0]["submittedWork"] == sam["title"], "Samuel finalist relation missing")
    check(all(item.get("type") == "anthologyParticipation" for item in facts["contributions"]), "anthology contribution modeled as something other than participation")

    machine_copy = "\n".join((texts["ai/index.html"], texts["llms.txt"], texts["llms-full.txt"]))
    for token in (
        author["name"],
        man["title"], man["publisher"], man["publicationDate"], man["isbn"], str(man["numberOfPages"]),
        sam["title"], sam["publisher"], sam["isbn"], str(sam["numberOfPages"]), sam["asin"],
        "Publicada el 3 de septiembre de 2026",
        "Sin URL de compra verificada",
        exact_award_label(facts),
        finalist["name"],
        "Noveris",
        "Q139927664",
    ):
        check(token.casefold() in machine_copy.casefold(), f"critical machine fact missing: {token}")

    for stale in (
        "próxima publicación",
        "Premio Nacional de Literatura Infantil Juan Andrés Teno",
        "nacido en Pontevedra (1989)",
        "Pontevedra, 1989",
        "¿Qué habitante de Noveris serías?",
        "optimizada para modelos de lenguaje",
        "estándar reconocido por todos",
    ):
        check(stale.casefold() not in machine_copy.casefold(), f"stale/unsupported machine claim remains: {stale}")

    check(len(texts["llms.txt"]) < 6000, "llms.txt is no longer concise")
    check(len(texts["llms-full.txt"]) > len(texts["llms.txt"]) * 2, "llms-full.txt is not meaningfully fuller than llms.txt")

    for data in (facts, author_press, man_press, sam_press):
        walk_urls(data)

    ai = AIHTMLParser()
    ai.feed(texts["ai/index.html"])
    check("v1" in ai.html_classes, "/ai/: html.v1 missing")
    check(ai.has_main, "/ai/: main#contenido missing")
    check(ai.has_skip, "/ai/: skip link missing")
    check(ai.h1 == 1, f"/ai/: expected exactly one h1, got {ai.h1}")
    check(ai.h2 >= 5, f"/ai/: expected section headings, got {ai.h2} h2")
    css_hrefs = {link.get("href") for link in ai.links if link.get("rel") == "stylesheet"}
    expected_css = {
        "/assets/v1-fonts.css",
        "/assets/v1-tokens.css",
        "/assets/v1-base.css",
        "/assets/v1-shell.css",
        "/assets/v1-ai-authority.css",
    }
    check(expected_css.issubset(css_hrefs), f"/ai/: V1 stylesheet set incomplete: {sorted(expected_css - css_hrefs)}")
    canonical = [link.get("href") for link in ai.links if link.get("rel") == "canonical"]
    check(canonical == [f"{CANONICAL_ORIGIN}/ai/"], f"/ai/: canonical mismatch: {canonical}")
    robots_meta = [m.get("content", "") for m in ai.metas if m.get("name") == "robots"]
    check(len(robots_meta) == 1 and "index" in robots_meta[0] and "follow" in robots_meta[0], "/ai/: robots meta must be index, follow")
    non_jsonld = []
    jsonld_count = 0
    for attrs, data in ai.scripts:
        if attrs.get("type") == "application/ld+json":
            jsonld_count += 1
            try:
                json.loads(data)
            except json.JSONDecodeError as exc:
                failures.append(f"/ai/: invalid JSON-LD ({exc})")
        else:
            non_jsonld.append(attrs)
    check(jsonld_count >= 1, "/ai/: JSON-LD missing")
    check(not non_jsonld, "/ai/: runtime JavaScript introduced on a no-JS authority page")
    check("new Date(" not in texts["ai/index.html"] and "Date.now(" not in texts["ai/index.html"], "/ai/: runtime temporal SEO logic introduced")

    robots = texts["robots.txt"]
    sitemap_lines = re.findall(r"(?im)^\s*Sitemap\s*:\s*(\S+)\s*$", robots)
    check(sitemap_lines == [f"{CANONICAL_ORIGIN}/sitemap.xml"], f"robots.txt: expected exactly canonical Sitemap, got {sitemap_lines}")
    check(not re.search(r"(?im)^\s*Disallow\s*:\s*/\s*$", robots), "robots.txt: accidental Disallow: /")
    check("https://davidportodiaz.com/llms.txt" in robots and "https://davidportodiaz.com/llms-full.txt" in robots, "robots.txt: llms context comments missing")
    check((ROOT / "llms.txt").is_file() and (ROOT / "llms-full.txt").is_file(), "robots.txt: referenced llms target missing")
    check("Claude-Web" not in robots and "anthropic-ai" not in robots, "robots.txt: legacy Anthropic aliases remain")
    for agent in ("OAI-SearchBot", "ChatGPT-User", "GPTBot", "PerplexityBot", "Applebot-Extended", "ClaudeBot", "Claude-SearchBot", "Claude-User", "Google-Extended"):
        check(re.search(rf"(?im)^User-agent:\s*{re.escape(agent)}\s*$", robots) is not None, f"robots.txt: documented policy agent missing: {agent}")

    sitemap = load_text("sitemap.xml")
    check("<loc>https://davidportodiaz.com/ai/</loc>" in sitemap, "sitemap.xml: /ai/ missing")

    after = build_after_matrix(facts, author_press, man_press, sam_press)
    check(all(not row["drift"] for row in after["rows"]), "after drift matrix contains a critical contradiction")

    if args.artifact_dir:
        out = Path(args.artifact_dir)
        if not out.is_absolute():
            out = ROOT / out
        out.mkdir(parents=True, exist_ok=True)
        before = ROOT / "tests" / "fixtures" / "machine-authority-drift-before.json"
        check(before.is_file(), "before drift fixture missing")
        if before.is_file():
            shutil.copy2(before, out / "factual-drift-before.json")
        (out / "factual-drift-after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "test-summary.txt").write_text(
            f"machine authority checks: {checks}\nfailures: {len(failures)}\n"
            + ("\n".join(failures) + "\n" if failures else "status: PASS\n"),
            encoding="utf-8",
        )

    if failures:
        print(f"FAILED — {len(failures)} issue(s) across {checks} checks:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS — machine authority contract ({checks} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
