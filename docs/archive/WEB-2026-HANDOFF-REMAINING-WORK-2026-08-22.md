# WEB 2026 — HANDOFF AUTORITATIVO DE TRABAJO PENDIENTE

> **Versión actualizada tras integrar las PR #21–#24.**
>
> Este documento sustituye como hoja de ruta operativa a las versiones anteriores del mismo fichero. Su objetivo es que otro agente/equipo pueda continuar el proyecto sin rehacer trabajo ya integrado, sin perder tareas que quedaron fuera y sin mezclar varias responsabilidades en una sola PR.
>
> **NO autoriza merge a `main`, producción ni despliegue.** Cada bloque se trabaja en una rama propia, abre una PR contra `implementacion-web-2026` y se detiene para revisión independiente.

---

# 0. SNAPSHOT Y ESTADO REAL AL ACTUALIZAR ESTE HANDOFF

Repositorio:

`davidpd89/web-escritor`

Rama de integración:

`implementacion-web-2026`

HEAD observado al crear esta versión:

`e9207278747646b76a0f22ebf3703b3e19c0c3db`

Ese SHA es **solo procedencia del documento**. Antes de CADA tarea hay que hacer `git fetch origin --prune` y obtener el HEAD real de `origin/implementacion-web-2026`. No se debe reutilizar este SHA como base fija.

## 0.1 PR recientes ya integradas — NO REHACER

Se han integrado y revisado, entre otras, estas piezas recientes:

- **PR #21 — Editoriales**: builder/templates reconciliados con V1, generación idempotente y test de paridad.
- **PR #22 — Convocatorias**: builder del radar migrado a shell V1 con paridad HTML/JSON/ICS e idempotencia.
- **PR #23 — Newsletter/contacto/Brevo**: cierre de conversión y contratos correspondientes.
- **PR #24 — acabado visual editorial**: marcos, rutas, tratamiento de media y correcciones posteriores de dead CSS/a11y.
- **PR #25 — documentación**: amplió el handoff con gates de zoom, ownership CSS, frescura y dos informes pendientes.

Además ya estaban trabajados/integrados antes:

- Home/cartografía estructural;
- herramientas de texto;
- Personajes/Nombres/POV;
- herramientas utilitarias y de publicación;
- hub/trust layer de herramientas;
- Books/Manecillas/Samuel;
- identidad pública: Autor/Prensa/Premios/Eventos;
- Cuaderno/editorial;
- recomendaciones;
- Asistente local/remoto con citas y endurecimiento;
- Privacidad/Aviso legal/consentimiento/telemetría;
- authority/machine-readable/AI discoverability;
- search/findability y otras migraciones V1 ya presentes en la rama.

**Regla:** no reabrir ninguna de estas áreas como proyecto nuevo salvo regresión reproducible encontrada por una tarea posterior.

## 0.2 Corrección importante sobre la antigua “Tarea 2”

La rama `gpt/global-shell-closure-v1` fue utilizada finalmente por la PR #22 para **Convocatorias builder parity**.

Por tanto, aunque el nombre de aquella rama sugiera otra cosa, **el cierre global de shell/navegación/footer/residuos legacy NO se ejecutó como bloque independiente**.

Ese trabajo vuelve a aparecer más abajo como tarea pendiente con rama nueva:

`gpt/global-shell-closure-v1-2`

No asumir que está hecho por el nombre histórico de la rama.

## 0.3 Trabajo activo que NO hay que pisar

Ahora mismo, **ninguno**. Las PR #26 a #38 están integradas y no queda ninguna
rama de trabajo abierta contra `implementacion-web-2026`. La única PR viva es la
#1 (`implementacion-web-2026` → `main`), que sigue en borrador y **no se
mergea**: GitHub Pages publica desde `main`, así que ese merge es el despliegue
a producción y lo decide una persona.

Sobre la antigua PR #27: GitHub la cerró sola al borrarse su rama base. Se
rehízo como **#37**, rebasada sobre `implementacion-web-2026` y con el informe
corregido para que no diga «listo para main». No reutilizar la #27.


## 0.4 Segunda ronda integrada (2026-08-22) — NO REHACER

Todas revisadas y corregidas en su propia rama antes de entrar. Ninguna quedó
pendiente.

| PR | Qué entró | Corregido al revisar |
|---|---|---|
| #26 | Social cards editoriales + test anti-regresión | — |
| #29 | Navegación de fragmentos de Manecillas | `syncHashScroll` en `script.js` llamaba a `decodeURIComponent` sin proteger: un `%` mal formado en el hash lanzaba un error **en todas las páginas del sitio** |
| #30 | Evidencia y atribución de premios | Timing en la QA de foco |
| #31 | Cartografía contextual de la Home | Cuatro medidas que no medían lo que decían (ver abajo) |
| #32 | UX conversacional del asistente | La QA exigía ≥16 px y ≥44 px y el CSS no lo cumplía: textarea a 14,72 px (iOS hace zoom al enfocar) y botones de 38 px |
| #33 | Gate de reflow sitewide | Rediseñaba la tablet sin declararlo; inventario de rutas desde disco |
| #34 | Paridad del archivo de ferias | Su *scope guard* bloqueaba **cualquier** PR posterior (retirado en la #38) |
| #35 | Familia editorial de /cuaderno/temas/ | Las series pasaron a `<ul>`: perdían el orden semántico que la propia página afirma tener |
| #36 | PWA / offline | Cinco assertions que pasaban por delante del caso que describen |
| #37 | Paquete de evidencia pre-main (sustituye a la #27) | Decía `READY_FOR_HUMAN_MAIN_REVIEW` sin abrir un navegador; su workflow nunca había corrido |
| #38 | Retirada del scope guard de Ferias | — |

