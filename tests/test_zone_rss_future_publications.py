from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'cuaderno/feed.xml'


def main():
    root = ET.parse(FEED).getroot()
    items = root.findall('./channel/item')
    assert items, f'{FEED}: no hay entradas publicadas que comprobar'
    now = datetime.now(timezone.utc)
    errors = []
    for item in items:
        title = item.findtext('title') or '(sin título)'
        url = item.findtext('link') or '(sin URL)'
        value = item.findtext('pubDate')
        if not value:
            errors.append(f'{url}: falta pubDate para {title}')
            continue
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                raise ValueError('fecha sin zona horaria')
            date = date.astimezone(timezone.utc)
        except (TypeError, ValueError) as exc:
            errors.append(f'{url}: pubDate inválido {value!r}: {exc}')
            continue
        if date > now + timedelta(days=1):
            errors.append(f'{url}: artículo {title!r} anunciado para el futuro: {value}; ahora={now.isoformat()}')
    assert not errors, '\n'.join(errors)
    print(f'PASS: {len(items)} entradas RSS con cronología válida')


if __name__ == '__main__':
    main()
