# Laboratorio de mejoras web (motor QA GPT adaptado)

Sistema que busca **sin fin** mejoras reales para davidportodiaz.com y las lleva hasta una PR hija en borrador, con la misma arquitectura que el QA GPT
(`automation/qa-gpt`) pero **totalmente separado**: otro Edge (CDP 9331), otro perfil, otra base SQLite, otras ramas, otros bloqueos, otro workflow.
Nada se fusiona solo ni toca `main`.

```
 INICIAR-MEJORAS-WEB.bat            EJECUTAR-ACTIONS-MEJORAS-WEB.bat                     (accion explicita)
 ┌──────────────────────────────┐   ┌─────────────────────────────────────────────┐    ┌────────────────────────┐
 │ GPT investiga  (job I)       │   │ validacion LOCAL en worktree separado       │    │ mw.py pr ID --confirmar │
 │ Claude contrasta             │   │ cola persistente (rama@sha, tests, runs)    │    │ PR hija EN BORRADOR →   │
 │ GPT desarrolla (job D)       │ → │ ≤3 grupos a la vez en Actions (dispatch)    │ →  │ lab/mejoras-web-2026... │
 │ Claude revisa el parche      │   │ recoge runs/artefactos, clasifica, no       │    │ (nunca fusiona)         │
 │  → expediente `preparado`    │   │ duplica envios por rama+SHA                 │    └────────────────────────┘
 └──────────────────────────────┘   └─────────────────────────────────────────────┘
        sin Actions, sin PR                 solo al pulsar EJECUTAR
```

## Los cuatro lanzadores (esta carpeta)

| Archivo | Que hace |
|---|---|
| `INICIAR-MEJORAS-WEB.bat` | Preflight (`--real`), abre el Edge 9331 y arranca/reanuda el investigador supervisado en segundo plano. **No envia Actions ni abre PR.** Pulsarlo dos veces no duplica nada; tras un cierre brusco reanuda los chats por su id sin reenviar. |
| `EJECUTAR-ACTIONS-MEJORAS-WEB.bat` | Proceso continuo y manual: valida en local lo `preparado`, mantiene hasta 3 grupos en Actions, recoge resultados y envia el siguiente. `Q`/`Ctrl+C`/cerrar ventana = dejar de lanzar; **los runs ya enviados no se cancelan** y se recogen al reabrirlo. |
| `ESTADO-MEJORAS-WEB.bat` | Expedientes por fase (investigados, descartados, preparados, en ejecucion, finalizados), gasto Claude, errores, cola con SHA y URL de runs, que esta listo para PR. `C` copia el informe completo. |
| `PARAR-MEJORAS-WEB.bat` | Parada limpia del investigador y del ejecutor, con gracia para capturar la respuesta en curso. **No cancela runs remotos.** |

Los `.bat` buscan Python 3.10+ solos (`MEJORAS_WEB_PYTHON`, `where python`, `py -3`, `%LOCALAPPDATA%\Programs\Python`, `%ProgramFiles%`), descartan el alias vacio de la Microsoft Store y
muestran un mensaje claro si falta algo.

## Instalacion en tu PC (una vez)

1. Clona o actualiza el repositorio en una carpeta/worktree **propio del laboratorio** (no el del QA):
   ```powershell
   git fetch origin main
   git worktree add ..\web-escritor-mejoras origin/main -b lab/mejoras-local
   cd ..\web-escritor-mejoras\experimentos\mejoras-web
   ```
