#!/usr/bin/env python3
"""MW-0054: idioma RSS y conservación de las seis entradas originales.

Prueba de aceptación determinista, sin red ni escritura de archivos.
Debe fallar sobre la base sin language y pasar tras aplicar MW-0054.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
FEED = ROOT / 'cuaderno' / 'feed.xml'
GENERATOR = ROOT / 'scripts' / 'build-feed.py'
BASE = 'https://davidportodiaz.com/cuaderno/'

# Identidades y fechas tomadas del RSS original de la rama de laboratorio.
# El orden de esta secuencia también forma parte del contrato.
EXPECTED = [
    (
        'feria-libro-madrid-2026-samuel-entre-mundos',
        'Thu, 11 Jun 2026 00:00:00 +0000',
    ),
    (
        'worldbuilding-noveris-ciudad-magica',
        'Wed, 27 May 2026 00:00:00 +0000',
    ),
    (
        'fantasia-juvenil-espanola-portales-magia-coste',
        'Tue, 26 May 2026 00:00:00 +0000',
    ),
    (
        'libros-fantasia-juvenil-espanola-2025-2026',
        'Tue, 26 May 2026 00:00:00 +0000',
    ),
    (
        'portal-fantasy-vs-fantasia-epica',
        'Tue, 26 May 2026 00:00:00 +0000',
    ),
    (
        'que-es-el-portal-fantasy',
        'Tue, 26 May 2026 00:00:00 +0000',
    ),
]


def main():
    xml_bytes = FEED.read_bytes()
    source = GENERATOR.read_text(encoding='utf-8')
    root = ET.fromstring(xml_bytes)

    assert root.tag == 'rss', 'La raíz debe ser rss'
    assert root.attrib.get('version') == '2.0', 'Debe mantenerse RSS 2.0'

    channels = root.findall('channel')
    assert len(channels) == 1, 'Debe existir exactamente un channel'
    channel = channels[0]

    languages = channel.findall('language')
    assert len(languages) == 1, (
        f'Se esperaba un único language en channel; encontrados: {len(languages)}'
    )
    assert languages[0].text == 'es-es', (
        f'Idioma RSS incorrecto: {languages[0].text!r}'
    )

    # El elemento debe aparecer después de description y antes de los items.
    tags = [child.tag for child in channel]
    assert tags.index('language') == tags.index('description') + 1, (
        'language debe seguir inmediatamente a description'
    )
    assert tags.index('language') < tags.index('item'), (
        'language debe ser un metadato de canal, anterior a los items'
    )

    # El metadato tiene que proceder del generador, no solo del XML publicado.
    expected_source = (
        "    SubElement(ch, 'description').text = 'Entradas recientes del cuaderno'\n"
        "    SubElement(ch, 'language').text = 'es-es'\n"
    )
    assert expected_source in source, (
        'El generador debe declarar language inmediatamente después de description'
    )
    assert source.count("SubElement(ch, 'language').text = 'es-es'") == 1, (
        'El generador debe insertar language una sola vez'
    )

    # Identidad, fechas y orden exactos de los seis artículos originales.
    items = channel.findall('item')
    assert len(items) == len(EXPECTED) == 6, (
        f'El feed debe conservar exactamente seis entradas; encontradas: {len(items)}'
    )

    actual = [
        (item.findtext('link'), item.findtext('guid'), item.findtext('pubDate'))
        for item in items
    ]
    expected = [
        (BASE + slug + '/', BASE + slug + '/', date)
        for slug, date in EXPECTED
    ]
    assert actual == expected, (
        'Los enlaces, GUID, fechas u orden del RSS han cambiado:\n'
        f'Esperado: {expected!r}\nActual: {actual!r}'
    )

    assert all(item.find('language') is None for item in items), (
        'language pertenece exclusivamente a channel, no a los items'
    )
    assert all(item.findtext('title') for item in items), (
        'Todas las entradas deben conservar un título'
    )
    assert all(item.findtext('description') for item in items), (
        'Todas las entradas deben conservar su descripción'
    )

    # No se deben perder la declaración XML ni la presentación XSL existente.
    assert xml_bytes.startswith(b"<?xml version='1.0' encoding='UTF-8'?>"), (
        'Debe conservarse la declaración XML'
    )
    assert b'<?xml-stylesheet type="text/xsl" href="/assets/rss.xsl"?>' in xml_bytes, (
        'Debe conservarse la referencia a rss.xsl'
    )

    print('MW-0054: OK - language es-es único, seis entradas intactas y generador actualizado')


if __name__ == '__main__':
    main()
