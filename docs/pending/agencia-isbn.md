# Agencia del ISBN — auditoría de asignación y plan de corrección

Fecha de investigación: **2026-09-07**  
PR owner: **#406 · `tracking/agencia-isbn`**  
Estado: **RESEARCHED · ISBN_AGENCY_OWNERSHIP_SPLIT_CONFIRMED · SAMUEL_SPAIN_RANGE · MANECILLAS_US_RANGE · EXTERNAL_ACTION_PENDING**

## Objetivo

Verificar los ISBN de `Samuel entre mundos` y `Las manecillas del recuerdo`, determinar **qué agencia/registrante es realmente responsable de cada ISBN** y dejar preparado el flujo correcto de corrección de metadatos.

El hallazgo principal de esta investigación cambia el planteamiento original de la PR:

> **No todos estos ISBN pertenecen a la Agencia del ISBN de España.**

Por tanto, no se debe enviar automáticamente cualquier incidencia de Manecillas a `agenciaisbn.es`.

## Hallazgo crítico: prefijos/agencias distintos

La Agencia Internacional del ISBN confirma actualmente:

- `979-13` → grupo asignado a **España**;
- `979-8` → grupo **exclusivo de Estados Unidos y territorios asociados**, gestionado dentro del sistema ISBN estadounidense.

Fuentes primarias:

- https://www.isbn-international.org/node/331 — la Agencia Internacional explica que `979-8` es exclusivo de Estados Unidos y territorios asociados.
- https://www.isbn-international.org/export_rangemessagebyprefix.pdf — Range Message oficial: `979-13 Spain`; `979-8 United States`.
- https://www.isbn-international.org/es/range_file_generation — explicación del fichero oficial de rangos.

### Aplicación a los libros

| Obra / formato | ISBN | Grupo | Agencia/owner de asignación a investigar |
|---|---:|---|---|
| `Samuel entre mundos` · tapa blanda | `9791387659776` | `979-13` | **España** |
| `Las manecillas del recuerdo` · tapa blanda | `9798905149351` | `979-8` | **Estados Unidos** |
| `Las manecillas del recuerdo` · Kindle/ebook | `9798906781925` | `979-8` | **Estados Unidos** |

Esto NO significa que Manecillas sea “una publicación estadounidense” a nivel editorial. Significa únicamente que **esos ISBN concretos fueron asignados dentro del rango de la agencia estadounidense**. Un editor puede usar un ISBN asignado por la agencia competente del registrante y comercializar el libro internacionalmente.

Antes de inferir quién pidió esos ISBN (`Monza`, proveedor de impresión, KDP u otro), Claude debe identificar el **registrant/publisher** exacto mediante el Global Register y la documentación editorial.

## Regla internacional relevante

La Agencia Internacional del ISBN indica que:

- cada ISBN identifica una edición/formato concreto;
- cada formato/edición diferente necesita normalmente un ISBN distinto;
- los editores solicitan los ISBN a la agencia que opera en el territorio donde están establecidos;
- `979-8` no debe reinterpretarse como un ISBN de otro grupo o convertirse a ISBN-10.

Fuentes:

- https://www.isbn-international.org/es/content/que-es-un-isbn/10
- https://grp.isbn-international.org/content/about-isbn/349
- https://www.isbn-international.org/es/node/37

## Estado factual canónico

### Samuel entre mundos

- título: `Samuel entre mundos`;
- autor: **David Porto Díaz**;
- editorial: **Libros Indie**;
- ISBN: `9791387659776`;
- tapa blanda;
- 422 páginas;
- publicación: 2025.

Su ISBN pertenece al grupo `979-13` de España y, por tanto, **sí entra en el ámbito natural de la Agencia del ISBN española**.

### Las manecillas del recuerdo — papel

- título: `Las manecillas del recuerdo`;
- autor: **David Porto Díaz**;
- editorial pública: **Monza Ediciones**;
- ISBN: `9798905149351`;
- ASIN: `B0HHY9MYLM`;
- tapa blanda;
- 272 páginas;
- publicación editorial: **2026-09-03**.

