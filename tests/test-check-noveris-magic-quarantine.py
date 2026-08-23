#!/usr/bin/env python3
"""Fixtures para scripts/check-noveris-magic-quarantine.py (K.4)."""
from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-noveris-magic-quarantine.py"
failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def write_page(tmp: Path, body: str, robots: str = "noindex, follow") -> None:
    d = tmp / "cuaderno" / "sistema-de-magia-noveris"
    d.mkdir(parents=True, exist_ok=True)
    html = (
        f'<meta name="robots" content="{robots}">'
        '<main><h1>Contenido temporalmente retirado</h1>'
        '<p>La URL se conserva para no romper enlaces existentes.</p>'
        '<a href="/libros/samuel-entre-mundos/">Ficha</a>'
        '<a href="/fragmento/">Fragmento</a>'
        f'{body}</main>'
    )
    (d / "index.html").write_text(html, encoding="utf-8")


def run_checker(tmp: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(tmp), "--check"],
        capture_output=True, text=True,
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        write_page(tmp, "<p>Consulta la obra publicada para información vigente.</p>")
        result = run_checker(tmp)
        check(result.returncode == 0, "cuarentena publica neutral pasa", result.stdout)

        write_page(tmp, "<p>x</p>", robots="index, follow")
        result = run_checker(tmp)
        check("debe seguir siendo noindex" in result.stdout, "perder noindex falla", result.stdout)

        write_page(tmp, "<p>Cada canalización consume esa historia residual de forma irreversible.</p>")
        result = run_checker(tmp)
        check("afirmacion factual conflictiva" in result.stdout, "claim conflictivo falla", result.stdout)

        write_page(tmp, "<script>{\"@type\":\"FAQPage\"}</script>")
        result = run_checker(tmp)
        check("FAQPage" in result.stdout, "FAQPage legacy falla", result.stdout)

        write_page(tmp, "<p>Existen versiones de trabajo incompatibles y queda pendiente de decidir.</p>")
        result = run_checker(tmp)
        check("copy editorial interno" in result.stdout, "copy interno de trabajo falla", result.stdout)

        # Falta el copy lector requerido.
        dpage = tmp / "cuaderno" / "sistema-de-magia-noveris" / "index.html"
        dpage.write_text('<meta name="robots" content="noindex"><a href="/libros/samuel-entre-mundos/">Ficha</a><a href="/fragmento/">Fragmento</a>', encoding="utf-8")
        result = run_checker(tmp)
        check("falta copy publico" in result.stdout, "cuarentena opaca sin explicacion falla", result.stdout)

        write_page(tmp, "<p>x</p>")
        (tmp / "sitemap.xml").write_text(
            "<urlset><url><loc>https://x/cuaderno/sistema-de-magia-noveris/</loc></url></urlset>", encoding="utf-8"
        )
        result = run_checker(tmp)
        check("aparece en el sitemap" in result.stdout, "URL cuarentenada en sitemap falla", result.stdout)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-noveris-magic-quarantine: OK")


if __name__ == "__main__":
    run()