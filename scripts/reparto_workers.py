"""Reparto del sitio en Workers Static Assets de Cloudflare (salida al tope de 1 GB de GitHub Pages, 27/11).

Pages admite 1 GB y la carga frena a 850 MB (scripts/presupuesto_sitio.py): con ~55 KB por libro caben ~15.000.
Workers Static Assets sirve ficheros sin límite de peticiones ni de tamaño total, pero cada Worker admite 20.000
ficheros (plan Free). El sitio se reparte entre varios Workers solo-assets (sin script: servir assets no cuenta como
invocación, comprobado con GraphQL el 27/11) bajo el mismo host:

- el «núcleo» tiene el dominio propio (Custom Domain) y recibe todo lo que no reclama una ruta;
- cada «fragmento» recibe por ruta de zona `host/<prefijo>*` las URL que empiezan por sus prefijos
  (p. ej. `recomendaciones/libros/a`). Una ruta más específica gana al dominio propio (piloto 27/11).

El plan (config/workers-reparto.json) está versionado: el despliegue no replanifica, así las rutas no bailan cada
noche. Avisa al pasar de `umbral_ficheros` en un Worker y falla al pasar de `maximo_ficheros`; entonces se ejecuta
`planificar --escribir` en un PR. Un fichero va a todo Worker que atiende alguna de sus URL (`d/index.html` también
se sirve como `d/` y `d`; `x.html` como `x`), así ningún listado queda en un Worker que no recibe su URL.

    python scripts/reparto_workers.py planificar --dist .preview-dist [--escribir]
    python scripts/reparto_workers.py repartir --dist .preview-dist --out $RUNNER_TEMP/workers
    python scripts/reparto_workers.py desplegar --repartido $RUNNER_TEMP/workers   # CLOUDFLARE_API_TOKEN/_ACCOUNT_ID
"""
import argparse
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config' / 'workers-reparto.json'
API = 'https://api.cloudflare.com/client/v4'
WRANGLER = 'wrangler@4.169.0'
MAX_BYTES_FICHERO = 25 * 1024 * 1024  # límite de Workers Static Assets por fichero
NO_SUBIR = {'_headers', '_redirects', '_worker.js', '.assetsignore'}  # wrangler los interpreta, no los sirve


def leer_plan(path=PLAN):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def ficheros(dist):
    dist = Path(dist)
    return sorted(p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file())


def urls_de(rel):
    """Rutas URL (sin la barra inicial) que sirve el fichero con html_handling auto-trailing-slash."""
    urls = [rel]
    if rel == 'index.html':
        return urls + ['']
    if rel.endswith('/index.html'):
        d = rel[:-len('index.html')]
        urls += [d, d[:-1]]
    elif rel.endswith('.html'):
        urls.append(rel[:-len('.html')])
    return urls


def indice_prefijos(plan):
    """[(prefijo, worker)] del más largo al más corto: la ruta más específica gana."""
    pares = [(p, f['worker']) for f in plan.get('fragmentos', []) for p in f['prefijos']]
    return sorted(pares, key=lambda kv: -len(kv[0]))


def worker_de_url(url, indice, nucleo):
    for prefijo, worker in indice:
        if url.startswith(prefijo):
            return worker
    return nucleo


def asignar(rels, plan):
    """{worker: [rel]} — un fichero puede ir a varios Workers si sus URL caen en varios."""
    indice, nucleo = indice_prefijos(plan), plan['nucleo']
    salida = {nucleo: []}
    for f in plan.get('fragmentos', []):
        salida[f['worker']] = []
    for rel in rels:
        if rel in NO_SUBIR:
            continue
        for w in sorted({worker_de_url(u, indice, nucleo) for u in urls_de(rel)}):
            salida[w].append(rel)
    return salida


def comprobar(plan, asignacion, dist=None):
    errores, avisos = [], []
    vistos = {}
    for f in plan.get('fragmentos', []):
        for p in f['prefijos']:
            if not p or not p.isascii() or '*' in p or p.startswith('/'):
                errores.append(f'Prefijo no válido en {f["worker"]}: {p!r}')
            if p in vistos:
                errores.append(f'Prefijo {p!r} repetido en {vistos[p]} y {f["worker"]}')
            vistos[p] = f['worker']
    for w, rels in asignacion.items():
        n = len(rels) + (1 if w != plan['nucleo'] else 0)  # 404.html propio en cada fragmento
        if n > plan['maximo_ficheros']:
            errores.append(f'{w}: {n} ficheros (> {plan["maximo_ficheros"]}); replanificar con `planificar --escribir`')
        elif n > plan['umbral_ficheros']:
            avisos.append(f'{w}: {n} ficheros (> {plan["umbral_ficheros"]}); conviene replanificar')
        if w != plan['nucleo'] and not rels:
            avisos.append(f'{w}: sin ficheros')
        for rel in rels:
            if w != plan['nucleo'] and not rel.isascii():
                errores.append(f'{w}: {rel!r} no es ASCII; las rutas comparan la URL codificada')
            if dist and (Path(dist) / rel).stat().st_size > MAX_BYTES_FICHERO:
                errores.append(f'{rel}: pasa de 25 MiB (límite de Workers Static Assets)')
    return errores, avisos


