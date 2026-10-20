# Encargo a Codex — Motor autónomo y gratuito de libros, novedades y afiliación (20/10/2026)

> **Estado de esta PR:** especificación técnica y utilidades deterministas de arranque. **No es el motor terminado ni habilita publicaciones.** Codex debe implementar aquí la integración completa **cuando el propietario lo encargue**, sin cobrar servicios externos ni llamar a modelos de lenguaje. No fusionar una especificación como si fuese producto.

## 0. Objetivo del propietario, literal en intención

Una vez configurado, davidportodiaz.com debe **descubrir, clasificar, añadir y actualizar automáticamente** libros españoles de editoriales tradicionales, en especial **novedades** y próximos lanzamientos, usando el diseño actual del catálogo de Coraline; mantener **editoriales** y **autores** relacionados; ofrecer un **enlace de afiliado Amazon.es** en la medida en que haya un destino identificable; dejar los libros listos para pines posteriores **Pinterest → ficha web → Amazon**. El propietario NO introducirá ISBN a mano todos los días, NO pagará DILVE/otros servicios, NO utilizará ChatGPT/LLM, sesiones de navegador ni tokens de IA en tareas recurrentes.

**Un único pipeline periódico y determinista, Python + APIs/fuentes gratuitas + JSON en repo + generadores existentes.** Google Sheets es opcional, nunca requisito del ciclo diario. No se prometen «todos los libros» de España: medir cobertura real con fuentes disponibles. No se puede deducir la presencia efectiva de un ISBN en Amazon.es sin consulta de producto fiable; un enlace de búsqueda afiliado es la alternativa visible cuando falta el ASIN.

## 1. Inspeccionar antes de escribir — estado del repositorio

Repositorio público: `davidpd89/web-escritor`, sitio `https://davidportodiaz.com`. PR #659 fusionada en main; **PR #660 abierta** el 20/10, con cambios de navegación, cuatro formatos de compra, perfil de autor, filtros comerciales y `assets/reading-market.json`. **Rebasar/revisar conflictos con #660** en el momento de implementar; no pisar los cambios de Codex que siga trabajando.

Reutilizar, no reimplementar:

- `scripts/build-reading-catalogue.py` + `scripts/templates/reading-catalogue.html.tmpl` → fichas estáticas `/recomendaciones/libros/<slug>/`, metadatos Book/SEO, filtros, sitemap e índice a través de scripts de build ya existentes.
- `data/reading-catalogue.json` (`schema_version: 1`, `categorias`, `libros`, `libro_categorias`), actualmente un único piloto `lib-0001`, Coraline, con 16 categorías.
- `data/reading-import-review.json` y `scripts/import-reading-sheet.py`: integración con hoja privada opcional; el importer actual requiere registro de revisión externo y **NO crea fichas por sí solo**.
- `scripts/discover-reading-books.py`: cliente Amazon Creators API que busca 3 consultas, 2 páginas por consulta y deja candidatos; **no es el pipeline que queremos**.
- `.github/workflows/reading-catalogue-sync.yml`: cron 06:30 UTC, disparo condicionado a `vars.READING_INTAKE_ENABLED`, hoy solo captura, informe efímero y **no publica**; adaptar/reemplazar conservando manejo de credenciales y compatibilidad.
- `docs/catalogo-lecturas-automatizacion.md`, `docs/catalogo-lecturas-flujo-pinterest-web-amazon.md`, `docs/catalogo-lecturas-contrato-drive.md`; tras implementación actualizar contradicciones, ya que parte de la documentación predecía Drive obligatorio.
- Revisar `editoriales/`, `data/content-registry.json`, `data/navigation.json`, `scripts/build-editoriales.py` y nuevos archivos de autores de PR #660 para reutilizar las fuentes de verdad de esos directorios.
- Mantener el sonido MP3 Elvira solo si existe descripción editorial propia y procede; **no generar un MP3 por cada libro al importar** sin un mecanismo gratuito demostrado. El contenido principal NO puede depender de audio.

