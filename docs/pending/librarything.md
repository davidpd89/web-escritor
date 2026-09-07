# LibraryThing — autor, libros y comunidad

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · FREE_AUTHOR_PROGRAM_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION`

## Objetivo

Conseguir una presencia correcta de David Porto Díaz y sus libros en LibraryThing y aprovechar únicamente las funciones gratuitas que sí aportan descubrimiento, autoridad bibliográfica/comunitaria y relación con lectores.

## Por qué sí merece la pena

LibraryThing es completamente gratuito y declara una comunidad cercana a 3 millones de amantes de los libros. Su propia documentación para autores permite:
- reclamar estatus oficial de `LibraryThing Author` desde la página de autor mediante `Is this you?`;
- mejorar página de autor con foto y enlaces a la web;
- completar `Common Knowledge` de autor y obras;
- catalogar libros y conectar con lectores;
- participar en `Hobnob with Authors`;
- usar Early Reviewers para nuevos títulos.

Fuentes oficiales:
- https://www.librarything.com/about/authors
- https://www.librarything.com/about
- https://www.librarything.com/t/es

## Guardrail comunitario

LibraryThing prohíbe usar la plataforma como medio publicitario agresivo. No:
- mensajes privados masivos;
- solicitudes indiscriminadas;
- posts promocionales genéricos;
- auto-reseñas o auto-ratings para manipular medias.

La propia web marca las reseñas del propio autor como tales; no nos aporta valor hacerlo.

## Datos canónicos

### David Porto Díaz
- Web: https://davidportodiaz.com/
- ORCID: 0009-0005-9089-3782
- Wikidata: Q139678851

### Samuel entre mundos
- ISBN: 9791387659776
- Editorial: Libros Indie
- Año: 2025
- Páginas actuales del proyecto: 422

### Las manecillas del recuerdo — papel
- ISBN: 9798905149351
- Editorial: Monza Ediciones
- Fecha: 2026-09-03
- Páginas actuales del proyecto: 272

### Las manecillas del recuerdo — ebook
- ISBN: 9798906781925
- Editorial: Monza Ediciones
- Fecha: 2026-08-12

No propagar aún las discrepancias 422/412 o 272/266 hasta resolver #429/#428/#404.

## Procedimiento Claude

1. Buscar autor, Samuel y Manecillas por nombre/título/ISBN.
2. Identificar Author page, Work IDs y ediciones existentes.
3. Si existe página de autor, usar `Is this you?` para solicitar `LibraryThing Author` si la opción está disponible.
4. Verificar que Samuel y Manecillas están asociados al autor correcto.
5. Revisar combinación/separación correcta de Works y Editions: papel y ebook de Manecillas no deben convertirse en dos obras distintas si son la misma obra con ediciones diferentes.
6. Revisar portada, publisher, fecha, ISBN, formato e idioma.
7. Completar `Common Knowledge` solo con hechos verificables y útiles; no llenar campos por llenar.
8. Añadir foto y web oficial a la página de autor si el sistema lo permite y faltan.
9. Revisar duplicados y solicitar combinación/corrección comunitaria si hace falta.
10. Guardar URLs/IDs canónicos.

## Oportunidades gratuitas adicionales

### LibraryThing Local
Si existe una presentación/firma pública futura, valorar añadirla a LibraryThing Local. La documentación de publishers indica que la plataforma integra lugares y eventos literarios.

### Author Interviews / Author Chats
LibraryThing mantiene entrevistas editoriales y chats con autores. Son oportunidades editoriales, no garantizadas; solo proponer cuando haya un lanzamiento/evento real y sin spam.

### Early Reviewers
Se gestiona aparte en #469 porque es temporal y requiere review copy completa autorizada por Monza.

## Posible cambio en la web

Si existe una página de autor oficial estable y reclamada:
- valorar añadirla a `Person.sameAs`;
- añadir Work URLs a `Book.sameAs` únicamente si representan inequívocamente la obra correcta.

## Criterio de cierre

`AUTHOR_PAGE_FOUND · LIBRARYTHING_AUTHOR_CLAIMED_OR_REQUESTED · SAMUEL_WORK_VERIFIED · MANECILLAS_WORK_VERIFIED · EDITIONS_REVIEWED · COMMON_KNOWLEDGE_CURATED · DUPLICATES_REVIEWED · WEBSITE_LINKED · SITE_GRAPH_UPDATED_IF_APPLICABLE · NO_SPAM`
