# Goodreads — paquete final de ejecución

Fecha: **2026-09-07**  
PR: **#397**  
Estado: **RESEARCHED · AUTHOR_CONFIRMED · MANECILLAS_VISIBLE · EDITION_STRUCTURE_PENDING_AUTHENTICATED_CHECK**

Este suplemento actualiza el snapshot público del runbook principal y deja las acciones exactas que Claude debe ejecutar. Si hay contradicción con `goodreads.md`, prevalece este documento para el estado observado el 2026-09-07.

## 1. Snapshot público más reciente

Perfil:

`https://www.goodreads.com/author/show/66843136.David_Porto_D_az`

El rastreo público más reciente disponible hoy muestra:

- **David Porto Díaz**;
- insignia **Goodreads Author**;
- nacido en Pontevedra, Spain;
- web `https://davidportodiaz.com`;
- géneros Fantasy, Young Adult, Portal Fantasy;
- miembro desde diciembre de 2025;
- **2 distinct works**;
- aparecen `Samuel entre mundos` y `Las Manecillas del Recuerdo`.

Por tanto, el estado anterior `MANECILLAS_RECORD_PROPAGATION_INCONSISTENT` ya no debe interpretarse como “Manecillas falta”. El snapshot más reciente confirma que la obra aparece en el perfil.

Lo que sigue sin estar resuelto públicamente es la **estructura work/edition**: necesitamos abrir Goodreads autenticado y capturar el work ID y los edition IDs reales para comprobar si papel y Kindle están combinados correctamente.

## 2. Problemas reales que sí siguen visibles

### Bio desactualizada

La bio pública rastreada sigue centrada casi exclusivamente en Samuel y no refleja adecuadamente que Manecillas ya está publicada.

Además conserva:

`Top 10 Finalista del Premio Nacional de Literatura Infantil Juan Andrés Teno (2025)`

mientras la autoridad actual del proyecto/web usa **2026**.

Acción: verificar la fuente interna/externa una vez más durante la sesión y, si 2026 sigue siendo el dato correcto, actualizar la bio.

### Nota/contacto histórico

La actividad pública conserva una nota del autor en Samuel con:

`samuelentremundos@gmail.com`

El contacto público actual del proyecto es:

`davidportodiaz@gmail.com`

No es obligatorio borrar historia válida, pero sí conviene evitar que un correo antiguo sea el punto de contacto protagonista. Revisar si la nota puede editarse/retirarse sin perder información útil.

### Auto-rating de Samuel

El perfil muestra una valoración propia de 5★ de Samuel con nota explícita de autor.

No se debe tocar ninguna reseña de terceros ni intentar mover la media. Por limpieza de confianza, revisar si se puede retirar el rating propio y conservar, si hace falta, una actualización de autor sin estrella. Si Goodreads no permite separar ambas cosas limpiamente, priorizar no manipular nada.

## 3. Datos canónicos preparados

### Autor

- Nombre: **David Porto Díaz**
- Website: `https://davidportodiaz.com/`
- Goodreads Author ID: `66843136`
- Perfil: `https://www.goodreads.com/author/show/66843136.David_Porto_D_az`

### Samuel entre mundos

- Ficha pública localizada: `https://www.goodreads.com/book/show/245605636-samuel-entre-mundos`
- ISBN-13: `9791387659776`
- Publisher: **Libros Indie**
- Formato: Paperback
- Páginas: 422
- Fecha pública Goodreads: **17 diciembre 2025**
- Idioma: Spanish

El hilo histórico de Goodreads Librarians que documentó el alta existe en:

`https://www.goodreads.com/topic/show/23309459-samuel-entre-mundos-david-porto-d-az-paperback-isbn-9791387659776`

### Las manecillas del recuerdo — papel

- Título canónico: **Las manecillas del recuerdo**
- Publisher: **Monza Ediciones**
- ISBN-13: `9798905149351`
- ASIN Amazon: `B0HHY9MYLM`
- Publicación: `2026-09-03`
- 272 páginas
- Paperback
- Spanish

### Las manecillas del recuerdo — Kindle

- Título canónico: **Las manecillas del recuerdo**
- Publisher: **Monza Ediciones**
- ISBN-13: `9798906781925`
- ASIN: `B0HHM71F46`
- Publicación: `2026-08-12`
- Kindle / ebook
- Spanish

No usar 272 páginas para Kindle por copia mecánica.

## 4. Bio lista para pegar

Versión recomendada:

> David Porto Díaz es un escritor español nacido en Pontevedra y residente en Madrid. Es autor de *Samuel entre mundos* (Libros Indie, 2025), novela de fantasía juvenil ambientada en Noveris, y de *Las manecillas del recuerdo* (Monza Ediciones, 2026), novela coral sobre memoria, familia y los objetos que heredamos. En 2026 obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue finalista del I Premio de Literatura Infantil Juan Andrés Teno. Más información en davidportodiaz.com.

Antes de guardar:

- verificar de nuevo el año/denominación exacta de los premios;
- no añadir ratings, ventas, rankings o superlativos;
- mantener la URL oficial.

## 5. Reglas de catálogo que Claude no debe improvisar

Goodreads maneja:

- **work** = obra conceptual;
- **edition** = edición/formato concreto.

Para Manecillas queremos:

- un único work;
- edición papel;
- edición Kindle;
- ambas **combined** bajo el mismo work;
- ningún registro duplicado del mismo ISBN.

Terminología:

