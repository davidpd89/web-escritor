# F.6 · Auditoría de lector de pantalla del asistente

**Estado histórico final de PR #135:** `PARTIAL_AUDIT`  
**Corrección material:** pasó de `IMPLEMENT_NOW` en revisiones intermedias a `PARTIAL_AUDIT` en la autoridad final.  
**Motivo:** el asistente ya tenía regiones live/status y UI dinámica; añadir ARIA a ciegas podía empeorar la experiencia.  
**Naturaleza de esta PR:** documentación; no cambia markup/ARIA/JS.

## 1. Hipótesis original

F.6 proponía verificar específicamente que el widget/asistente conversacional anunciara correctamente los mensajes dinámicos, inicialmente con énfasis en `aria-live`.

La premisa de accesibilidad era válida, pero la investigación fue corrigiendo la solución: el problema no era “falta `aria-live`”, sino **demostrar el journey real con accessibility tree y lector de pantalla antes de tocar ARIA**.

## 2. Evolución completa y contradicción que debe preservarse

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Verificar anuncios de mensajes del asistente vía `aria-live`. |
| Revisión 108/108 | `IMPLEMENT_NOW` | Auditar role/log, live regions, `aria-busy`, foco, errores y respuesta incremental. |
| Matriz operativa | `IMPLEMENTAR` | Alta prioridad: orden de foco, nombres, loading/error, cierre/dialog, mensajes dinámicos. |
| Blueprint W3 | **auditar antes de añadir ARIA** | El markup ya contenía regiones status/live; añadir más podía duplicar anuncios. |
| Orden neto de #135 | detrás de F.2/R.1/F.1/contraste/Pa11y | Sigue siendo importante, pero después de contratos base. |
| Autoridad final | `PARTIAL_AUDIT` | Cambio material: lector de pantalla real primero; código solo ante fallo reproducible. |
| Revalidación independiente | mantenido | Mantiene F.6 como auditoría, no implementación presupuesta. |

La autoridad final prevalece. Cualquier documento que presente F.6 hoy como `IMPLEMENT_NOW` sin esta corrección está incompleto.

## 3. Evidencia del repositorio

El blueprint histórico ya observó que `asistente/index.html` y `assets/assistant.js` contenían semántica/UI dinámica suficiente para invalidar la suposición “no hay live region”.

La revalidación contra `main@291c8c677aaa7df635142687d1a6848e80ffcaa2` confirma que la superficie actual sigue teniendo:

- botón de apertura del asistente en el shell;
- formularios y controles etiquetados;
- regiones `role="status"` / `aria-live="polite"` en partes dinámicas del shell/newsletter;
- UI del asistente con submit/stop, estados y contenido dinámico gestionado por JS;
- diálogo Explorar con semántica y control de foco propios.

Esto no prueba que el asistente sea perfecto con NVDA/VoiceOver. Prueba precisamente que **no se debe añadir otra capa ARIA sin ejecutar el journey**.

## 4. Blueprint W3 recuperado

Inspección browser inicial de regiones dinámicas:

```js
const live = await page
  .locator('[aria-live], [role="status"], [role="log"]')
  .evaluateAll(nodes => nodes.map(el => ({
    role: el.getAttribute('role'),
    live: el.getAttribute('aria-live'),
    atomic: el.getAttribute('aria-atomic'),
    text: (el.textContent || '').trim().slice(0, 120)
  })));
```

Journey mínimo histórico:

1. teclado abre el asistente;
2. foco entra donde corresponde;
3. usuario formula consulta;
4. aparece estado de carga;
5. llega respuesta;
6. se reproduce error/retry;
7. se cierra la superficie;
8. foco vuelve al trigger apropiado.

Pruebas manuales recomendadas por #135 cuando exista entorno:

- NVDA + Firefox/Chrome en Windows;
- VoiceOver + Safari en macOS/iOS.

## 5. Qué debe observar la auditoría

### Apertura/cierre

- nombre y rol del trigger;
- `aria-expanded`/estado cuando corresponda;
- destino de foco al abrir;
- no quedar atrapado fuera de la superficie;
- retorno de foco al cerrar.

### Formulario

- label/instrucciones del campo;
- submit/stop distinguibles;
- estado disabled/loading comprensible;
- errores asociados al campo/acción correcta.

### Respuesta dinámica

