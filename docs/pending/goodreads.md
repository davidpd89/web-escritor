# Goodreads — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#397 · `tracking/goodreads`**  
Estado: **RESOLVED · BOTH_WORKS_CORRECTLY_GROUPED · NO_ACTION_NEEDED · MINOR_THIRD_PARTY_EMAIL_NOTE**

## Verificación en vivo (2026-09-08) — la inconsistencia ya no existe

Abierta directamente la página pública de autor hoy:
https://www.goodreads.com/author/show/66843136.David_Porto_D_az

El snapshot antiguo que mostraba solo "1 distinct work" ya no representa
el estado actual. Hoy la página muestra correctamente:

- **"2 distinct works"** en el resumen de bibliografía;
- `Samuel entre mundos` — 5.00 avg rating, 14 ratings;
- `Las Manecillas del Recuerdo` — 5.00 avg rating, 1 rating, **2
  editions** (confirma que las ediciones papel + Kindle ya están
  agrupadas bajo la misma obra, no separadas como fichas distintas);
- bio actualizada mencionando ambos libros y sus editoriales
  (Libros Indie / Monza Ediciones) y los dos premios/reconocimientos.

No hace falta ninguna acción de re-agrupación ni contactar a Goodreads
Librarians: el propio catálogo ya se corrigió solo (probablemente al
propagarse los metadatos tras el alta de la segunda edición). Esta PR
puede considerarse cerrada.

### Nota aparte, no accionable desde aquí

La página muestra públicamente una actualización del propio autor (22 de
diciembre de 2025, "NOTA DEL AUTOR") que incluye su email en texto plano
para contacto de lectores. Es contenido histórico del propio autor en un
sitio de terceros (Goodreads), no algo que esta sesión pueda o deba
editar — solo se deja constancia por si el autor quiere revisar esa nota
él mismo, dado que esta noche se ha estado trabajando precisamente en
reducir la exposición pública del email en davidportodiaz.com.

## Objetivo

Dejar el perfil público de **David Porto Díaz** y las fichas/ediciones de `Samuel entre mundos` y `Las manecillas del recuerdo` coherentes, correctamente agrupadas y sin duplicados, aprovechando las herramientas del **Goodreads Author Program** sin manipular reseñas ni crear obras nuevas cuando ya existe un registro válido.

## Estado público observado hoy

### Perfil de autor

Perfil público actual:

- https://www.goodreads.com/author/show/66843136.David_Porto_D_az

La página pública rastreada el 2026-09-07 muestra que el perfil ya es **Goodreads Author**. No hay que volver a solicitar el programa salvo que la sesión autenticada revele que David no controla realmente ese perfil.

Datos públicos observados:

- nombre: **David Porto Díaz**;
- `Goodreads Author` activo;
- lugar de nacimiento mostrado: Pontevedra, Spain;
- web: `https://davidportodiaz.com`;
- géneros mostrados: Fantasy, Young Adult, Portal Fantasy;
- bio actual centrada en `Samuel entre mundos`;
- Goodreads muestra seguidores y métricas sociales, pero no deben copiarse a esta PR como datos estables porque cambian constantemente.

Fuente pública:

- https://www.goodreads.com/author/show/66843136.David_Porto_D_az

### Inconsistencia actual de catálogo / propagación

Hoy hay dos snapshots públicos recientes que no son totalmente coherentes entre sí:

1. una versión rastreada de la página de autor muestra **Samuel entre mundos** y **Las Manecillas del Recuerdo**;
2. otra vista reciente del perfil todavía informa `1 distinct work` y muestra solo Samuel dentro del listado detallado.

Esto se clasifica como:

`MANECILLAS_RECORD_PROPAGATION_OR_WORK_ASSOCIATION_INCONSISTENT`

No asumir ni que Manecillas “falta” ni que ya está todo resuelto. Claude debe abrir Goodreads en sesión actual y comprobar el catálogo real, work/edition IDs y cómo se presenta en la página pública.

## Samuel entre mundos — estado observado

Ficha pública localizada:

- https://www.goodreads.com/book/show/245605636-samuel-entre-mundos

Datos observados en la ficha pública actual:

- título: `Samuel entre mundos`;
- autor: David Porto Díaz;
- formato: Paperback;
- páginas: 422;
- publicación mostrada: 17 diciembre 2025;
- ISBN usado históricamente en la solicitud de alta: `9791387659776`;
- publisher: Libros Indie.

Las cifras de ratings/reviews son volátiles y no forman parte del contrato factual de esta PR.

