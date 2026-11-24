#!/usr/bin/env python3
"""Reverifica las convocatorias del radar contra su fuente oficial.

Una convocatoria deja de mostrarse a los 30 días de su `verified_at` (STALE_DAYS). Nadie lo renovaba, y el 19/11/2026
el radar público quedó vacío con 25 convocatorias aún abiertas. Este script renueva `verified_at` SOLO de las fichas con
plazo futuro cuya página oficial sigue mostrando ese plazo. No toca ningún otro campo y no inventa nada: lo que la
fuente no confirma queda sin renovar y se informa (informe JSON) para que una persona lo revise antes de que caduque.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'radar-opportunities.json'
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']
UA = 'Mozilla/5.0 (compatible; radar-reverificador; +https://github.com)'


def _texto(raw: str) -> str:
    raw = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', raw)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw))).lower()


def fecha_en_texto(texto: str, plazo: str) -> bool:
    """True si el texto de la fuente menciona el día del plazo (en formatos habituales en español)."""
    y, m, d = map(int, plazo.split('-'))
    mes = MESES[m - 1]
    t = _texto(texto) if '<' in texto else texto.lower()
    literales = [f'{d:02d}/{m:02d}/{y}', f'{d}/{m}/{y}', f'{d:02d}-{m:02d}-{y}', f'{d}-{m}-{y}', f'{plazo}',
                 f'{d:02d}.{m:02d}.{y}', f'{d:02d}/{m:02d}/{y % 100:02d}']
    if any(x in t for x in literales):
        return True
    return re.search(rf'(?<!\d){d}\s*(?:de\s+)?{mes}\b', t) is not None


def descargar(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    raw = urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()).read()
    return raw.decode('utf-8', 'ignore')


def reverificar(data: dict, hoy: date, fetch=descargar, edad_min: int = 10, pausa: float = 1.0) -> dict:
    """Actualiza `verified_at` in situ. Devuelve {confirmadas, sin_confirmar:[{id, motivo, plazo, verified_at}]}."""
    confirmadas, pendientes = [], []
    primera = True
    for item in data.get('items', []):
        plazo = item.get('deadline') or ''
        if plazo < hoy.isoformat() or not item.get('source_url'):
            continue
        verif = date.fromisoformat(item['verified_at'])
        if (hoy - verif).days < edad_min:
            continue
        if not primera and pausa:
            time.sleep(pausa)
        primera = False
        try:
            ok = fecha_en_texto(fetch(item['source_url']), plazo)
            motivo = 'la fuente no muestra ya el plazo' if not ok else ''
        except Exception as e:  # noqa: BLE001 - cualquier fallo de red es «sin confirmar», nunca «confirmada»
            ok, motivo = False, f'fuente inaccesible: {str(e)[:60]}'
        if ok:
            item['verified_at'] = hoy.isoformat()
            confirmadas.append(item['id'])
        else:
            pendientes.append({'id': item['id'], 'motivo': motivo, 'plazo': plazo, 'verified_at': item['verified_at']})
    return {'confirmadas': confirmadas, 'sin_confirmar': pendientes}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', default=str(DATA))
    ap.add_argument('--today', default=None)
    ap.add_argument('--edad-min', type=int, default=10)
    ap.add_argument('--informe', default=None, help='ruta del informe JSON')
    ap.add_argument('--aviso-dias', type=int, default=22, help='edad (días) desde la que «sin confirmar» es urgente')
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from site_clock import site_today
    hoy = date.fromisoformat(args.today) if args.today else site_today()
    path = Path(args.data)
    data = json.loads(path.read_text(encoding='utf-8'))
    informe = reverificar(data, hoy, edad_min=args.edad_min)
    if informe['confirmadas']:
        # Mismo formato que el resto de data/: se reescribe solo si algo cambió.
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    informe['urgentes'] = [p for p in informe['sin_confirmar']
                           if (hoy - date.fromisoformat(p['verified_at'])).days >= args.aviso_dias]
    if args.informe:
        Path(args.informe).write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"reverificadas={len(informe['confirmadas'])} sin_confirmar={len(informe['sin_confirmar'])} "
          f"urgentes={len(informe['urgentes'])}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
