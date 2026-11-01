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
    (r'\bfantasia\b|\bmagia\b|\bdragon', 'fantasia', 'Fantasía', 'genero'),
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