## Las manecillas del recuerdo — estado a verificar

El resultado público actual de Goodreads ya muestra una entrada titulada:

`Las Manecillas del Recuerdo`

asociada visualmente al perfil de David en al menos una versión rastreada.

Hay que comprobar en vivo:

- URL exacta del work;
- edición/ediciones existentes;
- ISBN de cada edición;
- si papel y Kindle están combinados bajo el mismo work;
- título/capitalización;
- autor;
- editorial;
- fecha;
- páginas de papel;
- formato;
- portada;
- descripción;
- edición primaria.

### Datos canónicos para comparar

| Formato | Editorial | Identificador | Publicación / dato estable |
|---|---|---|---|
| Tapa blanda | Monza Ediciones | ISBN `9798905149351`; ASIN `B0HHY9MYLM` | 2026-09-03 · 272 páginas |
| Kindle | Monza Ediciones | ISBN `9798906781925`; ASIN `B0HHM71F46` | 2026-08-12 |

Goodreads debe representar ambos formatos como **ediciones de la misma obra**, no como dos obras independientes, salvo que exista una razón bibliográfica real que demuestre lo contrario.

## Hallazgos de perfil que conviene corregir

### 1. Bio anterior a Manecillas

La bio pública rastreada sigue describiendo a David fundamentalmente como autor debutante de `Samuel entre mundos` y no refleja de forma completa que ya existe una segunda novela publicada.

Además, el texto rastreado muestra:

`Top 10 Finalista del Premio Nacional de Literatura Infantil Juan Andrés Teno (2025)`

mientras la autoridad pública actual de la web del autor sitúa ese reconocimiento en **2026**.

No editar a ciegas: verificar primero la fuente exacta y después hacer coincidir Goodreads con la autoridad factual actual.

### Bio recomendada preparada

Versión breve, sin marketing excesivo:

> David Porto Díaz es un escritor español nacido en Pontevedra y residente en Madrid. Es autor de *Samuel entre mundos* (Libros Indie, 2025), novela de fantasía juvenil ambientada en Noveris, y de *Las manecillas del recuerdo* (Monza Ediciones, 2026). En 2026 obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue finalista del I Premio de Literatura Infantil Juan Andrés Teno. Más información y obra en davidportodiaz.com.

Antes de publicarla, Claude debe verificar la formulación de premios contra las fuentes autoritativas actuales del proyecto y no ampliar con claims no demostrados.

### 2. Contacto antiguo en actividad pública

En el perfil/rastro público aparece una nota del autor sobre Samuel con:

`samuelentremundos@gmail.com`

La web oficial actual usa como contacto principal:

`davidportodiaz@gmail.com`

Revisar si esa actividad puede editarse o retirarse. Si el correo antiguo sigue siendo válido no es necesariamente “incorrecto”, pero crea fragmentación de identidad/contacto. Preferencia de cierre: que el perfil y bio remitan a la web/canal actual, no mantener información histórica innecesaria.

### 3. Auto-rating del autor

La actividad pública muestra que la cuenta de David calificó `Samuel entre mundos` con **5 estrellas** y añadió una nota que aclara que es el autor.

Goodreads permite que autores escriban sobre su propio libro si la autoría queda clara, y su material histórico del Author Program explica ese uso. Sin embargo, las **Rating and Review Guidelines actuales (2026)** enfatizan autenticidad y advierten contra ratings que puedan inflar o devaluar artificialmente la media.

No afirmamos que ese rating viole automáticamente una regla, pero por confianza/óptica editorial conviene revisar:

- si puede conservarse la nota sin estrella;
- o retirar el auto-rating y usar Author Updates / Ask the Author / bio para comunicar contexto.

No debe hacerse ninguna acción que influya en reseñas de terceros.

Fuentes:

- https://www.goodreads.com/review/guidelines
- https://www.goodreads.com/author/guidelines

## Goodreads Author Program — capacidad actual

La página oficial del programa confirma a fecha 2026-09-07 que un Goodreads Author puede:

- actualizar foto de perfil;
- actualizar biografía;
- mantener sus book listings;
- usar herramientas de promoción/Author Dashboard;
- interactuar mediante Ask the Author y updates respetando las reglas de comunidad.

Fuente oficial:

- https://www.goodreads.com/author/program

Como el perfil actual ya muestra la insignia **Goodreads Author**, la siguiente sesión debe empezar por `Author Dashboard`, no por volver a solicitar la reclamación.

