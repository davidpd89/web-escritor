
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
