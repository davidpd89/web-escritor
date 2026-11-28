@codex Ronda 2 de 5 (auditoría SEO/GEO, no cambies código; responde en un comentario, en español, con ruta:línea). Tema: **páginas de autor como entidad**.

Esta PR añade 1.120 fichas bibliográficas (`data/reading-authors.json`, regla `ensure_author_records` en `scripts/reading_intake_pipeline.py`) para que todo autor con ≥2 libros tenga página. Revisa `render_author`, `author_faq` y `similar_authors` en `scripts/build-reading-catalogue.py` y dime:
1. Qué falta en el marcado `Person`/`CollectionPage` para que Google y los asistentes identifiquen sin ambigüedad a la persona (sameAs, `@id` estable, `knowsAbout`, `mainEntityOfPage`, Wikidata). Qué sería inventar datos y no debe hacerse.
2. Si la descripción plantilla de las fichas nuevas («Libros de X incluidos en este catálogo: …») es contenido fino y cómo mejorarla solo con datos que ya tenemos (géneros, editoriales, fechas, próximos lanzamientos).
3. Riesgos de homónimos (dos autores con el mismo nombre) y de nombres mal partidos, mirando `split_authors`.
4. Una prioridad concreta para conseguir que las IA respondan «¿cuál es el próximo libro de X?» citando esta web.
