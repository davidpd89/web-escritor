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


def rule_allowed(kind: str, pattern: str, subject_text: str, own_text: str) -> bool:
    """Una regla vale si la respalda la materia/palabra clave o, salvo los temas, el título o la colección.

    Un tema por el título solo es una palabra suelta («Una conspiración de monstruos encantadores» no es un libro de
    política); una temporada, al revés, solo cuenta por el título o la colección (las palabras clave editoriales
    incluyen reclamos de regalo como «Navidad» o «verano»)."""
    if kind == 'temporada':
        return bool(re.search(pattern, own_text))
    return bool(re.search(pattern, subject_text) or (kind != 'tematica' and re.search(pattern, own_text)))


def extra_categories(record: dict) -> list[tuple[str, str, str]]:
    """(id, nombre, tipo) para cada regla que respaldan las palabras clave, la colección o el título."""
    subject_text = normalize_text(' , '.join(own_keywords(record)))
    own = normalize_text(' , '.join([record.get('coleccion', ''), record.get('titulo', '')]))
    found: list[tuple[str, str, str]] = []
    for pattern, ident, name, kind in RULES:
        if ident in {f[0] for f in found} or not rule_allowed(kind, pattern, subject_text, own):
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


# Lo que no se lee: cuadernos para rellenar, agendas, pegatinas, libros para colorear y métodos de idiomas. Amazon
# los vende como libros y la carga los publicaba con etiquetas inventadas por sus nodos. Patrones sobre el título
# normalizado; una novela que solo nombra un calendario o un cuaderno («Hasta que el calendario nos separe»,
# «Cuaderno blanco: Poemas») no coincide.
NON_READING_TITLE = (
    (r'\bpara colorear\b|\blibro de colorear\b|^colorea\b|\bpinta y pega\b', 'para colorear'),
    (r'\bpegatinas\b|\bstickers?\b', 'pegatinas'),
    (r'\bcalendario de adviento\b', 'calendario de Adviento'),
    (r'^agenda\b|\bagenda (?:anual|semanal|escolar|perpetua|\d{4})\b', 'agenda'),
    (r'(?:^|: )libretas?\b|\blibretas artisticas\b', 'libreta'),
    (r'\bcuadernos? (?:creativos?|de actividades|de pasatiempos|de invierno|de verano|de vacaciones|del detective'
     r'|de ejercicios|de caligrafia)\b|\bpasatiempos\b', 'cuaderno de actividades'),
    (r'\bdiario de \d+ anos\b', 'diario para rellenar'),
    (r'\bpack (?:de )?actividades\b|\blibro de actividades\b', 'actividades'),
    (r'\baprende (?:ingles|japones|chino|coreano|frances|aleman|italiano|portugues|idiomas)\b|\bnoken\b|\bjlpt\b'
     r'|\bnivel (?:a1|a2|b1|b2|c1|c2|n[1-5])\b|\(idiomas\)', 'método de idiomas'),
)
# Nodos de Amazon que marcan material de estudio o para rellenar aunque el título no lo diga («Sorry! But I Am
# With Hurry» está en «Aprendizaje y enseñanza de idiomas»).
NON_READING_NODES = {
    'aprendizaje y ensenanza de idiomas': 'método de idiomas', 'estudio de idiomas extranjeros': 'método de idiomas',
    'guias de estudio y repaso': 'material de estudio', 'libros para colorear': 'para colorear',
    'libros para colorear para adultos': 'para colorear', 'agendas': 'agenda', 'calendarios': 'calendario',
    'calendarios y agendas': 'agenda',
}


def non_reading_reason(title: str, nodes=()) -> str | None:
    """Motivo por el que un producto no es un libro de lectura para el catálogo, o None si lo es."""
    text = normalize_text(title)
    for pattern, why in NON_READING_TITLE:
        if re.search(pattern, text):
            return why
    for node in nodes:
        why = NON_READING_NODES.get(normalize_text(node))
        if why:
            return why
    return None


