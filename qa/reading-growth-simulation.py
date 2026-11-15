"""Simula el catálogo de lectura con más libros y mide lo que crece con él (tiempo de build, páginas, bytes).

Cada carga nocturna añade hasta 1000 libros; antes de llegar a esos tamaños hay que saber qué se rompe: tiempos
cuadráticos en el build, páginas sin paginar que pesan cada vez más o una hidratación que ya no cabe en el móvil.

Clona los libros publicados con ids, slugs e ISBN nuevos (válidos y únicos), reutilizando portadas y categorías, y
renderiza todo en memoria con scripts/build-reading-catalogue.py (no escribe nada en el repo). Uso:

    python qa/reading-growth-simulation.py [--extra 1000 2000 ...] [--json salida.json]
    python qa/reading-growth-simulation.py --extra 5000 --materializar   # escribe el catálogo crecido en el árbol

Con --materializar escribe en disco las páginas del último tamaño (solo en un checkout desechable, como el runner):
así la QA de navegador (paginación, filtros, búsqueda) se prueba contra el catálogo del futuro.

Falla si se supera algún presupuesto de PRESUPUESTOS para el tamaño simulado.
"""
import argparse
import copy
import gzip
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('growth_builder', ROOT / 'scripts/build-reading-catalogue.py')
if spec is None or spec.loader is None:
    raise ImportError('no se puede cargar scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
# Los clones reutilizan la portada de su original (no se generan miles de imágenes); el resto de reglas sigue igual.
_require = builder.require
builder.require = lambda ok, message: _require(ok or 'portada duplicada' in message, message)

# Presupuestos por tamaño (por libro o absolutos). Si un tamaño los rompe, hay que paginar o partir antes de llegar.
PRESUPUESTOS = {
    # Segundos de render por cada 1000 libros. Lineal desde el 15/11: 18,8 / 20,4 / 24,6 s por mil con 4.946 / 5.946 /
    # 9.946 libros en local (antes 40 / 45 / 85, cuadrático). Margen para runners más lentos que el portátil.
    'build_s_por_mil': 40.0,
    # /recomendaciones/ sin hidratar: 96 tarjetas de ~4,8 KB (545 KB el 15/11); no crece con el catálogo, vigila
    # que no se cuele contenido por libro en la primera página.
    'primera_pagina_kb': 600,
    'pagina_editorial_kb': 600,       # una página de sello o autor no paginada
    'hidratacion_gzip_mb': 12.0,      # todo /recomendaciones/pagina/N/ comprimido: lo que descarga el móvil al filtrar
}


def isbn13(n):
    stem = '979' + str(n).zfill(9)
    return stem + str(-sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(stem)) % 10)


def crecer(data, extra):
    """Añade `extra` libros clonados de los publicados, con identidad nueva y las mismas categorías."""
    data = copy.deepcopy(data)
    publicados = [b for b in data['libros'] if b.get('estado') == 'publicado']
    cats = {}
    for r in data.get('libro_categorias', []):
        cats.setdefault(r['libro_id'], []).append(r)
    usados = {b.get('isbn13') for b in data['libros']}
    n = 0
    for i in range(extra):
        base = publicados[i % len(publicados)]
        while isbn13(n) in usados:
            n += 1
        nuevo = copy.deepcopy(base)
        isbn = isbn13(n)
        usados.add(isbn)
        n += 1
        sufijo = f'sim-{i}'
        nuevo.update(id=f'{base["id"]}-{sufijo}', slug=f'{base["slug"]}-{sufijo}', isbn13=isbn,
                     titulo=f'{base["titulo"]} ({sufijo})',
                     descripcion_breve=f'{base.get("descripcion_breve", "")} ({sufijo})')
        for campo in ('url_amazon_afiliada', 'amazon_busqueda_isbn', 'asin'):
            nuevo.pop(campo, None)
        data['libros'].append(nuevo)
        data.setdefault('libro_categorias', []).extend({**r, 'libro_id': nuevo['id']} for r in cats.get(base['id'], []))
    return data


def medir(data, materializar=False):
    t = time.perf_counter()
    books, outputs = builder.render_outputs(ROOT, data)
    if materializar:
        for ruta, texto in outputs.items():
            destino = ROOT / ruta
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(texto.encode('utf-8'))
    segundos = time.perf_counter() - t
    hub = {k: v for k, v in outputs.items() if re.fullmatch(r'recomendaciones/(pagina/\d+/)?index\.html', k)}
    sellos = {k: v for k, v in outputs.items() if re.match(r'(recomendaciones/)?(editoriales|autores)/[^/]+/index\.html', k)}
    peso = lambda s: len(s.encode('utf-8'))  # noqa: E731
    mayor = max(sellos.items(), key=lambda kv: peso(kv[1]), default=('', ''))
    return {
        'libros': len(books),
        'build_s': round(segundos, 1),
        'ficheros': len(outputs),
        'paginas_hub': len(hub),
        'primera_pagina_kb': round(peso(outputs.get('recomendaciones/index.html', '')) / 1024),
        'hidratacion_mb': round(sum(map(peso, hub.values())) / 2**20, 1),
        'hidratacion_gzip_mb': round(sum(len(gzip.compress(v.encode('utf-8'), 6)) for v in hub.values()) / 2**20, 2),
        'pagina_editorial_kb': round(peso(mayor[1]) / 1024),
        'pagina_editorial_mayor': mayor[0],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extra', type=int, nargs='*', default=[0, 1000])
    parser.add_argument('--json', type=Path)
    parser.add_argument('--materializar', action='store_true', help='escribe en el árbol las páginas del último tamaño')
    args = parser.parse_args()
    data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    filas, fallos = [], []
    for extra in args.extra:
        ultimo = args.materializar and extra == args.extra[-1]
        fila = {'extra': extra, **medir(crecer(data, extra), materializar=ultimo)}
        filas.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)
        mil = max(fila['libros'], 1) / 1000
        if fila['build_s'] / mil > PRESUPUESTOS['build_s_por_mil']:
            fallos.append(f"+{extra}: build {fila['build_s']} s ({fila['build_s'] / mil:.1f} s por mil libros)")
        for clave in ('primera_pagina_kb', 'pagina_editorial_kb', 'hidratacion_gzip_mb'):
            if fila[clave] > PRESUPUESTOS[clave]:
                fallos.append(f'+{extra}: {clave} = {fila[clave]} > {PRESUPUESTOS[clave]}')
    if args.json:
        args.json.write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding='utf-8')
    if fallos:
        print('FAIL crecimiento:\n' + '\n'.join(fallos))
        return 1
    print(f'PASS crecimiento hasta +{max(args.extra)} libros dentro de presupuesto')
    return 0


if __name__ == '__main__':
    sys.exit(main())
