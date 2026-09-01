# Reflow · discrepancia local/CI de los 3 overflows residuales (2026-09-01)

## 1. El hallazgo

Ejecutando `qa/sitewide-reflow-browser.mjs` + `qa/text-resilience-report-gate.mjs` en local (Windows, Playwright con Chromium descargado por `npx playwright install`) sobre el `main` exacto de la PR #317 (`67bc6326`), el gate reporta:

```
text-resilience-gate: FINDINGS (456 checks; residual failures=3; ...)
/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/@320x900/resize-text-200: overflow=3, clips=0
/herramientas/auditor-pagina-libro/@320x900/resize-text-200: overflow=10, clips=0
/metodologia-editorial/@320x900/resize-text-200: overflow=17, clips=0
```

Pero el job `reflow-sitewide` de CI para ese mismo SHA (`run 33531738505`, `conclusion: success`) imprime:

```
text-resilience-gate: OK (456 checks; residual failures=0; ...)
```

Mismo commit, mismo script, mismo modo (`enforce`), resultado distinto: 3 vs 0.

## 2. Triangulación (no se da nada por hecho)

En vez de confiar en cualquiera de los dos resultados a ciegas, se comprobó un tercer entorno independiente: el motor Chromium del propio Browser pane de esta sesión (no el Chromium que descarga Playwright), navegando en vivo a las 3 rutas señaladas a 320px de ancho e inyectando exactamente la regla CSS de `resize-text-200` (`html{font-size:200%!important}`), midiendo `document.documentElement.scrollWidth - window.innerWidth`:

| Ruta | Playwright local (Windows) | Browser pane Chromium | CI (Ubuntu) |
|---|---:|---:|---:|
| `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` | 3px | **0px** | **0px** |
| `/herramientas/auditor-pagina-libro/` | 10px | **0px** | **0px** |
| `/metodologia-editorial/` | 17px | **0px** | **0px** |

Dos entornos independientes (CI Ubuntu, Browser pane Chromium) coinciden en 0px de overflow real. Solo el Chromium que `npx playwright install` descargó en esta máquina Windows reporta overflow, y con tres magnitudes distintas y pequeñas (3/10/17px) que son consistentes con una diferencia de métrica de fuente (sustitución de fuente, hinting o subpíxel), no con un fallo estructural de layout: un fallo real de CSS/grid produciría overflow en los tres entornos por igual, no en uno de tres.

## 3. Conclusión

Diferencia de entorno de renderizado de fuentes entre el Chromium de Playwright-Windows local y los otros dos entornos (CI Ubuntu, Browser pane). No hay evidencia de un defecto real de layout/CSS: ni CI ni un segundo motor Chromium independiente reproducen overflow alguno en estas 3 rutas bajo `resize-text-200` a 320px.

No se ignora ni se parchea a ciegas: se documenta con las tres mediciones que lo sustentan. Si en el futuro CI empieza a reportar estos mismos fallos (no solo el Playwright local de esta máquina), reabrir esto como regresión real, no como ruido de entorno.

## 4. Qué NO se ha hecho

No se ha tocado el CSS de esas 3 páginas para "arreglar" un overflow que no se reproduce fuera de un entorno local con una instalación de Chromium que difiere de CI. Modificar CSS a ciegas contra un resultado no reproducible en el entorno que realmente gatea los merges sería el error contrario: parchear ruido, no una regresión real.
