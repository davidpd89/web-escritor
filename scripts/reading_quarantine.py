"""Cuarentena por libro (docs/contrato-tarjeta-libro.md): un dato malo aparta su libro, no frena el lote.

La validación del catálogo se detiene en el primer error. Si el error nombra un libro, este módulo lo aparta y
vuelve a validar: un libro ya publicado recupera su última versión buena (la de HEAD) y uno nuevo sale del lote.
Lo apartado queda en data/reading-quarantine.json (ISBN, fuente, datos originales, motivo, causa agrupable e
intentos) y se reintenta en cada carga. Un error que no nombra un libro, o que aparta a más de la mitad del lote,
sigue parando la carga: eso es una regla rota, no un dato, y se notifica como fallo del workflow.

Aprender de cada caso: cuando una causa se corrige en la regla general, se añade una reparación en REPAIRS (o se
arregla el script que la produce) con su test de regresión, y la siguiente carga recupera todos los afectados.

    python scripts/reading_quarantine.py           aplica la cuarentena al árbol de trabajo
    python scripts/reading_quarantine.py --report  agrupa por causa lo apartado y lo pendiente de la ingesta
"""
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from reading_intake_fetch import write_if_changed
from reading_ratings_refresh import write_changed

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = 'data/reading-catalogue.json'
QUARANTINE = 'data/reading-quarantine.json'
PUBLISHERS = 'data/reading-publishers.json'
INTAKE_STATE = 'data/reading-intake-state.json'
MAX_BOOKS = 10       # siempre se toleran al menos estos libros apartados
MAX_SHARE = 0.5      # más de la mitad del lote apartada = regla rota, no datos
_spec = importlib.util.spec_from_file_location('reading_catalogue_build', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


def culprit(message, data):
    """Id del libro al que se refiere el error («<id>: …» o «<id>.campo: …»), si es un libro."""
    match = re.match(r'([a-z0-9-]+)[.:]', message)
    ids = {b['id'] for b in data['libros']}
    return match[1] if match and match[1] in ids else None


def cause(message):
    """Motivo sin el libro concreto ni cifras: la clave para agrupar incidencias de la misma regla."""
    text = re.sub(r'^[a-z0-9-]+(?=[.:])\.?', '', str(message)).lstrip(': ').strip()
    text = re.sub(r'\b(?:97[89])?\d{9}[\dXx]\b', '<isbn>', text)
    text = re.sub(r'https?://\S+', '<url>', text)
    return re.sub(r'\d+', 'N', text)[:160] or 'sin motivo'


def committed(root):
    try:
        out = subprocess.run(['git', 'show', 'HEAD:' + CATALOGUE], cwd=root, capture_output=True, check=True)
        return json.loads(out.stdout.decode('utf-8'))
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def limit(data, previous):
    """Libros apartables en este lote: los nuevos o cambiados respecto a lo publicado."""
    good = {b['id']: b for b in (previous or {}).get('libros', [])}
    batch = sum(1 for b in data['libros'] if good.get(b['id']) != b)
    return max(MAX_BOOKS, int(batch * MAX_SHARE))


def restore_cover(root, book):
    """Al volver a la versión publicada de un libro vuelve también su portada: la carga pudo sobrescribir el fichero
    (misma ruta) y revertir solo el JSON dejaba la imagen nueva con las medidas viejas o duplicada."""
    for rel in (book.get('portada_local', ''), book.get('portada_local', '').replace('.webp', '-320.webp')):
        if not rel.startswith('/assets/reading-covers/'):
            continue
        try:
            old = subprocess.run(['git', 'show', 'HEAD:' + rel.lstrip('/')], cwd=root, capture_output=True, check=True).stdout
        except (subprocess.CalledProcessError, OSError):
            continue
        path = Path(root) / rel.lstrip('/')
        if not path.is_file() or path.read_bytes() != old:
            path.write_bytes(old)


def isolate(data, root, previous=None, held=(), today=None):
    """Valida `data` apartando libros hasta que pasa. Devuelve (data, apartados) o lanza ValidationError."""
    today = today or date.today().isoformat()
    before = {h['libro']['id']: h for h in held}
    data = json.loads(json.dumps(data))
    present = {b['id'] for b in data['libros']}
    # Lo apartado antes vuelve a probarse, salvo que la carga haya traído ya una versión nueva de ese libro.
    for h in held:
        if h['libro']['id'] not in present:
            data['libros'].append(h['libro'])
            data['libro_categorias'] += [{'libro_id': h['libro']['id'], 'categoria_id': c} for c in h['categorias']]
    cap = limit(data, previous)
    good = {b['id']: b for b in (previous or {}).get('libros', [])}
    good_rel = {}
    for r in (previous or {}).get('libro_categorias', []):
        good_rel.setdefault(r['libro_id'], []).append(r)
    out, reverted = [], set()
    while True:
        try:
            build.validate(data, root)
            return data, out
        except build.ValidationError as exc:
            book_id = culprit(str(exc), data)
            twin = re.search(r'portada duplicada \(igual que ([a-z0-9-]+)\)', str(exc))
            if book_id and twin and twin[1] not in reverted and (book_id in reverted or good.get(book_id) == next(
                    b for b in data['libros'] if b['id'] == book_id)) and any(b['id'] == twin[1] for b in data['libros']):
                # De dos portadas iguales, la culpable es la que ha cambiado, no la que ya estaba publicada así.
                book_id = twin[1]
            # Sin libro, su versión buena también falla o la publicada falla sin cambios: es la regla, no el dato.
            if not book_id or book_id in reverted or good.get(book_id) == next(
                    b for b in data['libros'] if b['id'] == book_id):
                raise
            if len(out) >= cap:
                raise build.ValidationError(
                    f'Error global: más de {cap} libros apartados en un lote; causas: '
                    + '; '.join(sorted({cause(h['motivo']) for h in out}))[:400]) from exc
            at = next(i for i, b in enumerate(data['libros']) if b['id'] == book_id)
            book = data['libros'][at]
            prior = before.get(book_id, {})
            out.append({'libro': book, 'categorias': sorted(r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book_id),
                        'motivo': str(exc), 'causa': cause(exc), 'isbn': book.get('isbn13', ''),
                        'fuente': book.get('fuente_publicacion_url') or book.get('fuente_bibliografica_url', ''),
                        'desde': prior.get('desde', today), 'intentos': int(prior.get('intentos', 0)) + 1, 'ultimo_intento': today})
            mine = [r for r in data['libro_categorias'] if r['libro_id'] == book_id]
            if book_id in good:
                # Ya publicado: sigue en línea con su última versión buena; si esa también falla, la regla está rota.
                data['libros'][at] = good[book_id]
                restore_cover(root, good[book_id])
                if mine != good_rel.get(book_id, []):
                    data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book_id] + good_rel.get(book_id, [])
                reverted.add(book_id)
            else:
                del data['libros'][at]
                data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book_id]


