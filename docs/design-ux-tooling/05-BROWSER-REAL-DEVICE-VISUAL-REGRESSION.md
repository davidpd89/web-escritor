# 05 — Browser real, dispositivos y visual regression

## 1. Objetivo

Un diseño web no se valida en Figma.

Tampoco se valida con una única captura responsive de Chrome desktop.

Esta capa comprueba que una decisión de dirección de arte sobrevive a:

- DOM real;
- CSS real;
- fonts reales;
- contenido real;
- motores distintos;
- barras móviles;
- orientación;
- teclado;
- focus;
- zoom;
- carga de imágenes;
- estados dinámicos;
- cambios posteriores del repositorio.

## 2. Stack recomendado

### Observación exploratoria

Chrome DevTools for agents.

### Automatización reproducible

Playwright.

### Dispositivos reales

BrowserStack.

### Visual regression

Elegir una:

- Percy, si se adopta BrowserStack como plataforma principal;
- Chromatic, si su integración Playwright/revisión encaja mejor.

No mantener dos baselines visuales equivalentes por defecto.

## 3. Chrome DevTools: protocolo de observación

Para cada problema visual, Claude debe recoger:

1. URL;
2. commit/deploy;
3. viewport;
4. screenshot;
5. selector relevante;
6. computed styles;
7. bounding box;
8. reglas CSS de origen;
9. accessibility role/name si interactivo;
10. network/performance si media o script influyen.

Ejemplo de hallazgo útil:

```text
Problema: H1 de Autor domina 76 % de la primera pantalla a 390 px.
Evidencia:
- viewport 390×844
- font-size computed: ...
- 4 líneas
- retrato comienza por debajo de ...
- CTA/contexto no aparece hasta ...
Regla responsable: .v1-masthead h1 + token --text-hero
Hipótesis: cambiar relación de escala/orden en identity mobile, no token global.
```

Mucho mejor que:

> «La letra parece grande».

## 4. Playwright: capture pack

Crear un script dedicado, por ejemplo:

```text
scripts/design/capture-design-baseline.mjs
```

No implementarlo dentro de esta PR documental; Claude debe hacerlo en fase de ejecución.

### Inputs

- base URL;
- rutas;
- viewports;
- color scheme si procede;
- reduced motion;
- output directory;
- commit SHA/label.

### Outputs

```text
.design-evidence/
  <sha>/
    390/
      home.png
      author.png
      article.png
    1440/
      ...
    manifest.json
```

`.design-evidence/` debería ser un artefacto de CI/local y no formar parte del public dist.

## 5. Rutas mínimas

### Core

- `/`;
- `/las-manecillas-del-recuerdo/`;
- `/libros/samuel-entre-mundos/`;
- `/autor.html`;
- `/cuaderno/`;
- un artículo representativo;
- `/herramientas/`;
- una herramienta interactiva;
- `/prensa.html`;
- `/eventos.html`;
- `/editoriales/` o ficha de editorial.

### Estados

No capturar solo `load`.

Incluir cuando aplique:

- Explorar abierto;
- FAQ/details abierto;
- focus visible;
- hover desktop;
- tool result;
- form error;
- form success simulado sin escribir en servicios reales;
- long title fixture;
- no-JS;
- webfont fallback;
- reduced motion;
- 200 % zoom/text-spacing mediante entorno apropiado.

## 6. Viewports

Baseline mínimo:

```text
320×568
390×844
430×932
768×1024
1024×768
1440×900
1728×1117
667×375
844×390
```

No representan modelos exactos de dispositivo. Son stress points de composición.

## 7. Device matrix real

No hace falta una granja gigantesca.

### Tier A

- Safari iOS actual, iPhone moderno;
- Safari iOS en un viewport/dispositivo más pequeño si disponible;
- Chrome Android actual, Android moderno;
- Chrome Android en device con viewport más estrecho si disponible.

### Tier B

- Safari macOS;
- Chrome desktop;
- Firefox desktop;
- Edge desktop.

### Tier C

- Firefox Android/emulación;
- tablets según problema concreto.

## 8. Casos que requieren dispositivo real

Prioridad máxima para:

- browser bars dinámicas;
- safe areas;
- notch/home indicator;
- keyboard virtual;
- scroll/touch;
- orientation change;
- sticky header;
- dialog;
- inputs;
- tap targets;
- viewport resize on keyboard;
- font rendering si el problema es perceptible.

No introducir CSS específico de Safari por un fallo visto solo en emulación.

## 9. BrowserStack MCP

Usar a Claude como operador de test, no como juez estético.

Flujo:

```text
PR visual
→ preview URL
→ BrowserStack device session
→ ejecutar checklist
→ capturas/evidencia
→ registrar PASS/FAIL
```

### Autenticación

Preferir OAuth remoto si está disponible en la cuenta/configuración elegida.

Si se usa integración local:

```text
BROWSERSTACK_USERNAME
BROWSERSTACK_ACCESS_KEY
```

Solo en secreto local/CI autorizado.

