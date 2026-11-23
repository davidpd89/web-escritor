#!/usr/bin/env python3
"""Ensayo de carga hipotética: muta campo a campo libros reales y comprueba qué haría el código con cada uno.

La carga nocturna falló semanas seguidas por datos que nadie había probado (títulos de 206 caracteres, mojibake,
firmas institucionales...). Aquí se toma una muestra del catálogo real, se le aplican las mutaciones MUTACIONES (una
por caso, sobre una copia) y se pasa por validate() y por los generadores de texto de ficha. Cada caso acaba en:
  reparado   reading_normalizar lo reescribió bien y se publicaría corregido
  pasa       el libro mutado se publicaría tal cual
  aparta     validate lo rechaza nombrando el libro: la cuarentena lo apartaría (comportamiento correcto)
  SIN DUEÑO  el fallo no nombra al libro, o el código revienta con una excepción: pararía la carga entera (BUG)
Los SIN DUEÑO son los que hay que arreglar antes de la noche. Se agrupan por causa.

    python scripts/ensayo_carga.py [--muestra 40] [--semilla 1] [--json salida.json]
Sale con 1 si hay algún SIN DUEÑO.
"""
import argparse
import importlib.util
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
_spec = importlib.util.spec_from_file_location('rcb', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)
import reading_normalizar  # noqa: E402
import reading_quarantine  # noqa: E402

LARGO = ' '.join(['historia universal del pensamiento y de las ideas'] * 5)


def mojibake(texto):
    return texto.encode('utf-8').decode('latin-1')


def en_formatos(**cambios):
    return lambda b: [{**f, **cambios} for f in b.get('formatos_compra', [])]


def _isbn10(isbn13):
    """ISBN-10 equivalente de un ISBN-13 978…; los 979 no lo tienen y quedan igual."""
    if not isbn13.startswith('978'):
        return isbn13
    base = isbn13[3:12]
    resto = sum((10 - i) * int(c) for i, c in enumerate(base)) % 11
    control = (11 - resto) % 11
    return base + ('X' if control == 10 else str(control))


