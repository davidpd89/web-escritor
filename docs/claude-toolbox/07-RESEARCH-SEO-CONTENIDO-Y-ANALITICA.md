# 07 — Research, SEO, contenido y analítica

Este capítulo cubre herramientas que ayudan a Claude a **obtener mejores fuentes o datos**, no a sustituir las autoridades ya creadas para SEO, Search Console, IA o Brevo.

## 1. Context7 — documentación de software actual

```bash
/plugin install context7@claude-plugins-official
```

### Cuándo usar

- API/library cuya versión importa;
- sintaxis de una dependencia;
- ejemplo de integración que puede haber cambiado;
- migración de una librería;
- comprobar que una respuesta de Claude corresponde a la versión real.

### Cuándo no usar

- HTML/CSS platform estándar si una fuente primaria de navegador/MDN resuelve mejor;
- información editorial de David/libros;
- decisiones de diseño;
- SEO policies de Google cuando existe documentación Google primaria.

### Auth

Funciona anónimo. `CONTEXT7_API_KEY` solo si límites/uso real lo justifican.

## 2. Firecrawl — research estructurado, PILOT

Firecrawl ofrece crawl/scrape/map/search mediante API/MCP/plugins según integración disponible.

### Casos de uso válidos

- mapear la arquitectura pública de 10 sitios editoriales de referencia;
- recuperar headings/navigation de una muestra para comparar patrones;
- revisar documentación dispersa de un vendor;
- inventariar páginas de una editorial/medio;
- capturar evidencia estructurada antes de una auditoría.

### No usar

- clonar visualmente un sitio;
- scrapear grandes volúmenes sin necesidad/licencia;
- ingerir todo un dominio en Claude “por si acaso”;
- sustituir la inspección visual de Chrome/Figma;
- usar contenido de terceros como copy propio.

### Key

Si se adopta: `FIRECRAWL_API_KEY` local/secret store. No crearla antes del piloto.

### Pilot

Pregunta: ¿reduce significativamente tiempo y mejora evidencia frente a web search + Chrome para la matriz de referencias? Si no, no mantenerlo.

## 3. Exa — deep research, PILOT

Útil para encontrar fuentes/documentos semánticamente relacionados y extraer contenido.

### Buen fit

- descubrir entrevistas/reseñas/recursos externos sobre autores o tendencias;
- localizar fuentes primarias menos obvias;
- research técnico/documental.

### Gate

Comparar 20 consultas difíciles contra la búsqueda web habitual:

- precisión;
- fuentes primarias;
- frescura;
- duplicados;
- coste.

Solo adoptar si existe ganancia medible.

## 4. SearchFit SEO — secundario, no autoridad

Puede existir como plugin/SEO toolkit, pero este proyecto ya tiene documentación dedicada a Google SEO, Search Console y AI discoverability.

Regla:

- puede detectar un error técnico concreto;
- no puede decidir prioridades por un score propietario;
- no puede reescribir titles/content automáticamente;
- cualquier recomendación que contradiga Google/W3C/contrato propio se descarta.

Clasificación: `DEFER`.

## 5. Google Search Console — no duplicar

La PR/autoridad Search Console ya define:

- performance;
- indexation;
- URL inspection;
- APIs;
- BigQuery;
- GenAI reports;
- operations.

Claude puede usar esos conectores/scripts cuando se implementen. Esta toolbox solo documenta que el acceso debe ser read-first y no mezclar Search Console credentials con un MCP genérico.

## 6. CrUX API / CrUX History API

Esto sí es útil para diseño/performance porque aporta experiencia **de usuarios reales**, distinta de Lighthouse lab.

### Uso

- LCP/INP/CLS por origin/URL cuando haya datos;
- evolución histórica;
- comprobar si una mejora visual costosa ha empeorado field performance;
- no reaccionar a una sola corrida de Lighthouse.

### Auth

La CrUX API/History API se habilita en Google Cloud y usa API key. Si se implementa automatización:

- key separada/restringida;
- env/secret GitHub, nunca repo;
- cuota monitorizada;
- fallback claro si no hay suficiente tráfico/datos.

### Importante

“No hay datos CrUX” no significa “la página es rápida”. Significa que el dataset no tiene suficiente señal para esa granularidad.

## 7. PageSpeed Insights API

Útil para consultas programáticas puntuales, especialmente si necesitamos repetir auditorías fuera de LHCI. Pero el repo ya tiene Lighthouse CI.

