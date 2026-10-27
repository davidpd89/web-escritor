from html.parser import HTMLParser
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = "/cuaderno/sistema-de-magia-noveris/"


class MainLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside_main = False
        self.seen_main = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.inside_main = True
            self.seen_main = True
        elif tag == "a" and self.inside_main:
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag == "main":
            self.inside_main = False


def local_path(href):
    origin = "https://davidportodiaz.com"
    if href.startswith(origin + "/"):
        href = href[len(origin):]
    return href.split("?", 1)[0].split("#", 1)[0]


html = (ROOT / "mapa-del-sitio/index.html").read_text(encoding="utf-8")
parser = MainLinks()
parser.feed(html)
assert parser.seen_main, "MW-0008: falta el elemento main del mapa HTML"
paths = [local_path(href) for href in parser.links]

assert TARGET not in paths, (
    "MW-0008: el main del mapa HTML sigue enlazando al artículo retirado: " + TARGET
)

registry = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
defaults = registry.get("defaults", {})
excluded = {
    item["url"]
    for raw in registry["entries"]
    for item in [{**defaults, **raw}]
    if item.get("type") == "article"
    and item.get("sitemap") is False
    and item.get("searchIndex") is False
}
assert TARGET in excluded, "MW-0008: ha cambiado la clasificación del artículo retirado"
invalid = sorted(set(paths) & excluded)
assert not invalid, (
    "MW-0008: el mapa HTML promociona artículos excluidos de ambos índices: "
    + ", ".join(invalid)
)

before = "/cuaderno/que-es-el-portal-fantasy/"
after = "/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/"
assert before in paths and after in paths, (
    "MW-0008: deben conservarse los enlaces adyacentes al elemento retirado"
)
assert paths.index(before) < paths.index(after), (
    "MW-0008: ha cambiado el orden de los enlaces conservados"
)

retired = (ROOT / "cuaderno/sistema-de-magia-noveris/index.html").read_text(encoding="utf-8")
assert re.search(
    r'<meta\s+name="robots"\s+content="[^"]*\bnoindex\b',
    retired,
    re.I,
), "MW-0008: la página retirada debe conservar noindex"
assert (
    '<link rel="canonical" href="https://davidportodiaz.com' + TARGET + '"'
) in retired, "MW-0008: la página retirada debe conservar su canonical"

xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
assert TARGET not in xml, "MW-0008: el artículo retirado no debe figurar en sitemap.xml"

print("PASS MW-0008: mapa HTML sin artículos excluidos; enlaces, noindex y canonical conservados")
