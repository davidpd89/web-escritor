# I.1 · Revalidación de producción — dashboard público de analítica

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `REJECT · INTERNAL_ANALYTICS_IS_THE_OWNER · PUBLIC_TRAFFIC_DASHBOARD_HAS_NO_READER_JOB · NO_CODE`

## Estado real

La web ya dispone de analítica ligera y de una política pública que explica los proveedores relevantes. E.8/I.2 además han definido la dirección correcta para transparencia técnica: inventario versionado, minimización, CSP, purpose y revisión de terceros.

Nada de eso crea una necesidad de publicar cifras de tráfico.

## Por qué se mantiene el rechazo

Un dashboard público de visitas, países, referrals o páginas populares:

- no ayuda a leer un libro, artículo o recurso;
- crea una nueva superficie que mantener y explicar;
- puede convertir cohortes pequeñas en señales engañosas;
- añade riesgo de exponer información operacional innecesaria;
- puede incentivar optimización por vanity metrics;
- duplica transparencia sin mejorar la comprensión del tratamiento de datos.

La transparencia privacy-first se demuestra describiendo qué se recoge, por qué, mediante quién y con qué límites; no publicando el tamaño de la audiencia.

## Uso correcto de la analítica

Las métricas deben permanecer como herramienta interna para preguntas concretas:

- qué rutas funcionan;
- dónde hay errores;
- qué contenidos generan acciones útiles;
- qué experimentos deben mantenerse o retirarse;
- dónde invertir esfuerzo editorial/técnico.

Si de esos datos emerge una conclusión de interés público, puede publicarse la conclusión verificable en su contexto; no un panel vivo por defecto.

## No implementar

- No URL `/estadisticas/` o equivalente.
- No embed de GoatCounter/Metricool.
- No nuevo tracker para alimentar un dashboard.
- No países/referrals de cohortes pequeñas.
- No usar visitas como prueba de autoridad literaria.
- No contenido SEO basado en cifras de audiencia.

## Trigger excepcional

Solo reabrir como producto distinto ante un caso de uso explícito de datos abiertos/transparencia con audiencia propia, metodología, anonimización, umbrales y mantenimiento definidos. «Queda bien enseñar números» no es trigger.

## Cierre

I.1 permanece `REJECT`. El owner es la analítica interna; la transparencia pública pertenece a I.2/I.5 y a una política factual.