### Lo que se repite y conviene tener delante

**1. Un workflow que no se dispara se ve igual que uno que pasa.** Van tres
casos en dos rondas:

- el escaneo de secretos vivía en un workflow filtrado a rutas del asistente,
  así que una clave en cualquier otro sitio no lo activaba;
- el workflow de la #37 llevaba `branches: [implementacion-web-2026]` y la PR
  estaba apilada sobre otra rama: no corrió nunca, y por eso nadie vio que su
  `npm ci` no puede funcionar (no hay `package.json` en el repo);
- el gate de reflow recorría el disco y metía ficheros sin versionar: en CI no
  existen, así que salía verde por una razón distinta de la que creía.

**Antes de dar por buena una puerta nueva, comprueba que se ha ejecutado de
verdad** —mira el log del job, no el check verde— y **que falla cuando debe**:
rompe algo a propósito, míralo en rojo, revierte, y decláralo en la PR.

**2. Escribir la assertion no es cumplirla.** La #32 traía la QA correcta
(≥16 px de fuente, ≥44 px de área táctil) y el CSS sin tocar. Si añades un
contrato, deja el producto cumpliéndolo en la misma PR o marca la PR como
DRAFT diciéndolo.

**3. Medir en el tick equivocado.** Cinco fallos de esta ronda eran esto, no
bugs de producto:

- leer `getComputedStyle` justo después de `Tab` o `hover`, con una
  `transition` de por medio, devuelve el valor de partida;
- bajo `prefers-reduced-motion` la receta del sitio es
  `transition-duration:.01ms!important`, **no `0s`** (a `0s` no se dispara
  `transitionend`), así que hay una transición real, cortísima: hay que dejar
  pasar un frame, y **no** exigir `=== 0` en las assertions de reduced motion;
- `navigator.serviceWorker.ready` resuelve con el worker aún en `activating`, y
  `clients.claim()` dispara `controllerchange` **dentro** del `waitUntil` de
  `activate`: para saber que la activación terminó hay que esperar al estado
  `activated`, no al controlador ni a un `setTimeout`.

**4. Dos cosas que Playwright no hace y parece que sí.** Las dos costaron un
rato en la #36:

- `route.request().serviceWorker()` **no** da `true` para el `fetch()` que el
  propio worker hace dentro de su handler;
- `context.setOffline(true)` **no** alcanza a las peticiones que origina el
  worker.

Con las dos, la petición llega a la red, responde 200 y se cachea: la assertion
del fallback offline pasaba sin ver jamás el fallback. Lo que sí funciona es
cortar la conexión en el servidor de la propia QA.

**5. El widget del asistente se auto-abre.** 1,1 s después de cargar, una vez
por sesión, con un panel de 410×650 en escritorio. Cae encima de la cartografía
de la Home y roba el `:hover`. Cualquier QA de un componente de la Home debe
marcar antes la clave de sesión `davidporto-assistant-widget-auto-v1`.

### Dos hallazgos abiertos, para decidir

Ninguno se ha tocado: los dos son decisiones, no bugs con arreglo obvio.

- **Puntero y foco compiten por el resalte del mapa.** `v1-shell.js` escribe
  `data-active` tanto en `mouseenter` como en `focus`, y gana el último evento.
  Si el ratón descansa sobre un nodo y navegas con Tab, el scroll dispara un
  `mouseenter` tardío que le roba el resalte al nodo enfocado. Hay que decidir
  qué entrada manda antes de tocarlo.
- **El auto-open del asistente tapa el contenido principal de la Home.** Es
  deliberado y se limita a una vez por sesión, pero conviene mirarlo con ojos de
  producto, no de QA.


---

# 1. DIRECCIÓN DEL PROYECTO — NO REABRIR

Dirección visual cerrada:

**CARTOGRAFÍA EDITORIAL VIVA — V1-B**

Principios:

- shell claro + territorio principal oscuro cuando corresponda;
- diseño editorial contemporáneo, personal y humano;
- jerarquía mediante tipografía, espacio, líneas, composición y ritmo;
- evitar SaaS, dashboard, bento, card soup y landing de IA;
- evitar beige de agencia genérica;
- evitar clichés de escritor: pergamino, pluma, máquina de escribir, papel envejecido;
- evitar WebGL/canvas ornamental;
- no migrar framework ni rehacer stack;
- movimiento corto/funcional, normalmente 160–240 ms;
- base usable sin animación;
- `prefers-reduced-motion` obligatorio.

Topología semántica de Home que se preserva:

- obra: **Manecillas → Autor → Samuel**;
- proceso: **Autor → Cuaderno → Herramientas**;
- esfera pública: **Autor → Prensa/Eventos**;
- Autor = origen/bisagra humana;
- Manecillas = obra dominante actual;
- Samuel = segunda obra, secundaria;
- Cuaderno = proceso/pensamiento;
- Herramientas = extensión práctica;
- Prensa/Eventos = territorio público.

No modificar esta topología desde tareas de QA/cleanup.

---

# 2. PROTOCOLO DE EJECUCIÓN — OBLIGATORIO

## 2.1 Antes de cada tarea

```bash
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
git status
git rev-parse HEAD
```

El worktree debe estar limpio.

Si NO está limpio:

- DETENERSE;
- no `reset --hard`;
- no borrar archivos;
- no descartar trabajo automáticamente;
- informar qué cambios locales existen.

## 2.2 Una tarea = una rama = una PR

