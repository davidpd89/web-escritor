# Diseño — Club Samuel · contrato de unificación visual · 2026-08-30

## 1. Trazabilidad

Cadena de diseño:

1. #163 — HOME · unificación visual azul/dorado.
2. #174 — Libros · hub de Obras.
3. #205 — Manecillas · ficha principal.
4. #264 — Fragmentos · página de lectura.
5. #265 — Samuel entre mundos · ficha principal.
6. #266 — Samuel · capítulo 1.
7. #267 — Noveris · archivo de mundo.
8. esta PR — `/clubes-de-lectura/samuel-entre-mundos/`.

La rama nace exactamente del HEAD `d8cc212404e23cdfbea0286ed98153d13c83b7e2` de #267, con sus 11 workflows verdes. No mergear fuera de orden; al integrar las bases, retargetear a `main` y volver a comprobar el diff propio.

## 2. Objetivo

La página del Club debe leerse como **dossier de mediación / guía de sesión**, no como herramienta genérica, FAQ extensa ni copia del archivo Noveris.

La firma azul/negro/dorado se mantiene como continuidad Samuel, pero la jerarquía responde a tareas de un coordinador:

- entender rápidamente para qué grupo funciona el libro;
- preparar una sesión;
- consultar datos bibliográficos;
- recorrer una guía de debate numerada;
- invitar al autor;
- acceder a recursos de apoyo;
- cerrar la preparación con un CTA reconocible.

## 3. Invariantes

Esta PR no modifica `clubes-de-lectura/samuel-entre-mundos/index.html`.

Se preservan:

- title, description, canonical y OG/Twitter;
- JSON-LD `WebPage` + `Guide`/`LearningResource`;
- las 10 preguntas canónicas y sus respuestas;
- la separación explícita entre contenido sin spoilers y guía con spoilers;
- datos del libro, ISBN, páginas, editorial y año;
- información y condiciones de invitación al autor;
- links a Noveris, capítulo, ficha del libro, Amazon, prensa y guía imprimible;
- mailto y atributos de contacto;
- IDs/anchors y comportamiento nativo de `<details>`;
- navegación contextual Samuel;
- contratos funcionales, reflow, 200% texto, text spacing y CLS cubiertos por `qa/samuel-ecosystem-browser.mjs`.

La guía imprimible queda fuera de alcance visual y se trata como superficie separada.

## 4. Baseline auditado

Evidencia recuperada de `samuel-ecosystem-qa` en 1440 y 390 px:

1. hero heredado de herramienta genérica, con CTA principal negro;
2. tres cards iniciales con exactamente el mismo peso visual;
3. ficha del coordinador como lista plana sin jerarquía documental;
4. diez preguntas correctas pero con ritmo excesivamente uniforme en móvil;
5. invitación al autor presentada como bloque de herramienta;
6. recursos repetidos como otro trío de cards;
7. CTA final visualmente casi indistinguible de una sección ordinaria;
8. footer sin la firma Samuel aplicada en Noveris/ficha principal.

No se detectó necesidad de reescribir contenido ni de cambiar la arquitectura semántica.

## 5. Sistema visual

### Scoping

`assets/clubes-samuel.css` contiene una capa V2 protegida por la firma estructural única:

`html.v1[data-editorial-context="samuel"]:has(main[data-family="lore"]>#guia-rapida)`

El objetivo es impedir cualquier fuga a Noveris u otras superficies companion. El smoke cross-engine navega además a la guía imprimible y exige ausencia de `--club-blue`.

### Tokens

- azul `#1d4f96`;
- azul oscuro `#0d2c57`;
- dorado `#b8860b`;
- azul pálido `#eefaff`;
- tinta `#050505`;
- neutral `#6f6a64`.

### Hero

- apertura Yellowtail dorada con highlight azul;
- H1 editorial azul, sin apariencia de herramienta;
- lead serif/tinta;
- acciones manuscritas azules sin botón negro;
- doble cierre azul/dorado.

En `<=900px` las acciones pasan a columna. Además de mejorar el ritmo de tablet/móvil, esta regla elimina el rewrap inestable observado cuando Yellowtail termina de cargar.

### Guía rápida

Las tres cards se convierten en registros abiertos `01/02/03`, separados por reglas, con H3 azul y sin cajas decorativas. El registro pasa de 3 columnas a 1 en `901/900`.

### Plan de sesión e invitación

Los `.tool-two-col` pasan a pares de dossiers abiertos con reglas azul/dorado. En `<=767px` se apilan sin crear cajas nuevas.

### Ficha del coordinador

`.fact-list` se convierte en ledger factual de dos columnas con labels UI neutrales y texto de lectura. El seam contractual es `761/760`.

### Guía de debate

- nota de spoilers en superficie azul pálida con rail azul;
- diez preguntas como secuencia numerada `01–10`;
- títulos azules y número dorado;
- `<details>` permanece nativo;
- el estado abierto obtiene rail azul y superficie pálida para separar pregunta/respuesta sin añadir JS;
- en `<=640px` se reduce la columna numérica y el sangrado de la respuesta.

### Recursos y cierre

Los tres recursos se convierten en índice abierto 3→1 en `901/900`. `#cta-final` funciona como cierre de sesión con superficie pálida, rail azul y remate dorado.

