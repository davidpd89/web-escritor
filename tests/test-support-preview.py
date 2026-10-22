#!/usr/bin/env python3
"""La preview de apoyo permanece privada y sin métodos de pago.

Sin servicios ni cuentas externas; usa el builder y el shell existentes.
"""
from __future__ import annotations

import importlib.util
import json
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
    registry = json.loads((ROOT / "data" / "content-registry.json").read_text(encoding="utf-8"))
    nav = json.loads((ROOT / "data" / "navigation.json").read_text(encoding="utf-8"))

    assert '<meta name="robots" content="noindex,nofollow,noarchive"' in html
    assert html.count('<h1 id="support-title">') == 1
    assert '<main id="contenido"' in html
    assert html.count('class="site-footer"') == 1
    assert '<header class="site-header"' in html
    assert '<dialog class="explore-dialog"' in html
    assert 'href="https://davidportodiaz.com/apoyar/"' in html
    assert '<meta http-equiv="Content-Security-Policy"' in html

    # Sin enlace de pago, sin formulario, sin éxito falso ni inclusión de SDK.
    assert "Los métodos de pago todavía no están configurados" in html
    assert not re.search(r'href="https?://(?:[^/]*\.)?(?:paypal\.com|stripe\.com|ko-fi\.com)', source)
    assert '<form' not in source
    assert 'paypalobjects.com' not in source
    assert 'sk_live_' not in source
    assert 'hosted_button_id' not in source
    assert 'role="status"' in source
    assert '/privacidad.html' in source and '/aviso-legal.html' in source

    # Este archivo generado vive solo en lab, nunca en el artefacto público.
    assert builder.OUTPUT == ROOT / "lab" / "donaciones-preview" / "index.html"
    assert not (ROOT / "apoyar" / "index.html").exists()
    assert not any(e["url"] == "/apoyar/" for e in registry["entries"])
    assert not any("support-project" in ids for ids in nav["footer"].values())

    # El generador real mantiene la exclusión explícita de lab/.
    spec_public = importlib.util.spec_from_file_location(
        "build_public_dist", ROOT / "scripts" / "build-public-dist.py"
    )
    assert spec_public and spec_public.loader
    public = importlib.util.module_from_spec(spec_public)
    spec_public.loader.exec_module(public)
    assert not public.is_publishable("lab/donaciones-preview/index.html", ROOT)

    print("support-preview: OK (shell real, noindex y cero checkout; sin publicación)")


if __name__ == "__main__":
    main()
