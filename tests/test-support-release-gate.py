#!/usr/bin/env python3
"""Contrato de activación de /apoyar/ sin pagos de prueba ni red.

Hay dos estados válidos:
1) No activado: no existe la ruta ni se enlaza en navegación.
2) Activado: el registry declara página pública, existe HTML correcto,
   el pie la enlaza y hay un enlace PayPal/Stripe con forma válida.

Una URL con forma válida NO demuestra que cobre el titular. La revisión del
checkout/recibo y el pago real son puertas HUMANAS posteriores.
"""
from __future__ import annotations

import json
import re
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
GATED = {"noindex", "internal", "gated", "deprecated"}
PAYPAL_PATH = re.compile(r"/ncp/payment/[A-Za-z0-9]+", re.ASCII)
STRIPE_PATH = re.compile(r"/[A-Za-z0-9_-]+", re.ASCII)


class SupportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.methods: list[dict[str, str]] = []
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.external_payment_scripts: list[str] = []

    def handle_starttag(self, tag: str, raw: list[tuple[str, str | None]]) -> None:
        attrs = dict(raw)
        if tag == "a" and "support-method" in (attrs.get("class") or "").split():
            self.methods.append({k: v or "" for k, v in attrs.items()})
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href") or "")
        if tag == "meta" and attrs.get("name") == "robots":
            self.robots.append(attrs.get("content") or "")
        if tag == "script":
            src = attrs.get("src") or ""
            if any(name in src for name in ("paypalobjects.com", "stripe.com", "ko-fi.com")):
                self.external_payment_scripts.append(src)


def payment_link_valid(url: str) -> bool:
    if not url or url != url.strip():
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme != "https" or parts.query or parts.fragment:
        return False
    if parts.netloc in {"www.paypal.com", "paypal.com"}:
        return bool(PAYPAL_PATH.fullmatch(parts.path))
    if parts.netloc == "buy.stripe.com":
        token = parts.path.removeprefix("/")
        return bool(STRIPE_PATH.fullmatch(parts.path)) and not token.startswith("test_")
    return False


def release_errors(root: Path) -> list[str]:
    registry = json.loads((root / "data/content-registry.json").read_text(encoding="utf-8"))
    nav = json.loads((root / "data/navigation.json").read_text(encoding="utf-8"))
    entries = [e for e in registry.get("entries", []) if e.get("id") == "support-project"]
    footer = nav.get("footer", {})
    occurrences = [(group, pos) for group, ids in footer.items()
                   for pos, value in enumerate(ids) if value == "support-project"]
    page = root / "apoyar" / "index.html"
    errors: list[str] = []

    if len(entries) > 1:
        errors.append("support-project duplicado en registry")
    if not entries:
        if page.exists() or occurrences:
            errors.append("Ruta o navegación de apoyo sin contrato en registry")
        return errors

    entry = entries[0]
    if entry.get("url") != "/apoyar/" or entry.get("sourceFile") != "apoyar/index.html":
        errors.append("La fuente/canonical de support-project debe ser /apoyar/")
    status = entry.get("status", registry.get("defaults", {}).get("status", "public"))
    if status != "public":
        if status not in GATED:
            errors.append(f"Estado no protegido por build-public-dist.py: {status}")
        if occurrences:
            errors.append("Nunca enlazar una página todavía gated/noindex")
        return errors

    # Publicar una entrada de registry sin HTML falla también en el dist real.
    if not page.is_file():
        errors.append("support-project público sin apoyar/index.html")
        return errors
    if occurrences != [("Información", footer.get("Información", []).index("support-project"))]:
        errors.append("La página pública debe aparecer una sola vez en footer.Información")

    parser = SupportParser()
    html = page.read_text(encoding="utf-8")
    parser.feed(html)
    if parser.canonicals != ["https://davidportodiaz.com/apoyar/"]:
        errors.append("Canonical incorrecto o duplicado")
    if not parser.robots or any("noindex" in item.lower() for item in parser.robots):
        errors.append("Página pública debe tener robots indexable")
    if not parser.methods:
        errors.append("No publicar una página vacía sin método de pago")
    for item in parser.methods:
        if not payment_link_valid(item.get("href", "")):
            errors.append("Método de pago sin URL HTTPS PayPal/Stripe oficial")
        if item.get("target") == "_blank" and not {"noopener", "noreferrer"}.issubset(
            item.get("rel", "").split()
        ):
            errors.append("El enlace en otra pestaña exige noopener noreferrer")
    if parser.external_payment_scripts:
        errors.append("No cargar SDK de pago externo en V1")
    if any(secret in html for secret in ("sk_live_", "sk_test_", "hosted_button_id=")):
        errors.append("Marcador de credenciales/SDK prohibido en HTML")
    if "href=\"/privacidad.html\"" not in html or "href=\"/aviso-legal.html\"" not in html:
        errors.append("Enlaces de privacidad y aviso legal ausentes")
    return errors


VALID_HTML = """<!doctype html><html lang="es"><head>
<link rel="canonical" href="https://davidportodiaz.com/apoyar/">
<meta name="robots" content="index,follow">
</head><body>
<h1>Apoya el proyecto</h1>
<a class="support-method" href="https://www.paypal.com/ncp/payment/ABC123"
 target="_blank" rel="noopener noreferrer">PayPal</a>
<a href="/privacidad.html">Privacidad</a><a href="/aviso-legal.html">Aviso legal</a>
</body></html>"""


def fixture_tests() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "data").mkdir()
        (root / "apoyar").mkdir()
        registry = {"defaults": {"status": "public"}, "entries": []}
        nav = {"footer": {"Información": []}}

        def write() -> None:
            (root / "data/content-registry.json").write_text(
                json.dumps(registry), encoding="utf-8")
            (root / "data/navigation.json").write_text(
                json.dumps(nav), encoding="utf-8")

        write()
        assert release_errors(root) == []  # No activado
        page = root / "apoyar/index.html"
        page.write_text(VALID_HTML, encoding="utf-8")
        assert release_errors(root)  # Ruta accidental sin entry: BLOQUEAR
        entry = {"id": "support-project", "url": "/apoyar/",
                 "sourceFile": "apoyar/index.html", "status": "gated"}
        registry["entries"].append(entry)
        write()
        assert release_errors(root) == []  # Staging no enlazado, bloqueado por registry
        entry["status"] = "draft"
        write()
        assert release_errors(root)  # Estado no reconocido no protege
        entry["status"] = "public"
        write()
        assert release_errors(root)  # Sin footer: BLOQUEAR
        nav["footer"]["Información"].append("support-project")
        write()
        assert release_errors(root) == []  # Activación estructural correcta
        page.write_text(VALID_HTML.replace("www.paypal.com", "www.paypal.com.evil.test"), encoding="utf-8")
        assert release_errors(root)
        page.write_text(VALID_HTML.replace("ABC123", "ABC123?unsafe=1"), encoding="utf-8")
        assert release_errors(root)
        page.write_text(VALID_HTML.replace("index,follow", "noindex,follow"), encoding="utf-8")
        assert release_errors(root)
        page.write_text(VALID_HTML.replace("https://www.paypal.com/ncp/payment/ABC123",
                                          "https://buy.stripe.com/test_ABC123"), encoding="utf-8")
        assert release_errors(root)
        page.write_text(VALID_HTML, encoding="utf-8")
        assert release_errors(root) == []


if __name__ == "__main__":
    fixture_tests()
    issues = release_errors(ROOT)
    assert not issues, "\n".join(issues)
    print("support-release-gate: OK (fixture privado/activo y repo; no verifica cobro real)")
