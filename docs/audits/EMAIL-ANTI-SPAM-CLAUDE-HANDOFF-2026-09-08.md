# Handoff para Claude — cerrar protección anti-spam del correo

La PR contiene runtime + auditor + tests + contrato. Falta migrar los dos owners grandes con hunks mínimos.

## Haz esto

1. Actualiza la rama sobre `main` actual.
2. En `scripts/build-site-shell.py`:
   - elimina el correo literal `AUTHOR_EMAIL`;
   - elimina `obfuscated_mailto()` basado en entidades HTML;
   - genera en footer un trigger `[data-email-reveal]` con fallback `/prensa.html#contacto`;
   - carga `/assets/email-reveal.js?v=1` una sola vez.
3. Regenera el shell, sin reemplazar manualmente HTML generado página por página.
4. En `prensa.html`, sustituye TODOS los `mailto:` codificados por triggers `data-email-reveal` y conserva los subjects actuales mediante `data-email-subject`.
5. No pongas el email en `aria-label`, `title`, JSON-LD, comentarios o `data-*`.
6. Ejecuta `python scripts/audit-public-email-exposure.py --strict`.
7. Si da findings, corrige owners; no añadas allowlist para conseguir verde.
8. Cuando dé 0, añade el modo strict al gate transversal/Required merge gate que corresponda.
9. Browser QA: footer + prensa, pointer/keyboard, no-JS, 320/390, Resize Text 200 %, foco y subjects.
10. CI completo + smoke post-deploy mirando el HTML fuente público.

## No hacer

- No CAPTCHA/Turnstile solo para revelar el correo.
- No formulario server-side nuevo en esta PR.
- No sustituir el email por una imagen.
- No CSS-generated content para el email: perjudica accesibilidad.
- No afirmar que esto elimina el spam; reduce scraping estático.
- No whole-file rewrite de `build-site-shell.py`, `prensa.html` o JS globales.

## Cierre

Solo cerrar/mergear cuando:

`STATIC_EXPOSURES=0 · FOOTER_MIGRATED · PRESS_MIGRATED · NO_JS_OK · A11Y_OK · CI_GUARD=true · VERIFIED_LIVE_POST_DEPLOY`
