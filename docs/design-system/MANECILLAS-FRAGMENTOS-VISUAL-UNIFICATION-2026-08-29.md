# Diseño — `/las-manecillas-del-recuerdo/fragmentos/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Cadena de diseño:

1. PR #163 — `Diseño - HOME · unificación visual azul/dorado`.
2. PR #174 — `Diseño - Libros · unificación visual del hub de Obras`.
3. PR #205 — `Diseño - Manecillas · unificación visual de la ficha principal`.
4. Esta PR — `/las-manecillas-del-recuerdo/fragmentos/`.

La rama nace exactamente de `1f57df3e94256f53d26faac44ab8c473600bec2e`, HEAD documental cerrado de #205. No mergear antes de las PR previas. Tras fusionar cada base, retargetear manteniendo limpio el diff propio.

## 2. Objetivo

Fragmentos es una página de lectura. Debe pertenecer visualmente al mismo sistema azul/negro/dorado de HOME, Libros y Manecillas, pero sin convertir el texto literario en una sucesión de cards ni en una landing comercial.

Contrato:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- azul de header `#0a4d9f`;
- azul profundo de interacción `#0d2c57`;
- serif/negro para lectura extensa;
- grises neutros para registros, capítulos y metadatos;
- Yellowtail para aperturas y acciones;
- corner brackets en la portada;
- rails reales de `2.5px`;
- separadores azul/dorado;
- azul pálido solo en estados activos/bloques prácticos.

## 3. Contenido y comportamiento que no se toca

Preservar literalmente:

- title, description, canonical, OG/Twitter y JSON-LD;
- los tres fragmentos y su orden;
- `data-nosnippet` de los textos;
- anchors `#fragmento-1`, `#fragmento-2`, `#fragmento-3`, `#cta-final`;
- breadcrumbs y navegación contextual;
- destinos de todos los enlaces;
- `v1-fragments.js` y su lógica de `data-current`, hashchange e IntersectionObserver;
- `body[data-reading-progress]`;
- funnel/analytics existentes;
- portada y art direction.

## 4. Scope técnico

La ficha principal y Fragmentos comparten `data-editorial-context="manecillas"`, `v1-book.css` y clases de libro. La separación deliberada es:

- ficha principal #205: `body:not([data-reading-progress])`;
- Fragmentos: `body[data-reading-progress]`.

`v1-fragments.css` se usa como capa propia de Fragmentos y todas las reglas nuevas se restringen a `html.v1[data-editorial-context="manecillas"] body[data-reading-progress]`.

## 5. Inventario visual

### FRAG-01 · shell/contexto

Context nav, header, Explorar, footer y Volver arriba deben seguir el contrato ya cerrado en #205, sin teal/beige legacy en hover/focus.

### FRAG-02 · hero de lectura

Se mantiene portada + copy, sin inventar ledger. Adaptación:

- portada con brackets;
- apertura Yellowtail/dorada + highlight azul;
- H1 azul/dorado;
- lead serif negro;
- CTAs manuscritos azules;
- rail azul junto al copy en desktop.

### FRAG-03 · introducción

`Tres escenas, tres momentos distintos / Sin resumen ni destripes` funciona como apertura editorial: doble regla, label dorado y H2 azul. No card.

### FRAG-04 · índice de lectura

Debe ser una navegación legible, no tabla beige:

- reglas azul/dorado;
- `Registro I/II/III` neutro;
- título serif negro;
- estado activo azul pálido + rail azul real de 2.5px;
- hover/focus azul profundo + acento dorado;
- mantener `data-current` gestionado por JS.

### FRAG-05 · fragmentos

Cada sección conserva prosa serif/negro. Encabezados usan label Yellowtail/dorado, H2 azul/dorado y metadata neutral. La prosa recibe un rail azul 2.5px sin caja pesada.

### FRAG-06 · paginadores

Direcciones (`Anterior/Siguiente/Continuar`) permanecen UI neutra. Destinos pasan a Yellowtail azul. Separador superior azul/dorado. En móvil pasan a una columna sin alterar anchors.

### FRAG-07 · cita intermedia

`Este reloj ha vivido más vidas que yo.` es una pausa editorial: rail azul + acento dorado, sin card.

### FRAG-08 · CTA final

`La novela completa` es un bloque práctico/convertidor: azul pálido, borde azul + acento dorado, encabezado azul/dorado y acción Yellowtail.

### FRAG-09 · asistente

En `<=1300px` se oculta solo el launcher flotante duplicado. El acceso `Asistente` del header permanece.

## 6. Responsive

Costuras a validar:

- 1440 / 1280;
- 1024 / 900;
- 899 / 768;
- 767 / 640;
- 390 / 360.

Contrato:

- `>=900`: hero desktop con rail en copy;
- `768–899`: portada izquierda + copy derecha;
- `<=767`: apilado deliberado, rail exterior, índice/paginadores a una columna;
- `<=639`: context nav deja de ser sticky.

## 7. QA requerido

Crear un QA de navegador específico que pruebe, como mínimo:

- variables de Fragmentos presentes;
- portada cargada/visible + brackets;
- Yellowtail/dorado y H1 azul;
- índice de tres elementos;
- activación real de `data-current` al navegar/hash/scroll;
- rail activo de 2.5px;
- tres secciones de excerpt;
- prosa con rail 2.5px;
- paginadores y geometría móvil;
- CTA final;
- footer/launcher;
- hover/focus de shell/acciones;
- ausencia de overflow;
- screenshots full-page en seams.

Añadir smoke cross-engine específico si el general no comprueba estos invariantes en Chromium/Firefox/WebKit.

## 8. Fuera de alcance

- reescribir los fragmentos;
- cambiar SEO/structured data;
- cambiar `v1-fragments.js` salvo que aparezca un bug funcional objetivo;
- rediseñar Samuel u otras fichas;
- cambios globales de shell no necesarios para Fragmentos.

## 9. Revisión manual pendiente para Claude/mantenedor

Antes del merge revisar en navegador real:

- 1440/1280, 1024/900, 899/768, 767, 390/360;
- ritmo de lectura real y ancho de columna;
- que los rails no distraigan de la prosa;
- estado activo del índice durante scroll lento/rápido;
- hash directo a los tres fragmentos;
- navegación por teclado del índice y paginadores;
- Yellowtail/stroke dorado en distintos DPI;
- zoom/text-spacing;
- endpoint/funnel real si staging lo permite;
- ausencia de legacy teal/beige en estados interactivos.

## 10. Definition of Done

- [x] Rama apilada sobre #205.
- [x] Primera implementación visual page-scoped.
- [x] Contenido y JS de lectura preservados.
- [ ] QA específico con capturas y seams.
- [ ] Cross-engine específico si es necesario.
- [ ] CI verde sobre HEAD definitivo.
- [ ] Revisión humana final antes del merge.
