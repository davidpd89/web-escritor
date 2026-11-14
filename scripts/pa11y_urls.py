#!/usr/bin/env python3
"""URL que audita Pa11y en la vía completa, repartidas en shards.

Las familias generadas con una misma plantilla (fichas de libro, autores, editoriales) pasan de 5.000 páginas y
crecen cada noche: auditarlas todas cada vez dejó de caber en el límite de los jobs (14/11: 1.290 URL por shard,
30 min y cancelado, también en main) y repetía la misma plantilla miles de veces. De cada familia con más de
`LIMITE` páginas entra una muestra repartida que rota cada día, así que en unas semanas pasan todas; las páginas
sueltas (portada, cuaderno, atlas, herramientas, índices) entran siempre.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

LIMITE = 100
LOC = re.compile(r'<loc>https://davidportodiaz\.com([^<]*)</loc>')


def familia(ruta):
    """Las rutas hermanas de una misma plantilla: /recomendaciones/libros/x/ -> /recomendaciones/libros/*/."""
    return re.sub(r'[^/]+/$', '*/', ruta) if ruta.count('/') > 2 else ruta


def elegir(rutas, dia, limite=LIMITE):
    """Todas las páginas sueltas y, de cada familia grande, una de cada `vueltas` empezando por el turno del día."""
    grupos = defaultdict(list)
    for ruta in rutas:
        grupos[familia(ruta)].append(ruta)
    elegidas = set()
    for miembros in grupos.values():
        if len(miembros) <= limite:
            elegidas.update(miembros)
        else:
            vueltas = -(-len(miembros) // limite)
            elegidas.update(miembros[dia % vueltas::vueltas])
    return [ruta for ruta in rutas if ruta in elegidas]


def shard(rutas, indice, total):
    return [ruta for i, ruta in enumerate(rutas) if i % total == indice]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shard', type=int, required=True)
    p.add_argument('--shards', type=int, required=True)
    p.add_argument('--sitemap', default='sitemap.xml')
    p.add_argument('--config', default='.pa11yci')
    p.add_argument('--out', required=True)
    p.add_argument('--base', default='http://127.0.0.1:4173')
    # El turno de la rotación lo fija el workflow una vez por ejecución (run_number): si cada shard mirase su reloj,
    # dos shards a ambos lados de medianoche repartirían muestras distintas y alguna página quedaría sin auditar.
    p.add_argument('--dia', type=int, default=None)
    args = p.parse_args(argv)
    with open(args.sitemap, encoding='utf-8') as f:
        rutas = LOC.findall(f.read())
    dia = args.dia if args.dia is not None else datetime.now(timezone.utc).date().toordinal()
    mias = shard(elegir(rutas, dia), args.shard, args.shards)
    with open(args.config, encoding='utf-8') as f:
        config = json.load(f)
    config['concurrency'] = 4
    config['urls'] = [args.base + ruta for ruta in mias]
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(config, f)
    print(f'{len(mias)} URL en este shard (de {len(rutas)} en el sitemap)')


if __name__ == '__main__':
    main()