AMAZON_SOURCE = 'amazon.es/dp/'
RULE_OF = {ident: (pattern, kind) for pattern, ident, _name, kind in RULES}
DERIVED_IDS = {d[0] for d in DERIVED}


def subject_text(book: dict) -> str:
    """Materias de origen tal como las guarda la descripción («La editorial la incluye en fantasía, infantil.»)."""
    found = re.search(r'La editorial la incluye en ([^.]*)\.', book.get('descripcion_breve') or '')
    return normalize_text(found[1]) if found else ''


def rule_supported(book: dict, ident: str) -> bool:
    """Una etiqueta de regla en un alta de Amazon vale si la respaldan su materia guardada o su título."""
    if ident not in RULE_OF or AMAZON_SOURCE not in (book.get('fuente_bibliografica_url') or ''):
        return True
    subjects = subject_text(book)
    if not subjects and RULE_OF[ident][1] == 'genero':
        return True  # altas antiguas sin materia: el género del nodo es la única pista que hay
    own = normalize_text(' , '.join([book.get('coleccion') or '', book.get('titulo') or '']))
    return rule_allowed(RULE_OF[ident][1], RULE_OF[ident][0], subjects, own)


# Todo libro visible necesita un género: la tarjeta y los filtros públicos solo muestran género y edad, y 402 libros
# (2026-11-13) solo tenían temas internos («Madrid siglo 21»: arte y diseño). El género sale, por orden, del tema que
# ya tiene, de su edad o del género dominante de su sello; nunca se inventa.
FALLBACK_GENRES = {
    'arte-y-diseno': ('Arte y diseño', 'Arte, arquitectura, fotografía, cine y música.',
                      ('tema-arte-y-diseno', 'tema-arte', 'tema-arte-cine-y-musica', 'tema-peliculas-y-series')),
    'religion-y-espiritualidad': ('Religión y espiritualidad', 'Religión, espiritualidad y esoterismo.',
                                  ('tema-religion-y-espiritualidad', 'tema-religion', 'tema-esoterismo')),
    'economia-y-empresa': ('Economía y empresa', 'Economía, empresa y finanzas.',
                           ('tema-economia-y-empresa', 'tema-economia-politica-sociedad-y-actualidad')),
    'derecho': ('Derecho', 'Derecho y práctica legal.', ('tema-derecho',)),
    'politica-y-actualidad': ('Política y actualidad', 'Política, sociedad y actualidad.',
                              ('tema-poder-y-politica', 'tema-actualidad')),
    'viajes': ('Viajes', 'Guías y literatura de viajes.', ('tema-viajes',)),
    'ocio-y-aficiones': ('Ocio y aficiones', 'Deporte, manualidades, juegos y aficiones.',
                         ('tema-ocio-y-tiempo-libre', 'tema-deporte')),
    'ensayo': (None, None, ('tema-ciencias-humanas-y-sociales', 'tema-cronica')),
    'divulgacion-cientifica': (None, None, ('tema-ciencia-y-tecnologia',)),
    'narrativa-juvenil': (None, None, ('tema-novelas-juveniles', 'juvenil')),
    'narrativa': (None, None, ('clasicos',)),
}
# Colección de la edición: Amazon la pone entre paréntesis en el título («(Alfaguara Negra)», «(Otros Infantil)»,
# «(Best Seller | Ficción)»). Orden: lo infantil y lo juvenil antes que «ficción», que es la palabra más genérica.
COLLECTION_GENRES = (
    (r'infantil|álbum(es)? ilustrado|primeros lectores|\bkids\b', 'infantil'),
    (r'juvenil|young adult', 'narrativa-juvenil'),
    (r'\bnegra\b|polic[ií]aca|thriller|\bcr[ií]menes\b|\basesinatos?\b', 'misterio-y-thriller'),
    (r'\bfantasy\b|\bfantas[ií]a\b', 'fantasia'),
    (r'poes[ií]a', 'poesia'),
    (r'c[oó]mic|novela gr[aá]fica|\bmanga\b', 'comic-y-novela-grafica'),
    (r'\bficci[oó]n\b|\bnovela\b|\bnarrativa\b', 'narrativa'),
)
# Frases del título que dicen el público sin ambigüedad («Salamanca contada a los niños», «Aprende a leer con…»).
TITLE_GENRES = ((r'contad[ao]s? a (los )?niñ[oa]s|\baprender? a leer\b|\bjunior\b', 'infantil'),)


