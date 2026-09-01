# Legal — contrato de unificación visual

Fecha: 2026-08-31
Estado: contrato preparado; implementación pendiente
Cadena: continúa después de `DISEÑO - Club Samuel · guía imprimible` (#286)

## Superficies

- `/aviso-legal.html`
- `/privacidad.html`

Ambas rutas son `noindex, follow` y comparten `assets/v1-legal.css`. Deben cerrarse como una sola familia documental.

## Baseline verificado

Las dos páginas cargan los tokens/base/shell y el owner `v1-legal.css`. La hoja está concebida específicamente como familia legal y evita decoración global innecesaria. No se ha detectado una fuga cromática legacy equivalente a Asistente/Offline.

## Dirección visual

Documento legal profesional, sobrio y altamente legible. La unificación azul/dorado debe limitarse a orientación, jerarquía, reglas, foco y enlaces; nunca convertir el contenido legal en una landing promocional.

Prioridades:

1. lectura rápida mediante índice y headings claros;
2. anchura de línea y espaciado cómodos;
3. enlaces/contactos reconocibles;
4. callouts solo cuando la semántica lo justifique;
5. excelente impresión y navegación por anclas;
6. contraste AA/AAA práctico para texto largo cuando sea viable.

## Preservar estrictamente

- texto legal completo y su orden;
- fechas y referencias normativas;
- datos de contacto/responsable;
- condiciones de propiedad intelectual, afiliación y privacidad;
- `noindex, follow`;
- canonical de cada página;
- JSON-LD existente;
- anchors/índice;
- enlaces internos/externos;
- shell y navegación;
- contenido completo sin JS;
- estilos de impresión funcionales.

Una PR de diseño no debe reinterpretar ni reescribir obligaciones legales. Si aparece una posible inexactitud jurídica, documentarla aparte y no modificarla sin revisión específica.

## Implementación esperada

Mantener `v1-legal.css` como owner único de la familia. Evitar crear hojas por página.

Revisar:

- hero/cabecera documental;
- índice de contenidos y estados `:target` si existen;
- rhythm entre secciones;
- listas, definiciones y contactos;
- URLs/emails largos;
- callouts;
- enlaces y focus;
- footer/cierre;
- print.

## QA requerido

Ambas rutas en:

- 1440×1000 y 1280×800;
- 1024/768;
- 901/900 si existe cambio de composición;
- 390, 360 y 320 px;
- zoom 200 %;
- text spacing WCAG;
- teclado/focus y anchors;
- no-JS;
- print;
- cero overflow.

Comprobar además que los textos legales/fechas/canonical/robots no cambian respecto al baseline.

## Aislamiento

No alterar Accesibilidad, `/ai/`, Findability ni artículos de Cuaderno. El owner legal no debe filtrarse al shell general.

## Cierre

Mantener Draft y sin merge. Solo cerrar técnicamente tras QA visual, reflow, accesibilidad e impresión verdes; revisión física final según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.