# LibraryThing — autor, libros y comunidad

Fecha de revisión: 2026-09-07 (ejecutado: 2026-09-14, completado: 2026-09-15)

Estado: `SAMUEL_YEAR_FIXED · DUPLICATE_WORKS_COMBINED · AUTHOR_CLAIM_SUBMITTED_PENDING_REVIEW · CLOSED`

## Ejecución (2026-09-14, sesión `DavidPortoDiaz` autenticada)

### Buena noticia: reseña real de 5 estrellas de un lector

`Las manecillas del recuerdo (Spanish Edition)` (work `37203222`) tiene
una reseña real de 5 estrellas de un lector genuino, `carlosbermejop`
(125 reseñas en su perfil), publicada el 8 de septiembre de 2026:

> "Funciona de maravilla como antología, especialmente gracias a la
> historia marco del reloj y los temas comunes que recorren todo el
> libro: el tiempo, la memoria, el legado..."

URL: `https://www.librarything.com/work/37203222/book/322955985`

### Corregido: año de publicación de Samuel

La ficha de Samuel entre mundos en la biblioteca personal de David
(work `36438284`) tenía `Publication: Libros Indie, 2026` y
`Publication Date: 2026` — incorrecto, el año real es 2025 (diciembre
2025, confirmado ya en Amazon.es/ISFDB). Corregido vía "Edit Book" a
`2025-12-01` / `Libros Indie, 2025`. Verificado tras guardar.

### Corregido: dos fichas de obra (Work) separadas para Manecillas, ahora combinadas

El autor tenía **dos Work IDs distintos** para el mismo libro:

- `37203951` — "Las Manecillas Del Recuerdo", 0 members reales; su
  única edición listada era el ISBN `9798906781925` — el **Kindle**,
  no un registro genérico de feed externo como se pensó la ronda
  anterior.
- `37203222` — "Las Manecillas del Recuerdo (Spanish Edition)", 1
  member real (`carlosbermejop`) con la reseña de 5 estrellas citada
  arriba.

La ronda anterior no combinó esto por no encontrar la herramienta y por
prudencia ante una wiki comunitaria. La herramienta sí existe y es de
uso normal para cualquier miembro: desde la página de la obra →
`Editions` (`/work/<id>/editions`) → módulo "Potential Combinations" →
`Combine/separate potential work combinations…`
(`/combine.php?work=<id>`), marcar ambas obras y pulsar "Combine
Selected Works" → confirmar en la pantalla "Combine Works".

Esto **no es fusionar dos ediciones distintas en una** — el modelo de
LibraryThing usa "Work" precisamente para agrupar todas las ediciones
(papel, Kindle, traducciones) de una misma obra bajo una ficha común,
manteniendo cada edición/ISBN identificable dentro. Con el Kindle y el
papel de Manecillas ya identificados como ediciones de la misma novela,
combinarlas es exactamente lo que el sistema espera, no un riesgo.

**Ejecutado y verificado**: ambas obras combinadas el 2026-09-15. La
página del autor ahora muestra **2 Works** (antes 3). La reseña de
`carlosbermejop` sigue visible en la ficha combinada, junto con ambas
ediciones (Kindle ISBN `9798906781925` y la edición en papel).

### Confirmado: Common Knowledge del autor ya está bien completado

Bio corta, nacionalidad, lugar de nacimiento, premios y ocupación ya
constan correctamente en la página de autor (`/a/31983928/`), con la
forma canónica en español "Porto Díaz, David" (convención bibliográfica
normal, no un error). No se ha tocado.

### Solicitado: estatus de LibraryThing Author

Localizado en la página de autor, sección "Is This You?" →
"Become a LibraryThing Author" (`/author_claim.php?author=portodazdavid`):
formulario para seleccionar una obra propia + mensaje opcional +
aceptar las normas del programa ("How Authors Can Use LibraryThing").
Completado seleccionando `Samuel entre mundos`, con mensaje
identificando al autor y ambos libros, aceptando las normas y enviando
la solicitud.

Esto es un programa **moderado por el equipo de LibraryThing**, no
instantáneo: no hay ninguna confirmación visible en la propia web tras
enviarlo (ni aquí ni en el perfil), así que el resultado (aprobación o
petición de más información) llegará por email o mensaje interno de
LibraryThing más adelante — normal en un programa de curación humana,
no un fallo. No se ha vuelto a intentar más de lo necesario para no
generar solicitudes duplicadas.

### Qué queda

Nada accionable por ahora: revisar en unos días si LibraryThing
confirma el estatus de autor (badge amarillo "LT Author" en el perfil y
en las fichas de las obras) o pide algo más.

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

## Intento de verificación directa (2026-09-08)

Se intentó comprobar directamente si ya existe la ficha de Samuel entre
mundos (una referencia previa de otro documento apuntaba a
`librarything.com/work/36438284/t/Samuel-entre-mundos`). librarything.com
está detrás de un challenge anti-bot activo ("Verificación de seguridad
en curso") que no se ha intentado completar — mismo criterio que con
isni.org esta noche: no es responsable sortear verificaciones anti-bot
con un navegador automatizado.

**Esta comprobación necesita hacerse a mano** desde un navegador normal.
Si la URL de arriba ya resuelve a una ficha real, esta PR podría estar en
un estado similar a Open Library (#402): ya hecho, solo falta
confirmarlo. Vale la pena que el autor la abra directamente en su propio
navegador para confirmar antes de decidir si hace falta reclamar
"LibraryThing Author" o completar algo.
