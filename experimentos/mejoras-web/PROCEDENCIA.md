# Procedencia del codigo reutilizado del QA GPT

Referencia funcional: rama `automation/qa-gpt`, commit `fe131c8ce6a663b54ab067ea5bc123318ececbb0` (cabeza de la rama en el momento de la adaptacion), carpeta `scripts/qa-gpt/`.
Cada modulo adaptado lo declara tambien en su docstring (`PROCEDENCIA:`); `tests/test_procedencia.py` comprueba que los blobs citados son los reales.

| Modulo del laboratorio (`motor/`) | Origen en el QA (ruta @ blob) | Que se conserva literal | Que cambia |
|---|---|---|---|
| `gpt_browser.py` | `gpt_browser.py` @ `01ba6c7b92863948ce39248c4eae1681eac92935` | Lectura del backend de ChatGPT (no del DOM), reanudacion por chat id, recargas, limpieza de pestanas, limites, login | Puerto 9331; Project configurable y **se rechaza el del QA**; puertos 9230/9224/9225 prohibidos |
| `edge_launcher.py` | `edge_launcher.py` @ `8bdc21f28c0d475156819233c45f49237eb8ee4d` | Banderas de Edge, sondeo CDP, reutilizacion | Puerto 9331; perfil `%LOCALAPPDATA%\web-escritor-mejoras-web\edge-perfil`; se rehusa arrancar con puerto/perfil del QA |
| `claude_cli.py` | `qa_claude.py` @ `56189d8f2c8aa4fa7071b7143f5e90f4f13c9a6e` | `claude -p` headless con esquema JSON, cache por hash, lock, rotacion de cuentas por limite, registro de coste | `exe()` nativo/`MEJORAS_WEB_CLAUDE_EXE`; tope diario de gasto (`max_usd_dia`); sin cuentas extra heredadas |
| `clases.py` | `qa_clases.py` @ `d26c90d1bc8cf3d4fc8269da246f2bef7728df2c` | Expresiones y `clasificar_salida` (ok/sin_entorno/invalido/infra/hallazgo) | `estado_remoto()` en lugar de `estado_por_categoria()` |
| `ci_grupo.py` | `ci_grupo.py` @ `f56e5114db9ba0a44f6d0a245e7b83686898463e` | Runner del workflow: validacion de rutas, servidor local, aborto de arboles, resultados.json atomico | Solo `tests/mejoras-web/**`; modo unico `aceptacion` |
| `actions.py` | `qa_lote.py` @ `644aa2884fa672f88d28f7ea67e58b62358d63dd` + `qa_cobertura.py` @ `ea94e2ebf1c07123ba2a1ddcb06dbfb6e91c6a2e` | `run_cmd`, `ServidorEstatico`, validacion local abortable, `enviar`/`reconciliar`/`veredicto_remoto`, recuperacion de runs/artefactos/logs, bucle con tope de 3 grupos, parada que no cancela, `instalar_parada` | **Excluido**: `pr_auto`, `pr_merge`, `pr_cerrar --delete-branch`, `pr_actualizar`, `rerun_fallidos`, ramas `gpt-qa/*`, `Ciclo`, Via A, triaje, `estado.db` del QA. **Anadido**: `AUTORIZADO` (solo EJECUTAR despacha), linea base (el test debe fallar sin el cambio), run-name `sha #intento`, tope diario de envios |
| `parches.py` | `qa_pr.py` @ `aaa0a0404a8ef058c1c28543bc44f918d043c995` | `ruta_segura`, `validar_parche`, `aplicar_parche` (sustituciones exactas de un fragmento unico) | `ficheros_nuevos`, tests de aceptacion, procedencia de codigo externo, worktree desde `origin/lab/...`. **Excluido**: `Pr.preparar`, `Ciclo`, integracion/fusion |
| `supervisor.py` | `qa_supervisor.py` @ `13222b998e8bbfb590716b0cfd9621a55dbfdc63` | Hijo supervisado, `REINICIO=75`, firma de traceback | **Excluido**: reparacion automatica del codigo por Claude y PR de main en rojo |
| `mw.py`, `investigar.py` | `qa_gpt.py` @ `010ae0137d3307e1c5f3050ecbfc21c97bb40252` | `Conn` (rollback en 'database is locked'), WAL, `Lock`, `marcar`/`dormir`, `load_json_block`, jobs GPT reanudables (`process`/`fallo`), servicio continuo, `cmd_iniciar`/`cmd_parar` | Estado y cola propios; rotacion area x lente por epocas en lugar de zonas/familias/tipos; `Lock` y `pid_alive` tambien en Linux |
| `pr_hija.py` | `qa_pr.cuerpo_pr` y `qa_lote.Gh.pr_de_rama` | Estructura del cuerpo de PR y deteccion de PR existente | La base es SIEMPRE la rama de laboratorio; sin merge/auto-merge |
| `.github/workflows/mejoras-web-grupo.yml` | `qa-gpt-grupo.yml` | `workflow_dispatch`, driver desde el commit del workflow, artefacto de resultados | Entradas `sha/modo/tests/intento`; `run-name` con `sha #intento`; Node/Playwright solo si hay tests `node:`; sin fusion con main |

## Defecto encontrado en el QA original (NO modificado)
`scripts/qa-gpt/qa_gpt.py:537` (rama de limite de uso de ChatGPT en `process`): `UPDATE jobs ... error=?,no_antes=?,actualizado=? WHERE id=?` recibe 3 valores para 4 marcadores
(`sqlite3.ProgrammingError`), de modo que un limite de uso de ChatGPT tumba el paso en vez de pausarlo. El laboratorio lo corrige en `investigar.procesar_job` y tiene su test.

## De la PR #819 (lo que se conserva)
`motor/verificar_upstream.py` (blob/commit/ruta/licencia contra GitHub REST, sin cambios) y `motor/descubrimiento.py` (pistas opcionales GitHub/RSS, solo docstring). Reescritos: `preflight.py`, `preview.py`.
Retirados (sustituidos por el motor del QA, sin dos orquestadores): `ciclo.py`, `pr_laboratorio.py`, `claude_cli.py`, `gpt_browser.py`, `rotacion.py`, `verificar.py`, `catalogo.json` y los `.cmd/.ps1`. Documentos historicos en `legado-819/`.
