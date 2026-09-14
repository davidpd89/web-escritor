# Checklist de integración — email anti-spam

Esta checklist existe para que la implementación no se quede en documentación/runtime sin conectar.

- [x] Runtime local `assets/email-reveal.js` añadido.
- [x] Auditor `scripts/audit-public-email-exposure.py` añadido.
- [x] Unit tests del auditor añadidos.
- [x] Threat model y contrato de accesibilidad documentados.
- [ ] `scripts/build-site-shell.py`: retirar `AUTHOR_EMAIL` plaintext.
- [ ] `scripts/build-site-shell.py`: retirar `obfuscated_mailto()` por entidades HTML.
- [ ] `scripts/build-site-shell.py`: footer usa `[data-email-reveal]` con fallback `/prensa.html#contacto`.
- [ ] `scripts/build-site-shell.py`: runtime cargado una sola vez en páginas V1.
- [ ] Regenerar shell completo.
- [ ] `prensa.html`: migrar todos los mailto codificados a triggers sin destino estático.
- [ ] `prensa.html`: preservar subjects de cada CTA.
- [ ] `prensa.html`: eliminar dirección visible estática de la tarjeta de portada.
- [ ] Scan de cualquier otra superficie pública.
- [ ] `python scripts/audit-public-email-exposure.py --strict` = 0 findings.
- [ ] Añadir el modo strict a CI transversal.
- [ ] Browser QA pointer + teclado.
- [ ] Browser QA no-JS.
- [ ] Browser QA 320/390 + Resize Text 200 %.
- [ ] Pa11y verde.
- [ ] Sitewide Reflow verde.
- [ ] CSP public shell verde.
- [ ] `build-site-shell.py --check` verde.
- [ ] Smoke post-deploy: source HTML público no contiene dirección/mailto codificado.
- [ ] `VERIFIED_LIVE` solo después del smoke de producción.
