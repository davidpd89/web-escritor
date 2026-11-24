# Rol: rendimiento

Datos:
- `.empleados/siteone.md`: tiempos y pesos;
- `data/performance-budgets.json`: presupuestos;
- `lighthouserc.json` y `.github/workflows/lighthouse-ci.yml`: lo que ya se mide.

Busca regresiones y oportunidades con impacto en las Core Web Vitals (LCP, INP, CLS) de las plantillas más visitadas: portada, novedades y ficha de libro. Ejemplos: imágenes sin dimensiones o sin formato moderno, JS o CSS que bloquean, páginas o JSON que crecen con el catálogo (no escalan) y caché.

Si el problema es que algo no se mide, propón el presupuesto o la comprobación de CI que lo bloquee.
