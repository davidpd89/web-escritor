@codex Ronda 3 de 5 (auditoría SEO/GEO, sin cambiar código; comentario en español con ruta:línea). Tema: **fichas de libro e indexación**.

Mira `render_book` y `schema_synopsis` en `scripts/build-reading-catalogue.py` y una ficha cualquiera de `recomendaciones/libros/`. Solo el 7 % lleva sinopsis; el resto, descripción plantilla.
1. ¿Qué harías con las fichas sin sinopsis: `noindex`, fuera del sitemap, consolidar ediciones o dejarlas? Justifica con lo que ves y con la política de «scaled content abuse» de Google (cita la página oficial).
2. `Book`: ¿conviene añadir `workExample`/`exampleOfWork`, `offers` (precio de Amazon ya mostrado), `aggregateRating` (no hay reseñas propias: dime si sería engañoso)? Qué es elegible y qué no según Google.
3. Las ediciones de la misma obra (`group_editions`) ¿deberían compartir canónica? Riesgos.
4. Cualquier error de marcado que veas en las fichas (campos vacíos, fechas futuras en `datePublished`, `sameAs` a Amazon).