def collection_genre(title: str) -> str | None:
    lowered = title.casefold()
    parts = ' | '.join(re.findall(r'\(([^()]*)\)', lowered))
    for pattern, genre in COLLECTION_GENRES:
        if parts and re.search(pattern, parts):
            return genre
    return next((g for pattern, g in TITLE_GENRES if re.search(pattern, lowered)), None)


READER_TYPES = ('genero', 'tematica', 'epoca', 'edad')
AUTHOR_MIN = 2  # género del autor: al menos dos títulos suyos con género propio
PUBLISHER_SHARE, PUBLISHER_MIN = 0.6, 3  # género del sello: mayoría clara y no un solo título


class GenreFallback:
    """Género de respaldo de un libro, igual en cada pasada para que la reparación sea idempotente."""

    def __init__(self, catalogue: dict, by_book: dict):
        self.genres = {c['id'] for c in catalogue['categorias'] if c['tipo'] == 'genero' and c.get('activa', True)}
        self.genres |= set(FALLBACK_GENRES)
        self.ages = {c['id'] for c in catalogue['categorias'] if c['tipo'] == 'edad'}
        self.active = {c['id'] for c in catalogue['categorias'] if c.get('activa', True)} | set(FALLBACK_GENRES)
        # Lo que dice al lector qué libro es (y pide el módulo «para quién»): sin una de estas la ficha queda muda.
        self.reader = {c['id'] for c in catalogue['categorias']
                       if c.get('activa', True) and c['tipo'] in READER_TYPES} | set(FALLBACK_GENRES)
        self.by_publisher: dict = {}
        self.by_author: dict = {}
        for book in catalogue['libros']:  # solo géneros con respaldo propio: no cambian entre pasadas
            if book.get('estado') != 'publicado':
                continue
            for g in by_book.get(book['id'], set()) & self.genres:
                if rule_supported(book, g) and g not in FALLBACK_GENRES:
                    counts = self.by_publisher.setdefault(book.get('editorial') or '', {})
                    counts[g] = counts.get(g, 0) + 1
                    for author in book.get('autores') or []:
                        mine = self.by_author.setdefault(author, {})
                        mine[g] = mine.get(g, 0) + 1

    def pick(self, book: dict, assigned: set) -> str | None:
        excluded = set(book.get('categorias_excluidas') or [])
        own = {t for t in assigned if rule_supported(book, t)}  # un tema que solo puso un nodo no da género
        topic = next((g for g, (_n, _d, topics) in FALLBACK_GENRES.items() if own & set(topics)), None)
        if topic:
            return None if topic in excluded else topic
        if (series := collection_genre(book.get('titulo') or '')) and series in self.genres:
            return None if series in excluded else series
        if own & self.ages and 'infantil' not in excluded:
            return 'infantil'
        # Lo que el mismo autor publica con género propio, y si no, lo que publica su sello.
        sources = [(self.by_author.get(a, {}), AUTHOR_MIN) for a in book.get('autores') or []]
        sources.append((self.by_publisher.get(book.get('editorial') or '', {}), PUBLISHER_MIN))
        for counts, least in sources:
            best = max(counts, key=counts.get, default=None)
            if best and counts[best] >= least and counts[best] >= PUBLISHER_SHARE * sum(counts.values()):
                return None if best in excluded else best
        return None


