#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-performance-budgets.py'
spec = importlib.util.spec_from_file_location('performance_budgets', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_aliases_share_binary():
    css_path = ROOT / 'assets/v1-fonts.css'
    css = css_path.read_text(encoding='utf-8')
    declarations = module.CSS_FONT_FACE_RE.findall(css)
    faces = {}
    for declaration in declarations:
        family = re.search(r'font-family\s*:\s*[\'\"]?([^;\'\"]+)', declaration)
        if not family:
            continue
        urls = set()
        for groups in module.CSS_FONT_URL_RE.findall(declaration):
            url = next((part for part in groups if part), '')
            if url.endswith('.woff2'):
                urls.add(url)
        faces.setdefault(family.group(1).strip(), set()).update(urls)
    assert faces.get('Manrope'), 'assets/v1-fonts.css: falta Manrope'
    assert faces.get('Manrope Display'), 'assets/v1-fonts.css: falta Manrope Display'
    assert faces['Manrope'] == faces['Manrope Display'], f'assets/v1-fonts.css: Manrope={faces["Manrope"]}; Display={faces["Manrope Display"]}'
    files, errors = module.collect_graph(ROOT, ['assets/v1-fonts.css'])
    assert not errors, f'assets/v1-fonts.css: {errors}'
    binaries = [p for p in files if p.suffix == '.woff2']
    assert len(binaries) == len(set(binaries)), 'assets/v1-fonts.css: fuentes contabilizadas varias veces'
    metrics = module.metrics_for(files)
    expected = sum(module.served_size(p) for p in binaries)
    assert metrics['font_bytes'] == expected, f'assets/v1-fonts.css: font_bytes={metrics["font_bytes"]}, esperado={expected}'
    assert metrics['request_count'] == len(files), f'assets/v1-fonts.css: requests={metrics["request_count"]}, ficheros={len(files)}'

if __name__ == '__main__':
    test_aliases_share_binary()
