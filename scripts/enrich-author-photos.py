#!/usr/bin/env python3
"""Foto libre para los autores que Wikidata no resolvió: la imagen de cabecera de su artículo en Wikipedia (es, luego en).

Solo se acepta si el artículo se llama igual que el autor (tras redirecciones, sin tildes), su descripción lo da como
escritor/ilustrador/etc. y el fichero está en Wikimedia Commons con licencia libre (la misma comprobación y el mismo
guardado que `enrich-reading-authors.py`: 320 px en WebP, en el almacén externo, con crédito y licencia en la ficha).

Uso: python scripts/enrich-author-photos.py [--contar] [--limite N] [--solo slug,slug]
  --contar  solo informa de cuántos tendrían foto; no descarga ni escribe (no necesita el almacén).
Requiere READING_COVERS_STORE_DIR (copia local de web-escritor-portadas) salvo con --contar.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('enrich_reading_authors', ROOT / 'scripts' / 'enrich-reading-authors.py')
base = importlib.util.module_from_spec(spec)
sys.modules['enrich_reading_authors'] = base
spec.loader.exec_module(base)

WIKIS = ('es', 'en')
WRITER = re.compile(r'escritor|novelist|poet|ilustrador|dibujant|historiador|periodista|ensayist|guionist|dramaturg|traductor|'
                    r'writer|author|illustrator|journalist|historian|essayist|playwright|screenwriter|cartoonist|translator|'
                    r'academic|filósof|philosopher|psicólog|psycholog|científic|scientist|médic|physician', re.I)


def candidate(name: str) -> str | None:
    """Nombre del fichero de Commons de la imagen del artículo, o None."""
    wanted = base.norm(name)
    for lang in WIKIS:
        data = base.get_json(f'https://{lang}.wikipedia.org/w/api.php', {
            'action': 'query', 'titles': name, 'redirects': 1, 'prop': 'pageimages|description', 'piprop': 'name'})
        time.sleep(base.PAUSE)
        for page in data.get('query', {}).get('pages', []):
            if page.get('missing') or base.norm(page.get('title', '')) != wanted:
                continue
            if page.get('pageimage') and WRITER.search(page.get('description', '')):
                return page['pageimage']
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--contar', action='store_true')
    parser.add_argument('--limite', type=int, default=0)
    parser.add_argument('--solo', default='')
    args = parser.parse_args()
    data = json.loads(base.AUTHORS.read_text(encoding='utf-8'))
    only = set(filter(None, args.solo.split(',')))
    todo = [a for a in data['autores'] if not a.get('foto') and a['nombre'] not in base.COLLECTIVE and not a.get('foto_wikipedia_probada')
            and (not only or a['slug'] in only)]
    if args.limite:
        todo = todo[:args.limite]
    if not args.contar and base.cover_store.store_dir() is None:
        sys.exit(f'Falta {base.cover_store.STORE_DIR_ENV} (copia local de web-escritor-portadas).')
    hits = tried = 0
    for a in todo:
        tried += 1
        try:
            file = candidate(a['nombre'])
            if file:
                if args.contar:
                    hits += 1
                    print('candidata', a['nombre'], file, flush=True)
                else:
                    entity = {'claims': {'P18': [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': file}}}]}}
                    found = base.photo(entity, a['slug'], ROOT)
                    if found:
                        a['foto'] = found
                        hits += 1
                    else:
                        a['foto_wikipedia_probada'] = True
            elif not args.contar:
                a['foto_wikipedia_probada'] = True
        except Exception as exc:
            print('error', a['nombre'], exc, flush=True)
            time.sleep(5)
        if not args.contar and tried % 25 == 0:
            base.AUTHORS.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
            print(f'{tried}/{len(todo)} con foto: {hits}', flush=True)
    if not args.contar:
        base.AUTHORS.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f'Hecho: {tried} probados, {hits} con foto.')


if __name__ == '__main__':
    main()
