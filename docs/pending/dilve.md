# DILVE — auditoría de metadatos y plan de corrección

Fecha de investigación: **2026-09-07**  
PR owner: **#404 · `tracking/dilve`**  
Estado: **RESEARCHED · UPSTREAM_METADATA_OWNER_NOT_YET_VERIFIED · EXTERNAL_ACTION_PENDING**

## Objetivo

Auditar cómo están descritas y distribuidas `Samuel entre mundos` y `Las manecillas del recuerdo` en **DILVE (Distribuidor de Información del Libro Español en Venta)** y corregir los metadatos en el **owner upstream real**, de modo que la mejora se propague a librerías, distribuidoras y tiendas en línea sin mantener parches manuales distintos en cada retailer.

DILVE es especialmente importante porque no es una simple ficha pública: es infraestructura de intercambio de metadata del sector editorial.

## Qué es DILVE actualmente

DILVE se define como gestor y distribuidor de metadatos estandarizados del libro para toda la cadena comercial.

A fecha 2026-09-07 su web pública declara aproximadamente:

- más de **2 millones de libros gestionados**;
- alrededor de **1.480 editoriales**;
- cerca de **7.930 autores-editores**;
- más de **1.300 distribuidoras, librerías, tiendas online, desarrolladores y bibliotecas** conectadas en múltiples países.

Estas cifras son volátiles y no deben conservarse como KPI fijo del proyecto; solo demuestran el alcance actual del sistema.

Fuente primaria:

- https://web.dilve.es/

DILVE declara explícitamente que una metadata correcta permite:

- controlar los datos que circulan por el mercado;
- actualizar automáticamente información en la cadena comercial;
- mejorar presencia online;
- llegar a más distribuidoras/librerías;
- reducir errores generados por carga manual.

## Estándares actuales

DILVE usa estándares internacionales, especialmente:

- **ONIX for Books**;
- **Thema**;
- SINLI/CSV para determinados intercambios.

La versión interna actual indicada por DILVE es **ONIX 3.1**. Su documentación pública de 2026 ofrece listas de códigos ONIX Edición 72 (marzo de 2026).

Fuentes:

- https://web.dilve.es/onix/estandar-versiones-editeur/
- https://web.dilve.es/onix/documentacion-onix/

No hace falta “migrar” estos libros por nuestra cuenta a ONIX 3.1. El objetivo es comprobar qué metadata real envía el owner editorial y si esa metadata está completa/correcta.

## Relación DILVE ↔ Agencia ISBN

DILVE permite a las editoriales españolas automatizar el envío de altas hacia la Agencia del ISBN. Además, DILVE indica que las editoriales españolas suscritas reciben/cargan su catálogo para enriquecer metadatos y que las extracciones pueden incluir datos básicos de catálogos gestionados en Plataforma ISBN.

Fuentes:

- https://web.dilve.es/
- https://web.dilve.es/dilve/dilve-para-editoriales/
- https://www.agenciaisbn.es/web/info_editoriales.php?lang=es

### Hallazgo coordinado con #406

#406 ha demostrado que:

- Samuel `9791387659776` pertenece a `979-13` España;
- Manecillas papel `9798905149351` pertenece a `979-8` Estados Unidos;
- Manecillas ebook `9798906781925` pertenece a `979-8` Estados Unidos.

Esto afecta a la auditoría DILVE:

- Samuel encaja directamente en el circuito Agencia ISBN España ↔ DILVE;
- Manecillas **puede** estar en DILVE si Monza/distribuidor carga su metadata comercial, pero no debemos asumir que esos ISBN `979-8` estén registrados por la Agencia española;
- para Manecillas hay que comprobar el producto DILVE real y quién lo alimenta.

No rechazar un registro DILVE de Manecillas por usar `979-8`: DILVE distribuye metadata comercial y puede manejar productos con identificadores asignados fuera de España si el owner editorial los incorpora correctamente.

## Datos canónicos para comparar

### Samuel entre mundos

- título: `Samuel entre mundos`;
- autor: **David Porto Díaz**;
- editorial: **Libros Indie**;
- ISBN: `9791387659776`;
- tapa blanda;
- 422 páginas;
- publicación: 2025;
- idioma: español.

### Las manecillas del recuerdo · papel

- título: `Las manecillas del recuerdo`;
- autor: **David Porto Díaz**;
- editorial: **Monza Ediciones**;
- ISBN: `9798905149351`;
- ASIN: `B0HHY9MYLM`;
- tapa blanda;
- 272 páginas;
- publicación: **2026-09-03**;
- idioma: español.

