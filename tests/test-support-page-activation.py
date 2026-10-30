#!/usr/bin/env python3
"""build-support-page.py: sin canales no hay ruta; con canales válidos cumple el gate de activación."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("build_support_page", "scripts/build-support-page.py")
channels_mod = load("support_channels_test", "scripts/support_channels.py")
gate = load("support_gate", "tests/test-support-release-gate.py")

assert builder.check(ROOT) == [], "el repositorio debe estar coherente: sin canales no hay ruta; con canales, la página al día"
assert gate.release_errors(ROOT) == []

for kind, bad in (("paypal_me", "https://www.paypal.me/ab"), ("paypal_me", "https://www.paypal.me.evil.test/davidp"),
                  ("kofi", "http://ko-fi.com/david"), ("kofi", "https://ko-fi.com/david?x=1"),
                  ("buymeacoffee", "https://www.buymeacoffee.com/"), ("liberapay", "https://liberapay.com/a"),
                  ("paypal_link", "https://www.paypal.com/ncp/payment/ABC?x=1"), ("stripe", "https://buy.stripe.com/test_ABC"),
                  ("desconocido", "https://example.com/x")):
    try:
        channels_mod.validate_channel(kind, bad)
    except ValueError:
        continue
    raise AssertionError(f"canal no válido aceptado: {kind} {bad}")

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "data").mkdir()
    for name in ("content-registry.json", "navigation.json"):
        shutil.copy(ROOT / "data" / name, root / "data" / name)
    channels = [{"type": "paypal_me", "url": "https://www.paypal.me/davidporto"},
                {"type": "kofi", "url": "https://ko-fi.com/davidporto"}]
    builder.activate(root, channels)
    builder.activate(root, channels)  # idempotente
    assert gate.release_errors(root) == [], gate.release_errors(root)
    assert builder.check(root) == []
    html = (root / "apoyar/index.html").read_text(encoding="utf-8")
    assert "noindex" not in html
    # Solo dos botones: PayPal y Ko-fi (este con tarjeta y sin registro). Sin importes ni texto legal.
    cards = re.findall(r'<a class="support-method support-method--([a-z-]+)" href="([^"]+)"', html)
    assert cards == [("paypal-me", "https://www.paypal.me/davidporto"), ("kofi", "https://ko-fi.com/davidporto")], cards
    assert "sin registro" in html.split("support-method--kofi", 1)[1].split("</a>", 1)[0].lower()
    for forbidden in ("support-amount", "Importe", "EUR\"", "aviso-legal", "benéfica", "afiliado", "/privacidad/"):
        assert forbidden not in html.split('<main', 1)[1].split('</main>', 1)[0], forbidden
    assert "Todo es gratis" in html and 'data-family="support"' in html and "/assets/v1-support.css" in html
    registry = json.loads((root / "data/content-registry.json").read_text(encoding="utf-8"))
    assert sum(e["id"] == "support-project" for e in registry["entries"]) == 1
print("PASS: /apoyar/ multicanal solo existe con canales válidos y cumple el gate")
