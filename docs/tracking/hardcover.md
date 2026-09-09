# Hardcover.app — autor, libros y ediciones

Fecha de revisión: 2026-09-09

Estado: `AUTHENTICATED · MANECILLAS_PAPER_AND_EBOOK_BOTH_LIVE · SAMUEL_STILL_ABSENT_NOT_RESUBMITTED · AUTHOR_CLAIM_NOT_AVAILABLE`

## Cierre parcial (2026-09-09) v3 — edición ebook confirmada en vivo

Comprobado en vivo (`hardcover.app/books/las-manecillas-del-recuerdo/editions`):
el importador asíncrono resolvió la edición ebook encolada en el cierre
anterior. El libro ahora tiene **2 ediciones**, ambas correctas:

- **Ebook**: Kindle Edition, ISBN-13 `9798906781925`, ASIN `B0HHM71F46`,
  227 páginas, fecha `2026-08-12`.
- **Papel**: Paperback, ISBN-13 `9798905149351`, ASIN `B0HHY9MYLM`,
  266 páginas, fecha `2026-09-03`.

Con esto, el criterio original de esta PR (ambas ediciones de Manecillas
presentes) queda cumplido. **Samuel entre mundos sigue sin aparecer** —
re-verificado de nuevo en el buscador, sin resultados reales; sigue sin
reenviarse el alta (ya en cola desde antes). Sin más acción posible hasta
que el importador la resuelva o hasta que se decida forzar un nuevo intento
en una sesión futura.

## Cierre parcial (2026-09-09) v2 — edición ebook añadida, Samuel re-verificado

Una revisión externa (GPT) señaló correctamente que el cierre anterior solo
cubría la edición en papel de Manecillas, cuando el criterio original de
esta PR pedía ambas ediciones (papel + ebook). Corregido:

- **Edición ebook de Manecillas (ISBN `9798906781925`) añadida** desde la
  pestaña "Editions" del libro ya existente (`Add an Edition to Hardcover` →
  ISBN 10/13 → `9798906781925`), **no como obra nueva** — se usó
  deliberadamente el flujo "Add an Edition" sobre el libro ya localizado,
  no "Could you add it for us?", para que quede como segunda edición del
  mismo libro/familia en vez de un duplicado. Quedó en el mismo estado
  asíncrono "Looking up..." que ya se documentó para las altas anteriores;
  pendiente de revisar en una sesión futura si ya resolvió.
- **Samuel entre mundos re-verificado, sigue ausente.** Búsqueda por
  título en el buscador de Hardcover no devuelve el libro (solo coincidencias
  irrelevantes por la palabra "Samuel" en otros autores/títulos). Conforme a
  la nota ya dejada aquí, **no se ha vuelto a enviar el alta** — ya está en
  cola desde el intento anterior; solo falta comprobar más adelante si
  resolvió.

## Cierre parcial (2026-09-09)

Cuenta creada e iniciada sesión (`hardcover.app/@DavidPortoDiaz`, visible como "David Porto Díaz", vía el flujo de onboarding estándar del propio sitio — sin credenciales especiales, cuenta nueva del autor).

**Las manecillas del recuerdo — encontrada, alta confirmada y en vivo.** No existía. Se usó "Could you add it for us?" → alta por ISBN 13 (9798905149351, edición papel). La importación es un job asíncrono con delay real (varios minutos/horas, no instantáneo) — quedó en "Looking up..." en el intento anterior y se resolvió sola entre sesiones. Verificado en vivo el 2026-09-09:

- URL: https://hardcover.app/books/las-manecillas-del-recuerdo
- Autor: David Porto Díaz — correcto, sin duplicar.
- Año: 2026, 1 edición, "Available from 4 Sellers".
- Páginas mostradas: **266** (no 272). Es la discrepancia ya conocida y explícitamente cubierta por la nota de este documento ("No propagar 422/412 ni 272/266 hasta cerrar #429/#428/#404") — no se ha tocado ni se debe tocar hasta que esas issues internas se cierren.
- Sin descripción todavía (el propio Hardcover lo señala: "You can help out the author by adding a description") — no añadida esta sesión, queda pendiente si se quiere completar la ficha.

