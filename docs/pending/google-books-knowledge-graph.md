# Google Books + Knowledge Graph — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#405 · `tracking/google-books-knowledge-graph`**  
Estado: **RESEARCHED · PUBLIC_GOOGLE_BOOKS_RECORD_NOT_OBSERVED · KNOWLEDGE_PANEL_NOT_VERIFIED · EXTERNAL_ACTION_PENDING**

## Objetivo

Conseguir que Google represente de forma coherente a **David Porto Díaz** y sus obras en Google Books / Google Play Books y, si existe un panel de conocimiento elegible, dejar preparada su reclamación/corrección sin crear fichas duplicadas ni atribuir al autor permisos que correspondan a la editorial/distribuidor.

Esta PR separa tres superficies que no deben confundirse:

1. **Google Books**: catálogo/buscador bibliográfico y previews.
2. **Google Play Books Partner Center**: panel de publisher/partner para cargar y mantener libros/metadatos cuando se tienen derechos/control.
3. **Knowledge Graph / Knowledge Panel de Google Search**: entidad generada automáticamente a partir de múltiples fuentes web; no existe un botón para “crear” manualmente un panel.

## Estado factual canónico a 2026-09-07

### Autor

- Nombre canónico: **David Porto Díaz**.
- Web oficial: **https://davidportodiaz.com/**.
- Autor publicado de `Samuel entre mundos` y `Las manecillas del recuerdo`.
- Nacido en Pontevedra y residente en Madrid, según la web oficial actual.

### Obras / ediciones que hay que buscar por identificador

| Obra / formato | Editorial | Identificadores | Estado editorial canónico |
|---|---|---|---|
| `Samuel entre mundos` · tapa blanda | Libros Indie | ISBN `9791387659776`; ASIN usado por la web `B0GB6LGQFH` | Publicada en 2025; 422 páginas |
| `Las manecillas del recuerdo` · Kindle | Monza Ediciones | ISBN `9798906781925`; ASIN `B0HHM71F46` | Publicada 2026-08-12 |
| `Las manecillas del recuerdo` · tapa blanda | Monza Ediciones | ISBN `9798905149351`; ASIN `B0HHY9MYLM` | Publicada 2026-09-03; 272 páginas |

No fijar en esta PR como hechos estables precios, stock, ranking, reseñas ni disponibilidad geográfica: son datos volátiles.

## Resultado de búsqueda pública de hoy

El 2026-09-07 se han realizado búsquedas web públicas por:

- `David Porto Díaz` + Google Books;
- `Samuel entre mundos` + `9791387659776`;
- `Las manecillas del recuerdo` + `9798906781925`;
- `Las manecillas del recuerdo` + `9798905149351`.

No se ha obtenido mediante estas búsquedas una ficha inequívoca de `books.google.com` para ninguna de las ediciones anteriores.

Esto se clasifica como:

`PUBLIC_GOOGLE_BOOKS_RECORD_NOT_OBSERVED_WITH_CURRENT_SEARCH`

**No significa `ABSENT_FROM_GOOGLE_BOOKS`.** Un resultado no visible en el buscador web puede existir en el catálogo/Partner Center, estar pendiente de indexación, estar suministrado por un distribuidor o aparecer bajo una edición/identificador diferente. Claude debe comprobarlo directamente en Google Books y, si existe acceso autorizado, en Partner Center antes de crear nada.

## Qué permite Google Play Books Partner Center actualmente

La ayuda oficial de Google consultada el 2026-09-07 confirma que el Partner Center permite editar metadatos bibliográficos de libros que pertenecen a la cuenta/partner. Entre los campos disponibles figuran:

- título/subtítulo;
- descripción;
- idioma;
- publisher/editorial;
- fecha de publicación y fecha de salida;
- formato;
- número de páginas;
- géneros;
- autores/contribuidores;
- serie;
- rangos de edad;
- identificador ISBN/EAN o GGKEY cuando no existe ISBN.

Google indica que **título, género e identificador (por ejemplo ISBN) son datos fundamentales** y recomienda completar tantos metadatos como sea posible porque ayudan al descubrimiento.

Fuente primaria:

- https://support.google.com/books/partner/answer/3237055
- https://support.google.com/books/partner/answer/9261664
- https://support.google.com/books/partner/answer/4491716

### Regla crítica: ONIX puede sobrescribir el Partner Center

Google advierte expresamente que, para partners que envían datos mediante **ONIX**, los cambios manuales realizados en Partner Center deben realizarse también en el feed ONIX; de lo contrario, una futura ingestión puede sobrescribirlos.

Consecuencia para este proyecto:

- si Libros Indie/Monza/distribuidor es quien alimenta Google mediante ONIX, la corrección canónica debe ocurrir en el owner editorial/ONIX;
- no “arreglar” un dato únicamente en Google si el feed fuente seguirá reenviando el valor incorrecto.

