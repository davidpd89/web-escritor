# Diseño — `/fragmento/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Cadena de diseño:

1. #163 — `DISEÑO - HOME · unificación visual azul/dorado`.
2. #174 — `DISEÑO - Libros · unificación visual del hub de Obras`.
3. #205 — `DISEÑO - Manecillas · unificación visual de la ficha principal`.
4. #264 — `DISEÑO - Fragmentos · unificación visual de la página de lectura`.
5. #265 — `DISEÑO - Samuel entre mundos · unificación visual de la ficha principal`.
6. #266 — `DISEÑO - Samuel · unificación visual del capítulo 1`.

PR raíz de toda la cadena: **#163**.

La rama `design/samuel-fragmento-visual-unification-2026-08-29` nace de #265 y permanece apilada sobre `design/samuel-visual-unification-2026-08-29` hasta que las bases anteriores se integren.

No mergear fuera de orden. Tras integrar cada base, retargetear la siguiente PR a `main` y verificar que su diff propio continúe limpio.

## 2. Objetivo

`/fragmento/` no es una ficha de libro ni un artículo de Cuaderno: es una superficie de lectura de ficción larga. Conserva la arquitectura funcional de Article que ya resuelve medida de lectura, responsive, progreso, newsletter y shell, pero adquiere continuidad inequívoca con Samuel mediante materiales azul/negro/dorado.

Principios cerrados:

- prosa serif negra como protagonista;
- ancho de lectura existente preservado;
- azul `#1d4f96` para orientación/jerarquía;
- dorado `#b8860b` solo como acento editorial y aperturas grandes;
- Yellowtail para aperturas y acciones, nunca para la prosa literaria;
- rail azul real de `2.5px` acompañando figura + capítulo;
- dobles reglas azul/dorado para transiciones;
- azul pálido `#eefaff` solo en bloques prácticos/conversión;
- cero cards dentro del capítulo;
- CTA persistente compacto y compatible con safe areas;
- un solo acceso flotante/persistente por zona: en esta página el launcher flotante del asistente se desactiva y `Asistente` permanece en el header.

## 3. Invariantes de contenido y funcionalidad

No se modifica:

- title, description, canonical, OG/Twitter ni JSON-LD;
- texto del capítulo;
- `data-nosnippet`;
- breadcrumbs;
- metadatos de Samuel/Libros Indie;
- imagen/alt/width/height del capítulo;
- URL Amazon y afiliación;
- enlaces a ficha, Noveris y guía;
- formulario/newsletter ni endpoint;
- `data-reading-progress` ni el runtime que mueve la barra;
- lógica inline de `#sticky-cta`, dismissal en `sessionStorage` ni sus destinos;
- contratos no-JS/cross-engine/reflow previos.

`qa/samuel-book-fragment-browser.mjs` y `qa/samuel-ecosystem-browser.mjs` siguen siendo autoridad funcional.

## 4. Auditoría visual de baseline y defectos encontrados

Evidencia inicial recuperada del artefacto final de #265:

- `fragmento-1440x1000.png` — desktop;
- `fragmento-390x900.png` — móvil.

### FRG-01 · identidad genérica de Article

Hero, figura y capítulo se percibían como un artículo genérico del Cuaderno. No existía una continuidad material clara con la ficha Samuel.

**Cierre:** apertura, H1, rails, figura, separadores, CTA final, continuidad y newsletter usan ya el vocabulario Samuel sin alterar la medida de lectura.

### FRG-02 · sticky CTA negro

`#sticky-cta` utilizaba `--surface-inverse` negro y botones invertidos. En móvil ocupaba además una franja excesiva de lectura.

**Cierre:** banda blanca compacta con reglas azul/dorado, acciones Yellowtail azules, cierre circular y límite de altura automatizado.

### FRG-03 · launcher flotante en conflicto con la lectura/sticky

El baseline móvil ya mostraba el launcher invadiendo figura/caption. La primera implementación lo ocultó solo `<=1300px`, pero el QA real de 1440 descubrió un defecto adicional: el launcher coincidía exactamente con `#sticky-cta-close` e interceptaba el clic.

**Cierre definitivo:** el launcher flotante queda desactivado en **todos los anchos de `/fragmento/`**. No se elimina el asistente: `Asistente` permanece disponible en el header y el QA comprueba que siga visible antes y después de cerrar el sticky. La regla compartida está estrictamente acotada a `html[data-editorial-context="samuel"] body[data-reading-progress]`, por lo que no afecta a la ficha principal ni a Manecillas.

