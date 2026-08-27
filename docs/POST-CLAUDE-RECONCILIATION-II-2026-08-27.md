# Reconciliación II posterior a Claude · 27/08/2026

**Snapshot auditado de `main`:** `cc6a2466f42fec5af134fc66885f9cc8378298e3` (merge de #128)  
**Objetivo:** separar lo realmente cerrado de lo meramente mergeado/documentado, corregir estados obsoletos y dejar owners/DoD inequívocos para la siguiente pasada de Claude.

## 1. Resumen ejecutivo

La tanda #114–#128 mejoró materialmente el repositorio. No hay evidencia para reabrir #117, #119, #122, #123 o #124. #116 también está correctamente implementada en cuanto a release identity y deploy: el `main@cc6a...` ejecutó build, deploy y verificación posterior del release público exacto con éxito.

Lo que sí quedó desalineado es la **verdad operativa** alrededor de esos merges:

- #120 fue refrescada y está `behind_by=0`, pero su descripción y parte del corpus todavía contaban una historia anterior;
- #126 activó un ruleset real, pero la evidencia llama «Caso A real» a un push que el harness bloqueó antes de llegar a GitHub;
- #127 unificó Playwright, pero `docs/design-ux-tooling/14-FUENTES...` y `package.json` siguen describiendo el drift como situación presente;
- #128 arregló tres assumptions del QA de Home, pero rebajó el contrato de touch target de los **42 px que el CSS implementa deliberadamente** a los 24 px mínimos de WCAG; eso deja pasar una regresión visual/UX desde 42 a 24;
- #129 existe y está verde, por lo que el resumen «#120 es la única PR abierta» ya no es verdad. La auditoría posterior detectó blockers semánticos/mantenibilidad y #129 se ha vuelto a dejar en draft.

## 2. Estado PR por PR

### #114 — diseño/UX/tooling

**Estado:** mergeada; corpus estructuralmente completado después por #125.  
**No reabrir implementación.**

Pendiente real de mantenimiento:

- `14-FUENTES-Y-ESTADO-2026-08-27.md` quedó obsoleto tras #127: todavía presenta Playwright 1.55 ad-hoc como pendiente de unificar;
- la disponibilidad de un MCP «en una sesión» es una observación fechada, no estado de proyecto;
- la decisión Chrome DevTools MCP vs Playwright MCP como vía canónica de QA de diseño sigue abierta y debe resolverse en #120, no creando otro catálogo.

### #115 — repo hygiene

**Estado:** mergeada para su ronda 1.  
La regresión que introdujo (#123 restauró `/herramientas/auditor-web/` y `/publicar-web/`) está cerrada y #125 reforzó el trigger de CI.

Pendiente no urgente: segunda ronda fichero a fichero de `REVIEW/ARCHIVE-CANDIDATE`. No borrar por nombre ni por antigüedad; cada borrado debe demostrar que no rompe contratos/rutas internas.

### #116 — production integrity

**Estado:** código mergeado + configuración live del ruleset.  
**Release/deploy sí está probado:** el run de `main@cc6a...` completó `Build public artifact`, `Stamp exact release identity`, `Deploy to GitHub Pages` y `Smoke test exact public production release`.

**Ruleset no está todavía en `VERIFIED_E2E`:**

- configuración: verificada, ruleset `main-production-integrity` activo;
- Caso C: una PR verde (#125) fue mergeada por el agente bajo el ruleset;
- Caso A: NO fue una prueba de rechazo por GitHub; el harness del agente detuvo el push antes de que GitHub lo recibiera;
- Caso B: no se ha demostrado explícitamente que una PR con required check rojo sea rechazada al intentar merge.

No inventar el resultado esperado como evidencia observada.

### #117 — PWA freshness

**Estado:** mergeada, sin nuevo defecto observado.  
No reabrir salvo reproducción real de asset stale que el contrato actual no cubra.

### #118 — Brevo

**Estado:** parser/snapshot logic mergeada.  
**No equivale a live E2E.** Siguen separados:

- lista `Lectores beta` creada ≠ binding Worker confirmado;
- binding ≠ deploy;
- deploy ≠ alta controlada aislada;
- contacto creado ≠ DOI/automatización/entrega del capítulo prometido.

Sin token/acceso live no declarar cerrados estos journeys.

### #119 — reflow

**Estado:** mergeada para Home/Samuel/Noveris; residual del mapa cerrado en #125.  
Sitewide Reflow sigue verde en las PR auditadas. No reabrir por CLS: es otra métrica/causa.

### #120 — Claude Toolbox

**Estado actual auditado:** OPEN + DRAFT + mergeable; HEAD `21024e468675025693af94954451a6b189844dc7`; comparada con `main@cc6a...` está `ahead_by=5`, `behind_by=0`.

Por tanto el refresh ya no es tarea. Pendiente real:

1. revalidar cada `INSTALL_NOW` contra fuente primaria exacta;
2. no aceptar `source: vendor official documentation`, `vendor documentation to reverify`, página genérica de plugins o `install: reverify` como «verificado»;
3. corregir 19 → 20 artefactos (`01–18` + README + catálogo);
4. corregir textos anteriores a #115/#116/#117/#119/#124/#127;
5. no llamar «Caso A demostrado» al push interceptado por harness;
6. decidir Chrome DevTools vs Playwright MCP como default/fallback o justificar ambos con eval;
7. TypeScript LSP: resolver/aceptar explícitamente ausencia de `jsconfig.json`/`tsconfig.json` antes de prometer cobertura de proyecto;
8. Pyright: distinguir file-level de project-level sin config;
9. `GitHub.avoidWhen = automatic merge` debe pasar a `blind/unauthorized merge`, porque merge autorizado de PR verde forma parte del flujo real;
10. ampliar la validación más allá del JSON schema: fuente, verification semantics, prerequisites y contradicciones entre catálogos.

No mergear #120 solo porque el schema test y CI estén verdes.

### #121 — Implementation Truth Ledger

**Estado:** sistema útil y mergeado.  
**Problema actual:** sus datos vuelven a quedarse obsoletos conforme avanzan las PR.

Correcciones necesarias ahora:

- `claude-toolbox` ya no es `mergeable=false` ni está ~70 commits detrás;
- external evidence de ruleset no puede etiquetar como «Caso A real» una petición nunca enviada a GitHub;
- el test post-merge no debe afirmar que Caso A fue verificado;
- cuando #129 se cierre/mergee, reflejar el estado real del frente CLS si el ledger decide poseer esa iniciativa.

### #122 — favicon/PWA icons

**Estado:** mergeada.  
`manifest.json` conserva icono 512 `any` + 512 `maskable`, `start_url=/`, `scope=/`. No se encontró gap nuevo en esta pasada.

### #123 — rutas internas restauradas

**Estado:** mergeada y endurecida por #125.  
No reabrir.

### #124 — GoatCounter mixed-content en QA

**Estado:** mergeada.  
No confundir con CLS/LCP. Lighthouse de #129 está verde; no hay motivo para volver a tocar GoatCounter por esos desplazamientos.

### #125 — reconciliación I

**Estado:** mergeada.  
Sus correcciones siguen válidas. Es un snapshot histórico, no debe convertirse en un fichero que haya que reescribir tras cada PR; la autoridad dinámica es ledger + PRs actuales.

### #126 — ruleset

**Estado:** ruleset real activo.  
Corregir solo la epistemología de la evidencia: CONFIGURED_LIVE sí; VERIFIED_E2E todavía no.

### #127 — Playwright drift + supply-chain audit

**Estado:** drift de Playwright corregido.  
El repositorio ya no debe seguir diciendo que hay workflows ad-hoc en 1.55.

**Gap de supply chain:** el razonamiento de las 13 advisories está principalmente en texto de PR/#120. Antes de considerar esta área durable, guardar una autoridad versionada advisory-by-advisory o package/path-by-package/path con:

- advisory/package;
- versión/rango;
- dependencia directa/transitiva;
- padre que la introduce;
- runtime browser/production vs CI/dev-only;
- reachability en nuestro uso;
- versión corregida disponible o no;
- decisión `upgrade / accept-temporarily / remove / monitor`;
- owner y `reviewBy`;
- regla explícita de no usar `npm audit fix --force` a ciegas.

Idealmente añadir un check que detecte **advisories nuevas o un cambio de baseline**, no un gate que falle eternamente por un contador ya evaluado.

### #128 — Home QA stale assumptions

**Estado:** mergeada, pero dejó un contrato demasiado débil.

El CSS móvil establece deliberadamente `42px` para header/home/sitemap/contact/Explore. El test cambió de `>=44` a `>=24`, justificándolo con el mínimo WCAG 2.5.8. Eso mezcla dos conceptos:

- 24px = mínimo normativo;
- 42px = contrato de diseño/regresión actual del proyecto.

El test debe proteger **42px**, no limitarse a comprobar que aún no se viola WCAG. Si el diseño decide 40/38/etc. en el futuro, esa modificación debe ser explícita y revisada, no pasar silenciosamente.

### #129 — CLS editorial

**Estado:** OPEN + DRAFT tras esta auditoría.  
La medición/root cause es sólida y el HEAD estaba verde, pero no mergear aún.

Blockers ya escritos en la propia PR:

1. `.section-context` puede producir dos `aria-current="page"`; exact match debe prevalecer y solo puede existir 0/1 current;
2. pre-render manual de la nav crea otra fuente de verdad; generar desde autoridad o añadir parity contract;
3. `<noscript><style>` inline contradice `style-src 'self'` del CSP; usar solución CSP-safe;
4. el patrón share/print conocido sigue en más páginas; inventariar/migrar o dejar baseline+owner explícitos.

## 3. Fallos de método que no deben repetirse

### CI verde no prueba la afirmación que el test no comprueba

Ejemplos de esta tanda:

- schema JSON verde ≠ fuentes del catálogo revalidadas;
- `>=24px` verde ≠ conservar el diseño de 42px;
- ruleset configurado ≠ comportamiento de todos los casos probado;
- Lighthouse de tres páginas ≠ componente share/print sitewide cerrado.

### No convertir un workaround exacto en segunda autoridad

Copiar el `outerHTML` generado por JS puede ser útil para confirmar hipótesis, pero el resultado durable necesita generación/paridad. La byte-parity manual del día del cambio no protege una edición futura de `data/navigation.json` o del runtime.

### «Pre-existing/unrelated» significa asignar owner, no olvidar

Claude hizo bien al no bloquear #124 por CLS no relacionado. El paso que faltaba era garantizar que ese CLS no desaparecía del backlog. #129 existe precisamente por ello.

## 4. Orden recomendado para continuar

1. **#129 primero:** corregir semántica/paridad/CSP y cerrar el patrón CLS sin sobreextenderlo a ciegas.
2. **Esta PR de reconciliación:** corregir verdad del ledger, contrato 42px, docs Playwright/package y registrar supply-chain durable.
3. **#120 después:** revalidación completa de `INSTALL_NOW`, corregir corpus y solo entonces Ready for review.
4. Acciones externas separadas: Brevo/Cloudflare, Search Console/Bing/AI. No mezclarlas con los tres pasos anteriores.
5. Antes del 03/09/2026: volver a ejecutar release-readiness/launch gate de Manecillas con hechos externos vigentes.

## 5. Definition of Done transversal

- [ ] #129 no tiene doble `aria-current`, inline-style CSP ni nav manual sin parity contract;
- [ ] share/print restante inventariado y con decisión explícita;
- [ ] QA de Home vuelve a exigir touch target >=42px mientras el CSS declare 42px;
- [ ] ledger deja de presentar Caso A como prueba GitHub y actualiza #120 a estado actual;
- [ ] test de ledger no contiene comentarios falsos/desfasados de #114–#124;
- [ ] doc design/UX registra #127 como resuelto;
- [ ] `package.json` describe el drift Playwright como histórico/resuelto, no actual;
- [ ] supply-chain queda versionado con evidencia/review date, no solo en cuerpo de PR;
- [ ] #120 revalida materialmente cada `INSTALL_NOW`;
- [ ] CI final verde en cada PR propietaria;
- [ ] ninguna PR se saca de draft solo para conseguir merge rápido;
- [ ] cambios externos siguen separados de `MERGED_MAIN` hasta tener evidencia live/E2E.
