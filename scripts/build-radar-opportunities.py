#!/usr/bin/env python3
"""Valida oportunidades verificadas y genera una página estática + JSON + calendario ICS."""
from __future__ import annotations
import argparse, html, json, re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

STALE_DAYS=30
TITLE="Convocatorias para escritores: concursos, becas y manuscritos | David Porto Díaz"
DESCRIPTION="Radar de concursos, premios, becas, ayudas y convocatorias para escritores, verificados contra su fuente oficial y ordenados por fecha límite."
CANONICAL="https://davidportodiaz.com/convocatorias-escritores/"
# El HTML desplegado ya llevaba este bloque og:/twitter: completo, pero
# build_html() nunca lo generaba: quien ejecutara este builder para refrescar
# el radar (que es justo lo que exige la regla de 30 dias de caducidad)
# habria sobrescrito la pagina y perdido en silencio las meta tags sociales.
SHARE_IMAGE="https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp"
SHARE_IMAGE_WIDTH=1731
SHARE_IMAGE_HEIGHT=909
ALLOWED_TYPES={"concurso","premio","ayuda","beca","residencia","manuscritos"}
REQ={"id","title","type","organizer","deadline","genres","source_url","verified_at","published"}

def iso_date(v,field):
    try:return date.fromisoformat(v)
    except Exception: raise ValueError(f"{field}: fecha ISO inválida: {v!r}")
def esc(v):return html.escape(str(v or ""),quote=True)
def slug_ok(v):return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}",v))
def https(v):return urlparse(v).scheme=="https" and bool(urlparse(v).netloc)

def validate(item):
    miss=REQ-set(item)
    if miss: raise ValueError(f"{item.get('id','?')}: faltan {sorted(miss)}")
    if not slug_ok(item["id"]): raise ValueError(f"id inválido: {item['id']}")
    if item["type"] not in ALLOWED_TYPES: raise ValueError(f"{item['id']}: type no permitido")
    if not https(item["source_url"]): raise ValueError(f"{item['id']}: source_url debe ser HTTPS")
    if not isinstance(item["genres"],list) or not item["genres"]: raise ValueError(f"{item['id']}: genres vacío")
    iso_date(item["deadline"],"deadline"); iso_date(item["verified_at"],"verified_at")

def state(item,today):
    dl=iso_date(item["deadline"],"deadline"); verified=iso_date(item["verified_at"],"verified_at")
    if dl < today:return "expired"
    if today-verified > timedelta(days=STALE_DAYS):return "stale"
    if dl-today <= timedelta(days=7):return "closing_soon"
    return "open"

def card(item,today):
    st=state(item,today); days=(iso_date(item["deadline"],"deadline")-today).days
    badge="Cierra pronto" if st=="closing_soon" else "En plazo"
    genres=", ".join(item["genres"])
    fee="Sin tasa" if item.get("fee_eur")==0 else (f"Tasa: {item['fee_eur']} €" if isinstance(item.get("fee_eur"),(int,float)) else "Tasa: consultar")
    return f'''<article class="radar-card" data-radar-item data-type="{esc(item['type'])}" data-genres="{esc('|'.join(item['genres']).lower())}" data-title="{esc(item['title'].lower())}">
<div class="radar-card__top"><span class="radar-badge">{badge}</span><span>{esc(item['type'].capitalize())}</span></div>
<h2>{esc(item['title'])}</h2><p class="radar-org">{esc(item['organizer'])}</p>
<dl><div><dt>Fecha límite</dt><dd><time datetime="{esc(item['deadline'])}">{iso_date(item['deadline'],'deadline').strftime('%d/%m/%Y')}</time> · {days} días</dd></div><div><dt>Géneros</dt><dd>{esc(genres)}</dd></div><div><dt>Coste</dt><dd>{esc(fee)}</dd></div>{f'<div><dt>Premio/ayuda</dt><dd>{esc(item.get("prize"))}</dd></div>' if item.get('prize') else ''}</dl>
{f'<p>{esc(item.get("editorial_note"))}</p>' if item.get('editorial_note') else ''}
<p class="radar-verified">Verificado: <time datetime="{esc(item['verified_at'])}">{iso_date(item['verified_at'],'verified_at').strftime('%d/%m/%Y')}</time></p>
<p><a class="button secondary" data-radar-source data-radar-source-type="{esc(item['type'])}" href="{esc(item['source_url'])}" target="_blank" rel="noopener noreferrer">Ver fuente oficial</a></p></article>'''