Para cada bloque:

1. actualizar `implementacion-web-2026`;
2. registrar SHA base real;
3. crear la rama indicada desde ese HEAD;
4. recuperar ownership/source/template/builder/tests antes de editar;
5. implementar SOLO el scope;
6. ejecutar QA real;
7. revisar el diff completo;
8. commit + push;
9. PR contra `implementacion-web-2026`;
10. **NO MERGE**;
11. **DETENERSE**.

No empezar automáticamente el siguiente bloque.

## 2.3 No apilar tareas

No crear la siguiente rama desde una PR anterior sin integrar.

Después de que otra persona integre:

```bash
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
```

Y solo entonces crear la siguiente rama.

La PR #27 existente es la excepción histórica que demuestra por qué esta regla importa; no repetir el patrón.

## 2.4 Ownership antes de modificar generado

Antes de tocar una página/JSON/ICS/sitemap/output:

- localizar fuente de datos;
- template;
- builder;
- output;
- tests;
- workflow.

No editar manualmente un output si existe una fuente autoritativa.

## 2.5 Bug dentro del scope = bug corregido

Flujo obligatorio:

`REPRODUCE → CAUSA → FIX → TEST → REGRESSION TEST cuando sea razonable`

No se permite informar de un bug dentro del scope y declarar la PR lista sin corregirlo.

Si no se puede resolver:

- PR `DRAFT`;
- `bugs pendientes` no vacío;
- no escribir «listo para merge».

## 2.6 Estados de QA

Usar exclusivamente:

- `PASS`: ejecutado y correcto;
- `FAIL`: ejecutado y falla;
- `NO HECHO`: no se ejecutó;
- `INCOMPLETO`: comenzó pero no terminó.

No inferir PASS por inspección visual del código.

## 2.7 No arreglar el test para esconder el producto

Prohibido:

- bajar Lighthouse;
- aumentar tolerancias sin evidencia;
- borrar assertions;
- desactivar WCAG;
- relajar CSP;
- excluir rutas para “poner verde”;
- hardcodear opiniones del agente como gates.

Si un test está mal:

1. demostrarlo contra comportamiento real;
2. corregir el test;
3. conservar el contrato funcional que pretendía proteger.

## 2.8 Viewports limpios

Para QA responsive/reflow usar página/contexto nuevo o reload completo por condición:

- 320×900;
- 390×900;
- 768×1000;
- 1024×900;
- 1440×1000;
- 1728×1000;
- 844×390.

No depender solo de `setViewportSize()` sobre una aplicación ya inicializada.

## 2.9 No borrados silenciosos

Antes/después, cuando el bloque toca contenido:

- páginas;
- links;
- headings;
- facts;
- schema;
- assets;
- registros.

Toda eliminación debe aparecer en el informe final con motivo/evidencia.

---

# 3. ORDEN ACTUAL DE EJECUCIÓN

El orden recomendado desde este punto es:

