import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['assets/v1-fonts.css', 'assets/v1-accessibility-statement.css']


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)

errors = []
for name in FILES:
    css = strip_comments((ROOT / name).read_text(encoding='utf-8'))
    for match in re.finditer(r'@import\s+(?:url\(\s*)?[\'\"]?(https?:)?//[^\s;\)\'\"]+', css, re.I):
        errors.append(f'{name}: importacion externa {match.group(0)}')
    for match in re.finditer(r'url\(\s*[\'\"]?\s*((?:https?:)?//[^\)\'\"]+)', css, re.I):
        errors.append(f'{name}: recurso externo {match.group(1)}')
assert not errors, '\n'.join(errors)
print(f'PASS: {len(FILES)} hojas de estilo sin recursos de terceros')