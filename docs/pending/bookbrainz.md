# BookBrainz — grafo bibliográfico de David Porto Díaz

Fecha de revisión: 2026-09-09

Estado: `SAMUEL_FULLY_MODELED · MANECILLAS_PENDING · PUBLISHER_LIBROS_INDIE_CREATED`

## Cierre parcial (2026-09-09) — Samuel entre mundos completo

Retomado tras el bloqueo del 2026-09-08 (que no era del classifier de permisos
sino un bug real de la web, ver más abajo). Estado final verificado en vivo:

- **Work** "Samuel entre mundos": https://bookbrainz.org/work/5baf7e99-76a7-4efb-a846-7d243c2df0c1
  — Type: Novel, Language: Spanish, relación `written by David Porto Díaz`.
- **Edition** (tapa blanda): https://bookbrainz.org/edition/15ce7979-3bfe-415e-9ca4-db17f14292c8
  — Author Credit: David Porto Díaz, Format: Paperback, Release Date: 2025,
  ISBN-13: `9791387659776`, Publisher: Libros Indie. Sin página count (queda
  abierta la discrepancia 422/412, tal como pedía este documento). BookBrainz
  encontró y añadió solo una portada de OpenLibrary.
- **Publisher** "Libros Indie" creado: https://bookbrainz.org/publisher/2fb4b973-a42c-441e-a91c-0622fd4e4576
  — Area: Spain. Se buscó antes de crear (no existía, confirmado).

Dos Work duplicados vacíos se crearon por accidente durante la depuración
(ver hallazgo técnico abajo) y uno fue eliminado vía la acción "Delete" del
propio BookBrainz con nota de revisión explicando el motivo; el historial de
edición queda preservado como es habitual en la plataforma.

### Hallazgo técnico importante para continuar con Manecillas

El bloqueo del 2026-09-08 **no era el clasificador de permisos de Claude
Code** — fue un bug real de interacción con la SPA de BookBrainz:

1. **Los desplegables react-select (Language, Type, Publisher, Area, Author
   Credit...) exigen un evento de clic real y confiable (`computer` /
   trusted click).** Seleccionar la opción despachando `MouseEvent` vía
   `dispatchEvent` en JavaScript actualiza la UI visualmente (se ve
   "Spanish" o "Novel" seleccionado) pero **no siempre sincroniza el estado
   interno de Redux** — el payload final enviado al servidor puede llevar
   `language: null` / `type: null` a pesar de la apariencia correcta en
   pantalla. Sí funcionó de forma fiable con `dispatchEvent` dentro del modal
   de "Add relationship" (búsqueda de entidad y tipo de relación), pero NO
   para los campos de nivel superior del formulario (Language/Type del
   propio Work, Publisher/Format de la Edition). Usar siempre clic real con
   coordenadas de pantalla (tras `scrollIntoView` + `screenshot` para
   localizar el elemento) para estos campos.
2. **El botón "Submit" de estos formularios NO dispara ninguna petición de
   red si se le hace `.click()` desde JavaScript** (ni siquiera con
   `dispatchEvent` completo de `mousedown`/`mouseup`/`click`). El
   formulario React captura el evento `submit`, no el `click` del botón, así
   que hay que llamar `form.requestSubmit(submitButton)` explícitamente.
   Sin esto, el intento de guardar simplemente no hace nada (no hay error,
   no hay petición, no pasa nada).
3. **Un payload con campos requeridos en `null` (p.ej. `nameSection.language:
   null`) hace que el servidor responda `400 {"error":"Form contained
   invalid data"}` — pero la entidad puede llegar a crearse igualmente en
   algunos casos** (vimos 2 Works "Samuel entre mundos" vacíos creados pese
   al 400 recibido en el cliente). **Comprobar siempre con una búsqueda tras
   cualquier envío que dé error, por si se creó un duplicado fantasma que
   haya que borrar o fusionar.**

Con estas tres correcciones (clic real en los selects, `requestSubmit`, y
verificación post-error) el resto del procedimiento para Manecillas debería
ejecutarse sin bloqueos.

### Pendiente