## 10. Visual regression: qué baseline crear

No baseline de todas las páginas desde el día 1.

Orden:

1. shell;
2. Home;
3. familia piloto interior;
4. Book;
5. Identity;
6. Editorial;
7. Tools;
8. resto estable.

Una baseline masiva antes de arreglar el sistema solo congela deuda visual.

## 11. Percy o Chromatic

### Percy

Ventaja natural si BrowserStack es parte del stack.

Integrar con Playwright para:

- snapshots por viewport;
- PR diffs;
- aprobación explícita.

Secret:

```text
PERCY_TOKEN
```

solo tras autorización.

### Chromatic

Alternativa válida para Playwright visual tests.

Guardar su project token como secret, nunca en código.

### Elección

Hacer un piloto de una PR con cambios reales y comparar:

- calidad del diff;
- review UX;
- velocidad;
- ruido por fuentes/antialiasing;
- facilidad de actualizar baseline;
- precio/plan disponible;
- integración con GitHub.

## 12. Qué debe ignorarse en visual regression

Una baseline visual no debe ser tan frágil que falle por:

- timestamps dinámicos irrelevantes;
- contenido remoto no controlado;
- animación en progreso;
- cursor;
- blinking caret.

Congelar o excluir de forma controlada esos elementos en test.

No enmascarar regiones grandes para «hacer verde» el test.

## 13. Motion

Snapshots:

- usar reduced motion o estado estable;
- capturar final de transición si se necesita;
- no depender de `waitForTimeout(5000)` arbitrario.

Tests de motion por separado:

- no motion competitivo;
- no layout shift destructivo;
- reduced motion mantiene toda la información;
- View Transition no altera Back/scroll.

## 14. Geometry assertions

No convertir cada pixel en test. Sí proteger invariantes.

Ejemplos útiles:

- ningún elemento genera overflow horizontal;
- header no cubre H1/focus target;
- CTA esencial >= target requerido;
- portada no supera/cae por debajo de un rango razonable en contexto;
- reading measure no excede límite del sistema;
- dialog cabe o hace scroll en altura baja;
- sección principal no queda por debajo de un overlay.

Evitar asserts de `top === 128px` salvo que sea una geometría contractual real.

## 15. Screenshot review protocol

Cada diff visual debe responder:

1. ¿es esperado?;
2. ¿por qué existe?;
3. ¿mejora el problema declarado?;
4. ¿afecta otra familia?;
5. ¿cambió typography/media sin intención?;
6. ¿390 y 1440 mejoran simultáneamente?;
7. ¿320 sigue siendo coherente?;
8. ¿se introdujo slop de diseño?;
9. ¿hay regresión en focus/reflow?;
10. ¿baseline debe actualizarse?

Un botón «Accept all changes» sin revisión invalida el gate.

## 16. Font loading

Capturar:

- estado con fuentes cargadas;
- fallback simulado.

Comprobar que fallback no provoca:

- headings cortados;
- layout shift grande;
- botones ilegibles;
- navegación desbordada.

## 17. Image loading

Para cambios de media:

- captura con imagen cargada;
- dimensiones intrínsecas;
- `srcset/sizes`;
- aspect-ratio;
- focal point;
- LCP candidate;
- CLS.

No aprobar una mejora de composición que duplique bytes de la primera pantalla sin necesidad.

## 18. 200 % zoom y text spacing

Visual regression clásica no sustituye estos tests.

Crear escenarios específicos:

- browser zoom/reflow;
- stylesheet de WCAG text spacing;
- screenshots/checks de overflow y overlap.

## 19. Landscape

Para 667×375/844×390:

- no pedir que «todo el hero quepa»;
- probar scroll normal;
- comprobar header;
- Explorar;
- una página de libro;
- una herramienta/form.

## 20. PR evidence

Toda PR de rediseño relevante debería incluir en descripción/enlace a artefactos:

```text
BEFORE/AFTER
390
1440
320
landscape
real iOS
real Android
visual diff
accessibility result
performance note
```

No subir megabytes de screenshots al public artifact.

## 21. CI

El repo ya tiene:

- Lighthouse;
- Pa11y;
- reflow;
- browser QA;
- discoverability;
- family-specific QA.

No duplicarlos.

Nuevo workflow visual, si se aprueba, debe centrarse en:

- snapshots/diffs;
- un subconjunto representativo;
- PRs que toquen HTML/CSS/assets relevantes;
- artefactos de evidencia.

## 22. Failure policy

Un visual diff rojo no es automáticamente bug.

Un test sin diff tampoco es automáticamente bueno.

El gate correcto combina:

```text
intención
+ diff
+ browser/device
+ a11y
+ performance
+ review humano
```

## 23. Criterio final

La infraestructura es buena cuando un revisor puede saber exactamente:

- qué cambió;
- dónde;
- por qué;
- cómo se ve en mobile y desktop;
- si rompe algún estado;
- si fue probado en navegador real.

Sin depender de «a mí me parece más bonito».