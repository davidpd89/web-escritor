# Wikidata — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#398 · `tracking/wikidata`**  
Estado: **PHASE_1_2_3_AUDITED · PERSONAL_DATA_FLAG_FOR_AUTHOR_REVIEW · MANECILLAS_ITEM_NOT_YET_CREATED**

## Auditoría en vivo (2026-09-08, solo lectura — sin editar nada)

Fase 1 (inventario) y fase 2/3 (comparación autor/obras) completadas
abriendo directamente cada item público. **No se ha guardado ningún
cambio en Wikidata** — esto es una auditoría, no ejecución, a propósito:
crear/editar items es una acción sobre una wiki pública que este proyecto
ya trata con cautela (ver BookBrainz), y esta ronda concreta destapó algo
que de verdad necesita que lo mires tú antes de que nadie edite nada.

### ⚠️ Hallazgo que requiere tu atención: datos personales sin ninguna referencia

El item del autor (Q139678851) tiene en vivo, **hoy**, estas declaraciones
sin ni una sola fuente citada (`0 references`):

- **fecha de nacimiento: 31 de julio de 1989** (fecha completa y exacta)
- **educated at: Sacred Heart** (centro educativo concreto)
- sex or gender: male
- country of citizenship: Spain
- native language: Spanish

Esto no lo ha añadido esta sesión — ya estaba así al auditar. Pero es
exactamente lo que este mismo documento (sección 5) ya advertía que no
se debía hacer: *"no añadir fecha completa de nacimiento si no está
claramente publicada y respaldada"*. Una fecha de nacimiento exacta y un
centro educativo concreto, sin ninguna fuente, en un item público sobre
una persona viva, es un dato que **tú** deberías revisar: ¿es correcto?
¿lo quieres público con ese nivel de detalle? ¿hay una fuente real que
citar, o preferirías que se retirase o se dejara solo el año?

No se ha tocado nada de esto — es tu decisión, no la de Claude.

Lo que sí está bien en el autor: `official website`, ORCID (con
referencia), Goodreads author ID, Amazon author ID, `award received`
(Letras Como Espada, con referencia), occupation (writer/author). Falta
una etiqueta/descripción en español (solo existe en inglés) — un cambio
de bajo riesgo si algún día se quiere completar.

### Noveris (Q139927664)

