"""Equipo de expertos automáticos: elige el rol del día y prepara datos deterministas para el experto LLM.

Subórdenes:
  elegir [--rol R] [--fecha AAAA-MM-DD]   imprime el rol (y lo escribe en GITHUB_OUTPUT si existe)
  muestra --sitemap URL --n N --salida F  escribe N URL del sitemap (portada y novedades primero)
  resumir-siteone --json F --salida F     resume el JSON de SiteOne Crawler en markdown corto
  geo --base URL --muestra F --salida F   comprueba robots.txt, llms.txt y JSON-LD de la muestra
  seguridad --base URL --salida F         cabeceras de seguridad, bots de IA y ficheros sensibles versionados

Las herramientas deterministas miden; el experto LLM lee el resumen y propone (issues con la etiqueta `experto`).
Lista del equipo y estado: .ci/empleados-expertos.md.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import arbol_publicado  # noqa: E402  (árbol publicado: versionado + generado en disco)
PROMPTS = ROOT / '.github' / 'empleados'
# Todo lo que lee o escribe el script vive aquí: ningún argumento puede sacar una ruta fuera.
DATOS = Path(os.environ.get('EMPLEADOS_DATOS') or ROOT / '.empleados').resolve()
# Solo se descarga del sitio propio, por HTTPS: ni una URL del sitemap ni un argumento abren otra petición.
HOSTS = {'davidportodiaz.com', 'www.davidportodiaz.com'}
# Lunes=0. El investigador va una vez por semana (condición de Fable, R3-14).
ROTACION = ['investigador', 'seo', 'geo', 'ux', 'rendimiento', 'arquitecto', 'tester']
# Turno extra: el de seguridad va los domingos a otra hora (segundo cron del workflow), sin quitar el día a nadie.
ROLES = set(ROTACION) | {'seguridad'}
UA = 'Mozilla/5.0 (compatible; equipo-expertos/1.0; +https://davidportodiaz.com/)'
PRIORIDAD = ('/recomendaciones/pagina', '/recomendaciones/libros/', '/recomendaciones/autores/',
             '/recomendaciones/editoriales/')


def elegir(rol=None, fecha=None):
    if rol:
        if rol not in ROLES:
            raise SystemExit(f'rol desconocido: {rol}; válidos: {", ".join(sorted(ROLES))}')
        return rol
    fecha = fecha or date.today()
    return ROTACION[fecha.weekday()]


def url_segura(url):
    """La URL si es HTTPS del sitio propio; ValueError si no."""
    partes = urllib.parse.urlsplit(url)
    if partes.scheme != 'https' or partes.hostname not in HOSTS or partes.username or partes.port:
        raise ValueError(f'URL fuera del sitio: {url[:120]}')
    return partes.geturl()


def ruta_segura(nombre):
    """Ruta dentro de DATOS; ValueError si un argumento intenta salir (../, absoluta a otro sitio)."""
    ruta = Path(nombre).resolve()
    if not ruta.is_relative_to(DATOS):
        raise ValueError(f'ruta fuera de {DATOS}: {nombre}')
    return ruta


class _SinRedireccionAjena(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, url_segura(newurl))


_ABRIR = urllib.request.build_opener(_SinRedireccionAjena).open


def descargar(url, limite=5_000_000):
    req = urllib.request.Request(url_segura(url), headers={'User-Agent': UA})
    with _ABRIR(req, timeout=30) as r:  # noqa: S310 - url_segura: solo HTTPS del sitio propio
        return r.status, r.read(limite).decode('utf-8', 'replace')


def urls_sitemap(xml):
    return [html.unescape(u) for u in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', xml)]  # &amp; -> &


def ordenar_muestra(urls, n):
    """Portada primero, luego las rutas prioritarias (novedades, lecturas…) y después repartidas por el resto."""
    vistas, salida = set(), []

    def meter(u):
        if u not in vistas and len(salida) < n:
            vistas.add(u)
            salida.append(u)

    for u in urls:  # portada y portales de primer nivel (/recomendaciones/, /libros/…)
        if re.fullmatch(r'https?://[^/]+(/[^/]+)?/?', u):
            meter(u)
        if len(salida) >= max(2, n // 5):
            break
    for pref in PRIORIDAD:
        for u in [u for u in urls if pref in u][:max(1, n // 10)]:
            meter(u)
    resto = [u for u in urls if u not in vistas]
    if resto and len(salida) < n:
        paso = max(1, len(resto) // (n - len(salida)))
        for u in resto[::paso]:
            meter(u)
    return salida


def resumir_siteone(datos, maximo=12000):
    lineas = ['# Resumen SiteOne Crawler', '']
    resumen = (datos.get('summary') or {}).get('items') or []
    if resumen:
        orden = {'CRITICAL': 0, 'WARNING': 1, 'NOTICE': 2, 'INFO': 3, 'OK': 4}
        resumen = sorted(resumen, key=lambda i: orden.get(str(i.get('status', '')).upper(), 5))
        lineas.append('## Hallazgos (por gravedad)')
        for item in resumen:
            estado = str(item.get('status', '?')).upper()
            if estado == 'OK':
                continue
            lineas.append(f"- [{estado}] {item.get('aplCode', '')}: {item.get('text', '')}")
    else:
        lineas.append('(sin sección summary; claves: ' + ', '.join(sorted(datos)) + ')')
    texto = '\n'.join(lineas)
    return texto[:maximo]


class _Pagina(HTMLParser):
    """Bloques JSON-LD, <title> y canonical con el parser de la biblioteca estándar (sin regex con backtracking)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.jsonld, self.titulo, self.canonical = [], None, False
        self._en = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if tag == 'script' and 'ld+json' in a.get('type', '').lower():
            self._en = 'jsonld'
            self.jsonld.append('')
        elif tag == 'title' and self.titulo is None:
            self._en = 'title'
            self.titulo = ''
        elif tag == 'link' and 'canonical' in a.get('rel', '').lower().split() and a.get('href'):
            self.canonical = True

    def handle_endtag(self, tag):
        if tag in ('script', 'title'):
            self._en = None

    def handle_data(self, data):
        if self._en == 'jsonld':
            self.jsonld[-1] += data
        elif self._en == 'title':
            self.titulo += data


