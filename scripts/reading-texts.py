#!/usr/bin/env python3
"""Orientación propia por ficha: libro -> ChatGPT web (CDP) -> validación -> data/reading-texts -> main protegido.

  pending   lista los libros publicados sin texto vigente
  prompt    imprime la consulta de un lote (--ids o los primeros pendientes)
  validate  valida ficheros de salida contra los datos actuales
  run       bucle: consulta por lotes en un chat con correcciones, valida, guarda y publica en segundo plano
  publish   lleva los textos guardados a main con la misma cadena que el barrido

Los textos se guardan primero en .local/reading-texts/out (ignorado por git), para que el bucle
pueda cambiar de commit sin perder nada; publish los copia a data/reading-texts en un árbol de main.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/reading-texts/out'
STATE = ROOT / '.local/reading-texts/state.json'
PROMPT = ROOT / 'scripts/templates/reading-texts-prompt.md'
RRSS_TOOLS = Path(os.environ.get('RRSS_TOOLS', r'C:\GIT\RRSS_DavidPorto\tools'))
VERSION = 3
MAX_ATTEMPTS = 4
MAX_BLOCKS = 5
MIN_BLOCKS = 2
COPY_WORDS = 8
REPAIR_TURNS = 3  # correcciones dentro del mismo chat tras la primera respuesta
SHORT_BLOCK = 180  # un bloque válido más corto se pide más concreto en el turno de mejora
AFFINES = 5
AUDIENCES = (('infantil', {'infantil'}), ('juvenil', {'juvenil', 'fantasia-juvenil'}), ('adultos', {'adultos'}))
MIN_AFFINITY = 2.5  # suma de log(N/df): dos etiquetas muy comunes no bastan
# Siglas y nombres genéricos de formato o tienda: no son entidades que deban venir de las evidencias.
GENERIC_NAMES = {'isbn', 'kindle', 'amazon', 'ebook', 'pdf', 'epub', 'audible'}
# Afirmaciones que el modelo no puede sostener con los datos de entrada salvo que la sinopsis las traiga.
CLAIMS = re.compile(r'premi|galard|best ?seller|superventas|millones de|ejemplares vendidos|adaptaci|netflix|película|serie de televisi|'
                    r'la crítica|aclamad|traducid[oa] a|obra maestra|he leído|me encant|nuestra opinión|mi opinión|lo recomiendo', re.I)
# Valoraciones: la ficha orienta con hechos, no opina.
OPINION = re.compile(r'\britmo|trepidante|adictiv|apasionant|imprescindible|magistral|brillante|cautivador|emocionante|fascinante|inolvidable|'
                     r'absorbente|conmovedor|impresionante|maravillos|increíble|engancha|no te (puedes|puedas) perder|perfect[oa] para|'
                     r'ideal para|recomendamos|te encantar|una joya|bien escrit|prosa (cuidada|exquisita)', re.I)
# El lector no tiene que ver el proceso: dudas sobre las fuentes o referencias a «la sinopsis» delatan una ficha hueca.
META = re.compile(r'informaci[oó]n disponible|no se (detalla|especifica|indica|menciona|concreta|precisa|aclara|confirma)|'
                  r'no (existe|hay|consta) (una |ninguna )?(confirmaci|informaci|dato)|sin (una )?confirmaci|no (concreta|precisa|aclara|detalla|confirma)n?\b|'
                  r'\b(la|las|esta|estas) (sinopsis|evidencias?|fuentes?|datos disponibles)\b|seg[uú]n (la|los) (sinopsis|datos)', re.I)
# Muletillas de texto generado en español: suenan a plantilla y no informan.
# «Comparte las categorías Infancia e Infantil y juvenil» describe el menú de la web, no el libro.
TAXONOMY = re.compile(r'\bcategor[ií]as?\b', re.I)
AI_TELLS = re.compile(r'\ben definitiva\b|\bsin duda\b|sum[eé]rg|\bun viaje (a|por|hacia)\b|en un mundo (donde|en el que)|'
                      r'\bno solo\b[^.]{0,80}\bsino (también|que)\b|\bse erige\b|\bpromete\b|\bdescubre\b|a medida que avanza|'
                      r'\buna (lectura|obra|historia) que (nos )?invita|\bal fin y al cabo\b|\bcabe destacar\b|\bvale la pena\b', re.I)
FAMILIES = (  # Precedencia: lo infantil y lo práctico se reconocen antes que la no ficción y la narrativa.
    ('infantil', {'infantil', 'edad-de-0-a-3-anos', 'edad-a-partir-de-4-anos', 'edad-a-partir-de-7-anos'}),
    ('practico', {'cocina', 'desarrollo-personal', 'familia-y-crianza', 'nutricion-y-bienestar'}),
    ('no_ficcion', {'ensayo', 'historia', 'biografias-y-memorias', 'divulgacion-cientifica', 'filosofia'}),
)
EDITION = re.compile(r'traduc|prólogo|epílogo|introducción de|edición (especial|ilustrada|conmemorativa|limitada|revisada|anotada|definitiva|aniversario)|'
                     r'ilustrad[oa] por|ilustraciones de|cantos|notas de|apéndice|texto íntegro|edición bilingüe', re.I)
INTERACTIVE = re.compile(r'solapa|rueda|cartón|pegatina|texturas|pop-up|desplegable|sonido|actividades|colorear|juego|busca y encuentra|troquel', re.I)
CONTENTS = re.compile(r'recetas|ejercicios|índice|secciones|apartados|capítulos|pasos|técnicas|menús|planes', re.I)
ALL = {'narrativa', 'no_ficcion', 'practico', 'infantil', 'residual'}
MODULES = {  # módulo: (familias, necesidad del lector, condición sobre las evidencias)
    'para_quien': (ALL, 'saber en dos frases si encaja con lo que busca y con quién no encaja',
                   lambda e: e['categorias']),
    'edad_y_sensibilidad': ({'narrativa'}, 'saber si encaja por edad y contenido sensible',
                            lambda e: e.get('avisos_contenido') or e.get('edad_recomendada', 'Adultos') != 'Adultos'),
    'encaje_documentado': ({'narrativa'}, 'saber qué tipo de lectura propone según su género y premisa',
                           lambda e: len(e['sinopsis_editorial']) >= 400 and e['categorias']),
    'esta_edicion': ({'narrativa', 'no_ficcion', 'practico', 'infantil'}, 'distinguir esta edición de otras',
                     lambda e: EDITION.search(' '.join((e['sinopsis_editorial'], e.get('titulo', ''), e.get('edicion', ''))))),
    'temas_y_enfoque': ({'no_ficcion'}, 'saber qué cuestiones trata y desde qué enfoque',
                        lambda e: len(e['sinopsis_editorial']) >= 300),
    'contenido_y_uso': ({'practico'}, 'saber qué incluye y para qué sirve',
                        lambda e: CONTENTS.search(e['sinopsis_editorial'])),
    'como_se_utiliza': ({'infantil'}, 'saber cómo se usa o se juega con el libro',
                        lambda e: INTERACTIVE.search(e['sinopsis_editorial'])),
    'edad_y_formato': ({'infantil'}, 'saber si encaja por edad, formato y extensión',
                       lambda e: e.get('edad_recomendada')),
    'que_formato_elegir': (ALL, 'decidir entre tapa dura, tapa blanda, Kindle o audiolibro según el uso',
                           lambda e: len(e.get('formatos_disponibles', ())) >= 2 or (e.get('formato_edicion') and e.get('numero_paginas'))),
    'lecturas_afines': (ALL, 'saber con qué otros libros de este catálogo se compara y en qué se diferencia',
                        lambda e: e.get('afines_catalogo')),
}
FORMAT_LABELS = {'tapa-dura': 'Tapa dura', 'tapa-blanda': 'Tapa blanda', 'ebook': 'Kindle', 'audiolibro': 'Audiolibro'}
BASIC = {'titulo', 'autores', 'editorial', 'edicion', 'fecha_publicacion', 'numero_paginas', 'formato_edicion', 'idioma', 'isbn13'}


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalogue = load_module('reading_catalogue', 'scripts/build-reading-catalogue.py')


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def write_json(path, value):
    """Escritura atómica: la publicación en segundo plano lee las fichas mientras el bucle escribe otras."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def published(data):
    return [b for b in data['libros'] if b['estado'] == 'publicado']


