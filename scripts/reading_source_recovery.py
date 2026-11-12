"""Recuperación semántica de altas conservadas cuando main avanzó en los mismos JSON.

Solo añade libros nuevos respecto a la base común. Nunca rebobina libros, precios ni registros
ya publicados en main, ni recupera libros retirados o ya conservados en cuarentena.
"""
import io
import json
import subprocess
from pathlib import Path


def git(root, *args, data=None):
    return subprocess.check_output(['git', *args], cwd=root, input=data)


def document(root, ref, path, default):
    result = subprocess.run(['git', 'show', ref + ':' + path], cwd=root, capture_output=True)
    return json.loads(result.stdout) if result.returncode == 0 else default


def recover(root, source, base, latest):
    root = Path(root)
    path = 'data/reading-catalogue.json'
    current = document(root, latest, path, None)
    previous = document(root, source, path, None)
    original = document(root, base, path, None)
    if not all(isinstance(d, dict) and isinstance(d.get('libros'), list) for d in (current, previous, original)):
        raise ValueError('No se puede recuperar un catálogo sin sus tres versiones fuente')
    held = document(root, latest, 'data/reading-quarantine.json', {'libros': []})
    known = {b['id'] for b in current['libros']} | {b['id'] for b in original['libros']}
    known |= {h['libro']['id'] for h in held.get('libros', [])}
    additions = [b for b in previous['libros'] if b['id'] not in known]
    ids = {b['id'] for b in additions}
    changed = {}
    current['libros'].extend(additions)
    relations = [r for r in previous.get('libro_categorias', []) if r['libro_id'] in ids]
    if relations:
        existing = {c['id'] for c in current.get('categorias', [])}
        required = {r['categoria_id'] for r in relations}
        current.setdefault('categorias', []).extend(c for c in previous.get('categorias', []) if c['id'] in required and c['id'] not in existing)
        if not required <= {c['id'] for c in current['categorias']}:
            raise ValueError('La recuperación carece de categorías fuente')
        current.setdefault('libro_categorias', []).extend(relations)
    if additions:
        changed[path] = current
    # El importador exige procedencia publicada para cada alta ISBN; se traslada el registro original.
    state_path = 'data/reading-intake-state.json'
    state = document(root, latest, state_path, {'schema_version': 1, 'items': {}})
    old_state = document(root, source, state_path, {'items': {}})
    for book in additions:
        if not book['id'].startswith('isbn-'):
            continue
        key = 'isbn13:' + book.get('isbn13', '')
        evidence = old_state.get('items', {}).get(key, {})
        if evidence.get('estado_ingesta') != 'publicado' or evidence.get('libro_id') != book['id']:
            raise ValueError('La recuperación no tiene procedencia publicada: ' + book['id'])
        state.setdefault('items', {})[key] = evidence
    base_state = document(root, base, state_path, {'items': {}})
    # También conservamos candidatos nuevos pendientes; no resucitamos los retirados por main.
    pending_added = False
    for key, item in old_state.get('items', {}).items():
        if item.get('estado_ingesta') == 'publicado':
            continue  # altas ya trasladadas arriba; no reactivar libros retirados/cuarentenados
        if key not in state.get('items', {}) and key not in base_state.get('items', {}):
            state.setdefault('items', {})[key] = item
            pending_added = True
    if 'pending' in old_state:
        for item in old_state['pending']:
            if item not in state.get('pending', []) and item not in base_state.get('pending', []):
                state.setdefault('pending', []).append(item)
                pending_added = True
    if pending_added or any(b['id'].startswith('isbn-') for b in additions):
        changed[state_path] = state
    for file, key, field, needed in (
        ('data/reading-authors.json', 'autores', 'nombre', {a for b in additions for a in b.get('autores', [])}),
        ('data/reading-publishers.json', 'editoriales', 'slug', {b.get('editorial_catalogo_slug') for b in additions}),
    ):
        now = document(root, latest, file, {'schema_version': 1, key: []})
        old = document(root, source, file, {key: []})
        existing = {x['slug'] for x in now[key]}
        extra = [x for x in old[key] if x.get(field) in needed and x['slug'] not in existing]
        if extra:
            now[key].extend(extra)
            changed[file] = now
    market_file = 'assets/reading-market.json'
    market = document(root, latest, market_file, {'schema_version': 1, 'offers': [], 'ratings': []})
    old_market = document(root, source, market_file, {})
    for key in ('offers', 'ratings', 'sales_ranks'):
        extra = [row for row in old_market.get(key, []) if row.get('libro_id') in ids]
        if extra:
            market.setdefault(key, []).extend(extra)
            changed[market_file] = market
    # Solo portadas/audio de las altas, con una lectura conjunta de blobs; main conserva sus archivos.
    prefixes = tuple('assets/reading-covers/' + b['id'] for b in additions)
    explicit = {b.get('portada_local', '').lstrip('/') for b in additions}
    for book in additions:
        for field in ('audio_descripcion', 'audio_fragmento'):
            value = book.get(field)
            if isinstance(value, str) and value.startswith('/assets/reading-audio/'):
                explicit.add(value.lstrip('/'))
    entries = []
    for row in (git(root, 'ls-tree', '-r', '-z', source, '--', 'assets/reading-covers', 'assets/reading-audio').split(b'\0') if additions else []):
        if not row:
            continue
        meta, raw_path = row.split(b'\t', 1)
        name = raw_path.decode('utf-8')
        if name.startswith(prefixes) or name in explicit:
            target = (root / name).resolve()
            if not any(target.is_relative_to((root / allowed).resolve()) for allowed in ('assets/reading-covers', 'assets/reading-audio')):
                raise ValueError('Asset fuera del catálogo')
            if not target.exists():
                entries.append((target, meta.split()[2].decode()))
    blobs = {}
    if entries:
        hashes = sorted({sha for _, sha in entries})
        request = ('\n'.join(hashes) + '\n').encode()
        subprocess.run(['git', 'fetch', '--quiet', '--no-write-fetch-head', 'origin', '--stdin'], cwd=root, input=request, check=True, capture_output=True)
        data = io.BytesIO(git(root, 'cat-file', '--batch', data=request))
        for expected in hashes:
            sha, kind, size = data.readline().split()
            if sha.decode() != expected or kind != b'blob':
                raise ValueError('Blob fuente no disponible')
            blobs[expected] = data.read(int(size))
            if data.read(1) != b'\n':
                raise ValueError('Blob fuente incompleto')
    # Hasta aquí solo lectura/descarga: ningún JSON se cambia si falta la procedencia o un blob.
    for name, value in changed.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    for target, sha in entries:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blobs[sha])
    return sorted(ids) if changed else None
