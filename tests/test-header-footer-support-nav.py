#!/usr/bin/env python3
"""Contrato de cabecera y pie: RRSS (texto), Donar junto a Comprar y aviso sutil de apoyo.

- La cabecera de cada página con shell tiene el enlace de texto "RRSS" -> /redes-sociales/
  y, si hay canales de apoyo, el botón "Donar" -> /apoyar/ justo antes de "Comprar".
- Ya no existen los iconos de compartir ni de corazón.
- El pie lleva UNA frase de apoyo con enlace a /apoyar/ en todas las páginas con shell
  salvo /apoyar/ misma y las herramientas; el Atlas no mantiene su aviso propio.
- Las herramientas (páginas con v1-tools-identity.css) llevan en su lugar UNA nota
  .support-note al final del contenido, con botón a /apoyar/, y ninguna frase en el pie.
- El hub del Atlas usa el mismo encabezado .catalogue-hero que el resto de catálogos y no
  conserva el párrafo de método eliminado.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER_RE = re.compile(r"<header class=\"site-header\".*?</header>", re.S)
SKIP_FOOTER = {"apoyar/index.html"}
TOOL_MARK = "/assets/v1-tools-identity.css"


def shell_pages() -> list[Path]:
    files = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    pages = []
    for rel in files:
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        if "site-shell:header:start" in text:
            pages.append(ROOT / rel)
    return pages


def main() -> None:
    pages = shell_pages()
    assert len(pages) > 400, f"se esperaban >400 páginas con shell, hay {len(pages)}"
    errors: list[str] = []
    tools = 0
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text(encoding="utf-8")
        match = HEADER_RE.search(text)
        if not match:
            errors.append(f"{rel}: sin cabecera")
            continue
        header = match.group(0)
        if 'class="header-social" href="/redes-sociales/"' not in header or ">RRSS</a>" not in header:
            errors.append(f"{rel}: falta el enlace de texto RRSS")
        if 'class="header-donate" href="/apoyar/"' not in header or ">Donar</a>" not in header:
            errors.append(f"{rel}: falta el botón Donar")
        elif header.index("header-donate") > header.index("header-buy"):
            errors.append(f"{rel}: Donar debe ir antes de Comprar")
        if "header-support" in header or "<circle cx=\"6\" cy=\"12\"" in header:
            errors.append(f"{rel}: quedan los iconos antiguos de apoyo o compartir")
        is_tool = TOOL_MARK in text
        notes = text.count('class="support-note"')
        if notes != (1 if is_tool else 0):
            errors.append(f"{rel}: nota de apoyo x{notes} (esperado {int(is_tool)})")
        elif is_tool:
            note = text.split('class="support-note"', 1)[1].split("</aside>", 1)[0]
            if 'class="support-note__button" href="/apoyar/"' not in note:
                errors.append(f"{rel}: la nota de apoyo no enlaza a /apoyar/")
            if text.index('class="support-note"') > text.rindex("</main>"):
                errors.append(f"{rel}: la nota de apoyo debe ir dentro de <main>")
        tools += is_tool
        nudges = text.count('class="footer-support"')
        expected = 0 if rel in SKIP_FOOTER or is_tool else 1
        if nudges != expected:
            errors.append(f"{rel}: aviso de apoyo en el pie x{nudges} (esperado {expected})")
        elif nudges and 'href="/apoyar/">puedes apoyar el proyecto</a>' not in text:
            errors.append(f"{rel}: el aviso de apoyo no enlaza a /apoyar/")

    hub = (ROOT / "atlas-literario" / "index.html").read_text(encoding="utf-8")
    if '<header class="catalogue-hero">' not in hub:
        errors.append("atlas-literario/index.html: el encabezado no usa .catalogue-hero")
    for forbidden in ("atlas-rule", "atlas-hero", "support-cta", "Cada ficha indica", "también existe fuera de las páginas"):
        if forbidden in hub:
            errors.append(f"atlas-literario/index.html: contiene '{forbidden}'")

    if tools < 15:
        errors.append(f"solo {tools} herramientas con nota de apoyo; se esperaban al menos 15")
    if errors:
        raise SystemExit("FAIL:\n" + "\n".join(errors[:40]) + (f"\n... {len(errors)} errores" if len(errors) > 40 else ""))
    print(f"PASS: cabecera (RRSS + Donar + Comprar) y aviso de apoyo en {len(pages)} páginas")


if __name__ == "__main__":
    main()
