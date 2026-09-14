# VIAF — autoridad de David Porto Díaz

Fecha de revisión: 2026-09-07 (última reverificación en vivo: 2026-09-14)

Estado: `VIAF_AUDITED · NOT_OBSERVED_CONFIRMED_LIVE_TWICE · CORRECTION_OWNER_IS_BNE_421_422 · EXTERNAL_DEPENDENCY`

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

## Reverificación en vivo (2026-09-14)

Repetida la búsqueda directamente en viaf.org, una semana después y con
más cobertura que la primera vez:

- `David Porto Díaz` (orden nombre-apellido): **"No headings found"**.
- `Porto Díaz, David` (orden apellido-nombre): **"No headings found"**.
- ISBN `9791387659776` (Samuel entre mundos), campo "All Fields": **"No
  headings found"** — comprobación nueva, no se había buscado antes por
  ISBN directamente en viaf.org.

Mismo resultado que hace una semana, ahora con una tercera consulta
(ISBN) que tampoco encuentra nada. Esto confirma con más margen que no
existe cluster VIAF hoy, y sigue sin haber nada que corregir *en VIAF
mismo*: el bloqueador real es que #422 BNE ya confirmó por consulta
directa al catálogo que no hay registro bibliográfico ni de autoridad de
la BNE del que VIAF pudiera heredar un cluster. Sin autoridad fuente
(BNE u otra biblioteca participante), VIAF no tiene nada que agregar.

### Cierre de esta ronda

`VIAF_AUDITED · CLUSTER_NOT_OBSERVED_CONFIRMED_2026-09-14 · SOURCE_AUTHORITIES_IDENTIFIED_AS_BNE_421_422 · NO_DUPLICATE_FOUND · CORRECTION_OWNER_IDENTIFIED_UPSTREAM · SITE_GRAPH_NOT_UPDATED_NO_EVIDENCE`

Se cierra esta PR como auditoría completa, no como alta conseguida: no
hay nada que David ni esta sesión puedan hacer directamente en viaf.org.
El camino de entrada sigue siendo indirecto vía BNE (#422, ya documentado
como dependencia editorial de Depósito Legal) y/o ISNI (#421). Revisar
VIAF de nuevo solo si BNE o ISNI cambian de estado, no por rutina.
