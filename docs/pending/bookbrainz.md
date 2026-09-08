# BookBrainz — grafo bibliográfico de David Porto Díaz

Fecha de revisión: 2026-09-07

Estado: `PARTIALLY_EXECUTED · AUTHOR_CREATED · WORKS_EDITIONS_PENDING`

## Ejecución (2026-09-08)

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

### Pendiente (siguiendo el mismo procedimiento del documento original)

- Crear Work "Samuel entre mundos" (writer: el Author de arriba).
- Crear Edition de Samuel: tapa blanda, ISBN `9791387659776`, publisher
  Libros Indie, año 2025. No fijar páginas (queda abierta la discrepancia
  422/412 ya señalada en el documento original).
- Crear Work "Las manecillas del recuerdo" (writer: el Author de arriba).
- Crear Edition Group + Edition papel (ISBN `9798905149351`, Monza
  Ediciones, 2026-09-03) y Edition ebook (ISBN `9798906781925`, Monza
  Ediciones, 2026-08-12) de Manecillas, ambas en el mismo Edition Group.
  No fijar páginas mientras siga abierta la discrepancia 272/266.
- Crear/vincular publishers Libros Indie y Monza Ediciones (buscar antes
  de crear, ya confirmado que no existen todavía).
- Una vez estable: valorar añadir el BBID del Author a `Person.sameAs` en
  el JSON-LD del sitio.

Todo lo anterior puede repetirse en una sesión nueva siguiendo el
"Procedimiento para Claude" original de este documento tal cual, ya que
sigue siendo válido -- solo falta ejecutarlo desde el paso 3 (Works) en
adelante.

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
