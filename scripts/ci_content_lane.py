#!/usr/bin/env python3
"""Vía rápida de contenido: decide si un cambio es solo contenido generado y qué páginas muestrear.

Un cambio es «contenido» si TODOS sus ficheros pasan `allowed_path` de scripts/publish-reading-refresh.py, la
misma política que deja publicar al bot (fichas, autores, editoriales, portadas, índices, pagefind). Entonces las
plantillas, el CSS y el JS no cambian: basta con auditar los índices y una muestra de las páginas tocadas, las más
pesadas primero (peor caso de desborde y accesibilidad). La auditoría completa sigue en main y cada noche.

Cualquier otro fichero, o no poder calcular el diff, da `lane=full` (fail-closed).

  python scripts/ci_content_lane.py            # en Actions: escribe lane= y routes= en $GITHUB_OUTPUT
  python scripts/ci_content_lane.py --globs    # los globs de paths-ignore equivalentes a la política

Entorno: EVENT_NAME, BASE_SHA, HEAD_SHA, HEAD_REF (github.head_ref || github.ref_name).
"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('reading_publication_policy', ROOT / 'scripts/publish-reading-refresh.py')
_policy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_policy)
allowed_path = _policy.allowed_path

# Índices que pintan el catálogo entero: se auditan siempre que cambia contenido.
HUBS = ('/recomendaciones/', '/recomendaciones/autores/', '/recomendaciones/editoriales/')
MAX_SAMPLE = 12

# Globs de GitHub equivalentes a la política (para paths-ignore de los workflows que no miden el catálogo).
# tests/test-ci-content-lane.py comprueba que cubren cada ruta permitida y que los workflows usan esta lista.
CONTENT_GLOBS = (
    'assets/page-order.generated.js',
    'assets/reading-market.json',
    'assets/reading-covers/isbn-*.webp',
    'assets/reading-audio/*.mp3',
    'assets/pinterest/feeds/*.xml',
    'data/reading-catalogue.json',
    'data/reading-authors.json',
    'data/reading-publishers.json',
    'data/reading-intake-state.json',
    'data/reading-pinterest-state.json',
    'data/reading-texts/*.json',
    'data/content-registry.json',
    'recomendaciones/index.html',
    'recomendaciones/autores/index.html',
    'recomendaciones/editoriales/index.html',
    'recomendaciones/libros/*/index.html',
    'recomendaciones/autores/*/index.html',
    'recomendaciones/editoriales/*/index.html',
    'recomendaciones/proximos-lanzamientos.ics',
    'recomendaciones/llms.txt',
    'editoriales/*/index.html',
    'editoriales-sitemap.xml',
    'mapa-del-sitio/index.html',
    'sitemap.xml',
    'pagefind/**',
)

BOT_REF = re.compile(r'automation/reading-catalogue-[A-Za-z0-9-]+')


def git(*args: str) -> str:
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def is_content(files: list[str]) -> bool:
    return bool(files) and all(allowed_path(f.replace('\\', '/')) for f in files)


def page_route(f: str) -> str | None:
    if not f.endswith('/index.html'):
        return None
    return '/' + f[: -len('index.html')]


def sample_routes(files: list[str], size=lambda f: (ROOT / f).stat().st_size) -> list[str]:
    """Índices + páginas cambiadas que siguen existiendo, de más a menos peso, hasta MAX_SAMPLE."""
    pages = []
    for f in files:
        route = page_route(f)
        if route and route not in HUBS:
            try:
                pages.append((size(f), route))
            except OSError:
                continue  # borrada: no hay nada que auditar
    pages.sort(key=lambda item: (-item[0], item[1]))
    return [*HUBS, *[route for _, route in pages]][:MAX_SAMPLE]


def diff_range(event: str, base: str, head: str, ref: str) -> tuple[str, str] | None:
    if event == 'pull_request' and base:
        return base, head or 'HEAD'
    if event == 'workflow_dispatch' and BOT_REF.fullmatch(ref or ''):
        return git('merge-base', 'origin/main', 'HEAD').strip(), 'HEAD'
    return None


def decide(event: str, base: str, head: str, ref: str) -> tuple[str, list[str], str]:
    try:
        span = diff_range(event, base, head, ref)
        if span is None:
            return 'full', [], f'evento {event or "desconocido"}: auditoría completa'
        files = [f for f in git('diff', '--name-only', *span).splitlines() if f.strip()]
    except subprocess.CalledProcessError as exc:
        return 'full', [], f'no se pudo calcular el diff ({exc.returncode}): auditoría completa'
    if not is_content(files):
        others = [f for f in files if not allowed_path(f)]
        return 'full', [], 'hay cambios fuera del contenido generado: ' + ', '.join(others[:5]) + (' …' if len(others) > 5 else '')
    routes = sample_routes(files)
    return 'content', routes, f'{len(files)} fichero(s) de contenido generado; muestra de {len(routes)} página(s)'


def main(argv: list[str]) -> int:
    if '--globs' in argv:
        print('\n'.join(CONTENT_GLOBS))
        return 0
    lane, routes, reason = decide(os.environ.get('EVENT_NAME', ''), os.environ.get('BASE_SHA', ''),
                                  os.environ.get('HEAD_SHA', ''), os.environ.get('HEAD_REF', ''))
    print(f'lane={lane} | {reason}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
            fh.write(f'lane={lane}\nroutes={",".join(routes)}\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as fh:
            fh.write(f'### Vía de CI: {lane}\n{reason}\n' + ''.join(f'- `{r}`\n' for r in routes))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
