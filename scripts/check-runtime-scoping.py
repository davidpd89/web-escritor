#!/usr/bin/env python3
"""Runtime scoping gate (H.1, 2026-08-23): falla si una responsabilidad
especifica de pagina (popup de newsletter, modal de compra de Samuel)
vuelve a cargarse globalmente en script.js, o si el contrato entre "esta
pagina necesita el hook X" y "esta pagina carga el script X" se rompe en
cualquier direccion.

Nacio de una extraccion real: script.js concentraba el quiz de Noveris
(nunca se ejecutaba: su target no existe en ningun HTML), el modal de
compra de Samuel (solo se necesitaba en 1 pagina) y el popup de newsletter
(solo se necesitaba en 13), pero las tres se descargaban/ejecutaban en
TODAS las paginas. Este checker existe para que esa regresion no pueda
volver a colarse sin que CI se ponga en rojo.

Comprueba tres cosas, en ambas direcciones (ni falta ni sobra):
1. script.js no debe volver a contener el codigo del popup/modal/quiz
   (marcadores literales que solo deberian vivir en sus assets propios).
2. Toda pagina con un trigger [data-buy-modal] debe cargar
   assets/samuel-buy-modal.js, y ninguna otra pagina debe cargarlo.
3. Toda pagina bajo /cuaderno/, /recomendaciones/, /universo/noveris/ o
   /clubes-de-lectura/ que cargue script.js debe cargar tambien
   assets/newsletter-popup.js (+ su CSS), y ninguna pagina fuera de ese
   ambito debe cargarlos.

Python standard library only.

Usage:
    python scripts/check-runtime-scoping.py
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Marcadores estructurales (no simples menciones) que NUNCA deben
# reaparecer en script.js: si alguien pega de vuelta el bloque completo del
# popup/modal/quiz ahi, uno de estos patrones volveria a aparecer. No se
# usan los strings sueltos ("buy-dialog", "quiz-noveris-app") porque
# aparecen legitimamente fuera de una reimplementacion: script.js referencia
# a proposito ":not(#buy-dialog a)" en el tracker generico de clics de
# Amazon (para no contar doble un clic dentro del modal, que vive en otro
# fichero), y este mismo script explica en un comentario por que
# quiz-noveris-app ya no existe.
FORBIDDEN_PATTERNS_IN_SCRIPT_JS = {
    re.compile(r'overlay\.id\s*=\s*"nl-popup-overlay"'): "popup de newsletter reimplementado (debe vivir solo en assets/newsletter-popup.js)",
    re.compile(r'd\.id\s*=\s*"buy-dialog"'): "modal de compra de Samuel reimplementado (debe vivir solo en assets/samuel-buy-modal.js)",
    re.compile(r'getElementById\("quiz-noveris-app"\)'): "quiz de Noveris reintroducido (eliminado: superseded por assets/samuel-quiz.js)",
}

POPUP_SCOPE_PREFIXES = ("cuaderno/", "recomendaciones/", "universo/noveris/", "clubes-de-lectura/")


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel]


def check_script_js(root: Path) -> list[str]:
    text = (root / "script.js").read_text(encoding="utf-8")
    errors = []
    for pattern, why in FORBIDDEN_PATTERNS_IN_SCRIPT_JS.items():
        if pattern.search(text):
            errors.append(f"script.js: {why}")
    return errors


def check_buy_modal_scope(root: Path, pages: list[Path]) -> list[str]:
    errors = []
    for path in pages:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        has_trigger = "data-buy-modal" in text
        loads_script = bool(re.search(r'src=["\']?/assets/samuel-buy-modal\.js', text))
        if has_trigger and not loads_script:
            errors.append(f"{rel}: tiene [data-buy-modal] pero no carga assets/samuel-buy-modal.js")
        if loads_script and not has_trigger:
            errors.append(f"{rel}: carga assets/samuel-buy-modal.js pero no tiene ningun [data-buy-modal]")
    return errors


def check_popup_scope(root: Path, pages: list[Path]) -> list[str]:
    errors = []
    for path in pages:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        loads_core = bool(re.search(r'src=["\']?/script\.js', text))
        if not loads_core:
            continue  # paginas sin script.js nunca podian tener el popup de todas formas
        in_scope = rel.startswith(POPUP_SCOPE_PREFIXES)
        loads_js = bool(re.search(r'src=["\']?/assets/newsletter-popup\.js', text))
        loads_css = bool(re.search(r'href=["\']?/assets/newsletter-popup\.css', text))
        if in_scope and not (loads_js and loads_css):
            missing = []
            if not loads_js:
                missing.append("assets/newsletter-popup.js")
            if not loads_css:
                missing.append("assets/newsletter-popup.css")
            errors.append(f"{rel}: en ambito del popup pero le falta {', '.join(missing)}")
        if not in_scope and (loads_js or loads_css):
            errors.append(f"{rel}: fuera de ambito del popup pero carga sus assets (js={loads_js} css={loads_css})")
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

    for e in errors:
        print(f"ERROR {e}")

    if errors:
        print(f"\nFAIL: runtime scoping violado ({len(errors)} problema(s)).")
        return 1
    print(f"PASS: runtime scoping OK ({len(pages)} paginas HTML revisadas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
