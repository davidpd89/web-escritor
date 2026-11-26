#!/usr/bin/env python3
"""Verifica scripts/check-responsive-images.py con fixtures positivos y
negativos, sin depender del repo real (H.3, 2026-08-23).

Uso:
  python tests/test-check-responsive-images.py
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
_spec = importlib.util.spec_from_file_location("cri", ROOT / "scripts" / "check-responsive-images.py")
cri = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cri
_spec.loader.exec_module(cri)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def audit(html: str, tmp: Path) -> list[str]:
    page = tmp / "page.html"
    page.write_text(html, encoding="utf-8")
    return cri.audit_file(page, tmp)


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # Positivo: img de contenido sin width/height -> se detecta.
        errors = audit('<img src="/assets/foto-real.webp" alt="Foto">', tmp)
        check(any("MISSING_DIMENSIONS" in e for e in errors), "img de contenido sin width/height se detecta")

        # Negativo: la misma img con width/height -> no se detecta.
        errors = audit('<img src="/assets/foto-real.webp" alt="Foto" width="800" height="600">', tmp)
        check(not any("MISSING_DIMENSIONS" in e for e in errors), "img con width/height no genera falso positivo")

        # Negativo: icono pequeno sin dimensiones pero con clase icon -> excluido.
        errors = audit('<img src="/assets/x.png" alt="" class="icon-social">', tmp)
        check(not any("MISSING_DIMENSIONS" in e for e in errors), "icono con clase 'icon' no genera falso positivo")

        # Negativo: SVG -> excluido.
        errors = audit('<img src="/assets/x.svg" alt="">', tmp)
        check(not any("MISSING_DIMENSIONS" in e for e in errors), "SVG no genera falso positivo")

        # Negativo: decorativo (aria-hidden) -> excluido.
        errors = audit('<img src="/assets/deco.png" alt="" aria-hidden="true">', tmp)
        check(not any("MISSING_DIMENSIONS" in e for e in errors), "aria-hidden=true no genera falso positivo")

        # Positivo: srcset con descriptor de ancho sin sizes -> se detecta.
        errors = audit(
            '<img src="/assets/a-320.webp" srcset="/assets/a-320.webp 320w, /assets/a-768.webp 768w" width="768" height="512" alt="">',
            tmp,
        )
        check(any("SRCSET_WITHOUT_SIZES" in e for e in errors), "srcset con descriptor 'w' sin sizes se detecta")

        # Negativo: srcset con sizes -> no se detecta.
        errors = audit(
            '<img src="/assets/a-320.webp" srcset="/assets/a-320.webp 320w, /assets/a-768.webp 768w" sizes="100vw" width="768" height="512" alt="">',
            tmp,
        )
        check(not any("SRCSET_WITHOUT_SIZES" in e for e in errors), "srcset con sizes no genera falso positivo")

        # Positivo: candidato de srcset roto (fichero inexistente) -> se detecta.
        errors = audit(
            '<img src="/assets/real.webp" srcset="/assets/no-existe-1234.webp 320w" sizes="100vw" width="320" height="200" alt="">',
            tmp,
        )
        check(any("BROKEN_SRCSET_CANDIDATE" in e for e in errors), "candidato de srcset roto se detecta")

        # Positivo: loading=lazy + fetchpriority=high es incoherente -> se detecta.
        errors = audit(
            '<img src="/assets/real.webp" width="320" height="200" alt="" loading="lazy" fetchpriority="high">',
            tmp,
        )
        check(any("INCOHERENT_LOADING" in e for e in errors), "loading=lazy + fetchpriority=high se detecta")

        # Negativo: pagina noindex -> no se audita en absoluto.
        page = tmp / "noindex.html"
        # Portadas del almacén externo (#1588): no están en el checkout; el despliegue las reescribe a su URL.
        import json
        (tmp / "data").mkdir(exist_ok=True)
        (tmp / "data/reading-covers-store.json").write_text(json.dumps({
            "base_url": "https://example.github.io/portadas", "archivos": ["isbn-1.webp", "isbn-1-320.webp"],
            "sha256": {"isbn-1.webp": "a" * 64, "isbn-1-320.webp": "b" * 64}}), encoding="utf-8")
        img = ('<img src="/assets/reading-covers/{n}.webp" srcset="/assets/reading-covers/{n}-320.webp 320w, '
               '/assets/reading-covers/{n}.webp 640w" sizes="100px" width="100" height="150" alt="">')
        errors = audit(img.format(n="isbn-1") + '<picture><source srcset="/assets/reading-covers/isbn-1.webp"></picture>', tmp)
        check(not any("BROKEN_SRCSET_CANDIDATE" in e for e in errors), "portada del almacén no cuenta como rota", str(errors))
        errors = audit(img.format(n="isbn-2"), tmp)
        check(sum("BROKEN_SRCSET_CANDIDATE" in e for e in errors) == 2, "portada fuera del almacén y del disco sigue rota", str(errors))

        page.write_text(
            '<head><meta name="robots" content="noindex,follow"></head>'
            '<body><img src="/x.png" alt=""></body>', encoding="utf-8",
        )
        errors = cri.audit_file(page, tmp)
        check(errors == [], "pagina noindex no se audita")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-responsive-images: OK")


if __name__ == "__main__":
    run()
