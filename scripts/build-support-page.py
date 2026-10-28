#!/usr/bin/env python3
"""Activa o comprueba la página pública /apoyar/ (aportación voluntaria).

Sin enlace de cobro configurado no existe la ruta ni se enlaza en la web. El
titular crea un PayPal Payment Link «Customer-set price» en su cuenta Business
y lo registra aquí; la forma de la URL se valida, la titularidad no.

Uso:
  python scripts/build-support-page.py --paypal-url https://www.paypal.com/ncp/payment/ID
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
from support_paypal_link import render_paypal_support_link, validate_paypal_payment_link  # noqa: E402

LINKS = "data/support-links.json"
PAGE = "apoyar/index.html"
ENTRY_ID = "support-project"
ENTRY = {
    "id": ENTRY_ID, "url": "/apoyar/", "label": "Apoya este proyecto", "shortLabel": "Apoyar el proyecto",
    "type": "system", "territory": "sitio", "parentId": "home", "hubId": "home",
    "discoverability": "secondary", "footerEligible": True, "audience": ["reader", "writer"],
    "jobs": ["apoyar"], "sourceFile": PAGE, "status": "public",
}
DESCRIPTION = (
    "Las herramientas, las guías y los recursos de esta web se ofrecen gratis. Si te han resultado útiles "
    "y quieres ayudar a mantenerlos y crear otros nuevos, puedes hacer una aportación voluntaria."
)


def render(paypal_url: str) -> str:
    methods = render_paypal_support_link(paypal_url)
    source = f"""<!doctype html>
<html lang="es" class="v1">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <link rel="canonical" href="https://davidportodiaz.com/apoyar/" />
  <title>Apoya este proyecto | David Porto Díaz</title>
  <meta name="description" content="{DESCRIPTION}" />
  <meta name="theme-color" content="#ffffff" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="stylesheet" href="/assets/v1-fonts.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-tokens.css?v=1" />
  <link rel="stylesheet" href="/assets/v1-base.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-shell.css?v=6" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=3" />
  <link rel="stylesheet" href="/assets/v1-support.css?v=1" />
</head>
<body data-back-to-top>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>
  <header class="site-header" data-header></header>
  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>
  <main id="contenido" class="v1-main" tabindex="-1" data-family="support">
    <section class="support-page" aria-labelledby="support-title">
      <p class="eyebrow">Aportación voluntaria</p>
      <h1 id="support-title">Apoya este proyecto</h1>
      <p class="support-page__lead">{DESCRIPTION} Gracias por leer y utilizar este espacio.</p>
      <div class="support-methods">{methods}</div>
      <p class="support-page__note">El pago se completa en la plataforma elegida. Nosotros no recogemos datos de tarjeta en esta web.</p>
      <p class="support-page__legal">La aportación es voluntaria y única, no da acceso a ningún contenido extra ni es una donación benéfica. Esta web también incluye enlaces de afiliado de Amazon, como se explica en el aviso legal.</p>
      <p class="support-page__legal"><a href="/privacidad.html">Privacidad</a> · <a href="/aviso-legal.html">Aviso legal</a></p>
    </section>
  </main>
  <footer class="site-footer"></footer>
  <script src="/assets/v1-shell.js" defer></script>
</body>
</html>
"""
    return inject_shell_auto(source)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configured_url(root: Path) -> str:
    path = root / LINKS
    return (read_json(path).get("paypal_url") or "") if path.is_file() else ""


def activate(root: Path, url: str) -> None:
    validate_paypal_payment_link(url)
    write_json(root / LINKS, {"schema_version": 1, "paypal_url": url})
    (root / "apoyar").mkdir(exist_ok=True)
    (root / PAGE).write_text(render(url), encoding="utf-8")
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
    url = configured_url(root)
    registry = read_json(root / "data/content-registry.json")
    nav = read_json(root / "data/navigation.json")
    listed = any(e.get("id") == ENTRY_ID for e in registry["entries"])
    linked = ENTRY_ID in nav["footer"].get("Información", [])
    page = root / PAGE
    if not url:
        return [f"{what} sin enlace de cobro" for what, on in
                (("apoyar/index.html", page.exists()), ("registro", listed), ("pie", linked)) if on]
    try:
        validate_paypal_payment_link(url)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if not page.is_file() or page.read_text(encoding="utf-8") != render(url):
        errors.append("apoyar/index.html desactualizado: ejecuta scripts/build-support-page.py")
    if not (listed and linked):
        errors.append("falta la entrada del registro o del pie")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paypal-url")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.paypal_url:
        activate(ROOT, args.paypal_url)
        for script in ("build-site-shell.py", "build-sitemap.py", "build-pagefind-index.py"):
            subprocess.run([sys.executable, str(HERE / script)], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(HERE / "check-asset-versions.py"), "--update-hashes"], cwd=ROOT, check=False)
        print("ACTIVADO: /apoyar/ con el enlace de PayPal indicado")
        return 0
    errors = check(ROOT)
    for error in errors:
        print("FAIL " + error)
    print("PASS: " + ("página de apoyo al día" if configured_url(ROOT) else "apoyo no activado (sin enlace de cobro)") if not errors else "")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
