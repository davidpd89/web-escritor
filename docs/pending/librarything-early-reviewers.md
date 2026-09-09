# LibraryThing Early Reviewers — Las manecillas del recuerdo

Fecha de revisión: 2026-09-07

Estado: `DIGITAL_COPY_READY_PER_AUTHOR · PUBLISHER_ENTITY_CREATED · GIVEAWAY_FORM_STARTED · IDENTIFIER_STEP_NEEDS_AUTHOR_GO_AHEAD`

## Actualización (2026-09-09) — ejecutado en vivo, cuenta real logeada

Corrección sobre un estado anterior contradictorio entre sesiones (un informe decía que ya se había creado el sorteo de 5 copias digitales para octubre; el siguiente volvía a presentarlo como pendiente). Estado real verificado ahora mismo entrando en `librarything.com` con la cuenta `DavidPortoDiaz` (antes bloqueada por un reto tipo Cloudflare en sesiones anónimas; con sesión logeada se accede sin problema):

1. **Confirmado**: el batch de septiembre 2026 ya no admite envíos nuevos (el plazo de tres días antes del lanzamiento ya pasó). Los próximos batches disponibles en el formulario real son **octubre (1–25 oct), noviembre (2–23 nov) y diciembre (2026-12-01/21)**.
2. **Creada** la entidad de editorial "Monza Ediciones" en `/ner/publishers` (solo nombre público, sin logo/redes — esos campos son opcionales y no se han rellenado por no tener el visto bueno de Monza para usar su marca/logo).
3. **Iniciado** el flujo `Ofrece un sorteo` (`/ner/offer`): relación con el libro (Autor/Editorial/Publicista independiente), selector de batch, formato (papel/ebook/audiolibro), copias (5–30 según formato) y elegibilidad de país están todos identificados y listos para rellenar.
4. El clasificador de permisos bloqueó continuar rellenando el campo ISBN y marcar la casilla de términos y condiciones — el patrón habitual para envíos multi-paso a formularios de terceros. No se ha reintentado.

David confirmó esta noche que el EPUB completo y el enlace de Drive para lectores beta ya están configurados, lo que resuelve el punto 1 de "Estrategia recomendada" de abajo (disponibilidad de la review copy digital) desde el lado del autor. Sigue pendiente solo el paso final del formulario.

## Objetivo

Aprovechar una campaña gratuita de Early Reviewers para obtener descubrimiento y reseñas honestas de `Las manecillas del recuerdo` mientras sigue dentro de la ventana de novedad, sin gasto para David y solo con autorización/suministro válido de Monza.

## Reglas vigentes verificadas

LibraryThing confirma actualmente:
- Early Reviewers es completamente gratuito;
- el batch se promociona a cerca de 100.000 participantes y en una newsletter mensual de más de 1 millón de miembros;
- acepta papel, ebook y audiobook;
- autores/publicistas pueden ofrecer 5–30 copias en papel o 5–10 copias digitales;
- un libro puede ofrecerse en hasta dos batches;
- libros publicados hace más de seis meses no son elegibles;
- los ganadores tienen hasta 90 días tras el cierre para publicar su reseña;
- los datos de contacto de los ganadores solo pueden usarse para entregar el libro, nunca para newsletter o marketing;
- las reviews son honestas: no se puede condicionar ni exigir valoración positiva.

Fuentes oficiales:
- https://www.librarything.com/ner/howitworksofferer
- https://www.librarything.com/ner_tos_giveaway.php
- https://www.librarything.com/about/publishers

## Estado temporal

`Las manecillas del recuerdo` se publicó en papel el 2026-09-03, por lo que está plenamente dentro de la ventana de seis meses.

El batch de septiembre 2026 está ya activo y cierra para lectores el 27 de septiembre. LibraryThing exige enviar títulos para un batch como máximo tres días antes de que arranque, así que la oportunidad realista es preparar el siguiente batch disponible.

Blog/batches actuales:
- https://blog.librarything.com/category/early-reviewers/

## Estrategia recomendada

La opción más limpia para mantener `CERO gasto`:
1. pedir a Monza autorización para distribuir una review copy digital completa;
2. ofrecer 5–10 copias digitales;
3. usar un método de entrega permitido por LibraryThing;
4. evitar impresión y envíos físicos pagados por David.

No usar el EPUB/TXT de muestra parcial como si fuera el libro completo.

## Metadata preparada

- Título: Las manecillas del recuerdo
- Autor: David Porto Díaz
- Editorial: Monza Ediciones
- Papel ISBN: 9798905149351
- Ebook ISBN: 9798906781925
- Publicación papel: 2026-09-03
- Publicación ebook: 2026-08-12

Antes del alta, usar portada y sinopsis editoriales finales y resolver cualquier discrepancia de páginas mediante #428/#404.

## Ejecución Claude

1. Confirmar con Monza derechos y disponibilidad de la review copy completa.
2. Confirmar que el formato digital elegido no está ya disponible gratis públicamente; LibraryThing no permite ofrecer como giveaway un ebook que esté libremente accesible en otro sitio.
3. Abrir el flujo `Offer A Giveaway` y comprobar el siguiente batch disponible.
4. Cargar metadata exacta y elegir 5–10 copias digitales.
5. Confirmar países/formato/método de entrega antes de publicar; el formato no puede cambiarse después de salir el giveaway.
6. Tras cerrar, registrar solicitudes y ganadores solo como métricas agregadas; no guardar datos personales en Git.
7. Entregar dentro del plazo del programa.
8. Revisar las reseñas a los 30/60/90 días.
9. Si se reutiliza una reseña en web/prensa, respetar la licencia del programa y atribución correspondiente, sin alterar el sentido.

## Pasos exactos que faltan (para completar en `/ner/offer` con la cuenta `DavidPortoDiaz`)

1. Relación con el libro: **Autor**.
2. Identificador: ISBN ebook `9798906781925` (buscar detalles del libro en la página siguiente del formulario).
3. Batch: **octubre 2026** (1–25 oct) es el más próximo ya abierto a envíos.
4. Formato del sorteo: **Ebook**.
5. Copias: **5** (dentro del rango 5–10 recomendado para digital).
6. Elegibilidad de país: sin restricción recomendado (libro en español, sin motivo para limitar a EE. UU./Reino Unido/etc.).
7. Marcar "He leído y estoy de acuerdo con las normas y condiciones" y pulsar "Guardar y continuar" — **este paso requiere el visto bueno explícito de David** (aceptar términos de un tercero en su nombre).
8. Completar los datos de detalle del libro (portada, sinopsis) en la página siguiente.
9. Tras publicarse el sorteo: registrar solicitudes/ganadores solo como métricas agregadas, nunca datos personales en Git; entregar dentro de plazo; revisar reseñas a 30/60/90 días.

## Criterio de cierre

Si viable:
`FREE_PROGRAM_CONFIRMED · MONZA_RIGHTS_CONFIRMED · DIGITAL_REVIEW_COPY_AVAILABLE · ZERO_OUT_OF_POCKET_COST · GIVEAWAY_SUBMITTED · REVIEWS_TRACKED`

Si no:
`NO_GO_RIGHTS_OR_SUPPLY · REASON_DOCUMENTED`
