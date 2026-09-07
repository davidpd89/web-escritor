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
