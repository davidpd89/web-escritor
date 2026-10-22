# Investigación GPT — Pinterest (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Perfil y objetivo
https://www.pinterest.com/davidportodiaz/ verificado en autor.html. Tiene sentido editorial propio: derivación de Pinterest -> recomendaciones, libros, viajes literarios y afiliación web. Aunque Pinterest esté pausado como robot social, no ocultar una cuenta pública si sigue siendo útil; decidir visibilidad manual.

## Fuentes y campos reales
Pinterest Organic Analytics documenta un histórico de 90 días para reporting orgánico de cuentas, requiere permisos y algunas métricas exigen Business. Métrica de impresiones = veces que un Pin aparece en pantalla; no es alcance único. Metricool registra PIEV09 pinterestFollowers (LAST), PIEV01 pinterestImpressions (SUM) y PIEV06 pinterestOutboundClicks (SUM), que es relevante para visitas a la web. No mezclar «monthly views» con impresiones de rango arbitrario.

## Extractor genérico del resultado ya agregado (autoría propia)
~~~python
def normalize_pinterest(metricool_30d, as_of):
    return {
        "network": "pinterest", "observed_at": as_of,
        "followers": metricool_30d.get("PIEV09"),
        "impressions_30d": metricool_30d.get("PIEV01"),
        "outbound_clicks_30d": metricool_30d.get("PIEV06"),
        "views_30d": None, "source": "metricool-authorized"
    }
~~~
La selección previa debe preservar SUM 30d y LAST al cierre, sin duplicar pines vinculados al sitio.

## Fuentes primarias
[Orgánico Pinterest](https://developers.pinterest.com/docs/analytics-and-reports/organic-reporting/), [definiciones](https://developers.pinterest.com/docs/analytics-and-reports/metrics-glossary/), [OAuth](https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/), [límites](https://developers.pinterest.com/docs/reference/rate-limits/).

## QA pendiente
Verificar cuenta Business/claim website, scopes y ventana 90d, cuenta/Pin fuente, clicks salientes vs click total, deduplicación, caducidad de token, sin datos, no sumarlo como views. Sin API activada.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
