from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'cuaderno/feed.xml'
PLACEHOLDER = re.compile(r'\b(?:TODO|FIXME|TBD|lorem\s+ipsum)\b|\[\[pendiente\]\]', re.I)


def main():
    root = ET.parse(FEED).getroot()
    items = root.findall('./channel/item')
    assert items, f'{FEED}: no se encontraron entradas RSS'
    errors = []
    for item in items:
        url = (item.findtext('link') or '').strip()
        for field in ('title', 'link', 'description'):
            value = (item.findtext(field) or '').strip()
            if not value:
                errors.append(f'{FEED}: {url or "entrada sin enlace"}: {field} vacío')
            elif field != 'link' and PLACEHOLDER.search(value):
                errors.append(f'{FEED}: {url}: {field} contiene texto pendiente: {value[:120]!r}')
    assert not errors, '\n'.join(errors)
    print(f'PASS: {len(items)} entradas RSS sin campos vacíos ni relleno editorial')


if __name__ == '__main__':
    main()
