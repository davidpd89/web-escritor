# Herramientas · unificación visual del hub — 2026-08-30

## Alcance

PR #270, apilada sobre #269 (`design/cuaderno-visual-unification-2026-08-30`).

Ruta intervenida: `/herramientas/`.

Fuera de alcance deliberado: las herramientas individuales y sus motores. El hub recibe una capa visual exclusiva; `/herramientas/manuscrito/` se usa como control de aislamiento y no carga esa hoja.

La PR modifica únicamente el workflow de Tools, el JS de filtros del hub, la hoja exclusiva `assets/herramientas-index.css`, el HTML generado del índice, el contrato QA y el builder del índice. No se modifica `data/tools-hub.json`, ninguna página interna ni ningún motor de herramienta.

En producción, `scripts/build-tools-hub.py` añade únicamente el enlace a `/assets/herramientas-index.css`; `herramientas/index.html` fue regenerado desde el builder y su diff resultante fue exactamente una inserción: ese `<link>`.

## Diagnóstico de baseline

Antes de cerrar la dirección se añadió `qa/herramientas-index-design-browser.mjs` y se ejecutó contra el HEAD heredado.

Baseline y contrato trabajan con 13 anchuras: 1728, 1440, 1280, 1024, 901, 900, 768, 767, 640, 390, 389, 360 y 320 px.

La estructura heredada ya era válida: un masthead, finder con siete filtros, 22 herramientas agrupadas en ocho familias, dos directorios relacionados y bloque de metodología. La deuda principal era visual: tratamiento V1 genérico, jerarquía poco editorial y falta de continuidad con el sistema azul/dorado de la cadena de diseño.

No se justificó reconstruir contenido, URLs, JSON-LD, headings ni los motores.

## Dirección cerrada

El hub se define como **catálogo editorial de trabajo / workbench de escritor**, no como dashboard SaaS ni landing de cards genéricas.

La capa exclusiva `assets/herramientas-index.css` introduce:

- azul editorial `#1d4f96`;
- azul profundo `#0d2c57`;
- dorado `#b8860b`;
- pale blue `#eefaff`;
- apertura manuscrita Yellowtail con highlight;
- H1 editorial de gran escala;
- doble regla azul/dorado como transición del masthead;
- finder con rail azul/dorado y estado activo azul;
- familias numeradas `01 /` a `08 /`;
- catálogo 3→2→1 columnas según ancho;
- cards rectas con regla propia, sin esquinas redondeadas ni botones rellenos;
- CTAs de texto azul con subrayado dorado;
- directorios, metodología, navegación contextual y footer alineados con el mismo sistema.

Seams deliberados:

- >900 px: filtros en 4 columnas y catálogo en 3;
- <=900 px: filtros y catálogo en 2;
- <=767 px: cabecera de familia en una columna;
- <=640 px: catálogo en una columna;
- <=389 px: filtros en una columna.

## Aislamiento y paridad del generador

`assets/herramientas-index.css` se enlaza únicamente desde `/herramientas/`.

El workflow `Tools browser QA` ejecuta `python scripts/build-tools-hub.py data/tools-hub.json herramientas/index.html --check` antes de iniciar el navegador. La salida publicada y el builder quedan por tanto bajo contrato de paridad.

Durante la implementación se detectó que el HTML generado no contenía todavía el nuevo `<link>`. Se generó la salida con el propio builder y el commit automático `8b3e3e01caa913e035aeb5fda041223d1a5e8052` modificó `herramientas/index.html` con exactamente una inserción. Después se retiró el permiso temporal de escritura del workflow y volvió a `contents: read`.

## Defecto funcional encontrado y corregido

La revisión del hub descubrió un defecto preexistente no cubierto por el QA anterior: el botón `Para lectores` existía en el HTML, pero `assets/herramientas-hub.js` no definía el grupo `lectores`. Al pulsarlo se mostraban cero herramientas en lugar del test de lector.

Corrección: `77007ac5003455609beda80bce3de2579cacdd62` (`fix(herramientas): restore reader filter`).

El contrato final pulsa los siete filtros y verifica número de herramientas, número de familias, `aria-pressed` y contador del finder. Para `lectores` exige 1 herramienta en 1 familia.

## QA visual específico y falsos negativos corregidos

`qa/herramientas-index-design-browser.mjs` pasó de capturador a contrato. Comprueba, entre otros puntos:

- contexto editorial, canonical, H1 único, 22 herramientas, siete filtros, ocho familias y dos directorios;
- token azul y estados azul/dorado;
- acciones transparentes y no redondeadas;
- cadencia responsive exacta en 901/900, 768/767, 640 y 390/389;
- cero overflow horizontal;
- funcionamiento real de los siete filtros;
- aislamiento frente a `/herramientas/manuscrito/`;
- capturas completas en 13 viewports.

