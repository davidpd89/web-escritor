# A.2 · Revalidación actual 2026-08-29

## Decisión cerrada

**No crear nuevas páginas pilar paralelas.** Los hubs canónicos existentes ya cumplen la función legítima de orientación y consolidación editorial.

## Evidencia actual de `main`

`data/content-registry.json` mantiene una jerarquía explícita:

- `works-hub` → `/libros/`;
- `work-manecillas` → `/las-manecillas-del-recuerdo/`;
- `work-samuel` → `/libros/samuel-entre-mundos/`;
- recursos de Samuel como Noveris, fragmento y clubes cuelgan de la obra/hub correspondiente;
- `notebook-hub` y `notebook-topics` separan contenido editorial de obra.

`check-global-discoverability.py` valida además que las obras canónicas sigan siendo públicas, indexables, aparezcan en sitemap, mapa del sitio, footer y tengan enlace directo desde el hub de Obras.

## Investigación 2026

Google mantiene que las páginas importantes deben recibir al menos un enlace rastreable desde otra página y que los enlaces deben aportar contexto al lector. No existe una recomendación oficial de crear una segunda “pillar page” cuando ya hay una URL canónica que cumple esa función.

- https://developers.google.com/search/docs/crawling-indexing/links-crawlable

La guía 2026 para Search con IA prioriza contenido único/no commodity y organización útil para personas; crear una URL adicional que repita un hub existente iría en dirección contraria.

- https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

## Regla de reapertura

Solo se modifica un hub existente si una auditoría reproduce uno de estos fallos:

1. una entidad importante no es alcanzable mediante enlaces HTML rastreables;
2. la relación padre/hub del registry es incorrecta;
3. falta contexto humano suficiente para entender qué contiene el hub;
4. sitemap/mapa/footer contradicen la autoridad canónica.

No se autoriza una nueva URL únicamente para duplicar información ya contenida en Samuel, Manecillas, Noveris u Obras.

## Estado para merge

`ALREADY_COVERED`. La PR queda como guardrail de arquitectura; no requiere runtime nuevo mientras los contratos actuales pasen.