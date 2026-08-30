# Diseño — `/universo/noveris/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Cadena de diseño:

1. #163 — `DISEÑO - HOME · unificación visual azul/dorado`.
2. #174 — `DISEÑO - Libros · unificación visual del hub de Obras`.
3. #205 — `DISEÑO - Manecillas · unificación visual de la ficha principal`.
4. #264 — `DISEÑO - Fragmentos · unificación visual de la página de lectura`.
5. #265 — `DISEÑO - Samuel entre mundos · unificación visual de la ficha principal`.
6. #266 — `DISEÑO - Samuel · unificación visual del capítulo 1`.
7. esta PR — `/universo/noveris/`.

PR raíz: **#163**. La rama `design/noveris-visual-unification-2026-08-29` nace exactamente del HEAD de #266. No mergear fuera de orden; al integrar las bases, retargetear a `main` y verificar de nuevo el diff propio.

## 2. Objetivo

Noveris debe leerse como **archivo de mundo / documento de lore**, no como herramienta ni como grid genérico de cards. Comparte la firma azul/negro/dorado de Samuel, pero cada bloque conserva su función documental:

- mapa como pieza visual principal;
- focos de conocimiento como registros;
- sistema mágico/canalizadores como archivo técnico;
- zonas como registro geográfico;
- historia como ensayo documental;
- glosario como lexicón ledger;
- FAQ y lectura relacionada como cierre práctico.

No se homogeneizan estas superficies en una única tarjeta visual.

## 3. Invariantes

No se modifica `universo/noveris/index.html`. Se preservan:

- title, description, canonical y OG/Twitter;
- JSON-LD `WebPage`, `DefinedTermSet` y `FAQPage`;
- orden y texto de los términos canónicos;
- Wikidata `sameAs`;
- textos de lore;
- imágenes, alt, width/height y captions;
- enlaces a Samuel, capítulo, clubes, guía y Amazon;
- navegación contextual Samuel;
- IDs/anchors (`respuesta`, `sistema`, `mapa`, `historia`, `glosario`, `libro`, `preguntas-frecuentes`);
- comportamiento nativo de `<details>`;
- contratos de 200% texto, text spacing, CLS y reflow cubiertos por `qa/samuel-ecosystem-browser.mjs`.

## 4. Baseline auditado

La evidencia de #265 (`noveris-1440.png` y `noveris-390.png`) mostraba siete problemas objetivos:

1. hero de herramienta genérica, H1 negro y CTA negro;
2. exceso de `id-card` con jerarquía plana;
3. tabla de canalizadores dependiente de scroll horizontal en móvil;
4. mapa principal tratado como figura genérica;
5. glosario estructuralmente correcto pero sin firma Samuel;
6. shell/footer genéricos;
7. capturas full-page susceptibles de registrar reservas de lazy media antes de `decode()`.

## 5. Sistema visual aplicado

### Scoping y hoja compartida

`assets/noveris.css` **no es exclusiva de Noveris**: también la cargan superficies companion de Samuel, incluido el club/guía. Por eso la capa V2 del archivo se limita mediante el guard estructural de la ruta:

`html.v1[data-editorial-context="samuel"]:has(main[data-family="lore"]>#respuesta .lore-figure)`

Las primitivas anteriores al bloque V2 permanecen neutrales y compartidas. El smoke cross-engine comprueba que las reglas específicas de Noveris no se filtren al Club Samuel.

### Tokens

- azul `#1d4f96`;
- azul oscuro `#0d2c57`;
- dorado `#b8860b`;
- azul pálido `#eefaff`;
- negro `#050505`;
- neutral `#6f6a64`.

### Hero y secciones

- apertura Yellowtail/dorada + highlight azul;
- H1 `Noveris` azul con micro-stroke dorado;
- lead de lectura negro;
- acciones manuscritas azules, sin botón negro;
- dobles reglas azul/dorado;
- H2 azules y prosa serif con ancho de lectura.

### Mapa y focos

- rail azul real de `2.5px`;
- marco azul mínimo y cierre dorado;
- caption neutral;
- el mapa mantiene anchura protagonista;
- artefacto, facciones, ciudad y Velo/Barrera se convierten en registros editoriales abiertos, no en cajas uniformes.

### Canalizadores

Desktop conserva `<table>` y semántica tabular. En `<=760px` cada `tr` pasa visualmente a registro legible sin scroll horizontal, con etiquetas por pseudo-elemento y una presencia mínima de `60px` para las imágenes documentales.

### Zonas y glosario

