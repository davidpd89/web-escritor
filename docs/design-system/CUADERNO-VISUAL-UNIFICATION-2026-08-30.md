# Cuaderno · unificación visual del índice — 2026-08-30

## Alcance

PR #269, apilada sobre #268 (`design/club-samuel-visual-unification-2026-08-30`).

Ruta intervenida: `/cuaderno/`.

Fuera de alcance deliberado: los artículos individuales del Cuaderno. Siguen usando el sistema compartido de lectura `v1-editorial.css` y no cargan la capa exclusiva del índice.

No se modifican URLs, contenido editorial, JSON-LD, jerarquía de headings, newsletter, enlaces internos ni el shell generado. En `cuaderno/index.html` el único cambio de producción es la carga de `/assets/cuaderno-index.css`.

## Diagnóstico de baseline

Antes de modificar producción se añadió `qa/cuaderno-index-design-browser.mjs` y se ejecutó contra el HEAD heredado de #268.

Baseline verificado en 13 anchuras: 1728, 1440, 1280, 1024, 901, 900, 768, 767, 640, 390, 389, 360 y 320 px.

El baseline confirmó:

- estructura estable de masthead + folio + destacada + ledger + continuidad + newsletter;
- cinco piezas conservadas (`01` destacada + `02–05` archivo);
- cero overflow horizontal en las 13 anchuras;
- seam estructural previsto en 901→900;
- QA funcional existente, outputs generados, WCAG2AA y Lighthouse verdes;
- deuda principalmente visual: cian heredado, reglas grises y jerarquía V1 antigua, desconectados de la cadena azul/dorado ya cerrada en HOME/Obras/Manecillas/Samuel.

No se justificó reconstrucción semántica ni conversión a cards.

## Dirección cerrada

El Cuaderno se define como **publicación editorial viva / archivo de autor**, no como landing SaaS, blog-template, grid de cards ni réplica de Noveris.

La capa exclusiva `assets/cuaderno-index.css` introduce:

- azul editorial `#1d4f96`;
- azul profundo `#0d2c57`;
- dorado `#b8860b`;
- pale blue `#eefaff`;
- aperturas manuscritas Yellowtail con highlight azul;
- masthead de gran escala con folio lateral;
- doble regla azul/dorado como transición principal;
- destacada abierta, con rail azul/dorado en escritorio;
- ledger lineal, sin cards, con numeración dorada y titulares azules;
- continuidad y newsletter tratadas como secciones de la misma publicación;
- CTA y formulario sin lenguaje visual genérico;
- footer y navegación contextual alineados con el sistema azul/dorado.

## Aislamiento

La hoja `assets/cuaderno-index.css` se enlaza únicamente desde `/cuaderno/index.html`.

El contrato QA abre además `/cuaderno/que-es-el-portal-fantasy/` y exige que esa hoja no exista en el documento del artículo. La evidencia visual `article-long-1440.png` conserva la composición de lectura anterior.

No se añadieron reglas compartidas a `v1-editorial.css` para evitar fugas hacia artículos.

## QA visual específico

`qa/cuaderno-index-design-browser.mjs` pasó de capturador de baseline a contrato de diseño. Además de conservar estructura y overflow, exige:

- tokens azul/dorado del Cuaderno;
- navegación contextual activa en azul `#1d4f96`;
- H1 azul y aperturas manuscritas;
- masthead/destacada/ledger/continuidad/newsletter con el nuevo lenguaje;
- CTA editorial transparente donde corresponde;
- seam >900 / <=900;
- aislamiento frente a un artículo;
- capturas completas en 13 viewports.

El workflow canónico `Cuaderno editorial browser QA` ejecuta primero `qa/cuaderno-browser.mjs`, después el contrato visual, outputs generados, WCAG2AA y Lighthouse. No se sustituye ni relaja la autoridad funcional existente.

## Primer run del diseño y corrección

El primer run de la implementación mantuvo verde el QA funcional de toda la familia, pero el contrato visual falló en las 13 anchuras por una única causa:

`v1-site-cohesion-v6.css` mantenía el enlace activo de `.section-context` en el cian heredado `rgb(0, 114, 179)`.

No se modificó el test ni se usó `!important`. Se identificó el selector ganador y se aumentó de forma semántica la especificidad de la regla exclusiva del Cuaderno:

`html.v1[data-editorial-context="cuaderno"] .section-context[data-editorial-context-nav="cuaderno"] .section-context__links a[aria-current="page"]`

Commit correctivo: `bf373a58e03bc172c4ed43a7bbb7995edf13abb3`.

## Evidencia automática final de código

HEAD de código revisado: `bf373a58e03bc172c4ed43a7bbb7995edf13abb3`.

En ese HEAD: **11/11 workflows completados con success**:

- Check external links
- Tool engine tests
- Check content indexes
- Analytics taxonomy QA
- CSP public shell QA
- Runtime scoping QA
- Accessibility baseline (Pa11y)
- Cross-engine smoke
- Cuaderno editorial browser QA
- Sitewide Reflow QA
- Lighthouse CI

El artefacto `cuaderno-editorial-evidence` del run `33304157146` (artifact `9729959150`) contiene el reporte final y las capturas.

`cuaderno-index-design-report.json`: `failures: []`; `overflow: 0` en las 13 anchuras.

## Revisión visual final

Revisadas manualmente las capturas completas de 1728 y 1440, móvil 390, y comparativas de seams 901/900, 768/767, 390/389, además de 360/320.

Resultado:

- 1728/1440: el ancho de publicación y el espacio negativo son coherentes; no aparece sensación de dashboard ni de card-grid;
- 901→900: masthead, destacada, ledger, continuidad y newsletter cambian de columnas de forma limpia;
- 768→767: el formulario pasa de acción lateral a acción apilada sin colisión ni overflow;
- 390→389: el footer entra en su composición estrecha prevista;
- 360/320: títulos, metadatos, ledger y formulario siguen legibles; no hay desbordamientos ni elementos solapados;
- el artículo largo de control mantiene su sistema visual de lectura y no recibe la capa del índice.

## DoD

- [x] baseline real capturado antes de diseñar;
- [x] estructura/contenido preservados;
- [x] capa visual exclusiva del índice;
- [x] aislamiento de artículos comprobado;
- [x] contrato visual 13 viewports;
- [x] primer fallo real diagnosticado y corregido sin relajar QA;
- [x] 11/11 workflows verdes en HEAD de código;
- [x] capturas finales y seams revisados manualmente;
- [ ] revisión humana en dispositivos físicos según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Estado

**Técnicamente cerrado por código/CI/revisión visual automatizada.**

La PR debe permanecer **Draft, abierta y sin merge** hasta completar la revisión humana/física y respetar el orden de la cadena de PRs.

Este documento es el último commit documental de #269; el HEAD resultante debe volver a verificarse en CI antes de considerar definitivo el cierre técnico de la PR.