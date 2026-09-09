# StoryGraph — perfil público, autoría y ediciones

Fecha de investigación: **2026-09-07**  
PR owner: **#399 · `tracking/storygraph`**  
Estado: **SAMUEL_EXISTS_USER_ADDED · PAGE_COUNT_DISCREPANCY_NEW_DATA_POINT · MANECILLAS_MISSING · NEEDS_STORYGRAPH_ACCOUNT**

## Verificación directa (2026-09-08)

- `Samuel entre mundos` **ya existe** en StoryGraph, marcado
  `user-added` (alguien lo dio de alta manualmente, probablemente el
  propio autor o un lector): tapa blanda, 2025, género `fiction fantasy`.
- **Nuevo dato para la discrepancia de páginas ya abierta en #429/#404**:
  aquí figuran **409 páginas** — un TERCER número distinto de los 422/412
  ya documentados en otras fuentes. Cuantas más fuentes se comprueban,
  más varía la cifra; refuerza que hace falta que la editorial (Libros
  Indie) confirme el número real antes de intentar unificar nada.
- `Las manecillas del recuerdo`: búsqueda directa sin resultados — **no
  existe todavía** en StoryGraph.

Añadir Manecillas o corregir la página de Samuel requiere una cuenta de
StoryGraph — no se ha intentado crear ninguna ni editar nada de forma
anónima. Como ya señalaba este documento, StoryGraph todavía no ofrece
un programa de autor equivalente a Goodreads/Amazon, así que cualquier
alta se hace como una edición de catálogo normal, no como "reclamar
perfil".

## Objetivo

Dejar `Samuel entre mundos` y `Las manecillas del recuerdo` correctamente representados en The StoryGraph, con sus ediciones reales, ISBN, formatos, portadas y autoría, sin crear duplicados ni perder tiempo intentando “reclamar” una Author Page que la plataforma todavía no ofrece como Goodreads/Amazon.

Perfil público ya registrado en el repo:

- https://app.thestorygraph.com/profile/david_porto

Ese URL es un **perfil de usuario/lector**. Puede servir como identidad social pública si realmente pertenece a David, pero no debe confundirse con una Author Page reclamada.

## Hallazgo importante: StoryGraph todavía no tiene un Author Program equivalente

La roadmap pública de StoryGraph mantiene **Author pages** como trabajo `Medium-term` a 2026 y sigue describiendo mejoras futuras alrededor de perfiles/autores verificados.

Consecuencia:

- no buscar un flujo inexistente de `Claim Author Profile`;
- no pagar ni abrir tickets preguntando por un programa que todavía no está publicado;
- concentrar esta PR en **book data + editions + author attribution + perfil público del usuario**.

Fuente oficial/roadmap:

- https://roadmap.thestorygraph.com/requests-ideas/posts/author-pages

## Cómo funciona actualmente el catálogo

StoryGraph permite:

- buscar libros por título/autor/ISBN;
- añadir un libro manualmente si no existe;
- añadir una **edición nueva** desde la familia de un libro existente;
- cambiar de edición/formato;
- reportar información incorrecta o una edición mal agrupada;
- recurrir a volunteer librarians para corregir datos que un usuario normal no puede editar.

Fuentes oficiales:

- https://thestorygraph.freshdesk.com/support/solutions/articles/79000141991-how-to-add-a-new-book-or-new-edition-to-storygraph
- https://thestorygraph.freshdesk.com/support/solutions/articles/79000141927-switching-editions-formats-on-the-storygraph
- https://thestorygraph.freshdesk.com/support/solutions/articles/79000141981-become-a-storygraph-volunteer-librarian

## Regla crítica: libro vs edición

Para Manecillas:

- **obra/familia** = `Las manecillas del recuerdo`;
- papel = una edición;
- Kindle/ebook = otra edición.

Si ya existe la obra, NO usar `Add a Book` para el segundo formato. Abrir **Editions → Add Edition** para que herede título/autor y quede dentro de la misma familia.

StoryGraph confirma que, al añadir una edición desde `Editions`, pre-rellena gran parte de los datos y pide principalmente los propios de esa edición: ISBN, page count, cover, etc.

Esto evita el error histórico de crear dos libros independientes para papel/ebook.

## Datos canónicos preparados

### Samuel entre mundos · papel

- título: `Samuel entre mundos`
- autor: `David Porto Díaz`
- editorial: `Libros Indie`
- ISBN: `9791387659776`
- formato: paperback / print
- páginas canónicas actuales del proyecto: `422`
- publicación editorial: 2025
- idioma: Spanish
- portada: portada oficial actual de la web
- URL oficial: `https://davidportodiaz.com/libros/samuel-entre-mundos/`

