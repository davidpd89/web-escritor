from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from PIL import Image
import importlib.util
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('responsive', ROOT / 'scripts/check-responsive-images.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.candidates = []
    def handle_starttag(self, tag, attrs):
        if tag not in ('img', 'source'):
            return
        values = dict(attrs)
        for url, descriptor in module.parse_srcset(values.get('srcset', '')):
            if re.fullmatch(r'[1-9][0-9]*w', descriptor):
                self.candidates.append((url, int(descriptor[:-1])))

pages = [ROOT / 'libros/index.html']
failures = []
checked = 0
for page in pages:
    parser = Parser()
    parser.feed(page.read_text(encoding='utf-8'))
    for url, declared in parser.candidates:
        target = module.resolve_local(url, page, ROOT)
        if target is None:
            continue
        if not target.is_file():
            failures.append(f'{page.relative_to(ROOT)}: {url}: fichero ausente')
            continue
        with Image.open(target) as image:
            actual = image.width
        checked += 1
        if actual != declared:
            failures.append(f'{page.relative_to(ROOT)}: {url}: descriptor {declared}w, anchura real {actual}px')
assert not failures, '\n'.join(failures)
print(f'PASS responsive srcset real width: {checked} candidatos comprobados')