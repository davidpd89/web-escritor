#!/usr/bin/env python3
"""R5-3: los iconos del shell van por referencia a un sprite común, no repetidos en línea en cada página.

Vigila la clase de fallo, no un icono concreto:
- cualquier <svg> que pinte el shell (cabecera, explorar, pie) usa el sprite; un icono nuevo escrito en línea falla aquí;
- toda referencia del shell existe en el sprite publicado (assets/iconos.svg), sin ids huérfanos;
- el sprite conserva el dibujo y el relleno/trazo; la página, el viewBox, el tamaño, la clase y la accesibilidad;
- icon() rechaza lo que no sabe convertir en vez de publicar un icono roto.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shell', ROOT / 'scripts/build-site-shell.py')
shell = importlib.util.module_from_spec(spec)
sys.modules['shell'] = shell
spec.loader.exec_module(shell)

nav = shell.load_json(shell.NAV_PATH)
registry = shell.ensure_registry(shell.load_json(shell.REGISTRY_PATH))
extras = shell.load_json(shell.EXTRAS_PATH)
blocks = (
    shell.render_header(nav, registry, '/recomendaciones/'),
    shell.render_explore(nav, registry, '/recomendaciones/'),
    shell.render_footer(nav, registry, extras, 'recomendaciones/index.html', '/recomendaciones/'),
)
markup = ''.join(blocks)
svgs = re.findall(r'<svg\b[^>]*>.*?</svg>', markup, re.S)
assert len(svgs) >= 20, f'el shell debería pintar sus iconos ({len(svgs)})'
inline = [s for s in svgs if not re.fullmatch(r'<svg\b[^>]*><use href="/assets/iconos\.svg#i[0-9a-f]{6}"/></svg>', s)]
assert not inline, f'icono en línea en el shell; pásalo por icon(): {inline[0][:120]}'
assert not any(re.search(r'\s(fill|stroke)=', s) for s in svgs), 'relleno y trazo van en el <symbol>'
assert all('viewBox=' in s for s in svgs), 'el viewBox se queda en la página (con él en el symbol el dibujo se movía 1 px)'

sprite = (ROOT / shell.ICON_SPRITE_REL).read_text(encoding='utf-8')
assert sprite == shell.render_icon_sprite(), 'assets/iconos.svg desactualizado: python scripts/build-site-shell.py'
defined = set(re.findall(r'<symbol id="(i[0-9a-f]{6})"', sprite))
used = set(re.findall(r'#(i[0-9a-f]{6})"', markup))
assert used <= defined, f'referencias sin símbolo: {sorted(used - defined)}'
assert 'viewBox' not in sprite, 'el symbol no lleva viewBox: mismas coordenadas que el <svg> de la página'
assert sprite.startswith('<svg xmlns="http://www.w3.org/2000/svg">'), 'un sprite externo necesita su espacio de nombres'

# Ida y vuelta: el sprite más la página reconstruyen exactamente el icono original.
original = shell.FOOTER_SOCIAL[0][2]
ref = shell.icon(original)
ident = re.search(r'#(i[0-9a-f]{6})', ref).group(1)
drawing, inner = shell.ICONS[ident]
outer = re.match(r'<svg([^>]*)>', ref).group(1)
assert sorted(re.findall(r'\S+="[^"]*"', outer + drawing)) == sorted(re.findall(r'\S+="[^"]*"', re.match(r'<svg([^>]*)>', original).group(1)))
assert inner == re.fullmatch(r'<svg[^>]*>(.*)</svg>', original, re.S).group(1)
assert shell.icon(original) == ref, 'id estable'

for bad in ('<svg aria-hidden="true"><path d="M0 0"/></svg>', '<i>no</i>', '<svg viewBox="0 0 1 1"><svg></svg></svg>'):
    try:
        shell.icon(bad)
        raise AssertionError(f'icon() debería rechazar {bad}')
    except ValueError:
        pass

print(f'OK sprite: {len(svgs)} iconos del shell por referencia, {len(defined)} símbolos')
