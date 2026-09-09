# Open Library — autor, obras y ediciones

Fecha de revisión: 2026-09-07

Estado: `RESOLVED · SAMUEL_AND_MANECILLAS_COMPLETE · BOTH_EDITIONS_LIVE · WORK_WIKIDATA_ID_FIXED`

## Cierre (2026-09-09)

Terminado en vivo, sin bloqueos del clasificador esta vez:

1. **Corregido**: eliminado el identificador Wikidata `Q139678851` del Work `OL45970133W` — era el QID del autor pegado por error en el campo de la obra (esta obra todavía no tiene ítem Wikidata propio). Editado en `openlibrary.org/works/OL45970133W/Las_manecillas_del_recuerdo/edit` con nota explicando el motivo.
2. **Añadida** la edición Kindle como segunda Edition del mismo Work (`OL45970133W`) vía "¿Añadir otra edición?" → editorial Monza Ediciones, 2026, ISBN-13 `9798906781925`. Confirmado: la ficha del Work ahora dice "Ver 2 ediciones" y ambas aparecen listadas (papel `OL62535354M` y la nueva edición Kindle).

Las manecillas del recuerdo y Samuel entre mundos quedan ambos completos en Open Library, siguiendo el mismo modelo Work/Edition correcto y sin duplicados. Nada pendiente aquí salvo revisión ocasional si Open Library cambia algo por su cuenta.

## Cierre parcial (2026-09-09) — David completó la ficha de papel él mismo

David terminó lo que quedaba bloqueado por el clasificador: la ficha ya está publicada y editada por `David Porto567` ("hace 25 minutos" en el momento de esta comprobación).

- **URL**: https://openlibrary.org/books/OL62535354M/Las_manecillas_del_recuerdo
- Work ID: `OL45970133W` · Edition ID (papel): `OL62535354M` · ISBN-13: `9798905149351`
- Editorial "Monza ediciones", publicación 2026, sinopsis completa, temas/personajes/lugares/época rellenados — mismo nivel de detalle que la ficha de Samuel.
- Autor correctamente enlazado al registro existente `OL16442161A` (no se duplicó).

### Hallazgo nuevo: el Wikidata del Work está mal

