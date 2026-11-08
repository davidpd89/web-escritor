# Fable — catálogo, comunidad y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#430 · `tracking/fable`**  
Estado: **RESEARCHED · FREE_BOOK_REQUEST_ROUTE_CONFIRMED · BOOK_UPDATE_ROUTE_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION**

## Objetivo

Conseguir que `Samuel entre mundos` y `Las manecillas del recuerdo` estén presentes y correctamente representados en Fable si encajan en su catálogo, aprovechando la comunidad/clubes sin recurrir a publicidad pagada ni actividad artificial.

## Qué es útil hoy

Fable sigue activa en 2026 como plataforma social de lectura con:

- catálogo de más de un millón de ebooks en su store;
- listas;
- recomendaciones;
- clubs;
- feed social;
- posibilidad de añadir libros ausentes mediante Book Request Form o extensión de Chrome;
- formulario específico para pedir correcciones de metadata.

Fuentes oficiales actuales:

- https://fable.co/
- https://fable.co/store
- https://help.fable.co/article/90-i-cant-find-a-book-in-fable-can-a-book-be-added
- https://help.fable.co/article/168-how-can-i-request-updates-to-books-on-fable
- https://help.fable.co/article/133-browser-extension

## Estado de los libros

No declarar presencia/ausencia sin buscar dentro de Fable.

Datos canónicos:

### Samuel entre mundos

- David Porto Díaz
- Libros Indie
- ISBN `9791387659776`
- 2025
- formato documentado: tapa blanda

### Las manecillas del recuerdo — papel

- David Porto Díaz
- Monza Ediciones
- ISBN `9798905149351`
- publicación `2026-09-03`

### Las manecillas del recuerdo — ebook

- Monza Ediciones
- ISBN `9798906781925`
- ASIN `B0HHM71F46`
- publicación `2026-08-12`

No fijar todavía los page counts conflictivos 422/412 y 272/266 en una alta externa hasta resolver #429/#428/#404.

## Cómo añadir un libro ausente

La ayuda oficial de Fable confirma dos vías gratuitas:

### Book Request Form

Si un libro no aparece, puede solicitarse mediante el formulario de alta.

### Extensión Chrome beta

La extensión puede añadir al catálogo libros desde páginas que contengan:

- ISBN o ASIN;
- autor;
- título;
- portada.

Si el libro no existe, Fable indica que puede incorporarlo al catálogo y completar detalles posteriormente.

Para nosotros, usar una página canónica/retailer correcta como fuente, nunca una ficha con metadata dudosa.

## Cómo corregir metadata

Fable mantiene un **Book Updates form** para información ausente o incorrecta y dice que intenta completar solicitudes en aproximadamente una semana.

Fuente:

https://help.fable.co/article/168-how-can-i-request-updates-to-books-on-fable

No crear una segunda ficha para corregir la primera.

## Identidad de autor

Fable depende mucho de la consistencia del nombre del autor. Su propia ayuda indica que las estadísticas de autores pueden fragmentarse si el mismo autor aparece escrito de formas diferentes en distintas listings.

Por tanto Claude debe comprobar especialmente:

- `David Porto Díaz` exactamente;
- que no exista `David Porto Diaz`/`Porto Díaz David` como entidad separada accidental;
- que Samuel y Manecillas apunten al mismo autor cuando el modelo de Fable lo permita.

Fuente: https://help.fable.co/article/175-how-to-i-edit-my-most-read-authors-chart

## Fable for Authors

Fable mantiene actualmente una sección de soporte específica `Fable for Authors` con ayuda sobre promoción y venta.

No interpretar esto automáticamente como un Author Central reclamable. Claude debe comprobar qué controles reales ofrece la cuenta actual antes de declarar `AUTHOR_PROFILE_CLAIMED`.

Fuente: https://help.fable.co/collection/116-fable-for-authors

## Clubs

Crear un club oficial solo si hay un uso real.

Opciones sensatas:

- club temporal de lectura de Samuel;
- club de Manecillas si existe demanda;
- club asociado a una presentación/evento concreto.

No crear un club vacío únicamente para fabricar una URL/backlink.

Si se hace:

- descripción clara;
- libro correcto;
- moderación real;
- reglas básicas;
- enlace a recursos oficiales cuando Fable lo permita;
- medir participantes/actividad antes de mantenerlo.

## No auto-manipular señales

No:

- auto-reseñar;
- auto-calificar para elevar media;
- crear cuentas artificiales;
- inundar clubes con promoción;
- solicitar altas duplicadas.

El objetivo es catálogo correcto + descubrimiento legítimo.

## Procedimiento Claude

1. Crear/iniciar sesión gratuita si hace falta.
2. Buscar por:
   - `David Porto Díaz`
   - `Samuel entre mundos`
   - `9791387659776`
   - `Las manecillas del recuerdo`
   - `9798905149351`
   - `9798906781925`
   - ASIN `B0HHM71F46`
3. Guardar URLs/IDs de resultados.
4. Revisar autor, portada, publisher, fecha, ISBN/ASIN y edición.
5. Revisar duplicados de autor/libro/edición.
6. Si falta un libro, usar Book Request o extensión oficial.
7. Si existe con error, usar Book Updates form.
8. Esperar propagación y verificar.
9. Solo después valorar club/perfil/links.
10. Añadir `sameAs` en nuestra web solo si existe URL pública estable, inequívoca y realmente útil.

## Prioridad

`P2`.

Es más interesante que un directorio genérico porque tiene audiencia lectora y clubes, pero queda por detrás de Amazon/Goodreads/Wikidata/BNE/Open Library/LibraryThing para autoridad y catalogación.

## Criterio de cierre

`ACCOUNT_IF_NEEDED · AUTHOR_IDENTITY_AUDITED · SAMUEL_FOUND_OR_REQUESTED · MANECILLAS_FOUND_OR_REQUESTED · EDITIONS_VERIFIED · METADATA_CORRECT_OR_UPDATE_REQUESTED · DUPLICATES_REVIEWED · PUBLIC_URLS_RECORDED · CLUB_DECIDED · NO_SELF_RATING · NO_PAID_PROMOTION`

Si la plataforma no aporta señal real tras tener catálogo correcto:

`CATALOG_COMPLETE · COMMUNITY_LOW_VALUE · NO_FURTHER_MAINTENANCE`

## Fuentes

- https://fable.co/
- https://fable.co/store
- https://help.fable.co/article/90-i-cant-find-a-book-in-fable-can-a-book-be-added
- https://help.fable.co/article/168-how-can-i-request-updates-to-books-on-fable
- https://help.fable.co/article/133-browser-extension
- https://help.fable.co/collection/116-fable-for-authors
