# DILVE — actualización operativa 2026-09-07

Este documento complementa `dilve.md` y prevalece sobre cualquier snapshot comercial anterior que contradiga los datos actuales verificados del proyecto.

## Corrección factual inmediata

`Las manecillas del recuerdo` · papel:

- ISBN: `9798905149351`
- ASIN Amazon: `B0HHY9MYLM`
- editorial: Monza Ediciones
- publicación: `2026-09-03`
- páginas canónicas actuales del proyecto: `272`
- **PVP vigente actual: 15,99 €**

Cualquier `16,00 €` que aparezca en el runbook principal procede de snapshots comerciales anteriores y debe tratarse como **discrepancia a investigar**, no como autoridad actual.

Kindle:

- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- publicación: `2026-08-12`
- precio actual web/Amazon: `2,99 €`

Samuel:

- ISBN: `9791387659776`
- editorial: Libros Indie
- páginas canónicas del proyecto: `422`

## Discrepancias que Claude debe resolver upstream

### Manecillas papel

- proyecto/web: 272 páginas;
- algunos retailers observados: 266 páginas;
- proyecto/Amazon actual: 15,99 €;
- algunos snapshots comerciales: 16,00 €.

### Samuel

- proyecto/web: 422 páginas;
- Casa del Libro/Bookish observados: 412 páginas.

No corregir DILVE, TSL o retailers uno a uno hasta identificar el dato real del publisher/feed.

## Ficha DILVE/ONIX mínima que hay que capturar

Por ISBN:

- ProductIdentifier / ISBN;
- ProductForm;
- TitleDetail;
- Contributor + role;
- Publisher/Imprint;
- PublishingDate;
- PublishingStatus;
- NumberOfPages cuando proceda;
- Language;
- Subject/Thema;
- Audience;
- Collateral detail: cover + description;
- ProductSupply;
- Price + currency + tax/territory;
- SalesRights;
- RelatedProduct para enlazar papel/ebook cuando proceda.

Guardar el valor actual y la fuente/owner del dato.

## Ownership

Orden para resolver:

1. Monza Ediciones — Manecillas.
2. Libros Indie — Samuel.
3. Distribuidor/metadata provider si el publisher delega.
4. DILVE support si el owner no puede corregir o el feed no propaga.

No asumir que David tiene permisos para editar directamente un producto editorial.

## Qué debe considerarse éxito

- metadata fuente identificada;
- páginas reconciliadas;
- PVP real reconciliado;
- estado publicación ya no figura como próxima aparición;
- papel/ebook correctamente relacionados;
- autor exacto `David Porto Díaz`;
- portada y sinopsis correctas;
- propagación comprobada en #407 TodosTusLibros y #410 retailers.

## Cambio web posible

No hay cambio de código previo.

Si DILVE/retailers demuestran que el dato canónico actual de páginas o algún identificador del proyecto está equivocado, corregir primero la autoridad editorial y después actualizar el owner factual del repo + outputs + tests.

No cambiar `15,99 €` a `16 €` solo porque un retailer conserve un snapshot viejo.