def repair_amazon_rules(catalogue: dict, by_book: dict, fallback: GenreFallback) -> list:
    """Quita de las altas de Amazon las etiquetas que solo salían de sus nodos.

    Origen (carga del 2026-11-13): los nombres de nodo de Amazon, ancestros incluidos, entraban como palabras clave
    y las reglas leían «Ficción infantil sobre salud» como nutrición o «Libros de fantasía y ciencia ficción para
    niños» como ciencia ficción («El caballero Nacho y el príncipe feliz»). Ahora la materia de Amazon sale del mapa
    cerrado AMAZON_SUBJECTS; aquí una etiqueta de regla sigue si la respaldan la materia guardada o el título, o si
    es el género de respaldo del libro."""
    repaired = []
    for book in catalogue['libros']:
        if AMAZON_SOURCE not in (book.get('fuente_bibliografica_url') or ''):
            continue
        assigned = by_book.get(book['id'], set())
        drop = {c for c in assigned if not rule_supported(book, c)}
        if drop:
            kept = assigned - drop
            still = set(derived_categories(kept - DERIVED_IDS, book.get('titulo') or ''))
            # La derivación manda sobre la regla: «halloween» por «terror» vuelve con apply_derived (idempotencia).
            drop = (drop - still) | {c for c in kept & DERIVED_IDS if c not in still}
            if not (assigned - drop) & fallback.genres:
                drop.discard(fallback.pick(book, assigned - drop))
            # Sin categoría de lector ni género de respaldo la ficha quedaría muda: mejor sus etiquetas de antes.
            if not (assigned - drop) & fallback.reader and not fallback.pick(book, assigned - drop):
                drop = set()
        if not drop:
            continue
        catalogue['libro_categorias'] = [r for r in catalogue['libro_categorias']
                                         if not (r['libro_id'] == book['id'] and r['categoria_id'] in drop)]
        by_book[book['id']] = assigned - drop
        repaired.append(book['id'])
    return repaired


def ensure_genre(catalogue: dict, by_book: dict, fallback: GenreFallback) -> dict:
    """Da un género a cada libro no borrador que no lo tenga. Devuelve {libro: género}."""
    cats = {c['id']: c for c in catalogue['categorias']}
    added = {}
    for book in catalogue['libros']:
        assigned = by_book.get(book['id'], set())
        if book.get('estado') == 'borrador' or assigned & fallback.genres:
            continue
        pick = fallback.pick(book, assigned)
        if not pick:
            continue
        if pick not in cats:
            name, desc, _topics = FALLBACK_GENRES[pick]
            cats[pick] = {'id': pick, 'slug': pick, 'nombre': name, 'tipo': 'genero', 'descripcion': desc,
                          'orden': 230 + len(cats), 'activa': True}
            catalogue['categorias'].append(cats[pick])
        catalogue['libro_categorias'].append({'libro_id': book['id'], 'categoria_id': pick})
        by_book[book['id']] = assigned | {pick}
        added[book['id']] = pick
    return added


def repair_classification(catalogue, today=None):
    """Repara la clasificación automática: consulta→ensayo, etiquetas de nodos de Amazon y libros sin género.
    Idempotente; corre en cada carga (cuarentena) y en cada alta (apply_derived)."""
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
    by_book = {}
    for rel in catalogue['libro_categorias']:
        by_book.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    fallback = GenreFallback(catalogue, by_book)
    # Género antes y después de quitar etiquetas: el tema de un nodo («tema-viajes») deja su género de respaldo
    # antes de irse, y un libro que pierde su género por nodo recibe otro. Una sola pasada basta (idempotente).
    touched = set(ensure_genre(catalogue, by_book, fallback))
    touched |= set(repair_amazon_rules(catalogue, by_book, fallback)) | set(ensure_genre(catalogue, by_book, fallback))
    if today:
        for book in catalogue['libros']:
            if book['id'] in touched:
                book['fecha_actualizacion'] = today
    return repaired + sorted(touched - set(repaired))
