# web-escritor — Notas de seguimiento técnico

Archivo de seguimiento para Claude: estado técnico, pendientes de monitorizar y registro de cambios.

---

## Estado del Service Worker

- CACHE_VERSION actual: `david-porto-v2026-05-26-2`
- Último bump: 26 mayo 2026 (para invalidar caché de styles.css con fix de events-block)
- Política: network-first para navegación, cache-first para assets

---

## Cambios aplicados — 26 mayo 2026

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
