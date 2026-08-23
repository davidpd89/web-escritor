#!/usr/bin/env python3
"""Verifica scripts/build-pagefind-index.py contra un repositorio git de
fixture minimo y aislado (nunca el repo real, porque el propio builder
depende de `git ls-files`).

Cubre la regla de elegibilidad de AF.1 (docs/PENDIENTE-AF-ASSISTANT-PAGEFIND-
LOCAL-SEARCH.md): una pagina publica normal se indexa; una entrada con
searchIndex:false no; una ruta gated (status != public) no; una pagina sin
entrada en el registry pero con su propio <meta robots noindex> tampoco; un
fragmento bajo data/ nunca. Y el ciclo build() -> --check detecta cuando el
indice comprometido queda desactualizado respecto al corpus elegible actual.

Uso:
  python tests/test-build-pagefind-index.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("bpi", ROOT / "scripts" / "build-pagefind-index.py")
bpi = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bpi
_spec.loader.exec_module(bpi)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


PAGE = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="robots" content="{robots}">
<title>{title}</title></head>
<body><main><h1>{title}</h1><p>Contenido de sobra para superar cualquier minimo de longitud del indexador.</p></main></body></html>
"""


def make_fixture_repo(tmp: Path) -> Path:
    (tmp / "data").mkdir()

    # 1. Pagina publica normal, sin entrada en el registry -> default-include.
    (tmp / "public.html").write_text(PAGE.format(robots="index,follow", title="Publica"), encoding="utf-8")

    # 2. Pagina con entrada status=public en el registry -> incluida.
    (tmp / "registered.html").write_text(PAGE.format(robots="index,follow", title="Registrada"), encoding="utf-8")

    # 3. searchIndex:false en el registry -> excluida aunque no tenga noindex.
    (tmp / "privada-busqueda.html").write_text(PAGE.format(robots="index,follow", title="Privada busqueda"), encoding="utf-8")

    # 4. status distinto de public (gated/staging) -> excluida.
    (tmp / "gated").mkdir()
    (tmp / "gated" / "index.html").write_text(PAGE.format(robots="index,follow", title="Gated"), encoding="utf-8")

    # 5. Sin entrada en el registry, pero con su propio <meta robots noindex>.
    (tmp / "404.html").write_text(PAGE.format(robots="noindex,follow", title="No encontrada"), encoding="utf-8")

    # 6. Fragmento bajo data/ -> siempre excluido, tenga o no <html>.
    (tmp / "data" / "fragment.html").write_text("<p>Solo un fragmento inyectado en otra pagina.</p>", encoding="utf-8")

    registry = {
        "schema_version": 1,
        "defaults": {"status": "public", "searchIndex": True},
        "entries": [
            {"id": "registered", "sourceFile": "registered.html", "url": "/registered.html"},
            {"id": "privada", "sourceFile": "privada-busqueda.html", "url": "/privada-busqueda.html", "searchIndex": False},
            {"id": "gated", "sourceFile": "gated/index.html", "url": "/gated/", "status": "noindex"},
        ],
    }
    (tmp / "data" / "content-registry.json").write_text(json.dumps(registry), encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "fixture"],
        cwd=tmp, check=True,
    )
    return tmp


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = make_fixture_repo(Path(tmp_str))

        pages = bpi.eligible_pages(tmp)

        check("public.html" in pages, "1. pagina publica sin entrada en el registry -> incluida (default-include)")
        check("registered.html" in pages, "2. entrada status=public en el registry -> incluida")
        check("privada-busqueda.html" not in pages, "3. searchIndex:false -> excluida")
        check("gated/index.html" not in pages, "4. status != public (gated/staging) -> excluida")
        check("404.html" not in pages, "5. sin entrada en el registry pero con <meta robots noindex> propio -> excluida")
        check("data/fragment.html" not in pages, "6. fragmento bajo data/ -> siempre excluida")
        check(pages == sorted(pages), "7. eligible_pages() devuelve orden determinista (sorted)")

    # --- ciclo build() / --check sobre un pagefind real, sin red externa ---
    # tool-tests.yml ejecuta tests/test-*.py sin Node/npm instalados (a
    # diferencia de assistant-hardening-qa.yml, que si lo tiene). Sin `npx`
    # en el PATH esta parte no es comprobable aqui -- se omite explicitamente
    # en vez de contarla como fallo, para que este mismo fichero sirva en
    # ambos workflows sin duplicar el test de elegibilidad.
    if shutil.which("npx") is None:
        print("  skip 8-12. npx no disponible en este entorno (ver assistant-hardening-qa.yml para el ciclo build/--check completo)")
        if failures:
            print(f"\nFAIL: {len(failures)} check(s) de test-build-pagefind-index")
            raise SystemExit(1)
        print("\ntest-build-pagefind-index: OK (elegibilidad; ciclo build/--check omitido sin npx)")
        return

    with tempfile.TemporaryDirectory() as tmp_str2:
        tmp2 = make_fixture_repo(Path(tmp_str2))
        out_dir = tmp2 / "pagefind"
        src_dir = tmp2 / ".pagefind-src"

        try:
            rc_build = bpi.build(tmp2, out_dir, src_dir)
            check(rc_build == 0, "8. build() termina en 0 sobre el fixture")
            check((out_dir / "pagefind.js").exists(), "9. build() produce pagefind.js")
            check(not src_dir.exists(), "10. build() limpia el arbol temporal .pagefind-src tras indexar")

            rc_check_clean = bpi.check(tmp2, out_dir)
            check(rc_check_clean == 0, "11. --check pasa justo despues de construir")

            # Anadir una pagina publica nueva sin regenerar el indice: --check
            # debe detectar la desincronizacion (no solo asumir que sigue OK).
            (tmp2 / "nueva.html").write_text(PAGE.format(robots="index,follow", title="Nueva"), encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=tmp2, check=True)
            subprocess.run(
                ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "nueva pagina"],
                cwd=tmp2, check=True,
            )
            rc_check_stale = bpi.check(tmp2, out_dir)
            check(rc_check_stale == 1, "12. --check falla tras anadir una pagina elegible sin regenerar el indice")
        except FileNotFoundError as exc:
            check(False, "8-12. pagefind CLI no disponible en este entorno", str(exc))
        except Exception as exc:  # pragma: no cover - visibilidad de fallo real
            check(False, "8-12. build()/check() del fixture no lanzaron una excepcion inesperada", str(exc))

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) de test-build-pagefind-index")
        raise SystemExit(1)
    print("\ntest-build-pagefind-index: OK")


if __name__ == "__main__":
    run()
