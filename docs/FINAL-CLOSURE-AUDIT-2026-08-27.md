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

### CORRECCIÓN 28/08/2026 — la hipótesis de causa de abajo es incorrecta, verificado

Sesión de Claude del 28/08/2026: comprobé directamente `herramientas/index.html` y `herramientas/manuscrito/index.html` (`grep -n "section-context\|editorial-interior-v4"`) y **ninguna de las dos páginas carga `assets/v1-editorial-interior-v4.js` ni contiene `.section-context` en ningún sitio**. Sus únicos scripts son `/assets/v1-shell.js`, `/script.js` y `/assets/herramientas-hub.js`. `buildContextNav()` nunca se ejecuta en estas páginas — no puede ser la causa.

El patrón de #129 (inserción post-paint de `.section-context`) **no aplica aquí**. La causa real de los 0.1383 de CLS está en otro componente — casi con toda seguridad en `assets/herramientas-hub.js` (que renderiza/filtra el grid de 22 tarjetas de herramientas) o en el hero/cabecera de `scripts/build-tools-hub.py`. **No asumir la causa: instrumentar con `PerformanceObserver('layout-shift')` en local contra `/herramientas/` para identificar qué elemento concreto se mueve y en qué momento del ciclo de carga**, antes de proponer ningún fix.

### Causa original hipotetizada (no confirmada, mantenida solo como referencia histórica — no usar)

~~`assets/v1-editorial-interior-v4.js::buildContextNav()` inserta `.section-context`...~~ — descartada por la corrección de arriba, y luego **la corrección de arriba también resultó incorrecta** (ver RESOLUCIÓN abajo). Se deja toda la cadena visible a propósito: el error real no fue la hipótesis original, fue el método usado para descartarla.

### RESOLUCIÓN 28/08/2026 — `.section-context` sí era la causa; el grep de la corrección anterior tenía un punto ciego

Sesión de Claude del 28/08/2026 (posterior a la corrección de arriba, misma fecha): instrumenté `/herramientas/` en vivo con `PerformanceObserver('layout-shift')` tal y como pedía el punto 1 de la solución de abajo, en vez de seguir razonando desde un grep estático. Resultado: **un único shift de 0.128**, `source: MAIN#contenido.v1-main`, con `main` empujado 122px hacia abajo y la altura del `.site-header` sin cambiar entre el frame anterior y el posterior — exactamente la firma de "algo se insertó entre header y main después del primer paint", no un reflow del propio grid de tarjetas.

La corrección de arriba comprobó correctamente que **el HTML fuente** de `herramientas/index.html` no referencia `v1-editorial-interior-v4.js` ni contiene `.section-context` — pero de ahí concluyó que el script nunca corre en esta página, y esa inferencia era el error: `assets/v1-shell.js` (que sí carga toda página V1 vía `<script defer src="/assets/v1-shell.js">`) inyecta `v1-editorial-interior-v4.js` **dinámicamente** en runtime (`document.head.append(script)` dentro de `initLrbHeaderV2()`), sin dejar ningún rastro en el HTML fuente. Un `grep` del HTML nunca iba a encontrarlo. Comprobado leyendo `assets/v1-shell.js` línea por línea: `loadScript(EDITORIAL_INTERIOR_SRC, 'editorialInteriorV4')` se llama incondicionalmente, no solo en Home.

Y dentro de `v1-editorial-interior-v4.js`, el array `contexts` **sí** tiene una entrada `herramientas` (`matches: path.startsWith('/herramientas/') || ...`) que #129 nunca pre-renderizó — solo pre-renderizó `samuel` (3 páginas) y `cuaderno` (2 páginas). `herramientas`, `obras`, `autor`, `prensa` y `manecillas` se quedaron dependiendo de la inserción JS post-paint, el mismo patrón que #129 arregló para las otras 5.

