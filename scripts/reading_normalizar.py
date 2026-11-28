"""Normalización determinista de lo que la fuente trae «sucio»: se reescribe bien en el momento, no se bloquea.

23/11/2026: la carga se paraba (o el libro se apartaba un día entero) por cosas que se arreglan solas: un autor en
mayúsculas, un título en mojibake, un ISBN con guiones, una sinopsis con HTML o gritando, una URL http. Las reglas
estrictas se quedan como red de seguridad; esto corre ANTES de la cuarentena (REPAIRS) y solo apartará lo que de
verdad no tiene arreglo (sin título, sin autor, ISBN inválido, sin portada).

Cada función recibe el libro y devuelve cuántos campos cambió; todas son idempotentes. `normalizar(libros)` las pasa
todas. Se prueba con scripts/ensayo_carga.py (mutaciones por campo sobre libros reales).
"""
import html
import re
import unicodedata
from datetime import date

from reading_intake_core import clean_author, clean_title, strip_shouting
from reading_titles import fix_mojibake

LIGADURAS = {0xFB00: 'ff', 0xFB01: 'fi', 0xFB02: 'fl', 0xFB03: 'ffi', 0xFB04: 'ffl', 0xFB05: 'st', 0xFB06: 'st'}
TAG = re.compile(r'<[^>]+>')
SCRIPT = re.compile(r'<(script|style)\b.*?</\1>', re.I | re.S)
DMY = re.compile(r'^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$')
TITULO_MAX = 190  # se acorta a esto cuando pasa de 200
DESCRIPCION_MAX = 1200
URL_CAMPOS = ('portada_fuente_url', 'fuente_bibliografica_url', 'sinopsis_fuente_url')


def _set(book, key, value):
    if book.get(key) != value:
        book[key] = value
        return 1
    return 0


INVISIBLES = dict.fromkeys([0x200B, 0x2060, 0xFEFF, 0x00AD, *range(0x202A, 0x202F), *range(0x2066, 0x206A)])
ENTIDAD = re.compile(r'&(?:#\d+|#x[0-9a-f]+|[a-z]+);', re.I)


def texto_plano(value, parrafos=False):
    """Sin HTML, entidades ni espacios raros; NFC y ligaduras tipográficas a letras. Solo toca lo que lo necesita:
    un texto limpio sale idéntico (`parrafos` conserva los saltos de línea de las sinopsis)."""
    if '<' in value:
        value = html.unescape(TAG.sub(' ', SCRIPT.sub(' ', value)))
    elif ENTIDAD.search(value):
        value = html.unescape(value)
    value = fix_mojibake(unicodedata.normalize('NFC', value.translate(LIGADURAS).translate(INVISIBLES)))
    if parrafos:
        return '\n'.join(clean_title(linea) for linea in value.split('\n')).strip('\n ')
    return clean_title(value)


def recortar(value, limite):
    """Corta en límite de frase o de palabra sin pasarse de `limite`."""
    if len(value) <= limite:
        return value
    cut = value[:limite - 1]
    frase = max(cut.rfind('. '), cut.rfind('! '), cut.rfind('? '))
    if frase >= limite * 0.5:
        return cut[:frase + 1]
    return cut.rsplit(' ', 1)[0].rstrip(' ,;:-–—') + '…'


def normalizar_autores(book):
    autores = book.get('autores')
    if isinstance(autores, str):
        autores = [autores]
    if not isinstance(autores, list):
        return 0
    limpios = []
    for autor in autores:
        if not isinstance(autor, str):
            continue
        nombre = clean_author(texto_plano(autor))
        if nombre and nombre not in limpios:
            limpios.append(nombre)
    return _set(book, 'autores', limpios) if limpios else 0


def normalizar_titulo(book):
    titulo = book.get('titulo')
    if not isinstance(titulo, str) or not titulo.strip():
        return 0
    limpio = texto_plano(titulo)
    if len(limpio) > 200:  # el contrato admite hasta 200
        # Primero se quita el subtítulo; si aun así no cabe, corte por palabra.
        principal = re.split(r'\s[:\-–—]\s|:\s', limpio, maxsplit=1)[0].strip()
        limpio = principal if 12 <= len(principal) <= TITULO_MAX else recortar(limpio, TITULO_MAX)
    return _set(book, 'titulo', limpio)


def normalizar_isbn(book):
    isbn = book.get('isbn13')
    if isinstance(isbn, int):
        isbn = str(isbn)
    if not isinstance(isbn, str):
        return 0
    limpio = re.sub(r'[\s\-–]', '', isbn).upper()
    if re.fullmatch(r'\d{9}[\dX]', limpio) and isbn10_valido(limpio):  # ISBN-10 → ISBN-13 (prefijo 978)
        base = '978' + limpio[:9]
        limpio = base + str((10 - sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base)) % 10) % 10)
    return _set(book, 'isbn13', limpio) if re.fullmatch(r'\d{13}', limpio) else 0


def isbn10_valido(isbn):
    total = sum((10 - i) * (10 if c == 'X' else int(c)) for i, c in enumerate(isbn))
    return total % 11 == 0


