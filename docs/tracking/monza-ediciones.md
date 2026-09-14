# Monza Ediciones — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07** (cierre de esta ronda: **2026-09-14**)  
PR owner: **#428 · `tracking/monza-ediciones`**  
Estado: **PAGE_COUNT_AND_PVP_CLOSED_NOT_ACTIONABLE_OWNER_DECISION · PUBLICATION_DATE_DISCREPANCY_DOCUMENTED_NOT_PURSUED · NO_MONZA_CONTACT_BY_OWNER_DECISION · CLOSED_THIS_ROUND**

## Cierre de esta ronda (2026-09-14)

### Decisión del propietario del proyecto sobre páginas y PVP

El propietario del proyecto ha decidido **cerrar sin más acción** la
discrepancia de páginas (272 en la autoridad del proyecto vs. 266 en
Amazon.es/Casa del Libro/Agapea): cada tienda cuenta páginas con su
propio criterio (con o sin guardas/portadillas), no es un dato que se
pueda "arreglar" de forma unívoca, y no vale la pena perseguir cinco
fuentes por una diferencia de conteo. Esto aplica también, por la misma
razón, a #404 (DILVE) y #429 (Libros Indie/Samuel: 422 vs 412). No se
va a corregir ni a preguntar más por esto en ninguno de los tres frentes.

Comprobación en vivo de hoy (Amazon.es, ASIN `B0HHY9MYLM`) confirma
además que el **PVP no es una discrepancia real**: Amazon.es vende la
edición física a **15,99 €** y el Kindle a **2,99 €**, exactamente los
valores que ya usa el proyecto. La cifra de "16,00 €" que aparecía en un
snapshot antiguo de Agapea no se ha reproducido hoy; se cierra como ruido
histórico, no como discrepancia vigente.

### Matriz de verdad (2026-09-14, evidencia en vivo)

