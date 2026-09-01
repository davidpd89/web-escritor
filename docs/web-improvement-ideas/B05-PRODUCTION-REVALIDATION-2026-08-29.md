# B.5 · Revalidación de producción · 2026-08-29

## Veredicto

**IMPLEMENTED_IN_PR · CORPUS_OPERATIONALIZED · EXTERNAL_EXECUTION_REQUIRED**

La metodología histórica estaba bien diseñada, pero la inspección del `main` vivo encontró un hueco operativo concreto: el documento de autoridad proponía `data/ai-discoverability-benchmark.json` y ese corpus versionado no existía.

B.5 pasa por tanto de docs-only a implementación mínima y útil: **materializar el corpus y proteger su contrato**, sin fabricar resultados de productos externos que no se pueden ejecutar de forma comparable desde CI.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- `docs/ai-discoverability/08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md`;
- ausencia real de `data/ai-discoverability-benchmark.json`;
- workflow `machine-authority-check.yml`;
- Microsoft Clarity AI Visibility/Citations;
- Bing Webmaster Tools AI Performance;
- límites metodológicos ya definidos por #135.

## Hueco real

La autoridad existente especificaba:

- corpus inicial de 50 prompts;
- categorías 10 facts / 10 discovery / 10 Samuel / 10 Manecillas / 5 topic authority / 5 negative controls;
- IDs y metadata de ejecución;
- dimensiones separadas de scoring;
- 3 réplicas solo cuando un prompt estratégico se use para medir un cambio serio;
- rechazo de un único `AI Visibility Score`.

Pero el fichero de corpus propuesto no estaba creado.

Eso significa que la metodología existía, pero cada ejecución aún podía improvisar prompts distintos y perder comparabilidad.

## Implementación

### `data/ai-discoverability-benchmark.json`

Se crea un corpus v1 con exactamente 50 prompts:

- `FACT-001..010` — hechos de entidad;
- `DISC-001..010` — descubrimiento;
- `SAM-001..010` — encaje de recomendación de Samuel;
- `MAN-001..010` — encaje de recomendación de Manecillas;
- `TOP-001..005` — autoridad temática;
- `NEG-001..005` — controles negativos.

Los prompts de discovery/recommendation/topic/negative son **neutrales**: no nombran David Porto Díaz, Samuel, Manecillas ni Noveris en la pregunta. Así se evita dirigir al sistema hacia el resultado que queremos medir.

Los prompts factuales sí nombran la entidad porque su finalidad es medir exactitud sobre esa entidad concreta.

### Scoring preservado sin nota universal

El corpus registra las dimensiones de la autoridad original:

- factual accuracy;
- official mention;
- recommendation fit;
- citation quality.

`aggregateScore` está fijado a `null` deliberadamente.

### Negative controls

Los cinco controles negativos declaran `expectedTargetRecommendation: none`.

No se usan para castigar ausencia de mención; se usan para detectar recomendaciones engañosas/sobreoptimización cuando David/Samuel/Manecillas no encajan.

### Contrato de ejecución

El corpus conserva:

- locale `es-ES`;
- Tier A/Tier B;
- deep research separado;
- 1 réplica por defecto y 3 para medición estratégica;
- metadata mínima por run;
- no prescribir almacenamiento de cookies, cuentas, IDs de usuario o tokens de sesión.

## QA nuevo

Se añade `tests/test-ai-discoverability-benchmark.py`.

Valida:

1. schema/corpus versionados;
2. exactamente 50 prompts;
3. distribución exacta 10/10/10/10/5/5;
4. IDs únicos y prefijo coherente por categoría;
5. prompts únicos y concisos;
6. evaluation correcta por familia;
7. `trackedEntities` explícitas;
8. `expectedTargetRecommendation=none` solo en controles negativos;
9. que los prompts no factuales no nombren las entidades medidas;
10. ausencia de score agregado;
11. política de réplicas;
12. metadata mínima de ejecución;
13. ausencia de campos de sesión/identidad personal innecesarios.

## Integración CI