## Añadir libros y ediciones — flujo correcto

Goodreads distingue entre:

- **work**: la obra conceptual;
- **edition**: un formato/edición concreta.

Para Manecillas:

- papel y Kindle son ediciones distintas de la misma obra;
- no deben duplicarse como dos works si ya existe el work correcto.

El Goodreads Librarians Group oficial documenta actualmente que es el canal para:

- añadir libros/ediciones;
- editar información de libros y portadas;
- combinar ediciones;
- fusionar duplicados;
- corregir perfiles de autores no gestionados por Author Program.

Fuente:

- https://www.goodreads.com/group/show/220-goodreads-librarians-group

### Si David ya es Goodreads Author

Discusión reciente del grupo (2026) confirma que los Goodreads Authors pueden añadir un libro/edición desde `Author Dashboard → Add a book`, con el nombre del autor pre-rellenado.

Si el libro YA existe, no volver a crearlo: abrir el work/edition correcto y añadir únicamente el formato ausente.

## `combine` vs `merge` — no confundir

La terminología usada por los librarians actualmente:

- **combine**: vincular dos ediciones reales diferentes dentro del mismo work. Ninguna edición desaparece.
- **merge**: consolidar dos registros que son realmente duplicados de la misma edición; un registro redundante desaparece del catálogo.

Fuente pública reciente (agosto 2026):

- https://www.goodreads.com/topic/show/24728588-how-can-i-merge-two-book-editions-into-one

Aplicación:

- Manecillas papel + Kindle → **combine** dentro de un mismo work si ahora están separados.
- dos registros con el mismo ISBN de papel → posible **merge** después de verificar que sean duplicados reales.

## Edición primaria

Discusión reciente del Librarians Group confirma que los Goodreads Authors pueden establecer una edición como `primary edition` desde la edición deseada mediante `Edit book details → Set this book as the primary edition for this work`.

Fuentes:

- https://www.goodreads.com/topic/show/24651966-change-to-new-edition
- https://www.goodreads.com/topic/show/24547026-please-add-this-book-to-my-profile

No elegir primaria antes de ver las dos ediciones reales.

Criterio recomendado:

- edición con datos completos/correctos;
- portada editorial correcta;
- formato que represente mejor la obra actual;
- sin sacrificar ni borrar el otro formato.

Si papel es la edición editorial canónica completa y no hay otra razón operativa, es una candidata lógica; pero la decisión debe tomarse viendo el estado live, no preconfigurarse en esta PR.

## Metadatos a comprobar por edición

### Samuel

- [ ] título `Samuel entre mundos`;
- [ ] autor `David Porto Díaz`;
- [ ] ISBN `9791387659776`;
- [ ] Libros Indie;
- [ ] 422 páginas;
- [ ] Paperback;
- [ ] fecha correcta según edición;
- [ ] portada actual correcta;
- [ ] idioma Spanish;
- [ ] descripción actual coherente;
- [ ] work/edition no duplicado.

### Manecillas papel

- [ ] título canónico `Las manecillas del recuerdo`;
- [ ] autor `David Porto Díaz`;
- [ ] ISBN `9798905149351`;
- [ ] Monza Ediciones;
- [ ] 272 páginas;
- [ ] Paperback;
- [ ] 2026-09-03;
- [ ] portada editorial correcta;
- [ ] Spanish;
- [ ] asociado al work correcto.

### Manecillas Kindle

- [ ] título canónico `Las manecillas del recuerdo`;
- [ ] autor `David Porto Díaz`;
- [ ] ISBN `9798906781925`;
- [ ] ASIN `B0HHM71F46` si Goodreads lo admite en ese campo;
- [ ] Monza Ediciones;
- [ ] Kindle/ebook;
- [ ] 2026-08-12;
- [ ] portada correcta;
- [ ] asociado al MISMO work que papel.

No copiar el page count de la edición impresa al Kindle salvo que la plataforma/fuente bibliográfica lo justifique.

## Título de Manecillas

Una versión pública rastreada aparece como:

`Las Manecillas del Recuerdo`

La forma canónica de la web/editorial es:

`Las manecillas del recuerdo`

Verificar en live si la capitalización es realmente la del registro actual. Si lo es y Goodreads permite corregirla, usar la forma editorial canónica; no crear otro registro por una diferencia de mayúsculas.

## Reglas de comunidad que Claude debe respetar

Goodreads Author Guidelines vigentes:

