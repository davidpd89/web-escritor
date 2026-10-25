"""Campanas: los hallazgos deterministas de la Via A (agrupados por causa y familia de paginas) entran en el flujo de correccion.

Antes se quedaban en 'a_triar' para siempre: el escaner veia defectos visibles (objetivos tactiles < 24 px en 33 paginas, meta descriptions cortas)
y nadie los corregia. Aqui cada grupo genera un test determinista que reproduce el defecto en sus paginas y se registra como causa aprobada de
prioridad 1; despues sigue el camino normal (reproduccion en main, desarrollo de Claude con el probador, validacion, lote, CI, fusion).
Solo contratos con plantilla de test: anadir uno = anadir una funcion a PLANTILLAS."""
import hashlib, json, re

MAX_URLS = 12


def _ruta_html(url):
    p = re.sub(r"^https?://[^/]+", "", url).lstrip("/")
    return (p + "index.html") if (not p or p.endswith("/")) else p


def _tactiles(h, urls):
    nombre = f"qa/campana-tactiles-{h['familia']}.mjs"
    js = f"""// Campana determinista (Via A): objetivos tactiles de al menos 24x24 px en movil (WCAG 2.2, 2.5.8). Familia: {h['familia']}.
import {{ chromium }} from 'playwright';
const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:8080';
const URLS = {json.dumps(urls)};
const browser = await chromium.launch();
const ctx = await browser.newContext({{ viewport: {{ width: 375, height: 720 }}, hasTouch: true }});
const fallos = [];
for (const u of URLS) {{
  const page = await ctx.newPage();
  await page.goto(ORIGIN + u, {{ waitUntil: 'load', timeout: 30000 }});
  await page.evaluate(() => document.fonts && document.fonts.ready);
  const peq = await page.evaluate(() => [...document.querySelectorAll('a[href],button,input,select,textarea,summary')].filter(e => {{
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return b.width > 1 && b.height > 1 && cs.visibility !== 'hidden' && cs.opacity !== '0' && e.tabIndex >= 0 && !e.closest('[aria-hidden="true"],[hidden],[inert]') && b.right > 0 && b.bottom > 0 && b.left < innerWidth && (b.width < 24 || b.height < 24) && !(e.tagName === 'A' && e.closest('p,li,span,td') && cs.display === 'inline');
  }}).slice(0, 5).map(e => {{ const b = e.getBoundingClientRect(); return `${{e.tagName.toLowerCase()}}.${{String(e.className).slice(0, 30)}} "${{(e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 25)}}" ${{Math.round(b.width)}}x${{Math.round(b.height)}}`; }}));
  if (peq.length) fallos.push(`${{u}}: ${{peq.join('; ')}}`);
  await page.close();
}}
await browser.close();
if (fallos.length) {{ console.error('FAIL objetivos tactiles < 24px en movil (WCAG 2.5.8):\\n' + fallos.join('\\n')); process.exit(1); }}
console.log(`PASS: ${{URLS.length}} paginas sin objetivos tactiles < 24px`);
"""
    criterio = (f"En movil (375 px) ningun enlace, boton o control de {len(urls)} paginas de la familia '{h['familia']}' mide menos de 24x24 px "
                f"(salvo enlaces en linea dentro de texto): corregirlo en el CSS o la plantilla compartida, no pagina a pagina. {nombre} pasa.")
    return nombre, js, criterio


def _meta_description(h, urls):
    nombre = f"tests/test-campana-meta-description-{h['familia']}.py"
    paginas = [_ruta_html(u) for u in urls]
    py = f'''"""Campana determinista (Via A): meta description entre 50 y 200 caracteres. Familia: {h['familia']}."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGINAS = {json.dumps(paginas)}
mal = []
for rel in PAGINAS:
    t = (ROOT / rel).read_text(encoding="utf-8")
    m = re.search(r"<meta[^>]+name=[\\"']description[\\"'][^>]*content=[\\"']([^\\"']*)", t, re.I) or re.search(r"<meta[^>]+content=[\\"']([^\\"']*)[\\"'][^>]*name=[\\"']description", t, re.I)
    n = len(m.group(1).strip()) if m else 0
    if not 50 <= n <= 200: mal.append(f"{{rel}}: {{n}} caracteres")
if mal:
    print("FAIL meta description fuera de 50-200 caracteres:\\n" + "\\n".join(mal)); sys.exit(1)
print(f"PASS: {{len(PAGINAS)}} paginas con meta description valida")
'''
    criterio = (f"Las {len(paginas)} paginas de '{h['familia']}' tienen meta description de 50-200 caracteres, unica y descriptiva; si las genera un "
                f"script, se corrige el generador o sus datos. {nombre} pasa.")
    return nombre, py, criterio

