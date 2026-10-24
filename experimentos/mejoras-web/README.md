# Laboratorio de mejoras web (24-10-2026)

## Qué se crea realmente

Un **entorno de revisión aislado**, no una nueva versión desplegada de la web. Esta PR nace en `research/mejoras-web-orquestador-20261024` y apunta **solo** a `lab/mejoras-web-20261024`, NO a `main`. Ambas ramas parten del commit `5b64fc173e9b1f24a6e7c9ba9c6e7801f0820fac`.

El launcher de Windows abre un Edge **con perfil propio** en el puerto CDP `9331` y sirve la copia local del sitio en `127.0.0.1:8765`. No instala librerías ni llama a servicios de IA. La conexión del orquestador GPT/Claude **todavía no está implementada**: los scripts completos del circuito de conversación/creación automática de PR parecen residir en el ordenador del autor y no están en este repositorio. Aquí sí se ha inspeccionado `scripts/qa-gpt/{ci_grupo.py,qa_clases.py}`, que corresponde al ejecutor CI, no al orquestador local.

## Arquitectura objetivo (sin fingir que ya funciona)

```text
INICIAR MEJORAS (carpeta/worktree y Edge 9331)
  -> GPT investigador (una hipótesis, baseline real + web + upstream)
  -> Claude revisor (acepta/corrige/rechaza; autónomo respecto a GPT)
  -> propuesta medida con código upstream exacto, licencia y adaptación
  -> PR hija pequeña: feature/mejoras-web/*  -> base: lab/mejoras-web-20261024
  -> ejecutar CI, Playwright, presupuesto y regresión visual solo en laboratorio
  -> demo local: comparar antes/después con URLs y capturas
  -> aprobación humana: aceptar/rechazar/ajustar la propuesta
  -> merge manual a rama lab; más adelante PR independiente lab -> main,
     SOLO por petición expresa, tras rebase/validación contra main actual
```

No usar `main` como destino de PR hijas ni lanzar `deploy-pages.yml` desde este entorno. El review humano se produce **antes** de aceptar algo en el sitio público. Los cambios de la rama lab no heredan automáticamente los CI obligatorios configurados para PR hacia `main`; deberán lanzarse verificaciones manuales específicas, y al promocionar a `main` pasar todo el gate real.

## Arranque para Windows (se hace sobre esta rama, NO en main)

```powershell
git fetch origin research/mejoras-web-orquestador-20261024
git worktree add -b lab/mejoras-local ../web-escritor-mejoras origin/research/mejoras-web-orquestador-20261024
cd ../web-escritor-mejoras
python experimentos/mejoras-web/verificar.py
.\experimentos\mejoras-web\INICIAR-MEJORAS.cmd
```

Edge se abre en `http://127.0.0.1:8765/`; puerto de depuración `9331` enlazado solo a loopback. `Ctrl+C` en la consola termina el servidor local. Cerrar Edge no modifica Git. Si el puerto 8765 o 9331 está ocupado, **no** toma control de procesos ajenos: pide liberar el puerto. El script se niega a arrancar si el worktree está en `main`.

Requisitos: Windows, Python 3 y Microsoft Edge instalados; PowerShell 5.1+. Si el sitio necesita un Worker remoto, API o claves, la previsualización estática por sí sola **no** demuestra ese flujo: levantar un emulador local o fixture en una PR específica.

## Qué se aprovecha del repositorio real

- Estilo y guardrails: `docs/design-ux-tooling/README.md`, `15-ANTI-SLOP-DESIGN-REVIEW.md`, `docs/design-system/`.
- Investigación previa: `docs/web-improvements/`, el registro histórico de 108 ideas y `docs/web-improvement-ideas/`. No generar un segundo catálogo ignorando esas decisiones.
- QA existente: `qa/core-user-journeys-browser.mjs`, `qa/visual-regression-browser.mjs`, `qa/sitewide-reflow-browser.mjs`, `scripts/check-performance-budgets.py` y `scripts/qa-gpt/`.
- Stack real: HTML/CSS/JS estático; Playwright 1.62.1, Pagefind, Lighthouse y pa11y fijados en `package.json`; no imponer frameworks nuevos.

## Reglas mínimas por investigación

1. Baseline: ruta, commit, comportamiento y test en la versión actual. Si ya funciona, no repetir.
2. Problema observado, hipótesis falsable, beneficio para lector o para negocio y coste de cambio.
3. Máximo dos referencias upstream por entrega; ruta y SHA o versión verificables, licencia y código original *sin alterar* antes de la adaptación, con aviso de sus límites.
4. Si la documentación del proveedor cambia, verificar en fuente primaria **en ese momento**.
5. Claude revisa independencia, duplicación, identidad visual, efecto en el sitio, cobertura y si compensa.
6. PR hija aislada por mejora. Máximo **dos experimentos activos** hasta medir tiempos y valor; no inundar Actions.
7. Reporte para la persona: problema, antes/después, URL local, pruebas que pasaron, métricas, riesgos, recomendación A/B y posibilidad de deshacer.
8. No monetización especulativa: separar clic de venta confirmada, y nuevas APIs de fuentes ya incorporadas.

## Primeros entregables

- `catalogo.json`: 12 hipótesis concretas, todas **candidatas**, ninguna presentada como fallo demostrado.
- `contratos/GPT-INVESTIGAR.md` y `contratos/CLAUDE-REVISAR.md`: prompts versionables por etapa.
- `investigaciones/01-web-vitals.md`: primer candidato externo inspeccionado, con código literal upstream y licencia; aún NO integrado.
- `verificar.py`: validación offline del registro para evitar fichas vacías o duplicados.
- Launcher: solo navegador/servidor; no autopregunta, no autopull, no despliegue.

## Pendiente para que sea la misma cadena automática

Pedir al entorno **local** sus scripts reales de `EJECUTAR-ACTIONS-QA-GPT` y de GPT ↔ Claude ↔ PR, incluyendo estado persistido, bloqueo de Edge, detección de puerto y política de parada. Crear un adaptador nuevo que use esos componentes sin compartir carpetas de cola, sesiones, llaves de estado, puertos ni contadores con QA. Probar Q, Ctrl+C, reinicio e idempotencia. Solo entonces conectar `INICIAR-MEJORAS` al orquestador; la arquitectura de arriba es una especificación, no una ejecución ya verificada.

**Sin merge a lab ni a main desde esta PR; queda en borrador para investigación e implementación incremental.**
