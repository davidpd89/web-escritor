# Diseño, UX y dirección de arte — sistema operativo 2026

**Fecha de corte:** 27 de agosto de 2026  
**Repositorio:** `davidpd89/web-escritor`  
**Objetivo:** proporcionar a Claude un sistema profesional de observación, diseño, validación y aprendizaje para mejorar `davidportodiaz.com` sin caer en estética genérica generada por IA.

## Qué es esta carpeta

No es un rediseño cerrado y no dice «pon un fondo crema», «usa esta fuente» o «añade cards».

Es un **sistema operativo de diseño** para que Claude pueda:

1. observar la web real;
2. detectar problemas visuales y de UX con evidencia;
3. consultar fuentes expertas y referencias reales;
4. construir hipótesis de diseño;
5. prototiparlas;
6. contrastarlas en Figma y navegador;
7. probarlas en móvil real y varios motores;
8. validar accesibilidad, rendimiento y comportamiento;
9. someter cambios a visual regression;
10. obtener feedback de usuarios cuando corresponda;
11. preservar la identidad editorial ya definida en Drive;
12. evitar que una mejora termine convirtiendo el sitio en una plantilla IA.

## Diagnóstico resumido del estado actual

La implementación V1 tiene fundamentos técnicos buenos: tokens, tipografía propia, shell consistente, HTML semántico, navegación, responsive, reflow, accesibilidad, reduced motion, QA y familias CSS diferenciadas.

El problema principal observado no es «falta CSS». Es que **la dirección de arte definida en los contratos de Drive no llega con la misma fuerza a todas las familias ni a mobile**.

### Home

La Home ya contiene una composición más editorial:

- jerarquías desiguales;
- `river-grid`;
- media integrada en la composición;
- celdas con tratamiento distinto;
- transiciones de densidad;
- cartografía/ruta;
- una jerarquía visual reconocible.

### Páginas interiores

Autor, Cuaderno/artículos, Prensa/Eventos, Herramientas y otras familias dependen mucho más de:

- superficie blanca estable;
- hairlines de 1 px;
- títulos grandes;
- bloques apilados;
- grids que en móvil pasan a `1fr`;
- imágenes tratadas como inserciones más que como decisiones de dirección de arte;
- un mismo patrón vertical repetido durante muchas pantallas.

El resultado puede ser técnicamente correcto y, al mismo tiempo, sentirse plano.

### Mobile

La mayor desviación está aquí.

Los contratos de diseño existentes ya dicen:

> «Mobile: flujo propio, no simple colapso de columnas.»

Y también:

> «mobile está diseñado, no heredado».

Sin embargo, muchas reglas actuales resuelven responsive mediante `grid-template-columns: 1fr`, `display:block` y eliminación de columnas laterales. Eso evita desbordamientos, pero no recompone la escena.

**Reflow correcto ≠ dirección de arte móvil.**

El problema descrito por el usuario —«va todo seguido y no sabes cuándo empieza y termina un bloque»— se interpreta como un fallo de **segmentación perceptual y ritmo**, no como una invitación a envolver cada sección en una card o alternar colores arbitrarios.

## Autoridad existente que esta PR no sustituye

Google Drive ya contiene una dirección de arte bastante más exigente que la implementación actual. Debe conservarse como autoridad conceptual.

Especialmente:

- `16 — DIRECCIÓN DE ARTE Y EXPERIENCIA DE NIVEL PREMIO — CONTRATO V1`;
- `17 — ARQUITECTURA VISUAL POR TIPO DE PÁGINA`;
- `18 — QA DE NIVEL PREMIO`;
- `25 — IMPLEMENTATION HANDOFF MASTER V1`;
- `29 — REDLINES EXACTOS DE COMPOSICIÓN`;
- `30 — SISTEMA DE PRODUCCIÓN DE FOTOGRAFÍA/VÍDEO + MANIFEST JSON`;
- `34 — CONTENT RESILIENCE + EDGE STATES`;
- `35 — MICROTIPOGRAFÍA EDITORIAL ES`;
- `36 — MOBILE RUNTIME + VIEWPORT V1`;
- `13 — MATRIZ DE REFERENCIAS REALES`.

El doc 16 ya establece principios que esta PR convierte en tooling verificable:

- cartografía editorial viva;
- contraste real de escala;
- materialidad real;
- márgenes editoriales;
- composición asimétrica controlada;
- no cards por defecto;
- no bento genérico;
- no glassmorphism;
- no gradientes «creativos» genéricos;
- no fotografía IA que simule archivo real;
- mobile con dirección propia.

## Qué aporta esta PR que faltaba