Google también muestra campos bloqueados cuando considera que un valor no debe editarse directamente; en esos casos su propia ayuda indica contactar con soporte.

## Derechos/ownership — no crear libros por inercia

### Samuel

`Samuel entre mundos` está publicado por **Libros Indie**. Antes de añadir el ISBN a un Partner Center propio de David hay que comprobar quién controla actualmente su distribución digital/bibliográfica y qué derechos existen.

### Manecillas

`Las manecillas del recuerdo` está publicado por **Monza Ediciones**. No asumir que David puede cargar o editar estas ediciones desde una cuenta propia de Google Play Books.

Si Google Books muestra metadatos incorrectos:

1. identificar de qué edición/ISBN se trata;
2. averiguar si la fuente es Monza, Libros Indie, distribuidor, ONIX/metadata feed o una cuenta Partner Center autorizada;
3. corregir en el owner real;
4. usar soporte de Google cuando proceda;
5. verificar después la ficha pública.

**No crear un libro nuevo/GGKEY para “corregir” una edición que ya tiene ISBN.** Eso puede generar otro registro y fragmentar la entidad bibliográfica.

## Procedimiento exacto para Claude — Google Books

### Fase 1 · búsqueda pública

Buscar primero por identificador exacto:

1. `9791387659776`
2. `9798906781925`
3. `9798905149351`

Después por:

- `"Samuel entre mundos" "David Porto Díaz"`
- `"Las manecillas del recuerdo" "David Porto Díaz"`

Para cada resultado real guardar:

- URL Google Books;
- Google Books ID si aparece;
- título exacto;
- autor/contribuidor;
- editorial;
- ISBN/identificador;
- idioma;
- formato;
- fecha;
- páginas;
- portada;
- descripción;
- preview/no preview;
- enlaces de venta que Google muestre;
- si parece registro independiente o una edición relacionada con otra.

### Fase 2 · detectar problemas

Clasificar cada diferencia:

- `CORRECT`
- `MINOR_DISPLAY_VARIATION`
- `WRONG_METADATA`
- `WRONG_AUTHOR_ASSOCIATION`
- `DUPLICATE_EDITION`
- `MISSING_EDITION`
- `SOURCE_OWNER_UNKNOWN`
- `NOT_OBSERVED`

No tratar papel y Kindle de Manecillas como “duplicados”: son **ediciones/formats distintos**. Un duplicado es repetir la misma edición/identificador.

### Fase 3 · ownership

Si existe acceso autorizado a Partner Center:

- comprobar qué libros aparecen realmente en la cuenta;
- no añadir ninguno hasta confirmar derechos/control;
- identificar si los metadatos provienen de edición manual, spreadsheet u ONIX;
- anotar partner/account owner sin guardar IDs sensibles, tokens ni datos bancarios en Git.

Si no existe acceso/control:

- crear una lista exacta de correcciones para la editorial/distribuidor;
- incluir ISBN, URL, campo incorrecto, valor actual y valor canónico;
- marcar `EXTERNAL_DEPENDENCY_RECORDED`.

## Knowledge Graph / Knowledge Panel

La ayuda oficial de Google consultada hoy confirma que los paneles de conocimiento:

- se generan **automáticamente**;
- combinan información obtenida de distintas fuentes web y partners;
- pueden actualizarse automáticamente al cambiar las fuentes;
- permiten a una persona/entidad representada reclamar su panel **solo si el panel existe y Google ofrece la opción**.

Fuente primaria:

- https://support.google.com/knowledgepanel/answer/9163198?hl=es

### No existe un flujo para “crear un Knowledge Panel” a mano

No abrir una tarea que diga “crear panel de David”.

Procedimiento correcto:

1. buscar `David Porto Díaz` en Google con sesión limpia/incógnito y en móvil/escritorio;
2. comprobar si aparece un panel claramente asociado a este autor;
3. si no aparece: registrar `KNOWLEDGE_PANEL_NOT_OBSERVED`, sin inventar un claim;
4. si aparece: revisar nombre, descripción, foto, profesión/ocupación, obras y enlaces;
5. comprobar si aparece `Registrarse como responsable de este panel de información` / `Claim this knowledge panel`;
6. si procede, verificar identidad únicamente por las vías oficiales de Google.

Google indica actualmente que la verificación puede apoyarse en propiedades/perfiles oficiales asociados como:

- Search Console;
- YouTube;
- Twitter/X;
- Facebook.

Fuente primaria:

- https://support.google.com/knowledgepanel/answer/7534902?hl=es

Tras la verificación, la entidad puede **sugerir cambios**. No presentar esto como edición directa garantizada del Knowledge Graph.

## Coherencia de entidad que sí podemos preparar desde la web