### FRG-04 · CTA final genérica

`¿Qué pasa después?` era una caja blanca con borde neutral y botón negro.

**Cierre:** bloque práctico azul pálido con dobles reglas y acciones manuscritas, manteniendo copy, ISBN y destinos.

### FRG-05 · divisores y continuidad neutros

Divider interno, Article End y newsletter conservaban reglas del Article genérico.

**Cierre:** dobles reglas azul/dorado y jerarquía cromática de Samuel.

### FRG-06 · tokens del sticky fuera de scope

La primera implementación declaró `--frag-*` dentro de `.article-page`, pero `#sticky-cta` vive fuera de `<main>`. Cross-engine detectó que el sticky seguía resolviendo el material legacy negro.

**Cierre:** los tokens se elevaron a `html[data-editorial-context="samuel"]`. El test no se relajó; ahora exige el material azul/dorado efectivo.

### FRG-07 · safe area inferior de iPhone

`/fragmento/` ya usa `viewport-fit=cover`, pero el CTA `position:fixed` no reservaba `env(safe-area-inset-bottom)`.

**Cierre automático:** el padding inferior suma la safe area cuando el navegador la expone, sin aumentar la altura donde el inset es `0`.

**Pendiente físico:** verificar el resultado en Safari/iOS real.

### FRG-08 · evidencia full-page y elementos fixed

Las capturas full-page pueden representar un elemento `fixed` en una posición intermedia del documento durante el stitching aunque el contrato funcional lo haya cerrado. Por eso el QA no usa la miniatura full-page como única evidencia del sticky: genera capturas viewport específicas en 1280 y 390 y prueba clase `visible`, estilo efectivo, altura, clic de cierre y `sessionStorage`.

## 5. Implementación visual final

### Apertura

- eyebrow Yellowtail/dorado, tamaño editorial grande y highlight azul;
- H1 azul con stroke dorado fino;
- deck negro;
- metadata neutral con rail azul de `2.5px`;
- cierre del hero con doble regla azul/dorado.

### Lectura

- `article-layout` deja de reservar columnas sin TOC;
- `article-prose` conserva `--reading-max` y permanece centrado;
- rail azul `2.5px` acompaña figura + capítulo;
- figura con borde azul/acento dorado mínimo;
- título repetido del capítulo pequeño/UI, azul y con regla azul;
- párrafos, sangrías, diálogos y aside literario mantienen tipografía/ritmo;
- divider interno con doble regla azul/dorado.

### Conversión final

- bloque azul pálido, sin card redondeada;
- apertura Yellowtail/dorada;
- H2 azul;
- acciones Amazon/ficha/guía en Yellowtail azul, sin botón negro;
- ISBN neutral.

### Continuidad/newsletter

- dobles reglas azul/dorado;
- aperturas Yellowtail/doradas;
- H2 azules;
- enlaces de continuidad Yellowtail azul;
- submit newsletter azul con hover/focus pale/dorado.

### Sticky CTA

- blanco semitransparente, regla azul + oro y sombra azul mínima;
- acciones Yellowtail azules sin material negro;
- cierre circular azul/dorado;
- composición móvil compacta;
- lógica de visibilidad/dismiss intacta;
- tokens disponibles desde el contexto raíz;
- padding inferior con `env(safe-area-inset-bottom)`;
- launcher flotante del asistente desactivado en toda la ruta; acceso del header preservado.

### Reading progress

Se conserva el elemento funcional existente y únicamente cambia su material a gradiente azul→dorado.

## 6. Responsive certificado automáticamente

Viewports del QA específico final:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800;
- 900×800;
- 768×1024;
- 620×900;
- 390×844;
- 360×800.

El HEAD final automatiza:

- metadata desktop vs apilada `<=900`;
- rail continuo figura→fin de capítulo;
- medida de prosa estable;
- CTA sticky compacto y sin overflow;
- launcher flotante ausente en todos los anchos y `Asistente` del header disponible;
- CTA final/newsletter sin compresión ni columnas implícitas;
- sticky visible tras scroll real y dismiss persistente en `sessionStorage`;
- safe-area compatible por CSS;
- Sitewide Reflow sin fallos.

## 7. Rendimiento

Baseline conocido del Lighthouse focalizado de #265 para `/fragmento/`:

