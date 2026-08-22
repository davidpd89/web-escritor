#!/usr/bin/env python3
"""Regression checks for the public tools-hub registry boundary."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "tools-hub.json"
PRIVATE_PRIMITIVES = re.compile(
    r"\b(?:fetch|fetchLater|XMLHttpRequest|sendBeacon|WebSocket|EventSource|localStorage|sessionStorage|indexedDB)\b|document\.cookie"
)


def route_to_file(href: str) -> Path:
    if not (href.startswith("/") and href.endswith("/")):
        raise AssertionError(f"invalid registry route: {href}")
    return ROOT / href.strip("/") / "index.html"


data = json.loads(REGISTRY.read_text(encoding="utf-8"))
tools = data.get("tools", [])
directories = data.get("directories", [])
assert tools, "tools-hub registry must contain public tools"

hrefs = [item["href"] for item in tools] + [item["href"] for item in directories]
assert len(hrefs) == len(set(hrefs)), "duplicate public href in tools-hub registry"

# These routes intentionally exist, but are internal/noindex. They must not
# reappear as public hub products or public reference directories.
for internal_href in ("/herramientas/auditor-web/", "/publicar-web/"):
    assert internal_href not in hrefs, f"internal route leaked into public hub: {internal_href}"
    html_path = route_to_file(internal_href)
    assert html_path.exists(), f"internal route unexpectedly deleted: {internal_href}"
    html = html_path.read_text(encoding="utf-8").lower()
    assert 'name="robots"' in html and "noindex" in html, f"internal route lost noindex: {internal_href}"

def strip_js_comments(text: str) -> str:
    """Quita comentarios antes de buscar primitivas de red o almacenamiento.

    Sin esto el escaneo se dispara con la palabra escrita en prosa. Paso
    exactamente eso: assets/book-page-audit-rules.js abre con el comentario
    "No hace fetch, no puntua SEO...", o sea justo la afirmacion contraria, y
    la prueba lo marcaba como violacion del contrato local. Una puerta que
    falla al leer su propia documentacion no se puede usar.

    Se mantiene lo que la prueba comprueba: una llamada real a fetch, a
    XMLHttpRequest o a localStorage sigue estando en el codigo, no en un
    comentario, y sigue fallando.
    """
    out = []
    i, n = 0, len(text)
    quotes = ("'", chr(34), chr(96))
    while i < n:
        two = text[i:i + 2]
        if two == "//":
            j = text.find(chr(10), i)
            i = n if j == -1 else j
        elif two == "/*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif text[i] in quotes:
            quote = text[i]
            j = i + 1
            while j < n:
                if text[j] == chr(92):
                    j += 2
                    continue
                if text[j] == quote:
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)

# Every public registry target and implementation asset must exist. A route
# advertised by the public hub must not itself be noindex. For tools whose
# registry contract says "local", enforce the two static properties that
# protect private input: connect-src none on the page and no network/persistent
# storage primitive in the tool implementation source.
for item in tools:
    page = route_to_file(item["href"])
    assert page.exists(), f"public tool target missing: {item['href']}"
    html = page.read_text(encoding="utf-8")
    html_lower = html.lower()
    assert not ('name="robots"' in html_lower and "noindex" in html_lower), f"noindex route exposed as public tool: {item['href']}"

    source = ROOT / item["source_doc"]
    assert source.exists(), f"tool implementation source missing: {item['slug']} -> {item['source_doc']}"
    if item.get("privacy") == "local":
        assert "connect-src 'none'" in html, f"local tool lacks connect-src 'none': {item['href']}"
        source_text = strip_js_comments(source.read_text(encoding="utf-8"))
        match = PRIVATE_PRIMITIVES.search(source_text)
        assert not match, f"local tool source uses forbidden network/storage primitive {match.group(0)!r}: {item['source_doc']}"

for item in directories:
    page = route_to_file(item["href"])
    assert page.exists(), f"public directory target missing: {item['href']}"
    html = page.read_text(encoding="utf-8").lower()
    assert not ('name="robots"' in html and "noindex" in html), f"noindex route exposed as public directory: {item['href']}"

# The generated hub is part of the same contract.
hub = (ROOT / "herramientas" / "index.html").read_text(encoding="utf-8")
assert "/herramientas/auditor-web/" not in hub
assert "/publicar-web/" not in hub
assert f">{len(tools)} herramientas<" in hub

print(
    f"PASS tools-hub boundary: {len(tools)} public tools, {len(directories)} public directories; "
    "public routes are indexable, local tool sources avoid network/persistent storage, internal routes stay preserved and hidden"
)
