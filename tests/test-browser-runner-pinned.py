"""Los trabajos que instalan o usan navegadores corren en una imagen de Ubuntu fijada, nunca en ubuntu-latest.

2026-11-04: al moverse ubuntu-latest a 26.04 falló la instalación de dependencias de Playwright y se cayeron
decenas de comprobaciones a la vez. Las capturas visuales y las auditorías de accesibilidad también dependen de
las fuentes y librerías del sistema, así que el cambio de imagen se hace a propósito y en una sola PR.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER = re.compile(r'playwright install|install-deps|setup-chrome|browser-actions|puppeteer|pa11y-ci|npx pa11y|lhci (autorun|collect|assert)', re.I)
LHCI = re.compile(r'^\s*(?:- )?run:\s*lhci\b', re.M)
NPM = re.compile(r'npm (?:ci|install)')
JOB = re.compile(r'^  ([\w-]+):[ \t]*$', re.M)


def offenders(text: str, name: str) -> list[str]:
    """Divide la sección jobs: por trabajos de primer nivel (sin PyYAML, que la puerta no instala)."""
    jobs = text.split('\njobs:', 1)[1] if '\njobs:' in text else ''
    marks = list(JOB.finditer(jobs))
    out = []
    for i, mark in enumerate(marks):
        block = jobs[mark.end():marks[i + 1].start() if i + 1 < len(marks) else len(jobs)]
        runner = re.search(r'^    runs-on:\s*(.+)$', block, re.M)
        if runner and 'latest' in runner.group(1) and BROWSER.search(block):
            out.append(f'{name}:{mark.group(1)} ({runner.group(1).strip()})')
        # lhci sale del lockfile (node_modules/.bin): sin npm ci en el mismo trabajo el comando no existe (exit 127).
        if LHCI.search(block) and not NPM.search(block):
            out.append(f'{name}:{mark.group(1)} (lhci sin npm ci)')
    return out


SAMPLE = ('on: push\njobs:\n  a:\n    runs-on: {}\n    steps:\n      - run: {}\n'
          '  b:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo\n')
assert offenders(SAMPLE.format('ubuntu-latest', 'npx playwright install --with-deps'), 'x') == ['x:a (ubuntu-latest)']
assert not offenders(SAMPLE.format('ubuntu-24.04', 'npx playwright install'), 'x')
assert not offenders(SAMPLE.format('ubuntu-latest', 'python tests/x.py'), 'x')
assert offenders(SAMPLE.format('ubuntu-24.04', 'lhci collect'), 'x') == ['x:a (lhci sin npm ci)']

bad, checked = [], 0
for path in sorted((ROOT / '.github' / 'workflows').glob('*.y*ml')):
    checked += 1
    bad += offenders(path.read_text(encoding='utf-8'), path.name)
assert not bad, 'Trabajos con navegador en ubuntu-latest (usa ubuntu-24.04) o con lhci sin npm ci:\n' + '\n'.join(bad)
print(f'PASS todos los trabajos con navegador usan una imagen de Ubuntu fijada ({checked} workflows)')
