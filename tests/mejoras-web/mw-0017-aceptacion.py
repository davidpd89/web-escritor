from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / 'assets/v1-home-editorial-v3.js'
SHELL = ROOT / 'assets/v1-shell.js'
CHECKER = ROOT / 'scripts/check-asset-versions.py'
LOCK = ROOT / 'scripts/asset-version-hashes.json'
INDEX = ROOT / 'index.html'

home = HOME.read_text(encoding='utf-8')
shell = SHELL.read_text(encoding='utf-8')
checker = CHECKER.read_text(encoding='utf-8')
index = INDEX.read_text(encoding='utf-8')
lock = json.loads(LOCK.read_text(encoding='utf-8'))

assert '<main id="contenido" tabindex="-1">' in index, 'Falta el destino del foco'

start = home.index('function createBackToTop()')
end = home.index('function createYaleHero()', start)
block = home[start:end]

assert "button.addEventListener('click', () => {" in block
handler = block.split("button.addEventListener('click', () => {", 1)[1].split('\n    });', 1)[0]

scroll = "window.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' });"
focus = "document.getElementById('contenido')?.focus({ preventScroll: true });"
analytics = "emit('home_back_to_top');"

assert scroll in handler, 'Debe conservarse scrollTo y prefers-reduced-motion'
assert focus in handler, 'El botón debe transferir el foco a main#contenido'
assert analytics in handler, 'Debe conservarse el evento analítico'
assert handler.index(scroll) < handler.index(focus) < handler.index(analytics)
assert "const update = () => button.classList.toggle('is-visible', window.scrollY > 720);" in block
assert "addEventListener('scroll', update, { passive: true });" in block

match = re.search(r'"v1-home-editorial-v3\.js":\s*"(\d+)"', checker)
assert match, 'El módulo no está registrado en TRACKED_ASSETS'
version = int(match.group(1))
assert version > 9, 'La versión debe incrementarse respecto a v9'
assert lock['v1-home-editorial-v3.js']['version'] == str(version)
assert f"const HOME_EDITORIAL_SRC = '/assets/v1-home-editorial-v3.js?v={version}';" in shell

shell_match = re.search(r'"v1-shell\.js":\s*"(\d+)"', checker)
assert shell_match
shell_version = shell_match.group(1)
assert lock['v1-shell.js']['version'] == shell_version
assert f'/assets/v1-shell.js?v={shell_version}' in index

def sha256_normalized(path):
    content = path.read_bytes().replace(b'\r\n', b'\n')
    return hashlib.sha256(content).hexdigest()

for name, path in [('v1-home-editorial-v3.js', HOME), ('v1-shell.js', SHELL)]:
    actual = sha256_normalized(path)
    recorded = lock[name]['sha256']
    assert actual == recorded, f'Hash incorrecto para {name}: {actual} != {recorded}'

print('PASS MW-0017: foco, desplazamiento, analítica, versiones y hashes')
