#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto  # noqa: E402
from datetime import datetime
from html import escape
from urllib.parse import urlparse

ALLOWED_STAGES={"planificacion","escritura","revision","estadisticas","maquetacion","exportacion","epub","validacion","impresion","marketing","distribucion"}
# Los slugs de arriba son valores tecnicos: viajan en data-stages y es lo que
# filtra writer-tools.js. Pero tambien se pintaban tal cual como etiquetas
# visibles, asi que la ficha mostraba "planificacion / revision / maquetacion"
# justo debajo de un desplegable que ya decia "Planificacion / Revision /
# Maquetacion" bien acentuado. El dato sigue siendo el slug; lo que se lee, no.
PAGE_TITLE="Herramientas para escritores: directorio verificado | David Porto Díaz"
DESCRIPTION=("Directorio editorial de herramientas para escritores: precio, plataforma, "
             "privacidad, idioma, para qué sirve y para qué no, con fuentes y fecha de verificación.")
CANONICAL="https://davidportodiaz.com/recursos/herramientas-para-escritores/"
# Las etiquetas Open Graph / Twitter estaban escritas a mano en el HTML
# generado, no aqui: la primera regeneracion del fichero se las llevo por
# delante. Viven en el builder para que no vuelva a pasar.
SHARE_IMAGE="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp"
SHARE_IMAGE_WIDTH=1731
SHARE_IMAGE_HEIGHT=909

STAGE_LABELS={
    "planificacion":"Planificación","escritura":"Escritura","revision":"Revisión",
    "estadisticas":"Estadísticas","maquetacion":"Maquetación","exportacion":"Exportación",
    "epub":"EPUB","validacion":"Validación","impresion":"Impresión",
    "marketing":"Marketing","distribucion":"Distribución",
}
ALLOWED_STATUS={"active","monitor","deprecated"}
ALLOWED_PRICE={"gratis-open-source","gratis","freemium","suscripcion","pago-unico","variable"}
SLUG_RE=re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def fail(msg): raise ValueError(msg)
def is_https(url):
    try:
        p=urlparse(url); return p.scheme=="https" and bool(p.netloc)
    except Exception: return False

def validate(data):
    if data.get("schema_version")!=1: fail("schema_version debe ser 1")
    tools=data.get("tools")
    if not isinstance(tools,list) or len(tools)<3: fail("Se requieren al menos 3 herramientas")
    seen=set()
    for i,t in enumerate(tools,1):
        p=f"tools[{i}]"; slug=t.get("slug","")
        if not SLUG_RE.match(slug): fail(f"{p}: slug inválido")
        if slug in seen: fail(f"{p}: slug duplicado {slug}")
        seen.add(slug)
        if not t.get("name"): fail(f"{p}: falta name")
        if not is_https(t.get("website","")): fail(f"{p}: website debe ser HTTPS")
        stages=t.get("stages",[])
        if not stages or any(s not in ALLOWED_STAGES for s in stages): fail(f"{p}: stages inválidos")
        price=t.get("price",{})
        if price.get("model") not in ALLOWED_PRICE: fail(f"{p}: price.model inválido")
        if not price.get("display") or not is_https(price.get("source","")): fail(f"{p}: precio sin texto o fuente HTTPS")
        ver=t.get("verification",{})
        try: datetime.strptime(ver.get("checked_at",""),"%Y-%m-%d")
        except Exception: fail(f"{p}: verification.checked_at inválido")
        sources=ver.get("sources",[])
        if not sources or any(not is_https(u) for u in sources): fail(f"{p}: verification.sources inválidas")
        if ver.get("hands_on") is True and len((ver.get("test_notes") or "").strip())<40: fail(f"{p}: hands_on exige test_notes sustanciales")
        if t.get("affiliate") not in (False,True): fail(f"{p}: affiliate debe ser booleano")
        if t.get("affiliate") is True and not t.get("affiliate_disclosure"): fail(f"{p}: afiliación sin disclosure")
        if t.get("status") not in ALLOWED_STATUS: fail(f"{p}: status inválido")
        if {"rating","score","stars","rank"}.intersection(t.keys()): fail(f"{p}: no se permiten ratings/rankings numéricos")
    return True

def pill(text): return f'<span class="editorial-genre">{escape(str(text))}</span>'

