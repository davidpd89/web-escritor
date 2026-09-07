# BookBrainz — grafo bibliográfico de David Porto Díaz

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · ENTITY_MODEL_CONFIRMED · OPEN_DATA_VALUE_CONFIRMED · READY_FOR_EXECUTION`

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
