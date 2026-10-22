# Investigación GPT: página Redes sociales (22 octubre 2026)

ESTADO: documentación/investigación; NO desplegado, NO Actions, NO merge. Esta PR es padre de PR pequeñas por red, con base en la rama indicada.

## Validación conjunta reproducible — completada el 22/10/2026

Las PR #704–#707 se han montado **sin hacer merge** con sus archivos exactos verificados por Git SHA y se han ejecutado **130/130 pruebas Python y 22/22 Node (152/152, cero omitidas)**. Se ha incorporado [`scripts/research/run_social_cross_pr_qa.sh`](../../../../scripts/research/run_social_cross_pr_qa.sh) a #704 para reconstruir los 16 archivos de las cuatro ramas y repetir la prueba con `bash scripts/research/run_social_cross_pr_qa.sh` después de actualizar las refs remotas. El runner se ha validado contra esas versiones en un repositorio Git temporal; no ejecuta Actions ni toca el working tree.

**Correcciones que han salido de esta auditoría:** (1) una prueba del pipeline esperaba tres filas de estado, aunque el contrato ahora declara seis redes, y se ha corregido; (2) el lector del navegador ya no acepta una expiración arbitrariamente futura ni JSON generado hace más de 48 h; (3) Python y JavaScript evitan sumas que excedan el rango exacto de enteros JavaScript. Todas las regresiones se han ejecutado localmente. **No equivale a un test en vivo de APIs ni al CI completo del sitio.**

## Diagnóstico comprobado

- Sitio publicado de HTML/CSS/JS estático sin build de app (package.json), GitHub Pages. Data/navigation.json y scripts/build-site-shell.py gobiernan el menú; NO modificar solo la portada.
- Autor.html contiene Person.sameAs y URLs de perfiles; scripts/build-site-shell.py contiene SOCIAL_ROW con iconos existentes. Mantener una sola fuente autorizada de perfiles.
- data/site-human-stats.generated.json demuestra el patrón de estadísticas generadas, pero sus valores son de libros, herramientas y artículos y NO se reutilizan como comunidad social.
- data/third-party-integrations.json y data/analytics-events.json son contratos de integraciones/analítica; respetar CSP, privacidad, navegación, sitemap y QA.
- **Prueba de viabilidad**: la marca ya conectada en Metricool reconoce Bluesky, Threads, Instagram, Facebook, TikTok, Pinterest, YouTube y más. La consulta de métricas de 01–21/10/2026 devolvió series numéricas y también valores null según red/fecha. No se publican los valores de la cuenta en este documento. La conexión ChatGPT-Metricool no implica disponer de un backend API o permiso para un cron. Comprobado el 22/10/2026: MCP funciona también en Free, mientras la API HTTP independiente exige Advanced/Custom. La PR #705 ya demuestra la lectura real de **solo `THEV01` de Threads en un día cerrado**: una fila `[followers, YYYYMMDD]`, y aporta importador offline con **17/17 pruebas ejecutadas sobre código idéntico al de GitHub**. La PR #704 contiene un **compositor ejecutable de seis perfiles**, con 10 nuevas regresiones de identidad verificadas localmente, así como pruebas anteriores de fecha y sumatorios; rechaza cuentas duplicadas, proveedores atribuidos a la red equivocada, contadores caducados, URLs discordantes y métricas ambiguas. Publicación/UX aún pendientes. Eliminó la consulta innecesaria a `THEV06`. Make → MCP por OAuth sigue siendo **un piloto NO ejecutado**, no un refresco en producción. No considerar el piloto una solución implantada.

