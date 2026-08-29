# Diseño — `/las-manecillas-del-recuerdo/fragmentos/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

PR inicial de toda la cadena: [#163 — DISEÑO - HOME · unificación visual azul/dorado](https://github.com/davidpd89/web-escritor/pull/163).

Cadena de diseño:

1. PR #163 — `DISEÑO - HOME · unificación visual azul/dorado`.
2. PR #174 — `DISEÑO - Libros · unificación visual del hub de Obras`.
3. PR #205 — `DISEÑO - Manecillas · unificación visual de la ficha principal`.
4. PR #264 — `DISEÑO - Fragmentos · unificación visual de la página de lectura`.

La rama nace exactamente de `1f57df3e94256f53d26faac44ab8c473600bec2e`, HEAD documental cerrado de #205. No mergear antes de las PR previas. Tras fusionar cada base, retargetear manteniendo limpio el diff propio.

## 2. Objetivo

Fragmentos es una página de lectura. Debe pertenecer visualmente al mismo sistema azul/negro/dorado de HOME, Libros y Manecillas, pero sin convertir el texto literario en una sucesión de cards ni en una landing comercial.

Contrato:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- azul de header `#0a4d9f`;
- azul profundo de interacción `#0d2c57`;
- serif/negro para lectura extensa;
- grises neutros para registros, capítulos y metadatos;
- Yellowtail para aperturas y acciones;
- corner brackets en la portada;
- rails reales de `2.5px`;
- separadores azul/dorado;
- azul pálido solo en estados activos/bloques prácticos.

## 3. Contenido y comportamiento que no se toca

Preservado literalmente:

- title, description, canonical, OG/Twitter y JSON-LD;
- los tres fragmentos y su orden;
- `data-nosnippet` de los textos;
- anchors `#fragmento-1`, `#fragmento-2`, `#fragmento-3`, `#cta-final`;
- breadcrumbs y navegación contextual;
- destinos de todos los enlaces;
- `v1-fragments.js` y su lógica de `data-current`, hashchange e IntersectionObserver;
- `body[data-reading-progress]`;
- funnel/analytics existentes;
- portada y art direction.

## 4. Scope técnico

La ficha principal y Fragmentos comparten `data-editorial-context="manecillas"`, `v1-book.css` y clases de libro. La separación deliberada es:

- ficha principal #205: `body:not([data-reading-progress])`;
- Fragmentos: `body[data-reading-progress]`.

`v1-fragments.css` es la capa propia de Fragmentos y las reglas nuevas se restringen a `html.v1[data-editorial-context="manecillas"] body[data-reading-progress]`.

El aislamiento queda protegido en ambos sentidos por QA: la ficha principal recibe `--man-blue` y no `--frag-blue`; Fragmentos recibe `--frag-blue` y no `--man-blue`.

## 5. Implementación visual cerrada

### FRAG-01 · shell/contexto

Context nav, header, Explorar, footer y Volver arriba siguen el contrato ya cerrado en #205, sin teal/beige legacy en hover/focus.

### FRAG-02 · hero de lectura

Se mantiene portada + copy, sin inventar ledger:

- portada con brackets;
- apertura Yellowtail/dorada + highlight azul;
- H1 azul/dorado;
- lead serif negro;
- CTAs manuscritos azules;
- rail azul junto al copy en desktop.

### FRAG-03 · introducción

`Tres escenas, tres momentos distintos / Sin resumen ni destripes` funciona como apertura editorial: doble regla, label dorado y H2 azul. No card.

### FRAG-04 · índice de lectura

- reglas azul/dorado;
- `Registro I/II/III` neutro;
- título serif negro;
- estado activo azul pálido + rail azul real de 2.5px;
- hover/focus azul profundo + acento dorado;
- `data-current` continúa gestionado por el JS existente.

### FRAG-05 · fragmentos

Cada sección conserva prosa serif/negro. Encabezados usan label Yellowtail/dorado, H2 azul/dorado y metadata neutral. La prosa recibe rail azul de `2.5px` sin caja pesada.

### FRAG-06 · paginadores

Direcciones (`Anterior/Siguiente/Continuar`) permanecen UI neutra. Destinos pasan a Yellowtail azul. Separador superior azul/dorado.

La revisión de capturas descubrió un defecto real en `768–899`: el pager heredaba `grid-column:2` cuando la sección ya estaba en una sola columna. El navegador creaba una segunda columna implícita y comprimía la prosa. Se corrigió forzando pager y single-pager a `grid-column:1` y una única columna en esa banda. El QA mide ahora que pager y prosa compartan el ancho de lectura.

### FRAG-07 · cita intermedia

`Este reloj ha vivido más vidas que yo.` es una pausa editorial: rail azul + acento dorado, sin card.

### FRAG-08 · CTA final

`La novela completa` queda como bloque práctico: azul pálido, borde azul + acento dorado, encabezado azul/dorado y acciones Yellowtail.

### FRAG-09 · asistente

En `<=1300px` se oculta solo el launcher flotante duplicado. El acceso `Asistente` del header permanece.

### FRAG-10 · progreso de lectura

`script.js` sigue inyectando y calculando `.reading-progress`; no se modifica su lógica. La capa de Fragmentos cambia únicamente su presentación al gradiente azul→dorado. El QA desplaza la página y confirma que la barra avanza realmente.

## 6. Responsive cerrado

Viewports cubiertos:

- 1440×1000;
- 1280×800;
- 1024×768;
- 900×800;
- 899×800;
- 768×1024;
- 767×900;
- 390×844;
- 360×800.

Contrato efectivo:

- `>=900`: composición desktop;
- `768–899`: portada izquierda + copy derecha y lectura posterior a ancho completo;
- `<=767`: hero apilado, rail exterior, índice y paginadores a una columna;
- `<=639`: context nav deja de ser sticky.

Las capturas finales de 899 y 768 se inspeccionaron después de corregir la columna implícita: prosa a ancho completo, paginadores debajo del texto y transición limpia a 767.

## 7. QA automático

### Chromium / visual y geometría

`qa/manecillas-fragmentos-design-browser.mjs` valida:

- token propio `--frag-blue`;
- portada visible + brackets;
- Yellowtail/dorado y H1 azul;
- índice de tres registros;
- activación real de `data-current`;
- rail activo de `2.5px`;
- tres excerpts;
- prosa con rail `2.5px`;
- geometría de paginadores, incluido el defecto `768–899`;
- cita y CTA final;
- progreso de lectura azul/dorado y avance real al hacer scroll;
- footer, launcher y shell;
- hover/focus;
- ausencia de overflow;
- capturas full-page en todos los viewports.

### Navegación funcional

El workflow `Manecillas fragments navigation QA` permanece verde y cubre navegación, preservación, hashes y malformed-hash regression.

### Aislamiento

`qa/manecillas-scope-isolation.mjs` valida main ↔ Fragmentos en ambos sentidos.

### Cross-engine

`qa/manecillas-cross-engine.mjs` cubre la ficha principal y Fragmentos en Chromium, Firefox y WebKit, incluidos tokens propios, brackets y ausencia de contaminación entre capas.

### Gates generales sobre el HEAD de runtime `90cabf56e7286c787ff4713bc0a9437d91d8e3aa`

Todos verdes:

- Lighthouse CI;
- Accessibility baseline (Pa11y);
- Sitewide Reflow QA;
- Manecillas fragments navigation QA;
- Cross-engine smoke;
- CSP public shell QA;
- Runtime scoping QA;
- Analytics taxonomy QA;
- Check content indexes;
- Tool engine tests;
- Content parity — Libros + Manecillas.

## 8. Fuera de alcance

- reescribir los fragmentos;
- cambiar SEO/structured data;
- cambiar `v1-fragments.js` salvo bug funcional objetivo;
- rediseñar Samuel u otras fichas;
- cambios globales de shell no necesarios para Fragmentos.

## 9. Revisión manual pendiente para Claude/mantenedor

Antes del merge revisar en navegador real:

- 1440/1280, 1024/900, 899/768, 767, 390/360;
- ritmo de lectura real y ancho de columna;
- rails sobre prosa;
- estado activo del índice durante scroll lento/rápido;
- hash directo a los tres fragmentos;
- navegación por teclado del índice y paginadores;
- Yellowtail/stroke dorado en distintos DPI;
- barra de progreso durante lectura real;
- zoom/text-spacing;
- endpoint/funnel real si staging lo permite;
- ausencia de legacy teal/beige en estados interactivos.

Lo que exige navegador/staging real queda indicado aquí; lo reproducible automáticamente ya está cubierto por tests.

## 10. Definition of Done

- [x] Rama apilada sobre #205.
- [x] Implementación visual page-scoped.
- [x] Contenido y JS de lectura preservados.
- [x] QA específico con capturas y seams.
- [x] Cross-engine específico.
- [x] Aislamiento bidireccional con la ficha principal.
- [x] Defecto de pager implícito `768–899` corregido y testeado.
- [x] Progreso de lectura adaptado y testeado.
- [x] Todos los gates verdes sobre el HEAD definitivo de runtime.
- [ ] Revisión humana final de Claude/mantenedor antes del merge.

La PR está cerrada técnicamente. Puede permanecer Draft por el flujo de PRs apiladas; no mergear hasta completar la revisión humana y respetar el orden de la cadena.