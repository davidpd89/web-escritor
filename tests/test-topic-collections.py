#!/usr/bin/env python3
"""QA del doc 55 (seccion 13) contra el motor real de build-topic-collections.py.

- coleccion ready con 2 items -> FAIL;
- URL externa -> FAIL;
- URL duplicada -> FAIL;
- coleccion valida de 3 piezas -> genera hub;
- serie valida -> mantiene orden;
- --check detecta salida desactualizada;
- HTML generado con un H1 y enlaces <a> rastreables.

Uso:
  python tests/test-topic-collections.py
"""
from __future__ import annotations

import copy
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
_spec = importlib.util.spec_from_file_location("btc", ROOT / "scripts" / "build-topic-collections.py")
btc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = btc
_spec.loader.exec_module(btc)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def article(root: Path, rel: str, title: str = "Artículo") -> None:
    p = root / rel.strip("/") / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    canonical = f"https://davidportodiaz.com{rel}"
    p.write_text(
        f'<!doctype html><html><head><title>{title}</title>'
        f'<link rel="canonical" href="{canonical}"></head><body><h1>{title}</h1></body></html>',
        encoding="utf-8",
    )


print("tests/test-topic-collections")

BASE_DATA = {
    "schema_version": 1,
    "collections": [
        {
            "slug": "coleccion-real",
            "status": "ready",
            "mode": "collection",
            "title": "Colección real",
            "description": "Descripción.",
            "intro": "Introducción editorial.",
            "updated": "2026-08-21",
            "items": [
                {"url": "/cuaderno/a/", "title": "A", "description": "Pieza A.", "type": "articulo"},
                {"url": "/cuaderno/b/", "title": "B", "description": "Pieza B.", "type": "articulo"},
                {"url": "/cuaderno/c/", "title": "C", "description": "Pieza C.", "type": "articulo"},
            ],
        },
        {
            "slug": "serie-real",
            "status": "ready",
            "mode": "series",
            "title": "Serie real",
            "description": "Descripción de la serie.",
            "intro": "Estas entregas van en orden.",
            "updated": "2026-08-21",
            "items": [
                {"url": "/cuaderno/parte-2/", "title": "Segunda entrega", "description": "...", "type": "proceso"},
                {"url": "/cuaderno/parte-1/", "title": "Primera entrega", "description": "...", "type": "proceso"},
                {"url": "/cuaderno/parte-3/", "title": "Tercera entrega", "description": "...", "type": "proceso"},
            ],
        },
    ],
}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for coll in BASE_DATA["collections"]:
        for item in coll["items"]:
            article(root, item["url"], item["title"])
    data_path = root / "data.json"
    data_path.write_text(json.dumps(BASE_DATA, ensure_ascii=False), encoding="utf-8")

    # 1. colección válida de 3 piezas -> genera hub
    n, ready = btc.build(data_path, root, False)
    check(n == 2 and ready == 2, "las dos colecciones válidas (3 piezas cada una) generan hub", f"n={n} ready={ready}")
    hub = (root / "cuaderno" / "temas" / "coleccion-real" / "index.html").read_text(encoding="utf-8")
    check("<h1>" in hub, "el hub generado tiene un H1")
    check(hub.count('<a href="/cuaderno/') >= 3, "el hub tiene enlaces <a> rastreables a las 3 piezas")

    # serie válida -> mantiene el ORDEN DE ENTRADA del JSON (no reordena
    # alfabéticamente): "Segunda entrega" debe aparecer numerada 1, antes que
    # "Primera entrega" numerada 2, porque así está en items[].
    serie_hub = (root / "cuaderno" / "temas" / "serie-real" / "index.html").read_text(encoding="utf-8")
    pos_segunda = serie_hub.find("Segunda entrega")
    pos_primera = serie_hub.find("Primera entrega")
    check(0 < pos_segunda < pos_primera, "la serie mantiene el orden de items[], no lo reordena")
    check("<ol class=\"topic-list\"" in serie_hub, "una serie se renderiza como <ol> (orden), no <ul>")
    check('<ul class="topic-list"' in hub, "una colección libre se renderiza como <ul>, no <ol>")

    # --check detecta salida al día
    n2, ready2 = btc.build(data_path, root, True)
    check(ready2 == ready, "--check confirma que la salida recién generada está al día")

    # --check detecta salida DESACTUALIZADA: se borra un hub a mano y se
    # vuelve a comprobar. En modo --check, build() no lanza: devuelve
    # ready=-1 como señal de deriva (ver build-topic-collections.py).
    (root / "cuaderno" / "temas" / "coleccion-real" / "index.html").unlink()
    n3, ready3 = btc.build(data_path, root, True)
    check(ready3 == -1, "--check detecta que falta un hub ya generado antes (salida desactualizada)")

