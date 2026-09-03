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
SHARE_IMAGE="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg"
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
    # El header/dialog de abajo son placeholders minimos: apply_shell() en
    # build-site-shell.py los sustituye por completo (via HEADER_RE/DIALOG_RE)
    # antes de que inject_shell_auto() devuelva el HTML, asi que cualquier
    # contenido real de aqui se descarta sin llegar nunca a escribirse a
    # disco. Mantenerlos vacios evita otra copia a mano de cabecera/Explorar
    # -- ver scripts/site_shell.py.
    return f'''<!DOCTYPE html>
<html lang="es" class="v1">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="noindex,nofollow" />
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

  <link rel="stylesheet" href="/assets/v1-fonts.css?v=1" />
  <link rel="stylesheet" href="/assets/v1-tokens.css?v=1" />
  <link rel="stylesheet" href="/assets/v1-base.css?v=1" />
  <!-- v1-shell-preload:start (generated by scripts/add_v1_shell_preloads.py -- do not edit by hand) -->
  <link rel="preload" as="style" href="/assets/v1-shell-base.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-shell-lrb-v2.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-lrb-material-v2.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-home-editorial-v3.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-editorial-interior-v4.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-editorial-interactions-v4.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-site-cohesion-v6.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-reflow-hardening-v7.css?v=1" />
  <!-- v1-shell-preload:end -->
  <link rel="stylesheet" href="/assets/v1-shell.css?v=1" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-families.css?v=1" />
  <link rel="stylesheet" href="/assets/v1-tools.css?v=2" />
  <link rel="stylesheet" href="/assets/editoriales.css?v=1" />
  <script type="application/ld+json">{schema}</script>
</head>

<body>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>

  <header class="site-header" data-header></header>

  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>

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

  <footer class="site-footer"></footer>

  <script defer src="/assets/v1-shell.js?v=2"></script>
  <script src="/assets/writer-tools.js?v=1" defer></script>
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