### Las manecillas del recuerdo · ebook

- título: `Las manecillas del recuerdo`;
- autor: **David Porto Díaz**;
- editorial: **Monza Ediciones**;
- ISBN: `9798906781925`;
- ASIN: `B0HHM71F46`;
- formato digital/Kindle;
- publicación: **2026-08-12**;
- idioma: español.

No copiar páginas de la edición impresa al ebook salvo que la metadata editorial lo defina expresamente.

## Qué campos importa revisar

La documentación para editoriales de DILVE enumera un repertorio muy amplio, superior a 300 metadatos, que incluye:

- identificación;
- idiomas;
- edición;
- colección/serie;
- precio;
- estado comercial;
- disponibilidad;
- derechos de venta/territorios;
- cubierta;
- resumen/extractos;
- autorías/contribuidores;
- materias Thema/iBIC;
- público destinatario;
- características físicas/digitales;
- productos relacionados;
- premios.

Fuente:

- https://web.dilve.es/dilve/dilve-para-editoriales/

No hace falta completar todo por volumen. Priorizar los metadatos que cambien descubrimiento, identificación o compra real.

## Prioridad 1 · Identidad bibliográfica

Para cada producto:

- ISBN exacto;
- título/subtítulo;
- autor/contribuidores;
- editorial/sello;
- idioma;
- tipo/formato;
- edición;
- fecha de publicación;
- páginas cuando corresponda.

Cualquier error aquí puede contaminar múltiples destinos downstream.

## Prioridad 2 · Disponibilidad y estado comercial

DILVE distingue entre:

- estado del producto en el catálogo editorial;
- disponibilidad comercial;
- fecha de disponibilidad.

DILVE explica que la fecha de publicación debe ser real/completa y coherente con el estado. Por ejemplo, no debe mantenerse “Próxima aparición” cuando la fecha ya está en el pasado.

Fuentes:

- https://web.dilve.es/calidad-de-metadatos-2/metadatos/fecha-de-publicacion-y-estado-en-catalogo/
- https://web.dilve.es/calidad-de-metadatos-2/metadatos/disponibilidad-y-fecha-de-disponibilidad/

### Aplicación a Manecillas

A 2026-09-07:

- ebook publicado desde 2026-08-12;
- papel publicado desde 2026-09-03.

Si DILVE todavía marca cualquiera como `Próxima aparición`/equivalente, hay que corregir upstream.

No confundir “publicado” con “hay stock inmediato en todas las librerías”. Estado editorial y disponibilidad retailer son conceptos distintos.

## Prioridad 3 · Precio y derechos territoriales

DILVE indica que derechos de venta y precios deben ser coherentes por mercado.

Fuente:

- https://web.dilve.es/calidad-de-metadatos-2/metadatos/derechos-de-venta/

Revisar:

- PVP/moneda/IVA según metadata del editor;
- territorio al que aplica;
- derechos de venta declarados;
- disponibilidad por mercado si existe.

No copiar un precio promocional de Amazon como PVP editorial.

## Prioridad 4 · Materias Thema y descubrimiento

Thema existe para facilitar clasificación/intercambio internacional y descubrimiento.

No cambiar materias por intuición SEO. Para cada obra:

1. registrar códigos Thema actuales;
2. evaluar si describen realmente la obra;
3. detectar errores manifiestos (por ejemplo, género incompatible);
4. si hay mejora clara, prepararla para el owner editorial;
5. preservar consistencia en Agencia ISBN/DILVE.

DILVE mantiene un Grupo de trabajo ONIX/Thema con editoriales y agentes del canal (incluidos Amazon, Casa del Libro, CEGAL, El Corte Inglés, FNAC, etc.), lo que refuerza que estas decisiones afectan a downstreams reales.

Fuente:

- https://web.dilve.es/grupo-de-trabajo-onix-thema/

## Prioridad 5 · Datos ricos

Comprobar:

- portada de alta calidad correcta;
- sinopsis actual;
- bio de David;
- extracto/fragmento si lo suministra la editorial;
- premios únicamente cuando sean verificables y apropiados;
- enlaces/productos relacionados;
- público objetivo solo si editorialmente definido.

No inventar edades para Samuel/Manecillas simplemente para rellenar un campo.

## Portadas

Asegurar que:

- Samuel usa su portada editorial vigente;
- Manecillas usa la portada correcta;
- papel y ebook no apuntan accidentalmente a creatividades promocionales que no sean portada;
- no haya un asset antiguo con texto/edición incorrecta.