Existe, pero la interfaz en inglés lo muestra sin etiqueta ni descripción
("No label defined" / "No description defined"); el buscador sí devuelve
una descripción en español ("Ciudad dimensional ficticia en la novela
Samuel entre mundos"), lo que sugiere que la etiqueta/descripción en
español existe pero la inglesa no — modelo de idiomas incompleto, no un
error grave. `instance of: fictional city`, `creator: David Porto Díaz`,
`present in work: Samuel entre mundos`, `official website` — todo
correcto, pero sin referencias.

### Samuel entre mundos — YA CREADO (2025 → hoy 2026-09-08)

Encontrados y auditados, ambos creados hoy mismo:

- **Work**: `Samuel entre mundos` — Q139915381
- **Edition**: `Samuel entre mundos (first edition)` — Q139945987

El modelo sigue correctamente el patrón work/edition de WikiProject
Books: `instance of: literary work` / `version, edition or translation`,
`author`, `publisher: Libros Indie`, `ISBN-13: 979-13-87659-77-6`,
`number of pages: 422`, género (`portal fantasy`, `young adult
literature`), fecha de publicación diciembre 2025, idioma español. Sin
etiqueta en español (solo inglés) en ninguno de los dos, y la mayoría de
declaraciones están sin referencia — mismo patrón que el autor.

### Las manecillas del recuerdo — NO CREADO todavía

Búsqueda directa por título: **sin resultados** — Wikidata ofrece
literalmente crear el item. No se ha creado nada esta noche: crear un
work + edition nuevos con el modelo exacto de la sección 4 de este
documento (evitando el mismo error de ISBN/páginas que Samuel, y
resolviendo antes si procede separar edición papel/Kindle) merece una
sesión dedicada, no un tramo final de una noche ya muy larga. El
procedimiento del documento original sigue siendo válido tal cual.

## Qué falta (fases 4-6 del documento original)

- Añadir etiquetas/descripciones en español al autor, a Noveris y a los
  dos items de Samuel.
- Decidir qué hacer con las declaraciones personales sin referencia del
  autor (ver hallazgo de arriba) — **esto primero, antes que nada más**.
- Crear el work (+ edition/s) de Las manecillas del recuerdo siguiendo el
  modelo de la sección 4.
- Añadir referencias a las declaraciones que hoy tienen `0 references`.
- Una vez estable, añadir el QID de Samuel a `Book.sameAs` en
  `libros/samuel-entre-mundos/index.html` (hoy no lo tiene).

## Objetivo

Dejar el grafo público de **David Porto Díaz**, `Samuel entre mundos`, `Las manecillas del recuerdo` y `Noveris` correctamente modelado en Wikidata, con referencias y external IDs verificables, sin crear elementos promocionales ni inventar notoriedad.

Esta PR es prioritaria no porque “Wikidata dé SEO” de forma directa, sino porque Wikidata es una fuente estructurada reutilizada por buscadores, bases de autoridad, proyectos Wikimedia y flujos de IA. En 2026 Wikidata documenta además una **base vectorial** para búsqueda semántica/RAG y un **servidor MCP oficial** pensado para que LLM y agentes consulten Wikidata. Por tanto, tener una entidad correcta puede ayudar a la consistencia de identidad máquina↔autor↔obra, aunque no se debe prometer ninguna mejora de ranking.

Fuentes oficiales:

- `https://www.wikidata.org/wiki/Wikidata:Data_access/es`
- `https://www.wikidata.org/wiki/Wikidata:MCP`
- `https://www.wikidata.org/wiki/Wikidata:Vector_Database`

## 1. Entidades ya conocidas

### Autor

- Item conocido: **Q139678851**
- URL: `https://www.wikidata.org/wiki/Q139678851`
- Nombre canónico: **David Porto Díaz**
- Web oficial: `https://davidportodiaz.com/`
- ORCID: `0009-0005-9089-3782`
- Goodreads Author ID: `66843136`
- Amazon author ID: `B0GZFP1JV3`

### Noveris

- Item conocido: **Q139927664**
- URL: `https://www.wikidata.org/wiki/Q139927664`

No crear duplicados de estos dos items. La primera acción de Claude será abrirlos y auditar las declaraciones existentes.

### Samuel entre mundos

No tenemos todavía un QID canónico confirmado en el proyecto.

Datos preparados:

- título: **Samuel entre mundos**
- autor: David Porto Díaz
- editorial: **Libros Indie**
- idioma: español
- edición papel: ISBN-13 `9791387659776`
- páginas: 422
- fecha de la edición actual: `2025-12-17` según la ficha pública de Goodreads / alta bibliográfica usada por el proyecto
- Goodreads: `https://www.goodreads.com/book/show/245605636-samuel-entre-mundos`
- Amazon ASIN: `B0GB6LGQFH`
- Casa del Libro: `https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776`
- Open Library: `https://openlibrary.org/isbn/9791387659776`
- LibraryThing work: `https://www.librarything.com/work/36438284/t/Samuel-entre-mundos`
- Qué Libro Leo: `https://quelibroleo.com/samuel-entre-mundos`
- ISFDB title: `https://www.isfdb.org/cgi-bin/title.cgi?3117406`

### Las manecillas del recuerdo

No tenemos todavía un QID canónico confirmado en el proyecto.

Datos preparados del **work**:

- título: **Las manecillas del recuerdo**
- autor: David Porto Díaz
- idioma: español

Edición papel:

- editorial: **Monza Ediciones**
- ISBN-13: `9798905149351`
- ISBN presentado: `979-8-90514-935-1`
- ASIN: `B0HHY9MYLM`
- publicación: `2026-09-03`
- páginas: `272`
- formato: tapa blanda
- URL Amazon: `https://www.amazon.es/dp/B0HHY9MYLM`

Edición Kindle:

- editorial: **Monza Ediciones**
- ISBN-13: `9798906781925`
- ASIN: `B0HHM71F46`
- publicación: `2026-08-12`
- formato: ebook / Kindle
- URL Amazon: `https://www.amazon.es/dp/B0HHM71F46`

No asignar las 272 páginas de papel a Kindle por copia automática.

## 2. Regla de notoriedad: no crear items solo porque nos interese SEO

La política actual de Wikidata exige que un item cumpla al menos uno de estos criterios:

1. tener un sitelink Wikimedia válido; o
2. representar una entidad claramente identificable que pueda describirse con referencias serias y públicas; o
3. cumplir una necesidad estructural real del grafo.

Además, la propia ayuda de Wikidata dice expresamente que no se creen items con fines promocionales.

Fuentes oficiales:

- `https://www.wikidata.org/wiki/Wikidata:Notability`
- `https://www.wikidata.org/wiki/Help:Items`

Aplicación a este proyecto:

- **Q139678851** y **Q139927664** ya existen → auditar/corregir, no recrear.
- Para Samuel y Manecillas → primero buscar por título/ISBN/QID; si no existen, valorar creación únicamente si las referencias públicas y/o la necesidad estructural son suficientes.
- No crear un item de cada edición si no hay una justificación bibliográfica real o si el work ni siquiera cumple el criterio de item.
- No usar el sitio del autor como única prueba de notoriedad.

## 3. Modelo bibliográfico correcto de Wikidata

WikiProject Books recomienda un modelo de **dos capas: work + edition**. También recomienda evitar usar simplemente `book (Q571)` cuando borra la diferencia entre obra y edición.

Fuentes oficiales:

- `https://www.wikidata.org/wiki/Wikidata:WikiProject_Books/es`
- `https://www.wikidata.org/wiki/Wikidata:WikiProject_Books/Book_data_model`
- `https://www.wikidata.org/wiki/Help:Sources/es`

### Work

Declaraciones base:

- `instance of (P31)` → `written work (Q47461344)` o una subclase más precisa y correcta;
- `author (P50)` → `David Porto Díaz (Q139678851)`;
- `title (P1476)` → título en español;
- `language of work or name (P407)` → español;
- opcional, solo si es fiable: `genre (P136)`, `main subject (P921)`.

No meter publisher, ISBN o número de páginas del papel como si fueran propiedades universales del work cuando pertenecen a una edición concreta.

### Edition

Para una edición diferenciada:

- `instance of (P31)` → `version, edition or translation (Q3331189)`;
- `edition or translation of (P629)` → QID del work;
- `title (P1476)`;
- `language of work or name (P407)`;
- `publisher (P123)` si el publisher tiene item válido; si no, no crear publisher artificialmente solo para rellenar el campo;
- `publication date (P577)`;
- `ISBN-13 (P212)`;
- `number of pages (P1104)` cuando corresponda;
- otros IDs bibliográficos únicamente si son exactos.

El work puede enlazar las ediciones con `has edition or translation (P747)` si procede.

## 4. Modelo recomendado para nuestras obras

### Samuel

Si no existe y supera notoriedad/estructura:

#### Work item

- label es: `Samuel entre mundos`
- description es: `novela de David Porto Díaz`
- P31 → written work
- P50 → Q139678851
- P1476 → `Samuel entre mundos` @es
- P407 → español
- genre únicamente si existe item preciso y fuente suficiente; no llenar diez géneros promocionales.

#### Paper edition

- label: `Samuel entre mundos (edición de 2025)` o equivalente diferenciable
- P31 → version, edition or translation
- P629 → work de Samuel
- P1476 → `Samuel entre mundos` @es
- P407 → español
- P123 → Libros Indie, **solo si existe/creamos legítimamente su item**
- P577 → 2025-12-17
- P212 → `979-13-87659-77-6` si Wikidata acepta la forma normalizada correspondiente al ISBN actual
- P1104 → 422 páginas

Comprobar el formato de ISBN que Wikidata normaliza antes de guardar; no inventar guionado.

### Manecillas

Si no existe y supera notoriedad/estructura:

#### Work item

- label es: `Las manecillas del recuerdo`
- description es: `novela de David Porto Díaz`
- P31 → written work
- P50 → Q139678851
- P1476 → `Las manecillas del recuerdo` @es
- P407 → español

#### Paper edition

- P31 → version, edition or translation
- P629 → work de Manecillas
- P1476 → título @es
- P407 → español
- P123 → Monza Ediciones, solo si existe un item correcto
- P577 → 2026-09-03
- P212 → `979-8-90514-935-1`
- P1104 → 272 páginas

#### Kindle edition

Solo crear item separado si la edición electrónica cumple el modelo y existe suficiente soporte bibliográfico/estructural:

- P31 → version, edition or translation
- P629 → work de Manecillas
- P1476 → título @es
- P407 → español
- P123 → Monza Ediciones, si item correcto
- P577 → 2026-08-12
- P212 → `979-8-90678-192-5` si esa es la normalización válida del ISBN `9798906781925`

No usar ASIN como sustituto de ISBN. Antes de añadir ASIN buscar si existe una propiedad Wikidata específica y confirmar su dominio; no inventar una propiedad.

## 5. Autor Q139678851 — matriz de auditoría

Claude debe comparar el item actual contra esta matriz.

### Declaraciones principales

- label es: **David Porto Díaz**
- description es: `escritor español` o una descripción neutral equivalente
- `instance of (P31)` → human
- `occupation (P106)` → writer/escritor, si está correctamente modelado
- `official website (P856)` → `https://davidportodiaz.com/`
- `ORCID iD (P496)` → `0009-0005-9089-3782`
- `Goodreads author ID (P2963)` → `66843136`
- `Amazon author ID (P4862)` → `B0GZFP1JV3`

Fuentes de propiedades verificadas:

- P856: `https://www.wikidata.org/wiki/Property:P856`
- P496: `https://www.wikidata.org/wiki/Property:P496`
- P2963: `https://www.wikidata.org/wiki/Property:P2963`
- P4862: `https://www.wikidata.org/wiki/Property:P4862`

### Biografía personal

No añadir datos personales no necesarios por completar casillas.

Especialmente:

- no añadir fecha completa de nacimiento si no está claramente publicada y respaldada;
- no añadir dirección;
- no añadir teléfono;
- no añadir datos privados de cuentas;
- si birth place/residence ya existen, verificar fuentes antes de tocar.

Para una persona viva, priorizar referencias públicas fiables y una edición conservadora.

## 6. Obras y autor

Una vez existan work items correctos y estables, valorar conectar desde el autor mediante las propiedades que el modelo actual de Wikidata considere correctas (por ejemplo, `notable work` solo si realmente procede).

No añadir “notable work” automáticamente a cada libro publicado. El dato debe tener sentido semántico y no ser autopromoción.

La relación esencial ya estará expresada desde cada work con `author (P50) → Q139678851`.

## 7. Premios y reconocimientos

El sitio oficial actualmente presenta:

- Primer Premio — XII Certamen de Microrrelatos «De amor» · Letras Como Espada (2026)
- Top 10 / finalista — I Premio de Literatura Infantil Juan Andrés Teno (2026)

No añadir `award received (P166)` a Q139678851 solo porque la web propia lo diga.

Procedimiento:

1. localizar fuente externa/organizadora fiable;
2. comprobar que el certamen/premio tiene o merece item;
3. modelar solo si la propiedad encaja exactamente con el resultado obtenido;
4. distinguir ganador vs finalista vs selección.

Si no hay fuente o item adecuado, dejarlo fuera de Wikidata. La web puede seguir mencionándolo con su propia evidencia.

## 8. Noveris Q139927664

Auditar:

- label/aliases;
- description neutral;
- instance of correcto;
- creator/author relationship con David si el modelo lo soporta y está referenciado;
- fictional universe/work relationship;
- no mezclar Noveris con una ciudad real;
- no introducir lore no verificable desde fuentes públicas.

Si el item existe únicamente por necesidad estructural, conservarlo minimalista y bien enlazado; no convertirlo en una ficha promocional del universo.

## 9. Referencias: jerarquía recomendada

### Tier A — preferidas para datos bibliográficos

- Agencia del ISBN / registros ISBN
- BNE
- WorldCat/OCLC
- DILVE o catálogos editoriales/distribución profesionales
- catálogo de biblioteca fiable
- ORCID para ORCID
- Goodreads/Amazon únicamente para sus propios external IDs o datos propios de la plataforma

### Tier B — buenas para identidad/biografía cuando proceda

- entrevistas/perfiles editoriales independientes
- prensa cultural fiable
- páginas de certámenes/organizadores
- editoriales para datos que ellas publican de sus propios libros

### Tier C — fuente propia

`davidportodiaz.com` sirve muy bien para:

- `official website (P856)`;
- enlaces oficiales;
- confirmar cómo se presenta el autor a sí mismo.

No usarla como única prueba de notoriedad ni como referencia única para afirmaciones controvertidas/promocionales.

Wikidata recomienda que la mayoría de declaraciones sean verificables mediante referencias serias y públicas:

- `https://www.wikidata.org/wiki/Help:Sources`
- `https://www.wikidata.org/wiki/Wikidata:Verifiability`

## 10. External IDs y autoridad

Los external identifiers son especialmente útiles porque conectan la entidad con bases independientes y facilitan deduplicación/machine matching.

En el autor, priorizar:

1. ORCID
2. Goodreads author ID
3. Amazon author ID
4. VIAF / ISNI / BNE **solo cuando #419–#422 los hayan verificado**

No prellenar IDs futuros a partir de búsquedas dudosas.

En libros/ediciones, priorizar:

- ISBN-13;
- Open Library/LibraryThing/Google Books/WorldCat/BNE IDs únicamente cuando la propiedad exacta y el registro estén verificados.

## 11. Por qué esto importa para IA

No escribir en Wikidata que se está editando “para SEO”. El motivo operativo interno sí es relevante:

Wikidata publica en 2026:

- una base vectorial para búsquedas semánticas y flujos RAG/ML;
- un MCP oficial para que LLM/agentes exploren y consulten Wikidata programáticamente.

Esto convierte una entidad bien modelada y deduplicada en una fuente potencial de contexto máquina más valiosa que añadir perfiles arbitrarios en webs pequeñas.

No garantiza que ChatGPT, Google AI, Bing/Copilot u otro sistema concreto use un item determinado ni que mejore rankings.

Fuente:

`https://www.wikidata.org/wiki/Wikidata:Data_access/es`

## 12. Estado del repo y cambios de código preparados

### Autor

`autor.html` ya contiene:

`https://www.wikidata.org/wiki/Q139678851`

en `Person.sameAs`.

También contiene ORCID, Amazon Author Central y Goodreads. Por tanto, **no hay cambio de código necesario para el autor mientras Q139678851 siga siendo el item correcto**.

### Samuel

La ficha de Samuel ya tiene varios `sameAs` bibliográficos, pero no un QID de Wikidata conocido.

Si Claude verifica/crea legítimamente un QID de work para Samuel:

1. añadir `https://www.wikidata.org/wiki/Q...` a `Book.sameAs` en `libros/samuel-entre-mundos/index.html`;
2. actualizar la fuente canónica/generador si existe;
3. no añadir el QID de una edition como si fuera el work sin documentar la elección.

### Manecillas

El nodo Book principal de `las-manecillas-del-recuerdo/index.html` no tiene todavía `sameAs` bibliográfico externo.

Si se verifica/crea legítimamente el **work QID** de Manecillas:

1. añadir su URL Wikidata al `sameAs` del nodo `https://davidportodiaz.com/#book-manecillas`;
2. si existen QIDs separados para papel/Kindle, enlazarlos solo en los nodos de edición correspondientes si el modelo Schema del sitio se ajusta, sin confundir work/edition;
3. incorporar también el Goodreads URL exacto cuando #397 lo haya confirmado;
4. ejecutar machine-authority, schema/content parity y release-readiness.

Hasta tener QID real: **NO INVENTAR `sameAs`**.

## 13. Procedimiento exacto para Claude

### Fase 1 — inventario

Abrir directamente:

- `https://www.wikidata.org/wiki/Q139678851`
- `https://www.wikidata.org/wiki/Q139927664`

Buscar además por:

- `Samuel entre mundos`
- `9791387659776`
- `Las manecillas del recuerdo`
- `9798905149351`
- `9798906781925`

Registrar cualquier QID existente antes de editar.

### Fase 2 — autor

Comparar Q139678851 con la matriz de sección 5.

Corregir únicamente:

- errores objetivos;
- identifiers ausentes ya verificados;
- web oficial;
- referencias faltantes donde aporten valor.

No “rellenar” propiedades sin necesidad.

### Fase 3 — books

Para cada obra:

1. determinar si existe work item;
2. determinar si existen edition items;
3. verificar notoriedad antes de crear algo;
4. seguir el modelo work/edition de WikiProject Books;
5. referenciar datos de edición con fuente bibliográfica adecuada.

### Fase 4 — duplicados

Si hay dos items para la misma entidad:

- no borrar ni fusionar a ciegas;
- comparar sitelinks, identifiers y statements;
- seguir `Help:Merge` si es un duplicado real;
- conservar el QID mejor conectado y trasladar statements válidos según política.

### Fase 5 — repo

Cuando los QID finales estén estables:

- parchear `sameAs` donde corresponda;
- actualizar fuentes canónicas del repo, no solo HTML generado;
- regenerar artefactos;
- ejecutar CI relevante.

### Fase 6 — verificación máquina

Después de guardar:

- abrir cada QID públicamente;
- comprobar etiquetas en español/inglés si se añadieron;
- comprobar external IDs;
- comprobar relaciones work↔edition↔author;
- comprobar que el sitio apunta al QID correcto;
- probar que la entidad puede consultarse en Wikidata sin depender de un alias ambiguo.

## 14. Qué NO hacer

- No crear un item solo para conseguir un backlink.
- No crear items duplicados.
- No usar `book (Q571)` por comodidad si el modelo work/edition exige otra cosa.
- No mezclar ISBN de edición con el work conceptual.
- No inventar publisher QIDs.
- No crear items de premios/editoriales solo para poder rellenar una propiedad.
- No añadir reseñas, ventas, rankings ni claims promocionales.
- No añadir datos privados de una persona viva.
- No citar exclusivamente la web del autor para demostrar notoriedad.
- No añadir links de afiliado como external IDs.

## 15. Evidencia de cierre que debe quedar en #398

- snapshot inicial de Q139678851;
- snapshot inicial de Q139927664;
- statements corregidos en el autor + referencias;
- Goodreads ID `66843136` confirmado/añadido;
- Amazon author ID `B0GZFP1JV3` confirmado/añadido;
- ORCID confirmado;
- QID final de Samuel o `NOT_CREATED_NOTABILITY_INSUFFICIENT`;
- QID final de Manecillas o `NOT_CREATED_NOTABILITY_INSUFFICIENT`;
- edition QIDs creados/verificados, si procede;
- duplicados revisados;
- cambios de repo y tests;
- cualquier dependencia de BNE/VIAF/ISNI/ISBN pendiente claramente enlazada a sus PRs.

## 16. Criterio de cierre

Caso completo:

`AUTHOR_QID_VERIFIED · AUTHOR_IDENTIFIERS_COHERENT · NOVERIS_QID_VERIFIED · BOOK_ITEMS_AUDITED · WORK_EDITION_MODEL_CORRECT · REFERENCES_ADDED_WHERE_NEEDED · DUPLICATES_REVIEWED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · MACHINE_GRAPH_QA_DONE`

Caso en que una obra no deba tener item:

`NOTABILITY_CHECKED · NO_PROMOTIONAL_ITEM_CREATED · AUTHOR_GRAPH_CLEAN · EXTERNAL_DEPENDENCY_RECORDED`

## Nota de acceso (2026-09-08, segunda ronda)

Se consideró crear directamente el work/edition de Las manecillas del
recuerdo copiando el patrón ya validado de Samuel (Q139915381 /
Q139945987). Antes de tocar nada se comprobó el estado de sesión en
wikidata.org: **no hay ninguna cuenta logueada** en esta sesión. Los
items existentes de Samuel fueron creados por una cuenta autenticada; 
crear el equivalente de Manecillas de forma anónima (por IP) sería
inconsistente con eso y, en la práctica, este tipo de contribución
sustancial y no vinculada a una cuenta tiende a recibir más escrutinio y
reversión en wikis colaborativas. Se ha dejado sin crear.

**Para completarlo hace falta iniciar sesión en Wikidata** con la cuenta
que ya se usó para crear los items de Samuel (o una nueva) antes de que
Claude continúe con la fase 3 de este documento.
