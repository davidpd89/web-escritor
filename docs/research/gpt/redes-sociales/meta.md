# Investigación GPT — Instagram y Facebook (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Perfiles contrastados con autor.html
- Instagram: https://www.instagram.com/davidportodiaz/
- Facebook: https://www.facebook.com/profile.php?id=61590793667301
- La red enlazada es una página/identidad pública; confirmar mediante OAuth API la entidad apta para insights antes de programar. No confundir perfil personal, página y cuenta profesional.

## Evidencia de campos del catálogo Metricool (consultada)
Instagram IGEV01 followers, IGEV05 views (toda la cuenta, formatos y perfil), IGEV06 reach (personas únicas); IGEV09 interactions. Facebook FBEV17 fbFollowers, FBEV49 pageMediaView, FBEV11 reach, FBEV10 interactions. **FBEV02 pageImpressions está DEPRECATED**; no construir el tablero con ella.

## Adaptador de campos tras normalizar cada periodo (solo propuesta)
~~~python
def from_metricool(network, fields, observed_at):
    codes = {
        "instagram": ("IGEV01", "IGEV05", "IGEV09"),
        "facebook": ("FBEV17", "FBEV49", "FBEV10"),
    }
    follower, view, interaction = codes[network]
    return {"network": network, "observed_at": observed_at,
            "followers": fields.get(follower),
            "views_30d": fields.get(view),
            "interactions_30d": fields.get(interaction),
            "impressions_30d": None, "source": "metricool-authorized"}
~~~
Aquí fields debe ser el resumen de la ventana (LAST seguidores, SUM flujo), NO filas de un único día. Reach debe ser campo aparte y no se suma entre plataformas.

## Alternativa y licencias
Meta Graph/Insights vía OAuth solo para cuentas y permisos elegibles; no reutilizar bibliotecas de scraping privado para obtener cifras. Código adaptador arriba es propio y de Python estándar. Identidad y SVG locales ya en scripts/build-site-shell.py; para iconos, Simple Icons CC0 [licencia](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md) + [aviso de marcas](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md).

## QA pendiente
Probar autorización real, tipo de cuenta, períodos, deprecated, cero/null, seguidores vs me gusta de página, publicabilidad de métricas, expiración de token, 429 y retirada de permisos. Ninguna conexión ni cron aplicado.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
