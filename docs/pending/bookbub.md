# Pendiente — BookBub Author Profile

**Revisión:** 2026-09-08

**Estado:** `RESEARCHED · FREE_AUTHOR_PROFILE_CONFIRMED · US_RETAIL_EDITION_NOT_OBSERVED · READY_FOR_ELIGIBILITY_CHECK`

## Objetivo

Determinar si David Porto Díaz puede reclamar gratuitamente un BookBub Author Profile usando la edición digital legítima de `Las manecillas del recuerdo`, y dejar el perfil/libro correctos si BookBub confirma elegibilidad.

No se incluyen Featured Deals, Ads, Preorder Alerts ni promociones de pago.

## Por qué puede aportar valor

BookBub mantiene perfiles gratuitos de autor orientados a descubrimiento, seguidores y catálogo. Sin embargo, su modelo actual está fuertemente condicionado al mercado estadounidense: los Author Profiles muestran actualmente ediciones de EE. UU. y la elegibilidad para reclamar perfil exige un ebook publicado en un retailer compatible **en Estados Unidos**.

Por eso esta PR no debe ejecutarse como un alta automática: primero hay que demostrar que existe una edición US legítima de Manecillas.

## Modelo oficial actual

BookBub indica actualmente:

- el Author Profile es gratuito para autores elegibles;
- se reclama desde BookBub Partner Dashboard;
- la identidad del autor se revisa manualmente y la aprobación puede tardar hasta 7 días;
- solo pueden reclamarlo autores con ebooks publicados en un retailer compatible en EE. UU.;
- retailers compatibles: Amazon, Apple, Barnes & Noble, Google o Kobo;
- en los Author Profiles se listan actualmente las ediciones US;
- BookBub también puede obtener datos de libros de terceros como Bowker;
- New Release Alerts son gratuitos, pero actualmente solo para miembros US y el libro debe añadirse al perfil antes, el día de publicación o hasta 7 días después.

Fuentes oficiales:

- https://support.bookbub.com/articles/how-do-i-claim-my-author-profile/
- https://support.bookbub.com/articles/bookbubs-marketing-tools/
- https://support.bookbub.com/articles/how-do-i-get-books-listed-on-bookbub-com/

## Estado público observado 2026-09-08

No se ha localizado mediante búsqueda pública una ficha inequívoca de la edición Kindle de Manecillas en Amazon.com ni en otro retailer US compatible usando el ASIN/ISBN conocidos.

Estado correcto: `US_RETAIL_EDITION_NOT_OBSERVED`.

Esto **no demuestra ausencia**. Claude debe comprobar directamente cada retailer y, si es necesario, el Partner Dashboard autenticado.

No se ha verificado todavía un BookBub Author Profile público inequívoco de David.

## Datos canónicos

### Autor

- Nombre: `David Porto Díaz`
- Web oficial: https://davidportodiaz.com/
- Wikidata: `Q139678851`
- ORCID: `0009-0005-9089-3782`
- Amazon Author: `B0GZFP1JV3`
- Goodreads Author: `66843136`

### Las manecillas del recuerdo — Kindle

- Editorial: Monza Ediciones
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- Publicación: `2026-08-12`
- Precio canónico observado en Amazon.es: `2,99 €`
- Amazon.es: https://www.amazon.es/dp/B0HHM71F46
- Enlace afiliado del proyecto: https://amzn.to/3SM4Oxu

Es la única edición actual que puede servir de base para la elegibilidad BookBub porque BookBub exige un **ebook**.

La ventana del New Release Alert ya pasó: a 2026-09-08 han transcurrido más de 7 días desde 2026-08-12. No contar ese alert como beneficio de esta ejecución.

### Las manecillas del recuerdo — papel

- ISBN: `9798905149351`
- ASIN: `B0HHY9MYLM`
- Publicación: `2026-09-03`

El papel por sí solo no satisface el requisito de ebook para reclamar Author Profile.

### Samuel entre mundos

- ISBN: `9791387659776`
- Editorial: Libros Indie
- formato autorizado/documentado actualmente: papel

No crear ni distribuir un ebook de Samuel para intentar cumplir BookBub.

## Owner de distribución

