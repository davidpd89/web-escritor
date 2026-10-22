#!/usr/bin/env python3
"""Contratos offline del enlace Stripe (no toca cuentas, red ni CI)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.support_stripe_link import (  # noqa: E402
    render_stripe_support_link,
    validate_stripe_payment_link,
)


def must_reject(url: object, *, production: bool = True) -> None:
    try:
        validate_stripe_payment_link(url, production=production)
    except ValueError:
        return
    raise AssertionError(f"Se aceptó un enlace Stripe inseguro: {url!r}")


def main() -> None:
    live = "https://buy.stripe.com/abcDEF012345"
    test = "https://buy.stripe.com/test_abcDEF012345"

    assert validate_stripe_payment_link(live) == live
    assert validate_stripe_payment_link(test, production=False) == test
    assert render_stripe_support_link(None) == ""
    assert render_stripe_support_link("") == ""

    html = render_stripe_support_link(live)
    assert f'href="{live}"' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "pago único" in html
    assert '<script' not in html and '<iframe' not in html
    assert 'href="#"' not in html
    assert "sk_live_" not in html

    for value in (
        "https://buy.stripe.com/",
        "https://buy.stripe.com/test_abcDEF012345",  # no publicar test
        "https://buy.stripe.com.ejemplo.net/abc123",  # host parecido
        "https://stripe.com/abc123",                  # host no autorizado
        "http://buy.stripe.com/abc123",
        "javascript:alert(1)",
        "//buy.stripe.com/abc123",
        "https://buy.stripe.com:443/abc123",
        "https://user@buy.stripe.com/abc123",
        "https://buy.stripe.com/abc123?prefilled_email=x",
        "https://buy.stripe.com/abc123#ok",
        "https://buy.stripe.com/abc123/extra",
        " https://buy.stripe.com/abc123",
        "https://buy.stripe.com/abc123 ",
        "",
        None,
        42,
    ):
        must_reject(value)
    assert render_stripe_support_link(test, production=False).count('href=') == 1
    print("support-stripe-link: OK (offline; NO confirma enlace activo ni cobro)")


if __name__ == "__main__":
    main()