- `combine` = unir ediciones diferentes de la misma obra bajo un work;
- `merge` = eliminar/consolidar registros realmente duplicados de la misma edición.

No crear un segundo work porque falte una edición.

## 6. Orden exacto de ejecución

### A. Confirmar control del Author Program

1. Entrar en Goodreads.
2. Abrir Author Dashboard.
3. Confirmar que la cuenta controla el perfil `66843136`.
4. Si no, no crear otro perfil; resolver ownership.

### B. Perfil

1. Revisar foto y mantener la canónica si ya coincide.
2. Actualizar bio si sigue antigua.
3. Confirmar website.
4. Revisar el correo histórico en actividad.
5. Revisar el auto-rating propio de Samuel.

### C. Inventario antes de editar

Buscar en este orden:

1. `245605636` / Samuel
2. `9791387659776`
3. `Las manecillas del recuerdo`
4. `9798905149351`
5. `9798906781925`
6. `B0HHY9MYLM`
7. `B0HHM71F46`

Capturar:

- work ID de Samuel;
- edition ID de Samuel;
- work ID de Manecillas;
- edition ID papel;
- edition ID Kindle;
- cualquier duplicado.

No crear nada hasta tener este inventario.

### D. Manecillas

Si papel + Kindle ya están bajo el mismo work:

`NO_ACTION_COMBINE`.

Si son dos works diferentes:

- solicitar/ejecutar `combine` por la vía permitida;
- si requiere Goodreads Librarian, abrir request con ISBN/ASIN/URLs;
- no borrar una edición real.

Si falta una edición:

- añadir únicamente esa edition mediante Author Dashboard si se permite;
- asociarla al work existente;
- no crear un work nuevo.

### E. Primary edition

No cambiarla por rutina. Solo cambiar si la actual es claramente peor/incorrecta.

Candidata lógica: edición en papel de Monza, si tiene portada/metadatos completos y representa mejor la obra. Pero decidir únicamente viendo el estado live.

### F. Metadatos

Comprobar por edición:

- título;
- author;
- publisher;
- ISBN;
- fecha;
- formato;
- páginas cuando proceda;
- idioma;
- portada;
- descripción.

Capitalización preferida: `Las manecillas del recuerdo`, no crear duplicado para corregir mayúsculas.

## 7. Uso de Goodreads para visibilidad sin spam

Una vez el catálogo esté correcto, revisar únicamente herramientas gratuitas del Author Program que aporten valor real:

- Author Updates, si siguen disponibles en la interfaz actual;
- Ask the Author, si está habilitado;
- enlace web oficial;
- bio/foto coherentes.

No contactar a lectores que hayan añadido el libro para pedir reseñas. No responder a reseñas negativas. No manipular ratings.

Fuentes actuales:

- `https://www.goodreads.com/author/program`
- `https://www.goodreads.com/author/guidelines`
- `https://www.goodreads.com/review/guidelines`
- `https://www.goodreads.com/group/show/220-goodreads-librarians-group`

## 8. Estado del repo ya comprobado

### Autor

`autor.html` ya contiene el Goodreads Author Profile en `Person.sameAs`:

`https://www.goodreads.com/author/show/66843136.David_Porto_D_az`

No necesita cambio.

### Samuel

La ficha de Samuel ya contiene en `Book.sameAs`:

`https://www.goodreads.com/book/show/245605636-samuel-entre-mundos`

No necesita cambio salvo que Goodreads revele que ese ID fue sustituido/redirigido por otro canónico.

### Manecillas

La ficha `las-manecillas-del-recuerdo/index.html` todavía **no tiene un `sameAs` de Goodreads** porque no disponemos aún del URL/ID exacto y verificado de la obra/edición.

Esto sí deja una tarea de código preparada:

**DESPUÉS de capturar la URL canónica live de Manecillas en Goodreads:**

1. añadir esa URL al `sameAs` del nodo `Book` principal `https://davidportodiaz.com/#book-manecillas`;
2. no añadir una URL de búsqueda ni del perfil del autor como sustituto;
3. si Goodreads expone URLs separadas por edición, usar en el work principal la URL canónica del work/edición primaria que represente la obra y documentar la decisión;
4. no introducir ratings/reviewCount dinámicos en JSON-LD;
5. ejecutar los checks de machine authority / content parity / release readiness correspondientes.

Hasta obtener el ID real: **NO INVENTAR URL**.

## 9. Evidencia de cierre

Claude debe añadir a #397:

- Author Dashboard access confirmado;
- perfil público final;
- bio/foto/web `UPDATED/NO_ACTION`;
- work/edition IDs de Samuel;
- work/edition IDs de Manecillas;
- estado papel↔Kindle `COMBINED/ALREADY_COMBINED/REQUEST_PENDING`;
- primary edition + razón si se cambia;
- duplicados `NONE_FOUND` o lista;
- librarian request URL si existe;
- resultado del auto-rating/contacto histórico;
- URL canónica de Manecillas usada para el parche JSON-LD;
- QA desktop/mobile;
- tests del repo si se modificó código.

## 10. Criterio de cierre

`GOODREADS_AUTHOR_ACCESS_CONFIRMED · PROFILE_CURRENT · SAMUEL_VERIFIED · MANECILLAS_WORK_VERIFIED · PAPER_AND_KINDLE_COMBINED_OR_ESCALATED · METADATA_COHERENT · DUPLICATES_REVIEWED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · PUBLIC_MOBILE_DESKTOP_QA_DONE`
