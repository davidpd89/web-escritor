# Retailers y disponibilidad — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#410 · `tracking/retailers-books`**  
Estado: **RESEARCHED · CORE_RETAILERS_MAPPED · METADATA_DISCREPANCIES_CONFIRMED · FNAC_ECI_NOT_OBSERVED · DIGITAL_CHANNELS_DELEGATED · EXTERNAL_ACTION_PENDING**

## Objetivo

Mantener un mapa real y verificable de dónde aparecen `Samuel entre mundos` y `Las manecillas del recuerdo`, qué edición se vende en cada canal y qué inconsistencias deben corregirse upstream.

Esta PR NO debe convertirse en una base manual de precios/stock. Precio y disponibilidad son snapshots volátiles; la autoridad debe ser ISBN/ASIN + editorial + formato + URL estable.

## Ediciones canónicas

### Samuel entre mundos

- Autor: David Porto Díaz
- Editorial: Libros Indie
- ISBN: `9791387659776`
- Amazon ASIN usado por el proyecto: `B0GB6LGQFH`
- Formato: tapa blanda
- Páginas en autoridad actual del proyecto: 422
- Sin ebook documentado/autorizado actualmente.

### Las manecillas del recuerdo — tapa blanda

- Autor: David Porto Díaz
- Editorial: Monza Ediciones
- ISBN: `9798905149351`
- ASIN registrado por el proyecto: `B0HHY9MYLM`
- Publicación: 2026-09-03
- PVP editorial documentado: 16 €
- Páginas en autoridad actual del proyecto: 272

### Las manecillas del recuerdo — ebook

- Editorial: Monza Ediciones
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- Publicación: 2026-08-12
- Precio observado hoy en varias superficies: 2,99 €

## Matriz pública observada a 2026-09-07

| Canal | Samuel papel | Manecillas papel | Manecillas ebook | Estado |
|---|---|---|---|---|
| Amazon España | URL/ASIN registrado por proyecto; compra enlazada desde web oficial | ASIN/shortlink registrado por proyecto | ASIN/shortlink verificado por web oficial | `KNOWN_IDS · LIVE_DETAILS_TO_VERIFY` |
| Casa del Libro | ficha pública observada | no observada en esta búsqueda | ficha pública observada | `PARTIAL` |
| TodosTusLibros | registro público observado | no observado | no observado | `PARTIAL` |
| Agapea | no auditado a fondo | registro público observado | no auditado | `PARTIAL` |
| Bookish | registro público observado | no auditado | no auditado | `PARTIAL` |
| FNAC España | no observado hoy | no observado hoy | no observado hoy | `NOT_OBSERVED` |
| El Corte Inglés | no observado hoy | no observado hoy | no observado hoy | `NOT_OBSERVED` |
| Google Books/Play | owner #405 | owner #405 | owner #405 | `DELEGATED` |
| Apple Books | owner #411 | owner #411 | owner #411 | `DELEGATED` |
| Kobo | owner #412 | owner #412 | owner #412 | `DELEGATED` |

`NOT_OBSERVED` significa que la búsqueda pública realizada no devolvió una ficha inequívoca. No significa que el producto no esté en el catálogo interno.

## Samuel — fichas observadas

### Casa del Libro

URL pública identificada:

`https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720`

Campos observados:

- título correcto;
- autor: `DAVID PORTO DIAZ`;
- editorial: Libros Indie;
- ISBN correcto;
- castellano;
- tapa blanda;
- **412 páginas**;
- lanzamiento `05/01/2026`;
- año edición `2025`;
- plaza Sevilla.

### TodosTusLibros

Samuel aparece en la página editorial de Libros Indie.

Snapshot indexado:

- `SAMUEL ENTRE MUNDOS`;
- autor `DAVID, PORTO DÍAZ`;
- Libros Indie;
- 22,00 €;
- disponibilidad alta.

El precio/stock no se conserva como hecho estable.

### Bookish

Ficha pública:

- David Porto Diaz;
- Libros Indie;
- ISBN correcto;
- **412 páginas**;
- año edición 2025;
- fecha pública `01/01/2025`.

## Samuel — discrepancias a resolver

### Páginas

- web/autoridad del proyecto: **422**;
- Casa del Libro: **412**;
- Bookish: **412**.

Dos retailers con 412 hacen probable un origen upstream compartido, pero NO demuestran que 412 sea correcto.

Owner:

#429 Libros Indie → #404 DILVE → downstream.

### Fechas

- año editorial: 2025;
- Casa: 05/01/2026 lanzamiento;
- Bookish: 01/01/2025.

Resolver diferencia entre año de edición y fecha comercial/técnica. No uniformar sin fuente.

## Manecillas ebook — fichas observadas

### Casa del Libro

URL pública:

`https://www.casadellibro.com/ebook-las-manecillas-del-recuerdo-ebook/9798906781925/18596246`

Campos:

- título correcto;
- autor `PORTO DÍAZ DAVID`;
- Monza Ediciones;
- ISBN `9798906781925`;
- castellano;
- lanzamiento 12/08/2026;
- eBook EPUB con DRM;
- precio observado 2,99 €.

### Amazon Kindle

La web oficial mantiene como destino de compra el ASIN:

`B0HHM71F46`

Shortlink registrado:

`https://amzn.to/3SM4Oxu`

Claude debe comprobar ficha live antes de cerrar:

- title;
- author;
- publisher;
- price;
- Kindle format;
- reviews;
- relationship with paperback;
- territories.

No copiar ranking ni reseñas como datos permanentes.

## Manecillas papel — fichas observadas

### Agapea

Una página indexada el 2026-09-06/07 muestra:

