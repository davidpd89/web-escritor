# Inventaire.io — grafo bibliográfico abierto conectado con Wikidata

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · WORK_EDITION_MODEL_CONFIRMED · WIKIDATA_INTEROP_CONFIRMED · READY_FOR_EXECUTION`

## Objetivo

Revisar y, cuando falten, crear gratuitamente las entidades de David Porto Díaz, `Samuel entre mundos` y `Las manecillas del recuerdo` en Inventaire.io, aprovechando su integración con Wikidata y su modelo separado de obra/edición.

## Por qué merece la pena

Inventaire no es una tienda ni un perfil promocional. Su valor está en datos bibliográficos abiertos y conectados.

La documentación vigente confirma que:

- sus convenciones siguen de cerca WikiProject Books de Wikidata;
- distingue **obra** y **edición**;
- un ISBN pertenece al nivel de **edición**, no al de obra;
- el autor se asocia a la obra, no directamente a la edición;
- cada edición real con publisher/paginación/contenido distintos debe tener su propia entidad;
- reimpresiones idénticas no necesitan otra entidad;
- dispone de herramientas de deduplicación para autores/obras;
- las entidades Wikidata pueden convivir con entidades locales `inv:`.

Fuente principal actual:

- https://wiki.inventaire.io/wiki/Guides/fr
- https://wiki.inventaire.io/wiki/Roles_and_access_levels

Esto encaja muy bien con la estrategia de #398 Wikidata, #402 Open Library y #453 BookBrainz.

## Datos canónicos preparados

### Autor

- David Porto Díaz
- web: https://davidportodiaz.com/
- Wikidata: `Q139678851`
- ORCID: `0009-0005-9089-3782`

### Samuel entre mundos

**Work**
- título: Samuel entre mundos
- autor: David Porto Díaz

**Edition**
- ISBN `9791387659776`
- publisher: Libros Indie
- año: 2025
- formato: tapa blanda

No fijar páginas hasta resolver la discrepancia `422/412`.

### Las manecillas del recuerdo

**Work**
- título: Las manecillas del recuerdo
- autor: David Porto Díaz

**Edition papel**
- ISBN `9798905149351`
- publisher: Monza Ediciones
- publicación: 2026-09-03
- formato: tapa blanda

**Edition ebook**
- ISBN `9798906781925`
- publisher: Monza Ediciones
- publicación: 2026-08-12
- formato: ebook

No fijar páginas hasta resolver `272/266`.

## Regla de interoperabilidad con Wikidata

Antes de crear una entidad local `inv:` para autor u obra:

1. comprobar si ya existe entidad Wikidata equivalente;
2. comprobar si Inventaire ya la importa/reconoce;
3. evitar crear duplicado local cuando una entidad Wikidata correcta ya cubre el concepto;
4. si Wikidata está mal modelado, corregir primero en #398 y refrescar Inventaire cuando sea el flujo adecuado.

La documentación de Inventaire indica que algunos cambios de tipo obra/edición en entidades Wikidata deben hacerse en Wikidata y luego refrescarse en Inventaire.

## Procedimiento para Claude

### 1. Buscar antes de crear

Buscar:

- David Porto Díaz
- Samuel entre mundos
- Las manecillas del recuerdo
- los tres ISBN
- Wikidata `Q139678851`

Registrar URLs/IDs encontrados.

### 2. Autor

Si Inventaire ya muestra a David a través de Wikidata:

- verificar nombre;
- revisar obras vinculadas;
- comprobar posibles homónimos/duplicados locales.

Si no aparece, determinar primero si falta por sincronización con Wikidata o si procede crear una entidad local.

### 3. Obras

Cada novela debe tener una obra única.

No crear dos Works de Manecillas por tener papel/ebook.

### 4. Ediciones

Crear/revisar cada edición por separado:

- ISBN correcto;
- publisher;
- fecha;
- formato;
- idioma;
- título/subtítulo si procede;
- portada exacta;
- `edition of`/relación con la Work correcta.

La guía confirma que ISBN no debe ponerse en la Work.

### 5. Portadas

Inventaire acepta portadas de ediciones y recomienda reemplazar placeholders erróneos por la cubierta real.

Usar la portada editorial final correspondiente a cada edición, no mockups promocionales.

### 6. Duplicados

Usar las herramientas de deduplicación disponibles en páginas de autor/obra.

No crear una tercera entidad si ya hay:

- `wd:` + `inv:` duplicados;
- dos Works equivalentes;
- dos Editions con el mismo ISBN sin razón bibliográfica real.

### 7. Publishers

Verificar:

- Libros Indie
- Monza Ediciones

No crear publishers duplicados por mayúsculas, abreviaturas o pequeñas variantes.

## Qué NO hacer

- no usar la ficha como publicidad;
- no meter sinopsis promocional si no corresponde al modelo;
- no usar ISBN en Work;
- no asociar autor directamente a Edition si la UI/modelo lo impide;
- no copiar page count conflictivo todavía;
- no crear duplicados para obtener más URLs;
- no interpretar Inventaire como fuente primaria frente a ISBN/DILVE/editorial.

## Posible cambio en la web

Cuando las entidades sean públicas y estables:

- valorar la entidad de autor como `Person.sameAs`;
- valorar Works/editions como `Book.sameAs` cuando la semántica sea correcta.

No añadir URLs de búsqueda ni entidades duplicadas/inestables.

## Prioridad

`P1/P2`.

Tiene más valor que un directorio genérico porque es un grafo bibliográfico abierto y coordinable con Wikidata, pero debe ejecutarse después de que #398 deje clara la modelización principal.

## Criterio de cierre

`AUTHOR_ENTITY_VERIFIED · WIKIDATA_LINK_CONFIRMED · SAMUEL_WORK_EDITION_VERIFIED · MANECILLAS_WORK_VERIFIED · PAPER_EBOOK_EDITIONS_VERIFIED · PUBLISHERS_VERIFIED · DUPLICATES_REVIEWED · PUBLIC_URLS_RECORDED · SITE_GRAPH_UPDATED_IF_APPLICABLE`
