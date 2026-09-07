# ISFDB — Samuel entre mundos + autoridad de autor

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · MODERATED_EDIT_MODEL_CONFIRMED · SAMUEL_HIGH_FIT · READY_FOR_SUBMISSION`

## Objetivo

Conseguir una representación bibliográfica correcta de `Samuel entre mundos` y de David Porto Díaz en Internet Speculative Fiction Database (ISFDB), usando el flujo comunitario moderado y sin convertir la ficha en publicidad.

## Por qué merece la pena

ISFDB está especializada en ciencia ficción, fantasía y géneros relacionados. `Samuel entre mundos` encaja directamente por género y una ficha correcta aporta:

- autoridad bibliográfica temática externa;
- descubrimiento por lectores de fantasía/speculative fiction;
- otra entidad pública indexable del autor/obra;
- relación entre título, edición, publisher e ISBN;
- un posible nodo adicional para `sameAs` si queda inequívoco.

Para `Las manecillas del recuerdo`, no forzar inclusión: solo auditar si ya aparece o si ISFDB considera que entra claramente en su alcance editorial.

## Cómo funciona ISFDB actualmente

La documentación vigente indica que:

- los usuarios registrados pueden enviar nuevas novelas/publicaciones y correcciones;
- las propuestas pasan por moderación;
- `Add New Novel` se usa cuando la novela no existe todavía;
- si el título ya existe y falta una edición/publicación, se usa `Add Publication to This Title`, `Clone This Pub` o edición de publicación según el caso;
- los registros de autor no se crean manualmente como perfiles: aparecen a partir de publicaciones atribuidas a ese autor;
- los registros ya verificados deben tratarse con cuidado y, si se quiere cambiar información conflictiva, se recomienda contactar con el verifier/moderadores.

Fuentes oficiales:

- https://www.isfdb.org/wiki/index.php/ISFDB:FAQ
- https://www.isfdb.org/wiki/index.php/Help:Navigation_Bar
- https://www.isfdb.org/wiki/index.php/ISFDB:Help_desk

## Datos canónicos preparados

### Samuel entre mundos

- Autor: David Porto Díaz
- Editorial: Libros Indie
- ISBN: `9791387659776`
- Año editorial: 2025
- Formato: tapa blanda
- Género: fantasía juvenil / portal fantasy

No fijar el page count mientras siga abierta la discrepancia `422/412` en #429/#404.

### Autor

- Nombre canónico: David Porto Díaz
- Web oficial: https://davidportodiaz.com/
- Wikidata: `Q139678851`
- ORCID: `0009-0005-9089-3782`

No meter estos identificadores en ISFDB si el modelo de la ficha no los admite o no son pertinentes.

## Procedimiento para Claude

1. Buscar `David Porto Díaz`.
2. Buscar `Samuel entre mundos`.
3. Buscar ISBN `9791387659776`.
4. Revisar variantes del nombre/título antes de crear nada.
5. Si existe el título, guardar URL/ID y revisar si la edición de Libros Indie ya está vinculada.
6. Si falta solo la edición, usar la función de añadir publicación/clone, no `Add New Novel`.
7. Si no existe ninguna entrada, usar `Add New Novel` con metadata bibliográfica verificable.
8. Revisar:
   - autor;
   - título;
   - año;
   - publisher;
   - ISBN;
   - formato;
   - idioma;
   - portada solo cuando la licencia/fuente sea válida;
   - notas bibliográficas útiles.
9. Si un registro está primary/secondary verified y el cambio contradice datos existentes, seguir la etiqueta de verifier/moderación antes de sustituir información.
10. Guardar submission ID/estado si queda pendiente de moderación.
11. Tras aceptación, comprobar ficha pública y posible página de autor generada.

## Duplicados

No crear un nuevo título si:

- ya existe otra edición de Samuel;
- existe con una variante menor de nombre;
- el ISBN está registrado bajo un título equivalente.

Si hay duplicados o title records separados incorrectamente, usar las herramientas de merge/unmerge/variant según indique ISFDB o pedir ayuda en Help Desk/Moderator noticeboard.

## Portada

No subir una portada simplemente porque la tengamos en el repo. ISFDB tiene reglas propias de imágenes/licencias y flujo separado. Primero crear/verificar el registro y después seguir sus directrices de cover image.

## Las manecillas del recuerdo

Acción limitada:

1. buscar título/autor/ISBN;
2. si ya existe, revisar si la clasificación es razonable;
3. si no existe, no crearla salvo que su contenido encaje claramente dentro del alcance de ISFDB;
4. documentar `OUT_OF_SCOPE_OR_NOT_NEEDED` si procede.

## Posible cambio en la web

Solo después de tener URLs finales estables:

- `Person.sameAs` para una página inequívoca del autor;
- `Book.sameAs` para una entidad estable de Samuel.

No añadir una URL de búsqueda o submission pendiente.

## Prioridad

`P1 para Samuel`.

Es más valiosa que un directorio genérico porque es una base especializada y moderada exactamente en el género de Samuel.

## Criterio de cierre

`SAMUEL_SEARCHED · SAMUEL_TITLE_OR_PUBLICATION_CREATED_IF_NEEDED · AUTHOR_RECORD_VERIFIED · MODERATION_ACCEPTED_OR_PENDING · DUPLICATES_REVIEWED · MANECILLAS_SCOPE_DECIDED · PUBLIC_URLS_RECORDED · SITE_GRAPH_UPDATED_IF_APPLICABLE · NO_PROMOTIONAL_DATA`
