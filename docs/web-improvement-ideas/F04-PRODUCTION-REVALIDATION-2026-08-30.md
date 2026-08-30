# F.4 · Revalidación de producción — foco visible + Focus Not Obscured

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `PARTIAL_COVERAGE · BASE_FOCUS_STYLE_EXISTS · KEYBOARD_JOURNEY_EXISTS · GEOMETRY_AND_RETURN_FOCUS_GAP · SEQUENCE_AFTER_F2 · NO_CODE_YET`

## 1. Conclusión

F.4 no parte de cero. El sistema V1 ya define un indicador global `:focus-visible` y el QA de Cuaderno ejecuta un journey real de teclado sobre skip-link, TOC y el diálogo Explorar.

Lo que no queda demostrado por la cobertura inspeccionada es la parte madura de F.4: que el foco no quede oculto por UI sticky/fixed/overlay y que un overlay devuelva explícitamente el foco al trigger después de cerrarse.

Por tanto el gap es geométrico/de journey, no un problema de «falta outline» ni una ausencia total de keyboard QA.

## 2. Cobertura real existente

### CSS base

`assets/v1-base.css` elimina el outline nativo de controles V1 pero lo sustituye globalmente con:

```css
html.v1 :focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 3px;
}
```

También existe skip-link visible al recibir foco.

### Browser QA existente

`qa/cuaderno-browser.mjs` ya comprueba en un artículo representativo:

- ausencia de `tabindex` positivo;
- skip-link como primer foco;
- activación del skip-link;
- navegación de TOC por teclado;
- apertura de Explorar con Enter;
- cierre del diálogo con Escape;
- disponibilidad por teclado de acciones de compartir/imprimir.

Esto invalida cualquier conclusión de «no hay journey de teclado».

## 3. Gap que sí permanece

En el QA inspeccionado no se mide, durante cada paso del journey:

- `getBoundingClientRect()` del elemento enfocado;
- intersección del target con viewport visible;
- solapamiento con header/sticky CTA/overlay persistente;
- ocultación completa por contenido creado por el autor;
- retorno explícito del foco al trigger después de cerrar Explorar;
- el mismo contrato tras 200%/Text Spacing cuando la composición crece.

Pa11y/axe y la mera existencia de `:focus-visible` no sustituyen estas comprobaciones geométricas.

## 4. Secuenciación

La autoridad histórica colocó F.4 después de la deuda de accesibilidad inmediata. F.2 está convirtiendo precisamente Text Resilience en un gate sitewide y puede modificar geometría de componentes bajo estrés.

Por ello no se abre en paralelo un segundo crawler ni se duplica Sitewide Reflow. La implementación de F.4 debe reutilizar el harness browser estabilizado por F.1/F.2 una vez F.2 quede en enforcement.

## 5. Implementación siguiente cuando F.2 cierre

1. Reusar route discovery/harness browser existente.
2. Definir un conjunto pequeño de journeys representativos: shell/Explorar, formulario, herramienta, sticky CTA y cualquier diálogo real.
3. En cada foco, guardar selector/rect/viewport y regiones persistentes que puedan taparlo.
4. Fallar si el target queda enteramente oculto por contenido del autor; mantener además el estándar interno preferente de foco plenamente visible cuando sea razonable.
5. Comprobar que cerrar overlays devuelve el foco al trigger que los abrió.
6. Producir artifact diagnóstico con URL, paso, target y screenshot/rects.
7. Ejecutar también bajo los escenarios F.2 relevantes, sin duplicar su crawler.

## 6. Guardrails

- No añadir otro `outline` global y declarar F.4 terminado.
- No eliminar sticky UI únicamente durante tests.
- No usar `tabindex` positivo para forzar orden.
- No mover foco programáticamente en cada render.
- No crear un segundo crawler sitewide.
- No declarar `VERIFIED_E2E` sin geometría y retorno de foco.

## 7. Estado final

`PARTIAL_COVERAGE · BASE_FOCUS_STYLE_EXISTS · KEYBOARD_JOURNEY_EXISTS · GEOMETRY_AND_RETURN_FOCUS_GAP · SEQUENCE_AFTER_F2 · NO_CODE_YET`

F.4 sigue siendo trabajo válido, pero el alcance exacto es menor y más preciso que el descrito inicialmente: extender el QA browser existente con geometría/obscuration y focus return una vez F.2 sea autoridad estable.