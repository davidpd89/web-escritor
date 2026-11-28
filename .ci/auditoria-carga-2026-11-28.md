# Auditoría de las cargas nocturnas — 28/11/2026

Rama `auditoria-carga-2026-11-28` (worktree `.worktrees/auditoria-carga`, base `c696d7a906`).

## Causas de los fallos (de hoy hacia atrás)

| Noche | Qué pasó | Clase | Estado |
|---|---|---|---|
| 28/11 | #1627 y #1630 (992 libros) rojas en la QA de la PR: seis tests de código de `test_reading_texts` usaban el primer libro del catálogo vivo como ejemplo; el fallo no nombraba ningún id → la cuarentena no podía apartar nada → lote perdido | fallo sin atribuir fuera de la puerta previa | test arreglado en #1628; **clase** cubierta en esta rama (pasada amplia + bisección) |
| 27/11 | `gh api pulls/files` / `compare` devolvían 422 en PR grandes | límite de la API de GitHub | #1622, #1624 (en main) |
| 27/11 | espacio del almacén de portadas | capacidad | almacén con rotación automática (esta rama) |

## Cambios de esta rama

- **Pasada amplia previa a la PR** (`check-reading-data.py --amplia`): con la puerta de datos ya verde, se corren una vez
  todos los módulos de test que leen datos reales (`reading-catalogue.json`, `data/reading`, `recomendaciones/`) y que no
  están enteros en la puerta. Después solo se repiten los que fallaron.
- **Bisección** (`scripts/biseccion_carga.py`, `bisect_unattributed` en `refresh-reading-catalogue.py`): un fallo sin
  libro se atribuye buscando, entre los libros nuevos o cambiados, cuál lo provoca (1+log2 n sondas por culpable,
  todas las del catálogo restauradas al terminar). El culpable va a cuarentena como cualquier otro.
  - Si ni quitando toda la carga pasa → no se pudo atribuir (código, o un dato que no vive en el JSON): en la etapa
    de código se avisa y se publica (decide la PR); en la de datos se para como antes.
  - Plazo: antes de **cada** sonda (también la inicial y las de confirmación) se mira `PUBLICAR_HASTA − 75 min`.
    Límite real: una sonda ya empezada puede durar hasta 1800 s por grupo, y sin `PUBLICAR_HASTA` numérico no hay corte.
  - Robustez (ronda GPT 2): el fallo debe reproducirse con la carga entera antes de buscar; el arreglo debe pasar dos
    veces; una sonda que no se puede evaluar (puerta sin `fallos.json`, módulo «sin terminar») lanza `SinResolver` y
    no se aparta nada; un libro que solo cambia de géneros también es candidato.
- **Puerta paralela** (un módulo por proceso, `--solo`, límite por grupo 1800 s): 119 contratos de ~23 min a minutos.
- **Almacén de portadas automático** (`almacen_portadas.py auto`, tarea `WEB_Libros_Almacen_Portadas` 10:40): con el
  activo por encima de 700 MB prepara el siguiente repo de Pages; `nuevo` es reanudable.
- Telegram/Discord (web) y Pinterest/RRSS (`portada_web.py`) leen el mismo formato `almacenes`/`almacen` → encuentran
  portadas de cualquier almacén.

- **Ronda GPT 3 (revisión)** y revisión de CodeRabbit/Codex en #1634, aplicadas:
  - la puerta corre los tests sin el almacén de portadas vivo ni credenciales (`entorno_de_prueba`): un fixture de
    ingesta podía publicar una portada sintética en producción;
  - los hijos heredan `sys.path` (PYTHONPATH) — arregla el rojo de offline-tests;
  - 0 tests corridos = fallo, salvo módulos en script (aserciones al importar); un hijo con rc≠0 sin fallos listados
    (expectedFailure que pasa) = fallo;
  - `setUpClass (mod.Clase)` se repite por su clase; un módulo que no importa por código abandona la bisección;
  - tras apartar libros por la pasada amplia, la pasada amplia **entera** se repite antes de aceptar;
  - `almacen_portadas auto`: solo «variable no encontrada» usa el primer almacén; otro error no toca nada.
- **Ronda GPT 4 (escala)**: Cloudflare Pages/Workers Assets: 20k ficheros (Free), 100k (pago). Repo: 30611 ficheros,
  11757 html → margen, pero vigilar (memoria cf-workers-reparto, #1623). El token de la App (1 h) se genera justo antes de
  `gh pr create` (`publish-radar-refresh.app_env`), no al empezar el paso: comprobado, sin cambio.

## Verificado (local)

- `test_biseccion_carga` (16), `test_almacen_portadas`, `test_check_reading_data_procesos`, `test_night_faults`,
  `test_reading_source_recovery`: 58 tests OK. `test_check_reading_data_cobertura` OK.
- Puerta completa local (28/11): 157 contratos en 966 s + 24 en script en 355 s; único fallo, el módulo en script
  `test_reading_itemlist_detail_title_parity` con la regla de 0 tests → corregido y comprobado (rc 0).
- `test_reading_quarantine` + `test_check_reading_data_procesos`: 57 OK. Bisección, almacén, procesos, night_faults: 49 OK.
- Puerta paralela: 13 contratos en 46 s, rc 0. Tarea del almacén registrada; su ejecución: «518564 KB, sin cambios».

## Pendiente

- Prueba real en Actions (carga completa con la rama en main).
- Pasada amplia local: 645 tests en 13 min 45 s con 4 procesos, 0 fallos (rc 0) — sin exclusiones.

## Backlog (no bloquea)

- Guardián estático de fixtures que indexan el catálogo vivo: descartado por falsos positivos (la mayoría de
  `['libros'][0]` son sintéticos); la bisección cubre la clase en ejecución.
- Sondas solo sobre JSON: un test que lea páginas generadas y no se arregle quitando libros del JSON devuelve «sin
  culpable» (código: avisa y publica; datos: para).
- Reparto de python-tests en shards; test de crecimiento simulado de la puerta.
