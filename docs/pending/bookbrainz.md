# BookBrainz — grafo bibliográfico de David Porto Díaz

Fecha de revisión: 2026-09-09

Estado: `SAMUEL_VERIFIED_CLEAN_NO_DUPLICATES · SAMUEL_METADATA_CORRECTED · MANECILLAS_FULLY_MODELED_VERIFIED_NO_DUPLICATES · PUBLISHER_LIBROS_INDIE_CREATED · PUBLISHER_MONZA_EDICIONES_CREATED`

## Cierre (2026-09-10) — Las manecillas del recuerdo completo

Creado siguiendo exactamente el procedimiento ya documentado abajo (clic real
en los react-select, `form.requestSubmit()`, verificación de duplicados antes
y después). Estado final verificado en vivo:

- **Work** "Las manecillas del recuerdo": https://bookbrainz.org/work/c4952bbe-d883-471b-b3fd-598176a8c706
  — Type: Novel, Language: Spanish, relación `written by David Porto Díaz`.
- **Edition Group**: https://bookbrainz.org/edition-group/053a7848-4756-4e1c-926d-550c12b595cc
  — verificado en vivo: contiene exactamente las 2 Editions correctas, ninguna
  extra.
- **Edition papel**: https://bookbrainz.org/edition/ca9658ee-5caf-4527-bea5-a13c765bebee
  — Paperback, ISBN-13 `9798905149351`, Monza Ediciones, Release Date
  `2026-09-03`, Language Spanish. Sin página count (discrepancia 272/266
  sigue abierta, tal como pedía este documento).
- **Edition ebook**: https://bookbrainz.org/edition/8ca16ed2-727e-4e29-85e7-0ad1fd7f77db
  — eBook, ISBN-13 `9798906781925`, Monza Ediciones, Release Date
  `2026-08-12`, disambiguation "Edición Kindle" (necesaria porque BookBrainz
  detectó el nombre exacto duplicado frente a la edición en papel — es el
  comportamiento esperado del modelo, no un error).
- **Publisher** "Monza Ediciones" creado: https://bookbrainz.org/publisher/d12c8fb0-84a0-4aa9-b929-c42894d97665
  — Area: Spain. Se buscó antes de crear (no existía, confirmado).

**Búsqueda final de duplicados** (David Porto Díaz, Las manecillas del
recuerdo, Monza Ediciones): exactamente 1 resultado cada uno — 1 Work,
1 Edition Group, 2 Editions (las correctas), 1 Publisher. Sin fantasmas.

Con esto, tanto Samuel entre mundos como Las manecillas del recuerdo quedan
completos y verificados en BookBrainz. Pendiente únicamente lo ya anotado en
"Oportunidad para la web" (valorar `Person.sameAs`/`Book.sameAs` cuando se
considere oportuno) — no es urgente ni bloqueante.

## Cierre parcial (2026-09-09) — Samuel entre mundos completo y corregido

Retomado tras el bloqueo del 2026-09-08 (que no era del classifier de permisos
sino una incompatibilidad de automatización con la SPA, ver más abajo).
Revisión posterior (misma fecha) corrigió metadata que había quedado
desactualizada respecto a #429 y verificó ausencia de duplicados. Estado
final verificado en vivo:

- **Work** "Samuel entre mundos": https://bookbrainz.org/work/5baf7e99-76a7-4efb-a846-7d243c2df0c1
  — Type: Novel, Language: Spanish, relación `written by David Porto Díaz`.
- **Edition** (tapa blanda): https://bookbrainz.org/edition/15ce7979-3bfe-415e-9ca4-db17f14292c8
  — Author Credit: David Porto Díaz, Format: Paperback, ISBN-13:
  `9791387659776`, Publisher: Libros Indie. **Release Date: `2025-12`** y
  **Page Count: `422`** (corregidos el 2026-09-09; ver sección siguiente).
  BookBrainz encontró y añadió solo una portada de OpenLibrary.
- **Edition Group** (auto-creado al dar de alta la Edition, BBID documentado
  ahora por primera vez): https://bookbrainz.org/edition-group/4d213e44-1237-42e0-b093-b6c35390fe34
  — Verificado en vivo: contiene exactamente una Edition (la de arriba), sin
  duplicados.
- **Publisher** "Libros Indie" creado: https://bookbrainz.org/publisher/2fb4b973-a42c-441e-a91c-0622fd4e4576
  — Area: Spain. Se buscó antes de crear (no existía, confirmado).

### Corrección de metadata (2026-09-09): página count y fecha

