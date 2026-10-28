"""Canales de apoyo voluntario: validación de forma y render sin SDK, cookies ni scripts de terceros.

Cada canal es un enlace al proveedor; el pago se completa en su web. La forma de la URL
se valida; que la cuenta exista o cobre lo comprueba la persona titular.
"""
from __future__ import annotations

import re
from html import escape
from urllib.parse import urlsplit

from support_paypal_link import validate_paypal_payment_link
from support_stripe_link import validate_stripe_payment_link

AMOUNTS = (2, 5, 10)
HANDLE = r"[A-Za-z0-9_.-]{3,40}"

CHANNELS = {
    "paypal_me": {
        "label": "PayPal", "host": ("www.paypal.me", "paypal.me"), "path": rf"/[A-Za-z0-9]{{3,20}}",
        "blurb": "Con tu cuenta PayPal o con tarjeta. PayPal.me muestra el nombre de la cuenta que recibe.",
    },
    "paypal_link": {
        "label": "PayPal y tarjeta", "blurb": "Elige el importe en PayPal (aportación única).",
    },
    "kofi": {
        "label": "Ko-fi", "host": ("ko-fi.com",), "path": rf"/{HANDLE}",
        "blurb": "Un café, sin registrarte. Ko-fi no cobra comisión propia en aportaciones puntuales.",
    },
    "buymeacoffee": {
        "label": "Buy Me a Coffee", "host": ("www.buymeacoffee.com", "buymeacoffee.com"), "path": rf"/{HANDLE}",
        "blurb": "Un café con tarjeta o PayPal. La plataforma cobra una comisión.",
    },
    "liberapay": {
        "label": "Liberapay", "host": ("liberapay.com",), "path": rf"/{HANDLE}",
        "blurb": "Plataforma sin ánimo de lucro, para aportaciones recurrentes.",
    },
    "stripe": {
        "label": "Tarjeta u otros medios", "blurb": "Elige cuánto aportar en Stripe (pago único).",
    },
}


def validate_channel(kind: str, url: str) -> str:
    """Devuelve la URL validada o lanza ValueError."""
    if kind not in CHANNELS:
        raise ValueError(f"Canal desconocido: {kind!r}")
    if not isinstance(url, str) or not url or url != url.strip():
        raise ValueError(f"{kind}: falta la URL")
    if kind == "paypal_link":
        return validate_paypal_payment_link(url)
    if kind == "stripe":
        return validate_stripe_payment_link(url)
    spec = CHANNELS[kind]
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise ValueError(f"{kind}: URL incorrecta") from exc
    if (parts.scheme != "https" or parts.hostname not in spec["host"] or parts.username or parts.password
            or parts.port not in (None, 443) or parts.query or parts.fragment
            or not re.fullmatch(spec["path"], parts.path, flags=re.ASCII)):
        raise ValueError(f"{kind}: URL no válida")
    return url


def amount_url(kind: str, url: str, amount: int) -> str | None:
    """Solo PayPal.me admite el importe en la ruta: https://www.paypal.me/usuario/5EUR."""
    return f"{url}/{amount}EUR" if kind == "paypal_me" else None


def external(href: str, text: str, label: str, css: str = "support-method") -> str:
    return (f'<a class="{css}" href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="{escape(label, quote=True)}">{text}</a>')


def render_channel(kind: str, url: str) -> str:
    """Un bloque por canal: botón principal y, si procede, importes rápidos."""
    url = validate_channel(kind, url)
    spec = CHANNELS[kind]
    main = external(
        url, f'<strong>{escape(spec["label"])}</strong><span>{escape(spec["blurb"])}</span>',
        f'Apoyar con {spec["label"]}; se abre en otra pestaña')
    quick = ""
    if kind == "paypal_me":
        links = "".join(
            external(amount_url(kind, url, n), f"{n} €", f"Aportar {n} euros con PayPal; se abre en otra pestaña",
                     "support-amount") for n in AMOUNTS)
        quick = f'<p class="support-amounts"><span>Importe rápido:</span> {links}</p>'
    return f'<div class="support-channel">{main}{quick}</div>'


def render_channels(channels: list[dict]) -> str:
    return "".join(render_channel(c["type"], c["url"]) for c in channels)


def validate_config(config: dict) -> list[dict]:
    channels = config.get("channels") or []
    seen: set[str] = set()
    for channel in channels:
        kind, url = channel.get("type"), channel.get("url")
        validate_channel(kind, url)
        if kind in seen:
            raise ValueError(f"Canal repetido: {kind}")
        seen.add(kind)
    return channels
