#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
budgets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budgets)

def test_italic_metrics():
    css = (ROOT / 'assets/v1-fonts.css').read_text(encoding='utf-8')
    faces = budgets.CSS_FONT_FACE_RE.findall(css)
    for family in ('Newsreader', 'Instrument Serif'):
        for name, require_binary in ((family, True), (family + ' Fallback', False)):
            matches = [body for body in faces if re.search(r'font-family\s*:\s*[\'\"]?' + re.escape(name) + r'[\'\"]?\s*;', body) and re.search(r'font-style\s*:\s*italic\s*;', body)]
            assert matches, f'assets/v1-fonts.css: falta cursiva de {name}'
            if require_binary:
                urls = [part for body in matches for groups in budgets.CSS_FONT_URL_RE.findall(body) for part in groups if part and part.endswith('.woff2')]
                assert urls, f'assets/v1-fonts.css: {name} italic sin WOFF2'
                for url in urls:
                    path = (ROOT / 'assets' / url).resolve()
                    assert path.is_relative_to(ROOT) and path.is_file(), f'assets/v1-fonts.css: {name} italic: falta {url}'
            else:
                for metric in ('size-adjust', 'ascent-override', 'descent-override', 'line-gap-override'):
                    assert all(re.search(re.escape(metric) + r'\s*:\s*[0-9.]+%', body) for body in matches), f'assets/v1-fonts.css: {name} italic sin {metric}'
                assert all('local(' in body for body in matches), f'assets/v1-fonts.css: {name} italic sin fuente local'

if __name__ == '__main__':
    test_italic_metrics()
