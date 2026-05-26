"""Structural audit for remaining pages"""
import re

files_to_check = [
    'ferias.html',
    'premios.html',
    'empieza-aqui/index.html',
    'las-manecillas-del-recuerdo/index.html',
    'fragmento/index.html',
    'autor.html',
]

for fname in files_to_check:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            html = f.read()
        has_canonical = 'rel="canonical"' in html
        has_main = '<main' in html
        has_schema = 'application/ld+json' in html
        sections = len(re.findall(r'<section', html))
        print(f'{fname}: canonical={has_canonical}, main={has_main}, schema={has_schema}, sections={sections}')

        # Long paragraphs > 500 chars visible
        paras = re.findall(r'<p[^>]*>([^<]{500,})</p>', html)
        for p in paras[:2]:
            print(f'  LONG PARA ({len(p)}c): {p[:120]}')

    except Exception as e:
        print(f'{fname}: ERROR {e}')