2. Python 3.10+ y `pip install playwright` (solo se usa para hablar con Edge por CDP; no hace falta `playwright install`).
3. Microsoft Edge, `gh` (con `gh auth login` y scope `workflow`: `gh auth refresh -s repo,workflow`) y, para tests `.mjs`, Node 22 y un `node_modules` con Playwright (opcional; se enlaza si pones su ruta en `config.json` → `actions.node_modules`, por defecto `<estado>\node_modules`; **no se reutiliza el del QA**).
4. Claude Code CLI **nativo** (`claude`), con sesion iniciada. Se localiza en `MEJORAS_WEB_CLAUDE_EXE`, `~\.local\bin\claude.exe`, el paquete npm o el PATH.
5. Crea un **Project de ChatGPT nuevo** (instrucciones en `project_instructions.md`, conector de GitHub al repo) y pon su id `g-p-...` en `config.json` → `gpt.project_id` (o `MEJORAS_WEB_PROJECT_ID`). El id del Project del QA se rechaza.
6. El laboratorio comparte con el QA el Project de ChatGPT (`gpt.project_id`) y el perfil de Edge `C:\Temp\web-escritor-qa-gpt-edge` (sesion ya iniciada), pero en el puerto 9331. QA y laboratorio NO pueden correr a la vez: cierra el QA (y su Edge) antes de `INICIAR-MEJORAS-WEB.bat`. Las instrucciones del Project son las del QA; los prompts del laboratorio llevan su contexto completo en cada chat.

