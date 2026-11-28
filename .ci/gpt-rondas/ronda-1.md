# Ronda 1 — Diagnóstico de descubrimiento del catálogo de libros y autores

Contexto: davidportodiaz.com es la web de un escritor español (David Porto Díaz). Además de sus novelas, publica un
catálogo estático (HTML generado por Python, desplegado en GitHub Pages con Cloudflare delante) de libros de OTROS
autores publicados en España, con fichas por libro, por autor y por editorial. Objetivo: que más gente lo encuentre en
Google/Bing y que los asistentes de IA (ChatGPT Search, Perplexity, Gemini/AI Overviews, Copilot, Claude) lo citen cuando
alguien pregunta por un libro, un autor, «qué leer», «novedades de X», «último libro de X», etc.

## Evidencia sacada del código y de los ficheros publicados (28/11/2026)

Volumen
- 11.411 fichas de libro publicadas (`/recomendaciones/libros/<slug-isbn>/`), todas en el sitemap.
- Años de publicación: 2026 = 9.225, 2027 = 1.312 (próximos lanzamientos), 2025 = 241, 2024 o antes ≈ 600. Es, de facto, un catálogo de NOVEDADES y PRÓXIMOS LANZAMIENTOS en España.
- 11.465 nombres de autor distintos; solo 799 tienen página de autor (`/recomendaciones/autores/<slug>/`). Autores con ≥2 libros: 1.378, de los que solo 257 tienen página; con ≥5 libros: 178, solo 61 con página. Una página de autor exige un registro validado con fuentes.
- 144 páginas de editorial. 118 páginas de paginación del índice (`/recomendaciones/pagina/N/`).
- 93 categorías (35 géneros, 43 temáticas, 9 edades, 4 épocas, 2 de contenido) con `slug`, nombre y descripción de una línea. Las más pobladas: ensayo 1.763, narrativa 1.650, cómic/novela gráfica 1.273, infantil 1.110, historia 941, fantasía 788, juvenil 771, misterio y thriller 643, romance 642, novela histórica 342, ciencia ficción 214, terror 171, romantasy 150.

Enlazado interno
- Las etiquetas de género/tema de cada ficha enlazan a `/recomendaciones/#genero=fantasia` (fragmento hash con filtro JS). NO existe ninguna URL rastreable por categoría, ni por mes de publicación, ni por edad.
- Solo dos páginas temáticas editoriales a mano: `/recomendaciones/portal-fantasy-espanol/` y `/recomendaciones/magia-con-coste/`.
- Cada ficha tiene «También te puede interesar» con 6 libros (mismas categorías raras / mismo autor, sin cruzar público ni edad).
- En la ficha, el autor solo enlaza a su página si existe registro: en una muestra de 571 fichas, 73 (13 %) enlazan autor.

Contenido de una ficha típica (mediana ≈ 240 palabras en `<main>`, p10 195, p90 442)
- Título SEO «Título · Autor | Libros recomendados» (≤60/75 car.), meta description plantilla: «X, de Y. Edición de Z en castellano, en tapa blanda. Consta de 80 páginas. La editorial la incluye en …».
- Sinopsis: solo 834 fichas (7 %) tienen sinopsis breve (833 como «extracto_editorial», 1 resumen propio). El resto solo tiene la descripción plantilla.
- 3.195 fichas muestran un bloque «Para quién es».
- Precios de Amazon (afiliado) por formato, ISBN-13, idioma, páginas, editorial, fecha. Enlaces a Goodreads/editorial como «reseñas» externas (no hay reseñas propias ni valoración).
- JSON-LD: `@graph` con `Book` (name, description, author Person [con @id/url solo si hay página], image, bookEdition, publisher, inLanguage, numberOfPages, bookFormat, genre, keywords, audience, isbn, datePublished, sameAs → amazon.es/dp/…), `WebPage` con `dateModified` real, `BreadcrumbList`. Sin `offers`, sin `workExample`/`exampleOfWork`, sin `ItemList`.

Página de autor (ejemplo con 1 libro)
- `<title>Libros de X: títulos y novedades | David Porto Díaz</title>`; description «X: 1 libro recomendado (…), géneros y editoriales.»
- JSON-LD `Person` (+ `knowsAbout`) + `CollectionPage` (hasPart → libros) + Breadcrumb. 11 autores tienen texto propio largo; los demás una línea plantilla («X escribe sobre todo nutrición y bienestar…»).
- Bloque FAQ visible: «¿Cuál es el último libro de X publicado en España?», «¿Qué tipo de libros escribe X?», «¿Dónde comprar…?» (sin FAQPage en JSON-LD, correcto según Google desde 2023).
- Autores con registro rico llevan sameAs a Wikipedia/BNE/VIAF/ISNI/Goodreads/Wikidata.

Superficies para máquinas
- robots.txt permite explícitamente OAI-SearchBot, ChatGPT-User, GPTBot, PerplexityBot, ClaudeBot, Claude-SearchBot, Claude-User, Google-Extended, Applebot-Extended.
- `/llms.txt` (6 KB, perfil del autor) y `/llms-full.txt` (19 KB). `/recomendaciones/llms.txt`: UNA línea por libro → 11.422 líneas, **6,9 MB**.
- IndexNow se envía en cada deploy (script propio). Sitemap único con ≈12.600 URL. Feed `.ics` de próximos lanzamientos. Búsqueda interna con Pagefind.
- Analítica: GoatCounter, Clarity, Metricool. No consta Search Console/Bing WMT en el repo (sin verificar).

Hipótesis mías, para que las critiques (no las aceptes por defecto)
1. El mayor techo es la falta de páginas hub rastreables: género × novedades («novedades de romantasy 2026»), mes («libros que salen en diciembre de 2026»), edad («libros para niños de 8 años»), próximos lanzamientos por autor. Generarlas estáticas con `ItemList` y texto propio corto.
2. 11k fichas casi plantilla pueden leerse como contenido escalado de poco valor; conviene `noindex` o no incluir en sitemap las fichas sin sinopsis ni datos diferenciales, o enriquecerlas.
3. `/recomendaciones/llms.txt` de 6,9 MB no lo consume ningún asistente: partirlo en índices por letra/género o dejarlo en un índice corto.
4. Crear páginas de autor «bibliográficas» automáticas para los ~1.100 autores con ≥2 libros sin página.
5. Las páginas de autor responden bien la intención «último libro de X»: añadir «próximo libro de X» con fecha y `dateModified`.

## Qué te pido
1. Ordena de mayor a menor impacto las 8 acciones que harías, separando Google clásico de asistentes de IA cuando el efecto difiera. Para cada una: por qué (mecanismo concreto), riesgo, cómo medirlo.
2. Critica cada hipótesis 1–5: cuál es correcta, cuál es un mito o contraproducente, y qué variante es mejor.
3. Di qué NO harías aunque se suela recomendar.
4. Si conoces herramientas o repositorios públicos (licencia libre) que encajen con un sitio estático Python + GitHub Pages para esto, nómbralos con su uso exacto; marca «sin verificar» si no estás seguro de que existan o sigan activos.
Responde en Markdown, conciso, sin introducción.
