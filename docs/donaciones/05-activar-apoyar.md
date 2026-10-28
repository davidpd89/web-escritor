# Activar /apoyar/ (varios canales, cuenta personal)

Estado: **preparado, no activado**. Sin ningún canal configurado no existe la ruta `/apoyar/` ni se enlaza (ni el
icono de la cabecera, ni los bloques contextuales).

## Qué hace falta
Un enlace público por cada canal que quieras ofrecer. No hace falta PayPal Business: sirve la cuenta personal.

| Canal | Enlace | Nota |
|---|---|---|
| PayPal.me (cuenta personal) | `https://www.paypal.me/USUARIO` | Se ofrecen importes rápidos (3, 5, 10 €) y uno libre. Es lo más simple. |
| Ko-fi | `https://ko-fi.com/USUARIO` | Pago único o mensual, sin cuota para donaciones. |
| Buy Me a Coffee | `https://www.buymeacoffee.com/USUARIO` | Alternativa a Ko-fi. |
| Liberapay | `https://liberapay.com/USUARIO` | Donaciones recurrentes, sin comisión de plataforma. |
| PayPal Payment Link | `https://www.paypal.com/ncp/payment/ID` | Solo con PayPal Business. |
| Stripe Payment Link | `https://buy.stripe.com/ID` | Solo con cuenta Stripe. |

Bizum no se puede enlazar desde una web (depende del teléfono): no se ofrece.

## Activarlo
Un canal o varios, en una sola orden:

```
python scripts/build-support-page.py --add paypal_me=https://www.paypal.me/USUARIO --add kofi=https://ko-fi.com/USUARIO
```

Genera `apoyar/index.html`, añade `support-project` al registro y al pie («Información»), y regenera shell, sitemap,
Pagefind y hashes de assets. Se sube en una PR.

`python scripts/build-support-page.py --check` y `python tests/test-support-release-gate.py` deben pasar.

## Antes de publicar
1. Haz una aportación real mínima por cada canal y comprueba qué nombre y correo ve el donante.
2. Revisa el texto de `/apoyar/`: describe a quién va el dinero y que no es una compra ni da ventajas.

No hay SDK de pago, ni pop-ups, ni contadores. La URL se valida solo en su forma; la titularidad y el cobro los
comprueba la persona titular.
