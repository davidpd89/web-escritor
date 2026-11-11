"""Una caída de apt (DNS o espejo de Ubuntu) no tumba la QA de navegador; y ningún workflow llama a apt sin respaldo.

11/11/2026: «Temporary failure resolving 'azure.archive.ubuntu.com'» hizo fallar 11 trabajos de navegador de una
PR a la vez (antes, el 04/11, decenas por el cambio de imagen). Todos los workflows pasan por
scripts/ci/playwright-install-deps.sh, que reintenta y, sin red para apt, sigue con las librerías de la imagen.
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

bad = []
for path in sorted((ROOT / '.github' / 'workflows').glob('*.y*ml')):
    for no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if DIRECT.search(line):
            bad.append(f'{path.name}:{no}: {line.strip()}')
assert not bad, ('Llamadas directas a apt de Playwright (usa bash scripts/ci/playwright-install-deps.sh):\n'
                 + '\n'.join(bad))

bash = shutil.which('bash')
if bash:
    def run(dns_ok: bool, apt_ok: bool, mode: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir, log = Path(tmp) / 'bin', Path(tmp) / 'calls'
            bin_dir.mkdir()
            stubs = {
                'getent': f'exit {0 if dns_ok else 2}',
                'timeout': 'shift; "$@"',
                'npx': f'echo "$*" >> "{log.as_posix()}"\n'
                       f'case "$*" in *install-deps*|*--with-deps*) exit {0 if apt_ok else 100};; esac\nexit 0',
            }
            for name, body in stubs.items():
                stub = bin_dir / name
                stub.write_bytes(f'#!/usr/bin/env bash\n{body}\n'.encode())
                stub.chmod(0o755)
            env = dict(os.environ, PW_DEPS_PAUSE='0', PATH=f'{bin_dir.as_posix()}:/usr/bin:/bin')
            done = subprocess.run([bash, SCRIPT.as_posix(), mode, 'chromium'], env=env,
                                  capture_output=True, text=True)
            return done.returncode, log.read_text() if log.exists() else ''

    code, calls = run(dns_ok=False, apt_ok=False, mode='deps')
    assert code == 0 and calls == '', (code, calls)  # sin DNS ni se intenta apt: 0 minutos perdidos
    code, calls = run(dns_ok=True, apt_ok=False, mode='deps')
    assert code == 0 and calls.count('install-deps') == 2, (code, calls)
    code, calls = run(dns_ok=False, apt_ok=False, mode='full')
    assert code == 0 and calls.strip() == 'playwright install chromium', (code, calls)
    code, calls = run(dns_ok=True, apt_ok=True, mode='full')
    assert code == 0 and calls.strip() == 'playwright install --with-deps chromium', (code, calls)
print('PASS Playwright: apt con reintento y respaldo, y todos los workflows pasan por el script')
