# Laboratorio de mejoras web — PR #819

**Estado:** implementación versionada en borrador, pendiente de validar extremo a extremo en Windows y CI. No se ha fusionado `lab` ni `main` ni se ha desplegado una web de pruebas pública.

## Qué hace

1. Selecciona un **área de exploración**, no una mejora predeterminada: auditoría interna, repositorio GitHub, novedades web, APIs, o producto/editorial.
2. Obtiene fuentes **actuales** del repositorio local, GitHub REST o RSS primario de Search Central, filtradas por fecha y deduplicadas por URL más actualización. Las 68 propuestas de `catalogo.json` son ejemplos iniciales en 25 familias, no un techo: una vez agotadas, `motor/ciclo.py` sigue haciendo sondeos sucesivos. Si no aparece nada nuevo, registra ese resultado sin fabricar una tarea.
3. GPT investiga **una sola fuente y una sola necesidad hasta el final**: documentación primaria, pruebas existentes, compatibilidad, coste, alternativas A/B, código original de un repositorio y su adaptación posible.
4. `verificar_upstream.py` exige, para repositorios, un blob SHA Git de 40 hex que contenga literalmente el código aportado y licencia SPDX comprobada en GitHub. No ejecuta código de terceros.
5. Claude recibe el expediente y la verificación, devuelve decisión JSON (`aprobar`, `rechazar`, `investigar_mas`). No puede fusionar.
6. Si aprueba, GPT propone un parche acotado y tests. `pr_laboratorio.py` comprueba rutas, coincidencias exactas, secretos, aplica en worktree hijo de `origin/lab/mejoras-web-20261024`, ejecuta pruebas y abre PR **en borrador hacia lab**. No se auto-fusiona ni publica.
7. La persona evalúa diferencias, capturas y usabilidad. Solo un merge manual a lab acumula una mejora aceptada; promoción a main requiere proceso posterior separado.

La ejecución continua permite **máximo 2 PR hijas abiertas** en lab antes de detener la búsqueda para revisión humana.

## Código reutilizado de la rama de QA original

El código original sí está en GitHub, rama `automation/qa-gpt` (separada de `main`):

- `scripts/qa-gpt/gpt_browser.py`: usado como base de `motor/gpt_browser.py` (Edge **9331**, sesión y Project distintos). Blob original `4fda7332ee6597c8efcd1fcc37cdc63008d08d3d`.
- `scripts/qa-gpt/qa_claude.py`: base de `motor/claude_cli.py`; CLI Claude headless, JSON Schema, caché, límite de coste e historial SQLite. Blob original `7fe42e7bae24eeb78da271020ce1cf1f541f0a7b`.
- `scripts/qa-gpt/qa_pr.py` y `qa_cobertura.py`: patrones de validación, worktree, pruebas y deduplicación adaptados en `pr_laboratorio.py` y `rotacion.py`.

Es una adaptación aislada, no una segunda copia en marcha del servicio QA ni sus estados. No toca Edge 9230, 9224/9225 ni `C:\GIT\qa-gpt-state`.

## Arranque local (Windows)

Crear **una carpeta/worktree independiente** desde la rama de esta PR:

```powershell
git fetch origin research/mejoras-web-orquestador-20261024
git worktree add -b lab/mejoras-local ../web-escritor-mejoras origin/research/mejoras-web-orquestador-20261024
cd ../web-escritor-mejoras
python experimentos/mejoras-web/verificar.py
python -m unittest discover -s experimentos/mejoras-web -p 'test_*.py' -v
.\experimentos\mejoras-web\INICIAR-MEJORAS.cmd -Simular
```

`-Simular` no abre Edge ni llama a modelos ni a GitHub para escribir PR. `-SoloVista` solo muestra la web de esa carpeta en `127.0.0.1:8765` y Edge con CDP `9331`; **no reserva tarea**.

Para la ejecución **real** hacen falta: Python con `playwright`, Microsoft Edge autenticado en ChatGPT, un Project específico para mejoras en ChatGPT, Claude Code CLI y GitHub CLI con acceso al repositorio. Configurar, en la consola del laboratorio:

```powershell
$env:LAB_MEJORAS_PROJECT_ID = 'ID_REAL_DEL_PROJECT'
.\experimentos\mejoras-web\INICIAR-MEJORAS.cmd
```

El ID se obtiene de la URL del Project real; no reutilizar el Project de QA porque sus instrucciones son diferentes. El lanzamiento real activa el ciclo continuo, GPT/Claude y PR borrador a lab tras tests locales. Para escoger manualmente: `INICIAR-MEJORAS.cmd -IdeaId SEO-01`; para rotación de GitHub: `-Canal github`.

`Q` en consola detiene el director conservando su estado y el chat; `Ctrl+C` interrumpe el proceso. Cerrar la consola detiene nuevas consultas, aunque una operación externa ya enviada puede continuar. No se cancelan Jobs de Actions automáticamente.

## Estado, pruebas y previsualización

- `python experimentos/mejoras-web/motor/ciclo.py --estado` muestra el último expediente; incluye fuente, decisión, validación y ruta de su worktree, sin acceder a servicios.
- El estado persistente vive bajo `LOCALAPPDATA/web-escritor-mejoras/`, en una carpeta por worktree, nunca en Git ni la cola QA original.
- Para ver una propuesta antes de fusionarla, servir su `validacion.worktree` con `python -m http.server 8766 --bind 127.0.0.1 -d "RUTA_DEL_WORKTREE"`. No es el mismo fichero que la portada en 8765.
- `.github/workflows/lab-mejoras-offline.yml` ejecuta tests offline en esta rama, sin secretos. **No se deben declarar verdes sin resultado del run**. Los checks de navegador/performance habituales siguen siendo necesarios en cada PR hija.

## Puertas de aceptación aún pendientes

1. Suite offline realmente superada en Actions/Windows; revisar errores y resolverlos, no solo que exista el YAML.
2. Inicio de Edge 9331 y login de Project real; respuesta GPT completa desde backend y reanudación con chat_id tras Q.
3. Revisión Claude real con esquema, coste observado y prueba de rechazo/aceptación; comprobar herramientas de lectura y licencias.
4. PR hija piloto con modificación verificable, tests locales/Actions y sin rutas fuera de alcance ni cambios en main.
5. Previsualización y valoración humana móvil/escritorio, después integración voluntaria en lab.
6. Verificar recuperación tras errores de red, GitHub y una PR existente; no liberar límites sin datos.

**Hasta superar estos pasos, no declarar el sistema al 100 %.** Ver `CONTRATO-ORQUESTADOR.md` para comandos de estado y fuentes, y `FUENTES-2026-10-24.md` para evidencia vigente. Esta PR no debe fusionarse automáticamente.

## Previsualización de una propuesta concreta

Tras validar localmente una mejora, el estado contiene `validacion.worktree`. Ejecuta `PREVISUALIZAR-MEJORAS.cmd` en el laboratorio para servir **esa versión candidata** en `http://127.0.0.1:8766/` (la web base puede permanecer en 8765). No abre ni fusiona PR ni sirve públicamente. Solo acepta worktrees dentro del estado propio; rechaza cualquier ruta exterior. Sin propuesta validada, indica el motivo. Para abrirla sin navegador, pasar `--sin-abrir`.

El director usa un bloqueo con PID e identidad: si la ventana murió y el proceso ya no existe, recupera el bloqueo tras comprobarlo; si el proceso aún está vivo, impide un duplicado. La cola QA original sigue sin verse afectada.
