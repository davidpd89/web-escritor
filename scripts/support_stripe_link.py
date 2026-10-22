"""Render mínimo de enlace Stripe Payment Links para la futura página /apoyar/.

Sin SDK, cookies, iframe, API ni backend. No confirma pagos.
Importar desde el generador de la página de apoyo, pasando la URL del Dashboard.
"""
from __future__ import annotations

import re
from html import escape
from urllib.parse import urlsplit


def validate_stripe_payment_link(url: str, *, production: bool = True) -> str:
    """Devuelve una URL alojada en Stripe y validada, o lanza ValueError.

    La URL completa la proporciona Stripe; no construimos identificadores,
    importes, emails, destinos de retorno ni parámetros de tracking.
    """
    if not isinstance(url, str) or not url or url != url.strip():
        raise ValueError("Falta una URL Stripe real y sin espacios")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "buy.stripe.com"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Usa exclusivamente el enlace HTTPS oficial de buy.stripe.com")
    token = parsed.path.removeprefix("/")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", token, flags=re.ASCII):
        raise ValueError("Ruta de Payment Link no válida")
    if production and token.startswith("test_"):
        raise ValueError("Un enlace de prueba Stripe no se puede publicar como pago real")
    return url


def render_stripe_support_link(url: str | None, *, production: bool = True) -> str:
    """Sin URL configurada no aparece botón, nunca un enlace ficticio."""
    if url is None or url == "":
        return ""
    href = escape(validate_stripe_payment_link(url, production=production), quote=True)
    return (
        '<a class="support-method support-method--stripe" '
        f'href="{href}" target="_blank" rel="noopener noreferrer" '
        'aria-label="Hacer una aportación única con tarjeta u otros medios. '
        'Se abre el pago seguro de Stripe en otra pestaña">'
        '<strong>Tarjeta u otros medios</strong>'
        '<span>Elige cuánto aportar en Stripe (pago único)</span>'
        '</a>'
    )
