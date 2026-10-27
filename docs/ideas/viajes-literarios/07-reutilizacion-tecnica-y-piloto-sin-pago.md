# 07 · Patrones reutilizables, costes y experimento sin pago (21/10/2026)

## Auditoría concreta de repositorios públicos — lo que aporta cada uno

**[Read the Places](https://github.com/markselby9/readtheplaces.com)**, [schema real](https://github.com/markselby9/readtheplaces.com/blob/main/schema/waypoint.schema.json) — fuente de valor más próxima a nuestro caso novela↔punto. Esquema JSON Schema 2020-12 con:
- `progressLabel` narrativo, `character`, `placeCertainty=explicit|inferred|inspired_by|disputed`, `certaintyNote`, `sources[]`, `editorialStatus`; diferencia trama/certidumbre y guarda qué personaje recorre el lugar.
- `quoteAnchor` y `passage` son opcionales dependiendo de base legítima del texto; `position` se calcula del texto de origen. **No copiar fragmentos protegidos** ni exigir texto íntegro para libros recientes; usar capítulo o descripción propia y referencia de edición verificable.
- **Atención a coordenadas:** su `coords` es GeoJSON `[longitud, latitud]`, mientras que nuestro borrador Sheets usa columnas `lat` y `lon` distintas. El exportador debe convertir correctamente y testear posición. Ficheros `books/...` con datos CC BY-SA 4.0: no importarlos sin evaluar share-alike, atribución y compatibilidad; implementar concepto editorial propio, no clonar base.
- Mejora que nos interesa: relación con **personaje y punto narrativo** en tabla `05_RELACIONES`: campos opcionales `personaje_nombre`, `capitulo_referencia`, `orden_en_obra` y `certeza_narrativa`. Solo necesarios para obra/punto; no cargar las fichas de librerías con campos de novela.

**[Akhand](https://github.com/CodeRustyPro/akhand)**, README inspeccionado:
- Proyecto experimental completo Next.js + FastAPI, GeoJSON, filtros, MapLibre, export CSV; `backend/data/ingest.py` usa Open Library por lugar, `backend/data/wikidata.py` P840, NER local spaCy + GLiNER y geocoding. README reporta `working scaffold=11,073` y `strict release=9,057`; **no asumir que esas 9.057 relaciones estén todas editorialmente verificadas**.
- El README reconoce localizaciones aproximadas por centroides, limitación de Open Library/Wikidata, extracción de resúmenes y dependencia opcional de API Gemini (no completamente gratuita ni necesaria para MVP). La fuente de inspiración «Cities in Fiction» trae sus propias condiciones.
- **No hay archivo LICENSE en raíz** en la inspección realizada: solo referencia de arquitectura/algoritmos, no copiar ni redistribuir su código/datos sin aclarar licencia. Tampoco migrar nuestra web estática a Next.js/FastAPI: coste de mantenimiento injustificado en fase inicial.
- Patrones reusables conceptualmente: snapshot versionado, `/api/meta` de procedencia, calidad antes de release, degradación a catálogo estático, caché y reanudación de ingesta; podemos adaptar esos principios al builder actual sin servidor.

**[Literary Atlas](https://github.com/rostam/literary-atlas)**, README inspeccionado:
- Pipeline offline genera JSON y topología simplificada; mapa **SVG** simple sin dependencias cartográficas con hoja HTML estática. 191 reseñas, 147 ubicadas en mapa; reconoce **44 sin punto real** y 8 lugares ficcionalizados, y que sus perfiles fueron generados por modelo sin verificación manual.
- Opción **baratísima** si solo queremos mapa global de país/ciudad, no un callejero preciso: SVG o imagen estática con enlaces y leyenda. Para librerías por calle seguirá siendo preferible mapa con teselas.
- Sin LICENSE visible en la raíz; NO reutilizar código/datos; sí patrón conceptual «no representar ficción sin coordenada con pin falso».

**[Bookish Bay Area](https://github.com/yvonneyeh/bookish-bay-area)**:
- Búsqueda combinada de libros y bibliotecas cercanas, web tradicional Python/Flask; es referencia de cruces libro↔biblioteca. No adoptar Google Maps ni el stack por defecto; no consta LICENSE raíz.

## Qué añadir en futuro contrato de Sheets (aprobación pendiente)

Añadir a `05_RELACIONES` opcionales:
`personaje_nombre`, `capitulo_referencia`, `orden_en_obra`, `certeza_narrativa`, `origen_adaptacion` (ID de producción).

Añadir a `02_LUGARES`:
`wikimedia_commons_file`, `accesibilidad_fuente_url`, `fecha_revalidacion_operativa`, `fuente_geo`, `precision_geo`. No fabricar calles de ficción.

Añadir a tabla `06_FUENTES`:
`dataset_id`, `licencia_datos_url`, `attribution_text`, `last_modified_or_etag`, `uso_comercial_revisado`, `retention_policy`. La licencia de metadatos, la de fotografías y la del software son registros independientes.

Para placas literarias introducir tipo `placa_homenaje` y relación `homenaje_placa`. **Una placa alude a una obra, pero no convierte esa dirección automáticamente en lugar narrado.**

## Comparativa de opciones de mapa sin pago por solicitud de visitante

| Opción | Desarrollo | Coste de software | Infraestructura/terceros | Cuándo |
|---|---|---|---|---|
| Sin mapa integrado; ficha con coordenadas y enlace cartográfico externo | mínimo | cero | hosting actual y enlace a mapa tercero al pulsar | **Lanzamiento ultraligero y seguro** |
| SVG propio con mapa ciudad esquemático, sin mapa de calles | bajo | cero | hosting actual; no permite callejero detallado | Mapa resumen opcional accesible |
| Leaflet con tiles autorizadas según proveedor y política | bajo-medio | Leaflet licencia BSD-2 | peticiones externas, políticas OSM y posible coste según tráfico | Prototipo con pocos puntos, consentimientos/privacidad evaluados |
| MapLibre + subconjuntos PMTiles alojados por nosotros | medio-alto | MIT/BSD según componentes | almacenamiento, HTTP range, ancho de banda y posible preparación de basemaps | Cuando haya bastantes destinos y un presupuesto de alojamiento comprobado |

**Decisión provisional:** primero tarjetas con filtro y «abrir mapa», después evaluar mapa integrado por destino. Un sistema propio de teselas planetarias desde el día 1 no es «fácil y gratis». **No cargar 500 MB de teselas en la home**. El formato PMTiles usa solicitudes HTTP Range y está diseñado para acceso a segmentos; hosting debe soportarlo. Source: [PMTiles](https://github.com/protomaps/PMTiles) y [documentación](https://docs.protomaps.com/pmtiles/).

## Plantillas de descubrimiento (pseudoconsultas, NO ejecutadas)

**Overpass Turbo, para la zona dibujada en su UI:** [Overpass Turbo](https://overpass-turbo.eu/). Macro `{{bbox}}` se expande en Turbo, no en el endpoint HTTP plano. Consultar manualmente **área pequeña** y revisar cantidad, duplicados y límites de descarga.
```overpass
[out:json][timeout:25];
(
  nwr["shop"="books"]({{bbox}});
  nwr["amenity"="library"]({{bbox}});
);
out center tags;
```
Resultado: POIs candidatos. `out center` da centroide de way/relation, no la puerta exacta ni una fuente literaria. En futuras herramientas HTTP usar bbox o área previamente verificada; no sustituirla por una ciudad homónima.

**Wikidata, una obra validada:** [WDQS](https://query.wikidata.org/) — reemplazar `Q_OBRA_VALIDADA` por QID numérico real tras confirmar obra y autor.
```sparql
SELECT ?lugar ?lugarLabel WHERE {
  wd:Q_OBRA_VALIDADA wdt:P840 ?lugar .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en,fr". }
}
LIMIT 50
```
Esto genera candidatos a escenario narrativo de entidad exacta, **no coordenadas de escena**, ni evidencia suficiente sin referencia.

**Wikidata, adaptación audiovisual validada** — reemplazar `Q_ADAPTACION_VALIDADA` por la producción exacta.
```sparql
SELECT ?lugar ?lugarLabel WHERE {
  wd:Q_ADAPTACION_VALIDADA wdt:P915 ?lugar .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 50
```
No usar `P915` del libro ni `P840` de la adaptación como equivalentes. Para entidades con referencias serias, consultar statement/qualifiers y fuente específica; queries directas `wdt:` no devuelven procedencia.

**Open Library**: resolver obra por búsqueda identificada, ID `/works/...` y autores con caché, sin cientos de peticiones individuales diarias. Catálogo actual de `/recomendaciones/` prevalece para ID editorial público.

## Presupuesto operativo orientativo — hipótesis, NO costes medidos

- 1 ciudad nueva/quincena a modo piloto → descarga de 1–2 datasets municipales + 1 consulta Overpass acotada + varias búsquedas Wikidata/Open Library identificadas y **revisión editorial manual** de 3–5 candidatos.
- Instantánea de datos propia tras la revisión; HTML estático y JSON reducido para visitantes; 0 llamadas LLM por visita, 0 llamadas Google Places, 0 claves externas en JS.
- Fuente práctica difícil de automatizar: prueba real de que un libro menciona una calle concreta o que una librería tiene historia singular. Reservar tiempo humano, no crear una falsa confianza de datos 100% automáticos.

## Condiciones para comenzar código de implementación

1. Resolver ruta pública `/atlas-literario/` vs `/viajes-literarios/`.
2. Acordar 3–5 fichas que tengan fuente, estado, precisión y derechos.
3. Comprobar compatibilidad exacta con último main/PR #661 y #665.
4. Definir si se permiten placas, lugares reales, escenas de adaptación y bibliotecas por igual.
5. Decidir mapa liviano + licencias/hosting antes de introducir librerías JS.
6. PR separada de implementación. **No ejecutar Actions ni fusionar esta PR documental.**
