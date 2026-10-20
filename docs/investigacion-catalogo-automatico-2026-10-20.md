# Investigación adicional para Codex — código abierto y fuentes reales (20/10/2026)

Este documento conserva la investigación previa. La implementación de PR #661 eligió una fuente editorial pública sin clave, con 20 libros iniciales de ocho sellos. Google Books queda como adaptador opcional. El estado operativo actualizado está en [automatización](catalogo-lecturas-automatizacion.md).

**Leer junto a:** [encargo principal](../.github/plans/ingesta-automatica-libros-editoriales-2026-10-20.md) (ruta relativa desde `docs/`: `../.github/plans/ingesta-automatica-libros-editoriales-2026-10-20.md`).  
**Propósito:** ahorrar investigación repetida y evitar reproducir fallos conocidos; los ejemplos públicos no demuestran cobertura completa de novedades españolas y **NO se han importado/copias de código ajeno**.

## A. Referencias públicas VERIFICADAS — webs y código que resuelven piezas del problema

| Caso | Repositorio y ficheros concretos | Sitio/qué hace | Lo que SÍ reutilizar | Límite encontrado |
| --- | --- | --- | --- | --- |
| **History Books** | https://github.com/aewshopping/history_books ; [captación CSV](https://github.com/aewshopping/history_books/blob/main/.github/workflows/fetch-csv.yml); [build/deploy](https://github.com/aewshopping/history_books/blob/main/.github/workflows/build-and-deploy.yaml); [web 11ty](https://github.com/aewshopping/ssg-deploy-test) | https://popularhistorybooks.com/allbooks/ ; Google Books + ISBN + Sheets + etiquetas M:N + CI → catálogo público | **Separación ingest/build/deploy** y utilidad del ISBN como clave, categorías relacionadas y regeneración de catálogo. `workflow_run` tras importación; no depender de segundo `push` con `GITHUB_TOKEN`. | Su autor afirma que **Google Books tiene errores y campos vacíos**, por lo que corrige manualmente; el descubrimiento no es autónomo. Utiliza Vercel/Datasette: no migrar nuestra web a esa pila. Licencia del repo no acreditada: no copiar sus archivos. |
| **GetCreditWorth** | https://github.com/863683348/getcreditworth ; [único workflow de expansión](https://github.com/863683348/getcreditworth/blob/master/.github/workflows/book-expand.yml) ; [antiguo cron, ahora manual](https://github.com/863683348/getcreditworth/blob/master/.github/workflows/daily-data-update.yml) | https://getcreditworth.com/ ; catálogo público de audiolibros con fichas, taxonomía, afiliación y SEO | **UNA tarea programada = UNA escritura de datos + UNA publicación**; actualiza libros, listas y datos dependientes antes de un solo commit; evita carreras de flujos concurrentes y despliegues duplicados. | Usa PA-API/Audible y otros servicios; **no permite evitar** la elegibilidad Amazon. Su README describe un cron diario, pero el `daily-data-update.yml` tiene cron **comentado**, mientras `book-expand.yml` concentra actualizaciones. Next.js/Vercel no es necesario para nuestro sitio. Licencia MIT según README. |
| **Bookery** | https://github.com/JoeCotellese/bookery ; [metadata/cache.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/cache.py) ; [metadata/consensus.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/consensus.py) ; [metadata/http.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/http.py) ; [metadata/googlebooks.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/googlebooks.py) | CLI de catalogación de libros electrónicos, sin web pública afiliada equivalente | **Proveniencia por campo**, bloqueo de correcciones del propietario, consenso entre proveedores con prioridad, ISBN13 sobre ISBN10, caché con TTL y reintentos acotados 429/5xx. Convertir patrones en pequeñas funciones Python; no instalar toda la aplicación. | Enfocado a ficheros EPUB propios, no rastrea diariamente nuevas publicaciones de editoriales españolas. MIT verificada por GitHub. |
| **PrettyLazyLibWrapper** | https://github.com/bushibot/prettylazylibwrapper ; README, sección «NYT API key» | Auto-seguimiento de autores/series y vistas de novedades de audiolibros | **Cupos por autor/serie** y retención de preventas hasta su salida; advertencia sobre `sort newest` poco fiable. | Usa NYT Best Sellers para nuevas incorporaciones; NYT cubre mercado estadounidense y **NO es feed de lanzamientos de editoriales españolas**. Además depende de apps para adquirir libros; no instalar. |
| **Biblioteca Nacional de España** | https://datos.bne.es/ ; [ontología BNE](https://datos.bne.es/def/index-es.html) | Datos bibliográficos oficiales; documentación de endpoint SPARQL y descargas | Fuente complementaria futura para **comprobación de ISBN, autor y editorial** si endpoint funciona y sus datos coinciden. | No garantiza calendario inmediato ni preventas; no presentarla como API comercial de novedades. No implementar SPARQL sin probar resultados, condiciones y rendimiento. |