# --- Reparaciones de reglas generales -------------------------------------------------------------------------
# Cada reparación corrige una causa para TODOS los libros afectados (apartados o no) y tiene su test de regresión.

def repair_catalogue_publishers(books, root, today):
    """«sello del catálogo inexistente»: el sello se registra de nuevo desde la ficha oficial del propio libro.

    Origen (sync 41821191166 / #1152): el carry de una PR obsoleta no trasladaba data/reading-publishers.json y los
    libros de sellos nuevos (Neko Books, Yoyo…) quedaban sin su sello."""
    from reading_catalogue_publishers import PublisherError, catalogue_publisher
    from reading_intake_core import normalize_text
    path = root / PUBLISHERS
    store = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema_version': 1, 'editoriales': []}
    known = {p['slug'] for p in store['editoriales']}
    registry = json.loads((root / 'data/editoriales.json').read_text(encoding='utf-8'))
    config_path = root / 'data/reading-intake-config.json'
    aliases = json.loads(config_path.read_text(encoding='utf-8')).get('publisher_aliases', []) if config_path.exists() else []
    names = {normalize_text(n) for p in registry.get('publishers', []) for n in (
        p.get('name', ''), re.sub(r'^(?:Editorial|Ediciones)\s+', '', p.get('name', ''), flags=re.I))}
    names |= {normalize_text(a) for o in aliases for a in o.get('aliases', [])}
    slugs = {p.get('slug') for p in registry.get('publishers', [])}
    missing = [b for b in books if b.get('editorial_catalogo_slug') and b['editorial_catalogo_slug'] not in known]
    fixed = 0
    for book in missing:
        slug = book['editorial_catalogo_slug']
        source = book.get('fuente_publicacion_url') or book.get('fuente_bibliografica_url')
        if slug not in known and book.get('editorial') and source:
            try:
                item = catalogue_publisher(book['editorial'], store, source, book.get('fecha_verificacion') or today,
                                           directory_names=names, directory_slugs=slugs, group=book.get('grupo_editorial', ''))
                if item['slug'] == slug:
                    known.add(slug)
            except PublisherError:
                pass  # sigue apartado con su motivo; la regla no puede resolverlo sola
        fixed += slug in known
    if fixed:
        write_if_changed(path, store)
    return fixed  # libros cuyo sello vuelve a existir


