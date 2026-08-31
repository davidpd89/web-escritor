# Diseño — `/libros/samuel-entre-mundos/` · contrato de unificación visual · 2026-08-29

## 1. PR inicial y trazabilidad

PR inicial de toda la cadena: [#163 — DISEÑO - HOME · unificación visual azul/dorado](https://github.com/davidpd89/web-escritor/pull/163).

Cadena:

1. #163 — `DISEÑO - HOME · unificación visual azul/dorado`.
2. #174 — `DISEÑO - Libros · unificación visual del hub de Obras`.
3. #205 — `DISEÑO - Manecillas · unificación visual de la ficha principal`.
4. #264 — `DISEÑO - Fragmentos · unificación visual de la página de lectura`.
5. #265 — `DISEÑO - Samuel entre mundos · unificación visual de la ficha principal`.

La rama `design/samuel-visual-unification-2026-08-29` nace exactamente de `746c75a551babc3811d932aa2392fd2623f81dcb`, HEAD cerrado de #264. No mergear fuera de orden. Después de fusionar las bases, retargetear sucesivamente a `main` y comprobar que el diff propio permanece limitado al diseño/QA de Samuel.

## 2. Objetivo

Samuel ya tiene una identidad estructural propia: umbral, registros, ledgers, stream de reseñas, Noveris y quiz. La unificación no debe convertirla en una copia de Manecillas. El objetivo es conservar esa arquitectura y trasladar sus materiales al lenguaje aprobado:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- azul de controles del header `#0a4d9f`;
- azul profundo de interacción `#0d2c57`;
- negro para lectura;
- neutros para folios, metadatos y citas de fuente;
- Yellowtail para aperturas y acciones editoriales;
- brackets azul/dorado para portada;
- rails reales de `2.5px`;
- separadores azul/dorado;
- azul pálido para estados/práctica/interacción, no como fondo indiscriminado.

## 3. Contenido y funcionalidad preservados

Esta PR es diseño/UX. No modifica:

- title, description, canonical, OG/Twitter ni JSON-LD;
- ISBN `9791387659776`, 422 páginas, Libros Indie, año 2025;
- URLs verificadas de Libros Indie, Amazon España y Casa del Libro;
- rel de afiliación de Amazon;
- reseñas, textos, orden de registros y copy;
- enlaces a `/fragmento/`, Noveris, clubes y guía imprimible;
- lógica de `samuel-quiz.js`;
- lógica/focus trap/history/analytics de `samuel-buy-modal.js`;
- no-JS fallbacks;
- comportamiento de schema/metadata.

Los QA `samuel-book-fragment-browser.mjs` y `samuel-ecosystem-browser.mjs` siguen siendo autoridad funcional y no se sustituyen por el QA visual.

## 4. Implementación visual

### SAM-01 · shell y navegación contextual

Header, context nav, Explorar, footer y Volver arriba usan el contrato azul/dorado ya aprobado. Hover/focus no vuelve a teal.

### SAM-02 · umbral/hero

- se elimina el `min-height` de viewport excesivo;
- portada con brackets y sombra editorial;
- coordinate/caption permanecen neutros;
- eyebrow Yellowtail/dorado + highlight azul;
- H1 azul con stroke dorado fino;
- lead serif/negro;
- facts con regla azul, acento dorado y metadata neutral;
- acciones principales Yellowtail azul;
- rail del umbral pasa de 1px neutral a `2.5px` azul;
- el cierre del hero usa doble regla azul/dorado.

### SAM-03 · responsive del umbral

La ficha es más densa que Fragmentos, por lo que mantiene dos columnas solo por encima de 900 px. En `<=900` se apila deliberadamente y se elimina la vieja línea horizontal dibujada al 48% de altura: un rail exterior vertical azul acompaña portada + copy.

La costura 901/900 queda validada en capturas y QA geométrico: 901 mantiene dos columnas; 900 apila sin columna implícita, salto de 1px, doble rail ni overflow.

### SAM-04 · registros S/01…S/14

Samuel conserva sus registros. Cada cabecera usa:

- folio neutral;
- rail azul de `2.5px` junto al cuerpo de cabecera;
- apertura Yellowtail/dorada;
- H2 azul/dorado;
- cuerpo largo en serif/negro.

Cada sección termina con doble regla azul/dorado, evitando una serie de bordes grises genéricos.

### SAM-05 · sinopsis y ledgers técnicos

La prosa principal recibe rail azul sin convertirse en card. Ledgers conservan estructura, con labels neutrales, valores negros y reglas azul/dorado.

### SAM-06 · para quién / mecánica / rutas

Se mantienen splits y ledgers. No se introducen tarjetas. El seam del split usa azul; acciones de ruta pasan a Yellowtail azul; la información descriptiva conserva serif/neutros según función.

### SAM-07 · reseñas

Se conserva el stream editorial y la atribución. Folios/cites quedan neutrales, citas serif negras, reglas azul/dorado. No se inventan ratings agregados ni destacados nuevos.

### SAM-08 · compra y ejemplar firmado

El ledger de compra conserva los cinco destinos/acciones y sus URLs. Acciones usan Yellowtail azul. El bloque de ejemplar firmado utiliza azul pálido + rail azul + cierre dorado como énfasis práctico.

### SAM-09 · Noveris y FAQ

Noveris mantiene su bloque de transición, con reglas azul/dorado y acción manuscrita. FAQ usa títulos azules, símbolos dorados y respuestas negras.

### SAM-10 · quiz

El quiz sigue siendo un panel interactivo porque esa semántica sí lo requiere. Se elimina el aspecto genérico/SaaS:

- superficie azul pálida;
- borde azul y cierre dorado;
- sin card redondeada;
- progreso azul→dorado;
- pregunta azul;
- opciones blancas con reglas azules;
- hover/focus azul profundo;
- botones de resultado conservan semántica de controles y usan azul/dorado.

No se altera el cálculo, privacidad, navegación por teclado, share ni restart.

### SAM-11 · modal de compra

`samuel-buy-modal.js` queda intacto. `samuel-buy-modal.css` cambia de beige/marrón/dorado legacy a:

- blanco / azul pálido;
- borde azul + acento dorado;
- título azul con la familia UI canónica;
- eyebrow Yellowtail/dorado;
- retailers como filas editoriales, no cards redondeadas;
- CTA manuscrita azul;
- focus visible dorado/azul;
- disclosure afiliada neutral.

Se conserva dialog nativo, focus trap, cierre, restauración de foco, analytics, hash/history y URLs.

### SAM-12 · launcher del asistente

En `<=1300px` se oculta solo el launcher flotante para evitar que pise una página muy larga. `Asistente` sigue disponible en el header.

### SAM-13 · estabilidad geométrica y tipográfica

La auditoría final encontró tres defectos objetivos que no eran decisiones estéticas:

1. La imagen del medallón conservaba la altura presentacional intrínseca cuando su anchura se reducía y podía estirarse en la costura 901/900. Se fuerza `height:auto` solo en la imagen contextual de Samuel.
2. El label dorado del quiz era texto pequeño sobre blanco. Se convierte en una apertura editorial Yellowtail de tamaño grande para que el dorado siga siendo decorativo y cumpla el contrato de contraste.
3. El CLS del hero (`0.20296145`) procedía del fallback de Yellowtail: `Manrope Fallback` usa `size-adjust:128.11%`, ensanchaba el eyebrow y las acciones, creaba líneas/filas extra y colapsaba al cargar Yellowtail. Un fallback local `Samuel Yellowtail Fallback`, con huella horizontal próxima a Yellowtail, reduce el CLS medido a `0.00136518` sin cambiar la tipografía final ni relajar ningún gate. El mismo fallback se aplica a aperturas y acciones manuscritas de Samuel para estabilizar también cargas por deep link.

La instrumentación temporal usada para aislar la causa del CLS se eliminó antes del HEAD candidato; no forma parte del diff final.

## 5. QA añadido

### `qa/samuel-design-browser.mjs`

Viewports finales:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800;
- 900×800;
- 768×1024;
- 620×900;
- 390×844;
- 360×800.

Comprueba:

- token propio Samuel;
- H1/apertura;
- portada + brackets;
- rail hero `2.5px`;
- seam 901/900;
- facts;
- >=14 cabeceras de registro;
- sinopsis/ledgers/fit/rutas/mecánica/reseñas;
- cinco opciones de compra;
- bloque firmado;
- Noveris;
- quiz;
- modal visual + apertura/cierre + restauración de foco;
- shell/footer/launcher;
- hovers;
- overflow;
- capturas full-page.

### `qa/samuel-design-cross-engine.mjs`

Smoke visual específico en Chromium, Firefox y WebKit para hero, brackets, rail, registros, quiz, modal y reflow móvil.

### Evidencia final revisada

Artefacto `sitewide-reflow-qa` del runtime HEAD `1b2c996461dae68d82b01ab2997a12723c37f4af`:

- `samuel-desktop-1440.png`;
- `samuel-desktop-1280.png`;
- `samuel-tablet-1024.png`;
- `samuel-seam-901.png`;
- `samuel-seam-900.png`;
- `samuel-tablet-768.png`;
- `samuel-seam-620.png`;
- `samuel-mobile-390.png`;
- `samuel-mobile-360.png`;
- modal 1280 y 390.

La inspección de esas capturas no detecta defectos objetivos de overflow, columnas implícitas, rails partidos, jerarquía, footer, modal ni seam responsive. `samuel-design-report.json` devuelve `failures: []`; el Sitewide Reflow general cubre 76 rutas × 2 viewports y también devuelve `failures: []`.

### Gates verdes sobre el runtime HEAD `1b2c996461dae68d82b01ab2997a12723c37f4af`

- Samuel ecosystem browser QA #73;
- Lighthouse CI #825;
- Accessibility baseline (Pa11y) #956;
- Sitewide Reflow QA #857;
- Cross-engine smoke #319;
- Global discoverability closure QA #234;
- CSP public shell QA #575;
- Runtime scoping QA #615;
- Analytics taxonomy QA #635;
- Check content indexes #1221;
- Tool engine tests #946.

El Lighthouse focalizado del ecosistema ejecuta 15 auditorías (5 URLs × 3 runs). Su única observación es un warning no bloqueante de LCP en `/fragmento/` (`3642.2835ms` frente al warning `<=3500ms`); no pertenece a la ficha principal de Samuel y el gate concluye `success`.

## 6. Fuera de alcance de esta PR

Las siguientes superficies de Samuel se revisarán como PR propias después de cerrar esta ficha, porque son páginas completas con arquitectura independiente:

- `/fragmento/`;
- `/universo/noveris/`;
- `/clubes-de-lectura/samuel-entre-mundos/`;
- `/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`.

Tampoco se reescriben reseñas, SEO, schema, datos comerciales ni copy.

## 7. Revisión manual pendiente antes del merge

Claude/mantenedor debe hacer una última comprobación en navegador/dispositivo real de lo que no puede certificarse de forma equivalente desde capturas headless:

- percepción del ritmo vertical de los 14 registros;
- legibilidad subjetiva de Yellowtail y del stroke dorado en distintos DPI/subpixel rendering;
- quiz completo con uso real de ratón y teclado;
- modal con Tab/Shift+Tab/Escape/click backdrop/volver del navegador;
- zoom 200% y text-spacing en navegador real, aunque los gates automáticos correspondientes ya pasan;
- percepción de la ocultación del launcher <=1300, confirmando que `Asistente` en header conserva suficiente discoverability;
- hard reload/cache real y staging cuando la cadena se publique.

Si esa revisión revela una preferencia estética nueva, se trata como decisión de diseño separada. Solo un defecto reproducible de geometría, accesibilidad o funcionalidad debe reabrir esta PR.

## 8. Definition of Done

- [x] Rama apilada sobre #264.
- [x] Implementación visual de ficha, quiz y modal.
- [x] QA visual Chromium añadido.
- [x] QA visual cross-engine añadido.
- [x] Workflows conectados.
- [x] Capturas reales de todos los breakpoints revisadas.
- [x] Defectos objetivos encontrados durante la auditoría corregidos.
- [x] Todos los gates verdes en el HEAD de runtime definitivo.
- [ ] Revisión humana final antes del merge.

**Estado: cerrada técnicamente y lista para revisión.** La única casilla pendiente es deliberadamente humana/perceptiva y no representa deuda automática de código.