Escaneando las 7 entradas de `contexts` contra las rutas reales del sitio (comparando cada `<link rel="canonical">` contra las mismas reglas de match): **55 páginas** tenían este patrón, no 2. Arreglado en [PR #138](https://github.com/davidpd89/web-escritor/pull/138) con un builder nuevo (`scripts/build-section-context-nav.py`, mismo contrato marcador + `--check` que `build-site-shell.py`) que pre-renderiza el nav para las 55, más `scripts/site_shell.py` actualizado para que los 6 builders que generan algunas de esas páginas (editoriales, radar, temas del Cuaderno, writer-tools, tools-hub, autores-red) lo apliquen también desde su propio `inject_shell_auto()`, y `qa/section-context-parity.mjs` generalizado para descubrir las páginas desde git en vez de una lista de 5 hardcodeada.

Verificado tras el fix: `PerformanceObserver('layout-shift')` devuelve `[]` en `/herramientas/`, `/herramientas/manuscrito/` y `/autor.html`; los 4 puntos de la solución de abajo quedan resueltos por esa PR. **No fue necesario tocar `assets/herramientas-hub.js` ni `scripts/build-tools-hub.py`** — la hipótesis de la corrección anterior sobre esos ficheros tampoco era correcta.

**Lección para la próxima sesión que dude si un script "corre" en una página:** un grep del HTML fuente solo ve `<script src>` estático; no ve `document.createElement('script')`/`.append()` en runtime. Comprobar con `PerformanceObserver`/DevTools en vivo antes de descartar un componente por su ausencia en el HTML.

### Solución requerida (histórico — resuelta por PR #138, ver RESOLUCIÓN arriba)

No hacer otro parche de «dos URLs» manuales. Resolver el patrón de manera sistémica:

1. instrumentar `/herramientas/` y `/herramientas/manuscrito/` con `PerformanceObserver('layout-shift')` para identificar el elemento/selector exacto que causa el shift — **hecho, ver RESOLUCIÓN arriba: sí era `.section-context`**;
2. una vez identificada la causa real, decidir si es un patrón compartido con otras páginas o específico del hub de herramientas — **compartido, 55 páginas**;
3. si toca HTML generado, arreglar el builder (`scripts/build-tools-hub.py` y los que correspondan), no editar outputs a mano — **hecho vía `site_shell.py`, no tocó `build-tools-hub.py` directamente**;
4. si el trabajo de #129 sobre `.section-context`/`aria-current` resulta relevante en otras rutas (`autor`, `prensa`, `editoriales`, `convocatorias`), tratarlo como un frente aparte — **resuelto en la misma PR, no aparte, por ser la misma causa raíz**;
5. ampliar `qa/section-context-parity.mjs` solo si la causa real resulta estar relacionada con ese componente — **sí lo estaba; generalizado a descubrimiento por git**;
6. medir Lighthouse de `/herramientas/` y `/herramientas/manuscrito/` 3/3 tras el fix — **PerformanceObserver en vivo confirma 0 shifts; pendiente de que CI vuelva a correr Lighthouse tras mergear #138 para el número oficial 3/3**.

### Definition of Done

- [x] ninguna ruta pública con contexto añade una barra completa post-paint sin espacio estable (las 55 páginas con contexto quedan pre-renderizadas en #138);
- [ ] Herramientas y Manuscrito tienen CLS <=0.1 en 3/3 Lighthouse runs (verificado 0 shifts vía `PerformanceObserver` local; falta la corrida oficial de Lighthouse en CI tras mergear #138);
- [x] parity QA cubre las variantes pre-renderizadas/generadas (generalizada a 55 páginas descubiertas por git);
- [x] builders `--check` pasan (`build-site-shell.py`, `build-section-context-nav.py`, y los 6 builders de página que ahora comparten `inject_shell_auto()`);
- [ ] CSP/Pa11y/Reflow/Cross-engine/Runtime verdes (no re-ejecutados en esta pasada, solo `tests/*.{py,mjs}` + parity QA);
- [x] no copias manuales sin contrato de paridad (generado por script, no a mano).

**Owner recomendado:** PR propia `fix/section-context-first-paint-sitewide-*` — abierta como [PR #138](https://github.com/davidpd89/web-escritor/pull/138).

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

### Verificación en vivo 28/08/2026 — confirma que sigue BLOCKED, y por qué

El propietario pidió expresamente completar "lo pendiente de la migración" sobre Brevo. Antes de tocar nada en producción, verifiqué el estado real:

- **El Worker `subscribe.davidpd89.workers.dev` vive en `workers.dev`, no en una ruta de zona** (`script.js` línea 17: `endpoint: "https://subscribe.davidpd89.workers.dev"`). Los subdominios `workers.dev` no dependen de que exista una zona Cloudflare para el dominio — **la migración DNS de hoy no desbloquea nada aquí**. La columna "Cloudflare" del ledger se refería a que crear bindings/secrets/deploy requiere el dashboard de Cloudflare (categoría de actor `CLOUDFLARE` del backlog), no a la zona DNS.
- `curl -X POST` con `Origin: https://davidportodiaz.com` y payload `{email, source:"home"}` devolvió `400 {"message":"Missing required fields"}` — **ese mensaje no existe en el código actual del repo** (`cloudflare-worker-subscribe.js` solo devuelve `"Solicitud no válida."`, `"Dirección de email no válida."`, `"Origen de suscripción no válido."`). Conclusión dura: **el Worker desplegado en producción es una versión antigua, anterior a la reescritura DOI/`lectores-beta` de PENDIENTE-B (23/08/2026). El paso "deploy" del backlog nunca se ha ejecutado con el código actual.**
- En el dashboard de Brevo (cuenta real, vía navegador ya autenticado): la lista **`Lectores beta` existe con ID `#6`**, creada 27/08/2026, 0 contactos — coincide con lo que ya decía este documento. **No existe ningún template marcado/reconocible como DOI** en Transaccional → Plantillas: las 4 plantillas activas son `Bienvenida_Samuel_Email1` (×2), `Bienvenida_Samuel_Email2` — la secuencia de bienvenida del capítulo, no un email de confirmación de doble opt-in.
- La API key `BREVO_API_KEY` guardada en `.env` de este repo devuelve `401 Unauthorized` contra `api.brevo.com` — está caducada o no es la misma que la que Cloudflare tiene como secret. No usable para automatizar esto sin renovarla en el propio dashboard de Brevo.

**No se ha desplegado ni configurado nada en esta pasada.** Falta una decisión de contenido (texto del email DOI) y de producto (qué automatización dispara el capítulo prometido) que no me correspondía inventar solo con un "hazlo" genérico sobre "lo pendiente de la migración" — porque, verificado, nada de esto estaba realmente pendiente de la migración. Sigue exactamente `BLOCKED`, con la causa real ahora documentada en vez de asumida.

**Antes de que otra sesión toque esto, necesita del propietario:** (1) confirmar/crear un template Brevo real para el email de confirmación DOI y decidir su copy, (2) decidir qué automatización de Brevo entrega el capítulo de Samuel tras la confirmación, (3) renovar `BREVO_API_KEY` si se quiere automatizar la creación del template vía API en vez de a mano en el dashboard.

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