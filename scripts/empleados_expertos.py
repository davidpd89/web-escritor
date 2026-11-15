"""Equipo de expertos automáticos: elige el rol del día y prepara datos deterministas para el experto LLM.

Subórdenes:
  elegir [--rol R] [--fecha AAAA-MM-DD]   imprime el rol (y lo escribe en GITHUB_OUTPUT si existe)
  muestra --sitemap URL --n N --salida F  escribe N URL del sitemap (portada y novedades primero)
  resumir-siteone --json F --salida F     resume el JSON de SiteOne Crawler en markdown corto
  geo --base URL --muestra F --salida F   comprueba robots.txt, llms.txt y JSON-LD de la muestra

Las herramientas deterministas miden; el experto LLM lee el resumen y propone (issues con la etiqueta `experto`).
Lista del equipo y estado: .ci/empleados-expertos.md.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request
import urllib.robotparser
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / '.github' / 'empleados'
# Lunes=0. El investigador va una vez por semana (condición de Fable, R3-14).
ROTACION = ['investigador', 'seo', 'geo', 'ux', 'rendimiento', 'arquitecto', 'tester']
ROLES = set(ROTACION)
UA = 'Mozilla/5.0 (compatible; equipo-expertos/1.0; +https://davidportodiaz.com/)'
PRIORIDAD = ('/recomendaciones/pagina', '/recomendaciones/libros/', '/recomendaciones/autores/',
             '/recomendaciones/editoriales/')


def elegir(rol=None, fecha=None):
    if rol:
        if rol not in ROLES:
            raise SystemExit(f'rol desconocido: {rol}; válidos: {", ".join(ROTACION)}')
        return rol
    fecha = fecha or date.today()
    return ROTACION[fecha.weekday()]


def descargar(url, limite=5_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 - URL propia
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


def revisar_jsonld(html):
    bloques = re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I)
    tipos, errores = [], 0
    for b in bloques:
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
            titulo = re.search(r'<title>(.*?)</title>', html, re.S)
            canon = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
            out.append(f'- {u}: tipos={sorted(set(tipos)) or "NINGUNO"}'
                       f'{" JSON-LD roto=" + str(errores) if errores else ""}'
                       f'; title={len(titulo.group(1).strip()) if titulo else 0} car.'
                       f'; canonical={"sí" if canon else "NO"}')
        except Exception as e:  # noqa: BLE001
            out.append(f'- {u}: ERROR {type(e).__name__}')
    return '\n'.join(out)


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
        Path(a.salida).write_text('\n'.join(ordenar_muestra(urls_sitemap(xml), a.n)) + '\n', encoding='utf-8')
    elif a.orden == 'resumir-siteone':
        try:
            datos = json.loads(Path(a.json).read_text(encoding='utf-8'))
        except (OSError, ValueError) as ex:
            datos = {'summary': {'items': [{'status': 'CRITICAL', 'aplCode': 'crawler',
                                            'text': f'sin JSON del crawler: {type(ex).__name__}'}]}}
        Path(a.salida).write_text(resumir_siteone(datos), encoding='utf-8')
    elif a.orden == 'geo':
        muestra = [u for u in Path(a.muestra).read_text(encoding='utf-8').split() if u]
        Path(a.salida).write_text(geo(a.base, muestra), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
