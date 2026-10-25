import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for name in ('empieza-aqui/index.html', 'mapa-del-sitio/index.html', '404.html', 'destino/index.html'):
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('<main><p>Contenido publico</p></main>', encoding='utf-8')
    source = root / 'empieza-aqui/index.html'
    source.write_text('<main><a href="/destino/">Destino valido</a></main>', encoding='utf-8')
    script = root / 'qa/findability-inventory.mjs'
    script.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'qa/findability-inventory.mjs', script)
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=QA', '-c', 'user.email=qa@example.test', 'commit', '-qm', 'baseline'], cwd=root, check=True)
    base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    source.write_text('<main><p>Enlace eliminado</p></main>', encoding='utf-8')
    (root / 'destino/index.html').unlink()
    result = subprocess.run(['node', str(script)], cwd=root, env={**os.environ, 'BASE_SHA': base, 'QA_OUT': 'evidence'}, capture_output=True, text=True)
    assert result.returncode != 0, 'FALSO POSITIVO: se permite borrar un enlace valido junto con su destino. ' + result.stdout
print('PASS: preservation validates destinations against BASE_SHA')