**Resultado de la búsqueda:** no se ha verificado un repositorio público que implemente el paquete exacto «novedades de sellos españoles + ISBN/portada reales + Amazon.es afiliado + publicación diaria autónoma sin API comercial». Tomar las **piezas** con pruebas: no copiar un proyecto completo ni tratar la cantidad de estrellas como evidencia de disponibilidad.

## B. Hallazgo decisivo en nuestro propio repositorio: YA hay 150 editoriales

`data/editoriales.json` actualmente contiene **150 fichas de editoriales publicables**, 136 con `publisher_type=tradicional`; filtrando también `independiente` y géneros de fantasía/juvenil/romance/romantasy/terror/misterio/thriller/ciencia ficción se obtienen **aproximadamente 69 candidatas** antes de revisar alias/cobertura.

**Debe ser el registro canónico** de nombre, slug, grupo y géneros. El motor NO debe mantener manualmente otra lista de 150 sellos ni generar una nueva página editorial solo porque Google Books mencione un nombre parecido.

- Nueva utilidad creada: [`scripts/reading_intake_publishers.py`](../scripts/reading_intake_publishers.py) → filtra `data/editoriales.json`, fusiona alias opcionales y genera claves canónicas. Excluye modelos de autopublicación o servicios editoriales (sin confundir `status=closed`: significa **recepción de manuscritos cerrada**, no editorial cerrada). Test `tests/test_reading_intake_publishers.py`.
- Un `website_url` de editorial puede llevar al **formulario de manuscritos**, NO al catálogo de lanzamientos. No rastrear automáticamente la URL a ciegas. Futuro adaptador de feeds debe apuntar a **fuente de novedades concreta y comprobada**, configurable y con fixture/regresión por sello.
- Algunos resultados bibliográficos publican el **grupo editorial** en lugar del **sello**. No asignar el grupo a un sello arbitrario: mantener `pendiente_sello` o verificar ISBN en editorial.
- `data/autores-red.json` contiene entrevistas de autores invitados, NO es la tabla de autores bibliográficos del nuevo catálogo. Reutilizar la fuente de PR #660 (`data/reading-authors.json`) si está disponible; no mezclar perfiles de entrevista con directorio de obras.
- En la página de editoriales mostrar sus libros usando la relación por slug canónico; en autores generar relaciones por autor normalizado/ID estable, sin crear biografías inventadas.

## C. Revisión de fuentes gratis, con límites comprobados