def source_text(b):
    return '\n\n'.join(x for x in (b.get('sinopsis_completa'), b.get('sinopsis_breve'), b.get('descripcion_breve')) if x)


def family(cat_ids, synopsis):
    """Familia editorial por reglas; sin sinopsis útil no hay nada que orientar."""
    if len(synopsis) < 200:
        return 'residual'
    return next((name for name, ids in FAMILIES if cat_ids & ids), 'narrativa')


def payload(data, b):
    """Lo único que ve el modelo: evidencias de la edición con clave y los módulos que admite el libro."""
    cats = catalogue.categories(data, b)
    fields = ('titulo', 'autores', 'editorial', 'edicion', 'fecha_publicacion', 'numero_paginas', 'edad_recomendada', 'formato_edicion',
              'idioma', 'isbn13', 'avisos_contenido')
    evidence = {k: b[k] for k in fields if b.get(k)}
    evidence['categorias'] = [c['nombre'] for c in cats if c['tipo'] in ('genero', 'tematica', 'epoca', 'edad')]
    evidence['sinopsis_editorial'] = source_text(b)
    formats = sorted({o['formato'] for o in catalogue.purchase_formats(b)} | ({b['formato_edicion']} if b.get('formato_edicion') else set()),
                     key=list(FORMAT_LABELS).index)
    if formats:
        evidence['formatos_disponibles'] = [FORMAT_LABELS[f] for f in formats]
    affines = affine_books(data, b, {c['id'] for c in cats})
    if affines:
        # De qué va cada afín, no sus etiquetas: el modelo compara contenido y no el menú de la web.
        evidence['afines_catalogo'] = [f"«{x['titulo']}», de {', '.join(x['autores'])}: {gist(x)}" for x, _ in affines]
    fam = family({c['id'] for c in cats}, evidence['sinopsis_editorial'])
    modules = [{'modulo': m, 'titulo': catalogue.MODULE_TITLES[m], 'necesidad': need}
               for m, (fams, need, ok) in MODULES.items() if fam in fams and ok(evidence)]
    return {'id': b['id'], 'familia': fam, 'modulos_permitidos': modules, 'evidencias': evidence,
            'afines_ids': {x['titulo']: x['id'] for x, _ in affines}}


def gist(b, limit=200):
    """Primera frase de la sinopsis, cortada en palabra: basta para saber de qué va un libro afín."""
    text = ' '.join(source_text(b).split())
    first = re.split(r'(?<=[.!?])\s', text, maxsplit=1)[0]
    return first if len(first) <= limit else first[:limit].rsplit(' ', 1)[0] + '…'


