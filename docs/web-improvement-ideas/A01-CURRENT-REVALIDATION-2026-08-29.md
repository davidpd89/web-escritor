# A.1 · Revalidación actual 2026-08-29

## Decisión cerrada

**No desarrollar una segunda arquitectura de topical authority.** La capacidad base está ya cubierta por `data/topic-collections.json`, `scripts/build-topic-collections.py` y `tests/test-topic-collections.py`.

## Evidencia actual

- `fantasia-de-portales` está publicada como colección `ready` con tres piezas sustanciales.
- `como-construi-noveris` permanece `draft` con dos piezas y declara explícitamente que no se fuerza una tercera para superar el gate editorial.
- El builder valida URLs internas, duplicados, canonical, noindex y existencia real de los miembros.
- El test protege el mínimo de tres piezas para una colección `ready` y el orden semántico de las series.

## Investigación 2026

Google Search Central publicó en 2026 una guía específica para funciones generativas en Search que prioriza contenido único, útil y **no commodity**; no prescribe pillar pages, un número de satélites ni un “topical authority score”.

Fuente primaria:
- https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

El core update de Discover de febrero de 2026 añade que Google identifica experiencia **tema por tema** y favorece contenido profundo, original y oportuno. Eso respalda profundidad editorial real, no taxonomías artificiales.

Fuente primaria:
- https://developers.google.com/search/blog/2026/02/discover-core-update

Google también mantiene que toda página importante debe ser enlazable desde otra página y que no existe un número mágico de enlaces.

Fuente primaria:
- https://developers.google.com/search/docs/crawling-indexing/links-crawlable

## Regla de reapertura

A.1 solo se reabre si existe evidencia medible de un hueco real —GSC/Bing, intención o grafo— que **no pueda resolverse extendiendo** la autoridad existente.

No autorizados:
- segundo builder o segunda taxonomía;
- nuevas URLs por completar clusters;
- número mínimo de satélites como objetivo SEO;
- scores propietarios tratados como métrica de Google;
- contenido generado para rellenar una estructura.

## Estado para merge

`ALREADY_COVERED`. Esta PR debe funcionar como guardrail documental y de investigación; no necesita runtime nuevo.