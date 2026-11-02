# Informe de la noche del 02/11/2026: catálogo de lecturas

## Cambios (PR)
- Fusionadas: #1059 (relacionados ponderados por público y rareza) y #1062 (`publish` por stdin).
- Sincronizadas con main, en verde y con auto-merge:
  - #1052: caja de formatos y barrido de precios robusto (`DailyLimitReached`; un `KeyError` en los datos ya no corta el barrido en silencio; entradas sin `url` toleradas). 281 tests OK.
  - #1060: títulos SEO con autor; si el título choca con otro, el sufijo lleva autor e ISBN. 268 tests OK.
  - #1061: GEO (`llms.txt` y el índice de recomendaciones con todas las fichas; `dateModified`/lastmod en autores y editoriales). 268 tests OK.
  - #1063: textos de orientación en 181 fichas, conflicto con main resuelto (71c94686e). 263 tests OK.

## Verificaciones
- Tests locales tras cada sincronización: en verde (las cifras de arriba).
- CI: fallos intermitentes conocidos (la regresión visual da «dimensiones distintas» y browser-qa da timeout en `.assistant-message__sources`). Relanzados con `--failed`.

## Fallos
- Run 41402185280 de `reading-catalogue-sync`: no hizo ingesta. Intentó retomar la #1063, que no es del bot, y `resume_pending` se negó a reemplazarla. Es el guardián funcionando, no un bug. Queda pendiente relanzar el sync cuando se fusione la #1063.

## Prioridades de GPT (chat en el proyecto «MCP RRSS David Porto»)
Ya cubiertas: robots.txt (permite OAI-SearchBot, PerplexityBot, GPTBot y ClaudeBot), JSON-LD de Book, WebPage con `dateModified` y BreadcrumbList.

Requieren a David:
1. Auditoría de indexación en Search Console (fichas excluidas, canónicas, huérfanas).
2. Entre 8 y 12 páginas de selección editorial con intención de búsqueda real.
3. Criterio propio en 30 fichas («para quién es», «cuándo no lo recomendaría»), sin inventar opiniones.
4. Enlaces externos editoriales.
5. Medición de clics por formato.

Descartado: la «Novedad + fecha» es la fecha de publicación del libro (alimenta el filtro de Novedades), no una fecha de precio.

## Pendientes
- Confirmar que se fusionan la #1052, #1060, #1061 y #1063. Si una entra en conflicto tras otra fusión, sincronizarla con main.
- Relanzar `reading-catalogue-sync` (workflow_dispatch) tras la #1063 y revisar los libros nuevos, `sin_oferta` y `formatos_compra`.
- IndexNow para las fichas con textos nuevos, si el sync no lo hace solo.
