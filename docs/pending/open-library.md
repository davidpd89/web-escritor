# Open Library — autor, obras y ediciones

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · OPEN_LIBRARY_EDIT_MODEL_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION`

## Objetivo

Dejar correctamente representados a David Porto Díaz, `Samuel entre mundos` y `Las manecillas del recuerdo` en Open Library, distinguiendo Work y Edition y evitando duplicados.

## Modelo correcto de Open Library

La guía oficial actual indica:
- `Add a Book` crea un Work y una Edition cuando la obra no existe;
- si el Work ya existe y falta una edición concreta, hay que usar `Add an Edition` dentro del Work;
- los duplicados de autores, Works o Editions solo pueden fusionarlos Open Librarians;
- mover una Edition asociada al Work equivocado también es función de librarians; los usuarios normales deben reportarlo.

Fuentes:
- https://openlibrary.org/help/faq/editing/getting-started-guide
- https://openlibrary.org/help/faq/editing

## Datos canónicos

### Autor
- David Porto Díaz
- Web: https://davidportodiaz.com/

### Samuel entre mundos
- Editorial: Libros Indie
- ISBN: 9791387659776
- Año: 2025
- Formato: tapa blanda
- Páginas actuales del proyecto: 422

### Las manecillas del recuerdo — papel
- Editorial: Monza Ediciones
- ISBN: 9798905149351
- Publicación: 2026-09-03
- Formato: tapa blanda
- Páginas actuales del proyecto: 272

### Las manecillas del recuerdo — ebook
- Editorial: Monza Ediciones
- ISBN: 9798906781925
- Publicación: 2026-08-12
- Formato: ebook

No propagar todavía como autoridad externa las discrepancias 422/412 de Samuel o 272/266 de Manecillas: resolverlas primero en #429/#428/#404.

## Procedimiento para Claude

1. Buscar al autor por `David Porto Díaz` y variantes razonables.
2. Buscar ambos títulos y los tres ISBN exactos.
3. Registrar Author ID, Work ID y Edition ID de todo lo que ya exista.
4. Verificar que cada Edition está dentro del Work correcto.
5. Si falta una Edition pero el Work existe, usar `Add an Edition`; no crear un Work duplicado.
6. Para cada edición revisar: ISBN, publisher, fecha, idioma, formato, páginas y portada frontal exacta.
7. No sustituir una portada correcta por una creatividad promocional.
8. Revisar autores/works/editions duplicados.
9. Si hace falta merge o mover una Edition, abrir request a Open Library con URLs/IDs exactos.
10. Guardar el History de las ediciones realizadas como evidencia.

## Posible mejora en nuestra web

Cuando existan URLs estables e inequívocas:
- valorar Open Library Author en `Person.sameAs`;
- valorar Work/Edition correspondiente en `Book.sameAs`;
- actualizar el owner/generador factual y ejecutar QA/CI.

No añadir `sameAs` a una búsqueda genérica ni a una edición equivocada.

## Criterio de cierre

`AUTHOR_VERIFIED · SAMUEL_WORK_VERIFIED · SAMUEL_EDITION_VERIFIED · MANECILLAS_WORK_VERIFIED · PAPER_EDITION_VERIFIED · EBOOK_EDITION_VERIFIED_OR_ADDED · DUPLICATES_REVIEWED · LIBRARIAN_REQUESTS_RECORDED · SITE_GRAPH_UPDATED_IF_APPLICABLE`
