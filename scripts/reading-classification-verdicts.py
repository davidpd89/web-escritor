#!/usr/bin/env python3
"""Veredictos de clasificación automáticos: cada libro publicado sin veredicto pasa por ChatGPT hasta quedar fijado.

Proceso (diseño consultado con GPT el 27/11, con sus fuentes: self-consistency, sesgo de posición, Dual-Expert):
  R2  clasificación a ciegas en lotes de ~30 libros (sin enseñar la etiqueta de las reglas, ids temporales b01…).
      Si coincide con las reglas (mismos géneros y público) → veredicto «r2».
  R3  otra pasada a ciegas en una conversación nueva y otro orden. Si coincide con las reglas → «r3=reglas»;
      si coincide con R2 en público y género principal → «r2r3» (principal + secundarios comunes).
  R4  desempate: las dos lecturas como opciones A/B en orden aleatorio, con confianza y fuente. Alta o media → «r4».
      Si no, el libro se queda con las reglas y se reintenta solo si cambia su ficha (máx. INTENTOS por huella).

El estado de cada libro (respuestas de cada fase y la huella de su ficha) vive en .local/clasificacion-veredictos/
estado.json: una ejecución cortada (PC apagado) sigue donde iba sin repetir consultas. La publicación de textos
(scripts/reading-texts.py, 21 h) lleva los veredictos aceptados a data/reading-classification-verdicts.json con
`fusionar()`, rederiva el catálogo y regenera; el veredicto guarda `h` (huella de la ficha), `m` (método) y
`v` (versión del prompt). Un veredicto cuya `h` ya no casa con la ficha vuelve a la cola; los antiguos sin `h` valen.

    python scripts/reading-classification-verdicts.py estado
    python scripts/reading-classification-verdicts.py run [--puerto 9262] [--pestanas 2] [--lote 30] [--max-libros N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = 'data/reading-classification-verdicts.json'
DIR = ROOT / '.local' / 'clasificacion-veredictos'
ESTADO = DIR / 'estado.json'
METRICAS = DIR / 'metricas.jsonl'
DERIVADOS = {'romantasy', 'fantasia-juvenil', 'fantasia-oscura'}  # los pone el código, no se preguntan
FICCION = {'misterio-y-thriller', 'fantasia', 'romance', 'ciencia-ficcion', 'terror', 'novela-historica', 'aventuras', 'humor'}
INTENTOS = 2        # desempates fallidos con la misma ficha antes de dejarla con las reglas
REINTENTOS_FASE = 2  # respuestas inválidas de un libro en una fase antes de dejarlo para otra ejecución
LOTE = 30

CRITERIOS = """CRITERIOS por género: «aventuras» SOLO si la aventura/viaje/acción define el libro; «relatos» SOLO colección de cuentos o relatos independientes (nunca una novela); «narrativa» = novela o ficción literaria/contemporánea SIN género más concreto (si es thriller, romance, fantasía…, usa ese); «narrativa-juvenil» SOLO novela en prosa para jóvenes (nunca cómic/manga); «romance» solo si la historia de amor es el eje; «romance»+«fantasia» si el romance es central en una fantasía; «terror» solo si el miedo es el eje; «misterio-y-thriller» incluye policíaca, negra, suspense; «familia-y-crianza» SOLO guías para padres, embarazo y educación de hijos; «desarrollo-personal» autoayuda y hábitos; «infantil» libro para niños (álbum, primeros lectores, actividades); cómics y mangas: «comic-y-novela-grafica» + el género de su historia; «biografias-y-memorias» biografía, memorias, diarios; «guias-y-referencia» diccionarios, atlas, enciclopedias; cuadernos, agendas y libros de colorear → «ocio-y-aficiones»; la divulgación es para público general, lo profesional o universitario es «manuales-y-formacion»."""


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def write_json(path, value):
    """Escritura atómica: un corte a mitad no deja el estado ilegible."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_bytes((json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8'))
    os.replace(tmp, path)


def escribir_veredictos(path, value):
    """Formato del fichero publicado: un libro por línea y orden por id (diffs de una línea por veredicto)."""
    texto = '{\n' + ',\n'.join(f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}'
                                for k, v in sorted(value.items())) + '\n}\n'
    tmp = Path(path).with_suffix('.json.tmp')
    tmp.write_bytes(texto.encode('utf-8'))
    os.replace(tmp, path)