- `Las Manecillas Del Recuerdo`;
- Monza Ediciones;
- **266 páginas**;
- 16,00 € PVP, 15,20 € precio mostrado con descuento.

### Amazon

Proyecto registra:

- ASIN `B0HHY9MYLM`;
- shortlink `https://amzn.to/4zW6Yeu`.

Claude debe verificar el producto live, especialmente:

- autor;
- ISBN;
- page count;
- publicación;
- editorial;
- formato;
- agrupación con Kindle.

## Manecillas — discrepancia crítica

- autoridad web/proyecto: **272 páginas**;
- Agapea: **266 páginas**.

No ajustar la web ni retailers hasta que #428 Monza confirme ejemplar/metadata de producción.

## FNAC y El Corte Inglés

Las búsquedas públicas de hoy por título/ISBN no devolvieron fichas inequívocas.

Estado:

- `FNAC_PUBLIC_RECORD_NOT_OBSERVED`
- `ECI_PUBLIC_RECORD_NOT_OBSERVED`

Claude debe repetir búsqueda directa dentro de cada sitio por ISBN exacto.

Si no aparece:

1. comprobar si el distribuidor/feed incluye el canal;
2. preguntar al publisher/distribuidor, no al retailer primero;
3. no asumir que “debería aparecer” por existir en DILVE.

## Regla de ownership

### Metadata bibliográfica

Corregir upstream:

`publisher/distributor → DILVE/ONIX/ISBN → retailer`

### Amazon

Depende del owner de cada listing/KDP/editorial y Author Central para asociación autor↔obra.

### Stock

Retailer/librería/distribuidor, no ISBN.

### Precio

Canal/editorial según distribución. No congelar.

## Cómo auditar cada retailer

Guardar por edición:

- retailer;
- URL;
- ISBN;
- ASIN/SKU si existe;
- título;
- autor;
- editorial;
- formato;
- page count;
- fecha/año;
- idioma;
- precio snapshot;
- disponibilidad snapshot;
- portada;
- sinopsis;
- categorías;
- review count snapshot;
- fecha/hora de consulta.

## Clasificación de incidencias

### `IDENTITY_ERROR`

Libro atribuido a otro autor/edición.

### `METADATA_ERROR`

Páginas, fecha, editorial, ISBN, formato, portada, etc.

### `AVAILABILITY_ONLY`

Ficha correcta, stock no disponible.

### `PRICE_VARIANCE`

Precio/promoción distinta sin error bibliográfico.

### `DUPLICATE_RECORD`

Misma edición duplicada.

### `FORMAT_LINKING_ERROR`

Papel/ebook correctos pero no asociados cuando el canal soporta esa relación.

### `NOT_OBSERVED`

Sin ficha inequívoca pública. No declarar ausencia.

## Acción recomendada por tipo

| Tipo | Owner | Acción |
|---|---|---|
| ISBN/title/author/page count | publisher/DILVE | corregir upstream |
| Amazon author association | #396 Author Central | reclamar/asociar |
| Amazon listing metadata | publisher/KDP/Amazon owner | ticket autorizado |
| stock retailer | retailer/distributor | observar/escalar si anómalo |
| TSL metadata | #404/#407 | corregir DILVE |
| Apple | #411 | ejecutar allí |
| Kobo | #412 | ejecutar allí |
| Google Books | #405 | ejecutar allí |

## Enlaces desde la web oficial

Solo añadir retailers cuando:

- URL estable verificada;
- edición correcta;
- destino útil;
- no genera duplicidad/confusión.

Para Manecillas papel, sustituir cualquier placeholder comercial solo por URL verificada de esa edición.

No usar una ficha de Samuel como destino definitivo de Manecillas.

## Afiliación

Amazon puede usar el tag `davidporto-21` en superficies afiliadas del sitio.

Cualquier nuevo enlace afiliado debe conservar:

- disclosure visible;
- `rel="sponsored nofollow noopener noreferrer"` cuando aplique;
- políticas K.3 ya cerradas en el repo.

No etiquetar Casa del Libro/FNAC/etc. como afiliados sin relación real.

## Criterio de cierre

### Samuel

`AMAZON_VERIFIED · CASA_VERIFIED · TSL_VERIFIED · PAGE_COUNT_RESOLVED · DATE_METADATA_RECONCILED · FNAC_ECI_CHECKED`

### Manecillas papel

`AMAZON_PAPER_VERIFIED · PAGE_COUNT_RESOLVED · CASA_TSL_FNAC_ECI_CHECKED · DISTRIBUTION_SCOPE_DOCUMENTED`

### Manecillas ebook

`AMAZON_KINDLE_VERIFIED · CASA_EBOOK_VERIFIED · APPLE_KOBO_GOOGLE_DELEGATED_OR_VERIFIED`

### Global

`NO_UNOWNED_METADATA_GAPS · ALL_CORRECTIONS_UPSTREAM_OR_TICKETED · PUBLIC_LINKS_VALIDATED`

## Evidencia mínima

- URLs exactas;
- timestamp;
- campos clave;
- screenshot cuando importe;
- ticket/owner de corrección;
- recheck después de propagación;
- nada de credenciales/cookies en PR.

## Coordinación

- #396 Amazon Author Central.
- #404 DILVE.
- #405 Google Books.
- #406 ISBN.
- #407 TodosTusLibros.
- #411 Apple Books.
- #412 Kobo.
- #428 Monza.
- #429 Libros Indie.

## Guardrails

- `NOT_OBSERVED ≠ ABSENT`.
- `NO_STOCK ≠ NOT_PUBLISHED`.
- precio ≠ metadata estable.
- retailer ≠ authority primaria de datos editoriales.
- no mantener parches manuales distintos si comparten feed.
- no añadir Offer/schema de disponibilidad sin fuente que podamos mantener actualizada.
