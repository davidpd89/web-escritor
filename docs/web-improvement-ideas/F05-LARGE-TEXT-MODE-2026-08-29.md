# F.5 · Modo “texto grande” propio

**Estado histórico final de PR #135:** `REJECT`  
**Alternativa correcta:** hacer que zoom, Resize Text y ajustes nativos funcionen sin pérdida de contenido/funcionalidad.  
**Naturaleza de esta PR:** documentación; no añade toggle ni `localStorage`.

## 1. Hipótesis original

La idea inicial proponía un control persistente en la UI para aumentar el texto, independiente del zoom del navegador, guardando la preferencia en `localStorage` para lectores con baja visión.

Parecía una mejora inclusiva de bajo coste, pero la revisión de #135 concluyó lo contrario: añadía un **segundo sistema de tamaño de texto** que la web tendría que mantener además de las capacidades nativas del navegador/SO y podía ocultar el problema real si la interfaz no soportaba bien el aumento nativo.

## 2. Evolución de la decisión

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Toggle persistente de texto grande. |
| Revisión 108/108 | `REJECT` | No crear un modo propio para compensar una web que debe responder correctamente a zoom/text settings nativos. |
| Matriz | `DESCARTAR AHORA` | Multiplica estados a mantener y duplica funciones del user agent. |
| F.2 / evidencia #133 | alternativa demostrada | El problema real es la resiliencia a `font-size:200%` + Text Spacing, no ofrecer una ruta paralela. |
| Autoridad final | `REJECT` | Invertir en reflow nativo hasta 200% sin pérdida. |
| Revalidación independiente | mantenido | F.5 correctamente rechazado. |

## 3. Por qué se rechaza

Un toggle propio obliga a mantener combinaciones adicionales:

- tamaño normal/grande × desktop/mobile;
- tamaño propio × zoom del navegador;
- tamaño propio × preferencias del SO;
- tamaño propio × Text Spacing;
- tamaño propio × dialogs/sticky header/tools/forms;
- persistencia/localStorage y reset;
- posibles efectos sobre CLS, truncado y target-size.

Nada de eso sustituye la obligación base de que el sitio siga funcionando cuando la persona usa las herramientas de accesibilidad de su navegador.

Además, un “modo accesible” separado puede producir una experiencia de segunda clase: el sitio principal continúa frágil y solo una rama visual recibe mantenimiento.

## 4. Alternativa que #135 eligió

El trabajo equivalente que sí aporta es **F.2**:

- `font-size:200%` real;
- WCAG Text Spacing;
- navegador y viewports representativos;
- detección de recorte/overflow/solape/pérdida funcional;
- reparación del layout base;
- artifacts/offenders en CI.

F.1 y F.4 complementan el mismo objetivo: los targets y el foco deben seguir siendo utilizables cuando el texto crece.

## 5. Cuándo podría reabrirse

`REJECT` describe el proyecto actual, no una prohibición eterna. Solo tendría sentido reevaluar una preferencia propia si aparece evidencia que las capacidades nativas no pueden satisfacer y existe un requerimiento de producto/accesibilidad específico, por ejemplo:

- investigación con usuarios demuestra una necesidad persistente no resuelta por zoom/settings nativos;
- la solución puede basarse en tokens tipográficos sin crear layouts paralelos;
- se demuestra interoperabilidad con zoom y reflow;
- existe una política clara de persistencia/minimización;
- el coste de QA adicional está justificado.

Ese futuro trigger abriría una **nueva evaluación**, no convierte F.5 hoy en `DEFER`.

## 6. Qué no hacer

- No añadir `A+ / A-` por convención de webs “accesibles”.
- No usar JavaScript para escalar toda la página con `transform:scale()`.
- No guardar una preferencia en localStorage sin necesidad clara.
- No mantener estilos `large-text.css` paralelos por página.
- No usar el modo propio como excusa para fallos a 200% nativo.
- No ocultar texto/CTAs en la versión grande para que encaje.
- No reetiquetar la idea como `DEFER` solo porque quizá pueda ser útil algún día: la autoridad final es `REJECT` con triggers de reevaluación.

## 7. Definition of Done de F.5

Como idea rechazada, F.5 se cierra cuando:

- [ ] no se crea un toggle de texto grande propio;
- [ ] las necesidades que motivaron la idea quedan transferidas a F.2/F.1/F.4;
- [ ] cualquier futuro pedido de preferencia tipográfica debe presentar evidencia nueva;
- [ ] no quedan docs que llamen al modo propio una tarea pendiente aprobada;
- [ ] la web se evalúa a 200% y Text Spacing en su layout normal.

## 8. Relación con otras ideas

- **F.2:** sustituto técnico principal y prioridad superior.
- **F.1:** targets táctiles deben sobrevivir a ampliación de texto.
- **F.4:** foco visible/no-obscured en layouts ampliados.
- **D.2:** mismo principio de no construir un Reader Mode para compensar la experiencia base.
- **D.8:** otro toggle visual persistente diferido; no mezclar decisiones ni crear un panel de preferencias por acumulación de features.

## 9. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — propuesta original de toggle + localStorage.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `REJECT` y alternativa nativa.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — Resize Text/Text Spacing.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — reflow/QA existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y `...OVERRIDES-REPO...` — revisados, sin revocación del rechazo.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `DESCARTAR AHORA`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W1/F.2 como trabajo neto; F.5 no recibe blueprint propio.
- `data/web-improvement-decisions-2026-08-28.json` — `REJECT`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — “hacer que zoom/ajustes nativos funcionen hasta 200%”.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — rechazo mantenido.
- evidencia #133 — demuestra la utilidad de arreglar el layout base bajo 200%.
- pasadas posteriores — revisadas; ninguna aporta un trigger nuevo que reabra F.5.

## 10. Cierre

F.5 se descarta precisamente por accesibilidad: el objetivo no es ofrecer una versión especial de la web, sino conseguir que la web normal tolere correctamente las herramientas de ampliación que el usuario ya controla.