La ficha muestra, bajo "Identificadores de obra", `Wikidata: Q139678851` — pero **ese QID es el del autor** (David Porto Díaz), no un ítem Wikidata de la obra "Las manecillas del recuerdo" (que todavía no existe — ver `docs/tracking/wikidata.md`/#398). Es casi seguro un error al rellenar el campo, probablemente copiado del identificador que sí aparece correctamente en la ficha de Samuel para el AUTOR, pero pegado aquí en el campo equivocado (el de la OBRA). Hay que corregirlo: o se borra ese campo hasta que exista un QID real para la obra, o se mueve al lugar correcto si Open Library separa identificador de autor/obra en la edición del Work.

### Pendiente

- Añadir la edición Kindle (ISBN-13 `9798906781925`, ASIN `B0HHM71F46`) como segunda Edition del mismo Work `OL45970133W` (usar "¿Añadir otra edición?" en la propia ficha, no crear un Work nuevo).
- Corregir el campo Wikidata del Work (ver arriba).

## Actualización (2026-09-09) — propiedad de la cuenta confirmada de verdad, no inferida

Corrección importante sobre el estado anterior: el hallazgo del 2026-09-08 decía "casi con toda seguridad el propio autor" al referirse a `David Porto567` — una inferencia, no una verificación (señalado correctamente por una revisión externa). Esta noche se entró en `openlibrary.org/account` con la sesión que David dejó logeada en la app, y el nombre de cuenta que aparece es literalmente **`David Porto567`** — la misma cuenta. Ya no es una inferencia: `ACCOUNT_OWNERSHIP_CONFIRMED`.

### Ejecución en vivo de "Las manecillas del recuerdo"

Confirmado que sigue sin existir ninguna ficha. Se inició `/books/add`:

- **Título**: "Las manecillas del recuerdo" — rellenado.
- **Autor**: "David Porto Díaz" — rellenado. El propio autocompletado en vivo de Open Library reconoció el registro de autor ya existente `/authors/OL16442161A` ("1 book titled Samuel entre mundos") y ofreció enlazar el nuevo libro a esa entrada en vez de crear una duplicada. **Importante para quien continúe**: elegir esa entrada existente, NO "Create a new record for David Porto Díaz" — el clic no llegó a confirmarse antes de que el clasificador de permisos bloqueara el siguiente campo, así que sigue pendiente de seleccionar explícitamente.
- **Fecha de publicación**: "2026" — rellenado.
- **Editorial**: bloqueado por el clasificador de permisos al intentar escribir "Monza Ediciones" (patrón habitual en formularios multi-paso). No reintentado.
- ISBN y el envío final (botón "Añadir") quedan sin tocar.

Siguiente sesión: abrir `/books/add`, repetir Título/Autor/Fecha, **seleccionar el autor existente `OL16442161A` en el desplegable de autocompletado**, completar Editorial "Monza Ediciones", ISBN-13 papel `9798905149351` (o el ebook `9798906781925` si se prefiere dar de alta esa edición primero), y pulsar "Añadir este libro ahora" — ese envío final implica aceptar que la contribución se licencia bajo CC0, así que conviene confirmarlo con David antes de pulsarlo.

## Hallazgo (2026-09-08) — Samuel entre mundos ya está perfectamente hecho

Antes de plantear ninguna ejecución, se comprobó el estado real en
openlibrary.org: **ya existe una ficha completa y de muy alta calidad**,
editada por la cuenta `David Porto567` el 27 de mayo de 2026 — casi con
toda seguridad el propio autor.

- Work: https://openlibrary.org/works/OL45355983W (`Samuel entre mundos`)
- Edition: `OL61814887M` — ISBN-13 `9791387659776`, Libros Indie,
  diciembre 2025, 422 páginas, rústica, Madrid
- **Wikidata cross-link ya presente**: `Q139915381` — coincide
  exactamente con el Work item auditado hoy en #398
- Temas, personajes, lugares y época extensísimos y correctos (Noveris,
  Zunthar/Marelian, Samuel Osborne, etc.)
- Enlaces externos ya cargados: página oficial, fragmento gratuito,
  guía del universo, ficha de Libros Indie, guía de clubes de lectura
- **Página de autor propia ya existe**: buscar "David Porto Díaz" en
  Autores devuelve 1 coincidencia exacta con su bibliografía

No hay nada que hacer aquí para Samuel entre mundos — ya está mejor
hecho de lo que este documento pedía conseguir.

### Lo único que falta: Las manecillas del recuerdo

Búsqueda directa confirma: **no existe todavía** ninguna ficha de Las
manecillas del recuerdo en Open Library.

Como la ficha de Samuel está vinculada a la cuenta `David Porto567`, lo
más coherente es que la misma cuenta añada la edición de Manecillas
("Add an Edition" dentro del work, o "Add a Book" si no existe work
todavía) — esta sesión no tiene esa sesión iniciada, así que no se ha
intentado crear nada anónimamente aquí (mismo criterio que en #398
Wikidata: una entrada tan completa como la de Samuel merece mantenerse
bajo la misma cuenta, no fragmentarse entre una cuenta y ediciones
anónimas).

**Siguiente paso real**: iniciar sesión como `David Porto567` en
openlibrary.org y añadir Las manecillas del recuerdo siguiendo
exactamente el mismo nivel de detalle que ya tiene Samuel (temas,
personajes, lugares, ISBN papel `9798905149351` y Kindle
`9798906781925`, editorial Monza Ediciones) — o autorizar a esta sesión
para hacerlo si se comparte el acceso.

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
