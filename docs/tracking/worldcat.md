# WorldCat / OCLC — bibliografía, autoridad y linked data

Fecha de investigación: **2026-09-07**  
PR owner: **#419 · `tracking/worldcat`**  
Estado: **RESEARCHED · PUBLIC_RECORDS_NOT_OBSERVED · READY_FOR_DIRECT_AUDIT**

## Objetivo

Comprobar si **David Porto Díaz**, `Samuel entre mundos` y `Las manecillas del recuerdo` están correctamente representados en WorldCat/OCLC, y aprovechar cualquier registro/OCN/WorldCat Entity estable como autoridad bibliográfica externa.

WorldCat no es una ficha promocional que un autor pueda crear libremente. Es un catálogo cooperativo alimentado por bibliotecas miembro y fuentes de metadata. Por tanto, el trabajo correcto es:

1. localizar registros reales;
2. corregir errores en el owner adecuado;
3. conseguir catalogación por una biblioteca OCLC si una obra realmente no está en WorldCat;
4. capturar OCN/WorldCat Entity solo cuando estén inequívocamente verificados.

## Por qué merece la pena

OCLC describe WorldCat como la base de datos más completa de colecciones bibliotecarias y la hace accesible gratuitamente en WorldCat.org.

Además, **WorldCat Entities** modela Personas, Obras, Lugares y Eventos como linked data y conecta con vocabularios/authority files externos. Si aparece una entidad estable de David o de sus obras, puede reforzar el grafo de identidad bibliográfica y aportar un `sameAs` institucional real.

Fuentes oficiales:

- https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors
- https://www.oclc.org/en/worldcat/entities.html

## Estado público observado hoy

Búsquedas públicas por:

- `9791387659776`
- `9798905149351`
- `9798906781925`
- `David Porto Díaz`
- títulos exactos

no han devuelto en el rastreo web actual una ficha WorldCat inequívoca.

Estado correcto:

`PUBLIC_WORLDCAT_RECORD_NOT_OBSERVED`

Esto **NO significa** que los registros no existan. WorldCat puede contener registros no bien indexados por Google, agrupaciones, holdings no visibles en WorldCat.org o registros recientes.

Claude debe buscar directamente en WorldCat.org antes de concluir ausencia.

## Datos canónicos preparados

### Samuel entre mundos

- autor: `David Porto Díaz`
- editorial: `Libros Indie`
- ISBN: `9791387659776`
- formato: paperback
- páginas autoridad actual: `422`
- publicación editorial: 2025
- idioma: Spanish
- URL oficial: `https://davidportodiaz.com/libros/samuel-entre-mundos/`

Discrepancia externa ya conocida: algunos retailers muestran `412` páginas. No corregir WorldCat a 422 sin comprobar antes #429 Libros Indie / #404 DILVE si WorldCat contiene otro valor.

### Las manecillas del recuerdo · papel

- autor: `David Porto Díaz`
- editorial: `Monza Ediciones`
- ISBN: `9798905149351`
- ASIN: `B0HHY9MYLM`
- fecha: `2026-09-03`
- páginas autoridad actual: `272`
- PVP actual: `15,99 €` — no es dato relevante para el registro WorldCat
- idioma: Spanish

Discrepancia externa conocida: algunos retailers muestran `266` páginas. Resolver primero #428/#404.

### Las manecillas del recuerdo · ebook

- autor: `David Porto Díaz`
- editorial: `Monza Ediciones`
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- fecha: `2026-08-12`
- formato: ebook
- idioma: Spanish

Papel y ebook son manifestaciones/ediciones distintas. No tratarlas como duplicados solo porque comparten título.

## Cómo entran los libros en WorldCat

OCLC indica expresamente a los autores que WorldCat es un catálogo cooperativo y que, si una obra no está presente, la vía normal es contactar con una **biblioteca miembro de OCLC** para que catalogue el libro.

Importante: incluso si una biblioteca miembro añade el registro, la visualización pública en WorldCat.org depende de las suscripciones/holdings correspondientes.

