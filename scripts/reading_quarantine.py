"""Cuarentena por libro (docs/contrato-tarjeta-libro.md): un dato malo aparta su libro, no frena el lote.

La validación del catálogo se detiene en el primer error. Si el error nombra un libro, este módulo lo aparta y
vuelve a validar: un libro ya publicado recupera su última versión buena (la de HEAD) y uno nuevo sale del lote.
Lo apartado queda en data/reading-quarantine.json con su motivo y se reintenta en la siguiente carga. Un error
que no nombra un libro, o demasiados libros apartados, sigue parando la carga: eso es una regla rota, no un dato.
"""
import importlib.util
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from reading_intake_fetch import write_if_changed
from reading_ratings_refresh import write_changed

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = 'data/reading-catalogue.json'
QUARANTINE = 'data/reading-quarantine.json'
MAX_BOOKS = 10
_spec = importlib.util.spec_from_file_location('reading_catalogue_build', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


def culprit(message, data):
    """Id del libro al que se refiere el error («<id>: …» o «<id>.campo: …»), si es un libro."""
    match = re.match(r'([a-z0-9-]+)[.:]', message)
    ids = {b['id'] for b in data['libros']}
    return match[1] if match and match[1] in ids else None


def committed(root):
    try:
        out = subprocess.run(['git', 'show', 'HEAD:' + CATALOGUE], cwd=root, capture_output=True, check=True)
        return json.loads(out.stdout.decode('utf-8'))
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def isolate(data, root, previous=None, held=(), today=None):
    """Valida `data` apartando libros hasta que pasa. Devuelve (data, apartados) o lanza ValidationError."""
    today = today or date.today().isoformat()
    since = {h['libro']['id']: h['desde'] for h in held}
    data = json.loads(json.dumps(data))
    present = {b['id'] for b in data['libros']}
    # Lo apartado antes vuelve a probarse, salvo que la carga haya traído ya una versión nueva de ese libro.
    for h in held:
        if h['libro']['id'] not in present:
            data['libros'].append(h['libro'])
            data['libro_categorias'] += [{'libro_id': h['libro']['id'], 'categoria_id': c} for c in h['categorias']]
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
            # Sin libro, su versión buena también falla o la publicada falla sin cambios: es la regla, no el dato.
            if not book_id or book_id in reverted or len(out) >= MAX_BOOKS or good.get(book_id) == next(
                    b for b in data['libros'] if b['id'] == book_id):
                raise
            at = next(i for i, b in enumerate(data['libros']) if b['id'] == book_id)
            book = data['libros'][at]
            out.append({'libro': book, 'categorias': sorted(r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book_id),
                        'motivo': str(exc), 'desde': since.get(book_id, today)})
            mine = [r for r in data['libro_categorias'] if r['libro_id'] == book_id]
            if book_id in good:
                # Ya publicado: sigue en línea con su última versión buena; si esa también falla, la regla está rota.
                data['libros'][at] = good[book_id]
                if mine != good_rel.get(book_id, []):
                    data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book_id] + good_rel.get(book_id, [])
                reverted.add(book_id)
            else:
                del data['libros'][at]
                data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book_id]


def apply(root=ROOT):
    """Aplica la cuarentena a los datos del árbol de trabajo. Devuelve la lista de libros apartados."""
    path, held_path = root / CATALOGUE, root / QUARANTINE
    data = json.loads(path.read_text(encoding='utf-8'))
    held = json.loads(held_path.read_text(encoding='utf-8'))['libros'] if held_path.exists() else []
    clean, out = isolate(data, root, committed(root), held)
    if clean != data:  # mismo formato que el último escritor del catálogo (precios), sin reordenar claves
        write_changed(path, clean)
    if out or held_path.exists():
        write_if_changed(held_path, {'schema_version': 1, 'libros': out})
    for h in out:
        print(f"Cuarentena: {h['libro']['id']} — {h['motivo']}", flush=True)
    return out


if __name__ == '__main__':
    apply()
