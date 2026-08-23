# AD — Diseño final · sistema transversal

Fuentes de diseño cruzadas:

- `24 — COMPONENTES GLOBALES MASTER V1`
- `27 — MOTION + TRANSITION CHOREOGRAPHY V1`
- `29 — COMPONENT REDLINES V1`
- `31 — UI COPY + MICROCOPY V1`
- `06 — DESIGN TOKENS V1` como autoridad de tokens a reconciliar

Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Motivo de PR independiente

Las familias #82/#85/#86/#87/#88 deben compartir una gramática única. El repo ya tiene `v1-tokens.css`, `v1-components.css`, `v1-shell.css` y hojas de familia, pero existe drift entre la implementación y las redlines posteriores.

Ejemplos reales en HEAD:

- `--radius-control:4px` y `--radius-input:6px`, mientras doc 29 fija 2px como default V1;
- `--ease-standard:cubic-bezier(.2,.8,.2,1)`, mientras doc 27 fija `cubic-bezier(.2,0,0,1)`;
- los tokens actuales agregan tiempos genéricos, pero doc 27 distingue press/link/node/preview/header/dialog/page/hero con presupuestos concretos.

No se cambian estos valores de forma mecánica: primero se audita qué componentes consumen cada token y se prueba el impacto acumulado.

## AD.1 — Tokens y redlines

Reconciliar de forma única:

- gutters/grid por 320/390/768/1024/1440+;
- radios de controles/media/dialog;
- hairlines y énfasis;
- sombras solo para objeto físicamente plausible;
- tamaños/targets de botones, links aislados, icon buttons y controles;
- inputs/textarea/select/checkbox/radio;
- header/Explorar/nodos/ledger/TOC/figuras/quotes/related;
- focus visible y offset;
- escalas tipográficas y anchos de lectura.

Regla: una familia no crea un radio, sombra, hex, easing o duración local por gusto. Si necesita excepción, debe ser explícita y justificable.

## AD.2 — Componentes globales

Cerrar una gramática reutilizable sin convertirla en librería genérica de cards:

- header/shell;
- Explorar como modal semántico, pero navegación/territorios siguen gobernados por #68;
- footer;
- enlaces textuales y route links;
- primary / secondary / text action;
- breadcrumb/back;
- ledger/metadata;
- figure/media/lightbox condicional;
- related content;
- newsletter/forms;
- details/disclosure;
- TOC/jump links;
- notes/callouts;
- blockquote;
- tablas;
- paginación/archive;
- share/copy;
- status/toast;
- loading/empty/error/404;
- focus/touch/iconos/tags;
- print.

No crear componente porque una sola página tenga una composición distinta.

## AD.3 — Motion como partitura

Funciones permitidas: orientar, confirmar estado, mantener contexto y dirigir atención.

Presupuesto canónico inicial del doc 27:

- press: 100–120ms;
- link/focus: 140–180ms;
- node: 160–200ms;
- preview: 180–240ms;
- header: 220–280ms;
- dialog open: 320–420ms;
- dialog close: 220–300ms;
- page contextual transition: 320–460ms;
- hero completo: 480–680ms, hard max 800ms.

Easing:

- standard `cubic-bezier(.2,0,0,1)`;
- enter `cubic-bezier(.16,1,.3,1)`;
- exit `cubic-bezier(.4,0,1,1)`.

Reglas:

- estado estático completo primero;
- motion solo bajo `prefers-reduced-motion: no-preference` cuando sea espacial/narrativo;
- no `transition: all`;
- no stagger de listas salvo caso mínimo demostrado;
- no parallax/Lenis/scroll-jacking/custom cursor/magnetic hover/WebGL/partículas;
- ninguna animación retrasa interacción;
- cambios de preferencia reduced-motion en sesión deben resolver estado final si existe JS de motion.

Parejas View Transition concretas siguen siendo ownership de sus superficies: #82 Home→Manecillas/Autor; #86 solo Cuaderno→artículo si existe pareja natural.

## AD.4 — UI copy y microcopy

Centralizar la voz funcional sin reescribir contenido SEO/editorial.

Principios:

- literal antes que ingenioso;
- humano, no promocional;
- verbo + resultado/destino;
- no culpar al usuario;
- labels visibles y estables;
- visible y accessible name cuentan la misma tarea;
- errores = problema + corrección;
- éxitos breves y sin celebración artificial.

Auditar especialmente:

- navegación/Explorar contra la autoridad viva #68, no contra listas históricas de 7 destinos;
- hero Home;
- libros/retailers;
- Cuaderno/artículos;
- Autor/Prensa/Eventos;
- Herramientas y verbos de acción;
- newsletter según flujo real #55;
- copiar/compartir;
- loading/empty/error;
- 404;
- downloads/formatos;
- captions/transcript de media;
- fechas y métricas.

No reintroducir frases bloqueadas tipo «sumérgete», «tu viaje», «oops», «algo salió mal» sin explicación, «leer más» repetido o «comprar ahora» si no describe el destino real.

## AD.5 — Estados obligatorios

Para cada componente interactivo aplicable:

- default;
- hover cuando exista;
- focus-visible;
- active;
- disabled;
- loading solo si existe espera;
- success/error cuando cambia datos;
- coarse pointer;
- reduced motion;
- no-JS cuando corresponda.

El QA debe probar edge states reales, no solo happy path.

## Coordinación

- #68: navegación/territorios/findability; AD no cambia su semántica.
- #82: Home/cartografía/Explorar visual y View Transitions prioritarias.
- #83: media/provenance/color; doc 30 se absorbe allí.
- #85–#88: familias de página; consumen AD, no duplican primitivas.
- #61: runtime/scoping y funciones preservadas.
- #55: newsletter/DOI, cuyo estado real gobierna microcopy de confirmación.
- #66/#78: cross-engine/resilience.
- #84: certificación final y CSS ownership.

## Decisión vigente sobre media generada

Doc 30 conserva valor como contrato de producción, crops, focal point, captions, vídeo y manifest, pero su prohibición histórica absoluta de una categoría generada queda superada por la decisión actual del autor.

Se permiten recursos generados/adaptados/retocados y reconstrucciones basadas en referencias reales si:

- tienen función concreta;
- se registran honestamente como generados/adaptados cuando #83 lo exige;
- no falsifican material documental;
- no sustituyen un asset factual que debería ser real;
- no producen estética IA genérica/intercambiable.

## No hacer

- no cambiar todos los tokens por búsqueda/reemplazo sin comprobar consumidores;
- no crear una segunda implementación de Explorar;
- no modificar hechos, schema o navegación para satisfacer microcopy histórico;
- no convertir componentes en cards por uniformidad;
- no añadir dependencias de motion si CSS/plataforma resuelve el caso;
- no diseñar loading ficticio.

## Definition of Done

- tokens/redlines reconciliados y documentados;
- componentes compartidos consumidos sin forks visuales innecesarios por Home + Libro + Artículo + Autor + una Herramienta;
- motion usa propiedades y tiempos explícitos, no `transition: all`;
- reduced motion conserva estados finales completos;
- microcopy funcional converge a una autoridad estable y al estado real de cada flujo;
- 320/390/768/1024/1440/1728, teclado, coarse pointer, 200% zoom y text spacing revisados;
- no hay drift local de radios/sombras/colores/duraciones sin excepción registrada;
- #84 puede certificar el sistema transversal sobre el HEAD final.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.