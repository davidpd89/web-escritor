"""Una caída de apt (DNS o espejo de Ubuntu) no tumba la QA de navegador; y ningún workflow llama a apt sin respaldo.

11/11/2026: «Temporary failure resolving 'azure.archive.ubuntu.com'» durante horas hizo fallar 11 trabajos de
navegador a la vez, y otros agotaban su límite porque apt perdía 5-8 min por intento (el 04/11, decenas por el
cambio de imagen). Todos pasan por scripts/ci/apt-ready.sh: cambia a archive.ubuntu.com si Azure no resuelve y,
sin ningún espejo, Playwright sigue con las librerías de la imagen en segundos.
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'ci' / 'playwright-install-deps.sh'
DIRECT = re.compile(r'npx playwright install(?:-deps| [^\n]*--with-deps)')
AZURE = 'azure.archive.ubuntu.com'

bad = []
for path in sorted((ROOT / '.github' / 'workflows').glob('*.y*ml')):
    text = path.read_text(encoding='utf-8')
    for no, line in enumerate(text.splitlines(), 1):
        if DIRECT.search(line):
            bad.append(f'{path.name}:{no}: {line.strip()} (usa bash scripts/ci/playwright-install-deps.sh)')
    if re.search(r'apt(?:-get)? install', text) and 'scripts/ci/apt-ready.sh' not in text:
        bad.append(f'{path.name}: apt-get install sin bash scripts/ci/apt-ready.sh antes')
assert not bad, 'Llamadas a apt sin respaldo ante caídas del espejo:\n' + '\n'.join(bad)

bash = shutil.which('bash')
if bash:
    def run(hosts: set[str], apt_ok: bool, mode: str, browser: str = 'chromium',
            missing: str = '', busy: str = '') -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bin_dir, log, etc, browsers = tmp / 'bin', tmp / 'calls', tmp / 'apt', tmp / 'browsers'
            bin_dir.mkdir()
            (browsers / f'{browser}-2336' / 'lib').mkdir(parents=True)
            (browsers / f'{browser}-2336' / 'lib' / 'libbundled.so.1').write_bytes(b'')
            installed = tmp / 'installed'

            (etc / 'sources.list.d').mkdir(parents=True)
            (etc / 'apt-mirrors.txt').write_bytes(
                f'http://{AZURE}/ubuntu/\tpriority:1\nhttps://archive.ubuntu.com/ubuntu/\tpriority:2\n'.encode())
            known = ' '.join(sorted(hosts))
            stubs = {
                'getent': f'for h in {known}; do [ "$2" = "$h" ] && exit 0; done; exit 2',
                'sudo': '"$@"',
                'timeout': 'shift; "$@"',
                'npx': f'echo "$*" >> "{log.as_posix()}"\n'
                       f'case "$*" in *install-deps*|*--with-deps*) exit {0 if apt_ok else 100};; esac\nexit 0',
                # ldd informa de la librería ausente hasta que apt-get la instala.
                'ldd': f'[ -n "{missing}" ] && [ ! -e "{installed.as_posix()}" ] && '
                       f'printf "\\t%s => not found\\n" "{missing}"; exit 0',
                'apt-cache': '[ "$2" = libevent-2.1-7t64 ]',
                'apt-get': f'echo "apt-get $*" >> "{log.as_posix()}"; touch "{installed.as_posix()}"',
                # Un apt-get huérfano de install-deps sigue vivo en la primera consulta y termina en la segunda.
                'pgrep': f'[ "$2" = apt-get ] || exit 1; [ -n "{busy}" ] && [ ! -e "{tmp.as_posix()}/idle" ] && '
                         f'{{ echo "pgrep busy" >> "{log.as_posix()}"; touch "{tmp.as_posix()}/idle"; exit 0; }}; exit 1',
                'sleep': 'exit 0',
            }
            for name, body in stubs.items():
                stub = bin_dir / name
                stub.write_bytes(f'#!/usr/bin/env bash\n{body}\n'.encode())
                stub.chmod(0o755)
            env = dict(os.environ, PW_DEPS_PAUSE='0', APT_PROBE_PAUSE='0', APT_ETC=etc.as_posix(),
                       PLAYWRIGHT_BROWSERS_PATH=browsers.as_posix(), PATH=f'{bin_dir.as_posix()}:/usr/bin:/bin')
            done = subprocess.run([bash, SCRIPT.as_posix(), mode, browser], env=env,
                                  capture_output=True, text=True)
            calls = log.read_text() if log.exists() else ''
            return done.returncode, calls, (etc / 'apt-mirrors.txt').read_text()

    every = {AZURE, 'archive.ubuntu.com', 'security.ubuntu.com'}
    # Sin ningún espejo: ni se intenta apt (antes, 5-8 min perdidos por intento) y se sigue.
    code, calls, _ = run(set(), apt_ok=False, mode='deps')
    assert code == 0 and calls == '', (code, calls)
    # Azure caído y el espejo oficial vivo: apt pasa a archive.ubuntu.com y se instala.
    code, calls, mirrors = run(every - {AZURE}, apt_ok=True, mode='deps')
    assert code == 0 and calls.strip() == 'playwright install-deps chromium', (code, calls)
    assert AZURE not in mirrors and 'archive.ubuntu.com' in mirrors, mirrors
    # Con DNS pero apt roto: un solo intento y se sigue con la imagen.
    code, calls, mirrors = run(every, apt_ok=False, mode='deps')
    assert code == 0 and calls.count('install-deps') == 1 and AZURE in mirrors, (code, calls)
    # Modo completo sin apt: el navegador sigue saliendo del CDN de Playwright.
    code, calls, _ = run(set(), apt_ok=False, mode='full')
    assert code == 0 and calls.strip() == 'playwright install chromium', (code, calls)
    code, calls, _ = run(every, apt_ok=True, mode='full')
    assert code == 0 and calls.strip() == 'playwright install --with-deps chromium', (code, calls)
    # 18/11: apt vivo pero install-deps sin terminar; WebKit sin libevent. Solo se instala ese paquete (t64).
    code, calls, _ = run(every, apt_ok=False, mode='deps', browser='webkit', missing='libevent-2.1.so.7')
    assert code == 0 and calls.splitlines()[-1] == (
        'apt-get -o DPkg::Lock::Timeout=300 install -y --no-install-recommends libevent-2.1-7t64'), (code, calls)
    # 23/11: el apt-get de install-deps sigue vivo tras el tope; se espera a que suelte dpkg antes del respaldo.
    code, calls, _ = run(every, apt_ok=False, mode='deps', browser='webkit', missing='libevent-2.1.so.7', busy='1')
    lines = calls.splitlines()
    assert code == 0 and 'pgrep busy' in lines and lines.index('pgrep busy') < len(lines) - 1         and lines[-1].startswith('apt-get -o DPkg::Lock::Timeout='), (code, calls)
    # Sin red no se intenta apt aunque falten librerías.
    code, calls, _ = run(set(), apt_ok=False, mode='deps', browser='webkit', missing='libevent-2.1.so.7')
    assert code == 0 and 'apt-get' not in calls, (code, calls)
    # Con todo presente no se toca apt tras el fallo.
    code, calls, _ = run(every, apt_ok=False, mode='full', browser='webkit')
    assert code == 0 and 'apt-get' not in calls, (code, calls)
print('PASS apt: cambia de espejo o se salta en segundos, y todos los workflows pasan por el respaldo')