# ---------------------------------------------------------------- planificar

def _hijos(rels, carpeta):
    """{hijo directo (fichero o carpeta): nº de ficheros} bajo `carpeta` (con barra final)."""
    cuenta = {}
    for rel in rels:
        if rel.startswith(carpeta):
            hijo = rel[len(carpeta):].split('/', 1)[0]
            cuenta[hijo] = cuenta.get(hijo, 0) + 1
    return cuenta


def _unidades(cuenta, objetivo, prefijo=''):
    """Parte los nombres por prefijo hasta que cada unidad cabe en `objetivo`. [(prefijo, nº)] en orden.

    Nunca devuelve el prefijo vacío: la ruta `carpeta/*` se llevaría `carpeta/` y dejaría `carpeta` (sin barra,
    que redirige) en el núcleo sin su fichero."""
    nombres = [k for k in cuenta if k.startswith(prefijo)]
    total = sum(cuenta[k] for k in nombres)
    if not total:
        return []
    if prefijo and (total <= objetivo or prefijo in cuenta):  # un nombre exacto no se separa de sus extensiones
        return [(prefijo, total)]
    salida = []
    for c in sorted({k[len(prefijo)] for k in nombres if len(k) > len(prefijo)}):
        salida += _unidades(cuenta, objetivo, prefijo + c)
    return salida


def nombre_fragmento(plan, prefijos):
    """Nombre por contenido: replanificar crea Workers nuevos y los viejos siguen sirviendo hasta que su ruta se
    mueve (PUT); después se borran. Así un cambio de plan no deja URL sin fichero entre despliegues."""
    huella = hashlib.sha1(chr(10).join(prefijos).encode()).hexdigest()[:8]
    return f'{plan["prefijo_worker"]}-{huella}'


def planificar(rels, plan):
    """Fragmentos nuevos: mientras el núcleo pase de `objetivo_ficheros`, divide la carpeta con más hijos
    directos (fichas de libro, fragmentos de pagefind...) en lotes consecutivos de prefijos."""
    objetivo = plan['objetivo_ficheros']
    nuevo = dict(plan, fragmentos=[])
    divididas = set()
    while True:
        restantes = asignar(rels, nuevo)[nuevo['nucleo']]
        if len(restantes) <= objetivo:
            return nuevo
        hijos_por_carpeta = {}
        for rel in restantes:
            partes = rel.split('/')
            for i in range(1, len(partes)):
                c = '/'.join(partes[:i]) + '/'
                if c not in divididas:
                    hijos_por_carpeta.setdefault(c, set()).add(partes[i])
        if not hijos_por_carpeta:
            raise SystemExit(f'No hay carpeta que dividir y el núcleo tiene {len(restantes)} ficheros')
        carpeta = max(hijos_por_carpeta, key=lambda c: (len(hijos_por_carpeta[c]), len(c)))
        divididas.add(carpeta)
        lote, cuenta = [], 0
        for pref, n in _unidades(_hijos(restantes, carpeta), objetivo) + [(None, 0)]:
            if pref is None or (lote and cuenta + n > objetivo):
                if lote:
                    prefijos = [carpeta + p for p in lote]
                    nuevo['fragmentos'].append({'worker': nombre_fragmento(plan, prefijos), 'prefijos': prefijos})
                lote, cuenta = [], 0
            if pref is not None:
                lote.append(pref)
                cuenta += n


# ---------------------------------------------------------------- repartir

def wrangler_config(plan, worker):
    cfg = {'name': worker, 'compatibility_date': plan['compatibility_date'], 'workers_dev': False,
           'preview_urls': False,
           'assets': {'directory': './dist', 'html_handling': 'auto-trailing-slash',
                      'not_found_handling': '404-page'}}
    if worker == plan['nucleo']:
        cfg['routes'] = [{'pattern': plan['host'], 'custom_domain': True}]
    return cfg


