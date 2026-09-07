# Cierre de Amazon Author Central, Goodreads y Wikidata (2026-09-07)

Estado: **EJECUTADO EN SESIÓN AUTENTICADA**. Cierra las tareas dejadas en las PR de tracking #396 (Amazon Author Central), #397 (Goodreads) y #398 (Wikidata).

Fuentes de partida: `docs/pending/amazon-author-central-execution-2026-09-07.md`, `docs/pending/goodreads-execution-2026-09-07.md` y `docs/pending/wikidata.md` (contenido preparado por una sesión anterior, no mergeado en `main`; el texto completo queda accesible en las ramas `tracking/amazon-author-central`, `tracking/goodreads` y `tracking/wikidata` aunque las PR se cierren).

## 1. Amazon Author Central

- **Ownership confirmado**: `https://www.amazon.es/stores/author/B0GZFP1JV3`, único perfil público bajo "David Porto Díaz" en Amazon.es (verificado con búsqueda pública: 3 resultados, sin duplicados).
- **Bio corregida** (dos errores factuales reales, no estilísticos):
  - Decía que *Las manecillas del recuerdo* era una "próxima obra" — ya está publicada desde el 3 de septiembre de 2026. Corregido a "en septiembre de 2026 publicó su segunda novela...".
  - El Premio Juan Andrés Teno decía "(2025)"; la fuente de autoridad del proyecto usa 2026. Corregido.
  - Se conservó el resto del texto (antología, proyecto PIEL) porque no había nada objetivamente incorrecto en ello.
- **Foto**: ya era la correcta y de buena calidad → sin cambios.
- **Libros — hallazgo real**: en la Biblioteca de Amazon.es solo figuraba *Samuel entre mundos*. **Las dos ediciones de *Las manecillas del recuerdo* no estaban dadas de alta**, a pesar de llevar semanas publicadas.
  - Añadida edición Kindle: ASIN `B0HHM71F46`, marketplace España (`A1RKKUPIHCS9HS`), verificado por metadatos (`Monza Ediciones`, `mobipocket_ebook`, 227 págs. según el propio catálogo de Amazon).
  - Añadida edición papel: ASIN `B0HHY9MYLM`, marketplace España, ISBN `979-8905149351`, tapa blanda, 266 págs. según el propio catálogo de Amazon.
  - Amazon documenta que el alta puede tardar en propagarse; **pendiente de verificar en unos días** que ambas ediciones aparezcan públicamente y que papel↔Kindle queden agrupadas bajo el mismo título.
- **Duplicados**: ninguno encontrado (ni de perfil de autor ni de fichas de libro).

## 2. Goodreads

- **Acceso a Author Dashboard confirmado** sobre el perfil `66843136`.
- **Bio corregida**: seguía centrada solo en Samuel y con el mismo error de año (2025→2026) en el premio Juan Andrés Teno. Reescrita para incluir Manecillas y corregir el año.
- **Hallazgo real de catálogo**: *Las manecillas del recuerdo* existía como **dos `work` distintos** en vez de un único work con dos ediciones combinadas:
  - `258289637` — Kindle Edition, 227 págs., publicado 12 ago 2026 (correcto), 1 reseña real de un lector (Carlos) — **no se tocó ninguna reseña de terceros**.
  - `258422630` — Paperback, 266 págs. — **con un error de metadatos real**: la fecha de publicación decía "12 de agosto de 2026" (la fecha de la edición Kindle) en vez del 3 de septiembre de 2026, que es la fecha real de la edición en papel. Corregido vía el editor de la ficha.
  - Enviado trabajo de **combinar ediciones** (`Combine Editions`) para unir ambos registros bajo un único work. Goodreads encola este proceso de forma asíncrona ("puede tardar"); **se envió dos veces y sigue sin completarse al cierre de esta sesión — pendiente de revisar en las próximas horas** si el work ya aparece unificado.
- **Limpieza de confianza**: la propia reseña/nota del autor sobre *Samuel entre mundos* tenía una autovaloración de 5★ (rating propio del libro) y mencionaba el correo antiguo `samuelentremundos@gmail.com`. Se retiró la estrella (queda como nota del autor sin rating, usando la opción "Clear" del propio editor de Goodreads) y se actualizó el correo a `davidportodiaz@gmail.com`, sin tocar ninguna reseña ni valoración de terceros.