### Las manecillas del recuerdo · papel

- título: `Las manecillas del recuerdo`
- autor: `David Porto Díaz`
- editorial: `Monza Ediciones`
- ISBN: `9798905149351`
- ASIN: `B0HHY9MYLM` — solo referencia Amazon, no sustituir ISBN
- formato: paperback / print
- páginas canónicas actuales del proyecto: `272`, todavía coordinado con #428/#404 por discrepancias de retailers
- publicación: `2026-09-03`
- PVP actual del proyecto/Amazon: `15,99 €` — **StoryGraph no necesita este precio como dato bibliográfico**
- idioma: Spanish
- portada: portada editorial oficial
- URL oficial: `https://davidportodiaz.com/las-manecillas-del-recuerdo/`

### Las manecillas del recuerdo · Kindle/ebook

- título: `Las manecillas del recuerdo`
- autor: `David Porto Díaz`
- editorial: `Monza Ediciones`
- ISBN: `9798906781925`
- ASIN: `B0HHM71F46`
- formato: digital / ebook
- publicación: `2026-08-12`
- precio actual: `2,99 €` — no es necesario para la ficha bibliográfica
- idioma: Spanish
- misma obra/familia que papel

No copiar `272 páginas` a la edición digital si StoryGraph pide page count y no tenemos una fuente editorial clara para el equivalente digital.

## Primera operación: inventario, no creación

Claude debe entrar autenticado y buscar, en este orden:

1. `9791387659776`
2. `9798905149351`
3. `9798906781925`
4. `Samuel entre mundos David Porto Díaz`
5. `Las manecillas del recuerdo David Porto Díaz`

Para cada resultado guardar:

- URL StoryGraph;
- internal book/edition UUID si aparece en URL;
- family/book principal;
- edición exacta;
- ISBN;
- format;
- publisher;
- publication date;
- page count;
- language;
- cover;
- description/blurb;
- author attribution;
- si está agrupada con otras ediciones.

No crear nada hasta completar los tres ISBN.

## Casos posibles

### A. Obra + edición ya correctas

`NO_ACTION`.

No “mejorar” por estética si el registro ya identifica correctamente la edición.

### B. Obra existe, edición concreta falta

Usar:

`Editions → Add Edition`

No `Add a Book`.

### C. No existe ninguna obra

Solo entonces usar `Add a Book`:

- https://app.thestorygraph.com/books/new

Después añadir el segundo formato desde Editions.

### D. ISBN ya ocupado por edición incorrecta

No intentar reutilizarlo creando otra edición. StoryGraph tiene restricciones cuando un ISBN ya está asignado.

Usar `Report missing/incorrect book information` / soporte/librarians e indicar:

- URL incorrecta;
- ISBN;
- qué campo está mal;
- fuente correcta;
- URL oficial/editorial.

La roadmap de 2025–2026 sigue registrando problemas/casos de ISBN bloqueados por ediciones incorrectas, por lo que esta ruta de corrección es preferible a duplicar.

### E. Papel y Kindle aparecen como dos libros independientes

No borrarlos ni crear un tercero.

Abrir ticket indicando que deben ser **editions de la misma book family** y aportar los dos URLs/ISBN.

## Autoría

Comprobar que las fichas usan exactamente:

`David Porto Díaz`

No aceptar por defecto:

- `David Porto Diaz` si StoryGraph permite tildes correctamente;
- `David Porto`;
- otro autor homónimo;
- perfil de usuario como sustituto de author entity.

Si la autoría está mal y el usuario normal no puede editarla, StoryGraph indica que ciertos campos requieren librarian/support.

No crear un autor duplicado por una tilde sin reportar primero el registro existente.

## Portadas

StoryGraph permite aportar cover al añadir una edición.

Usar:

- Samuel → portada editorial oficial actual;
- Manecillas → portada editorial oficial actual.

No usar:

- mockups 3D;
- creatividades de Instagram;
- banners;
- OG cards;
- imágenes generadas promocionales.

Si una portada existente está equivocada, reportarla. Si simplemente falta, comprobar qué edición acepta el upload y usar el asset editorial limpio.

## Descripción

Preferencia: sinopsis editorial/retailer coherente con la edición, no copy SEO de la web.

Para Manecillas, usar la sinopsis oficial que ya aparece en canales editoriales si StoryGraph necesita completar el campo. No meter keywords, premios o enlaces dentro de la descripción del libro.

Para Samuel, usar sinopsis editorial actual verificada.