def min_age(b):
    """Edad mínima de lectura declarada (Adultos = 18) o None si la editorial no la da."""
    age = b.get('edad_recomendada') or ''
    if age.casefold().startswith('adult'):
        return 18
    m = re.search(r'\d+', age)
    return int(m.group(0)) if m else None


def audience(cat_ids):
    """Público declarado por el catálogo (infantil, juvenil, adultos) o None si no consta."""
    return next((name for name, ids in AUDIENCES if cat_ids & ids), None)


def affine_books(data, b, cat_ids):
    """Libros publicados del catálogo más parecidos (o del mismo autor), para comparar y enlazar.

    Cada categoría compartida pesa según lo rara que es: compartir «Fantasía» dice poco y compartir «Hockey», mucho.
    Un álbum de 4 años y una novela de 12, o una juvenil y una de adultos, no se comparan aunque coincidan las etiquetas.
    """
    names = {c['id']: c['nombre'] for c in data['categorias'] if c['tipo'] in ('genero', 'tematica')}
    wanted = cat_ids & set(names)
    books = [x for x in published(data) if x['id'] != b['id']]
    cats = {x['id']: {c['id'] for c in catalogue.categories(data, x)} for x in books}
    df = {c: sum(c in v for v in cats.values()) + 1 for c in wanted}
    total = len(books) + 1
    age, public = min_age(b), audience(cat_ids)
    rows = []
    for x in books:
        shared = wanted & cats[x['id']]
        author = bool(set(x['autores']) & set(b['autores']))
        other, other_public = min_age(x), audience(cats[x['id']])
        if not author and ((age is not None and other is not None and abs(age - other) > 4)
                           or (public and other_public and public != other_public)):
            continue
        score = sum(math.log(total / df[c]) for c in shared)
        if author or (shared and score >= MIN_AFFINITY):
            rows.append((author, score, x['titulo'].casefold(), x, sorted(names[c] for c in shared) or ['autor']))
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    return [(r[3], r[4]) for r in rows[:AFFINES]]


def source_hash(p):
    """Cambia si cambian los datos que sostienen el texto o el contrato; no por precios ni por los libros afines,
    que crecen con el catálogo (el constructor oculta la comparación si un afín deja de estar publicado)."""
    stable = {**p, 'evidencias': {k: v for k, v in p['evidencias'].items() if k != 'afines_catalogo'}, 'afines_ids': None,
              'modulos_permitidos': [m['modulo'] for m in p['modulos_permitidos'] if m['modulo'] != 'lecturas_afines'], 'version': VERSION}
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def pending(data, out=OUT, state=None):
    state = {} if state is None else state
    rows = []
    for b in published(data):
        p = payload(data, b)
        if not p['modulos_permitidos']:
            continue
        h = source_hash(p)
        saved = read_json(out / (b['id'] + '.json'))
        entry = state.get(b['id'], {})
        if entry.get('hash') == h and entry.get('intentos', 0) >= MAX_ATTEMPTS:
            continue
        # Un texto vigente vuelve a la cola mientras le falten bloques que se descartaron o que el validador ya no acepta.
        stale = [f"{x.get('modulo')}: " + '; '.join(validate_block(p, x)) for x in (saved or {}).get('bloques', []) if validate_block(p, x)]
        if saved and saved.get('fuente_hash') == h and saved.get('version') == VERSION and not saved.get('descartados') and not stale:
            continue
        if stale:  # el motivo llega al prompt como «corregir»
            base = entry if entry.get('hash') == h else {'hash': h, 'intentos': 0}
            state[b['id']] = {**base, 'errores': list(dict.fromkeys([*base.get('errores', []), *stale]))}
        rows.append((bool(catalogue.amazon_destination(b)), len(p['modulos_permitidos']), b.get('fecha_publicacion') or '', b))
    # Primero lo que se puede comprar, con más evidencia aprovechable y más reciente.
    return [r[-1] for r in sorted(rows, key=lambda r: r[:3], reverse=True)]


def build_prompt(payloads, state=None):
    """Cada libro va con los motivos del rechazo anterior: se repara en vez de abstenerse."""
    state = state or {}
    books = []
    for p in payloads:
        row = {k: v for k, v in p.items() if k != 'afines_ids'}
        entry = state.get(p['id'], {})
        if entry.get('errores') and entry.get('hash') == source_hash(p):
            row['corregir'] = entry['errores']
        books.append(row)
    return PROMPT.read_text(encoding='utf-8').replace('{{LIBROS}}', json.dumps(books, ensure_ascii=False))


def words(text):
    return re.findall(r'\w+', unicodedata.normalize('NFKC', text).lower())


def ngrams(text, n=COPY_WORDS, names=()):
    """Secuencias de n palabras; cada nombre (título, autores) cuenta como una sola, porque citarlo no es copiar."""
    w = words(text)
    for name in sorted((words(x) for x in names), key=len, reverse=True):
        k, i = len(name), 0
        while k > 1 and i <= len(w) - k:
            if w[i:i + k] == name:
                w[i:i + k] = ['\x00']
            i += 1
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def as_text(value):
    return ' '.join(map(str, value)) if isinstance(value, list) else str(value)