0. ~~Terminar/revisar PR #26~~ — **HECHA E INTEGRADA**.
1. **Global shell/navigation/footer closure** — reinsertada porque quedó sin ejecutar. **SIGUIENTE.**
2. ~~Sitewide reflow 200 % + text-spacing gate~~ — **HECHA E INTEGRADA (PR #33)**.
3. **CSS ownership/component-definition gate**.
4. **Radar de convocatorias freshness gate**.
5. **Build reproducibility/source↔generated parity global**.
6. **Performance/Core Web Vitals closure**.
7. **Cross-browser runtime compatibility**.
8. **Edge/HTTP/redirect/security-header contract**.
9. **Informe de assets `alicia_capitulo_*`** — informe, NO borrar.
10. **Informe de outliers SEO title/description** — informe, NO aplicar copy.
11. **Release readiness V2 FINAL** — siempre la última.

Las Tareas 3 y 4 pueden ejecutarse de forma separada y en paralelo. Tareas 5–8 deben trabajar contra un estado ya razonablemente final para evitar conclusiones obsoletas.

Si #26 encuentra una nueva familia coherente que no encaja en estas tareas, se documenta y se crea un bloque separado. No absorber silenciosamente un refactor grande en #26.

---

# TAREA 0 — TERMINAR Y REVISAR PR #26, SIN DUPLICARLA

Estado:

**ACTIVA / EN REVISIÓN**.

No crear rama nueva mientras la PR siga abierta.

Antes de integrarla, el revisor debe comprobar independientemente:

- base real;
- HEAD;
- diff;
- que solo contiene residual cleanup y no features nuevas;
- social cards corregidas y dimensiones reales;
- test anti-regresión añadido;
- assets locales;
- authority/discoverability;
- CI.

Tras merge:

```bash
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
```

Registrar nuevo HEAD y continuar con Tarea 1.

---

# TAREA 1 — GLOBAL SHELL / NAVEGACIÓN / FOOTER / LEGACY CLOSURE

Rama:

`gpt/global-shell-closure-v1-2`

PR:

`Global shell: close remaining V1 navigation surfaces`

## Por qué sigue pendiente

La antigua rama `gpt/global-shell-closure-v1` terminó siendo la PR de Convocatorias builder parity. El trabajo global de shell no debe darse por hecho.

## Objetivo

Inventariar todas las superficies públicas y corregir **solo** aquellas que todavía utilicen accidentalmente:

- shell antiguo;
- header/footer antiguos;
- `styles.css`/`styles.min.css` legacy cuando no corresponda;
- `script.js` legacy cuando no corresponda;
- logo/nav antiguos;
- navegación duplicada;
- `aria-current` incorrecto;
- Explore/shell V1 ausente donde el contrato indique que debe existir.

No es un rediseño global.

## Implementación

1. Construir inventario desde rutas públicas reales: sitemap, registry/builders y HTML indexable.
2. Clasificar cada ruta:
   - V1 correcta;
   - V1 con residual legacy;
   - legacy intencional/documentado;
   - técnico/no público;
   - redirect/404.
3. Localizar consumers reales de CSS/JS legacy.
4. Migrar únicamente residuos accidentales.
5. Priorizar template/builder/source central frente a editar outputs masivamente.
6. Preservar contenido, metadata, canonical, robots, JSON-LD y rutas.
7. No tocar Home/topología por “uniformidad”.
8. No borrar `styles.css`, `script.js` ni otros legacy hasta demostrar:
   - cero consumers públicos;
   - cero builders/templates dependientes;
   - cero tests/outputs dependientes.
9. Si quedan consumers legítimos, documentarlos y conservar los assets.
10. Añadir un check objetivo si existe un patrón de regresión fácilmente detectable, pero no crear una blocklist de páginas basada en opinión.

## QA

- route inventory before/after;
- `check-navigation-coverage`;
- `check-internal-graph`;
- local assets;
- canonical/robots;
- keyboard/nav/Explore;
- no-JS;
- 320–1728 + landscape;
- smoke de Home, Manecillas, Samuel, Autor, Cuaderno, Herramientas, Recomendaciones, Editoriales, Convocatorias, Prensa, Eventos, Privacidad y 404/findability si son públicos;
- Lighthouse representativo.

## Stop condition

Si el inventario descubre una familia grande con lógica propia, detener esa parte y proponer split. No convertir esta tarea en una PR monstruosa.

---

# TAREA 2 — ZOOM 200 % Y WCAG TEXT-SPACING COMO GATE SITEWIDE

## ESTADO: HECHA E INTEGRADA (PR #33, 2026-08-22)

No reabrir. Lo que quedó en la rama:

- `qa/sitewide-reflow-browser.mjs` — **66 rutas × 2 viewports = 132 comprobaciones**,
  con text-spacing de WCAG 1.4.12 inyectado por hoja de inspector CDP (no
  `addStyleTag`: las páginas llevan `style-src 'self'` y el inline se rechaza) y
  zoom 200 %;
- `.github/workflows/sitewide-reflow-qa.yml`;
- el CSS corregido en 12 hojas V1.

Tres cosas que se corrigieron **al revisar la PR** y que conviene no repetir en
las tareas siguientes, porque son errores fáciles de cometer otra vez:

1. **Arreglar el reflow no es rediseñar.** La primera versión quitaba mínimos
   duros a base de aplanar layouts: `.v1-section__head` perdía sus dos columnas
   a 768 px, `.contact-grid` pasaba de dos columnas a una en tablet, y el `h1`
   del masthead se iba de 489 px a 713 px al soltarle el `max-width`. Nada de
   eso hacía falta: `minmax(min(N,100%),1fr)` ata el mínimo al contenedor y a
   ancho normal no cambia nada. Se midió con A/B geométrico contra la base
   (8 rutas × 3 anchos) hasta dejar la diferencia en **0**.

   **Regla para las tareas 3, 5, 6 y 7: si un arreglo cambia la geometría a
   ancho normal, mídelo y decláralo. No lo cuentes como «endurecer».**

2. **El inventario de rutas no puede salir de recorrer el disco.**
   `walkHtmlFiles` recorría el árbol de ficheros, así que metía en la puerta el
   HTML suelto de las carpetas de notas e ideas sin versionar —cientos de px de
   desbordamiento en ficheros que no se publican—. En CI no aparecían, porque no
   están en el repo: **el gate salía verde por accidente, no por acuerdo.** Sale
   de `git ls-files`, que da el mismo conjunto en local y en CI.

3. **Ojo con `overflow-wrap:anywhere` frente a `break-word`.** `anywhere` aplana
   el `min-content` a un glifo, así que una pista dimensionada por contenido se
   colapsa. `break-word` parte igual cuando no cabe y **no** toca el
   `min-content`. Salvo que quieras lo primero a propósito, usa `break-word`.

Referencia de patrones que ya funcionan, para reutilizar:

| Síntoma | Arreglo |
|---|---|
| Rejilla con mínimo en `rem`/`px` que no encoge | `minmax(min(N,100%),1fr)` |
| Palabra larga que no cabe | `overflow-wrap:break-word` |
| Hijo de grid/flex que no baja de su `min-content` | `min-width:0` en el hijo |

Ese último caso es el que tenían los `<nav>` del pie: son `display:grid`, así que
sus enlaces arrastraban `min-width:auto`.

---

# TAREA 3 — CSS OWNERSHIP / CLASES SIN DEFINICIÓN CARGADA

Rama:

`gpt/css-ownership-gate-v1`

PR:

`CI: fail when a page uses a class no stylesheet it loads defines`

## Objetivo

Evitar regresiones como `.button` o `.social-row`: HTML usa una clase, pero la regla vive en una hoja que esa página no carga.

## Implementación

1. Crear script determinista que por HTML público:
   - obtenga stylesheets enlazadas;
   - obtenga clases usadas;
   - obtenga clases definidas en esas sheets + `<style>` propio;
   - informe página + clase no resuelta.
2. Es una heurística: permitir excepciones SOLO explícitas y comentadas para clases JS/estado/generadas.
3. Prohibido un wildcard genérico que vacíe el check.
4. Ejecutar sobre HEAD y corregir problemas reales.
5. Regla de ownership:
   - componente multi-familia → hoja compartida adecuada;
   - componente de una familia → hoja local + link correcto.
6. Al mover reglas, auditar cascada y specificity para consumers existentes.
7. Cablear a un workflow global existente si encaja, sin duplicar CI innecesariamente.

## QA

- introducir temporalmente una clase inexistente, demostrar FAIL, revertir, demostrar PASS;
- screenshots/browser QA de páginas realmente afectadas a 390 y 1440;
- no cambios visuales accidentales en consumers de reglas movidas.

---

# TAREA 4 — RADAR DE CONVOCATORIAS: FRESHNESS REAL

Rama:

`gpt/radar-freshness-gate-v1`

PR:

`CI: fail when the opportunities radar goes stale`

## Importante

La PR #22 arregló **builder parity V1** de Convocatorias. Esta tarea es distinta: comprueba que el dataset no pueda quedar congelado indefinidamente mientras CI sigue verde.

Antes de hacer nada, verificar si alguna PR posterior ya resolvió exactamente este contrato. Si existe un gate real equivalente, documentar evidencia y NO duplicarlo.

## Problema a proteger

Históricamente `check-professional-resources.py` usaba `generated_for` como referencia de “hoy”. Un fichero viejo podía seguir siendo internamente coherente y pasar CI para siempre.

## Implementación

1. Comparar `generated_for` contra fecha real de ejecución.
2. Definir límite de frescura justificándolo con la política `STALE_DAYS` existente; no inventar un número arbitrario.
3. Tests con reloj inyectable/fijo para no depender del día en que corra CI.
4. Demostrar:
   - dataset viejo → FAIL;
   - dataset actual → PASS.
5. Documentar comportamiento cuando la lista está fresca pero no tiene oportunidades activas.
6. Probar HTML/JSON-LD/estado vacío.
7. No crear un cron de scraping/regeneración automática: la verificación externa sigue siendo manual según contrato actual.
8. Mantener coherencia JSON↔ICS↔HTML y fechas civiles.

---

# TAREA 5 — BUILD REPRODUCIBILITY / SOURCE ↔ GENERATED PARITY GLOBAL

Rama:

`gpt/build-reproducibility-v1`

PR:

`Build: verify generated-source parity and idempotence V1`

## Por qué se añade

Dos fallos distintos demostraron el mismo riesgo:

- Editoriales: builder legacy podía revertir páginas V1;
- Convocatorias: builder/output necesitó reconciliación y test de paridad.

Corregir dos builders no demuestra que el resto del repo sea reproducible.

## Antes de ejecutar

Revisar el resultado de PR #26 y Tareas 1–4. Si una de ellas ya ha creado un gate GLOBAL que ejecuta todos los builders reales, dos veces, y garantiza `git diff --exit-code`, esta tarea puede declararse satisfecha con evidencia y no duplicarse.

## Objetivo

Demostrar que todos los artefactos generados públicos pueden reconstruirse desde sus fuentes sin:

- reversiones a legacy;
- drift de metadata;
- cambios silenciosos de copy;
- diferencias de orden no deterministas;
- cambios en segunda ejecución.

## Implementación

1. Inventariar `scripts/build-*`, generators y outputs públicos.
2. Crear matriz:

`BUILDER → INPUT → OUTPUT → --check → TEST → IDEMPOTENCE`

3. En worktree/entorno limpio:
   - ejecutar checks;
   - ejecutar builders REALES;
   - revisar diff;
   - ejecutar segunda vez;
   - exigir diff limpio tras estado esperado.
4. No asumir que `--check` valida output: verificar semántica de cada builder.
5. Donde haya riesgo real y no exista gate, añadir paridad/check mínimo.
6. No construir un framework de builds nuevo por gusto.
7. No reescribir manualmente generated output para “hacerlo coincidir”.

## QA/Stop

La tarea no está cerrada si existe un builder público que al ejecutarse sobre HEAD limpio produce un diff inesperado no explicado.

---

# TAREA 6 — PERFORMANCE / CORE WEB VITALS CLOSURE

Rama:

`gpt/performance-cwv-gate-v1`

PR:

`Performance: close representative Core Web Vitals regressions V1`

## Objetivo

Cerrar rendimiento real antes del release, sin perseguir puntuaciones artificiales ni optimizar cada página de forma aislada.

## Scope

Primero seleccionar rutas REPRESENTATIVAS por familia, incluyendo como mínimo:

- `/`;
- Manecillas;
- Samuel;
- Autor;
- Cuaderno índice + artículo largo;
- Herramientas hub + una herramienta compleja;
- Recomendaciones;
- Editoriales/Convocatorias;
- página pública con imagen documental;
- una página legal/IA si aporta cobertura distinta.

## Auditar

- LCP y asset responsable;
- CLS;
- JS blocking/TBT cuando aplique;
- tamaños de imágenes;
- `srcset/sizes`;
- preload/fetchpriority;
- lazy loading;
- fonts y fallback;
- CSS/JS global innecesario;
- third-party load según consentimiento;
- tamaño de dist público si existe pipeline.

## Reglas

- no cambiar el contenido para ganar puntos;
- no esconder elementos en mobile;
- no preloadear todo;
- no cambiar `font-display` global sin regresión demostrada;
- no bajar Lighthouse thresholds;
- no introducir CDN/librería nueva;
- si un asset pesado no se usa pero ya tiene URLs públicas, NO borrarlo desde esta tarea: coordinar con el informe de assets.

## QA

- Lighthouse móvil/escritorio representativo;
- comparar before/after de cualquier fix;
- CLS visual real;
- LCP asset correcto;
- 390/1440;
- no regresión a11y/SEO.

Si no se encuentra una regresión significativa, la PR puede ser de tests/gates/evidencia mínima; no hacer cambios cosméticos para justificarla.

---

# TAREA 7 — CROSS-BROWSER RUNTIME COMPATIBILITY

Rama:

`gpt/cross-browser-runtime-v1`

PR:

`QA: close cross-browser runtime compatibility V1`

## Objetivo

La mayor parte del browser QA actual se apoya en Chromium. Antes del release necesitamos detectar APIs/layout que funcionen allí pero fallen en otros motores.

## Cobertura

Usar Playwright Chromium + Firefox + WebKit si el entorno/CI lo soporta.

WebKit de Playwright es una aproximación al motor; **no afirmar que esto equivale a probar físicamente Safari iOS**.

## Rutas/controles representativos

- navegación/Explore/dialog/focus;
- Home;
- formularios newsletter;
- share/clipboard fallbacks;
- tool con SVG/local-scroll;
- tool con file/import/export;
- inputs date/datetime si existen;
- sticky/TOC;
- print smoke;
- Manecillas/Samuel;
- Cuaderno;
- Asistente local (sin proveedor real);
- Privacidad/consentimiento con stubs donde sea necesario.

## Reglas

- no usar APIs propietarias sin fallback;
- no meter polyfill enorme por una función trivial;
- CI no depende de APIs externas reales;
- corregir producto, no excluir navegador sin justificación.

## QA

Por motor:

- pageerror;
- console errors relevantes;
- funcionalidad crítica;
- keyboard básico;
- 390 y 1440 con contextos limpios;
- local overflow;
- downloads/copy/share con fallback según soporte.

Documentar cualquier limitación de Playwright que impida reproducir comportamiento de dispositivo real.

---

# TAREA 8 — EDGE / HTTP / REDIRECTS / SECURITY HEADERS CONTRACT

Rama:

`gpt/edge-http-contract-v1`

PR:

`Release: verify redirects headers and HTTP contract V1`

## Objetivo

Auditar lo que no se puede demostrar únicamente mirando HTML: comportamiento HTTP/hosting/edge que afectará al release.

## Primero: descubrir autoridad real

Localizar si el repo controla mediante archivos/config/build:

- redirects;
- headers;
- Cloudflare/Pages/Worker;
- 404 fallback;
- canonical host;
- cache policy;
- API routes.

No inventar `_headers`, `_redirects`, `wrangler.toml` u otra infraestructura si el hosting no los usa.

## Verificar, donde el proyecto tenga autoridad

- HTTP→HTTPS;
- host canónico www/no-www;
- trailing slash y rutas antiguas;
- redirects existentes;
- 404 real/status;
- MIME/content-type de HTML/CSS/JS/JSON/ICS/fonts/images;
- CSP;
- HSTS si aplica;
- `X-Content-Type-Options`;
- `Referrer-Policy`;
- `Permissions-Policy` cuando exista contrato;
- cache headers para HTML vs assets versionados;
- robots/sitemap/manifest;
- CORS/same-origin en Workers/APIs;
- CSP/Turnstile/analytics según contratos ya integrados.

## Regla de entorno

NO desplegar producción.

Si existe preview/staging autorizado, usarlo.

Si un comportamiento solo puede comprobarse en configuración externa no accesible:

marcar `NO HECHO — HOSTING LEVEL` y documentar el paso exacto que debe validar una persona.

No fingir que `python -m http.server` representa Cloudflare/GitHub Pages.

## Stop

No cambiar headers de seguridad por intuición. Toda modificación debe explicar impacto y rutas afectadas.

---

# TAREA 9 — INFORME DE ASSETS `alicia_capitulo_*` — NO BORRAR

Rama:

`gpt/unreferenced-assets-report-v1`

PR:

`Docs: inventory the unreferenced alicia_capitulo_* assets`

## Tipo de tarea

**INFORME SOLAMENTE.**

No borrar, mover ni renombrar assets.

## Antecedente

El análisis previo detectó aproximadamente 174 ficheros `assets/alicia_capitulo_*`, unos 292,8 MB, aparentemente sin referencias internas. Ya han podido existir públicamente en producción, por lo que “no referenciado en HTML” no significa “seguro de borrar”.

## Producir

Documento en `docs/` con:

1. lista completa ruta/tamaño;
2. commit de introducción si se puede obtener;
3. búsqueda exacta en HTML/CSS/JS/JSON/feeds/sitemap/schema;
4. presencia/ausencia en build/dist;
5. si las URLs son alcanzables en producción, solo si se puede verificar de forma fiable;
6. indicios de indexación/enlaces solo con evidencia;
7. opciones:
   - conservar;
   - excluir de futuro dist manteniendo hosting histórico si fuera posible;
   - mover con redirects;
   - borrar asumiendo 404;
8. coste/riesgo de cada opción;
9. recomendación marcada claramente como recomendación.

## Prohibido

- borrar;
- mover;
- modificar `.assetsignore`;
- modificar build para excluirlos;
- ejecutar una “limpieza” automática.

La decisión es humana posterior.

---

# TAREA 10 — INFORME DE OUTLIERS SEO TITLE/DESCRIPTION — NO APLICAR COPY

Rama:

`gpt/seo-length-report-v1`

PR:

`Docs: report title/description length outliers`

## Tipo de tarea

**INFORME SOLAMENTE.**

No editar `<title>` ni meta descriptions en esta PR.

## Objetivo

Recalcular sobre el HEAD actual los outliers respecto a la guía SEO vigente.

El handoff anterior encontró 26 páginas y ejemplos como `autor.html` y `worldbuilding-noveris`, pero esa cifra es histórica. Recalcular tras los merges.

## Producir por página

- URL;
- title actual;
- longitud;
- description actual;
- longitud;
- umbral/guía usada;
- exceso;
- estimación prudente de truncado, sin fingir que Google usa un número fijo de caracteres;
- una alternativa propuesta que conserve intención/voz;
- marcar claramente `PROPUESTA — NO APLICADA`.

Añadir sección aparte sobre un posible gate de CI:

- umbrales;
- número de páginas que fallaría hoy;
- riesgos de convertir una guía editorial en hard gate.

No añadir el gate en esta tarea.

---

# TAREA 11 — RELEASE READINESS V2 FINAL — SIEMPRE LA ÚLTIMA

Rama:

`gpt/release-readiness-v2`

PR:

`Release: regenerate final pre-main readiness from integrated HEAD V2`

## Precondición absoluta

No ejecutar hasta que:

- PR #26 haya sido resuelta/integrada o descartada conscientemente;
- Tareas 1–8 aplicables estén integradas;
- Tareas 9–10 hayan producido sus informes y las decisiones humanas necesarias estén registradas;
- no haya otras PR funcionales pendientes que vayan a cambiar `implementacion-web-2026`.

La PR #27 histórica NO satisface esta condición porque está apilada sobre #26 y fue generada antes de los gates pendientes.

## Objetivo

Generar el paquete FINAL de evidencia desde el HEAD real de `implementacion-web-2026`.

No mergear `main`.

No desplegar.

## Evidencia mínima

- HEAD exacto;
- lista/ventana de commits;
- CI completa;
- route inventory;
- build reproducibility;
- shell/legacy closure;
- reflow/text-spacing;
- CSS ownership;
- radar freshness;
- performance/CWV;
- cross-browser;
- HTTP/edge checks disponibles;
- machine authority;
- editorial facts;
- sitemap/robots;
- tools suites;
- privacy/security;
- newsletter/contracts;
- local assets/internal graph;
- Lighthouse;
- browser smoke;
- no-JS;
- rollback.

## Gate temporal de lanzamiento — obligatorio

Fecha de publicación de **Las manecillas del recuerdo**:

`2026-09-03`

Facts autorizados:

- Monza Ediciones;
- ISBN `979-8-90514-935-1`;
- 272 páginas;
- PVP 16 €.

En el momento real de release, comprobar coherencia entre:

- HTML visible;
- metadata;
- JSON-LD;
- `/ai/`;
- `llms.txt`;
- `llms-full.txt`;
- press-kit JSON;
- editorial facts.

No puede coexistir sin intención explícita:

- “próxima publicación” en una superficie;
- “publicada” en otra.

No inventar retailers, availability, Offer ni compra antes de que estén autorizados/confirmados.

Samuel:

- ISBN `9791387659776`;
- 422 páginas;
- Libros Indie;
- paperback;
- publicación 2025 según autoridad actual.

Eventos completados conocidos:

- Aranjuez — 23/05/2026;
- Feria del Libro de Madrid — 10/06/2026, 19:00–20:00, caseta 337.

No inventar futuros eventos.

Jaula:

- mantener contención/restricciones;
- no exponer material privado/no publicado durante release.

## Rollback

Documentar:

- SHA de release candidate;
- SHA anterior estable;
- procedimiento exacto de rollback;
- smoke mínimo post-rollback;
- señales que justificarían rollback.

No ejecutar rollback salvo incidencia y autorización.

## Resultado permitido

Solo uno de:

`READY_FOR_HUMAN_MAIN_REVIEW`

`BLOCKED`

`READY_FOR_HUMAN_MAIN_REVIEW` NO significa “sin bugs”. Significa que los gates definidos han sido ejecutados y no tienen blockers conocidos.

Incluso en READY:

**NO MERGE A MAIN / NO PRODUCCIÓN SIN AUTORIZACIÓN EXPLÍCITA DEL USUARIO.**

---

# 4. GATES TRANSVERSALES QUE NINGUNA TAREA DEBE ROMPER

A medida que avancen los bloques, preservar:

## Contenido/SEO

- canonical;
- robots;
- titles/descriptions salvo scope explícito;
- JSON-LD;
- OG/Twitter;
- facts de libros/autor/premios/eventos;
- contenido literario preservation-critical.

## Accesibilidad

- teclado;
- focus visible;
- skip links;
- headings;
- labels;
- zoom 200 %;
- WCAG text-spacing;
- reduced motion;
- no dependencia del color;
- touch targets.

## Responsive

- cero overflow horizontal de página;
- local scroll solo cuando está documentado/justificado;
- fresh context por viewport.

## Privacidad/seguridad

- no secretos en cliente;
- no relajación CSP;
- no third-party nuevo por comodidad;
- consentimiento/telemetría ya integrados no se reescriben salvo regresión demostrada;
- Assistant deny-by-default/citation validation se preserva.

## Generated/source

- fuente antes que output;
- builders idempotentes;
- no drift silencioso;
- checks que fallen por comportamiento real, no por el `main` antiguo.

---

# 5. FORMATO OBLIGATORIO DEL INFORME DE CADA PR

Al terminar una tarea de implementación, devolver:

1. tarea;
2. rama;
3. SHA base real;
4. HEAD;
5. URL PR;
6. draft sí/no;
7. commits;
8. archivos modificados;
9. archivos eliminados;
10. ownership/source/template encontrados;
11. estado inicial;
12. cambios implementados;
13. contenido/facts/schema modificados exactamente;
14. contenido/facts/schema eliminados exactamente;
15. tests ejecutados + `PASS/FAIL/NO HECHO/INCOMPLETO`;
16. browser QA;
17. responsive por viewport;
18. keyboard/focus;
19. zoom/text-spacing;
20. reduced motion;
21. no-JS;
22. Lighthouse/performance si aplica;
23. CI final;
24. screenshots/artifacts;
25. bugs encontrados;
26. bugs corregidos;
27. bugs pendientes;
28. riesgos;
29. siguiente bloque sugerido, **sin empezarlo**.

Si `bugs pendientes` contiene un bug real de scope:

- PR DRAFT;
- no escribir “listo para integrar”.

Para las tareas 9 y 10, el informe debe dejar claro que son **report-only** y que no se ha aplicado la decisión destructiva/editorial.

---

# 6. SUPERPROMPT PARA EL AGENTE QUE ESTÁ TRABAJANDO

```text
Continúa EXACTAMENTE WEB 2026 en:

davidpd89/web-escritor

NO reinicies investigación.
NO reabras la dirección visual.
NO trabajes sobre main.
NO despliegues.
NO integres tus propias PR.
NO apiles tareas.

Tu autoridad operativa es:

docs/WEB-2026-HANDOFF-REMAINING-WORK.md

Lee el documento COMPLETO antes de decidir qué sigue.

ANTES DE CUALQUIER TAREA:

git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
git status
git rev-parse HEAD

Si el worktree no está limpio, DETENTE y no descartes trabajo.

ESTADO IMPORTANTE:
- PR #21 Editoriales builder parity: integrada.
- PR #22 Convocatorias builder parity: integrada.
- PR #23 Newsletter/contacto/Brevo: integrada.
- PR #24 acabado visual: integrada.
- La antigua rama gpt/global-shell-closure-v1 NO hizo el cierre global de shell: fue utilizada por Convocatorias. El cierre global está reinsertado como gpt/global-shell-closure-v1-2.
- PR #26 site residual cleanup puede seguir activa: NO la dupliques ni la pises. Si sigue abierta, termina/reporta tu trabajo actual y espera revisión antes de crear una tarea que solape.
- PR #27 release-readiness-v1 es provisional y está apilada sobre #26. NO es la readiness final y NO debes seguir construyendo encima de ella.

PROTOCOLO:
1. Ejecuta SOLO la primera tarea pendiente aplicable del handoff.
2. Crea la rama exacta desde el HEAD actualizado de origin/implementacion-web-2026.
3. Recupera ownership/source/template/builder/tests antes de editar.
4. Implementa completamente el scope.
5. Bug dentro del scope = reproducir + corregir + test.
6. No rebajes CI/Lighthouse/a11y/CSP/security.
7. No conviertas opiniones tuyas en assertions.
8. PASS solo si ejecutaste la prueba.
9. Revisa todo el diff antes de push.
10. Abre PR contra implementacion-web-2026.
11. NO MERGE.
12. DETENTE y entrega el informe requerido.

No empieces la tarea siguiente hasta que una persona haya revisado/integrado la PR anterior y hayas actualizado de nuevo implementacion-web-2026.

Si descubres que una tarea ya está objetivamente resuelta por una PR integrada, NO la dupliques: demuestra la evidencia, marca SATISFECHA y pasa esa conclusión al revisor. No saltes tareas basándote solo en nombres de ramas o PR.
```

---

# 7. CHECKLIST DEL REVISOR / CONTROL TOWER

Nunca aprobar basándose únicamente en el informe del trabajador.

Para cada PR:

1. obtener PR live de GitHub;
2. comprobar base/head;
3. comprobar que la rama nace del integration HEAD correcto;
4. revisar diff real y `name-status`;
5. buscar archivos inesperados;
6. revisar borrados de contenido/facts/schema;
7. comprobar CI real;
8. reproducir al menos la garantía central del bloque;
9. distinguir warning/baseline/regresión;
10. corregir bugs de review antes de integrar;
11. integrar solo si procede;
12. después del merge obtener el nuevo HEAD de `implementacion-web-2026`.

Especialmente:

- no dar por terminada Tarea 1 solo porque exista la rama histórica `gpt/global-shell-closure-v1`;
- no dar por cerrada la frescura del radar solo porque builder parity esté verde;
- no considerar PR #27 la readiness final;
- no borrar assets no referenciados sin decisión humana;
- no aplicar propuestas SEO del informe sin decisión editorial.

---

# 8. DEFINITION OF DONE REAL DE ESTA FASE

La fase puede pasar a revisión humana de `main` cuando:

- PR #26/residual audit está resuelta;
- no quedan superficies públicas legacy accidentales;
- reflow/text-spacing sitewide está protegido;
- CSS ownership tiene gate suficiente;
- Convocatorias no puede quedar stale silenciosamente;
- builders públicos son reproducibles/idempotentes;
- performance/CWV no tiene blocker conocido;
- cross-browser smoke no descubre regresiones críticas;
- edge/HTTP contract está verificado hasta donde el repo/staging permite;
- informes de assets y SEO existen y sus decisiones pendientes están explícitas;
- no hay PR funcional que vaya a cambiar el release candidate;
- Release Readiness V2 se genera DESDE ESE HEAD FINAL;
- existe rollback documentado;
- el resultado es `READY_FOR_HUMAN_MAIN_REVIEW`.

Y aun así:

**NO MERGE A `main` Y NO PRODUCCIÓN SIN AUTORIZACIÓN EXPLÍCITA DEL USUARIO.**
