# 11 — Skills y agentes para Claude

## 1. Objetivo

Las herramientas solo son útiles si Claude tiene procedimientos consistentes para usarlas.

No necesitamos un «superagente diseñador». Necesitamos **roles limitados con responsabilidades distintas**.

La arquitectura propuesta separa:

- observación;
- ideación;
- crítica;
- responsive;
- accesibilidad;
- rendimiento;
- research;
- aprobación.

El agente que propone no debe ser el único que valida.

## 2. Estructura propuesta

Futuro, si se decide implementarla:

```text
.claude/
  skills/
    design-observe-live/
    mobile-composition-audit/
    figma-explore/
    media-art-direction/
    a11y-design-review/
    visual-regression-review/
    ux-study-design/
    design-pr-gate/
```

No crear estas skills dentro de la documentación si no están listas para ejecutarse. El backlog define su implementación.

## 3. Skill `design-observe-live`

### Pregunta

¿Qué está ocurriendo realmente en el navegador?

### Tools

- Chrome DevTools;
- Playwright;
- repo/GitHub.

### Inputs

- URL;
- viewport;
- problema descrito;
- family.

### Output

```yaml
problem:
evidence:
  screenshots:
  selectors:
  computedStyles:
  geometry:
  sourceRules:
severity:
hypotheses:
```

### Prohibido

- proponer paleta/fuente antes de observar;
- diagnosticar por screenshot únicamente;
- hacer cambios en producción.

## 4. Skill `mobile-composition-audit`

### Pregunta

¿Qué jerarquía desktop se perdió en mobile y cómo puede reconstruirse?

### Inputs

- 390 current capture;
- 1440 current capture;
- DOM order;
- contracts 16/17/36;
- family rules.

### Debe evaluar

- scene boundaries;
- protagonist;
- section rhythm;
- type dominance;
- media role;
- gutter/full-bleed;
- metadata position;
- action visibility;
- orientation/keyboard constraints.

### Output

Máximo 3 hipótesis compositivas.

### Prohibido

- cards como solución universal;
- alternar backgrounds sin rationale;
- copiar desktop en columna;
- ocultar contenido por falta de espacio.

## 5. Skill `figma-explore`

### Pregunta

¿Cómo se representa y compara una hipótesis antes de tocar código?

### Tool

Figma MCP.

### Inputs

- baseline screenshot;
- real copy/assets;
- hypothesis;
- viewports;
- kill-list.

### Output

- frames A/B/C;
- rationale;
- preserves/changes;
- implementation notes;
- rejection reasons.

### Prohibido

- inventar imágenes/documentos;
- diseñar con lorem ipsum final;
- cambiar tokens globales sin evidencia;
- generar una landing desde cero.

## 6. Skill `media-art-direction`

### Pregunta

¿Qué material real existe y cuál es su papel?

### Tools

- repo assets;
- Drive;
- Figma;
- Canva MCP si se autoriza.

### Output

- asset inventory;
- provenance gaps;
- focal points;
- crop matrix;
- shot list si falta material;
- responsive recommendations.

### Prohibido

- fake photography;
- stock por relleno;
- paper/grain filters para «literary feel»;
- 16:9 universal.

## 7. Skill `a11y-design-review`

### Pregunta

¿La intención visual sigue funcionando con constraints de accesibilidad?

### Tools

- Stark o axe;
- Playwright;
- browser manual;
- WCAG docs.

### Checks

- reflow;
- zoom;
- text spacing;
- contrast;
- focus;
- target size;
- DOM order;
- motion;
- orientation;
- forms/dialogs.

### Prohibido

- «solucionar» quitando personalidad sin explorar otra composición;
- silenciar reglas;
- depender solo de scanner automático.

## 8. Skill `visual-regression-review`

### Pregunta

¿El diff visual corresponde exactamente a la intención declarada?

### Tools

- Percy o Chromatic;
- Playwright;
- GitHub diff.

### Output

Por cada diff:

```text
expected/unexpected
rationale
affected family
mobile status
desktop status
a11y concern
performance concern
accept/reject/rework
```

### Prohibido

- Accept all;
- actualizar baseline para silenciar ruido sin investigarlo;
- máscaras enormes.

## 9. Skill `ux-study-design`

### Pregunta

¿Qué evidencia humana podría decidir entre hipótesis?

### Tools

- Maze;
- manual moderated testing;
- Clarity solo si aprobado.

### Output

- research question;
- participant profile;
- tasks;
- success criteria;
- anti-bias wording;
- analysis template.

### Prohibido

- usar LLMs como participantes;
- preguntar solo preferencias;
- inventar resultados.

## 10. Skill `design-pr-gate`

### Papel

Último crítico antes de marcar una PR visual como lista.

### Inputs

- PR diff;
- evidence pack;
- Figma approved frame;
- visual regression;
- a11y;
- device QA;
- performance;
- contracts.

### Debe bloquear si

- falta mobile;
- cambio no tiene problema/rationale;
- introduce slop de kill-list;
- pierde contenido/SEO;
- rompe 320/zoom;
- no existe evidencia real del resultado;
- asset sin procedencia;
- se cambió una familia global para arreglar una sola página sin revisar efectos.