Dos fallos del propio contrato se corrigieron sin tocar producción:

1. `getComputedStyle(..., '::before').content` devuelve la expresión CSS `counter(tools-family, decimal-leading-zero) " / "`, no el valor resuelto `01 /`. El QA pasó a validar `counter-increment: tools-family` y la expresión `counter(...)`.
2. `innerText()` aplicaba `text-transform: uppercase` al contador del finder (`8 HERRAMIENTAS`). Se sustituyó por `textContent()` para comprobar el contenido funcional real sin confundirlo con presentación CSS.

Commits de estabilización del contrato: `1608c9e5c926531000abbba4149f581bd240ec99` y `6af19b1aa67b9f2a839ed5a8484db27c2606a681`.

## Defecto visual encontrado en la evidencia y corregido

La primera revisión manual del artefacto verde de `6af19b1aa67b9f2a839ed5a8484db27c2606a681` encontró un defecto no detectable por métricas: la primera familia contiene siete herramientas y el `gap` de 1 px con fondo azul pálido hacía que las dos celdas inexistentes de la última fila apareciesen como un bloque azul vacío.

No se aceptó como detalle cosmético. Se cambió el sistema de separación para que cada herramienta tenga su propia regla y el contenedor permanezca transparente; las posiciones vacías vuelven a papel blanco.

Commit correctivo final de código: `2b8692f4d34af588bb66df950a9806aeb77812a1` (`fix(herramientas): keep empty catalog cells on paper`). El diff está limitado a `assets/herramientas-index.css`: 5 adiciones y 6 eliminaciones.

## Evidencia automática final de código

HEAD de código revisado: `2b8692f4d34af588bb66df950a9806aeb77812a1`.

En ese HEAD: **11/11 workflows completados con success**:

- Check external links
- Tool engine tests
- Check content indexes
- Analytics taxonomy QA
- CSP public shell QA
- Runtime scoping QA
- Tools browser QA
- Accessibility baseline (Pa11y)
- Cross-engine smoke
- Sitewide Reflow QA
- Lighthouse CI

El artefacto `tools-browser-qa` del run `33306958839` (artifact `9730787314`) tiene digest `sha256:a1e984e9426540fb01f6bc7f6bfe67b050c6fa3af61677cff26b724fc9fa3b94`.

`herramientas-index-design-report.json`: `failures: []`; `overflow: 0` en las 13 anchuras. La paridad del builder también devuelve `OK: 22 herramientas, 2 directorios`.

## Revisión visual final

Revisadas manualmente las capturas completas y comparativas de 1728/1440/1280/1024, seams 901/900 y 768/767, 640, 390/389, 360 y 320 px.

Resultado:

- 1728/1440/1280/1024: jerarquía editorial estable, finder legible y familias claramente diferenciadas;
- el bloque azul fantasma de la última fila ha desaparecido; las celdas inexistentes quedan en papel blanco;
- 901→900: filtros cambian 4→2 y catálogo 3→2 de forma limpia;
- 768→767: la cabecera de familia pasa a una columna sin colisión;
- 640: catálogo entra correctamente en una columna;
- 390→389: filtros cambian 2→1 sin overflow ni solapamiento;
- 360/320: H1, finder, cards y CTAs siguen siendo legibles; no hay desbordamientos horizontales;
- `/herramientas/manuscrito/` conserva su sistema visual y no recibe la hoja del hub.

## DoD

- [x] baseline real capturado antes de cerrar la dirección;
- [x] 22 herramientas, ocho familias, dos directorios y contenido preservados;
- [x] capa visual exclusiva del hub;
- [x] builder y HTML generado sincronizados y bajo `--check`;
- [x] filtro `Para lectores` reparado y cubierto por QA;
- [x] aislamiento de herramientas individuales comprobado;
- [x] contrato visual y funcional en 13 viewports;
- [x] falsos negativos del QA corregidos sin relajar producción;
- [x] defecto visual de celdas vacías detectado en capturas y corregido;
- [x] 11/11 workflows verdes en HEAD de código;
- [x] capturas finales y seams revisados manualmente;
- [ ] revisión humana en dispositivos físicos según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Estado

**Técnicamente cerrado por código/CI/revisión visual automatizada y manual de capturas.**

La PR debe permanecer **Draft, abierta y sin merge** hasta completar la revisión humana/física y respetar el orden de la cadena de PRs.

Este documento es el último commit documental de #270; el HEAD resultante debe volver a verificarse en CI antes de considerar definitivo el cierre técnico de la PR.