# Y — Diseño final · líneas 301–369 (EOF)

Fuente auditada: `PENDIENTE DISEÑO GPT.txt`, líneas **301–369 (EOF)**.
Base: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Clasificación del bloque

### Back to top — NO abrir owner nuevo

Las líneas 301–322 describen el botón `back-to-top` global/legacy y piden convertirlo en comportamiento `SCOPE`/opt-in para páginas realmente largas.

Ese problema ya pertenece al owner funcional de runtime **#61 H.1** y además está recogido por `data/ux-feature-retention.json` (`long-page-only`, focus visible, reduced motion, no colisión con flotantes).

Esta PR Y no reimplementa el botón ni modifica `script.js`.

### QA técnico con owners ya existentes

Las líneas 343–351 no justifican PR duplicadas:

- cross-browser Chromium/Firefox/WebKit → **#66**;
- runtime móvil/resiliencia/safe-area/no-JS/edge states → **#78**;
- Performance/Core Web Vitals/Lighthouse integrado → **#77 + release #1**;
- HTTP real, staging, redirects/publicación/headers → **#58 + #62 + #79 + #1**;
- estabilidad/reproducibilidad de Playwright → **#65** y owners QA existentes.

Y no debe absorber ni relajar esos gates.

## Deuda nueva real 1 — CSS ownership global

La línea 347 identifica un fallo de clase que ya ha ocurrido en el proyecto: HTML que usa una clase cuya definición CSS no está realmente cargada por esa página/familia.

No basta con buscar el nombre en todo el repositorio. El gate debe razonar sobre **CSS efectivamente cargado por cada documento**.

### Contrato

Crear un checker global, nombre orientativo `scripts/check-css-ownership.py`, que para cada HTML público relevante:

1. resuelva las hojas de estilo locales cargadas por esa página;
2. siga imports locales si existen;
3. extraiga las clases usadas en el HTML;
4. compruebe si esas clases tienen definición en la cascada realmente cargada;
5. permita hooks/clases deliberadamente no visuales mediante una autoridad explícita y justificada, no un ignore global;
6. distinga clases de estado añadidas por JS mediante un pequeño manifest/contrato runtime si es necesario;
7. falle cuando una clase visual se usa pero su CSS solo existe en otra familia que la página no carga.

Debe probarse con mutaciones que reproduzcan el fallo real:

- clase presente en CSS global cargado → PASS;
- clase presente únicamente en CSS no cargado → FAIL;
- clase eliminada de su stylesheet → FAIL;
- hook no visual explícitamente permitido → PASS;
- allowlist sin razón/entrada válida → FAIL.

No debe obligar a que toda clase tenga reglas propias si su semántica es de hook JS/QA; esas excepciones deben ser explícitas y pequeñas.

## Deuda nueva real 2 — certificación humana/visual final «nivel premio»

Las líneas 353–364 dejan claro que la infraestructura automática no puede certificar el objetivo visual final.

Esta PR es el owner del **cierre visual humano sobre el HEAD definitivo**, no de la implementación estética de cada página.

### Momento correcto

No ejecutar ni aprobar este gate sobre el diseño intermedio.

Debe hacerse después de:

- #82 Home/cartografía/motion/materialidad;
- #83 procedencia/media/color;
- #85 familia Libro;
- #86 Cuaderno + artículos;
- #87 Autor + Prensa + Eventos;
- #88 Herramientas;
- cualquier otra PR transversal de diseño final que salga del cruce posterior con `DISEÑO Y DEMÁS`;
- integración de navegación/shell/runtime que afecten la experiencia;
- QA técnico principal en verde.

## Scorecard oficial de producción — autoridad doc 18

El cruce posterior con `DISEÑO Y DEMÁS` ya ha resuelto el umbral. La autoridad más específica es:

`18 — QA DE NIVEL PREMIO — SCORECARD · TEST DE IDENTIDAD · UX · RESPONSIVE · MOTION`.

### BLOQUE A — Webby-like

- Content presentation: **≥ 8.5/10**
- Structure & Navigation: **≥ 8.5/10**
- Visual Design: **≥ 8.7/10**
- Functionality: **≥ 8.5/10**
- Interactivity: **≥ 8.0/10**
- Innovation: **≥ 8.0/10**
- Overall Experience: **≥ 8.7/10**

### BLOQUE B — CSSDA-like

- UI: **≥ 8.7/10**
- UX: **≥ 8.5/10**
- Innovation: **≥ 8.0/10**

### BLOQUE C — gates NO compensables

Todos deben ser PASS:

- Accesibilidad;
- Responsive;
- contenido SEO preservado;
- sin JavaScript esencial;
- reduced motion;
- presupuesto de rendimiento;
- procedencia final de media.

En lab, procedencia de media puede quedar `PENDING`; **en producción debe ser PASS**.

