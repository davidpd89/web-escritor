# QA-GPT 2026-10-24: ventanas negras, informe con C, auditoria de pruebas pendientes

## Causa de las ventanas negras
El worker corre con pythonw (DETACHED_PROCESS, sin consola). Cada git/powershell/tasklist hijo sin CREATE_NO_WINDOW abre su propia ventana. El 100 % de las invocaciones carecia del flag. Ahora todo pasa por `qa_cobertura.run/popen` (flag + stdin DEVNULL + GIT_TERMINAL_PROMPT=0, GH_PROMPT_DISABLED=1; el GCM grafico y los errores siguen visibles).

## Cambios
- qa_cobertura.py: run/popen, cache de lecturas git (memoria + disco).
- qa_gpt.py: sh/git via cob.run; `reparar_perdidas`; rollback selectivo en `stage()` (antes `reset --hard`+`clean` borraba propuestas ya preparadas); subcomando `informe [--copiar]`.
- qa_lote.py: un ls-remote, un for-each-ref, un fetch por lote; junction nativa (sin cmd mklink); `capturar` llama a `reparar_perdidas`.
- qa_viaa.py, qa_coste.py: cob.run/popen.
- ESTADO-QA-GPT.bat: tecla C copia el informe (Set-Clipboard), S sale.

## Verificaciones
- Procesos git: ESTADO 71 -> 39 (frio) -> 6 (caliente). Lote de 3 ramas/45 tests: 34 git + 3 cmd (todos con ventana) -> 20 git, 0 cmd, 0 sin NO_WINDOW. Extrapolado a 68 ramas: ~770 -> ~300 git (no medido).
- Copia: via el BAT, 12968 caracteres, 176 lineas, verificado con Get-Clipboard; acentos OK.
- Ensayo local reanudable: pasada cortada a 80 s, la 2a reanudo el lote #1 sin duplicados (199,8 s). Resultado de los 3 items: a_triar (pruebas exploratorias que fallan por aserccion).
- Pendientes ejecutables: 991/991 (611 .mjs + 396 .py), sin rutas ni huellas duplicadas, 78 ramas. 12 estaban sin fichero en su commit por el bug de rollback: reparadas a `aceptada`.
- Por que ESTADO muestra 0 validadas / 0 aprobadas: la aprobacion es el clic de EJECUTAR y la validacion local ocurre despues; antes es normal que sea 0.
- Tests: test_qa_lote 32 OK, test_qa_gpt 22 OK, viaa 4 OK, migrar 7 OK, contratos 3 OK.

## Pendiente / no comprobado
- El worker (PID 29292) sigue con el codigo viejo en memoria: hay que PARAR/INICIAR para cargar los cambios (no se reinicio para no interrumpirlo).
- No hay pruebas unitarias nuevas de reparar_perdidas, rollback de stage, cob.run ni informe (cubiertos solo por ensayo manual).
- Las 991 no se ejecutaron en Actions (por indicacion).
