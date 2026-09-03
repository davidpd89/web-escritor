#!/usr/bin/env python3
"""Regresion (item 16/17 de la ronda 2026-09: extraccion tipo Reader Mode /
Readability): en las-manecillas-del-recuerdo/ y su pagina de fragmentos, el
<nav class="book-breadcrumb"> vivia como PRIMER HIJO de <article
class="book-page">, en vez de como hermano anterior (el patron que ya usan
correctamente los articulos de cuaderno/, con <nav class="editorial-
breadcrumb"> antes de <article>, no dentro).

Bug real encontrado con Mozilla Readability (la libreria que usan Firefox/
Safari Reader Mode y herramientas de "guardar para leer despues"): al
extraer el articulo, el texto empezaba con "InicioLas manecillas del
recuerdoFragmentos ..." -- las migas de pan coladas antes del contenido
real -- porque Readability no siempre limpia un <nav> corto anidado DENTRO
del contenedor que elige como articulo principal. Moviendo el breadcrumb
fuera de <article> (como hermano de <main>) el texto extraido empieza
limpio con el contenido real; verificado con @mozilla/readability+jsdom
durante la investigacion (no como dependencia permanente del repo).

Uso:
  python tests/test-manecillas-breadcrumb-outside-article.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "las-manecillas-del-recuerdo/index.html",
    "las-manecillas-del-recuerdo/fragmentos/index.html",
]

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


for rel in PAGES:
    text = (ROOT / rel).read_text(encoding="utf-8")
    breadcrumb_idx = text.find('class="book-breadcrumb"')
    article_idx = text.find('<article class="book-page')
    check(breadcrumb_idx != -1 and article_idx != -1, f"{rel}: both breadcrumb and article present")
    check(
        breadcrumb_idx != -1 and article_idx != -1 and breadcrumb_idx < article_idx,
        f"{rel}: book-breadcrumb appears BEFORE <article>, not nested inside it",
    )
    # The breadcrumb's own <nav>...</nav> must fully close before <article> opens.
    nav_close_idx = text.find("</nav>", breadcrumb_idx)
    check(
        nav_close_idx != -1 and nav_close_idx < article_idx,
        f"{rel}: the breadcrumb <nav> closes before <article> opens (not nested)",
    )

print(f"tests/test-manecillas-breadcrumb-outside-article: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