def render_tool(t):
    stages=" ".join(t["stages"])
    localish=t["data_mode"] in ("local","local-con-sync-opcional","desktop")
    es=str(t["interface_es"]).startswith("sí")
    tested=t["verification"].get("hands_on") is True
    tested_label="Probado directamente" if tested else "Verificado documentalmente"
    sources="".join(f'<li><a href="{escape(u)}" target="_blank" rel="noopener noreferrer">Fuente {n}</a></li>' for n,u in enumerate(t["verification"]["sources"],1))
    return f'''
<article class="id-card wt-card" data-name="{escape(t["name"].lower())}" data-stages="{escape(stages)}" data-price="{escape(t["price"]["model"])}" data-local="{"1" if localish else "0"}" data-spanish="{"1" if es else "0"}" data-account="{"0" if t["account_required"] is False else "1" if t["account_required"] is True else "unknown"}">
<div class="editorial-card__head"><div><p class="tool-meta">{escape(tested_label)}</p><h2>{escape(t["name"])}</h2></div><span class="editorial-verified">Verificado {escape(t["verification"]["checked_at"])}</span></div>
<div class="editorial-genres">{''.join(pill(STAGE_LABELS.get(x, x)) for x in t["stages"])}</div>
<dl class="spec-ledger">
<div><dt>Precio</dt><dd>{escape(t["price"]["display"])}</dd></div>
<div><dt>Plataformas</dt><dd>{escape(", ".join(t["platforms"]))}</dd></div>
<div><dt>Datos</dt><dd>{escape(t["data_note"])}</dd></div>
<div><dt>Interfaz en español</dt><dd>{escape(str(t["interface_es"]))}</dd></div>
</dl>
<div class="tool-findings-block"><h3>Para qué sí</h3><p>{escape(t["best_for"])}</p></div>
<div class="tool-findings-block"><h3>Para qué no</h3><p>{escape(t["not_for"])}</p></div>
<p>{escape(t["editorial_note"])}</p>
<details><summary>Fuentes y verificación</summary><ul class="tool-source-list">{sources}</ul></details>
<div class="id-card__actions"><a class="text-action" href="{escape(t["website"])}" target="_blank" rel="noopener noreferrer">Web oficial</a></div>
</article>'''