_tildes_spec = importlib.util.spec_from_file_location('check_copy_tildes', ROOT / 'scripts/check-copy-tildes.py')
tildes = importlib.util.module_from_spec(_tildes_spec)
_tildes_spec.loader.exec_module(tildes)
PROSE_FIELDS = ('titulo', 'descripcion_breve', 'sinopsis_breve', 'sinopsis_completa', 'edad_recomendada')


def repair_title_accents(books, root, today):
    """«"edicion" debería ser "edición"»: el texto de la fuente recupera las tildes que exige check-copy-tildes.

    Origen (sync 42444782344 / #1228): títulos de Norma, Sillón Orejero y HarperCollins sin tildes («Nueva edicion
    integral», «nueva edicion») tumbaron content-index-check con 38 avisos en fichas, relacionados y mapa."""
    fixed = 0
    for book in books:
        for field in PROSE_FIELDS:
            value = book.get(field)
            if isinstance(value, str) and value != (repaired := tildes.restore_accents(value)):
                book[field] = repaired
                fixed += 1
    return fixed


REPAIRS = (repair_catalogue_publishers, repair_title_accents)


def apply(root=ROOT, today=None):
    """Aplica la cuarentena a los datos del árbol de trabajo. Devuelve la lista de libros apartados."""
    today = today or date.today().isoformat()
    path, held_path = root / CATALOGUE, root / QUARANTINE
    data = json.loads(path.read_text(encoding='utf-8'))
    original = json.loads(json.dumps(data))
    held = json.loads(held_path.read_text(encoding='utf-8'))['libros'] if held_path.exists() else []
    for repair in REPAIRS:
        repair(data['libros'] + [h['libro'] for h in held], root, today)
    clean, out = isolate(data, root, committed(root), held, today=today)
    if clean != original:  # mismo formato que el último escritor del catálogo (precios), sin reordenar claves
        write_changed(path, clean)
    if out or held_path.exists():
        write_if_changed(held_path, {'schema_version': 1, 'libros': out})
    for h in out:
        print(f"Cuarentena: {h['libro']['id']} — {h['motivo']}", flush=True)
    return out


def report(root=ROOT):
    """Incidencias agrupadas por causa: cuarentena del catálogo + libros pendientes de datos en la ingesta."""
    groups = {}
    held_path = root / QUARANTINE
    for h in (json.loads(held_path.read_text(encoding='utf-8'))['libros'] if held_path.exists() else []):
        key = ('cuarentena', h.get('causa') or cause(h['motivo']))
        groups.setdefault(key, []).append(f"{h['libro'].get('isbn13', '')} {h['libro'].get('titulo', '')} (desde {h['desde']}, {h.get('intentos', 1)} intentos)")
    state_path = root / INTAKE_STATE
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'items': {}}
    for item in state.get('items', {}).values():
        if item.get('estado_ingesta') == 'pendiente_datos':
            key = ('ingesta', cause(item.get('motivo', '')))
            groups.setdefault(key, []).append(f"{item.get('isbn13') or item.get('fuente', '?')} (desde {item.get('primera_deteccion', '?')}, {item.get('intentos', 1)} intentos)")
    lines = []
    for (where, why), books in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"[{where}] {len(books)} × {why}")
        lines += [f"    {b}" for b in books[:5]] + ([f"    … y {len(books) - 5} más"] if len(books) > 5 else [])
    return '\n'.join(lines) or 'Sin incidencias.'


if __name__ == '__main__':
    if '--report' in sys.argv[1:]:
        print(report())
    else:
        apply()