- warning no bloqueante de LCP: mediana observada `3642.2835ms` con warning `<=3500ms`;
- workflow general `success`.

#266 no añade imágenes, JavaScript ni fuentes. Lighthouse general y el gate focalizado de Samuel pasan en el HEAD técnico final.

## 8. QA final

### Chromium / capturas

`qa/samuel-fragmento-design-browser.mjs` valida:

- identidad/canonical/data-nosnippet;
- apertura/H1/meta;
- rail `2.5px`;
- figura azul/dorada;
- capítulo/divider;
- CTA final;
- Article End/newsletter;
- reading-progress;
- sticky real, altura y materiales;
- dismiss + `sessionStorage`;
- ausencia del launcher y disponibilidad del asistente del header;
- overflow;
- capturas full-page de nueve viewports;
- capturas viewport específicas del sticky en 1280 y 390.

Artefacto final `sitewide-reflow-qa` del último HEAD runtime certificado:

- `samuel-fragmento-design-report.json`: `failures: []`;
- `sitewide-reflow-report.json`: `failures: []`;
- las nueve capturas y los dos estados sticky fueron inspeccionados manualmente en esta revisión y no muestran un defecto objetivo pendiente de geometría, seam u overflow.

### Cross-engine

`qa/samuel-fragmento-design-cross-engine.mjs` comprueba Chromium, Firefox y WebKit en desktop/móvil, incluido sticky, cierre y ausencia permanente del launcher flotante.

### Autoridad funcional

`Samuel ecosystem browser QA` permanece verde. Los contratos previos de Samuel/fragmento no se sustituyen.

### Estado de CI del HEAD runtime certificado

Verificados en `success`:

- Sitewide Reflow QA;
- Cross-engine smoke;
- Samuel ecosystem browser QA;
- Accessibility baseline / Pa11y;
- Runtime scoping QA;
- CSP public shell QA;
- Analytics taxonomy QA;
- Check content indexes;
- Tool engine tests;
- Check external links;
- Lighthouse CI / budgets.

## 9. Revisión real multi-dispositivo pendiente antes del merge

Esta PR hereda `docs/design-system/REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

Claude/mantenedor debe comprobar como mínimo:

### iPhone físico + Safari/iOS

- carga y scroll largo del capítulo;
- rail, figura y caption;
- sticky CTA durante scroll real, altura, cierre y persistencia;
- safe area inferior con indicador Home/Dynamic Island;
- orientación vertical/horizontal;
- teclado/focus en newsletter;
- back-forward cache y vuelta desde background;
- `Reducir movimiento` activado/desactivado;
- que el sticky no tape contenido ni controles de Safari;
- que `Asistente` del header siga siendo un acceso suficiente al no existir launcher flotante.

### Otros dispositivos

- Android/Chrome real cuando esté disponible;
- tablet real si es posible;
- desktop Chrome/Firefox y Safari/Edge en la revisión global de publicación.

La incidencia de vídeo/tinta de HOME reproducida en iPhone pertenece a #163 y no debe corregirse mezclándola en esta PR.

## 10. Revisión humana perceptiva pendiente

Además del hardware real, revisar:

- ritmo de lectura prolongada;
- percepción del rail durante scroll largo;
- Yellowtail/stroke a distintos DPI;
- hard reload/cache/staging;
- que la conversión no resulte intrusiva frente al texto.

Una preferencia estética nueva no reabre automáticamente la PR; un defecto reproducible sí.

## 11. Definition of Done

- [x] Rama apilada sobre #265 y enlazada a #163.
- [x] Baseline desktop/móvil recuperado e inspeccionado.
- [x] Capa visual específica aplicada en `assets/fragmento.css`.
- [x] QA visual dedicado añadido.
- [x] QA cross-engine específico añadido.
- [x] Defecto de tokens del sticky fuera de scope corregido.
- [x] Safe-area inferior incorporada.
- [x] Colisión launcher/sticky detectada y corregida sin duplicar accesos.
- [x] Capturas finales revisadas en nueve breakpoints + sticky 1280/390.
- [x] Gates verdes en HEAD runtime certificado.
- [ ] Revisión iPhone/Safari en hardware real.
- [ ] Revisión humana final antes del merge.

`/fragmento/` queda **cerrada técnicamente**. La PR permanece Draft y no debe declararse lista para merge hasta completar la revisión real/humana pendiente.