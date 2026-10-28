"""dedupe: deduplicacion de mejoras por NECESIDAD y COMPORTAMIENTO, no por URL ni por titulo.

Dos expedientes son la misma mejora si cubren la misma necesidad del lector/editor (texto normalizado, similitud de conjuntos de conceptos) o si
producen el mismo comportamiento observable (mismos ficheros objetivo + criterio de aceptacion equivalente). La URL de la fuente no cuenta: dos
fuentes distintas pueden respaldar la misma mejora, y una misma fuente puede respaldar mejoras distintas.
Solo stdlib y funciones puras: se prueba sin base de datos ni red.
"""
import hashlib, re, unicodedata

STOP = set("""a al algo ante con contra cual cuando de del desde donde el ella en entre es esta este esto la las lo los mas me mi muy no nos o para pero por que
se si sin sobre su sus tambien tiene todo un una uno unos y ya the and for with that this from into your are was were will can has have not but
usar usa uso mejorar mejora mejoras anadir agregar permitir sitio pagina paginas web""".split())
SUFIJOS = ("amientos", "imientos", "aciones", "iciones", "amiento", "imiento", "acion", "icion", "mente", "adores", "adoras", "ables", "ibles", "ando", "iendo",
           "ados", "adas", "idos", "idas", "ador", "adora", "ar", "er", "ir", "es", "os", "as", "s")


def _sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def raiz(palabra):
    """Raiz muy simple (plural, sufijo comun, vocal final): 'filtros' == 'filtro' == 'filtr', 'lectores' == 'lector'. Suficiente para comparar conjuntos de conceptos."""
    if len(palabra) > 4 and palabra.endswith("s"): palabra = palabra[:-1]
    for s in SUFIJOS:
        if len(palabra) - len(s) >= 4 and palabra.endswith(s): palabra = palabra[:-len(s)]; break
    if len(palabra) > 4 and palabra[-1] in "aeo": palabra = palabra[:-1]
    return palabra


def conceptos(texto):
    """Conjunto de raices significativas del texto (sin acentos, sin palabras vacias, sin numeros sueltos)."""
    t = _sin_acentos((texto or "").lower())
    return {raiz(p) for p in re.findall(r"[a-z0-9]{3,}", t) if p not in STOP and not p.isdigit()}


def jaccard(a, b):
    """Mezcla de Jaccard y coeficiente de solapamiento (|A&B|/min): dos redacciones de la misma necesidad de distinta longitud siguen puntuando alto."""
    if not a or not b: return 0.0
    inter = len(a & b)
    return 0.5 * inter / len(a | b) + 0.5 * inter / min(len(a), len(b))


def huella(conjunto):
    return hashlib.sha1("|".join(sorted(conjunto)).encode("utf-8")).hexdigest()[:16]


def huella_necesidad(necesidad):
    return huella(conceptos(necesidad))


def _ruta_clave(ruta):
    r = (ruta or "").strip().lower().replace("\\", "/").lstrip("./")
    return r.rstrip("/")


def huella_comportamiento(archivos, criterio):
    """Mismo conjunto de ficheros objetivo + mismo criterio (por conceptos) = mismo comportamiento."""
    rutas = sorted({_ruta_clave(a) for a in (archivos or []) if a})
    return hashlib.sha1((",".join(rutas) + "#" + huella(conceptos(criterio))).encode("utf-8")).hexdigest()[:16]


def similitud(a, b):
    """a, b: dicts con necesidad, criterio, archivos. -> (puntuacion 0..1, motivo)."""
    ca, cb = conceptos(a.get("necesidad", "") + " " + a.get("titulo", "")), conceptos(b.get("necesidad", "") + " " + b.get("titulo", ""))
    nec = jaccard(ca, cb)
    ra, rb = {_ruta_clave(x) for x in a.get("archivos") or [] if x}, {_ruta_clave(x) for x in b.get("archivos") or [] if x}
    crit = jaccard(conceptos(a.get("criterio", "")), conceptos(b.get("criterio", "")))
    mismo_archivo = jaccard(ra, rb)
    comp = 0.5 * mismo_archivo + 0.5 * crit if ra and rb else crit * 0.5
    puntos = max(nec, comp)
    motivo = "misma necesidad" if nec >= comp else "mismo comportamiento"
    return puntos, motivo


UMBRAL_NECESIDAD = 0.55
UMBRAL_COMPORTAMIENTO = 0.6


def buscar_duplicado(candidato, existentes, umbral_nec=UMBRAL_NECESIDAD, umbral_comp=UMBRAL_COMPORTAMIENTO):
    """-> (id_existente, motivo, puntuacion) o None. `existentes`: iterable de dicts con id + los campos de `similitud`.
    Huella exacta primero (barata); despues similitud difusa. Nunca compara con el propio id."""
    hn = huella_necesidad(candidato.get("necesidad", ""))
    hc = huella_comportamiento(candidato.get("archivos"), candidato.get("criterio", ""))
    mejor = None
    for e in existentes:
        if e.get("id") == candidato.get("id"): continue
        if e.get("h_necesidad") and e["h_necesidad"] == hn and conceptos(candidato.get("necesidad", "")): return e["id"], "misma necesidad (huella exacta)", 1.0
        if e.get("h_comportamiento") and e["h_comportamiento"] == hc and candidato.get("archivos"): return e["id"], "mismo comportamiento (huella exacta)", 1.0
        p, motivo = similitud(candidato, e)
        umbral = umbral_nec if motivo == "misma necesidad" else umbral_comp
        if p >= umbral and (mejor is None or p > mejor[2]): mejor = (e["id"], motivo, round(p, 2))
    return mejor
