# Investigación GPT: página Redes sociales (22 octubre 2026)

ESTADO: documentación/investigación; NO desplegado, NO Actions, NO merge. Esta PR es padre de PR pequeñas por red, con base en la rama indicada.

## Diagnóstico comprobado

- Sitio publicado de HTML/CSS/JS estático sin build de app (package.json), GitHub Pages. Data/navigation.json y scripts/build-site-shell.py gobiernan el menú; NO modificar solo la portada.
- Autor.html contiene Person.sameAs y URLs de perfiles; scripts/build-site-shell.py contiene SOCIAL_ROW con iconos existentes. Mantener una sola fuente autorizada de perfiles.
- data/site-human-stats.generated.json demuestra el patrón de estadísticas generadas, pero sus valores son de libros, herramientas y artículos y NO se reutilizan como comunidad social.
- data/third-party-integrations.json y data/analytics-events.json son contratos de integraciones/analítica; respetar CSP, privacidad, navegación, sitemap y QA.
- **Prueba de viabilidad**: la marca ya conectada en Metricool reconoce Bluesky, Threads, Instagram, Facebook, TikTok, Pinterest, YouTube y más. La consulta de métricas de 01–21/10/2026 devolvió series numéricas y también valores null según red/fecha. No se publican los valores de la cuenta en este documento. La conexión ChatGPT-Metricool no implica disponer de un backend API o permiso para un cron: comprobar export/API habilitado antes de su automatización.

## Propuesta UX

Página pública /redes-sociales/ con introducción breve («Lectura, escritura y cultura»), enlaces reales de perfil, tarjetas elegantes por marca y logo SVG local, seguidores y una métrica de impacto válida si existe, fecha de actualización, descripción de comunidad, y enlace a prensa/colaboraciones. Resumen superior sencillo: «seguidores en las redes verificadas» (SUMA de relaciones, no personas únicas); «visualizaciones de contenido últimos 30 días»; «impresiones últimos 30 días» si datos homogéneos. NO mostrar reach, impressions y views como equivalentes. Mostrar cobertura por cada total; ocultar métricas sin fuente. Enlace «Seguir en ...» abre perfil oficial: seguir dentro de la web exigiría autorización del visitante y no se propone.

Página semántica indexable en móvil/teclado, visible sin JavaScript, tamaño responsive 320 px y accesibilidad AA. No meter iframes de terceros ni peticiones de API con secretos en el navegador. Ubicar acceso en zona Autor o Información sin romper las prioridades de menú.

## Arquitectura, separada de UI

1. Registro data/social-profiles.json con id, URL, handle, nombre, orden y visibilidad; migrar gradualmente desde autor.html, mantener consistencia con builder y sameAs.
2. Recogida fuera del navegador: público sin token para Bluesky/Mastodon; Metricool/insights/OAuth solo cuando esté permitida una integración independiente desatendida; nunca publicar tokens.
3. Un normalizador recibe, por red, {id, observed_at, source, followers, posts, impressions_30d, views_30d, interactions_30d, status}; los campos sin datos son null (no 0) y tienen periodo, definición y origen.
4. Exportar JSON público generado a data/social-metrics.generated.json, consumido con mejoras progresivas por UI; refresco recomendado 12–24 h, no «tiempo real» falso. Mantener último dato válido con sello stale cuando falle la fuente; no sobrescribir null por cero.
5. Agregados: únicamente mismas definiciones + misma ventana, con cobertura visible (por ejemplo «6 de 9 perfiles con datos»); no inferir usuarios únicos, ni sumar impresiones y alcance. Si hay dos fechas comparables mostrar evolución, en otro caso no.

Ejemplo de contrato propuesto (datos ficticios prohibidos, cifras deliberadamente ausentes):

~~~json
{"schema_version":1,"generated_at":null,"period":{"from":null,"to":null,"tz":"Europe/Madrid"},"networks":[{"id":"bluesky","followers":null,"views_30d":null,"impressions_30d":null,"observed_at":null,"source":null,"status":"pending"}]}
~~~

## Viabilidad por red (fuentes revisadas)

| Red | Fuente preferente | Datos defendibles | A comprobar |
|---|---|---|---|
| Bluesky | https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=davidportoescritor.bsky.social | followersCount, postsCount | no hay impresiones de cuenta públicas |
| Mastodon | https://docs.joinmastodon.org/methods/accounts/ | followers_count, statuses_count con GET público por ID local | /accounts/lookup requiere read:accounts para resolución inicial; no impresiones |
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
| [#704](https://github.com/davidpd89/web-escritor/pull/704) | UX/contrato y sumatorios | [ux.md](./ux.md) |
| [#705](https://github.com/davidpd89/web-escritor/pull/705) | Fuente agregada Metricool | [metricool.md](./metricool.md) |
| [#706](https://github.com/davidpd89/web-escritor/pull/706) | Bluesky | [bluesky.md](./bluesky.md) |
| [#707](https://github.com/davidpd89/web-escritor/pull/707) | Mastodon (autorización lookup diferenciada) | [mastodon.md](./mastodon.md) |
| [#708](https://github.com/davidpd89/web-escritor/pull/708) | Threads | [threads.md](./threads.md) |
| [#709](https://github.com/davidpd89/web-escritor/pull/709) | Instagram y Facebook | [meta.md](./meta.md) |
| [#710](https://github.com/davidpd89/web-escritor/pull/710) | TikTok | [tiktok.md](./tiktok.md) |
| [#711](https://github.com/davidpd89/web-escritor/pull/711) | X | [x.md](./x.md) |
| [#712](https://github.com/davidpd89/web-escritor/pull/712) | Pinterest | [pinterest.md](./pinterest.md) |
| [#713](https://github.com/davidpd89/web-escritor/pull/713) | Reddit | [reddit.md](./reddit.md) |
| [#714](https://github.com/davidpd89/web-escritor/pull/714) | LinkedIn y YouTube | [linkedin-youtube.md](./linkedin-youtube.md) |

Los documentos de PR hijas no existen todavía en esta rama padre porque cada uno está deliberadamente aislado en su rama correspondiente. Para revisar, seguir los enlaces de PR. Al fusionar una hija en la padre, su archivo pasará a estar accesible desde el índice. No fusionar ninguna hasta aprobación.
