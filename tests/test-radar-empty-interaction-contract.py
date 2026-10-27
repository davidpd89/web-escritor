from __future__ import annotations
import importlib.util
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('radar_empty',ROOT/'scripts'/'build-radar-opportunities.py')
r=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=r
spec.loader.exec_module(r)
html=r.render_page_body([],date(2026,10,24),[])
assert 'No hay oportunidades verificadas activas ahora mismo.' in html
assert '<article class="radar-card' not in html
assert '0 convocatorias verificadas' in html

class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active=[]
    def handle_starttag(self,tag,attrs):
        if tag not in {'input','select','button'}:
            return
        attributes=dict(attrs)
        if any(name.startswith('data-radar-') for name in attributes) and any(name in attributes for name in ('data-radar-search','data-radar-type','data-radar-genre','data-radar-kind','data-radar-soon','data-radar-expired','data-radar-clear')):
            if 'disabled' not in attributes:
                self.active.append((tag,attributes.get('id','')))

parser=Controls()
parser.feed(html)
assert not parser.active,f'Controles sin funcionalidad sobre dataset vacío: {parser.active}'
print('PASS empty radar interaction contract')