# 2. colección ready con 2 items -> FAIL
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = copy.deepcopy(BASE_DATA)
    bad["collections"] = [bad["collections"][0]]
    bad["collections"][0]["items"] = bad["collections"][0]["items"][:2]
    for item in bad["collections"][0]["items"]:
        article(root, item["url"], item["title"])
    data_path = root / "data.json"
    data_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    try:
        btc.build(data_path, root, False)
        check(False, "ready con 2 piezas debe fallar la validación")
    except btc.ValidationError as exc:
        check("3 piezas" in str(exc) or "al menos 3" in str(exc), "ready con 2 piezas falla con el motivo correcto", str(exc))

# 3. URL externa -> FAIL
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = copy.deepcopy(BASE_DATA)
    bad["collections"] = [bad["collections"][0]]
    bad["collections"][0]["items"][0]["url"] = "https://example.com/externo/"
    data_path = root / "data.json"
    data_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    try:
        btc.build(data_path, root, False)
        check(False, "una URL externa debe rechazar el build")
    except btc.ValidationError as exc:
        check("interna" in str(exc) or "externa" in str(exc), "una URL externa se rechaza con el motivo correcto", str(exc))

# 4. URL duplicada -> FAIL
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = copy.deepcopy(BASE_DATA)
    bad["collections"] = [bad["collections"][0]]
    bad["collections"][0]["items"][1]["url"] = bad["collections"][0]["items"][0]["url"]
    data_path = root / "data.json"
    data_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    try:
        btc.build(data_path, root, False)
        check(False, "una URL duplicada dentro de la colección debe rechazar el build")
    except btc.ValidationError as exc:
        check("duplicada" in str(exc), "una URL duplicada se rechaza con el motivo correcto", str(exc))

# 5. --root: una pieza en noindex debe rechazar el build (contrato compartido
# con build-surprise-content.py, doc 59).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = copy.deepcopy(BASE_DATA)
    data["collections"] = [data["collections"][0]]
    for item in data["collections"][0]["items"]:
        article(root, item["url"], item["title"])
    # una de las piezas pasa a noindex
    p = root / "cuaderno" / "b" / "index.html"
    p.write_text(p.read_text(encoding="utf-8").replace("</head>", '<meta name="robots" content="noindex"></head>'), encoding="utf-8")
    data_path = root / "data.json"
    data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        btc.build(data_path, root, False)
        check(False, "una pieza en noindex debe rechazar el build")
    except btc.ValidationError as exc:
        check("noindex" in str(exc), "una pieza en noindex se rechaza con el motivo correcto", str(exc))

# 6. Contra el repositorio real: la colección "ready" real de este sitio
# (fantasia-de-portales) debe validar y su salida debe estar al día en el
# repo (no solo en un fixture temporal).
data_real = ROOT / "data" / "topic-collections.json"
n_real, ready_real = btc.build(data_real, ROOT, True)
check(ready_real != -1, "contra el repo real: la salida en cuaderno/temas/ está al día")
check(ready_real == 1, "contra el repo real: exactamente 1 colección publicada (fantasia-de-portales)", str(ready_real))

print("tests/test-topic-collections: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
