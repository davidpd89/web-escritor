# Biblioteca Nacional de España — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#422 · `tracking/bne`**  
Estado: **CATALOG_QUERIED_DIRECTLY · CONFIRMED_ABSENT_NOT_JUST_UNOBSERVED · DEPOSITO_LEGAL_LIKELY_PENDING · EXTERNAL_ACTION_PENDING**

## Consulta directa al catálogo (2026-09-08)

La investigación anterior se basó en búsqueda web general y explícitamente
no descartaba que el catálogo tuviera el registro sin exponerlo bien al
buscador. Esta ronda consulta **directamente** `catalogo.bne.es`
(interfaz Primo/Ex Libris, `vid=34BNE_INST:CATALOGO`), que es justo lo
que este documento pedía hacer antes de concluir ausencia:

- Búsqueda por `David Porto Díaz`: 11 resultados, ninguno relacionado —
  todos son coincidencias sueltas de "David", "Porto" o "Díaz" como
  fragmentos de nombre en obras de cine/audio/tesis sin relación.
- Búsqueda por ISBN `9791387659776` (Samuel entre mundos): **0
  resultados** — "No se encontraron registros".
- Búsqueda por ISBN `9798905149351` (Manecillas, papel): **0
  resultados** — "No se encontraron registros".

Esto ya no es `NOT_OBSERVED_WITH_CURRENT_SEARCH` (un buscador general que
podría no exponerlo bien): es una consulta directa al catálogo por ISBN
exacto, con resultado limpio y explícito de "no encontrado". La
interpretación más probable es que el **Depósito Legal** de ninguno de
los dos libros se ha completado o procesado todavía en el catálogo BNE —
en España esto suele ser responsabilidad de la editorial (Libros Indie /
Monza Ediciones), no algo que el autor o esta sesión puedan completar
directamente desde aquí.

**Siguiente paso real**: confirmar con Libros Indie y Monza Ediciones si
el Depósito Legal de sus ISBN se tramitó, y si no, que lo tramiten — esto
sigue bloqueado en las editoriales, coordinable con #428/#404/#429, igual
que la discrepancia de páginas ya documentada ahí.

## Objetivo

Comprobar y, cuando proceda, mejorar la representación bibliográfica y de autoridad de **David Porto Díaz**, `Samuel entre mundos` y `Las manecillas del recuerdo` en la Biblioteca Nacional de España, sin confundir:

- catálogo bibliográfico;
- registro de autoridad de persona;
- Bibliografía Española;
- Depósito Legal;
- VIAF/ISNI;
- Wikidata u otros grafos externos.

La prioridad es obtener una autoridad bibliográfica institucional correcta. No se trata de crear “perfiles promocionales” ni de presentar la BNE como una ficha editable por el autor.

## Estado factual canónico a 2026-09-07

### Autor

- Nombre público: **David Porto Díaz**.
- Web oficial: **https://davidportodiaz.com/**.
- Autor de `Samuel entre mundos` y `Las manecillas del recuerdo`.
- La forma exacta del encabezamiento de autoridad BNE **no se presupone**. Puede aplicar reglas de catalogación propias; hay que registrar la forma autorizada que realmente use la BNE.

### Ediciones a buscar

| Obra / formato | Editorial | Identificador | Fecha / dato estable |
|---|---|---|---|
| `Samuel entre mundos` · tapa blanda | Libros Indie | ISBN `9791387659776` | 2025 · 422 páginas |
| `Las manecillas del recuerdo` · tapa blanda | Monza Ediciones | ISBN `9798905149351` | 2026-09-03 · 272 páginas |
| `Las manecillas del recuerdo` · Kindle | Monza Ediciones | ISBN `9798906781925` | 2026-08-12 |

Para BNE no asumir que la edición Kindle y la impresa deban aparecer del mismo modo ni que ambas estén sujetas al mismo flujo de Depósito Legal/catalogación. Son manifestaciones distintas.

## Resultado de búsqueda pública de hoy

El 2026-09-07 se han realizado búsquedas web públicas por:

- `David Porto Díaz` restringido a BNE;
- `Samuel entre mundos` + autor;
- `Las manecillas del recuerdo` + autor;
- títulos/ISBN en resultados públicos del catálogo.

No se ha localizado mediante esas búsquedas un registro bibliográfico o de autoridad inequívoco de David/las obras.

Estado correcto:

`PUBLIC_BNE_RECORD_NOT_OBSERVED_WITH_CURRENT_SEARCH`