# ---------------------------------------------------------------- catálogo

def taxonomia(data: dict) -> dict:
    """Géneros que se preguntan: activos del catálogo menos los derivados, más los nuevos que admite el código."""
    from reading_taxonomy import NEW_GENRES
    gen = {c['id']: (c['nombre'], c.get('descripcion') or '') for c in data['categorias']
           if c['tipo'] == 'genero' and c.get('activa', True) and c['id'] not in DERIVADOS}
    for gid, (nombre, desc, _orden) in NEW_GENRES.items():
        gen.setdefault(gid, (nombre, desc))
    return dict(sorted(gen.items()))


def version_prompt(gen: dict) -> str:
    return hashlib.sha256((CRITERIOS + json.dumps(gen, ensure_ascii=False, sort_keys=True) + PROMPT_CIEGO + PROMPT_R4)
                          .encode()).hexdigest()[:8]


def texto(b: dict) -> str:
    return (b.get('sinopsis_breve') or b.get('descripcion_breve') or b.get('sinopsis_completa') or '').replace('\n', ' ')


def huella(b: dict) -> str:
    """Lo que el clasificador lee de la ficha. Si cambia, el veredicto deja de valer y el libro vuelve a la cola."""
    campos = (b.get('titulo'), b.get('autores'), b.get('editorial'), texto(b), b.get('edad_recomendada'),
              b.get('publico_amazon'), b.get('formato_edicion'))
    return hashlib.sha256(json.dumps(campos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def etiquetas_reglas(data: dict) -> dict:
    """{id: (géneros sin derivados ni «infantil», público)} tal como lo deja hoy el clasificador."""
    genero = {c['id'] for c in data['categorias'] if c['tipo'] == 'genero'}
    por_libro: dict[str, set] = {}
    for r in data['libro_categorias']:
        por_libro.setdefault(r['libro_id'], set()).add(r['categoria_id'])
    out = {}
    for i, cs in por_libro.items():
        g = cs & genero
        pub = 'i' if 'infantil' in g else 'j' if ('juvenil' in cs or 'narrativa-juvenil' in g) else 'a'
        out[i] = (frozenset(g - DERIVADOS - {'infantil'}), pub)
    return out


def publicados(data: dict) -> dict:
    return {b['id']: b for b in data['libros'] if b.get('estado') == 'publicado'}


def pendientes(data: dict, veredictos: dict, estado: dict) -> list[str]:
    """Libros publicados sin veredicto vigente y que no se dieron ya por imposibles con esta misma ficha."""
    out = []
    for i, b in publicados(data).items():
        v, h = veredictos.get(i), huella(b)
        if v and v.get('h', h) == h:
            continue
        e = estado.get(i) or {}
        if e.get('h') == h and (e.get('aceptado') or e.get('intentos', 0) >= INTENTOS):
            continue
        out.append(i)
    return sorted(out)


# ---------------------------------------------------------------- prompts y validación

PROMPT_CIEGO = """Eres catalogador editorial experto (criterios BISAC/Thema) de una librería online española. Clasifica CADA libro de la lista de forma independiente. Usa título, autor, editorial y sinopsis; si no conoces el libro o la sinopsis es solo bibliográfica, búscalo en internet (ficha de la editorial, Goodreads, Casa del Libro…). No inventes: si de verdad no puedes saberlo, marca "dudoso": true.

1. «pub» = público real: "i" infantil (hasta ~11 años), "j" juvenil/young adult (12-17), "a" adultos.
2. «gen» = 1 género PRINCIPAL y como máximo 2 secundarios, solo si son CENTRALES en el libro (no tangenciales). Principal primero. Ids permitidos (id: nombre — definición):
{generos}
3. {criterios}

Responde SOLO con un bloque JSON, con TODOS los ids de la lista y ninguno más:
{{"libros": [{{"id": "b01", "pub": "a", "gen": ["misterio-y-thriller"], "dudoso": false}}, ...]}}

Libros (id | título | autores | editorial | edad | sinopsis):
"""

PROMPT_R4 = """Eres catalogador editorial experto (criterios BISAC/Thema) de una librería online española. Para cada libro hay dos clasificaciones posibles, A y B (el orden no indica nada). Busca el libro en internet (editorial, Goodreads, Casa del Libro…) y decide cuál es correcta. Si ninguna lo es, da la tuya en «gen» y «pub». Indica la confianza («alta», «media» o «baja») y la URL que lo respalda.

«pub»: "i" infantil (hasta ~11), "j" juvenil (12-17), "a" adultos. «gen»: principal primero y como máximo 2 secundarios centrales. Ids permitidos:
{generos}
{criterios}

Responde SOLO con un bloque JSON, con TODOS los ids:
{{"libros": [{{"id": "b01", "elige": "A", "pub": "a", "gen": ["fantasia"], "conf": "alta", "fuente": "https://..."}}, ...]}}
(«elige»: "A", "B" o "ninguna"; «gen» y «pub» siempre, los de la opción elegida o los tuyos.)

Libros:
"""


def lista_generos(gen: dict) -> str:
    return '\n'.join(f'- {g}: {n} — {d}' if d else f'- {g}: {n}' for g, (n, d) in gen.items())


def fila(tid: str, b: dict) -> str:
    edad = b.get('edad_recomendada') or b.get('publico_amazon') or '-'
    return f"{tid} | {b['titulo']} | {'; '.join(b.get('autores') or [])} | {b.get('editorial') or '-'} | {edad} | {texto(b)[:420]}"


def orden(ids, semilla: str) -> list[str]:
    """Orden pseudoaleatorio estable por semilla: los parecidos no van juntos y cada fase baraja distinto."""
    return sorted(ids, key=lambda i: hashlib.sha256(f'{semilla}:{i}'.encode()).hexdigest())


def etiqueta_txt(gen, pub) -> str:
    return f"pub={pub}; gen={', '.join(gen)}"


def prompt(fase: str, libros: list[tuple[str, dict]], gen: dict, opciones: dict | None = None) -> str:
    base = PROMPT_R4 if fase == 'r4' else PROMPT_CIEGO
    filas = []
    for tid, b in libros:
        filas.append(fila(tid, b))
        if opciones:
            a, bb = opciones[tid]
            filas.append(f'    A: {etiqueta_txt(*a)}\n    B: {etiqueta_txt(*bb)}')
    return base.format(generos=lista_generos(gen), criterios=CRITERIOS) + '\n'.join(filas) + '\n'


def extraer(respuesta: str):
    """El JSON {"libros": [...]} de la respuesta, aunque GPT escriba texto o citas alrededor."""
    for m in re.finditer(r'\{\s*"libros"', respuesta):
        fin = respuesta.rfind('}')
        while fin > m.start():
            try:
                return json.loads(respuesta[m.start():fin + 1])['libros']
            except (ValueError, KeyError, TypeError):
                fin = respuesta.rfind('}', m.start(), fin)
    return None


def normalizar(o: dict, gen: dict):
    """(géneros, público) válidos o None. Quita «narrativa» junto a un género de ficción y lo adulto de un infantil."""
    pub = o.get('pub')
    g = o.get('gen')
    if pub not in ('i', 'j', 'a') or not isinstance(g, list) or not g:
        return None
    if any(not isinstance(x, str) or x not in gen for x in g):
        return None
    g = list(dict.fromkeys(g))
    if len(g) > 1 and 'narrativa' in g and set(g) & FICCION:
        g.remove('narrativa')
    from reading_taxonomy import verdict_genres  # un solo lado del eje: el mismo criterio que al aplicarlo
    lado = verdict_genres(g, set(gen))
    g = [x for x in g if x in lado]
    if pub == 'i':
        g = [x for x in g if x not in ('romance', 'familia-y-crianza', 'desarrollo-personal')] or ['infantil']
    return tuple(g[:3]), pub


def validar(fase: str, respuesta: str, tids: list[str], gen: dict) -> dict:
    """{tid: resultado} de los válidos; los que faltan, sobran, se repiten o no validan se quedan fuera."""
    arr = extraer(respuesta) or []
    vistos = Counter(o.get('id') for o in arr if isinstance(o, dict))
    out = {}
    for o in arr:
        if not isinstance(o, dict) or o.get('id') not in tids or vistos[o['id']] > 1:
            continue
        n = normalizar(o, gen)
        if not n:
            continue
        r = {'gen': list(n[0]), 'pub': n[1]}
        if fase == 'r4':
            if o.get('conf') not in ('alta', 'media', 'baja'):
                continue
            r.update(conf=o['conf'], fuente=str(o.get('fuente') or '')[:300], elige=str(o.get('elige') or ''))
        else:
            r['dudoso'] = bool(o.get('dudoso'))
        out[o['id']] = r
    return out


# ---------------------------------------------------------------- decisión

def sin_infantil(g) -> frozenset:
    return frozenset(g) - {'infantil'} - DERIVADOS


def decidir(reglas, e: dict):
    """Siguiente paso de un libro: ('acepta', gen, pub, método) | ('r3',) | ('r4',) | ('reglas',)."""
    rg, rp = reglas
    r2, r3, r4 = e.get('r2'), e.get('r3'), e.get('r4')
    if not r2:
        return ('r2',)
    if not r2['dudoso'] and sin_infantil(r2['gen']) == rg and r2['pub'] == rp:
        return ('acepta', r2['gen'], rp, 'r2')
    if not r3:
        return ('r3',)
    if not r3['dudoso'] and sin_infantil(r3['gen']) == rg and r3['pub'] == rp:
        return ('acepta', r3['gen'], rp, 'r3=reglas')
    if not (r2['dudoso'] or r3['dudoso']) and r2['pub'] == r3['pub'] and r2['gen'][0] == r3['gen'][0]:
        comunes = [g for g in r2['gen'][1:] if g in r3['gen'][1:]]
        return ('acepta', [r2['gen'][0], *comunes], r2['pub'], 'r2r3')
    if not r4:
        return ('r4',)
    if r4['conf'] in ('alta', 'media'):
        return ('acepta', r4['gen'], r4['pub'], 'r4')
    return ('reglas',)


def opciones_r4(tid_semilla: str, e: dict):
    a = (e['r2']['gen'], e['r2']['pub'])
    b = (e['r3']['gen'], e['r3']['pub'])
    return (a, b) if int(hashlib.sha256(tid_semilla.encode()).hexdigest(), 16) % 2 else (b, a)


# ---------------------------------------------------------------- ChatGPT

def edge_vivo(puerto: int) -> bool:
    url = f'http://127.0.0.1:{puerto}/json/version'
    for intento in range(2):
        try:
            urllib.request.urlopen(url, timeout=5).read()
            return True
        except OSError:
            if intento:
                return False
            edge = next((p for p in (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                                     r'C:\Program Files\Microsoft\Edge\Application\msedge.exe') if os.path.exists(p)), None)
            if not edge:
                return False
            perfil = Path.home() / f'.edge-gpt-{puerto}'
            subprocess.Popen([edge, f'--remote-debugging-port={puerto}', f'--user-data-dir={perfil}', '--no-first-run',
                              'https://chatgpt.com/'], creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0))
            time.sleep(25)
    return False


def preguntar(texto_prompt: str, puerto: int) -> str:
    """Una consulta en pestaña nueva (conversación nueva) con scripts/gpt-consulta.mjs; '' si falla."""
    with tempfile.TemporaryDirectory() as d:
        q, a = Path(d) / 'q.txt', Path(d) / 'a.txt'
        q.write_text(texto_prompt, encoding='utf-8')
        try:
            r = subprocess.run(['node', str(ROOT / 'scripts/gpt-consulta.mjs'), str(q), str(a)], cwd=ROOT,
                               env={**os.environ, 'GPT_PUERTO': str(puerto)}, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=1900)
        except subprocess.TimeoutExpired:
            return ''
        if r.returncode:
            print('  conductor:', (r.stderr or r.stdout).strip()[-300:], flush=True)
        return a.read_text(encoding='utf-8') if a.exists() else ''


# ---------------------------------------------------------------- bucle

def catalogo_main() -> dict:
    """El catálogo de origin/main (el del árbol puede ir atrasado respecto a la carga de esta noche)."""
    subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT, check=False)
    r = subprocess.run(['git', 'show', 'origin/main:data/reading-catalogue.json'], cwd=ROOT, capture_output=True)
    if r.returncode == 0:
        return json.loads(r.stdout.decode('utf-8'))
    return read_json(ROOT / 'data/reading-catalogue.json')


