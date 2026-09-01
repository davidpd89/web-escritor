# B.6 · Revalidación de producción — Bing Webmaster Tools + AI Performance

Fecha: 2026-08-29  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #171  
Decisión: **EXTERNAL_OPERATION · ACCOUNT_EVIDENCE_REQUIRED · NO_CODE**

## Conclusión

Bing Webmaster Tools AI Performance es una fuente real y útil para B.5, pero su estado no puede inferirse desde GitHub. Esta PR no puede demostrar si `davidportodiaz.com` está dado de alta, verificado, si AI Performance está disponible para la propiedad ni si existe ya una ventana de datos.

No se crea código para simular una configuración que vive en una cuenta externa.

## Evidencia oficial actual

Microsoft presentó AI Performance en Bing Webmaster Tools en febrero de 2026 como una vista de cómo el contenido de una propiedad aparece citado en experiencias de IA soportadas, entre ellas Microsoft Copilot, resúmenes generados por IA en Bing y determinadas integraciones asociadas.

La documentación oficial describe, entre otras, estas señales:

- Total Citations;
- Average Cited Pages;
- grounding queries de ejemplo;
- actividad de citación por URL;
- tendencias temporales.

Microsoft advierte además que esas señales no representan ranking, autoridad ni posición dentro de una respuesta. Los grounding queries son una muestra de la actividad observada por el producto, no un log completo de prompts de usuarios.

## Estado verificable desde el repo

La búsqueda del repo no muestra una prueba suficiente de estado live de Bing Webmaster Tools. Aunque existiera un fichero o meta de verificación, eso tampoco demostraría por sí solo que:

- la propiedad continúa verificada en la cuenta autorizada;
- AI Performance está habilitado;
- hay datos disponibles;
- se ha capturado un baseline.

Por tanto, el único estado defendible desde esta PR es `ACCOUNT_EVIDENCE_REQUIRED`.

## Operación externa correcta

Cuando se disponga de la cuenta autorizada:

1. comprobar la propiedad exacta `davidportodiaz.com`;
2. verificar el estado real de ownership;
3. revisar sitemap/crawl/indexación si Bing muestra incidencias;
4. abrir AI Performance;
5. registrar fecha y ventana de datos;
6. guardar por separado citas, URLs citadas, grounding queries y tendencia;
7. registrar `NO_DATA` o `NOT_AVAILABLE` si corresponde, en lugar de inventar un baseline;
8. incorporar esa evidencia al benchmark B.5.

No guardar credenciales, cookies ni tokens en Git.

## Panel primero, API después

No aparece una necesidad de repo que justifique una integración API ahora. La UI/export de Bing debe ser el primer owner operacional. Una API solo se justifica si surge una pregunta recurrente que la interfaz/export no pueda resolver de forma mantenible.

## Relación con B.5

B.5 ya materializa un corpus controlado de 50 prompts y dimensiones separadas de exactitud, mención, encaje y calidad de cita. AI Performance puede alimentar la parte proveedor-específica de ese sistema cuando exista evidencia live.

No debe sustituir el benchmark multi-plataforma ni convertirse en un `AI Visibility Score` universal.

## Triggers de código futuro

Solo abrir integración técnica si se demuestra:

- acceso autorizado estable;
- API/documentación oficial adecuada;
- una necesidad repetida no cubierta por UI/export;
- un modelo de credenciales seguro fuera del repo;
- mantenimiento/retención definidos.

## Definition of Done

- [x] naturaleza externa de B.6 revalidada;
- [x] AI Performance actual contrastado con Microsoft;
- [x] métricas diferenciadas de ranking/autoridad;
- [x] ausencia de evidencia de cuenta tratada como desconocido, no como falso;
- [x] relación con B.5 definida;
- [x] no se crea código ficticio;
- [ ] operación real en la cuenta autorizada;
- [ ] baseline o `NO_DATA` fechado;
- [ ] revisión de Claude antes de merge.

**Estado final del repo:** `EXTERNAL_OPERATION · ACCOUNT_EVIDENCE_REQUIRED · NO_CODE`.