def leer_pagina(html):
    p = _Pagina()
    p.feed(html)
    p.close()
    return p


def revisar_jsonld(html):
    tipos, errores = [], 0
    for b in leer_pagina(html).jsonld:
        try:
            d = json.loads(b)
        except ValueError:
            errores += 1
            continue
        for nodo in (d if isinstance(d, list) else d.get('@graph', [d]) if isinstance(d, dict) else []):
            if isinstance(nodo, dict):
                t = nodo.get('@type')
                tipos.extend(t if isinstance(t, list) else [t])
    return [t for t in tipos if t], errores


BOTS_IA = ('OAI-SearchBot', 'GPTBot', 'PerplexityBot', 'ClaudeBot', 'Google-Extended', 'Bingbot')


def robots_bots(robots, base):
    """Estado de cada bot en la portada según RFC 9309: sin grupo propio, hereda el de `User-agent: *`."""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots.splitlines())
    return [(bot, 'permitido' if rp.can_fetch(bot, base.rstrip('/') + '/') else 'BLOQUEADO') for bot in BOTS_IA]


def geo(base, muestra):
    base = base.rstrip('/')
    out = ['# Comprobaciones GEO deterministas', '']
    for ruta in ('/robots.txt', '/llms.txt', '/sitemap.xml'):
        try:
            st, cuerpo = descargar(base + ruta, 200_000)
            out.append(f'- {ruta}: {st}, {len(cuerpo)} car.')
            if ruta == '/robots.txt':
                out += [f'  - {bot}: {estado}' for bot, estado in robots_bots(cuerpo, base)]
        except Exception as e:  # noqa: BLE001 - informe, no fallo
            out.append(f'- {ruta}: ERROR {type(e).__name__}')
    out += ['', '## JSON-LD por página']
    for u in muestra:
        try:
            _, html = descargar(u)
            tipos, errores = revisar_jsonld(html)
            pagina = leer_pagina(html)
            out.append(f'- {u}: tipos={sorted(set(tipos)) or "NINGUNO"}'
                       f'{" JSON-LD roto=" + str(errores) if errores else ""}'
                       f'; title={len((pagina.titulo or "").strip())} car.'
                       f'; canonical={"sí" if pagina.canonical else "NO"}')
        except Exception as e:  # noqa: BLE001
            out.append(f'- {u}: ERROR {type(e).__name__}')
    return '\n'.join(out)