def veredictos_main() -> dict:
    r = subprocess.run(['git', 'show', 'origin/main:' + VERDICTS], cwd=ROOT, capture_output=True)
    return json.loads(r.stdout.decode('utf-8')) if r.returncode == 0 else read_json(ROOT / VERDICTS, {})


def run(args) -> int:
    data = catalogo_main()
    gen = taxonomia(data)
    v = version_prompt(gen)
    libros = publicados(data)
    reglas = etiquetas_reglas(data)
    estado = read_json(ESTADO, {})
    cola = pendientes(data, {**veredictos_main(), **aceptados(estado)}, estado)
    if args.max_libros:
        cola = cola[:args.max_libros]
    print(f'{len(cola)} libros sin veredicto (prompt v{v})', flush=True)
    if not cola:
        print('FIN: catálogo con veredictos')
        return 0
    if not edge_vivo(args.puerto):
        print(f'Edge {args.puerto} no responde', flush=True)
        return 3
    for i in cola:  # ficha nueva: se empieza de cero con ella
        h = huella(libros[i])
        if (estado.get(i) or {}).get('h') != h:
            estado[i] = {'h': h, 'intentos': 0}
    fallos_seguidos = 0
    cerrados = set()  # desempate fallido: el reintento es en otra ejecución (otro día, quizá otra ficha)
    for vuelta in range(3 * REINTENTOS_FASE + 3):
        trabajo: dict[str, list[str]] = {'r2': [], 'r3': [], 'r4': []}
        for i in cola:
            e = estado[i]
            if e.get('aceptado') or e.get('intentos', 0) >= INTENTOS or i in cerrados:
                continue
            paso = decidir(reglas.get(i, (frozenset(), 'a')), e)
            if paso[0] == 'acepta':
                e['aceptado'] = {'gen': list(paso[1]), 'pub': paso[2], 'h': e['h'], 'm': paso[3], 'v': v}
            elif paso[0] == 'reglas':
                e['intentos'] = e.get('intentos', 0) + 1
                cerrados.add(i)
                for k in ('r2', 'r3', 'r4'):  # el siguiente intento vuelve a empezar a ciegas
                    e.pop(k, None)
            elif e.get('fallos_' + paso[0], 0) < REINTENTOS_FASE:
                trabajo[paso[0]].append(i)
        write_json(ESTADO, estado)
        lotes = []
        for fase, ids in trabajo.items():
            ids = orden(ids, f'{date.today()}:{fase}:{vuelta}')
            lotes += [(fase, ids[k:k + args.lote]) for k in range(0, len(ids), args.lote)]
        if not lotes:
            break
        print(f'vuelta {vuelta + 1}: ' + ', '.join(f'{f} {len(i)}' for f, i in trabajo.items() if i), flush=True)

        def consultar(fase_ids):
            fase, ids = fase_ids
            tids = [f'b{n:02d}' for n in range(1, len(ids) + 1)]
            mapa = dict(zip(tids, ids))
            opciones = {t: opciones_r4(f'{date.today()}:{mapa[t]}', estado[mapa[t]]) for t in tids} if fase == 'r4' else None
            texto_prompt = prompt(fase, [(t, libros[mapa[t]]) for t in tids], gen, opciones)
            res = validar(fase, preguntar(texto_prompt, args.puerto), tids, gen)
            if fase == 'r4':
                for t, r in res.items():  # «elige» se guarda como la fase elegida, no como la letra barajada
                    e = estado[mapa[t]]
                    a_es_r2 = opciones[t][0] == (e['r2']['gen'], e['r2']['pub'])
                    r['elige'] = {'A': 'r2' if a_es_r2 else 'r3', 'B': 'r3' if a_es_r2 else 'r2'}.get(r['elige'], 'propia')
            return fase, mapa, res

        with ThreadPoolExecutor(max_workers=args.pestanas) as pool:
            for fase, mapa, res in pool.map(consultar, lotes):
                for t, i in mapa.items():
                    if t in res:
                        estado[i][fase] = res[t]
                    else:
                        estado[i]['fallos_' + fase] = estado[i].get('fallos_' + fase, 0) + 1
                fallos_seguidos = 0 if res else fallos_seguidos + 1
                print(f'  {fase}: {len(res)}/{len(mapa)} válidos', flush=True)
                write_json(ESTADO, estado)
        if fallos_seguidos >= 4:
            print('4 lotes seguidos sin respuesta válida: paro (Edge, sesión de ChatGPT o cuota)', flush=True)
            break
    for i in cola:  # los fallos de respuesta no cuentan para la ejecución siguiente
        for k in ('fallos_r2', 'fallos_r3', 'fallos_r4'):
            estado[i].pop(k, None)
    write_json(ESTADO, estado)
    metricas(cola, estado, reglas, v)
    return 0


