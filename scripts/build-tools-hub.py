#!/usr/bin/env python3
import argparse, html, json, sys
from pathlib import Path

CATEGORIES = {
    "revisar-texto": ("Revisar un texto", "Métricas descriptivas para encontrar patrones que merecen una segunda mirada."),
    "revisar-manuscrito": ("Ver el manuscrito completo", "Comparaciones internas para entender la estructura del propio libro."),
    "personajes-estructura": ("Personajes y estructura", "Visualiza o comprueba elementos que suelen ser difíciles de ver en una lista plana."),
    "lectura-eventos": ("Lecturas y eventos", "Prepara lecturas públicas y recursos de calendario sin repetir datos a mano."),
    "publicar-web": ("Publicar en la web", "Metadatos, marcado y comprobaciones orientadas a una web de escritor."),
    "publicar-promocionar": ("Prensa y promoción", "Recursos para empaquetar material profesional sin convertirlo en una fábrica de copy."),
    "investigar-recordar": ("Investigar y recordar", "Prepara conversaciones y fichas para recoger historia real antes de convertirla en material narrativo."),
}
FILTER_GROUPS = {
    "revisar": ("Revisar texto", {"revisar-texto", "revisar-manuscrito"}),
    "estructura": ("Personajes y estructura", {"personajes-estructura"}),
    "publicar": ("Publicar y promocionar", {"publicar-web", "publicar-promocionar", "lectura-eventos"}),
    "investigar": ("Investigar y recordar", {"investigar-recordar"}),
}
PRIVACY = {
    "local": "En tu navegador",
    "network-required": "Necesita consultar una URL pública",
}

def validate(data):
    if data.get("schema_version") != 1:
        raise ValueError("schema_version debe ser 1")
    tools = data.get("tools")
    if not isinstance(tools, list) or len(tools) < 5:
        raise ValueError("se esperan al menos 5 herramientas")
    seen_slug, seen_href = set(), set()
    for i, tool in enumerate(tools, 1):
        for key in ("slug", "name", "href", "category", "summary", "privacy", "input", "source_doc"):
            if not isinstance(tool.get(key), str) or not tool[key].strip():
                raise ValueError(f"herramienta {i}: falta {key}")
        if tool["slug"] in seen_slug:
            raise ValueError(f"slug duplicado: {tool['slug']}")
        if tool["href"] in seen_href:
            raise ValueError(f"href duplicado: {tool['href']}")
        if tool["category"] not in CATEGORIES:
            raise ValueError(f"categoría desconocida: {tool['category']}")
        if tool["privacy"] not in PRIVACY:
            raise ValueError(f"privacy desconocida: {tool['privacy']}")
        if not tool["href"].startswith("/") or not tool["href"].endswith("/"):
            raise ValueError(f"ruta inválida: {tool['href']}")
        # The hub must not list itself as one of the tools it indexes.
        if tool["href"] == "/herramientas/":
            raise ValueError("el hub no puede listarse a sí mismo como herramienta")
        seen_slug.add(tool["slug"]); seen_href.add(tool["href"])

    directories = data.get("directories", [])
    if not isinstance(directories, list):
        raise ValueError("directories debe ser una lista")
    for i, entry in enumerate(directories, 1):
        for key in ("name", "href", "summary"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"directorio {i}: falta {key}")
        if entry["href"] in seen_href:
            raise ValueError(f"href duplicado entre herramientas y directorios: {entry['href']}")

    return tools, directories


def card(tool):
    return f'''<article class="id-card" data-tool data-category="{html.escape(tool['category'])}" data-privacy="{html.escape(tool['privacy'])}">
          <p class="tool-meta">{html.escape(PRIVACY[tool['privacy']])}</p>
          <h3><a href="{html.escape(tool['href'])}">{html.escape(tool['name'])}</a></h3>
          <p>{html.escape(tool['summary'])}</p>
          <div class="id-card__actions"><a class="text-action" href="{html.escape(tool['href'])}">Abrir herramienta</a></div>
        </article>'''


def directory_card(entry):
    return f'''<article class="id-card">
          <h3><a href="{html.escape(entry['href'])}">{html.escape(entry['name'])}</a></h3>
          <p>{html.escape(entry['summary'])}</p>
        </article>'''


def noscript_item(i, tool):
    return f'''<li><span>{i:02d}</span><div><strong><a href="{html.escape(tool['href'])}">{html.escape(tool['name'])}</a></strong></div></li>'''


def item_list_entry(i, tool):
    return json.dumps({"@type": "ListItem", "position": i, "url": "https://davidportodiaz.com" + tool["href"], "name": tool["name"]}, ensure_ascii=False)


