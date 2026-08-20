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
    return f'''<article class="tool-card" data-tool data-category="{html.escape(tool['category'])}" data-privacy="{html.escape(tool['privacy'])}">
  <p class="tool-meta"><span>{html.escape(PRIVACY[tool['privacy']])}</span></p>
  <h3><a href="{html.escape(tool['href'])}">{html.escape(tool['name'])}</a></h3>
  <p>{html.escape(tool['summary'])}</p>
  <a class="tool-link" href="{html.escape(tool['href'])}">Abrir herramienta <span aria-hidden="true">→</span></a>
</article>'''


def directory_card(entry):
    return f'''<article class="directory-card">
  <h3><a href="{html.escape(entry['href'])}">{html.escape(entry['name'])}</a></h3>
  <p>{html.escape(entry['summary'])}</p>
</article>'''


def render(data, tools, directories):
    sections=[]
    for key,(title,desc) in CATEGORIES.items():
        subset=[t for t in tools if t['category']==key]
        if not subset: continue
        sections.append(f'''<section class="tools-section" data-tool-section>
<h2>{html.escape(title)}</h2><p>{html.escape(desc)}</p>
<div class="tools-grid">{''.join(card(t) for t in subset)}</div>
</section>''')
    items=''.join('<li><a href="{0}">{1}</a></li>'.format(html.escape(t['href']), html.escape(t['name'])) for t in tools)
    directories_section = ''
    if directories:
        directories_section = f'''<section class="tools-directories"><h2>Checklists y directorios relacionados</h2>
<p>Estas páginas no son herramientas interactivas: son listas de comprobación o directorios de referencia. No cuentan como parte de las {len(tools)} herramientas de arriba.</p>
<div class="directories-grid">{''.join(directory_card(d) for d in directories)}</div>
</section>'''
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="index,follow,max-image-preview:large">
<title>Herramientas gratuitas para escritores | David Porto Díaz</title>
<meta name="description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador.">
<meta property="og:title" content="Herramientas gratuitas para escritores | David Porto Díaz">
<meta property="og:description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://davidportodiaz.com/herramientas/">
<meta property="og:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp">
<meta property="og:image:width" content="1731">
<meta property="og:image:height" content="909">
<meta property="og:image:alt" content="Herramientas gratuitas para escritores | David Porto Díaz">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="David Porto Díaz">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Herramientas gratuitas para escritores | David Porto Díaz">
<meta name="twitter:description" content="Herramientas gratuitas para revisar manuscritos, personajes, metadatos, eventos y webs de escritor. Sin registro; las herramientas de texto indican cuándo todo se procesa en tu navegador.">
<meta name="twitter:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp">
<meta name="twitter:image:alt" content="Herramientas gratuitas para escritores | David Porto Díaz">
<link rel="canonical" href="https://davidportodiaz.com/herramientas/">
<link rel="icon" type="image/png" href="/assets/david-porto-favicon.png">
<link rel="apple-touch-icon" href="/assets/david-porto-favicon.png">
<link rel="manifest" href="/manifest.json">
<link rel="stylesheet" href="/styles.css?v=202609-launch-1"><link rel="stylesheet" href="/assets/herramientas-hub.css?v=20260819-1">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"Herramientas gratuitas para escritores","url":"https://davidportodiaz.com/herramientas/","inLanguage":"es","mainEntity":{{"@type":"ItemList","numberOfItems":{len(tools)},"itemListElement":[{','.join(json.dumps({'@type':'ListItem','position':i+1,'url':'https://davidportodiaz.com'+t['href'],'name':t['name']}, ensure_ascii=False) for i,t in enumerate(tools))}]}}}}</script>
</head><body>
<a class="skip-link" href="#main-content">Saltar al contenido</a>
<div class="site-shell"><main id="main-content" class="tools-page" tabindex="-1">
<nav class="breadcrumb" aria-label="Ruta de navegación"><a href="/">Inicio</a><span aria-hidden="true">›</span><span>Herramientas</span></nav>
<header class="tools-hero"><p class="eyebrow">Recursos para escritores</p><h1>Herramientas pequeñas para problemas concretos.</h1>
<p class="lead">Sin cuenta y sin convertir cada decisión en un «score». Si una herramienta recibe texto privado, la página indica de forma explícita si se procesa solo en tu navegador.</p></header>
<section class="tool-finder" aria-labelledby="finder-title"><h2 id="finder-title">¿Qué necesitas hacer?</h2>
<div class="tool-filters" role="group" aria-label="Filtrar herramientas"><button type="button" data-filter="all" aria-pressed="true">Todas</button><button type="button" data-filter="revisar">Revisar texto</button><button type="button" data-filter="estructura">Personajes y estructura</button><button type="button" data-filter="publicar">Publicar y promocionar</button><button type="button" data-filter="investigar">Investigar y recordar</button><button type="button" data-filter="local">Solo navegador</button></div>
<p class="tool-count" data-tool-count aria-live="polite">{len(tools)} herramientas</p></section>
{''.join(sections)}
{directories_section}
<section class="tools-method"><h2>Qué significa «privada» aquí</h2><p>Las herramientas marcadas «En tu navegador» no necesitan enviar el texto o los datos introducidos a nuestro servidor para calcular el resultado. Las que necesitan consultar una URL pública lo dicen de forma distinta. No usamos «privada» como sello de seguridad genérico.</p></section>
<section class="tools-external"><h2>¿Buscas software externo?</h2><p>Este hub reúne herramientas creadas para davidportodiaz.com. La selección de programas y servicios de terceros vive aparte para poder verificar precio, plataforma, idioma y tratamiento del manuscrito sin mezclar recomendaciones con producto propio.</p><p><a href="/recursos/herramientas-para-escritores/">Ver directorio curado de herramientas para autores</a></p></section>
<noscript><section class="tools-noscript"><h2>Todas las herramientas</h2><ul>{items}</ul></section></noscript>
</main></div><script src="/assets/herramientas-hub.js?v=20260819-1" defer></script></body></html>'''


def main():
    p=argparse.ArgumentParser(); p.add_argument('data'); p.add_argument('output'); p.add_argument('--check', action='store_true'); args=p.parse_args()
    data=json.loads(Path(args.data).read_text(encoding='utf-8')); tools,directories=validate(data); out=render(data,tools,directories); target=Path(args.output)
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != out:
            print('OUTDATED', file=sys.stderr); return 2
        print(f'OK: {len(tools)} herramientas, {len(directories)} directorios'); return 0
    target.write_text(out,encoding='utf-8'); print(f'GENERATED: {len(tools)} herramientas, {len(directories)} directorios'); return 0

if __name__=='__main__': raise SystemExit(main())
