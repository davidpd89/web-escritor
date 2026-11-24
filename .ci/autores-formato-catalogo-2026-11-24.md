# Autores con formato de catálogo — 24/11/2026

## Hecho y comprobado
- PR #1546 fusionada (3a9db4d70e). Deploy OK y producción verificada: listado de autores, paginación, ficha de stephen-king y enlaces de Amazon con tag (tienda del autor o búsqueda p_27).
- Backlog anotado en la issue #1556; no se arregla ahora.
- PR #1561 fusionada (adfc6a59e1). El contrato de tildes ya no marca los títulos extranjeros propios de la ficha (palabras de los campos `titulo*` del JSON de textos).
- Publicación de textos (PR #1562, automation/reading-catalogue-textos-2026-11-24-182832): falla sitewide-reflow-qa en el run 45449172316. Hay desbordes de 2 a 37 px a 320x900 con texto al 200 % más espaciado en 8 fichas: victor-dixen, tim-collins, sophie-jomain, sigmund-freud, sarah-lark, patricia-garcia-rojo, jeff-kinney e ian-stewart.
  - Causa: títulos largos (enlaces `inline-block`) en «Por dónde empezar», «Si te gusta», fuentes y obras, sin `overflow-wrap`.
  - Arreglo por método (rama autores-reflow-textos):
    - el builder marca todas las secciones de texto de autor con `.catalogue-author-text`;
    - el CSS aplica `overflow-wrap:anywhere; max-width:100%` a esas secciones, sus enlaces y el índice.
  - Comprobación local sobre el árbol de publicación (8 rutas más stephen-king como control): antes, 12 a 37 px de desborde; después, 0 px en todas.

## Pendiente
- Regenerar los artefactos (materializar_generados.py), abrir la PR del arreglo y fusionarla sin ingesta en curso.
- Volver a publicar los textos con `python scripts/reading-texts.py publish` desde .worktrees/autores. Sustituye a #1562, que se cierra sola.
- Comprobar que la publicación se fusiona y se despliega.

## Procesos activos
- Bucle de generación de textos (PID 146376, `reading-author-texts.py run --hours 24`). Arrancó el 24/11 a las 16:55 y termina el 25/11 hacia las 16:55. Hay 321 JSON en .local/reading-author-texts/out/. No lanzar otro bucle encima.
