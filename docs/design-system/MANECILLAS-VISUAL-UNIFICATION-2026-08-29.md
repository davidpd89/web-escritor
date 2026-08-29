# Diseño — `/las-manecillas-del-recuerdo/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Cadena de diseño:

1. PR #163 — `Diseño - HOME · unificación visual azul/dorado`.
2. PR #174 — `Diseño - Libros · unificación visual del hub de Obras`.
3. PR #205 — ficha principal de `Las manecillas del recuerdo`.

La rama de #205 nace del HEAD cerrado de #174: `18e7877f7d0522a9b4b3dd384c36ad2eca6f812c`. No debe mergearse antes que #163 y #174. Tras fusionar las bases, retargetear sucesivamente a `main` verificando que el diff propio siga limitado a esta página y su QA.

## 2. Alcance y contrato visual

Página: `/las-manecillas-del-recuerdo/`.

Debe sentirse como ficha editorial de una obra, no como otra HOME ni como landing SaaS. Reutiliza el sistema aprobado:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- azul de controles del header `#0a4d9f`;
- azul profundo de interacción `#0d2c57`;
- negro para lectura principal;
- grises/neutros para metadatos y rótulos internos;
- Yellowtail para aperturas y acciones;
- `corner-bracket-blue-gold.svg` para portada;
- rails reales de `2.5px`;
- separadores azul/dorado;
- blanco como superficie principal y azul muy pálido solo para énfasis práctico/secundario.

## 3. Contenido que se preserva

Esta PR es visual/UX. Se mantienen:

- title, description, canonical, OG/Twitter y JSON-LD;
- ISBN `979-8-90514-935-1`, 272 páginas, Monza Ediciones, PVP 16 €, fecha 3 de septiembre de 2026;
- orden y copy de sinopsis, tres puertas, dedicatoria, muestra, texto de cubierta, disponibilidad y newsletter;
- destinos de enlaces/CTA;
- ausencia actual de un destino comercial propio verificado;
- navegación contextual `Manecillas`;
- formulario y comportamiento funcional de newsletter/compartir;
- portada y art direction existentes.

El workflow `Content parity — Libros + Manecillas` debe permanecer verde.

## 4. Scope técnico: ficha principal ≠ Fragmentos

`/las-manecillas-del-recuerdo/fragmentos/` comparte:

- `data-editorial-context="manecillas"`;
- `v1-book.css`;
- clases como `.book-page--manecillas`, `.book-hero` y `.book-cover`.

Por tanto, contexto o clase por sí solos **no aíslan la ficha principal**.

La página de Fragmentos lleva `body[data-reading-progress]`; la ficha principal no. La V8 exige:

`html.v1[data-editorial-context="manecillas"] body:not([data-reading-progress])`

Esto impide que #205 rediseñe Fragmentos antes de su propia PR.

`qa/manecillas-scope-isolation.mjs` valida en 1280 y 390 px que Fragmentos no reciba `--man-blue` ni los corner brackets de #205. `qa/manecillas-cross-engine.mjs` repite este aislamiento en Chromium, Firefox y WebKit.

## 5. Implementación visual cerrada

### MAN-01 · barra contextual

Blanco + azul; activo azul pálido con acento dorado. En móvil estrecho deja de ser sticky para evitar una banda multilínea permanente.

### MAN-02 · hero

Se conserva portada + copy + ledger. Cambios:

- portada con corner brackets;
- apertura Yellowtail/dorada + highlight azul;
- H1 azul con contorno dorado fino;
- autor/fecha neutros;
- lead serif negro;
- CTAs Yellowtail azules;
- ledger con claves neutras, valores negros y reglas azul/dorado;
- rail azul real en la costura de desktop;
- rail exterior al apilarse.

### MAN-03 · transición hero → contenido

`book-seam` pasa a doble regla azul/dorado con diamante centrado.

### MAN-04 · jerarquía de secciones

`La novela`, `Tres puertas`, `Dedicatoria`, `Muestra de lectura`, `Texto de cubierta`, `Disponibilidad` y `Novedades` usan la nueva jerarquía. Metadatos internos (`Editorial`, `Género`, `Páginas`, `ISBN`, numeraciones...) permanecen neutros.

### MAN-05 · lectura

H2 principales entran en azul/dorado; párrafos largos conservan serif/negro. No se fuerza sans-serif sobre lectura narrativa.

### MAN-06 · cita marginal

Fondo azul pálido, acento dorado inferior y rail azul. El rail no usa `border-left:2.5px`: Chromium cuantizaba el borde fraccional a `2px` en computed layout. Se usa `background-image` con `background-size:2.5px 100%`, igual que el patrón robusto de HOME/Libros.

### MAN-07 · Tres puertas

Tres columnas deliberadas en desktop, una en móvil. No cards SaaS. Separadores azules y rótulos internos neutros.

### MAN-08 · dedicatoria

Pausa editorial con rail azul y reglas; sin caja pesada.

### MAN-09 · muestra y texto editorial

Título azul/dorado, cuerpo serif negro y CTA Yellowtail.

El alias invisible `#muestra` (`.book-anchor-alias`) estaba entrando como primer grid item. Consecuencia observada en capturas reales:

- a 1200 px desplazaba label/prosa una columna;
- a 1199/900 px podía dejar el título a la derecha y devolver la prosa a la izquierda en otra fila.

Se mantiene el ancla pero se saca del grid con `position:absolute`. El QA valida tanto esa propiedad como la geometría label↔prosa a ambos lados de 900/899.