_CABECERA = '''import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
'''


def _estatica(h, urls, slug, titulo, cuerpo, criterio):
    """Plantilla estatica comun: recorre las paginas HTML de la familia y acumula 'mal'; cuerpo (indentado 4) opera sobre rel, t y mal."""
    nombre = f"tests/test-campana-{slug}-{h['familia']}.py"
    paginas = [_ruta_html(u) for u in urls]
    py = (f'"""Campana determinista (Via A): {titulo}. Familia: {h["familia"]}."""\n' + _CABECERA
          + f"PAGINAS = {json.dumps(paginas)}\nmal = []\n"
          + 'for rel in PAGINAS:\n    t = (ROOT / rel).read_text(encoding="utf-8")\n' + cuerpo
          + f'if mal:\n    print("FAIL {titulo}:\\n" + "\\n".join(mal[:50])); sys.exit(1)\n'
          + 'print(f"PASS: {len(PAGINAS)} paginas correctas")\n')
    return nombre, py, f"Las {len(paginas)} paginas de '{h['familia']}' cumplen: {titulo}; se corrige el generador o sus datos, no solo la salida. {nombre} pasa. " + criterio


_CUERPO_AXE = r'''    if not re.search(r"<html[^>]+lang=", t, re.I): mal.append(f"{rel}: <html> sin lang")
    for m in re.finditer(r"<img\b(?![^>]*\balt=)[^>]*>", t, re.I): mal.append(f"{rel}: img sin alt {m.group(0)[:80]}")
    for m in re.finditer(r"<button\b([^>]*)>\s*</button>", t, re.I):
        if "aria-label" not in m.group(1): mal.append(f"{rel}: button sin nombre accesible")
    if len(re.findall(r"<h1\b", t, re.I)) != 1: mal.append(f"{rel}: debe haber exactamente un h1")
'''

_CUERPO_LINKS = r'''    for href in re.findall(r"<a\b[^>]*\bhref=[\"']([^\"'#?]+)", t, re.I):
        if re.match(r"[a-z][a-z0-9+.-]*:|//", href, re.I): continue
        dest = (ROOT / href.lstrip("/")) if href.startswith("/") else (ROOT / rel).parent / href
        if dest.is_dir(): dest = dest / "index.html"
        if not dest.exists(): mal.append(f"{rel}: enlace roto {href}")
'''

_CUERPO_RESOURCES = r'''    for src in re.findall(r"<(?:img|script|source)\b[^>]*\bsrc=[\"']([^\"'#?]+)", t, re.I) + re.findall(r"<link\b[^>]*\bhref=[\"']([^\"'#?]+)", t, re.I):
        if re.match(r"[a-z][a-z0-9+.-]*:|//", src, re.I): continue
        dest = (ROOT / src.lstrip("/")) if src.startswith("/") else (ROOT / rel).parent / src
        if not dest.exists(): mal.append(f"{rel}: recurso inexistente {src}")
'''

_CUERPO_JSONLD = r'''    bloques = re.findall(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", t, re.I | re.S)
    if not bloques: mal.append(f"{rel}: sin JSON-LD")
    for b in bloques:
        try: d = json.loads(b)
        except ValueError as e: mal.append(f"{rel}: JSON-LD invalido ({e})"); continue
        for o in (d if isinstance(d, list) else [d]):
            if isinstance(o, dict) and "@graph" not in o and not (o.get("@context") and o.get("@type")): mal.append(f"{rel}: JSON-LD sin @context/@type")
'''


def _axe(h, urls):
    return _estatica(h, urls, "axe", "reglas axe estaticas (lang, alt, botones con nombre, un h1)", _CUERPO_AXE, "")


def _links(h, urls):
    return _estatica(h, urls, "enlaces", "enlaces internos que resuelven a un fichero existente", _CUERPO_LINKS, "")


