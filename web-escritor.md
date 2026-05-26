# web-escritor — Notas de seguimiento técnico

Archivo de seguimiento para Claude: estado técnico, pendientes de monitorizar y registro de cambios.

---

## Estado del Service Worker

- CACHE_VERSION actual: `david-porto-v2026-05-26-3`
- Último bump: 26 mayo 2026 (actualizado en sesión anterior)
- Política: network-first para navegación, cache-first para assets

---

## Cambios aplicados — 26 mayo 2026 (cuarta ronda — Bloques AA, AE, P, Brevo)

### Brevo MCP
- Configurado en VS Code settings.json (`mcp.servers.brevo`) con clave API full-access
- Worker actual ya envía email al endpoint de Brevo API; los atributos FACCION_NOVERIS y SOURCE deben crearse en Brevo antes de usarlos en automatizaciones (ver checklist W1 en Respuestas a tus preguntas.txt)

### Schema Person (index.html y libros/samuel-entre-mundos/)
- Añadido `disambiguatingDescription`: "Escritor español de fantasía juvenil, autor de Samuel entre mundos (Libros Indie, 2025). No confundir con David Porto Arias, docente de Formación Profesional en A Coruña."
- Añadido "David Porto Díaz (escritor)" a `alternateName`

### Schema Book — AggregateRating (index.html + libro page)
- Corregido `ratingCount` y `reviewCount`: de "8" a "3" (coincide con las 3 review visibles en el DOM)
- Eliminado `ratingExplanation` (no es una propiedad estándar de schema.org)
- HTML del libro: "8 reseñas en Amazon España" → "Valoraciones verificadas de lectores"

### fragmento/index.html
- Meta description actualizada: capturas query "samuel entre mundos gratis" sin registro
- Añadido `<p class="fragment-notice">` al inicio de la sección de lectura para interceptar búsquedas de "pdf gratis"

### llms.txt
- Desambiguación actualizada: "David Porto Arias (docente FP, A Coruña)" específicamente mencionado
- Calificación actualizada: "reseñas en Amazon España y Goodreads" (sin número fijo)

### PageSpeed / CSS inline (index.html)
- Añadido `will-change:backdrop-filter;contain:layout style` a `.site-header`
- Añadido `will-change:transform` a `body::before` y `body::after`
- Añadido `@media(prefers-reduced-motion:reduce)` al final del CSS inline
- Hero author photo: `loading="eager"` + `decoding="sync"` (era `decoding="async"`)

---

## Cambios aplicados — 26 mayo 2026 (tercera ronda — Bloque T+U segunda respuesta)

### llms.txt
- Eliminada frase "Es la primera portal fantasy española de debut..." (claim difícil de probar)
- Sustituida por: "Samuel entre mundos es una novela española de portal fantasy juvenil con sistema de magia estructurado, objetos con memoria, protagonista no-elegido y misterio familiar."

### autor.html
- `geo-answer` reescrito: eliminada mención a "romantasy y ficción especulativa"
- Nueva versión: "portal fantasy juvenil" como sintagma fijo (optimizado para LLMs)
- Premio aclarado: "Primer Premio Letras Como Espada 2026 en microrrelatos"

### script.js
- Añadida línea `submitNewsletter("newsletter-form-cuaderno", ...)` para el futuro artículo de blog /cuaderno/

### Respuestas a tus preguntas.txt
- Eliminadas respuestas de Bloque T y U insertadas por el usuario (líneas 32-1551)
- Archivo: 4773 → 3730 líneas

### cosas-pendientes-david.txt
- Añadidas secciones: dominio duplicado davidpd89.github.io (CRÍTICO), Bing Webmaster Tools, test mensual IA, Open Library, Goodreads listas, Instagram bio, primer artículo /cuaderno/

---

## Cambios aplicados — 26 mayo 2026 (primera ronda)

### service-worker.js
- Bumpeada CACHE_VERSION → `david-porto-v2026-05-26-2` para invalidar caché y mostrar el fix del layout de eventos

### ai/index.html
- Añadida aclaración "(categoría microrrelatos, no la novela)" al Premio Letras Como Espada
- Corregida valoración: Goodreads → Amazon España (8 reseñas verificadas, 5★)
- Añadida sección "Desambiguaciones importantes" con 6 puntos clave para LLMs
- Añadida sección "Preguntas frecuentes con respuesta directa" (formato Q&A para GEO)
- Actualizada fecha al 26 mayo 2026

### humans.txt
- Creado nuevo archivo `/humans.txt` (estándar humanstxt.org)

### script.js — Modal de compra
- Añadida nota "Amazon ofrece 30 días de devolución en papel" en el diálogo de compra
- Añadido `history.pushState({ buyModal: true }, '', '#comprar')` al abrir el modal
- Añadido `window.addEventListener('popstate', ...)` para cerrar el modal con el botón Atrás

### script.js — Newsletter
- Diferenciación de error 400: si Brevo devuelve "already exist", muestra "Ya estás suscrito a la lista. ¡Gracias!" en lugar del mensaje de éxito normal

### Respuestas a tus preguntas.txt
- Eliminados bloques procesados: O, R, S, T (preguntas y respuestas)
- Conservados: Bloque Q (con respuestas) + todos los bloques nuevos (U, V, W, X, Z, AA, AB, N, P, Q2, AC, AD, AE, VI y el Bloque U de competencia)

### cosas-pendientes-david.txt
- Añadida sección "POSICIONAMIENTO EN IAs — PRIORIDAD ALTA (Bloque T)" con 5 acciones concretas para David (Babelio, StoryGraph, Goodreads, menciones externas, frase canónica)

---

## Cosas a monitorizar (Claude)

### Premio Letras Como Espada
- Verificar que llms.txt sigue diciendo "Primer Premio — XII Certamen de Microrrelatos" (correcto)
- Si David menciona el premio en RRSS, confirmar que añade "(microrrelatos)" o "(certamen de microrrelatos)"

### Modal de compra — Back button
- El `history.pushState` añade `#comprar` a la URL cuando se abre el modal
- Si el modal se abre al cargar la página con `#comprar` en la URL, puede ser confuso → monitorizar si David reporta comportamiento extraño

### Newsletter — Duplicados
- Con el fix actual: error 400 + body con "already exist" → mensaje "Ya estás suscrito"
- Si Brevo cambia su API de respuesta de error, el mensaje podría caer al catch genérico → monitorizar si David reporta errores raros en el formulario

### /ai/index.html
- Revisar cada vez que haya datos nuevos del libro (reseñas, premios, etc.)
- La sección FAQ debe actualizarse si cambia el número de reseñas o el precio

---

## Pendientes técnicos (Claude, no David)

- [ ] Añadir enlace a `/ai/` y `/llms.txt` desde el footer de todas las páginas (actualmente solo está en ai/index.html)
- [ ] Cuando existan `/recomendaciones/portal-fantasy-en-espanol/` y `/recomendaciones/libros-parecidos-a-harry-potter/`, añadir enlace desde index.html libro y samuel page (ver nota en cosas-pendientes)
- [ ] Revisar si el sticky CTA del fragmento funciona correctamente en iOS (se oculta en los últimos CTAs)

---

## Herramientas útiles

- GoatCounter: https://davidportodiaz.goatcounter.com/
- PageSpeed Insights: https://pagespeed.web.dev/analysis?url=https://davidportodiaz.com/
- Schema validator: https://validator.schema.org/?url=https://davidportodiaz.com/
- Rich Results Test: https://search.google.com/test/rich-results?url=https://davidportodiaz.com/libros/samuel-entre-mundos/