- un mensaje nuevo se anuncia una vez, no dos;
- no se relee todo el historial ante cada token/cambio;
- streaming/incremental no produce una tormenta de anuncios;
- la transición loading → respuesta es comprensible;
- las citas/fuentes tienen nombres y destinos entendibles;
- el orden accesible coincide con el orden conversacional.

### Error/retry

- error anunciado de forma no intrusiva;
- retry accionable con teclado;
- no se pierde la consulta/estado sin explicación;
- Turnstile u otras dependencias no bloquean silenciosamente.

## 6. Por qué `PARTIAL_AUDIT` es más correcto que `IMPLEMENT_NOW`

Un estado `IMPLEMENT_NOW` sugería que ya conocíamos el defecto y la reparación. W3 descubrió lo contrario: el sitio ya tenía semántica relacionada y un cambio automático podía introducir:

- anuncios duplicados por `role=status` + `aria-live` redundantes;
- relectura completa del contenido durante streaming;
- `aria-atomic` demasiado agresivo;
- cambios de foco que interrumpen al lector;
- conflicto entre el asistente y el diálogo/shell.

Por tanto, la primera unidad de trabajo es **evidencia**. Solo después se abre una reparación concreta.

## 7. Qué no hacer

- No añadir `aria-live="polite"` a cada mensaje por reflejo.
- No usar `role="alert"` para respuestas normales.
- No mover foco a cada respuesta/token.
- No hacer `aria-atomic="true"` sobre todo el transcript sin prueba.
- No considerar axe/Pa11y verde como prueba de experiencia screen-reader.
- No simular lector de pantalla únicamente leyendo el accessibility tree.
- No marcar `VERIFIED_E2E` sin registrar lector/navegador/journey.
- No retener prompts/conversaciones para esta auditoría; F.6 no autoriza nueva analítica.

## 8. Plan de auditoría

1. Inventariar live/status/log actuales y su ownership.
2. Ejecutar journey keyboard con browser automation y accessibility snapshot.
3. Probar loading, respuesta corta/larga, fuentes, error, stop/retry y cierre.
4. Ejecutar NVDA y VoiceOver en una muestra representativa.
5. Documentar exactamente el comportamiento observado y el expected behavior.
6. Solo si hay defecto reproducible, modificar el elemento/JS propietario.
7. Añadir regresión automatizable para la parte estable; conservar manual screen-reader como evidencia donde no haya automatización fiable.

## 9. Definition of Done

F.6 no queda cerrada por añadir atributos. Queda cerrada cuando:

- [ ] existe registro de browser + screen reader + versión/entorno;
- [ ] apertura/cierre y retorno de foco son correctos;
- [ ] loading/error/retry se anuncian con claridad;
- [ ] cada respuesta se anuncia sin duplicados ni spam incremental;
- [ ] fuentes/citas y controles tienen nombres útiles;
- [ ] el journey puede completarse solo con teclado/lector;
- [ ] cualquier reparación corresponde a un fallo reproducido;
- [ ] las regresiones automatizables se cubren sin crear un segundo framework;
- [ ] Pa11y/axe se conservan como capas complementarias;
- [ ] no se almacena nueva PII/prompts por realizar la auditoría.

## 10. Relación con otras ideas

- **F.4:** comparte foco, dialogs y keyboard journey; reutilizar la autoridad global.
- **F.1:** botones/controles del asistente deben cumplir target size.
- **F.2:** el asistente debe sobrevivir a 200%/Text Spacing.
- **G.1:** cualquier ampliación conversacional debe pasar el mismo contrato F.6.
- **G.5:** analítica de preguntas es otra decisión de privacidad; F.6 no la autoriza.

## 11. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis `aria-live`.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — estado intermedio `IMPLEMENT_NOW`.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — accesibilidad dinámica.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — asistente existente.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` / repo overrides — revisados.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — intermedio `IMPLEMENTAR`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W3: auditar antes de añadir ARIA.
- `data/web-improvement-decisions-2026-08-28.json` — final `PARTIAL_AUDIT`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — corrección material a auditoría real de lector de pantalla.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — status mantenido.
- orden neto de #135 — F.6 se mantiene en la ola de accesibilidad después de contratos más transversales.
- `main@291c8c.../asistente/index.html` — evidencia actual de semántica dinámica ya existente.

## 12. Cierre

F.6 pasó de “hay que añadir/ajustar ARIA” a una formulación más rigurosa: **primero escuchar cómo funciona el asistente con lectores de pantalla reales; después reparar únicamente lo que falle**. Esa transición es parte esencial de la información de #135.