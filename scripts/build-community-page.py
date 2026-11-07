#!/usr/bin/env python3
"""Genera o comprueba la página pública /comunidad/ (canales de Telegram y servidor de Discord).

Los grupos salen de data/communities.json. Un grupo sin enlace público de invitación
nunca muestra botón: aparece como «Enlace muy pronto» (activo) o «Próximamente»
(previsto). Así la página no promete destinos que todavía no existen.

Uso:
  python scripts/build-community-page.py          # escribe comunidad/index.html con el shell
  python scripts/build-community-page.py --check  # falla si la página no está al día
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from site_shell import inject_shell_auto  # noqa: E402

DATA = "data/communities.json"
PAGE = "comunidad/index.html"
URL = "https://davidportodiaz.com/comunidad/"
TITLE = "Comunidad lectora en Telegram y Discord | David Porto Díaz"
META_DESCRIPTION = (
    "Únete gratis a los canales de Telegram y al servidor de Discord: novedades editoriales "
    "del día, ofertas de libros, los más votados y grupos por género."
)
INVITE_HOSTS = {
    "telegram": {"t.me", "telegram.me"},
    "discord": {"discord.gg", "discord.com"},
}
SECTIONS = {
    "al-dia": ("Para estar al día", "Avisos automáticos a partir del catálogo de libros recomendados."),
    "temas": ("Por género y temática", "Solo los libros de los géneros que te interesan. Únete a todos los que quieras."),
}
STATUS_LABEL = {"active": "Activo", "planned": "Próximamente"}
ICONS = {
    "telegram": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.4 3.6 2.9 10.8c-1.2.5-1.2 1.2-.2 1.5l4.7 1.5 1.8 5.6c.2.6.4.8.9.8.4 0 .6-.2.9-.5l2.3-2.2 4.7 3.5c.9.5 1.5.2 1.7-.8l3.1-14.5c.3-1.3-.5-1.8-1.4-1.5zM9.6 14.4l-.4 4.1-1.4-4.6 10.4-6.6-8.6 7.1z"/></svg>',
    "discord": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M19.3 5.3A16.6 16.6 0 0 0 15.2 4l-.5 1a15.4 15.4 0 0 0-5.4 0L8.8 4a16.6 16.6 0 0 0-4.1 1.3C2.1 9.2 1.4 13 1.7 16.7a16.7 16.7 0 0 0 5.1 2.6l1.1-1.8c-.6-.2-1.2-.5-1.7-.9l.4-.3a11.9 11.9 0 0 0 10.8 0l.4.3c-.5.4-1.1.7-1.7.9l1.1 1.8a16.6 16.6 0 0 0 5.1-2.6c.4-4.3-.7-8-3-11.4zM8.7 14.4c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2zm6.6 0c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2z"/></svg>',
}
FAQ = [
    ("¿Cuesta algo unirse?",
     "No. Los canales y el servidor son gratuitos y no piden registro en esta web. Solo necesitas una cuenta de Telegram o de Discord."),
    ("¿Verán los demás mi número de teléfono?",
     "En los canales de Telegram, no: solo publica el canal y las personas suscritas no ven quién más está dentro."),
    ("¿Cuántos mensajes voy a recibir?",
     "Como máximo un envío al día por canal, siempre a la misma hora: de lunes a viernes a las 11:30 y los fines de semana a las 18:30 (hora de Madrid). Próximos lanzamientos sale los lunes y Los más votados, los sábados. Puedes silenciar cualquier canal sin salir de él."),
    ("¿Los enlaces a libros son de afiliado?",
     "Sí. Los enlaces a Amazon llevan un código de afiliado: si compras, la web recibe una pequeña comisión sin que el precio cambie para ti."),
    ("¿Puedo proponer un canal nuevo?",
     "Sí. Escríbeme desde la página de contacto con el género o el tema que echas de menos."),
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def load(root: Path) -> dict:
    return json.loads((root / DATA).read_text(encoding="utf-8"))


def validate(config: dict) -> list[str]:
    errors: list[str] = []
    platforms = config.get("platforms") or {}
    seen: set[str] = set()
    for key, platform in platforms.items():
        if key not in INVITE_HOSTS:
            errors.append(f"plataforma desconocida: {key}")
        errors += check_invite(key, platform.get("invite", ""), key)
    for group in config.get("groups") or []:
        gid = group.get("id", "")
        if not gid or gid in seen:
            errors.append(f"id vacío o repetido: {gid!r}")
        seen.add(gid)
        if group.get("avatar") and not (ROOT / group["avatar"].lstrip("/")).is_file():
            errors.append(f"{gid}: falta el avatar {group['avatar']}")
        if group.get("platform") not in platforms:
            errors.append(f"{gid}: plataforma sin definir")
        if group.get("status") not in STATUS_LABEL:
            errors.append(f"{gid}: status debe ser active o planned")
        if group.get("status") == "planned" and group.get("invite"):
            errors.append(f"{gid}: un grupo previsto no puede tener enlace")
        errors += check_invite(group.get("platform", ""), group.get("invite", ""), gid)
    return errors


def check_invite(platform: str, invite: str, label: str) -> list[str]:
    if not invite:
        return []
    parts = urlsplit(invite)
    if parts.scheme != "https" or parts.hostname not in INVITE_HOSTS.get(platform, set()):
        return [f"{label}: el enlace debe ser https a {sorted(INVITE_HOSTS.get(platform, set()))}"]
    return []


def join_button(platform: str, name: str, invite: str, label: str = "") -> str:
    label = label or f"Unirme en {name}"
    return (f'<a class="community-join community-join--{platform}" href="{esc(invite)}" '
            f'target="_blank" rel="noopener noreferrer">{ICONS[platform]}<span>{esc(label)}</span></a>')


def render_group(group: dict, platform_name: str) -> str:
    status = group["status"]
    invite = group.get("invite", "")
    if invite:
        action = join_button(group["platform"], platform_name, invite)
    elif group["platform"] == "discord" and status == "active":
        action = ""  # se entra con la invitación del servidor, arriba
    elif status == "active":
        action = '<span class="community-soon">Enlace muy pronto</span>'
    else:
        action = '<span class="community-soon">Próximamente</span>'
    return (
        f'<li class="community-card" id="{esc(group["id"])}" data-status="{status}">'
        f'<div class="community-card__head">{avatar(group)}<h4>{esc(group["name"])}</h4>'
        f'<span class="community-badge community-badge--{status}">{STATUS_LABEL[status]}</span></div>'
        f'<p>{esc(group["description"])}</p>'
        f'<p class="community-card__cadence">{esc(group["cadence"])}</p>'
        f'{action}</li>'
    )


def avatar(group: dict) -> str:
    src = group.get("avatar", "")
    if not src:
        return ""
    return (f'<img class="community-card__avatar" src="{esc(src)}" alt="" width="48" height="48" '
            'loading="lazy" decoding="async" />')


def render_platform_intro(key: str, platform: dict) -> str:
    invite = platform.get("invite", "")
    action = join_button(key, platform["name"], invite, platform.get("invite_label", "")) if invite else ""
    return (
        f'<div class="community-platform__intro"><span class="community-platform__icon">{ICONS[key]}</span>'
        f'<div><p class="community-platform__kind">{esc(platform["kind"])}</p>'
        f'<p>{esc(platform["summary"])}</p>{action}</div></div>'
    )


def render_telegram(config: dict) -> str:
    platform = config["platforms"]["telegram"]
    blocks = []
    for section, (heading, intro) in SECTIONS.items():
        groups = [g for g in config["groups"] if g["platform"] == "telegram" and g["section"] == section]
        if not groups:
            continue
        cards = "".join(render_group(g, platform["name"]) for g in groups)
        blocks.append(
            f'<div class="community-block"><h3>{heading}</h3><p class="community-block__intro">{intro}</p>'
            f'<ul class="community-grid">{cards}</ul></div>'
        )
    return (
        '<section class="community-platform community-platform--telegram" id="telegram" aria-labelledby="telegram-title">'
        '<h2 id="telegram-title">Canales de Telegram</h2>'
        + render_platform_intro("telegram", platform) + "".join(blocks) + '</section>'
    )


def render_discord(config: dict) -> str:
    platform = config["platforms"]["discord"]
    groups = [g for g in config["groups"] if g["platform"] == "discord"]
    cards = "".join(render_group(g, platform["name"]) for g in groups)
    return (
        '<section class="community-platform community-platform--discord" id="discord" aria-labelledby="discord-title">'
        '<h2 id="discord-title">Servidor de Discord</h2>'
        + render_platform_intro("discord", platform)
        + f'<div class="community-block"><h3>Canales del servidor</h3><ul class="community-grid">{cards}</ul></div>'
        '</section>'
    )


def render_faq() -> str:
    items = "".join(
        f'<details class="community-faq__item"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in FAQ
    )
    return ('<section class="community-faq" aria-labelledby="community-faq-title">'
            f'<h2 id="community-faq-title">Preguntas frecuentes</h2>{items}</section>')


def json_ld(config: dict) -> str:
    items = [
        {"@type": "ListItem", "position": i, "name": f'{g["name"]} ({config["platforms"][g["platform"]]["name"]})',
         "url": f'{URL}#{g["id"]}'}
        for i, g in enumerate(config["groups"], start=1)
    ]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": f"{URL}#page",
                "url": URL,
                "name": "Comunidad lectora en Telegram y Discord",
                "description": META_DESCRIPTION,
                "inLanguage": "es",
                "isPartOf": {"@id": "https://davidportodiaz.com/#website"},
                "breadcrumb": {"@id": f"{URL}#breadcrumb"},
                "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{URL}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://davidportodiaz.com/"},
                    {"@type": "ListItem", "position": 2, "name": "Redes sociales", "item": "https://davidportodiaz.com/redes-sociales/"},
                    {"@type": "ListItem", "position": 3, "name": "Comunidad", "item": URL},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\n  ")


def render(config: dict) -> str:
    source = f"""<!doctype html>
