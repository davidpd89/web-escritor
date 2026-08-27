# Reconciliación post-Claude — 27/08/2026

**Corte auditado:** `main@20411ed92c651f400ed4cec53998371da9815978` (merge de PR #124).  
**Objetivo:** no confundir `merged` con `cerrado`, preservar los hallazgos aparecidos durante la tanda #114–#124 y dejar a Claude un orden de continuación verificable.

## 1. Estado real al terminar la tanda

### Confirmado en `main`

- PR #114 — corpus de diseño/UX/tooling mergeado.
- PR #115 — primera limpieza mergeada; introdujo una regresión al borrar rutas internas que #123 restauró.
- PR #116 — gate universal de PR, identidad exacta de release y verificación HTTP post-deploy mergeados.
- PR #117 — política PWA durable: media/Range fuera de CacheStorage genérico; assets mutables con SWR; CSS/JS network-first.
- PR #118 — snapshot Brevo corregido para no confiar en falsos `0` del endpoint agregado.
- PR #119 — regresiones de reflow de Samuel/Noveris corregidas para el alcance de esa PR.
- PR #121 — Implementation Truth Ledger creado.
- PR #122 — favicon/PWA icon amarillo.
- PR #123 — restauración de `/herramientas/auditor-web/`, `/publicar-web/` y fuentes asociadas borradas por #115.
- PR #124 — GoatCounter pasa de URL relativa al protocolo a `https://gc.zgo.at/count.js`; el falso `is-on-https` de Lighthouse desaparece.

El deploy de `main@20411ed...` terminó en success. Esto demuestra que el código de #116 está operativo en la cadena de Pages; no demuestra que GitHub obligue a usarla.

## 2. P0 — `main` sigue sin protección real

Snapshot posterior a #124:

```text
main protected=false
required status checks=[]
repository rulesets: ninguno observado
```

El mayor gap de gobernanza sigue abierto:

```text
buen gate universal != gate obligatorio
```

### Acción para Claude

Aplicar la configuración ya especificada en `docs/production-integrity/02-RULESET-MAIN-Y-CHECKS-OBLIGATORIOS.md`, solo con autorización/capacidad de cuenta adecuada.

Criterios mínimos:

1. PR obligatoria para `main`.
2. `Required merge gate` obligatorio.
3. `Public artifact contract` obligatorio.
4. Sitewide Reflow y Pa11y obligatorios con sus contexts reales, si se ejecutan universalmente o la configuración evita un required check que pueda quedar eternamente pending por `paths:`.
5. `required approvals = 0` para conservar el flujo agent-operable definido por el proyecto.
6. force push y deletion bloqueados.
7. prueba conductual: push directo normal rechazado.
8. prueba conductual: PR verde mergeable por agente autorizado sin aprobación manual rutinaria.

No marcar esta iniciativa `CONFIGURED_LIVE` ni `VERIFIED_E2E` hasta tener evidencia del comportamiento real.

## 3. P0 — reconciliar el Implementation Truth Ledger

`data/implementation-truth-ledger.json` quedó obsoleto después de que #121 se mergeara y Claude continuara con el resto de PR.

Cambios que deben reflejarse:

| ID | Estado actual que debe quedar | Nota |
|---|---|---|
| `production-release-integrity` | `MERGED_MAIN` | Gate + release identity + post-deploy verify están en main; ruleset sigue separado y no configurado. |
| `github-main-ruleset` | `DOCUMENTED` | Sigue correcto mientras `main` continúe `protected:false`. |
| `pwa-asset-freshness` | `MERGED_MAIN` | Política durable y contrato están en main; no inventar prueba E2E de todos los móviles. |
| `mobile-reflow-shared-components` | `MERGED_MAIN` | #119 está mergeada; el residual de `/mapa-del-sitio/` pertenece a discoverability/findability, no debe reabrir artificialmente Samuel/Noveris. |
| `design-ux-tooling-system` | `MERGED_MAIN` | Corpus mergeado, pero faltan tres artefactos prometidos; stage y completion no son lo mismo. |
| `repo-hygiene-round-1` | `MERGED_MAIN` | Registrar explícitamente la regresión #115→#123 y el nuevo gate de paths de esta PR. |
| `claude-toolbox` | `IMPLEMENTED_IN_PR` | #120 sigue draft y necesita refresh sobre main actual. |
| `brevo-snapshot-list-counts` | `MERGED_MAIN` | Parser/test están en main; snapshot live corregido aún debe regenerarse con acceso real. |

Añadir además una entrada específica para el residual `findability-sitemap-reflow` hasta que Global Discoverability demuestre 320 px + 200 % + text-spacing sin overflow.

Regla nueva que conviene institucionalizar: toda PR que cambie materialmente una iniciativa del ledger debe actualizar la entrada en la misma PR o explicar por qué no aplica. No depender de una reconciliación manual varias PR después.

## 4. P0/P1 — residual real de `/mapa-del-sitio/`

En el HEAD final de #119, Global Discoverability reprodujo:

```text
/mapa-del-sitio/ @ viewport 320
200 % + text spacing
scrollWidth/clientWidth = 349/320
```

Esta PR propone un fix conservador y localizado en `assets/v1-findability.css`:

- `min-width:0` en los `li` del directorio;
- `min-width:0` en los anchors;
- `overflow-wrap:anywhere` en labels/enlaces del directorio.

No usa `overflow-x:hidden` y no recorta contenido.

### Criterio de aceptación

- Global Discoverability verde.
- `/mapa-del-sitio/` 320 px + 200 % + text-spacing: `scrollWidth <= clientWidth + 1`.
- Sitewide Reflow permanece verde.
- Pa11y permanece verde.
- no pérdida visual inaceptable en 390/768/1440.

Si CI sigue rojo, no relajar el gate: usar el offender exacto y corregir la causa restante.

## 5. P1 — el fallo de #115 podía repetirse por `paths:`

`tests/test-tools-hub-public-registry.py` exige que estas rutas internas sigan existiendo y sigan noindex:

- `/herramientas/auditor-web/`;
- `/publicar-web/`.

#115 las borró, pero `Tool engine tests` no se ejecutó porque los paths borrados no estaban en su filtro.

Esta PR amplía el trigger a:

- `herramientas/**`;
- `publicar-web/**`;
- `data/tools-hub.json`;
- `scripts/audit-author-web.py`.

Así el mismo tipo de regresión deja de poder entrar silenciosamente por otra limpieza.

## 6. P1 — conservar evidencia cuando Global Discoverability falla

El browser QA ya crea su carpeta, pero una assertion temprana puede impedir que se genere `browser-report.json` y las screenshots finales.

Esta PR captura siempre stdout/stderr en:

- `artifacts/global-discoverability/browser.log`;
- `artifacts/sitewide-reflow/reflow.log`.

El artifact upload pasa a `if-no-files-found:error` porque los logs se crean antes de ejecutar los tests.

Objetivo: un rojo debe dejar más evidencia que un verde, no menos.

## 7. P1 — #114 está mergeada, pero no completa

`docs/design-ux-tooling/README.md` enumera 16 artefactos. En `main` faltan todavía:

- `14-FUENTES-Y-ESTADO-2026-08-27.md`;
- `15-ANTI-SLOP-DESIGN-REVIEW.md`;
- `tools-catalog.json`.

### Acción para Claude

Crear los tres sin rellenarlos con teoría genérica.

`14-FUENTES...` debe registrar fuente primaria, URL, corte, estado y qué claim sostiene.  
`15-ANTI-SLOP...` debe convertir la kill-list existente en un review gate operativo con ejemplos de fallo/aceptación.  
`tools-catalog.json` debe ser machine-readable y distinguir claramente `RECOMMENDED`, `PILOT`, `DEFER`, `NOT_APPLICABLE`, requisitos, credencial, coste/gate y evidencia oficial.

Añadir un test/validador del catálogo si puede comprobar señal real sin duplicar Markdown.

## 8. P1 — #120 Claude Toolbox necesita refresh, no merge directo

#120 sigue `draft` y GitHub la reporta actualmente `mergeable:false`.

Su base documentada es `main@b3db6b6...`; desde ese punto `main` ha avanzado 69 commits hasta `20411ed...`.

Antes de tocar su contenido:

1. actualizar/rebasar la rama contra `main` actual;
2. no arrastrar runtime antiguo de la rama huérfana;
3. corregir frases que todavía describen #115/#116/#119 como PR pendientes;
4. incorporar que #124 cerró el falso `is-on-https` de GoatCounter;
5. revalidar `tools-catalog.json`, especialmente LSP/prerequisites y cada `INSTALL_NOW`;
6. añadir validador machine-readable si aporta señal;
7. mantener `INSTALL_NOW/PILOT` como recomendación, no como afirmación de instalación;
8. CI transversal del HEAD final.

No instalar MCP/plugins, conectar OAuth ni crear secrets como efecto colateral de cerrar la documentación.

## 9. P1 — Lighthouse/CLS: deuda real separada de GoatCounter

#124 resolvió el problema `is-on-https`; no resolvió todos los rojos de Lighthouse.

Datos reproducidos en el último run auditado de #124:

- `/libros/samuel-entre-mundos/`: CLS `0.183686...` en los tres runs de Lighthouse.
- `/recomendaciones/portal-fantasy-espanol/` a 320: CLS `0.1062` en Recommendations browser QA.
- `/recomendaciones/magia-con-coste/` a 768: CLS `0.2863`.
- Home y otras rutas muestran LCP/performance warnings; no deben confundirse automáticamente con regresión de #124.

### Acción

Abrir una PR propietaria de layout stability/performance, no mezclarla con GoatCounter.

Orden recomendado:

1. reproducir CLS en `main` fresco;
2. identificar `layout-shift` sources/elementos exactos con trace o PerformanceObserver;
3. clasificar font swap, media sin dimensiones, DOM dinámico, shell/intro, newsletter o contenido;
4. corregir causa, no subir umbrales;
5. comparar antes/después con al menos 3 runs;
6. mantener Lighthouse/Recommendations browser verde en los umbrales actuales.

`magia-con-coste = 0.2863` es suficientemente alto para exigir diagnóstico, no para etiquetarlo de ruido sin evidencia.

## 10. P1 — Cross-engine tiene al menos una carrera de interacción

Durante #124 un cross-engine smoke falló porque el trigger `Explorar` dejó de estar visible en el instante del click; Claude reprodujo el mismo suite limpio localmente y lo trató como flakiness.

No silenciar el test ni añadir sleeps grandes por defecto.

Investigar:

- transición compacta del header;
- scroll/visibility race;
- estabilidad del locator;
- `waitFor(state=visible)` + condición real del header;
- si el elemento se oculta/reemplaza durante la transición.

El objetivo es hacer determinista la interacción o demostrar una regresión real, no convertir un click flaky en `force:true`.

## 11. P1 — supply chain Node

Los `npm ci` recientes informan 13 vulnerabilidades en el árbol instalado (2 low, 1 moderate, 10 high) y varias dependencias deprecadas.

Eso no equivale a 10 vulnerabilidades de producción.

### Acción correcta

Generar una auditoría de reachability:

- advisory/CVE;
- paquete y versión;
- cadena de dependencia;
- runtime público vs dev/CI tooling;
- si el código vulnerable es alcanzable en nuestro uso;
- versión mínima corregida;
- cambio breaking o no;
- prueba después del upgrade.

No ejecutar `npm audit fix --force` a ciegas.

Revisar además las advertencias de GitHub Actions que actualmente fuerzan acciones basadas en Node 20 a Node 24 y actualizar a releases oficiales compatibles cuando existan.

## 12. P1/external — Brevo sigue teniendo trabajo live

Aunque #118 esté mergeada, siguen abiertos:

- regenerar el snapshot live usando el parser corregido;
- verificar `BREVO_BETA_LIST_ID=6` en el Worker correcto;
- deploy autorizado de ese Worker si el binding falta;
- smoke controlado de aislamiento beta;
- verificar DOI → automation → entrega del capítulo de Samuel o retirar/narrow la promesa pública mientras no pueda demostrarse.

No usar la existencia de la lista 6 como prueba de journey E2E.

## 13. P1/P2 external — Search Console e IA siguen documentados, no activados

Las PR de Search Console y AI discoverability dejaron backlogs exhaustivos. No inferir configuración real de cuenta por estar los docs en `main`.

Pendientes externos siguen incluyendo, según disponibilidad/autorización:

- propiedad Domain y baseline real de Search Console;
- BigQuery bulk export;
- GenAI controls/report si el rollout está disponible;
- propiedades de Instagram/TikTok si son elegibles;
- IndexNow/Bing Webmaster/AI Performance del plan de AI discoverability;
- WAF/crawler verification donde proceda.

Cada activación real debe actualizar el ledger con evidencia externa.

## 14. Lanzamiento de Manecillas — 03/09/2026

No dejar que esta reconciliación técnica borre el gate de lanzamiento.

Antes y después del 03/09:

- verificar disponibilidad/retailer real antes de cambiar copy o schema comercial;
- no inventar `Offer`/stock/precio;
- annotation de Search Console cuando la cuenta esté operativa;
- inspección de URLs prioritarias;
- smoke de funnel/fragmentos/CTA;
- revalidar hechos públicos, llms/ai/press-kit y artefacto público después del cambio.

## 15. Orden recomendado para Claude

### Camino A — menor riesgo

1. Terminar esta PR de reconciliación y dejar sus checks verdes.
2. Actualizar el ledger dentro de esta misma PR o inmediatamente después sin perder el snapshot anterior.
3. Completar los tres artefactos ausentes de #114.
4. Rebase/refresh y cierre de #120.
5. PR separada de CLS/performance.
6. PR separada de supply-chain.
7. acciones externas: ruleset → Brevo → Search Console/Bing/IA según autorización.

### Camino B — si quiere agrupar documentación

Puede completar #114 + ledger dentro de esta PR, pero **no** mezclar aquí upgrades masivos de dependencias, instalaciones de MCP, cambios live de cuentas o una reescritura visual completa. Esos frentes tienen riesgo y DoD distintos.

## 16. Definition of Done de esta reconciliación

Esta PR puede considerarse cerrada cuando:

- el residual de `/mapa-del-sitio/` está verde en Global Discoverability;
- el artifact de un fallo browser conserva logs;
- Tool engine tests se dispara al tocar/borrar las rutas que su propio contrato protege;
- el ledger deja de presentar PR ya mergeadas como `IMPLEMENTED_IN_PR`;
- #114 deja explícito si sus tres artefactos se completan aquí o en una PR propietaria con owner/DoD;
- #120 se mantiene draft hasta refresh real contra `main` actual;
- CLS, supply-chain y trabajo live externo permanecen visibles con owner y criterio de cierre;
- no se desactiva ningún gate para conseguir verde;
- no se hace push directo a `main` como método de cierre.
