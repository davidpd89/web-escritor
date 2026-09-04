#!/usr/bin/env python3
"""Comprueba que cada entidad JSON-LD compartida (autor, libros, editoriales)
use SIEMPRE el mismo @id en todo el sitio.

Por qué hace falta un checker propio: check-jsonld-absolute-urls.py ya obliga a
que los @id sean URLs absolutas, pero eso no impide que la misma obra se declare
con dos identificadores absolutos distintos en páginas distintas — que es lo que
pasaba con Las manecillas del recuerdo (`/#book-manecillas` en la home frente a
`/las-manecillas-del-recuerdo/#book-manecillas` en /libros/) y con Samuel entre
mundos (`/#book-samuel` frente a `/libros/samuel-entre-mundos/#book`). Para un
consumidor RDF eso no es una entidad citada dos veces: son dos entidades
distintas, y las señales (premios, reseñas, enlaces) se reparten entre ambas en
vez de acumularse.

Regla: para cada `name` de una entidad de tipo vigilado, todos los @id no nulos
que aparezcan en el sitio deben coincidir. Las obras de terceros (recomendaciones
literarias) no llevan @id y se ignoran: no son entidades nuestras.

Uso:
  python scripts/check-canonical-entity-ids.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "scripts", "archive",
    "WEB DAVID PORTO nuevas ideas", ".codex_work", ".preview-dist", "dist",
    ".claude",
}
WATCHED_TYPES = {"Book", "Person", "Organization"}
LD_BLOCK = re.compile(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)

# Identificadores canonicos fijados. La comprobacion de consistencia por si sola
# no basta: si un cambio masivo moviera TODAS las paginas al mismo @id
# equivocado, seguirian siendo consistentes entre si y el checker pasaria,
# mientras los buscadores empezarian a acumular las senales en una entidad
# nueva y vacia. Anclarlos aqui convierte eso en un fallo.
EXPECTED_IDS = {
    "David Porto Díaz": "https://davidportodiaz.com/#author",
    "Las manecillas del recuerdo": "https://davidportodiaz.com/#book-manecillas",
    "Samuel entre mundos": "https://davidportodiaz.com/#book-samuel",
}


def html_files():
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        yield rel.as_posix(), path


def types_of(node: dict) -> set[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {t for t in raw if isinstance(t, str)}
    return set()


def walk(node, found):
    if isinstance(node, dict):
        # A node that declares exampleOfWork (2026-09-04, Manecillas Kindle
        # launch) is explicitly modeling itself as one SPECIFIC EDITION of
        # another watched entity -- schema.org's own pattern for "same work,
        # different format" (e.g. a paperback's #book-manecillas and its
        # Kindle edition #book-manecillas-kindle, linked via
        # workExample/exampleOfWork). That's a deliberate second @id sharing
        # the work's name, not the accidental entity-fragmentation bug this
        # checker exists to catch, so it's excluded from the collision check
        # below entirely (its own @id is never itself required to be the
        # canonical one).
        if types_of(node) & WATCHED_TYPES and "exampleOfWork" not in node:
            name, entity_id = node.get("name"), node.get("@id")
            if isinstance(name, str) and isinstance(entity_id, str):
                found.append((name.strip(), entity_id.strip()))
        for value in node.values():
            walk(value, found)
    elif isinstance(node, list):
        for value in node:
            walk(value, found)


def main() -> int:
    by_name: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for rel, path in html_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for block in LD_BLOCK.finditer(text):
            try:
                data = json.loads(block.group(1))
            except json.JSONDecodeError:
                continue  # validate_jsonld.py es quien reporta JSON inválido
            found: list[tuple[str, str]] = []
            walk(data, found)
            for name, entity_id in found:
                by_name[name][entity_id].add(rel)

    errors = []
    for name, ids in sorted(by_name.items()):
        if len(ids) > 1:
            detail = "; ".join(
                f"{entity_id} ({', '.join(sorted(files))})" for entity_id, files in sorted(ids.items())
            )
            errors.append(f'"{name}" usa {len(ids)} @id distintos: {detail}')

    for name, expected in EXPECTED_IDS.items():
        seen = by_name.get(name)
        if not seen:
            errors.append(f'"{name}" no aparece con @id en ninguna página (se esperaba {expected})')
            continue
        wrong = sorted(i for i in seen if i != expected)
        if wrong:
            files = sorted({f for i in wrong for f in seen[i]})
            errors.append(
                f'"{name}" debe usar el @id canónico {expected}, pero aparece como '
                f'{", ".join(wrong)} en: {", ".join(files)}'
            )

    if errors:
        print(f"CANONICAL ENTITY IDs: FAILED ({len(errors)})")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"CANONICAL ENTITY IDs: OK ({len(by_name)} entidades con @id, todas consistentes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