Fuente oficial:

- https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors/How_can_I_add_my_work_to_WorldCat

### Consecuencia para nosotros

No intentar “subir un libro” directamente desde una cuenta de usuario WorldCat.

Si Samuel o Manecillas realmente no existen:

1. comprobar BNE/#422 y eBiblio/bibliotecas;
2. comprobar con editorial/distribuidor;
3. localizar una biblioteca OCLC que tenga/adquiera el ejemplar;
4. solicitar catalogación por el canal normal si procede;
5. esperar aparición del registro/holding.

No pagar servicios de catalogación privados para esta tarea.

## Correcciones de registros

OCLC tiene un canal específico para autores.

Para cambios bibliográficos de títulos:

- `bibchange@oclc.org`

Para errores de nombre, información personal o atribución de autor:

- `authfile@oclc.org`

También existe el WorldCat and Authority Record Quality Control Request form.

OCLC pide normalmente:

- OCLC Number / OCN;
- URL del registro;
- campo incorrecto;
- valor correcto y evidencia.

Fuente oficial:

- https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors/How_can_I_request_a_change_to_my_works_record_in_WorldCat

Regla: **primero corregir publisher/metadata source cuando el error nace upstream**. La propia guía de OCLC recomienda contactar primero con publisher/institution owner porque suelen aportar los metadatos que WorldCat refleja.

## Autoría incorrecta

Si un registro muestra otro autor o una forma equivocada que cambia identidad, OCLC recomienda registrar el OCN y reportar el problema a personal de catalogación / authority control.

No pedir corrección solo porque la forma autorizada sea bibliográficamente `Porto Díaz, David`. Esa serialización puede ser normal.

Fuente:

- https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors/What_do_I_do_if_my_work_has_a_different_authors_name_in_the_record

## Portada

WorldCat no carga portadas individuales simplemente porque el autor envíe una imagen nueva. OCLC obtiene cover art de grandes proveedores y recomienda suministrar la portada correcta a los trading partners.

Si una portada está **equivocada** en una ficha existente, sí se puede reportar a OCLC con URL + OCN + captura.

Fuente:

- https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors/How_do_I_correct_the_cover_art_for_my_work

Consecuencia:

- portada ausente → mejorar upstream/editorial/trading partners;
- portada incorrecta → OCLC correction request.

## WorldCat Entities

Buscar también en:

- https://entities.oclc.org/

por:

- `David Porto Díaz`
- `Samuel entre mundos`
- `Las manecillas del recuerdo`

WorldCat Entities puede tener entidades de Person/Work aunque la navegación bibliográfica pública sea diferente.

Para cada entity encontrada guardar:

- entity URI/ID;
- type (Person/Work);
- preferred label;
- alternate names;
- works/connections;
- external authority links;
- ISBN/OCN asociados cuando aparezcan;
- evidencia de que realmente es David/obra correcta.

No aceptar una coincidencia solo por nombre.

## Relación con VIAF/ISNI/BNE/Wikidata

WorldCat/OCLC forma parte del ecosistema de autoridad bibliográfica, pero no debemos crear loops de evidencia circular.

Orden de verificación:

1. registro WorldCat/OCN real;
2. WorldCat Entity real;
3. autoridad BNE/VIAF/ISNI si está enlazada;
4. comparar con Wikidata `Q139678851`;
5. solo después actualizar `sameAs`.

No usar el hecho de que Wikidata ya diga algo como prueba para crear la misma afirmación en OCLC si no hay evidencia independiente.

## Duplicados / ediciones

WorldCat puede agrupar ediciones/formatos en la experiencia de búsqueda. No interpretar una vista agrupada como una sola edición bibliográfica.

Para cada ISBN comprobar su registro/OCN específico.

### No son duplicados

- Manecillas papel vs ebook;
- distintas ediciones con ISBN distintos;
- registros con naturaleza bibliográfica diferente legítima.

