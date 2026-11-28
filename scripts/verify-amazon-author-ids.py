#!/usr/bin/env python3
"""Comprueba que cada `amazon_autor_id` abre la página de autor de Amazon.es de esa persona.

Lee `authorName` de /stores/author/<ID> y lo compara, sin tildes ni mayúsculas, con el nombre del autor. Si no coincide, no lo quita:
lo lista para revisarlo a mano (seudónimos como Sarah Lark = Christiane Gohl), con --quitar sí lo quita: el enlace cae a la ficha de su libro más reciente, que sí es suyo. Las páginas
bloqueadas o sin nombre no cambian nada y se anotan para repetir.

Uso: python scripts/verify-amazon-author-ids.py [--pausa 1.5] [--informe ruta.json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('ids', ROOT / 'scripts' / 'enrich-amazon-author-ids.py')
ids = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ids)

NAME = re.compile(r'"authorName":"([^"]+)"')
TITLE = re.compile(r'<title>Amazon\.es: ([^<]+?): libros', re.I)


def same(a: str, b: str) -> bool:
    """«Barbara Wertheim Tuchman» y «Pierce Elliot Brown» son quienes son: vale que las palabras del nombre más corto
    (sin iniciales) estén todas en el otro. «Hyuganatsu» y «Natsu Hyuuga» se comparan sin espacios ni vocales dobles."""
    x, y = ids.norm(a).split(), ids.norm(b).split()
    short, long_ = sorted((x, y), key=len)
    words = [w for w in short if len(w) > 1]
    if words and all(w in long_ for w in words):
        return True
    def squash(ws: list[str]) -> str:
        return re.sub(r'([aeiou])\1', r'\1', ''.join(ws))
    return bool(x and y) and (squash(sorted(x)) == squash(sorted(y)) or squash(x) in {squash(y), squash(y[::-1])})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--pausa', type=float, default=1.5)
    ap.add_argument('--informe', default='')
    ap.add_argument('--quitar', action='store_true')
    args = ap.parse_args()
    data = json.loads(ids.AUTHORS.read_text(encoding='utf-8'))
    authors = data if isinstance(data, list) else data['autores']
    report = {'ok': [], 'distinto': [], 'sin_nombre': []}
    for a in authors:
        ident = a.get('amazon_autor_id')
        if not ident:
            continue
        try:
            page = ids.get('https://www.amazon.es/stores/author/' + ident)
        except Exception as exc:  # red: se repite otro día
            report['sin_nombre'].append([a['slug'], ident, str(exc)[:80]])
            continue
        m = NAME.search(page) or TITLE.search(page)
        if not m:
            report['sin_nombre'].append([a['slug'], ident, ''])
        elif same(m.group(1), a['nombre']):
            report['ok'].append(a['slug'])
        else:
            report['distinto'].append([a['slug'], ident, m.group(1)])
            if args.quitar:
                a.pop('amazon_autor_id', None)
        time.sleep(args.pausa)
    ids.AUTHORS.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f"ok={len(report['ok'])} distinto={len(report['distinto'])} sin_nombre={len(report['sin_nombre'])}")
    for row in report['distinto']:
        print('  distinto', *row)
    if args.informe:
        Path(args.informe).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
