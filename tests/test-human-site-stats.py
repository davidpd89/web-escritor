#!/usr/bin/env python3
"""Fixture del propio documento 60 (seccion "QA"), verificado contra el motor real.

El documento dice haber probado: 2 libros indexables + 1 noindex, 3 articulos
indexables + 1 noindex, 2 herramientas, 1 bloque data-public-sample, y una
canonical duplicada como caso de error. Nada de eso tenia un test hasta ahora.

De paso, esta es la pieza que descubrio que la clasificacion "PENDIENTE/
HUERFANO — nunca conectado a un output visible" del catalogo de docs de
20/08/2026 era un falso negativo: autor.html SI tiene los marcadores
`human-site-stats:start/end` y el CSS enlazado. Solo estaba desactualizado.
No estaba huerfano, estaba parado.

Actualizado 22/08/2026: libros y herramientas ya no se cuentan por prefijo de
URL sino desde su registro canonico. Se anaden aqui los dos casos que ese
cambio hace posibles —registro y HTML en desacuerdo— y, sobre todo, la
comprobacion que faltaba: **el sitio no puede volver a publicar dos numeros
distintos de herramientas**. Esa incoherencia (17 en el hub, 15 en "Esta web,
en cifras") sobrevivio a una CI verde justamente porque cada numero era
correcto segun su propio metodo y nadie comparaba los dos.

Uso:
  python tests/test-human-site-stats.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "build_human_site_stats", ROOT / "scripts" / "build-human-site-stats.py"
)
bhs = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bhs  # @dataclass necesita el modulo ya registrado
_spec.loader.exec_module(bhs)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def page(rel: str, canonical: str, noindex: bool = False, extra: str = "") -> tuple[str, str]:
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    return rel, (
        f'<!doctype html><html><head><link rel="canonical" href="{canonical}">'
        f"{robots}</head><body>{extra}</body></html>"
    )


def build_root(tmp: str, pages: list[tuple[str, str]], registry: dict, hub: dict) -> Path:
    root = Path(tmp)
    for rel, content in pages:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "content-registry.json").write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    (data / "tools-hub.json").write_text(json.dumps(hub, ensure_ascii=False), encoding="utf-8")
    return root


def work(entry_id: str, url: str, source: str, status: str | None = None) -> dict:
    entry = {"id": entry_id, "url": url, "type": "work", "hubId": "works-hub", "sourceFile": source}
    if status:
        entry["status"] = status
    return entry


BASE_PAGES = [
    # Las dos obras publicas viven en prefijos distintos a proposito: es
    # exactamente el caso que rompia el contador anterior.
    page("libros/samuel/index.html", "https://davidportodiaz.com/libros/samuel/"),
    page("manecillas/index.html", "https://davidportodiaz.com/manecillas/"),
    page("jaula/index.html", "https://davidportodiaz.com/jaula/", noindex=True),
    page("libros/index.html", "https://davidportodiaz.com/libros/"),
    page("cuaderno/a/index.html", "https://davidportodiaz.com/cuaderno/a/"),
    page("cuaderno/b/index.html", "https://davidportodiaz.com/cuaderno/b/"),
    page("cuaderno/c/index.html", "https://davidportodiaz.com/cuaderno/c/"),
    page("cuaderno/d/index.html", "https://davidportodiaz.com/cuaderno/d/", noindex=True),
    page("herramientas/x/index.html", "https://davidportodiaz.com/herramientas/x/"),
    page(
        "recursos/y/index.html",
        "https://davidportodiaz.com/recursos/y/",
        extra='<p>Antes.</p><div data-public-sample>Cinco palabras de muestra aqui.</div><p>Despues, no cuenta.</p>',
    ),
]
BASE_REGISTRY = {
    "defaults": {"status": "public"},
    "entries": [
        {"id": "works-hub", "url": "/libros/", "type": "work", "hubId": "works-hub", "sourceFile": "libros/index.html"},
        work("work-samuel", "/libros/samuel/", "libros/samuel/index.html"),
        work("work-manecillas", "/manecillas/", "manecillas/index.html"),
        work("work-jaula", "/jaula/", "jaula/index.html", status="noindex"),
        {"id": "some-article", "url": "/cuaderno/a/", "type": "article"},
    ],
}
# Una herramienta bajo /herramientas/ y otra fuera: el hub cuenta las dos, el
# glob antiguo solo veia la primera.
BASE_HUB = {
    "tools": [
        {"slug": "x", "href": "/herramientas/x/"},
        {"slug": "y", "href": "/recursos/y/"},
    ]
}


print("tests/test-human-site-stats")

with tempfile.TemporaryDirectory() as tmp:
    root = build_root(tmp, BASE_PAGES, BASE_REGISTRY, BASE_HUB)
    items = bhs.stats(root)
    by_key = {i["key"]: i["value"] for i in items}
    check(
        by_key.get("books") == 2,
        "cuentan las 2 obras publicas del registro, no el hub ni la noindex, y da igual el prefijo de URL",
        str(by_key),
    )
    check(by_key.get("articles") == 3, "3 articulos indexables cuentan, el noindex no", str(by_key))
    check(
        by_key.get("tools") == 2,
        "las herramientas salen del registro del hub, incluida la que vive fuera de /herramientas/",
        str(by_key),
    )
    # "Cinco palabras de muestra aqui." = 5 palabras; el texto fuera del bloque
    # data-public-sample ("Antes."/"Despues, no cuenta.") no debe sumarse.
    check(
        by_key.get("sample_words") == 5,
        "solo las palabras dentro de data-public-sample cuentan",
        str(by_key),
    )

    fragment = bhs.render(items, "2026-08-21")
    check("<script" not in fragment.lower(), "el fragmento no lleva JavaScript (doc 60: sin JS en cliente)")

# El registro dice que una obra es publica y el HTML dice noindex: contarla
# publicaria una cifra falsa. Tiene que reventar el build, no redondear.
with tempfile.TemporaryDirectory() as tmp:
    registry = json.loads(json.dumps(BASE_REGISTRY))
    for entry in registry["entries"]:
        if entry["id"] == "work-jaula":
            del entry["status"]  # el registro la declara publica...
    root = build_root(tmp, BASE_PAGES, registry, BASE_HUB)  # ...pero su pagina sigue noindex
    try:
        bhs.stats(root)
        check(False, "una obra publica en el registro con pagina noindex debe rechazar el build")
    except ValueError as exc:
        check(
            "noindex" in str(exc),
            "una obra publica en el registro con pagina noindex debe rechazar el build",
            str(exc),
        )

# Lo mismo por el otro lado: una herramienta anunciada cuya pagina no existe.
with tempfile.TemporaryDirectory() as tmp:
    hub = {"tools": BASE_HUB["tools"] + [{"slug": "fantasma", "href": "/herramientas/fantasma/"}]}
    root = build_root(tmp, BASE_PAGES, BASE_REGISTRY, hub)
    try:
        bhs.stats(root)
        check(False, "una herramienta anunciada sin pagina debe rechazar el build")
    except ValueError as exc:
        check("no existe" in str(exc), "una herramienta anunciada sin pagina debe rechazar el build", str(exc))

# Canonical duplicada: caso de error explicito del documento. Sigue vivo en el
# unico contador que aun recorre el disco por prefijo (los articulos).
with tempfile.TemporaryDirectory() as tmp:
    dup = "https://davidportodiaz.com/cuaderno/a/"
    pages = [
        page("cuaderno/a/index.html", dup),
        page("cuaderno/otro/index.html", dup),
    ]
    root = build_root(tmp, pages, {"defaults": {"status": "public"}, "entries": []}, {"tools": []})
    try:
        bhs.stats(root)
        check(False, "una canonical duplicada debe rechazar el build")
    except ValueError as exc:
        check("duplicad" in str(exc), "una canonical duplicada debe rechazar el build", str(exc))

# ---------------------------------------------------------------------------
# Contra el repositorio real: el sitio solo puede publicar UN numero de
# herramientas. Esto es lo que faltaba.
# ---------------------------------------------------------------------------
published = json.loads((ROOT / "data" / "site-human-stats.generated.json").read_text(encoding="utf-8"))
published_by_key = {i["key"]: i["value"] for i in published["stats"]}
hub_html = (ROOT / "herramientas" / "index.html").read_text(encoding="utf-8")
hub_headline = re.search(r">(\d+) herramientas<", hub_html)
check(bool(hub_headline), "el hub publica un titular con el numero de herramientas")
if hub_headline:
    check(
        published_by_key.get("tools") == int(hub_headline.group(1)),
        "«Esta web, en cifras» y el titular de /herramientas/ publican el mismo numero",
        f'cifras={published_by_key.get("tools")} hub={hub_headline.group(1)}',
    )

registry_works = [
    entry
    for entry in json.loads((ROOT / "data" / "content-registry.json").read_text(encoding="utf-8"))["entries"]
    if entry.get("type") == "work" and entry.get("id") != entry.get("hubId") and entry.get("status", "public") == "public"
]
check(
    published_by_key.get("books") == len(registry_works),
    "«Libros publicados» coincide con las obras publicas del registro de contenido",
    f'cifras={published_by_key.get("books")} registro={len(registry_works)}',
)
check(
    published_by_key.get("books", 0) >= 2,
    "las dos obras publicadas cuentan (Manecillas vive fuera de /libros/)",
    str(published_by_key),
)

print("tests/test-human-site-stats: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
