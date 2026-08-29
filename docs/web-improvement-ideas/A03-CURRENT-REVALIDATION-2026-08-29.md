# A.3 · Revalidación actual 2026-08-29

## Decisión cerrada

**No crear otro crawler de enlazado interno.** La autoridad correcta es el conjunto formado por `scripts/check-internal-graph.py` y `scripts/check-global-discoverability.py`.

## Evidencia actual

`check-internal-graph.py` ya detecta:

- enlaces internos rotos;
- páginas indexables huérfanas;
- canonicals ausentes;
- colisiones de canonical;
- exclusión explícita de assets, utilidades y páginas `noindex`.

`check-global-discoverability.py` añade controles de arquitectura que el grafo genérico no debe duplicar:

- paridad entre `content-registry` y sitemap;
- rutas públicas vs gated/noindex;
- mapa del sitio humano;
- navegación global;
- presencia y accesibilidad de Obras/Manecillas/Samuel.

## Investigación actual

Google sigue recomendando enlaces `<a href>` rastreables, contexto descriptivo y que toda página importante reciba al menos un enlace desde otra página del sitio. También dice expresamente que no existe una cantidad ideal “mágica” de enlaces.

Fuente primaria:
- https://developers.google.com/search/docs/crawling-indexing/links-crawlable

## Regla de extensión

Solo se modifica el checker existente cuando aparezca un fallo reproducible que no detecte hoy y exista un consumidor claro de la nueva señal. Ejemplos válidos:

- distinguir enlaces de navegación global y enlaces contextuales si una decisión editorial depende de esa diferencia;
- hacer obligatorio un enlace contextual para una familia explícitamente marcada como `discoverabilityRequired`;
- emitir JSON si un proceso real lo consume.

No válidos:
- segundo crawler;
- score propietario de “link equity”;
- número mínimo de enlaces por URL;
- añadir enlaces sin utilidad humana solo para modificar el grafo.

## Estado para merge

`ALREADY_COVERED STRONGLY`. Mantener y extender la autoridad actual es mejor que reemplazarla.