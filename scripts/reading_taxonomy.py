"""Categorías adicionales a partir de las palabras clave que la propia editorial publica.

Sin modelos ni costes: cada regla es un patrón sobre las palabras clave y la colección de la
ficha oficial. Solo se añaden categorías; nunca se retira una asignada a mano.
"""
from __future__ import annotations

import re

from reading_intake_core import normalize_text

# (patrón sobre texto normalizado, id, nombre, tipo). El orden fija la prioridad si hay tope.
RULES = (
    (r'\b(thriller|novela negra|suspense|intriga|misterio)\b', 'misterio-y-thriller', 'Misterio y thriller', 'genero'),
    (r'\bfantasia\b|\bromantasy\b|\bnovela fantastica\b|\bliteratura fantastica\b', 'fantasia', 'Fantasía', 'genero'),
    (r'\bromance\b|novela romantica|\bromantasy\b', 'romance', 'Romance', 'genero'),
    (r'ciencia ficcion|distopi', 'ciencia-ficcion', 'Ciencia ficción', 'genero'),
    (r'\bterror\b', 'terror', 'Terror', 'genero'),
    (r'novela historica', 'novela-historica', 'Novela histórica', 'genero'),
    (r'\baventura', 'aventuras', 'Aventuras', 'genero'),
    (r'\bpoesia\b|\bpoemas?\b', 'poesia', 'Poesía', 'genero'),
    (r'\bhumor\b|comedia', 'humor', 'Humor', 'genero'),
    (r'\bensayo\b', 'ensayo', 'Ensayo', 'genero'),
    (r'novela grafica|\bcomic\b', 'comic-y-novela-grafica', 'Cómic y novela gráfica', 'genero'),
    (r'biografia|memorias|autobiograf', 'biografias-y-memorias', 'Biografías y memorias', 'genero'),
    (r'\brecetas?\b|\bcocina\b|reposteria|\bbarbacoa\b', 'cocina', 'Cocina', 'genero'),
    (r'autoayuda|desarrollo personal|crecimiento personal|mindfulness|\bhabitos\b|autoestima|psicologia|motivacion|bienestar emocional', 'desarrollo-personal', 'Desarrollo personal', 'genero'),
    (r'novela contemporanea|literatura contemporanea|narrativa contemporanea', 'narrativa', 'Narrativa contemporánea', 'genero'),
    (r'\bfamilia\b|\bfamiliar', 'tema-familia', 'Familia', 'tematica'),
    (r'\bamistad\b', 'tema-amistad', 'Amistad', 'tematica'),
    (r'\bamor\b|relaciones de pareja|\bpareja\b', 'tema-amor-y-pareja', 'Amor y pareja', 'tematica'),
    (r'\bsecretos?\b|\bmisterios? familiar', 'tema-secretos', 'Secretos', 'tematica'),
    (r'\bvenganza\b', 'tema-venganza', 'Venganza', 'tematica'),
    (r'corrupcion|politic|geopolitica|conspiracion|\belites?\b', 'tema-poder-y-politica', 'Poder y política', 'tematica'),
    (r'\bduelo\b|\bperdida\b|superacion', 'tema-superacion-y-duelo', 'Superación y duelo', 'tematica'),
    (r'\bviajes?\b|\bviajar\b', 'tema-viajes', 'Viajes', 'tematica'),
    (r'supervivencia', 'tema-supervivencia', 'Supervivencia', 'tematica'),
    (r'feminis|\bmujeres\b', 'tema-mujeres', 'Mujeres', 'tematica'),
    (r'\bmemoria\b|\brecuerdos?\b', 'tema-memoria', 'Memoria', 'tematica'),
    (r'\bmigracion\b|exilio', 'tema-migracion-y-exilio', 'Migración y exilio', 'tematica'),
    (r'\bdeporte\b|\bfutbol\b', 'tema-deporte', 'Deporte', 'tematica'),
    (r'salud\b|alimentacion saludable|nutricion|\bdieta\b|\bfibra\b|\bintestin', 'nutricion-y-bienestar', 'Nutrición y bienestar', 'tematica'),
    (r'\bvegetal|\bvegetarian|\bvegano', 'tema-cocina-vegetal', 'Cocina vegetal', 'tematica'),
    (r'\bnaturaleza\b|\banimales\b', 'tema-naturaleza', 'Naturaleza', 'tematica'),
    (r'\binfancia\b|\bninos?\b', 'tema-infancia', 'Infancia', 'tematica'),
    (r'\bnavidad', 'navidad', 'Navidad', 'temporada'),
    (r'\bhalloween\b', 'halloween', 'Halloween', 'temporada'),
    (r'\bverano\b', 'verano', 'Verano', 'temporada'),
    (r'edad media|medieval', 'epoca-edad-media', 'Edad Media', 'epoca'),
    (r'siglo xix|decimononic', 'epoca-siglo-xix', 'Siglo XIX', 'epoca'),
    (r'siglo xx\b|guerra civil|posguerra|franquis', 'epoca-siglo-xx', 'Siglo XX', 'epoca'),
)

