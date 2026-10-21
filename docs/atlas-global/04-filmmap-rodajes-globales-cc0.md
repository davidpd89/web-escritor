# Filmación global abierta (CC0): Movie Scene Map / FilmMap

**Investigación 21/10/2026 — hija [#667](https://github.com/davidpd89/web-escritor/pull/667), ADR único [#666](https://github.com/davidpd89/web-escritor/pull/666).**

## Recurso directamente reutilizable, no solo una API

- [Repositorio `Flightmussy/filmmap-dataset`](https://github.com/Flightmussy/filmmap-dataset) publica CSV y GeoJSON; **instantánea versionada del 18 de agosto de 2026**, con **15.272 lugares / 161 países / 12.762 producciones** según su README. No declarar esas cifras como datos en vivo.
- [Descargas actuales](https://moviescenemap.com/data/) y [sitio mapa](https://moviescenemap.com/) apuntan a actualizaciones posteriores. **No hemos descargado ni comprobado los ficheros en vivo.**
- Archivos del snapshot GitHub: `filming-locations.csv` (~7 MB), `filming-locations.geojson` (~13 MB) y `productions.csv` (~4 MB); guardarlos fuera de la web y de GitHub Actions, después extraer solo los campos/filas que aporten contenido.
- [Licencia CC0](https://github.com/Flightmussy/filmmap-dataset/blob/main/LICENSE) sobre **registros fácticos** con permisos comerciales, comprobada directamente; **fotografías Wikimedia y frases Wikipedia NO están incluidas** en CC0. La licencia original se ha archivado en [#668](https://github.com/davidpd89/web-escritor/pull/668).
- [Servidor MCP público](https://moviescenemap.com/mcp) con herramientas `where_was_it_filmed`, `what_was_filmed_here`, `search_locations`, `search_productions`, `locations_near`, `list_countries`, etc., según el README. **No asumir servicio/SLAs ilimitados**. Para ingesta masiva preferir los CSV/GeoJSON CC0, no cientos de llamadas MCP ni IA.
- [Servidor MIT de origen](https://github.com/Flightmussy/filmmap-mcp): `server.mjs` de ~52 KB **sin dependencias npm externas** (Node ≥18 según fuente), pero **NECESITA `atlas-compact.json` del autor, que no está en el repositorio del dataset CC0**, y está preparado para servir MCP, no para insertar código JS en nuestra web. **Copia literal sin ejecutar en [#668](https://github.com/davidpd89/web-escritor/pull/668)** con licencia MIT.

## Lo que nos interesa importar (sin inventar relación obra↔escena)

| Origen | Columna | Destino del modelo |
| --- | --- | --- |
| `filming-locations.csv` | `qid`, `name`, `country`, `iso`, `latitude`, `longitude`, `category`, `resolution` | POI candidato con Wikidata QID y precisión real (exact/town/region/fiction). No poner pin fachada cuando sea solo `town` |
| `productions.csv` | `qid`, `name`, `kind`, `year`, `series` | **Producción/adaptación** canónica con QID propio, nunca ID de la novela |
| `productions.csv` | `relation` (`filmed at` / `set in`) | Tipo de relación **diferenciado**: `filming_location` solo si es cine/TV y fuente respalda P915; `narrative_explicit` para mundos de ficción no es conexión automática con una novela del catálogo |
| Evidencia | `productions` vs `wiki_productions`, `wiki_evidence_url` | Distinguir **Wikidata statement** de **cita de sección de Wikipedia**; no mezclar las columnas como si fueran prueba equivalente |
| Fotos | `image`, `image_page` | Solo ENLACES para investigar metadatos Commons, no descarga y publicación automática |

### Limitación crítica para nuestro proyecto

La instantánea mezcla **películas, series, videojuegos, manga y anime**: un videojuego o anime no «se rodó» físicamente donde se ambienta; usa P840 como ambientación en esos casos. Tampoco podemos afirmar **escena concreta** por P915 (propiedad «rodado en», a nivel producción). Una film commission municipal o testimonio de producción puede dar precisión adicional, con fuente individual. [Wikidata P915](https://www.wikidata.org/wiki/Property:P915) lo diferencia explícitamente de [P840](https://www.wikidata.org/wiki/Property:P840).

**Límite editorial adicional:** que una película se base en un libro no autoriza automáticamente a importar todos sus rodajes como **lugares del libro**. Vincular `adaptation.original_work_id` requiere comprobar adaptación concreta y obra original. Así evitamos confundir Harry Potter novela / película / parque temático, o Juego de tronos libros / serie / exteriores.

## Complemento oficial de alta calidad: San Francisco Film Commission

[DataSF Film Locations](https://data.sf.gov/Culture-and-Recreation/Film-Locations-in-San-Francisco/yitu-d5am/about_data): **2.214 filas y 18 columnas** en la ficha oficial consultada, actualizaciones publicadas septiembre 2026, con **título, año de estreno, lugar, coordenadas, reparto, director y datos descriptivos**, descargar CSV/JSON/GeoJSON. [Ficha dataset catalog.data.gov](https://catalog.data.gov/dataset/film-locations-in-san-francisco) muestra licencia **PDDL 1.0** (public domain database). Se puede usar para **contrastar** rodajes por ciudad; cada título que sea adaptación requerirá cruzar con obra literaria real sin asumirlo.

## Pipeline futuro por lotes sin coste IA

1. Descargar snapshot CC0 versionado cuando se autorice, guardar manifest de SHA, fecha, tamaño, fuente y licencia fuera de Git. Ignorar fotos/quotes.
2. Ingerir CSV streaming, IDs Wikidata para películas/series y destinos, relacionar solo rows de `kind=film/tv` con `relation=filmed at`; `game/anime/manga` quedan como otra clase opcional, no filmación.
3. Cruzar QID de películas con Wikidata/Open Library/obra del catálogo (relación `adaptation`) y deduplicar POIs contra Overture/OSM por QID + geometría/precisión. **Ninguna unión por mero título**.
4. Generar vínculos `candidate` con `source_ids` de repositorio de datos/Wikidata. La validez de lugar real se revisa contra fuentes de producción/film commissions al publicar.
5. Producir páginas HTML estáticas/JSON shard aprobados, sin consultar MCP remoto por visita.
6. Renovar snapshot con diffs y revalidar sin despublicar de forma automática si una entrada desaparece.

**No ejecutado:** descarga de dataset, llamadas MCP, joins, código de publicación o Actions. La investigación puede permitir cobertura mundial de rodajes mucho más rápido que escribir una lista manual.