<html lang="es" class="v1">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <link rel="canonical" href="{URL}" />
  <title>{TITLE}</title>
  <meta name="description" content="{META_DESCRIPTION}" />
  <meta property="og:title" content="{TITLE}" />
  <meta property="og:description" content="{META_DESCRIPTION}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{URL}" />
  <meta property="og:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
  <meta property="og:image:width" content="1731" />
  <meta property="og:image:height" content="909" />
  <meta property="og:image:alt" content="{TITLE}" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="David Porto Díaz" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{TITLE}" />
  <meta name="twitter:description" content="{META_DESCRIPTION}" />
  <meta name="twitter:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
  <meta name="twitter:image:alt" content="{TITLE}" />
  <meta name="theme-color" content="#ffffff" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="stylesheet" href="/assets/v1-fonts.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-tokens.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-base.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-shell.css?v=21" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-community.css?v=2" />
  <script type="application/ld+json">
  {json_ld(config)}
  </script>
</head>
<body data-back-to-top>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>
  <header class="site-header" data-header></header>
  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>
  <main id="contenido" class="v1-main" tabindex="-1" data-family="community">
    <nav class="community-crumbs" aria-label="Migas de pan"><a href="/">Inicio</a> <span aria-hidden="true">/</span> <a href="/redes-sociales/">Redes sociales</a> <span aria-hidden="true">/</span> <span aria-current="page">Comunidad</span></nav>
    <section class="community-hero" aria-labelledby="community-title">
      <p class="community-eyebrow">Telegram · Discord</p>
      <h1 id="community-title">Únete a la comunidad lectora</h1>
      <p class="community-lead">Novedades editoriales del día, ofertas de libros, los más votados y canales por género. Elige tu plataforma y quédate solo con lo que te interesa.</p>
      <p class="community-switch"><a href="#telegram">{ICONS["telegram"]}<span>Telegram</span></a><a href="#discord">{ICONS["discord"]}<span>Discord</span></a></p>
    </section>
    {render_telegram(config)}
    {render_discord(config)}
    <section class="community-how" aria-labelledby="community-how-title">
      <h2 id="community-how-title">Cómo funciona</h2>
      <ul>
        <li><strong>Gratis y sin registro aquí.</strong> Te unes desde la propia app de Telegram o Discord.</li>
        <li><strong>Avisos automáticos.</strong> Salen del <a href="/recomendaciones/">catálogo de libros recomendados</a>, el mismo que ves en la web.</li>
        <li><strong>Tú decides el ritmo.</strong> Únete solo a los géneros que te interesan y silencia o abandona cualquier canal cuando quieras.</li>
        <li><strong>Transparencia.</strong> Los enlaces a Amazon son de afiliado y así se indica.</li>
      </ul>
    </section>
    {render_faq()}
    <section class="community-other" aria-labelledby="community-other-title">
      <h2 id="community-other-title">Más formas de seguir la web</h2>
      <ul>
        <li><a href="/recomendaciones/">Libros recomendados</a></li>
        <li><a href="/redes-sociales/">Redes sociales</a></li>
      </ul>
    </section>
  </main>
  <footer class="site-footer"></footer>
  <script src="/assets/v1-shell.js?v=36" defer></script>
</body>
</html>
"""
    return inject_shell_auto(source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = load(ROOT)
    errors = validate(config)
    if not errors:
        page = ROOT / PAGE
        expected = render(config)
        if args.check:
            if not page.is_file() or page.read_text(encoding="utf-8") != expected:
                errors.append(f"{PAGE} desactualizado: ejecuta scripts/build-community-page.py")
        else:
            page.parent.mkdir(exist_ok=True)
            page.write_text(expected, encoding="utf-8", newline="\n")
    for error in errors:
        print("FAIL " + error)
    if not errors:
        print("PASS: /comunidad/ al día" if args.check else f"Escrito {PAGE}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