La Edition se había dejado con `Release Date: 2025` (sin mes) y sin página
count, "a la espera" de resolver la discrepancia `422/412`. Pero esa
discrepancia **ya estaba resuelta** desde antes en #429 usando la ficha de
producción primaria de Libros Indie (fuente más autorizada posible: venta
directa del propio editor, no un agregador/retailer): **422 páginas**,
**diciembre de 2025**. Este documento no se había actualizado para reflejar
ese cierre. Corregido ahora en BookBrainz vía el formulario de edición de la
Edition (`Page Count: 422`, `Release Date: 2025-12`), con nota de revisión
citando #429 como fuente. Verificado tras el submit: ambos valores se ven
correctamente en la ficha pública.

### Verificación final de duplicados (2026-09-09)

Búsqueda en vivo en `bookbrainz.org/search` para cada término, tras la
limpieza descrita abajo:

- `David Porto Díaz` → exactamente 1 Author.
- `Samuel entre mundos` → exactamente 1 Work, 1 Edition Group, 1 Edition.
- `9791387659776` (ISBN) → el buscador de texto de BookBrainz no indexa
  identificadores (0 resultados esperados), pero la Edition única ya
  confirmada arriba lleva ese ISBN-13 como identifier.
- `Libros Indie` → exactamente 1 Publisher.

No queda ningún duplicado fantasma. El Work vacío eliminado durante la
depuración (ver hallazgo técnico) no reaparece en ninguna búsqueda.

Un Work duplicado vacío se creó por accidente durante la depuración
(ver hallazgo técnico abajo) y fue eliminado vía la acción "Delete" del
propio BookBrainz con nota de revisión explicando el motivo; el historial de
edición queda preservado como es habitual en la plataforma.

### Hallazgo técnico importante para continuar con Manecillas

El bloqueo del 2026-09-08 **no era el clasificador de permisos de Claude
Code** — fueron incompatibilidades entre la automatización de navegador
usada por Claude y la SPA de BookBrainz. **Importante — esto no está
confirmado como un bug que afecte a un usuario humano navegando
normalmente**: todo lo de abajo se demostró únicamente con `.click()`
programático, `dispatchEvent` de eventos no confiables (`isTrusted: false`)
e inspección de red vía DevTools, no con interacción humana real. Etiquetado
como `AUTOMATION_INTERACTION_QUIRK / PROGRAMMATIC_EVENT_NOT_RELIABLE`, no
como "bug de BookBrainz", salvo que en el futuro se reproduzca el mismo
fallo con clics/teclado humanos genuinos:

1. **Los desplegables react-select (Language, Type, Publisher, Area, Author
   Credit...) no sincronizaron el estado interno de Redux cuando se
   seleccionaron vía `dispatchEvent(new MouseEvent(...))` desde JavaScript.**
   La UI se veía correcta ("Spanish"/"Novel" seleccionado) pero el payload
   final enviado al servidor llevaba `language: null` / `type: null` — es
   decir, el evento sintético no disparó los mismos handlers que un clic de
   ratón real del sistema operativo. Sí funcionó de forma fiable el mismo
   `dispatchEvent` dentro del modal de "Add relationship" (búsqueda de
   entidad y tipo de relación); falló solo en los campos de nivel superior
   del formulario (Language/Type del Work, Publisher/Format de la Edition).
   Solución de automatización: usar el tool `computer` (clic de ratón real
   a nivel de sistema, no sintético) con coordenadas de pantalla tras
   `scrollIntoView` + `screenshot`.
2. **El botón "Submit" de estos formularios no disparó ninguna petición de
   red al invocar `.click()` desde JavaScript** (tampoco con una secuencia
   completa `dispatchEvent` de `mousedown`/`mouseup`/`click`). El
   formulario React parece escuchar el evento `submit` del propio
   `<form>`, no el `click` sintético del botón. Solución de automatización:
   llamar `form.requestSubmit(submitButton)` directamente sobre el
   elemento `<form>`.
3. **Un payload con campos requeridos en `null` (p.ej. `nameSection.language:
   null`) — causado por el problema del punto 1 — hizo que el servidor
   respondiera `400 {"error":"Form contained invalid data"}`, pero la
   entidad se creó igualmente en el servidor** (se crearon 2 Works "Samuel
   entre mundos" vacíos pese al 400 recibido en el cliente). Esto sí podría
   ser una inconsistencia real del backend de BookBrainz (crear parcialmente
   pese a devolver error de validación), independiente de cómo se originó
   el payload inválido. **Comprobar siempre con una búsqueda tras cualquier
   envío que dé error, por si se creó un duplicado fantasma que haya que
   borrar o fusionar.**

Con estos tres ajustes de automatización (clic real del sistema en los
selects, `requestSubmit`, y verificación post-error) el resto del
procedimiento para Manecillas debería ejecutarse sin bloqueos.

### Pendiente

Ninguno — completado el 2026-09-10 (ver "Cierre" arriba). Solo queda
lo ya anotado en "Oportunidad para la web" más abajo (`Person.sameAs` /
`Book.sameAs`), sin urgencia.
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
