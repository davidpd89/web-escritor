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

La rama `design/samuel-fragmento-visual-unification-2026-08-29` nace del HEAD documental de cierre de #265 y permanece apilada sobre `design/samuel-visual-unification-2026-08-29` hasta que las bases anteriores se integren.

No mergear fuera de orden. Tras integrar cada base, retargetear la siguiente PR a `main` y verificar que su diff propio continúe limpio.

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
- CTA persistente compacto: nunca debe tapar varias líneas de lectura en móvil;
- elementos `fixed` compatibles con las safe areas de iPhone cuando `viewport-fit=cover` está activo.

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

- `fragmento-1440x1000.png` — desktop;
- `fragmento-390x900.png` — móvil.

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

### FRG-06 · tokens del sticky fuera de scope

La primera implementación declaró `--frag-*` dentro de `.article-page`, pero `#sticky-cta` vive fuera de `<main>`. El QA cross-engine detectó que el sticky seguía resolviendo el material legacy negro. Los tokens se elevaron a `html[data-editorial-context="samuel"]`; el test no se relajó.

### FRG-07 · safe area inferior de iPhone

`/fragmento/` ya usa `viewport-fit=cover`, pero el CTA `position:fixed` terminaba en `bottom:0` sin reservar `env(safe-area-inset-bottom)`. Se mantiene la misma altura en navegadores con inset `0` y se suma únicamente la safe area cuando iOS la expone.

La corrección automática no sustituye la comprobación en un iPhone físico.

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
- la lógica de visibilidad/dismiss no cambia;
- sus tokens se resuelven desde el contexto raíz de la página;
- padding inferior suma `env(safe-area-inset-bottom)` para iPhone con indicador Home.

### Reading progress

Se conserva el elemento funcional existente y solo se cambia su material a gradiente azul→dorado.

## 6. Responsive certificado automáticamente

Viewports del QA específico:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800;
- 900×800;
- 768×1024;
- 620×900;
- 390×844;
- 360×800.

Se comprueba:

- hero metadata desktop vs apilado `<=900`;
- rail continuo figura→fin del capítulo;
- medida de prosa estable;
- sticky CTA compacto y sin overflow a 390/360;
- launcher ausente `<=1300` y ausencia de colisión con sticky;
- CTA final y newsletter sin compresión/columnas implícitas;
- footer sin superposición con sticky;
- sticky visible tras el scroll esperado y dismiss persistente por `sessionStorage`;
- texto 200% y text spacing por QA funcional existente.

## 7. Rendimiento

Baseline conocido del Lighthouse focalizado de #265 para `/fragmento/`:

- warning no bloqueante de LCP: mediana observada `3642.2835ms` con warning `<=3500ms`;
- workflow general `success`.

Esta PR no añade imágenes, JS ni fuentes. La implementación se mantiene en CSS, QA y documentación. Lighthouse general y el gate focalizado de Samuel deben permanecer verdes en el HEAD definitivo.

## 8. QA implementado

### Chromium / capturas

`qa/samuel-fragmento-design-browser.mjs` valida:

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
- launcher y colisiones;
- overflow en todos los viewports;
- capturas full-page y capturas específicas del sticky.

El script está integrado en `Sitewide Reflow QA`.

### Cross-engine

`qa/samuel-fragmento-design-cross-engine.mjs` se ejecuta dentro del smoke de diseño de Samuel y comprueba la misma identidad básica en Chromium, Firefox y WebKit, incluido sticky y dismiss.

### Autoridad funcional

Los QA previos de Samuel/fragmento permanecen activos y no se sustituyen. El gate `Samuel ecosystem browser QA` debe pasar completo.

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
- que el sticky no tape contenido ni controles de Safari.

### Otros dispositivos

- Android/Chrome real cuando esté disponible;
- tablet real si es posible;
- desktop Chrome/Firefox y Safari/Edge en la revisión global de publicación.

La incidencia de vídeo/tinta de HOME reproducida en iPhone pertenece a #163 y no debe corregirse mezclándola en esta PR.

## 10. Revisión humana perceptiva

Además del hardware real, revisar:

- ritmo de lectura prolongada;
- percepción del rail durante scroll largo;
- Yellowtail/stroke a distintos DPI;
- hard reload/cache/staging;
- que la conversión no resulte intrusiva frente al texto.

Una preferencia estética nueva no reabre automáticamente la PR; un defecto reproducible sí.

## 11. Definition of Done

- [x] Rama apilada exactamente sobre #265.
- [x] Baseline desktop/móvil recuperado e inspeccionado.
- [x] Capa visual específica aplicada en `assets/fragmento.css`.
- [x] QA visual dedicado añadido.
- [x] QA cross-engine específico añadido.
- [x] Capturas automatizadas revisadas en todos los breakpoints antes del ajuste de safe-area; el HEAD final debe volver a generarlas.
- [x] Defectos objetivos detectados en implementación inicial corregidos, incluidos tokens del sticky y safe-area.
- [ ] Gates verdes en HEAD definitivo posterior al ajuste de safe-area/documentación.
- [ ] Revisión iPhone/Safari en hardware real.
- [ ] Revisión humana final antes del merge.

`/fragmento/` puede declararse cerrada técnicamente cuando los gates del HEAD definitivo estén verdes. No declararla lista para merge hasta completar la revisión real/humana pendiente.