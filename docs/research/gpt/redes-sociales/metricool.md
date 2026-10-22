# Investigación GPT — Fuente agregada Metricool (22/10/2026)

**PR hija de #699.** Rama basada en research/gpt-social-dashboard-2026-10-22. Solo análisis y código de referencia, no instalado ni ejecutado; sin Actions ni merge.

## Evidencia REAL de la cuenta conectada (22/10/2026)
El conector Metricool reconoce una marca con redes Bluesky, Threads, Instagram, Facebook, TikTok, Pinterest, YouTube y otros canales; el acceso de lectura respondió con series diarias del 01–21 de octubre. Se comprobaron campos con números y algunos NULL, incluidos datos ausentes de X/LinkedIn. No escribir IDs internos, tokens ni series privadas en el sitio público. **Importante:** tener conector ChatGPT no prueba acceso API REST automático para GitHub Actions; esta diferencia es bloqueo de integración, no de diseño.

Campos actuales del catálogo del conector (verificados mediante getAnalyticsAvailableMetrics, no suponer API HTTP equivalente):
- Bluesky BKEV01 followers (LAST).
- Threads THEV01 followers (LAST), THEV05 interactions SUM, THEV06 views SUM.
- Instagram IGEV01 followers LAST, IGEV05 views SUM; reach IGEV06 NO se suma a views.
- Facebook FBEV17 fbFollowers LAST, FBEV49 pageMediaView SUM; FBEV02 pageImpressions está DEPRECATED.
- TikTok TKEV07 followers LAST, TKEV02 views SUM.
- Pinterest PIEV09 followers LAST, PIEV01 impressions SUM, PIEV06 outbound clicks SUM.
- X TTEV01 followers LAST, TTEV11 impressions SUM si hay datos.
- YouTube YTEV01 subscribers LAST, YTEV02 videoViews SUM.
- LinkedIn LIEV01 followers LAST si se obtienen, no asumir cuenta de empresa equivalente a perfil personal.

## Código de adaptación: filas posicionales (propuesta no integrada)
La respuesta observada contiene rows=[[valor_col0,..., fecha_YYYYMMDD]], NO nombres de columnas; preservar el orden solicitado y ordenar fechas, porque las filas llegaron desordenadas.
~~~python
from datetime import datetime

def snapshot_from_rows(rows, metric_ids):
    ordered = sorted(rows, key=lambda row: datetime.strptime(str(row[-1]), "%Y%m%d"))
    out = {}
    for idx, field_id in enumerate(metric_ids):
        valid = [(str(row[-1]), row[idx]) for row in ordered if row[idx] is not None]
        out[field_id] = (valid[-1] if valid else None)  # LAST: fecha y valor
    return out
~~~
No utilizar ese helper para sumatorias de visitas: vistas requieren selección de ventana y SUM, no LAST. Distinguir métrica agregada por conector y no sumar endpoints derivados de la misma métrica.

## Gate técnico
Verificar contrato de API/export de Metricool, condiciones del plan, autenticación backend, límites, propiedad de series, ventanas y posibilidad de automatizar sin interacción. Si no está disponible, usar APIs públicas y un CSV/manual temporal verificable, nunca scraping de panel privado.

## QA pendiente
Comprobar orden de columnas, null, períodos 30d, UTC/Madrid, deprecated, último día incompleto, fila duplicada, 429/5xx, falta de conexión. No cron, token ni Actions.

## Entrega Claude
Releer fuente oficial y estado main, integrar una sola vez sobre el contrato padre, ejecutar pruebas offline/live autorizadas, documentar limitaciones reales antes de solicitar merge. Se mantiene aislamiento respecto de las demás hijas.
