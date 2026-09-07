# TodosTusLibros — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#407 · `tracking/todostuslibros`**  
Estado: **RESEARCHED · SAMUEL_PUBLIC_RECORD_OBSERVED · MANECILLAS_PUBLIC_RECORD_NOT_OBSERVED · UPSTREAM_DILVE_OWNER_CONFIRMED · EXTERNAL_ACTION_PENDING**

## Objetivo

Comprobar cómo aparecen `Samuel entre mundos` y `Las manecillas del recuerdo` en TodosTusLibros y dejar claro qué debe corregirse en TodosTusLibros, qué debe corregirse realmente en DILVE/ISBN/editorial y qué información es puramente volátil (stock/precio/librerías).

La prioridad es evitar parches downstream: TodosTusLibros confirma expresamente que sus fichas bibliográficas proceden de la versión oficial del ISBN y que se incorporan automáticamente desde DILVE.

## Fuentes oficiales y públicas revisadas

- TodosTusLibros — qué es el servicio: `https://www.todostuslibros.com/servicios/quienes_somos`
- TodosTusLibros — política de privacidad y procedencia de fichas bibliográficas: `https://www.todostuslibros.com/pages/politica-de-privacidad`
- TodosTusLibros — editorial Libros Indie: `https://www.todostuslibros.com/editorial/libros-indie`
- DILVE: `https://web.dilve.es/`
- Agencia ISBN: `https://agenciaisbn.es/`
- Web oficial del autor: `https://davidportodiaz.com/`

## Cómo funciona TodosTusLibros actualmente

TodosTusLibros es propiedad de **CEGAL — Confederación Española de Gremios y Asociaciones de Librerías**.

La plataforma declara actualmente más de cuatro millones de referencias bibliográficas y utiliza la red de librerías para mostrar disponibilidad/compra.

Punto clave para cualquier corrección:

> Los datos de las fichas bibliográficas reproducidas en TodosTusLibros proceden de la versión oficial del ISBN y las fichas se incorporan automáticamente desde DILVE.

Consecuencia operativa:

- error en título/autor/editorial/formato/ISBN/etc. repetido en TSL y otros retailers → corregir **upstream**;
- stock o disponibilidad de una librería concreta → dato comercial volátil, no metadata bibliográfica;
- no abrir múltiples correcciones manuales si el origen es el feed.

## Datos canónicos de las obras

### Samuel entre mundos

- Autor: **David Porto Díaz**
- Editorial: **Libros Indie**
- ISBN: `9791387659776`
- Formato: tapa blanda
- Páginas canónicas del proyecto: **422**
- Año editorial: 2025
- Distribución comercial real observada: Amazon, Casa del Libro, TodosTusLibros/librerías y otros retailers.

### Las manecillas del recuerdo — papel

- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- ISBN: `9798905149351`
- Publicación editorial: **2026-09-03**
- PVP editorial documentado: **16 €**
- Páginas canónicas del proyecto: **272**, pendiente de reconciliar con fuentes comerciales que actualmente muestran **266**.

### Las manecillas del recuerdo — ebook

- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- Publicación: **2026-08-12**
- Precio observado en la autoridad web del proyecto: **2,99 €**; comprobar live antes de fijarlo en evidencia.

## Auditoría pública a 2026-09-07

### Samuel — registro observado

La página editorial de Libros Indie en TodosTusLibros muestra actualmente `SAMUEL ENTRE MUNDOS`.

Datos públicos observados en el resultado indexado:

- autor mostrado como `DAVID, PORTO DÍAZ`;
- editorial: Libros Indie;
- precio observado en la última captura pública del índice: **22,00 €**;
- disponibilidad: **alta**.

No congelar precio/stock: son datos volátiles.

### Punto a revisar: forma del nombre de autor

El nombre canónico es `David Porto Díaz`.

`DAVID, PORTO DÍAZ` puede ser solo una serialización bibliográfica invertida y no necesariamente un error de identidad. Antes de pedir corrección:

1. abrir la ficha individual;
2. comprobar si el frontend normaliza el nombre de otra forma;
3. comparar el contributor del feed DILVE/ISBN;
4. corregir solo si existe un error real de orden/campos, no por estilo visual de índice.

### Samuel — discrepancias externas ya detectadas

No atribuirlas automáticamente a TodosTusLibros, pero usarlas como señal para #404 DILVE:

- web oficial/proyecto: **422 páginas**;
- Casa del Libro: **412 páginas**;
- Bookish: **412 páginas**.

También hay diferencias públicas de fecha:

- año de edición 2025;
- Casa del Libro muestra lanzamiento 05/01/2026;
- Bookish muestra 01/01/2025.

La prioridad es determinar el dato bibliográfico oficial del producto físico y corregir upstream si procede.

## Manecillas — estado público actual

Las búsquedas públicas realizadas hoy no han devuelto una ficha inequívoca de TodosTusLibros para:

- `9798905149351`;
- `9798906781925`;
- título exacto + David Porto Díaz.

Estado correcto:

`PUBLIC_TODOSTUSLIBROS_RECORD_NOT_OBSERVED`

NO significa:

`NOT_IN_DILVE`

