"""Normalización común de títulos para todas las fuentes del catálogo (Amazon, todostuslibros, editoriales)."""
from __future__ import annotations

import re

from reading_ratings_refresh import key


ARTICLE_AT_END = re.compile(r'^(.+?),\s*(el|la|los|las|lo|un|una|unos|unas)$', re.I)
ROMAN = re.compile(r'^(?=[ivxlc]+$)c{0,3}(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})$', re.I)
SHORT_WORDS = set('de la el en un mi tu su se no lo le al es me te si ya yo ni os ha he oh ay ti da ve va'.split())
SENTENCE_START = re.compile(r'(^|[.:!?¡¿«"(]\s*)(\w)')


SHOUT_SHARE = 0.7


def is_shouted(word):
    """Palabra de dos o más letras escrita entera en mayúsculas («MICROBIOS», «II», «IA»)."""
    letters = [c for c in word if c.isalpha() and c not in 'ªº']
    return len(letters) >= 2 and all(c.isupper() for c in letters)


TRAILING_GROUP = re.compile(r'\s*\([^()]*\)\s*$')


def is_shouting(title):
    """Título entero en mayúsculas, o casi: Amazon añade la colección o «Vol.» en minúscula a uno gritado.
    La colección entre paréntesis del final no cuenta: «NI ORIENTE NI OCCIDENTE (Andalucía)»."""
    core = title
    while TRAILING_GROUP.search(core) and TRAILING_GROUP.sub('', core).strip():
        core = TRAILING_GROUP.sub('', core)
    if sum(c.isalpha() for c in core) >= 4:
        title = core
    letters = sum(c.isalpha() for c in title)
    shouted = sum(c.isalpha() for w in title.split(' ') if is_shouted(w) for c in w)
    return letters >= 4 and shouted >= SHOUT_SHARE * letters


class ProperWords(dict):
    """Forma escrita de cada nombre propio conocido; `names` son los que solo salen en nombres de autor."""

    def __init__(self, *args, names=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.names = set(names)


def title_case(words):
    """Título en estilo inglés (Mayúscula En Cada Palabra): sus mayúsculas no distinguen nombres propios."""
    return len(words) >= 3 and sum(w[:1].isupper() for w in words) * 2 > len(words)


def proper_words(catalogue):
    """Palabras que el catálogo escribe con mayúscula en mitad de un título o en un nombre: «Lorca», «Dios»."""
    # Solo cuenta una palabra que el catálogo nunca escribe en minúscula: así «Al», «De» o «The» no se cuelan.
    # Los títulos gritados, los de estilo inglés y la traducción tras « / » no dicen nada de mayúsculas.
    upper, lower = {}, set()
    for book in catalogue['libros']:
        title = book.get('titulo', '').split(' / ')[0]
        if title.upper() == title or is_shouting(title):
            continue
        words = re.findall(r'(?<=[\w,;] )\w+', title)
        if title_case(words):
            continue
        for word in words:
            if word[:1].isupper() and (not word.isupper() or 3 <= len(word) <= 6):
                upper.setdefault(key(word), word)  # nombre propio, o sigla escrita así fuera de mayúsculas: ONU
            elif word.islower():
                lower.add(key(word))
    names = {}
    for book in catalogue['libros']:
        for name in book.get('autores', []):
            if name.upper() != name:
                for word in name.split():
                    if word[:1].isupper() and word.isalpha() and len(word) > 2:
                        names.setdefault(key(word), word)
    found = {k: v for k, v in {**names, **upper}.items() if k not in lower and len(k) > 2}
    # Un apellido suelto («Ruta», «Guerrero», «Ángeles») también es una palabra común: solo vale en un nombre.
    return ProperWords(found, names=set(found) - set(upper))


def tidy_title(title, proper=None):
    """Título entero (o casi) en mayúsculas → mayúscula inicial (norma del español), con los nombres propios
    que el catálogo ya conoce y los numerales romanos; el artículo pospuesto de catálogo («MUNDO, EL») vuelve
    delante."""
    proper = proper or {}
    names = getattr(proper, 'names', set())
    if is_shouting(title):
        words = []
        parts = title.split(' ')
        cores = [re.sub(r'^\W+|\W+$', '', w) for w in parts]

        def known(i):
            return 0 <= i < len(cores) and cores[i] and key(cores[i]) in proper

        for i, (word, core) in enumerate(zip(parts, cores)):
            if not core.isupper():
                words.append(word)  # lo que ya viene en minúscula o mixto se respeta: «Vol.», «Nº», «(Andalucía)»
            elif core and ROMAN.match(core) and len(core) <= 4 and core.lower() not in {'mi', 'di', 'li', 'ci'}:
                words.append(word)
            elif len(core) == 2 and core.isalpha() and core.lower() not in SHORT_WORDS:
                words.append(word)  # sigla: IA, UE, TV
            elif known(i) and (key(core) not in names or known(i - 1) or known(i + 1)):
                form = proper[key(core)]
                if form.lower() != core.lower():
                    form = core[:1] + core[1:].lower()  # las tildes de la fuente: «AGUSTÍN», no «Agustin»
                words.append(word.replace(core, form))
            else:
                words.append(word.lower())
        title = SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), ' '.join(words))
    moved = ARTICLE_AT_END.match(title)
    if moved:
        rest = moved.group(1)
        if key(rest.split(' ')[0]) not in proper:
            rest = rest[:1].lower() + rest[1:]
        title = moved.group(2).capitalize() + ' ' + rest
    return title