### Shell

Footer, Volver arriba, navegación contextual y hover/focus de Asistente siguen la firma azul/dorado. El launcher flotante se oculta en `<=1300px`, manteniendo accesible el Asistente del header.

## 6. QA específico

`qa/club-samuel-design-browser.mjs` cubre:

- 1440×1000;
- 1280×800;
- 1024×768;
- 901×800 / 900×800;
- 768×1024;
- 761×900 / 760×900;
- 641×900 / 640×900;
- 390×844;
- 360×800.

Comprueba scope, canonical, navegación contextual, Asistente, overflow, hero, acciones, briefing 3→1, dossiers, ficha 2→1, diez preguntas, estado abierto, recursos, cierre, footer, launcher y genera capturas full-page más `club-samuel-design-report.json`.

`qa/club-samuel-design-cross-engine.mjs` ejecuta Chromium, Firefox y WebKit y valida además que la capa no se filtre a `/guia-imprimible/`.

El módulo cross-engine se importa desde `qa/samuel-design-cross-engine.mjs`, y Sitewide Reflow ejecuta el contrato visual del Club como step independiente.

La evidencia automatizada de implementación quedó cerrada en `1f8f19ff66fca3e0decff18aa8a848f38b0ed515`: 10/10 workflows disparados por esta PR en verde, incluido Sitewide Reflow completo, Samuel ecosystem browser QA, Cross-engine smoke, Lighthouse CI y Accessibility baseline. El artefacto Sitewide del mismo SHA (`sitewide-reflow-qa`, digest `sha256:63a3d445474b8867e14d779267019094bbf1b4b5823562b5dd777fafad41d8f7`) contiene las 12 capturas y `club-samuel-design-report.json` con `failures: []`.

## 7. Defectos encontrados y cierre

La primera implementación no se aceptó por inercia; los gates detectaron y la revisión manual aisló cuatro problemas concretos:

1. **CLS real en tablet:** `qa/samuel-ecosystem-browser.mjs` midió `0.1913` a 768 px frente al máximo contractual `0.1`. No se relajó el umbral. Las acciones manuscritas, todavía en `flex-wrap`, podían cambiar de fila al terminar de cargar Yellowtail. Se estabilizaron en columna para `<=900px`; el mismo gate volvió a verde manteniendo el límite original.
2. **Lectura prematura del estado abierto:** el smoke cross-engine consultaba el rail azul del `<details>` inmediatamente después del click y alcanzaba el primer frame de la transición. El contrato espera 260 ms, por encima de los 220 ms de `--motion-state`, y valida el estado final real en Chromium, Firefox y WebKit.
3. **CSS counters mal observados por el test:** CSSOM devuelve la expresión `counter(...)` en `content`, no el valor visual ya resuelto `01`. El QA se corrigió para comprobar el mecanismo completo —`counter-reset`, `counter-increment` y `content: counter(...)`— tanto en briefing como en preguntas, sin modificar la presentación.
4. **Captura full-page contaminada por el estado del runner:** después de abrir la primera pregunta Playwright había desplazado la página; el shell `fixed`/sticky podía quedar cosido a media captura. Antes de fotografiar se limpia foco y se vuelve a `scrollTo(0,0)`. La evidencia final ya no contiene el bloque `Saltar al contenido` ni una cabecera duplicada en mitad de la página.

Revisión manual final del artefacto limpio:

- 1440/1280: jerarquía de dossier consistente y cierre/footer limpios;
- 1024/768: transición coherente de acciones/briefing sin romper los dossiers que todavía deben permanecer en dos columnas;
- 901/900: briefing y recursos 3→1, acciones horizontal→columna, sin overflow;
- 761/760: ficha del coordinador 2→1 limpia;
- 641/640: ajuste del gutter de preguntas sin salto ni desbordamiento;
- 390/360: lectura, preguntas, autor, recursos, CTA final y footer estables.

## 8. Definition of Done

- [x] rama creada exactamente sobre #267 ya verde;
- [x] baseline 1440/390 recuperado e inspeccionado;
- [x] dirección visual de dossier definida;
- [x] implementación CSS-only y scoped;
- [x] QA Chromium específico añadido;
- [x] QA cross-engine y aislamiento añadidos;
- [x] Sitewide Reflow conectado;
- [x] primera ejecución CI revisada;
- [x] defectos objetivos de navegador corregidos;
- [x] capturas finales y seams revisados;
- [x] todos los gates de implementación/evidencia verdes;
- [ ] revisión física/humana antes del merge.

## 9. Revisión física pendiente

Antes de mergear, heredar `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` y comprobar en dispositivo real:

- iPhone/Safari y Android/Chrome;
- lectura de las diez preguntas con varias abiertas/cerradas;
- densidad real de la ficha del coordinador;
- tap targets y scroll de la navegación contextual;
- rotación y safe areas;
- zoom/text spacing en navegador real;
- hover/focus en desktop real;
- cache, hard reload y back-forward cache.

**Estado técnico:** evidencia automatizada y revisión visual de escritorio/headless cerradas. Mantener la PR en Draft y sin mergear hasta completar la revisión física/humana y respetar el orden de la cadena de PRs.