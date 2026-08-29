# Diseño — `/fragmento/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Cadena de diseño:

1. #163 — `Diseño - HOME · unificación visual azul/dorado`.
2. #174 — `DISEÑO - Libros · unificación visual del hub de Obras`.
3. #205 — `DISEÑO - Manecillas · unificación visual de la ficha principal`.
4. #264 — `DISEÑO - Fragmentos · unificación visual de la página de lectura`.
5. #265 — `Diseño - Samuel entre mundos · unificación visual de la ficha principal`.
6. Esta rama — `/fragmento/`, capítulo 1 gratuito de Samuel.

La rama `design/samuel-fragmento-visual-unification-2026-08-29` nace exactamente de `5c5190d5c135710cbd33169ba7f11ee8aaf36f40`, HEAD documental de cierre de #265. El runtime certificado inmediatamente anterior de #265 es `1b2c996461dae68d82b01ab2997a12723c37f4af`.

No mergear fuera de orden. Esta PR debe permanecer apilada sobre `design/samuel-visual-unification-2026-08-29` hasta que las bases anteriores se integren.

## 2. Objetivo

`/fragmento/` no es una ficha de libro ni un artículo de Cuaderno: es una superficie de lectura de ficción larga. Debe conservar la arquitectura funcional de Article que ya resuelve medida de lectura, responsive, progreso, newsletter y shell, pero adquirir continuidad inequívoca con Samuel mediante materiales azul/negro/dorado.

Principios:

- prosa serif negra como protagonista;
- ancho de lectura actual preservado;
- azul `#1d4f96` para orientación/jerarquía;
- dorado `#b8860b` solo como acento editorial y aperturas grandes;
- Yellowtail para aperturas y acciones, no para el texto literario;
- rail azul real de `2.5px` acompañando figura + capítulo;
- dobles reglas azul/dorado para transiciones;
- azul pálido `#eefaff` solo en bloques prácticos/conversión;
- sin cards dentro del capítulo;
- CTA persistente compacto: nunca debe tapar varias líneas de lectura en móvil.

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
- no-JS/cross-engine/reflow cubiertos por los QA existentes.

`qa/samuel-book-fragment-browser.mjs` y `qa/samuel-ecosystem-browser.mjs` siguen siendo autoridad funcional.

## 4. Auditoría visual de baseline

Evidencia recuperada del artefacto final de #265:

- `fragmento-1440x1000.png` — 1440 × 11777;
- `fragmento-390x900.png` — 390 × 14976.

Defectos objetivos de coherencia/superposición observados:

### FRG-01 · identidad genérica de Article

Hero, figura y capítulo se percibían como un artículo genérico del Cuaderno. No había rail de lectura ni transiciones azul/dorado que lo conectasen visualmente con la ficha Samuel.

### FRG-02 · sticky CTA negro

`#sticky-cta` usaba `--surface-inverse` negro y botones invertidos. Era el mayor material legacy de la página y rompía el sistema ya cerrado en #265.

En 390 px aparecía como una franja de gran altura justo al empezar la lectura, ocupando varias líneas útiles y compitiendo con el capítulo.

### FRG-03 · launcher flotante sobre lectura

La captura móvil mostraba el launcher del asistente solapando el área de figura/caption. La misma decisión ya cerrada en #265 se replica: ocultar solo el launcher flotante `<=1300px`, manteniendo `Asistente` accesible en el header.

### FRG-04 · CTA final genérica

El bloque `¿Qué pasa después?` era una caja blanca con borde neutral y botón negro. Se convierte en un bloque práctico azul pálido con dobles reglas y acciones manuscritas, sin alterar copy ni URLs.

### FRG-05 · divisores y continuidad

El separador interno del capítulo, Article End y newsletter conservaban reglas neutras genéricas. Se trasladan a dobles reglas azul/dorado manteniendo la jerarquía y el flujo.

## 5. Implementación visual

### Apertura