def validate_block(p, x):
    """Errores de un bloque; las cifras y los nombres tienen que estar en las evidencias que el propio bloque cita."""
    if not isinstance(x, dict) or x.get('modulo') not in {m['modulo'] for m in p['modulos_permitidos']}:
        return ['módulo no permitido']
    text, keys = x.get('texto'), x.get('evidencias')
    if not isinstance(text, str) or not 80 <= len(text.strip()) <= 650 or '\n' in text.strip():
        return ['texto: entre 80 y 650 caracteres, sin saltos de línea']
    if not isinstance(keys, list) or not keys or any(k not in p['evidencias'] for k in keys):
        return ['evidencias inexistentes']
    errors = ['más de cuatro frases'] if len(re.findall(r'[.!?](?:\s|$)', text.strip())) > 4 else []
    if meta := META.search(text):
        errors.append('habla de las fuentes en vez de informar: ' + meta.group(0).lower())
    if tell := AI_TELLS.search(text):
        errors.append('muletilla: ' + tell.group(0).lower())
    if TAXONOMY.search(text):
        errors.append('nombra las categorías del catálogo: explica el parecido para el lector (tema, tono, público, autoría)')
    if x['modulo'] == 'lecturas_afines' and not linked(p, text):
        errors.append('no nombra ningún título de afines_catalogo')
    cited = ' '.join(as_text(p['evidencias'][k]) for k in keys)
    if x['modulo'] == 'lecturas_afines':  # nombrar un afín trae su título y su autoría aunque no cite afines_catalogo
        cited += ' ' + as_text(p['evidencias'].get('afines_catalogo', []))
    own = p['evidencias'].get('titulo', '') + ' ' + as_text(p['evidencias'].get('autores', ''))
    source = p['evidencias']['sinopsis_editorial']
    names = [p['evidencias'].get('titulo', ''), *p['evidencias'].get('autores', [])]
    if ngrams(text, names=names) & ngrams(source, names=names):
        errors.append(f'copia {COPY_WORDS} palabras seguidas de la sinopsis')
    numbers = set(re.findall(r'\d+', text)) - set(re.findall(r'\d+', cited + ' ' + own))
    if numbers:
        errors.append('cifras sin respaldo: ' + ', '.join(sorted(numbers)))
    claims = {m.group(0).lower() for m in CLAIMS.finditer(text)} - {m.group(0).lower() for m in CLAIMS.finditer(source)}
    if claims:
        errors.append('afirmaciones sin respaldo: ' + ', '.join(sorted(claims)))
    if opinion := OPINION.search(text):
        errors.append('valoración: ' + opinion.group(0).lower())
    known = set(words(cited + ' ' + own))
    # Mayúscula a mitad de frase = nombre propio: tiene que venir de las evidencias citadas.
    names = {m.group(0) for m in re.finditer(r'[A-ZÁÉÍÓÚÑ][\wáéíóúñü]+', text)
             if (before := text[:m.start()].rstrip()) and before[-1] not in '.!?¿¡«"(:\n'}
    unknown = sorted(n for n in names if n.lower() not in known | GENERIC_NAMES)
    if unknown:
        errors.append('nombres sin respaldo: ' + ', '.join(unknown[:5]))
    return errors


def valid_blocks(p, blocks):
    """Bloques guardados que siguen pasando el validador vigente: endurecerlo retira lo que ya no cumple."""
    return [x for x in blocks or [] if not validate_block(p, x)]


def title_forms(title):
    """El título completo y su forma corta: sin paréntesis de edición o colección ni subtítulo tras «:» o « - »."""
    short = re.split(r'\s+[-–—]\s+|:\s', re.sub(r'\s*\([^)]*\)', '', title))[0].strip(' .,;')
    return {f for f in (title.strip(), short) if len(f) >= 8 or f == title.strip()}


def linked(p, text):
    """Ids de los libros afines que el texto nombra por su título (completo o en su forma corta)."""
    folded = text.casefold()
    return [i for title, i in p.get('afines_ids', {}).items() if any(f.casefold() in folded for f in title_forms(title))]


def validate_text(p, t):
    """Devuelve (bloques aceptados, errores). Un bloque malo se descarta y su motivo vuelve al prompt para repararlo."""
    if not isinstance(t, dict) or t.get('id') != p['id']:
        return [], ['id distinto']
    blocks = t.get('bloques')
    if not isinstance(blocks, list) or len(blocks) > MAX_BLOCKS:
        return [], ['bloques: lista inválida']
    if not blocks:
        return [], ['sin bloques: no se admite abstenerse, escribe los módulos permitidos con lo que sí dicen las evidencias']
    accepted, errors = [], []
    for x in blocks:
        problems = validate_block(p, x)
        if not problems and x['modulo'] in {y['modulo'] for y in accepted}:
            problems = ['módulo repetido']
        mine = set(words(x['texto'])) if not problems else set()
        if not problems and any(len(mine & set(words(y['texto']))) > 0.6 * len(mine) for y in accepted):
            problems = ['repite otro bloque']
        if problems:
            errors.append(f"{x.get('modulo') if isinstance(x, dict) else '?'}: " + '; '.join(problems))
            continue
        accepted.append({'modulo': x['modulo'], 'texto': x['texto'].strip(), 'evidencias': x['evidencias'],
                         **({'enlaces': linked(p, x['texto'])} if x['modulo'] == 'lecturas_afines' else {})})
    missing = sorted({m['modulo'] for m in p['modulos_permitidos']} - {x['modulo'] for x in accepted})
    if missing:
        errors.append('faltan módulos: ' + ', '.join(missing))
    # Umbral: al menos dos evidencias distintas y una que no sea un dato bibliográfico básico.
    keys = {k for x in accepted for k in x['evidencias']}
    if accepted and (len(keys) < 2 or not keys - BASIC):
        return [], errors + ['por debajo del umbral: solo datos básicos']
    if len(accepted) < min(MIN_BLOCKS, len(p['modulos_permitidos'])):
        return [], errors + [f'menos de {MIN_BLOCKS} bloques válidos']
    return accepted, errors


