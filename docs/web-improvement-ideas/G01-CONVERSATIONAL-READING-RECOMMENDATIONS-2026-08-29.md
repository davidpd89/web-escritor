# G.1 · Recomendación de lectura conversacional

**Estado histórico final de PR #135:** `PARTIAL_AUDIT`  
**Regla central:** medir primero el asistente existente; ampliar corpus/routing solo ante fallos reproducibles.  
**Grounding:** únicamente catálogo, obras y recomendaciones reales del sitio; negativos y no-hallucination obligatorios.  
**Naturaleza de esta PR:** documentación; no cambia modelo, Worker, corpus ni UI.

## 1. Hipótesis original

G.1 proponía extender el asistente existente para responder preguntas del tipo “¿qué debería leer si me gustó X?”, reutilizando `recomendaciones/` como base y sin inventar títulos/datos fuera del catálogo real.

La investigación rechazó tratar esa frase como una orden de construir una nueva capacidad. El asistente ya existía, Pagefind/búsqueda local ya existía y el primer paso correcto era saber **si realmente fallaba** en esas consultas.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis de extensión | Añadir recomendación conversacional grounded. |
| Revisión 108/108 | `PARTIAL_AUDIT` | Benchmark de 10–20 consultas “qué leer”; cambiar corpus/routing solo si hay fallo reproducible. |
| Matriz | `PILOTAR` | Exclusivamente grounded; tests negativos y no-hallucination. |
| Repo override D.5 | Pagefind `ALREADY_COVERED` | El asistente ya consume Pagefind con fallback local; no añadir embeddings/vector DB por defecto. |
| Autoridad final | `PARTIAL_AUDIT` | Mantiene la recomendación como capacidad condicionada a evaluación real. |
| Revalidación independiente | mantenido | Cambios IA deben ser grounded/human-reviewed y no abrir retención de prompts. |

La traducción de `PILOTAR` de la matriz al vocabulario final es `PARTIAL_AUDIT`: no hay feature aprobada hasta que el benchmark encuentre un gap.

## 3. Qué debe medir el benchmark

La evaluación histórica propuesta era pequeña y decisional, aproximadamente 10–20 consultas. Debe cubrir al menos:

### Positivos

- “Me gustó la fantasía de portales, ¿qué puedo leer?”
- “Quiero empezar por un libro de David Porto, ¿cuál encaja si busco X?”
- “¿Qué recomendáis parecido a Samuel?”
- “¿Hay algo más realista/emocional que fantasía?”
- preguntas que puedan resolverse con `/libros/`, `/recomendaciones/`, `/empieza-aqui/` y contenido factual del sitio.

### Negativos / límites

- pedir una obra que no existe;
- atribuir a David un libro ajeno;
- preguntar por una secuela inexistente;
- pedir una edición/formato/edad/reseña que el sitio no confirma;
- solicitar “el mejor libro” sin criterios suficientes;
- recomendar fuera del corpus cuando no existe una fuente autorizada.

### Métricas cualitativas

- factualidad;
- cita/fuente correcta;
- utilidad de la recomendación;
- capacidad de decir “no tengo información suficiente”;
- no alucinar catálogo, argumentos, edades, disponibilidad o relaciones entre libros;
- dirigir a una URL realmente existente;
- accesibilidad/latencia del journey si se activa capa IA.

## 4. Estado del repositorio que condiciona G.1

#135 encontró que Pagefind no era un experimento pendiente: `scripts/build-pagefind-index.py`, tests, índice versionado y consumo desde `assets/assistant.js` ya formaban una autoridad real. Por eso D.5 terminó `ALREADY_COVERED`.

G.1 debe apoyarse en esa infraestructura si el benchmark demuestra que el problema es recuperación/relevancia. No debe saltar directamente a:

- embeddings;
- vector database;
- API/modelo adicional;
- crawler paralelo;
- un segundo chatbot.

Primero hay que localizar el fallo: corpus insuficiente, query rewriting, ranking, prompting, grounding, UI o simplemente una pregunta que el sitio no tiene datos para responder.

## 5. Grounding y canon

La recomendación solo puede usar hechos realmente presentes en autoridades del sitio:

- catálogo/registry de obras;
- fichas de libro;
- recomendaciones editoriales publicadas;
- `/empieza-aqui/` cuando sea relevante;
- Cuaderno si contiene comparaciones/criterios auténticos;
- estado factual de formatos/venta, si está publicado y vigente.

No se autoriza a inferir:

- que Samuel y Manecillas son saga;
- edades recomendadas no publicadas;
- comparables externos inventados;
- disponibilidad comercial no verificada;
- “si te gustó X te encantará Y” como hecho objetivo sin criterio editorial.

## 6. Privacidad y analítica

G.1 no autoriza almacenar conversaciones para mejorar el sistema. Esa decisión pertenece a G.5/privacidad y requiere minimización, retención y tratamiento de PII definidos.

Un benchmark puede ejecutarse con un set de prompts versionado y sintético/curado, sin capturar conversaciones reales de usuarios.

## 7. Plan de auditoría/piloto

1. Congelar 10–20 prompts con expected facts/sources y negativos.
2. Ejecutarlos contra el asistente vigente sin cambiar código.
3. Clasificar cada fallo: retrieval, grounding, hallucination, routing, UI/a11y, falta de contenido fuente.
4. Si todo funciona suficientemente bien, cerrar G.1 como `NO_ACTION/ALREADY_SUFFICIENT` para ese corte.
5. Si aparece un gap reproducible, modificar **la autoridad existente** mínima necesaria.
6. Volver a ejecutar el benchmark completo y comprobar que no se degradan negativos.
7. Cualquier modificación del asistente debe pasar F.6 (screen reader), F.4 (focus), performance/CSP y privacidad aplicables.

## 8. Qué no hacer

- No añadir embeddings/vector DB sin benchmark.
- No ampliar el corpus con texto generado para que el asistente “tenga más que decir”.
- No dejar que el modelo recomiende libros/ediciones fuera de fuentes permitidas.
- No usar una respuesta fluida como sustituto de factualidad/citas.
- No guardar prompts reales por defecto.
- No construir un quiz conversacional duplicando D.6 rechazado.
- No crear una nueva landing SEO para cada recomendación generada.
- No marcar la feature implementada porque el asistente ya exista: G.1 es una capacidad específica que debe evaluarse.

## 9. Definition of Done del `PARTIAL_AUDIT`

- [ ] set versionado de 10–20 consultas representativas;
- [ ] expected facts/sources y negativos definidos;
- [ ] baseline del asistente actual registrado;
- [ ] cada fallo clasificado y reproducible;
- [ ] no hay alucinaciones de catálogo/formatos/relaciones en el set aprobado;
- [ ] las recomendaciones enlazan fuentes reales;
- [ ] cualquier cambio de corpus/routing se justifica por un fallo concreto;
- [ ] no se introduce infraestructura IA adicional sin necesidad demostrada;
- [ ] no se añade retención de prompts/PII;
- [ ] si hay cambio de UI/assistant, se revalida F.6/F.4.

## 10. Relación con otras ideas

- **D.5:** Pagefind/búsqueda ya es autoridad existente; extender, no duplicar.
- **D.6:** quiz general rechazado; G.1 no debe recrearlo con apariencia conversacional.
- **C.3/G.5:** preguntas reales pueden inspirar contenido solo bajo la política específica de privacidad/agregación.
- **F.6:** cualquier respuesta dinámica nueva entra en screen-reader audit.
- **B.3/B.8:** no reescribir contenido para “alimentar IA” si no mejora la pieza humana.

## 11. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `PARTIAL_AUDIT`, benchmark 10–20.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — principios de IA/search y people-first.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — asistente y búsqueda existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y `...OVERRIDES-REPO...` — Pagefind encontrado como autoridad real.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `PILOTAR`, grounding/negativos.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no abre un backend IA nuevo para G.1.
- `data/web-improvement-decisions-2026-08-28.json` — `PARTIAL_AUDIT` final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — grounding + negatives/no-hallucination.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — status mantenido, sin nueva retención de prompts.
- pasadas posteriores — revisadas; no cambian el trigger audit-first.

## 12. Cierre

G.1 no es “añadir IA de recomendaciones”. Es comprobar si el asistente actual resuelve una necesidad concreta sin inventar nada. Solo un fallo medido justifica cambiar el corpus o routing; y el cambio mínimo debe reutilizar la infraestructura existente.