- zonas: registro 2×2 que pasa a una columna en `<=760px`;
- glosario: ledger término/definición que se apila en `<=640px`;
- FAQ, lectura relacionada, footer y Volver arriba siguen la firma azul/dorado de Samuel.

## 6. Responsive contractual

El QA específico cubre:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800 y 900×800;
- 768×1024;
- 761×900 y 760×900;
- 641×900 y 640×900;
- 390×844;
- 360×800.

Costuras:

- `901/900`: registro/bento documental de dos columnas a una;
- `761/760`: tabla y zonas a registro móvil;
- `641/640`: glosario lateral a apilado.

## 7. QA y defectos corregidos

### Chromium visual

`qa/noveris-design-browser.mjs` comprueba identidad, rail, mapa, registros, tabla móvil, imágenes, zonas, 14 términos del glosario, FAQ, footer, launcher, overflow, carga/`decode()` y capturas full-page de los 12 viewports.

Durante la primera ejecución se encontraron y corrigieron defectos reales:

- hover/focus del `Asistente` sin el estado azul pálido contractual;
- miniaturas de canalizadores capaces de encogerse por debajo de `60px` entre 761 y 1024;
- `<caption>` de la tabla colapsado en `<=760px`, que llegaba a pintarse letra a letra en vertical;
- popup de newsletter contaminando la evidencia visual del hero.

También se corrigió un falso negativo del propio QA: `header-search` y `Explorar` tienen transición contractual de `220ms`; la comprobación visual espera al estado final antes de leer `getComputedStyle()`.

### Cross-engine y aislamiento

`qa/noveris-design-cross-engine.mjs` cubre Chromium, Firefox y WebKit. El smoke valida además que el scoping V2 de `noveris.css` no afecte al Club Samuel.

### Autoridad funcional

`qa/samuel-ecosystem-browser.mjs` sigue siendo autoridad para contenido/schema/glosario, imágenes, anchors, 320→1728, landscape, stress de contenido, 200% texto, text spacing y CLS.

## 8. Evidencia final revisada

Artefacto final de `Sitewide Reflow QA` del HEAD técnico `b78f249bc6b0d910e4fe47d201cfdbdaabc06526`:

- `noveris-desktop-1440.png`;
- `noveris-desktop-1280.png`;
- `noveris-tablet-1024.png`;
- `noveris-bento-901.png` / `noveris-bento-900.png`;
- `noveris-tablet-768.png`;
- `noveris-table-761.png` / `noveris-table-760.png`;
- `noveris-glossary-641.png` / `noveris-glossary-640.png`;
- `noveris-mobile-390.png`;
- `noveris-mobile-360.png`.

Inspección visual final: sin overflow visible; transición 901/900 coherente; tabla correcta en 761/760; caption móvil ya no colapsa; glosario correcto en 641/640; 390/360 mantienen jerarquía, imágenes, FAQ y footer sin recortes ni solapes observables.

Los **11 workflows** asociados a ese HEAD terminaron `completed/success`: Tool engine tests, Check content indexes, Analytics taxonomy QA, CSP public shell QA, Runtime scoping QA, Accessibility baseline (Pa11y), Cross-engine smoke, Global discoverability closure QA, Samuel ecosystem browser QA, Sitewide Reflow QA y Lighthouse CI.

## 9. Revisión física/humana pendiente antes del merge

Heredar `docs/design-system/REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` y comprobar:

- iPhone/Safari real: tabla móvil, mapa, scroll largo, FAQ, safe areas y rotación;
- Android/Chrome real;
- tablet real si es posible;
- Safari/Edge desktop en la revisión global;
- legibilidad de registros de canalizadores a DPI real;
- detalle útil del mapa y ritmo del glosario largo;
- hard reload, cache y back-forward cache;
- hover/focus de acciones, FAQ, footer y Volver arriba.

La incidencia de tinta de HOME en iPhone pertenece a #163 y no se mezcla aquí.

## 10. Definition of Done

- [x] rama apilada sobre #266 y ligada a #163;
- [x] baseline 1440/390 recuperado e inspeccionado;
- [x] dirección documental definida;
- [x] capa visual implementada con scoping aislado;
- [x] QA Chromium específico añadido;
- [x] QA cross-engine específico añadido;
- [x] ejecución CI revisada;
- [x] defectos objetivos de navegador corregidos;
- [x] capturas finales y seams revisados;
- [x] 11 gates finales verdes en el HEAD técnico auditado;
- [ ] revisión física/humana antes del merge.

**Estado:** técnicamente cerrada a nivel de código, CI y evidencia automatizada. Mantener la PR en Draft y no mergear hasta completar la revisión física/humana y respetar el orden de la cadena.