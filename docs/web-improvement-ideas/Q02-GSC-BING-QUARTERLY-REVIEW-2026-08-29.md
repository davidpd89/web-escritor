# Q.2 · Revisión conjunta Search Console + Bing Webmaster Tools — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `EXTERNAL_OPERATION`.

## 1. Hipótesis original

Q.2 proponía establecer una revisión trimestral conjunta de Google Search Console y Bing Webmaster Tools en lugar de depender únicamente de Google.

La idea se apoya en B.6: Bing Webmaster Tools incorpora señal tradicional de búsqueda y, desde 2026, AI Performance para citas/grounding en experiencias de IA de Microsoft.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `IMPLEMENT_NOW`.

La revisión consideró que GSC ya era operativo y Bing era la siguiente fuente externa de alto valor. La recomendación fue un runbook conjunto, no un dashboard ornamental.

### Matriz final 28/08

Decisión: `IMPLEMENTAR`.

Se mantuvo la revisión periódica de ambos paneles y se conectó con B.6.

### Autoridad final humana + machine-readable

Estado: `EXTERNAL_OPERATION`.

La corrección de estado es importante: configurar/verificar una propiedad, acceder a los paneles y exportar datos ocurre fuera de Git. Un documento o script del repo no demuestra que Bing esté configurado live.

Regla final:

> GSC ya está operativo; verificar/configurar Bing Webmaster/AI Performance por separado y establecer cadencia solo cuando ambos existan.

## 3. Revalidación independiente y fuentes actuales

La revalidación independiente mantiene la decisión.

La documentación actual de Bing confirma:

- AI Performance muestra páginas citadas, citas, grounding queries y tendencias;
- los datos son agregados y no representan ranking, autoridad o importancia;
- puede haber poca o ninguna señal cuando la actividad es escasa;
- el panel permite export CSV/Excel;
- Bing Webmaster Tools necesita propiedad verificada y tiempo para recopilar datos;
- las APIs SOAP/POX legacy se retiran el 31/08/2026: si algún día se automatiza, usar REST vigente.

Esto refuerza el enfoque manual-first de #135.

## 4. Estado actual del repositorio

Git contiene documentación y decisiones relacionadas con GSC/Bing, pero no puede acreditar por sí solo:

- que la propiedad Bing esté verificada;
- qué cuenta tiene acceso;
- que AI Performance muestre datos;
- que una revisión trimestral se haya ejecutado;
- que se hayan exportado baselines recientes.

Por tanto no debe cambiarse `EXTERNAL_OPERATION` a `ALREADY_COVERED` por existir documentación.

## 5. Runbook trimestral mínimo

Cuando ambas propiedades estén disponibles:

### Google Search Console

- rendimiento orgánico: clicks, impressions, CTR, position;
- queries y páginas;
- branded vs no branded cuando sea útil;
- países/dispositivos solo cuando cambien una decisión;
- indexación/sitemaps;
- Core Web Vitals si existe muestra suficiente.

### Bing Webmaster Tools

- Search Performance;
- Site Explorer / URL Inspection cuando haya anomalías;
- Site Scan de forma razonable;
- backlinks/keywords si aportan información no visible en GSC;
- AI Performance: páginas citadas, grounding queries, tendencias y `NO_DATA` si corresponde.

## 6. Comparación correcta

No mezclar métricas como si fueran equivalentes.

Ejemplos:

- clicks de Google ≠ citas de AI Performance;
- citation count ≠ ranking;
- impressions de Bing pueden incluir superficies distintas a Search clásico;
- ausencia de grounding query no significa penalización;
- cambios entre cortes pueden responder a volumen de preguntas, updates o contenido, sin causalidad demostrada.

## 7. Entregable recomendado por corte

Un registro breve, versionable y sin PII:

- fecha del corte;
- periodo comparado;
- top cambios materiales;
- URLs/queries con señal real;
- anomalías;
- hipótesis que merece experimento;
- tareas derivadas;
- `NO_DATA` donde corresponda;
- enlaces o referencia a exports externos, sin commitear datos sensibles innecesarios.

## 8. Relación con otras ideas

- **B.6:** configura/verifica Bing; Q.2 establece la cadencia conjunta.
- **B.5:** benchmark de citaciones IA complementario, no duplicado.
- **C.3:** preguntas/queries reales pueden alimentar contenido.
- **Q.3:** cualquier cambio experimental derivado de los paneles debe registrarse antes de ejecutarlo.
- **Q.1:** CrUX aporta field CWV cuando exista muestra.

## 9. Definition of Done de la operación

Solo marcar una revisión como realizada cuando:

- GSC y Bing son accesibles;
- periodo y fecha están registrados;
- se revisan las mismas áreas mínimas del runbook;
- `NO_DATA` se registra explícitamente en lugar de inventar interpretación;
- se separan hechos de hipótesis;
- las acciones posteriores tienen owner/prioridad;
- no se crean cambios SEO solo por variación pequeña o vanity metrics.

## 10. Conclusión

Q.2 es una operación externa útil, no código pendiente. #135 acertó al cambiar su lectura de `IMPLEMENT_NOW` a `EXTERNAL_OPERATION`: el repo puede contener el runbook, pero solo los paneles y sus exports pueden demostrar que la revisión GSC+Bing existe realmente.