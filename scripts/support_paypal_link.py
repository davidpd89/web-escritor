"""Enlace PayPal Payment Links sin SDK para la futura página /apoyar/.

Solo acepta la ruta /ncp/payment/ que PayPal documenta para enlaces alojados.
No verifica que la cuenta, el enlace o el importe estén activos: la prueba real
se hace en el Dashboard y en el checkout, antes de publicarlo.
"""
from __future__ import annotations

import re
from html import escape
from urllib.parse import urlsplit

PAYPAL_HOSTS = frozenset({"www.paypal.com", "paypal.com"})
PAYPAL_LINK_PATH = re.compile(r"/ncp/payment/[A-Za-z0-9]+", re.ASCII)


def validate_paypal_payment_link(url: str) -> str:
    """Valida la forma del enlace, nunca su titularidad o disponibilidad."""
    if not isinstance(url, str) or not url or url != url.strip():
        raise ValueError("Falta la URL real de PayPal Payment Links")
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise ValueError("URL PayPal incorrecta") from exc
    if (
        parsed.scheme != "https"
        or parsed.netloc not in PAYPAL_HOSTS
        or parsed.query
        or parsed.fragment
        or not PAYPAL_LINK_PATH.fullmatch(parsed.path)
    ):
        raise ValueError("Solo se admite https://www.paypal.com/ncp/payment/ID_REAL")
    return url


def render_paypal_support_link(url: str | None) -> str:
    """No crea un botón si no existe una URL configurada."""
    if url is None or url == "":
        return ""
    href = escape(validate_paypal_payment_link(url), quote=True)
    return (
        '<a class="support-method support-method--paypal" '
        f'href="{href}" target="_blank" rel="noopener noreferrer" '
        'aria-label="Apoyar con PayPal o tarjeta; se abre PayPal en otra pestaña">'
        '<strong>PayPal y tarjeta</strong>'
        '<span>Elige el importe en PayPal (aportación única)</span>'
        '</a>'
    )
