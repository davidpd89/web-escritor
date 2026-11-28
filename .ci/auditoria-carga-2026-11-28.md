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
  - Si ni quitando toda la carga pasa → no es un dato: en la etapa de código se avisa y se publica (decide la PR);
    en la de datos se para como antes.
  - Plazo: se corta a `PUBLICAR_HASTA − 75 min` para que siempre quede tiempo de abrir la PR.
  - Robustez (ronda GPT 2): el fallo debe reproducirse con la carga entera antes de buscar; el arreglo debe pasar dos
    veces; una sonda que no se puede evaluar (puerta sin `fallos.json`, módulo «sin terminar») lanza `SinResolver` y
    no se aparta nada; un libro que solo cambia de géneros también es candidato.
- **Puerta paralela** (un módulo por proceso, `--solo`, límite por grupo 1800 s): 119 contratos de ~23 min a minutos.
- **Almacén de portadas automático** (`almacen_portadas.py auto`, tarea `WEB_Libros_Almacen_Portadas` 10:40): con el
  activo por encima de 700 MB prepara el siguiente repo de Pages; `nuevo` es reanudable.
- Telegram/Discord (web) y Pinterest/RRSS (`portada_web.py`) leen el mismo formato `almacenes`/`almacen` → encuentran
  portadas de cualquier almacén.

## Verificado (local)

- `test_biseccion_carga` (16), `test_almacen_portadas`, `test_check_reading_data_procesos`, `test_night_faults`,
  `test_reading_source_recovery`: 58 tests OK. `test_check_reading_data_cobertura` OK.
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