### MAN-10 · disponibilidad

Bloque práctico azul muy pálido, borde azul y acento dorado. Se conserva literalmente el estado comercial actual: no inventar Amazon/tienda mientras no exista destino propio verificado.

### MAN-11 · newsletter

Formulario intacto; superficie/bordes/submit y estados de interacción pasan al sistema azul/dorado.

### MAN-12 · shell

Header, Explorar, footer y Volver arriba siguen #163/#174.

Se cerraron además:

- hover/focus del header al azul de marca;
- drawer Explorar con borde/título/índices azules;
- toggle de subopciones azul y hover azul/blanco;
- rail de subopciones dorado;
- formulario de Explorar azul/dorado;
- footer y sociales azul/dorado;
- back-to-top azul con aro dorado.

### MAN-13 · launcher flotante del asistente

Las capturas muestran que en una ficha de lectura el launcher fijo puede pasar sobre copy a anchuras de portátil/tablet/móvil. Igual que #174:

- en `<=1300px` se oculta solo `.assistant-widget__launcher`;
- el widget sigue montado;
- `Asistente` permanece en el header y abre el mismo panel;
- en desktop >1300 el launcher sigue disponible.

El QA espera explícitamente ese contrato.

## 6. Responsive validado por contrato

`qa/manecillas-design-browser.mjs` ejecuta:

- 1440×1000;
- 1200×850;
- 1199×850;
- 1024×768;
- 900×800;
- 899×800;
- 768×1024;
- 767×900;
- 390×844;
- 360×800.

Se prueban expresamente las costuras `1200/1199`, `900/899` y `768/767`. El shell global ya cambia el footer a 2 columnas en `<=767` y a 1 columna en `<389`; no duplicar esa lógica localmente.

## 7. QA automático específico

### Chromium / geometría y capturas

`qa/manecillas-design-browser.mjs` valida:

- portada visible y brackets;
- apertura Yellowtail/dorada y H1 azul;
- CTAs y metadatos;
- seam azul/dorado;
- rail de cita `2.5px` efectivo;
- tres puertas;
- geometría de `#muestra`;
- disponibilidad y newsletter;
- context nav móvil;
- footer;
- launcher `<=1300`;
- hover de header, CTA, newsletter, social y toggle de Explorar;
- ausencia de overflow;
- capturas full-page de todos los viewports.

### Aislamiento

`qa/manecillas-scope-isolation.mjs` garantiza que Fragmentos queda sin la V8 de esta PR.

### Cross-engine

`qa/manecillas-cross-engine.mjs` ejecuta Chromium, Firefox y WebKit y comprueba:

- contexto correcto;
- H1/apertura;
- brackets;
- rail de cita;
- reflow móvil sin overflow;
- alias fuera del grid;
- aislamiento de Fragmentos.

`.github/workflows/cross-engine-smoke.yml` ejecuta este smoke específico después del smoke general y del de Libros.

### Gates generales

Deben quedar verdes sobre el HEAD definitivo:

- Lighthouse CI;
- Accessibility baseline (Pa11y);
- Sitewide Reflow QA;
- Cross-engine smoke;
- CSP public shell QA;
- Runtime scoping QA;
- Analytics taxonomy QA;
- Check content indexes;
- Tool engine tests;
- Content parity — Libros + Manecillas.

## 8. Fuera de alcance

- `/las-manecillas-del-recuerdo/fragmentos/`: propia PR de diseño;
- `/libros/samuel-entre-mundos/`: propia PR;
- reescritura editorial/SEO/datos comerciales;
- cambios globales no necesarios para cerrar esta ficha.

## 9. Revisión manual que debe hacer Claude/mantenedor antes del merge

El QA automatizado no sustituye una inspección humana final. Revisar en navegador real:

- 1440×1000 y 1280×800;
- 1200/1199 y 900/899;
- 768/767;
- 390×844 y 360×800;
- legibilidad real de Yellowtail y del stroke dorado en distintos DPI;
- conexión visual de rails/separadores;
- transición `Muestra de lectura` tras sacar `#muestra` del grid;
- hover/focus con teclado en header, Explorar, CTAs, formulario, footer y back-to-top;
- que ocultar el launcher `<=1300` no reduzca discoverability porque `Asistente` sigue visible en el header;
- newsletter con endpoint/configuración real de staging si se dispone;
- ausencia de beige/teal efectivo en estados interactivos;
- ausencia de clipping/overflow con zoom y text spacing.

Si aparece una preferencia estética nueva, tratarla como decisión separada. Si aparece un defecto geométrico, de accesibilidad o de responsive, corregirlo antes del merge.

## 10. Definition of Done

- [x] Diff propio apilado sobre #174.
- [x] Hero, portada, secciones, temas, dedicatoria, disponibilidad y newsletter adaptados.
- [x] Contenido/SEO/structured data preservados y cubiertos por parity.
- [x] Fragmentos aislado y protegido por QA específico.
- [x] QA de Manecillas con capturas en breakpoints críticos.
- [x] Estados interactivos principales incorporados al QA.
- [x] Smoke de diseño específico en Chromium/Firefox/WebKit añadido.
- [ ] Todos los gates verdes sobre el HEAD definitivo de #205.
- [ ] Revisión humana final de Claude/mantenedor antes del merge.

No marcar la PR como cerrada técnicamente hasta que el primer punto pendiente quede verde. Puede permanecer Draft incluso después, para la revisión humana/apilado de PRs.