Antes de pedir cualquier corrección a Google, verificar consistencia entre:

- nombre `David Porto Díaz`;
- web `https://davidportodiaz.com/`;
- página de autor;
- Amazon Author Central;
- Goodreads;
- Wikidata, si el item es válido y correctamente referenciado;
- ORCID, si existe y realmente corresponde al autor;
- publisher pages (Libros Indie / Monza);
- perfiles sociales oficiales.

No añadir `sameAs` en la web únicamente porque una plataforma tenga una página parecida: primero confirmar que la entidad es realmente de David y es el perfil canónico.

## Datos que NO deben forzarse para “ayudar al Knowledge Graph”

- No crear Wikidata/Google Books duplicados.
- No crear perfiles ficticios en plataformas externas para aumentar el número de `sameAs`.
- No inventar profesión, premios, fecha de nacimiento completa u otros datos personales no publicados de forma legítima.
- No añadir reseñas/rankings como hechos estructurados.
- No cambiar el schema de la web solo porque un panel aún no aparezca.
- No prometer que una modificación en Wikidata/Google Books producirá un Knowledge Panel: Google no documenta esa causalidad como garantía.

## Checklist de ejecución

### Google Books

- [ ] Buscar los 3 ISBN exactos directamente en Google Books.
- [ ] Buscar ambos títulos + autor.
- [ ] Registrar todas las fichas/IDs encontradas.
- [ ] Comparar metadatos contra autoridad canónica.
- [ ] Determinar owner de cada registro/feed.
- [ ] Corregir solo mediante owner autorizado o soporte.
- [ ] Verificar que no se cree ningún duplicado.
- [ ] Volver a comprobar ficha pública tras propagación.

### Knowledge Panel

- [ ] Buscar autor en Google desktop incógnito.
- [ ] Buscar autor en móvil.
- [ ] Registrar panel `OBSERVED` / `NOT_OBSERVED`.
- [ ] Si existe, comprobar entidad y fuentes/enlaces.
- [ ] Si procede, solicitar claim con cuenta autorizada.
- [ ] Guardar evidencia del resultado de verificación.
- [ ] Sugerir únicamente correcciones factuales sustentadas.
- [ ] Revalidar públicamente tras propagación.

## Evidencia mínima para cerrar

Guardar en la PR, sin secretos:

- fecha/hora de comprobación;
- consultas/ISBN usados;
- URLs de fichas Google Books encontradas;
- Google Books IDs, si existen;
- capturas de errores relevantes;
- owner de la corrección: David / Libros Indie / Monza / distribuidor / Google Support;
- estado del Knowledge Panel: `NOT_OBSERVED`, `OBSERVED_UNCLAIMED`, `CLAIM_PENDING`, `CLAIMED`;
- lista de cambios solicitados y resultado;
- QA público final.

## Criterio de cierre

La PR solo puede cerrarse con uno de estos estados explícitos:

### Caso ideal

`GOOGLE_BOOKS_EDITION_RECORDS_VERIFIED · METADATA_COHERENT · NO_RELEVANT_DUPLICATES · KNOWLEDGE_PANEL_VERIFIED_OR_NOT_OBSERVED · PUBLIC_QA_DONE`

### Dependencia editorial

`GOOGLE_BOOKS_ISSUES_DOCUMENTED · EXTERNAL_PUBLISHER_OR_DISTRIBUTOR_DEPENDENCY_RECORDED · NO_DUPLICATE_CREATED · KNOWLEDGE_PANEL_STATUS_VERIFIED`

### Sin registros observables

`GOOGLE_BOOKS_RECORDS_NOT_OBSERVED_AFTER_DIRECT_CHECK · NO_UNAUTHORIZED_UPLOAD · KNOWLEDGE_PANEL_STATUS_VERIFIED`

No usar `COMPLETE` únicamente porque el buscador web no devuelva resultados.

## Fuentes primarias consultadas · 2026-09-07

Google Play Books / Google Books:

- https://support.google.com/books/partner/answer/3237055 — Book metadata & information.
- https://support.google.com/books/partner/answer/9261664 — Quickstart guide to add a new book.
- https://support.google.com/books/partner/answer/4491716 — bibliographic information / ISBN.
- https://support.google.com/books/partner/ — Partner Center Help.

Knowledge Graph / Knowledge Panel:

- https://support.google.com/knowledgepanel/answer/9163198?hl=es — cómo se generan los paneles.
- https://support.google.com/knowledgepanel/answer/7534902?hl=es — verificación/reclamación.

Autoridad factual propia:

- https://davidportodiaz.com/
- https://davidportodiaz.com/libros/samuel-entre-mundos/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/

Última regla: **mejor un `NOT_OBSERVED` honesto que crear un registro externo duplicado para poder marcar el checklist como hecho.**