Esto **NO equivale a `ABSENT_FROM_BNE`**. El catálogo puede contener registros no bien expuestos por el buscador general, variantes del encabezamiento, registros recién procesados o entradas todavía en flujo de depósito/catalogación. Claude debe consultar directamente el catálogo BNE por ISBN y autor antes de concluir ausencia.

## Qué es el Catálogo de Autoridades BNE

BNElab describe el catálogo de autoridades como un conjunto de **más de 300.000 registros** que normalizan los encabezamientos usados en registros bibliográficos para personas, entidades, títulos y materias.

La BNE publica además una versión semantizada/enriquecida con fuentes externas como **VIAF**.

Fuente primaria:

- https://bnelab.bne.es/dato/catalogo-de-autoridades/

Implicación para David:

- si existe un registro de autoridad, ese registro es el owner institucional para la forma normalizada del nombre dentro del catálogo BNE;
- no copiar a Wikidata/VIAF/ISNI un identificador simplemente porque “parece” corresponder;
- primero confirmar el registro exacto y sus enlaces externos.

## Qué es el catálogo bibliográfico

El dataset oficial BNE incluye monografías modernas, recursos electrónicos y otros materiales, con acceso en formatos bibliográficos y linked data.

Fuente:

- https://bnelab.bne.es/dato/catalogo-bibliografico/

Para cada libro hay que distinguir:

- registro bibliográfico de una edición concreta;
- autoridad personal del autor;
- relación entre ambos.

Papel + Kindle de Manecillas no son “duplicados” por ser el mismo título. Solo hay duplicado si se repite indebidamente la misma manifestación/edición.

## Bibliografía Española

La BNE define la **Bibliografía Española** como el registro de documentos publicados en España que ingresan conforme a las disposiciones vigentes de Depósito Legal; funciona como control bibliográfico nacional de la producción editorial española.

Fuente:

- https://bnelab.bne.es/dato/bibliografia-espanola/

Consecuencia:

- una ausencia observable no debe resolverse creando un registro manual externo;
- puede reflejar un proceso de depósito/catalogación todavía no completado;
- si realmente falta una edición que debería haber ingresado, hay que investigar el flujo de Depósito Legal/editorial.

## Depósito Legal — quién es responsable

La documentación oficial de la BNE sobre Depósito Legal identifica al **editor como sujeto central** del sistema para publicaciones tangibles. La legislación vigente mantiene el depósito de las publicaciones físicas dentro del circuito legal correspondiente y la BNE ejerce funciones de conservación, coordinación, seguimiento e inspección.

Fuentes:

- https://www.bne.es/export/sites/BNWEB1/es/Servicios/PreguntasMasFrecuentes/docs/Deposito_Legal.pdf
- https://www.bne.es/sites/default/files/repositorio-archivos/BOE-A-2022-7311-consolidado.pdf

### Aplicación al proyecto

- Samuel → comprobar con **Libros Indie** si el depósito/catalogación fue tramitado correctamente si no aparece tras búsqueda directa.
- Manecillas → comprobar con **Monza Ediciones** si el depósito/catalogación está completado si la edición impresa no aparece tras un plazo razonable.
- David no debe presentar un depósito duplicado “para que aparezca en BNE” sin confirmar primero la responsabilidad y el estado del editor/oficina correspondiente.

La BNE publica informes recientes de seguimiento que muestran que el servicio reclama publicaciones que no han ingresado y corrige datos de depósito, de modo que una ausencia puede ser una incidencia operativa real, pero debe probarse antes de escalarla.

Fuente de contexto operativo:

- https://www.bne.es/sites/default/files/repositorio-archivos/informe_seguimiento_dl_2024_0.pdf

## ISNI — oportunidad institucional real

La Carta de Servicios de la BNE incluye entre sus servicios la **Solicitud de ISNI**.

Fuente primaria:

- https://www.bne.es/sites/default/files/repositorio-archivos/carta_de_servicios_2022_2025_0.pdf

A fecha de esta investigación no se ha verificado un ISNI inequívoco de David Porto Díaz.

Estado:

`ISNI_NOT_VERIFIED`

Procedimiento correcto:

1. comprobar primero el catálogo de autoridades BNE;
2. buscar David Porto Díaz directamente en ISNI;
3. si ya existe un ISNI, verificar que identidad/obras corresponden;
4. si no existe y la BNE admite la solicitud aplicable, usar el canal oficial de solicitud;
5. guardar únicamente el identificador público final, nunca datos privados del trámite.

