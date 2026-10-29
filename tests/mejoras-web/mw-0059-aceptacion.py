#!/usr/bin/env python3
"""MW-0059: enlace RSS visible y conservación del feed y newsletter."""

from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
FEED_HREF = "/cuaderno/feed.xml"
LINK_TEXT = "Seguir el Cuaderno por RSS"
HELP_TEXT = "Sin correo electrónico: copia este enlace en tu lector RSS"


class CuadernoInspector(HTMLParser):
    """Inspecciona la estructura HTML sin navegador ni dependencias externas."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_main = False
        self.in_newsletter = False
        self.capturing_rss = False
        self.current_link_text = []
        self.rss_links = []
        self.alternate_links = []
        self.newsletter_forms = 0
        self.newsletter_text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        if tag == "head":
            self.in_head = True
        elif tag == "main":
            self.in_main = True
        elif tag == "section" and self.in_main:
            classes = attributes.get("class", "").split()
            if "editorial-newsletter" in classes:
                self.in_newsletter = True

        if tag == "link" and self.in_head:
            relations = attributes.get("rel", "").split()
            if (
                "alternate" in relations
                and attributes.get("type") == "application/rss+xml"
            ):
                self.alternate_links.append(attributes.get("href", ""))

        if tag == "form" and self.in_main and self.in_newsletter:
            if attributes.get("id") == "newsletter-form-cuaderno":
                self.newsletter_forms += 1

        if tag == "a" and self.in_main and self.in_newsletter:
            if attributes.get("href") == FEED_HREF:
                self.capturing_rss = True
                self.current_link_text = []

    def handle_data(self, data):
        if self.in_newsletter:
            self.newsletter_text.append(data)
        if self.capturing_rss:
            self.current_link_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.capturing_rss:
            text = " ".join("".join(self.current_link_text).split())
            self.rss_links.append(text)
            self.capturing_rss = False
        elif tag == "section" and self.in_newsletter:
            self.in_newsletter = False
        elif tag == "main":
            self.in_main = False
        elif tag == "head":
            self.in_head = False


def check_html():
    page = ROOT / "cuaderno" / "index.html"
    assert page.is_file(), f"No existe {page}"

    inspector = CuadernoInspector()
    inspector.feed(page.read_text(encoding="utf-8"))
    inspector.close()

    assert LINK_TEXT in inspector.rss_links, (
        "Falta un enlace visible con href='/cuaderno/feed.xml' "
        "y texto 'Seguir el Cuaderno por RSS' dentro de "
        "main > section.editorial-newsletter"
    )

    newsletter_copy = " ".join(" ".join(inspector.newsletter_text).split())
    assert HELP_TEXT in newsletter_copy, (
        "Falta la explicación sobre suscripción RSS sin correo electrónico"
    )

    assert any(
        href.endswith(FEED_HREF) for href in inspector.alternate_links
    ), "Se ha perdido el link alternate RSS del head"

    assert inspector.newsletter_forms == 1, (
        "Debe conservarse exactamente un formulario "
        "#newsletter-form-cuaderno en la sección editorial-newsletter"
    )


def check_feed():
    feed = ROOT / "cuaderno" / "feed.xml"
    assert feed.is_file(), f"No existe {feed}"

    root = ET.parse(feed).getroot()
    assert root.tag == "rss", "La raíz del feed debe ser rss"
    assert root.attrib.get("version") == "2.0", (
        "El feed debe declarar RSS versión 2.0"
    )

    channels = root.findall("channel")
    assert len(channels) == 1, "RSS 2.0 requiere un único channel"
    channel = channels[0]

    for field in ("title", "link", "description"):
        assert (channel.findtext(field) or "").strip(), (
            f"Falta el campo obligatorio channel/{field}"
        )

    items = channel.findall("item")
    assert items, "El feed del Cuaderno debe contener artículos"

    for index, item in enumerate(items, start=1):
        assert (item.findtext("title") or "").strip(), (
            f"El artículo RSS {index} carece de título"
        )
        assert (item.findtext("link") or "").strip(), (
            f"El artículo RSS {index} carece de enlace"
        )
        assert (item.findtext("description") or "").strip(), (
            f"El artículo RSS {index} carece de descripción"
        )


def main():
    check_html()
    check_feed()
    print("MW-0059 PASS: enlace RSS visible, newsletter y RSS 2.0 conservados")


if __name__ == "__main__":
    main()
