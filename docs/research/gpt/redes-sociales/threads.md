# Investigación GPT — Threads (22/10/2026)

**PR hija de #699.** Rama basada en research/gpt-social-dashboard-2026-10-22. Solo análisis y código de referencia, no instalado ni ejecutado; sin Actions ni merge.

## Diagnóstico y fuente
Perfil: https://www.threads.com/@davidportodiaz (ya en autor.html). API Threads oficial (colección Meta) dispone de endpoints de información, publicaciones e insights, bajo autorización de cuenta; no inventar una ruta pública sin token. En el conector Metricool asociado sí aparecen THEV01 (seguidores), THEV05 (interacciones) y THEV06 (vistas de posts) con datos consultables, además de campos no disponibles en ciertas fechas. Prioridad: Metricool si su integración **automática** tiene permiso; API Meta solo si se verifica OAuth/insights y costes.

## Adaptación al contrato sin confundir unidades
~~~python
def normalize_threads(metricool_record, date):
    return {
        "network": "threads", "observed_at": date,
        "followers": metricool_record.get("THEV01"),  # LAST
        "interactions_30d": metricool_record.get("THEV05"),  # SUM ventana
        "views_30d": metricool_record.get("THEV06"),  # SUM ventana
        "impressions_30d": None,  # NO derivar automáticamente de views
        "source": "metricool-authorized"
    }
~~~
El código presupone que metricool_record ya está agregado con el operador correcto; no usar una fila diaria como sumatoria 30d.

## Referencias
[Meta Threads API collection](https://www.postman.com/meta/threads/), [Get Post Insights](https://www.postman.com/meta/threads/request/34203612-385abc7d-b3cc-4e5d-9937-ebbe7174e041). No reutilizar ejemplos con tokens literales o permisos de publicación si solo se requieren estadísticas.

## QA pendiente
Verificar scopes, propiedad de cuenta y métrica concreta; comprobar 30d incompletos, conteo cuenta frente a post, edad de dato, 401/403, desaparición de cuenta, CTA abre perfil y no requiere login en la web. Documentación, sin OAuth ni tests ejecutados.

## Entrega Claude
Releer fuente oficial y estado main, integrar una sola vez sobre el contrato padre, ejecutar pruebas offline/live autorizadas, documentar limitaciones reales antes de solicitar merge. Se mantiene aislamiento respecto de las demás hijas.