**No autogenerar ni inventar un ISNI.**

## VIAF

El catálogo semantizado BNE puede enlazar registros con VIAF. A fecha de hoy no se ha verificado un VIAF inequívoco para David mediante la evidencia obtenida.

Estado:

`VIAF_NOT_VERIFIED`

Orden recomendado:

1. localizar autoridad BNE;
2. comprobar si el propio registro BNE expone VIAF;
3. si no, buscar por nombre + obra + país en VIAF;
4. no aceptar coincidencias solo por nombre;
5. documentar URL/ID únicamente cuando autoría y obras permitan desambiguar.

## Procedimiento exacto para Claude

### Fase 1 · catálogo bibliográfico

Buscar directamente en `https://catalogo.bne.es/` por identificador exacto:

1. `9791387659776`
2. `9798905149351`
3. `9798906781925`

Después buscar:

- `David Porto Díaz`
- `Porto Díaz, David`
- `Samuel entre mundos`
- `Las manecillas del recuerdo`

No asumir de antemano cuál es la forma autorizada del apellido/nombre; las variantes se usan únicamente para localizar el registro.

Para cada registro encontrado guardar:

- URL/permalink;
- número/ID BNE si aparece;
- tipo de registro;
- título;
- mención de responsabilidad/autor;
- editorial;
- lugar de publicación;
- fecha;
- ISBN;
- descripción física/páginas;
- lengua;
- materias/géneros;
- depósito legal si aparece;
- enlaces al registro de autoridad del autor;
- cualquier diferencia frente a los datos canónicos.

### Fase 2 · autoridad del autor

Abrir el registro de autoridad vinculado o buscar directamente en el catálogo de autoridades.

Guardar:

- encabezamiento autorizado exacto;
- variantes del nombre;
- identificador BNE;
- ocupación u otros datos públicos si existen;
- obras relacionadas;
- VIAF/ISNI u otros enlaces externos expuestos por BNE;
- fuentes/notas públicas del registro.

No solicitar que BNE añada premios, biografía promocional o perfiles sociales salvo que formen parte legítima del modelo de autoridad y exista fuente apropiada.

### Fase 3 · comprobar errores

Clasificar cada caso:

- `CORRECT`
- `NOT_OBSERVED`
- `BIBLIOGRAPHIC_METADATA_ERROR`
- `AUTHOR_AUTHORITY_MISMATCH`
- `DUPLICATE_BIBLIOGRAPHIC_RECORD`
- `DEPOSIT_OR_PROCESSING_PENDING`
- `PUBLISHER_DEPENDENCY`
- `BNE_CORRECTION_REQUEST_REQUIRED`

### Fase 4 · resolver por el owner correcto

#### Error editorial/fuente

Ejemplos: ISBN, título, editorial, fecha o autor enviados incorrectamente por publisher/distribuidor.

- comprobar primero Libros Indie/Monza/DILVE/Agencia ISBN;
- corregir en la fuente si procede;
- después pedir a BNE revisión si el registro no se actualiza.

#### Error de catalogación/autoridad BNE

Usar los canales de información bibliográfica de BNE y documentar:

- URL de registro;
- campo actual;
- valor correcto;
- fuente verificable;
- número/referencia de la consulta si lo proporcionan.

La Carta de Servicios confirma que la BNE ofrece **información bibliográfica especializada en línea** y acceso a sus catálogos. No usar `bnelab@bne.es` como buzón genérico para correcciones: ese contacto aparece asociado a los datasets de BNElab.

### Fase 5 · IDs externos

Cuando exista autoridad inequívoca:

- confirmar VIAF;
- confirmar/solicitar ISNI si procede;
- comparar con Wikidata #398;
- solo entonces considerar incorporar esos IDs como `sameAs`/identificadores en la web u otros registros.

No hacer el camino inverso de forma automática: Wikidata no debe imponerse sobre una autoridad BNE sin evidencia.

## Coordinación con las otras PR de metadatos

### #406 — Agencia del ISBN

Usar para confirmar la asignación ISBN y datos registrales. ISBN ≠ Depósito Legal y un registro ISBN correcto no demuestra que la BNE ya haya catalogado el ejemplar.

### #404 — DILVE

Puede ser upstream de metadatos comerciales/distribución. Una discrepancia DILVE/editorial debe corregirse en el owner correspondiente antes de perseguir síntomas downstream.

