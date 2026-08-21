#!/usr/bin/env python3
"""Static contract checks for the isolated Home V1 lab. Standard library only."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "index.html", "components.html", "book-manecillas.html", "cuaderno.html", "article-pilot.html", "README.md", "INTEGRATION.md", "BRANCH-AUDIT.md", "MIGRATION-MATRIX.md", "MANECILLAS-MIGRATION.md", "EDITORIAL-MIGRATION.md", "IMPLEMENTATION-READINESS.md", "QA.md",
    "CLAUDE-HANDOFF.md", "REFERENCIAS-HUMANAS.md", "ROUTE-INVENTORY.md", "SIGNATURE-SYSTEM.md", "THIRD-PARTY-NOTICES.md",
    "author.html", "awards.html", "book-samuel.html", "book-jaula.html", "books-index.html", "events.html", "press.html", "tools-hub.html", "tool-pilot.html",
    "css/fonts-lab.css", "css/tokens.css", "css/base.css", "css/shell.css", "css/home.css", "css/book.css", "css/editorial.css", "css/variants.css", "css/components.css",
    "css/scaffold.css", "css/signatures.css", "css/families.css", "css/tools.css", "css/secondary.css", "css/samuel.css", "css/awards.css",
    "js/lab.js", "js/fixtures.js", "js/book-fixtures.js", "js/editorial.js", "js/extension.js", "js/signatures.js",
    "scripts/check_preservation.py", "scripts/validate_extension.py",
    "data/media-manifest.json", "data/font-contract.json", "data/routes.json", "data/migration-map.json", "data/manecillas-preservation.json", "data/home-preservation.json", "data/cuaderno-preservation.json", "data/article-preservation.json",
    "data/branch-baseline.json", "data/reference-catalog.json", "data/route-inventory.json", "data/samuel-preservation.json", "data/jaula-preservation.json", "data/awards-preservation.json",
]

FORBIDDEN_HISTORIC_HEX = {"#17120B", "#F4EBDD", "#C27937", "#6E8EC5"}
FORBIDDEN_PATTERNS = [
    "three.js", "lenis", "gsap", "custom cursor", "scroll-jacking", "magnetic",
]
FORBIDDEN_PRODUCTION_IMPORTS = {"/styles.css", "styles.css", "/assets/manecillas-extras.css", "assets/manecillas-extras.css"}
FORBIDDEN_DUPLICATE_ASSET_PREFIX = "/assets/las-manecillas/"
EXPECTED_TARGET_BRANCH = "implementacion-web-2026"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
HEAD_POLICY_MARKER = "Baseline informativa"


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.dialogs = 0
        self.h1 = 0
        self.inline_handlers: list[str] = []
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.meta_robots: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.append(data["id"])
        if tag == "a":
            self.hrefs.append(data.get("href", ""))
        if tag == "dialog":
            self.dialogs += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and data.get("rel") == "stylesheet":
            self.stylesheets.append(data.get("href", ""))
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag == "meta" and data.get("name") == "robots":
            self.meta_robots.append(data.get("content", ""))
        for key in data:
            if key.startswith("on"):
                self.inline_handlers.append(key)


def parse_html(path: Path) -> AuditParser:
    parser = AuditParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing required file: {rel}")

    for rel in ("index.html", "components.html", "book-manecillas.html", "book-jaula.html", "cuaderno.html", "article-pilot.html"):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        parser = parse_html(path)
        dup = sorted({i for i in parser.ids if parser.ids.count(i) > 1})
        if dup:
            fail(errors, f"{rel}: duplicate ids: {dup}")
        if any(not href.strip() for href in parser.hrefs):
            fail(errors, f"{rel}: empty href")
        if parser.h1 != 1:
            fail(errors, f"{rel}: expected exactly one h1, got {parser.h1}")
        if parser.inline_handlers:
            fail(errors, f"{rel}: inline event handlers: {parser.inline_handlers}")
        if not any("noindex" in x for x in parser.meta_robots):
            fail(errors, f"{rel}: missing noindex robots meta")
        if any(x in FORBIDDEN_PRODUCTION_IMPORTS for x in parser.stylesheets):
            fail(errors, f"{rel}: imports production/historic stylesheet")
        if any(x in {"/script.js", "script.js"} for x in parser.scripts):
            fail(errors, f"{rel}: imports production script.js")
        if FORBIDDEN_DUPLICATE_ASSET_PREFIX in text:
            fail(errors, f"{rel}: uses duplicate asset hierarchy {FORBIDDEN_DUPLICATE_ASSET_PREFIX}")

    home = parse_html(ROOT / "index.html") if (ROOT / "index.html").exists() else None
    if home and home.dialogs != 1:
        fail(errors, f"index.html: expected one native dialog, got {home.dialogs}")
    components_path = ROOT / "components.html"
    if components_path.exists():
        components_text = components_path.read_text(encoding="utf-8")
        for required_form_primitive in ("form-field-label", "form-row", "form-input", "form-submit", "form-consent", "form-status"):
            if required_form_primitive not in components_text:
                fail(errors, f"components.html: Gate 0 must exercise shared form primitive {required_form_primitive}")
        for legacy_specimen_form in ("field-row", "field-help", "privacy-copy"):
            if legacy_specimen_form in components_text:
                fail(errors, f"components.html: obsolete specimen-only form class present: {legacy_specimen_form}")
    book_path = ROOT / "book-manecillas.html"
    if book_path.exists():
        book_text = book_path.read_text(encoding="utf-8")
        book = parse_html(book_path)
        if book.dialogs != 1:
            fail(errors, f"book-manecillas.html: expected one native dialog, got {book.dialogs}")
        for required in (
            "book-meta-ledger",
            'id="sinopsis"',
            'id="fragmento"',
            'id="disponibilidad"',
            'id="relacionado"',
            "/assets/portada-las-manecillas-del-recuerdo-1024.webp",
            "newsletter-form-manecillas",
            'data-newsletter-source="manecillas"',
            'data-book-meta="genero"',
            "Novela coral · Ficción especulativa",
        ):
            if required not in book_text:
                fail(errors, f"book-manecillas.html: missing Book V1 contract {required}")
        for forbidden in ("manecillas-book-mockup.webp", "manecillas-extras.css", "manecillas-theme-card", "feature-card"):
            if forbidden in book_text:
                fail(errors, f"book-manecillas.html: legacy Manecillas pattern present: {forbidden}")
        for fixture_hook in ("data-book-meta", "data-book-related", "data-book-title", "book-fixtures.js"):
            if fixture_hook not in book_text:
                fail(errors, f"book-manecillas.html: missing resilience hook {fixture_hook}")

    for css in (ROOT / "css").glob("*.css"):
        text = css.read_text(encoding="utf-8")
        if text.count("{") != text.count("}"):
            fail(errors, f"{css.relative_to(ROOT)}: unbalanced braces")
        if css.name != "fonts-lab.css":
            hits = sorted(h for h in FORBIDDEN_HISTORIC_HEX if h.lower() in text.lower())
            if hits:
                fail(errors, f"{css.relative_to(ROOT)}: historic hex values present: {hits}")
        lower = text.lower()
        for item in FORBIDDEN_PATTERNS:
            if item in lower:
                fail(errors, f"{css.relative_to(ROOT)}: forbidden pattern '{item}'")

    # Raw color literals belong in tokens.css only; page/component CSS consumes semantic tokens.
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    for css in (ROOT / "css").glob("*.css"):
        if css.name in {"tokens.css", "fonts-lab.css"}:
            continue
        literals = sorted(set(hex_pattern.findall(css.read_text(encoding="utf-8"))))
        if literals:
            fail(errors, f"{css.relative_to(ROOT)}: local hex colors forbidden outside tokens.css: {literals}")

    manifest = ROOT / "data/media-manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"media-manifest.json invalid: {exc}")
        else:
            if data.get("schema_version") != 2:
                fail(errors, "media-manifest.json: expected schema_version 2")
            if data.get("targetBranch") != EXPECTED_TARGET_BRANCH:
                fail(errors, f"media-manifest.json: targetBranch must be {EXPECTED_TARGET_BRANCH}")
            if not SHA40_RE.match(str(data.get("lastAuditedHead", ""))):
                fail(errors, "media-manifest.json: lastAuditedHead must be a 40-hex informational baseline")
            if HEAD_POLICY_MARKER not in str(data.get("headPolicy", "")):
                fail(errors, "media-manifest.json: missing non-rigid branch drift policy")
            assets = data.get("assets", [])
            raw = json.dumps(data, ensure_ascii=False)
            for width in (320, 512, 768, 1024):
                expected = f"/assets/portada-las-manecillas-del-recuerdo-{width}.webp"
                if expected not in raw:
                    fail(errors, f"media manifest: missing repo target {expected}")
            if FORBIDDEN_DUPLICATE_ASSET_PREFIX in raw:
                fail(errors, "media manifest: duplicate /assets/las-manecillas/ target hierarchy is forbidden")
            if sum(1 for a in assets if a.get("repo_verified_target_branch")) < 5:
                fail(errors, "media manifest: expected verified cover variants + portrait candidate")
            portraits = [a for a in assets if a.get("id") == "author-portrait-current"]
            if len(portraits) != 1:
                fail(errors, "media manifest: expected exactly one author-portrait-current entry")
            else:
                portrait = portraits[0]
                expected_portrait = {
                    "source_drive_file_id": "1Tb4HxsMokS-eiW4Dqr9pwhxlquV1Qxc9",
                    "lab_drive_file_id": "1EkUZKUv1r7xx9ZNS6abtTqfW-sh-1Nr_",
                    "repo_path": "/assets/david-porto-foto-portada-sinfondo.webp",
                    "lab_path": "/assets/david-porto-foto-portada-sinfondo.webp",
                    "intrinsic_width": 433,
                    "intrinsic_height": 577,
                    "alpha": True,
                    "resolution_gate": "pass-no-destructive-upscale",
                    "required_for_home_ab_gate": True,
                    "required_for_gate_0": False,
                }
                for key, value in expected_portrait.items():
                    if portrait.get(key) != value:
                        fail(errors, f"media manifest portrait: {key} must be {value!r}")
                if portrait.get("display_max_width_css_px", 9999) > portrait.get("intrinsic_width", 0):
                    fail(errors, "media manifest portrait: declared max CSS width would upscale the selected raster")
                if len(portrait.get("alternatives_reviewed", [])) < 3:
                    fail(errors, "media manifest portrait: real alternative review must remain documented")
                if portrait.get("bytes", 999999) > 15000:
                    fail(errors, "media manifest portrait: selected transparent portrait exceeds 15 KB lab budget")
            budgets = data.get("performance_budget", {})
            if budgets.get("selected_home_media_estimate_bytes_at_1440", 9999999) > budgets.get("home_above_fold_media_bytes_max", 0):
                fail(errors, "media manifest: Home above-fold media estimate exceeds declared budget")
            for width, ceiling in ((320,45000),(512,100000),(768,190000),(1024,280000)):
                item = next((a for a in assets if a.get("id") == f"manecillas-cover-{width}"), None)
                if not item or item.get("bytes", ceiling+1) > ceiling:
                    fail(errors, f"media manifest: cover {width} exceeds performance budget")
                if item and item.get("aspect_ratio") != "2:3":
                    fail(errors, f"media manifest: cover {width} must preserve 2:3 ratio")

    font_contract = ROOT / "data/font-contract.json"
    if font_contract.exists():
        try:
            fonts = json.loads(font_contract.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"font-contract.json invalid: {exc}")
        else:
            if fonts.get("schema_version") != 1:
                fail(errors, "font-contract.json: expected schema_version 1")
            if fonts.get("production", {}).get("remote_google_fonts_import_allowed") is not False:
                fail(errors, "font-contract.json: production remote font import must be forbidden")
            if fonts.get("production", {}).get("delivery") != "self-host":
                fail(errors, "font-contract.json: production delivery must be self-host")
            by_family = {f.get("family"): f for f in fonts.get("families", [])}
            for family in ("Instrument Serif", "Manrope", "Newsreader"):
                if family not in by_family:
                    fail(errors, f"font-contract.json: missing family {family}")
            if by_family.get("Instrument Serif", {}).get("allowed_weights") != [400]:
                fail(errors, "font-contract.json: Instrument Serif must remain 400 only")
            if by_family.get("Manrope", {}).get("allowed_weights") != [400, 500, 600, 700]:
                fail(errors, "font-contract.json: Manrope allowed weights drift")
            if "italic-400" not in by_family.get("Newsreader", {}).get("allowed_styles", []):
                fail(errors, "font-contract.json: Newsreader real 400 italic is required")

    fonts_lab = ROOT / "css/fonts-lab.css"
    if fonts_lab.exists():
        raw_fonts = fonts_lab.read_text(encoding="utf-8")
        for marker in ("LAB ONLY", "Instrument+Serif:ital@0;1", "Manrope:wght@400;500;600;700", "Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400"):
            if marker not in raw_fonts:
                fail(errors, f"fonts-lab.css: missing exact prototype marker {marker}")
        if "fonts.googleapis.com" not in raw_fonts:
            fail(errors, "fonts-lab.css: isolated lab import missing")
    for css in (ROOT / "css").glob("*.css"):
        if css.name != "fonts-lab.css" and "fonts.googleapis.com" in css.read_text(encoding="utf-8"):
            fail(errors, f"{css.relative_to(ROOT)}: remote font import is allowed only in fonts-lab.css")

    routes_path = ROOT / "data/routes.json"
    if routes_path.exists():
        try:
            routes = json.loads(routes_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"routes.json invalid: {exc}")
        else:
            if routes.get("schema_version") != 2:
                fail(errors, "routes.json: expected schema_version 2")
            if routes.get("targetBranch") != EXPECTED_TARGET_BRANCH:
                fail(errors, f"routes.json: targetBranch must be {EXPECTED_TARGET_BRANCH}")
            if not SHA40_RE.match(str(routes.get("targetHeadVerified", ""))):
                fail(errors, "routes.json: targetHeadVerified must be a 40-hex informational baseline")
            if HEAD_POLICY_MARKER not in str(routes.get("headPolicy", "")):
                fail(errors, "routes.json: missing branch drift policy")
            territories = routes.get("territories", [])
            if len(territories) != 7:
                fail(errors, f"routes.json: expected 7 territories, got {len(territories)}")
            by_id = {r.get("id"): r for r in territories}
            tools = by_id.get("herramientas", {})
            if not tools.get("targetBranchAvailable") or tools.get("promotionBlocked"):
                fail(errors, "routes.json: Herramientas must be verified in target branch and not promotion-blocking")
            if tools.get("status") != "verified-target-branch":
                fail(errors, "routes.json: Herramientas status must be verified-target-branch")
            jaula = by_id.get("jaula", {})
            if jaula.get("targetBranchAvailable") or not jaula.get("promotionBlocked"):
                fail(errors, "routes.json: Jaula target route must remain promotion-blocking until a real branch route exists")
            if jaula.get("status") != "content-authorized-route-pending":
                fail(errors, "routes.json: Jaula must record authorized content while target route is pending")
            blocked_hrefs = {r.get("href") for r in territories if r.get("promotionBlocked")}
            for rel in ("index.html", "book-manecillas.html"):
                page = ROOT / rel
                if not page.exists():
                    continue
                page_text = page.read_text(encoding="utf-8")
                if 'data-route-planned="true"' not in page_text or "Dónde empieza la jaula" not in page_text:
                    fail(errors, f"{rel}: Jaula must remain visible as an explicit planned editorial state")
                if re.search(r'<a\b[^>]*data-route-planned=["\']true["\']', page_text, re.I):
                    fail(errors, f"{rel}: planned routes must be semantically non-interactive, never guarded anchors")
                for href in blocked_hrefs:
                    if href and f'href="{href}"' in page_text:
                        fail(errors, f"{rel}: blocked route must not expose a live href in lab: {href}")

    migration_path = ROOT / "data/migration-map.json"
    if migration_path.exists():
        try:
            migration = json.loads(migration_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"migration-map.json invalid: {exc}")
        else:
            if migration.get("schema_version") != 1:
                fail(errors, "migration-map.json: expected schema_version 1")
            if migration.get("target_branch") != EXPECTED_TARGET_BRANCH:
                fail(errors, f"migration-map.json: target_branch must be {EXPECTED_TARGET_BRANCH}")
            if not SHA40_RE.match(str(migration.get("target_head_verified", ""))):
                fail(errors, "migration-map.json: target_head_verified must be a 40-hex informational baseline")
            if HEAD_POLICY_MARKER not in str(migration.get("head_policy", "")):
                fail(errors, "migration-map.json: missing branch drift policy")
            mappings = migration.get("mappings", [])
            if len(mappings) < 18:
                fail(errors, f"migration-map.json: expected at least 18 mappings, got {len(mappings)}")
            raw_migration = json.dumps(migration, ensure_ascii=False)
            for required_contract in (
                "GLOBAL EXPLORE MENU IIFE",
                "mobile-bottom-nav IIFE",
                "newsletter-form-home",
                "sourceLabel='home'",
                "sourceLabel='manecillas'",
                "pending-verified-retailer-urls",
                "/assets/manecillas-extras.css",
                "/donde-empieza-la-jaula/",
            ):
                if required_contract not in raw_migration:
                    fail(errors, f"migration-map.json: missing migration contract {required_contract}")

    # Jaula source contract: real chapter 1 is present in the noindex scaffold, but production remains gated by missing route.
    jaula_contract = ROOT / "data/jaula-preservation.json"
    jaula_page = ROOT / "book-jaula.html"
    if jaula_contract.exists() and jaula_page.exists():
        try:
            j = json.loads(jaula_contract.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"jaula-preservation.json invalid: {exc}")
        else:
            ch = j.get("chapter1", {})
            text = jaula_page.read_text(encoding="utf-8")
            if j.get("status") != "AUTHORIZED_FOR_STAGING" or j.get("productionAllowed") is not False:
                fail(errors, "Jaula preservation status must be AUTHORIZED_FOR_STAGING / production false")
            if j.get("source", {}).get("driveId") != "1bfo_20JoPw3W_oHK8k-G1rd3v-K1Jfvx":
                fail(errors, "Jaula preservation source id mismatch")
            if ch.get("paragraphCount") != 133 or ch.get("wordCount") != 2158:
                fail(errors, "Jaula chapter count contract drift")
            sha = ch.get("sha256", "")
            if not sha or f'data-source-chapter-sha256="{sha}"' not in text:
                fail(errors, "book-jaula.html missing chapter SHA marker")
            if ch.get("firstParagraph", "") not in text or ch.get("lastParagraph", "") not in text:
                fail(errors, "book-jaula.html chapter boundary text mismatch")

    # Architecture boundary: reusable shell must not leak back into page-family CSS.
    for page_css_name in ("home.css", "book.css"):
        page_css_path = ROOT / "css" / page_css_name
        page_css = page_css_path.read_text(encoding="utf-8") if page_css_path.exists() else ""
        for forbidden_selector in (".site-header", ".primary-nav", ".explore-dialog", ".site-footer"):
            if forbidden_selector in page_css:
                fail(errors, f"{page_css_name}: global shell selector leaked into page CSS: {forbidden_selector}")
        for duplicate_form_selector in ("input[type=\"email\"]", ".newsletter input", ".newsletter button", ".book-newsletter input", ".book-newsletter button", ".book-consent"):
            if duplicate_form_selector in page_css:
                fail(errors, f"{page_css_name}: shared form primitive duplicated in page CSS: {duplicate_form_selector}")
    base_css = (ROOT / "css/base.css").read_text(encoding="utf-8") if (ROOT / "css/base.css").exists() else ""
    compact_base = re.sub(r"\s+", "", base_css.lower())
    if re.search(r"body\{[^}]*overflow-wrap:anywhere", compact_base):
        fail(errors, "base.css: global body overflow-wrap:anywhere is forbidden by microtypography contract")
    if ".technical-string{overflow-wrap:anywhere;word-break:normal}" not in compact_base:
        fail(errors, "base.css: technical strings need the explicit selective overflow primitive")
    for required_form_selector in (".form-field-label", ".form-row", ".form-input", ".form-submit", ".form-consent", ".form-status"):
        if required_form_selector not in base_css:
            fail(errors, f"base.css: missing shared form primitive {required_form_selector}")
    shell_css = (ROOT / "css/shell.css").read_text(encoding="utf-8") if (ROOT / "css/shell.css").exists() else ""
    for required_selector in (".site-header", ".primary-nav", ".explore-dialog", ".site-footer"):
        if required_selector not in shell_css:
            fail(errors, f"shell.css: missing global selector {required_selector}")
    compact_shell = re.sub(r"\s+", "", shell_css.lower())
    if re.search(r"@media\(max-width:1023px\).*?\.primary-nav\{display:none", compact_shell):
        fail(errors, "shell.css: primary navigation must remain directly available on mobile; Explorar cannot be the only route surface")
    if "grid-column:1/-1" not in compact_shell or "overflow-x:auto" not in compact_shell:
        fail(errors, "shell.css: mobile primary navigation must recompose into its own row and tolerate narrow widths")

    # Home newsletter lab must reproduce production-level consent semantics without network side effects.
    home_html_path = ROOT / "index.html"
    home_html_text = home_html_path.read_text(encoding="utf-8") if home_html_path.exists() else ""
    if 'src="/assets/david-porto-foto-portada-sinfondo.webp" alt="David Porto Díaz" width="433" height="577"' not in home_html_text:
        fail(errors, "index.html: author portrait must declare intrinsic 433x577 dimensions")

    for required_hook in (
        'id="newsletter-form-home"',
        'data-newsletter-source="home"',
        'id="nl-email-home"',
        'id="nl-gdpr-home"',
        'id="nl-status-home"',
        'type="checkbox"',
        'required',
    ):
        if required_hook not in home_html_text:
            fail(errors, f"index.html: newsletter lab missing consent/production hook {required_hook}")
    lab_js_path = ROOT / "js/lab.js"
    lab_js_text = lab_js_path.read_text(encoding="utf-8") if lab_js_path.exists() else ""
    for required_logic in ("consent", ".checked", "Acepta la política de privacidad"):
        if required_logic not in lab_js_text:
            fail(errors, f"lab.js: newsletter consent validation missing {required_logic}")
    if re.search(r"\bfetch\s*\(", lab_js_text):
        fail(errors, "lab.js: isolated newsletter demo must not make network requests")

    home_pres_path = ROOT / "data/home-preservation.json"
    if home_pres_path.exists():
        try:
            home_pres = json.loads(home_pres_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"home-preservation.json invalid: {exc}")
        else:
            if home_pres.get("schema_version") != 1:
                fail(errors, "home-preservation.json: expected schema_version 1")
            if home_pres.get("target_branch") != EXPECTED_TARGET_BRANCH:
                fail(errors, f"home-preservation.json: target_branch must be {EXPECTED_TARGET_BRANCH}")
            if not SHA40_RE.match(str(home_pres.get("target_head_verified", ""))):
                fail(errors, "home-preservation.json: target_head_verified must be a 40-hex informational baseline")
            if HEAD_POLICY_MARKER not in str(home_pres.get("head_policy", "")):
                fail(errors, "home-preservation.json: missing branch drift policy")
            raw_h = json.dumps(home_pres, ensure_ascii=False)
            for required in (
                "https://davidportodiaz.com/#website",
                "https://davidportodiaz.com/#author",
                "https://davidportodiaz.com/#book-manecillas",
                "FAQPage",
                "styles.css",
                "assets/manecillas-extras.css",
            ):
                if required not in raw_h:
                    fail(errors, f"home-preservation.json: missing SEO/schema policy marker {required}")

    manecillas_path = ROOT / "data/manecillas-preservation.json"
    if manecillas_path.exists():
        try:
            manecillas = json.loads(manecillas_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"manecillas-preservation.json invalid: {exc}")
        else:
            if manecillas.get("schema_version") != 1:
                fail(errors, "manecillas-preservation.json: expected schema_version 1")
            if manecillas.get("target_branch") != EXPECTED_TARGET_BRANCH:
                fail(errors, f"manecillas-preservation.json: target_branch must be {EXPECTED_TARGET_BRANCH}")
            if not SHA40_RE.match(str(manecillas.get("target_head_verified", ""))):
                fail(errors, "manecillas-preservation.json: target_head_verified must be a 40-hex informational baseline")
            if HEAD_POLICY_MARKER not in str(manecillas.get("head_policy", "")):
                fail(errors, "manecillas-preservation.json: missing branch drift policy")
            raw_m = json.dumps(manecillas, ensure_ascii=False)
            for required in (
                "https://davidportodiaz.com/#book-manecillas",
                "newsletter-form-manecillas",
                "source:manecillas",
                "genreVisible",
                "Novela coral · Ficción especulativa",
                "data-newsletter-source",
                "pending-verified-retailer-urls",
                "Te has suscrito correctamente. Recibirás las novedades de Las manecillas del recuerdo y de David Porto Díaz.",
                "/assets/portada-las-manecillas-del-recuerdo-1024.webp",
                "manecillas-book-mockup.webp",
            ):
                if required not in raw_m:
                    fail(errors, f"manecillas-preservation.json: missing preservation/debt marker {required}")

    variants = ROOT / "css/variants.css"
    if variants.exists():
        text = variants.read_text(encoding="utf-8")
        if 'data-variant="a"' not in text or 'data-variant="b"' not in text:
            fail(errors, "variants.css: both A and B selectors are required")
        if ".explore-dialog" in text or ".explore-row" in text or ".primary-nav" in text or ".site-header" in text:
            fail(errors, "variants.css: A/B must not restyle shell/Explore/navigation")
        for variant in ("a", "b"):
            match = re.search(rf'html\[data-variant="{variant}"\]\{{(.*?)\}}', text, re.S)
            if not match or "--surface-dialog:var(--dp-paper)" not in match.group(1):
                fail(errors, f"variants.css: variant {variant.upper()} must preserve the same paper dialog surface; Explore cannot be an A/B variable")
        if "display:none" in text.replace(" ", "").lower():
            compact = text.replace(" ", "").replace("\n", "").lower()
            allowed = 'html[data-variant="b"].home-hero::after{display:none}'
            residual = compact.replace(allowed, "")
            if "display:none" in residual:
                fail(errors, "variants.css: variant-specific content hiding is forbidden")


    # Low-height landscape/split-screen shell must compact instead of consuming a large sticky band.
    shell_path = ROOT / "css/shell.css"
    if shell_path.exists():
        shell_text = shell_path.read_text(encoding="utf-8")
        if "(max-height:520px)" not in shell_text or "(min-width:560px)" not in shell_text:
            fail(errors, "shell.css: low-height landscape recomp is required for 560–1023px widths")
        low_blocks = re.findall(r"@media[^\{]*max-height:520px[^\{]*\{(.*?)\n\}", shell_text, re.S)
        if not low_blocks:
            fail(errors, "shell.css: low-height media block could not be resolved")
        elif any(".primary-nav{display:none" in b.replace(" ", "") for b in low_blocks):
            fail(errors, "shell.css: low-height mode cannot hide primary navigation")

    # Planned destinations are visible editorial states, not fake links.
    if shell_path.exists():
        shell_text = shell_path.read_text(encoding="utf-8")
        if ".explore-row--planned" not in shell_text or "pointer-events:none" not in shell_text.replace(" ", ""):
            fail(errors, "shell.css: planned Explore state must be visually distinct and non-interactive")
    home_css_path = ROOT / "css/home.css"
    if home_css_path.exists():
        home_css_text = home_css_path.read_text(encoding="utf-8")
        if ".map-node--planned" not in home_css_text:
            fail(errors, "home.css: planned map-node state is required")
    if "protectPlannedRoutes" in lab_js_text:
        fail(errors, "lab.js: planned destinations must not rely on click interception")

    # Render-discovered invariants: hidden semantics must beat component display rules,
    # and Book screenshots need the same clean capture mode as Home.
    base_css_path = ROOT / "css/base.css"
    if base_css_path.exists():
        base_css = base_css_path.read_text(encoding="utf-8")
        if not re.search(r"\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important", base_css, re.S):
            fail(errors, "base.css: [hidden]{display:none!important} is required so CSS cannot resurrect hidden fixtures/fallbacks")

    book_html_path = ROOT / "book-manecillas.html"
    book_css_path = ROOT / "css/book.css"
    if book_html_path.exists() and book_css_path.exists():
        book_html_text = book_html_path.read_text(encoding="utf-8")
        book_css_text = book_css_path.read_text(encoding="utf-8")
        if "p.get('capture')==='1'" not in book_html_text and 'p.get("capture")==="1"' not in book_html_text:
            fail(errors, "book-manecillas.html: ?capture=1 support is required")
        if 'html[data-capture="true"] .book-lab-toolbar' not in book_css_text:
            fail(errors, "book.css: Book lab toolbar must hide in capture mode")

    book_css_path = ROOT / "css/book.css"
    if book_css_path.exists():
        raw_book_css = book_css_path.read_text(encoding="utf-8")
        if "@media print" not in raw_book_css or ".book-utility-actions" not in raw_book_css:
            fail(errors, "book.css: print contract and subordinate utility row are required")
        if 'content:"davidportodiaz.com/las-manecillas-del-recuerdo/"' not in raw_book_css.replace(" ", ""):
            fail(errors, "book.css: print output must expose canonical book URL")
    if 'hidden data-share-url="https://davidportodiaz.com/las-manecillas-del-recuerdo/"' not in book_html_text:
        fail(errors, "book-manecillas.html: canonical share URL missing")
    for marker in ("navigator.share", "Enlace copiado.", "copyShareUrl", "button.hidden = false"):
        if marker not in lab_js_text:
            fail(errors, f"lab.js: share/copy-link contract missing {marker}")

    for rel in ("js/lab.js", "js/fixtures.js", "js/book-fixtures.js"):
        path = ROOT / rel
        if path.exists() and re.search(r"\b(eval|new\s+Function)\s*\(", path.read_text(encoding="utf-8")):
            fail(errors, f"{rel}: dynamic code execution is forbidden")

    # Manecillas deep-link and editorial-pause compatibility.
    book_path = ROOT / "book-manecillas.html"
    book_css_path = ROOT / "css/book.css"
    if book_path.exists():
        book_text = book_path.read_text(encoding="utf-8")
        for anchor in ("aviso", "muestra", "sinopsis-editorial", "newsletter-manecillas"):
            if not re.search(rf'id=["\']{re.escape(anchor)}["\']', book_text):
                fail(errors, f"book-manecillas.html: missing preserved deep link #{anchor}")
        dedication = "«A quienes alguna vez olvidaron que el tiempo no vuelve.»"
        if book_text.count(dedication) != 1:
            fail(errors, "book-manecillas.html: dedication must appear exactly once")
        if 'href="#newsletter-manecillas">Recibir novedades</a>' not in book_text:
            fail(errors, "book-manecillas.html: pending commercial state must keep Recibir novedades -> #newsletter-manecillas")
        if "manecillas-quote-band" in book_text:
            fail(errors, "book-manecillas.html: legacy quote-band must not return")
    if book_css_path.exists():
        book_css = book_css_path.read_text(encoding="utf-8")
        if ".book-anchor-alias" not in book_css or "scroll-margin-top" not in book_css:
            fail(errors, "css/book.css: preserved alias anchors need scroll-margin for sticky header")
        if ".book-dedication" not in book_css:
            fail(errors, "css/book.css: missing editorial dedication treatment")
        if "@media (min-width:768px) and (max-width:899px)" not in book_css:
            fail(errors, "css/book.css: explicit 768–899 Book recomposition is required by master 20")
        if "font-size:clamp(3rem,7vw,4rem)" not in book_css:
            fail(errors, "css/book.css: 768 Book H1 must stay within the 48–64 px contract")


    # Cuaderno + Article executable-family contract.
    cuaderno_path = ROOT / "cuaderno.html"
    article_path = ROOT / "article-pilot.html"
    editorial_css_path = ROOT / "css/editorial.css"
    editorial_js_path = ROOT / "js/editorial.js"
    if cuaderno_path.exists():
        cuaderno_text = cuaderno_path.read_text(encoding="utf-8")
        cuaderno = parse_html(cuaderno_path)
        if cuaderno.dialogs != 1:
            fail(errors, f"cuaderno.html: expected one native dialog, got {cuaderno.dialogs}")
        if re.search(r"\sstyle=[\"']", cuaderno_text):
            fail(errors, "cuaderno.html: inline styles are forbidden in the V1 scaffold")
        required_routes = [
            "/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/",
            "/cuaderno/que-es-el-portal-fantasy/",
            "/cuaderno/portal-fantasy-vs-fantasia-epica/",
            "/cuaderno/sistema-de-magia-noveris/",
            "/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/",
            "/cuaderno/worldbuilding-noveris-ciudad-magica/",
            "/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/",
        ]
        for route in required_routes:
            if route not in cuaderno_text:
                fail(errors, f"cuaderno.html: missing existing article route {route}")
        for marker in (
            'href="https://davidportodiaz.com/cuaderno/feed.xml"',
            'id="newsletter-form-cuaderno"', 'data-newsletter-source="cuaderno"',
            'id="nl-email-cuaderno"', 'id="nl-gdpr-cuaderno"', 'id="nl-status-cuaderno"',
            'data-surprise-me', 'href="/mapa-del-sitio/"',
            'class="cuaderno-ledger"', 'Las manecillas del recuerdo', 'Samuel entre mundos'
        ):
            if marker not in cuaderno_text:
                fail(errors, f"cuaderno.html: missing editorial/preservation marker {marker}")
        if "card" in cuaderno_text.lower():
            fail(errors, "cuaderno.html: archive must not drift into a card-grid vocabulary")

    if article_path.exists():
        article_text = article_path.read_text(encoding="utf-8")
        article = parse_html(article_path)
        if article.dialogs != 1:
            fail(errors, f"article-pilot.html: expected one native dialog, got {article.dialogs}")
        if re.search(r"\sstyle=[\"']", article_text):
            fail(errors, "article-pilot.html: inline styles are forbidden in the V1 scaffold")
        for anchor in ("que-es-el-portal-fantasy", "magia-con-coste", "protagonistas-ordinarios", "fantasia-juvenil-espanola", "faq"):
            if not re.search(rf'id=["\']{re.escape(anchor)}["\']', article_text):
                fail(errors, f"article-pilot.html: missing preserved pilot anchor #{anchor}")
        for marker in (
            'data-article-body', 'data-reading-progress-meter', 'data-article-toc',
            'data-share-url="https://davidportodiaz.com/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/"',
            'data-print', '<details', '<summary>', 'role="note"',
            'id="newsletter-form-cuaderno"', 'data-newsletter-source="cuaderno"',
            'Fantasía juvenil española con portales, magia con coste y mundos ocultos'
        ):
            if marker not in article_text:
                fail(errors, f"article-pilot.html: missing reading/preservation marker {marker}")

    if editorial_css_path.exists():
        editorial_css = editorial_css_path.read_text(encoding="utf-8")
        if re.search(r"#[0-9a-fA-F]{3,8}\b", editorial_css):
            fail(errors, "editorial.css: local hex colors are forbidden; use semantic tokens")
        for forbidden in ("linear-gradient", "radial-gradient", "backdrop-filter", "grid-template-columns:repeat("):
            if forbidden in editorial_css:
                fail(errors, f"editorial.css: generic/legacy visual pattern forbidden: {forbidden}")
        for required in (".cuaderno-masthead", ".cuaderno-ledger", ".article-layout", ".article-toc", ".article-prose", ".article-faq", "@media print"):
            if required not in editorial_css:
                fail(errors, f"editorial.css: missing family primitive {required}")
        if "var(--font-reading)" not in editorial_css:
            fail(errors, "editorial.css: long reading must use the shared Newsreader role")

    if editorial_js_path.exists():
        editorial_js = editorial_js_path.read_text(encoding="utf-8")
        for required in ("data-reading-progress-meter", "IntersectionObserver", "data-print", "window.print"):
            if required not in editorial_js:
                fail(errors, f"editorial.js: missing progressive reading utility {required}")
        if re.search(r"\bfetch\s*\(", editorial_js) or re.search(r"\b(eval|new\s+Function)\s*\(", editorial_js):
            fail(errors, "editorial.js: network/dynamic code is forbidden in the isolated family lab")

    for rel, kind in (("data/cuaderno-preservation.json", "cuaderno"), ("data/article-preservation.json", "article")):
        pp = ROOT / rel
        if pp.exists():
            try:
                data = json.loads(pp.read_text(encoding="utf-8"))
            except Exception as exc:
                fail(errors, f"{rel} invalid: {exc}")
            else:
                if data.get("schema_version") != 1 or data.get("target_branch") != EXPECTED_TARGET_BRANCH:
                    fail(errors, f"{rel}: schema/branch contract drift")
                if not SHA40_RE.match(str(data.get("target_head_verified", ""))):
                    fail(errors, f"{rel}: target_head_verified must be a 40-hex informational baseline")
                raw = json.dumps(data, ensure_ascii=False)
                if "newsletter-form-cuaderno" not in raw or "cuaderno" not in raw:
                    fail(errors, f"{rel}: newsletter/source preservation missing")
                if kind == "cuaderno":
                    for marker in ("CollectionPage", "feed.xml", "data-surprise-me", "/mapa-del-sitio/"):
                        if marker not in raw:
                            fail(errors, f"{rel}: missing Cuaderno preservation marker {marker}")
                else:
                    for marker in ("Article", "BreadcrumbList", "FAQPage", "preserve_body_copy_verbatim", "rebuild_schema_from_visible_answers_at_integration"):
                        if marker not in raw:
                            fail(errors, f"{rel}: missing Article preservation marker {marker}")

    readiness_path = ROOT / "IMPLEMENTATION-READINESS.md"
    if readiness_path.exists():
        readiness = readiness_path.read_text(encoding="utf-8")
        for marker in ("LISTO PARA IMPLEMENTACIÓN EN STAGING", "IMPLEMENT_READY", "AUTHORIZED_FOR_STAGING", "BLOCKED_BY_STAGING", "Definition of implementation-ready global"):
            if marker not in readiness:
                fail(errors, f"IMPLEMENTATION-READINESS.md: missing handoff guard {marker}")
        for family in ("Home", "Manecillas", "Samuel", "Cuaderno", "Artículo", "Autor", "Prensa", "Premios", "Eventos", "Herramientas"):
            if family not in readiness:
                fail(errors, f"IMPLEMENTATION-READINESS.md: missing family state {family}")

    extension_validator = ROOT / "scripts/validate_extension.py"
    if extension_validator.exists():
        proc = subprocess.run([sys.executable, str(extension_validator)], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            fail(errors, "validate_extension.py failed:\n" + (proc.stdout + proc.stderr).strip())

    if errors:
        print("LAB VALIDATION: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("LAB VALIDATION: OK")
    print(f"- root: {ROOT}")
    print(f"- required files: {len(REQUIRED)}")
    print(f"- target branch contract: {EXPECTED_TARGET_BRANCH}")
    print("- audited HEAD baselines: informational + drift-policy enforced; not a rigid SHA lock")
    print("- HTML: one H1, no duplicate IDs/inline handlers, no production CSS/JS")
    print("- Gate 0: specimen exercises the same shared form primitives as Home/Book")
    print("- Home/Book/Cuaderno/Article: one native <dialog> per shell")
    print("- CSS: balanced; no historical palette/patterns in component styles")
    print("- media: real target-branch asset paths; traced portrait resolution gate; no duplicate cover hierarchy")
    print("- fonts: exact V1 families/weights/italic contract; remote import isolated to lab; production self-host enforced")
    print("- routes: 7 territories; Herramientas verified; Jaula content authorized with route/promotion gate")
    print("- migration: selector/function map bound to active branch contract")
    print("- CSS architecture: base/shell/page separation enforced; forms centralized; technical wrapping selective; mobile primary nav direct")
    print("- Home/Book newsletter: source markers preserved; email + consent lab validation; no network request")
    print("- Home SEO: identity vs conditional-schema preservation contract present")
    print("- Manecillas: preservation + genre + permanent newsletter source/copy + commercial gate + Book V1/print/share/fixtures")
    print("- Cuaderno/Article: executable editorial family + preservation + RSS/anchors/FAQ/reading utilities")
    print("- Readiness: Claude staging handoff covered; merge/production remain explicitly blocked pending browser evidence")
    print("- variants: A/B selectors present; shell/navigation/Explore invariant enforced")
    print("- render visibility: hidden invariant + clean Book capture mode")
    print("- low-height shell: compact one-row landscape mode without hiding primary routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
