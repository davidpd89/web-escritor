# Auditoría final de cierre · 27/08/2026

**Base exacta:** `main@f03fb12630d7ce0005f6b1bd5fa188b2def83d5e` (merge de PR #129).  
**Objetivo:** responder una sola pregunta: qué falta realmente antes de poder decir «la tanda técnica está terminada» sin confundir documentación, CI verde parcial, configuración externa y comportamiento probado.

## Veredicto

**Todavía no está todo cerrado.** Quedan cuatro bloques técnicos obligatorios, dos bloques operativos externos que el ledger mantiene abiertos y un gate futuro de lanzamiento. Cloudflare y la auditoría de cuenta/UI de Search Console se consideran cerrados según la evidencia operativa aportada por el propietario y no se reabren aquí.

Esta PR no debe convertirse en una bolsa infinita de mejoras. Solo contiene residuos ya demostrados o estados que las propias autoridades del repo marcan como pendientes.

---

## 1. P0 · CLS sitewide por `.section-context` post-paint

### Evidencia reproducible

El HEAD final de #129 (`7020995...`) ejecutó Lighthouse 3 veces por URL. Dos rutas fallaron el budget duro `cumulative-layout-shift <= 0.1`:

- `/herramientas/`: `0.1383315936568492` en **3/3** runs;
- `/herramientas/manuscrito/`: `0.1383315936568492` en **3/3** runs.

PR #133, cuyo único cambio es un grid de Samuel, vuelve a producir exactamente los mismos dos fallos y exactamente el mismo valor en 3/3 runs. Por tanto el fallo:

- está presente en `main`;
- no fue causado por #133;
- no es ruido de una ejecución aislada;
- no quedó resuelto por #129.

### Causa más probable, consistente con #129

`assets/v1-editorial-interior-v4.js::buildContextNav()` inserta `.section-context` después del header cuando el JS ya corre. #129 demostró que esa inserción post-paint era causa de CLS y pre-renderizó varias rutas.

`/herramientas/` sigue llegando sin `.section-context` en el HTML inicial y la obtiene por runtime. Además ese HTML declara que es generado por `scripts/build-tools-hub.py`. Arreglar el fichero generado a mano sería incorrecto.

### Solución requerida

No hacer otro parche de «dos URLs» manuales. Resolver el patrón de manera sistémica:

1. identificar **todas** las rutas públicas que `buildContextNav()` clasifica en un contexto y que todavía dependen de inserción post-paint;
2. elegir una autoridad única para generar/pre-renderizar el componente antes del primer paint;
3. incluir builders/generadores (`scripts/build-tools-hub.py` y los que correspondan), no editar outputs a mano;
4. mantener el algoritmo de `aria-current` de #129 (máximo uno, exact > prefijo más específico);
5. ampliar `qa/section-context-parity.mjs` para cubrir las nuevas rutas/generadores;
6. medir Lighthouse de `/herramientas/` y `/herramientas/manuscrito/` 3/3 tras el fix;
7. revisar otras familias (`autor`, `prensa`, `editoriales`, `convocatorias`, etc.) para que el cierre sea de patrón, no de muestra.

### Definition of Done

- [ ] ninguna ruta pública con contexto añade una barra completa post-paint sin espacio estable;
- [ ] Herramientas y Manuscrito tienen CLS <=0.1 en 3/3 Lighthouse runs;
- [ ] parity QA cubre las variantes pre-renderizadas/generadas;
- [ ] builders `--check` pasan;
- [ ] CSP/Pa11y/Reflow/Cross-engine/Runtime verdes;
- [ ] no copias manuales sin contrato de paridad.

**Owner recomendado:** PR propia `fix/section-context-first-paint-sitewide-*`.

---

## 2. P0 · Samuel todavía tiene un residual de reflow bajo 200% de texto

PR #133 corrige correctamente un bug concreto:

```css
.samuel-route-list li { grid-template-columns: 2.2rem 1fr }
```

pasa a:

```css
.samuel-route-list li { grid-template-columns: 2.2rem minmax(0,1fr) }
```

El repro de #133 confirma ~53px -> 0 para ese componente.

Pero la propia PR registra **~19px de overflow todavía presente** en el bloque de testimonios/blockquote bajo el mismo modo de 200% de texto.

### Gap de cobertura descubierto

`qa/sitewide-reflow-browser.mjs` está verde pese a esos fallos porque su modo principal aplica:

```js
document.documentElement.style.zoom = '2'
```

mientras el repro fiel de Samuel utiliza:

```css
html.qa-text-200 { font-size: 200% !important }
```

No son equivalentes. El hecho de que el sitewide gate pase mientras el repro `font-size:200%` encuentra 53px/19px lo demuestra empíricamente.

### DoD de #133 / Samuel

- [ ] identificar selector exacto del residual testimonial ~19px;
- [ ] corregir sin clipping, `overflow-x:hidden` ni reducción artificial de tipografía;
- [ ] añadir un QA CI que use `font-size:200%` real, no solo CSS `zoom`;
- [ ] 390px + 200% texto: <=1px overflow para los componentes Samuel auditados;
- [ ] mantener también el sitewide reflow actual; ambos modos son complementarios.

PR #133 debe permanecer DRAFT hasta esto.

---

## 3. P0 · Política de merge no debe aceptar un hard check rojo conocido

La tanda ha demostrado un hueco de gobernanza distinto del ya corregido en #130.

#130 incorporó todos los `tests/test-*.py` y `tests/*.mjs` al context requerido `Required merge gate`. Eso cerró el caso en que Tool engine tests podía estar rojo mientras el gate requerido estaba verde.

Pero Lighthouse es una suite browser pesada separada. #129 fue mergeada con Lighthouse rojo y #133 aparece mergeable con Lighthouse rojo porque Lighthouse no es uno de los cuatro contexts requeridos por el ruleset.

No hay que convertir automáticamente cada workflow path-filtered en required context: eso puede bloquear PRs donde el check no se crea. Hay que diseñar una solución que preserve señal sin crear deadlocks.

### Opciones aceptables a evaluar

- integrar en `Required merge gate` un contrato determinista ligero para los bugs de layout que deban ser universales;
- crear un aggregate merge-readiness estable que recoja las suites obligatorias aplicables sin carreras;
- convertir Lighthouse en workflow siempre presente si se decide que su budget duro es universal;
- mantener Lighthouse fuera del ruleset pero codificar una política de agente verificable que prohíba merge con un check hard-failure no clasificado, con excepción explícita/documentada para flaky/infra.

### DoD

- [ ] demostrar Caso B real: un **required** check rojo bloquea el merge;
- [ ] decidir/documentar qué significa «CI verde» para checks no-required;
- [ ] una PR con Lighthouse hard-failure reproducible no puede declararse lista sin owner/clasificación;
- [ ] no añadir required contexts condicionales que queden eternamente `Expected`;
- [ ] evaluar `strict_required_status_checks_policy=false` con PRs concurrentes y decidir conscientemente si exigir base actualizada.

No cambiar el ruleset live sin autorización explícita.

---

## 4. P0/P1 · PR #120 Claude Toolbox sigue sin cerrar

Estado en este corte:

- OPEN + DRAFT;
- HEAD `21024e468675025693af94954451a6b189844dc7`;
- contra `main@f03fb126...`: `status=diverged`, `ahead_by=18`, `behind_by=5`.

Pendientes propios:

1. refrescar contra main actual;
2. revalidar cada `INSTALL_NOW` contra fuente primaria exacta;
3. eliminar fuentes/comandos `reverify`/genéricos de items declarados verificados;
4. resolver Chrome DevTools MCP vs Playwright MCP como default/fallback o justificar ambos con eval;
5. resolver alcance real de TypeScript LSP/Pyright sin configuración de proyecto;
6. alinear GitHub plugin con merge autorizado condicionado a checks, no prohibición absoluta de «automatic merge»;
7. reconciliar duplicados con `docs/design-ux-tooling/tools-catalog.json`;
8. enlazar las autoridades posteriores de supply-chain y Node24.

#120 no debe absorber fixes web, Cloudflare, Search Console, Brevo ni secretos.

---

## 5. P1 · GitHub Actions todavía usa Actions con runtime Node 20 deprecado

Autoridad existente: `docs/ci/GITHUB-ACTIONS-NODE24-MIGRATION-2026-08-27.md`.

Los propios runs actuales siguen mostrando el warning:

```text
Node 20 is being deprecated. This workflow is running with Node 24 by default.
```

En Lighthouse aparecen, entre otras:

- `actions/checkout@v4`;
- `actions/setup-node@v4`;
- `actions/upload-artifact@v4`.

No está roto hoy, pero la migración documentada sigue con DoD completamente pendiente. Abrir PR propia después de cerrar los P0 de layout.

No hacer reemplazo global ciego. Inventario, release notes, workflows normales primero, workflows sensibles/deploy/required después, CI y rollback.

---

## 6. P1 · supply-chain npm todavía no tiene autoridad advisory-by-advisory

Autoridad existente: `docs/supply-chain/NPM-AUDIT-BASELINE-2026-08-27.md`.

Estado honesto:

- audit observado: 13 vulnerabilities (2 low, 1 moderate, 10 high);
- investigación previa: transitivas de tooling CI/dev; no se identificó ruta explotable en el uso observado;
- no había fix seguro que justificase `npm audit fix --force`;
- **pero faltan** IDs/rangos/paths/reachability/decisión/owner/reviewBy por advisory.

DoD ya definido en ese documento y todavía sin marcar. No llamar a este frente «cerrado» hasta repetir `npm audit --json` en HEAD actual o recuperar/normalizar el detalle real y versionarlo.

---

## 7. Operacional externo · Brevo aún contiene dos journeys `BLOCKED`

El ledger actual mantiene explícitamente:

- `brevo-beta-worker-routing` → `BLOCKED`;
- `brevo-newsletter-samuel-chapter-delivery` → `BLOCKED`.

El snapshot live sí está corregido y la lista beta existe; eso no prueba:

- binding correcto del Worker a lista 6 + deploy + alta beta aislada E2E;
- DOI/automation/entrega real del capítulo prometido tras suscripción.

Si estos journeys ya fueron probados después del último snapshot, actualizar ledger con evidencia sanitizada. Si no, siguen siendo pendientes reales. No inventar cierre a partir de que Cloudflare DNS esté terminado: DNS/zone y Workers/Brevo son capas distintas.

---

## 8. Gate futuro inevitable · Manecillas 03/09/2026

`manecillas-launch-state-2026-09-03` está implementado en `main`, pero su `nextAction` ocurre el **3 de septiembre de 2026 o después**.

Hasta esa fecha no puede haberse ejecutado honestamente la transición final de lanzamiento.

En la fecha:

1. ejecutar/checkear `scripts/apply-manecillas-launch-state.py` según el runbook;
2. verificar retailer/purchase URL/disponibilidad comercial real antes de publicar `Offer`/compra;
3. comprobar sitemap/robots/canonical/structured data del estado final;
4. registrar la anotación/evento de Search Console si forma parte del runbook de lanzamiento;
5. probar el funnel público final.

Esto no significa que el código actual esté mal; significa que el proyecto tiene un gate temporal aún no ejecutable.

---

## 9. Cerrado y NO reabrir sin nueva evidencia

### Cloudflare

Según la verificación operativa aportada por el propietario: nameservers propagados, zona activa, 13/13 DNS, sitio/redirect/DKIM/DMARC correctos y PR #131/#132 mergeadas. No reabrir desde esta auditoría.

Activar proxy/nube naranja en el futuro sería una decisión nueva de producto/infra, no un bug pendiente.

### Search Console · cuenta/UI

Según la auditoría operativa aportada por el propietario: sitemap reenviado y 27→58 páginas descubiertas, 10 no-indexadas clasificadas correctamente, seguridad/manual actions limpias, robots válido, GenAI incluido y baseline de rendimiento/enlaces revisado. No reabrir esa fase.

El plan PR #110 también documenta BigQuery/API automation. **Si el propietario decide que esas capas avanzadas no son necesarias ahora, marcarlas explícitamente DEFER/OPTIONAL en el ledger/backlog en vez de fingir CONFIGURED_LIVE.** La ausencia de BigQuery/API no invalida el cierre de la cuenta/UI de Search Console.

### También cerrados

No hay evidencia para reabrir #117, #119, #122, #123, #124, #125, #127, #128, #130, #131, #132 por sus alcances ya corregidos. #129 está mergeada pero deja el residual sitewide de `.section-context` descrito en §1; no revertir sus mejoras.

---

## 10. Mantenimiento no bloqueante para «fin de tanda»

El ledger conserva una segunda ronda de repo-hygiene `REVIEW/ARCHIVE-CANDIDATE`. Es mantenimiento útil, pero no debe impedir declarar terminada esta tanda una vez cerrados los P0/P1 anteriores, siempre que siga con owner/criterio y no haya secretos/artefactos peligrosos.

La decisión Chrome DevTools MCP vs Playwright MCP pertenece a #120, no al runtime web.

---

## Orden de ejecución para Claude

1. **PR sitewide section-context CLS**: Herramientas/Manuscrito y todas las rutas afectadas; 3/3 Lighthouse verdes.
2. **#133 Samuel**: residual testimonial + QA real `font-size:200%`; después merge si todo verde.
3. **Gobernanza CI**: definir hard-red policy/Caso B/strict-up-to-date sin romper checks condicionales.
4. **#120 Toolbox**: refresh + revalidación material y merge.
5. **Supply-chain**: advisory-by-advisory + baseline machine-readable/CI si aporta señal.
6. **GitHub Actions Node24**: migración controlada de majors.
7. **Brevo**: cerrar o retirar/narrow las dos promesas/journeys BLOCKED con E2E real.
8. **03/09**: ejecutar gate de lanzamiento Manecillas.

## Criterio final para poder decir «terminado»

La tanda puede darse por terminada cuando:

- no quede ningún bug reproducible P0/P1 sin owner;
- todas las PR de implementación de esta lista estén mergeadas o explícitamente DEFER con razón;
- no haya hard CI failure conocido en el HEAD que se pretende mergear;
- Toolbox deje de estar draft;
- supply-chain/Actions tengan decisiones durables, aunque alguna advisory quede aceptada temporalmente con `reviewBy`;
- los dos journeys Brevo estén VERIFIED_E2E o la promesa pública correspondiente se haya retirado/estrechado;
- y, tras el 03/09, el launch gate se haya ejecutado con hechos comerciales reales.

Hasta entonces la frase correcta es: **«la mayor parte de la infraestructura y de las auditorías está cerrada, pero quedan residuos finales concretos y trazables»**.