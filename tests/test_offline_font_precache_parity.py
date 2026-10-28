from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
offline = (ROOT / 'offline.html').read_text(encoding='utf-8')
sw = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
shell_match = re.search(r'const APP_SHELL\s*=\s*\[([^\]]+)\]', sw, re.S)
assert shell_match, 'service-worker.js: APP_SHELL ausente'
shell = set(re.findall(r'[\"\'](/[^\"\']+)[\"\']', shell_match.group(1)))
font_blocks = re.findall(r'@font-face\s*\{([^}]+)\}', offline, re.S)
assert font_blocks, 'offline.html: no se encontraron las fuentes locales declaradas'
for block in font_blocks:
    urls = re.findall(r'url\(\s*[\"\']?(/[^)\"\']+)', block)
    assert urls, 'offline.html: @font-face sin recurso local'
    for url in urls:
        assert url in shell, f'offline.html: fuente {url} no precargada por service-worker.js'
        path = ROOT / url.lstrip('/')
        assert path.is_file(), f'offline.html: fuente inexistente {url}'
        assert path.stat().st_size > 0, f'offline.html: fuente vacía {url}'
print(f'PASS: {len(font_blocks)} fuentes offline integradas en APP_SHELL')