La web oficial/press kit puede servir como referencia visual, pero la fuente de envío DILVE debe ser la editorial autorizada.

## Autorías

DILVE ofrece documentación específica para **corrección de autorías**.

Fuente:

- https://web.dilve.es/herramientas/documentacion-herramientas/

Revisar especialmente:

- `David Porto Díaz` con acentos y orden correcto;
- evitar variantes como `David Porto Diaz` si no son necesarias para el feed;
- que no se confundan autor, editor, traductor u otros roles;
- que papel/ebook de Manecillas estén vinculados al mismo autor.

## Ediciones y formatos

DILVE recuerda que una nueva edición implica un nuevo ISBN; una reimpresión de la misma edición no cambia ISBN.

Fuente:

- https://web.dilve.es/calidad-de-metadatos-2/metadatos/edicion/

Aplicación:

- Manecillas papel y ebook son productos distintos con ISBN distintos: correcto;
- no duplicar producto solo por una reimpresión;
- si Samuel tiene una única edición impresa actual, no crear otra por un cambio menor de disponibilidad/cubierta que no constituya nueva edición según el publisher.

## Resultado de búsqueda pública

Las búsquedas web públicas del 2026-09-07 no han expuesto fichas DILVE indexadas inequívocas para Samuel/Manecillas.

Esto es normal/posible porque DILVE funciona principalmente como plataforma profesional autenticada y distribuidor de feeds.

Estado:

`PUBLIC_DILVE_RECORD_NOT_OBSERVED`

No significa que los productos no estén cargados.

La auditoría definitiva requiere:

- acceso del editor/distribuidor;
- extracción autorizada;
- o evidencia downstream que permita determinar qué metadata circula.

## Quién puede corregir

### Samuel

Owner probable a verificar:

**Libros Indie** / cuenta editorial o distribuidor que mantenga el registro.

David no debe abrir una cuenta autor-editor para reapropiarse del ISBN de una edición ya publicada por Libros Indie.

### Manecillas

Owner probable a verificar:

**Monza Ediciones** / distribuidor / proveedor que envíe la metadata.

El hecho de que los ISBN sean `979-8` no cambia quién mantiene necesariamente la ficha comercial en DILVE. Hay que preguntar/inspeccionar el feed.

## Canal de incidencias DILVE

DILVE publica actualmente:

`asistencia@dilve.es`

como canal de asistencia.

También documenta un canal de incidencias para entidades del canal que reciben metadatos; DILVE puede contactar con la editorial para que subsane errores reportados.

Fuente:

- https://web.dilve.es/dilve/dilve-para-distribuidoras/

Si David no tiene control editorial de DILVE:

- preferir primero solicitar corrección a Libros Indie/Monza;
- usar asistencia/incidencia DILVE cuando haya un error propagado y el owner no esté claro o se requiera soporte;
- no pedir credenciales ajenas.

## Procedimiento exacto para Claude

### Fase 1 · identificar owner/feed

Para cada ISBN:

1. comprobar #406 (agencia/registrant);
2. preguntar/consultar qué editorial/distribuidor mantiene DILVE;
3. determinar si existe cuenta DILVE autorizada a la que tengamos acceso;
4. no solicitar acceso de terceros ni guardar credenciales.

### Fase 2 · exportar/inventariar metadata

Si hay acceso autorizado:

- buscar por ISBN;
- exportar una ficha/CSV/ONIX si es posible;
- guardar únicamente la evidencia no sensible necesaria;
- comparar campo a campo.

Si no hay acceso:

- usar ficha editorial/retailers downstream para detectar síntomas;
- preparar tabla de correcciones;
- solicitar al publisher captura/export de DILVE o corrección upstream.

### Fase 3 · matriz por ISBN

Crear tabla:

`campo | valor DILVE actual | valor canónico | gravedad | owner | acción | estado`

Campos mínimos:

- ISBN;
- título;
- autor;
- editorial;
- formato;
- fecha;
- páginas;
- idioma;
- Thema;
- estado catálogo;
- disponibilidad;
- precio;
- derechos territoriales;
- portada;
- sinopsis;
- bio;
- producto relacionado/otra edición.

### Fase 4 · corregir upstream

Corregir mediante:

- Libros Indie;
- Monza;
- distribuidor autorizado;
- DILVE support cuando proceda.

No corregir primero Amazon/Casa del Libro/FNAC/TodosTusLibros si todos están repitiendo el mismo valor DILVE incorrecto.

### Fase 5 · propagación downstream

Después de corregir DILVE, comprobar:

