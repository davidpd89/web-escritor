# F.6 · Revalidación de producción — asistente y lector de pantalla

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `PARTIAL_AUDIT · STRONG_AUTOMATED_SEMANTICS_AND_FOCUS_COVERAGE · MANUAL_SCREEN_READER_EVIDENCE_REQUIRED · NO_RUNTIME_CHANGE`

## 1. Qué se revalida

F.6 no autoriza a añadir ARIA por reflejo. La pregunta correcta es si el asistente actual expone una estructura dinámica coherente y si existe un defecto reproducible que justifique cambiarla.

La revisión histórica de #135 ya había corregido la idea original de “añadir `aria-live`” a `PARTIAL_AUDIT`. La inspección de producción confirma que esa corrección sigue siendo la adecuada.

## 2. Runtime real del asistente

La superficie authored de `/asistente/` contiene fallback usable sin JS, pero con scripting activo `assets/assistant.js` transforma el panel en el owner real de la conversación.

El runtime actual crea:

- un transcript `role="log"`;
- `aria-live="polite"` en el log;
- `aria-relevant="additions"`, de forma que las nuevas entradas son el cambio relevante y las retiradas no se convierten por defecto en anuncios;
- un estado breve separado con `role="status"` + `aria-live="polite"`;
- `aria-busy="true|false"` en el formulario durante una consulta;
- labels/nombres accesibles para textarea, enviar y detener;
- Turnstile fuera del árbol accesible mientras funciona como infraestructura antiabuso (`aria-hidden="true"` en su host runtime);
- mensajes añadidos al log sin mover el foco a cada respuesta;
- retorno del foco al textarea al finalizar `submitQuery()`.

No aparece aquí un defecto evidente que justifique añadir otra live region, `role="alert"`, `aria-atomic` global o movimientos de foco adicionales.

## 3. Coherencia con WAI-ARIA

Referencia normativa vigente inspeccionada:

- WAI-ARIA 1.2, `log`: <https://www.w3.org/TR/wai-aria-1.2/#log>
- WAI-ARIA 1.2, `status`: <https://www.w3.org/TR/wai-aria-1.2/#status>
- WAI-ARIA 1.2, `aria-relevant`: <https://www.w3.org/TR/wai-aria-1.2/#aria-relevant>

Puntos relevantes para esta implementación:

- `log` es una live region y tiene `aria-live="polite"` implícito;
- `status` es información consultiva, también con `aria-live="polite"` implícito, y no debe recibir foco solo porque cambie el estado;
- `aria-relevant` permite expresar qué tipos de mutación son semánticamente relevantes para las notificaciones.

El hecho de que el runtime explicite algunos valores implícitos no demuestra por sí mismo un problema. Cambiar o eliminar atributos solo sería correcto después de observar un defecto real en la combinación navegador + tecnología de asistencia.

## 4. Cobertura automatizada que ya existe

`qa/assistant-browser.mjs` ya cubre mucho más que una auditoría estática:

- siete viewports;
- existencia del `data-assistant-log` runtime;
- validación y estados del formulario;
- respuestas locales;
- mock de respuesta remota;
- fallback/error;
- stop/estado busy indirectamente a través del journey;
- CSP/runtime errors;
- no fuga de la consulta cuando el remoto está desactivado;
- navegación por teclado;
- primer Tab al skip link;
- activación de una pregunta sugerida por teclado;
- retorno del foco al textarea después de la respuesta;
- resiliencia de texto;
- fallback no-JS.

Por tanto F.6 no parte de “sin QA”. Lo que falta no debe duplicar ese browser suite.

## 5. Qué NO demuestra Playwright

Un accessibility tree o un DOM correcto no permiten declarar que una experiencia se anuncia bien en un lector de pantalla real.

No existe evidencia registrada en este corte para afirmar que se han ejecutado y superado, por ejemplo:

- NVDA + Firefox/Chrome en Windows;
- VoiceOver + Safari en macOS;
- VoiceOver + Safari en iOS.

No se reconstruye esa evidencia de memoria y no se etiqueta como `VERIFIED_E2E`.

## 6. Matriz manual pendiente

Cuando exista entorno para la auditoría real, registrar por combinación:

| Journey | Qué observar |
|---|---|
| cargar `/asistente/` | nombre/estructura del chat sin anuncio redundante inicial |
| enfocar textarea | label comprensible |
| enviar consulta | busy/loading comprensible sin mover foco innecesariamente |
| respuesta local | una nueva respuesta anunciada una vez y en orden |
| respuesta remota | idem; fuentes navegables y con nombres útiles |
| error/fallback | estado comprensible, sin `alert` agresivo para un fallo recuperable |
| detener | cancelación anunciada sin perder contexto |
| segunda consulta | no releer todo el transcript |
| cerrar cualquier overlay relacionado | retorno de foco correcto al control que lo abrió |

Registrar como mínimo lector, versión, navegador, SO, journey, resultado observado y expected behavior.

## 7. Gate para cualquier cambio futuro

Solo abrir código en F.6 si se reproduce uno de estos defectos:

- respuesta no anunciada;
- respuesta anunciada varias veces;
- relectura del historial completo;
- spam durante actualizaciones incrementales;
- estado de error/loading incomprensible;
- foco perdido o movido a contenido no solicitado;
- control sin nombre accesible;
- orden accesible distinto al conversacional de forma material.

La reparación debe hacerse en el owner (`assets/assistant.js`, markup o componente que corresponda) y añadir una regresión automatizable cuando exista señal estable. No se crea un framework paralelo de accesibilidad.

## 8. Qué no hacer

- No añadir `aria-live` a cada mensaje.
- No añadir `role="alert"` a respuestas normales.
- No mover el foco a cada respuesta.
- No usar `aria-atomic="true"` sobre todo el transcript sin evidencia.
- No considerar Pa11y/axe/Playwright equivalentes a una prueba NVDA/VoiceOver.
- No almacenar prompts ni nueva PII para realizar esta auditoría.

## 9. Relación con F.1/F.2/F.4

- F.1 ya protege geometría de targets de forma sitewide.
- F.2 protege el asistente bajo Resize Text 200% + Text Spacing cuando esa PR se integre.
- F.4 es el owner transversal de focus visible / Focus Not Obscured y debe absorber cualquier defecto geométrico de foco común al shell, en vez de duplicarlo dentro de F.6.

## 10. Cierre

La revalidación cambia la lectura práctica de F.6: el asistente actual ya tiene una arquitectura ARIA razonable y una cobertura browser fuerte. El trabajo pendiente es **evidencia con tecnologías de asistencia reales**, no una nueva capa de atributos.

Hasta que exista un defecto reproducible con lector de pantalla, el resultado correcto es `NO_RUNTIME_CHANGE`.
