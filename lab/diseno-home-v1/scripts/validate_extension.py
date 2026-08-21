#!/usr/bin/env python3
"""Static contract validator for the V1 author-site extension.
Stdlib only. It validates design coverage and guardrails; it is NOT browser QA.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "5c4a9afca7c009bd78d5dd44ca4b6c656239527c"
EXPECTED_SITEMAP = 55
EXPECTED_TOTAL = 59
EXTENSION_HTML = {
    "author.html", "awards.html", "book-companion.html", "book-excerpt.html",
    "book-samuel.html", "book-jaula.html", "books-index.html", "events.html", "press.html",
    "reference-detail.html", "reference-index.html", "secondary.html",
    "tool-pilot.html", "tools-hub.html", "wayfinding.html",
}
BASE_SCAFFOLDS = {"index.html", "book-manecillas.html", "cuaderno.html", "article-pilot.html"}
REQUIRED = {
    "README.md", "CLAUDE-HANDOFF.md", "REFERENCIAS-HUMANAS.md",
    "ROUTE-INVENTORY.md", "SIGNATURE-SYSTEM.md", "THIRD-PARTY-NOTICES.md",
    "css/families.css", "css/scaffold.css", "css/secondary.css", "css/signatures.css",
    "css/tools.css", "css/samuel.css", "css/awards.css",
    "js/extension.js", "js/signatures.js",
    "data/branch-baseline.json", "data/reference-catalog.json", "data/route-inventory.json",
    "data/samuel-preservation.json", "data/jaula-preservation.json", "data/awards-preservation.json",
    "scripts/validate_extension.py", "scripts/check_preservation.py",
} | EXTENSION_HTML

GENERIC_CLASS = re.compile(r"(?:^|[-_])(card|badge|pill|bento|glass)(?:$|[-_])", re.I)
FORBIDDEN_CSS = [
    r"backdrop-filter", r"linear-gradient\s*\(", r"radial-gradient\s*\(",
    r"filter\s*:\s*blur\s*\(", r"repeat\s*\(\s*auto-(?:fit|fill)",
]
FORBIDDEN_RUNTIME = [r"\bgsap\b", r"\blenis\b", r"\bthree(?:\.js)?\b", r"custom[-_]cursor", r"magnetic"]
FORBIDDEN_JS = [r"\beval\s*\(", r"new\s+Function\s*\(", r"\bfetch\s*\(", r"XMLHttpRequest", r"WebSocket\s*\("]

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


class AuditHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.h1 = 0
        self.dialogs = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "h1": self.h1 += 1
        if tag == "dialog": self.dialogs += 1
        if data.get("id"): self.ids.append(data["id"] or "")
        if "href" in data and not (data.get("href") or "").strip(): fail("empty href")
        if "style" in data: fail("inline style attribute")
        for name, _ in attrs:
            if name.lower().startswith("on"): fail(f"inline event handler: {name}")
        classes = (data.get("class") or "").split()
        for cls in classes:
            if GENERIC_CLASS.search(cls): fail(f"generic class name: {cls}")


# 1. Required file set
for rel in sorted(REQUIRED):
    if not (ROOT / rel).is_file(): fail(f"missing required file: {rel}")

# 2. HTML structural contracts
for name in sorted(EXTENSION_HTML):
    path = ROOT / name
    if not path.exists(): continue
    text = path.read_text(encoding="utf-8")
    parser = AuditHTML()
    before = len(errors)
    try: parser.feed(text)
    except Exception as exc: fail(f"{name}: HTML parser error: {exc}")
    if parser.h1 != 1: fail(f"{name}: expected one h1, found {parser.h1}")
    duplicates = sorted({x for x in parser.ids if parser.ids.count(x) > 1})
    if duplicates: fail(f"{name}: duplicate ids: {duplicates}")
    robots = re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)', text, re.I)
    if not robots or "noindex" not in robots.group(1).lower(): fail(f"{name}: lab must be noindex")
    if re.search(r'href=["\']/styles\.css', text) or re.search(r'src=["\']/script\.js', text):
        fail(f"{name}: imports production global CSS/JS")
    if "https://fonts.googleapis.com" in text or "https://fonts.gstatic.com" in text:
        fail(f"{name}: external font dependency in HTML")
    if len(errors) > before:
        # Prefix parser-origin errors that do not yet have the file name.
        for i in range(before, len(errors)):
            if not errors[i].startswith(name + ":"):
                errors[i] = f"{name}: {errors[i]}"

# 3. Anti-generic checks apply only to this extension's CSS.
# Base CSS has its own validator and intentionally owns palette tokens / the controlled Home A-B variant.
EXTENSION_CSS = {
    "families.css", "scaffold.css", "secondary.css", "signatures.css",
    "tools.css", "samuel.css", "awards.css",
}
for name in sorted(EXTENSION_CSS):
    path = ROOT / "css" / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_CSS + FORBIDDEN_RUNTIME:
        if re.search(pattern, text, re.I): fail(f"{path.name}: forbidden pattern /{pattern}/")
    # Extension CSS owns no palette; it consumes shared semantic tokens.
    if re.search(r"#[0-9a-f]{3,8}\b", text, re.I): fail(f"{path.name}: raw hex color outside token layer")

# 4. JS enhancement-only checks apply only to extension modules.
EXTENSION_JS = {"extension.js", "signatures.js"}
for name in sorted(EXTENSION_JS):
    path = ROOT / "js" / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_RUNTIME + FORBIDDEN_JS:
        if re.search(pattern, text, re.I): fail(f"{path.name}: forbidden runtime/network pattern /{pattern}/")

# 5. Route coverage
routes_path = ROOT / "data/route-inventory.json"
if routes_path.exists():
    data = json.loads(routes_path.read_text(encoding="utf-8"))
    routes = data.get("routes", [])
    if data.get("baselineHead") != EXPECTED_HEAD: fail("route inventory baseline HEAD drift")
    if data.get("sitemapRouteCount") != EXPECTED_SITEMAP: fail("route inventory declared sitemap count != 55")
    if len(routes) != EXPECTED_TOTAL: fail(f"route inventory expected {EXPECTED_TOTAL} entries, found {len(routes)}")
    sitemap = [r for r in routes if r.get("inSitemap")]
    if len(sitemap) != EXPECTED_SITEMAP: fail(f"expected 55 in-sitemap routes, found {len(sitemap)}")
    paths = [r.get("path") for r in routes]
    if len(paths) != len(set(paths)): fail("duplicate route paths")
    for must in ("/404.html", "/privacidad.html", "/aviso-legal.html"):
        match = next((r for r in routes if r.get("path") == must), None)
        if not match or match.get("inSitemap"): fail(f"missing/invalid off-sitemap operational route {must}")
    jaula = next((r for r in routes if r.get("path") == "/donde-empieza-la-jaula/"), None)
    if not jaula or jaula.get("scaffold") != "book-jaula.html" or jaula.get("status") != "AUTHORIZED_FOR_STAGING" or jaula.get("productionAllowed") is not False:
        fail("Jaula must be authorized for staging with book-jaula.html and remain production-blocked")
    for r in routes:
        if r.get("designStatus") != "IMPLEMENT_READY":
            fail(f"route missing IMPLEMENT_READY design status: {r.get('path')}")
    for r in sitemap:
        sc = r.get("scaffold")
        if not sc: fail(f"sitemap route without scaffold: {r.get('path')}")
        elif sc not in EXTENSION_HTML | BASE_SCAFFOLDS: fail(f"unknown scaffold {sc} for {r.get('path')}")
    samuel = next((r for r in routes if r.get("path") == "/libros/samuel-entre-mundos/"), {})
    awards = next((r for r in routes if r.get("path") == "/premios.html"), {})
    if samuel.get("scaffold") != "book-samuel.html": fail("Samuel must map to book-samuel.html")
    if awards.get("scaffold") != "awards.html": fail("Premios must map to awards.html")

# 6. Baseline contract
bp = ROOT / "data/branch-baseline.json"
if bp.exists():
    b = json.loads(bp.read_text(encoding="utf-8"))
    if b.get("auditedHead") != EXPECTED_HEAD: fail("branch baseline HEAD mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", b.get("auditedHead", "")): fail("invalid audited HEAD")
    facts = b.get("knownFacts", {})
    if facts.get("sitemapRouteCount") != 55 or facts.get("toolCountDeclaredByHub") != 17: fail("baseline route/tool facts mismatch")
    if facts.get("jaulaPublicRouteExists") is not False: fail("baseline incorrectly marks Jaula live")
    if facts.get("generatedWriterToolsHaveBuilderContract") is not True: fail("writer-tools builder contract missing")

# 7. Preservation contracts
sp = ROOT / "data/samuel-preservation.json"
if sp.exists():
    s = json.loads(sp.read_text(encoding="utf-8"))
    facts = s.get("preserve", {}).get("facts", {})
    if facts.get("isbn") != "9791387659776" or facts.get("pages") != 422 or facts.get("year") != 2025: fail("Samuel fixed bibliographic facts mismatch")
    anchors = set(s.get("preserve", {}).get("anchors", []))
    expected = {"sinopsis-tecnica","para-quien","ficha","clubes-bibliotecas","mecanica","validacion-social","comprar","ejemplar-firmado","para-quien-detalle","por-que-empieza","noveris-intro","quiz-noveris","faq"}
    if not expected.issubset(anchors): fail("Samuel preservation anchors incomplete")

# Jaula content/preservation contract: authorized for staging but not yet live in branch.
jp = ROOT / "data/jaula-preservation.json"
if jp.exists():
    j = json.loads(jp.read_text(encoding="utf-8"))
    if j.get("route") != "/donde-empieza-la-jaula/" or j.get("status") != "AUTHORIZED_FOR_STAGING" or j.get("productionAllowed") is not False:
        fail("Jaula preservation route/status contract mismatch")
    src = j.get("source", {})
    ch = j.get("chapter1", {})
    if src.get("driveId") != "1bfo_20JoPw3W_oHK8k-G1rd3v-K1Jfvx": fail("Jaula source Drive id mismatch")
    if src.get("chapterStartHeading") != "CAPÍTULO 1" or src.get("chapterEndExclusiveHeading") != "CAPÍTULO 2": fail("Jaula chapter boundary contract mismatch")
    if ch.get("paragraphCount") != 133 or ch.get("wordCount") != 2158: fail("Jaula chapter 1 count contract drift")
    page = (ROOT / "book-jaula.html").read_text(encoding="utf-8") if (ROOT / "book-jaula.html").exists() else ""
    sha = ch.get("sha256", "")
    if not sha or f'data-source-chapter-sha256="{sha}"' not in page: fail("Jaula page missing chapter source hash marker")
    if ch.get("firstParagraph", "") not in page or ch.get("lastParagraph", "") not in page: fail("Jaula page first/last chapter paragraph drift")
    for forbidden in ("ISBN", "Editorial</dt>", "PVP", "Comprar", "publicationDate"):
        if forbidden in page: fail(f"Jaula scaffold contains forbidden publication metadata/action: {forbidden}")
    html = (ROOT / "book-samuel.html").read_text(encoding="utf-8") if (ROOT/"book-samuel.html").exists() else ""
    for anchor in expected:
        if f'id="{anchor}"' not in html: fail(f"Samuel scaffold missing anchor #{anchor}")

ap = ROOT / "data/awards-preservation.json"
if ap.exists():
    a = json.loads(ap.read_text(encoding="utf-8"))
    p = a.get("preserve", {})
    if len(p.get("formalDistinctions", [])) != 2: fail("Awards must identify exactly two formal winner/finalist distinctions in current visible contract")
    if not p.get("editorialSelection") or not p.get("trajectoryNotAwards"): fail("Awards semantic separation incomplete")

# 7b. Jaula preservation must be executable, not just documented.
checker = (ROOT / "scripts/check_preservation.py").read_text(encoding="utf-8") if (ROOT / "scripts/check_preservation.py").exists() else ""
for required in ("--jaula", "data/jaula-preservation.json", "chapter SHA-256 mismatch", "robots must contain"):
    if required not in checker: fail(f"Jaula executable preservation gate missing marker: {required}")

# 8. Human-reference provenance
rp = ROOT / "data/reference-catalog.json"
if rp.exists():
    refs = json.loads(rp.read_text(encoding="utf-8")).get("references", [])
    if len(refs) < 10: fail("reference catalog too small for current research pass")
    for ref in refs:
        for field in ("id", "kind", "title", "url", "transfer", "reject"):
            if not str(ref.get(field, "")).strip(): fail(f"reference {ref.get('id','?')} missing {field}")
        if "mit" in ref.get("kind", "").lower() and ref.get("license") != "MIT": fail(f"MIT reference {ref.get('id')} missing license")

# 9. Handoff status is explicit
hp = ROOT / "CLAUDE-HANDOFF.md"
if hp.exists():
    text = hp.read_text(encoding="utf-8")
    required_markers = [
        "`CLAUDE_IMPLEMENT_READY`: **YES_FOR_STAGING_IMPLEMENTATION**",
        "`MERGE_READY`: **NO**",
        "`PRODUCTION_READY`: **NO**",
        EXPECTED_HEAD,
        "main`: NO TOCAR",
    ]
    for marker in required_markers:
        if marker not in text: fail(f"handoff missing marker: {marker}")

if errors:
    print("EXTENSION VALIDATION: FAIL")
    for e in errors: print(f"- {e}")
    sys.exit(1)

print("EXTENSION VALIDATION: OK")
print(f"- extension HTML scaffolds: {len(EXTENSION_HTML)}")
print(f"- route inventory: {EXPECTED_SITEMAP} sitemap + 3 operational + 1 staging-authorized/off-sitemap = {EXPECTED_TOTAL}")
print("- Samuel and Premios use dedicated families/preservation contracts")
print("- no generic tile/pill/glass/gradient/runtime-library patterns in extension")
print("- human reference provenance complete")
print(f"- audited branch HEAD: {EXPECTED_HEAD}")
print("NOTE: static validation only; visual/browser QA remains required before merge.")