Se extiende `.github/workflows/machine-authority-check.yml`, owner natural de las superficies machine-readable/AI del repo:

- paths incluyen el corpus y su test;
- nuevo step `Validate AI discoverability benchmark corpus`;
- no se crea un workflow paralelo.

El Required merge gate también ejecuta los tests Python universales del repo.

## Qué NO se implementa

No se inventa una tabla de resultados.

No es legítimo escribir en el repo respuestas atribuidas a:

- ChatGPT Search;
- Gemini Search-grounded;
- Claude web search;
- Perplexity;
- Copilot;

sin haber ejecutado esas superficies con fecha, locale, producto y modelo observables.

Tampoco se scrapean interfaces consumidor ni se simulan con otro modelo.

La ejecución real sigue siendo externa/manual o mediante APIs/productos cuyo uso y términos permitan guardar resultados comparables.

## Revalidación Microsoft 2026

### Bing Webmaster Tools AI Performance

Microsoft documenta en preview:

- total citations;
- average cited pages;
- grounding queries;
- actividad de citas por URL;
- tendencias.

También aclara que citation count no equivale a ranking/importancia/posición.

Fuente:

- `https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview`.

### Clarity Citation dashboard

Microsoft Clarity permite verificar dominio mediante:

- tracking Clarity;
- Google Search Console;
- Bing Webmaster Tools.

Por tanto, el piloto puede hacerse sin instalar tracking comportamental solo para habilitar Citation dashboard.

Clarity muestra page citations, share of authority, AI referral traffic, grounding queries y cited pages. Son métricas de la cobertura de Clarity, no una verdad universal de todas las IA.

Fuente:

- `https://learn.microsoft.com/en-us/clarity/ai-visibility/ai-citations`.

### Clarity MCP

La documentación vigente del MCP describe acceso a datos de analytics mediante Data Export API token. No demuestra que el MCP exponga el Citation dashboard.

Se mantiene el guardrail histórico: no generar token/instalar MCP solo suponiendo que dará acceso a AI Citations.

Fuente:

- `https://learn.microsoft.com/en-us/clarity/third-party-integrations/clarity-mcp-server`.

## Próximo uso del corpus

Una ejecución válida debe guardar al menos:

```text
runDate
platform
surface
modelAsDisplayed
locale
loggedIn
locationMode
promptId
response
citations
```

Después puntuar dimensiones separadas y registrar errores materiales.

Para facts P0, contrastar contra autoridades canónicas del repo, no contra la memoria del evaluador.

## Triggers futuros

- nueva obra/lanzamiento → versionar corpus si cambia el universo de preguntas;
- cambio de producto/modelo → registrar metadata, no sobrescribir runs anteriores;
- nueva señal Bing/Clarity → añadir campo opcional si cambia una decisión;
- drift de prompt → nueva corpusVersion;
- automatización → solo mediante API/flujo permitido que preserve producto/superficie y reproducibilidad.

## Definition of Done

- [x] metodología histórica inspeccionada;
- [x] hueco `data/ai-discoverability-benchmark.json` confirmado;
- [x] corpus de 50 prompts materializado;
- [x] distribución histórica preservada;
- [x] prompts de recommendation/discovery neutralizados contra leading;
- [x] negative controls materializados;
- [x] scoring multidimensional preservado;
- [x] test de corpus añadido;
- [x] workflow propietario extendido;
- [x] Bing AI Performance revalidado;
- [x] Clarity Citations revalidado;
- [x] MCP no sobreinterpretado;
- [ ] CI del HEAD final completamente verde;
- [ ] primera ejecución externa real guardada cuando se disponga de las superficies comparables;
- [ ] revisión de Claude antes de merge.

## Cierre

B.5 ya no depende de improvisar un listado de prompts en cada revisión. El repo incorpora el corpus versionado y su contrato de QA. Lo único que queda necesariamente fuera del código es ejecutar productos externos reales y registrar resultados verdaderos; esa limitación se preserva explícitamente en lugar de rellenarla con datos sintéticos.