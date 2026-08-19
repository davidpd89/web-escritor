#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from datetime import datetime
from html import escape
from urllib.parse import urlparse

ALLOWED_STAGES={"planificacion","escritura","revision","estadisticas","maquetacion","exportacion","epub","validacion","impresion","marketing","distribucion"}
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

def pill(text): return f'<span class="wt-pill">{escape(str(text))}</span>'

def render_tool(t):
    stages=" ".join(t["stages"])
    localish=t["data_mode"] in ("local","local-con-sync-opcional","desktop")
    es=str(t["interface_es"]).startswith("sí")
    tested=t["verification"].get("hands_on") is True
    tested_label="Probado directamente" if tested else "Verificado documentalmente"
    sources="".join(f'<li><a href="{escape(u)}" target="_blank" rel="noopener noreferrer">Fuente {n}</a></li>' for n,u in enumerate(t["verification"]["sources"],1))
    return f'''
<article class="wt-card" data-name="{escape(t["name"].lower())}" data-stages="{escape(stages)}" data-price="{escape(t["price"]["model"])}" data-local="{"1" if localish else "0"}" data-spanish="{"1" if es else "0"}" data-account="{"0" if t["account_required"] is False else "1" if t["account_required"] is True else "unknown"}">
<header class="wt-card__head"><div><p class="wt-kicker">{escape(tested_label)}</p><h2>{escape(t["name"])}</h2></div><span class="wt-verified">Verificado {escape(t["verification"]["checked_at"])}</span></header>
<div class="wt-pills">{''.join(pill(x) for x in t["stages"])}</div>
<dl class="wt-facts">
<div><dt>Precio</dt><dd>{escape(t["price"]["display"])}</dd></div>
<div><dt>Plataformas</dt><dd>{escape(", ".join(t["platforms"]))}</dd></div>
<div><dt>Datos</dt><dd>{escape(t["data_note"])}</dd></div>
<div><dt>Interfaz en español</dt><dd>{escape(str(t["interface_es"]))}</dd></div>
</dl>
<section><h3>Para qué sí</h3><p>{escape(t["best_for"])}</p></section>
<section><h3>Para qué no</h3><p>{escape(t["not_for"])}</p></section>
<p class="wt-editorial">{escape(t["editorial_note"])}</p>
<details class="wt-sources"><summary>Fuentes y verificación</summary><ul>{sources}</ul></details>
<p class="wt-actions"><a class="button secondary" href="{escape(t["website"])}" target="_blank" rel="noopener noreferrer">Web oficial</a></p>
</article>'''

def render(data):
    cards="\n".join(render_tool(t) for t in data["tools"] if t["status"]!="deprecated")
    count=sum(1 for t in data["tools"] if t["status"]!="deprecated")
    checked=data["methodology"]["checked_at"]
    return f'''<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="index,follow,max-image-preview:large">
<title>Herramientas para escritores: directorio verificado | David Porto Díaz</title>
<meta name="description" content="Directorio editorial de herramientas para escritores: precio, plataforma, privacidad, idioma, para qué sirve y para qué no, con fuentes y fecha de verificación.">
<link rel="canonical" href="https://davidportodiaz.com/recursos/herramientas-para-escritores/">
<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/assets/writer-tools.css">
</head><body>
<a class="skip-link" href="#main-content">Saltar al contenido</a><main id="main-content" class="wt-page">
<nav class="breadcrumb" aria-label="Ruta de navegación"><a href="/">Inicio</a> › <a href="/herramientas/">Herramientas</a> › Herramientas para escritores</nav>
<header class="wt-hero"><p class="eyebrow">Recursos para escritores</p><h1>Herramientas para escritores, verificadas una a una.</h1><p class="lead">No es una lista de cien aplicaciones. Son herramientas con fuentes, fecha de comprobación y una explicación concreta de para qué sirven y para qué no.</p><p class="wt-meta">{count} herramientas en la V1 · última revisión global: {escape(checked)}</p></header>
<aside class="wt-method" aria-labelledby="wt-method-title"><h2 id="wt-method-title">Cómo se construye este directorio</h2><ul><li>Precio y plataforma se contrastan con la fuente original cuando es posible.</li><li>«Probado directamente» y «verificado documentalmente» no significan lo mismo.</li><li>No hay puntuaciones de 1 a 10 ni un ganador universal.</li><li>Una herramienta desactualizada se marca; no se rejuvenece la fecha sin revisarla.</li><li>Los futuros enlaces afiliados se declararán de forma visible y técnica.</li></ul></aside>
<form class="wt-filters" data-wt-filters aria-label="Filtrar herramientas">
<label>Buscar<input type="search" data-wt-search placeholder="Scrivener, EPUB, maquetación…"></label>
<label>Etapa<select data-wt-stage><option value="">Todas</option><option value="planificacion">Planificación</option><option value="escritura">Escritura</option><option value="revision">Revisión</option><option value="maquetacion">Maquetación</option><option value="epub">EPUB</option></select></label>
<label>Precio<select data-wt-price><option value="">Todos</option><option value="gratis-open-source">Gratis / open source</option><option value="freemium">Freemium</option><option value="pago-unico">Pago único</option><option value="suscripcion">Suscripción</option></select></label>
<label class="wt-check"><input type="checkbox" data-wt-no-account> Sin cuenta</label><label class="wt-check"><input type="checkbox" data-wt-local> Priorizar local</label><label class="wt-check"><input type="checkbox" data-wt-spanish> Interfaz ES confirmada</label>
<button type="button" class="button secondary" data-wt-clear>Limpiar</button><p class="wt-result-count" data-wt-count aria-live="polite">{count} herramientas</p></form>
<section class="wt-grid" data-wt-grid aria-label="Herramientas">{cards}</section><p class="wt-empty" data-wt-empty hidden>No hay herramientas que cumplan esos filtros.</p>
<section class="wt-contribute"><h2>¿Falta una herramienta?</h2><p>Que exista no basta para entrar. Necesito una fuente oficial verificable y una razón concreta por la que ayude a un escritor. La inclusión no se compra.</p></section>
</main><script src="/assets/writer-tools.js" defer></script></body></html>'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("data",type=Path); ap.add_argument("--output",type=Path); ap.add_argument("--check",action="store_true")
    a=ap.parse_args(); data=json.loads(a.data.read_text(encoding="utf-8")); validate(data); out=render(data)
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
