# aNobii — catálogo y descubrimiento lector

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · SPANISH_CATALOG_ACTIVE · FREE_CONTRIBUTION_ROUTE_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION`

## Objetivo

Comprobar y, cuando falten, incorporar gratuitamente las fichas correctas de David Porto Díaz, `Samuel entre mundos` y `Las manecillas del recuerdo` en aNobii, usando la plataforma como superficie de descubrimiento lector y catálogo, no como autoridad bibliográfica primaria.

## Estado actual verificado

aNobii sigue activa en 2026 y ofrece interfaz completa en español. La navegación pública actual incluye:

- buscador por **título, autor o ISBN**;
- libros, colecciones, clasificaciones y comunidad;
- categorías como `Ciencia ficción y fantasía` y `Adolescentes`;
- sección `Contribuir`;
- `Directrices para contribuir`;
- botón `Proponer un nuevo libro`;
- `Grupo de asistencia`;
- canal `Escríbenos`.

Fuentes públicas actuales:

- https://www.anobii.com/es/
- https://www.anobii.com/es/charts
- cualquier ficha pública actual expone en el footer `Directrices para contribuir` y `Proponer un nuevo libro`.

La UI pública observada muestra versión `v5.35.0` en septiembre de 2026, por lo que no estamos documentando una funcionalidad histórica abandonada.

## Qué valor aporta

Valor real, aunque secundario:

1. otra ficha pública indexable del libro/autor;
2. búsqueda directa por ISBN;
3. descubrimiento dentro de una comunidad lectora internacional y multilingüe;
4. clasificación en géneros útiles para Samuel;
5. vía gratuita para proponer un título ausente;
6. posible referral hacia tiendas/otras superficies según la ficha.

No usar aNobii como fuente para corregir DILVE, ISBN, Wikidata, BNE o nuestra web. Los datos canónicos fluyen **hacia** aNobii.

## Datos canónicos preparados

### Samuel entre mundos

- Autor: David Porto Díaz
- Editorial: Libros Indie
- ISBN: `9791387659776`
- Año: 2025
- Formato: tapa blanda

### Las manecillas del recuerdo — papel

- Autor: David Porto Díaz
- Editorial: Monza Ediciones
- ISBN: `9798905149351`
- Publicación: 2026-09-03
- ASIN: `B0HHY9MYLM`

### Las manecillas del recuerdo — ebook

- Autor: David Porto Díaz
- Editorial: Monza Ediciones
- ISBN: `9798906781925`
- Publicación: 2026-08-12
- ASIN: `B0HHM71F46`

No fijar todavía las discrepancias de páginas `422/412` de Samuel o `272/266` de Manecillas hasta cerrar #429/#428/#404.

## Procedimiento de ejecución

1. Buscar por nombre del autor.
2. Buscar los tres ISBN exactos.
3. Buscar por título sin ISBN por si existe una ficha sin identificador correcto.
4. Registrar cualquier URL existente.
5. Revisar en cada ficha:
   - autor;
   - título;
   - ISBN;
   - publisher;
   - idioma;
   - fecha/año;
   - portada;
   - edición/formato;
   - género/categoría;
   - otras ediciones enlazadas.
6. Si un libro falta realmente, entrar en `Proponer un nuevo libro` y revisar primero las directrices vigentes.
7. No duplicar un Work porque exista papel y ebook: seguir el modelo que use aNobii para ediciones.
8. Si existe un duplicado o edición mezclada, usar la vía de contribución/soporte y guardar la solicitud.
9. Revisar el resultado público en desktop y móvil.
10. Guardar URL final y fecha.

## Género

Para Samuel interesa comprobar cómo clasifica aNobii obras de fantasía juvenil. Existen categorías públicas como:

- `Ciencia ficción y fantasía`;
- `Adolescentes`.

No elegir categoría para ganar visibilidad si no corresponde al contenido real. Si la plataforma permite varias, usar únicamente las justificables por la obra.

Para Manecillas no asumir `fantasía` ni `juvenil`; clasificar según el modelo real de la plataforma y la obra.

## Perfil / autor

No asumir que una cuenta de usuario equivale a una página de autor reclamada. Claude debe distinguir:

- cuenta de usuario;
- página bibliográfica de autor;
- fichas de libros.

Si aNobii no ofrece claim de autor, no fabricar uno mediante un perfil de lector.

## Reseñas y actividad

No:

- auto-reseñar los propios libros;
- auto-calificarlos;
- crear actividad artificial para subir rankings;
- mandar mensajes promocionales masivos.

Sí:

- corregir datos;
- responder a incidencias si la plataforma lo permite;
- conservar URLs públicas;
- medir si realmente genera referrals antes de dedicar más tiempo.

## Posible cambio en la web

Solo si queda una URL estable e inequívoca de autor/obra:

- `Person.sameAs` para una verdadera página pública de autor;
- `Book.sameAs` para una ficha canónica de obra/edición.

No añadir perfiles de usuario genéricos por acumular `sameAs`.

## Prioridad

`P2`.

Por detrás de Amazon Author, Goodreads, Wikidata, BNE, ISNI, VIAF, Open Library, LibraryThing, ALIBRATE y Lecturalia. Aun así merece ejecución porque es gratuita, activa y permite alta/corrección directa.

## Criterio de cierre

`AUTHOR_SEARCHED · SAMUEL_FOUND_OR_PROPOSED · MANECILLAS_FOUND_OR_PROPOSED · EDITIONS_VERIFIED · DUPLICATES_REVIEWED · METADATA_CORRECT_OR_REQUESTED · PUBLIC_URLS_RECORDED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · NO_PAID_FEATURES · NO_SELF_RATING`
