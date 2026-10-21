# Viajes literarios · propuesta de producto e investigación (v0.1)

> **ESTADO: HISTÓRICO.** La fuente única de decisiones actuales es [README.md — ADR-000](README.md), actualizado el 21/10/2026. Este documento se conserva como investigación inicial para trazabilidad: las rutas alternativas, estados de PR y fases que aparezcan aquí no sustituyen el ADR. No añadir nuevas decisiones en este fichero.

**Fecha:** 2026-10-21. **Estado:** investigación, no implementación. **Repositorio:** davidpd89/web-escritor. **Propietario decide el lanzamiento.**

## 1. Visión y promesa editorial

Crear un atlas de lugares relacionados con libros y escritores para descubrir destinos desde tres puertas equivalentes:

1. **Voy a una ciudad** → librerías históricas, bibliotecas, museos, casas visitables de autores, monumentos, escenarios de novelas y rodajes identificados, rutas, eventos y obras relacionadas.
2. **Me interesa un libro o saga** → lugares narrados, reales que inspiraron la obra, localizaciones de adaptaciones y lugares biográficos del autor; cada tipo explícito y separado.
3. **Me interesa un autor** → lugares **públicos** y documentados asociados a su trayectoria, obras, rutas y recursos culturales. No mostrar direcciones privadas ni residencias particulares actuales.

