# G.1 · Revalidación de producción — recomendación conversacional

**Fecha:** 2026-08-30  
**Base revalidada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `IMPLEMENTED_IN_PR · MEASURED_ROUTING_GAP_FIXED · DETERMINISTIC_LOCAL_ROUTING · NO_VECTOR_DB · REMOTE_OFF`

## 1. Qué se midió antes de cambiar nada

La hipótesis histórica de G.1 se convirtió primero en un benchmark browser-based de 12 consultas reales de intención lectora:

- 4 consultas genéricas de recomendación;
- 4 consultas específicas de portal fantasy;
- 4 consultas específicas de fantasía con magia que implica coste/consecuencias.

El benchmark fuerza el asistente remoto a OFF y cuenta cualquier POST remoto como defecto. La primera ejecución dio:

- total: `5/12`;
- genérico: `4/4`;
- portal fantasy: `0/4`;
- magia con coste: `1/4`;
- `remotePosts: 0`.

Por tanto había un fallo reproducible y suficientemente acotado para actuar.

## 2. Causa raíz

No faltaba búsqueda semántica, embeddings ni una base vectorial.

La causa era determinista y local:

1. `resolveLocalAnswer()` reconocía de forma demasiado amplia la intención genérica de recomendaciones y podía resolverla antes de que la búsqueda local afinara el destino;
2. `data/assistant-source-registry.json` no contenía las dos páginas de recomendaciones específicas que ya eran contenido público canónico del sitio.

Las páginas ya existían en `data/content-registry.json` con IDs canónicos:

- `recommend-portal-es` → `/recomendaciones/portal-fantasy-espanol/`;
- `recommend-magic-cost` → `/recomendaciones/magia-con-coste/`.

## 3. Corrección aplicada

La PR extiende el owner existente, sin crear otro motor:

- registra esas dos fuentes en `data/assistant-source-registry.json` reutilizando los IDs canónicos del content registry;
- regenera `assets/assistant-source-registry.js` mediante el contrato existente;
- añade intents locales específicos para portal fantasy y magia con coste antes del fallback genérico;
- conserva `/recomendaciones/` como destino de la intención genérica;
- añade `tests/test-assistant-recommendation-routing.mjs`;
- convierte `qa/assistant-recommendation-benchmark.mjs` en gate `enforce` dentro de `Assistant hardening QA`.

Un intento intermedio de inventar IDs propios fue rechazado correctamente por `Required merge gate`. Se corrigió reutilizando la identidad canónica ya existente; no se debilitó el contrato.

## 4. Resultado medido final

El HEAD funcional validado por `Assistant hardening QA` devuelve:

- total: `12/12`;
- genérico: `4/4`;
- portal fantasy: `4/4`;
- magia con coste: `4/4`;
- `rate: 1`;
- `remotePosts: 0`;
- modo: `enforce`.

También pasan:

- paridad del registry generado;
- contrato del asistente;
- tests unitarios específicos G.1;
- Pagefind real search;
- navegación desde fuentes;
- browser QA del asistente;
- Required merge gate;
- Tool engine tests;
- CSP, runtime, analytics e índices.

## 5. Lo que G.1 NO introduce

- no vector DB;
- no embeddings;
- no nuevo proveedor IA;
- no activación del Worker remoto;
- no retención de prompts;
- no recomendaciones inventadas fuera de páginas reales;
- no catálogo paralelo al `content-registry`.

## 6. Guardrail de mantenimiento

Una nueva categoría conversacional solo debe añadirse cuando concurran las dos condiciones:

1. exista una página/fuente pública canónica real;
2. un benchmark reproduzca un fallo que el routing/búsqueda actual no resuelva.

El benchmark debe permanecer en `enforce` y con `remotePosts=0` para esta capacidad local.

## 7. Cierre

G.1 ya no es una hipótesis ni un `PARTIAL_AUDIT`: se encontró un fallo medido, se corrigió en la autoridad existente y se dejó protegido por regresión. La mejora procede de routing grounded y fuentes canónicas, no de aumentar complejidad de IA.