def _enlazar(origen, destino):
    """Enlace duro (mismo disco: sin duplicar 500 MB en el runner); copia si no se puede."""
    try:
        os.link(origen, destino)
    except OSError:
        shutil.copyfile(origen, destino)


def repartir(dist, out, plan):
    dist, out = Path(dist), Path(out)
    asignacion = asignar(ficheros(dist), plan)
    errores, avisos = comprobar(plan, asignacion, dist)
    if errores:
        return asignacion, errores, avisos
    if out.exists():
        shutil.rmtree(out)
    for w, rels in asignacion.items():
        destino = out / w / 'dist'
        for rel in rels:
            (destino / rel).parent.mkdir(parents=True, exist_ok=True)
            _enlazar(dist / rel, destino / rel)
        destino.mkdir(parents=True, exist_ok=True)  # un prefijo sin ficheros también lleva su 404
        if w != plan['nucleo'] and (dist / '404.html').exists():
            shutil.copyfile(dist / '404.html', destino / '404.html')
        cabeceras = (dist / '_headers').read_text(encoding='utf-8') if (dist / '_headers').exists() else ''
        if plan.get('noindex'):
            cabeceras += '\n/*\n  X-Robots-Tag: noindex\n'
        if cabeceras.strip():
            destino.mkdir(parents=True, exist_ok=True)
            (destino / '_headers').write_text(cabeceras.lstrip('\n'), encoding='utf-8')
        (out / w / 'wrangler.jsonc').write_text(json.dumps(wrangler_config(plan, w), indent=2), encoding='utf-8')
    rutas = {f'{plan["host"]}/{p}*': f['worker'] for f in plan.get('fragmentos', []) for p in f['prefijos']}
    resumen = {'host': plan['host'], 'zona': plan['zona'], 'nucleo': plan['nucleo'],
               'prefijo_worker': plan['prefijo_worker'],
               'workers': {w: len(r) for w, r in asignacion.items()}, 'rutas': rutas,
               'muestras': {w: next((r for r in rels if r.endswith('/index.html')), rels[0] if rels else None)
                            for w, rels in asignacion.items()}}
    (out / 'reparto.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    return asignacion, errores, avisos


# ---------------------------------------------------------------- desplegar

def _api(metodo, ruta, token, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo,
                                 headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)['result']


def sincronizar_rutas(resumen, token, api=_api):
    """Deja en la zona exactamente las rutas del plan para su host. Cambiar de Worker es un PUT (sin hueco) y las
    rutas sobrantes se borran al final: si `x/a*` pasa a `x/ab*` y `x/ac*`, las nuevas ya existen al borrar la vieja."""
    zona = api('GET', f'/zones?name={resumen["zona"]}', token)[0]['id']
    actuales = api('GET', f'/zones/{zona}/workers/routes', token)
    deseadas = dict(resumen['rutas'])
    hecho, sobrantes = [], []
    for r in actuales:
        if not r['pattern'].startswith(resumen['host'] + '/'):
            continue  # rutas de otros hosts (staging de otros proyectos): no se tocan
        if r['pattern'] in deseadas:
            script = deseadas.pop(r['pattern'])
            if r.get('script') != script:
                api('PUT', f'/zones/{zona}/workers/routes/{r["id"]}', token, {'pattern': r['pattern'], 'script': script})
                hecho.append(f'mover {r["pattern"]} -> {script}')
        else:
            sobrantes.append(r)
    for patron, script in deseadas.items():
        api('POST', f'/zones/{zona}/workers/routes', token, {'pattern': patron, 'script': script})
        hecho.append(f'crear {patron} -> {script}')
    for r in sobrantes:
        api('DELETE', f'/zones/{zona}/workers/routes/{r["id"]}', token)
        hecho.append(f'borrar {r["pattern"]}')
    return hecho


def borrar_huerfanos(resumen, token, cuenta, api=_api):
    """Fragmentos de planes anteriores (mismo prefijo de nombre, fuera del plan y ya sin rutas)."""
    vivos = set(resumen['workers'])
    zona = api('GET', f'/zones?name={resumen["zona"]}', token)[0]['id']
    con_ruta = {r.get('script') for r in api('GET', f'/zones/{zona}/workers/routes', token)}
    borrados = []
    for script in api('GET', f'/accounts/{cuenta}/workers/scripts', token):
        nombre = script['id']
        if nombre.startswith(resumen['prefijo_worker'] + '-') and nombre not in vivos and nombre not in con_ruta:
            api('DELETE', f'/accounts/{cuenta}/workers/scripts/{nombre}', token)
            borrados.append(nombre)
    return borrados


NOMBRE_WORKER = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}$')
NOMBRE_HOST = re.compile(r'^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')