Estado persistente (fuera de Git): `%LOCALAPPDATA%\web-escritor-mejoras-web\estado\` (`mejoras.db`, `servicio.log`, `actions\ejecutar.log`, `respuestas\`, `wt\`). Se puede mover con `MEJORAS_WEB_STATE`.

## Pruebas offline (no usan Edge, modelos, GitHub ni Actions)

```powershell
pip install pyyaml            # opcional: sin el, se omiten las pruebas que leen los workflows
python motor\preflight.py --offline
python -m unittest discover -s tests -p "test_*.py" -v
```

## Comandos utiles (`python motor\mw.py ...`)

| Comando | Para que |
|---|---|
| `estado [--completo]` | Lo mismo que ESTADO |
| `validar [ID]` | Validar en local los `preparado` **sin** GitHub (ni push ni dispatch) |
| `vista-previa [ID]` | Servir en `127.0.0.1:8766` la rama base del laboratorio o la candidata de un expediente |
| `pr ID [--confirmar] [--solo-local]` | Preparar la PR hija **en borrador** hacia `lab/mejoras-web-20261024`. Sin `--confirmar` solo muestra lo que haria |
| `reintentar-infra ID` | Pedir un envio nuevo (intento 2, 3...) tras un fallo de infraestructura. Nunca ocurre solo |
| `descartar ID --motivo ".."` | Descartar a mano un expediente |

## Garantias de aislamiento y de coste (con su prueba)

* **Edge/CDP**: 9331 y perfil propio; 9230/9224/9225 y el perfil del QA se rechazan al arrancar (`test_servicio.Aislamiento`).
* **Estado**: carpeta propia fuera de Git; nunca `C:\GIT\qa-gpt-state` ni `estado.db` del QA. Sin bloqueos, colas ni limites compartidos (`Lock` propios: `worker`, `actions`, `supervisor`).
* **Ramas**: solo `mejoras-web/<id>` (push) y PR hacia `lab/mejoras-web-20261024`. `main`, `lab/*`, `gpt-qa/*`, `qa-fix/*`, `research/*` rechazadas (`mw.rama_permitida`; `test_integracion_git` con un remoto real).
* **Actions**: el unico `workflow_dispatch` del laboratorio esta en `actions.Gh.dispatch` y exige `AUTORIZADO`, que solo concede `actions.main` (EJECUTAR). INICIAR no puede despachar (`test_servicio.InicioSinEfectosRemotos`). Maximo 3 grupos (`MAX_GRUPOS`), 12 envios/dia (`actions.max_envios_dia`), un run por `sha #intento`.
* **Sin acciones peligrosas**: no hay fusion, auto-merge, cierre/borrado de ramas, `rerun`, `cancel` ni push forzado en ningun modulo (`test_codigo_fuente_sin_ordenes_peligrosas`).
* **Claude**: sin herramientas de escritura (`Read,Grep,Glob`), tope por llamada (0,5 USD) y diario (`claude.max_usd_dia`, 10 USD), cache por hash y cada llamada registrada con coste y tokens. **ChatGPT**: una peticion a la vez, `flujo.consultas_gpt_por_hora`.
* **Tests escritos por GPT**: se ejecutan en tu equipo (igual que en el QA). Antes de aceptarlos se rechazan los que usan `subprocess`, `os.system`, sockets, red, `eval/exec`, escritura o borrado de ficheros, `child_process`, etc. (`parches.validar_pruebas`). Es una barrera de higiene, **no un sandbox**: revisa de vez en cuando `tests/mejoras-web/` de las candidatas antes de pulsar EJECUTAR.
* **Parches**: sustituciones exactas de un fragmento unico; se rechazan ficheros con fin de linea CRLF (convertirian el archivo entero), rutas sensibles y secretos.
* **Parada**: `PARAR` activa dos banderas (`stop`, `stop_actions`); arrancar EJECUTAR no borra la parada del investigador, y un EJECUTAR largo nunca es terminado por otro que arranca.
* **Rama base**: se hace `git fetch` de `origin/lab/mejoras-web-20261024` cada 20 min y, si no existe en tu clon, el preflight lo dice con el comando exacto.
* **Rama de desarrollo**: ningun disparador automatico. Los workflows del laboratorio son solo `workflow_dispatch`; los commits que tocan `experimentos/mejoras-web/**` y los workflows nuevos no coinciden con los filtros `paths` de los workflows existentes con `push` sin rama (cuaderno).

## Dependencia de rama del workflow

GitHub solo despacha un workflow que existe en la rama que se pasa a `--ref`. `config.json` -> `workflow_ref` es `lab/mejoras-web-20261024` (la rama de integracion del laboratorio, que contiene
`mejoras-web-grupo.yml` y el driver `motor/ci_grupo.py`). No uses `main` ni una rama de desarrollo que vayas a borrar al fusionar su PR: EJECUTAR comprueba al arrancar que el workflow existe en
`workflow_ref` (y `preflight --real` lo avisa); si no, valida en local y no envia nada. Si el dispatch no crea ningun run en `actions.espera_run_min` (10 min), el item pasa a `revision_humana`.
El workflow checkoutea el `sha` de la rama `mejoras-web/*` (publicada por EJECUTAR) y toma el driver del commit del workflow.

## Enlace verificable de la web con las mejoras (documentado, NO activado)

* **Local, siempre disponible**: `python motor\mw.py vista-previa` sirve la rama base del laboratorio (la web «como si fuera main pero con las mejoras aceptadas») y `vista-previa MW-0001` una candidata.
* **Enlace publico**: `.github/workflows/mejoras-web-preview.yml` (solo `workflow_dispatch`, con confirmacion escrita `PUBLICAR-PREVIEW`). Monta el sitio de `lab/mejoras-web-20261024`, lo marca `noindex` y lo sube como artefacto; si existen el secreto `CLOUDFLARE_API_TOKEN`, el secreto `CLOUDFLARE_ACCOUNT_ID` y la variable `MEJORAS_WEB_PAGES_PROJECT`, lo publica en un proyecto de **Cloudflare Pages separado** como rama `lab-mejoras-web` →
  `https://lab-mejoras-web.<proyecto>.pages.dev`. No usa GitHub Pages ni toca el despliegue de produccion. Para activarlo: crear el proyecto de Pages, anadir esos tres valores y lanzar el workflow a mano. Pasar a `main` solo cuando David lo ordene.

## Que se conservo y que se retiro de la PR #819

Ver `PROCEDENCIA.md` (tabla completa) y `legado-819/INDICE.md`. Resumen: se conservan `verificar_upstream.py` y `descubrimiento.py` (pistas opcionales); se reescriben `preflight.py` y `preview.py`;
se sustituyen por el motor del QA `ciclo.py`, `pr_laboratorio.py`, `claude_cli.py`, `gpt_browser.py` y `rotacion.py`; no hay catalogo fijo: la rotacion area × lente (100 pares) cambia de orden en cada vuelta y no se agota.

## Estado de integracion
El laboratorio ya esta en `main` (#959). Las mejoras aceptadas se acumulan en `lab/mejoras-web-20261024` mediante PR hijas (`mejoras-web/<id>` -> lab, en borrador, `mw.py pr`); pasar a `main` solo cuando David lo ordene.
