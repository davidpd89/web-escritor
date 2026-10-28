# FilmMap: servidor MCP de búsqueda de rodajes — archivado literal, no conectado (21/10/2026)

**PR hija [#668](https://github.com/davidpd89/web-escritor/pull/668)**, decisiones generales en [ADR-000 #666](https://github.com/davidpd89/web-escritor/pull/666).

## Código MIT copiado tal cual

- [Upstream `Flightmussy/filmmap-mcp/server.mjs`](https://github.com/Flightmussy/filmmap-mcp/blob/main/server.mjs) → `research/vendor/filmmap-mcp/server.mjs`, blob SHA **`5465b531d36c847a606cde47c1a375e1e77d7703`**. Servidor MCP HTTP/stdio de consulta, cerca de 52 KB.
- [LICENSE upstream MIT](https://github.com/Flightmussy/filmmap-mcp/blob/main/LICENSE) → `research/vendor/filmmap-mcp/LICENSE.upstream`, blob SHA **`ed10712cbb6c86d21e9e8406b7519ff5f3fe25ca`**.
- [LICENSE dataset fuente CC0](https://github.com/Flightmussy/filmmap-dataset/blob/main/LICENSE) → `research/vendor/filmmap-dataset/LICENSE.upstream`, blob SHA **`e7771b0e763d51a318a01bf5cb28f75250eaf6dd`**. **El dataset completo NO se copió:** ya existe públicamente en [repositorio de descarga](https://github.com/Flightmussy/filmmap-dataset) y sus miles de filas serían un material derivado ajeno que debemos cargar por lotes según versión/fecha.

## Por qué puede reducir muchísimo esfuerzo

El servidor upstream implementa un protocolo público de consulta con funciones `where_was_it_filmed`, `what_was_filmed_here`, `search_locations`, `search_productions`, `locations_near`, `list_countries`, etc. Su código es **MIT** y su mapa de producción usa datos **CC0** de Wikidata, con distinción entre rodaje P915 y ambientación P840. Si el usuario quiere agentes investigando lugares sin llamadas a modelo en cada ficha, consultar el dataset versionado **directamente** es más escalable; este servidor MCP permite opcionalmente interrogar la fuente, no debe convertirse en dependencia online de la web.

**REQUISITO real** (inspección del código): Node ≥18 y fichero `atlas-compact.json` que la web upstream genera. Este fichero no está en esta PR; por tanto `node server.mjs` **NO es una orden funcional dentro de nuestro repo**. Para usarlo con nuestros datos habría que implementar/convertir su estructura, seleccionar endpoints, aislar servidor/secretos y evaluar operación. Aunque el proyecto upstream declara «sin npm deps», eso no significa sin hosting ni sin datos. La copia es **fuente de implementación para una PR posterior**, no software desplegado.

La licencia MIT del servidor no cubre las fotos Wikimedia ni texto Wikipedia que aparezcan enlazados; los registros factuales CC0 sí se pueden procesar para uso comercial sin copiar fotografías/quotes.

## Cuándo convertir en código de producción

- Si seguimos con **web estática y generadores**: no levantar MCP en producción; extraer CSV/GeoJSON fuente offline y generar solo relaciones revisadas.
- Si en el futuro habilitamos herramienta para asistentes que investiguen: adaptar el `server.mjs` con JSON compacto propio, API local read-only, límites de consultas y referencia de fuentes; nunca ofrecer (status=approved) por tener coordenada en Wikidata.
- Conservar fuente exacta (blob SHA) y licencia; adaptar en carpeta separada, evitando «parches» invisibles al vendor.

**CERO ejecuciones, cero Actions, cero merges.** Ver [#667](https://github.com/davidpd89/web-escritor/pull/667) para esquema de importación y procedencia del snapshot audiovisual mundial.