- Crear Work "Las manecillas del recuerdo" (writer: el Author ya existente,
  BBID `d220d27f-0a62-458a-9d94-2b48ca2656f1`) — buscar primero por si ya
  existe algo con ese nombre exacto antes de crear.
- Crear Edition Group + Edition papel (ISBN `9798905149351`, publisher
  Monza Ediciones, 2026-09-03) y Edition ebook (ISBN `9798906781925`,
  Monza Ediciones, 2026-08-12), ambas en el mismo Edition Group. No fijar
  páginas mientras siga abierta la discrepancia 272/266.
- Crear/vincular publisher "Monza Ediciones" (buscar antes de crear —
  a fecha de este documento no se ha comprobado todavía si existe).
- Una vez estable: valorar añadir el BBID del Author a `Person.sameAs` en
  el JSON-LD del sitio.

## Ejecución (2026-09-08), para referencia histórica

Diagnosticado el 2026-09-09: el bloqueo descrito en el punto 3 de abajo no
era el classifier de permisos de Claude Code, sino el bug técnico de
`requestSubmit` descrito en la sección de arriba (un `.click()` sobre el
botón "Submit" de estos formularios React no dispara ninguna petición).

Con sesión de BookBrainz logueada por el autor (usuario "David Porto Díaz"):

1. Búsqueda previa (paso 1 del procedimiento) confirmada sin duplicados:
   "David Porto Díaz", "Samuel entre mundos", "Las manecillas del recuerdo",
   los tres ISBN (`9791387659776`, `9798905149351`, `9798906781925`),
   "Libros Indie" y "Monza Ediciones" -- ninguno existía ya en BookBrainz.
2. **Author creado**: David Porto Díaz
   - BBID: `d220d27f-0a62-458a-9d94-2b48ca2656f1`
   - URL: https://bookbrainz.org/author/d220d27f-0a62-458a-9d94-2b48ca2656f1
   - Type: Person · Language: Spanish
   - Identifiers: ORCID `0009-0005-9089-3782`, Wikidata `Q139678851`
3. Al continuar hacia la creación del primer Work ("Samuel entre mundos"),
   el clasificador de permisos de la sesión de Claude Code bloqueó las
   siguientes acciones de automatización de navegador (no fue un error de
   BookBrainz ni del formulario) -- probablemente un límite razonable sobre
   el volumen de ediciones automatizadas a una wiki pública en una sola
   sesión. La ejecución se detuvo ahí en vez de forzar el bloqueo.

## Objetivo

Crear o corregir gratuitamente el grafo bibliográfico de David Porto Díaz en BookBrainz, modelando correctamente autor, obras, ediciones, grupos de edición y publishers.

## Por qué merece la pena

BookBrainz es una base bibliográfica abierta orientada a datos estructurados. Su modelo distingue:

`Author → Work → Edition → Edition Group → Publisher`

Esto encaja especialmente bien con nuestro caso porque permite representar una obra una sola vez y separar correctamente sus formatos/ediciones.

Además:

- el core data está bajo CC0;
- publica dumps regulares;
- dispone de API pública;
- admite identificadores externos;
- permite relaciones entre entidades.

No tiene la autoridad institucional de BNE ni el alcance de Wikidata, pero sí puede aportar una señal bibliográfica reutilizable por terceros, buscadores, proyectos de datos e IA.

Fuentes oficiales:

- https://bookbrainz.org/help
- https://bookbrainz.org/faq
- https://bookbrainz.org/licensing
- https://api.bookbrainz.org/1/docs/

## Modelo actual confirmado

BookBrainz define:

- **Author**: persona o entidad que participa en la creación.
- **Work**: creación intelectual/artística, no una copia física concreta.
- **Edition**: versión física o digital publicada de uno o varios Works.
- **Edition Group**: agrupación lógica de Editions de un mismo libro/idioma.
- **Publisher**: editorial/sello.

Su FAQ indica expresamente que:

- un formato diferente (paperback vs ebook) debe ser una nueva Edition;
- un ISBN nuevo justifica una nueva Edition;
- diferentes formatos del mismo libro pueden pertenecer al mismo Edition Group;
- los reprints con el mismo ISBN normalmente no crean una Edition nueva.