Los documentos anteriores dicen **qué calidad perseguir**. Esta carpeta añade **cómo conseguir que Claude pueda verla, medirla, contrastarla y mantenerla**.

### P0 — observación real

- Chrome DevTools for agents;
- Playwright MCP/CLI;
- screenshot matrices;
- computed styles;
- accessibility tree;
- layout geometry;
- performance traces;
- responsive emulation;
- DOM/overflow/focus inspection.

### P0 — diseño estructurado

- Figma MCP remoto;
- Agent Skills de Figma;
- sistema de páginas/frames para explorar familias;
- prototipos mobile como composición distinta;
- relación diseño ↔ tokens ↔ código;
- Code Connect solo si la arquitectura lo justifica.

### P0/P1 — dispositivos reales y regresión

- BrowserStack MCP;
- iOS Safari real;
- Android Chrome real;
- Percy o Chromatic como visual regression, no ambos por defecto;
- baseline aprobada por familia y viewport.

### P1 — accesibilidad experta

- Stark MCP o axe MCP;
- WCAG 2.2 como norma;
- Pa11y/Lighthouse existentes siguen siendo QA básico;
- una herramienta experta añade diagnóstico, governance y remediación, no duplica CI.

### P1 — investigación con usuarios

- Maze para prototype/live website testing;
- pruebas de comprensión, first-click, navegación y jerarquía;
- Clarity únicamente bajo gate de privacidad/consentimiento y adecuación de audiencia;
- evidencia humana antes de declarar que una variante «funciona mejor».

### P1 — rendimiento visual real

- CrUX API / CrUX History;
- PSI API solo como complemento de Lighthouse local;
- correlación entre composición, media, LCP/CLS/INP y experiencia móvil real.

### P1 — producción visual

- Canva MCP para moodboards, composiciones promocionales y tratamiento de assets;
- NO usar Canva como fuente de verdad del layout web;
- Figma sigue siendo el espacio de diseño web estructurado;
- material real del autor/libros prima sobre media sintética.

## Herramientas recomendadas por prioridad

| Prioridad | Herramienta | Papel | Credencial |
|---|---|---|---|
| P0 | Chrome DevTools for agents | inspección real, CSS, screenshots, rendimiento, a11y | ninguna |
| P0 | Playwright | navegación reproducible, viewport matrix, screenshot/interaction QA | ninguna |
| P0 | Figma MCP remoto | prototipo, sistema visual, contexto de diseño para Claude | OAuth |
| P0/P1 | BrowserStack MCP | dispositivos/navegadores reales | OAuth remoto preferible o username/access key |
| P1 | Percy **o** Chromatic | visual regression | token del servicio |
| P1 | Stark **o** axe MCP | accesibilidad experta | OAuth/API según producto |
| P1 | Maze | estudios con usuarios | cuenta; integración según flujo |
| P1 | CrUX API | campo real CWV | Google Cloud API key |
| P1 | Canva MCP | assets/moodboards/variantes de media | OAuth |
| Condicional | Clarity | heatmaps/recordings reales | Project ID + consentimiento válido |
| Defer | Storybook MCP | component governance | sin valor suficiente mientras el sitio siga static HTML/CSS |

## Regla: no acumular herramientas por acumular

Cada herramienta debe tener una pregunta que responda.

Ejemplos:

- «¿Por qué esta página se siente plana en 390 px?» → Chrome DevTools + captura + auditoría geométrica.
- «¿Qué composición alternativa mantiene identidad sin cards?» → Figma MCP + referencias anotadas.
- «¿Se rompe en Safari real?» → BrowserStack.
- «¿Este cambio movió media/espaciado sin querer?» → Percy/Chromatic.
- «¿El foco/contraste/touch es robusto?» → axe/Stark + WCAG.
- «¿Un lector entiende dónde acaba una sección?» → Maze con tarea concreta.
- «¿La imagen hero empeora LCP real?» → CrUX/PSI + DevTools trace.

Si no existe una pregunta, no se instala otra plataforma.

## Método obligatorio para cualquier cambio visual

```text
problema observado
→ evidencia reproducible
→ intención de la familia
→ 2–3 hipótesis compositivas
→ referencias con procedencia
→ prototipo
→ revisión contra kill-list
→ móvil + desktop
→ a11y + rendimiento
→ device/browser QA
→ visual regression
→ feedback humano si la decisión es de comprensión/preferencia
→ implementación pequeña
→ revalidación
```

Claude no puede saltar directamente de «se ve plano» a «he cambiado la paleta».

## Qué significa jerarquía móvil en esta web

No significa más colores ni más cajas.

Puede construirse mediante combinación deliberada de:

