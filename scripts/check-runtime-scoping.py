#!/usr/bin/env python3
"""Static runtime gate for PR #61.

Checks page-specific scoping, native-dialog contracts, mojibake and the
back-to-top immediate interaction without changing global analytics taxonomy.
Python standard library only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMUEL_PAGE = "libros/samuel-entre-mundos/index.html"
POPUP_SCOPE_PREFIXES = ("cuaderno/", "recomendaciones/", "universo/noveris/", "clubes-de-lectura/")
MOJIBAKE_MARKERS = ("Ã", "Â", "â€", "â‚", "ï¿½", "\ufffd")
MOJIBAKE_PATHS = (
    "styles.css",
    "script.js",
    "assets/newsletter-popup.js",
    "assets/newsletter-popup.css",
    "assets/samuel-buy-modal.js",
    "assets/samuel-buy-modal.css",
    SAMUEL_PAGE,
)

FORBIDDEN_PATTERNS_IN_SCRIPT_JS = {
    re.compile(r'overlay\.id\s*=\s*["\']nl-popup-overlay["\']'): "popup newsletter reimplementado en script.js",
    re.compile(r'd\.id\s*=\s*["\']buy-dialog["\']'): "modal Samuel reimplementado en script.js",
    re.compile(r'getElementById\(["\']quiz-noveris-app["\']\)'): "quiz Noveris muerto reintroducido en runtime global",
}


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel]


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def check_script_js(root: Path) -> list[str]:
    text = read(root, "script.js")
    errors: list[str] = []
    for pattern, why in FORBIDDEN_PATTERNS_IN_SCRIPT_JS.items():
        if pattern.search(text):
            errors.append(f"script.js: {why}")

    marker = text.find("// Back-to-top button")
    click = re.search(r'btn\.addEventListener\("click",\s*\(\)\s*=>\s*\{([\s\S]*?)\n\s*\}\);', text[marker:] if marker >= 0 else "")
    if not click:
        errors.append("script.js: no se localiza handler de Volver arriba")
    else:
        body = click.group(1)
        if "scheduleTask(" in body:
            errors.append("script.js: Volver arriba difiere scrollTo fuera del mismo turno")
        if "window.scrollTo" not in body:
            errors.append("script.js: Volver arriba ya no llama a scrollTo")
        if "prefers-reduced-motion: reduce" not in body:
            errors.append("script.js: Volver arriba perdió reduced-motion")
    return errors


def check_buy_modal_scope(root: Path, pages: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in pages:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="strict")
        has_trigger = "data-buy-modal" in text
        loads_js = bool(re.search(r'src=["\']?/assets/samuel-buy-modal\.js', text))
        loads_css = bool(re.search(r'href=["\']?/assets/samuel-buy-modal\.css', text))
        if rel == SAMUEL_PAGE:
            if not has_trigger:
                errors.append(f"{rel}: falta [data-buy-modal]")
            if not loads_js:
                errors.append(f"{rel}: falta assets/samuel-buy-modal.js")
            if text.count("/assets/samuel-buy-modal.js") != 1:
                errors.append(f"{rel}: samuel-buy-modal.js debe cargarse exactamente una vez")
            if loads_css:
                errors.append(f"{rel}: el CSS del modal debe cargarlo el runtime validado, no el HTML")
        elif has_trigger or loads_js or loads_css:
            errors.append(f"{rel}: runtime/trigger Samuel fuera de su única página")

    js = read(root, "assets/samuel-buy-modal.js")
    required = (
        'const EXPECTED_PATH = "/libros/samuel-entre-mundos/"',
        'main[data-family="book-samuel"]',
        'STYLE_HREF = "/assets/samuel-buy-modal.css"',
        'pageRoot.addEventListener("click"',
    )
    for token in required:
        if token not in js:
            errors.append(f"assets/samuel-buy-modal.js: falta contrato fail-closed: {token}")
    if 'document.addEventListener("keydown"' in js:
        errors.append("assets/samuel-buy-modal.js: listener global de teclado/focus trap manual reintroducido")
    return errors


def check_popup_scope(root: Path, pages: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in pages:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="strict")
        loads_core = bool(re.search(r'src=["\']?/script\.js', text))
        if not loads_core:
            continue
        in_scope = rel.startswith(POPUP_SCOPE_PREFIXES)
        loads_js = bool(re.search(r'src=["\']?/assets/newsletter-popup\.js', text))
        loads_css = bool(re.search(r'href=["\']?/assets/newsletter-popup\.css', text))
        if in_scope and not (loads_js and loads_css):
            missing = []
            if not loads_js:
                missing.append("assets/newsletter-popup.js")
            if not loads_css:
                missing.append("assets/newsletter-popup.css")
            errors.append(f"{rel}: popup en scope pero falta {', '.join(missing)}")
        if not in_scope and (loads_js or loads_css):
            errors.append(f"{rel}: popup cargado fuera de scope (js={loads_js} css={loads_css})")

    popup = read(root, "assets/newsletter-popup.js")
    if 'document.createElement("dialog")' not in popup or ".showModal()" not in popup:
        errors.append("assets/newsletter-popup.js: popup debe usar <dialog> nativo + showModal()")
    if 'document.addEventListener("keydown"' in popup:
        errors.append("assets/newsletter-popup.js: listener global de teclado/focus trap manual reintroducido")
    if "nl-popup-overlay" in popup or "nl-popup-overlay" in read(root, "assets/newsletter-popup.css"):
        errors.append("newsletter popup: queda overlay custom legacy")
    return errors


def check_global_css(root: Path) -> list[str]:
    global_css = read(root, "styles.css")
    errors: list[str] = []
    for token in ("#buy-dialog", ".buy-dialog-", ".buy-option"):
        if token in global_css:
            errors.append(f"styles.css: CSS específico de Samuel sigue global ({token})")
    modal_css = read(root, "assets/samuel-buy-modal.css")
    for token in ("#buy-dialog", ".buy-dialog-inner", ".buy-option"):
        if token not in modal_css:
            errors.append(f"assets/samuel-buy-modal.css: falta {token}")
    return errors


def check_mojibake(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in MOJIBAKE_PATHS:
        text = read(root, rel)
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                errors.append(f"{rel}: posible mojibake {marker!r}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root).resolve()
    pages = tracked_html(root)

    errors: list[str] = []
    errors += check_script_js(root)
    errors += check_buy_modal_scope(root, pages)
    errors += check_popup_scope(root, pages)
    errors += check_global_css(root)
    errors += check_mojibake(root)

    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"\nFAIL: runtime scoping violado ({len(errors)} problema(s)).")
        return 1
    print(f"PASS: runtime scoping/focus/mojibake OK ({len(pages)} paginas HTML revisadas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
