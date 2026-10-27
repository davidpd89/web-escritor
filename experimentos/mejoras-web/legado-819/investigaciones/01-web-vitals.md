# PERF-01 — web-vitals, candidato real para diagnóstico INP (24-10-2026)

**Estado: preselección documentada; no auditoría exhaustiva, no implementación ni mejora medida.**

## Brecha a comprobar

El repositorio ya ejecuta Lighthouse, presupuestos de rendimiento y QA de navegador. No se ha demostrado que falte RUM ni que su instalación mejore INP. Primera tarea: inspeccionar `scripts/check-performance-budgets.py`, `lighthouserc.json`, instrumentación del sitio y la analítica actual para ver si existe observación por interacción y si sus datos serían útiles.

**Métrica**: INP, LCP y CLS en sesiones comparables y pruebas dirigidas sobre filtros de `recomendaciones/`; distinguir métricas de laboratorio de field data. Objetivo no es "poner una librería", sino aislar una ralentización verificable.

## Upstream contrastado (fuente primaria)

- Código/documentación: https://github.com/GoogleChrome/web-vitals/blob/main/README.md
- Archivo comprobado en GitHub: `README.md` blob SHA `31be2f9a254ea5177022e5e20146b815131178d9`.
- Licencia `Apache-2.0`: https://github.com/GoogleChrome/web-vitals/blob/main/LICENSE (blob SHA `618d629b34698247942650cfed9dcc11b8ba036b`).
- API de atribución: https://github.com/GoogleChrome/web-vitals#attribution
- Definición oficial y objetivos de métricas: https://developers.google.com/search/docs/appearance/core-web-vitals

**Código literal upstream** (README, sección *From npm*, no adaptación):
```js
import {onLCP, onINP, onCLS} from 'web-vitals';
```

**Código literal upstream** (README, ejemplo CDN, se conserva su uso exacto):
```js
  onCLS(console.log);
  onINP(console.log);
  onLCP(console.log);
```

Es una muestra de interfaz, NO la copia del paquete ni una integración productiva. Antes de adaptar: inspeccionar `src/`, tests reales, versión fijada, camino de distribución compatible con la web estática y consentimiento/almacenamiento de datos. Si se distribuye código upstream adaptado, conservar avisos y licencia correspondientes.

## Alternativa A / B

- **A (primero)**: usar PerformanceObserver y medición local/Playwright, sin añadir dependencia ni endpoint, capturando acciones específicas de filtros. Menor coste, no representa población real.
- **B (condicional)**: módulo `web-vitals/attribution` autoalojado y muestreo de campo con datos mínimos, solo si la auditoría verifica ausencia de cobertura y se acuerdan datos, privacidad, coste e integración.

## Puerta de ejecución

1. Confirmar baseline de QA y de instrumentación existente. 2. Seleccionar recorrido y producir distribución/valores comparables antes/después. 3. Claude revisa si hay una optimización real que justifique la PR hija. 4. Integrar solo lo necesario en la rama lab, medir peso extra y verificar que no empeora otras métricas. 5. **No asumir un aumento de SEO/ventas** por instalar la librería.