def metricas(cola, estado, reglas, v):
    """Deriva sin humano: cuántos géneros da GPT, qué método decide y cuánto se mueve el público respecto a las reglas."""
    acept = {i: estado[i]['aceptado'] for i in cola if estado[i].get('aceptado')}
    m = {'fecha': date.today().isoformat(), 'v': v, 'cola': len(cola), 'aceptados': len(acept),
         'con_reglas': sum(1 for i in cola if estado[i].get('intentos', 0) >= INTENTOS and not estado[i].get('aceptado')),
         'metodo': dict(Counter(a['m'] for a in acept.values())),
         'n_generos': dict(Counter(str(len(a['gen'])) for a in acept.values())),
         'publico': dict(Counter(f"{reglas.get(i, (0, '?'))[1]}>{a['pub']}" for i, a in acept.items()
                                 if reglas.get(i, (0, '?'))[1] != a['pub']))}
    METRICAS.parent.mkdir(parents=True, exist_ok=True)
    with METRICAS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(m, ensure_ascii=False) + '\n')
    print('métricas:', json.dumps(m, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- publicación (la llama reading-texts.py)

def aceptados(estado: dict) -> dict:
    return {i: e['aceptado'] for i, e in estado.items() if e.get('aceptado')}


def fusionar(tree: Path, estado_path: Path = ESTADO) -> int:
    """Lleva al árbol de main los veredictos aceptados cuya ficha sigue igual; devuelve cuántos cambian.

    No rederiva: quien llama aplica `repair_classification` al catálogo y regenera."""
    nuevos = aceptados(read_json(estado_path, {}))
    if not nuevos:
        return 0
    data = read_json(tree / 'data/reading-catalogue.json')
    libros = publicados(data)
    actuales = read_json(tree / VERDICTS, {})
    def vigente(i):  # un veredicto de main con la ficha de hoy (manual o anterior) no se pisa
        v = actuales.get(i)
        return bool(v) and v.get('h', huella(libros[i])) == huella(libros[i])
    cambios = {i: a for i, a in nuevos.items() if i in libros and a['h'] == huella(libros[i]) and not vigente(i)}
    if cambios:
        escribir_veredictos(tree / VERDICTS, {**actuales, **cambios})
    return len(cambios)


def publicar_cmd(args) -> int:
    """En el árbol de main: fusiona los veredictos aceptados y rederiva el catálogo con ellos (idempotente)."""
    n = fusionar(ROOT, Path(args.estado))
    print(f'{n} veredictos nuevos', flush=True)
    if n:
        from reading_ratings_refresh import write_changed
        from reading_taxonomy import load_verdicts, repair_classification, _published_verdicts
        _published_verdicts.cache_clear()
        path = ROOT / 'data/reading-catalogue.json'
        data = read_json(path)
        repair_classification(data, today=date.today().isoformat())
        assert load_verdicts(), 'el código no lee el fichero de veredictos recién escrito'
        print('Catálogo rederivado' if write_changed(path, data) else 'Catálogo ya derivado', flush=True)
    return 0


def estado_cmd(_args) -> int:
    data = read_json(ROOT / 'data/reading-catalogue.json')
    estado = read_json(ESTADO, {})
    cola = pendientes(data, {**read_json(ROOT / VERDICTS, {}), **aceptados(estado)}, estado)
    fases = Counter(next((k for k in ('r4', 'r3', 'r2') if k in estado.get(i, {})), 'nuevo') for i in cola)
    print(f'pendientes {len(cola)} {dict(fases)}; aceptados sin publicar {len(aceptados(estado))}')
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--puerto', type=int, default=int(os.environ.get('GPT_PUERTO', '9262')))
    r.add_argument('--pestanas', type=int, default=2)
    r.add_argument('--lote', type=int, default=LOTE)
    r.add_argument('--max-libros', type=int, default=0, help='0 = todos')
    sub.add_parser('estado')
    pu = sub.add_parser('publicar', help='(lo llama reading-texts.py publish en el árbol de main)')
    pu.add_argument('--estado', default=str(ESTADO))
    a = p.parse_args(argv)
    if getattr(a, 'puerto', 0) == 9240:
        p.error('9240 es el Edge de los textos')
    return {'run': run, 'estado': estado_cmd, 'publicar': publicar_cmd}[a.cmd](a)


if __name__ == '__main__':
    raise SystemExit(main())