def _resources(h, urls):
    return _estatica(h, urls, "recursos", "recursos locales (img, script, css) que existen", _CUERPO_RESOURCES, "")


def _jsonld(h, urls):
    return _estatica(h, urls, "jsonld", "JSON-LD valido con @context y @type", _CUERPO_JSONLD, "")


def _sitemap(h, urls):
    nombre = f"tests/test-campana-sitemap-{h['familia']}.py"
    rutas = [re.sub(r"^https?://[^/]+", "", u) or "/" for u in urls]
    py = f'''"""Campana determinista (Via A): las URLs de la familia {h['familia']} figuran en sitemap.xml."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUTAS = {json.dumps(rutas)}
sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
mal = [r for r in RUTAS if r not in sm]
if mal:
    print("FAIL URLs ausentes de sitemap.xml:\\n" + "\\n".join(mal)); sys.exit(1)
print(f"PASS: {{len(RUTAS)}} URLs en sitemap")
'''
    return nombre, py, f"Las {len(rutas)} URLs de '{h['familia']}' figuran en sitemap.xml (se corrige el generador del sitemap). {nombre} pasa."


PLANTILLAS = {"ux-objetivos-tactiles": _tactiles, "seo-description": _meta_description, "a11y-imagenes": _axe, "navegacion-enlaces": _links,
              "datos-jsonld": _jsonld, "seo-sitemap": _sitemap}


def sembrar(q, c, out=print):
    """Hallazgos a_triar con plantilla -> propuesta con su test + causa aprobada (prioridad 1). Idempotente: el hallazgo pasa a 'en_campana'."""
    import qa_triaje
    try: filas = c.execute("SELECT * FROM hallazgos WHERE estado='a_triar' ORDER BY paginas DESC").fetchall()
    except Exception: return 0
    n = 0
    for h in filas:
        gen = PLANTILLAS.get(h["contrato"])
        if not gen: continue
        urls = list(dict.fromkeys(json.loads(h["urls"] or "[]")))[:MAX_URLS]
        if not urls: continue
        ruta, contenido, criterio = gen(h, urls)
        datos = {"titulo": f"Campana {h['contrato']} en {h['familia']}", "zona": "campana", "familias": [h["familia"]], "tecnica": {"id": "campana-" + h["contrato"], "nombre": h["contrato"]},
                 "funcionalidad": h["causa"], "invariante": criterio, "categoria": "regresion", "ficheros_fuente": [], "ficheros_nuevos": [{"ruta": ruta, "contenido": contenido}],
                 "como_ejecutar": ("node " if ruta.endswith(".mjs") else "python ") + ruta, "workflow": None, "via": "campana"}
        huella = "campana:" + hashlib.sha1(f"{h['clave']}|{ruta}".encode()).hexdigest()[:16]
        c.execute("INSERT OR IGNORE INTO propuestas(huella,area,titulo,datos,estado,creado,actualizado,tecnica,funcionalidad) VALUES(?,?,?,?,?,?,?,?,?)",
                  (huella, "campana:" + h["contrato"], datos["titulo"], json.dumps(datos, ensure_ascii=False), "campana", q.now(), q.now(), datos["tecnica"]["id"], h["causa"]))
        pid = c.execute("SELECT id FROM propuestas WHERE huella=?", (huella,)).fetchone()[0]
        dec = {"decision": "corregir", "prioridad": 1, "causa_probable": h["causa"], "criterio_aceptacion": criterio, "archivos": [], "confianza": "alta",
               "justificacion": f"Defecto determinista de la Via A en {h['paginas']} paginas: {(h['ejemplos'] or '')[:300]}"}
        qa_triaje.guardar(c, q.now(), "campana:" + h["clave"], f"{h['causa']} ({h['paginas']} paginas de '{h['familia']}')", "defecto_web", [pid], [],
                          h["evidencia"] or "", datos["como_ejecutar"], criterio, "viaa", decision="corregir", prioridad="1", decision_json=json.dumps(dec, ensure_ascii=False))
        c.execute("UPDATE hallazgos SET estado='en_campana',nota=? WHERE clave=?", (f"causa campana:{h['clave']}", h["clave"]))
        c.commit(); n += 1
        out(f"  campana: {h['contrato']} en '{h['familia']}' ({h['paginas']} paginas) -> causa aprobada con test {ruta}")
    return n
