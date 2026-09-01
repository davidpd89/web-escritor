# F.4 · Revalidación de producción — foco visible + Focus Not Obscured

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `PARTIAL_COVERAGE · BASE_FOCUS_STYLE_EXISTS · KEYBOARD_AND_RETURN_FOCUS_EXIST · GEOMETRY_GAP · WAIT_FOR_SHARED_F1_F2_HARNESS · NO_CODE`

## 1. Conclusión corregida

F.4 no parte de cero y la primera revalidación de esta PR todavía sobreestimaba el gap.

El sistema V1 ya tiene:

- indicador global `:focus-visible`;
- skip-link visible al recibir foco;
- keyboard journey real en Cuaderno;
- `<dialog>` modal para Explorar;
- focus trap explícito dentro de Explorar;
- foco inicial en el botón de cierre al abrir;
- **retorno explícito del foco al opener al cerrar el diálogo**.

Por tanto el retorno de foco ya NO es deuda de F.4.

El único gap material que queda es geométrico: no existe todavía una prueba transversal que demuestre que el componente enfocado no queda completamente oculto por sticky/fixed/overlay author-created UI.

## 2. Cobertura real existente

### Focus visible

`assets/v1-base.css` define el indicador global V1:

```css
html.v1 :focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 3px;
}
```

La existencia del outline no certifica Focus Not Obscured, pero sí invalida cualquier diagnóstico de “falta focus visible global”.

### Journey keyboard

`qa/cuaderno-browser.mjs` comprueba en una superficie editorial representativa:

- ausencia de `tabindex` positivo;
- skip-link como primer foco;
- activación del skip-link;
- navegación desde TOC;
- apertura de Explorar con Enter;
- cierre con Escape;
- disponibilidad por teclado de compartir/imprimir.

### Focus management de Explorar

`assets/v1-shell.js` mantiene un `opener` real. Al abrir:

- guarda el trigger;
- llama `dialog.showModal()`;
- mueve foco a `[data-explore-close]`;
- confina Tab/Shift+Tab dentro del diálogo.

Al evento `close`:

- restaura el estado del shell;
- recupera el scroll previo si procede;
- ejecuta `opener.focus({ preventScroll: true })` en `requestAnimationFrame` y una segunda pasada defensiva.

El supuesto “return-focus gap” de la revalidación anterior queda por tanto descartado.

## 3. Requisito vigente

Referencia: WCAG 2.2, SC 2.4.11 Focus Not Obscured (Minimum), Level AA:  
<https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html>

El mínimo AA exige que, cuando un componente recibe foco por teclado, no quede **enteramente oculto** por contenido creado por el autor.

W3C identifica como riesgos típicos sticky headers, sticky footers y overlays. También explica que un modal correctamente construido no presenta ese problema porque toma foco y confina la interacción hasta cerrarse.

El estándar interno puede aspirar a que el foco quede completamente visible, pero no debe etiquetarse ese objetivo más estricto como requisito AA 2.4.11.

## 4. Gap real restante

Falta una medición browser que, durante journeys representativos, registre:

- `getBoundingClientRect()` del target enfocado;
- intersección con viewport visible;
- cobertura por regiones sticky/fixed/overlay creadas por el sitio;
- si queda al menos una parte visible del componente;
- screenshot/rects cuando existe ocultación total.

Debe incluir al menos:

- shell/header;
- skip-link;
- navegación/editorial TOC;
- Explorar modal;
- sticky CTA real cuando exista en la ruta;
- formularios/herramientas representativos;
- asistente/widget si su overlay está activo en el escenario.

## 5. Por qué no se añade código todavía en esta PR

F.1 y F.2 están implementando sus respectivos contratos sobre el mismo owner sitewide (`qa/sitewide-reflow-browser.mjs` + `Sitewide Reflow QA`) desde ramas DRAFT independientes.

F.4 debe reutilizar esa autoridad una vez las dos piezas estén reconciliadas en un único harness. Crear ahora otro route discovery/crawler para Focus Not Obscured produciría exactamente la duplicidad que #135 intentó evitar.

Además, el conector disponible en esta revisión no permite aplicar hunks sobre `qa/cuaderno-browser.mjs`; solo permite reemplazar el fichero completo. No se reconstruye manualmente un QA browser grande solo para insertar unas líneas, porque el riesgo de corrupción/regresión supera el beneficio.

Esto no invalida F.4; fija correctamente su punto de integración.

## 6. Plan de implementación tras reconciliar F.1/F.2

1. Reusar el route discovery y navegador del harness común.
2. Añadir un helper geométrico de foco, no otro crawler.
3. Ejecutar un conjunto reducido de journeys por familia/owner, no tabular ciegamente miles de nodos sin contexto.
4. Fallar cuando el componente enfocado quede totalmente fuera de viewport o totalmente cubierto por author-created sticky/fixed UI.
5. Mantener como señal diagnóstica adicional cuánto del target queda visible.
6. Conservar el focus-return existente de Explorar y añadir una regresión explícita sobre él si el mismo harness puede hacerlo sin duplicación.
7. Ejecutar los journeys relevantes también bajo F.2 cuando la composición expandida pueda cambiar la geometría.
8. Generar artifact con URL, step, selector, rect del target, rect del blocker y screenshot.

## 7. Guardrails

- No añadir otro outline global y declarar F.4 terminado.
- No eliminar sticky UI durante tests.
- No usar `tabindex` positivo para forzar orden.
- No mover foco programáticamente a cada render.
- No duplicar route discovery.
- No confundir “100% visible” con el mínimo AA, aunque sea objetivo interno preferente.
- No volver a implementar focus return: ya existe en el shell owner.

## 8. Estado final

`PARTIAL_COVERAGE · BASE_FOCUS_STYLE_EXISTS · KEYBOARD_AND_RETURN_FOCUS_EXIST · GEOMETRY_GAP · WAIT_FOR_SHARED_F1_F2_HARNESS · NO_CODE`

F.4 sigue siendo trabajo válido, pero su alcance se reduce a una sola pieza bien definida: **medir Focus Not Obscured con geometría real dentro del harness común cuando F.1/F.2 estén integradas**.
