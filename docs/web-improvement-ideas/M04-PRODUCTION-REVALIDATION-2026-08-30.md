# M.4 · Revalidación de producción · monitor periódico

Fecha: 2026-08-30  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`IMPLEMENTED_IN_PR · EXISTING_SMOKE_REUSED · PERIODIC_GITHUB_MONITOR · EXTERNAL_SAAS_STILL_CONDITIONAL`

La primera fase recomendada por #135 ya queda implementada en esta PR: observar producción periódicamente reutilizando el mismo smoke GET-only que el deploy ejecuta después de publicar.

## Owner existente confirmado

`main` ya contiene:

- `.github/workflows/deploy-pages.yml`;
- `tests/test-staging-smoke.mjs`;
- `.github/workflows/staging-smoke-test.yml`.

`deploy-pages.yml` despliega el artefacto allowlist-first a GitHub Pages y, después del deploy, ejecuta `tests/test-staging-smoke.mjs` contra `https://davidportodiaz.com` con identidad exacta del SHA.

El mismo test se usa a diario contra staging.

No hacía falta crear otro checker.

## Implementación de M.4

Se añade únicamente `.github/workflows/production-smoke-monitor.yml`.

Características:

- `schedule` cada 6 horas (`17 */6 * * *`);
- `workflow_dispatch`;
- validación en PR cuando cambia el workflow o el smoke compartido;
- Node 22;
- reutiliza `tests/test-staging-smoke.mjs`;
- target `https://davidportodiaz.com`;
- no define `EXPECTED_RELEASE_SHA`, porque su objetivo entre deploys es disponibilidad/contrato público, no demostrar qué commit acaba de publicarse;
- dos intentos con 30 segundos de separación para reducir falsos positivos transitorios;
- sin secrets;
- sin mutaciones/formularios;
- sin SDK cliente.

## Qué observa el smoke compartido

El test realiza únicamente GET y comprueba:

- cinco rutas públicas críticas → HTTP 200 + `<title>`;
- rutas internas que nunca deben publicarse → HTTP 404;
- `robots.txt`, `sitemap.xml` y `llms.txt`;
- JSON-LD y canonical en Home/Manecillas;
- validación TLS normal del runtime de Node;
- resolución/red implícita: un fallo DNS/TLS/timeout hace fallar el smoke.

No proporciona aviso anticipado de expiración de certificado; detecta rotura TLS cuando el handshake deja de ser válido. Un servicio externo especializado seguiría aportando valor si se desea aviso preventivo e independencia de GitHub Actions.

## Evidencia

HEAD de implementación validado: `48868bd776d6e8996e8dbfd332223128aea24741`.

Primer run del nuevo workflow:

- `Production smoke monitor` run `33325912154` → `success`.

En el mismo HEAD también terminaron `success`:

- Required merge gate;
- Public artifact contract;
- Check content indexes;
- Analytics taxonomy QA;
- Runtime scoping QA;
- CSP public shell QA;
- Accessibility baseline (Pa11y);
- Sitewide Reflow QA.

## Qué sigue siendo condicional

UptimeRobot u otro proveedor externo solo se justifica si se quiere una segunda capa independiente de GitHub Actions y existe:

```text
operational owner
alert destination
account maintenance
alert drill
clear response path
```

`CONFIGURED_LIVE` de un proveedor externo no puede inferirse ni crearse correctamente desde esta PR sin esas decisiones.

## Qué NO hacer

- no crear un segundo script de smoke;
- no insertar RUM/SDK en las páginas;
- no ejecutar formularios ni endpoints mutables;
- no monitorizar cientos de URLs;
- no crear cuenta externa por checklist;
- no convertir un fallo transitorio único en arquitectura compleja;
- no confundir este monitor GitHub-hosted con independencia de proveedor.

## Estado final

La capa first-party programada queda implementada y probada. La capa externa independiente permanece `CONDITIONAL` y debe activarse solo como decisión operativa consciente.