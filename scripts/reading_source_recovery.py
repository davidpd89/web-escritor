"""Recuperación semántica de altas conservadas cuando main avanzó en los mismos JSON.

Añade los libros nuevos respecto a la base común y traslada los cambios de libros existentes que main no
tocó (fusión a tres bandas por libro). Nunca rebobina libros, precios ni registros ya publicados en main:
si main también cambió un libro, gana main. Tampoco recupera libros retirados o ya en cuarentena.
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


def recover(root, source, base, latest, skipped=None):
    """`skipped` recoge los ids de altas sin procedencia publicada: se apartan y el resto se recupera."""
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
    # El importador exige procedencia publicada para cada alta ISBN. Un libro sin ella se aparta (y lo conserva
    # quien llama, en `reading-atascado-*`); nunca tumba el resto del lote (CodeRabbit #1397).
    state_path = 'data/reading-intake-state.json'
    old_state = document(root, source, state_path, {'items': {}})

    def provenance(book):
        evidence = old_state.get('items', {}).get('isbn13:' + book.get('isbn13', ''), {})
        return evidence.get('estado_ingesta') == 'publicado' and evidence.get('libro_id') == book['id']
    # Un nombre del almacén sin huella en el manifiesto de origen no prueba que sus bytes llegaran al almacén
    # (20/11, #1500: la carga 44767256039 dio de alta 500 nombres y su runner murió antes de subirlos). Esos
    # nombres no viajan y sus libros se apartan como los que no tienen procedencia: la consulta siguiente los rehace.
    store_file = 'data/reading-covers-store.json'
    store_old = document(root, source, store_file, {'archivos': [], 'sha256': {}})
    store_now = document(root, latest, store_file, {'base_url': '', 'archivos': [], 'sha256': {}})
    old_digests = store_old.get('sha256') or {}
    # Un nombre que main ya registró con su huella sí está probado (el almacén es de solo añadir; Codex #1501).
    proven_in_main = store_now.get('sha256') or {}
    unproven = {n for n in store_old.get('archivos', []) if n not in old_digests and n not in proven_in_main}

    def cover_unproven(book):
        cover = book.get('portada_local')
        if not unproven or not isinstance(cover, str) or not cover:
            return False
        name = cover.rsplit('/', 1)[-1]
        return name in unproven or name.replace('.webp', '-320.webp') in unproven
    orphans = [b['id'] for b in additions if b['id'].startswith('isbn-') and not provenance(b)]
    stranded = [b['id'] for b in previous['libros'] if b['id'] not in orphans and cover_unproven(b)]
    if orphans or stranded:
        if skipped is None:
            raise ValueError('La recuperación no tiene procedencia publicada: ' + ', '.join(orphans + stranded))
        skipped.extend(orphans + stranded)
        known |= set(orphans) | set(stranded)
        additions = [b for b in additions if b['id'] not in known]
    ids = {b['id'] for b in additions}
    changed = {}
    # Libros que ya existían: antes solo se trasladaban altas, y un punto de guardado con solo cambios de
    # libros existentes devolvía None y se borraba sin publicarlos (#1312, CodeRabbit).
    base_books = {b['id']: b for b in original['libros']}
    position = {b['id']: i for i, b in enumerate(current['libros'])}
    updated = []
    # Libros que main no tocó (ni su ficha cambió desde la base): de ellos el origen manda en ficha, relaciones,
    # autores, editorial y recursos (CodeRabbit #1320: una portada nueva sin cambio de ficha se perdía).
    untouched = set(ids)
    for book in previous['libros']:
        old, i = base_books.get(book['id']), position.get(book['id'])
        if book['id'] in stranded:
            continue
        if old is not None and i is not None and current['libros'][i] == old:
            untouched.add(book['id'])
            if book != old:
                current['libros'][i] = book
                updated.append(book['id'])
    current['libros'].extend(additions)
    carried = additions + [b for b in previous['libros'] if b['id'] in set(updated)]

    def row(r):
        return json.dumps(r, sort_keys=True)
    seen = {row(r) for r in original.get('libro_categorias', []) + current.get('libro_categorias', [])}
    relations = [r for r in previous.get('libro_categorias', []) if r['libro_id'] in untouched and row(r) not in seen]
    if relations:
        existing = {c['id'] for c in current.get('categorias', [])}
        required = {r['categoria_id'] for r in relations}
        current.setdefault('categorias', []).extend(c for c in previous.get('categorias', []) if c['id'] in required and c['id'] not in existing)
        if not required <= {c['id'] for c in current['categorias']}:
            raise ValueError('La recuperación carece de categorías fuente')
        current.setdefault('libro_categorias', []).extend(relations)
    if additions or updated or relations:
        changed[path] = current
    # Se traslada el registro de procedencia original de cada alta ISBN (ya comprobado arriba).
    state = document(root, latest, state_path, {'schema_version': 1, 'items': {}})
    for book in additions:
        if book['id'].startswith('isbn-'):
            key = 'isbn13:' + book.get('isbn13', '')
            state.setdefault('items', {})[key] = old_state['items'][key]
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
        ('data/reading-authors.json', 'autores', 'nombre', {a for b in carried for a in b.get('autores', [])}),
        ('data/reading-publishers.json', 'editoriales', 'slug', {b.get('editorial_catalogo_slug') for b in carried}),
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
    # Portadas del almacén externo: el manifiesto viaja como unión (main gana en sus nombres). Es seguro porque el
    # almacén es de solo añadir y el punto de guardado solo se escribe con sus bytes ya subidos (CodeRabbit #1495).
    present = set(store_now.get('archivos', []))
    extra_names = [n for n in store_old.get('archivos', []) if n not in present and n not in unproven]
    if extra_names:
        store_now['base_url'] = store_now.get('base_url') or store_old.get('base_url', '')
        store_now['archivos'] = sorted(present | set(extra_names))
        store_now['sha256'] = {**{n: old_digests[n] for n in extra_names}, **store_now.get('sha256', {})}
        changed[store_file] = store_now
    # Portadas/audio de las altas y de los libros que main no tocó, con una lectura conjunta de blobs.
    moved = [b for b in previous['libros'] if b['id'] in untouched]

    def owned(books):
        prefixes = tuple('assets/reading-covers/' + b['id'] for b in books)
        explicit = {b.get('portada_local', '').lstrip('/') for b in books} - {''}
        for book in books:
            for field in ('audio_descripcion', 'audio_fragmento'):
                value = book.get(field)
                if isinstance(value, str) and value.startswith('/assets/reading-audio/'):
                    explicit.add(value.lstrip('/'))
        return lambda name: name.startswith(prefixes) or name in explicit
    of_addition, of_untouched = owned(additions), owned(moved)
    entries = []
    def tree(ref):
        rows = git(root, 'ls-tree', '-r', '-z', ref, '--', 'assets/reading-covers', 'assets/reading-audio').split(b'\0')
        return {r.split(b'\t', 1)[1].decode('utf-8'): r.split(b'\t', 1)[0].split()[2].decode() for r in rows if r}
    # Un fichero que main dejó como estaba en la base (portada rehecha del libro) se sustituye; uno que main
    # cambió por su cuenta se respeta.
    in_base, in_main = (tree(ref) if moved else {} for ref in (base, latest))
    for row in (git(root, 'ls-tree', '-r', '-z', source, '--', 'assets/reading-covers', 'assets/reading-audio').split(b'\0') if moved else []):
        if not row:
            continue
        meta, raw_path = row.split(b'\t', 1)
        name = raw_path.decode('utf-8')
        sha = meta.split()[2].decode()
        # Un alta trae lo que main no tenga; un libro existente, solo lo que el origen cambió y main no (un fichero
        # que main borró o rehízo por su cuenta se respeta).
        if of_addition(name):
            wanted = not (root / name).exists() or (in_main.get(name) != sha and in_main.get(name) == in_base.get(name))
        else:
            wanted = sha != in_base.get(name) and in_main.get(name) == in_base.get(name) and of_untouched(name)
        if wanted:
            target = (root / name).resolve()
            if not any(target.is_relative_to((root / allowed).resolve()) for allowed in ('assets/reading-covers', 'assets/reading-audio')):
                raise ValueError('Asset fuera del catálogo')
            entries.append((target, sha))
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
    return sorted(ids) if changed or entries else None
