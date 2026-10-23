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
