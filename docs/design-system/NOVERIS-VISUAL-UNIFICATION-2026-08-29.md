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

PR raíz: **#163**.

La rama `design/noveris-visual-unification-2026-08-29` nace exactamente del HEAD documental de #266. No mergear fuera de orden; al integrar las bases, retargetear la siguiente PR a `main` y verificar su diff propio.

## 2. Objetivo

Noveris debe leerse como **archivo de mundo / documento de lore**, no como herramienta ni como grid genérico de cards. Comparte la firma azul/negro/dorado de Samuel, pero su función es documental:

- mapa como pieza visual principal;
- focos de conocimiento como registros;
- sistema mágico/canalizadores como archivo técnico;
- zonas como registro geográfico;
- historia como ensayo documental;
- glosario como lexicón ledger;
- FAQ y lectura relacionada como cierre práctico.

No se homogeneizan estas superficies en una única tarjeta visual.

## 3. Invariantes que no deben alterarse

- title, description, canonical, OG/Twitter;
- JSON-LD `WebPage`, `DefinedTermSet` y `FAQPage`;
- orden y texto de los términos canónicos;
- Wikidata `sameAs` de Noveris;
- textos de lore;
- imágenes, alt, width/height y captions;
- enlaces a Samuel, capítulo, clubes, guía y Amazon;
- navegación contextual Samuel;
- IDs/anchors (`respuesta`, `sistema`, `mapa`, `historia`, `glosario`, `libro`, `preguntas-frecuentes`);
- comportamiento nativo de `<details>`;
- contratos de 200% texto/text spacing, CLS y reflow ya cubiertos por `qa/samuel-ecosystem-browser.mjs`.

No se modifica `universo/noveris/index.html` en esta primera implementación.

## 4. Baseline auditado

Evidencia recuperada de `Samuel ecosystem browser QA` de #265:

- `noveris-1440.png`;
- `noveris-390.png`.

Problemas objetivos encontrados:

### NOV-01 · hero de herramienta genérica

La apertura usa `.tool-hero`, H1 negro y botón negro. Visualmente parece una herramienta del sitio, no el archivo oficial de un mundo narrativo.

### NOV-02 · exceso de cards

Los focos de conocimiento y las cuatro zonas se apoyan en `id-card`, generando una sucesión de cajas con peso similar. Se pierde jerarquía entre artefacto central, facciones, infraestructura y física dimensional.

### NOV-03 · tabla horizontal en móvil

La tabla de canalizadores conserva un `min-width` grande y depende de scroll horizontal. Es funcional, pero poco cómoda para lectura documental prolongada en 390/360.

### NOV-04 · mapa tratado como contenido genérico

El mapa es el recurso visual más valioso de la página, pero baseline lo encierra en el mismo lenguaje neutral que cualquier figura.

### NOV-05 · glosario correcto pero sin firma Samuel

La estructura ledger ya es adecuada y debe conservarse. Solo necesita jerarquía azul/dorado y mejores reglas.

### NOV-06 · shell/footer genérico

Footer y Volver arriba no mantienen la firma que ya se cerró en la ficha principal de Samuel.

### NOV-07 · lazy media en evidencia visual

Las capturas full-page pueden mostrar grandes reservas de espacio antes de que imágenes lazy terminen de decodificarse. El QA específico debe forzar carga/`decode()` de las imágenes documentales antes de capturar para distinguir un problema real de layout de una evidencia incompleta.

## 5. Sistema visual aplicado

### Tokens

- azul `#1d4f96`;
- azul oscuro `#0d2c57`;
- dorado `#b8860b`;
- azul pálido `#eefaff`;
- negro `#050505`;
- neutral `#6f6a64`.

Los tokens se definen en el contexto raíz de Samuel dentro de `noveris.css`, que solo se carga en esta ruta.

### Hero

- apertura Yellowtail/dorada + highlight azul;
- H1 `Noveris` azul con micro-stroke dorado y peso UI fuerte, diferenciándolo de la ficha de libro;
- lead de lectura negro;
- acciones Yellowtail azules sin botón negro;
- cierre doble azul/dorado.

### Secciones

- aperturas de sección Yellowtail/doradas;
- H2 azules;
- transiciones entre secciones mediante doble regla azul/dorado;
- prose mantiene ancho de lectura y serif.

### Mapa y figuras

- rail azul real de `2.5px`;
- marco azul mínimo;
- cierre dorado;
- caption neutral;
- el mapa conserva anchura protagonista y no se convierte en card.

