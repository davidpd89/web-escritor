#!/usr/bin/env python3
"""MW-0010: contrato estático de carga diferida de imágenes editoriales."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'assets/v1-home-editorial-v3.js').read_text(encoding='utf-8')
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')


def section(name):
    marker = f'  function {name}() {{'
    assert SOURCE.count(marker) == 1, f'Función ausente o duplicada: {name}'
    return SOURCE.split(marker, 1)[1].split('\n  function ', 1)[0]


for function, variable in (
    ('createEvents', 'leadImage'),
    ('createYaleSamuelFeature', 'image'),
    ('createYaleWorksGrid', 'img'),
):
    body = section(function)
    loading = f"{variable}.loading = 'lazy';"
    src = f'{variable}.src ='
    assert body.count(loading) == 1, f'{function}: loading lazy obligatorio y único'
    assert body.count(src) == 1, f'{function}: asignación src única'
    assert body.index(loading) < body.index(src), (
        f'{function}: loading debe asignarse antes de src'
    )
    assert f"{variable}.loading = 'eager';" not in body, (
        f'{function}: imagen secundaria no debe ser eager'
    )

# Comprobar las dimensiones intrínsecas originales.
events = section('createEvents')
assert 'leadImage.width = 1086;' in events
assert 'leadImage.height = 1448;' in events
assert "leadImage.src = '/assets/eventos/david-porto-diaz-lectores-feria-libro-madrid-2026-samuel.webp';" in events

works = section('createYaleWorksGrid')
assert 'img.width = srcWidth;' in works
assert 'img.height = srcHeight;' in works
assert '/assets/manecillas-del-recuerdo-3d-transparent.webp' in works
assert '/assets/samuel_entre_mundos_3d.webp' in works
assert '/assets/david-porto-memoria-sinfondo.webp' in works

samuel = section('createYaleSamuelFeature')
assert 'image.width = 1530;' in samuel
assert 'image.height = 2400;' in samuel
assert "image.src = '/assets/samuel_entre_mundos_3d.webp';" in samuel

# La imagen LCP debe conservar carga inmediata y prioridad alta.
hero = section('createYaleHero')
assert "image.loading = 'eager';" in hero
assert "image.fetchPriority = 'high';" in hero
assert "image.src = '/assets/manecillas-del-recuerdo-3d-transparent.webp';" in hero
assert 'image.width = 700;' in hero
assert 'image.height = 982;' in hero

# La precarga condicional de index.html permanece disponible.
assert 'document.write(' in HTML
assert '<link rel="preload" as="image"' in HTML
assert 'fetchpriority="high"' in HTML
assert '/assets/manecillas-del-recuerdo-3d-transparent.webp' in HTML

print('PASS MW-0010: lazy antes de src, dimensiones y LCP preservados')
