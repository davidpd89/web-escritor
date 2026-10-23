# Atlas mundial · APIs y descargas con fuentes y licencias (2026-10-21)

**PR hija de [#666](https://github.com/davidpd89/web-escritor/pull/666).** Investigación únicamente. Cobertura **global**, no España ni una lista corta de novelas. Datos sin revisión = CANDIDATOS, nunca afirmaciones publicadas.

## Tres capas, que NO se deben confundir

1. **Obras y autores** (obra≠edición, autor≠seudónimo): Open Library, Project Gutenberg, Wikidata.
2. **Geografía física y lugares culturales** (ciudad, librería, biblioteca, monumento, museo, calle): OSM/Geofabrik, GeoNames, Wikidata, catálogos institucionales.
3. **Vínculo preciso obra↔lugar / autor↔lugar / adaptación↔rodaje**: Wikidata P840/P915 con referencias, fuente institucional primaria, texto legalmente accesible, literatura académica / film commissions; revisión humana por vínculo. **No existe ninguna API gratuita demostrada que dé todas las escenas de todas las novelas del mundo**.

## Matriz por cobertura, precio y modalidad

| Fuente y docs oficiales | Cobertura / dato útil | Forma barata de uso mundial | Licencia / restricciones y riesgo |
|---|---|---|---|
| [Open Library dumps](https://openlibrary.org/developers/dumps) | Works, editions, authors, IDs; dumps mensuales | **Descarga mensual** y filtrado por país/idioma/destino en local con DuckDB, no pedir miles de obras a API | [Datos y licencias de Open Library](https://openlibrary.org/developers/licensing); volcado global multi-GB, infraestructura/disco NO gratis. No asumir que subject_places equivale a escenario literal. |
| [Open Library Search API](https://openlibrary.org/dev/docs/api/search) y [Subjects API experimental](https://openlibrary.org/dev/docs/api/subjects) | Localiza works por título/autor, subjects y lugares asociados | Solo enriquecimiento puntual por lotes pequeños, solicitar campos mínimos, caché | No usar como recopilación mundial de alta frecuencia; Subjects API experimental. |
| [Wikidata SPARQL](https://query.wikidata.org/), [API](https://www.wikidata.org/wiki/Wikidata:Data_access), [dumps](https://www.wikidata.org/wiki/Wikidata:Database_download) | Grafo multilingüe de obra, autor, ciudad, P840 ambientación, P915 rodaje | SPARQL con ID correcto y límites para piloto; **volcado local** si la cobertura y escala justifican coste de procesado | Datos estructurados [CC0](https://www.wikidata.org/wiki/Wikidata:Licensing). Referencias incompletas, falsos positivos y QIDs homónimos. |
| [Geofabrik](https://download.geofabrik.de/), [descargas](https://www.geofabrik.de/data/download.html), [índice JSON](https://download.geofabrik.de/index-v1-nogeom.json) | OSM de todo el mundo por continentes/países; librerías `shop=books`, bibliotecas `amenity=library`, librerías de segunda mano, museos, lugares de memoria | **PBF regional diario** en lotes con [PyOsmium](https://github.com/osmcode/pyosmium) o [osmium-tool](https://github.com/osmcode/osmium-tool) en lugar de extraer ciudades de API pública miles de veces | [ODbL](https://www.openstreetmap.org/copyright): atribución, obligaciones para bases derivadas. Archivos de país pueden superar GB; evitar planet dump en CI. |
| [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) | Candidatos geográficos de zonas acotadas | Solo ciudades del piloto y datos frescos; `out center tags` | Instancias públicas saturadas y pueden bloquear cloud IP. NO depender de Overpass para cosecha planetaria en cron. |
| [GeoNames descargas](https://www.geonames.org/) | Nombres de ciudades/localidades, variantes, geografía mundial, país/región | `allCountries.zip` o cada país; normalizar alias y geonameid | **CC BY 4.0**, atribución; geocoding de ciudades, NO escenario literario. API gratuita requiere cuenta y tiene restricciones. |
| [Project Gutenberg catálogos](https://www.gutenberg.org/ebooks/offline_catalogs.html) | RDF/CSV bibliográfico actualizado (XML diario/CSV semanal), obras clásicas | Importar catálogo RDF/CSV sin crawling; búsqueda de obras con texto reutilizable solo tras comprobar dominio público en país pertinente | Metadatos no demuestran ambientación; derechos del **texto completo** varían por territorio y libro. No copiar textos protegidos. |
| [Wikimedia Commons API](https://www.mediawiki.org/wiki/API:Imageinfo) | Fotografías de POIs, autores y monumentos con metadatos | Descubrir imágenes por QID/Commons y procesar solo candidatas autorizadas | Licencia y autor por **archivo**, autoría/atribución/uso comercial y derechos adicionales; fuente de imagen≠permiso automático. |
| [Google Books API](https://developers.google.com/books/docs/v1/using) | Bibliografía complementaria, ISBN, idioma, títulos traducidos | Resolver discrepancias puntuales; evitar duplicar importación de catálogo de lecturas | Cuota y condiciones variables, no importar sinopsis protegidas ni ratings como si fueran propios; no geolocaliza escenas. |
| [Europeana APIs](https://pro.europeana.eu/page/apis) | Patrimonio cultural europeo, imágenes, autor/lugar históricos | Enriquecer museos y materiales seleccionados | API key/registro y derechos a nivel objeto, NO fuente global primaria. |
| [Wikimedia Wikipedias / MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page) | Contexto para buscar bibliografía o lugares, referencias por idioma | Identificar fuentes primarias desde artículos, no volcar sus textos como copy propio | Texto Wikipedia **CC BY-SA**, distinto del CC0 de Wikidata; no mezclar licencias. |
| [Datos municipales y nacionales](https://www.data.gov/) / [data.europa.eu](https://data.europa.eu/) / [data.gov.uk](https://www.data.gov.uk/) / [data.gov.au](https://data.gov.au/) / [data.gouv.fr](https://www.data.gouv.fr/) | directorios patrimoniales, museos, bibliotecas y turismo | «Adapters» por territorio cuando un dato oficial tenga valor; sin bloquear el atlas mundial | Licencia y campos varían según portal y dataset. |

## Fuentes con costes evitable vs inevitables

- **Datos gratuitos no equivalen a coste operativo nulo.** Multi-GB de Open Library / Geofabrik y consultas de joins necesitarán disco/RAM/CPU; GitHub Actions no es almacén de dumps.
- Primer MVP: usar un índice **acotado** de obras candidatas existentes en el catálogo + export regional para ciudades aprobadas, y escalar a jobs de lotes cuando se mida tamaño real.
- Por país: elegir fuente más sólida; por libro: preferir work ID Open Library y QID, no ISBN de una traducción; por POI: OSM type+id/Wikidata QID/GeoNames geonameid.
- Diccionario multilingüe: `nombre_local`, `nombre_es`, `alias[]`, `language`; no inventar traducciones. La fuente del título de libro puede ser editorial en ES.
- `P840` («narrative location») no exige coordenada de calle; `P915` es rodaje de adaptación, no pasaje novelesco. Cuidado con lugares imaginarios y ciudades repetidas en distintos países.
- Los datos de vidas de autores nunca deben exponer un domicilio particular actual.

## MVP escalable propuesto

**M0:** 100–500 obras enlazadas al catálogo vigente (no importar nueva edición), 10 destinos diversos de regiones distintas, candidatos 50–200 POIs; solo 10–30 asociaciones verificadas se convierten en afirmaciones públicas. Estas cifras son objetivos de diseño, NO observaciones.
**M1:** 1.000–5.000 obras **indexadas como candidatas internas**, 100 destinos y POIs automáticos; no prometer 5.000 fichas públicas. Revisión editorial escalonada.
**M2:** importar por regiones/idiomas y cultura con prioridad dinámica basada en demanda; procesar dumps offline por fragmentos. Construir atlas mundial de POIs culturales aunque parte aún carezca de vínculo literario específico.
**M3:** grafo de rutas narrativas y datos de escenas para obras cuyo texto es legalmente reutilizable o cuya evidencia externa es sólida, con protección de spoilers.

La métrica de éxito no es el total de registros descargados sino `relaciones_verificadas / relaciones_propuestas`, exactitud geográfica, calidad de fuente y tráfico útil a fichas reales.

## Investigación pendiente antes de escribir importadores a escala

- [ ] Descargar un **pequeño fragmento** real de obras Open Library y examinar campos `subject_places`/IDs/estructura, sin sacar conclusiones sobre su exhaustividad.
- [ ] Evaluar géneros y países con mayor cobertura de P840 y P915 mediante consulta limitada y normalización de QID.
- [ ] Medir PBF por regiones con un adaptador de etiquetas y licencias; seleccionar PyOsmium/osmium-tool tras revisar avisos de paquetes.
- [ ] Confirmar descarga automática autorizada (etag/compresión) por proveedor y coste en CI; lotes fuera de `main`.
- [ ] Crear un glosario de categorías de POI y relaciones soportado en al menos diez idiomas sin cambiar claves internas.
- [ ] Definir condiciones de publicación en un feed RSS para Pinterest, únicamente en futuro y sin superar la PR #662.

## 21/10/2026 — nuevas fuentes complementarias revisadas y riesgos

**[World Historical Gazetteer (WHG)](https://docs.whgazetteer.org/content/technical/apis.html)**: **NO es una API anónima universal**; la documentación oficial exige token para la mayoría de endpoints y los datos son federados con licencias heterogéneas. Expone **Linked Places Format (LPF)**, nombre histórico, alias multilingües, coordenadas/áreas y épocas; es muy útil para vincular `Constantinopla`/Istanbul, ciudades antiguas, topónimos históricos y rutas de clásicos. Pero para registros con distribución contractual impedida devuelve **HTTP 451** aunque estén indexados; ante **HTTP 503** hay que reintentar y no guardar como «lugar inexistente». El `/api/sources/` contiene condiciones por proveedor (`redistributable`), no hay licencia global. **Estado**: fuente de reconciliación opcional con credenciales/atribución, NO alimentador gratuito principal, y nada se ha solicitado con token.

**[GeoNames](https://www.geonames.org/)**: descarga global diaria **CC BY 4.0**, alternativa fuerte a geocoding remoto repetitivo para normalizar ciudades, regiones y alias en lote offline. El servicio API web gratuito requiere cuenta y dispone de versión premium: preferir fichero `allCountries.zip` o extractos por país con atribución. No usar centroides de país para marcar escenas a nivel calle.

**[Open Library API Usage](https://openlibrary.org/developers/api)**: especifica directamente que la API gratuita **NO puede utilizarse como backend comercial masivo** ni para descargar cientos de libros uno a uno. Uso identificado máximo **3 req/s** y sin identificar **1 req/s** bajo sus términos; para nuestro objetivo global solo dumps mensuales y solicitudes humanas ocasionales. Los scripts de #671 **no** llaman esta API.

**Overture**: consultar [ADR-000](https://github.com/davidpd89/web-escritor/blob/research/viajes-literarios-atlas-2026-10-21/docs/ideas/viajes-literarios/README.md), apartado «Métrica Overture»; explorador taxonómico 78.517.770 vs notas de release 81.455.425. No mantener un único número exacto global sin comprobar misma edición/filtro.

Estos recursos complementan la arquitectura, no aportan por sí solos lugares literarios referidos a novelas. La evidencia de una escena seguirá siendo individual.