Una media alta NO salva un fallo en un gate no compensable.

## Scorecard reproducible

Crear una scorecard versionada y un protocolo de evidencia que cubra, como mínimo:

### Identidad y comprensión

- **test de 5 segundos:** qué es esta web, quién es David y cuál es la obra protagonista;
- **modelo mental a 30 segundos:** si se entiende qué puede hacer/leer el usuario y cómo se estructura el sitio;
- **test sin logo/nombre:** si el sistema visual sigue teniendo identidad propia;
- **test sin motion:** si la identidad y jerarquía sobreviven sin animación;
- **test sin imágenes decorativas:** si tipografía/espacio/estructura sostienen la interfaz aunque se retiren assets no esenciales;
- coherencia entre Home y páginas internas sin que todas parezcan la misma plantilla.

### Originalidad y craft

- evitar apariencia de plantilla SaaS/blog/card-grid genérica;
- composición y ritmo editorial;
- tipografía y jerarquía;
- uso deliberado de espacio, líneas, materialidad y media;
- calidad de detalles, estados y transiciones;
- consistencia sin monotonía;
- relación real entre diseño y obra/autor, no decoración intercambiable;
- cualquier textura/sombra/anotación/documento final debe poder explicar su origen material o volver a una solución tipográfica neutral.

### Variantes / deuda de artificio

Si sigue existiendo una comparación entre soluciones V1-A/V1-B o equivalentes, no decidir por gusto. Comparar claridad, impacto, deuda de artificio, extensibilidad a internas, rendimiento y complejidad. Una mejora visual pequeña no compensa una complejidad muy superior o una peor extensión al resto del sitio.

### Memoria

- prueba de recuerdo tras 24–48 h cuando sea viable;
- registrar qué elemento/idea visual se recuerda y si se asocia correctamente a David/Manecillas.

### Experiencia por superficies

La muestra mínima debe incluir:

- Home;
- Las manecillas del recuerdo;
- Samuel entre mundos;
- Autor;
- Cuaderno + un artículo largo;
- Herramientas + al menos una herramienta interactiva;
- Prensa/Eventos;
- Explorar;
- móvil 320/390, tablet 768, 1024, desktop 1440 y ultrawide 1728+;
- reduced motion para comprobar que el diseño no depende del efecto.

### Tareas de navegación

Registrar éxito/fracaso, primer click, dudas y ruta real para al menos:

1. descubrir Manecillas;
2. encontrar Samuel;
3. saber quién es David;
4. abrir un artículo del Cuaderno;
5. encontrar una herramienta;
6. localizar próximos eventos/prensa;
7. volver al inicio;
8. abrir/cerrar Explorar;
9. repetir las tareas esenciales solo con teclado en desktop.

No optimizar solo número de clicks: comprensión y modelo mental pesan más.

## Evidencia

La certificación no puede ser un «se ve bien».

Debe dejar:

- HEAD/SHA evaluado;
- fecha;
- navegador/dispositivo/viewport;
- capturas o referencias visuales suficientes cuando sean útiles;
- puntuaciones/observaciones por criterio;
- defectos encontrados y owner;
- resultado final PASS/BLOCKED;
- resultado de cada gate no compensable;
- excepciones explícitas, si alguna, sin rebajar los mínimos anteriores.

## Regla de aprobación

No se puede marcar «nivel premio» porque CI esté verde.

Tampoco se puede aprobar si:

- la Home impresiona pero las internas parecen otra web;
- el diseño solo funciona con motion;
- móvil parece una versión degradada;
- la identidad depende de una imagen hero aislada;
- hay problemas de legibilidad, foco, reflow o rendimiento que el diseño introdujo;
- una pieza visual clave carece de procedencia/gobierno cuando #83 la exige;
- se incumple cualquier threshold del scorecard;
- falla cualquier gate no compensable.

## Relación con release #1

#1 sigue siendo el gate de release técnico/global. Y debe aportar la **certificación visual/humana final** antes de considerar el diseño listo para producción, pero no sustituye los checks técnicos de #1/#58/#66/#77/#78/#79.

## Definition of Done

Esta PR no estará lista hasta que:

1. CSS ownership global tenga checker + tests de mutación y pase sobre el HEAD integrado;
2. exista scorecard final versionada con los umbrales del doc 18;
3. el conjunto de páginas/viewports esté definido;
4. se haya ejecutado realmente sobre el HEAD final, no sobre una rama antigua;
5. defectos encontrados estén corregidos o explícitamente bloqueen release;
6. la revisión se repita tras cambios visuales sustanciales posteriores;
7. el resultado humano y los gates automáticos coincidan en un único paquete de evidencia de release;
8. todos los gates no compensables estén en PASS para producción.

## Estado

PR **DRAFT** y deliberadamente tardía.

No toca `main`, no despliega producción y no activa auto-merge.
