# qa-gpt — descubrimiento QA asistido por ChatGPT (solo descubrimiento; sin ejecucion de tests)

Comandos (`scripts\qa-gpt.cmd <cmd>`): `estado`, `iniciar [--ahora]` (tarea programada diurna), `pausa`/`reanudar`, `parar`, `quitar-servicio`,
`inventario`, `aceptadas [--todas]`, `pendientes`, `aprobar <ids|todas>`, `fallos`, `recuperar --job N [--chat ID]`, `reabrir <ids>` (propuesta atascada → PASS B), `descartar <id> --motivo`, `simular --rondas N` (rotacion sin gastar peticiones), `scan-once [--manual]`,
`autorizar-noche` + `lote-nocturno --confirmar` (UNICO camino que publica PR/lanza Actions; exige autorizacion del dia), `informe-matinal`.

- Lectura de la respuesta por el backend del chat (no DOM); chat_id persistido para reanudar sin reenviar; respuesta vacia/invalida nunca es exito.
- Modos rotativos: zona, tipo, familia (matriz de cobertura), cambio, auditoria. Tecnicas abiertas (semilla + descubiertas). Dedup por huella conductual.
- Ciclo: propuesta → revisar → aceptada/rechazada/bloqueada (siempre con `siguiente`) → preparada (rama local) → aprobada → publicada → ejecutada.
- Servicio continuo con arranque/parada manual (INICIAR-QA-GPT.bat, PARAR-QA-GPT.bat, ESTADO-QA-GPT.bat). Sin horario, cupos ni esperas entre rondas correctas; solo backoff ante limites reales de ChatGPT. 1 worker. Estado fuera de Git: C:GITqa-gpt-state. Tests/Actions solo con autorizar-noche + lote-nocturno --confirmar.
- Instrucciones del Project: `project_instructions.md` (pegado manual en Ajustes del Project).
- Pruebas offline: `python scripts/qa-gpt/test_qa_gpt.py` (sin navegador ni GPT). Recuperacion: rama `automation/qa-gpt` + `.ci/qa-gpt/estado.pre-fix.db`.

## EJECUTAR-ACTIONS-QA-GPT.bat (4.º BAT)
Doble clic = autorización. Procesa las propuestas `preparada` existentes en ese momento: valida en local (worktree desacoplado + merge de origin/main), clasifica (local_ok / defecto_demostrado / fallo_test / infra / sin_entorno), empuja solo `gpt-qa/*` por sha y lanza `workflow_dispatch` del workflow que realmente ejecuta el test. Sin PRs, sin tocar main. Idempotente (lock + clave rama@sha), reanuda lotes abiertos y reconcilia con GitHub. Tests: `python scripts/qa-gpt/test_qa_lote.py`.
Requisito para ramas que modifican workflows: `gh auth refresh -s workflow`.

## Flujo Claude -> GPT -> PR (hilo `flujo-pr` dentro de EJECUTAR)
- INICIAR: arranca el worker GPT; PARAR (o Q / Ctrl+C / cerrar ventana) lo detiene sin marcar fallos (`interrumpida`); al reabrir se retoma sin duplicar PR (se vincula la rama existente).
- EJECUTAR: lanza Actions (max 3 grupos), agrupa, y el ciclo (`Ciclo.paso`, cada `flujo.ciclo_s`) decide con Claude, encola desarrollos de GPT solo para `corregir`, valida (baseline en main, parche, verificadores), abre PR hasta `max_pr_activas`, revisa con Claude cuando el CI esta verde.
- Integracion: modo `recomendacion` por defecto; `auto` solo tras `calibracion_min` y con riesgo bajo y CLEAN. Nunca `--admin`.
- Claude: CLI headless, `claude-sonnet-5-5`, esfuerzo low, JSON con esquema, cache por hash. Consumo en tabla `claude_llamadas` (visible en ESTADO).
- ESTADO: cifras reales; tecla C copia el informe.
- Recuperar: la BD `C:\GIT\qa-gpt-state\estado.db` conserva todo; copias en `backups\`. Migraciones idempotentes.