def build_html(items,today):
    active=[i for i in items if i.get("published") and state(i,today) in {"open","closing_soon"}]
    active.sort(key=lambda i:i["deadline"])
    cards="\n".join(card(i,today) for i in active) or '<p data-radar-empty>No hay oportunidades verificadas activas ahora mismo.</p>'
    types=sorted({i["type"] for i in active}); genres=sorted({g for i in active for g in i["genres"]})
    opts=lambda vals:'\n'.join(f'<option value="{esc(v)}">{esc(v.capitalize())}</option>' for v in vals)
    schema=json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Convocatorias para escritores","url":"https://davidportodiaz.com/convocatorias-escritores/","inLanguage":"es","isPartOf":{"@id":"https://davidportodiaz.com/#website"}},ensure_ascii=False,separators=(",",":"))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{TITLE}</title><meta name="description" content="{DESCRIPTION}"><meta property="og:title" content="{TITLE}"><meta property="og:description" content="{DESCRIPTION}"><meta property="og:type" content="website"><meta property="og:url" content="{CANONICAL}"><meta property="og:image" content="{SHARE_IMAGE}"><meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}"><meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}"><meta property="og:image:alt" content="{TITLE}"><meta property="og:locale" content="es_ES"><meta property="og:site_name" content="David Porto Díaz"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{TITLE}"><meta name="twitter:description" content="{DESCRIPTION}"><meta name="twitter:image" content="{SHARE_IMAGE}"><meta name="twitter:image:alt" content="{TITLE}"><link rel="canonical" href="{CANONICAL}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="stylesheet" href="/styles.css?v=202609-launch-1"><link rel="stylesheet" href="/assets/radar-convocatorias.css"><script type="application/ld+json">{schema}</script></head><body><a href="#main-content" class="skip-link">Saltar al contenido</a><main id="main-content" class="radar-page"><nav class="breadcrumb" aria-label="Ruta de navegación"><a href="/">Inicio</a> › <a href="/herramientas/">Herramientas</a> › Convocatorias</nav><header class="radar-hero"><p class="eyebrow">Radar para escritores · fuentes verificadas</p><h1>Convocatorias que todavía están a tiempo.</h1><p class="lead">Concursos, premios, ayudas, becas, residencias y recepción de manuscritos. Cada ficha enlaza la fuente oficial y muestra cuándo se comprobó.</p><p><a data-radar-calendar href="/convocatorias-escritores/deadlines.ics">Añadir fechas a mi calendario</a></p></header><section class="radar-filters" aria-label="Filtrar convocatorias"><label>Buscar <input type="search" data-radar-search autocomplete="off" placeholder="Título u organizador"></label><label>Tipo <select data-radar-type><option value="">Todos</option>{opts(types)}</select></label><label>Género <select data-radar-genre><option value="">Todos</option>{opts(genres)}</select></label><label class="radar-check"><input type="checkbox" data-radar-soon> Cierra en 7 días</label><button type="button" class="button secondary" data-radar-clear>Limpiar</button></section><p class="radar-count" role="status" aria-live="polite" data-radar-count>{len(active)} convocatorias verificadas</p><section class="radar-grid" data-radar-grid>{cards}</section><section class="radar-method"><h2>Cómo se mantiene este radar</h2><p>Una lista de fuentes oficiales se revisa para detectar posibles cambios y nuevas convocatorias. Nada se publica automáticamente: una oportunidad solo aparece después de revisar la fuente oficial, su fecha límite y sus condiciones básicas. Una convocatoria activa que lleva más de 30 días sin volver a comprobarse deja de mostrarse aquí aunque su plazo siga abierto.</p></section></main><script src="/assets/radar-convocatorias.js" defer></script></body></html>'''

def ics(items,today):
    lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//David Porto Diaz//Radar escritores//ES","CALSCALE:GREGORIAN","METHOD:PUBLISH","X-WR-CALNAME:Convocatorias para escritores"]
    for i in items:
        if not i.get("published") or state(i,today) not in {"open","closing_soon"}:continue
        d=iso_date(i["deadline"],"deadline"); nxt=d+timedelta(days=1)
        summary=("Cierra: "+i["title"]).replace("\\","\\\\").replace(",","\\,").replace(";","\\;")
        lines += ["BEGIN:VEVENT",f"UID:{i['id']}@davidportodiaz.com",f"DTSTART;VALUE=DATE:{d:%Y%m%d}",f"DTEND;VALUE=DATE:{nxt:%Y%m%d}",f"SUMMARY:{summary}",f"URL:{i['source_url']}","END:VEVENT"]
    lines += ["END:VCALENDAR",""]
    return "\r\n".join(lines)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--out",required=True); ap.add_argument("--today",default=date.today().isoformat()); ap.add_argument("--check",action="store_true"); args=ap.parse_args()
    data=json.loads(Path(args.data).read_text(encoding="utf-8")); items=data.get("items",[]); ids=set()
    for i in items:
        validate(i)
        if i["id"] in ids: raise ValueError(f"id duplicado: {i['id']}")
        ids.add(i["id"])
    today=iso_date(args.today,"today")
    if args.check:
        print(f"OK items={len(items)} active={sum(state(i,today) in {'open','closing_soon'} and i.get('published') for i in items)}"); return
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    active=[i for i in items if i.get("published") and state(i,today) in {"open","closing_soon"}]
    (out/"index.html").write_text(build_html(items,today),encoding="utf-8")
    (out/"opportunities.json").write_text(json.dumps({"generated_for":today.isoformat(),"items":active},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"deadlines.ics").write_text(ics(items,today),encoding="utf-8",newline="")
    print(f"built active={len(active)} expired={len(items)-len(active)}")
if __name__=="__main__": main()