- eyebrow Yellowtail/dorado, tamaño editorial grande y highlight azul;
- H1 azul con stroke dorado fino;
- deck negro;
- metadata neutral con rail azul de `2.5px`;
- cierre del hero con doble regla azul/dorado.

### Lectura

- `article-layout` deja de reservar columnas vacías que no tienen TOC en esta ruta;
- `article-prose` conserva `--reading-max`, centrado;
- rail azul `2.5px` acompaña figura + capítulo;
- figura recibe borde azul/acento dorado mínimo;
- título repetido del capítulo permanece pequeño/UI, pero azul y con regla azul: orienta sin competir con el H1;
- párrafos, sangrías, diálogos y aside literario conservan la tipografía/ritmo de lectura;
- divider interno pasa a doble regla azul/dorado.

### Conversión final

- bloque azul pálido, sin card redondeada;
- apertura Yellowtail/dorada;
- H2 azul;
- acciones Amazon/ficha/guía pasan a Yellowtail azul, sin botón negro;
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
- en móvil las dos acciones permanecen en una fila compacta cuando el ancho lo permite;
- la lógica de visibilidad/dismiss no cambia.

### Reading progress

Se conserva el elemento funcional existente y solo se cambia su material a gradiente azul→dorado.

## 6. Responsive que debe certificarse

Viewports de diseño:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800;
- 900×800;
- 768×1024;
- 620×900;
- 390×844;
- 360×800.

Comprobar especialmente:

- hero metadata desktop vs apilado `<=900`;
- rail continuo figura→fin del capítulo;
- medida de prosa estable;
- sticky CTA compacto y sin overflow a 390/360;
- launcher ausente `<=1300` y presente en desktop ancho si carga el widget;
- CTA final y newsletter sin compresión/columnas implícitas;
- footer sin superposición con sticky;
- texto 200% y text spacing por QA existente.

## 7. Rendimiento

Baseline conocido del Lighthouse focalizado de #265 para `/fragmento/`:

- warning no bloqueante de LCP: mediana observada `3642.2835ms` con warning `<=3500ms`;
- workflow general `success`.

Esta PR no debe empeorar de forma material ese dato. No se añadirán nuevas imágenes, JS ni fuentes; el cambio se limita a CSS y QA/documentación salvo que aparezca un defecto funcional reproducible.

## 8. QA previsto

Añadir `qa/samuel-fragmento-design-browser.mjs` para validar:

- token/colores de página;
- eyebrow/H1/meta;
- rail `2.5px`;
- figura azul/dorada;
- capítulo y divider;
- CTA final;
- Article End/newsletter;
- reading-progress;
- sticky CTA visible y compacto tras activarlo;
- dismiss del sticky;
- launcher oculto `<=1300`;
- overflow en todos los viewports;
- capturas full-page.

Añadir smoke cross-engine específico si los contratos existentes no cubren suficientemente los materiales nuevos.

Los QA funcionales de Samuel/fragmento permanecen activos y no se sustituyen.

## 9. Revisión humana pendiente antes del merge

Tras cerrar QA automático, Claude/mantenedor debe comprobar:

- ritmo real de lectura prolongada;
- percepción del rail durante scroll largo;
- Yellowtail/stroke a distintos DPI;
- sticky CTA durante scroll real y al cerrarlo;
- teclado/focus en CTA/newsletter;
- hard reload/cache/staging;
- que la conversión no resulte intrusiva frente al texto.

Una preferencia estética nueva no reabre automáticamente la PR; un defecto reproducible sí.

## 10. Definition of Done

- [x] Rama apilada exactamente sobre #265.
- [x] Baseline desktop/móvil recuperado e inspeccionado.
- [x] Primera capa visual específica aplicada en `assets/fragmento.css`.
- [ ] QA visual dedicado añadido.
- [ ] Capturas finales revisadas en todos los breakpoints.
- [ ] Defectos objetivos encontrados corregidos.
- [ ] Gates verdes en HEAD definitivo.
- [ ] Revisión humana final antes del merge.

No declarar `/fragmento/` cerrada técnicamente hasta completar las casillas automáticas.