### Posible duplicado real

- dos registros bibliográficos que describen exactamente la misma edición/ISBN sin razón catalográfica.

Si hay duplicado, reportar los OCN implicados; no elegir uno arbitrariamente y añadir ambos a `sameAs`.

## Bibliotecas/holdings

WorldCat permite ver qué bibliotecas poseen una obra cuando sus holdings son visibles.

Esto puede darnos dos utilidades:

1. descubrir presencia real de Samuel/Manecillas en bibliotecas;
2. detectar bibliotecas a las que tiene sentido ofrecer información de club de lectura/evento más adelante.

Pero no usar el número de libraries como una cifra estable de marketing: OCLC advierte que holdings pueden fluctuar.

## Secuencia exacta para Claude

### Fase 1 · búsqueda WorldCat

Buscar por ISBN exacto:

1. `9791387659776`
2. `9798905149351`
3. `9798906781925`

Después:

- `David Porto Díaz`
- `Samuel entre mundos`
- `Las manecillas del recuerdo`

Por resultado guardar:

- URL permanente;
- OCN/OCLC number;
- title;
- author heading;
- publisher;
- place/date;
- ISBN;
- format;
- pages/physical description;
- language;
- subjects;
- notes;
- holdings/libraries como snapshot;
- related editions/formats.

### Fase 2 · WorldCat Entities

Buscar Person + Works y capturar IDs reales.

### Fase 3 · comparar

Cruzar:

- #422 BNE;
- #420 VIAF;
- #421 ISNI;
- #398 Wikidata;
- #404 DILVE;
- #428/#429 publishers.

### Fase 4 · corregir

Clasificar:

- `CORRECT`
- `NOT_OBSERVED`
- `BIBLIOGRAPHIC_ERROR`
- `AUTHORITY_ERROR`
- `DUPLICATE`
- `UPSTREAM_PUBLISHER_ERROR`
- `CATALOGING_REQUIRED`
- `EXTERNAL_DEPENDENCY`

Si es bibliographic/authority error, usar los canales OCLC documentados.

### Fase 5 · si el libro falta realmente

No abrir un ticket de “añádeme”. Buscar primero una biblioteca miembro OCLC / BNE que pueda catalogar legítimamente el ejemplar.

### Fase 6 · QA público

Tras propagación:

- ISBN search;
- title search;
- author search;
- mobile/desktop;
- related editions;
- holdings;
- WorldCat Entity;
- external authority links.

## Posibles cambios en la web

La web no necesita ningún cambio previo.

Si se obtiene un WorldCat/Entities URL estable y canónico:

### Autor

Añadir a `Person.sameAs` únicamente si la WorldCat Entity es inequívocamente David Porto Díaz.

### Libros

Añadir a `Book.sameAs` únicamente si:

- el WorldCat URL identifica la misma obra/edición;
- no es una página de búsqueda temporal;
- no es un holding local;
- no hay ambigüedad de formato.

Preferir WorldCat Entity/Work estable frente a una URL de resultados.

Después actualizar owner factual/generador correspondiente y CI (`machine-authority`, identidad, schema, etc.).

## Evidencia mínima de cierre

Por autor/obra:

- URL WorldCat;
- OCN;
- Entity ID/URI si existe;
- metadata final;
- holdings snapshot;
- corrección enviada/no necesaria;
- ticket/reference;
- fecha QA.

## Criterio de cierre

`WORLDCAT_ISBNS_AUDITED · OCN_CAPTURED_OR_NOT_OBSERVED · AUTHOR_AUTHORITY_AUDITED · WORLDCAT_ENTITIES_AUDITED · DUPLICATES_REVIEWED · METADATA_CORRECT_OR_REQUEST_OPENED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · PUBLIC_QA_DONE`

Si no hay registros y la vía correcta es biblioteca:

`CATALOGING_PATH_IDENTIFIED · EXTERNAL_DEPENDENCY_RECORDED · NO_FAKE_RECORD_CREATED`
