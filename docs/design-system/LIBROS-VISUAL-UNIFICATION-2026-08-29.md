# Diseño — `/libros/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Esta revisión continúa el sistema cerrado en **PR #163 — `Diseño - HOME · unificación visual azul/dorado`**.

La rama de esta PR nace del HEAD de #163 (`6850d653717beec771c75cd789940c12f0d2a5f8`) y la PR se apila inicialmente sobre esa rama. Así el diff de `/libros/` contiene solo las diferencias propias de esta página, sin repetir los cambios de HOME. Cuando #163 se fusione, esta PR puede retargetearse a `main`.

No mezclar ni revertir decisiones cerradas de #163 durante esta revisión.

## 2. Página elegida y objetivo

Página: `https://davidportodiaz.com/libros/` (`libros/index.html`).

Función: hub editorial de Obras. Debe conservar su carácter de catálogo/ficha editorial, pero hablar el mismo lenguaje visual que la HOME:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- negro para títulos de contenido;
- neutros/grises para metadatos y rótulos internos;
- Yellowtail para rótulos de apertura y enlaces de acción;
- corner brackets azul/dorado en portadas;
- rails de `2.5px` y separadores azul/dorado físicamente conectados;
- composición plana/editorial, sin volver a tarjetas SaaS, sombras arbitrarias ni beige/teal legacy.

No se convierte `/libros/` en una copia literal de HOME: se conserva la alternancia de obras y la densidad informativa propia de un índice editorial.

## 3. Contenido y estructura que NO se reescriben

Esta PR es de diseño. Se preservan:

- title/meta/OG/Twitter/canonical;
- JSON-LD de `CollectionPage`, `ItemList` y `Book`;
- jerarquía editorial Manecillas → Samuel → antología;
- datos de editorial, fechas, páginas, ISBN, formato, PVP y género;
- URLs y destinos de CTA existentes;
- exclusión pública de Jaula documentada en la propia página;
- navegación generada del shell y `section-context` (se estiliza, no se reescribe);
- bloque de recursos para lectores/prensa y sus destinos.

Si se detecta un dato factual o enlace incorrecto que no sea consecuencia de esta PR, se documenta aparte antes de modificarlo.

## 4. Inventario visual previo

### LIBROS-01 · barra contextual todavía beige/legacy

`data-editorial-context="obras"` conserva `--dp-context-hover:#eee8dc`, `--dp-context-active:#e5ddcf` y tinta marrón. Es incompatible con el sistema azul/dorado ya aprobado.

**Cierre:** blanco + azul/dorado; estado activo con azul muy claro y subrayado dorado; hover/focus azul canónico. La barra sigue siendo compacta y horizontal-scroll en pequeño.

### LIBROS-02 · masthead de interior no coincide con HOME

El encabezado usa Instrument Serif, fondo/linea neutra y `coordinate` de UI. Visualmente parece una capa anterior.

**Cierre:** `Obra` pasa al tratamiento Yellowtail dorado con highlight azul; H1 usa el mismo azul con fino contorno dorado que la HOME; lead conserva serif de lectura; separador inferior azul/dorado + diamante.

### LIBROS-03 · portadas sin el marco aprobado

Las tres portadas usan solo `box-shadow`.

**Cierre:** corner brackets azul/dorado idénticos al recurso de HOME (`corner-bracket-blue-gold.svg`). La sombra se reduce a drop-shadow de objeto.

### LIBROS-04 · stages demasiado genéricos y con regla gris

`books-stage` usa `min-height:82svh` + un único `border-bottom` neutro. En pantallas bajas obliga a demasiado vacío y no conecta con el nuevo motivo de rails.

**Cierre:** altura dirigida por contenido, separador azul/dorado con diamante, y rail de `2.5px` en la costura entre portada/copia. La obra invertida conserva su dirección y mueve el rail a la costura opuesta.

En `<=900px`, la composición apilada usa un rail único en el borde izquierdo del stage para evitar que la línea quede separada entre portada y copia.

### LIBROS-05 · jerarquía de rótulos

Los `folio` (`Obra 01`, `Obra 02`, `Antología`) son rótulos internos y permanecen grises/neutros. No convertirlos a dorado.

El dorado manuscrito queda reservado a aperturas de bloque: `Obra` del masthead y `Recursos`.

### LIBROS-06 · CTAs con lenguaje anterior

`primary-action` sigue siendo botón negro/rectangular y `text-action` sigue uppercase-sans subrayado.

**Cierre:** dentro de `books-index`, ambos roles pasan a Yellowtail azul con flecha, sin caja ni subrayado convencional. Los destinos externos usan flecha diagonal. Se conserva la semántica y prioridad del orden de enlaces.

### LIBROS-07 · metadatos

La tabla técnica usa reglas grises.

**Cierre:** regla superior azul y regla inferior dorada; `dt` gris, `dd` negro. No usar fondos de tarjeta.

### LIBROS-08 · Recursos

El bloque final usa `v1-section` + ledger neutral y acciones uppercase.

**Cierre:** transición azul/dorado; `Recursos` dorado/Yellowtail; título azul con contorno dorado; ledger con rail azul y separadores azul/dorado; acciones Yellowtail.

### LIBROS-09 · shell de la página

Header hover, Explorar, footer y Volver arriba deben ser coherentes con la HOME.

**Cierre:** mismos azules de #163 (`#0a4d9f` reservado al header/logo; `#1d4f96` al contenido), footer azul/dorado, back-to-top azul/dorado y estados del drawer sin teal/beige.

## 5. Responsive mínimo

Validar:

- 1440 × 1000
- 1280 × 800
- 1024 × 768
- 901 × 800
- 900 × 800
- 768 × 1024
- 600 × 900
- 390 × 844
- 360 × 800

Especial atención a 900/901 px por el cambio entre rail interior y rail exterior apilado.

## 6. Checks visuales/computed styles

Comprobar en preview/local:

- `section-context` sin beige/marrón efectivo;
- `coordinate` en Yellowtail/dorado;
- H1 azul + stroke dorado;
- corner brackets visibles en las tres portadas;
- rail desktop tocando los separadores sin gap;
- rail móvil continuo por portada + copia;
- ninguna CTA de stages recupera fondo negro, uppercase o border-bottom;
- `folio`, `dt` y metadatos siguen neutros;
- ledger de Recursos mantiene legibilidad con zoom/text spacing;
- hover/focus de header, context nav, Explorar, CTA, footer y back-to-top;
- ningún overflow horizontal a 360/390px.

## 7. Definition of Done

- [ ] La PR contiene solo cambios de `/libros/` y documentación asociada por encima de #163.
- [ ] El contenido/SEO/structured data no se alteran por el rediseño.
- [ ] No queda beige/teal legacy efectivo en navegación o interacciones de esta página.
- [ ] Azul/dorado se usa con la misma semántica que HOME.
- [ ] Rótulos internos permanecen neutros.
- [ ] Portadas usan corner brackets, no marco de fotografía.
- [ ] Rails de 2.5px y section-breaks se conectan.
- [ ] CTAs usan Yellowtail y flechas.
- [ ] Desktop/tablet/mobile pasan reflow y accesibilidad.
- [ ] CI verde.
- [ ] Revisión visual humana de los viewports anteriores antes del merge.

## 8. Fuera de alcance

- rediseñar las fichas `/las-manecillas-del-recuerdo/` y `/libros/samuel-entre-mundos/`;
- rediseñar `/cuaderno/`, `/autor`, `/prensa`, `/herramientas/`;
- cambiar información editorial o SEO salvo regresión introducida por esta PR;
- cambiar destinos comerciales/externos por criterio visual.