CABECERAS = ('strict-transport-security', 'content-security-policy', 'x-content-type-options',
             'referrer-policy', 'permissions-policy', 'x-frame-options')
# Por nombre de fichero, nunca por contenido: el catálogo tiene títulos con «secreto».
SENSIBLES = re.compile(r'(^|/)(\.env(\.(?!example$|sample$)[^/]*)?|id_[rd]sa[^/]*|[^/]*\.(pem|key|p12|pfx|keystore|jks|sqlite3?)'
                       r'|credentials[^/]*\.json|service[-_]account[^/]*\.json|\.npmrc|\.pypirc|\.netrc)$', re.I)


def ficheros_sensibles(rutas):
    return [r for r in rutas if SENSIBLES.search(r)]


def cabeceras(base):
    req = urllib.request.Request(url_segura(base.rstrip('/') + '/'), headers={'User-Agent': UA}, method='HEAD')
    with _ABRIR(req, timeout=30) as r:  # noqa: S310 - url_segura: solo HTTPS del sitio propio
        return {k.lower(): v for k, v in r.headers.items()}


def seguridad(base):
    base = base.rstrip('/')
    out = ['# Comprobaciones de seguridad deterministas', '', '## Cabeceras de la portada']
    try:
        h = cabeceras(base)
        out += [f'- {c}: {h[c][:160] if c in h else "FALTA"}' for c in CABECERAS]
    except Exception as e:  # noqa: BLE001 - informe, no fallo
        out.append(f'- ERROR {type(e).__name__}')
    out += ['', '## Bots de IA en robots.txt (un bloqueo quita visibilidad en buscadores de IA)']
    try:
        _, robots = descargar(base + '/robots.txt', 200_000)
        out += [f'- {bot}: {estado}' for bot, estado in robots_bots(robots, base)]
    except Exception as e:  # noqa: BLE001
        out.append(f'- ERROR {type(e).__name__}')
    rutas = arbol_publicado.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=False).stdout.splitlines()
    sens = ficheros_sensibles(rutas)
    out += ['', '## Ficheros con nombre sensible versionados (solo la ruta, nunca el contenido)']
    out += [f'- {r}' for r in sens[:50]] or ['- ninguno']
    out += ['', 'Línea base de avisos de workflows: `.github/seguridad-base.json` (auditoría semanal zizmor/pip-audit/gitleaks).']
    return '\n'.join(out)


# --- Experto LLM gratuito: GitHub Models con el GITHUB_TOKEN del run (permiso `models: read`, sin coste) ---
# Claude por la cuenta queda para emergencias (autorreparación de la carga y las publicaciones), no para rondas diarias.
MODELOS_URL = 'https://models.github.ai/inference/chat/completions'
MODELOS = ('openai/gpt-4.1', 'openai/gpt-4.1-mini')   # el segundo si el primero agota su cuota diaria
MAX_DATOS = 14000        # el nivel gratuito admite unos 8000 tokens de entrada por petición
MAX_ISSUES = 3
REPO_TEMAS = ('seo', 'web-performance', 'accessibility', 'structured-data', 'github-actions-security',
              'link-checker', 'static-site', 'llms-txt')


def _gh(*args):
    r = subprocess.run(['gh', *args], capture_output=True, text=True, check=False, timeout=120)
    return r.stdout if r.returncode == 0 else ''