def validar_resumen(resumen):
    """reparto.json llega del disco: nombres y host se validan antes de usarlos en comandos o URL."""
    for w in resumen['workers']:
        if not NOMBRE_WORKER.match(w):
            raise ValueError(f'Nombre de Worker no válido: {w!r}')
    for clave in ('host', 'zona'):
        if not NOMBRE_HOST.match(resumen[clave]):
            raise ValueError(f'{clave} no válido: {resumen[clave]!r}')
    return resumen


def desplegar(repartido, token):
    repartido = Path(repartido)
    resumen = validar_resumen(json.loads((repartido / 'reparto.json').read_text(encoding='utf-8')))
    # Fragmentos antes que el núcleo y rutas al final: una ruta nunca apunta a un Worker sin sus ficheros.
    orden = [w for w in resumen['workers'] if w != resumen['nucleo']] + [resumen['nucleo']]
    for w in orden:
        print(f'::group::wrangler deploy {w} ({resumen["workers"][w]} ficheros)')
        subprocess.run(['npx', '--yes', WRANGLER, 'deploy', '--config', str(repartido / w / 'wrangler.jsonc')],
                       check=True, shell=os.name == 'nt')
        print('::endgroup::')
    for linea in sincronizar_rutas(resumen, token):
        print(linea)
    for nombre in borrar_huerfanos(resumen, token, os.environ['CLOUDFLARE_ACCOUNT_ID']):
        print(f'borrar Worker huérfano {nombre}')
    return resumen


def humo(resumen, abrir=urllib.request.urlopen):
    """Cada Worker sirve su muestra por el host público."""
    validar_resumen(resumen)
    fallos = []
    for w, rel in resumen['muestras'].items():
        if not rel:
            continue
        url = f'https://{resumen["host"]}/' + (rel[:-len('index.html')] if rel.endswith('index.html') else rel)
        try:
            with abrir(urllib.request.Request(url, headers={'User-Agent': 'reparto-workers-humo'}), timeout=30) as r:
                if r.status != 200:
                    fallos.append(f'{w}: {url} -> {r.status}')
        except (urllib.error.URLError, OSError) as e:
            fallos.append(f'{w}: {url} -> {e}')
    return fallos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='orden', required=True)
    p = sub.add_parser('planificar'); p.add_argument('--dist', required=True); p.add_argument('--escribir', action='store_true')
    r = sub.add_parser('repartir'); r.add_argument('--dist', required=True); r.add_argument('--out', required=True)
    d = sub.add_parser('desplegar'); d.add_argument('--repartido', required=True)
    for s in (p, r, d):
        s.add_argument('--plan', default=str(PLAN))
    a = ap.parse_args(argv)
    plan = leer_plan(a.plan)

    if a.orden == 'planificar':
        nuevo = planificar(ficheros(a.dist), plan)
        cuentas = {w: len(rs) for w, rs in asignar(ficheros(a.dist), nuevo).items()}
        print(json.dumps({'fragmentos': nuevo['fragmentos'], 'ficheros': cuentas}, indent=2, ensure_ascii=False))
        if a.escribir:
            Path(a.plan).write_text(json.dumps(nuevo, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return 0

    if a.orden == 'repartir':
        asignacion, errores, avisos = repartir(a.dist, a.out, plan)
        for w, rels in asignacion.items():
            print(f'{w}: {len(rels)} ficheros')
        for x in avisos:
            print(f'::warning::{x}')
        for x in errores:
            print(f'::error::{x}')
        return 1 if errores and plan.get('bloqueante') else 0

    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    if not token or not os.environ.get('CLOUDFLARE_ACCOUNT_ID'):
        print('Sin CLOUDFLARE_API_TOKEN/CLOUDFLARE_ACCOUNT_ID: no se despliega a Workers.')
        return 0
    try:
        resumen = desplegar(a.repartido, token)
        fallos = humo(resumen)
    except (subprocess.CalledProcessError, urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as e:
        fallos = [f'despliegue a Workers: {e}']
    for x in fallos:
        print(f'::error::{x}')
    # Mientras Pages sirva producción (bloqueante=false), un fallo de Workers avisa sin tumbar el despliegue.
    return 1 if fallos and plan.get('bloqueante') else 0


if __name__ == '__main__':
    sys.exit(main())