- #407 TodosTusLibros;
- #410 retailers;
- #405 Google Books cuando corresponda;
- fichas editoriales;
- otros destinos que consuman DILVE/ONIX.

Registrar cuánto tarda en propagarse, sin asumir actualización instantánea.

## Casos que requieren especial atención

### Manecillas postlanzamiento

Como hoy es 2026-09-07, cualquier dato todavía marcado como lanzamiento futuro debe revisarse.

### Papel vs ebook

No mezclar:

- ISBN;
- fechas;
- formato;
- disponibilidad;
- precio;
- páginas;
- derechos territoriales.

### Nombre del autor

Debe ser consistente y con acentos correctos.

### Descripción

Comparar con copy editorial actual. No sustituir la sinopsis oficial por texto SEO inventado.

## Qué NO hacer

- No crear registros DILVE duplicados desde una cuenta personal.
- No solicitar ISBN nuevos para arreglar metadata.
- No sobrescribir un feed editorial sin ownership.
- No poner categorías Thema falsas por SEO.
- No publicar precios dinámicos como PVP permanente.
- No declarar disponibilidad global si solo se ha verificado España/Amazon.
- No usar el número de páginas de papel para ebook por comodidad.
- No borrar un libro porque esté descatalogado: DILVE indica que se debe actualizar su estado para que el cambio llegue a la cadena comercial.

## QA final

Por cada edición:

- [ ] identificación correcta;
- [ ] autor correcto;
- [ ] editorial correcta;
- [ ] formato correcto;
- [ ] fecha correcta;
- [ ] estado postlanzamiento correcto;
- [ ] disponibilidad coherente;
- [ ] precio/territorio coherentes;
- [ ] portada vigente;
- [ ] sinopsis vigente;
- [ ] Thema revisado;
- [ ] productos relacionados correctos;
- [ ] no duplicados;
- [ ] downstream spot-check realizado.

## Evidencia mínima de cierre

Guardar:

- fecha de consulta;
- ISBN;
- export/captura de campos relevantes;
- owner del feed;
- matriz de discrepancias;
- solicitud/ticket al publisher/DILVE;
- estado de propagación downstream;
- QA final.

No guardar credenciales ni exports con datos internos innecesarios.

## Criterio de cierre

### Todo correcto

`DILVE_OWNER_VERIFIED · ALL_RELEVANT_EDITIONS_PRESENT · CORE_METADATA_COHERENT · COMMERCIAL_STATUS_CURRENT · RICH_METADATA_REVIEWED · DOWNSTREAM_SPOTCHECK_DONE`

### Correcciones tramitadas

`DILVE_AUDITED · METADATA_ISSUES_DOCUMENTED · PUBLISHER_OR_DILVE_CORRECTION_REQUEST_OPENED · EXTERNAL_DEPENDENCY_RECORDED`

### Sin acceso

`DILVE_ACCESS_NOT_AVAILABLE · OWNER_IDENTIFIED · CORRECTION_MATRIX_PREPARED · PUBLISHER_ACTION_REQUESTED`

## Fuentes primarias consultadas · 2026-09-07

- https://web.dilve.es/ — alcance, integración y herramientas.
- https://web.dilve.es/dilve/dilve-para-editoriales/ — funciones editoriales/campos.
- https://web.dilve.es/herramientas/documentacion-herramientas/ — documentación, corrección autorías/comparativa ISBN.
- https://web.dilve.es/onix/estandar-versiones-editeur/ — ONIX 3.1.
- https://web.dilve.es/onix/documentacion-onix/ — documentación/listas ONIX actuales.
- https://web.dilve.es/grupo-de-trabajo-onix-thema/ — gobernanza sectorial.
- https://web.dilve.es/calidad-de-metadatos-2/metadatos/fecha-de-publicacion-y-estado-en-catalogo/ — fecha/estado.
- https://web.dilve.es/calidad-de-metadatos-2/metadatos/disponibilidad-y-fecha-de-disponibilidad/ — disponibilidad.
- https://web.dilve.es/calidad-de-metadatos-2/metadatos/derechos-de-venta/ — territorios/derechos.
- https://web.dilve.es/calidad-de-metadatos-2/metadatos/edicion/ — edición/reimpresión.
- https://web.dilve.es/dilve/dilve-para-distribuidoras/ — canal de incidencias y distribución.

Coordinación:

- #406 Agencia ISBN.
- #407 TodosTusLibros.
- #410 retailers.

Regla final: **si un dato incorrecto nace en DILVE/editorial, corregir el upstream antes de parchear cada librería por separado.**
