"""Enlaces de terceros de las fichas de autor (web oficial de Wikidata, fuentes del texto GPT): solo se enlaza lo
que respondió.

Wikidata y los textos traen webs que caducan (dominios vencidos, TLS roto) y que el control de enlaces de la CI
tumba en cada PR. Este módulo guarda el estado de cada URL en `data/reading-author-links.json` y el constructor
pregunta `alive(url)`: una URL sin comprobar o caída no se enlaza (la fuente queda como texto). La comprobación usa
el mismo agente y los mismos códigos aceptados que Lychee en `broken-links.yml`, para que «vivo» aquí sea «pasa» allí.

Uso: python scripts/reading_author_links.py check [--todas]   (por defecto, solo las nuevas y las de más de 30 días)
"""
from __future__ import annotations

import argparse
import glob
import json
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = 'data/reading-author-links.json'
# Igual que `--user-agent` y `--accept` de Lychee en .github/workflows/broken-links.yml.
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
RECHECK_DAYS = 30
_cache: dict[Path, dict] = {}


def load(root: Path = ROOT) -> dict:
    path = root / STATE
    if path not in _cache:
        _cache[path] = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    return _cache[path]


def ok(status) -> bool:
    return isinstance(status, int) and (200 <= status < 300 or status == 429)


def alive(url: str, root: Path = ROOT) -> bool:
    entry = load(root).get(url)
    return bool(entry) and ok(entry.get('estado'))


def urls(root: Path = ROOT) -> list[str]:
    """Las URL de terceros que pinta una ficha de autor."""
    found = []
    for author in json.loads((root / 'data/reading-authors.json').read_text(encoding='utf-8')).get('autores', []):
        if web := author.get('identificadores', {}).get('web'):
            found.append(web)
    for path in sorted(glob.glob(str(root / 'data/reading-author-texts/*.json'))):
        found += [s['url'] for s in json.loads(Path(path).read_text(encoding='utf-8')).get('fuentes', []) if s.get('url')]
    return sorted(set(found))


def probe(url: str, timeout: int = 20):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,*/*;q=0.8'})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, OSError, ValueError) as exc:  # DNS, TLS, conexión: caído
        return f'error: {type(getattr(exc, "reason", exc)).__name__}'


def check(root: Path = ROOT, everything: bool = False, today: date | None = None, fetch=probe) -> dict:
    today = today or date.today()
    state = load(root)
    limit = (today - timedelta(days=RECHECK_DAYS)).isoformat()
    wanted = urls(root)
    todo = [u for u in wanted if everything or u not in state or state[u].get('fecha', '') < limit]
    with ThreadPoolExecutor(8) as pool:
        for url, status in zip(todo, pool.map(fetch, todo)):
            state[url] = {'estado': status, 'fecha': today.isoformat()}
    for url in set(state) - set(wanted):  # las que ya no pinta nadie no se guardan
        del state[url]
    (root / STATE).write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='')
    return {'comprobadas': len(todo), 'vivas': sum(ok(v['estado']) for v in state.values()), 'total': len(state)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('accion', choices=['check'])
    parser.add_argument('--todas', action='store_true')
    print(check(everything=parser.parse_args().todas))
    sys.exit(0)