# Reviewed against the editions' descriptions. Existing catalogue imports can still
# carry the old automatic match until their classifications are regenerated.
REVIEWED_CATEGORY_EXCLUSIONS = {
    "9789403247854": {"fantasia"},  # La magia de las luces: el baile de las princesas
    "9789403247878": {"fantasia"},  # La magia de las luces: un día con los bomberos
    "9788411214315": {"fantasia"},  # Astrología, filosofía y magia (ensayo de práctica espiritual)
}


MAX_EXTRA = 6


def keyword_list(raw: str) -> list[str]:
    seen, out = set(), []
    for part in re.split(r'\s*[,;]\s*', str(raw or '')):
        clean = ' '.join(part.split())
        key = normalize_text(clean)
        if clean and key not in seen and len(key) <= 60:
            seen.add(key)
            out.append(clean)
    return out[:40]


def own_keywords(record: dict) -> list[str]:
    """Palabras clave que hablan de este libro y no de otras obras que la editorial promociona.

    Las editoriales rellenan sus palabras clave con títulos vecinos: «virginia woolf una biografia»
    en La señora Dalloway o «hachis...salud» (otro tebeo) en Ibáñez Mítico 2. Una palabra clave con
    el nombre del autor pero sin el título, o con puntos suspensivos de título, no clasifica el libro.
    """
    title = normalize_text(record.get('titulo', ''))
    names = [n for a in record.get('autores', []) for n in [normalize_text(a)] if n]
    names += [w for n in names for w in n.split() if len(w) >= 5]
    kept = []
    for raw in record.get('palabras_clave', []):
        key = normalize_text(raw)
        if '...' in str(raw) or '…' in str(raw):
            continue
        if any(re.search(r'\b' + re.escape(n) + r'\b', key) for n in names) and not (title and title in key):
            continue
        kept.append(raw)
    return kept


def extra_categories(record: dict) -> list[tuple[str, str, str]]:
    """(id, nombre, tipo) para cada regla que coincide con palabras clave, colección o título."""
    haystack = normalize_text(' , '.join([
        *own_keywords(record), record.get('coleccion', ''), record.get('titulo', ''),
    ]))
    own = normalize_text(' , '.join([record.get('coleccion', ''), record.get('titulo', '')]))
    found: list[tuple[str, str, str]] = []
    for pattern, ident, name, kind in RULES:
        if not re.search(pattern, haystack) or ident in {f[0] for f in found}:
            continue
        # Las palabras clave editoriales incluyen reclamos de regalo («Navidad», «verano»):
        # una temporada solo cuenta si aparece en el título o la colección.
        if kind == 'temporada' and not re.search(pattern, own):
            continue
        found.append((ident, name, kind))
    if 'tema-cocina-vegetal' in {f[0] for f in found} and 'cocina' not in {f[0] for f in found}:
        found = [f for f in found if f[0] != 'tema-cocina-vegetal']
    return found[:MAX_EXTRA]


# Clasificación propia: categorías que se deducen de las ya asignadas y del título, sin fuentes externas.
# (id, nombre, tipo, descripción, categorías que la activan, patrón sobre el título normalizado).
# Romantasy es la excepción: exige romance y algún género de fantasía a la vez.
DERIVED = (
    ('romantasy', 'Romantasy', 'genero', 'Fantasía con la historia de amor en el centro.',
     set(), None),
    ('halloween', 'Halloween', 'temporada', 'Terror, fantasía oscura y lecturas de miedo para Halloween.',
     {'terror', 'fantasia-oscura'}, r'\bbrujas?\b|\bfantasmas?\b|\bvampir|\bzombi|\bhalloween\b|\bmiedo\b'),
    ('navidad', 'Navidad', 'temporada', 'Lecturas y regalos para Navidad.',
     set(), r'\bnavid|\badviento\b|\breyes magos\b|\bpapa noel\b'),
    ('san-valentin', 'San Valentín', 'temporada', 'Romance y romantasy para San Valentín.',
     {'romance', 'romantasy', 'tema-amor-y-pareja'}, None),
    ('dia-de-la-madre', 'Día de la Madre', 'temporada', 'Maternidad, crianza y libros para regalar a una madre.',
     {'familia-y-crianza'}, r'\bmadres?\b|\bmama\b|\bmaternidad\b'),
    ('dia-del-padre', 'Día del Padre', 'temporada', 'Paternidad, crianza y libros para regalar a un padre.',
     {'familia-y-crianza'}, r'\bpadres?\b|\bpapa\b|\bpaternidad\b'),
    ('edicion-especial', 'Ediciones especiales', 'contenido',
     'Ediciones especiales, limitadas, de coleccionista, ilustradas o conmemorativas.',
     set(), r'\bedicion (especial|limitada|coleccionista|de coleccionista|ilustrada|conmemorativa|aniversario|de lujo)\b'
     r'|\bcantos (tintados|decorados)\b|\baniversario\b|\breedicion\b'),
)
FANTASY = {'fantasia', 'fantasia-juvenil', 'fantasia-oscura'}
# Un libro de crianza vale para ambos días salvo que el título hable solo del otro progenitor.
OTHER_PARENT = {'dia-de-la-madre': r'\bpadres?\b|\bpapa\b|\bpaternidad\b',
                'dia-del-padre': r'\bmadres?\b|\bmama\b|\bmaternidad\b'}


