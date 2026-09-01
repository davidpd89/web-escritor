# Club Samuel · guía imprimible — contrato de unificación visual

Fecha: 2026-08-31
Estado: contrato preparado; implementación pendiente
Cadena: continúa después de `DISEÑO - Lectores beta` (#285)

## Superficie

- `/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`

Esta ruta quedó explícitamente fuera de #268 Club Samuel. Es una pieza autónoma, autocontenida y orientada a impresión; no debe heredar a ciegas el tratamiento de la guía web.

## Baseline verificado

La página actual:

- es `noindex,nofollow`;
- tiene CSS inline propio;
- usa `theme-color #F4EFE7`;
- define una paleta propia de papel/azul/terracota (`#F4EFE7`, `#617887`, `#4C6474`, `#A8664A`, `#CFC7BC`);
- incluye cabecera, bloques de sesión, preguntas, notas, contacto y copyright;
- dispone de botón de impresión con `window.print()`;
- contiene reglas `@media print` orientadas a A4 y oculta controles no imprimibles.

No es un defecto que una pieza impresa tenga identidad algo distinta. La tarea es reconciliarla con Samuel y con el sistema azul/dorado sin degradar su función editorial/impresa.

## Dirección visual

Tratarla como **cuadernillo editorial imprimible**, no como una página web reducida ni como un formulario.

Prioridades:

1. jerarquía y lectura excelentes tanto en pantalla como en papel A4;
2. continuidad reconocible con Samuel y la web principal;
3. uso contenido de azul/dorado, evitando convertir cada bloque en un recurso decorativo;
4. preguntas, notas y espacios de trabajo con ritmo de cuadernillo;
5. impresión en color y en escala de grises comprensible;
6. evitar fondos que consuman tinta sin aportar estructura.

## Preservar estrictamente

- `noindex,nofollow`;
- texto, preguntas, datos del libro, contacto y copyright;
- orden y numeración;
- semántica de headings y listas;
- acción `window.print()` y su accesibilidad;
- layout de impresión A4;
- page breaks razonables;
- contenido legible sin JS salvo el acto de invocar imprimir;
- URLs/enlaces existentes.

No actualizar hechos ni contenido dentro de una PR visual.

## Implementación esperada

Preferir mantener el aislamiento de esta pieza. Si se extrae el CSS inline a un owner propio por mantenibilidad, hacerlo únicamente si mejora trazabilidad y no altera la impresión. No cargar todo el shell de la web solo para conseguir colores o tipografías.

Revisar especialmente:

- paleta actual terracota/azul y qué elementos realmente necesitan migración;
- contraste AA en pantalla;
- contraste y jerarquía al imprimir en B/N;
- tamaños mínimos y longitud de línea;
- márgenes A4;
- encabezados al comienzo/final de página;
- cortes de bloques/preguntas;
- botón de impresión y foco;
- URLs y textos largos;
- ausencia de overflow horizontal.

## QA requerido

### Pantalla

- 1440×1000;
- 1280×800;
- 1024/768;
- 390 y 360 px;
- zoom 200 %;
- text spacing WCAG;
- teclado/focus;
- no-JS;
- cero overflow.

### Impresión

Validar con Playwright/Chromium `media=print` y, cuando sea viable, WebKit:

- A4 portrait;
- color;
- grayscale/forced-color-compatible reading where practical;
- botón web ausente en impresión;
- ningún contenido crítico oculto;
- preguntas y bloques sin cortes absurdos;
- márgenes seguros y ausencia de clipping;
- número de páginas estable o cualquier variación documentada.

Generar evidencia de al menos portada/primera página, una página intermedia con preguntas y página final.

## Aislamiento

La PR no debe alterar:

- `/clubes-de-lectura/samuel-entre-mundos/` (#268);
- `/clubes-de-lectura/preparar-sesion/` (familia herramientas);
- ficha `/samuel-entre-mundos/`;
- otros CSS de impresión globales.

## Cierre

No marcar como técnicamente cerrada hasta tener contrato visual + impresión + reflow verdes. Mantener Draft y sin merge. La comprobación final en dispositivo/impresora real queda bajo `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.