- cambio de escala;
- cambio de medida de línea;
- cambio de alineación;
- ruptura controlada del gutter;
- full-bleed selectivo de media real;
- metadata que cambia de posición;
- ritmo vertical asimétrico;
- una costura/ruta;
- alternancia de densidad;
- tratamiento tipográfico distinto de fragmento/cita/listado;
- agrupación perceptual;
- silencios intencionales;
- cambio de composición, no solo de tamaño;
- un único momento firma por página interior.

El objetivo es que el usuario pueda percibir «ha terminado una escena; empieza otra» sin necesidad de meter cada escena dentro de un rectángulo.

## Kill-list resumida

Rechazar por defecto si Claude propone sin una necesidad demostrada:

- bento grid;
- cards uniformes;
- hero centrado genérico;
- badges/pills por todas partes;
- glassmorphism;
- blobs;
- gradientes morado/azul;
- black/gold «premium»;
- grano falso;
- papel sintético;
- sombra genérica de SaaS;
- icono en círculo para cada idea;
- carruseles de contenido principal;
- marquee;
- parallax continuo;
- custom cursor;
- fade-up en cada sección;
- vídeo hero por impacto;
- WebGL sin función;
- fotografías IA presentadas como realidad;
- tipografía enorme como sustituto de composición;
- alternar dos fondos solo para «que se noten secciones»;
- rediseñar todas las familias con el mismo template.

## Documentos

1. `01-AUDITORIA-VISUAL-ESTADO-ACTUAL.md` — diagnóstico del código real.
2. `02-MOBILE-JERARQUIA-Y-COMPOSICION.md` — cómo auditar/recomponer mobile sin cardificar.
3. `03-CATALOGO-HERRAMIENTAS-MCP-APIS.md` — herramientas vigentes y setup.
4. `04-FIGMA-MCP-Y-SISTEMA-DE-DISENO.md` — flujo Figma ↔ Claude ↔ código.
5. `05-BROWSER-REAL-DEVICE-VISUAL-REGRESSION.md` — Chrome, Playwright, BrowserStack, Percy/Chromatic.
6. `06-ACCESIBILIDAD-COMO-DISENO.md` — Stark/axe + WCAG + governance.
7. `07-UX-RESEARCH-Y-COMPORTAMIENTO-REAL.md` — Maze, estudios, Clarity condicional.
8. `08-ART-DIRECTION-MEDIA-FOTOGRAFIA.md` — assets reales, crops, Canva y manifest.
9. `09-TIPOGRAFIA-RITMO-DENSIDAD.md` — medir jerarquía sin prescribir una nueva fuente.
10. `10-REFERENCIAS-EXPERTOS-Y-PATRONES.md` — fuentes de criterio, no galería para copiar.
11. `11-SKILLS-Y-AGENTES-PARA-CLAUDE.md` — skills propuestos y contratos de uso.
12. `12-SEGURIDAD-CREDENCIALES-COSTES-PRIVACIDAD.md` — keys/OAuth/planes/gates.
13. `13-BACKLOG-IMPLEMENTACION-CLAUDE.md` — tareas ejecutables y DoD.
14. `14-FUENTES-Y-ESTADO-2026-08-27.md` — fuentes primarias y fecha de corte.
15. `15-ANTI-SLOP-DESIGN-REVIEW.md` — revisión específica contra diseño genérico de IA.
16. `tools-catalog.json` — catálogo machine-readable de tooling y requisitos.

## Definition of Done de una familia rediseñada

No se aprueba una familia porque «se ve mejor» en una captura de escritorio.

Debe cumplir:

- intención clara en 5 segundos;
- protagonista reconocible;
- inicio/final de escenas perceptible;
- jerarquía de 3+ niveles sin depender solo de tamaño de letra;
- 320/390/768/1024/1440/1728 revisados;
- Safari iOS y Chrome Android reales o evidencia equivalente;
- portrait + landscape;
- 200 % zoom/reflow;
- text spacing;
- keyboard/focus;
- reduced motion;
- imágenes con crop/resolution correctos;
- LCP/CLS/INP sin regresión material;
- no pérdida SEO/semántica;
- visual regression aprobada;
- si el cambio pretende mejorar comprensión o navegación, evidencia con usuarios o test comparable;
- sin elementos de la kill-list introducidos sin justificación escrita.

## Principio final

La herramienta no decide el diseño.

Claude tampoco.

Las herramientas permiten que Claude **vea mejor, mida mejor, compare mejor y descarte mejor**. La decisión final se construye con intención editorial, contenido real, referencias procedentes, comportamiento del sitio y validación humana.