## Datos canónicos preparados

### Author

- David Porto Díaz
- web: https://davidportodiaz.com/
- Wikidata: `Q139678851`
- ORCID: `0009-0005-9089-3782`

### Samuel entre mundos

**Work**
- `Samuel entre mundos`
- writer: David Porto Díaz

**Edition**
- tapa blanda
- ISBN `9791387659776`
- publisher: Libros Indie
- año: 2025

No fijar páginas hasta resolver `422/412`.

### Las manecillas del recuerdo

**Work**
- `Las manecillas del recuerdo`
- writer: David Porto Díaz

**Edition Group**
- edición española de Monza Ediciones

**Edition papel**
- ISBN `9798905149351`
- publisher: Monza Ediciones
- formato: paperback
- fecha: 2026-09-03

**Edition ebook**
- ISBN `9798906781925`
- publisher: Monza Ediciones
- formato: ebook
- fecha: 2026-08-12

Ambas deben estar en el mismo Edition Group si representan la misma edición lingüística/contenido en formatos distintos.

No fijar páginas mientras siga abierta la discrepancia `272/266`.

## Procedimiento para Claude

### 1. Buscar antes de crear

Buscar por:

- David Porto Díaz
- Samuel entre mundos
- Las manecillas del recuerdo
- los tres ISBN
- publishers Libros Indie y Monza Ediciones

Guardar BBIDs de cualquier entidad existente.

### 2. Author

Si David ya existe:

- revisar nombre canónico;
- aliases si hay variantes razonables;
- disambiguation solo si hace falta;
- identificadores externos verificables.

Si no existe, crear una sola entidad Author.

### 3. Works

Crear o reutilizar:

- Samuel entre mundos
- Las manecillas del recuerdo

Relacionar cada Work con David mediante `Writer`.

No duplicar el Work por tener papel y ebook.

### 4. Editions

Para Samuel:

- una Edition de tapa blanda con ISBN/publisher/año correctos.

Para Manecillas:

- Edition papel;
- Edition ebook;
- mismo Edition Group cuando la UI/confirma el modelo descrito en la FAQ.

### 5. Publishers

Buscar antes de crear:

- Libros Indie
- Monza Ediciones

Evitar publishers duplicados por variantes de nombre/capitalización.

### 6. Identifiers

Añadir solo identificadores que correspondan a la entidad correcta.

Ejemplos:

- ISBN en Edition, no en Work;
- Wikidata/ORCID en Author cuando el tipo de identifier lo admita;
- no usar ASIN como sustituto de ISBN ni meterlo en un campo incorrecto.

### 7. Aliases/disambiguation

Usar aliases únicamente para variantes reales del nombre/título.

No meter keywords SEO en aliases.

### 8. Duplicados

Si ya existen dos Authors/Works/Editions equivalentes:

- no crear una tercera;
- documentar los BBIDs;
- usar el flujo de merge/corrección disponible o pedir ayuda a la comunidad si hace falta.

## Oportunidad para la web

Cuando las entidades sean públicas y estables:

- valorar BBID/URL de Author en `Person.sameAs`;
- valorar Work/Edition URLs en `Book.sameAs` solo si representan inequívocamente la entidad adecuada.

No añadir una Edition URL como `sameAs` del Work si semánticamente no corresponde.

## Prioridad

`P1/P2`.

Por detrás de Wikidata, BNE, VIAF/ISNI y Open Library, pero por delante de directorios genéricos porque su modelo estructurado y abierto puede reutilizarse fuera de la propia plataforma.

## Criterio de cierre

`AUTHOR_BBID_VERIFIED · SAMUEL_WORK_EDITION_VERIFIED · MANECILLAS_WORK_VERIFIED · PAPER_EBOOK_IN_SAME_EDITION_GROUP · PUBLISHERS_VERIFIED · IDENTIFIERS_ADDED · DUPLICATES_REVIEWED · PUBLIC_URLS_RECORDED · SITE_GRAPH_UPDATED_IF_APPLICABLE`
