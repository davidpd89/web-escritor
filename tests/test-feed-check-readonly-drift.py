#!/usr/bin/env python3
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_check_qa', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    notebook = root / 'cuaderno'
    notebook.mkdir()
    page = notebook / 'article.html'
    page.write_text('<html><head><title>Prueba RSS</title><link rel="canonical" href="https://davidportodiaz.com/cuaderno/qa/"><meta name="datePublished" content="2026-10-20"></head></html>', encoding='utf-8')
    xsl = root / 'rss.xsl'
    shutil.copyfile(ROOT / 'assets/rss.xsl', xsl)
    mod.CUADERNO = str(notebook)
    mod.OUT = str(notebook / 'feed.xml')
    mod.XSL_PATH = str(xsl)
    old_argv = sys.argv
    try:
        sys.argv = ['build-feed.py']
        assert mod.main() == 0
        target = Path(mod.OUT)
        good = target.read_bytes()
        target.write_bytes(good + b'\nBROKEN')
        corrupted = target.read_bytes()
        sys.argv = ['build-feed.py', '--check']
        assert mod.main() != 0, '--check no detecta deriva'
        assert target.read_bytes() == corrupted, '--check escribió en disco'
        sys.argv = ['build-feed.py']
        assert mod.main() == 0
        assert target.read_bytes() == good
    finally:
        sys.argv = old_argv
print('PASS: --check es de solo lectura y la regeneración repara deriva')