ni:

`NOT_DISTRIBUTED`

La edición ebook ya aparece públicamente en Casa del Libro con Monza, ISBN correcto y fecha 12/08/2026. La edición física aparece en otros retailers, por lo que hay distribución downstream observable.

## Hallazgo cruzado crítico de Manecillas

Agapea muestra actualmente para `Las manecillas del recuerdo`:

- Monza Ediciones;
- **266 páginas**;
- PVP **16,00 €**.

La autoridad interna/web del proyecto mantiene **272 páginas**.

Este gap debe tratarse como **metadata discrepancy**, no resolverse cambiando la web sin verificar el ejemplar/ficha editorial real.

Owner sugerido:

1. #428 Monza — confirmar edición física real;
2. #404 DILVE — confirmar page count transmitido;
3. #407 TSL — comprobar propagación;
4. #410 retailers — medir consistencia.

## Qué debe revisar Claude en TodosTusLibros

### Samuel

Buscar directamente por:

1. ISBN `9791387659776`;
2. título exacto;
3. autor `David Porto Díaz`.

Guardar:

- URL individual;
- título;
- autor mostrado;
- editorial;
- ISBN;
- formato;
- número de páginas si aparece;
- fecha/año;
- PVP;
- estado de disponibilidad;
- número aproximado de librerías con disponibilidad si el sitio lo muestra;
- portada;
- sinopsis;
- materias/categoría visibles;
- duplicados.

### Manecillas papel

Buscar:

- `9798905149351`;
- `Las manecillas del recuerdo`;
- `David Porto Díaz`.

Si no aparece:

1. comprobar #404 DILVE;
2. comprobar owner del feed con Monza;
3. NO crear ficha manual en TSL;
4. registrar `UPSTREAM_RECORD_PENDING/NOT_PROPAGATED` solo si la evidencia lo demuestra.

### Manecillas ebook

Buscar `9798906781925`.

No asumir que TodosTusLibros tenga que comercializar todos los ebooks del mismo modo que tiendas digitales. Clasificar según lo que realmente exponga la plataforma.

## Cómo corregir

### Error bibliográfico

Prioridad:

`editorial/distribuidor → DILVE/ISBN → TodosTusLibros → retailers`

No al revés.

### Error personal del nombre de autor

TodosTusLibros explica un canal de derechos personales vía CEGAL, pero la propia plataforma recomienda dirigirse preferentemente al origen ISBN/DILVE porque las fichas se sincronizan automáticamente.

No usar GDPR como sustituto de una corrección bibliográfica normal salvo que realmente sea un problema de dato personal.

### Disponibilidad/stock

Si una librería dice no disponible y otra disponible:

- no es necesariamente error;
- registrar fecha/hora;
- no pedir a DILVE que «corrija stock» salvo que el feed comercial tenga un problema documentado.

## QA de duplicados

Para cada ISBN:

- una ficha bibliográfica principal;
- no confundir distintas ediciones/formatos;
- título/autor consistentes;
- papel y ebook no deben mezclarse bajo el mismo ISBN;
- no pedir merge de registros distintos solo porque comparten título.

## Beneficio para la web/SEO

TodosTusLibros es una fuente externa relevante de ecosistema librero español, pero no debe tratarse como backlink que controlamos.

Si existe ficha correcta:

- mantener ISBN exacto en la web oficial;
- se puede añadir TSL como destino de “buscar en librerías” si UX/comercial lo justifica;
- no etiquetar disponibilidad permanente;
- no introducir precio/stock schema a partir de TSL sin ownership y actualización fiable.

## Criterio de cierre

### Samuel

`SAMUEL_RECORD_VERIFIED · BIBLIOGRAPHIC_FIELDS_RECONCILED · PAGE_COUNT_RESOLVED_OR_UPSTREAM_TICKET_RECORDED · DUPLICATES_REVIEWED`

### Manecillas

Uno de:

- `MANECILLAS_RECORDS_VERIFIED`
- `UPSTREAM_DILVE_PROPAGATION_PENDING`
- `EDITORIAL_FEED_DEPENDENCY_RECORDED`

### General

`TSL_SOURCE_CHAIN_CONFIRMED · NO_DOWNSTREAM_PATCHING · PUBLIC_QA_DONE`

## Evidencia mínima al cerrar

Guardar en la PR:

- fecha/hora;
- URLs exactas;
- ISBN consultados;
- capturas o transcripción de campos;
- librerías/stock solo como snapshot;
- diferencias detectadas;
- ticket/email upstream si existe;
- resultado tras propagación.

## Coordinación

- #404 — DILVE: metadata upstream.
- #406 — Agencia ISBN/registrant.
- #428 — Monza Ediciones.
- #429 — Libros Indie.
- #410 — retailers y disponibilidad.
- #422 — BNE/autoridad bibliográfica.

## Guardrails

- No declarar `NO_STOCK` como estado permanente.
- No confundir ISBN con disponibilidad comercial.
- No editar downstream si el error nace en DILVE.
- No cambiar la web oficial de 422/272 páginas solo porque un retailer diga otra cifra: resolver autoridad primero.
- No crear fichas duplicadas.