def extract_json(answer):
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', answer, re.S)
    for chunk in fenced[::-1] + [answer[answer.find('{'):answer.rfind('}') + 1]]:
        try:
            value = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get('fichas'), list):
            return value['fichas']
    return None


def answer_label(ids):
    def label(answer):
        rows = extract_json(answer or '')
        if rows is None:
            return 'JSON_TRUNCADO'
        return 'JSON_VALIDO' if sorted(r.get('id') for r in rows if isinstance(r, dict)) == sorted(ids) else 'IDS_INCORRECTOS'
    return label


def save_results(payloads, rows, state, out=OUT):
    by_id = {r.get('id'): r for r in rows if isinstance(r, dict)}
    saved = rejected = 0
    for p in payloads:
        entry = state.setdefault(p['id'], {})
        h = source_hash(p)
        if entry.get('hash') != h:
            entry.update(hash=h, intentos=0)
        entry['intentos'] += 1
        t = by_id.get(p['id'])
        blocks, errors = ([], ['sin respuesta']) if t is None else validate_text(p, t)
        entry['errores'] = errors
        old = read_json(out / (p['id'] + '.json'))
        kept = valid_blocks(p, old.get('bloques')) if old and old.get('fuente_hash') == h else []
        # Una reparación completa lo guardado (puede traer solo el módulo que faltaba); una peor no lo sustituye.
        merged = blocks + [x for x in kept if x['modulo'] not in {y['modulo'] for y in blocks}]
        blocks = merged if blocks and len(merged) > len(kept) else []
        if not blocks:  # se reintenta con los motivos hasta MAX_ATTEMPTS
            rejected += 1
            continue
        record = {'id': p['id'], 'familia': p['familia'], 'bloques': blocks,
                  'descartados': errors, 'version': VERSION, 'fuente_hash': h, 'origen': 'chatgpt-web'}
        write_json(out / (p['id'] + '.json'), record)
        saved += 1
    return saved, rejected


def instant_power(pg, _level=None):
    """Selector de ChatGPT al mínimo (Instant) para los textos de fichas.

    Prueba del 02/11/2026 con los mismos 5 libros: Instant tarda ~136 s por lote frente a 163-291 s en
    High y el validador acepta los mismos bloques (88 % frente a 90 %). RRSS sigue en Alta: su consulta
    vuelve a subir el selector en cada uso. Se lleva al extremo con flechas, sin depender del idioma.
    """
    try:
        button = pg.locator('button[aria-label*="modelo" i], button[aria-label*="model" i]').first
        button.wait_for(state='visible', timeout=20000)
        button.click()
        pg.wait_for_timeout(1200)
        slider = pg.locator('[role="slider"]').first
        if slider.count():
            slider.focus()
            for _ in range(4):
                pg.keyboard.press('ArrowLeft')
                pg.wait_for_timeout(600)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(500)
        return bool(slider.count())
    except Exception:  # noqa: BLE001 - sin selector se escribe con el nivel que haya
        return False


def rrss():
    """Navegador y proyecto de ChatGPT de RRSS, solo importados: sus ficheros no cambian."""
    # El horario de descanso 00-07 h es de las redes sociales (parecer uso humano); los textos de la
    # web trabajan toda la noche (David, 02/11/2026), así que este proceso queda fuera de esa regla.
    os.environ['RRSS_NIGHT_OK'] = '1'
    sys.path.insert(0, str(RRSS_TOOLS))
    import chatgpt_consult
    return chatgpt_consult


def json_label(answer):
    return 'JSON_VALIDO' if extract_json(answer or '') is not None else 'JSON_TRUNCADO'


def chat(question, port, wait_min, follow_up):
    """Un chat nuevo con varios turnos: tras cada respuesta, `follow_up(respuesta, turno)` da el siguiente mensaje
    o None. El turno del navegador se toma solo para escribir; la espera de cada respuesta va sin él."""
    os.environ['RRSS_CHATGPT_CDP_PORT'] = str(port)
    cc = rrss()
    import action_ledger as al
    import browser_common as bc
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    pg = None
    try:
        target, turn = cc.browser_target()
        message, n = question, 0
        while message:
            with al.browser_session(wait_minutes=40, name=turn):
                if pg is None:
                    browser = bc.connect_cdp(p.chromium, f'http://127.0.0.1:{target}')
                    if not browser.contexts:
                        raise RuntimeError('CDP sin contexto ChatGPT')
                    pg = browser.contexts[0].new_page()
                    pg.goto(cc.PROJECT_URL, wait_until='domcontentloaded', timeout=40000)
                    pg.wait_for_timeout(6000)
                    if 'auth' in pg.url or 'login' in pg.url or cc._login_button_visible(pg):
                        cc.notify_login_needed(target)
                        raise cc.ChatGPTLoginRequired('ChatGPT pide iniciar sesión: lo hace David')
                    cc.assert_expected_project(pg.url)
                    instant_power(pg)
                pg.locator('[contenteditable="true"]').first.fill(message)
                pg.wait_for_timeout(2000)
                pg.locator(cc.SEND_BUTTON).first.click()
                pg.wait_for_timeout(6000)
            answer, _ = cc._wait_answer(pg, wait_min if n == 0 else max(3, min(wait_min, 10)), json_label)
            n += 1
            if n == 1 and not answer:
                raise RuntimeError('respuesta no confirmada de ChatGPT: fin de plazo')
            message = follow_up(answer, n)
    finally:
        try:
            if pg is not None:
                pg.close()
        finally:
            p.stop()
        cc._close_dedicated_if_idle()


