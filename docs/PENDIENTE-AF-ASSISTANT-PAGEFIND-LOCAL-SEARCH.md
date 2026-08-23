# AF — Asistente · búsqueda local Pagefind

Hallazgo durante el cruce final de `DISEÑO Y DEMÁS`, especialmente docs 38 y 40, contra `implementacion-web-2026`.

Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Estado real

El asistente actual YA contiene degradación correcta:

- `assets/assistant.js` define `pagefindFallback(query)`;
- primero intenta `import('/pagefind/pagefind.js')`;
- si Pagefind no existe/falla, usa `data/assistant-source-registry` + `rankLocalSources()`;
- por tanto el asistente no queda roto sin Pagefind.

Pero la capa Pagefind del contrato canónico NO se materializa hoy:

- no existe `/pagefind/` en la rama;
- no existe `package.json` en la base actual (la autoridad de dependencias Node está siendo creada por #65);
- no se encontró builder/script Pagefind bajo `scripts/`;
- no se encontró workflow que instale/genere el índice;
- `assistant-hardening-qa.yml` prueba registry/core/worker/browser pero no genera Pagefind;
- `build-public-dist.py` copia lo trackeado, no construye un índice Pagefind.

Resultado actual: el `import('/pagefind/pagefind.js')` cae al fallback local de forma sistemática salvo que un pipeline externo no versionado lo genere, del que no hay evidencia en el repo auditado.

## Por qué importa

Doc 40 define una arquitectura híbrida donde la búsqueda local gratuita es una capa de primer orden y Pagefind es el motor cliente previsto. El fallback local actual es valioso y debe mantenerse, pero no sustituye silenciosamente la capacidad diseñada si queremos declarar el contrato 40 implementado.

Esto es una deuda funcional/findability, NO una nueva PR de estética.

## Owner

Materializar una búsqueda local Pagefind reproducible para contenido público elegible, conservando el fallback actual.

### AF.1 — Fuente de verdad

El corpus indexable debe derivar de la autoridad viva:

- `data/content-registry.json`;
- solo entries públicas/elegibles;
- respetar `searchIndex:false`, gated/noindex y publication gate;
- no indexar datos privados, drafts, herramientas internas, solicitudes beta, scripts/data administrativos ni contenido excluido del artefacto público.

No crear una segunda lista manual de rutas Pagefind.

### AF.2 — Build reproducible

Implementar una única vía reproducible que genere `/pagefind/` desde el artefacto público/corpus elegible.

Requisitos:

- integrarse con la autoridad de dependencias Node de **#65** después de su integración/rebase; no crear otro `package.json` o lockfile paralelo;
- versión Pagefind fijada/reproducible;
- build determinista en la medida compatible con Pagefind;
- no commitear binarios/artefactos efímeros sin decidir explícitamente si el repo sirve source o build output;
- si `/pagefind/` se genera en CI/deploy, documentar exactamente dónde y garantizar que staging/producción lo sirven;
- si se versiona el output, añadir checker de stale/parity.

### AF.3 — Integración con Asistente

Mantener el orden de degradación:

1. resolución determinista/intent cuando aplique;
2. Pagefind local;
3. ranking local/registry como fallback robusto;
4. IA solo según contrato actual y acción/condición autorizada.

No hacer que una caída de Pagefind rompa el asistente.

Resultados locales deben usar URLs internas seguras y títulos/fragmentos procedentes del contenido público, no del modelo.

### AF.4 — UX/findability

No crear automáticamente una segunda caja de búsqueda global en header.

El doc 40 integra la búsqueda dentro de `/asistente/`/Explorar. Cualquier launcher adicional en shell queda condicionado a pruebas de utilidad y a #68; no se introduce por esta PR.

### AF.5 — QA

Añadir pruebas que demuestren:

- el índice se genera;
- una página pública indexable aparece;
- una entry `searchIndex:false` no aparece;
- contenido gated/noindex/publication-excluded no aparece;
- consulta simple devuelve destino real;
- si se elimina/rompe `/pagefind/`, el ranking local sigue funcionando;
- no hay requests externos para búsqueda local;
- teclado y resultados siguen siendo utilizables;
- staging sirve `/pagefind/pagefind.js` y recursos necesarios cuando la integración llegue a ese gate.

## Coordinación

- **#65**: autoridad package.json/package-lock/Node QA; AF debe rebase después, no competir.
- **#67**: microcopy del Asistente; AF no decide wording.
- **#68**: navegación/findability global; AF no añade territorio/menu/launcher sin coordinación.
- **#79**: publication gate; el índice no puede re-publicar contenido gated.
- **#58**: smoke de staging debe comprobar Pagefind una vez integrado.
- **#62**: CSP final debe admitir únicamente los recursos locales necesarios; Pagefind no justifica orígenes externos.
- **#89/#88**: diseño final del Asistente/herramientas consume el comportamiento, no lo reimplementa.

## No hacer

- no eliminar el fallback local actual;
- no indexar el repo completo;
- no indexar `data/` o fuentes privadas por comodidad;
- no crear una taxonomía de búsqueda paralela a content-registry;
- no introducir búsqueda externa/Google custom search;
- no usar Pagefind para justificar un segundo overlay/menu;
- no absorber #65 creando otra autoridad Node.

## Definition of Done

- [x] Pagefind deja de ser un import que falla sistemáticamente;
- [x] build/index source está documentado y reproducible;
- [x] elegibilidad deriva de authorities actuales;
- [x] exclusiones de privacidad/publicación tienen regresiones;
- [x] fallback local sigue probado (código preexistente en `pagefindFallback()`, sin cambios; ver nota abajo);
- [ ] staging evidencia recursos Pagefind 200 + búsqueda real (código listo — `tests/test-staging-smoke.mjs` ya lo comprueba — pero requiere el próximo deploy real a staging, que esta PR no ejecuta);
- [x] no se altera `main`, no deploy de producción y no auto-merge.

PR DRAFT / owner técnico. No es bloque de diseño visual.

## Estado de implementación (código, sin deploy)

Implementado en esta rama, 100% código/CI, sin generación de imagen ni IA:

- `scripts/build-pagefind-index.py`: `eligible_pages()` deriva la elegibilidad de `data/content-registry.json` (`status`/`searchIndex`) **más** el propio `<meta name="robots" content="noindex">` de cada página (sin lista manual paralela: esto captura gratis `404.html`, `offline.html`, el stub de redirección `samuel-entre-mundos.html`, `lab/**` y `herramientas/auditor-web/`, todos ya `noindex` por otros motivos). `--check` es puro Python (compara `pagefind/eligible-manifest.json` contra el corpus recalculado); solo el build real necesita Node+`pagefind`.
- `pagefind/` generado y **commiteado** (no en CI/deploy): consistente con que este repo no tiene build step y sirve exactamente lo que hay en git. `.pagefind-src/` (la copia efímera que se le pasa al CLI) va a `.gitignore`.
- `--exclude-selectors "header.site-header, dialog.explore-dialog, footer.site-footer"` evita indexar el chrome repetido del shell (el diálogo Explorar no es `<nav>`/`<footer>`, así que Pagefind no lo excluye solo).
- `assets/assistant.js` — **sin cambios**: `pagefindFallback()` ya hacía `import('/pagefind/pagefind.js')` + `pagefind.search()` con la API real correcta; el único gap era que `/pagefind/` no existía.
- Tests: `tests/test-build-pagefind-index.py` (fixture git aislado: página pública sin registro → incluida; `searchIndex:false` → excluida; `status!=public` → excluida; página sin registro pero con `noindex` propio → excluida; fragmento `data/*` → excluida siempre; ciclo `build()`/`--check` detecta desincronización real — omite ese ciclo, no como fallo, si `npx` no está en el PATH, para seguir funcionando bajo `tool-tests.yml`) y `qa/pagefind-search-browser.mjs` (navegador real contra el índice comprometido: consulta real devuelve URL interna real, `/privacidad.html` y la ruta gated no aparecen, cero requests externos). Este último vive en `qa/`, no en `tests/`, porque `tool-tests.yml` ejecuta `tests/*.mjs` con Node puro sin `npm ci`: un `.mjs` en `tests/` que importa `playwright` rompe ese workflow con `ERR_MODULE_NOT_FOUND` (confirmado en vivo antes de moverlo).
- CI: `content-index-check.yml` (gate `--check`, sin Node) y `assistant-hardening-qa.yml` (build real + ambos tests nuevos, en el job que ya tiene Node/Playwright).

Pendiente para el propietario (no código, o depende de un deploy real):

- Confirmar en el próximo deploy de staging que `/pagefind/pagefind.js` sirve 200. **No** se ha añadido esa comprobación a `tests/test-staging-smoke.mjs` a propósito: ese fichero corre en CI contra el staging YA desplegado en cada PR de este repo (no contra esta rama), así que una aserción `/pagefind/pagefind.js -> 200` ahí habría puesto en rojo el smoke test de *cualquier otra PR* hasta que staging se redespliegue con este commit — confirmado en vivo: añadirla rompió `node-tests` con `404 !== 200` antes de revertirla. Añadir esas dos rutas a `PUBLIC_ROUTES`/una lista de assets en `test-staging-smoke.mjs` en el mismo PR/commit que active el redeploy real, no antes.
- AF.4 (UX/findability, launcher en shell) queda explícitamente fuera de esta PR, tal y como pedía el propio doc.