
## Actualizacion (continuacion de sesion)

Comprobado:
- #1: causa raiz = `como_ejecutar` era prosa libre de GPT, sin validador de codigo. Ahora `normalizar_comandos` (qa_cobertura.py) lo convierte al ingerir en pasos argv explicitos (`python|node <fichero declarado>` + env validadas), sin shell. `qa_lote.comandos` usa esos pasos. 6 tests nuevos; suite `test_qa_gpt` + `test_qa_lote`: 43 OK.
- Mutacion en aislado (worktree origin/main, descartado): #7 mato 8/9 mutantes (sobrevive restaurar orden de disponibilidad); #8 y #10 = defectos reales demostrados (fallan en main, pasan con arreglo minimo en build-sitemap.py, reading_planeta_source.py, build-reading-catalogue.py:563); #1 y #2 pasan y matan mutantes.
- Commit 6bdd46e7 en automation/qa-gpt.

NO hecho / pendiente (no marcar como validado):
- #11: falta cablear `qa/reading-market-url-parity-browser.mjs` en recommendations-browser-qa.yml (paths + paso run) y test de cableado; Playwright local no ejecutado.
- #3: Playwright local y analisis del scope `workflow` (accion de usuario: `gh auth refresh -s workflow`) sin hacer.
- Re-normalizar datos existentes en estado.db y `reabrir 1/2`: no hecho (servicio vivo, PID 37904 con codigo antiguo en memoria; requiere reinicio del worker para aplicar la normalizacion).
- Auditoria BAT con simulaciones, contadores/panel, estimacion de coste Actions: no hecho.
- Lote real de Actions NO lanzado; servicio y puertos 9224/9225/9230 intactos.

## Cierre de la auditoria (2026-10-23, tarde)

Comprobado:
- Pruebas: `test_qa_gpt` + `test_qa_lote` + `test_qa_migrar` = **61 OK** (antes 43). Incluyen cableado (workflow que omite el test, comentarios, `*` suelto, sin workflow_dispatch), token sin permisos, lock, panel, migracion (ensayo, idempotencia, rollback, backup, ejecutadas/publicadas intactas), coste.
- Bugs reales hallados y corregidos: falso cableado por un `*` suelto; BAT siempre SIN_ENTORNO por el puerto 4173 ocupado (`puerto_libre`/`entorno_url`); regex de `entorno_url` con un caracter de control; `LoteLock` fallaba si no existia la carpeta de estado; filtro del BAT ("Proximo pendiente").
- #11: SHA 0d77c4e8 cablea el test (paths + paso run). Playwright local: **defecto_demostrado** (`valoracion: la URL anuncia un filtro que ya no se aplica`). Log `qa-gpt-state/auditoria/11-local.log`. Escenario `descuento` no llego a ejecutarse.
- #3 (7664eb25): Playwright local PASS (156 documentos, 2m11s). Unico bloqueo para publicar: scope `workflow`.
- #7 (a16014e3): el mutante "reset sin restaurar orden" sobrevivia (laguna real) y ahora muere. Superviviente `availability->return 0` = equivalente (sort estable sobre instantanea en orden original); documentado, no forzado. La lista original de 9 mutantes no se pudo reconstruir: solo se reprobaron 3.
- #8 y #10: siguen fallando por aserciones con el codigo actual (los ficheros fuente no cambian entre su rama y origin/main 78188455). Logs `auditoria/*-reverif.log`.
- Migracion `estado.db`: copia `backups/estado-pre-migracion-20261023T195137.db`, 13 propuestas normalizadas, 4 omitidas (ejecutada/publicada), contadores identicos, idempotente. Actualizados sha de #7 y #11 y parche de workflow de #11.
- Worker reiniciado en parada limpia: unico pythonw (pid 5488), Edge 9230 vivo, reglas nuevas. `reabrir 1 2` hecho (un solo job PASS B; la 2a llamada se absorbio sin duplicar). #9 y #14 siguen bloqueadas.
- BAT: EJECUTAR simulado con estado vacio (no cierra tras error, muestra panel, pausa); ESTADO ok; INICIAR/PARAR usados de verdad.
- Coste (tabla `coste-actions`): editoriales 2 jobs ~6m21s reloj/~2 min facturable; recomendaciones ~3m59s/~4 min; newsletter ~1m14s/~2; paridad ~2m13s/~3; cambio-reciente ~0m18s/~1 (medianas de n=5 runs anteriores, no garantia).

NO hecho / pendiente:
- **NO se lanzo el lote real** ni ninguna Action. Los 5 tests siguen "escritos, sin ejecutar".
- Accion de David: `gh auth refresh -s workflow` (desbloquea #3 y #11, que modifican workflows).
- Simulaciones con GitHub real (caida, cola) cubiertas solo con FakeGh; no se probo contra GitHub.
- Reevaluaciones PASS B de #1/#2 en curso en el worker; resultado pendiente.
- Commits locales en `automation/qa-gpt` sin push.
