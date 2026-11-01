#!/usr/bin/env python3
"""Activa o comprueba la página pública /apoyar/ (aportación voluntaria) con varios canales.

Sin ningún canal configurado no existe la ruta ni se enlaza en la web. Con uno o más
(PayPal.me personal, Ko-fi, Buy Me a Coffee, Liberapay, PayPal Payment Link, Stripe) se
genera la página, se añade al pie y aparece el icono de apoyo en la cabecera. La forma de
cada URL se valida; la titularidad y el cobro los comprueba la persona titular.

Uso:
  python scripts/build-support-page.py --add paypal_me=https://www.paypal.me/usuario --add kofi=https://ko-fi.com/usuario
  python scripts/build-support-page.py --check
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from site_shell import inject_shell_auto  # noqa: E402
from support_channels import render_channels, validate_config, validate_channel  # noqa: E402

LINKS = "data/support-links.json"
PAGE = "apoyar/index.html"
ENTRY_ID = "support-project"
ENTRY = {
    "id": ENTRY_ID, "url": "/apoyar/", "label": "Apoya este proyecto", "shortLabel": "Apoyar el proyecto",
    "type": "system", "territory": "sitio", "parentId": "home", "hubId": "home",
    "discoverability": "secondary", "footerEligible": True, "audience": ["reader", "writer"],
    "jobs": ["apoyar"], "sourceFile": PAGE, "status": "public",
}
LEAD = (
    "Las herramientas, las guías, el catálogo de lecturas y el Atlas literario son gratuitos: "
    "sin registro y sin muros de pago. Si te ayudan, un café los mantiene vivos y ayuda a crear otros nuevos."
)
CUP_SVG = (
    '<svg class="support-cup" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
    '<path class="support-cup__steam" d="M25 6c-3 4 3 7 0 11M33 4c-3 4 3 7 0 11M41 6c-3 4 3 7 0 11"/>'
    '<path class="support-cup__body" d="M12 24h36v14a16 16 0 0 1-16 16h-4a16 16 0 0 1-16-16z"/>'
    '<path class="support-cup__handle" d="M48 29h3a7 7 0 0 1 0 14h-4"/>'
    '<path class="support-cup__saucer" d="M6 58h48"/></svg>'
)


META_DESCRIPTION = (
    "Si las herramientas, guías y recursos de esta web te han resultado útiles, "
    "puedes hacer una aportación voluntaria para que siga creciendo."
)


def render(channels: list[dict]) -> str:
    methods = render_channels(channels)
    source = f"""<!doctype html>
<html lang="es" class="v1">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <link rel="canonical" href="https://davidportodiaz.com/apoyar/" />
  <title>Apoya este proyecto | David Porto Díaz</title>
  <meta name="description" content="{META_DESCRIPTION}" />
  <meta property="og:title" content="Apoya este proyecto | David Porto Díaz" />
  <meta property="og:description" content="{META_DESCRIPTION}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://davidportodiaz.com/apoyar/" />
  <meta property="og:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
  <meta property="og:image:width" content="1731" />
  <meta property="og:image:height" content="909" />
  <meta property="og:image:alt" content="Apoya este proyecto | David Porto Díaz" />
  <meta property="og:locale" content="es_ES" />
  <meta property="og:site_name" content="David Porto Díaz" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Apoya este proyecto | David Porto Díaz" />
  <meta name="twitter:description" content="{META_DESCRIPTION}" />
  <meta name="twitter:image" content="https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg" />
  <meta name="twitter:image:alt" content="Apoya este proyecto | David Porto Díaz" />
  <meta name="theme-color" content="#ffffff" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="stylesheet" href="/assets/v1-fonts.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-tokens.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-base.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-shell.css?v=18" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-support.css?v=6" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": "https://davidportodiaz.com/apoyar/#page",
    "url": "https://davidportodiaz.com/apoyar/",
    "name": "Apoya este proyecto",
    "inLanguage": "es",
    "isPartOf": {{"@id": "https://davidportodiaz.com/#website"}}
  }}
  </script>
