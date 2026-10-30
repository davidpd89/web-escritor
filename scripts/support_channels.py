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

HANDLE = r"[A-Za-z0-9_.-]{3,40}"

CHANNELS = {
    "paypal_me": {
        "label": "PayPal", "host": ("www.paypal.me", "paypal.me"), "path": rf"/[A-Za-z0-9]{{3,20}}",
        "blurb": "Si ya tienes cuenta, en dos clics. Tú eliges el importe.", "action": "Donar con PayPal",
    },
    "paypal_link": {
        "label": "PayPal y tarjeta", "blurb": "Elige el importe en PayPal (aportación única).",
        "action": "Donar con PayPal",
    },
    "kofi": {
        "label": "Ko-fi", "host": ("ko-fi.com",), "path": rf"/{HANDLE}",
        "blurb": "¿Prefieres tarjeta y sin registrarte? Invítame a un café en Ko-fi.",
        "action": "Invitar a un café", "badge": "Tarjeta · sin registro",
    },
    "buymeacoffee": {
        "label": "Buy Me a Coffee", "host": ("www.buymeacoffee.com", "buymeacoffee.com"), "path": rf"/{HANDLE}",
        "blurb": "Un café con tarjeta o PayPal.", "action": "Invitar a un café",
    },
    "liberapay": {
        "label": "Liberapay", "host": ("liberapay.com",), "path": rf"/{HANDLE}",
        "blurb": "Plataforma sin ánimo de lucro, para aportaciones recurrentes.", "action": "Apoyar en Liberapay",
    },
    "stripe": {
        "label": "Tarjeta", "blurb": "Elige cuánto aportar con tarjeta (pago único).", "action": "Donar con tarjeta",
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


def external(href: str, inner: str, label: str, css: str = "support-method") -> str:
    return (f'<a class="{css}" href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="{escape(label, quote=True)}">{inner}</a>')


def render_channel(kind: str, url: str) -> str:
    """Una tarjeta por canal: toda la tarjeta es el enlace, sin importes prefijados."""
    url = validate_channel(kind, url)
    spec = CHANNELS[kind]
    badge = f'<span class="support-method__badge">{escape(spec["badge"])}</span>' if spec.get("badge") else ""
    inner = (f'{badge}<strong class="support-method__name">{escape(spec["label"])}</strong>'
             f'<span class="support-method__text">{escape(spec["blurb"])}</span>'
             f'<span class="support-method__action" aria-hidden="true">{escape(spec["action"])}</span>')
    return external(url, inner, f'{spec["action"]} ({spec["label"]}); se abre en otra pestaña',
                    f"support-method support-method--{kind.replace('_', '-')}")


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
