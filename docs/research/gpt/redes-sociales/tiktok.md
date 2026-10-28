# Investigación GPT — TikTok (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Camino ya probado: Metricool, sin OAuth nuevo (22/10/2026)

`getBrandSettings` de la marca conectada confirma TikTok **`davidportoescritor`**, exactamente el handle público enlazado en `autor.html` y `scripts/build-site-shell.py`. El campo `TKEV07` (followers, agregación `LAST`) devolvió valor no nulo en la consulta MCP real conjunta de 21/10/2026. No se publican los valores personales.

**Reutilización directa:** lector multired ejecutable de la [PR #705](https://github.com/davidpd89/web-escritor/pull/705) y compositor de la [PR #704](https://github.com/davidpd89/web-escritor/pull/704), que ya admite `tiktok` como sexto conjunto de redes elegibles (seis en total). Las regresiones de identidad, suma, proveedor y expiración ya están codificadas. El desarrollo OAuth ilustrativo de abajo **solo es alternativa**, no implementación prioritaria ni camino demostrado. No prometer actualización desatendida MCP hasta verificarla.

## Perfil
Cuenta pública según autor.html: https://www.tiktok.com/@davidportoescritor. TikTok Display API GET /v2/user/info/ devuelve follower_count, likes_count, video_count con consentimiento OAuth y scope user.info.stats. La Research API se reserva para investigaciones autorizadas: NO considerarla acceso público ordinario. El conector Metricool tiene TKEV07 followers y TKEV02 views, donde views es rendimiento de vídeos en periodo, no vistas acumuladas del perfil.

## Adaptador OAuth Python propuesto (NO se prueba con credenciales)
~~~python
import json
from urllib.request import Request, urlopen

def tiktok_stats(access_token):
    fields = "display_name,follower_count,likes_count,video_count"
    url = "https://open.tiktokapis.com/v2/user/info/?fields=" + fields
    req = Request(url, headers={"Authorization": "Bearer " + access_token,
                                "Accept": "application/json"})
    with urlopen(req, timeout=10) as response:
        payload = json.load(response)
    if payload.get("error", {}).get("code") != "ok":
        raise ValueError("TikTok API no devolvió ok")
    data = payload["data"]["user"]
    return {"followers": data.get("follower_count"),
            "posts": data.get("video_count"),
            "views_30d": None, "source": "tiktok-display"}
~~~
Access token solo en backend/secret store, nunca en la página. La respuesta puede no incluir stats si scopes insuficientes: mantener NULL.

## Documentación oficial actual
[Get User Info](https://developers.tiktok.com/docs/en/tiktok-api-v2-get-user-info); [scopes](https://developers.tiktok.com/docs/en/tiktok-api-scopes); [autorización Display API](https://developers.tiktok.com/docs/en/display-api-get-started). No copiar código de SDK terceros sin licencia verificada; este fragmento usa librería estándar.

## QA pendiente
App aprobada, token refresh, scopes, 401/403, error.code, nulidad y consentimiento; comparar follower_count con Metricool en misma fecha, diferenciar likes acumulados de engagement 30d. No OAuth configurado.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
