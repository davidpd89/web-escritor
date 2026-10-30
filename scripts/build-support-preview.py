#!/usr/bin/env python3
"""Vista previa NO PUBLICABLE de /apoyar/ con el shell editorial real.

La salida va exclusivamente a lab/donaciones-preview/, excluido del sitio.
No acepta ni genera URLs de cobro; activación en otra PR tras prueba del receptor.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_ROOT = ROOT / "lab" / "donaciones-preview"
OUTPUT = PREVIEW_ROOT / "index.html"


def render_preview_source() -> str:
    """HTML fuente, sin repetir header/footer. El generador de shell los rellena."""
    return """<!DOCTYPE html>
<html lang="es" class="v1">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="noindex,nofollow,noarchive" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <!-- Canonical técnico: el bridge del shell deriva /apoyar/ desde este campo.
       La preview es noindex y vive fuera del árbol público. -->
  <link rel="canonical" href="https://davidportodiaz.com/apoyar/" />
  <title>Apoya este proyecto — vista previa | David Porto Díaz</title>
  <meta name="description" content="Vista previa local del apoyo voluntario al contenido gratuito." />
  <meta name="theme-color" content="#F4EFE7" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="stylesheet" href="/assets/v1-fonts.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-tokens.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-base.css?v=2" />
  <link rel="stylesheet" href="/assets/v1-shell.css?v=8" />
  <link rel="stylesheet" href="/assets/v1-components.css?v=3" />
  <style>
    .support-preview{width:min(calc(100% - 2rem),44rem);margin:clamp(2rem,6vw,5rem) auto}
    .support-preview h1{font-size:clamp(2.4rem,6vw,4rem);line-height:1.06}
    .support-preview__lead{font-size:clamp(1rem,2vw,1.2rem);line-height:1.7}
    .support-preview__status{margin-block:2rem;padding:1rem 0;
      border-top:1px solid var(--color-border);border-bottom:1px solid var(--color-border)}
    .support-preview__status p{margin:.4rem 0;color:var(--color-muted)}
    .support-preview__legal{font-size:.9rem;color:var(--color-muted)}
  </style>
</head>
<body data-back-to-top>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>
  <header class="site-header" data-header></header>
  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>
  <main id="contenido" class="v1-main" tabindex="-1">
    <section class="support-preview" aria-labelledby="support-title">
      <p class="eyebrow">Colaboración voluntaria</p>
      <h1 id="support-title">Apoya este proyecto</h1>
      <p class="support-preview__lead">Las herramientas, las guías y los recursos
        de esta web son gratuitos. Si te han servido, puedes contribuir a
        mantenerlos y ayudar a crear otros nuevos.</p>
      <div class="support-preview__status" role="status">
        <strong>Vista previa para revisión</strong>
        <p>Los métodos de pago todavía no están configurados. No se ha activado
          ningún cobro.</p>
      </div>
      <p class="support-preview__legal">Cuando se active, la aportación será
        voluntaria y única, y el pago se completará en el proveedor elegido.
        Esta web no recogerá datos de tarjeta.</p>
      <p><a href="/privacidad.html">Privacidad</a> ·
        <a href="/aviso-legal.html">Aviso legal</a></p>
    </section>
  </main>
  <footer class="site-footer"></footer>
  <script src="/assets/v1-shell.js" defer></script>
</body>
</html>
"""


def render_preview() -> str:
    """Aprovecha el shell del repositorio, sin copiar 100 cabeceras o pies."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from site_shell import inject_shell_auto  # pylint: disable=import-outside-toplevel

    # La ruta de esta preview es LOCAL: no se registra en sitemap ni navigation.
    return inject_shell_auto(render_preview_source())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verifica la vista previa sin escribir")
    args = parser.parse_args()
    html = render_preview()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != html:
            print("FAIL: genera la preview con python scripts/build-support-preview.py", file=sys.stderr)
            return 1
        print("OK: preview local actualizada, sin métodos de pago")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"PREVIEW LOCAL: {OUTPUT.relative_to(ROOT)} (no pública, sin cobro)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
