# Investigación GPT — X / Twitter (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Identidad y estado
Existe actividad del autor en X; antes de publicar comprobar que el perfil público y URL son realmente https://x.com/davidportodiaz y añadirlo al registro canónico. En autor.html/shell actual no se detecta enlace de X en el bloque principal auditado, de modo que NO completar la URL automáticamente con una suposición.

## Datos / permisos
API v2 de X exige autenticación y tiene precios/cuotas según plan. user.fields=public_metrics puede devolver followers_count, tweet_count; las impresiones suelen pertenecer a métricas de posts y permisos/capacidades concretas, nunca son garantía de analítica gratuita pública. Metricool enumera TTEV01 followers, TTEV11 impressions, pero la consulta real mostró NULL para el campo followers en el intervalo verificado: una definición de campo no equivale a datos disponibles.

## Extractor conservador de la API oficial (adaptación Python, NO ejecutada)
~~~python
def normalize_x_api(user_payload):
    user = user_payload.get("data") or {}
    stats = user.get("public_metrics") or {}
    return {
        "network": "x", "followers": stats.get("followers_count"),
        "posts": stats.get("tweet_count"), "impressions_30d": None,
        "source": "x-api-authorized"
    }
~~~
El cliente HTTP se añadirá solamente si hay token autorizado y coste aceptado. Nunca hacer scrape de sesiones autenticadas como sustitución silenciosa.

## Decisión A/B
A: si existe Metricool export/API permitido, validar su campo y publicarlo con fecha. B: si no existe, tarjeta con enlace/descripcion y métrica no disponible. Evitar que esta red bloquee el lanzamiento de todo el panel.

## QA pendiente
Documentar precio y cuota real del acceso del titular, URL, token, endpoints y 429; comparar dos lecturas con rango válido; cuando sea NULL esconder cifra sin inventar 0. Sin compras, cambios de API ni Actions.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
