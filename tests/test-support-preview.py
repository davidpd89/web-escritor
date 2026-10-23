#!/usr/bin/env python3
"""La preview de apoyo permanece privada y sin métodos de pago.

Sin servicios ni cuentas externas; usa el builder y el shell existentes.
"""
from __future__ import annotations

import importlib.util
import tempfile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_FILE = ROOT / "scripts" / "build-support-preview.py"
SPEC = importlib.util.spec_from_file_location("build_support_preview", BUILD_FILE)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def main() -> None:
    source = builder.render_preview_source()
    html = builder.render_preview()  # shell auténtico, no markup fingido

    assert '<meta name="robots" content="noindex,nofollow,noarchive"' in html
    assert html.count('<h1 id="support-title">') == 1
    assert '<main id="contenido"' in html
    assert html.count('class="site-footer"') == 1
    assert '<header class="site-header"' in html
    assert '<dialog class="explore-dialog"' in html
    assert 'href="https://davidportodiaz.com/apoyar/"' in html
    assert '<meta http-equiv="Content-Security-Policy"' in html

    # El shell añade el formulario EXISTENTE de newsletter a Explorar.
    # Comprobar el contenido real renderizado: nunca un checkout dentro de main.
    assert '<form class="explore-subscribe"' in html
    main_match = re.search(
        r'<main\b[^>]*\bid="contenido"[^>]*>(.*?)</main>',
        html,
        flags=re.I | re.S,
    )
    assert main_match, "Debe mantenerse el contenido principal"
    main_html = main_match.group(1)
    assert not re.search(r'<form\b', main_html, flags=re.I), (
        "La sección de apoyo no debe incorporar formularios de pago"
    )
    assert not re.search(
        r'href="https?://(?:[^/]*\.)?(?:paypal\.com|stripe\.com|ko-fi\.com)',
        main_html, flags=re.I
    ), "La vista previa no debe contener enlaces de cobro"
    assert "Los métodos de pago todavía no están configurados" in html
    assert not re.search(r'href="https?://(?:[^/]*\.)?(?:paypal\.com|stripe\.com|ko-fi\.com)', source)
    assert '<form' not in source
    assert 'paypalobjects.com' not in html
    assert 'js.stripe.com' not in html
    assert 'sk_live_' not in html
    assert 'hosted_button_id' not in html
    assert 'role="status"' in source
    assert '/privacidad.html' in source and '/aviso-legal.html' in source

    # Este archivo generado vive solo en lab, nunca en el artefacto público.
    assert builder.OUTPUT == ROOT / "lab" / "donaciones-preview" / "index.html"
    # No prohibir aquí una activación futura correcta de /apoyar/.
    # Los estados de publicación se validan en test-support-release-gate.py.

    # El generador real mantiene la exclusión explícita de lab/.
    spec_public = importlib.util.spec_from_file_location(
        "build_public_dist", ROOT / "scripts" / "build-public-dist.py"
    )
    assert spec_public and spec_public.loader
    public = importlib.util.module_from_spec(spec_public)
    spec_public.loader.exec_module(public)
    assert not public.is_publishable("lab/donaciones-preview/index.html", ROOT)

    # Un prototipo olvidado SIN meta noindex tampoco puede contaminar el
    # sitemap de producción. Antes collect_urls() recorría lab/ sin excluirla.
    spec_sitemap = importlib.util.spec_from_file_location(
        "build_sitemap", ROOT / "scripts" / "build-sitemap.py"
    )
    assert spec_sitemap and spec_sitemap.loader
    sitemap = importlib.util.module_from_spec(spec_sitemap)
    spec_sitemap.loader.exec_module(sitemap)
    assert "lab" in sitemap.EXCLUDE_DIRS
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp)
        control = fixture / "control" / "index.html"
        control.parent.mkdir(parents=True)
        control.write_text(
            '<link rel="canonical" href="https://davidportodiaz.com/control/" />',
            encoding="utf-8",
        )
        preview = fixture / "lab" / "donaciones-preview" / "index.html"
        preview.parent.mkdir(parents=True)
        preview.write_text(
            '<link rel="canonical" href="https://davidportodiaz.com/apoyar/" />',
            encoding="utf-8",
        )
        sitemap_urls = sitemap.collect_urls(fixture)
        # El control prueba que el walker funciona: sin él, "ausente" sería vacuo.
        assert "https://davidportodiaz.com/control/" in sitemap_urls
        assert "https://davidportodiaz.com/apoyar/" not in sitemap_urls

    print("support-preview: OK (shell real, noindex y cero checkout; sin publicación)")


if __name__ == "__main__":
    main()