MUTACIONES = {
    'titulo largo 206': ('titulo', lambda b: (b['titulo'] + ' ' + LARGO)[:206]),
    'titulo 500': ('titulo', lambda b: (b['titulo'] + ' ' + LARGO * 3)[:500]),
    'titulo mayusculas': ('titulo', lambda b: b['titulo'].upper()),
    'titulo mojibake': ('titulo', lambda b: mojibake(b['titulo'] + ' ñandú')),
    'titulo inicial caida': ('titulo', lambda b: b['titulo'][0].lower() + b['titulo'][1:].upper()),
    'titulo con autor repetido': ('titulo', lambda b: f"{b['titulo']} - {b['autores'][0]}"),
    'titulo espacios y saltos': ('titulo', lambda b: f"  {b['titulo']}\n\t  "),
    'titulo con html': ('titulo', lambda b: b['titulo'] + ' <b>&amp;</b> "x"'),
    'titulo emoji': ('titulo', lambda b: b['titulo'] + ' 📚'),
    'titulo ligaduras': ('titulo', lambda b: b['titulo'] + ' ﬁn ﬂor'),
    'titulo vacio': ('titulo', lambda b: ''),
    'titulo solo numeros': ('titulo', lambda b: '1984'),
    'autor institucional largo': ('autores', lambda b: ['Grupo Andaluz de Trabajo en Endometriosis de la Sociedad Andaluza de Ginecología y Obstetricia']),
    'autores 12': ('autores', lambda b: [f'Autor Número {i} Apellido' for i in range(12)]),
    'autor mayusculas': ('autores', lambda b: [b['autores'][0].upper()]),
    'autor vacio': ('autores', lambda b: ['']),
    'autor mojibake': ('autores', lambda b: [mojibake('José Ángel Mañas')]),
    'autor con coma': ('autores', lambda b: ['Pérez-Reverte, Arturo']),
    'autor una letra': ('autores', lambda b: ['A.']),
    'sinopsis gritando': ('descripcion_breve', lambda b: b['descripcion_breve'].upper()),
    'sinopsis corta': ('descripcion_breve', lambda b: 'Corta.'),
    'sinopsis 5000': ('descripcion_breve', lambda b: (b['descripcion_breve'] + ' ') * 40),
    'sinopsis mojibake': ('descripcion_breve', lambda b: mojibake(b['descripcion_breve'] + ' Año')),
    'sinopsis html': ('descripcion_breve', lambda b: '<p>' + b['descripcion_breve'] + '</p><script>x</script>'),
    'isbn invalido': ('isbn13', lambda b: '9788498382373'),
    'isbn corto': ('isbn13', lambda b: '12345'),
    'isbn con guiones': ('isbn13', lambda b: '{}-{}-{}-{}-{}'.format(b['isbn13'][:3], b['isbn13'][3:5], b['isbn13'][5:9], b['isbn13'][9:12], b['isbn13'][12:])),
    'isbn-10 equivalente': ('isbn13', lambda b: _isbn10(b['isbn13'])),
    'titulo con caracteres invisibles': ('titulo', lambda b: '﻿' + b['titulo'][:3] + '​' + b['titulo'][3:] + '‮'),
    'isbn tipo': ('isbn13', lambda b: 9788498382372),
    'fecha invalida': ('fecha_publicacion', lambda b: '2026-13-45'),
    'fecha formato': ('fecha_publicacion', lambda b: '23/11/2026'),
    'fecha lejana': ('fecha_publicacion', lambda b: '2099-01-01'),
    'fecha tipo': ('fecha_publicacion', lambda b: 20261123),
    'anio absurdo': ('anio_publicacion', lambda b: 1),
    'editorial vacia': ('editorial', lambda b: ''),
    'editorial mayusculas': ('editorial', lambda b: (b.get('editorial') or 'X').upper()),
    'editorial slug inexistente': ('editorial_slug', lambda b: 'no-existe-xyz'),
    'portada inexistente': ('portada_local', lambda b: '/assets/reading-covers/no-existe.webp'),
    'portada fuente http': ('portada_fuente_url', lambda b: 'http://example.com/x.jpg'),  # NOSONAR: dato hostil de prueba
    'portada fuente vacia': ('portada_fuente_url', lambda b: ''),
    'edad rara': ('edad_recomendada', lambda b: 'de 3 a 99 años!!'),
    'campo desconocido': ('campo_nuevo_xyz', lambda b: 'x'),
    'slug mayusculas': ('slug', lambda b: b['slug'].upper()),
    'slug acentos': ('slug', lambda b: b['slug'] + '-ñ'),
    'precio negativo': ('formatos_compra', en_formatos(precio_centimos=-5)),
    'precio cero': ('formatos_compra', en_formatos(precio_centimos=0)),
    'precio como texto': ('formatos_compra', en_formatos(precio_centimos='12,50')),
    'precio enorme': ('formatos_compra', en_formatos(precio_centimos=99999999)),
    'url amazon http': ('formatos_compra', en_formatos(url='http://www.amazon.es/dp/x')),  # NOSONAR
    'formatos vacios': ('formatos_compra', lambda b: []),
    'None en titulo': ('titulo', lambda b: None),
    'None en autores': ('autores', lambda b: None),
    'autores string': ('autores', lambda b: 'Un Autor'),
}


def resultado(data, libro):
    """(clase, causa) de validar `data` con `libro` dentro y generar sus textos de ficha."""
    try:
        build.validate(data, ROOT)
    except build.ValidationError as exc:
        dueno = exc.libro == libro or exc.otro == libro or exc.posicion is not None
        return ('aparta' if dueno else 'SIN DUEÑO'), str(exc)[:160]
    except Exception as exc:
        return 'SIN DUEÑO', f'{type(exc).__name__}: {str(exc)[:140]}'
    b = next(x for x in data['libros'] if x['id'] == libro)
    try:
        build.book_title(b, data['libros'])
        build.card_title(b)
        build.book_meta_description(data, b)
    except Exception as exc:
        return 'SIN DUEÑO', f'texto de ficha: {type(exc).__name__}: {str(exc)[:140]}'
    return 'pasa', ''


