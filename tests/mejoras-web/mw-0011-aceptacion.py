"""MW-0011: paridad entre el archivo visible y CollectionPage.hasPart."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://davidportodiaz.com/"
GUIDES = (
    "https://davidportodiaz.com/recomendaciones/portal-fantasy-espanol/",
    "https://davidportodiaz.com/recomendaciones/magia-con-coste/",
)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.jsonld_scripts = []
        self._jsonld_chunks = None
        self.canonicals = []
        self.feature_links = []
        self.ledger_links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonicals.append(attrs["href"])
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._jsonld_chunks = []
        if tag == "a" and "href" in attrs:
            in_feature = any(
                "cuaderno-feature__body" in classes for _, classes in self.stack
            )
            in_ledger = any(
                parent == "ol" and "cuaderno-ledger" in classes
                for parent, classes in self.stack
            )
            if in_feature and any(parent == "h2" for parent, _ in self.stack):
                self.feature_links.append(attrs["href"])
            elif in_ledger and any(parent == "h3" for parent, _ in self.stack):
                self.ledger_links.append(attrs["href"])
        if tag not in VOID_TAGS:
            self.stack.append((tag, set(attrs.get("class", "").split())))

    def handle_endtag(self, tag):
        if tag == "script" and self._jsonld_chunks is not None:
            self.jsonld_scripts.append("".join(self._jsonld_chunks))
            self._jsonld_chunks = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self._jsonld_chunks is not None:
            self._jsonld_chunks.append(data)


def parse_page(path):
    page = PageParser()
    page.feed(path.read_text(encoding="utf-8"))
    page.close()
    return page


def graph_nodes(page):
    assert page.jsonld_scripts, "No se ha encontrado JSON-LD"
    nodes = []
    for script in page.jsonld_scripts:
        document = json.loads(script)
        assert isinstance(document, dict), "JSON-LD no es un objeto"
        nodes.extend(document.get("@graph", []))
    return nodes


def main():
    archive = parse_page(ROOT / "cuaderno/index.html")
    collections = [
        node for node in graph_nodes(archive)
        if node.get("@type") == "CollectionPage"
    ]
    assert len(collections) == 1, "Debe existir un único CollectionPage"
    parts = collections[0]["hasPart"]
    assert isinstance(parts, list), "hasPart debe ser una lista"
    ids = [part["@id"] for part in parts]
    assert len(ids) == 8, f"hasPart tiene {len(ids)} entradas; se esperan 8"
    assert len(set(ids)) == 8, "hasPart contiene @id duplicados"

    assert len(archive.feature_links) == 1, "Se espera una pieza destacada"
    assert len(archive.ledger_links) == 7, "Se esperan siete entradas en el archivo"
    visible = [
        urljoin(BASE_URL, href)
        for href in archive.feature_links + archive.ledger_links
    ]
    assert len(set(visible)) == 8, "El archivo visible contiene destinos repetidos"
    normalized = {identifier.removesuffix("#article") for identifier in ids}
    assert normalized == set(visible), (
        f"Faltan en hasPart: {sorted(set(visible) - normalized)}; "
        f"sobran en hasPart: {sorted(normalized - set(visible))}"
    )

    for url in GUIDES:
        assert url in ids, f"Falta el @id exacto de la guía: {url}"
        relative_path = urlsplit(url).path.lstrip("/")
        guide = parse_page(ROOT / relative_path / "index.html")
        assert guide.canonicals == [url], f"Canonical incorrecto: {url}"
        webpages = [
            node for node in graph_nodes(guide)
            if node.get("@type") == "WebPage"
        ]
        assert len(webpages) == 1, f"WebPage ausente o duplicado: {url}"
        assert webpages[0].get("@id") == url, f"@id WebPage distinto: {url}"


if __name__ == "__main__":
    main()
