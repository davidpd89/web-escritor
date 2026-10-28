from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
NAME = 'samuel_entre_mundos_3d'
WEBP = ROOT / 'assets' / (NAME + '.webp')
AVIF = ROOT / 'assets' / (NAME + '.avif')
EXPECTED_WEBP_SHA = '899f076acad818abe866702aeebd8b7ccbd6b5c3e6b448320aaae4237117f0ba'
EXPECTED_AVIF_SHA = 'ac7a9b4a9af43086b5fbd6ddac702a5e7bcc4d204c1b222c724247b1dd992a08'

manifest = json.loads((ROOT / 'data/image-format-ladder.json').read_text(encoding='utf-8'))
entries = [entry for entry in manifest['eligible_sources'] if entry['source'] == 'assets/' + NAME + '.webp']
assert len(entries) == 1, 'Debe existir exactamente una pareja Samuel en el manifiesto'
entry = entries[0]
assert entry['derivative'] == 'assets/' + NAME + '.avif'
assert entry['source_sha256'] == EXPECTED_WEBP_SHA
assert entry['derivative_sha256'] == EXPECTED_AVIF_SHA
assert hashlib.sha256(WEBP.read_bytes()).hexdigest() == EXPECTED_WEBP_SHA
assert hashlib.sha256(AVIF.read_bytes()).hexdigest() == EXPECTED_AVIF_SHA

# Read the actual image headers without generating or modifying files.
webp = WEBP.read_bytes()
avif = AVIF.read_bytes()
assert webp[:4] == b'RIFF' and webp[8:16] == b'WEBPVP8X'
webp_size = (1 + int.from_bytes(webp[24:27], 'little'),
             1 + int.from_bytes(webp[27:30], 'little'))
ispe = avif.find(b'ispe')
assert ispe >= 0, 'El AVIF debe declarar dimensiones ispe'
avif_size = (int.from_bytes(avif[ispe + 8:ispe + 12], 'big'),
             int.from_bytes(avif[ispe + 12:ispe + 16], 'big'))
assert webp_size == avif_size == (1530, 2400), (webp_size, avif_size)

html = (ROOT / 'index.html').read_text(encoding='utf-8')
js = (ROOT / 'assets/v1-home-editorial-v3.js').read_text(encoding='utf-8')
css = (ROOT / 'assets/v1-home.css').read_text(encoding='utf-8')

fallback = re.search(
    r'<picture>\s*<source\s+type="image/avif"\s+srcset="/assets/samuel_entre_mundos_3d\.avif"\s*/>\s*'
    r'(<img\b[^>]*>)\s*</picture>',
    html,
)
assert fallback, 'La alternativa sin JS debe contener picture con source AVIF'
tag = fallback.group(1)
for attr, value in {
    'src': '/assets/samuel_entre_mundos_3d.webp',
    'alt': 'Portada de Samuel entre mundos',
    'width': '1530',
    'height': '2400',
    'loading': 'lazy',
    'decoding': 'async',
}.items():
    assert f'{attr}="{value}"' in tag, (attr, tag)

assert 'function wrapSamuelPicture(image)' in js
assert "source.type = 'image/avif';" in js
assert "source.srcset = '/assets/samuel_entre_mundos_3d.avif';" in js
assert 'picture.append(source, image);' in js
assert "src === '/assets/samuel_entre_mundos_3d.webp'" in js
assert '? wrapSamuelPicture(img)' in js
assert 'media.append(wrapSamuelPicture(image));' in js
assert 'html.v1[data-lrb-home="true"] .media-frame > picture{display:block}' in css
assert 'html.v1 .promo-band > picture{display:block;line-height:0}' in css

print('MW-0031 static acceptance: PASS')