def datos_rol(rol, hoy=None):
    """Datos deterministas de los roles que no miran la web: el LLM nunca trabaja sin evidencia."""
    hoy = hoy or date.today()
    if rol == 'arquitecto':
        fallos = _gh('issue', 'list', '--label', 'fallo', '--state', 'all', '--limit', '30',
                     '--json', 'number,title,state', '-q', '.[]|"#\\(.number) [\\(.state)] \\(.title)"')
        cis = sorted((ROOT / '.ci').glob('*.md'), key=lambda f: f.stat().st_mtime)[-12:]
        return ('# Issues `fallo` recientes\n' + (fallos or '(ninguna)') + '\n\n# Informes .ci más recientes\n'
                + '\n'.join(f'## {f.name}\n{f.read_text(encoding="utf-8", errors="replace")[:600]}' for f in cis))
    if rol == 'tester':
        tests = ' '.join(f.read_text(encoding='utf-8', errors='replace') for f in (ROOT / 'tests').glob('*.py'))
        sin = [f.name for f in sorted((ROOT / 'scripts').glob('*.py'))
               if f.stem not in tests and f.stem.replace('-', '_') not in tests]
        return '# Scripts sin ningún test que los nombre\n' + '\n'.join(f'- {s}' for s in sin)
    if rol == 'investigador':
        desde = date.fromordinal(hoy.toordinal() - 30).isoformat()
        filas = []
        for tema in REPO_TEMAS:
            filas += _gh('api', '-X', 'GET', 'search/repositories', '-f', f'q=topic:{tema} pushed:>={desde} stars:>=300',
                         '-f', 'sort=stars', '-f', 'per_page=8', '-q',
                         '.items[]|"- \\(.full_name) ★\\(.stargazers_count) [\\(.license.spdx_id // "sin licencia")] '
                         '\\(.description // "" | .[0:140]) \\(.html_url)"').splitlines()
        return f'# Repositorios públicos activos (último push ≥ {desde}, ≥300 estrellas)\n' + '\n'.join(sorted(set(filas)))
    return ''


def prompt_experto(rol, datos):
    comun = (PROMPTS / 'comun.md').read_text(encoding='utf-8')
    propio = (PROMPTS / f'{rol}.md').read_text(encoding='utf-8')
    equipo = (ROOT / '.ci' / 'empleados-expertos.md')
    equipo = equipo.read_text(encoding='utf-8')[:3000] if equipo.exists() else ''
    return [{'role': 'system', 'content': comun + '\n\n' + propio},
            {'role': 'user', 'content': f'# Equipo actual (resumen)\n{equipo}\n\n# Datos de hoy\n{datos[:MAX_DATOS]}'}]


