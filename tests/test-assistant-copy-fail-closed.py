from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts/check-assistant-copy.py'

with TemporaryDirectory() as directory:
    root = Path(directory)
    result = subprocess.run(
        [sys.executable, str(CHECKER), '--check', '--root', str(root)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0, (
        'El checker devuelve éxito sin ningún archivo: ' + result.stdout
    )

    (root / 'assets').mkdir()
    (root / 'asistente').mkdir()
    (root / 'assets/assistant-copy.js').write_text(
        'export const ASSISTANT_COPY={heroTitle:"Prueba"};', encoding='utf-8'
    )
    result = subprocess.run(
        [sys.executable, str(CHECKER), '--check', '--root', str(root)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0, (
        'El checker devuelve éxito con archivos parcialmente ausentes: ' + result.stdout
    )

print('assistant-copy-fail-closed: OK')
