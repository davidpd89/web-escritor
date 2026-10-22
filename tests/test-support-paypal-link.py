#!/usr/bin/env python3
"""Contratos offline PayPal Payment Links: no toca red ni ejecuta pagos."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.support_paypal_link import (  # noqa: E402
    render_paypal_support_link,
    validate_paypal_payment_link,
)


def reject(value: object) -> None:
    try:
        validate_paypal_payment_link(value)
    except ValueError:
        return
    raise AssertionError(f"Se aceptó un enlace no permitido: {value!r}")


def main() -> None:
    # Formato tomado de la FAQ oficial de PayPal, NO es enlace del autor.
    example = "https://www.paypal.com/ncp/payment/F3YMU2ZGT49XX"
    assert validate_paypal_payment_link(example) == example
    assert validate_paypal_payment_link(
        "https://paypal.com/ncp/payment/F3YMU2ZGT49XX"
    )
    # PayPal documenta locale.x + country.x para controlar el idioma/país.
    localized = example + "?locale.x=es_ES&country.x=ES"
    assert validate_paypal_payment_link(localized) == localized
    assert validate_paypal_payment_link(
        example + "?country.x=JP&locale.x=ja_JP"
    )
    assert (
        f'href="{example}?locale.x=es_ES&amp;country.x=ES"'
        in render_paypal_support_link(localized)
    )
    assert render_paypal_support_link(None) == ""
    assert render_paypal_support_link("") == ""
    html = render_paypal_support_link(example)
    assert f'href="{example}"' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "PayPal y tarjeta" in html
    assert "<script" not in html and "<iframe" not in html
    assert "href=\"#\"" not in html

    for bad in (
        "http://www.paypal.com/ncp/payment/F3YMU2ZGT49XX",
        "https://www.paypal.com.ejemplo.org/ncp/payment/F3YMU2ZGT49XX",
        "https://paypal.me/nombre",
        "https://www.paypal.com/donate/?hosted_button_id=999",
        "https://www.paypal.com/ncp/payment/",
        "https://www.paypal.com/ncp/payment/ID_OTRO",
        "https://www.paypal.com/ncp/payment/ABC/extra",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=es_ES",
        "https://www.paypal.com/ncp/payment/ABC?country.x=ES",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=es_ES&country.x=ES&foo=bar",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=es_ES&country.x=ES&country.x=JP",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=%0A&country.x=ES",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=es_ES&country.x=ES&",
        "https://www.paypal.com/ncp/payment/ABC?locale.x=es_ES&country.x=ES#fragment",
        "https://www.paypal.com/ncp/payment/ABC#payment",
        "https://seller@www.paypal.com/ncp/payment/ABC",
        "https://www.paypal.com:443/ncp/payment/ABC",
        "https://sandbox.paypal.com/ncp/payment/ABC",
        "https://www.paypal.com/ncp/payment/ABC/",
        "//www.paypal.com/ncp/payment/ABC",
        "javascript:alert(1)",
        " https://www.paypal.com/ncp/payment/ABC",
        "https://www.paypal.com/ncp/payment/ABC ",
        None,
        123,
        "",
    ):
        reject(bad)
    print("support-paypal-link: OK (solo validación offline, no cobro real)")


if __name__ == "__main__":
    main()