def _pedir_modelo(mensajes, modelo, token):
    cuerpo = json.dumps({'model': modelo, 'messages': mensajes, 'temperature': 0.2, 'max_tokens': 3000,
                         'response_format': {'type': 'json_object'}}).encode()
    req = urllib.request.Request(MODELOS_URL, data=cuerpo, method='POST', headers={
        'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 - URL fija de GitHub Models
        crudo = r.read()
    try:
        return json.loads(crudo)['choices'][0]['message']['content']
    except ValueError as e:  # 21/11: ambos modelos devolvían un cuerpo que no era JSON; sin verlo no se podía diagnosticar
        raise ValueError(f'cuerpo no JSON ({e}): {crudo[:200]!r}') from e


def propuestas(texto):
    """Lista de issues válidas del JSON del modelo; lo que no tenga las cuatro partes se descarta."""
    try:
        datos = json.loads(texto)
    except ValueError:
        return []
    salida = []
    for p in (datos.get('issues') if isinstance(datos, dict) else None) or []:
        if not isinstance(p, dict):
            continue
        campos = [str(p.get(k) or '').strip() for k in ('titulo', 'evidencia', 'impacto', 'arreglo', 'comprobar')]
        if all(campos):
            salida.append(dict(zip(('titulo', 'evidencia', 'impacto', 'arreglo', 'comprobar'), campos)))
    return salida[:MAX_ISSUES]


def _sin_menciones(texto):
    return re.sub(r'@(?=\w)', '@​', texto)   # el texto del modelo no avisa a nadie en GitHub


def cuerpo_issue(p, rol, modelo):
    return _sin_menciones(
        f"**Evidencia**\n\n{p['evidencia'][:3000]}\n\n**Impacto**\n\n{p['impacto'][:1500]}\n\n"
        f"**Arreglo propuesto**\n\n{p['arreglo'][:3000]}\n\n**Cómo comprobarlo**\n\n{p['comprobar'][:1500]}\n\n"
        f"_Experto automático `{rol}` ({modelo}, GitHub Models gratuito). Equipo: `.ci/empleados-expertos.md`._")


def publicar(props, rol, modelo, dry=False):
    """Crea las issues que no tengan ya una abierta con el mismo título. Devuelve los títulos creados."""
    abiertas = set(_gh('issue', 'list', '--state', 'open', '--label', 'experto', '--limit', '200',
                       '--json', 'title', '-q', '.[].title').splitlines())
    creadas = []
    for p in props:
        titulo = _sin_menciones(f"{rol}: {p['titulo']}")[:200]
        if titulo in abiertas:
            continue
        if not dry:
            f = ruta_segura(DATOS / f'issue-{len(creadas)}.md')
            f.write_text(cuerpo_issue(p, rol, modelo), encoding='utf-8')
            _gh('issue', 'create', '--label', 'experto', '--label', f'rol:{rol}', '--title', titulo, '--body-file', str(f))
        creadas.append(titulo)
    return creadas


def experto(rol, dry=False):
    datos = '\n\n'.join(f.read_text(encoding='utf-8', errors='replace')
                        for f in sorted(DATOS.glob('*.md')) if not f.name.startswith('issue-'))
    datos += '\n\n' + datos_rol(rol)
    if not datos.strip():
        print('sin datos: no se consulta al modelo')
        return []
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN', '')
    for modelo in MODELOS:
        try:
            texto = _pedir_modelo(prompt_experto(rol, datos), modelo, token)
        except urllib.error.HTTPError as e:
            print(f'{modelo}: HTTP {e.code}')   # 429 = cuota diaria agotada: siguiente modelo
            continue
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError) as e:
            print(f'{modelo}: respuesta no válida ({type(e).__name__}: {str(e)[:300]})')   # sin JSON de chat: siguiente modelo
            continue
        ruta_segura(DATOS / 'respuesta-modelo.json').write_text(texto, encoding='utf-8')
        creadas = publicar(propuestas(texto), rol, modelo, dry)
        print(f'{modelo}: {len(creadas)} issues', *creadas, sep='\n- ')
        return creadas
    raise SystemExit('ningún modelo respondió')


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='orden', required=True)
    e = sub.add_parser('elegir')
    e.add_argument('--rol', default='')
    e.add_argument('--fecha', default='')
    m = sub.add_parser('muestra')
    m.add_argument('--sitemap', required=True)
    m.add_argument('--n', type=int, default=40)
    m.add_argument('--salida', required=True)
    r = sub.add_parser('resumir-siteone')
    r.add_argument('--json', required=True)
    r.add_argument('--salida', required=True)
    g = sub.add_parser('geo')
    g.add_argument('--base', required=True)
    g.add_argument('--muestra', required=True)
    g.add_argument('--salida', required=True)
    s = sub.add_parser('seguridad')
    s.add_argument('--base', required=True)
    s.add_argument('--salida', required=True)
    x = sub.add_parser('experto')
    x.add_argument('--rol', required=True)
    x.add_argument('--dry', action='store_true')
    a = p.parse_args(argv)

    if a.orden == 'elegir':
        rol = elegir(a.rol or None, date.fromisoformat(a.fecha) if a.fecha else None)
        if not (PROMPTS / f'{rol}.md').exists():
            raise SystemExit(f'falta el prompt {rol}.md')
        print(rol)
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
                f.write(f'rol={rol}\n')
    elif a.orden == 'muestra':
        _, xml = descargar(a.sitemap)
        ruta_segura(a.salida).write_text('\n'.join(ordenar_muestra(urls_sitemap(xml), a.n)) + '\n', encoding='utf-8')
    elif a.orden == 'resumir-siteone':
        try:
            datos = json.loads(ruta_segura(a.json).read_text(encoding='utf-8'))
        except (OSError, ValueError) as ex:
            datos = {'summary': {'items': [{'status': 'CRITICAL', 'aplCode': 'crawler',
                                            'text': f'sin JSON del crawler: {type(ex).__name__}'}]}}
        ruta_segura(a.salida).write_text(resumir_siteone(datos), encoding='utf-8')
    elif a.orden == 'geo':
        muestra = [u for u in ruta_segura(a.muestra).read_text(encoding='utf-8').split() if u]
        ruta_segura(a.salida).write_text(geo(url_segura(a.base), muestra), encoding='utf-8')
    elif a.orden == 'seguridad':
        ruta_segura(a.salida).write_text(seguridad(url_segura(a.base)), encoding='utf-8')
    elif a.orden == 'experto':
        DATOS.mkdir(parents=True, exist_ok=True)
        experto(elegir(a.rol), a.dry)
    return 0


if __name__ == '__main__':
    sys.exit(main())
