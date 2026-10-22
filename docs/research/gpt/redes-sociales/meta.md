# Investigación GPT — Instagram y Facebook (22/10/2026)

**PR hija de #699**. Base research/gpt-social-dashboard-2026-10-22. Solo investigación verificable y código ilustrativo, no integrado. Sin CI, Actions, deploy ni merge.

## Solución preferente ya comprobada para Instagram (22/10/2026)

La cuenta de Instagram vinculada a la marca Metricool identifica **`davidportodiaz`**, exactamente el perfil en `autor.html` y `scripts/build-site-shell.py`. El catálogo Metricool identifica `IGEV01` como seguidores (`LAST`), y una consulta real conjunta de 21/10/2026 devolvió ese campo no nulo junto con otras siete métricas de seguidores. **Ya hay código funcional y pruebas:** [#705](https://github.com/davidpd89/web-escritor/pull/705) contiene `scripts/research/gpt_metricool_followers.py` y [#704](https://github.com/davidpd89/web-escritor/pull/704) incorpora Instagram al JSON de **seis perfiles** tras comprobar su identidad. No replicar un cliente OAuth Meta para obtener **solo seguidores**.

**Facebook no está resuelto:** el identificador de Facebook vinculado a la marca Metricool no coincide directamente con el identificador mostrado por la URL pública `facebook.com/profile.php?id=...` del sitio. Que `FBEV17` dé un número no demuestra que corresponda a esa página. Debe cotejarse primero el objeto Page con el URL real. **No publicar ese contador ni sumarlo a Instagram.** No se incorporó credencial ni cifra privada al repositorio.

El siguiente apartado de métricas de vistas/interacciones queda como **investigación no probada**; los códigos `IGEV05` y `FBEV49` NO se consideran todavía `views_30d` publicable: falta demostrar exactamente su definición temporal y el alcance de cuenta frente a contenido.

## Perfiles contrastados con autor.html
- Instagram: https://www.instagram.com/davidportodiaz/
- Facebook: https://www.facebook.com/profile.php?id=61590793667301
- La red enlazada es una página/identidad pública; confirmar mediante OAuth API la entidad apta para insights antes de programar. No confundir perfil personal, página y cuenta profesional.

## Evidencia de campos del catálogo Metricool (consultada)
Instagram IGEV01 followers, IGEV05 views (toda la cuenta, formatos y perfil), IGEV06 reach (personas únicas); IGEV09 interactions. Facebook FBEV17 fbFollowers, FBEV49 pageMediaView, FBEV11 reach, FBEV10 interactions. **FBEV02 pageImpressions está DEPRECATED**; no construir el tablero con ella.

## Contrato real reutilizado, sin fragmentos ilustrativos

**Datos disponibles ahora:** seguidores Instagram mediante `IGEV01` → adaptador multired de #705 → compositor de #704. Los campos `views_30d`, `impressions_30d`, `interactions_30d` permanecen sin acreditar y no se publican. Esta PR no añade un segundo extractor; los dos scripts probados y sus pruebas residen en las PR enlazadas, de modo que Claude debe reutilizarlos tras integrar las ramas con autorización.

## Alternativa y licencias
Meta Graph/Insights vía OAuth solo para cuentas y permisos elegibles; no reutilizar bibliotecas de scraping privado para obtener cifras. Código adaptador arriba es propio y de Python estándar. Identidad y SVG locales ya en scripts/build-site-shell.py; para iconos, Simple Icons CC0 [licencia](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md) + [aviso de marcas](https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md).

## QA pendiente
Probar autorización real, tipo de cuenta, períodos, deprecated, cero/null, seguidores vs me gusta de página, publicabilidad de métricas, expiración de token, 429 y retirada de permisos. Ninguna conexión ni cron aplicado.

## Handoff
Claude podrá reutilizar esta investigación, cotejar licencias/estado vigente sobre main, implementar con contrato de PR #699, validar tests unitarios y de UI por red y solicitar revisión antes de merge. No asumir que el código mostrado ya se ejecutó.
