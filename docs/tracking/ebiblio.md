# eBiblio — bibliotecas públicas digitales españolas

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · NATIONAL_SERVICE_ACTIVE · MADRID_ACQUISITION_ROUTE_CONFIRMED · MANECILLAS_PRIORITY · READY_FOR_EXECUTION`

## Objetivo

Comprobar si `Las manecillas del recuerdo` está disponible en eBiblio y, si no, determinar la vía real y gratuita para que Monza/la cadena de distribución la haga adquirible por las bibliotecas públicas digitales españolas.

Para `Samuel entre mundos`, no inventar una edición digital: solo avanzar si existe una edición ebook legítima o Libros Indie confirma un canal aplicable.

## Por qué esta PR sí merece prioridad

El Ministerio de Cultura publicó en marzo de 2026 las cifras de eBiblio 2025:

- **59.222 títulos distintos**;
- **700.736 licencias**;
- **239.502 usuarios únicos**;
- alrededor de **4,8 millones de préstamos** durante 2025.

El servicio está coordinado por la Subdirección General de Coordinación Bibliotecaria del Ministerio de Cultura junto a las comunidades y ciudades autónomas.

Fuente oficial:

- https://www.cultura.gob.es/cultura/bibliotecas/noticias/2026/ebiblio-en-cifras-2025.html

Esto convierte eBiblio en una superficie de lectura real y relevante en España, no en un directorio marginal.

## eBiblio Madrid — canal concreto

La ayuda oficial de eBiblio Madrid confirma actualmente:

> Las novedades editoriales se incluyen en los pedidos habituales de eBiblio.

Y permite a los lectores proponer adquisiciones desde el área de usuario del Catálogo de Bibliotecas Públicas de Madrid, con **una propuesta de adquisición por persona y mes**.

Fuente:

- https://madrid.ebiblio.es/about

Además mantiene formulario de contacto con campo específico `Sugerencia de compra` y `Título o ISBN del libro`:

- https://madrid.ebiblio.es/remarks/new

No utilizar esto para pedir a amigos/lectores que hagan campañas coordinadas. La opción existe para una recomendación legítima de adquisición, no para manipular el catálogo.

## Catálogo actual

eBiblio Madrid mantiene un catálogo activo con decenas de miles de títulos para adultos y miles de ebooks/audiolibros. La interfaz permite filtrar por:

- ebook/audiobook;
- idioma;
- fecha;
- disponibilidad;
- público;
- accesibilidad;
- adquisiciones recientes.

La presencia puede variar por comunidad autónoma y por licencias adquiridas.

## Diferencia esencial: distribución vs adquisición

Hay tres estados distintos:

1. **el publisher/distribuidor ofrece el ebook al circuito bibliotecario**;
2. **eBiblio/comunidad puede adquirir la licencia**;
3. **una comunidad concreta ya la ha comprado y ofrece préstamos**.

No confundirlos.

Que Manecillas no aparezca en Madrid no demuestra que no esté disponible para compra institucional ni que no exista en otra eBiblio autonómica.

## Las manecillas del recuerdo

Edición digital legítima:

- autor: David Porto Díaz;
- editorial: Monza Ediciones;
- ISBN ebook: `9798906781925`;
- ASIN Amazon: `B0HHM71F46`;
- publicación: 2026-08-12;
- idioma: castellano.

Esta es la prioridad.

### Claude debe comprobar

1. búsqueda en eBiblio Madrid por ISBN/título/autor;
2. búsqueda en el portal eBiblio de Galicia si el acceso/catálogo público lo permite;
3. una muestra adicional razonable de catálogos autonómicos, no las 17 comunidades manualmente si el resultado upstream ya está claro;
4. si aparece, revisar metadata/licencia;
5. si no aparece, preguntar a Monza/distribuidor si el ebook está disponible para adquisición en eBiblio/bibliotecas españolas;
6. identificar agregador/feed real;
7. si la edición ya es adquirible pero Madrid no la tiene, valorar una **única propuesta de adquisición legítima** desde la cuenta de biblioteca de David si cumple condiciones.

## Samuel entre mundos

Actualmente el proyecto no documenta una edición ebook comercial/autorizada.

Por tanto:

- buscar por título/ISBN físico solo para saber si existe alguna ficha inesperada;
- no subir archivos propios;
- no crear edición digital;
- no pedir adquisición de un ebook inexistente;
- continuar únicamente si #429 Libros Indie confirma un formato digital legítimo.

## Metadata a auditar si Manecillas aparece

- título;
- David Porto Díaz;
- ISBN `9798906781925`;
- Monza Ediciones;
- idioma;
- formato;
- fecha;
- portada;
- sinopsis;
- categorías/materias;
- accesibilidad si se declara;
- modelo/estado de licencia cuando sea visible.

No usar eBiblio para decidir páginas o precio comercial de Amazon.

## Vía correcta si hay errores

Si la ficha recibe metadata incorrecta:

1. identificar si procede de Monza/agregador;
2. corregir upstream;
3. esperar propagación;
4. usar soporte eBiblio solo si el dato permanece incorrecto o es un error local del catálogo.

Coordinar con:

- #428 Monza;
- #404 DILVE/ONIX;
- #433 OverDrive/Libby;
- #410 retailers solo como comparación, no como owner de eBiblio.

## Oportunidad para la web

Solo si Manecillas llega a estar realmente disponible en eBiblio:

- valorar una mención secundaria `Disponible también en bibliotecas digitales`;
- enlazar al catálogo concreto solo si la URL es estable/útil;
- mejor ubicación: ficha del libro, clubs de lectura o recursos para lectores;
- no sustituir CTA de compra ni presentarlo como disponible en toda España si solo lo está en una comunidad.

Puede ser especialmente útil para clubs de lectura y lectores que prefieren préstamo bibliotecario.

## Seguimiento de impacto

Si se consigue inclusión:

- registrar comunidad/catálogo;
- fecha de incorporación;
- tipo de formato;
- URL;
- si existe una forma pública de observar disponibilidad/reservas, guardarla solo como snapshot;
- no presentar número de préstamos como dato estable si no es público/fiable.

## Guardrails

- cero gasto de David;
- no campañas coordinadas de sugerencias;
- no distribución paralela contra derechos de Monza;
- no subir EPUB del libro completo sin autorización;
- no confundir catálogo nacional con adquisición autonómica;
- no inventar ebook de Samuel.

## Criterio de cierre

`MANECILLAS_EBIBLIO_SEARCHED · AUTONOMIC_AVAILABILITY_REVIEWED · PUBLISHER_LIBRARY_DISTRIBUTION_OWNER_IDENTIFIED · ACQUISITION_ROUTE_CONFIRMED · SINGLE_LEGITIMATE_REQUEST_SENT_IF_USEFUL · METADATA_CORRECT_OR_UPSTREAM_REQUESTED · SAMUEL_DIGITAL_STATUS_DOCUMENTED · WEB_LINK_ADDED_ONLY_IF_REAL · ZERO_COST`