Propuesta de nombre visible: **Viajes literarios**. **Corrección tras auditoría del 21/10:** en main ya existe el builder original de Atlas con canonical **/atlas-literario/**, aunque no publica fichas; preferir **/atlas-literario/** como ruta técnica provisional y «Viajes literarios» como título editorial. **/viajes-literarios/** queda como alternativa, nunca segunda URL indexada en paralelo. Ver [04-auditoria-legado-prs-2026-10-21.md](04-auditoria-legado-prs-2026-10-21.md).
Entrada desde Cuaderno, enlaces recíprocos al catálogo de **/recomendaciones/** y futuras fichas **/recomendaciones/libros/<slug>/**; sin crear un segundo catálogo de obras.
Cada lugar tiene UNA ficha canónica; aparece bajo múltiples libros, ciudades, temáticas y rutas mediante relaciones. Un destino puede incluir cero, una o muchas obras; una obra puede enlazar múltiples destinos.

**Decisión de investigación A (recomendada):** base de datos editorial con sincronización controlada desde Sheets, exportación versionada y páginas HTML estáticas; buscador/filtros y mapa opcional consumen JSON local. El visitante no lanza búsquedas IA ni geocodifica en directo.
**Alternativa B (no recomendada en lanzamiento):** responder en vivo usando buscador/LLM/varias APIs en cada visita. Mayor coste, latencia, riesgo de atribuciones falsas, rotura de servicios, privacidad y dificultad de indexación. Un asistente IA sí puede ayudar a INVESTIGAR candidaturas en fase editorial con revisión humana.

## 2. Descubrimiento dentro del repositorio: NO partir de cero

Ya existe **data/atlas-literario.json** desde 2026-08-18, con seis categorías y 12 propuestas en estado planned; también **scripts/build-atlas-literario.py**, **assets/atlas-literario.{js,css}** y **tests/test-atlas-literario.py** de la [PR #59 ya fusionada](https://github.com/davidpd89/web-escritor/pull/59). El generador **no crea páginas individuales**, pese a que sus tarjetas apuntan a ellas. Incluye Harry Potter (separar novela/rodaje), Don Quijote, Drácula/Whitby, Joanina, Strahov, Long Room, Urueña, Barrio de las Letras, Livraria Lello, Hay-on-Wye, Wigtown y bibliotecas singulares españolas. Este material es un **backlog semilla**, no prueba de que haya fichas publicadas ni de que sus asociaciones estén verificadas.
No renombrar, eliminar o publicar esas entradas automáticamente. En futura implementación, migración idempotente con equivalencia entre antiguo slug y nuevo ID, trazabilidad y decisión editorial expresa.
 
Arquitectura real del sitio, observada en main:
- Web estática HTML/CSS/JS; hay scripts propios para el catálogo y publicación.
- /recomendaciones/ tiene filtros, fichas, canonical y rutas de libros; **docs/catalogo-lecturas-contrato-drive.md** documenta entidades Libro/Categoría y Sheets opcional.
- data/content-registry.json, data/navigation.json, scripts/build-section-context-nav.py, scripts/build-sitemap.py, scripts/build-pagefind-index.py, generadores de shell y reglas de CSP/SEO son dependencias existentes.
- Las PR recientes de lecturas (ej. #660, #661, #662 y #665) tienen funciones en distintos estados: NO depender del código no fusionado, no modificar sus ramas ni bloquearlas.
- No insertar HTML nuevo, no tocar navegación ni maquetación, no abrir Actions, no activar crons y no fusionar esta PR.

## 3. Qué debe ver el visitante (idea de UX, no diseño cerrado)

**Hub:** búsqueda libre; filtros de país/ciudad, libro, autor, tipo de lugar, vinculación, visita (visitable/exterior/no visitable), temática, accesibilidad y grado de verificación. Tarjetas visuales con fotografía autorizada, ciudad, tipo de conexión y breve explicación. Alternar vista lista y mapa; lista navegable sin JavaScript. Conteo y filtros combinables con estado vacío útil.

**Destino /viajes-literarios/destinos/<ciudad>/**: introducción editorial original y práctica; mapa con puntos; secciones librerías, bibliotecas, escenarios, casas-museo, lugares de rodaje, rutas; conexiones a libros del catálogo, enlaces oficiales. No crear páginas indexables por filtros arbitrarios sin contenido propio.

**Lugar /viajes-literarios/lugares/<slug>/**: qué es; por qué interesa al lector; tipo de relación con cada obra; hechos contrastados y fuentes; información de visita únicamente con fecha y fuente; mapa/coordenadas si se verifican; fotos con licencia; relaciones a destinos/rutas/libros. Si es zona amplia o conexión literaria no localizable exactamente, no fabricar un punto preciso.

**Obra:** reutilizar primero ficha existente en /recomendaciones/libros/; incluir bloque «Viajar por sus escenarios» y enlace a lugares. Para títulos aún no existentes, relación editorial interna hasta su alta; evitar fichas duplicadas o vacías.

**Rutas:** lista de paradas con orden editorial y modo recomendado; no prometer duración/distancia/entrada sin datos oficiales o cálculo real. Filtro de spoiler (sin spoilers por defecto) y aviso cuando una ruta pertenezca a una adaptación y no al libro.

## 4. Taxonomía de conexiones (no mezclar)

- **ambientacion_literal:** lugar real explícitamente identificado en la narración.
- **inspiracion_documentada:** sitio real que inspiró la obra según fuente sólida.
- **rodaje_adaptacion:** lugar donde se filmó una película/serie: enlazar adaptación concreta, NUNCA atribuirlo automáticamente a la novela.
- **vida_autor_publica:** casa-museo, nacimiento u otro lugar biográfico documentado, visitable o exterior público. No domicilios privados.
- **biblioteca / libreria / museo / archivo / monumento / festival:** lugares culturales sin necesidad de vincularse a una obra concreta.
- **homenaje / ruta_oficial:** lugar conmemorado o ruta diseñada por institución.
- **atribucion_popular_no_verificada:** conservar para fact-check editorial, EXCLUIR de resultados afirmativos; si se publica un artículo sobre el mito, etiquetarlo claramente.
- **ubicacion_ficticia/no_geocodificable:** relación narrativa sin marcador exacto (se conserva como texto).

El vínculo tiene estado propio: propuesto, investigando, verificado, rechazado o retirado. «Verificado» exige evidencia de la asociación concreta, no solo de que exista el lugar.

## 5. MVP recomendado y evolución

**Fase 0 · investigación continua (ESTA PR):** inventario del repo; fuentes/competidores/proyectos/licencias; modelo de datos y encabezados Sheets; criterios de calidad; preguntas abiertas; piloto definido. Solo Markdown de investigación.

**Fase 1 · piloto editorial NO público:** seleccionar tres pruebas de comportamiento, no una carga masiva:
- Madrid: Barrio de las Letras + librerías/bibliotecas de referencia (verificadas individualmente).
- París: librerías y un escenario de novela documentado, comprobando que la obra menciona un sitio real.
- Una saga adaptada: distinguir localización de rodaje de lugar narrativo, por ejemplo Juego de tronos. No asociar ciudades hasta comprobar fuente y tipo.
Los 12 elementos de data/atlas-literario.json forman backlog alternativo. Las propuestas no son afirmaciones de visita, horarios o relaciones.

**Fase 2 · datos:** acordar con el usuario Google Sheets maestro, roles, registros y caducidades; importar fuentes verificadas y resolver duplicados. Google Drive actúa como mesa editorial, NO como backend del navegador.

**Fase 3 · ingeniería (PR separada, solo cuando se autorice):** validador, importación snapshot a JSON, páginas estáticas y fichas, listas/filtros, enlaces recíprocos, mapa si supera prueba de rendimiento y licencias; integración QA y SEO.

**Fase 4 · contenidos y distribución:** ampliar destinos/libros, actualizar datos prácticos, conectar Pinterest → ficha de lugar/destino → fichas de libros → Amazon cuando enlace afiliado real exista y se declare. No presuponer afiliación de hoteles o actividades.

## 6. Principios no negociables

- No inventar citas, coordenadas, escenas, inspiraciones, horarios ni domicilios. Cada asociación pública tiene evidencia específica y fecha de verificación.
- No confundir obra, adaptación, biografía y promoción turística; separar tipo de afirmación y nivel de certeza.
- No copiar artículos de blogs, guías o sinopsis; redactar texto propio y enlazar las fuentes.
- No reutilizar fotografías por estar visibles en Internet; comprobar licencia, atribución, posibles cambios y contexto comercial.
- Revisión humana antes de pasar contenido público. Estado borrador nunca accesible por generador público o buscador.
- Preservar URLs, indexación y rendimiento de la web actual. Filtros no deben multiplicar páginas duplicadas.
- Progreso se anotará en la PR y en estos archivos; no convertir esta investigación en un desarrollo automático accidental.

## 7. Decisiones pendientes del propietario (no bloquean la investigación)

Nombre definitivo y ubicación de menú; nivel de detalle en bibliotecas/librerías frente a novelas; mapas desde el MVP o fase posterior; países e idiomas priorizados; volumen aceptable de revisión editorial; posibilidad de rutas descargables; atribución/monetización adicional; momento de crear Sheets y secretos. Por defecto, investigar ES-ES, localizaciones reales y alcance internacional gradual.

Documentación complementaria: **01-modelo-datos-drive.md**, **02-fuentes-y-repos.md**, **03-piloto-y-qa.md**, **04-auditoria-legado-prs-2026-10-21.md**, **05-captacion-gratuita-automatizacion-2026-10-21.md**, **06-pilotos-reales-evidencias-2026-10-21.md** y **07-reutilizacion-tecnica-y-piloto-sin-pago.md**.

## 8. Programa de investigación mundial organizado en PR hijas (actualizado 21/10/2026)

**Alcance corregido por el propietario:** mundial (no Madrid/París como límite). Madrid y París son solo pilotos editoriales, igual que una saga adaptada. El objetivo a largo plazo es el mayor número sostenible de **obras, ciudades y lugares verificables**, no publicar automáticamente todas las coincidencias no contrastadas. Usar dumps estructurados, no miles de llamadas LLM.

Todas las PR hijas apuntan a main como **cambios independientes** y enlazan a esta PR padre para seguimiento; **no son ramas Git apiladas**. Orden lógico de revisión:
1. [#667 — fuentes mundiales](https://github.com/davidpd89/web-escritor/pull/667): Open Library dumps, Wikidata, Geofabrik, GeoNames, Gutenberg, Commons, licencias, consultas y presupuesto de APIs.
2. [#668 — código MIT vendorizado](https://github.com/davidpd89/web-escritor/pull/668): detector de lugares y comprobador de frescura de Read the Places, con normalizador y licencia, copias originales **sin integración**; matriz de software libre reutilizable.
3. [#669 — contrato de datos v1](https://github.com/davidpd89/web-escritor/pull/669): JSON Schema, validador de referencias, tests sintéticos (sin ejecutar); debe pasar validación antes del merge.
4. [#670 — arquitectura y fases](https://github.com/davidpd89/web-escritor/pull/670): pipeline incremental, snapshots, homogeneización y publicación serializada, futuras P5-P11.
5. [#671 — muestreador Open Library offline](https://github.com/davidpd89/web-escritor/pull/671): lectura en streaming de Works con lugares candidatos y límites, sin API ni LLM; falta cotejo de dump real, checkpoint mundial y contrato.
6. [#672 — prototipo SEO y rendimiento](https://github.com/davidpd89/web-escritor/pull/672): HTML estático para destinos/lugares y JSON de facetas por destino; no mapas en render inicial ni filtros generando URLs rastreables. Vista previa sin integración ni pruebas ejecutadas.
7. [#673 — Overture Places POIs mundiales](https://github.com/davidpd89/web-escritor/pull/673): extractor offline por bbox de lugares culturales, con IDs GERS y taxonomía 2026; no afirma relación con novelas.

**Importante:** el programador de [#661](https://github.com/davidpd89/web-escritor/pull/661) ya publica libros y restringe rutas generadas. No autorizar otro autopublicador simultáneo; en la fase de ingeniería real hay que ampliar el gate explícitamente o empezar mediante PR manual. [#662](https://github.com/davidpd89/web-escritor/pull/662) puede servir posteriormente para Pinterest.

**No se han descargado dumps enormes, ni usado claves, ni ejecutado CI/Actions, ni puesto nuevos lugares en producción.** Cada PR registra exactamente código, documentación y sus limitaciones. Ninguna está fusionada; las fases futuras se abren solo con contenido real.

### Hallazgos nuevos de rendimiento y SEO (21/10/2026)

- [Overture Places](https://docs.overturemaps.org/guides/places/) proporciona decenas de millones de POIs culturales/comerciales globales, con licencias de datos permisivas (según fuente) y descargas GeoParquet. El [explorador de la edición septiembre 2026](https://docs.overturemaps.org/guides/places/taxonomy-explorer/) registra 78.517.770 POIs **generales**, no narrativas literarias. En esa edición `categories` fue eliminado y reemplazado por `basic_category/taxonomy`. Esto entra en [#667](https://github.com/davidpd89/web-escritor/pull/667) y [#673](https://github.com/davidpd89/web-escritor/pull/673).
- [Google recomienda controlar filtros por facetas](https://developers.google.com/crawling/docs/faceted-navigation) para no generar espacios infinitos de URL que desperdician rastreo. Crear canonicals de destinos/lugares aprobados, no miles de búsquedas indexables.
- [Google eliminó sitelinks search box en 2024](https://developers.google.com/search/blog/2024/10/sitelinks-search-box). El `SearchAction` antiguo del fichero MIT upstream no debe copiarse como ventaja SEO.
- [Google advierte sobre abuso de contenido a escala](https://developers.google.com/search/docs/essentials/spam-policies). **Descargar 78M registros ≠ publicar 78M páginas**. Mantener cola masiva interna, pero producir solo páginas que aporten información original, datos contrastados y utilidad real.
- [#672](https://github.com/davidpd89/web-escritor/pull/672) incorpora cachos JSON pequeños por destino; filtros país/ciudad/libro/autor/relación descargan únicamente el shard necesario en una implementación posterior.

### Prototipo adicional de filtros por demanda (21/10/2026)

En [#672](https://github.com/davidpd89/web-escritor/pull/672) están ya archivados código del [filtro JS sin framework](https://github.com/davidpd89/web-escritor/blob/feat/atlas-seo-renderer-prototype-2026-10-21/research/atlas-ui/atlas-filters-preview.js) y [HTML accesible de ejemplo](https://github.com/davidpd89/web-escritor/blob/feat/atlas-seo-renderer-prototype-2026-10-21/research/atlas-ui/filters.example.html). País/city/tipo/obra/autor/relación/texto, 30 elementos por página, enlaces sanitizados, reintento tras fallo de red, `Intl.DisplayNames('es')`, hash para evitar URLs SEO de facetas y JSON por destino sólo bajo interacción. **No se ha integrado ni probado en navegador**; sigue el circuito de #672. Pendiente extensión posterior para buscar una obra **globalmente** antes de elegir ciudad, sin cargar un índice gigantesco: Pagefind existente o índice invertido de obras repartido por prefijos/países.
