# VIAF — autoridad de David Porto Díaz

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · SOURCE_AUTHORITY_MODEL_CONFIRMED · READY_FOR_DIRECT_AUDIT`

## Objetivo

Comprobar si David Porto Díaz tiene un cluster VIAF inequívoco, qué archivos de autoridad lo alimentan, si existen duplicados o atribuciones erróneas y cómo corregirlos en la fuente correcta.

VIAF no es un perfil social editable por el autor. OCLC agrupa registros de autoridad enviados por bibliotecas nacionales y otros contribuidores y recibe actualizaciones periódicas de esas fuentes. Por eso, cuando el dato erróneo nace en BNE/u otra autoridad participante, la corrección estable debe hacerse allí y después propagarse al cluster VIAF.

Fuentes oficiales:
- https://www.oclc.org/en/viaf.html
- https://www.oclc.org/en/viaf/contributing.html
- https://www.oclc.org/developer/api/oclc-apis/viaf.en.html

## Identidad canónica para desambiguar

- Nombre: David Porto Díaz
- Web: https://davidportodiaz.com/
- Wikidata: Q139678851
- ORCID: 0009-0005-9089-3782
- Amazon Author: B0GZFP1JV3
- Goodreads Author: 66843136
- Samuel entre mundos: ISBN 9791387659776
- Las manecillas del recuerdo, papel: ISBN 9798905149351
- Las manecillas del recuerdo, ebook: ISBN 9798906781925

## Procedimiento para Claude

1. Buscar `David Porto Díaz`, `Porto Díaz, David` y variantes razonables.
2. Repetir búsqueda combinando nombre con `Samuel entre mundos` y `Las manecillas del recuerdo`.
3. Si aparece un candidato, comprobar obras, fuentes participantes y source IDs antes de aceptarlo.
4. Guardar: VIAF ID, URL, forma preferida, variantes, fuentes participantes, source authority IDs y obras asociadas.
5. Buscar clusters duplicados o un cluster que mezcle a otra persona.
6. Si el error procede de una autoridad fuente, coordinar la corrección con #422 BNE, #421 ISNI o #419 WorldCat/OCLC según corresponda.
7. Volver a comprobar VIAF tras la siguiente actualización de la fuente.

## Posible cambio en la web

Solo cuando el cluster sea inequívoco:
- añadir URL VIAF a `Person.sameAs`;
- añadir el VIAF ID a Wikidata si procede y no existe ya;
- ejecutar QA de identidad/schema.

No añadir un resultado solo por coincidencia de nombre.

## Criterio de cierre

`VIAF_AUDITED · CLUSTER_CONFIRMED_OR_NOT_OBSERVED · SOURCE_AUTHORITIES_IDENTIFIED · DUPLICATES_REVIEWED · CORRECTION_OWNER_IDENTIFIED · SITE_GRAPH_UPDATED_IF_APPLICABLE`

## Audición directa (2026-09-08)

Búsqueda ejecutada directamente en viaf.org ("All Fields" → "David Porto
Díaz"): **"No headings found"** — confirmado, no existe registro VIAF hoy.
Esto es coherente con lo esperado: VIAF federa autoridades de bibliotecas
nacionales (BNE, Library of Congress, etc.), así que la vía de entrada
sigue siendo indirecta — normalmente aparece automáticamente una vez la
BNE/ISNI tramitan la autoridad del autor (ver #422 BNE, #421 ISNI), no
por una alta directa en viaf.org.