HINTS = (  # motivo del validador -> instrucción concreta para la corrección
    ('cifras sin respaldo', 'cada cifra tiene que estar literalmente en las evidencias que cita el bloque (o en el título); si no, quítala'),
    ('nombres sin respaldo', 'quita los nombres propios que no estén en las evidencias citadas: nada de autores, obras ni lugares traídos de fuera'),
    ('no nombra ningún título', 'nombra uno o dos títulos de afines_catalogo tal como aparecen, sin comillas'),
    ('más de cuatro frases', 'máximo cuatro frases (cuenta cada punto, exclamación o interrogación final)'),
    ('copia', 'reformula con palabras propias: no repitas ocho palabras seguidas de la sinopsis'),
    ('valoración', 'describe sin valorar ni recomendar'),
    ('muletilla', 'quita la muletilla y di el dato concreto'),
    ('habla de las fuentes', 'no menciones fuentes ni datos ausentes: escribe con lo que sí hay'),
    ('categorías', 'explica el parecido por tema, tono, público o autoría, sin decir «categoría»'),
    ('entre 80 y 650', 'el texto va de 80 a 650 caracteres en un solo párrafo'),
    ('repite otro bloque', 'que no repita lo que dice otro bloque de la ficha'),
)


def absorb(payloads, fichas, rows, improving=False):
    """Funde un turno en las fichas: el bloque nuevo sustituye al del mismo módulo si el anterior no pasaba el
    control o, en el turno de mejora, si el nuevo también pasa y es más completo."""
    for r in rows:
        p = payloads.get(r.get('id')) if isinstance(r, dict) else None
        if not p or not isinstance(r.get('bloques'), list):
            continue
        blocks = fichas.setdefault(p['id'], {'id': p['id'], 'bloques': []})['bloques']
        for x in r['bloques']:
            if not isinstance(x, dict):
                continue
            i = next((k for k, y in enumerate(blocks) if y.get('modulo') == x.get('modulo')), None)
            if i is None:
                blocks.append(x)
            elif improving:
                if not validate_block(p, x) and len(str(x.get('texto', ''))) > len(str(blocks[i].get('texto', ''))):
                    blocks[i] = x
            elif validate_block(p, blocks[i]):
                blocks[i] = x


def repair_message(payloads, fichas):
    """Mensaje de corrección en el mismo chat con los motivos de cada ficha, o None si todas pasan."""
    lines, hints = [], []
    for p in payloads.values():
        if p['id'] not in fichas:
            lines.append(f"- {p['id']}: falta la ficha completa")
            continue
        _, errors = validate_text(p, fichas[p['id']])
        if 'módulo no permitido' in ' '.join(errors):
            errors.append('módulos permitidos: ' + ', '.join(m['modulo'] for m in p['modulos_permitidos']))
        lines += [f"- {p['id']}: {e}" for e in errors]
        hints += [h for key, h in HINTS for e in errors if key in e]
    if not lines:
        return None
    return ('Algunos bloques no pasan el control de calidad. Corrige solo estos, con las mismas reglas y las mismas evidencias de cada libro:\n'
            + '\n'.join(lines) + '\n\nCómo corregirlos:\n' + '\n'.join('- ' + h for h in dict.fromkeys(hints))
            + '\n\nResponde con un único bloque ```json {"fichas": [{"id": "...", "bloques": [...]}]} que traiga solo esas fichas, '
              'con los bloques corregidos y los módulos que faltan; los demás bloques ya están aceptados.')


def improve_message(payloads, fichas):
    """Turno de mejora: los bloques válidos pero escuetos se piden más concretos; None si no hay ninguno."""
    lines = []
    for p in payloads.values():
        blocks, _ = validate_text(p, fichas.get(p['id'], {'id': p['id'], 'bloques': []}))
        lines += [f"- {p['id']} / {x['modulo']}: «{x['texto']}»" for x in blocks if len(x['texto']) < SHORT_BLOCK]
    if not lines:
        return None
    return ('Estos bloques pasan el control pero son escuetos. Reescríbelos más concretos y útiles para decidir, con datos de las '
            'evidencias de su libro (puedes citar más claves de evidencias), de 2 a 4 frases y con las mismas reglas:\n' + '\n'.join(lines)
            + '\n\nResponde con un único bloque ```json {"fichas": [...]} que traiga solo esas fichas y esos bloques.')


def converse(payloads, state, port, wait_min, send=chat):
    """Consulta de un lote en un único chat: respuesta, hasta REPAIR_TURNS correcciones con los motivos del
    validador y un turno final de mejora. Devuelve las fichas fundidas; validate_text decide al guardar."""
    by_id = {p['id']: p for p in payloads}
    fichas, phase = {}, {'mejora': False}
    ids = ', '.join(by_id)

    def follow_up(answer, n):
        rows = extract_json(answer or '')
        if rows is None:
            return None if n > REPAIR_TURNS else (
                'Devuelve otra vez la respuesta completa: un único bloque ```json con {"fichas": [...]} y estos id: ' + ids)
        absorb(by_id, fichas, rows, improving=phase['mejora'])
        if phase['mejora']:
            return None
        message = repair_message(by_id, fichas) if n <= REPAIR_TURNS else None
        if message:
            print(f'  turno {n + 1}: corrección', flush=True)
            return message
        phase['mejora'] = True
        message = improve_message(by_id, fichas)
        if message:
            print(f'  turno {n + 1}: mejora de bloques escuetos', flush=True)
        return message

    send(build_prompt(payloads, state), port, wait_min, follow_up)
    return list(fichas.values())