El ISBN pertenece al grupo `979-8` estadounidense.

### Las manecillas del recuerdo — ebook/Kindle

- título: `Las manecillas del recuerdo`;
- autor: **David Porto Díaz**;
- editorial pública: **Monza Ediciones**;
- ISBN: `9798906781925`;
- ASIN: `B0HHM71F46`;
- publicación: **2026-08-12**.

También pertenece al grupo `979-8` estadounidense.

No asumir que el titular/registrant del ISBN sea Amazon, Monza o David hasta consultarlo en el Global Register o documentación de la edición.

## Agencia del ISBN española — qué gestiona actualmente

La Agencia española está gestionada por la **Federación de Gremios de Editores de España (FGEE)** mediante convenio con la International ISBN Agency.

Fuente:

- https://www.agenciaisbn.es/web/agencia.php

Para editoriales registradas, la Plataforma ISBN permite:

- registrar libros publicados;
- gestionar información comercial/metadatos;
- actualizar información que después se pone a disposición de la cadena comercial.

La propia Agencia destaca que los metadatos de calidad son fundamentales para librerías, distribuidores, tiendas online y lectores.

Fuente:

- https://www.agenciaisbn.es/web/info_editoriales.php?lang=es

### DILVE es parte crítica del flujo español

La Agencia señala que **DILVE es obligatorio para el registro de libros desde 2020** y que amplía la gestión de datos ricos como:

- portada;
- resumen;
- biografía;
- otros metadatos comerciales.

Por ello #406 y #404 deben coordinarse:

- Agencia ISBN → asignación/registro ISBN y metadatos básicos/comerciales del circuito español;
- DILVE → enriquecimiento y distribución amplia de metadata comercial;
- corregir solo uno de los dos puede no ser suficiente si el otro sigue emitiendo información contradictoria.

## Thema / clasificación

La Agencia española indica que utiliza **Thema** para describir materias y mejorar el descubrimiento comercial internacional de libros.

Fuente:

- https://www.agenciaisbn.es/web/info_editoriales.php?lang=es

Cuando Claude audite Samuel, registrar también los códigos/materias si la plataforma o DILVE los expone. No cambiar categorías por intuición SEO: comparar primero con género/contenido real y owner editorial.

## Importante: ISBN ≠ copyright ≠ Depósito Legal

No usar el ISBN para demostrar:

- propiedad intelectual;
- derechos de edición;
- Depósito Legal completado;
- disponibilidad en BNE;
- stock/venta.

Cada sistema tiene un propósito distinto.

La Agencia Internacional define ISBN como identificador internacional de publicaciones para descubrimiento, suministro, comercio y gestión bibliográfica.

## Cómo verificar el registrant real

El **Global Register of Publishers** de la International ISBN Agency permite búsquedas públicas por:

- prefijo ISBN;
- ISBN completo en determinados casos;
- nombre de publisher;
- agencia/país.

Fuentes:

- https://grp.isbn-international.org/node/357
- https://grp.isbn-international.org/content/using-register/358

El registro global contiene información sobre publishers/registrants, no una base completa de metadatos de cada libro.

### Procedimiento para Claude

Buscar:

1. `9791387659776`
2. `9798905149351`
3. `9798906781925`

Para cada uno anotar:

- grupo/agencia;
- registrant/publisher mostrado;
- prefijo de registrant;
- estado active/inactive si aparece;
- fuente/URL;
- si coincide con la editorial pública de la edición.

No publicar direcciones/telefonía de una persona física si el registro devuelve información privada/no necesaria. Solo conservar los datos institucionales imprescindibles.

## Samuel — auditoría en Agencia ISBN España

Como `9791387659776` pertenece a `979-13 España`, Claude debe:

1. buscar/consultar el registro ISBN por los canales disponibles de Agencia/Libros Indie;
2. comparar:
   - título;
   - autor;
   - editorial/sello;
   - formato;
   - fecha;
   - idioma;
   - materia/Thema;
   - PVP si el registro comercial lo contiene;
   - estado comercial si se expone;
