# Investigación GPT — LinkedIn y YouTube (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Inventario
LinkedIn personal enlazado en autor.html: https://www.linkedin.com/in/davidportodiaz/. YouTube consta como canal conectado a la marca Metricool, pero el enlace público exacto para página social debe cotejarse con el canal antes de insertarlo en sameAs; no inferir nombre o handle.

## LinkedIn
El endpoint oficial memberFollowersCount describe seguidores del miembro autenticado; los endpoints de organizaciones son DISTINTOS y no deben tratarse como perfil personal. El conector Metricool enumera LIEV01 followers, pero la consulta de ejemplo devolvió NULL en fechas consultadas. Fallback: mostrar el botón «Conectar en LinkedIn» sin seguidores hasta verificar permisos y datos.
[Member follower statistics](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/follower-statistics).

## YouTube
YouTube Data API channels.list part=statistics devuelve subscriberCount (redondeado a tres cifras significativas según documentación) y viewCount; desde agosto 2026 la semántica de viewCount incorpora Shorts desde el inicio de la reproducción, incluidas reproducciones automáticas. Metricool enumera YTEV01 subscribers, YTEV02 videoViews (periodo). Distinguir suscriptores actuales de vistas del canal, y redondeo de cifra.
[Channels API](https://developers.google.com/youtube/data/reference/rest/v3/channels).

## Normalización del contrato (autoría propia)
~~~python
def normalize_secondary(network, stats):
    if network == "youtube":
        return {"network": network,
                "followers": stats.get("subscriberCount"),
                "channel_views_lifetime": stats.get("viewCount"),
                "impressions_30d": None}
    if network == "linkedin":
        return {"network": network,
                "followers": stats.get("memberFollowersCount"),
                "views_30d": None, "impressions_30d": None}
    raise ValueError("unsupported network")
~~~
El helper no convierte views_lifetime en views_30d. No sumar subscripciones YouTube redondeadas como una precisión exacta si se publica un total redondeado.

## QA pendiente
Cuenta exacta, permisos LinkedIn personales, API key/cuota YouTube, privacidad, campos escondidos, fecha/definición de Shorts, null y redondeos, diferencias Metricool vs API. Ninguna conexión nueva ni Actions.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
