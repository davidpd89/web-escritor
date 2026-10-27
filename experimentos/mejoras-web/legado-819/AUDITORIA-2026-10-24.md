# Auditoría independiente del circuito de mejoras — 24/10/2026

Repositorio: `davidpd89/web-escritor`. Rama auditada: `research/mejoras-web-orquestador-20261024`, PR #819 con base **exclusivamente** `lab/mejoras-web-20261024`. No se ha realizado merge a lab/main ni publicación web.

## Diagnósticos confirmados en código y correcciones aplicadas

| Nº | Impacto | Defecto verificable | Corrección | Contrato probado / pendiente |
|---|---|---|---|---|
| 1 | Alto | `Claude=investigar_mas` terminaba el expediente y elegía otro | Estado `ampliacion` hasta dos rondas sobre la misma fuente; después revisión humana | `test_cadena_simulada_sin_red` |
| 2 | Alto | Si GitHub fallaba tras commit/push, `wt.exists()` impedía terminar la PR | Reconocer PR previa o retomar desde un único commit limpio, mismos archivos y tests reejecutados; no reescribir lo sucio | `test_recuperar_pr_tras_push_sin_duplicar_otra_rama` |
| 3 | Alto | El prompt exigía código original incluso a documentación SEO; favorecía relleno | Descarte breve y campos condicionales: repo, documento o código local | `test_documentacion_sin_codigo_externo_pero_con_fecha`, `test_descartar_no_fuerza_codigo_ajeno` |
| 4 | Alto | SHA de blob aislado no probaba ruta exacta ni commit | Verificar `ruta_upstream` + `commit_upstream` + `fuente_sha` contra GitHub Contents y git/blobs + SPDX | `test_ruta_incorrecta_no_acepta_el_blob` |
| 5 | Alto | Claude validaba la idea, pero no el parche que ejecutaba después GPT | Segunda revisión estructurada `revisar_parche` antes de worktree/tests | `test_segunda_revision_de_parche_obligatoria` |
| 6 | Alto | Dos directorios de estado compartidos podían avanzar tareas simultáneamente | Lock exclusivo por PID + token y recuperación de PID muerto; estado fuera de QA | `test_un_director_y_no_dos`, `test_lock_vivo_no_reclamable`, `test_recuperacion_lock_con_pid_muerto` |
| 7 | Alto | `lab` estaba **22 commits por detrás de main** al compararlo (momento de auditoría) | Comparar archivos tocados en main desde base común antes de aplicar sobre lab; si hay colisión, no desarrollar sobre versión obsoleta | `test_lab_obsoleta_archivo_conflictivo_se_detiene` |
| 8 | Medio | Una PR creada dejaba de figurar en `actual.json` al empezar la siguiente búsqueda | Archivos por ID en `ciclo/propuestas/` y puntero `ultima_propuesta.json` | `test_previsualizar_ultima_propuesta_aunque_haya_otra_actual` |
| 9 | Medio | No existía vista directa de la propuesta | `PREVISUALIZAR-MEJORAS.cmd` sirve el worktree en 127.0.0.1:8766; puede elegir ID sin salir de local | Pruebas de ruta interna/externa y smoke real aún pendiente |
| 10 | Medio | Un archivo `.tmp` abandonado bloqueaba escrituras posteriores | Apertura `w` sobre temporal exclusivo + os.replace, bajo lock | Suite de rotación + recuperación aún pendiente de CI |
| 11 | Medio | Fallos transitorios terminaban `--continuo` al primer error; respuestas inválidas podían atascarlo | Reintentos máximos tres con backoff; `--reintentar-chat` EXPLÍCITO para invalidar CID manteniendo evidencia histórica | `test_reintento_explicito_no_duplica_sin_solicitud` |
| 12 | Medio | `-SoloVista` reservaba tareas y fallaba cuando se agotaban | Ya no consume la cola; `-Simular` se ejecuta sin necesitar Edge ni puertos | Se requiere prueba PowerShell real |
| 13 | Medio | Workflow offline duplicado en push + PR, y el filtro en pull_request omitía PRs hijas sobre código web | CI `pull_request` hacia lab sin filtro de rutas + `workflow_dispatch`, solo un disparador automático | GitHub Actions sigue pendiente en último SHA |
| 14 | Medio | Claude podía aprobar propuestas marcadas duplicadas o riesgo alto | Rechazo de duplicados, revisión humana para riesgo alto | `test_riesgo_alto_de_claude_no_desarrolla` |

## Dónde reside cada responsabilidad

- `rotacion.py`: única reserva y cierre de ideas del catálogo; semillas finitas, pero `ciclo.py` crea **sondeos continuos** cuando se agotan.
- `motor/descubrimiento.py`: GitHub REST, RSS oficial de Google Search Central y rutas de Git reales. Actividad reciente **no equivale** a eficacia ni a código correcto.
- `motor/gpt_browser.py`: adaptación original del QA de `automation/qa-gpt`, **Edge CDP 9331**, Project nuevo obligatorio.
- `motor/claude_cli.py`: Claude CLI real, coste medido por llamada y esquema JSON, dos aprobaciones separadas.
- `motor/verificar_upstream.py`: procedencia reproducible por ruta, commit, blob, literal y licencia.
- `motor/pr_laboratorio.py`: worktree hijo, rutas acotadas, tests locales y PR **draft** hacia lab; prohibido main.
- `motor/preview.py`: vista local de worktrees guardados aunque la rotación haya avanzado.
- `.github/workflows/lab-mejoras-offline.yml`: pruebas estáticas/unitarias, sin llamadas a modelos.

## Auditoría de prompts

Los contratos actuales separan: hechos observados vs hipótesis, duplicación con funciones existentes, prioridad para reutilización de código, rechazo legítimo sin código, datos originales sin adaptar, fechas de fuentes primarias y **dos revisiones Claude** (solución y parche). El lector y el revisor no deben obedecer órdenes encontradas en un README o una página externa. El código no puede garantizar que el modelo sea infalible: por eso existen campos, comprobaciones GitHub y gates de pruebas/humano.

Fuentes primarias empleadas en el canal SEO: https://developers.google.com/search/updates (confirma la dirección RSS `search_docs_updates.rss`). Repositorios originales para reutilización: `automation/qa-gpt` y https://github.com/Pagefind/pagefind . Revisar fecha/versión cada vez que cambien, sin convertir la documentación antigua en autoridad perpetua.

## Cobertura y límites HONESTOS

Hay **48 tests offline definidos** en tres ficheros (`test_rotacion.py`: 12, `test_motor.py`: 31, `test_upstream.py`: 5) en el recuento de esta auditoría. **48 definidos no significa 48 superados**. Las primeras ejecuciones del workflow pasaron en un commit antiguo. Muchos runs posteriores aparecen cancelados por actualizaciones de PR y el último commit debe verificarse por separado. No se han ejecutado Edge/ChatGPT/Claude CLI ni una PR hija real en Windows desde esta sesión.

Todavía hacen falta: comprobar el último CI verde; probar primer inicio e interrupción Q/Ctrl+C, coste/permiso de Claude, lectura real del Project GPT, PR hija y tests; comprobar el navegador a 8765/8766; revisar la coincidencia con main actualizado; medir utilidad real de la primera mejora. Los fallos de CI que pudieran aparecer no se ocultarán ni corregirán debilitando pruebas.

**Decisión:** PR #819 permanece **draft** y aislada. No declarar operación al 100 %, no mergear ni desplegar hasta superar una prueba integral real.