**Google Books:** [volumes.list](https://developers.google.com/books/docs/v1/reference/volumes/list), [volume schema](https://developers.google.com/books/docs/v1/reference/volumes), [uso de API key](https://developers.google.com/books/docs/v1/using) y [condiciones](https://developers.google.com/books/terms).
- `inpublisher:`, `orderBy=newest`, `langRestrict=es`, `maxResults<=40`, `showPreorders=true` están documentados. **Novedad en Google Books ≠ estreno confirmado en España**: verificar `publishedDate`, ISBN y sello editorial con fuentes de edición. Puede contener reediciones o fechas incompletas; un desarrollador de PrettyLazyLibWrapper informa que la ordenación por novedad no sirve como garantía de lanzamientos recientes.
- Requiere identificar la aplicación (clave API para cuotas). Los términos **no conceden permiso universal para republicar/copiar sus descripciones e imágenes**; Google dice que la API no sustituye a servicios comerciales de datos. Mostrar datos bibliográficos mínimos, resúmenes propios factuales y enlazar a fuentes.
- El ISBN 979-13 ya es un bloque nuevo de España: [Agencia del ISBN](https://www.agenciaisbn.es/) noticia de 2026. Mantener soporte ISBN13 978 y 979 y NO exigir derivar ISBN10 de ISBN13 `979`.
- Se ha mejorado `scripts/reading_intake_core.py`: rechaza etiquetas `OTHER` como ISBN aunque sus dígitos parezcan válidos; prefiere `ISBN_13`, usa `ISBN_10` como fallback verificado.

**Open Library:** [política de uso actual](https://openlibrary.org/developers/api), [dumps masivos](https://openlibrary.org/data). La documentación vigente **desaconseja usar su API como backend de harvesting/comercio de alto volumen**; indica 1 req/s por defecto y 3 req/s con `User-Agent` identificable. Para importación masiva recomienda dumps mensuales, que son voluminosos y no constituyen un feed diario de editoriales españolas. Por tanto, **no diseñar 500 llamadas individuales cada mañana**. Mantener como enriquecimiento esporádico por ISBN/fuente auxiliar con presupuesto y respuesta en caché, o descartar si no mejora cobertura.

**Amazon:** `AssociateNotEligible` sigue bloqueando Creators API para esta cuenta. Enlaces de búsqueda por ISBN con tag son una **salida de compra general**; no indican edición en stock ni ASIN verificado y pueden convertir peor que la ficha directa. Producto directo solo cuando otro dato fiable o Amazon autorizado comprueben ASIN y edición. Documentación de [formato de enlace directo](https://afiliados.amazon.es/help/node/topic/GP38PJ6EUR6PFBEC) y [tipos de enlaces](https://afiliados.amazon.es/help/node/topic/G5KVDATAT5RKBBBG). No usar sesiones de navegador, HTML de Amazon como fuente de datos, imagen Amazon API para Pinterest ni precios en caché permanente.

**BNE / Datos enlazados**: posible contraste gratuito para edición/ISBN/autor (SPARQL); no es una API demostrada de novedades. No convertirla en dependencia esencial ni presumir respuesta JSON sin prueba.

## D. Trabajo nuevo que YA queda en PR #661 para Codex

- [`scripts/reading_intake_core.py`](../scripts/reading_intake_core.py): ISBN10→13, ISBN 979-13, fecha de precisión año/mes/día, ventanas novedad 30/90 y próximo 30, alias de sello, enlaces Amazon producto/búsqueda, query y candidato de Google Books.
- [`scripts/reading_intake_publishers.py`](../scripts/reading_intake_publishers.py): genera sellos compatibles con las páginas de editoriales; sin red ni intervención.
- [`scripts/reading_intake_fetch.py`](../scripts/reading_intake_fetch.py): captación de candidatos Google Books con **`--fixture` offline o `--live` explícito**; no descarga portadas ni publica en la web, controla cuotas, reintentos y fallos por sello, deduplica ISBN publicados, estado idempotente por ISBN y rotación diaria de sellos para evitar que el presupuesto ignore siempre los últimos.
- [`data/reading-intake-sources.example.json`](../data/reading-intake-sources.example.json): configuración inicial, **conector deshabilitado**, alias de sellos y cuotas.
- Fixtures completamente ficticias `tests/fixtures/reading-google-books-2026.json`, pruebas unitarias `tests/test_reading_intake_core.py`, `tests/test_reading_intake_fetch.py`, `tests/test_reading_intake_publishers.py` y workflow de prueba `.github/workflows/reading-intake-qa.yml`. **No declarar superadas pruebas que no hayan ejecutado GitHub Actions.**

**Comandos de la fase de pruebas:**

```bash
python -m unittest discover -s tests -p 'test_reading_intake_*.py' -v
python scripts/reading_intake_fetch.py \
  --fixture tests/fixtures/reading-google-books-2026.json \
  --out .ci/reading-intake/pilot.json --today 2026-10-20
```

**Para acceso REAL** (futura ejecución voluntaria de Codex, no activada por esta PR): crear clave `GOOGLE_BOOKS_API_KEY` una vez, habilitar `google_books.enabled` en configuración real, ejecutar `--live --max-requests 30 --write-state`. Si un proveedor devuelve 403/429/404, conservar fichas publicadas y reportar error en vez de inventar datos. `--write-state` guarda candidatos, NO fichas publicadas ni resultados Amazon.

## E. Publicación: adaptar al mecanismo de esta web, no al de los ejemplos

Nuestra web ya tiene [`.github/workflows/deploy-pages.yml`](../.github/workflows/deploy-pages.yml): evento `push main` y `workflow_dispatch`, genera `.preview-dist`, valida artefacto, despliega con `actions/deploy-pages` y verifica la URL real tras publicación.

**Problema comprobado por GitHub:** un `git push` con `GITHUB_TOKEN` desde el cron NO dispara otro workflow con `on: push`, ni el build de Pages. [GitHub Token](https://docs.github.com/en/actions/concepts/security/github_token). Una forma compatible es **hacer el build, pruebas y commit en un solo proceso**, y luego activar el **`workflow_dispatch` del deploy existente**, evento exceptuado de esa limitación. Dar al token permiso `actions:write` solo donde proceda; comprobar que el deploy usa el commit recién publicado. **No hacer un segundo cron dedicado a escribir el mismo JSON.**

Hay un matiz: el workflow `deploy-pages.yml` solo deriva URLs cambiadas para IndexNow cuando recibe `push`. Con `workflow_dispatch` su fichero de cambio queda vacío. Codex debe preservar esta funcionalidad al integrar el disparo explícito, o tramitar IndexNow una vez validado el despliegue. No saltar el chequeo postdeploy ni sustituirlo por «push correcto».

[Guía oficial Pages Action](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## F. Decisiones acotadas para que Codex no gaste tokens

1. Priorizar **reutilizar `data/editoriales.json` y el build actual**, NO inventar nuevo CMS/Next.js, no instalar una librería entera solo para normalizar ISBN.
2. Google Books es **descubridor de candidatos**, no autoridad exclusiva para fecha, cubierta o publicación. Confirmar por sello cuando se pueda, registrar precisión. No etiquetar como «recién publicado» si solo sabemos el año.
3. **Una tarea programada para entrada/cambio**, un único lote/versionado de ficheros cuando haya novedades y el despliegue real por workflow existente. Mantener SQLite/caché solo si lo justifica volumen; para unas decenas de consultas diarias, estado JSON versionado basta.
4. Portadas y fragmentos: no inventarlos. Preferir enlaces oficiales y fichas bibliográficas útiles; no copiar sinopsis externas literalmente. Fotos de Pinterest en fase independiente, destino web siempre.
5. Probar con 20 candidatos reales de diversos sellos y **reportar cuántos cumplen los campos**, sin confundir «visto por Google» con «novedad editorial» o «disponible en Amazon».
6. Priorizar completar **ingesta → libro publicable → generador → despliegue**. Nuevos filtros, estudios SEO avanzados y Pinterest son posteriores. El cliente quiere mantenimiento 0 tokens/0 euros, no más paneles o herramientas.

**Pendiente real:** investigación de licencias de cada origen concreto de portadas, feeds editoriales publicados, conexión de fuente real al generador, configuración de API key y disparo de Pages. Estos puntos **no están resueltos por los proyectos analizados**. No habilitar autocarga masiva hasta la prueba en al menos una rama y comprobación del despliegue.


## G. Segunda comprobación y correcciones efectivas (20/10/2026, revisión posterior)

Referencias oficiales actuales: [Google Books `volumes.list`](https://developers.google.com/books/docs/v1/reference/volumes/list) documenta `orderBy=newest`, `showPreorders`, `maxResults<=40`; [Open Library API](https://openlibrary.org/developers/api) se actualizó el **9/10/2026** y declara expresamente que no es backend para harvesting comercial masivo; [Google Search `Book`](https://developers.google.com/search/docs/appearance/structured-data/book) separa **obra** de **edición** y exige ISBN de edición para casar registros. **No presentar a Google Books como feed exhaustivo de lanzamientos ni a Open Library como backend principal diario.**

**Error corregido en `scripts/reading_intake_fetch.py`:** antes el contador `max_requests` solo se incrementaba tras una respuesta HTTP **correcta**. Con 403/429/timeout repetidos, podía intentar **muchos más requests de los configurados** al iterar por todos los sellos. Ahora cada llamada intentada consume presupuesto, aunque falle, y `tests/test_reading_intake_fetch.py::test_failed_requests_still_consume_daily_budget` comprueba el comportamiento con una fuente que falla siempre. **Corrección adicional de cuota:** el cliente HTTP opera con **0 reintentos automáticos por defecto**: cada consulta lógica cuenta exactamente un intento HTTP. Antes realizaba hasta 3 intentos internos por resultado, lo que habría vuelto insuficiente el presupuesto de 30 consultas. Si más adelante se habilitan reintentos explícitos por 429/5xx, Codex debe añadir un contador físico compartido para no superar el límite de solicitudes. No leer la clave API de los logs.

**NUEVO `scripts/reading_editorial_metadata.py` y `tests/test_reading_editorial_metadata.py`:** extractor autónomo, sin red, de las etiquetas `<script type="application/ld+json">` **del HTML editorial que Codex ya haya recuperado de forma permitida**. Busca tipos `Book` (incluidas páginas `@graph`), contrasta ISBN13 e ISBN10, extrae **título, autor, sello, `datePublished` con precisión, portada HTTPS y URL de ficha editorial**. Ignora `Product` sueltos, ISBN diferentes, JSON inválido y campos ausentes. **No hace scraping HTTP ni copia sinopsis** y NO resuelve por sí solo el descubrimiento de novedades: hay que programar adaptadores individuales para catálogos/feeds de los sellos que realmente publiquen datos.

El extractor ofrece una forma barata de **corroborar fecha y cubierta de la edición** antes de marcar `fecha_publicacion` como novedad o publicar una ficha; junto con Google Books permite minimizar llamadas a GPT (cero por diseño).

### Secuencia de integración obligatoria, sin nuevos sistemas

1. Ejecutar todas las pruebas del branch (los dos comandos del workflow `reading-intake-qa.yml`), más `python scripts/reading_intake_fetch.py --fixture tests/fixtures/reading-google-books-2026.json --today 2026-10-20`. **No escribir estado en `main` a partir de fixture.**
2. Leer `data/editoriales.json` (fuente canónica, no duplicar 150 slugs), distribuir el presupuesto de Google Books entre sellos y guardar en staging solo ISBN válidos.
3. Aplicar fuentes editoriales **oficiales y específicas** para el ISBN detectado. Buscar una página/producto del sello a partir de URL editorial validada; recuperar JSON-LD público y comprobar coincidencia **exacta de ISBN de edición**. Datos incompatibles quedan pendientes, no se pisa una edición ya corregida.
4. Enriquecer plantilla web con portada auténtica, categorías y texto útil no inventado; preparar link directo Amazon si ASIN verificado o alternativa **rotulada como búsqueda** por ISBN. No resolver ISBN→ASIN mágicamente ni atribuir venta.
5. Regenerar ficheros web y la relación autor/editorial, aplicar tests y desplegar **únicamente el lote realmente cambiado**. Aprovechar `deploy-pages.yml`, no crear otro hosting.
6. Luego conectar la PR **#662**: regenerar el RSS en el mismo lote, respetar cola de pines y publicar solo tras verificar el dominio de Pinterest y conectar cada RSS al tablero adecuado. Si no hay nuevos libros, el cron diario **aun así debe avanzar el RSS** para que salgan los pines cuya fecha de cola ha llegado.

### Coste, límites y trabajo pendiente sin ocultarlo

La ingesta puede consumir **cero tokens de IA y cero licencias de software**; eso no garantiza cuota ilimitada en Google Books, datos editoriales completos, permiso automático de portadas ni disponibilidad en Amazon. La publicación RSS Pinterest no requiere API v5 ni OAuth, pero **sí cuenta Business, dominio reclamado y conexión de feeds en la cuenta**, pasos manuales una sola vez.

Google `Book` schema: **no copiar el ejemplo de Google "Book actions" con `ReadAction` como si la web fuese un vendedor directo**; son feeds para proveedores que participan en una funcionalidad específica, no una mejora SEO automática para cualquier blog. Mantener `Book` + `WebPage` de las fichas existentes con ISBN y autor verificados.

**Diferencia clave del proyecto:** no convertir el objetivo de "muchos libros" en cientos de páginas pobres. Medir libros descubiertos, confirmados, completos y realmente publicados; generar un informe de excepciones por fuente y aplicar un máximo de altas por lote.
