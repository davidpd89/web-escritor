# Informe de continuidad: CLS Yellowtail en Manecillas (2026-10-23)

## Cambios
- PR #741 mergeado (squash) en main: `30b0d130`. Usa el fallback con size-adjust de Samuel para Yellowtail en `assets/v1-manecillas-design-v8.css`; test `tests/test-manecillas-yellowtail-fallback.py`.
- PR #740 mergeado antes (main `a0b7b3ca`). PR #739 no tocado.

## Verificado
- Checks de #741 en verde y estado CLEAN al hacer merge. `smoke` y `sitewide-console-errors` salieron canceladas a los 15-20 min (instalacion de deps de Playwright colgada); se relanzaron solo esos jobs y pasaron. `Sitewide Reflow QA` tarda ~1 h de forma normal.
- Deploy Pages por push sobre `30b0d130`: success.
- CLS en produccion (Chromium, con y sin fuentes retrasadas 350 ms):
  - /las-manecillas-del-recuerdo/: 360px 0,0002; 768px 0,0007; 1280px 0,0003 (antes 0,134 a 768px y 0,151 a 1280px).
  - /autor.html: 0 en 360, 768 y 1280 px; no se reproduce CLS intermitente.

## Estado final
- Cerrados los servidores temporales 8781/8782. No se tocaron GPT QA, RRSS ni otros procesos.
- Pendiente: Sitewide Reflow QA y Pa11y del push a main seguian en curso al escribir esto (no verificados).
- Worktree `C:/GIT/web-escritor-fix-cls` (rama fix/manecillas-cls) sigue existiendo; se puede borrar.