Clasificación: `ON_DEMAND`, no añadir workflow duplicado por defecto.

Usar para:

- ver field/lab data combinados cuando proceda;
- diagnóstico externo de una URL publicada;
- comparar con CrUX.

No convertir el PSI score en KPI de diseño.

## 8. Google Trends

No requiere plugin Claude específico para ser útil.

Casos:

- lenguaje que usan lectores;
- estacionalidad de temas;
- comparación relativa de conceptos;
- calendario editorial.

No usar 0–100 como volumen absoluto ni para decidir cambios visuales.

## 9. Analytics actual vs PostHog/Amplitude

El proyecto ya ha tomado decisiones de analytics/privacy. PostHog y Amplitude son productos reales y tienen integraciones agentic, pero introducirlos cambia:

- script/runtime;
- data collection;
- privacy/legal;
- consent;
- CSP;
- operación.

Por tanto **no son plugins de Claude que debamos instalar simplemente para analizar mejor**.

### Reabrir PostHog si

- necesitamos experiment flags/surveys/session/product analytics que el stack actual no puede responder;
- existe un caso de negocio definido;
- privacidad/consentimiento se aprueban;
- se hace PR específica.

### Reabrir Amplitude si

Hay una necesidad de product analytics avanzada que justifica adoptar esa plataforma en vez de otra. No ambas.

## 10. Sentry

Mismo principio. Sentry es útil cuando existe un problema de errores/runtime que necesitamos capturar en campo.

Para un sitio estático con JS relativamente acotado:

- primero console QA, Playwright y logs existentes;
- si errores reales en producción no son observables, evaluar Sentry;
- cualquier SDK nuevo requiere privacy/performance/CSP review.

El plugin Sentry solo tiene valor **después** de que Sentry sea una fuente de datos real del proyecto.

## 11. Clarity / heatmaps / replay

No se instala como “plugin que nos dirá el diseño correcto”. Session replay/heatmaps pueden ayudar a formular hipótesis, pero:

- están sujetos a privacidad/consentimiento;
- no explican intención por sí solos;
- un heatmap no sustituye user test;
- incorporar un tracker por una pregunta visual puntual es desproporcionado.

Clasificación: `DEFER` hasta que la PR de privacidad/product analytics lo justifique.

## 12. Maze / user testing

No hace falta un MCP para que sea una herramienta de alto valor.

Usar estudios con tareas concretas:

- “Encuentra dónde leer un fragmento de Manecillas.”
- “Dime cuándo crees que ha terminado una sección y empieza la siguiente.”
- “Encuentra una herramienta para analizar ritmo.”
- “¿Qué tres cosas recuerdas después de recorrer esta página?”

Claude puede:

1. diseñar test;
2. preparar variantes/prototype;
3. organizar resultados anonimizados;
4. codificar temas;
5. proponer hipótesis.

No debe inventar participantes ni respuestas.

## 13. Research de referencias visuales

### Fuentes con valor metodológico

- case studies de estudios (Pentagram, AREA 17, etc.);
- premios con criterios públicos (Webby/CSSDA/Awwwards);
- sitios editoriales vivos;
- Fonts In Use;
- literatura UX de NN/g, Baymard cuando aplique;
- docs de browser/WCAG para constraints.

### Método de Claude

Para cada referencia guardar:

```text
URL
fecha
qué problema resuelve
qué decisión observable interesa
qué NO copiar
qué familia David podría aprender de ello
riesgos responsive/a11y/perf
```

Esto convierte inspiración en evidencia, no en moodboard infinito.

## 14. Investigación de competencia / autores

Firecrawl/Exa/browser pueden usarse para analizar:

- arquitectura;
- discoverability;
- treatment de books/press/newsletter;
- velocidad visual;
- navegación;
- rich media;
- recursos para lectores.

Nunca para:

- copiar copy;
- replicar trade dress;
- generar “la web de X pero con David”;
- asumir que algo está bien porque otro autor lo usa.

## 15. Data minimization

Toda herramienta de research/analytics debe responder:

- ¿necesita datos de usuarios o solo páginas públicas?
- ¿se puede lograr con datos agregados?
- ¿se puede ejecutar una semana en vez de permanentemente?
- ¿qué cambia en privacidad/CSP?
- ¿qué dato concreto decide una acción?

Si no hay una decisión que dependa del dato, no se recolecta.