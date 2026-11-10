#!/usr/bin/env python3
"""Contrato de /comunidad/: página al día, sin enlaces ficticios y enlazada desde pie, redes y catálogo."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("community_page", ROOT / "scripts" / "build-community-page.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    builder = load_builder()
    config = builder.load(ROOT)
    failures: list[str] = list(builder.validate(config))

    # Un grupo sin enlace no puede tener botón de unión; uno previsto no puede tener enlace.
    bad = dict(config, groups=[dict(config["groups"][0], invite="https://ejemplo.com/x")])
    if not builder.validate(bad):
        failures.append("validate acepta un enlace fuera de t.me")
    planned = dict(config, groups=[dict(config["groups"][1], status="planned", invite="https://t.me/x")])
    if not builder.validate(planned):
        failures.append("validate acepta un grupo previsto con enlace")

    page = (ROOT / "comunidad" / "index.html").read_text(encoding="utf-8")
    if page != builder.render(config):
        failures.append("comunidad/index.html desactualizado")
    invites = [g for g in config["groups"] if g.get("invite")]
    if page.count('class="community-join ') != len(invites) + sum(
        1 for p in config["platforms"].values() if p.get("invite")
    ):
        failures.append("hay botones de unión sin enlace público")
    for anchor in ("telegram", "discord"):
        if f'id="{anchor}"' not in page:
            failures.append(f"falta el ancla #{anchor}")
    for group in config["groups"]:
        if f'id="{group["id"]}"' not in page:
            failures.append(f"falta la tarjeta {group['id']}")
    if '<link rel="canonical" href="https://davidportodiaz.com/comunidad/" />' not in page:
        failures.append("canonical incorrecto")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        json.loads(block)

    checks = {
        "redes-sociales/index.html": ['href="/comunidad/#telegram"', 'href="/comunidad/#discord"',
                                      "Comunidad de Telegram", "Comunidad de Discord"],
        "recomendaciones/index.html": ["Únete a nuestra comunidad de", 'href="/comunidad/"', "Únete a la comunidad de Telegram o Discord",
                                       'href="#comunidad"', 'href="' + config["platforms"]["discord"]["invite"] + '"'],
        "index.html": ['class="ft-social" href="/comunidad/#telegram"', 'class="ft-social" href="/comunidad/#discord"'],
        "mapa-del-sitio/index.html": ['href="/comunidad/"'],
    }
    for rel, needles in checks.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        failures += [f"{rel}: falta {n}" for n in needles if n not in text]

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    if "https://davidportodiaz.com/comunidad/" not in sitemap:
        failures.append("sitemap.xml no incluye /comunidad/")

    for failure in failures:
        print("FAIL " + failure)
    print("PASS: comunidad" if not failures else f"{len(failures)} fallos")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
