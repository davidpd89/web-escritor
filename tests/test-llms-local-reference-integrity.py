from pathlib import Path
from urllib.parse import urlsplit, unquote
import re

ROOT = Path(__file__).resolve().parents[1].resolve()
ORIGIN = 'https://davidportodiaz.com'


def check():
    text = (ROOT / 'llms.txt').read_text(encoding='utf-8')
    urls = set(re.findall(r'https://davidportodiaz\.com/[^\s<>\])]+', text))
    assert len(urls) >= 15, 'Cobertura insuficiente de referencias internas'
    errors = []
    for raw in sorted(urls):
        url = raw.rstrip('.,;')
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.netloc != 'davidportodiaz.com':
            errors.append(f'Origen inválido: {url}')
            continue
        relative = unquote(parts.path).lstrip('/')
        target = (ROOT / relative).resolve()
        if not target.is_relative_to(ROOT):
            errors.append(f'Ruta fuera del repositorio: {url}')
            continue
        if target.is_dir():
            target = target / 'index.html'
        if not target.is_file():
            errors.append(f'Destino inexistente: {url} -> {target}')
    assert not errors, '\n'.join(errors)


if __name__ == '__main__':
    check()
    print('PASS llms local reference integrity')