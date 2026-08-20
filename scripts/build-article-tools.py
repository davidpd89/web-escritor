#!/usr/bin/env python3
"""Pre-renderiza el bloque "Herramientas de lectura" (article-tools) en el HTML.

Por que existe: article-tools.js construia todo el bloque en cliente sobre un
`<div id="article-tools">` vacio. Con la cache fria el script `defer` se ejecuta
DESPUES del primer pintado, el bloque aparece de golpe encima del articulo y
empuja hacia abajo todo lo que hay debajo. Lighthouse lo midio como un
Cumulative Layout Shift de 0,2765 en /recomendaciones/portal-fantasy-espanol/
(limite del proyecto: 0,1). No es un artefacto de laboratorio: cualquier lector
con conexion lenta ve saltar el articulo entero.

Reservar altura por CSS no sirve aqui: la altura depende del numero de titulos
de cada pagina, asi que cualquier `min-height` fijo o deja hueco o se queda
corto. La solucion sin heuristicas es que el bloque ya venga en el HTML: si no
se inyecta nada, no hay desplazamiento posible.

De paso arregla los `id` de los titulos. El JS los generaba en cliente con
`replace(/[^a-z0-9-]+/gi,'-')`, que convierte "El Leon, la bruja..." en
`el-le-n-la-bruja-y-el-armario`: cada acento se perdia como guion y los
anclajes solo existian una vez ejecutado el script. Aqui se generan con
transliteracion real y quedan escritos en el HTML.

Uso:
  python scripts/build-article-tools.py           # reescribe el HTML
  python scripts/build-article-tools.py --check   # falla si hay deriva (CI)
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import unicodedata
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "scripts", "archive",
    "WEB DAVID PORTO nuevas ideas", ".codex_work", ".preview-dist", "dist",
}

CONTAINER_OPEN_RE = re.compile(r'<div\s+id="article-tools"[^>]*>')
DIV_TOKEN_RE = re.compile(r'<div\b[^>]*>|</div\s*>', re.I)
MAIN_RE = re.compile(r'<main\b[^>]*id="main-content"[^>]*>(.*?)</main>', re.S)
HEADING_RE = re.compile(r'<(h2|h3)\b([^>]*)>(.*?)</\1>', re.S | re.I)
ID_ATTR_RE = re.compile(r'\bid\s*=\s*("|\')(.*?)\1', re.S)
TAG_RE = re.compile(r'<[^>]+>')

# El boton de progreso local solo lo pinta el JS cuando la pagina NO tiene ya
# la barra global. En tiempo de ejecucion el JS mira `.reading-progress`, pero
# ese elemento no esta en el HTML: lo crea script.js, y solo si el <body> lleva
# `data-reading-progress`. Ese atributo es la fuente de verdad y si es visible
# en el HTML, asi que la condicion estatica se evalua sobre el, no sobre la
# clase que aun no existe.
GLOBAL_PROGRESS_RE = re.compile(r'<body\b[^>]*\bdata-reading-progress\b')


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def unescape(text: str) -> str:
    pairs = (
        ("&nbsp;", " "), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
        ("&#39;", "'"), ("&mdash;", "—"), ("&ndash;", "–"), ("&amp;", "&"),
    )
    for raw, out in pairs:
        text = text.replace(raw, out)
    return text


def slugify(text: str) -> str:
    """Transliteracion real: "El Leon, la bruja" -> "el-leon-la-bruja".

    El JS original aplicaba `[^a-z0-9-]+ -> '-'` sobre el texto con acentos, asi
    que cada vocal acentuada desaparecia como guion. Aqui se descompone en NFD y
    se quitan las marcas diacriticas antes de filtrar.
    """
    norm = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    stripped = stripped.replace("ñ", "n").replace("Ñ", "n")
    slug = re.sub(r"[^a-z0-9]+", "-", stripped.lower()).strip("-")
    return slug or "seccion"


def heading_text(inner: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub("", inner))).strip()


def find_container(text: str) -> tuple[int, int, int] | None:
    """Localiza el contenedor contando profundidad de <div>.

    Un `(.*?)</div>` no vale: en cuanto el bloque esta pre-renderizado, el
    contenedor tiene <div> anidados y el cierre no-avaro corta dentro del
    primer hijo. El resultado era que la segunda ejecucion dejaba HTML
    duplicado y el script no era idempotente (`--check` fallaba justo despues
    de generar). Se cuenta la profundidad hasta el cierre real.

    Devuelve (inicio_etiqueta, fin_etiqueta_apertura, inicio_cierre).
    """
    m = CONTAINER_OPEN_RE.search(text)
    if not m:
        return None
    depth = 1
    pos = m.end()
    for tok in DIV_TOKEN_RE.finditer(text, pos):
        if tok.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return m.start(), m.end(), tok.start()
        else:
            depth += 1
    return None


def render_block(headings: list[tuple[str, str]], has_global_progress: bool) -> str:
    parts: list[str] = []
    if len(headings) >= 2:
        items = "".join(
            '<li><a href="#{0}" class="at-toc-link">{1}</a></li>'.format(esc(hid), esc(text))
            for hid, text in headings
        )
        parts.append(
            '<div class="at-toc"><strong>En esta página</strong>'
            '<ol class="at-toc-list">{0}</ol></div>'.format(items)
        )
    controls = [
        '<div class="at-print"><button class="at-btn" type="button" '
        'aria-label="Imprimir o guardar como PDF">Imprimir / PDF</button></div>'
    ]
    if not has_global_progress:
        controls.append(
            '<div class="at-progress"><button class="at-btn" type="button">'
            'Mostrar progreso</button></div>'
        )
    controls.append(
        '<div class="at-share"><button class="at-btn" type="button">Compartir</button></div>'
    )
    parts.append('<div class="at-controls">{0}</div>'.format("".join(controls)))
    return "".join(parts)


def process(text: str) -> tuple[str, list[str]]:
    """Devuelve (html nuevo, notas). No toca nada si la pagina no usa el bloque."""
    if 'id="article-tools"' not in text:
        return text, []
    main = MAIN_RE.search(text)
    if not main:
        return text, ['sin <main id="main-content">: no se puede calcular el indice']

    notes: list[str] = []
    main_inner = main.group(1)
    used_ids = {m.group(2) for m in ID_ATTR_RE.finditer(text)}
    headings: list[tuple[str, str]] = []
    replacements: list[tuple[int, int, str]] = []

    for m in HEADING_RE.finditer(main_inner):
        attrs, inner = m.group(2), m.group(3)
        label = heading_text(inner)
        if not label:
            continue
        id_m = ID_ATTR_RE.search(attrs)
        if id_m:
            hid = id_m.group(2)
        else:
            base = slugify(label)
            hid = base
            n = 2
            while hid in used_ids:
                hid = "{0}-{1}".format(base, n)
                n += 1
            used_ids.add(hid)
            replacements.append((m.start(2), m.end(2), ' id="{0}"'.format(hid) + attrs))
            notes.append('id generado para "{0}": #{1}'.format(label, hid))
        headings.append((hid, label))

    for start, end, new in reversed(replacements):
        main_inner = main_inner[:start] + new + main_inner[end:]
    text = text[: main.start(1)] + main_inner + text[main.end(1):]

    block = render_block(headings, bool(GLOBAL_PROGRESS_RE.search(text)))

    span = find_container(text)
    if span is None:
        return text, notes + ["no se pudo aislar el contenedor article-tools"]
    tag_start, tag_end, close_start = span
    open_tag = text[tag_start:tag_end]
    if "data-article-tools=" not in open_tag:
        open_tag = open_tag[:-1] + ' data-article-tools="static">'
    return text[:tag_start] + open_tag + block + text[close_start:], notes


def html_files():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        yield rel.as_posix(), path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="falla si el HTML no esta al dia")
    args = ap.parse_args()

    changed: list[str] = []
    touched = 0
    for rel, path in html_files():
        text = path.read_text(encoding="utf-8")
        if 'id="article-tools"' not in text:
            continue
        touched += 1
        new_text, notes = process(text)
        if new_text != text:
            changed.append(rel)
            if not args.check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new_text)
        for n in notes:
            print("  {0}: {1}".format(rel, n))

    if args.check:
        if changed:
            print("ARTICLE TOOLS: FAILED ({0} pagina(s) desactualizada(s))".format(len(changed)))
            for c in changed:
                print("- {0}: el bloque estatico no coincide con los titulos actuales".format(c))
            print("Ejecuta: python scripts/build-article-tools.py")
            return 1
        print("ARTICLE TOOLS: OK ({0} pagina(s) con el bloque pre-renderizado al dia)".format(touched))
        return 0

    print("ARTICLE TOOLS: {0} de {1} pagina(s) actualizada(s)".format(len(changed), touched))
    for c in changed:
        print("- {0}".format(c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
