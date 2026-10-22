# Hija de #718 — clics de opiniones y CTA por libro (22/10/2026)

## Problema confirmado en el código

`script.js` de #720 clasificaba `https://www.amazon.es/dp/B0GB6LGQFH#customerReviews` como `comprar-amazon`, aunque el visitante salía a LEER opiniones. También `autor.html` anunciaba «Amazon España y Goodreads» con un único href hacia Amazon. Manecillas no tenía ningún CTA visible para valorar la obra, pese a que su URL de Goodreads figuraba en datos estructurados.

## Integración concreta sin duplicar #717/#720/#721

Rama nacida de `feat/amazon-author-follow-cta-2026-10-22` (#721), que a su vez depende de #720, a su vez de #717. No cambiar la base a main hasta incorporar las dependencias. #718 conserva la investigación independiente y remite a esta PR.

- **El mismo listener delegado** de `script.js` decide entre evento de reseñas y evento de compra: no añade un segundo listener, fetch, SDK, instancia de GoatCounter ni un evento de pedido inexistente.
- **Un único helper puro** `_readerReviewOutboundCategory(href, platform, book)` reconoce *solo* cinco combinaciones concretas de ISBN/ID/plataforma, con host HTTPS exacto y ruta canónica. Para Amazon exige además `#customerReviews`. Las marcas `data-reader-review` inválidas no caen en el contador de compra.
- `_amazonOutboundCategory` devuelve `null` en `#customerReviews` aunque no esté marcado: no se atribuye como compra por descuido. Se preservan `amzn.to`, slug/`dp`, búsquedas ISBN, `#buy-dialog` y CTA Follow de #721.
- `data/analytics-events.json`: cinco eventos `visita-resenas-{plataforma}-{libro}` con acción `review_outbound`. Son salidas, **no reseñas publicadas**, compras ni seguidores confirmados.
- `autor.html`: sustituye el CTA engañoso por Amazon opiniones de Samuel y Goodreads de la obra, cada uno con enlace específico.
- `libros/samuel-entre-mundos/index.html`: Amazon, Goodreads y Casa del Libro; el enlace de opiniones Amazon ya no es afiliado (la compra conserva el tag y su flujo).
- `las-manecillas-del-recuerdo/index.html`: sección «Opiniones sobre la novela», con Goodreads y Casa del Libro. No se añade un enlace Amazon de Manecillas sin validación del destino papel/Kindle mediante navegador real, para no prometer una ficha equivocada.

## Cinco destinos validados de origen y contrato

| Plataforma | Obra | Destino |
|---|---|---|
| Amazon ES | Samuel | https://www.amazon.es/dp/B0GB6LGQFH#customerReviews |
| Goodreads | Samuel | https://www.goodreads.com/book/show/245605636-samuel-entre-mundos |
| Casa del Libro ES | Samuel | https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720 |
| Goodreads | Manecillas | https://www.goodreads.com/book/show/258289637-las-manecillas-del-recuerdo |
| Casa del Libro ES | Manecillas | https://www.casadellibro.com/libro-las-manecillas-del-recuerdo/9798905149351/18668032 |

**Validación**: URLs presentes en fichas/JSON-LD y página pública correspondiente; en Casa del Libro sí se comprobó el ISBN y botón «Escribir reseña» para Manecillas por búsqueda pública (rastreo del mes anterior). Goodreads se ha utilizado por la URL canónica registrada del repositorio; no se ha autenticado ni probado el formulario real. Amazon KDP documenta que `#customerReviews` lleva al bloque donde el lector puede elegir «Escribir opinión de este producto», **no** una URL que cree automáticamente la reseña: https://kdp.amazon.com/es_ES/help/topic/G202101910.

## Código externo contrastado y decisión

`arp242/goatcounter`: https://github.com/arp242/goatcounter/blob/main/public/count.js . La licencia global del repositorio es EUPL modificada; la licencia específica del cliente `count.js` es **ISC**: https://github.com/arp242/goatcounter/blob/main/LICENSE . Ya está integrado en `script.js` como `_gcEvent`; se reutiliza intacto. **Copiar el script externo completo crearía una segunda instrumentación y dobles conteos**; no hay una ganancia técnica que justifique ese cambio.

## Control de calidad y salida

- Comprobación de sintaxis de `script.js` mediante V8: correcta.
- `tests/test-reader-review-outbound.mjs`: 6 pruebas de regresión escritas: rutas aceptadas, fraude de host/ruta, producto Amazon con hash, CTAs HTML reales, listener delegado con un solo evento, compatibilidad Author Follow.
- `tests/test-amazon-outbound-events.mjs`: actualizado el test de cardinalidad que en #721 ya se había quedado obsoleto: ahora verifica una única salida comercial o lectora **y**, separadamente, un evento Follow.
- **16 aserciones funcionales aisladas** ejecutadas sobre el código efectivamente obtenido de la rama GitHub en V8, con parser URL de prueba para URLs absolutas; todas correctas. Esto no reemplaza `node --test` ni la validación visual.
- Pendiente antes de merge: `node --check script.js`, `node --test tests/test-reader-review-outbound.mjs tests/test-amazon-outbound-events.mjs tests/test-amazon-author-follow.mjs`, `python scripts/check-analytics-taxonomy.py --check`, revisión en navegador desktop/móvil y confirmación de que CSS existente presenta la sección Manecillas sin ruptura.

**No ejecutado:** GitHub Actions, suite total del repositorio, tests Node del proyecto, peticiones autenticadas, creación/publicación de reseñas, merge ni despliegue.
