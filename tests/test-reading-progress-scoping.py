#!/usr/bin/env python3
"""D.3 contract: reading progress is opt-in for real long-form reading surfaces."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

LONG_FORM = [
    "fragmento/index.html",
    "las-manecillas-del-recuerdo/fragmentos/index.html",
    "cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html",
    "cuaderno/que-es-el-portal-fantasy/index.html",
    "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
    "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
    "cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html",
    "cuaderno/worldbuilding-noveris-ciudad-magica/index.html",
]

SHORT_OR_RETIRED = [
    "cuaderno/sistema-de-magia-noveris/index.html",
]


def body_tag(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)
    assert match, f"{path}: falta <body>"
    return match.group(0)


def main() -> None:
    runtime = (ROOT / "script.js").read_text(encoding="utf-8")
    assert 'document.body.hasAttribute("data-reading-progress")' in runtime, (
        "script.js: el progreso debe seguir siendo opt-in"
    )

    for path in LONG_FORM:
        assert "data-reading-progress" in body_tag(path), (
            f"{path}: superficie long-form sin opt-in de progreso"
        )

    for path in SHORT_OR_RETIRED:
        assert "data-reading-progress" not in body_tag(path), (
            f"{path}: superficie corta/retirada no debe montar progreso"
        )

    print("OK: reading-progress permanece selectivo (long-form sí; stub retirado no).")


if __name__ == "__main__":
    main()
