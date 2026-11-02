# Informe de cierre · 2026-11-02

## Cambios en main
- **#1075** (5fe03828a): el radar de Amazon (Creators API) saca los ISBN de las novedades y de los próximos lanzamientos, ordenados por fecha. La ficha se construye con los datos de todostuslibros: sello, grupo, fecha, PVP, páginas, materias y descripción de la editorial. La cubierta es tipográfica y propia. De Amazon solo se usan los ISBN, en la misma ejecución: no se guarda nada ni se usan sus imágenes.
- **#1078**:
  - `concurrency` en los 71 workflows: en una PR, un push nuevo cancela la CI del commit anterior; main y los programados no se cancelan. Test `tests/test-ci-pr-concurrency.py` (sin PyYAML).
  - El Atlas y el radar de fuentes pasan a las 00:00 UTC (la 01:00 en Madrid). El sync de libros no se mueve.
  - Metas de lectura: recortan los datos de la edición antes de rendirse. En llms.txt, el «Para quién es» cede espacio para no pasar de 700 caracteres.
- **#1079**: textos de GPT para 21 fichas, ya desplegados (smoke de producción PASS, run 41498959760). Sustituye a la #1077, que se cerró.
- **Fix de la PR de textos** (`pending_batches`): el sync de libros ya no se bloquea con una PR de textos abierta (`automation/reading-catalogue-textos-*`). Tiene test (`tests/test_reading_pending_texts.py`).
- **#1080**: los títulos de las fichas con muchos autores conservan el primero («· Autor y otros»), lo que evita los títulos duplicados o sin autor que tumbaban el sync.
- **#1082**: la prueba del navegador `qa/reading-catalogue-v2-browser.mjs` deriva el reloj de la etiqueta Novedad/Próximamente a partir del primer libro del listado. Con la fecha fija del 21/10 y 341 libros ordenados por fecha (los primeros, de diciembre de 2026 a febrero de 2027), fallaba en la PR de libros #1081.

## Limpieza
- Ramas: de 757 a unas 30. Copia de los SHA en `.git/ramas-borradas-2026-11-02.txt` del repo vivo.
- Worktrees retirados: wt-amzradar, wt-amzintake, wt-ci y wt-titulos, con sus ramas.
- Cachés de pip y npm vaciadas: el disco queda con 69 GB libres (86 % ocupado).

## Verificaciones
- unittest de lectura: 878 tests OK con los textos nuevos.
- El test de concurrency detecta la mutación (quitar la `concurrency` de tool-tests).
- Sync 41500973485: 341 libros publicados (100 nuevos, 0 errores, 467 peticiones). Abrió la PR #1081, con content-index y required-merge-gate en PASS. Falló solo recommendations-browser-qa (41510646502), por la fecha fija; lo corrige la #1082.
- Sync 41517361319 tras la #1082: PASS en los 14 workflows (recommendations-browser-qa incluido), **#1083 fusionada**, Pages y smoke de producción en PASS (41525863167).

## Pendientes
- Precios de Amazon: «provider_unavailable» en 5 intentos. No bloquea, pero hay que revisarlo en el próximo sync.
- **`wt-comunidades`** (feat/comunidades-telegram-discord): es de otra sesión y no tiene PR. No se ha tocado: que lo decida David.
- **Radar de Amazon:** 82 próximos lanzamientos, muchos de ellos cómics en inglés. Solo entran los ISBN españoles en castellano.
- **Licencia de Amazon:** sus datos no se guardan más de 24 h. El radar solo usa los ISBN durante la ejecución.

## Estado final
- 341 libros publicados en producción (#1083). La #1081 se cerró sola por estar desfasada respecto a main.
- Worktree en uso: `C:\GIT\wt-textos2`, detached en origin/main, con `.local/reading-texts/main` para el bucle de textos.
- Procesos temporales del agente: ninguno activo.