def ensayo(muestra=40, semilla=1, por_mutacion=3):
    data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    publicados = [b for b in data['libros'] if b.get('estado') == 'publicado' and b.get('formatos_compra')]
    elegidos = random.Random(semilla).sample(publicados, min(muestra, len(publicados)))
    # Subconjunto: validar los 7.500 libros por caso tardaba ~10 s; con la muestra y sus relaciones, décimas.
    ids = {b['id'] for b in elegidos}
    data = {**data, 'libros': [b for b in data['libros'] if b['id'] in ids],
            'libro_categorias': [r for r in data['libro_categorias'] if r['libro_id'] in ids]}
    casos = []
    for nombre, (campo, fn) in MUTACIONES.items():
        for b in elegidos[:por_mutacion]:  # varios libros por mutación: el efecto depende del libro
            copia = json.loads(json.dumps(data))
            destino = next(x for x in copia['libros'] if x['id'] == b['id'])
            try:
                destino[campo] = fn(destino)
            except (KeyError, TypeError, IndexError):  # la mutación no aplica a este libro
                continue
            # Como la carga real: primero se reescribe lo reparable (reading_normalizar), luego se valida.
            reparado = reading_normalizar.normalizar([destino])
            reparado += reading_quarantine.repair_titles([destino], ROOT, '2026-11-23')
            clase, causa = resultado(copia, b['id'])
            casos.append((nombre, b['id'], 'reparado' if clase == 'pasa' and reparado else clase, causa))
    return casos


def aplicar(nombre, semilla=1):
    """Carga hipotética real: una mutación por libro (los que pasan validate) escrita en el catálogo de `raiz`.
    Es destructivo: usar solo en un worktree desechable; luego build-reading-catalogue.py + check-reading-data.py.
    Devuelve {id: mutación}."""
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', nombre):
        raise SystemExit('--aplicar: nombre de worktree inválido')
    ruta = ROOT / '.worktrees' / nombre / 'data/reading-catalogue.json'
    data = json.loads(ruta.read_text(encoding='utf-8'))
    publicados = [b for b in data['libros'] if b.get('estado') == 'publicado' and b.get('formatos_compra')]
    elegidos = random.Random(semilla).sample(publicados, len(MUTACIONES))
    aplicado = {}
    for (nombre, (campo, fn)), b in zip(MUTACIONES.items(), elegidos):
        try:
            b[campo] = fn(b)
        except (KeyError, TypeError, IndexError):
            continue
        aplicado[b['id']] = nombre
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return aplicado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--aplicar', help='nombre de un worktree desechable de .worktrees/ donde escribir la carga hipotética')
    ap.add_argument('--muestra', type=int, default=40)
    ap.add_argument('--semilla', type=int, default=1)
    ap.add_argument('--json')
    args = ap.parse_args()
    if args.aplicar:
        print(json.dumps(aplicar(args.aplicar, args.semilla), ensure_ascii=False, indent=1))
        return 0
    casos = ensayo(args.muestra, args.semilla)
    por = defaultdict(lambda: defaultdict(list))
    for nombre, _libro, clase, causa in casos:
        por[clase][nombre].append(causa)
    for clase in ('SIN DUEÑO', 'pasa', 'reparado', 'aparta'):
        print(f'\n== {clase}: {sum(len(v) for v in por[clase].values())} casos')
        for nombre, causas in sorted(por[clase].items()):
            print(f'  {nombre} ×{len(causas)}' + (f'  → {causas[0]}' if causas[0] and clase != 'aparta' else ''))
    if args.json:
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,60}', args.json):
            raise SystemExit('--json: solo un nombre de fichero, sin rutas')
        (Path.cwd() / args.json).write_text(json.dumps(casos, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if por['SIN DUEÑO'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
