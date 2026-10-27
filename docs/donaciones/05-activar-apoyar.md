# Activar /apoyar/ (cuando exista el enlace de cobro)

Estado: **preparado, no activado**. Sin enlace de cobro no existe la ruta ni se enlaza.

1. En la cuenta **PayPal Business** crea un Payment Link con **Customer-set price** (aportación única). Usa nombre público/comercial, no el personal.
2. Haz una aportación real mínima y comprueba el checkout y el justificante: qué nombre y correo ve el donante.
3. Activa la página con el enlace (`https://www.paypal.com/ncp/payment/ID`):

```
python scripts/build-support-page.py --paypal-url https://www.paypal.com/ncp/payment/ID
```

Genera `apoyar/index.html`, añade `support-project` al registro y a `footer.Información`, y regenera shell, sitemap, Pagefind y hashes de assets. Se sube en una PR.

4. `python scripts/build-support-page.py --check` y `python tests/test-support-release-gate.py` deben pasar.

No se añade SDK de pago, ni pop-ups, ni contadores. La URL se valida solo en su forma; la titularidad y el cobro los comprueba la persona titular.