### Focos de conocimiento

El antiguo bento de cards se transforma en un registro editorial:

- artefacto central con superficie azul pálida degradada;
- facciones/ciudad como registros laterales;
- Velo/Barrera como registro de anchura completa;
- hairlines y reglas, sin cajas independientes.

### Canalizadores

Desktop conserva `<table>` y semántica tabular, con tratamiento de archivo.

En `<=760px`:

- la tabla deja de exigir scroll horizontal;
- cada `tr` se presenta como registro grid;
- nombre arriba, imagen/usuario y descripción en una composición legible;
- se añaden etiquetas visuales por pseudo-elemento sin modificar la semántica DOM;
- imágenes conservan presencia mínima verificable.

### Zonas

Las cuatro `id-card` pasan a un registro geográfico 2×2 de reglas abiertas; `<=760px` se convierte en ledger de una columna.

### Glosario

Se conserva la estructura ledger existente:

- término azul a la izquierda;
- definición negra/serif a la derecha;
- reglas azul translúcido;
- cierre dorado;
- `<=640px` apila término/definición.

### FAQ y cierre

- FAQ con regla azul superior, dorada inferior y summaries azules;
- lectura relacionada usa acciones Yellowtail;
- footer/Volver arriba adoptan el patrón azul/dorado de Samuel.

## 6. Responsive contractual

Viewports del QA específico:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800;
- 900×800;
- 768×1024;
- 761×900;
- 760×900;
- 641×900;
- 640×900;
- 390×844;
- 360×800.

Costuras importantes:

- `901/900`: bento documental pasa de dos columnas a una;
- `761/760`: tabla y zonas pasan a registro móvil;
- `641/640`: glosario pasa de ledger lateral a apilado.

## 7. QA

### Visual Chromium

`qa/noveris-design-browser.mjs` comprueba:

- contexto/canonical/familia;
- ausencia de overflow;
- hero y acciones;
- section openings/H2;
- mapa/rail/marco;
- bento sin card boxed;
- tabla desktop vs registro móvil;
- presencia de imágenes de canalizadores;
- zonas 2→1 columnas;
- 14 términos visibles del glosario y seam 641/640;
- FAQ funcional;
- footer/Volver arriba;
- launcher oculto `<=1300` manteniendo `Asistente` del header;
- carga/decodificación de imágenes antes de las capturas;
- captura full-page de todos los viewports.

Está integrado en `Sitewide Reflow QA`.

### Cross-engine

`qa/noveris-design-cross-engine.mjs` valida identidad, mapa, bento, tabla móvil, glosario y overflow en Chromium/Firefox/WebKit. Se ejecuta desde el smoke de diseño Samuel existente.

### Autoridad funcional

`qa/samuel-ecosystem-browser.mjs` continúa siendo autoridad para:

- contenido/schema/glosario;
- imágenes y alt/dimensiones;
- anchors;
- 320→1728 y landscape;
- stress de contenido;
- 200% texto;
- text spacing;
- CLS.

## 8. Revisión real/humana pendiente antes del merge

Heredar `docs/design-system/REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` y comprobar:

- iPhone/Safari real: tabla móvil, mapa, scroll largo, FAQ, safe areas y rotación;
- Android/Chrome real;
- tablet real si es posible;
- Safari/Edge desktop en la revisión global;
- legibilidad de los registros de canalizadores a DPI real;
- que el mapa no monopolice la pantalla ni pierda detalle útil;
- que el largo glosario mantenga ritmo y escaneabilidad;
- hard reload/cache/back-forward cache;
- hover/focus de acciones, FAQ, footer y Volver arriba.

La incidencia de tinta de HOME en iPhone pertenece a #163 y no debe mezclarse en esta PR.

## 9. Definition of Done

- [x] rama apilada sobre #266 y ligada a #163;
- [x] baseline 1440/390 recuperado e inspeccionado;
- [x] dirección documental definida;
- [x] primera capa visual implementada en `assets/noveris.css`;
- [x] QA Chromium específico añadido;
- [x] QA cross-engine específico añadido;
- [ ] primera ejecución CI revisada;
- [ ] defectos objetivos encontrados en navegador corregidos;
- [ ] capturas finales de todos los seams revisadas;
- [ ] gates finales verdes;
- [ ] revisión física/humana antes del merge.

No declarar esta PR técnicamente cerrada hasta completar los checks automatizados y la inspección final de capturas.