- no contactar a usuarios que hayan añadido/shelved el libro con fines promocionales;
- no intentar influir en ratings/reviews;
- no responder a reseñas negativas;
- participar en grupos como lector, respetando reglas, no como spam promocional;
- usar las herramientas oficiales de Author Program para promoción.

Fuente:

- https://www.goodreads.com/author/guidelines

## Procedimiento exacto para Claude

### Fase 1 · sesión autenticada

1. Entrar en Goodreads con la cuenta correcta.
2. Confirmar acceso a Author Dashboard.
3. Guardar `GOODREADS_AUTHOR_ACCESS_CONFIRMED` sin exponer credenciales.
4. Abrir el perfil público en una ventana limpia/incógnito para comparar.

### Fase 2 · identidad

1. Revisar foto.
2. Revisar bio y actualizar Manecillas/año del reconocimiento si procede.
3. Confirmar web `https://davidportodiaz.com/`.
4. Revisar contacto antiguo en notas/updates.
5. Revisar auto-rating de Samuel y decidir limpieza de confianza.

### Fase 3 · catálogo

1. Abrir Samuel por ISBN.
2. Abrir Manecillas por título.
3. Buscar ISBN papel.
4. Buscar ISBN Kindle.
5. Identificar work ID y edition IDs.
6. Determinar si las dos ediciones de Manecillas están combinadas.
7. Detectar duplicados del mismo ISBN.
8. No crear nada hasta completar este inventario.

### Fase 4 · corrección

- editar directamente lo permitido por Author Program;
- añadir solo la edición realmente ausente;
- pedir librarian cuando la operación requiera combine/merge o un campo no editable;
- guardar URL del hilo/request si se abre;
- no duplicar una edición para saltarse un bloqueo.

### Fase 5 · QA

Comprobar en sesión pública limpia:

- perfil autor;
- foto/bio/web;
- Samuel visible;
- Manecillas visible;
- papel + Kindle bajo el mismo work;
- edición primaria intencional;
- ISBN/autor/editorial/fecha/formato correctos;
- sin duplicados evidentes;
- versión desktop + móvil.

## Evidencia mínima de cierre

Guardar en la PR:

- URLs públicas finales;
- work ID y edition IDs de cada libro;
- ISBN asociado a cada edición;
- capturas antes/después de errores corregidos;
- cambios de bio;
- primary edition elegida + razón;
- librarian request URL si existe;
- cualquier dependencia pendiente de Goodreads Staff/Librarians;
- fecha del QA final.

No guardar cookies, email de login privado, tokens ni datos sensibles de cuenta.

## Criterio de cierre

Caso ideal:

`GOODREADS_AUTHOR_ACCESS_CONFIRMED · PROFILE_CURRENT · SAMUEL_VERIFIED · MANECILLAS_WORK_VERIFIED · PAPER_AND_KINDLE_COMBINED · METADATA_COHERENT · DUPLICATES_REVIEWED · PUBLIC_MOBILE_DESKTOP_QA_DONE`

Si Goodreads requiere intervención externa:

`PROFILE_CURRENT · CATALOG_AUDITED · LIBRARIAN_REQUEST_OPENED · EXTERNAL_DEPENDENCY_RECORDED · NO_DUPLICATE_CREATED`

No marcar `COMPLETE` solo porque Manecillas aparezca en una búsqueda: hay que verificar edición, work y asociación real.

## Fuentes consultadas · 2026-09-07

- https://www.goodreads.com/author/show/66843136.David_Porto_D_az — perfil público.
- https://www.goodreads.com/book/show/245605636-samuel-entre-mundos — ficha Samuel.
- https://www.goodreads.com/author/program — Author Program.
- https://www.goodreads.com/author/guidelines — Author Guidelines.
- https://www.goodreads.com/review/guidelines — Rating and Review Guidelines.
- https://www.goodreads.com/group/show/220-goodreads-librarians-group — canal oficial de catálogo.
- https://www.goodreads.com/topic/show/24728588-how-can-i-merge-two-book-editions-into-one — combine vs merge, 2026.
- https://www.goodreads.com/topic/show/24651966-change-to-new-edition — primary edition, 2026.
- https://www.goodreads.com/topic/show/24107381-adding-new-edition — flujo para Goodreads Authors, 2026.

Autoridad factual propia:

- https://davidportodiaz.com/
- https://davidportodiaz.com/libros/samuel-entre-mundos/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/
- https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/

Regla final: **primero identificar work/editions reales; después corregir. Nunca crear otro libro para solucionar un problema de asociación.**
