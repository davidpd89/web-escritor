#!/usr/bin/env python3
"""Fail if key indexable article pages regress to the generic site social card."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERIC = "https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp"
TARGETS = [
    "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
    "cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html",
    "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
    "cuaderno/que-es-el-portal-fantasy/index.html",
    "cuaderno/sistema-de-magia-noveris/index.html",
    "recomendaciones/magia-con-coste/index.html",
    "recomendaciones/portal-fantasy-espanol/index.html",
]

errors: list[str] = []

for rel in TARGETS:
    path = ROOT / rel
    html = path.read_text(encoding="utf-8")
    if GENERIC in html:
        errors.append(f"{rel}: still uses generic social card")

if errors:
    print("test-social-card-article-specific: FAIL")
    for item in errors:
        print("  -", item)
    raise SystemExit(1)

print(f"test-social-card-article-specific: OK ({len(TARGETS)} pages checked)")
