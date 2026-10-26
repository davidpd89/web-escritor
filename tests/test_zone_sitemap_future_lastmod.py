from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
SITEMAP = ROOT / 'sitemap.xml'


def parse_date(value):
    if len(value) == 10:
        return datetime.strptime(value, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('fecha sin zona horaria')
    return date.astimezone(timezone.utc)


def main():
    root = ET.parse(SITEMAP).getroot()
    urls = root.findall('s:url', NS)
    assert urls, f'{SITEMAP}: sitemap sin URLs'
    now = datetime.now(timezone.utc)
    errors = []
    checked = 0
    for entry in urls:
        loc = entry.findtext('s:loc', default='(sin loc)', namespaces=NS)
        value = entry.findtext('s:lastmod', namespaces=NS)
        if not value:
            continue
        checked += 1
        try:
            date = parse_date(value)
        except (TypeError, ValueError) as exc:
            errors.append(f'{loc}: lastmod inválido {value!r}: {exc}')
            continue
        if date > now + timedelta(days=1):
            errors.append(f'{loc}: lastmod futuro {value}; fecha actual UTC {now.date()}')
    assert not errors, '\n'.join(errors)
    print(f'PASS: {checked} fechas lastmod comprobadas en {len(urls)} URLs')


if __name__ == '__main__':
    main()
