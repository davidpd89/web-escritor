# Investigación GPT — Reddit (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Estado de identidad
Autor.html ya referencia aportaciones a la comunidad r/FreeEBOOKS, pero NO confirma el handle personal de Reddit. Guardar reddit_username=[[pendiente]] hasta que se coteje con el perfil enlazado realmente; no derivarlo de usuario GitHub, alias ni enlace de una publicación.

## Métricas
GET /user/{username}/about (API Reddit, autenticación según política/solicitudes actuales) describe karma. Karma NO es seguidores, impresiones ni alcance; no debe sumarse a comunidad ni interacciones en un dashboard profesional. La mejor tarjeta inicial puede ser «Participo en comunidades lectoras» + enlace al perfil validado, sin contador.

## Pequeño extractor tras respuesta autorizada (autoría propia)
~~~python
def normalize_reddit(payload):
    user = payload.get("data") or {}
    return {"network": "reddit", "followers": None,
            "impressions_30d": None, "views_30d": None,
            "karma": user.get("total_karma"),
            "source": "reddit-authorized"}
~~~
No forzar métricas Reddit a otras unidades; para marcas podría omitirse el karma y destacar participación cualitativa.

## Referencias
[API Reddit](https://www.reddit.com/dev/api/) y [modelo User](https://developers.reddit.com/docs/api/redditapi/models/classes/User). Las políticas de acceso pueden cambiar; comprobar OAuth, user agent y licencia si se reutiliza un SDK. Sin scraping de Reddit no autenticado como prueba de viabilidad.

## QA pendiente
Validar identidad, privacidad del perfil, permiso API, respuesta data/karma, 401/429, ausencia de followers, y enlace directo al perfil; no implementado.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