def idle_seconds(exc):
    """Pausa tras un fallo de la consulta: hasta el fin del horario de descanso de RRSS o un minuto ante otros errores."""
    if type(exc).__name__ == 'QuietHoursError':
        sys.path.insert(0, str(RRSS_TOOLS))
        import quiet_hours
        return max(60, quiet_hours.seconds_until_active())
    return 60


def consult_batch(payloads, state, args):
    """Respuesta del lote, o None si falló la consulta: un fallo de infraestructura no gasta intentos de los libros."""
    ids = [p['id'] for p in payloads]
    try:
        return converse(payloads, state, args.port, args.wait_min)
    except Exception as exc:  # noqa: BLE001 - un lote fallido no para el bucle
        wait = idle_seconds(exc)
        print(f'Lote {ids[0]}…: {type(exc).__name__}; espera {wait // 60:.0f} min', flush=True)
        time.sleep(wait)
        return None


def git(*args, cwd=ROOT, capture=False):
    if capture:
        return subprocess.check_output(['git', *args], cwd=cwd, text=True, encoding='utf-8')
    subprocess.run(['git', *args], cwd=cwd, check=True)


def git_add(paths, cwd=ROOT):
    """Añade las rutas por stdin: cientos de fichas regeneradas superan el límite de línea de comandos de Windows."""
    subprocess.run(['git', 'add', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=cwd, check=True,
                   input='\0'.join(paths).encode('utf-8'))


CATALOGUE_YIELD = timedelta(hours=2)


def catalogue_in_ci(opened, now=None):
    """Rama de una carga de libros abierta hace menos de CATALOGUE_YIELD, o None.

    Los textos regeneran fichas y pagefind igual que la carga: fusionar durante sus ~35 min de CI la dejaba en
    conflicto (PR #1145, 100 libros, por #1144). Los textos esperan en su estado local; una carga roja olvidada
    deja de frenarlos al cabo de CATALOGUE_YIELD.
    """
    now = now or datetime.now(timezone.utc)
    for pr in opened:
        name = pr['headRefName']
        if name.startswith('automation/reading-catalogue-') and not name.startswith('automation/reading-catalogue-textos-') and \
                now - datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00')) < CATALOGUE_YIELD:
            return name
    return None


def publish(out=OUT):
    """Copia los textos a un árbol limpio de origin/main y publica con el flujo protegido del barrido."""
    texts = sorted(out.glob('*.json'))
    if not texts:
        print('Sin textos que publicar')
        return False
    publisher = load_module('publish_reading_refresh', 'scripts/publish-reading-refresh.py')
    batch = catalogue_in_ci(json.loads(publisher.publication.gh(
        'pr', 'list', '--state', 'open', '--base', 'main', '--limit', '100', '--json', 'headRefName,createdAt')))
    if batch:
        print(f'Carga del catálogo en CI ({batch}): los textos esperan a la siguiente publicación', flush=True)
        return False
    tree = ROOT / '.local/reading-texts/main'
    git('fetch', '-q', 'origin', 'main')
    if not tree.exists():
        git('worktree', 'add', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    git('clean', '-qfd', cwd=tree)
    data = read_json(tree / 'data/reading-catalogue.json')
    ids = {b['id'] for b in published(data)}
    target = tree / 'data/reading-texts'
    target.mkdir(exist_ok=True)
    for path in texts:
        record = read_json(path)
        if path.stem in ids:
            # Se publica solo lo que pasa el validador vigente, aunque se guardara con uno más permisivo.
            blocks = valid_blocks(payload(data, next(b for b in published(data) if b['id'] == path.stem)), record.get('bloques'))
            if len(blocks) >= MIN_BLOCKS:
                write_json(target / path.name, {**record, 'bloques': blocks})
    run = lambda *cmd: subprocess.run([sys.executable, *cmd], cwd=tree, check=True)
    for script in ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        run('scripts/' + script)
    for script in ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        run('scripts/' + script, '--check')
    run('tests/test-reading-catalogue.py')
    run('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_reading*.py', '-q')
    paths = [line[3:] for line in git('status', '--porcelain', '--untracked-files=all', cwd=tree, capture=True).splitlines()]
    if not paths:
        print('Los textos ya están en main')
        return False
    publisher = load_module('publish_reading_refresh', 'scripts/publish-reading-refresh.py')
    outside = [p for p in paths if not publisher.allowed_path(p)]
    if outside:
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str(outside))
    now = datetime.now(ZoneInfo('Europe/Madrid'))
    branch = 'automation/reading-catalogue-textos-' + now.strftime('%Y-%m-%d-%H%M%S')
    count = len([p for p in paths if p.startswith('data/reading-texts/')])
    git('switch', '-q', '-c', branch, cwd=tree)
    git_add(paths, cwd=tree)
    git('commit', '-q', '-m', f'Orientación propia en {count} fichas de lectura', cwd=tree)
    git('push', '-q', 'origin', 'HEAD:refs/heads/' + branch, cwd=tree)
    body = tree.parent / 'pr-body.md'
    body.write_text(f'Añade texto propio validado a {count} fichas: por qué leerlo, para quién, tono, libros afines del catálogo y preguntas frecuentes.\n\n'
                    'Cada texto pasa el validador de scripts/reading-texts.py (sin copia de la sinopsis, sin cifras, nombres ni premios sin respaldo). '
                    'Se ejecutan las reglas de main antes de fusionar y después se despliega.\n', encoding='utf-8')
    for old in json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--json', 'number,headRefName')):
        if old['headRefName'].startswith('automation/reading-catalogue-textos-'):
            publisher.publication.gh('pr', 'close', str(old['number']), '--comment', 'Sustituida por una publicación de textos más reciente.')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', f'Orientación propia en {count} fichas de lectura', '--body-file', str(body))
    git('switch', '-q', '--detach', cwd=tree)
    publisher.run(branch)
    return True


def publish_due(args, now, last):
    """Toca publicar: a una de las horas de --publish-at (Madrid), una vez por hora y día, o al llegar a --publish-every."""
    if args.publish_at:
        return now.hour in args.publish_at and now.strftime('%Y-%m-%d %H') != last
    return bool(args.publish_every)


def start_publish():
    """Publicación en segundo plano: el bucle sigue generando mientras corren las pruebas locales y el CI de la PR."""
    log = open(ROOT / '.local/reading-texts/publish.log', 'a', encoding='utf-8')
    log.write(f'--- {datetime.now(ZoneInfo("Europe/Madrid")):%Y-%m-%d %H:%M} publicación\n')
    log.flush()
    return subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), 'publish'], cwd=ROOT, stdout=log, stderr=log,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def loop(args):
    state = read_json(STATE, {})
    data = read_json(ROOT / 'data/reading-catalogue.json')
    deadline = time.time() + args.hours * 3600
    done = since_publish = 0
    publishing, last = None, ''
    while time.time() < deadline and done < args.max_books:
        now = datetime.now(ZoneInfo('Europe/Madrid'))
        if publishing is not None and publishing.poll() is not None:
            print(f'Publicación terminada ({publishing.returncode})', flush=True)
            publishing = None
        if publishing is None and since_publish and publish_due(args, now, last) and \
                (args.publish_at or since_publish >= args.publish_every):
            publishing, last, since_publish = start_publish(), now.strftime('%Y-%m-%d %H'), 0
            print('Publicación lanzada en segundo plano', flush=True)
        books = pending(data, state=state)[:args.batch]
        if books:
            payloads = [payload(data, b) for b in books]
            rows = consult_batch(payloads, state, args)
            if rows is None:
                continue
            saved, rejected = save_results(payloads, rows, state)
            write_json(STATE, state)
            done += len(books)
            since_publish += saved
            print(f'Lote de {len(books)}: {saved} guardados, {rejected} rechazados', flush=True)
        elif not args.refresh_data:
            print('Sin pendientes', flush=True)
            break
        else:  # sin pendientes se esperan los libros nuevos que traiga la ingesta
            time.sleep(600)
        if args.refresh_data:
            try:
                git('fetch', '-q', 'origin', 'main')
                data = json.loads(git('show', 'origin/main:data/reading-catalogue.json', capture=True))
            except (subprocess.CalledProcessError, ValueError) as exc:  # p. ej. la publicación tiene la referencia bloqueada
                print(f'Catálogo sin refrescar: {exc}', flush=True)
    if publishing is not None:
        publishing.wait()
    elif since_publish and not args.publish_at and args.publish_every:
        publish()


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pending')
    pr = sub.add_parser('prompt')
    pr.add_argument('--ids', nargs='*')
    pr.add_argument('--batch', type=int, default=5)
    va = sub.add_parser('validate')
    va.add_argument('files', nargs='+', type=Path)
    ru = sub.add_parser('run')
    ru.add_argument('--port', type=int, default=9240)
    ru.add_argument('--batch', type=int, default=5)
    ru.add_argument('--max-books', type=int, default=10 ** 6)
    ru.add_argument('--hours', type=float, default=24)
    ru.add_argument('--wait-min', type=int, default=20)
    ru.add_argument('--publish-every', type=int, default=0, help='0 = solo guardar en .local')
    ru.add_argument('--publish-at', type=int, nargs='*', default=[],
                    help='horas de Madrid a las que publicar en segundo plano (p. ej. 21); sustituye a --publish-every')
    ru.add_argument('--refresh-data', action='store_true', help='releer el catálogo de origin/main tras cada lote')
    sub.add_parser('publish')
    args = parser.parse_args(argv)
    data = read_json(ROOT / 'data/reading-catalogue.json')
    if args.cmd == 'pending':
        rows = pending(data, state=read_json(STATE, {}))
        print(f'{len(rows)} pendientes')
        for b in rows[:20]:
            print(b['id'], b['titulo'])
    elif args.cmd == 'prompt':
        books = [b for b in published(data) if b['id'] in args.ids] if args.ids else pending(data)[:args.batch]
        print(build_prompt([payload(data, b) for b in books]))
    elif args.cmd == 'validate':
        by_id = {b['id']: b for b in published(data)}
        bad = 0
        for path in args.files:
            t = read_json(path)
            for row in (t['fichas'] if 'fichas' in t else [t]):
                blocks, errors = validate_text(payload(data, by_id[row['id']]), row) if row.get('id') in by_id else ([], ['libro desconocido'])
                bad += bool(errors)
                print(row.get('id'), f'{len(blocks)} bloques', 'OK' if not errors else '; '.join(errors))
        return 1 if bad else 0
    elif args.cmd == 'run':
        loop(args)
    elif args.cmd == 'publish':
        publish()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