## 3. Wikidata

Los dos ítems ya existentes (`Q139678851` autor, `Q139927664` Noveris) se auditaron contra la matriz del runbook.

- **Autor (`Q139678851`)**: faltaba el identificador **Amazon author ID (P4862)**. Añadido: `B0GZFP1JV3`. El resto de identificadores (ORCID, Goodreads) ya eran correctos.
- **Noveris (`Q139927664`)**: revisado, correctamente modelado (ciudad ficticia, creador, obra relacionada, sitio web) — sin cambios.
- **Hallazgo no anticipado por el runbook**: *Samuel entre mundos* **ya tenía QID** en Wikidata desde antes (`Q139915381` work, `Q139945987` primera edición), pero el sitio no los enlazaba y contenían **tres errores factuales reales**:
  1. Fecha de publicación en ambos ítems decía **2026**; la fecha real es **17 de diciembre de 2025**. Corregido en el work y en la edición, incluidas las descripciones en español e inglés (que también decían "2026 novel...").
  2. El work tenía un género **"comedia"** que no corresponde al libro (portal fantasy / literatura juvenil). Eliminado.
  3. El work tenía adjunto **"premio recibido: Premio Letras Como Espada"** — ese premio es por un microrrelato independiente, no por esta novela; ya está correctamente registrado en el ítem del autor. Eliminado del work del libro por estar mal atribuido.
  - Añadido `número de páginas: 422` a la edición (dato ya verificado y ausente).
  - Enlazado el QID `Q139915381` en el `sameAs` de `libros/samuel-entre-mundos/index.html` (cambio de código, ver más abajo).
- **Las manecillas del recuerdo**: sin QID en Wikidata. Búsqueda por título e ISBN confirma que no existe. Siguiendo la política de notoriedad del propio runbook (no crear ítems solo por SEO/backlink), **no se ha creado** — se deja documentado como `NOT_CREATED_NOTABILITY_INSUFFICIENT` hasta que haya referencias externas sólidas (prensa, reseñas serias) que lo justifiquen.

## 4. Cambios de código en este repositorio

- [`libros/samuel-entre-mundos/index.html`](../libros/samuel-entre-mundos/index.html): añadido `https://www.wikidata.org/wiki/Q139915381` al `sameAs` del nodo `Book`; `dateModified` actualizado a 2026-09-07.
- [`scripts/check-wikidata-sameas.py`](../scripts/check-wikidata-sameas.py): añadido `Q139915381` a `KNOWN_GOOD` (verificado manualmente contra la API en vivo antes de añadirlo, como exige el propio script).
- Verificado localmente: `check-wikidata-sameas.py`, `check-article-dates.py --check`, `check-canonical-entity-ids.py`, `check-runtime-scoping.py`, `check-no-stale-contact-email.py` — todos en verde. JSON-LD de la página validado sintácticamente.
- **No se tocó** `las-manecillas-del-recuerdo/index.html` porque todavía no hay ningún ID externo verificado (ni Goodreads work combinado, ni QID de Wikidata) que añadir de forma honesta a su `sameAs`.

## 5. Qué queda pendiente (por tiempo de propagación externa, no por trabajo interno)

- **Amazon**: confirmar en 24–48h que ambas ediciones de Manecillas aparecen públicamente en la Author Page y que Amazon las agrupa papel↔Kindle bajo el mismo título; si no las agrupa automáticamente, haría falta abrir una incidencia con Amazon/Monza.
- **Goodreads**: confirmar que el job de "Combine Editions" ha terminado y que *Las manecillas del recuerdo* aparece como un único work con ambas ediciones combinadas (se reenvió el job dos veces sin ver aún el resultado).
- **Goodreads/Amazon**: cuando el work de Manecillas en Goodreads quede combinado y estable, añadir su URL canónica al `sameAs` de `las-manecillas-del-recuerdo/index.html` (tarea de código ya prevista en la PR #397 original).
- **Wikidata**: si en el futuro aparecen referencias externas serias sobre *Las manecillas del recuerdo* (reseñas de prensa, blogs con autoridad), valorar crear su item siguiendo el modelo work/edition ya documentado — no antes.
- Nada de esto requiere una nueva sesión completa: son solo comprobaciones puntuales de que los procesos asíncronos de Amazon/Goodreads han terminado.
