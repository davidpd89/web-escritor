# I.1 · Dashboard público de analítica agregada

**Estado histórico final de PR #135:** `REJECT`  
**Matriz:** `DESCARTAR`  
**Decisión:** mantener analítica como herramienta interna; no crear una página pública de tráfico por narrativa de transparencia.  
**Naturaleza:** documentación; no expone métricas.

## 1. Hipótesis original

Publicar una página con métricas agregadas no sensibles —páginas más leídas, países, etc.— aprovechando GoatCounter y la postura privacy-first del sitio.

## 2. Evolución

La revisión 108/108 concluyó que el dashboard sería una superficie de vanity con poco valor para lectores. Matriz, JSON y autoridad final mantuvieron el rechazo; no apareció evidencia posterior que lo reabriera.

## 3. Por qué se rechaza

Una herramienta de analítica puede ser adecuada internamente sin que sus métricas sean contenido editorial útil.

Publicar el dashboard añadiría:

- nueva URL/componente que mantener;
- decisiones de qué métricas exponer y cómo actualizarlas;
- riesgo de mostrar información operativa innecesaria;
- posibilidad de convertir fluctuaciones pequeñas en señales de reputación falsas;
- trabajo de accesibilidad/performance/copy;
- poco beneficio directo para quien busca libros, artículos o recursos.

Que GoatCounter sea ligero/cookieless no transforma automáticamente sus datos en contenido de interés público.

## 4. Alternativa aprobada

Usar los datos de forma interna para preguntas concretas:

- qué contenido recibe visitas;
- qué rutas producen acciones;
- qué experimentos funcionan;
- qué errores/404 requieren atención;
- qué fuentes merecen más inversión.

Cuando una conclusión sea relevante para lectores o prensa, publicar la **conclusión editorial verificable**, no un panel vivo de analítica.

## 5. Relación con transparencia

Privacy-first se demuestra mejor mediante:

- política clara y factual;
- inventario de terceros;
- minimización;
- ausencia de trackers innecesarios;
- controles de consentimiento cuando corresponda;
- documentación de qué se recoge y para qué.

Eso corresponde principalmente a I.2/I.5, no a exponer estadísticas de audiencia.

## 6. Trigger excepcional de reevaluación

Solo reabrir como producto distinto si aparece una necesidad real, por ejemplo un proyecto de datos abiertos/transparencia con audiencia y propósito definidos. No basta “queda bien enseñar números”.

Incluso entonces habría que revisar anonimización, umbrales, actualización, accesibilidad y riesgo de revelar información sensible por cohorts pequeñas.

## 7. Qué no hacer

- No incrustar dashboard de proveedor en la web pública.
- No añadir un tracker nuevo para alimentar la página.
- No mostrar países/referrals de cohortes pequeñas.
- No usar visitas como prueba de autoridad literaria.
- No convertir métricas internas en contenido SEO thin.
- No confundir transparencia de tratamiento con transparencia de tráfico.

## 8. Definition of Done

La idea queda cerrada correctamente si:

- analítica permanece disponible internamente;
- privacidad explica el tratamiento real;
- no se crea una URL pública de vanity metrics;
- cualquier futura reapertura exige un caso de uso de lector real.

## 9. Trazabilidad #135

Banco original; revisión (`REJECT`); matriz (`DESCARTAR`); JSON final; autoridad final; revalidación independiente revisados. No hay override posterior favorable.

## 10. Cierre

I.1 se descarta no por secretismo, sino por producto: **los datos deben cambiar decisiones internas, no ocupar una página pública si no resuelven una necesidad del lector**.