def normalizar_fechas(book):
    cambios = 0
    for key in ('fecha_publicacion', 'fecha_verificacion', 'fecha_actualizacion', 'portada_fecha_revision'):
        valor = book.get(key)
        if isinstance(valor, int) and 19000101 <= valor <= 21001231:  # 20261123
            valor = f'{valor // 10000}-{valor // 100 % 100:02d}-{valor % 100:02d}'
            cambios += _set(book, key, valor)
        if isinstance(valor, str) and (m := DMY.match(valor.strip())):
            try:
                cambios += _set(book, key, date(int(m[3]), int(m[2]), int(m[1])).isoformat())
            except ValueError:
                pass  # fecha imposible (31/02): no se inventa, la cuarentena la aparta
    return cambios


def normalizar_urls(book):
    cambios = 0
    for key in URL_CAMPOS:
        valor = book.get(key)
        if isinstance(valor, str) and valor.startswith('http://'):
            cambios += _set(book, key, 'https://' + valor[len('http://'):])
    return cambios


def normalizar_sinopsis(book):
    cambios = 0
    for key, limite in (('descripcion_breve', DESCRIPCION_MAX), ('sinopsis_breve', 700), ('sinopsis_completa', 4500)):
        valor = book.get(key)
        if isinstance(valor, str):
            limpio = texto_plano(valor, parrafos=True)
            letras = [c for c in limpio if c.isalpha()]
            if letras and sum(c.isupper() for c in letras) / len(letras) > 0.6:  # gritada entera: solo entonces
                limpio = strip_shouting(limpio)
            limpio = recortar(limpio, limite)
            cambios += _set(book, key, limpio)
    return cambios


FUNCIONES = (normalizar_autores, normalizar_titulo, normalizar_isbn, normalizar_fechas, normalizar_urls,
             normalizar_sinopsis)


SUSTITUCION = '�'
PALABRA = re.compile(r'[^\W\d_]+')
PALABRA_ROTA = re.compile(rf'(?:[^\W\d_]|{SUSTITUCION})*{SUSTITUCION}(?:[^\W\d_]|{SUSTITUCION})*')
NO_ASCII = '[^\\W\\d_a-zA-Z]'  # la «�» de una decodificación fallida solo sustituye letras no ASCII


def _textos(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for item in valor.values():
            yield from _textos(item)
    elif isinstance(valor, list):
        for item in valor:
            yield from _textos(item)


def _reescribir(valor, cambiar):
    if isinstance(valor, str):
        return cambiar(valor)
    if isinstance(valor, dict):
        return {k: _reescribir(v, cambiar) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_reescribir(v, cambiar) for v in valor]
    return valor


def reparar_sustitucion(libros):
    """Rehace las palabras con «�» (U+FFFD) a partir del propio catálogo: «Fi�dor» → «Fiódor», «Bront�» → «Brontë».

    28/11/2026: Amazon trajo tres autores con la letra acentuada ya perdida («Fi�dor M. Dostoievski», «Plat�n») y
    la cuarentena los apartaba en cada carga, sin fin: la fuente no se corrige sola. La letra no se puede leer, pero
    el catálogo tiene la palabra bien escrita en otros libros. Cada «�» se prueba como una letra no ASCII y se
    acepta la palabra del vocabulario solo si es la única que encaja o dobla en apariciones a la siguiente; si no,
    se deja como está y el contrato «texto sin mojibake» sigue apartando el libro (red de seguridad).
    Devuelve el número de campos reescritos."""
    libros = [b for b in libros if isinstance(b, dict)]
    rotos = [b for b in libros if any(SUSTITUCION in t for t in _textos(b))]
    if not rotos:
        return 0
    vocabulario = {}
    for libro in libros:
        for texto in _textos(libro):
            for palabra in PALABRA.findall(texto):
                vocabulario[palabra] = vocabulario.get(palabra, 0) + 1
    elegidas = {}

    def elegir(rota):
        if rota not in elegidas:
            patron = re.compile(re.escape(rota).replace(re.escape(SUSTITUCION), NO_ASCII) + r'\Z')
            candidatas = sorted(((n, p) for p, n in vocabulario.items() if patron.match(p)), reverse=True)
            ok = rota.strip(SUSTITUCION) and candidatas and (len(candidatas) == 1 or candidatas[0][0] >= 2 * candidatas[1][0])
            elegidas[rota] = candidatas[0][1] if ok else rota
        return elegidas[rota]

    def cambiar(texto):
        return PALABRA_ROTA.sub(lambda m: elegir(m.group()), texto) if SUSTITUCION in texto else texto

    cambios = 0
    for libro in rotos:
        for clave, valor in list(libro.items()):
            nuevo = _reescribir(valor, cambiar)
            cambios += _set(libro, clave, nuevo)
    return cambios


def normalizar(libros):
    """Normaliza cada libro; devuelve el número de campos reescritos."""
    return sum(f(b) for b in libros if isinstance(b, dict) for f in FUNCIONES) + reparar_sustitucion(libros)
