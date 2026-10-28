#!/usr/bin/env python3
"""MW-0007: coherencia de la fecha del índice editorial y ambos sitemaps."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = "https://davidportodiaz.com/editoriales/"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_lastmod(path: Path) -> str:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    matches = [
        item
        for item in root.findall("sm:url", NS)
        if item.findtext("sm:loc", namespaces=NS) == CANONICAL
    ]
    assert len(matches) == 1, f"{path.name}: se esperaba una URL única para el índice"
    value = matches[0].findtext("sm:lastmod", namespaces=NS)
    assert value, f"{path.name}: falta lastmod del índice"
    return value


def main() -> None:
    dataset = json.loads((ROOT / "data/editoriales.json").read_text(encoding="utf-8"))
    records = [r for r in dataset["publishers"] if r.get("publish") is True]
    assert records, "El directorio no contiene registros publicados"

    expected = max(r["page_updated_at"] for r in records)
    assert date.fromisoformat(expected).isoformat() == expected, "Fecha editorial no ISO"

    html = (ROOT / "editoriales/index.html").read_text(encoding="utf-8")
    scripts = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    )
    pages = []
    for script in scripts:
        document = json.loads(script)
        nodes = document.get("@graph", [document]) if isinstance(document, dict) else document
        pages.extend(
            node for node in nodes
            if isinstance(node, dict)
            and node.get("@type") == "CollectionPage"
            and node.get("@id") == CANONICAL
        )

    assert len(pages) == 1, "Debe existir exactamente un CollectionPage del índice"
    modified = pages[0].get("dateModified")
    assert modified == expected, (
        f"CollectionPage.dateModified={modified!r}; esperado={expected!r}"
    )

    # La fecha máxima debe corresponder a contenido realmente visible en el índice.
    # Evita atribuir frescura al índice cuando solo cambia el interior de una ficha.
    latest = [r for r in records if r["page_updated_at"] == expected]
    assert latest, "No hay registros que justifiquen la fecha máxima"
    cards = re.findall(
        r'<article\b[^>]*\bdata-editorial-card\b[^>]*>.*?</article>',
        html,
        flags=re.S,
    )
    visible_latest = []
    for record in latest:
        slug_link = f'href="/editoriales/{record["slug"]}/"'
        matching = [card for card in cards if slug_link in card]
        assert len(matching) == 1, f"Tarjeta ausente o duplicada: {record['slug']}"
        card = matching[0]
        if (
            record["verified_at"] == expected
            and f'data-verified-at="{expected}"' in card
            and f'<time datetime="{expected}">{expected}</time>' in card
        ):
            visible_latest.append(record["slug"])

    assert visible_latest, (
        "La fecha máxima solo corresponde a cambios de fichas individuales; "
        "no se acredita una comprobación actualizada y visible en el índice"
    )

    main_lastmod = sitemap_lastmod(ROOT / "sitemap.xml")
    secondary_lastmod = sitemap_lastmod(ROOT / "editoriales-sitemap.xml")
    assert main_lastmod == expected, (
        f"Sitemap principal: {main_lastmod!r}; esperado: {expected!r}"
    )
    assert secondary_lastmod == expected, (
        f"Sitemap editorial: {secondary_lastmod!r}; esperado: {expected!r}"
    )
    assert modified == main_lastmod == secondary_lastmod

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    announced = re.findall(r"^Sitemap:\s*(\S+)\s*$", robots, re.M | re.I)
    assert announced == ["https://davidportodiaz.com/sitemap.xml"], (
        "robots.txt debe conservar el sitemap principal como autoridad anunciada"
    )

    print(
        f"MW-0007 OK: CollectionPage y ambos sitemaps = {expected}; "
        f"tarjetas actualizadas visibles: {', '.join(visible_latest)}"
    )


if __name__ == "__main__":
    main()
