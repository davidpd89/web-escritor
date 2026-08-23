#!/usr/bin/env python3
"""Gate de regresion: el email de contacto obsoleto
`samuelentremundos@gmail.com` no debe reaparecer en ninguna superficie
publica (2026-08-23, encontrado durante N.1 mientras se auditaba
autor.html).

Se detecto en dos formas reales, ninguna de las cuales atrapaba el grep
literal `samuelentremundos@gmail.com` que auditorias previas ya habian
dado por resuelto:

  1. Texto visible codificado con la entidad HTML `&#64;` en vez del
     caracter `@` literal (siete instancias reales en index.html,
     libros/samuel-entre-mundos/index.html, autor.html y prensa.html):
     el `href` real apuntaba correctamente a davidportodiaz@gmail.com,
     pero el TEXTO visible/copiable decia samuelentremundos@gmail.com.
  2. `data-n="samuelentremundos"` en un enlace con ofuscacion de email
     (clubes-de-lectura/samuel-entre-mundos/index.html): script.js
     reconstruye `el.href` en tiempo de ejecucion a partir de
     data-n+'@'+data-d, así que este SI era un bug funcional real -- el
     enlace "Contactar al autor" abria un mailto: a la direccion
     equivocada, no solo un problema de texto visible.

Python standard library only.

Usage:
    python scripts/check-no-stale-contact-email.py
    python scripts/check-no-stale-contact-email.py --check
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    for path in tracked_html(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        if "samuelentremundos" in text.lower():
            errors.append(f"{rel}: contiene 'samuelentremundos' (email de contacto obsoleto o su fragmento en data-n) -- la direccion vigente es davidportodiaz@gmail.com")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nStale contact email check: {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
