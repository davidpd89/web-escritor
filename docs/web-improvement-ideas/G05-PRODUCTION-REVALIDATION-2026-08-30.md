# G.5 · Revalidación de producción — analítica de preguntas del asistente

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `DEFER · REMOTE_OFF · NO_RAW_QUERY_LOGGING · DATA_MINIMIZATION_FIRST · NO_CODE`

## Estado real

`assets/assistant-config.js` mantiene `remoteEnabled: false`. El modo remoto requiere además `ASSISTANT_ENABLED=true` en el Worker, por lo que el producto público actual no necesita una capa de almacenamiento de consultas para funcionar.

No se ha localizado en el cliente una autoridad editorial que conserve texto de preguntas para analítica. Esto es coherente con la postura privacy-first del proyecto y no constituye un gap.

## Qué problema intentaba resolver G.5

Aprender qué preguntan los visitantes podría descubrir:

- intents no cubiertos;
- contenido difícil de encontrar;
- rutas canónicas que el asistente no resuelve;
- necesidades editoriales repetidas.

Pero almacenar prompts/conversaciones crudas crea una superficie de datos personales desproporcionada antes de demostrar que el dato es necesario.

## Jerarquía de evidencia aprobada

Si en el futuro se necesita medir demanda, priorizar:

1. contadores de intent normalizado;
2. éxito/fallo de routing;
3. destino canónico seleccionado;
4. categoría de error/fallback;
5. métricas agregadas sin texto libre;
6. solo como último recurso, muestra temporal de consultas minimizadas y con un protocolo explícito.

## Gate antes de almacenar texto

Debe existir una decisión documentada sobre:

- finalidad concreta;
- campos exactos;
- PII/redaction;
- retención corta;
- acceso;
- proveedor;
- transferencias;
- disclosure de privacidad;
- borrado;
- volumen mínimo que justifique el riesgo;
- criterio de cierre del experimento.

No guardar una consulta «por si luego resulta útil».

## Relación con G.1

G.1 ya demostró una alternativa preferible: un benchmark determinista detectó un fallo de routing de recomendaciones sin conservar prompts reales de usuarios. Este patrón debe seguir siendo la primera opción para mejorar cobertura.

## No implementar

- No raw prompt logging.
- No session replay del asistente.
- No historial persistente en localStorage como sustituto de analítica.
- No envío del texto a GoatCounter/Metricool.
- No vectorización/embeddings de conversaciones.
- No panel de «preguntas reales» sin consentimiento/minimización.

## Trigger de reapertura

Solo si un objetivo editorial medible no puede resolverse con benchmarks, intents agregados o routing telemetry no textual.

## Cierre

G.5 permanece `DEFER`: el beneficio potencial no supera todavía el coste de privacidad. El siguiente paso, si aparece necesidad, es diseñar una métrica agregada; no empezar almacenando conversaciones.