### #407 — TodosTusLibros

Es un destino downstream/comercial, no autoridad BNE.

### #398 — Wikidata

Solo enlazar BNE/VIAF/ISNI una vez confirmados. No crear referencias circulares donde web propia → Wikidata → BNE se usen para probarse mutuamente.

## Qué NO hacer

- No crear registros BNE manuales ficticios.
- No solicitar un segundo registro de autoridad si ya existe uno.
- No tratar papel/Kindle como duplicados solo por compartir título.
- No asumir que ausencia en Google = ausencia en BNE.
- No afirmar incumplimiento de Depósito Legal sin comprobar editor/oficina/proceso.
- No presentar premios o copy promocional como datos de autoridad sin justificación bibliográfica.
- No inventar VIAF/ISNI.
- No publicar datos personales privados dentro de Git.

## QA público final

Después de cualquier corrección:

- [ ] ISBN Samuel devuelve la edición correcta.
- [ ] ISBN Manecillas papel devuelve la edición correcta o dependencia documentada.
- [ ] ISBN Manecillas Kindle revisado según alcance del catálogo.
- [ ] búsqueda por nombre devuelve una autoridad inequívoca o `NOT_OBSERVED` documentado.
- [ ] todas las obras correctas enlazan al mismo autor cuando corresponda.
- [ ] no quedan duplicados relevantes conocidos.
- [ ] VIAF confirmado o `NOT_VERIFIED`.
- [ ] ISNI confirmado/solicitado o `NOT_VERIFIED/NOT_APPLICABLE`.
- [ ] diferencias con Agencia ISBN/DILVE registradas con owner.

## Evidencia mínima para cerrar

Guardar en la PR:

- fecha/hora de búsqueda;
- consultas exactas;
- URLs/IDs BNE;
- autoridad BNE final, si existe;
- VIAF/ISNI confirmados, si existen;
- capturas de errores relevantes;
- tickets/consultas abiertas sin información sensible;
- owner de cada corrección;
- estado final de cada ISBN.

## Criterios de cierre

### Caso completo

`BNE_BIBLIOGRAPHIC_RECORDS_VERIFIED · AUTHOR_AUTHORITY_VERIFIED · WORK_AUTHOR_LINKS_COHERENT · DUPLICATES_REVIEWED · VIAF_ISNI_VERIFIED_OR_EXPLICITLY_NOT_AVAILABLE · PUBLIC_QA_DONE`

### Dependencia editorial/BNE

`BNE_AUDITED · ISSUES_DOCUMENTED · PUBLISHER_OR_BNE_REQUEST_OPENED · EXTERNAL_DEPENDENCY_RECORDED · NO_DUPLICATE_CREATED`

### Sin registros observables

`DIRECT_BNE_SEARCH_COMPLETED · RECORDS_NOT_OBSERVED · DEPOSIT_PUBLISHER_STATUS_REQUESTED_OR_DOCUMENTED · NO_FALSE_ABSENCE_CLAIM`

## Fuentes primarias consultadas · 2026-09-07

- https://catalogo.bne.es/ — catálogo BNE.
- https://bnelab.bne.es/dato/catalogo-de-autoridades/ — Catálogo de Autoridades.
- https://bnelab.bne.es/dato/catalogo-bibliografico/ — Catálogo bibliográfico/datasets.
- https://bnelab.bne.es/dato/bibliografia-espanola/ — Bibliografía Española.
- https://www.bne.es/export/sites/BNWEB1/es/Servicios/PreguntasMasFrecuentes/docs/Deposito_Legal.pdf — FAQ Depósito Legal.
- https://www.bne.es/sites/default/files/repositorio-archivos/BOE-A-2022-7311-consolidado.pdf — legislación consolidada de Depósito Legal publicada por BNE.
- https://www.bne.es/sites/default/files/repositorio-archivos/informe_seguimiento_dl_2024_0.pdf — seguimiento operativo del Depósito Legal.
- https://www.bne.es/sites/default/files/repositorio-archivos/carta_de_servicios_2022_2025_0.pdf — servicios BNE, incluida solicitud de ISNI e información bibliográfica.

Autoridad factual propia:

- https://davidportodiaz.com/
- https://davidportodiaz.com/libros/samuel-entre-mundos/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/

Regla final: **BNE/VIAF/ISNI son autoridades bibliográficas, no perfiles promocionales. Primero identificar el registro real y su owner; después corregir con evidencia.**