def derived_categories(assigned: set[str], title: str) -> list[str]:
    """Ids de la clasificación propia que corresponden a un libro con esas categorías y ese título."""
    title = normalize_text(title)
    out = []
    current = set(assigned)
    for ident, _name, _kind, _desc, triggers, pattern in DERIVED:
        if ident == 'romantasy':
            hit = 'romance' in current and bool(current & FANTASY)
        else:
            own = bool(pattern and re.search(pattern, title))
            hit = own or bool(current & triggers)
            if ident in OTHER_PARENT and not own and re.search(OTHER_PARENT[ident], title):
                hit = False
        if hit and ident not in current:
            out.append(ident)
            current.add(ident)
    return out


def apply_derived(catalogue: dict) -> dict[str, list[str]]:
    """Añade en el catálogo la clasificación propia que falte (idempotente; respeta categorias_excluidas)."""
    repair_classification(catalogue)
    known = {c['id']: c for c in catalogue['categorias']}
    for order, (ident, name, kind, desc, *_rest) in enumerate(DERIVED):
        if ident not in known:
            known[ident] = {'id': ident, 'slug': ident, 'nombre': name, 'tipo': kind, 'descripcion': desc,
                            'orden': 140 + order, 'activa': True}
            catalogue['categorias'].append(known[ident])
    by_book: dict[str, set[str]] = {}
    for rel in catalogue['libro_categorias']:
        by_book.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    added: dict[str, list[str]] = {}
    for book in catalogue['libros']:
        blocked = set(book.get('categorias_excluidas', []))
        new = [c for c in derived_categories(by_book.get(book['id'], set()), book.get('titulo', ''))
               if c not in blocked]
        if new:
            catalogue['libro_categorias'] += [{'libro_id': book['id'], 'categoria_id': c} for c in new]
            added[book['id']] = new
    return added


REFERENCE_ID = 'guias-y-referencia'
FICTION_GENRES = {'narrativa','narrativa-juvenil','novela-historica','romance','romantasy','fantasia','fantasia-juvenil','fantasia-oscura','ciencia-ficcion','misterio-y-thriller','terror','aventuras','relatos'}


def reference_work(title, assigned):
    """Forma de consulta explícita; un título de novela que diga diccionario no basta."""
    text = normalize_text(title)
    return not (set(assigned) & FICTION_GENRES) and bool(re.search(
        r'\bguia visual\b|^(?:(?:el|la|un|una) )?(?:enciclopedia|diccionario|atlas)\b', text))


def category_priority(category):
    """El tipo de obra no desaparece detrás de sus temas al resumir dos etiquetas."""
    kind = {'genero':0,'temporada':1,'tematica':2,'epoca':3,'contenido':4,'edad':5}
    return (0 if category['id'] in {'comic-y-novela-grafica', REFERENCE_ID} else 1,
            kind[category['tipo']], category['orden'], category['id'])


def repair_classification(catalogue, today=None):
    """Corrige la antigua inferencia consulta→ensayo para todas las altas automáticas afectadas."""
    by_book = {}
    for rel in catalogue['libro_categorias']:
        by_book.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    repaired = []
    for book in catalogue['libros']:
        assigned = by_book.get(book['id'], set())
        legacy = 'tema-diccionarios-y-referencia' in assigned and not (assigned & FICTION_GENRES)
        inferred = 'ensayo' in assigned and reference_work(book.get('titulo',''), assigned)
        if not book['id'].startswith('isbn-') or not (legacy or inferred):
            continue
        catalogue['libro_categorias'] = [r for r in catalogue['libro_categorias']
            if not (r['libro_id']==book['id'] and r['categoria_id'] in {'ensayo', 'tema-diccionarios-y-referencia'})]
        if REFERENCE_ID not in assigned:
            catalogue['libro_categorias'].append({'libro_id':book['id'],'categoria_id':REFERENCE_ID})
        if not any(c['id']==REFERENCE_ID for c in catalogue['categorias']):
            catalogue['categorias'].append({'id':REFERENCE_ID,'slug':REFERENCE_ID,'nombre':'Guías y referencia',
                'tipo':'genero','descripcion':'Guías, diccionarios y obras de consulta.','orden':217,'activa':True})
        if book.get('descripcion_breve'):
            book['descripcion_breve'] = re.sub(r'La editorial la incluye en [^.]+\.',
                'Clasificación: guías y referencia.',book['descripcion_breve'])
        if today:
            book['fecha_actualizacion'] = today
        repaired.append(book['id'])
    return repaired
