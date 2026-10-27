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
   git fetch origin research/mejoras-web-motor-qa-20261027
   git worktree add ..\web-escritor-mejoras origin/research/mejoras-web-motor-qa-20261027 -b lab/mejoras-local
   cd ..\web-escritor-mejoras\experimentos\mejoras-web
   ```
2. Python 3.10+ y `pip install playwright` (solo se usa para hablar con Edge por CDP; no hace falta `playwright install`).
3. Microsoft Edge, `gh` (con `gh auth login` y scope `workflow`: `gh auth refresh -s repo,workflow`) y, para tests `.mjs`, Node 22 y un `node_modules` con Playwright (opcional; se enlaza si pones su ruta en `config.json` → `actions.node_modules`, por defecto `<estado>\node_modules`; **no se reutiliza el del QA**).
4. Claude Code CLI **nativo** (`claude`), con sesion iniciada. Se localiza en `MEJORAS_WEB_CLAUDE_EXE`, `~\.local\bin\claude.exe`, el paquete npm o el PATH.
5. Crea un **Project de ChatGPT nuevo** (instrucciones en `project_instructions.md`, conector de GitHub al repo) y pon su id `g-p-...` en `config.json` → `gpt.project_id` (o `MEJORAS_WEB_PROJECT_ID`). El id del Project del QA se rechaza.
6. Primera vez: `INICIAR-MEJORAS-WEB.bat` abre un Edge con perfil nuevo en `%LOCALAPPDATA%\web-escritor-mejoras-web\edge-perfil`; inicia sesion en ChatGPT ahi (una vez; no se copia ninguna sesion del QA).

Estado persistente (fuera de Git): `%LOCALAPPDATA%\web-escritor-mejoras-web\estado\` (`mejoras.db`, `servicio.log`, `actions\ejecutar.log`, `respuestas\`, `wt\`). Se puede mover con `MEJORAS_WEB_STATE`.

## Pruebas offline (no usan Edge, modelos, GitHub ni Actions)

```powershell
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
* **Rama de desarrollo**: ningun disparador automatico. Los workflows del laboratorio son solo `workflow_dispatch`; los commits que tocan `experimentos/mejoras-web/**` y los workflows nuevos no coinciden con los filtros `paths` de los workflows existentes con `push` sin rama (cuaderno).

## Dependencia de rama del workflow (no se activa por commitear)

GitHub solo despacha un workflow que existe en la rama que se pasa a `--ref`. `mejoras-web-grupo.yml` vive hoy en `research/mejoras-web-motor-qa-20261027` y `config.json` → `workflow_ref`
apunta ahi. Al integrar el laboratorio en `lab/mejoras-web-20261024`, cambia `workflow_ref` a esa rama (y si algun dia pasa a `main`, a `main`). Si el dispatch no crea ningun run en `actions.espera_run_min` (10 min),
el item pasa a `revision_humana` indicando exactamente eso. El workflow checkoutea el `sha` de la rama `mejoras-web/*` (publicada por EJECUTAR) y toma el driver (`ci_grupo.py`) del commit del workflow.

## Enlace verificable de la web con las mejoras (documentado, NO activado)

* **Local, siempre disponible**: `python motor\mw.py vista-previa` sirve la rama base del laboratorio (la web «como si fuera main pero con las mejoras aceptadas») y `vista-previa MW-0001` una candidata.
* **Enlace publico**: `.github/workflows/mejoras-web-preview.yml` (solo `workflow_dispatch`, con confirmacion escrita `PUBLICAR-PREVIEW`). Monta el sitio de `lab/mejoras-web-20261024`, lo marca `noindex` y lo sube como artefacto; si existen el secreto `CLOUDFLARE_API_TOKEN`, el secreto `CLOUDFLARE_ACCOUNT_ID` y la variable `MEJORAS_WEB_PAGES_PROJECT`, lo publica en un proyecto de **Cloudflare Pages separado** como rama `lab-mejoras-web` →
  `https://lab-mejoras-web.<proyecto>.pages.dev`. No usa GitHub Pages ni toca el despliegue de produccion. Para activarlo: crear el proyecto de Pages, anadir esos tres valores y lanzar el workflow a mano. Pasar a `main` solo cuando David lo ordene.

## Que se conservo y que se retiro de la PR #819

Ver `PROCEDENCIA.md` (tabla completa) y `legado-819/INDICE.md`. Resumen: se conservan `verificar_upstream.py` y `descubrimiento.py` (pistas opcionales); se reescriben `preflight.py` y `preview.py`;
se sustituyen por el motor del QA `ciclo.py`, `pr_laboratorio.py`, `claude_cli.py`, `gpt_browser.py` y `rotacion.py`; no hay catalogo fijo: la rotacion area × lente (100 pares) cambia de orden en cada vuelta y no se agota.

## Integrar esta rama en la #819 sin PR duplicadas

La #819 (`research/mejoras-web-orquestador-20261024`, cerrada sin fusionar) **no se reabre ni se crea otra PR mientras se desarrolla**. Cuando David lo decida:
1. Revisar localmente `research/mejoras-web-motor-qa-20261027` (tests offline + una ronda real).
2. Avanzar la rama de la #819 a este trabajo: `git checkout research/mejoras-web-orquestador-20261024 && git merge --ff-only research/mejoras-web-motor-qa-20261027 && git push` (es fast-forward: esta rama parte del HEAD de la #819). Con la PR cerrada el push no dispara CI.
3. Solo entonces reabrir **esa misma** PR #819 (o abrir una unica nueva hacia `lab/mejoras-web-20261024`, cerrando la antigua). Las PR hijas de cada mejora (`mejoras-web/<id>` → `lab/...`) las crea `mw.py pr`, que detecta una PR existente por rama y no la duplica; el tope por defecto es 2 abiertas.
4. Cambiar `workflow_ref` a la rama donde viva `mejoras-web-grupo.yml`.