| Campo | Nuestro dato | Dato externo confirmado hoy | Evidencia | Owner | Acción |
|---|---|---|---|---|---|
| Páginas (físico) | 272 | 266 | Amazon.es, Casa del Libro Colombia, Agapea (histórico) | — | **Cerrado, no accionable — decisión del propietario** |
| PVP físico | 15,99 € | 15,99 € | Amazon.es (ASIN B0HHY9MYLM), en vivo hoy | — | Sin discrepancia, cerrado |
| PVP Kindle | 2,99 € | 2,99 € | Amazon.es, en vivo hoy | — | Sin discrepancia, cerrado |
| **Fecha de publicación (físico)** | **2026-09-03** | **12 agosto 2026** | Amazon.es (ficha oficial del producto) y Casa del Libro Colombia, ambos en vivo hoy, coincidentes entre sí | Monza | **Abierto — preguntar a Monza cuál es la fecha real** |
| Encuadernación | tapa blanda (sin detalle) | Tapa blanda **con solapas** | Casa del Libro Colombia, en vivo hoy | Monza | Actualizar copy propio si Monza confirma |
| Dimensiones/peso | no documentado | 15.2 × 22.8 cm, 370 g (Casa del Libro); 15.19 × 1.7 × 22.81 cm (Amazon.es, incluye grosor de lomo) | en vivo hoy, ambas fuentes | Monza | Informativo, no urgente |
| Registrant ISBN 979-8 (ambos) | desconocido | no verificado hoy | — | Monza / agencia registrant | Preguntar a Monza |
| Owner DILVE/ONIX/feed comercial | desconocido | no verificado hoy — Monza es entidad británica (Companies House `SC839555`), no se debe asumir DILVE español como origen | — | Monza | Preguntar a Monza antes de tocar #404 |
| Depósito Legal (físico) | desconocido | ausente del catálogo BNE (ver #422), causa no verificada | catalogo.bne.es, en vivo hoy | Monza | Preguntar a Monza (ver #422) |
| Metadata oficial ebook | ver arriba | consistente con lo publicado hoy | Amazon.es/Casa del Libro | Monza | Sin acción |

La fecha de publicación es el único campo con una discrepancia real,
confirmada por dos fuentes independientes hoy mismo (no un hallazgo
antiguo sin repetir). El resto de preguntas a Monza (registrant ISBN,
owner DILVE/ONIX, Depósito Legal) siguen abiertas por falta de respuesta
de la editorial, no por evidencia contradictoria.

### Decisión final (2026-09-14): no se contacta a Monza esta ronda

No existe un canal editorial público de Monza Ediciones (sin web propia
indexada, sin email de contacto público; solo el registro de Companies
House `SC839555`, que es una dirección registral, no un canal editorial).
El propietario del proyecto ha decidido explícitamente **no perseguir un
contacto con Monza** para resolver esto ahora. Se cierra esta PR con la
discrepancia de fecha documentada como hallazgo, no como incidencia
abierta:

- fecha propia del proyecto: `2026-09-03`;
- fecha coincidente en Amazon.es + Casa del Libro: `12/08/2026`;
- no se ha corregido la web propia ni se ha escrito a nadie por esto;
- si en el futuro surge un canal real con Monza (contrato, renovación,
  nueva edición), es el momento natural para preguntar de paso, no antes.

### Qué NO se ha hecho

- No se ha contactado a Monza — decisión explícita del propietario, no
  falta de canal únicamente.
- No se ha cambiado ningún dato en la web propia — ni páginas, ni PVP,
  ni fecha.
- No se ha tocado #407 TodosTusLibros ni #410 retailers para Manecillas:
  no hay nada nuevo que propagar sin confirmación de Monza, y esa
  confirmación no se va a pedir esta ronda. #404 DILVE ya se cerró por
  separado (ver esa PR) por el mismo motivo.

## Objetivo

Dejar preparada una sesión con Monza Ediciones para revisar `Las manecillas del recuerdo` como publicación editorial real, corregir cualquier dato upstream y aprovechar la relación editorial para mejorar autoridad, distribución, enlaces y promoción sin inventar canales ni modificar downstream manualmente.

## Estado editorial verificable a 2026-09-07

`Las manecillas del recuerdo` figura públicamente asociada a **Monza Ediciones** en múltiples superficies independientes.

Datos canónicos del proyecto:

### Tapa blanda

- Título: `Las manecillas del recuerdo`
- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- ISBN: `9798905149351`
- Publicación editorial: **2026-09-03**
- PVP editorial documentado: **16 €**
- Páginas mantenidas actualmente por la web/autoridad del proyecto: **272**
- ASIN registrado por el proyecto: `B0HHY9MYLM`

### Ebook

- Editorial: Monza Ediciones
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- Fecha pública observada: **2026-08-12**
- Precio público observado: **2,99 €**

## Evidencia externa actual

### Casa del Libro — ebook

La ficha pública actual muestra:

- `LAS MANECILLAS DEL RECUERDO`
- autor: `PORTO DÍAZ DAVID`
- editorial: Monza Ediciones
- ISBN: `9798906781925`
- idioma: castellano
- lanzamiento: `12/08/2026`
- eBook EPUB con DRM
- precio observado: 2,99 €

La sinopsis coincide en sustancia con la descripción canónica del proyecto.

### Agapea — tapa blanda

Una página de novedades indexada ayer muestra actualmente:

- `Las Manecillas Del Recuerdo`
- Monza Ediciones
- **266 páginas**
- PVP **16,00 €**

Este es el principal gap factual de la auditoría.

## Discrepancia crítica: 272 vs 266 páginas

La web oficial del autor mantiene actualmente **272 páginas** para la edición impresa.

Agapea muestra **266**.

NO corregir ninguna superficie por intuición.

### Claude debe verificar la autoridad física real

Orden recomendado:

1. ejemplar final de producción / colofón;
2. metadata oficial de Monza;
3. ficha ONIX/DILVE si existe;
4. ISBN/registrant metadata;
5. retailers.

Resultados posibles:

- ejemplar = 272 → corregir Monza/feed si distribuye 266;
- ejemplar = 266 → corregir web oficial/press kit/metadata propia;
- distintas tiradas/ediciones → documentar cada ISBN/edición por separado.

No asumir que 6 páginas de diferencia sean “guardas” o front/back matter sin comprobar el ejemplar.

## Situación pública de Monza

Las búsquedas realizadas hoy no han localizado una ficha editorial pública inequívoca en una web propia de Monza para David Porto Díaz o `Las manecillas del recuerdo`.

Estado correcto:

`PUBLIC_MONZA_BOOK_PAGE_NOT_OBSERVED`

Esto NO significa que Monza no tenga web, backend, catálogo privado, redes o material no indexado.

Existe evidencia pública independiente de que Monza Ediciones inició actividad editorial en 2025 y de que la sociedad `MONZA EDICIONES LTD` figura activa en Reino Unido con actividad de publicación de libros. Esto sirve para identificación institucional, no para inferir contratos o derechos concretos de David.

Fuentes públicas:

- La Voz de Galicia, 20/05/2025: nacimiento de Monza Ediciones.
- Companies House: `MONZA EDICIONES LTD`, company number `SC839555`, active; SIC incluye `58110 - Book publishing`.

## Hallazgo de ISBN coordinado con #406

Los dos ISBN de Manecillas empiezan por `979-8`.

La International ISBN Agency asigna ese registration group a Estados Unidos.

Consecuencia:

- no asumir que la Agencia ISBN española mantiene esos registros;
- identificar el registrant real;
- Monza puede ser editorial pública sin ser necesariamente el registrant ISBN;
- si un dato duro está mal, corregirlo con quien controla el registro/feed real.

## Qué debe pedir/revisar Claude con Monza

### Identidad editorial

- nombre exacto del sello que debe mostrarse públicamente;
- URL oficial de Monza, si existe;
- email/contacto editorial autorizado para metadatos;
- distributor/metadata provider;
- owner de DILVE/ONIX;
- registrant de ambos ISBN;
- ownership de fichas Amazon/ebook/papel.

### Tapa blanda

Confirmar:

- ISBN;
- ASIN;
- título exacto;
- autor exacto;
- fecha 03/09/2026;
- PVP;
- page count real;
- dimensiones;
- encuadernación;
- portada final;
- sinopsis final;
- idioma;
- Thema/BISAC si existe;
- disponibilidad/distribución;
- territorios;
- retailer URLs autorizadas.

### Ebook

Confirmar:

- ISBN `9798906781925`;
- ASIN `B0HHM71F46`;
- fecha 12/08/2026;
- formato real distribuido;
- DRM según canal;
- territorios/derechos;
- precio actual solo como snapshot;
- si Amazon/otros retailers reciben metadata de Monza, distribuidor o plataforma técnica.

## Distribución — no inventar

Hoy hay evidencia pública de:

- Amazon/Kindle mediante la web oficial del autor;
- Casa del Libro para ebook;
- Agapea para la edición física;
- otros canales se revisarán en #410.

No escribir en la PR “distribuido en todas las librerías”, “POD”, “DILVE confirmado” o similar hasta que Monza lo confirme o exista evidencia técnica.

## Autoridad y backlinks — oportunidad concreta

Si Monza dispone de web pública/catalogue page, interesa que la ficha contenga:

- nombre canónico `David Porto Díaz`;
- ficha completa del libro;
- enlace a `https://davidportodiaz.com/` o a la ficha canónica de Manecillas;
- press kit si editorialmente útil;
- eventos/firma solo si están vigentes;
- foto/bio actualizadas.

Esto debe plantearse como mejora editorial/UX, no como petición de “backlink SEO” artificial.

## Bio corta preparada

Usar solo si Monza solicita copy:

> David Porto Díaz es escritor nacido en Pontevedra y residente en Madrid. Es autor de `Samuel entre mundos` (Libros Indie, 2025) y `Las manecillas del recuerdo` (Monza Ediciones, 2026). En 2026 obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue Top 10 finalista del I Premio de Literatura Infantil Juan Andrés Teno.

No atribuir esos reconocimientos a Manecillas ni Samuel salvo fuente que lo haga expresamente.

## Sinopsis

La sinopsis pública de Casa del Libro para el ebook es coherente con el concepto canónico: novela coral conectada por un reloj que cambia de manos y acumula memoria, pérdida, culpa, familia y tiempo.

Si Monza mantiene una sinopsis oficial distinta, la editorial debe ser autoridad para retailers; la web del autor puede adaptar copy editorial sin crear contradicción factual.

## Correcciones: owner matrix

| Gap | Owner primario | Segundo paso |
|---|---|---|
| Page count | Monza / ejemplar físico | DILVE/retailers/web oficial |
| ISBN registrant | registrant real | Monza/autor documentan |
| Autor mal escrito en retailers | metadata upstream | retailer tras propagación |
| Sinopsis incorrecta | Monza/distribuidor | DILVE/retailer |
| Precio | Monza/canal | no congelar en web sin estrategia |
| Formato papel+ebook | owner por canal | Amazon/retailer |
| Portada | Monza/distribuidor | downstream |
| Enlace web del autor | Monza web/editorial | QA público |

## Checklist de ejecución para Claude

### Paso 1 — contacto/owner

- identificar canal real con Monza;
- preguntar quién controla metadata;
- confirmar si existe DILVE/ONIX;
- confirmar registrant ISBN;
- confirmar distribución actual.

### Paso 2 — reconciliar producto físico

- inspeccionar ejemplar;
- resolver 272 vs 266;
- guardar evidencia.

### Paso 3 — comparar downstream

Revisar:

- Amazon;
- Casa del Libro;
- Agapea;
- TodosTusLibros;
- FNAC/ECI y resto en #410.

### Paso 4 — autoridad/editorial

Si Monza tiene perfil público:

- bio;
- foto;
- ficha de libro;
- enlace a web oficial;
- press kit;
- menciones/eventos útiles.

### Paso 5 — solicitar correcciones

Enviar una única matriz clara:

`campo | actual | correcto | evidencia | owner | destino`

Evitar emails separados por cada retailer.

## Criterio de cierre

`MONZA_OWNER_IDENTIFIED · PAPER_METADATA_VERIFIED · EBOOK_METADATA_VERIFIED · PAGE_COUNT_RESOLVED · DISTRIBUTION_CHANNELS_DOCUMENTED · UPSTREAM_CORRECTIONS_SENT_OR_NOT_NEEDED · AUTHOR_BOOK_PUBLIC_PRESENCE_QA_DONE`

Si falta control externo:

`EXTERNAL_DEPENDENCY_RECORDED`

No cerrar como `COMPLETE` solo porque Casa del Libro tenga el ebook correcto.

## Evidencia mínima

- fecha/hora;
- contacto/canal usado sin publicar datos privados innecesarios;
- metadata oficial recibida;
- ISBN/ASIN;
- page count verificado;
- URLs retailer;
- ticket/email de corrección;
- fecha de propagación;
- screenshots antes/después cuando existan.

## Coordinación

- #406 — registrant ISBN.
- #404 — DILVE/ONIX.
- #407 — TodosTusLibros.
- #410 — retailers.
- #396 — Amazon Author Central.
- #411/#412 — Apple/Kobo si la distribución digital lo permite.

## Guardrails

- No inventar contrato ni derechos.
- No afirmar DILVE hasta verificarlo.
- No crear ISBN nuevo para arreglar metadata.
- No usar precio/stock como dato permanente.
- No cambiar page count canónico hasta resolver el ejemplar/metadata real.
- No publicar emails privados internos de Monza en documentación pública si no son contactos oficiales.
