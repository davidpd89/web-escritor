#!/usr/bin/env python3
"""Creators API → bandeja temporal de candidatos. Nunca publica automáticamente.

No almacena imágenes ni contenido de Amazon en Git. El informe temporal caduca
en 24 h y no es un catálogo exhaustivo de novedades ni de subidas en 24 horas.
"""
import argparse
import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path


def post(url, payload, headers=None):
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', **(headers or {})}, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def request_body(query, tag, page):
    if not query.strip() or not re.fullmatch(r'[A-Za-z0-9-]+', tag) or not 1 <= page <= 10:
        raise ValueError('Consulta/tag/página inválidos')
    return {'partnerTag': tag, 'marketplace': 'www.amazon.es', 'searchIndex': 'Books', 'keywords': query, 'sortBy': 'NewestArrivals', 'itemCount': 10, 'itemPage': page, 'resources': ['itemInfo.title', 'itemInfo.byLineInfo', 'itemInfo.contentInfo', 'itemInfo.externalIds']}


def candidates(payload, seen):
    if payload.get('errors'):
        raise ValueError('Creators API devolvió errores: revisar la consulta en el panel de Amazon')
    results = []
    for item in payload.get('searchResult', {}).get('items', []):
        asin = item.get('asin', '')
        if not re.fullmatch(r'[A-Z0-9]{10}', asin) or asin in seen:
            continue
        seen.add(asin)
        info = item.get('itemInfo') or {}
        results.append({'asin': asin, 'titulo': (info.get('title') or {}).get('displayValue', ''), 'url': item.get('detailPageURL', ''), 'datos_edicion': info.get('contentInfo'), 'autoria_editorial': info.get('byLineInfo'), 'identificadores': info.get('externalIds'), 'estado': 'pendiente_revision'})
    return results


def is_pending_eligibility(status, payload):
    return status == 403 and payload.get('message') == 'Your account does not currently meet the eligibility requirements.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', action='append', required=True)
    parser.add_argument('--pages', type=int, default=2, choices=range(1, 11))
    parser.add_argument('--out', type=Path, default=Path('.ci/reading-discovery/candidates.json'))
    args = parser.parse_args()
    client, secret, tag = (os.environ.get(key) for key in ('AMAZON_CREATORS_CLIENT_ID', 'AMAZON_CREATORS_CLIENT_SECRET', 'AMAZON_PARTNER_TAG'))
    if not all((client, secret, tag)):
        parser.error('Configurar credenciales Creators API EU y tag en secretos; no se necesita abrir una sesión del navegador')
    seen, found, status = set(), [], 'ok'
    try:
        access = post('https://api.amazon.co.uk/auth/o2/token', {'grant_type': 'client_credentials', 'client_id': client, 'client_secret': secret, 'scope': 'creatorsapi::default'})['access_token']
        for query in args.query:
            for page in range(1, args.pages + 1):
                payload = post('https://creatorsapi.amazon/catalog/v1/searchItems', request_body(query, tag, page), {'Authorization': 'Bearer ' + access, 'x-marketplace': 'www.amazon.es'})
                found += candidates(payload, seen)
                if len(payload.get('searchResult', {}).get('items', [])) < 10:
                    break
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read(10000))
        if not is_pending_eligibility(exc.code, payload):
            raise SystemExit(f'Creators API: HTTP {exc.code}; revisar configuración o servicio. No se publica ningún dato.')
        status = 'pending_amazon_eligibility'
        found = []
    now = datetime.now(timezone.utc)
    output = {'status': status, 'generated_at': now.isoformat(), 'expires_at': (now + timedelta(hours=24)).isoformat(), 'scope': 'Muestra por búsquedas; no todas las subidas ni todas las editoriales', 'items': found}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Pendiente de elegibilidad en Amazon; volver a comprobar en la siguiente ejecución.' if status != 'ok' else f'{len(found)} candidatos para revisar; informe temporal, sin imágenes ni publicación.')


if __name__ == '__main__':
    main()
