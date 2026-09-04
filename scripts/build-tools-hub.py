#!/usr/bin/env python3
import argparse, html, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto  # noqa: E402

CATEGORIES = {
    "revisar-texto": ("Revisar un texto", "Métricas descriptivas para encontrar patrones que merecen una segunda mirada."),
    "revisar-manuscrito": ("Ver el manuscrito completo", "Comparaciones internas para entender la estructura del propio libro."),
    "personajes-estructura": ("Personajes y estructura", "Visualiza o comprueba elementos que suelen ser difíciles de ver en una lista plana."),
    "lectura-eventos": ("Lecturas y eventos", "Prepara lecturas públicas y recursos de calendario sin repetir datos a mano."),
    "publicar-web": ("Publicar en la web", "Metadatos, marcado y comprobaciones orientadas a una web de escritor."),
    "publicar-promocionar": ("Prensa y promoción", "Recursos para empaquetar material profesional sin convertirlo en una fábrica de copy."),
    "investigar-recordar": ("Investigar y recordar", "Prepara conversaciones y fichas para recoger historia real antes de convertirla en material narrativo."),
    "lectores": ("Para lectores", "No todo aquí es para quien escribe: alguna herramienta está pensada para quien solo quiere leer."),
}
FILTER_GROUPS = {
    "revisar": ("Revisar texto", {"revisar-texto", "revisar-manuscrito"}),
    "estructura": ("Personajes y estructura", {"personajes-estructura"}),
    "publicar": ("Publicar y promocionar", {"publicar-web", "publicar-promocionar", "lectura-eventos"}),
    "investigar": ("Investigar y recordar", {"investigar-recordar"}),
    "lectores": ("Para lectores", {"lectores"}),
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
        <p class="eyebrow">Directorios relacionados</p>
        <div><h2>Referencia, no herramientas interactivas.</h2><p>Estas páginas son directorios de referencia. No cuentan como parte de las {len(tools)} herramientas de arriba.</p></div>
      </div>
      <div class="id-cards">
        {chr(10).join(directory_card(d) for d in directories)}
      </div>
    </section>'''

    noscript_items = '\n          '.join(noscript_item(i, t) for i, t in enumerate(tools, 1))
    item_list_json = ','.join(item_list_entry(i, t) for i, t in enumerate(tools, 1))

    # El header/dialog/footer de abajo son placeholders minimos: apply_shell() en
    # build-site-shell.py los sustituye por completo (via HEADER_RE/DIALOG_RE/
    # FOOTER_RE) antes de que inject_shell_auto() devuelva el HTML, asi que
    # cualquier contenido real de aqui se descarta sin llegar nunca a escribirse
    # a disco. Mantenerlos vacios evita otra copia a mano de cabecera/Explorar/
    # pie -- ver scripts/site_shell.py.
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
  <meta property="og:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
  <meta property="og:image:width" content="1731" />
  <meta property="og:image:height" content="909" />
  <meta property="og:image:alt" content="Herramientas gratuitas para escritores | David Porto Díaz" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="David Porto Díaz" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Herramientas gratuitas para escritores | David Porto Díaz" />
  <meta name="twitter:description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador." />
  <meta name="twitter:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
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
  <link rel="preload" as="style" href="/assets/v1-site-cohesion-v6.css?v=2" />
  <link rel="preload" as="style" href="/assets/v1-reflow-hardening-v7.css?v=1" />
  <link rel="preload" as="style" href="/assets/v1-text-resilience-v8.css?v=1" />
  <!-- v1-shell-preload:end -->
  <link rel="stylesheet" href="/assets/v1-shell.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-families.css?v=2" />
  <link rel="stylesheet" href="/assets/herramientas-index.css?v=1" />

  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Herramientas gratuitas para escritores","url":"https://davidportodiaz.com/herramientas/","inLanguage":"es","mainEntity":{{"@type":"ItemList","numberOfItems":{len(tools)},"itemListElement":[{item_list_json}]}}}}</script>
</head>

<body data-back-to-top>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>

  <header class="site-header" data-header></header>

  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>

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

    <noscript>
      <section class="v1-section">
        <div class="v1-section__head"><p class="eyebrow">Sin JavaScript</p><h2>Todas las herramientas.</h2></div>
        <ul class="samuel-route-list">
          {noscript_items}
        </ul>
      </section>
    </noscript>
  </main>

  <footer class="site-footer"></footer>

  <script defer src="/assets/v1-shell.js?v=6"></script>
  <script defer src="/script.js?v=202609-launch-4"></script>
  <script src="/assets/herramientas-hub.js?v=20260819-1" defer></script>
</body>
</html>
'''


def main():
    p = argparse.ArgumentParser(); p.add_argument('data'); p.add_argument('output'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    data = json.loads(Path(args.data).read_text(encoding='utf-8')); tools, directories = validate(data); # El shell lo genera scripts/build-site-shell.py desde data/navigation.json;
    # la plantilla de este fichero ya no manda sobre cabecera, Explorar ni pie.
    out = inject_shell_auto(render(data, tools, directories)); target = Path(args.output)
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != out:
            print('OUTDATED', file=sys.stderr); return 2
        print(f'OK: {len(tools)} herramientas, {len(directories)} directorios'); return 0
    target.write_text(out, encoding='utf-8'); print(f'GENERATED: {len(tools)} herramientas, {len(directories)} directorios'); return 0

if __name__ == '__main__': raise SystemExit(main())