**Precaución real**: el validador actual del builder exige `portada_local` en `/assets/reading-covers/`, dimensiones y varios metadatos de aprobación; su contrato de `url_amazon_afiliada` admite URLs directas de producto, pero **no búsquedas**. Planificar y probar una evolución del esquema, o representar búsqueda como tipo de enlace separado; no inyectar `/s?k=...` en el campo validado para URL de producto ni saltarse las validaciones. Campos de revisión existentes en JSON pueden seguir en lógica interna; no volver a añadir campos de derechos/alertas a Google Sheets, que el propietario pidió retirar.

## 2. Arquitectura única y barata

```
Cron GitHub Actions diario (public repo; runner estándar)
  → discovery: Google Books API (por sello, idioma, géneros; orden newest)
  → discovery opcional: RSS/feeds públicos de sellos + fuentes bibliográficas públicas
  → staging ISBN (deduplicado, estado, fuente/fecha)
  → enrichment por ISBN: Google Books / Open Library / fuente editorial permitida
  → normalización + clasificación reglada + autor/editorial + portada/fechas
  → enlaces Amazon: ASIN comprobado => /dp/ASIN?tag=...; si no => búsqueda por ISBN con tag
  → convertidor al schema del builder + pruebas por libro + cuarentena de incompletos
  → actualización incremental de JSON, imágenes, fichas y directorios
  → validación de publicación completa + cambios versionados → despliegue permitido
  → informe de métricas mínimo; sin tokens IA
```

**Propietario solo configura inicialmente** credenciales gratuitas y autoriza la automatización tras el ensayo. No pagos, no DILVE, no crear un sistema nuevo en Notion/Sheets, no generar conversaciones GPT. Los errores de alguna fuente o libro quedan registrados para el siguiente ciclo y NO bloquean los demás.

## 3. Fuentes y límites reales documentados

### Google Books API — núcleo gratuito de descubrimiento

Docs oficiales:
- API pública: https://developers.google.com/books/docs/v1/using
- `volumes.list`: https://developers.google.com/books/docs/v1/reference/volumes/list
- Campos de volumen: https://developers.google.com/books/docs/v1/reference/volumes

**Clave API de proyecto Google Cloud necesaria para llamadas públicas**; crear una clave restringida para Books API con una cuota/límite administrado. Comprobar cuotas y condiciones del proyecto antes de activar; no asegurar una cifra fija de solicitudes gratis sin comprobar el panel. No usar OAuth personal si basta API key. Guardar `GOOGLE_BOOKS_API_KEY` en GitHub Secrets, no en repo.

Ejemplo conceptual (URL codificada con `urllib.parse.urlencode`):

```python
params = {"q": "inpublisher:Salamandra", "orderBy": "newest",
          "printType": "books", "langRestrict": "es",
          "maxResults": 40, "startIndex": 0,
          "key": os.environ["GOOGLE_BOOKS_API_KEY"]}
url = "https://www.googleapis.com/books/v1/volumes?" + urlencode(params)
```

- `inpublisher:`, `subject:`, `isbn:`, `orderBy=newest`, `langRestrict=es`, hasta `maxResults=40`, paginación `startIndex`. `publishedDate` puede ser solo año/año-mes o referirse a una edición no publicada en España; puede faltar o ser inexacta. Una búsqueda **NO es feed exhaustivo** ni puede demostrar qué ha sido publicado «hoy»; validar candidatos contra editoriales y fechas.
- Variar consultas por **sellos** y algunos géneros, no «una búsqueda por cada libro». Permitir paginar con presupuesto de solicitudes por día y rotación de sellos. Ordenar de forma determinista; guardar cursor/última ventana consultada. Investigar `showPreorders=true` para próximos lanzamientos (las preventas se excluyen por defecto) y cotejar fechas con el sello.
- Procesar **únicamente** registros cuyo ISBN13 sea válido, `volumeInfo.language` español cuando venga, editorial incluida en lista blanca de **sellos** (no confundir con grupos), y datos pertinentes. Si no hay ISBN, candidato pendiente, no ficha.
- Etiquetas/editoriales normalizadas por alias; lista blanca no prueba distribución real en Amazon.
- No publicar por defecto las descripciones de Google Books copiadas íntegramente, ni descargar ciegamente sus imágenes: verificar condiciones de la API y usar alternativas propias/editoriales compatibles con el caso.