La existencia o no de Manecillas en retailers US depende de Monza y/o su distribuidor digital. Si el ebook no está disponible en EE. UU., esta PR **no** debe abrir una distribución paralela desde la cuenta personal de David.

Coordinar cualquier duda de territorios/distribución con #428 Monza y las PR de Apple/Kobo/Google Play.

## Procedimiento exacto para Claude

1. Buscar `B0HHM71F46`, `9798906781925` y `Las manecillas del recuerdo` directamente en:
   - Amazon.com;
   - Apple Books US;
   - Barnes & Noble;
   - Google Play Books US;
   - Kobo US.
2. Guardar URL y retailer únicamente si la edición es inequívocamente la de Monza/David.
3. Si no aparece en ninguno, registrar `NO_GO_US_RETAIL_AVAILABILITY` y coordinar con #428; no crear distribución nueva.
4. Si aparece en al menos uno, entrar en BookBub Partner Dashboard con una cuenta de tipo `Author`.
5. Buscar primero un perfil `David Porto Díaz` existente y posibles variantes antes de crear/reclamar nada.
6. Reclamar el Author Profile mediante la vía oficial y completar la verificación de identidad solicitada por BookBub.
7. Esperar/revisar la aprobación manual sin crear perfiles duplicados.
8. Tras aprobación, auditar:
   - nombre;
   - foto;
   - bio;
   - web oficial;
   - Manecillas ebook;
   - portada;
   - retailer links;
   - fecha/publicación;
   - duplicados de autor/libro.
9. Añadir otros libros solo si cumplen el modelo real de BookBub. No añadir Samuel como ebook inexistente.
10. Guardar URL pública estable del Author Profile y del libro.

## Contenido del perfil

Usar una bio factual y actual, sin claims promocionales no respaldados. Priorizar:

- David Porto Díaz como autor;
- `Las manecillas del recuerdo` como obra principal actual;
- `Samuel entre mundos` solo si BookBub permite representarlo legítimamente dentro de su modelo;
- web oficial.

No copiar ratings/reseñas ni inventar bestseller, premios o categorías.

## Web / sameAs

No hay cambio previo de código.

Solo después de reclamar/verificar un Author Profile público, estable e inequívoco, valorar añadir su URL a `Person.sameAs` y/o superficies sociales del sitio. No usar como `sameAs` una cuenta de Partner Dashboard privada.

Si se añade:

1. modificar el owner factual/canónico correcto;
2. regenerar derivados;
3. actualizar allowlists/tests;
4. ejecutar CI;
5. verificar producción.

## Medición

Si el perfil queda activo:

- registrar seguidores iniciales;
- comprobar referrals reales desde BookBub en analítica propia;
- revisar a 30/60/90 días;
- no contratar promoción para forzar señal.

## Guardrails

- Cero BookBub Ads.
- Cero Featured Deals/promociones de pago.
- Cero Preorder Alerts de pago.
- No cambiar país/mercado con datos falsos para desbloquear funciones.
- No distribuir ebooks sin derechos.
- No crear perfil duplicado.
- No interpretar `NOT_OBSERVED` como `ABSENT`.

## Criterio de cierre

### Si es elegible

`US_RETAIL_EDITION_VERIFIED · FREE_AUTHOR_PROFILE_CLAIMED · IDENTITY_APPROVED · MANECILLAS_EBOOK_LISTED · METADATA_AUDITED · DUPLICATES_REVIEWED · PUBLIC_PROFILE_URL_RECORDED · SITE_GRAPH_UPDATED_IF_APPLICABLE · ZERO_PAID_PROMOTION`

### Si no es elegible

`US_RETAILERS_CHECKED · NO_ELIGIBLE_US_EBOOK · DISTRIBUTION_OWNER_RECORDED · NO_PARALLEL_DISTRIBUTION · NO_GO_US_RETAIL_AVAILABILITY · ZERO_SPEND`

## Fuentes oficiales

- Claim de Author Profile: https://support.bookbub.com/articles/how-do-i-claim-my-author-profile/
- Overview de herramientas/regiones/coste: https://support.bookbub.com/articles/bookbubs-marketing-tools/
- Alta/listado de ebooks: https://support.bookbub.com/articles/how-do-i-get-books-listed-on-bookbub-com/
- Author Profiles: https://support.bookbub.com/articles/what-are-author-profiles/
