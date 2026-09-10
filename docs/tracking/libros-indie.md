# Libros Indie — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#429 · `tracking/libros-indie`**  
Estado: **RESEARCHED · PUBLISHER_PUBLIC_SITE_CONFIRMED · SAMUEL_DOWNSTREAM_RECORDS_CONFIRMED · PAGE_COUNT_DISCREPANCY_CONFIRMED · EXTERNAL_ACTION_PENDING**

## Objetivo

Auditar la presencia editorial de `Samuel entre mundos` y de David Porto Díaz en Libros Indie, separar los datos que controla la editorial de los que muestran terceros y dejar preparada una única solicitud de corrección/enriquecimiento que pueda propagarse a DILVE/retailers sin parches repetidos.

## Identidad editorial actual

Libros Indie mantiene una web pública activa:

- `https://librosindie.net/`
- catálogo: `https://librosindie.net/catalogo-editorial/`
- contacto oficial: `https://librosindie.net/contacto/`

La editorial se define como sello especializado en autores independientes y mantiene un catálogo editorial público.

La **Federación de Gremios de Editores de España** muestra actualmente a Libros Indie como miembro de la Asociación de Editores de Andalucía y enlaza su web oficial.

Fuente institucional actual:

`https://federacioneditores.org/editoriales/libros-indie/`

Esto es autoridad institucional útil para identificar correctamente el publisher; no debe usarse para inferir distribución concreta de Samuel.

## Contacto público actual

La web oficial publica actualmente:

- `info@librosindie.net`

La ficha institucional de Federación de Editores muestra:

- `admin@librosindie.net`

Usar el canal que corresponda al asunto; para metadata de un libro ya publicado, empezar por el contacto editorial conocido del contrato/proyecto si existe y no publicar conversaciones privadas en la PR.

## Samuel entre mundos — datos canónicos del proyecto

- Título: `Samuel entre mundos`
- Autor: **David Porto Díaz**
- Editorial: **Libros Indie**
- ISBN: `9791387659776`
- Formato: tapa blanda
- Año editorial: **2025**
- Páginas mantenidas por la web/autoridad del proyecto: **422**
- No existe edición ebook autorizada/documentada actualmente.

## Evidencia comercial pública actual

### TodosTusLibros

La página de editorial Libros Indie incluye actualmente `SAMUEL ENTRE MUNDOS`.

Datos observados en el resultado público indexado:

- autor: `DAVID, PORTO DÍAZ`;
- editorial: Libros Indie;
- precio observado: 22,00 €;
- disponibilidad alta.

Precio/stock son snapshots, no datos permanentes.

### Casa del Libro

La ficha pública actual muestra:

- título: Samuel entre mundos;
- autor: David Porto Diaz;
- editorial: Libros Indie;
- ISBN: `9791387659776`;
- castellano;
- **412 páginas**;
- tapa blanda;
- fecha de lanzamiento: **05/01/2026**;
- año de edición: **2025**;
- plaza de edición: Sevilla.

### Bookish

La ficha pública muestra:

- Libros Indie (2025);
- ISBN `9791387659776`;
- **412 páginas**;
- fecha pública `01/01/2025`.

## Gap principal: 422 vs 412 páginas

La web oficial del autor y varios recursos internos/canónicos mantienen **422 páginas**.

Casa del Libro y Bookish muestran **412**.

Este patrón en dos retailers independientes sugiere que **412 puede venir del feed upstream**, pero no demuestra que sea el dato correcto.

Antes de tocar la web del autor o pedir correcciones downstream:

1. inspeccionar el ejemplar físico final;
2. comprobar colofón/ficha de producción de Libros Indie;
3. comprobar DILVE/ISBN;
4. determinar si 412 es metadata enviada por la editorial/distribuidor;
5. corregir una sola vez en la fuente verdadera.

Resultados:

- físico = 422 → pedir a Libros Indie/DILVE corregir 412;
- físico = 412 → corregir web oficial/press kit/clubes/JSON-LD;
- si existen tiradas/ediciones diferentes → cada una debe tener identidad/ISBN propios cuando corresponda.

No explicar la diferencia como “páginas en blanco/guardas” sin evidencia.

## Gap de fechas

Se observan simultáneamente:

- año editorial: 2025;
- Casa del Libro: lanzamiento 05/01/2026;
- Bookish: 01/01/2025;
- la web del proyecto presenta la publicación como 2025 en las superficies principales.

Esto puede ser diferencia entre:

- año de edición;
- fecha de puesta a la venta;
- fecha técnica cargada por retailer;
- placeholder de fecha.

Claude debe pedir/confirmar con Libros Indie la fecha bibliográfica/comercial que debe transmitirse y no uniformar retailers por intuición.

## Nombre de autor

El nombre público canónico es `David Porto Díaz`.

Variantes observadas:

- `DAVID, PORTO DÍAZ` en TodosTusLibros;
- `DAVID PORTO DIAZ` en Casa del Libro/Bookish.

La pérdida de tildes puede ser normalización del retailer. La inversión `DAVID, PORTO DÍAZ` puede ser serialización de apellido/nombre.

Solo pedir corrección si el contributor ONIX está estructuralmente mal (p. ej. nombre/apellido intercambiados), no por capitalización visual.

## Ficha pública de Libros Indie

Las búsquedas públicas/indexadas realizadas hoy no han localizado inequívocamente una URL individual actual de Samuel dentro de `librosindie.net`, aunque el catálogo general de la editorial está activo y terceros identifican Libros Indie como publisher.

Estado:

`PUBLIC_PUBLISHER_BOOK_URL_NOT_OBSERVED_WITH_CURRENT_SEARCH`

No significa que no exista.

