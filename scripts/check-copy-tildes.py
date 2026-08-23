#!/usr/bin/env python3
"""Busca texto publicado en espanol al que le faltan las tildes.

Por que existe: ha pasado dos veces en este repositorio, y ninguna la detecto
ningun checker. La pagina /metodologia-editorial/ se genero entera sin acentos
("Metodologia", "Como", "informacion", "recepcion", incluso "David Porto Diaz"),
y el generador de kit de prensa mostraba al usuario "el maximo es 10". Las dos
salieron a revision manual. Es exactamente el tipo de defecto que un ordenador
detecta mejor que una lectura: no rompe nada, no falla ningun test, y solo se ve
si alguien se fija.

Que mira: el texto visible del HTML y los literales de cadena del JavaScript que
puedan acabar en pantalla.

Que NO mira: identificadores, claves de datos, nombres de fichero, slugs,
atributos tecnicos y URLs. Ahi la forma sin acentos es la correcta.

La lista de palabras es deliberadamente corta: solo formas que en espanol llevan
tilde SIEMPRE, sin homografo valido. "publico" (yo publico), "genero" (yo
genero), "titulo" (yo titulo), "mas" (conjuncion) o "como" (verbo/conjuncion)
son palabras correctas sin tilde segun el contexto, asi que quedan fuera: un
checker que grita cuando el texto esta bien acaba ignorandose.

Uso:
  python scripts/check-copy-tildes.py
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
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "archive",
    "WEB DAVID PORTO nuevas ideas", ".codex_work", ".preview-dist", "dist",
    "pagefind",  # vendored JS from the `pagefind` npm package, not our copy
}

# Solo formas que siempre llevan tilde. Ver el docstring: nada con homografo.
#
# Ojo con los plurales: en espanol las palabras terminadas en -ion PIERDEN la
# tilde al pluralizar ("opción" -> "opciones", "versión" -> "versiones"). En una
# primera version estaban en la lista y el checker senalaba texto perfectamente
# correcto en seis paginas, que es la forma mas rapida de que un checker deje de
# leerse. Solo van los singulares.
ACCENTED_FORM = {
    "maximo": "máximo", "maxima": "máxima", "maximos": "máximos", "maximas": "máximas",
    "minimo": "mínimo", "minima": "mínima", "tamano": "tamaño", "tamanos": "tamaños",
    "anadir": "añadir", "tambien": "también", "aqui": "aquí", "asi": "así",
    "segun": "según", "informacion": "información", "seleccion": "selección",
    "descripcion": "descripción", "generacion": "generación", "opcion": "opción",
    "version": "versión", "edicion": "edición", "pagina": "página",
    "paginas": "páginas", "linea": "línea", "lineas": "líneas",
    "parrafo": "párrafo", "parrafos": "párrafos", "capitulo": "capítulo",
    "capitulos": "capítulos", "analisis": "análisis", "estadistica": "estadística",
    "metrica": "métrica", "metricas": "métricas", "rapido": "rápido", "rapida": "rápida",
    "unico": "único", "unica": "única", "ultimo": "último", "ultima": "última",
    "proximo": "próximo", "proxima": "próxima", "despues": "después",
    "ademas": "además", "todavia": "todavía", "ingles": "inglés", "frances": "francés",
    "aleman": "alemán", "ortografia": "ortografía", "silaba": "sílaba",
    "silabas": "sílabas", "puntuacion": "puntuación", "acentuacion": "acentuación",
    "deberia": "debería", "podria": "podría", "estara": "estará", "habra": "habrá",
    "deteccion": "detección", "conexion": "conexión", "revision": "revisión",
    "actualizacion": "actualización", "comprobacion": "comprobación",
    "representacion": "representación", "garantia": "garantía", "traves": "través",
    "historico": "histórico", "historica": "histórica", "articulo": "artículo",
    "articulos": "artículos", "categoria": "categoría", "corazon": "corazón",
    "metodologia": "metodología", "recepcion": "recepción", "clasico": "clásico",
    "clasica": "clásica", "practico": "práctico", "practica": "práctica",
    "tecnico": "técnico", "tecnica": "técnica", "publicacion": "publicación",
    "traduccion": "traducción", "narracion": "narración", "ficcion": "ficción",
    "cronologia": "cronología", "biografia": "biografía", "quiza": "quizá",
}
WORD_RE = re.compile(
    r"\b(" + "|".join(sorted(ACCENTED_FORM, key=len, reverse=True)) + r")\b", re.IGNORECASE
)

# Literales de cadena de JS. El backtick se construye por codigo para que no
# haya dudas sobre el escapado dentro del propio patron.
_BS = chr(92)
_QUOTES = "['" + '"' + chr(96) + "]"
JS_STRING_RE = re.compile(
    "(" + _QUOTES + ")((?:" + _BS + _BS + ".|(?!" + _BS + "1)[^" + _BS + _BS + _BS + "n])*)" + _BS + "1"
)

SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")
ENTITY_RE = re.compile(r"&[a-z#0-9]+;", re.I)


def html_visible_text(src: str) -> list[tuple[int, str, str]]:
    """Texto que ve el lector, con el numero de linea aproximado."""
    out: list[tuple[int, str, str]] = []
    cleaned = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    cleaned = SCRIPT_STYLE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), cleaned)
    pos = 0
    for m in TAG_RE.finditer(cleaned):
        chunk = cleaned[pos:m.start()]
        if chunk.strip():
            clean = ENTITY_RE.sub(" ", chunk)
            out.append((cleaned[:pos].count("\n") + 1, clean, clean))
        pos = m.end()
    tail = cleaned[pos:]
    if tail.strip():
        clean = ENTITY_RE.sub(" ", tail)
        out.append((cleaned[:pos].count("\n") + 1, clean, clean))
    return out


def js_strings(src: str) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for m in JS_STRING_RE.finditer(src):
        text = m.group(2)
        # Una frase para el usuario tiene espacios; sin ellos es un identificador,
        # una clase CSS, una clave o una ruta.
        if len(text) < 8 or " " not in text:
            continue
        if text.startswith(("http", "/", "./", "../")) or "://" in text:
            continue
        line_no = src[:m.start()].count("\n") + 1
        lines = src.splitlines()
        context = lines[line_no - 1] if line_no <= len(lines) else text
        out.append((line_no, text, context))
    return out


def is_technical_use(text: str, word: str, context: str = "") -> bool:
    """Descarta los usos donde la forma sin tilde es la correcta.

    Tres casos reales de este repositorio:

    - Nombre de fichero o ruta: el README del kit de prensa lista
      `textos/biografia-corta.txt`, y ese fichero se llama asi de verdad.
    - Termino de busqueda: book-page-audit-rules.js rastrea el texto de una
      pagina ajena y necesita las dos grafias, por lo que escribe
      'primer capitulo','primer capítulo' una al lado de la otra. Por eso se
      mira la LINEA entera y no solo el literal: las dos variantes son cadenas
      distintas, y comparando solo dentro de una nunca se veria la pareja.
    - Slug o identificador pegado a guiones bajos o barras.
    """
    accented = ACCENTED_FORM.get(word)
    haystack = (context or text).lower()
    if accented and accented.lower() in haystack:
        return True
    for m in re.finditer(re.escape(word), text, re.IGNORECASE):
        before = text[max(0, m.start() - 1):m.start()]
        after = text[m.end():m.end() + 5]
        if before in ("/", "-", "_", "."):
            continue
        if re.match(r"[-_/.][a-z0-9]", after, re.I):
            continue
        return False  # al menos un uso es texto normal
    return True


def files():
    for pattern in ("*.html", "*.js"):
        for path in sorted(ROOT.rglob(pattern)):
            rel = path.relative_to(ROOT)
            if any(part in SKIP_PARTS for part in rel.parts):
                continue
            yield rel.as_posix(), path


def main() -> int:
    findings: list[str] = []
    scanned = 0
    for rel, path in files():
        src = path.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        pieces = html_visible_text(src) if path.suffix == ".html" else js_strings(src)
        for line, text, context in pieces:
            for word in sorted(set(w.lower() for w in WORD_RE.findall(text))):
                if is_technical_use(text, word, context):
                    continue
                snippet = re.sub(r"\s+", " ", text).strip()[:110]
                findings.append(
                    f'{rel}:{line}: "{word}" deberia ser "{ACCENTED_FORM[word]}" — {snippet}'
                )

    if findings:
        print(f"COPY TILDES: FAILED ({len(findings)})")
        for f in findings:
            print(f"- {f}")
        return 1
    print(f"COPY TILDES: OK ({scanned} ficheros HTML/JS revisados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