def render(data):
    cards="\n".join(render_tool(t) for t in data["tools"] if t["status"]!="deprecated")
    count=sum(1 for t in data["tools"] if t["status"]!="deprecated")
    checked=data["methodology"]["checked_at"]
    schema=json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage","name":PAGE_TITLE,
        "url":CANONICAL,"description":DESCRIPTION,"inLanguage":"es",
        "isPartOf":{"@id":"https://davidportodiaz.com/#website"},
        "author":{"@id":"https://davidportodiaz.com/#author"},
    },ensure_ascii=False,separators=(",",":"))
    return f'''<!DOCTYPE html>
<html lang="es" class="v1">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <title>{PAGE_TITLE}</title>
  <meta name="description" content="{DESCRIPTION}">
  <meta property="og:title" content="{PAGE_TITLE}">
  <meta property="og:description" content="{DESCRIPTION}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{CANONICAL}">
  <meta property="og:image" content="{SHARE_IMAGE}">
  <meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}">
  <meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}">
  <meta property="og:image:alt" content="{PAGE_TITLE}">
  <meta property="og:locale" content="es_ES">
  <meta property="og:site_name" content="David Porto Díaz">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{PAGE_TITLE}">
  <meta name="twitter:description" content="{DESCRIPTION}">
  <meta name="twitter:image" content="{SHARE_IMAGE}">
  <meta name="twitter:image:alt" content="{PAGE_TITLE}">
  <meta name="theme-color" content="#F4EFE7" />
  <link rel="canonical" href="{CANONICAL}" />
  <link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />
  <link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />
  <link rel="manifest" href="/manifest.json" />

  <link rel="stylesheet" href="/assets/v1-fonts.css" />
  <link rel="stylesheet" href="/assets/v1-tokens.css" />
  <link rel="stylesheet" href="/assets/v1-base.css" />
  <link rel="stylesheet" href="/assets/v1-shell.css" />
  <link rel="stylesheet" href="/assets/v1-components.css" />
  <link rel="stylesheet" href="/assets/v1-families.css" />
  <link rel="stylesheet" href="/assets/v1-tools.css" />
  <link rel="stylesheet" href="/assets/editoriales.css" />
  <link rel="stylesheet" href="/assets/writer-tools.css" />
  <script type="application/ld+json">{schema}</script>
</head>

<body>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>

  <header class="site-header" data-header>
    <div class="site-header__inner">
      <a class="brand" href="/" aria-label="David Porto Díaz — inicio">
        <span class="brand__name">David Porto Díaz</span>
        <span class="brand__role">Escritor</span>
      </a>
      <nav class="primary-nav" aria-label="Navegación principal">
        <a href="/libros/">Obra</a>
        <a href="/cuaderno/">Cuaderno</a>
        <a href="/herramientas/">Herramientas</a>
      </nav>
      <button class="explore-trigger" type="button" aria-haspopup="dialog" aria-controls="explore-dialog" aria-expanded="false" data-explore-open>
        Explorar
      </button>
    </div>
  </header>

  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog>
    <div class="explore-dialog__shell">
      <div class="explore-dialog__head">
        <div>
          <p class="eyebrow">Índice general</p>
          <h2 id="explore-title">Explorar</h2>
        </div>
        <button class="icon-button" type="button" aria-label="Cerrar Explorar" data-explore-close>
          <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path d="M5 5l14 14M19 5L5 19"/></svg>
        </button>
      </div>

      <div class="explore-dialog__grid">
        <nav class="explore-list" aria-label="Destinos de la web">
          <a class="explore-row" href="/las-manecillas-del-recuerdo/" data-preview="manecillas">
            <span class="explore-row__index">01</span>
            <span class="explore-row__body"><strong>Las manecillas del recuerdo</strong><small>La obra actual.</small></span>
          </a>
          <a class="explore-row" href="/autor.html" data-preview="autor">
            <span class="explore-row__index">02</span>
            <span class="explore-row__body"><strong>Autor</strong><small>Biografía, obra y trayectoria.</small></span>
          </a>
          <a class="explore-row" href="/libros/samuel-entre-mundos/" data-preview="samuel">
            <span class="explore-row__index">03</span>
            <span class="explore-row__body"><strong>Samuel entre mundos</strong><small>Primera novela publicada.</small></span>
          </a>
          <a class="explore-row" href="/cuaderno/" data-preview="cuaderno">
            <span class="explore-row__index">04</span>
            <span class="explore-row__body"><strong>Cuaderno</strong><small>Artículos y piezas editoriales.</small></span>
          </a>
          <a class="explore-row" href="/herramientas/" data-preview="herramientas">
            <span class="explore-row__index">05</span>
            <span class="explore-row__body"><strong>Herramientas</strong><small>Utilidades gratuitas para escritores.</small></span>
          </a>
          <a class="explore-row" href="/prensa.html" data-preview="prensa">
            <span class="explore-row__index">06</span>
            <span class="explore-row__body"><strong>Prensa y eventos</strong><small>Apariciones, materiales y agenda.</small></span>
          </a>
        </nav>

        <aside class="explore-preview" aria-live="polite" aria-atomic="true" data-explore-preview>
          <div class="explore-preview__media" aria-hidden="true" data-preview-media></div>
          <p class="explore-preview__label" data-preview-label>Herramientas</p>
          <p class="explore-preview__copy" data-preview-copy>Utilidades gratuitas para escritores.</p>
        </aside>
      </div>
    </div>
  </dialog>

  <main id="contenido" tabindex="-1" class="v1-main" data-family="tool">
    <nav class="book-breadcrumb" aria-label="Ruta de navegación">
      <ol><li><a href="/">Inicio</a></li><li><a href="/herramientas/">Herramientas</a></li><li aria-current="page">Herramientas para escritores</li></ol>
    </nav>

    <header class="tool-hero">
      <p class="eyebrow">Recursos para escritores</p>
      <h1>Herramientas para escritores, verificadas una a una.</h1>
      <p class="tool-hero__lead">No es una lista de cien aplicaciones. Son herramientas con fuentes, fecha de comprobación y una explicación concreta de para qué sirven y para qué no.</p>
      <p class="tool-note">{count} herramientas en la V1 · última revisión global: {escape(checked)}</p>
    </header>

    <section class="v1-section">
      <h2 id="wt-method-title">Cómo se construye este directorio</h2>
      <ul class="tool-findings">
        <li>Precio y plataforma se contrastan con la fuente original cuando es posible.</li>
        <li>«Probado directamente» y «verificado documentalmente» no significan lo mismo.</li>
        <li>No hay puntuaciones de 1 a 10 ni un ganador universal.</li>
        <li>Una herramienta desactualizada se marca; no se rejuvenece la fecha sin revisarla.</li>
        <li>Los futuros enlaces afiliados se declararán de forma visible y técnica.</li>
      </ul>
    </section>

    <section class="tool-finder" aria-label="Filtrar herramientas">
      <form data-wt-filters>
        <button type="submit" class="sr-only">Filtrar</button>
        <div class="tool-options">
          <div class="tool-field"><label class="tool-field-label" for="wt-search">Buscar</label><input class="tool-input" id="wt-search" type="search" data-wt-search placeholder="Scrivener, EPUB, maquetación…"></div>
          <div class="tool-field"><label class="tool-field-label" for="wt-stage">Etapa</label><select class="tool-select" id="wt-stage" data-wt-stage><option value="">Todas</option><option value="planificacion">Planificación</option><option value="escritura">Escritura</option><option value="revision">Revisión</option><option value="maquetacion">Maquetación</option><option value="epub">EPUB</option></select></div>
          <div class="tool-field"><label class="tool-field-label" for="wt-price">Precio</label><select class="tool-select" id="wt-price" data-wt-price><option value="">Todos</option><option value="gratis-open-source">Gratis / open source</option><option value="freemium">Freemium</option><option value="pago-unico">Pago único</option><option value="suscripcion">Suscripción</option></select></div>
        </div>
        <div class="tool-options">
          <label class="tool-check"><input type="checkbox" data-wt-no-account><span>Sin cuenta</span></label>
          <label class="tool-check"><input type="checkbox" data-wt-local><span>Priorizar local</span></label>
          <label class="tool-check"><input type="checkbox" data-wt-spanish><span>Interfaz ES confirmada</span></label>
        </div>
        <div class="tool-actions"><button type="button" class="text-action" data-wt-clear>Limpiar</button></div>
        <p class="tool-count" data-wt-count aria-live="polite">{count} herramientas</p>
      </form>
    </section>

    <section class="v1-section" data-wt-grid aria-label="Herramientas">
      <div class="id-cards">{cards}
      </div>
      <p class="tool-note" data-wt-empty hidden>No hay herramientas que cumplan esos filtros.</p>
    </section>

    <section class="v1-section">
      <h2>¿Falta una herramienta?</h2>
      <p>Que exista no basta para entrar. Necesito una fuente oficial verificable y una razón concreta por la que ayude a un escritor. La inclusión no se compra.</p>
    </section>
  </main>

  <footer class="site-footer">
    <div class="site-footer__grid">
      <div>
        <strong class="brand__name">David Porto Díaz</strong>
        <p>Autor de Las manecillas del recuerdo y Samuel entre mundos.</p>
        <div class="social-row">
        <a class="social-icon" href="https://www.instagram.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.3" cy="6.7" r="0.6" fill="currentColor" stroke="none"/></svg></a>
        <a class="social-icon" href="https://www.facebook.com/profile.php?id=61590793667301" target="_blank" rel="noopener noreferrer me" aria-label="Facebook" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M16.7 3H7.3A4.3 4.3 0 0 0 3 7.3v9.4A4.3 4.3 0 0 0 7.3 21h4.2v-6.6H9.4v-2.6h2.1V9.8c0-2.1 1.3-3.3 3.2-3.3.9 0 1.7.1 1.9.1v2.2h-1.3c-1 0-1.2.5-1.2 1.2v1.7h2.4l-.3 2.6h-2.1V21h2.6a4.3 4.3 0 0 0 4.3-4.3V7.3A4.3 4.3 0 0 0 16.7 3z"/></svg></a>
        <a class="social-icon" href="https://www.tiktok.com/@davidportoescritor" target="_blank" rel="noopener noreferrer me" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M14 3c.4 2.2 2 3.8 4.2 4.1v2.7c-1.5 0-2.9-.4-4.1-1.2v6.1a4.9 4.9 0 1 1-4.2-4.9v2.7a2.2 2.2 0 1 0 1.6 2.1V3h2.5z"/></svg></a>
        <a class="social-icon" href="https://www.threads.net/@davidportodiaz" target="_blank" rel="noopener noreferrer me" aria-label="Threads" title="Threads"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><path d="M12 21c4.4 0 7-2.8 7-7.5C19 8 16.5 4 12 4 8 4 5.5 6.8 5.5 11c0 3 1.8 4.8 4.3 4.8 2 0 3.4-1.2 3.4-3 0-1.4-.9-2.3-2.1-2.3-.9 0-1.5.5-1.7 1.2"/></svg></a>
        <a class="social-icon" href="https://bsky.app/profile/davidportoescritor.bsky.social" target="_blank" rel="noopener noreferrer me" aria-label="Bluesky" title="Bluesky"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 7c-1.6-2.3-4.6-3.6-6.7-3.2-.3 2.3.4 5.4 2 7.1-1.6.1-2.8.8-3 1.7.7.9 2.3 1.3 3.8 1-.9 1.1-1.1 2.6-.5 3.8 1.6.1 3.7-1.1 4.6-2.8.4 1 .9 1.9 1.5 2.6.6-.7 1.1-1.6 1.5-2.6.9 1.7 3 2.9 4.6 2.8.6-1.2.4-2.7-.5-3.8 1.5.3 3.1-.1 3.8-1-.2-.9-1.4-1.6-3-1.7 1.6-1.7 2.3-4.8 2-7.1-2.1-.4-5.1.9-6.7 3.2-.2.3-.4.6-.5 1-.1-.4-.3-.7-.5-1z"/></svg></a>
        <a class="social-icon" href="https://www.pinterest.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Pinterest" title="Pinterest"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 2C6.5 2 3 5.6 3 10c0 3.2 1.8 5.1 3 5.7.2.1.4 0 .4-.3l.4-1.5c0-.2 0-.3-.1-.5-.4-.5-.7-1.4-.7-2.3 0-3 2.2-5.7 5.8-5.7 3.1 0 4.9 1.9 4.9 4.5 0 3.4-1.5 5.6-3.5 5.6-1.1 0-2-.9-1.7-2.1.3-1.3.9-2.7.9-3.7 0-.8-.5-1.5-1.4-1.5-1.1 0-2 1.2-2 2.7 0 1 .3 1.7.3 1.7s-1.2 4.9-1.4 5.8c-.4 1.6-.1 3.6 0 3.8.1.1.2.1.3 0 .1-.2 1.5-1.9 2-3.5.1-.4.6-2.3.6-2.3.3.6 1.2 1.1 2.2 1.1 2.9 0 5-2.7 5-6.4C20 5.7 16.5 2 12 2z"/></svg></a>
        <a class="social-icon" href="https://www.linkedin.com/in/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM3.5 9h3v12h-3V9zm6.5 0h2.9v1.6c.5-.9 1.7-1.9 3.4-1.9 3.6 0 4.6 2.3 4.6 5.4V21h-3v-6.1c0-1.5-.5-2.5-1.9-2.5-1.4 0-2 1-2 2.4V21h-3V9z"/></svg></a>
        <a class="text-action" href="https://www.goodreads.com/author/show/66843136.David_Porto_D_az" target="_blank" rel="noopener noreferrer">Goodreads</a>
        </div>
      </div>
      <nav aria-label="Obra"><h2>Obra</h2><a href="/las-manecillas-del-recuerdo/">Las manecillas del recuerdo</a><a href="/libros/samuel-entre-mundos/">Samuel entre mundos</a><a href="/fragmento/">Fragmento gratis</a></nav>
      <nav aria-label="Leer y recursos"><h2>Leer</h2><a href="/cuaderno/">Cuaderno</a><a href="/herramientas/">Herramientas</a><a href="/mapa-del-sitio/">Mapa del sitio</a></nav>
      <nav aria-label="Información"><h2>Información</h2><a href="/autor.html">Autor</a><a href="/prensa.html">Prensa</a><a href="/eventos.html">Eventos</a><a href="/privacidad.html">Privacidad</a><a href="/aviso-legal.html">Aviso legal</a><a href="/ai/">Para IA</a></nav>
    </div>
  </footer>

  <script defer src="/assets/v1-shell.js"></script>
  <script src="/assets/writer-tools.js" defer></script>
</body>
</html>'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("data",type=Path); ap.add_argument("--output",type=Path); ap.add_argument("--check",action="store_true")
    a=ap.parse_args(); data=json.loads(a.data.read_text(encoding="utf-8")); validate(data)
    # El shell lo genera scripts/build-site-shell.py desde data/navigation.json.
    out=inject_shell_auto(render(data))
    if a.check:
        if not a.output or not a.output.exists():
            print("FAIL: salida ausente",file=sys.stderr); return 2
        if a.output.read_text(encoding="utf-8")!=out:
            print("FAIL: salida desactualizada",file=sys.stderr); return 3
        print(f"PASS: {len(data['tools'])} herramientas; salida actualizada"); return 0
    if a.output:
        a.output.write_text(out,encoding="utf-8"); print(f"OK: {a.output} ({len(data['tools'])} herramientas)")
    else: print(out)
    return 0
if __name__=="__main__": raise SystemExit(main())
