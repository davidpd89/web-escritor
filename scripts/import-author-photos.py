#!/usr/bin/env python3
"""Fotos de autor desde las candidatas de `author-photo-candidates.mjs`, con revisión visual antes de publicar.

  --preparar          descarga la primera candidata válida de cada autor a .local/photos y genera hojas de contacto
                      (.local/photos/hoja-NN.png, 20 por hoja, numeradas) para comprobar a ojo que es la persona.
  --aplicar 3,5,7-9   da por buenas esas casillas (de .local/photos/indice.json): 320 px WebP al almacén externo y `foto` en
                      data/reading-authors.json (READING_COVERS_STORE_DIR obligatorio); --subir publica el almacén.
"""
from __future__ import annotations
import argparse, io, json, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_cover_store as cover_store
AUTHORS = ROOT / 'data/reading-authors.json'
CAND = ROOT / '.local/author-photo-candidates.json'
OUT = ROOT / '.local/photos'
SKIP_HOST = re.compile(r'mercadolibre|walmart|imusic|ebay|aliexpress|temu|etsy|amazon|casadellibro\.com/libro|penguinrandomhouse\.com/books|booktopia|bookdepository|abebooks', re.I)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept': 'image/*,*/*;q=0.8'}


def fetch(url: str) -> Image.Image | None:
    try:
        req = urllib.request.Request(url, headers={**UA, 'Referer': url})
        data = urllib.request.urlopen(req, timeout=20).read(8_000_000)
        im = Image.open(io.BytesIO(data)); im.load()
        return im.convert('RGB')
    except Exception:
        return None


def valid(im: Image.Image | None) -> bool:
    return bool(im) and im.width >= 200 and 0.8 <= im.height / im.width <= 2.0


def one_face(im: Image.Image) -> bool:
    """Un solo rostro grande (Haar de OpenCV): descarta portadas, paisajes, grupos y productos."""
    import cv2, numpy as np
    gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = det.detectMultiScale(gray, 1.1, 6, minSize=(max(40, im.width // 9),) * 2)
    return len(faces) == 1


def preparar(cand_file: str = '', vistos: bool = False) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cands = json.loads((ROOT / cand_file if cand_file else CAND).read_text(encoding='utf-8'))
    prev = set()
    if vistos and (OUT / 'indice.json').exists():
        prev = {e['img'] for e in json.loads((OUT / 'indice.json').read_text(encoding='utf-8'))}
        for f in OUT.glob('hoja-*.png'):
            f.unlink()
    names = {a['slug']: a['nombre'] for a in json.loads(AUTHORS.read_text(encoding='utf-8'))['autores']}
    index = []
    have = {a['slug'] for a in json.loads(AUTHORS.read_text(encoding='utf-8'))['autores'] if a.get('foto')}
    for slug, items in cands.items():
        if slug in have:
            continue
        for c in items:
            if SKIP_HOST.search(c['page'] + c['img']) or c['img'] in prev:
                continue
            im = fetch(c['img']) or fetch(c['thumb'])
            if valid(im) and one_face(im):
                im.thumbnail((640, 800)); im.save(OUT / f'{slug}.jpg', quality=88)
                index.append({'slug': slug, 'nombre': names.get(slug, slug), 'page': c['page'], 'img': c['img']})
                break
    (OUT / 'indice.json').write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    per, cols, w, h = 20, 5, 200, 250
    for s in range(0, len(index), per):
        chunk = index[s:s + per]
        sheet = Image.new('RGB', (cols * w, ((len(chunk) + cols - 1) // cols) * (h + 34)), 'white')
        d = ImageDraw.Draw(sheet)
        for k, e in enumerate(chunk):
            im = Image.open(OUT / f"{e['slug']}.jpg"); im.thumbnail((w - 6, h - 6))
            x, y = (k % cols) * w, (k // cols) * (h + 34)
            sheet.paste(im, (x + 3, y + 3))
            d.text((x + 4, y + h + 2), f"{s + k}: {e['nombre'][:30]}", fill='black')
        sheet.save(OUT / f'hoja-{s // per:02d}.png')
    print(len(index), 'autores con candidata descargada;', (len(index) + per - 1) // per, 'hojas en', OUT)


def aplicar(spec: str, subir: bool) -> None:
    if cover_store.store_dir() is None:
        sys.exit(f'Falta {cover_store.STORE_DIR_ENV}')
    index = json.loads((OUT / 'indice.json').read_text(encoding='utf-8'))
    chosen = set()
    for part in filter(None, spec.split(',')):
        a, _, b = part.partition('-'); chosen.update(range(int(a), int(b or a) + 1))
    payload = json.loads(AUTHORS.read_text(encoding='utf-8'))
    by = {a['slug']: a for a in payload['autores']}
    done = 0
    for i in sorted(chosen):
        e = index[i]; im = Image.open(OUT / f"{e['slug']}.jpg").convert('RGB')
        if im.width > 320:
            im = im.resize((320, round(im.height * 320 / im.width)), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, 'WEBP', quality=80, method=6); content = buf.getvalue()
        path = cover_store.fresh_name(f'{cover_store.LOGICAL_PREFIX}autor-{e["slug"]}.webp', content)
        cover_store.put(ROOT, path, content)
        host = urllib.parse.urlparse(e['page']).netloc.removeprefix('www.') or 'web'
        by[e['slug']]['foto'] = {'url': path, 'ancho': im.width, 'alto': im.height, 'autor': host[:120], 'licencia': 'Fuente web', 'fuente_url': e['page'] if e['page'].startswith('https://') else 'https://' + host}
        done += 1
    AUTHORS.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(done, 'fotos aplicadas')
    if subir:
        print('Subidas al almacén:', cover_store.flush('Fotos de autores (búsqueda web)', ROOT))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--preparar', action='store_true'); p.add_argument('--aplicar', default=''); p.add_argument('--cand', default=''); p.add_argument('--vistos', action='store_true'); p.add_argument('--subir', action='store_true')
    a = p.parse_args()
    if a.preparar: preparar(a.cand, a.vistos)
    if a.aplicar: aplicar(a.aplicar, a.subir)
