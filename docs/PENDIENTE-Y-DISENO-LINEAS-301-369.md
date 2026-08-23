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
- cualquier otra PR de diseño final que salga del cruce posterior con `DISEÑO Y DEMÁS`;
- integración de navegación/shell/runtime que afecten la experiencia;
- QA técnico principal en verde.

## Scorecard reproducible

Crear una scorecard versionada y un protocolo de evidencia que cubra, como mínimo, los tests citados en este tramo/documentos 18/25:

### Identidad y comprensión

- **test de 5 segundos:** qué es esta web, quién es David y cuál es la obra protagonista;
- **modelo mental a 30 segundos:** si se entiende qué puede hacer/leer el usuario y cómo se estructura el sitio;
- **test sin logo/nombre:** si el sistema visual sigue teniendo identidad propia;
- **test sin motion:** si la identidad y jerarquía sobreviven sin animación;
- coherencia entre Home y páginas internas sin que todas parezcan la misma plantilla.

### Originalidad y craft

- evitar apariencia de plantilla SaaS/blog/card-grid genérica;
- composición y ritmo editorial;
- tipografía y jerarquía;
- uso deliberado de espacio, líneas, materialidad y media;
- calidad de detalles, estados y transiciones;
- consistencia sin monotonía;
- relación real entre diseño y obra/autor, no decoración intercambiable.

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
- móvil 320/390 y escritorio amplio;
- reduced motion para comprobar que el diseño no depende del efecto.

El conjunto exacto se puede ampliar al cruzar la carpeta `DISEÑO Y DEMÁS`.

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
- threshold global exacto tomado de la autoridad de Drive si allí está definido.

**No inventar ahora un umbral numérico** si el documento maestro todavía no se ha cruzado en esta fase. Cuando revisemos `DISEÑO Y DEMÁS`, incorporar el umbral real de la autoridad vigente.

## Regla de aprobación

No se puede marcar «nivel premio» porque CI esté verde.

Tampoco se puede aprobar si:

- la Home impresiona pero las internas parecen otra web;
- el diseño solo funciona con motion;
- móvil parece una versión degradada;
- la identidad depende de una imagen hero aislada;
- hay problemas de legibilidad, foco, reflow o rendimiento que el diseño introdujo;
- una pieza visual clave carece de procedencia/gobierno cuando #83 la exige.

## Relación con release #1

#1 sigue siendo el gate de release técnico/global. Y debe aportar la **certificación visual/humana final** antes de considerar el diseño listo para producción, pero no sustituye los checks técnicos de #1/#58/#66/#77/#78/#79.

## Definition of Done

Esta PR no estará lista hasta que:

1. CSS ownership global tenga checker + tests de mutación y pase sobre el HEAD integrado;
2. exista scorecard final versionada;
3. el conjunto de páginas/viewports esté definido;
4. se haya ejecutado realmente sobre el HEAD final, no sobre una rama antigua;
5. defectos encontrados estén corregidos o explícitamente bloqueen release;
6. la revisión se repita tras cambios visuales sustanciales posteriores;
7. el resultado humano y los gates automáticos coincidan en un único paquete de evidencia de release.

## Estado

PR **DRAFT** y deliberadamente tardía.

No toca `main`, no despliega producción y no activa auto-merge.
