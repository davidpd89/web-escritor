# Lecturalia — autor y libros

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · ACTIVE_SPANISH_CATALOG_CONFIRMED · USER_REQUEST_ROUTE_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION`

## Objetivo

Conseguir que David Porto Díaz, `Samuel entre mundos` y `Las manecillas del recuerdo` estén presentes y correctamente descritos en Lecturalia, una superficie española de descubrimiento literario que sigue activa y actualizando catálogo en 2026.

## Valor real verificado

Lecturalia muestra actualmente aproximadamente:
- 113.600 libros;
- 24.686 autores;
- 97.000 usuarios registrados.

Mantiene páginas de autores, novedades, libros actualizados, valoraciones y comentarios, con categorías como ciencia ficción/fantasía y narrativa. La propia web dice que incorpora nuevos libros tanto por investigación editorial como por **peticiones concretas enviadas por usuarios desde su área personal**.

Fuentes:
- https://www.lecturalia.com/
- https://www.lecturalia.com/portada/libros
- https://www.lecturalia.com/portada/autores
- https://www.lecturalia.com/libros/nu/nuevos
- https://www.lecturalia.com/libros/ac/ultimos-actualizados

## Datos canónicos

### David Porto Díaz
- web: https://davidportodiaz.com/

### Samuel entre mundos
- ISBN: 9791387659776
- editorial: Libros Indie
- año: 2025
- páginas actuales del proyecto: 422

### Las manecillas del recuerdo — papel
- ISBN: 9798905149351
- editorial: Monza Ediciones
- publicación: 2026-09-03
- páginas actuales del proyecto: 272

### Las manecillas del recuerdo — ebook
- ISBN: 9798906781925
- editorial: Monza Ediciones
- publicación: 2026-08-12

No propagar las discrepancias 422/412 y 272/266 hasta cerrar #429/#428/#404.

## Procedimiento Claude

1. Buscar por nombre, título y los tres ISBN.
2. Guardar URL de autor y libro si existen.
3. Revisar autoría, portada, sinopsis, editorial, fecha, género, ISBN y formato.
4. Revisar si papel/ebook aparecen como edición/registro coherente y no duplicados accidentales.
5. Si falta un libro, usar la petición desde el área personal documentada por Lecturalia.
6. Si falta el autor pero se crea el libro, comprobar si Lecturalia genera/asocia automáticamente la página de autor o requiere petición específica.
7. Si un dato es incorrecto, enviar una sola petición con campo actual, valor correcto y fuente.
8. No auto-reseñar ni auto-votar para alterar rankings.
9. No usar Lecturalia como fuente primaria para corregir nuestra web: sus datos se contrastan contra editorial/ISBN/DILVE.

## Posible cambio en la web

Si obtenemos una página de autor estable, completa e inequívoca, valorar `Person.sameAs`. Para libros, valorar `Book.sameAs` solo si la URL representa correctamente la obra.

## Prioridad

`P1/P2`: útil por audiencia española, catálogo activo y vía gratuita de petición. Más útil para nosotros que directorios genéricos, aunque por detrás de Goodreads/Amazon/Wikidata/BNE.

## Criterio de cierre

`AUTHOR_AUDITED · SAMUEL_AUDITED · MANECILLAS_AUDITED · MISSING_RECORDS_REQUESTED_IF_NEEDED · METADATA_CORRECT_OR_REQUESTED · DUPLICATES_REVIEWED · SITE_GRAPH_UPDATED_IF_APPLICABLE · NO_SELF_PROMOTION_SPAM`