</head>
<body data-back-to-top>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>
  <header class="site-header" data-header></header>
  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>
  <main id="contenido" class="v1-main" tabindex="-1" data-family="support">
    <div class="support-sheet">
      <section class="support-hero" aria-labelledby="support-title">
        {CUP_SVG}
        <h1 id="support-title" class="support-title">Gracias por estar aquí</h1>
        <p class="support-lead">{LEAD}</p>
      </section>
      <div class="support-methods" aria-label="Formas de aportar">{methods}</div>
    </div>
    <section class="support-other" aria-labelledby="support-other-title">
      <h2 id="support-other-title">¿Ahora no puedes? También ayudas así</h2>
      <ul class="support-other__list">
        <li><a href="/libros/">Recomienda mis novelas</a></li>
        <li><a href="/redes-sociales/">Sígueme en redes</a></li>
      </ul>
    </section>
  </main>
  <footer class="site-footer"></footer>
  <script src="/assets/v1-shell.js?v=35" defer></script>
</body>
</html>
"""
    return inject_shell_auto(source)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configured_channels(root: Path) -> list[dict]:
    """Canales configurados; admite el formato anterior (`paypal_url`)."""
    path = root / LINKS
    if not path.is_file():
        return []
    config = read_json(path)
    channels = list(config.get("channels") or [])
    if config.get("paypal_url"):
        channels.append({"type": "paypal_link", "url": config["paypal_url"]})
    return channels


def activate(root: Path, channels: list[dict]) -> None:
    validate_config({"channels": channels})
    if not channels:
        raise ValueError("Indica al menos un canal")
    write_json(root / LINKS, {"schema_version": 2, "channels": channels})
    (root / "apoyar").mkdir(exist_ok=True)
    (root / PAGE).write_text(render(channels), encoding="utf-8")
    reg_path = root / "data/content-registry.json"
    registry = read_json(reg_path)
    if not any(e.get("id") == ENTRY_ID for e in registry["entries"]):
        registry["entries"].append(ENTRY)
        write_json(reg_path, registry)
    nav_path = root / "data/navigation.json"
    nav = read_json(nav_path)
    info = nav["footer"]["Información"]
    if ENTRY_ID not in info:
        info.append(ENTRY_ID)
        write_json(nav_path, nav)


def check(root: Path) -> list[str]:
    channels = configured_channels(root)
    registry = read_json(root / "data/content-registry.json")
    nav = read_json(root / "data/navigation.json")
    listed = any(e.get("id") == ENTRY_ID for e in registry["entries"])
    linked = ENTRY_ID in nav["footer"].get("Información", [])
    page = root / PAGE
    if not channels:
        return [f"{what} sin canal de apoyo" for what, on in
                (("apoyar/index.html", page.exists()), ("registro", listed), ("pie", linked)) if on]
    try:
        validate_config({"channels": channels})
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if not page.is_file() or page.read_text(encoding="utf-8") != render(channels):
        errors.append("apoyar/index.html desactualizado: ejecuta scripts/build-support-page.py")
    if not (listed and linked):
        errors.append("falta la entrada del registro o del pie")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add", action="append", default=[], metavar="TIPO=URL",
                        help="Añade un canal: paypal_me, kofi, buymeacoffee, liberapay, paypal_link o stripe")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.add:
        channels = {c["type"]: c for c in configured_channels(ROOT)}
        for item in args.add:
            kind, _, url = item.partition("=")
            validate_channel(kind, url)
            channels[kind] = {"type": kind, "url": url}
        activate(ROOT, list(channels.values()))
        for script in ("build-site-shell.py", "build-sitemap.py", "build-pagefind-index.py"):
            subprocess.run([sys.executable, str(HERE / script)], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(HERE / "check-asset-versions.py"), "--update-hashes"], cwd=ROOT, check=False)
        print("ACTIVADO: /apoyar/ con " + ", ".join(sorted(channels)))
        return 0
    errors = check(ROOT)
    for error in errors:
        print("FAIL " + error)
    if not errors:
        print("PASS: " + ("página de apoyo al día" if configured_channels(ROOT) else "apoyo no activado (sin canales)"))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