def render(data, tools, directories):
    sections = []
    for key, (title, desc) in CATEGORIES.items():
        subset = [t for t in tools if t['category'] == key]
        if not subset:
            continue
        sections.append(f'''    <section class="tools-section" data-tool-section>
      <h2>{html.escape(title)}</h2>
      <p>{html.escape(desc)}</p>
      <div class="id-cards">
        {chr(10).join('        ' + card(t) if False else card(t) for t in subset)}
      </div>
    </section>''')

    filter_buttons = '\n        '.join(
        f'<button type="button" data-filter="{key}">{html.escape(label)}</button>'
        for key, (label, _cats) in FILTER_GROUPS.items()
    )

    directories_section = ''
    if directories:
        directories_section = f'''    <section class="v1-section" id="directorios">
      <div class="v1-section__head">
        <p class="eyebrow">Checklists y directorios relacionados</p>
        <div><h2>Referencia, no herramientas interactivas.</h2><p>Estas páginas son listas de comprobación o directorios de referencia. No cuentan como parte de las {len(tools)} herramientas de arriba.</p></div>
      </div>
      <div class="id-cards">
        {chr(10).join(directory_card(d) for d in directories)}
      </div>
    </section>'''

    noscript_items = '\n          '.join(noscript_item(i, t) for i, t in enumerate(tools, 1))
    item_list_json = ','.join(item_list_entry(i, t) for i, t in enumerate(tools, 1))

    return f'''<!DOCTYPE html>
<html lang="es" class="v1">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large" />

  <title>Herramientas gratuitas para escritores | David Porto Díaz</title>
  <meta name="description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador." />
  <meta property="og:title" content="Herramientas gratuitas para escritores | David Porto Díaz" />
  <meta property="og:description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://davidportodiaz.com/herramientas/" />
  <meta property="og:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp" />
  <meta property="og:image:width" content="1731" />
  <meta property="og:image:height" content="909" />
  <meta property="og:image:alt" content="Herramientas gratuitas para escritores | David Porto Díaz" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="David Porto Díaz" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Herramientas gratuitas para escritores | David Porto Díaz" />
  <meta name="twitter:description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador." />
  <meta name="twitter:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp" />
  <meta name="twitter:image:alt" content="Herramientas gratuitas para escritores | David Porto Díaz" />

  <meta name="theme-color" content="#F4EFE7" />
  <link rel="preconnect" href="https://gc.zgo.at" />
  <link rel="canonical" href="https://davidportodiaz.com/herramientas/" />
  <link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />
  <link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />
  <link rel="manifest" href="/manifest.json" />

  <!-- V1 editorial system — Herramientas hub uses the identity family's
       card grid (the one place a card grid is the right default: unrelated
       utilities, not an editorial archive). Generated by
       scripts/build-tools-hub.py from data/tools-hub.json — do not edit
       this file by hand; edit the JSON and regenerate. -->
  <link rel="stylesheet" href="/assets/v1-fonts.css" />
  <link rel="stylesheet" href="/assets/v1-tokens.css" />
  <link rel="stylesheet" href="/assets/v1-base.css" />
  <link rel="stylesheet" href="/assets/v1-shell.css" />
  <link rel="stylesheet" href="/assets/v1-components.css" />
  <link rel="stylesheet" href="/assets/v1-families.css" />

  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Herramientas gratuitas para escritores","url":"https://davidportodiaz.com/herramientas/","inLanguage":"es","mainEntity":{{"@type":"ItemList","numberOfItems":{len(tools)},"itemListElement":[{item_list_json}]}}}}</script>
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
        <a href="/herramientas/" aria-current="page">Herramientas</a>
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

  <main id="contenido" tabindex="-1" class="v1-main" data-family="tools-hub">
    <nav class="book-breadcrumb" aria-label="Ruta de navegación">
      <ol><li><a href="/">Inicio</a></li><li aria-current="page">Herramientas</li></ol>
    </nav>

    <header class="v1-masthead">
      <div>
        <span class="coordinate">Recursos</span>
        <p class="eyebrow">Recursos para escritores</p>
        <h1>Herramientas pequeñas para problemas concretos.</h1>
        <p class="v1-masthead__lead">Sin cuenta y sin convertir cada decisión en un «score». Si una herramienta recibe texto privado, la página indica de forma explícita si se procesa solo en tu navegador.</p>
      </div>
    </header>

    <section class="tool-finder" aria-labelledby="finder-title">
      <h2 id="finder-title">¿Qué necesitas hacer?</h2>
      <div class="tool-filters" role="group" aria-label="Filtrar herramientas">
        <button type="button" data-filter="all" aria-pressed="true">Todas</button>
        {filter_buttons}
        <button type="button" data-filter="local">Solo navegador</button>
      </div>
      <p class="tool-count" data-tool-count aria-live="polite">{len(tools)} herramientas</p>
    </section>

{chr(10).join(sections)}

{directories_section}

    <section class="v1-section" id="metodo">
      <div class="v1-section__head"><p class="eyebrow">Método</p><h2>Qué significa «privada» aquí.</h2></div>
      <p class="samuel-narrow" style="max-width:64ch">Las herramientas marcadas «En tu navegador» no necesitan enviar el texto o los datos introducidos a nuestro servidor para calcular el resultado. Las que necesitan consultar una URL pública lo dicen de forma distinta. No usamos «privada» como sello de seguridad genérico.</p>
    </section>

    <section class="v1-section" id="externas">
      <div class="v1-section__head"><p class="eyebrow">¿Buscas software externo?</p><h2>Este hub reúne herramientas propias.</h2></div>
      <p class="samuel-narrow" style="max-width:64ch">La selección de programas y servicios de terceros vive aparte para poder verificar precio, plataforma, idioma y tratamiento del manuscrito sin mezclar recomendaciones con producto propio.</p>
      <p style="margin-top:1rem"><a class="text-action" href="/recursos/herramientas-para-escritores/">Ver directorio curado de herramientas para autores</a></p>
    </section>

    <noscript>
      <section class="v1-section">
        <div class="v1-section__head"><p class="eyebrow">Sin JavaScript</p><h2>Todas las herramientas.</h2></div>
        <ul class="samuel-route-list">
          {noscript_items}
        </ul>
      </section>
    </noscript>
  </main>

  <footer class="site-footer">
    <div class="site-footer__grid">
      <div>
        <strong class="brand__name">David Porto Díaz</strong>
        <p>Autor de Las manecillas del recuerdo y Samuel entre mundos.</p>
        <div class="social-row">
        <a class="social-icon" href="https://www.instagram.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.3" cy="6.7" r="0.6" fill="currentColor" stroke="none"/></svg></a>
        <a class="social-icon" href="https://www.tiktok.com/@davidportoescritor" target="_blank" rel="noopener noreferrer me" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M14 3c.4 2.2 2 3.8 4.2 4.1v2.7c-1.5 0-2.9-.4-4.1-1.2v6.1a4.9 4.9 0 1 1-4.2-4.9v2.7a2.2 2.2 0 1 0 1.6 2.1V3h2.5z"/></svg></a>
        <a class="social-icon" href="https://www.linkedin.com/in/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM3.5 9h3v12h-3V9zm6.5 0h2.9v1.6c.5-.9 1.7-1.9 3.4-1.9 3.6 0 4.6 2.3 4.6 5.4V21h-3v-6.1c0-1.5-.5-2.5-1.9-2.5-1.4 0-2 1-2 2.4V21h-3V9z"/></svg></a>
        </div>
      </div>
      <nav aria-label="Obra"><h2>Obra</h2><a href="/las-manecillas-del-recuerdo/">Las manecillas del recuerdo</a><a href="/libros/samuel-entre-mundos/">Samuel entre mundos</a><a href="/fragmento/">Fragmento gratis</a></nav>
      <nav aria-label="Leer y recursos"><h2>Leer</h2><a href="/cuaderno/">Cuaderno</a><a href="/herramientas/" aria-current="page">Herramientas</a><a href="/mapa-del-sitio/">Mapa del sitio</a></nav>
      <nav aria-label="Información"><h2>Información</h2><a href="/autor.html">Autor</a><a href="/prensa.html">Prensa</a><a href="/eventos.html">Eventos</a><a href="/privacidad.html">Privacidad</a><a href="/aviso-legal.html">Aviso legal</a><a href="/ai/">Para IA</a></nav>
    </div>
    <p class="footer-legal">
      <span>© 2026 David Porto Díaz. Todos los derechos reservados.</span>
    </p>
  </footer>

  <script defer src="/assets/v1-shell.js"></script>
  <script defer src="/script.js?v=202609-launch-1"></script>
  <script src="/assets/herramientas-hub.js?v=20260819-1" defer></script>
</body>
</html>
'''


def main():
    p = argparse.ArgumentParser(); p.add_argument('data'); p.add_argument('output'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    data = json.loads(Path(args.data).read_text(encoding='utf-8')); tools, directories = validate(data); out = render(data, tools, directories); target = Path(args.output)
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != out:
            print('OUTDATED', file=sys.stderr); return 2
        print(f'OK: {len(tools)} herramientas, {len(directories)} directorios'); return 0
    target.write_text(out, encoding='utf-8'); print(f'GENERATED: {len(tools)} herramientas, {len(directories)} directorios'); return 0

if __name__ == '__main__': raise SystemExit(main())
