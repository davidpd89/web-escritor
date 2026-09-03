#!/usr/bin/env python3
"""Regresion: extract_metadata() debe leer name/url/datePublished/description
del nodo Article dentro de un JSON-LD @graph, no del objeto @graph envolvente.

Bug real encontrado en produccion: todos los articulos de /cuaderno/ emiten
su JSON-LD como {"@context":..., "@graph": [Article, BreadcrumbList]}, nunca
como un Article plano en el nivel superior. extract_metadata() hacia
`node = j` (el envoltorio @graph completo) y luego `node.get('datePublished')`,
que siempre devolvia None -- asi que feed.xml en produccion no tenia NUNCA
<pubDate> en ningun item, y el orden se degradaba al fallback alfabetico por
URL en vez de la fecha de publicacion real.

Uso:
  python tests/test-build-feed.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("build_feed", ROOT / "scripts" / "build-feed.py")
build_feed = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = build_feed
_spec.loader.exec_module(build_feed)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


print("tests/test-build-feed")

GRAPH_ARTICLE_HTML = """<!DOCTYPE html>
<html><head>
<title>Titulo de pagina (fallback) | David Porto Diaz</title>
<meta name="description" content="Descripcion de pagina (fallback)." />
<link rel="canonical" href="https://davidportodiaz.com/cuaderno/ejemplo/" />
<script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
  {"@type": "Article", "headline": "Titulo real del articulo",
   "url": "https://davidportodiaz.com/cuaderno/ejemplo/",
   "datePublished": "2026-05-26", "description": "Descripcion real del articulo."},
  {"@type": "BreadcrumbList", "itemListElement": []}
]}
</script>
</head><body></body></html>"""

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    page = root / "index.html"
    page.write_text(GRAPH_ARTICLE_HTML, encoding="utf-8")

    meta = build_feed.extract_metadata(str(page))

    # 1. El titulo debe venir del nodo Article dentro de @graph, no del <title> de pagina.
    check(meta["title"] == "Titulo real del articulo", "1. title se lee del nodo Article en @graph", str(meta))

    # 2. La fecha debe venir del nodo Article -- este es el bug real: antes
    #    del fix, date quedaba en None porque se buscaba en el envoltorio @graph.
    check(meta["date"] == "2026-05-26", "2. datePublished se lee del nodo Article en @graph (no None)", str(meta))

    # 3. La URL tambien debe venir del nodo Article.
    check(meta["url"] == "https://davidportodiaz.com/cuaderno/ejemplo/", "3. url se lee del nodo Article en @graph", str(meta))

    # 4. La descripcion tambien debe venir del nodo Article, no del meta description de pagina.
    check(meta["description"] == "Descripcion real del articulo.", "4. description se lee del nodo Article en @graph", str(meta))

# 5. El pubDate resultante debe ser un RFC 2822 valido derivado de esa fecha.
rfc = build_feed.iso_to_rfc2822("2026-05-26")
check(rfc == "Tue, 26 May 2026 00:00:00 +0000", "5. iso_to_rfc2822 convierte la fecha extraida correctamente", str(rfc))

# 6. Grafo real: TODOS los articulos actuales de /cuaderno/ deben producir
#    un date no-None (si alguno vuelve a faltar, es una regresion real).
build_feed.CUADERNO = str(ROOT / "cuaderno")
items, skipped = build_feed.collect_items()
missing_dates = [it["path"] for it in items if not it.get("date")]
check(
    len(items) >= 5 and not missing_dates,
    "6. todos los articulos reales de cuaderno/ producen una fecha (ninguno cae en None)",
    f"items={len(items)} missing_dates={missing_dates}",
)

# 7. El orden resultante debe ser estrictamente por fecha descendente
#    (con desempate por URL), no el orden de os.walk.
dates = [it["date"] for it in items]
check(dates == sorted(dates, reverse=True), "7. collect_items() ordena por fecha real descendente", str(dates))

print("tests/test-build-feed: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
