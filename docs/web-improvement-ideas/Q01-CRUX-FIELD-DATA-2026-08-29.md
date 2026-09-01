# Q.1 · Core Web Vitals de campo con CrUX — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `CONDITIONAL`.

## 1. Hipótesis original

Q.1 proponía disponer de un panel propio de Core Web Vitals de campo utilizando CrUX, para contrastar Lighthouse/QA de laboratorio con experiencia real de usuarios.

La idea es técnicamente válida, pero depende de una condición que no controla el repositorio: que el origen/URL tenga muestra suficiente para entrar en el dataset CrUX.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `IMPLEMENT_AFTER_CURRENT_DEBT`.

Se consideró de alto valor porque CrUX es field data real. La revisión fijó una regla esencial:

- `NO_DATA` es un resultado válido;
- no inventar métricas de campo si no existe muestra;
- Search Console/CrUX deben complementar, no reemplazar, el QA de laboratorio.

### Matriz final 28/08

Decisión: `CONDICIONAL`.

La matriz corrigió el impulso de automatizar desde el principio:

1. consultar primero CrUX Vis, gratis y sin integración;
2. solo si existe dataset y una necesidad repetida, considerar API/History API;
3. si no hay datos, mantener Lighthouse/browser QA.

### Autoridad final humana + machine-readable

Estado final: `CONDITIONAL`.

Regla final:

> CrUX Vis/no-key primero; API con key restringida solo si hay datos de campo suficientes.

## 3. Revalidación independiente

La revalidación independiente mantiene Q.1 y especifica CrUX Vis antes que API.

Las fuentes primarias de Google confirman:

- CrUX Vis visualiza datos históricos semanales de CrUX History API;
- no todos los sitios/orígenes tienen datos: puede faltar muestra suficiente;
- CrUX API da datos agregados reales a nivel de página/origen;
- la API requiere una API key de Google Cloud;
- CrUX API/History API y Search Console exponen vistas distintas del mismo tipo de field data y no deben confundirse con Lighthouse lab data.

## 4. Estado actual de `main`

El repositorio dispone de una capa de QA/lanzamiento fuerte —Lighthouse, reflow, accesibilidad, browser QA y release readiness—, pero esa evidencia no debe etiquetarse como field data.

En #135 se documentó que la muestra de campo era insuficiente en el corte revisado. No aparece evidencia nueva en `main` que autorice a afirmar ahora que el origen ya dispone de muestra CrUX suficiente.

Por tanto el estado práctico sigue siendo `CONDITIONAL`: primero se consulta la fuente pública.

## 5. Flujo correcto

### Nivel 0 — sin integración

Consultar CrUX Vis para:

- origen `https://davidportodiaz.com`;
- páginas clave solo si hay page-level data;
- LCP;
- INP;
- CLS;
- distribución por good / needs improvement / poor;
- evolución histórica disponible.

Registrar uno de dos resultados:

- `DATA_AVAILABLE`;
- `NO_DATA`.

`NO_DATA` no es un fallo del sitio ni de CI.

### Nivel 1 — análisis periódico manual

Si hay datos, incorporar un corte periódico a la revisión técnica sin construir dashboard propio.

Comparar:

- CrUX/field;
- Lighthouse/lab;
- trazas de interacción;
- cambios de plantilla/deploy.

No atribuir causalidad a un deploy solo porque la curva cambie.

### Nivel 2 — API

Solo si la consulta manual se vuelve repetitiva y el dataset es útil:

- usar CrUX API o History API;
- key restringida y gestionada fuera del repo;
- no commitear secretos;
- cachear/registrar únicamente datos agregados necesarios;
- definir cadencia acorde a la frecuencia real del dataset.

## 6. Qué no hacer

- crear un dashboard vacío porque CrUX no tiene muestra;
- sustituir Lighthouse por CrUX;
- tratar lab score como field CWV;
- generar un RUM propio solo para «tener datos» sin revisión de privacidad;
- exponer una API key en logs/commits;
- convertir pequeñas oscilaciones en causalidad de cambios concretos.

## 7. Trigger para automatizar

Q.1 solo pasa de `CONDITIONAL` a implementación cuando:

1. CrUX devuelve datos reales del origen o páginas relevantes;
2. hay una pregunta periódica que la consulta manual ya no resuelve cómodamente;
3. la automatización producirá una decisión o alerta concreta;
4. se define owner/cadencia/retención;
5. se evita duplicar Search Console o un panel de Google ya suficiente.

## 8. Definition of Done si se activa

- baseline guardado con fecha y granularidad;
- `NO_DATA` soportado como estado normal;
- LCP/INP/CLS distinguen origin/page cuando corresponda;
- no se mezclan lab y field en una misma métrica;
- key fuera de Git y restringida;
- fallo/ausencia de API no bloquea deploy;
- reportes describen periodos correctamente;
- cambios solo generan acción si existe umbral/criterio previamente definido.

## 9. Relaciones

- **E.2:** INP usa field data cuando exista; mientras tanto, traces reproducibles.
- **E.5:** performance budget de artifacts no sustituye CWV.
- **Q.3:** cualquier experimento de rendimiento debe registrar hipótesis/ventana antes de interpretar CrUX.
- **M.4:** uptime y CWV son problemas distintos.

## 10. Conclusión

Q.1 no autoriza construir un panel propio ahora. La decisión madura de #135 es `CONDITIONAL`: comprobar primero CrUX Vis; automatizar solo cuando exista muestra real y una necesidad repetida. Hasta entonces, el QA de laboratorio continúa siendo evidencia válida, pero debe llamarse exactamente eso: lab/QA, no field CWV.