**Ampliación contrastada 22/10/2026 (PR #705):** la marca conectada en Metricool devolvió **una fila de nueve columnas** al consultar juntos ocho campos `LAST` de seguidores para el 21/10 cerrado: `BKEV01`, `THEV01`, `IGEV01`, `FBEV17`, `TKEV07`, `PIEV09`, `YTEV01`, `TTEV01`. Hay un importador adicional `scripts/research/gpt_metricool_followers.py` con **18 pruebas offline ejecutadas**; reutiliza el normalizador diario de Threads y genera registros **candidatos**, sin publicar cifras ni URLs. La PR #704 comprueba identidad y fuente para **seis redes** tras cotejar con la marca conectada; no amplía Facebook, X o YouTube sin esa comprobación ni confundir esta lectura con un cron MCP funcionando.

**Integración incremental de lotes (22/10/2026):** la PR #704 ya admite **directamente** el envoltorio `metricool-follower-candidates` producido por #705. Valida la estructura, la fecha, las duplicaciones y el proveedor, e incorpora **Threads, Instagram, TikTok y Pinterest** al JSON público; descarta Bluesky del lote para mantener su fuente AppView y omite Facebook/X/YouTube hasta cotejar su identidad. Si no queda un contador vigente, no sobrescribe el último archivo de salida. Código y diez pruebas de regresión incorporados a #704; además se ejecutaron **35 pruebas locales** sobre el puente con hashes exactos de los tres scripts principales contrastados con GitHub. **Completado posteriormente:** suite conjunta de **152/152 tests versionados** ejecutada en checkout temporal sin merge. No existe todavía cron, web desplegada ni autenticación automática de la exportación MCP.

## Propuesta UX

Página pública /redes-sociales/ con introducción breve («Lectura, escritura y cultura»), enlaces reales de perfil, tarjetas elegantes por marca y logo SVG local, seguidores y una métrica de impacto válida si existe, fecha de actualización, descripción de comunidad, y enlace a prensa/colaboraciones. Resumen superior sencillo: «seguidores en las redes verificadas» (SUMA de relaciones, no personas únicas); «visualizaciones de contenido últimos 30 días»; «impresiones últimos 30 días» si datos homogéneos. NO mostrar reach, impressions y views como equivalentes. Mostrar cobertura por cada total; ocultar métricas sin fuente. Enlace «Seguir en ...» abre perfil oficial: seguir dentro de la web exigiría autorización del visitante y no se propone.

Página semántica indexable en móvil/teclado, visible sin JavaScript, tamaño responsive 320 px y accesibilidad AA. No meter iframes de terceros ni peticiones de API con secretos en el navegador. Ubicar acceso en zona Autor o Información sin romper las prioridades de menú.

## Arquitectura, separada de UI

1. Registro data/social-profiles.json con id, URL, handle, nombre, orden y visibilidad; migrar gradualmente desde autor.html, mantener consistencia con builder y sameAs.
2. Recogida fuera del navegador: público sin token para Bluesky/Mastodon; Metricool/insights/OAuth solo cuando esté permitida una integración independiente desatendida; nunca publicar tokens.
3. Los **adaptadores internos** pueden recibir {id, observed_at, source, followers, posts, impressions_30d, views_30d, interactions_30d, status}; el **compositor público v1 probado** expone solo identificador, enlace canónico, seguidores, fecha, fuente, estado, totales y cobertura. Las métricas no justificadas quedan fuera del documento público.
4. Exportar JSON público generado a data/social-metrics.generated.json, consumido con mejoras progresivas por UI; refresco recomendado 12–24 h, no «tiempo real» falso. Mantener último dato válido con sello stale cuando falle la fuente; no sobrescribir null por cero.
   - **Corrección implementada en la PR #704:** el contador en el último fichero bueno puede quedar desactualizado si deja de ejecutarse el generador. Por eso cada red tiene ahora `valid_until` UTC y el total `totals.valid_until` es la primera expiración entre los contadores participantes. El nuevo módulo `scripts/research/gpt_social_reader.mjs` **recalcula en el navegador** usando únicamente cifras aún vigentes, sin confiar en el total o estado guardados. Hay 7 pruebas Python, 16 Node y 3 pruebas cruzadas Python→JS ejecutadas, **con hashes Git idénticos** a los archivos de la PR. No está conectado aún a la web ni se ha validado con Actions.
5. Agregados: únicamente mismas definiciones + misma ventana, con cobertura visible (por ejemplo «6 de 9 perfiles con datos»); no inferir usuarios únicos, ni sumar impresiones y alcance. Si hay dos fechas comparables mostrar evolución, en otro caso no.
   - **Corrección concreta (22/10, PR #705):** el conector Metricool denomina `THEV06` «Post Views», pero [su documentación oficial](https://help.metricool.com/es/diferencia-entre-posts-publicados-y-posts-vistos-en-el-periodo-2pwtf) separa vistas acumuladas de posts publicados y vistas generadas durante el período. `THEV06` **no se debe mapear a `views_30d`** hasta demostrar el alcance real de esa serie. El adaptador Threads lo suprime deliberadamente. **La PR #708 ha corregido la sugerencia anterior que equiparaba `THEV06` con `views_30d`** y ahora remite al código probado de #705/#704. `THEV11` son vistas del perfil, no de los posts.

Contrato **v1 efectivamente implementado en PR #704** (salida vacía de ejemplo, sin números de cuenta). El esquema inicial de investigación que contenía `period` y `views_30d` **NO coincidía** con el compositor; se elimina para evitar que Claude implemente un JSON incompatible. `generated_at` es siempre timestamp UTC de ejecución; aquí se utiliza una fecha ilustrativa. Se admiten **seis redes**: Bluesky y Mastodon desde APIs públicas; Threads, Instagram, TikTok y Pinterest desde la marca Metricool cuyos identificadores se cotejaron con las URLs del sitio. Facebook, X y YouTube aún no se incluyen en los totales.

~~~json
{
  "schema_version": 1,
  "generated_at": "2026-10-22T12:00:00Z",
  "networks": [
    {
      "id": "bluesky",
      "profile_url": "https://bsky.app/profile/davidportoescritor.bsky.social",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "mastodon",
      "profile_url": "https://mastodon.social/@davidportodiaz",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "threads",
      "profile_url": "https://www.threads.com/@davidportodiaz",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "instagram",
      "profile_url": "https://www.instagram.com/davidportodiaz/",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "tiktok",
      "profile_url": "https://www.tiktok.com/@davidportoescritor",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "pinterest",
      "profile_url": "https://www.pinterest.com/davidportodiaz/",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    }
  ],
  "totals": {
    "follower_relationships": null,
    "valid_until": null,
    "coverage": 0,
    "eligible": 6,
    "label": "Seguidores sumados en redes con datos vigentes (no personas únicas)"
  }
}
~~~

**QA vigente:** **152/152 tests offline versionados** (130 Python + 22 Node). Las cifras 81 y 35 de fases anteriores ya han sido sustituidas por la ejecución conjunta actual. No prueba APIs en vivo, CI de GitHub ni despliegue.

## Viabilidad por red (fuentes revisadas)

| Red | Fuente preferente | Datos defendibles | A comprobar |
|---|---|---|---|
| Bluesky | https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=davidportoescritor.bsky.social | followersCount, postsCount | no hay impresiones de cuenta públicas |
| Mastodon | https://docs.joinmastodon.org/methods/search/ | /api/v2/search anónimo, sin resolve/offset; devuelve Account con followers_count y statuses_count | Validar en vivo cuenta exacta; /accounts/lookup sí exige token, pero ya no hace falta para este flujo; no impresiones |
| Threads | https://www.postman.com/meta/threads/ | seguidores/insights de cuenta si se autorizan; Metricool conectado | alcance del token y métricas disponibles |
| Instagram/Facebook | API Meta o Metricool autorizado | seguidores, vistas, alcance según cuenta | permisos, campo views vigente; deprecated pageImpressions |
| TikTok | https://developers.tiktok.com/docs/en/tiktok-api-scopes | follower_count requiere user.info.stats y autorización | aprobación Display API y OAuth |
| Pinterest | https://developers.pinterest.com/docs/analytics-and-reports/organic-reporting/ | impresiones/acciones en periodo | OAuth y cuenta Business |
| X | https://docs.x.com/x-api | seguidores públicos en API autenticada | precios, cuotas y accesibilidad |
| Reddit | https://www.reddit.com/dev/api/ | karma, no seguidores comparables | usuario exacto, acceso autorizado |
| LinkedIn | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/follower-statistics | seguidores personales si se tiene permiso API | derechos de app/perfil |
| YouTube | https://developers.google.com/youtube/data/reference/rest/v3/channels | suscriptores, vistas | suscriptores redondeados y semántica de vistas |

## Reutilización pública: licencia primero

Repositorio público no significa derecho de copia sin licencia. Ejemplos verificados: Mastodon.py (MIT) https://github.com/halcy/Mastodon.py/blob/master/LICENSE; SDK atproto (MIT) https://github.com/MarshalX/atproto/blob/main/LICENSE; Simple Icons (CC0) https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md, con advertencia de marcas https://github.com/simple-icons/simple-icons/blob/develop/DISCLAIMER.md; Lucide (ISC) https://github.com/lucide-icons/lucide/blob/main/LICENSE. Ejemplos concretos y adaptaciones por PR hija. Preservar notices, versión y procedencia. No usar scraping frágil como fuente primaria si hay API oficial.

## QA necesario ANTES de fusionar (no ejecutado)

Fechas UTC/Madrid; 0 vs null; 429/401/5xx; falsos aumentos; ventana desalineada; datos parciales; caducidad; fallos de red; validación de URLs/JSON; protección de tokens; CSP/privacidad; id de mismo perfil no duplicado; tests de navegación y shell; sitemap y canonical; Pagefind; WCAG AA teclado/320px; Lighthouse. No crear cron, correr Actions, publicar ni mergear sin orden explícita. Claude revisará sobre main vigente y probará por PR.

## Entrega

Documento rector y PR hijas: base técnica, fuente central Metricool, Bluesky, Mastodon, Threads, Meta, TikTok, X, Pinterest, y grupo de redes secundarias, cada una con fuente, código pequeño, límites, pruebas y pasos. Se documentará progreso real en cada PR, evitando afirmaciones de «listo para producción» cuando solo se haya investigado.


## Índice de PR hijas abiertas (borradores, base de GitHub: research/gpt-social-dashboard-2026-10-22)

| PR | Alcance | Documento |
|---|---|---|
| [#704](https://github.com/davidpd89/web-escritor/pull/704) | Compositor y lector JS para 6 perfiles, expiración UTC y pruebas locales | [ux.md](./ux.md) |
| [#705](https://github.com/davidpd89/web-escritor/pull/705) | Fuente agregada Metricool | [metricool.md](./metricool.md) |
| [#706](https://github.com/davidpd89/web-escritor/pull/706) | Bluesky | [bluesky.md](./bluesky.md) |
| [#707](https://github.com/davidpd89/web-escritor/pull/707) | Mastodon (búsqueda pública, adaptador y 18 pruebas offline) | [mastodon.md](./mastodon.md) |
| [#708](https://github.com/davidpd89/web-escritor/pull/708) | Threads (reutilización #705 sin vistas 30d ambiguas) | [threads.md](./threads.md) |
| [#709](https://github.com/davidpd89/web-escritor/pull/709) | Instagram y Facebook | [meta.md](./meta.md) |
| [#710](https://github.com/davidpd89/web-escritor/pull/710) | TikTok | [tiktok.md](./tiktok.md) |
| [#711](https://github.com/davidpd89/web-escritor/pull/711) | X | [x.md](./x.md) |
| [#712](https://github.com/davidpd89/web-escritor/pull/712) | Pinterest | [pinterest.md](./pinterest.md) |
| [#713](https://github.com/davidpd89/web-escritor/pull/713) | Reddit | [reddit.md](./reddit.md) |
| [#714](https://github.com/davidpd89/web-escritor/pull/714) | LinkedIn y YouTube | [linkedin-youtube.md](./linkedin-youtube.md) |

Los documentos de PR hijas no existen todavía en esta rama padre porque cada uno está deliberadamente aislado en su rama correspondiente. Para revisar, seguir los enlaces de PR. Al fusionar una hija en la padre, su archivo pasará a estar accesible desde el índice. No fusionar ninguna hasta aprobación.
