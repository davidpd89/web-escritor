# Autoridad de enlaces externos — hallazgo pendiente (2026-09-07)

Estado: **PENDIENTE** — no es una tarea de código, requiere trabajo de difusión fuera del repositorio.

## Qué se encontró

Durante una re-auditoría de Bing Webmaster Tools y Google Search Console (ambos con propiedad verificada y sin errores de configuración), Bing marcó como su única recomendación de severidad **moderada**:

> "Your site does not have enough inbound links from high quality domains."

Google Search Console (Enlaces → Enlaces externos) corrobora el mismo hallazgo con datos concretos:

- **22 enlaces externos totales** hacia davidportodiaz.com.
- Páginas más enlazadas: `/` (16), `/fragmento/` (2), `/libros/samuel-entre-mundos/` (2), `/universo/noveris/` (2).
- Dominios de origen: **reddit.com (14)**, bookdala.com (2), pinterest.com (2), arbolinvertido.com (1), babelio.com (1).

No hay ningún error técnico detrás de esto (sitemap correcto, sin acciones manuales, sin páginas rotas apuntando aquí desde fuera) — es, sencillamente, un perfil de enlaces entrantes todavía pequeño y concentrado en muy pocas fuentes, normal para una web que acaba de publicar su primer libro con editorial.

## Por qué no se resuelve con un commit

Un enlace entrante de un dominio de autoridad no se puede fabricar desde el propio sitio: lo decide un tercero (una editorial, una librería, un medio, otro autor) al enlazar hacia aquí. Cualquier intento de "generar" enlaces desde dentro del repositorio (granjas de enlaces, intercambios masivos, directorios de baja calidad) sería contraproducente y penalizable.

## Candidatas para cuando se aborde (sin decidir aquí cuál priorizar)

- Ficha de autor/libro en librerías y catálogos que aceptan altas de autores independientes o de editoriales pequeñas (Monza Ediciones, distribuidores).
- Perfiles de autor verificados con enlace a la web: Goodreads, StoryGraph, Babelio, Wikidata (ya enlazado como identificador en `editorial-facts.json`, pero comprobar que el propio Wikidata enlace de vuelta), Amazon Author Central.
- Cobertura de prensa/blogs literarios sobre *Las manecillas del recuerdo* o *Samuel entre mundos* — el kit de prensa (`/prensa.html`, `press-kit/`) ya existe para facilitar esto.
- Menciones en foros/comunidades de fantasía en español donde el autor ya participa (reddit ya es la fuente principal — mantener esa presencia orgánica en vez de forzarla).
- Reseñas de clubes de lectura o booktokers/bookstagrammers que enlacen la ficha del libro.

## Qué NO hacer

- No comprar enlaces ni usar redes de intercambio.
- No crear páginas de "directorio" propias solo para generar enlaces salientes/entrantes artificiales.
- No perseguir volumen de enlaces de baja calidad a costa de relevancia temática.

## Referencia

- Bing Webmaster Tools → Recomendaciones (severidad moderada, sin páginas asociadas porque es una señal de dominio, no de página).
- Google Search Console → Enlaces → Enlaces externos (`sc-domain:davidportodiaz.com`), corte del 2026-09-07.

## Ranking de oportunidades (añadido 2026-09-07, con datos de la sesión de SEO/IA)

Ordenado por valor esperado (relevancia temática real + autoridad + viabilidad sin pagar ni intercambiar enlaces), no por orden alfabético. Ninguna de estas es "fabricar" un enlace: todas son sitios que ya tendrían un motivo genuino, propio, para enlazar aquí.

1. **Monza Ediciones (la propia editorial de *Las manecillas del recuerdo*)** — el enlace de mayor autoridad posible y el más fácil de conseguir: es una relación comercial ya activa. Pedir que su ficha de catálogo/autor enlace a `davidportodiaz.com` es una solicitud estándar, no una petición inusual.
2. **Distribuidores/librerías donde el libro ya está a la venta** (Casa del Libro, FNAC, La Casa del Libro, librerías independientes que lo tengan en catálogo) — sus fichas de producto o de autor a menudo permiten un enlace a la web oficial; coste de gestión bajo, autoridad de dominio alta.
3. **Blogs/canales de reseñas de fantasía juvenil española y portal fantasy** — esta sesión confirmó con datos reales (Bing AI Performance) que `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` ya es, con diferencia, la pieza más citada por IA del sitio (29 citas) y que el propio término "libros de fantasía juvenil" genera una cuota de citación del 18,52 % en Bing Copilot. Un blog/canal de ese nicho exacto enlazando a esa pieza concreta (no a la home) es la oportunidad de mayor relevancia temática encontrada.
4. **Prensa local (Pontevedra/Galicia, origen del autor; Madrid, residencia)** — cobertura de un autor debutante con editorial es un ángulo habitual para prensa local/regional; el kit de prensa (`/prensa.html`, `press-kit/`) ya está listo para facilitar esto.
5. **Comunidad de escritores que buscan editorial** — hallazgo nuevo de esta sesión: Google Search Console muestra tráfico real y posiciones ya buenas (página 1) para búsquedas como "nocturna ediciones manuscritos" y "minotauro manuscritos" hacia `/editoriales/`. Foros/comunidades de escritores hispanohablantes (no genéricos, sino los específicos donde se discuten convocatorias y editoriales) tendrían un motivo real para enlazar esas fichas como recurso útil.
6. **Perfiles de autor verificados ya existentes** (Goodreads, StoryGraph, Babelio, Amazon Author Central, Wikidata) — de menor impacto por ser enlaces `nofollow` en su mayoría, pero conviene confirmar que los 5 apuntan de verdad a `davidportodiaz.com` y no a una URL antigua.
7. **Clubes de lectura y booktokers/bookstagrammers** que ya reseñan el género — la web ya tiene una página dedicada (`/clubes-de-lectura/`) pensada para esto; el enlace vendría como consecuencia natural de una reseña real, no de una solicitud fría.

## Qué NO hacer (confirmado, no cambia con el ranking anterior)

Directorios de enlaces genéricos, guest posts pagados, redes PBN o intercambios de enlaces no entran en este ranking bajo ningún puesto: son exactamente el patrón que el usuario pidió evitar, y no aportan autoridad temática real.