**Samuel entre mundos — todavía ausente, alta reintentada, en cola.** Búsqueda por título e ISBN (9791387659776) siguen sin resultado ("We couldn't find this book in our library"). Se repitió el mismo flujo de alta por ISBN 13 el 2026-09-09; quedó igual que Manecillas antes de resolverse: encolado en el importador asíncrono, sin confirmación inmediata. **Acción pendiente para una futura sesión: volver a buscar `9791387659776` en Hardcover; si ya aparece, solo falta verificar autor/edición/páginas (422) igual que se hizo con Manecillas — no repetir el alta si ya existe.**

No se ha tocado `Person`/`Author` claim (sigue sin existir ese flujo en Hardcover, ver hallazgo original más abajo). No se ha creado ninguna reseña ni valoración propia.

## Objetivo

Conseguir que Samuel y Las manecillas estén correctamente representados en Hardcover como obras/ediciones localizables por lectores, sin perder tiempo intentando reclamar un Author Program que todavía no existe.

## Hallazgo actual importante

Hardcover tiene páginas públicas de autor y de libros, pero su propio roadmap de 2026 mantiene como propuesta futura los `Verified Author Badges & Enhanced Author Profiles`. No debemos asumir que hoy existe un flujo oficial para que David reclame/edite su author page como en Goodreads o LibraryThing.

Fuente:
- https://roadmap.hardcover.app/feature-requests/posts/verified-author-badges-enhanced-author-profiles

El valor real hoy está en **catálogo + ediciones + descubrimiento de lectores**.

## Cómo se añaden/corrigen libros actualmente

El equipo/comunidad de Hardcover documenta que:
- cualquier usuario puede intentar añadir una edición mediante ISBN-10, ISBN-13, Goodreads ID, Open Library ID o Google Books ID;
- usuarios con rol Librarian pueden añadir libros/ediciones manualmente;
- existe un canal `#book-data-requests` en su Discord para pedir a librarians altas/correcciones cuando la importación por identificador no funciona.

Fuentes de roadmap/equipo:
- https://roadmap.hardcover.app/feature-requests/posts/choose-which-edition-you-are-reading
- https://roadmap.hardcover.app/feature-requests/posts/add-books-manually-1

## Datos canónicos

### Samuel entre mundos
- autor: David Porto Díaz
- ISBN: 9791387659776
- editorial: Libros Indie
- año: 2025
- páginas actuales del proyecto: 422

### Las manecillas del recuerdo — papel
- ISBN: 9798905149351
- editorial: Monza Ediciones
- fecha: 2026-09-03
- páginas actuales del proyecto: 272

### Las manecillas del recuerdo — ebook
- ISBN: 9798906781925
- editorial: Monza Ediciones
- fecha: 2026-08-12

No propagar 422/412 ni 272/266 hasta cerrar #429/#428/#404.

## Procedimiento Claude

1. Buscar David Porto Díaz y ambos títulos.
2. Buscar directamente los tres ISBN.
3. Registrar URLs/IDs existentes de autor, work/book y editions.
4. Revisar que papel/ebook de Manecillas estén tratados como ediciones de la misma obra y no como obras duplicadas.
5. Verificar portada, idioma, editorial, fecha, ISBN, formato y páginas.
6. Si falta una edición, intentar alta por ISBN/ID.
7. Si la importación falla o hay datos bloqueados, solicitar a Librarian mediante el canal oficial de book-data requests.
8. Revisar duplicados y asociaciones de autor incorrectas.
9. No crear un perfil de usuario pensando que equivale a “reclamar” la author page.
10. No auto-reseñar/auto-calificar para mejorar medias.

## ¿Añadir a sameAs?

Hardcover es una comunidad/catalogador, no autoridad primaria. Valorar `Book.sameAs` solo si obtenemos URLs públicas estables e inequívocas y aporta señal útil; no es prioridad frente a Goodreads/Open Library/LibraryThing.

No añadir un perfil de usuario de David como `Person.sameAs` salvo que realmente represente una identidad pública oficial útil, no simplemente una cuenta lectora.

## Prioridad

`P2`: útil para lectores y consistencia bibliográfica, pero por detrás de Amazon, Goodreads, Wikidata, BNE, Open Library, LibraryThing y ALIBRATE para nuestro caso actual.

## Criterio de cierre

`AUTHOR_PAGE_AUDITED · SAMUEL_FOUND_OR_ADDED · MANECILLAS_FOUND_OR_ADDED · EDITIONS_VERIFIED · DUPLICATES_REVIEWED · LIBRARIAN_REQUESTS_RECORDED_IF_NEEDED · NO_FALSE_AUTHOR_CLAIM · NO_PAID_FEATURES`