### Fuentes complementarias gratuitas

1. **Páginas/feeds oficiales de novedades** de sellos en nuestra lista. Registrar cada fuente en config (`tipo: rss|json|html`, URL, selector/API cuando proceda, `enabled`) y habilitar solo conectores que se hayan probado. No asumir que Penguin o Planeta tienen API pública gratuita o RSS estable; si solo hay HTML, adaptar con pruebas de regresión y respetar `robots.txt`, ritmo y respuesta. Usar principalmente para **detectar ISBN/fecha editorial**, no recopilar HTML comercial en masa.
2. **Open Library** para completar ediciones por ISBN (https://openlibrary.org/dev/docs/api/books) y metadatos de obra/edición; no confundir año de primera publicación con fecha de la edición española. Cubiertas: https://openlibrary.org/dev/docs/api/covers. **No rastrear masivamente la API de portadas**: ISBN cover endpoints limitados y no pensados para descarga en lote. Su documentación recomienda servir imagen desde su URL para webs, y hay que verificar edición/portada.
3. Google Books como proveedor secundario de datos del ISBN cuando otra fuente descubrió el libro; registrar procedencia por campo y confianza.
4. Amazon **Creators API opcional**, únicamente si la cuenta pasa de `AssociateNotEligible` a aprobada, **sin bloquear el motor principal**. Docs: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/troubleshooting/error-codes-and-messages. El error real del repo es 403 con cuenta no elegible: Amazon declara 10 ventas cualificadas en 30 días. Tener credenciales OAuth no equivale a autorización de catálogo. Verificar si cambia el requisito y operar el conector únicamente con cuota/permiso válido.
5. No añadir proveedores de pago, scraping de Amazon.es (incluido Selenium/Playwright en sesión del propietario), servicios de datos comerciales de terceros ni bots de ChatGPT. No trasladar el bloqueo de Amazon a otro canal de extracción de su catálogo. No capturar precios/ofertas ni reseñas Amazon si no se dispone de la vía permitida.

### Afiliación sin Creators API

Docs Amazon.es:
- https://afiliados.amazon.es/help/node/topic/G7N4YLMP8XV5WX2Q
- https://afiliados.amazon.es/promotion/gettingstarted
- https://afiliados.amazon.es/help/node/topic/GWJ4AHCH7U5LCL86

Existen enlaces de afiliado **a productos** y **a resultados de búsqueda**. El repo ya usa `davidporto-21`: leer tag de configuración real existente (`AMAZON_PARTNER_TAG`, comprobar en Afiliados si hace falta) y NO inventar otro.

- `asin_confirmado` obtenido de fuente fiable y correspondencia de título/autor/ISBN/edición → `https://www.amazon.es/dp/<ASIN>?tag=<tag>`; `tipo_enlace=producto_verificado`; botón `Ver en Amazon`.
- Si se conoce ISBN13, pero **no** se verificó ASIN/producto → `https://www.amazon.es/s?k=<ISBN13>&tag=<tag>`, correctamente URL-encoded; `tipo_enlace=busqueda_isbn`; botón `Buscar este ISBN en Amazon`. **NO anunciar «comprar esta edición» ni prometer que el producto existe o una venta.** Validar el formato de enlace y el modo de atribución con SiteStripe/panel de Afiliados antes de encender lote.
- Cuando no hay ISBN/edición comprobada → no afirmar URL Amazon del libro; dejar staging o link no disponible.
- En ambos casos navegación **solo tras clic explícito** desde la ficha; portada de la ficha clicable hacia Amazon si el enlace de ese libro es apropiado; Pinterest enlazará **siempre a la ficha propia**, jamás a Amazon.
- `autores` y `formatos_compra` de PR #660: no convertir por regla el ISBN10 de bolsillo en un ASIN sin contraste, ni mezclar Kindle/audiolibro/tapa dura; nunca fabricar precios, descuentos o stock.
- Afiliación visible conforme al programa, `rel="sponsored nofollow noopener noreferrer"`, `target="_blank"` cuando proceda, y enlaces de compra identificados. No garantizar comisión por cada visita.

## 4. Contrato canónico para ingesta (interno, separado del JSON web)

Añadir un **staging** versionado o fichero local `data/reading-intake-state.json` (o SQLite de trabajo → JSON final) e informe para errores. Evitar miles de pequeños archivos y grandes diffs innecesarios; no copiar el texto íntegro de resultados externos. Una entrada debe conservar, como mínimo:

```json
{
  "candidate_key": "isbn13:9788498382372",
  "work_key": "normalized:coraline|neil-gaiman",
  "isbn13": "9788498382372",
  "titulo": "Coraline",
  "autores": ["Neil Gaiman"],
  "editorial_sello": "Salamandra",
  "grupo_editorial": "Penguin Random House",
  "idioma": "es",
  "fecha_publicacion_edicion": null,
  "precision_fecha": "anio",
  "anio_publicacion": 2009,
  "primera_deteccion": "2026-10-20",
  "ultima_verificacion": "2026-10-20",
  "fuentes": {"isbn13": "https://...", "fecha": "https://...", "portada": "https://..."},
  "temas_fuente": ["Fantasía juvenil"],
  "categorias": ["fantasia-juvenil", "fantasia-oscura"],
  "portada_candidata": null,
  "amazon": {"tipo": "producto_verificado", "asin": "8498382378",
             "url": "https://www.amazon.es/dp/8498382378?tag=davidporto-21"},
  "estado_ingesta": "candidato",
  "motivo_pendiente": null
}
```

**Ejemplo ilustrativo del contrato**, no registro nuevo ni aprobación de datos; la primera entrada existente Coraline siempre conserva `id`, `slug`, edición y fuentes actuales. No volver a importar Coraline como un libro distinto.

Estados internos: `descubierto`, `enriquecido`, `publicable`, `pendiente_datos`, `publicado`, `descartado`; reproducibles por ISBN/candidato, con `last_error`, fecha y backoff. **No llenar la web con 404 de cubiertas, párrafos repetidos o ISBN falsos.**

La fuente de verdad pública continúa en `data/reading-catalogue.json` y extensiones de PR #660. Adaptar hacia `BOOK_FIELDS` y los validadores existentes, ampliando a `tipo_enlace=busqueda_isbn` sin reemplazar el tipo de producto. Relación **una obra/slug/URL canónica**, **varias categorías** y ediciones/formato en una única ficha cuando tengan identificadores fiables. Mantener `LIB-0001`/slug Coraline, las rutas anteriores y editoriales ya existentes.

## 5. Reglas deterministas, novedades y calendario

- Elegibilidad editorial: `editorial_sello` normalizado y **presente** en allowlist; alias y grupo asociados a cada sello. Rechazar autopublicaciones, resultados solo en inglés, genéricos `Independently published`, `KDP` y editoriales desconocidas **sin borrar candidatos** (pueden quedar pendientes).
- Selección de temas: taxonomía `data/reading-catalogue.json.categorias` + diccionario de materias/sinónimos por sello, Google categories y títulos. Clasificar con reglas **conservadoras** y explicar origen; no asignar `romantasy` solo porque contiene una pareja, ni `Halloween` por llevar «fantasía»; temporadas son asignaciones editoriales razonables, no fechas de publicación.
- Fechas: conservar precisión `AAAA`, `AAAA-MM` o `AAAA-MM-DD`. **NOVEDAD 30/90 días solo con fecha día/mes/año confirmada** y no futura; `próximamente` solo con fecha futura confirmada y ventana 30 días. Libros con solo año pueden presentarse con ese año, pero **no entrar en novedades**. No confundir `first_seen` con `published_date`.
- Calcular ventanas en hora civil `Europe/Madrid`. Al cambiar el día, libros salen/entran en filtros sin editar manualmente miles de fichas; el builder puede usar fecha actual al regenerar índice. `lastmod` de sitemap solo cambia ante contenido real, no por un cron sin cambios.
- Evitar duplicados por `ISBN13`, identificadores externos y clave de obra; **no fusionar por título solo** ni borrar reediciones/variaciones útiles. Una obra → una ficha canónica; múltiples ISBN/formatos opcionales asociados.
- Fecha editorial y editorial en el dataset con **fuente por campo** y fecha de consulta. Catálogos Google Books y Open Library son bases de datos colaborativas o mixtas: ninguna garantiza exhaustividad de novedades españolas.

## 6. Portadas, descripciones, autores y editoriales

- Priorizar **portada REAL de edición correcta**, fuente editorial o recurso bibliográfico comprobado. El builder actual exige imagen local válida, dimensiones, URL de fuente y varios campos internos de revisión. Integrar una política automática de selección/conversión proporcional **cuando la fuente lo permita**; portada opcional/preparada en staging, ficha pública solo con recurso admisible y de calidad. No inventar portadas ni llamar a ImageGen.
- Si una fuente devuelve imagen con condiciones de visualización externa (p. ej. Open Library), permitir futuro modo de imagen remota con dimensiones/fallbacks cuando se haya probado el contrato SEO/CSP/caché. **Las imágenes Creators API de Amazon NO deben descargarse/reconvertirse como assets propios ni utilizarse para un pin que enlace a nuestra web**; los activos Pinterest son independientes y se preparan en fase posterior.
- Sinopsis: NO copiar fichas comerciales en bloque ni reformular automáticamente el mismo párrafo de un catálogo. Sin LLM recurrente, generar un **resumen factual de plantilla** con título, autor, género confirmado, edición y premisa solo si hay una fuente descriptiva que lo respalde; si no, ficha bibliográfica útil y accesible. Codex debe diseñar campos y umbrales de valor real; no afirmar que se han leído obras ni inventar valoración propia.
- Editoriales existentes: primero enlazar a la página `/editoriales/<slug>/` si existe. **No fabricar nuevas páginas de editorial vacías** por un solo string; cuando un sello nuevo sea recurrente y verificado, crear una entrada normalizada que pueda alimentar `scripts/build-editoriales.py` y páginas de editorial, respetando HTML fuente/SEO que ya existe.
- Autores: reusar `data/reading-authors.json` y perfiles de PR #660. Generar enlaces entre libros, autores y editoriales; crear perfiles solo con datos contrastados y contenido suficiente. No volcar biografías externas literalmente; los libros del autor pueden mostrarse de forma automática por relaciones.
- SEO: una canonical por libro, Book/WebPage/BreadcrumbList con campos reales, metadatos distintos, sitemap/Pagefind/navegación y URLs permanentes; las páginas de «novedades» deben ser listados verdaderamente actualizados, sin generar variantes vacías ni textos repetidos. **Google considera spam la producción masiva de páginas de escaso valor**; optimizar por páginas útiles, no volumen bruto.
- `/recomendaciones/` y Cuaderno conservan URLs y guías históricas; no sacrificar contenido anterior ni crear 404. No editar artefactos generados a mano: cambiar generadores y ejecutar build.

## 7. Ejecución diaria completamente desatendida (después del piloto)

Separar **ingesta** de **publicación** dentro del mismo workflow. Propuesta: cron `17 6 * * *` UTC (evitar minuto 00, Github puede retrasar el horario) + `workflow_dispatch`. Sin servidor ni base de datos de pago.

Implementar:

1. `--dry-run` (sin commits/acciones remotas); `--fixture` para CI offline; `--max-requests`, `--max-new-books`, `--days-back`, `--publisher`; configuración con `enabled=false` hasta aprobación del propietario.
2. HTTP con `User-Agent`, tiempos de espera, rate limit global/por proveedor, `Retry-After`, backoff ante 429/5xx, control de cuota y **no reintentos infinitos**. Fallo Google Books → conservar fichas actuales y probar adaptadores secundarios; no publicar con respuesta incompleta.
3. Staging idempotente, ordenar por ISBN, hashes de cambios y marcas `first_seen`/`last_seen`. Reprocesar solo nuevos/tocados y los que hayan alcanzado TTL. Guardar contadores de `detectados/elegibles/descartados/publicados/errores`. No sobrescribir correcciones humanas ni metadatos más fiables por otra fuente débil.
4. Generar nuevas fichas **solo** si cumplen contrato y pruebas existentes; si faltan portada, fecha o correspondencia de edición, quedarse en pendientes, pero otros libros publican.
5. `data/reading-catalogue.json` → `build-reading-catalogue.py` → builds de shell, sitemap, Pagefind, pruebas Python + navegador/SEO y QA habitual. Hacer diffs **solo si cambia contenido real**. Reutilizar caches de dependencies en Actions.
6. GitHub Actions: plan de permisos mínimos para persistir cambios y publicar. **Preferencia**: rama de lote/PR y autopublicación únicamente después de que pasen los checks y con la autorización del propietario; comprobar que **PR/commits hechos con `GITHUB_TOKEN` no disparan siempre los workflows requeridos**. **Dato oficial:** un commit con `GITHUB_TOKEN` no desencadena GitHub Pages ni un posterior workflow `push`. Diseñar el proceso para que **despliegue efectivamente la web**, por ejemplo con `workflow_dispatch`/`repository_dispatch` o credenciales de GitHub App admitidas, y comprobar HTTP/HTML ya publicados, no solo el commit; asimismo tener en cuenta aprobación requerida en PRs creadas por Actions. Como alternativa, validar y publicar desde un único workflow controlado conforme a protección de `main`. NO activar escrituras ni auto-merge antes de resolver ese detalle. No deshabilitar checks ni forzar push en `main`.
7. Modo cotidiano automático tras la aprobación: limitar inicialmente 5 fichas/día, ampliar tras una semana estable. **No requiere validación humana para cada libro si pasa condiciones automáticas acordadas**; casos ambiguos, fuentes con discrepancias o imágenes no verificables quedan en staging; informe semanal de excepciones si se desea. Informar fallos sin detener todo.
8. Cron/servicio 0 tokens de IA, sin OAuth de navegador, sin scraping Amazon y sin secretos en publicaciones. Repositorio es **público**; Actions en runners estándar para repos públicos es gratuito según GitHub, sujeto a cambios/uso y a los servicios externos.
9. El futuro proceso Pinterest lee exclusivamente fichas **publicadas**, activo de pin independiente y categorías elegidas; no automatizar Pinterest en esta PR. Destino `https://davidportodiaz.com/recomendaciones/libros/<slug>/`, después portada o botón web a enlace afiliado Amazon.

## 8. Experimento previo obligatorio: 20 libros actuales reales, no 20 inventados

Preparar una prueba **real** sobre un subconjunto de ≥5 sellos distintos y un periodo definido en 2026:
- Ejecutar Google Books con clave propia y algunas fuentes editoriales verificables.
- Medir cuántos registros tienen ISBN13 correcto, idioma ES, editorial de lista blanca, fecha completa, portada correspondiente a edición, enlace Amazon producto verificado vs búsqueda y sinopsis útil. **No inventar que hemos probado la API o 20 libros si la cuenta/cuota no permite consulta.**
- Capturar ≥20 **candidatos reales** cuando existan; clasificar `publicable` vs `pendiente`, explicar por qué. **No exigir publicar 20 si faltan datos auténticos.**
- Ejecutar piloto offline con fixtures para CI: 1 Coraline preexistente y mínimo 3 ISBN nuevos sintéticos aislados **solo de pruebas**, varios tipos de fecha, portada ausente, categoría cruzada, ediciones múltiples, repetición cron, fallo de API y backoff.
- QA: sin cambios en segundo run, sin duplicados, sin canonicals cambiadas, importador compatible con Sheets, sin precios/valoraciones inventados, cálculos 30/90/30 correctos y botón distinguible producto/búsqueda. Índice y sitemap consistentes.
- No desplegar masivamente antes de verificar cobertura/plantillas en móvil, la atribución Amazon del enlace de búsqueda y la interacción con PR #660.

Métricas de aceptación **del mecanismo**: sin coste recurrente obligatorio, **cero llamadas LLM**, ejecución desatendida, trazabilidad, reintentos y recuperabilidad, resultados cuantificados por fuente, ficha real consistente con Coraline y canónica estable; las cifras de cobertura dependen de las APIs y no se garantizan.

## 9. Orden de implementación para ahorrar tokens y diffs

1. **Revisar PR #660 + contrato final de libros**, resolver importador, ediciones/ASIN, portada local/remota, productos vs búsquedas afiliadas y taxonomía, antes de introducir datos nuevos.
2. Implementar **un solo** `scripts/reading_intake_core.py` determinista (en esta PR se entrega base), tests y config de sellos; luego adaptador Google Books con API key y proveedor Open Library opcional. Reusar funciones en lugar de crear capas grandes de clases y abstracciones.
3. Implementar almacenamiento de estado, conversión al JSON y actualizaciones editoriales; enlazar al builder/QA.
4. Implementar publicaciones incrementales usando workflow actual, primero manual/dry-run y tests, después cron y publicación autorizada.
5. Ensayo 20 candidatos + métricas, actualizar documentación, explicar con claridad qué datos/campos faltan de fuentes; dejar claro que Amazon Creators API continúa opcional.
6. **Esperar aprobación del propietario para activar auto-publicación**; una vez activado el sistema debe ser autónomo.

### Hechos y documentación consultada (20/10/2026)

- Google Books API requiere identificador/API key para datos públicos y permite búsquedas por editorial, newest y 40 resultados por página: https://developers.google.com/books/docs/v1/using ; https://developers.google.com/books/docs/v1/reference/volumes/list
- Contenido/cubiertas Google Books sujetos a condiciones, no es licencia genérica para reventa/redistribución: https://developers.google.com/books/terms ; https://developers.google.com/books/docs/overview
- Open Library ISBN/ediciones: https://openlibrary.org/dev/docs/api/books ; portadas API/rate limit: https://openlibrary.org/dev/docs/api/covers
- Creators API 403 `AssociateNotEligible` por 10 ventas cualificadas/30 días: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/troubleshooting/error-codes-and-messages
- Amazon.es permite enlaces de búsqueda/producto con afiliación: https://afiliados.amazon.es/help/node/topic/G7N4YLMP8XV5WX2Q ; https://afiliados.amazon.es/promotion/gettingstarted
- Uso de datos Amazon y necesidad de que su contenido enlace a Amazon: https://afiliados.amazon.es/help/operating/policies
- Acciones gratuitas en repo público con runner estándar: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Schedule puede retrasarse/desecharse: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Restricciones de `GITHUB_TOKEN`, PRs creadas por Actions y despliegue de GitHub Pages: https://docs.github.com/en/actions/concepts/security/github_token
- Google desaconseja páginas a escala de escaso valor: https://developers.google.com/search/docs/essentials/spam-policies

**Entrega que Codex debe producir en ESTA PR al retomarla**: código del pipeline funcionando con pruebas, contrato web compatible, workflow parametrizado, informe de ensayo con cifras reales, QA y guía de activación en pocos pasos. No basta con añadir otra propuesta/documentación o un script que liste candidatos.