Claude debe usar el buscador/catálogo interno de Libros Indie y, si existe ficha:

- guardar URL;
- verificar metadata;
- pedir que sea indexable/canonical si editorialmente procede;
- evitar crear otra ficha duplicada.

## Perfil de autor / autoridad

Si Libros Indie dispone de página de autor, debería contener como mínimo:

- `David Porto Díaz`;
- bio actual;
- Samuel entre mundos;
- enlace a web oficial si la política editorial lo admite.

No he localizado hoy una página pública inequívoca de autor en el sitio.

Esto es una oportunidad razonable para preguntar a la editorial, no una obligación ni un derecho contractual asumido.

## Bio actual preparada

Si la editorial solicita actualización:

> David Porto Díaz es escritor nacido en Pontevedra y residente en Madrid. Debutó con `Samuel entre mundos` (Libros Indie, 2025), novela de fantasía juvenil ambientada en Noveris. En 2026 publicó `Las manecillas del recuerdo` con Monza Ediciones. Ese mismo año obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue Top 10 finalista del I Premio de Literatura Infantil Juan Andrés Teno.

No decir que Samuel ganó esos premios.

## Sinopsis

La sinopsis que circula actualmente por Casa del Libro y Bookish empieza con la medalla que “late” y la grieta en Noveris; parece una versión editorial coherente con el posicionamiento actual de la obra.

Claude debe confirmar si es la sinopsis oficial vigente de Libros Indie.

Si se actualiza:

- hacerlo upstream;
- después esperar propagación;
- no mantener cinco sinopsis retailer divergentes manualmente.

## Distribución

Evidencia actual de presencia:

- TodosTusLibros;
- Casa del Libro;
- Bookish;
- Amazon según web oficial del autor;
- librerías físicas mediante ISBN según disponibilidad.

No convertir esta lista en afirmación exhaustiva de distribución contractual.

Preguntar a Libros Indie:

- distribuidor actual;
- owner DILVE/ONIX;
- territorios;
- print-on-demand si aplica realmente;
- condiciones de reposición/stock para librerías;
- canales autorizados.

## DILVE / ISBN

#406 ha confirmado que `9791387659776` pertenece al grupo `979-13`, asignado a España.

Esto hace especialmente importante coordinar:

`Libros Indie → Agencia ISBN/DILVE → TodosTusLibros/retailers`

Si 412 páginas o una fecha incorrecta viven en DILVE, Libros Indie/owner upstream debe corregirlo allí.

## Oportunidades editoriales útiles

Sin pedir “SEO” de forma artificial, se puede solicitar si la editorial lo ve adecuado:

- enlace desde ficha de autor/libro a `https://davidportodiaz.com/`;
- enlace al capítulo gratuito;
- press kit;
- guía de clubes de lectura;
- noticia/archivo de Feria del Libro de Madrid 2026;
- actualización de bio con segunda novela publicada;
- eventos futuros reales.

La relación editorial es una fuente natural de autoridad si el contenido aporta al lector.

## Material preparado para la editorial

### Web oficial

`https://davidportodiaz.com/`

### Samuel

`https://davidportodiaz.com/libros/samuel-entre-mundos/`

### Capítulo 1

`https://davidportodiaz.com/fragmento/`

### Clubes de lectura

`https://davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/`

### Prensa

Usar el press kit actual del sitio, no adjuntos antiguos si existe una versión más reciente.

## Checklist de Claude

### 1. Abrir ficha editorial real

- buscar ISBN;
- título;
- autor;
- catálogo interno.

### 2. Confirmar metadata de producción

- page count;
- fecha;
- PVP;
- dimensiones;
- portada;
- sinopsis;
- Thema/BISAC;
- contributor;
- ISBN.

### 3. Identificar owner

- quién sube DILVE/ONIX;
- distribuidor;
- quién puede corregir metadata.

### 4. Reconciliar discrepancias

Crear tabla:

`campo | web autor | ejemplar | Libros Indie | DILVE | TSL | Casa | Bookish | correcto`

### 5. Pedir una sola corrección upstream

No tickets separados a cada librería si el feed es común.

### 6. Authority/enlaces

- página de autor si existe;
- ficha del libro;
- enlace web oficial;
- bio actualizada;
- recursos para lectores si editorialmente útiles.

### 7. QA final

Tras propagación:

- TSL;
- Casa del Libro;
- Bookish;
- Amazon;
- web oficial.

## Criterio de cierre

`PUBLISHER_BOOK_RECORD_VERIFIED · PAGE_COUNT_RESOLVED · PUBLICATION_DATE_RECONCILED · DILVE_OWNER_IDENTIFIED · DOWNSTREAM_METADATA_CHECKED · AUTHOR_PROFILE_OR_NOT_APPLICABLE · LINK_OPPORTUNITY_RESOLVED · EXTERNAL_CORRECTIONS_SENT_OR_NOT_NEEDED`

## Evidencia mínima

- URL de ficha editorial;
- captura/copia metadata;
- confirmación page count;
- fecha correcta;
- owner DILVE;
- email/ticket de corrección si procede;
- comprobación downstream posterior.

## Coordinación

- #404 — DILVE.
- #406 — Agencia ISBN.
- #407 — TodosTusLibros.
- #410 — retailers.
- #397 — Goodreads.
- #402/#403 — catálogos lectores/bibliográficos.

## Guardrails

- No afirmar que Libros Indie controla cada retailer.
- No congelar stock/precio.
- No corregir 422→412 o viceversa sin ejemplar/metadata de producción.
- No atribuir premios del autor a Samuel.
- No pedir una edición ebook de Samuel: no existe como producto autorizado actualmente.
- No publicar datos contractuales privados en la PR.
