from pathlib import Path
import base64
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
html = (ROOT / 'index.html').read_text(encoding='utf-8')
media_src = '/assets/video/hero-tinta-david-porto.mp4?v=2'

# Contrato del marcado: no debe quedar un src que el navegador pueda
# descubrir antes de ejecutar la comprobación de sesión y movimiento.
video = re.search(
    r'<video\b[^>]*\bdata-hero-video\b[^>]*>([\s\S]*?)</video>\s*<script>([\s\S]*?)</script>',
    html,
    re.I,
)
assert video, 'El vídeo y su inicializador síncrono deben ser contiguos'

source = re.search(r'<source\b([^>]+)>', video.group(1), re.I)
assert source, 'No se encontró el source MP4'
assert f'data-src="{media_src}"' in source.group(1)
assert not re.search(r'(?<![\w-])src\s*=', source.group(1), re.I), 'source conserva src inmediato'
assert 'type="video/mp4"' in source.group(1)

initializer = video.group(2)
assert "sessionStorage.getItem('dp-intro-seen')" in initializer
assert "matchMedia('(prefers-reduced-motion: reduce)').matches" in initializer
assert 'if (seen ||' in initializer
assert 'source.src = source.dataset.src;' in initializer
assert 'video.load();' in initializer
assert initializer.index('source.src = source.dataset.src;') < initializer.index('video.load();')

# El constructor scripts/build-site-shell.py calcula hashes SHA-256 sobre
# el contenido exacto de cada bloque inline ejecutable, sin trim().
# La CSP versionada debe coincidir con esos hashes y con su orden.
csp = re.search(
    r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"',
    html,
    re.I,
)
assert csp, 'Falta la Content-Security-Policy'
script_src = re.search(r'(?:^|;)\s*script-src\s+([^;]+)', csp.group(1))
assert script_src, 'La CSP no declara script-src'

inline_scripts = re.findall(
    r'<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>([\s\S]*?)</script>',
    html,
    re.I,
)
assert initializer in inline_scripts, 'El inicializador no figura entre los scripts ejecutables'

hashes = []
for script in inline_scripts:
    digest = hashlib.sha256(script.encode('utf-8')).digest()
    token = "'sha256-" + base64.b64encode(digest).decode('ascii') + "'"
    if token not in hashes:
        hashes.append(token)

expected = "'self' " + ' '.join(hashes) + ' '
assert script_src.group(1).startswith(expected), (
    'La CSP no coincide con los hashes generados por build-site-shell.py'
)

print('PASS MW-0009: source diferido, orden de carga y CSP coherente')
