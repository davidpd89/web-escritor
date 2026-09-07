# Google Play Books / Partner Center — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#413 · `tracking/google-play-books`**  
Estado: **RESEARCHED · PUBLIC_RECORD_NOT_OBSERVED · DISTRIBUTION_OWNER_NOT_VERIFIED · READY_FOR_AUTHENTICATED_AUDIT**

## Objetivo

Comprobar si `Samuel entre mundos` y `Las manecillas del recuerdo` están correctamente representados en Google Books / Google Play Books y determinar quién controla cada edición antes de tocar Partner Center.

La prioridad NO es autopublicar otra copia. Es evitar duplicados y corregir en la fuente real.

## Estado público observado a 2026-09-07

Las búsquedas públicas realizadas hoy por título, autor e ISBN no han devuelto una ficha inequívoca de Google Books/Google Play Books para las obras.

Estado correcto:

`PUBLIC_GOOGLE_BOOK_RECORD_NOT_OBSERVED`

Esto NO equivale a:

`NOT_IN_GOOGLE_BOOKS`

ni a:

`NOT_DISTRIBUTED`

Claude debe comprobar directamente el catálogo y, si tiene acceso, Partner Center/feed.

## Datos canónicos

### Samuel entre mundos

- Autor: **David Porto Díaz**
- Editorial: **Libros Indie**
- ISBN papel: `9791387659776`
- Año editorial: 2025
- Formato documentado: tapa blanda
- No existe en el proyecto una edición digital de Samuel que pueda subirse a Google Play por iniciativa propia.

### Las manecillas del recuerdo — papel

- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- ISBN: `9798905149351`
- Publicación: `2026-09-03`
- ASIN de referencia: `B0HHY9MYLM`

### Las manecillas del recuerdo — ebook

- Editorial: **Monza Ediciones**
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- Publicación: `2026-08-12`

## Qué permite Google actualmente

Google Play Books Partner Center permite a autores y editores:

- enviar libros a Google Books;
- vender ebooks en Google Play sin coste de alta;
- añadir un libro por ISBN/EAN o, solo si no existe identificador, obtener un `GGKEY`;
- gestionar título, descripción, publisher, publicación, formato, categorías, contributors y otros metadatos;
- subir EPUB/PDF;
- controlar territorios y precios cuando la cuenta es el owner de venta.

Fuentes oficiales actuales:

- https://support.google.com/books/partner/answer/9261664
- https://support.google.com/books/partner/answer/1079107?hl=es
- https://support.google.com/books/partner/answer/3237055
- https://support.google.com/books/partner/answer/3244021?hl=es

## Regla crítica de ONIX

Google documenta expresamente que, si un partner utiliza ONIX, un feed ONIX posterior puede **sobrescribir** cambios manuales hechos en Partner Center.

Consecuencia:

- si Monza/Libros Indie/distribuidor envía ONIX → corregir allí;
- no mantener un parche manual en Google que el siguiente feed vaya a revertir;
- coordinar con #404 DILVE y #428/#429.

## No crear GGKEY innecesarios

Los tres productos ya tienen ISBN.

No crear un `GGKEY` para “hacer aparecer” una edición que ya tiene ISBN. Eso puede crear un producto duplicado y fragmentar señales/reseñas/catalogación.

## Ownership / derechos

### Samuel

No subir un ebook de Samuel salvo confirmación expresa de derechos digitales y existencia de una edición digital legítima.

### Manecillas

Es publicación de Monza. Antes de usar Partner Center:

1. confirmar si Monza o su distribuidor ya entrega Google Play Books;
2. confirmar quién controla el ISBN digital;
3. confirmar territorios/derechos;
4. corregir mediante ese owner.

No crear distribución directa desde una cuenta del autor si duplicaría la distribución editorial.

## Metadata a auditar

Por cada edición real encontrada guardar:

- Google Books volume ID / URL;
- ISBN;
- título/subtítulo;
- autor/contributor;
- editorial;
- idioma;
- fecha publicación/on-sale;
- formato;
- portada;
- descripción;
- categorías;
- preview;
- territorios;
- precio solo como snapshot;
- source/owner del registro;
- duplicados.

## Procedimiento exacto para Claude

1. Buscar directamente en Google Books por:
   - `9791387659776`
   - `9798905149351`
   - `9798906781925`
2. Repetir por título + autor.
3. Guardar IDs/URLs si existen.
4. Si hay acceso a Partner Center, comprobar si alguna edición pertenece ya a la cuenta.
5. Identificar si metadata llega por ONIX/feed/editorial.
6. No reclamar ni recrear productos controlados por publisher sin autorización.
7. Corregir errores en el owner upstream.
8. Revalidar la ficha pública después de propagación.
9. Si hay URL canónica estable, valorar `Book.sameAs` en la web solo si representa la edición/obra correcta.

## Oportunidad para la web

Si Manecillas ebook aparece correctamente en Google Play Books, puede ser un destino secundario de compra digital para usuarios que prefieran Google.

Condiciones:

- URL estable;
- edición correcta;
- disponibilidad real;
- no sustituir el CTA principal por intuición;
- no prometer precio/territorio permanente.

## Criterio de cierre

`ISBN_SEARCH_DONE · GOOGLE_BOOK_IDS_CAPTURED_OR_NOT_OBSERVED · DISTRIBUTION_OWNER_IDENTIFIED · NO_DUPLICATE_CREATED · METADATA_CORRECT_OR_UPSTREAM_REQUESTED · RIGHTS_RESPECTED · PUBLIC_QA_DONE · SITE_LINK_DECIDED`

Si el publisher no distribuye allí:

`NOT_DISTRIBUTED_BY_CURRENT_OWNER · NO_UNAUTHORIZED_UPLOAD`

## Fuentes

- https://support.google.com/books/partner/answer/9261664
- https://support.google.com/books/partner/answer/1079107?hl=es
- https://support.google.com/books/partner/answer/3237055
- https://support.google.com/books/partner/answer/3244021?hl=es
- autoridad factual del repo y PR #404/#428/#429