3. comparar los datos ricos en DILVE (#404);
4. si existe error, determinar si **Libros Indie** controla el registro;
5. solicitar a Libros Indie/Agencia la corrección en el owner real;
6. comprobar propagación a TodosTusLibros/retailers.

No crear otro ISBN para corregir metadatos de la misma edición.

## Manecillas — NO tramitar como ISBN español por defecto

Los dos ISBN `979-8` son de rango estadounidense.

Para cada formato:

1. identificar el registrant en el Global Register;
2. revisar documentación contractual/editorial de Monza;
3. determinar si la asignación procede de:
   - Monza mediante un registrant/proveedor;
   - Amazon/KDP;
   - otro servicio de impresión/distribución;
4. comprobar quién tiene capacidad para corregir los metadatos asociados al ISBN;
5. escalar al owner correcto.

**No escribir a la Agencia española pidiendo “corregir el ISBN de Manecillas” sin esta comprobación previa.** Esa agencia no es la autoridad de asignación de `979-8`.

## ¿Debe preocupar que Manecillas use 979-8?

No por sí mismo.

La International ISBN Agency confirma que un ISBN `979-8` válido puede utilizarse para identificar, comercializar y vender libros internacionalmente. El dato que importa es:

- que el ISBN sea válido;
- que corresponda exactamente a esa edición/formato;
- que el registrant sea legítimo;
- que los metadatos sean coherentes;
- que no se reutilice para otra edición incompatible.

No intentar migrar Manecillas a `979-13` solo porque la editorial sea española. Un cambio de ISBN significaría una nueva asignación/identidad bibliográfica y requiere justificación editorial real.

## Cada formato necesita su propia identidad

La International ISBN Agency establece que diferentes formatos/ediciones deben identificarse por separado.

Por tanto, que Manecillas papel y ebook tengan ISBN distintos es conceptualmente correcto.

Auditar que:

- papel `9798905149351` identifica SOLO la edición impresa correspondiente;
- ebook `9798906781925` identifica SOLO la edición digital correspondiente;
- no estén cruzados en retailers/catalogadores;
- ASINs Amazon estén asociados al formato correcto.

## Datos volátiles

No tratar como autoridad permanente de ISBN:

- stock;
- ranking;
- reviews;
- promociones;
- disponibilidad inmediata;
- precio Amazon puntual.

El PVP editorial puede auditarse como metadata comercial si el owner lo publica, pero cualquier discrepancia debe distinguir precio editorial de descuento/precio retailer.

## Procedimiento completo de auditoría

### Fase 1 · validar estructura/agencia

- [x] Samuel → `979-13` España.
- [x] Manecillas papel → `979-8` Estados Unidos.
- [x] Manecillas ebook → `979-8` Estados Unidos.
- [ ] identificar registrant exacto de cada ISBN en Global Register.

### Fase 2 · verificar metadata

Para cada ISBN:

- [ ] título exacto;
- [ ] autor exacto;
- [ ] publisher/registrant;
- [ ] sello editorial mostrado;
- [ ] formato;
- [ ] idioma;
- [ ] fecha;
- [ ] páginas cuando proceda;
- [ ] materia/Thema si aplica;
- [ ] precio comercial si aplica;
- [ ] estado comercial;
- [ ] portada/resumen en DILVE para ISBN españoles/cadena española.

### Fase 3 · clasificación de discrepancias

Usar:

- `CORRECT`
- `DISPLAY_VARIATION_ONLY`
- `WRONG_TITLE`
- `WRONG_AUTHOR`
- `WRONG_FORMAT`
- `WRONG_PUBLISHER_OR_REGISTRANT`
- `WRONG_DATE`
- `WRONG_SUBJECT_METADATA`
- `ISBN_REUSED_OR_CROSSED`
- `OWNER_UNKNOWN`
- `PUBLISHER_ACTION_REQUIRED`
- `ISBN_AGENCY_ACTION_REQUIRED`

### Fase 4 · corrección por owner

#### Samuel

Prioridad:

`Libros Indie → Plataforma ISBN/DILVE → Agencia ISBN España si requiere soporte`.

La Agencia publica actualmente:

- `agencia@agenciaisbn.es`
- Plataforma ISBN para editoriales registradas.

No enviar datos privados de credenciales a Git.

#### Manecillas

Prioridad:

`registrant real 979-8 / Monza / proveedor de publicación → agencia/soporte correspondiente`.

No presuponer que la cuenta KDP del autor controla las ediciones.

## Coordinación downstream

Una corrección ISBN/metadata puede tardar en propagarse. Después hay que comprobar:

- #404 DILVE;
- #407 TodosTusLibros;
- #410 retailers;
- #405 Google Books;
- #422 BNE;
- #396 Amazon Author Central;
- #397 Goodreads.

No corregir manualmente seis downstreams si todos consumen el mismo dato incorrecto del publisher/feed.

## QA final

### Samuel

- [ ] ISBN válido y asociado a Samuel.
- [ ] autor David Porto Díaz.
- [ ] publisher/sello correcto.
- [ ] formato/fecha coherentes.
- [ ] datos DILVE/retailers sin contradicción material.

### Manecillas papel

- [ ] registrant `979-8` identificado.
- [ ] ISBN asociado solo a papel.
- [ ] autor/título/editorial coherentes.
- [ ] no cruzado con ebook.

### Manecillas ebook

- [ ] registrant `979-8` identificado.
- [ ] ISBN asociado solo al formato digital.
- [ ] autor/título/editorial coherentes.
- [ ] no cruzado con papel.

## Evidencia mínima de cierre

Guardar en PR:

- captura/resultado del Global Register para cada ISBN;
- agency/group confirmado;
- registrant público confirmado;
- metadata comparada;
- discrepancias;
- solicitud/ticket enviado y owner, si existe;
- propagación final relevante;
- fecha de QA.

No almacenar credenciales, facturas privadas, datos de pago ni documentación personal del registrant.

## Criterios de cierre

### Todo correcto

`ISBN_AGENCIES_VERIFIED · REGISTRANTS_VERIFIED · FORMAT_IDENTITIES_CORRECT · METADATA_COHERENT · DOWNSTREAM_SPOTCHECK_DONE`

### Correcciones pendientes

`ISBN_OWNERSHIP_VERIFIED · METADATA_ISSUES_DOCUMENTED · RESPONSIBLE_PUBLISHER_OR_AGENCY_REQUEST_OPENED · EXTERNAL_DEPENDENCY_RECORDED`

### Muy importante

No cerrar como `AGENCIA_ISBN_ESPAÑA_VERIFIED` para Manecillas: **sus ISBN no pertenecen al rango español**.

## Fuentes primarias consultadas · 2026-09-07

Agencia del ISBN España:

- https://www.agenciaisbn.es/web/ — estado/prefijo español `979-13`.
- https://www.agenciaisbn.es/web/agencia.php — gestión FGEE.
- https://www.agenciaisbn.es/web/info_editoriales.php?lang=es — Plataforma ISBN, DILVE, metadata y Thema.
- https://www.agenciaisbn.es/web/autoreseditores.php — autor/editor y datos ricos.
- https://www.agenciaisbn.es/web/comunicacion.php — comunicación de datos/editoriales.

International ISBN Agency / Global Register:

- https://www.isbn-international.org/node/331 — `979-8` Estados Unidos.
- https://www.isbn-international.org/export_rangemessagebyprefix.pdf — rango oficial `979-13 Spain / 979-8 United States`.
- https://www.isbn-international.org/es/range_file_generation — rango machine-readable.
- https://www.isbn-international.org/es/content/que-es-un-isbn/10 — estructura ISBN.
- https://grp.isbn-international.org/content/about-isbn/349 — ISBN y formatos.
- https://grp.isbn-international.org/node/357 — búsqueda del Global Register.
- https://grp.isbn-international.org/content/using-register/358 — alcance del Register.

Autoridad factual del proyecto:

- https://davidportodiaz.com/libros/samuel-entre-mundos/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/

Regla final: **primero determinar qué agencia/registrant asignó cada ISBN; después corregir metadatos en el verdadero owner.**