## 11. Agente 1 — Observer

No diseña.

Responsabilidad:

- obtener hechos;
- reproducir;
- capturar;
- señalar patrones.

Temperatura creativa conceptual: baja.

Debe decir «no sé» cuando no puede medir.

## 12. Agente 2 — Art Director

Recibe evidencia, no acceso libre para cambiar código.

Responsabilidad:

- formular 2–3 hipótesis;
- conectar con contrato 16/17;
- usar referencias con procedencia;
- mantener identidad.

Debe explicar también qué decide **no** añadir.

## 13. Agente 3 — Responsive Specialist

Responsabilidad:

- 320/390/768;
- portrait/landscape;
- reflow;
- browser chrome;
- safe areas;
- keyboard;
- content order;
- media crop.

Puede rechazar una propuesta desktop excelente si mobile no tiene composición propia.

## 14. Agente 4 — Accessibility Reviewer

Independiente del Art Director.

Responsabilidad:

- constraints;
- scan;
- manual checks;
- focus/keyboard;
- text resize.

No «premia» estética.

## 15. Agente 5 — Performance Reviewer

Responsabilidad:

- media bytes;
- LCP candidate;
- CLS;
- fonts;
- script/motion cost;
- CrUX/PSI cuando exista data.

Pregunta central:

> ¿La nueva dirección de arte aumenta coste perceptible y está justificado?

## 16. Agente 6 — Researcher

Responsabilidad:

- referencias;
- provenance;
- guidelines;
- Maze study;
- external expert patterns.

No implementa.

## 17. Agente 7 — Final Critic

Debe ser el más adversarial.

Checklist:

- ¿se solucionó el problema o solo se decoró?;
- ¿parece más a David o más a Behance/AI?;
- ¿hay una señal repetida demasiadas veces?;
- ¿hay un elemento que podamos quitar y mejorar?;
- ¿mobile recompone?;
- ¿la imagen es real/necesaria?;
- ¿qué se degradó?;
- ¿el diseño resiste sin motion?;
- ¿resiste en grayscale/blur?;
- ¿hay razón para cada excepción?

## 18. Secuencia multi-agente

```text
Observer
  ↓
Responsive audit
  ↓
Art Director hypotheses
  ↓
Figma Explore
  ↓
Final Critic (pre-code)
  ↓
Implementation
  ↓
Accessibility + Performance
  ↓
BrowserStack + Visual Regression
  ↓
UX research si corresponde
  ↓
Final PR Gate
```

No ejecutar todos los agentes en cada cambio de 2 líneas.

## 19. Evidence-first prompts

### Observer

```text
Audita esta URL a 390 y 1440. No propongas cambios visuales todavía. Devuelve solo evidencia: geometría, computed styles, repetición de patrones, media, heading hierarchy, scroll structure y source CSS.
```

### Art Director

```text
Usa el diagnóstico adjunto y los contratos 16/17. Genera exactamente tres hipótesis que cambien composición, no paleta. Cada una debe preservar HTML/SEO, explicar qué elimina y señalar riesgos mobile/a11y/performance.
```

### Critic

```text
No mejores esta propuesta. Intenta rechazarla. Señala elementos de plantilla/AI slop, decisiones sin evidencia, pérdida de jerarquía, repetición, problemas mobile y cualquier cambio que no derive del contenido real.
```

## 20. Qué contexto cargar

No inyectar 40 documentos enteros en cada agent.

Crear context packs por tarea:

### Mobile article

- relevant CSS;
- doc 16 extract;
- doc 17 Article/Mobile;
- doc 36 relevant runtime;
- current captures;
- problem statement.

### Book

- v1-book/v1-samuel CSS;
- doc 17 Book;
- media manifest;
- current captures.

Reducir ruido mejora decisiones.

## 21. Skills oficiales vs propias

Si una herramienta ofrece Skills oficiales —Chrome/Figma, por ejemplo—, usarlas como base para operación de esa herramienta.

Las skills propias deben orquestar el **criterio del proyecto**, no duplicar la documentación oficial del MCP.

## 22. Versionado

Cada skill debe incluir:

```yaml
name:
version:
lastReviewed:
tools:
authorityDocs:
outputs:
forbidden:
```

Revisar cuando cambia significativamente el MCP o el contrato del sitio.

## 23. No autopublish

Ningún agente de diseño obtiene permiso para:

- mergear;
- desplegar;
- cambiar DNS;
- crear keys;
- activar tracking;
- actualizar baselines globales sin review;
- modificar datos editoriales.

## 24. Learning loop

Después de una mejora mergeada:

1. observar producción;
2. registrar qué hipótesis funcionó;
3. actualizar pattern ledger;
4. convertir un aprendizaje repetible en skill/check;
5. evitar convertir una solución local en regla universal demasiado pronto.

## 25. Criterio final

El sistema de agentes tiene éxito cuando Claude deja de responder:

> «he hecho el diseño más moderno»

Y empieza a responder:

> «detecté esta pérdida de jerarquía, probé estas tres composiciones, descarté dos por estos motivos y la solución final ha pasado estos gates.»