## Page count: no propagar discrepancias

### Samuel

Proyecto: `422`.

Hay retailers que muestran `412`. Antes de cambiar StoryGraph si ya muestra un valor, coordinar con #429 Libros Indie / #404 DILVE para resolver la autoridad de la edición.

### Manecillas papel

Proyecto: `272`.

Algunos retailers muestran `266`. Coordinar con #428 Monza / #404 DILVE.

Si StoryGraph muestra 266/412, no cambiar a ciegas solo porque la web diga otra cifra; primero comprobar la autoridad editorial. Si ya está 272/422 y no hay nueva evidencia, mantener.

## Perfil público `@david_porto`

Auditar únicamente como perfil de usuario:

- username;
- display name si existe;
- avatar;
- bio;
- pronouns solo si David quiere publicarlos;
- visibilidad;
- enlaces si la plataforma los ofrece.

Objetivo: que si alguien llega al perfil no parezca abandonado o contradictorio.

No convertirlo en un anuncio permanente de los libros. Una bio breve tipo:

`Escritor · David Porto Díaz · Samuel entre mundos · Las manecillas del recuerdo · davidportodiaz.com`

solo si la interfaz actual permite bio y no desplaza el uso natural del perfil como lector.

## Reseñas / ratings del propio autor

No usar la cuenta del autor para puntuar artificialmente sus propios libros.

Si existen ratings/reviews propios, revisar y evitar cualquier cosa que parezca manipulación de media. Preferir perfil/bio/listas públicas para identificar autoría.

No pedir reseñas a usuarios mediante mensajes no solicitados.

## Listas públicas — oportunidad opcional

StoryGraph permite tags/listas públicas compartibles.

Podría tener valor crear **una lista editorial útil**, no promocional, por ejemplo:

- `Portal fantasy en español`
- `Fantasía juvenil española que recomiendo`

solo si David realmente usa StoryGraph como lector y la lista tiene valor independiente. Samuel puede incluirse con transparencia junto a otras obras.

No crear 20 listas para generar backlinks: sería spam y no aporta autoridad.

Fuente oficial:

- https://thestorygraph.freshdesk.com/support/solutions/articles/79000141960-how-to-create-custom-lists-on-the-storygraph

## Cambio potencial en la web

`autor.html` ya contiene:

`https://app.thestorygraph.com/profile/david_porto`

en `Person.sameAs`.

Mantenerlo solo si Claude confirma que:

- el perfil es realmente de David;
- es público;
- es estable;
- no existe un URL canónico mejor de author entity en StoryGraph.

### Libros

Si StoryGraph genera URLs estables para Samuel/Manecillas:

- considerar `Book.sameAs` para la **book family/obra** cuando represente inequívocamente la misma obra;
- no meter una URL de perfil lector en `Book.sameAs`;
- si solo hay URLs de ediciones, decidir según cómo el schema actual modela cada edición.

No añadir URLs hasta verificarlas live.

## QA final

Después de cambios:

- buscar por título;
- buscar por ISBN;
- buscar por autor;
- abrir desktop;
- abrir móvil;
- comprobar Spanish edition;
- comprobar papel/ebook;
- comprobar portada;
- comprobar páginas;
- comprobar fechas;
- comprobar autor;
- comprobar que no haya duplicados nuevos;
- comprobar que ratings/reviews existentes no se hayan perdido por una mala fusión.

## Evidencia a guardar

Por cada libro:

- StoryGraph family URL;
- edition URLs/UUIDs;
- ISBN;
- formato;
- metadata final;
- cambio realizado o `NO_ACTION`;
- ticket/support URL o número si existe;
- duplicados resueltos/pendientes;
- fecha QA.

Por perfil:

- URL;
- ownership confirmado;
- cambios de bio/avatar o `NO_ACTION`.

No guardar datos privados de login.

## Criterio de cierre

`STORYGRAPH_PROFILE_OWNERSHIP_CONFIRMED · SAMUEL_FAMILY_VERIFIED · SAMUEL_EDITION_VERIFIED · MANECILLAS_FAMILY_VERIFIED · PAPER_EDITION_VERIFIED · EBOOK_EDITION_VERIFIED_OR_EXTERNAL_DEPENDENCY · AUTHOR_ATTRIBUTION_CORRECT · DUPLICATES_REVIEWED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · PUBLIC_MOBILE_DESKTOP_QA_DONE`

Si la plataforma requiere librarian/support:

`CATALOG_AUDITED · CORRECTION_REQUEST_OPENED · NO_DUPLICATE_CREATED · EXTERNAL_DEPENDENCY_RECORDED`
