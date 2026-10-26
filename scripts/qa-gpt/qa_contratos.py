"""qa_contratos: Via A. Contratos deterministas parametrizados por familia de paginas (sin GPT, sin navegador).

Un contrato = una comprobacion reutilizable aplicada a TODAS las paginas de una familia. Los fallos se agrupan por
(contrato, causa, familia): 1 causa comun en 60 paginas es UN hallazgo con 60 ejemplos, no 60 incidencias.
Las aserciones NO se cuentan como tests: se informan por separado (paginas x contratos).
"""
import hashlib, json, re, time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse, urlsplit

SITE = "https://davidportodiaz.com"
FAMILIAS = {  # familia -> (glob bajo ROOT, cuantas paginas del piloto)
    "libros": ("recomendaciones/libros/*/index.html", 30),
    "autores": ("recomendaciones/autores/*/index.html", 25),
    "recomendaciones-editoriales": ("recomendaciones/editoriales/*/index.html", 15),
    "editoriales": ("editoriales/*/index.html", 30),
}
VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "track", "wbr"}


class Pagina(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None; self.metas = {}; self.canonical = None; self.lang = None; self.h = []; self.ids = []; self.links = []; self.imgs = []
        self.jsonld = []; self.landmarks = Counter(); self.sig = []; self._t = None; self._h = None; self._ld = False; self._txt = []; self.skip = False

    def handle_starttag(self, tag, a):
        a = dict(a); i = a.get("id")
        if i: self.ids.append(i)
        if tag == "html": self.lang = a.get("lang")
        elif tag == "title": self._t = []
        elif tag == "meta":
            k = a.get("name") or a.get("property")
            if k: self.metas[k.lower()] = a.get("content", "")
        elif tag == "link" and "canonical" in (a.get("rel") or "").lower().split(): self.canonical = a.get("href")
        elif tag in ("h1", "h2", "h3"): self._h = [tag, []]
        elif tag == "a" and a.get("href") is not None:
            self.links.append(a["href"])
            if "skip" in (a.get("class") or "") or (a["href"].startswith("#") and "contenido" in a["href"]): self.skip = True
        elif tag == "img": self.imgs.append(a)
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json": self._ld = True; self._txt = []
        if tag in ("main", "nav", "header", "footer", "article", "section", "aside"): self.landmarks[tag] += 1; self.sig.append(tag)
        if a.get("role") in ("main", "navigation", "banner", "contentinfo", "search") and a["role"] != {"main": "main", "nav": "navigation"}.get(tag): self.landmarks["role:" + a["role"]] += 1

    def handle_endtag(self, tag):
        if tag == "title" and self._t is not None: self.title = "".join(self._t).strip(); self._t = None
        elif tag in ("h1", "h2", "h3") and self._h: self.h.append((self._h[0], "".join(self._h[1]).strip())); self._h = None
        elif tag == "script" and self._ld: self.jsonld.append("".join(self._txt)); self._ld = False

    def handle_data(self, d):
        if self._t is not None: self._t.append(d)
        if self._h: self._h[1].append(d)
        if self._ld: self._txt.append(d)


def leer(root, ruta):
    p = Pagina(); p.feed(Path(ruta).read_text(encoding="utf-8", errors="replace")); return p


def url_de(root, ruta):
    rel = Path(ruta).relative_to(root).as_posix()
    return f"{SITE}/{rel[:-len('index.html')]}" if rel.endswith("index.html") else f"{SITE}/{rel}"


def existe(root, href):
    """href interno ('/x/y/', '/x.css', relativo) -> existe fichero o carpeta con index.html."""
    path = unquote(urlparse(href).path)
    if not path.startswith("/"): return None  # relativo: lo resuelve el llamador
    base = Path(root).resolve(); t = (base / path.lstrip("/")).resolve()
    if not t.is_relative_to(base): return False  # '/../x' no puede validar ficheros fuera del sitio
    return t.is_file() or (t / "index.html").is_file()


def tipos_jsonld(p):
    out, malos = [], 0
    for raw in p.jsonld:
        try: d = json.loads(raw)
        except ValueError: malos += 1; continue
        nodos = d.get("@graph", [d]) if isinstance(d, dict) else d
        if not isinstance(nodos, list): malos += 1; continue  # raiz escalar o @graph mal tipado: bloque invalido, no aborta
        for n in nodos:
            if isinstance(n, dict):
                t = n.get("@type"); out += t if isinstance(t, list) else [t]
    return out, malos


# --------- contratos: (id, descripcion, funcion(ctx) -> lista de (causa, detalle)) ---------
def c_title(c):
    t = c["p"].title
    if not t: return [("sin <title>", "")]
    return [("title fuera de 10-75 caracteres", f"{len(t)}c")] if not 10 <= len(t) <= 75 else []

def c_description(c):
    d = c["p"].metas.get("description", "")
    if not d: return [("sin meta description", "")]
    return [("meta description fuera de 50-200 caracteres", f"{len(d)}c")] if not 50 <= len(d) <= 200 else []

def c_canonical(c):
    k, esp = c["p"].canonical, c["url"]
    if not k: return [("sin canonical", "")]
    if k.rstrip("/") != esp.rstrip("/"): return [("canonical distinto de la URL de la pagina", f"{k} != {esp}")]
    return []

def c_h1(c):
    n = sum(1 for t, _ in c["p"].h if t == "h1")
    return [(f"{n} <h1> (debe haber 1)", "")] if n != 1 else []

def c_idioma_viewport(c):
    out = []
    if not c["p"].lang: out.append(("<html> sin lang", ""))
    if "viewport" not in c["p"].metas: out.append(("sin meta viewport", ""))
    return out

def c_robots(c):
    r = c["p"].metas.get("robots", "")
    return [("sin meta robots", "")] if not r else ([("noindex en pagina que esta en el sitemap", r)] if "noindex" in r and c["en_sitemap"] else [])

def c_jsonld(c):
    tipos, malos = tipos_jsonld(c["p"]); out = [("JSON-LD no parsea", f"{malos} bloque(s)")] if malos else []
    if not tipos and not malos: out.append(("sin JSON-LD", ""))
    return out

def c_social(c):
    m, out = c["p"].metas, []
    for k in ("og:title", "og:description", "og:image", "og:url"):
        if not m.get(k): out.append((f"falta {k}", ""))
    if m.get("og:url") and c["p"].canonical and m["og:url"].rstrip("/") != c["p"].canonical.rstrip("/"): out.append(("og:url distinto del canonical", m["og:url"]))
    return out

def c_imagenes(c):
    out = []
    for im in c["p"].imgs:
        if im.get("alt") is None: out.append(("<img> sin atributo alt", im.get("src", "")[:60]))
        s = im.get("src") or ""
        if s.startswith("/") and existe(c["root"], s) is False: out.append(("imagen interna inexistente", s[:80]))
    return out

def c_enlaces(c):
    out, base = [], Path(c["ruta"]).parent
    for h in c["p"].links:
        if not h or h.startswith(("#", "mailto:", "tel:", "javascript:", "http:", "https:", "//", "data:")): continue
        e = existe(c["root"], h)
        if e is None:
            t = (base / unquote(urlparse(h).path)); e = t.is_file() or (t / "index.html").is_file()
        if not e: out.append(("enlace interno roto", h[:80]))
    ids = set(c["p"].ids)
    for h in c["p"].links:
        if h.startswith("#") and len(h) > 1 and h[1:] not in ids and unquote(h[1:]) not in ids: out.append(("ancla interna sin destino", h))
    return out

def c_landmarks(c):
    l, out = c["p"].landmarks, []
    if l["main"] + l["role:main"] != 1: out.append((f"{l['main'] + l['role:main']} landmarks main (debe haber 1)", ""))
    if not (l["nav"] or l["role:navigation"]): out.append(("sin navegacion (<nav>)", ""))
    return out

def c_ids_unicos(c):
    d = [i for i, n in Counter(c["p"].ids).items() if n > 1]
    return [("ids duplicados", ", ".join(d[:3]))] if d else []

def c_encabezados(c):
    niv, out, prev = [int(t[1]) for t, _ in c["p"].h], [], 0
    for n in niv:
        if prev and n > prev + 1: out.append(("salto de nivel de encabezado", f"h{prev}->h{n}")); break
        prev = n
    return out

def c_sitemap(c): return [] if c["en_sitemap"] else [("no esta en ningun sitemap", c["url"])]

CONTRATOS = [("seo-title", "title presente y de longitud razonable", c_title), ("seo-description", "meta description 50-200c", c_description),
             ("seo-canonical", "canonical = URL de la pagina", c_canonical), ("estructura-h1", "un unico h1", c_h1),
             ("estructura-idioma-viewport", "lang y viewport", c_idioma_viewport), ("seo-robots-sitemap", "robots coherente con el sitemap", c_robots),
             ("datos-jsonld", "JSON-LD valido", c_jsonld), ("seo-social", "Open Graph completo y coherente", c_social),
             ("a11y-imagenes", "alt e imagenes existentes", c_imagenes), ("navegacion-enlaces", "enlaces y anclas internos resuelven", c_enlaces),
             ("a11y-landmarks", "un main y una nav", c_landmarks), ("estructura-ids", "ids unicos", c_ids_unicos),
             ("a11y-encabezados", "sin saltos de nivel", c_encabezados), ("seo-sitemap", "la pagina esta en un sitemap", c_sitemap)]


def homogeneidad(paginas):
    """Contrato comparativo: huella estructural (landmarks + niveles de encabezado + tipos JSON-LD) frente a la mayoria de la familia."""
    huellas = {}
    for fam, ps in paginas.items():
        for c in ps:
            tipos, _ = tipos_jsonld(c["p"])
            huellas[c["ruta"]] = (fam, hashlib.sha1(json.dumps([sorted(k for k in c["p"].landmarks if k != "section"), [t for t, _ in c["p"].h][:6], sorted(t for t in tipos if t)]).encode()).hexdigest()[:8], tuple(sorted(t for t in tipos if t)))
    out = []
    for fam in paginas:
        cnt = Counter(h[1] for r, h in huellas.items() if h[0] == fam)
        if not cnt: continue
        comun, n = cnt.most_common(1)[0]
        for c in paginas[fam]:
            f = huellas[c["ruta"]]
            if f[1] != comun and n / len(paginas[fam]) >= 0.5: out.append((fam, c, "estructura distinta de la plantilla mayoritaria", f"huella {f[1]} vs {comun} ({n}/{len(paginas[fam])})"))
    return out


def muestra(root, glob_pat, n):
    todas = sorted(Path(root).glob(glob_pat))
    if len(todas) <= n: return todas
    paso = len(todas) / n; return [todas[int(i * paso)] for i in range(n)]  # reparto uniforme y determinista


def sitemap_urls(root):
    urls = set()
    for f in Path(root).glob("*sitemap*.xml"):
        try: urls |= {(e.text or "").strip() for e in ET.parse(f).iter() if isinstance(e.tag, str) and e.tag.rsplit("}", 1)[-1] == "loc"}  # namespaces/prefijos y entidades
        except (ET.ParseError, OSError): urls |= set(re.findall(r"<(?:\w+:)?loc>([^<]+)</(?:\w+:)?loc>", f.read_text(encoding="utf-8", errors="replace")))
    return {u.rstrip("/") for u in urls if u}


def familia_de(url):
    """Familia de contrato segun la ruta: paginas que realmente comparten plantilla. Los indices/hubs y el resto van aparte."""
    r = urlparse(url).path.strip("/").split("/")
    if r[0] == "recomendaciones" and len(r) == 3 and r[1] in ("libros", "autores", "editoriales"): return {"libros": "libros", "autores": "autores", "editoriales": "recomendaciones-editoriales"}[r[1]]
    if r[0] == "editoriales" and len(r) >= 2: return "editoriales"
    if r[0] == "cuaderno" and len(r) >= 2: return "cuaderno"
    if r[0] == "herramientas" and len(r) >= 2: return "herramientas"
    return "generales"


def paginas_del_sitio(root):
    """Todas las paginas HTML listadas en los sitemaps que existen en disco -> {familia: [rutas]} (determinista)."""
    root = Path(root); fams = defaultdict(list)
    propio = urlsplit(SITE)
    for u in sorted(sitemap_urls(root)):
        s = urlsplit(u)
        if (s.scheme, s.netloc.lower()) != (propio.scheme, propio.netloc): continue  # URLs de otros dominios no son paginas del sitio
        path = unquote(urlparse(u).path).lstrip("/")
        f = root / path / "index.html" if (not path or path.endswith("/") or "." not in path.rsplit("/", 1)[-1]) else root / path
        if f.is_file() and f.suffix == ".html": fams[familia_de(u)].append(f)
    return dict(fams)


def ejecutar(root, familias=FAMILIAS, contratos=CONTRATOS):
    return correr(root, {fam: muestra(root, pat, n) for fam, (pat, n) in familias.items()}, contratos)


def ejecutar_sitio(root, contratos=CONTRATOS):
    """Cobertura completa: todas las paginas aplicables del sitemap, por familia."""
    return correr(root, paginas_del_sitio(root), contratos)


def correr(root, rutas_por_familia, contratos=CONTRATOS):
    t0 = time.time(); root = Path(root); sm = sitemap_urls(root); paginas = {}; fallos = defaultdict(list); aserciones = 0
    for fam, rutas in rutas_por_familia.items():
        paginas[fam] = []
        for ruta in rutas:
            p = leer(root, ruta); url = url_de(root, ruta)
            paginas[fam].append({"p": p, "ruta": ruta, "url": url, "root": root, "en_sitemap": url.rstrip("/") in sm})
    for fam, ps in paginas.items():
        for c in ps:
            for cid, _, fn in contratos:
                aserciones += 1
                for causa, det in fn(c): fallos[(cid, causa, fam)].append((c["url"], det))
    comparables = {f: v for f, v in paginas.items() if f != "generales" and len(v) >= 8}
    for fam, c, causa, det in homogeneidad(comparables): aserciones += 1; fallos[("homogeneidad-plantilla", causa, fam)].append((c["url"], det))
    grupos = [{"contrato": k[0], "causa": k[1], "familia": k[2], "paginas": len({u for u, _ in v}), "urls": sorted({u for u, _ in v}), "ejemplos": [f"{u} {d}".strip() for u, d in v[:3]]} for k, v in fallos.items()]
    grupos.sort(key=lambda g: -g["paginas"])
    n_pag = sum(len(v) for v in paginas.values())
    return {"segundos": round(time.time() - t0, 2), "paginas": n_pag, "familias": {f: len(v) for f, v in paginas.items()}, "contratos": len(contratos) + 1,
            "aserciones": aserciones, "fallos_brutos": sum(len(v) for v in fallos.values()), "fallos_unicos": len(grupos), "grupos": grupos}


def informe(res, max_grupos=40):
    L = [f"Via A: {res['contratos']} contratos x {res['paginas']} paginas ({', '.join(f'{k} {v}' for k, v in res['familias'].items())}) en {res['segundos']} s, sin navegador ni GPT.",
         f"{res['aserciones']} aserciones (NO son tests independientes) -> {res['fallos_brutos']} fallos brutos -> {res['fallos_unicos']} hallazgos unicos tras agrupar por causa y familia.", ""]
    for g in res["grupos"][:max_grupos]:
        L.append(f"- [{g['contrato']}] {g['causa']} | {g['familia']} | {g['paginas']} pag. | ej: {g['ejemplos'][0]}")
    if len(res["grupos"]) > max_grupos: L.append(f"... y {len(res['grupos']) - max_grupos} grupos mas (ver JSON)")
    return "\n".join(L)
