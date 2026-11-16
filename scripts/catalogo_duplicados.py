"""Detector de libros duplicados o casi duplicados en data/reading-catalogue.json.

Informativo: nombra los ids de cada pareja sospechosa y nunca tumba la carga. Solo «--estricto» devuelve 1,
y solo por identificadores repetidos (ISBN o slug), que sí rompen fichas.

Clases de hallazgo:
  isbn_repetido   dos libros con el mismo ISBN-13
  slug_repetido   dos libros con el mismo slug (la segunda ficha pisa a la primera)
  misma_edicion   mismo autor, mismo título, mismo formato y misma editorial, con ISBN distinto
  titulo_parecido mismo autor, mismo formato y editorial, y títulos casi iguales (errata, subtítulo o espacios)

Dos ediciones de la misma obra (tapa dura y blanda, o editoriales distintas) son legítimas: se cuentan, no se listan.
Usa RapidFuzz si está instalado (CI); si no, difflib de la biblioteca estándar, con el mismo resultado en lo esencial.

Uso: python scripts/catalogo_duplicados.py [--catalogo RUTA] [--umbral 92] [--salida informe.md] [--json datos.json] [--estricto]
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / 'data' / 'reading-catalogue.json'
UMBRAL = 92
TOPE_LISTA = 200

try:
    from rapidfuzz.fuzz import ratio as _ratio

    def parecido(a, b):
        return _ratio(a, b)
    MOTOR = 'rapidfuzz'
except ImportError:  # sin dependencias: suficiente para probar en local
    from difflib import SequenceMatcher

    def parecido(a, b):
        return 100.0 * SequenceMatcher(None, a, b, autojunk=False).ratio()
    MOTOR = 'difflib'


def normalizar(texto):
    """Minúsculas, sin tildes ni signos, espacios simples. «El Señor de los Anillos» → «el senor de los anillos»."""
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFKD', str(texto or '')) if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', sin_tildes.lower()).split())


def clave_autor(libro):
    """Primer autor con sus palabras ordenadas: «Gaiman, Neil» y «Neil Gaiman» caen en el mismo grupo."""
    autores = libro.get('autores') or []
    if isinstance(autores, str):
        autores = [autores]
    return ' '.join(sorted(normalizar(autores[0]).split())) if autores else ''


ROMANO = re.compile(r'^(?=.)m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$')
PALABRA = 80


def es_numero(palabra):
    """«2», «iii»: lo que distingue los tomos de una serie."""
    return palabra.isdigit() or bool(ROMANO.match(palabra))


def casi_iguales(titulo_a, titulo_b, umbral=UMBRAL):
    """Nota de 0 a 100 si dos títulos ya normalizados parecen el mismo libro mal escrito; None si no.

    Se compara palabra a palabra: «Capítulo III» / «Capítulo V» o «Ilíada…» / «Odisea…» se parecen mucho
    letra a letra y son libros distintos.
    """
    a, b = titulo_a.split(), titulo_b.split()
    corto, largo = sorted((a, b), key=len)
    if len(corto) >= 3 and len(corto) < len(largo) and largo[:len(corto)] == corto:
        return None if any(es_numero(p) for p in largo[len(corto):]) else 90.0  # el mismo título con subtítulo
    if len(a) == len(b):
        distintas = [(x, y) for x, y in zip(a, b) if x != y]
        if len(distintas) != 1 or any(es_numero(p) for p in distintas[0]):
            return None
        nota = parecido(*distintas[0])
        return nota if nota >= PALABRA else None  # una sola palabra cambia, y poco: errata
    if [p for p in a if es_numero(p)] != [p for p in b if es_numero(p)]:
        return None
    nota = parecido(''.join(a), ''.join(b))
    return nota if nota >= max(umbral, 97) else None  # mismas letras con los espacios en otro sitio


def misma_tirada(a, b):
    return (a.get('formato_edicion') == b.get('formato_edicion')
            and (a.get('editorial_slug') or normalizar(a.get('editorial'))) == (b.get('editorial_slug') or normalizar(b.get('editorial'))))


def repetidos(libros, campo):
    grupos = defaultdict(list)
    for libro in libros:
        if libro.get(campo):
            grupos[str(libro[campo])].append(libro.get('id'))
    return [{'clase': f'{campo.replace("13", "")}_repetido', 'valor': valor, 'ids': ids}
            for valor, ids in sorted(grupos.items()) if len(ids) > 1]


def buscar(libros, umbral=UMBRAL):
    """Devuelve (hallazgos, ediciones): parejas sospechosas y número de parejas que son ediciones legítimas."""
    hallazgos = repetidos(libros, 'isbn13') + repetidos(libros, 'slug')
    por_autor, ediciones = defaultdict(list), 0
    for libro in libros:
        clave = clave_autor(libro)
        if clave:
            por_autor[clave].append((normalizar(libro.get('titulo')), libro))
    for grupo in por_autor.values():
        for (titulo_a, a), (titulo_b, b) in combinations(grupo, 2):
            if not titulo_a or not titulo_b or (a.get('isbn13') and a.get('isbn13') == b.get('isbn13')):
                continue
            igual = titulo_a == titulo_b
            nota = 100.0 if igual else casi_iguales(titulo_a, titulo_b, umbral)
            if nota is None:
                continue
            if not misma_tirada(a, b):
                ediciones += 1
                continue
            hallazgos.append({'clase': 'misma_edicion' if igual else 'titulo_parecido', 'parecido': round(nota, 1),
                              'ids': [a.get('id'), b.get('id')], 'titulos': [a.get('titulo'), b.get('titulo')],
                              'autor': (a.get('autores') or [''])[0], 'estados': [a.get('estado'), b.get('estado')]})
    return hallazgos, ediciones


def informe(hallazgos, ediciones, total):
    cuenta = defaultdict(int)
    for h in hallazgos:
        cuenta[h['clase']] += 1
    lineas = ['# Duplicados del catálogo', '',
              f'{total} libros revisados con {MOTOR}. '
              + (', '.join(f'{n} {clase}' for clase, n in sorted(cuenta.items())) or 'Ningún duplicado sospechoso')
              + f'. {ediciones} parejas son ediciones distintas de la misma obra (no se listan).', '']
    if hallazgos:
        lineas += ['| Clase | Ids | Detalle |', '| --- | --- | --- |']
        for h in hallazgos[:TOPE_LISTA]:
            detalle = h.get('valor') or f'{h["autor"]}: «{h["titulos"][0]}» / «{h["titulos"][1]}» ({h["parecido"]})'
            lineas.append(f'| {h["clase"]} | {", ".join(f"`{i}`" for i in h["ids"])} | {str(detalle).replace("|", "/")} |')
        if len(hallazgos) > TOPE_LISTA:
            lineas.append(f'\nSe muestran {TOPE_LISTA} de {len(hallazgos)}; la lista completa está en el JSON.')
    return '\n'.join(lineas) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--catalogo', default=str(CATALOGO))
    parser.add_argument('--umbral', type=float, default=UMBRAL)
    parser.add_argument('--salida')
    parser.add_argument('--json')
    parser.add_argument('--estricto', action='store_true', help='devuelve 1 si hay ISBN o slug repetidos')
    args = parser.parse_args(argv)
    libros = json.loads(Path(args.catalogo).read_text(encoding='utf-8')).get('libros', [])
    hallazgos, ediciones = buscar(libros, args.umbral)
    texto = informe(hallazgos, ediciones, len(libros))
    if args.salida:
        Path(args.salida).write_text(texto, encoding='utf-8')
    else:
        sys.stdout.write(texto)
    if args.json:
        Path(args.json).write_text(json.dumps({'motor': MOTOR, 'libros': len(libros), 'ediciones': ediciones,
                                               'hallazgos': hallazgos}, ensure_ascii=False, indent=1), encoding='utf-8')
    rotos = [h for h in hallazgos if h['clase'] in ('isbn_repetido', 'slug_repetido')]
    return 1 if args.estricto and rotos else 0


if __name__ == '__main__':
    sys.exit(main())
