# B.5 · Monitorizar citaciones y respuestas de IA

Fecha de reconstrucción: 2026-08-29

Idea original: revisar periódicamente cómo ChatGPT, Perplexity, Copilot y otras superficies responden sobre David Porto Díaz, sus obras y recursos, y qué fuentes citan.

Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.

Estado final: `ALREADY_COVERED`.

## Veredicto reconciliado

**ALREADY_COVERED. EJECUTAR Y MANTENER EL BENCHMARK YA DISEÑADO; NO CREAR OTRO “AI VISIBILITY SCORE”.**

B.5 no quedó descartada por falta de valor. Ocurrió lo contrario: la investigación evolucionó desde una revisión manual trimestral sencilla hasta un sistema de medición mucho más riguroso ya documentado en `docs/ai-discoverability/08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md`. Por eso la autoridad final la clasifica como cubierta: el siguiente trabajo es ejecutar ese marco y guardar evidencias, no diseñar otra metodología paralela.

## 1. Hipótesis original de #135

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` planteó búsquedas periódicas como:

- “David Porto Díaz”;
- “Samuel entre mundos”;
- preguntas sobre Las manecillas del recuerdo;
- consultas de descubrimiento/recomendación.

La versión inicial decía que bastaba una revisión manual trimestral para saber si el sitio estaba siendo citado y con qué precisión.

## 2. Evolución cronológica

### 2.1 · Revisión exhaustiva → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` encontró que la estrategia de benchmark/monitor ya estaba desarrollada en `docs/ai-discoverability/` y cambió la tarea de “crear un monitor” a **ejecutar la autoridad existente**.

### 2.2 · Matriz final → `IMPLEMENTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` preservó el valor operacional de ejecutar un benchmark manual/versionado de prompts, midiendo exactitud factual y fuentes citadas, y rechazó comprar una métrica opaca solo por disponer de ella.

Ese `IMPLEMENTAR` intermedio no contradice el final `ALREADY_COVERED`: significa que **la rutina sí merece hacerse**, mientras que el diseño/metodología ya está construido.

### 2.3 · Autoridad final → `ALREADY_COVERED`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó:

> El plan/benchmark de discoverability IA ya existe. Ejecutarlo periódicamente; no comprar “AI visibility scores” sin impacto decisional.

### 2.4 · Revalidación independiente

La revisión independiente mantuvo B.5 y elevó además una oportunidad complementaria: Microsoft Clarity AI Citations puede pilotarse **sin instalar tracking comportamental**, verificando el dominio mediante Google Search Console o Bing Webmaster Tools.

Esto es una fuente adicional posible, no un reemplazo del benchmark multi-plataforma.

### 2.5 · Decimoquinta pasada R.82 → Clarity con límites claros

`docs/IDEAS-MEJORA-WEB-DECIMOQUINTA-PASADA-2026-08-28.md` corrigió una posible sobreinterpretación:

- AI Visibility / Citation dashboard de Clarity sí puede ser útil;
- verificar con GSC/BWT evita añadir tracking solo para esta pregunta;
- el MCP oficial de Clarity usa Data Export API;
- no hay evidencia en esas fuentes de que instalar el MCP exponga automáticamente el Citation dashboard;
- por tanto: `PILOT_NO_TRACKING_MCP_DEFER`.

Secuencia:

```text
hipótesis: revisión manual trimestral
→ se descubre autoridad ai-discoverability ya diseñada
→ matriz: ejecutar benchmark real
→ autoridad final: ALREADY_COVERED como sistema
→ R.82: Clarity Citations opcional sin tracking; MCP no asumido
→ revalidación: mantener y ejecutar
```

## 3. Estado real de `main`

`docs/ai-discoverability/08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md` ya define un sistema considerablemente más completo que la hipótesis original.

Incluye:

- corpus inicial recomendado de 50 prompts;
- categorías de hechos, discovery, Samuel, Manecillas, topic authority y negative controls;
- Tier A mensual: ChatGPT Search, Gemini/Search-grounded, Claude con web search, Perplexity y Copilot;
- Tier B trimestral;
- metadata de ejecución: fecha, plataforma, superficie, modelo mostrado, locale y prompt ID;
- factual accuracy;
- official mention;
- recommendation fit;
- calidad/tipo de fuente citada;
- 3 réplicas para prompts estratégicos cuando se evalúe un cambio serio;
- cadencias semanal/mensual/trimestral;
- citation ledger;
- taxonomía de errores stale/hallucination/entity collision/attribution/commerce/recommendation mismatch/source quality;
- referrals cuando sean observables;
- crawler observability;
- umbral de incidentes P0;
- guardrails de privacidad;
- rechazo explícito de una única nota “AI Visibility 87/100”.

Por tanto, B.5 no necesita un nuevo fichero de diseño ni una nueva plataforma para estar definida.

## 4. Qué se puede medir de verdad

El marco de #135 distingue correctamente entre señales observables y preguntas imposibles de responder de forma completa.

### Observable

- citas/reportes propios de proveedores cuando existen;
- URLs citadas;
- grounding queries cuando el proveedor las expone;
- respuestas a un benchmark controlado;
- errores factuales;
- referrals identificables;
- crawler hits/errores cuando haya logs.

### No observable globalmente

- “qué piensa ChatGPT de David” como estado estable;
- posición universal dentro de todos los modelos;
- porcentaje de conversaciones privadas donde aparece;
- prompts de otros usuarios;
- un ranking interno transversal de todas las IA.

No rellenar esos huecos con métricas comerciales opacas.

## 5. Benchmark mínimo preservado

### Hechos

Ejemplos:

- ¿Quién es David Porto Díaz?
- ¿Qué libros ha publicado?
- ¿Qué es Noveris?
- ¿Qué editorial publica Las manecillas del recuerdo?

### Descubrimiento/recomendación

- autores españoles de fantasía juvenil;
- portal fantasy español;
- novela coral sobre memoria/familia;
- recursos gratuitos para escritores en español.

### Negative controls

Consultas donde David/Samuel/Manecillas **no deberían** aparecer, para detectar sobreoptimización o recomendaciones engañosas.

## 6. Scoring sin nota única

Preservar dimensiones separadas:

- exactitud factual;
- mención;
- cita del sitio oficial;
- encaje de recomendación;
- fuente citada;
- stale errors.

No sumarlas en una sola cifra que oculte que una plataforma puede acertar facts y fallar recomendaciones, o citar una fuente externa mejor/peor.

## 7. Clarity AI Citations: complemento opcional

La investigación tardía de #135 permite un piloto si el dominio es elegible/verificable, preferentemente mediante GSC/BWT y **sin instalar tracking solo para obtener citaciones**.

Fuente primaria:

- https://learn.microsoft.com/en-us/clarity/ai-visibility/ai-citations

Interpretación correcta:

- métricas de Clarity describen la cobertura/metodología de Clarity;
- no equivalen a “todas las IA”;
- compararlas con Bing AI Performance puede descubrir diferencias útiles;
- diferencias entre plataformas no son un bug por defecto.

MCP oficial:

- https://learn.microsoft.com/en-us/clarity/third-party-integrations/clarity-mcp-server
- https://github.com/microsoft/clarity-mcp-server

Solo pilotarlo si existe una pregunta recurrente que Data Export pueda responder. No generar tokens ni instalar MCP por tenerlo disponible.

## 8. Relación con B.6

B.5 define **cómo medir visibilidad/citas de forma amplia**.

B.6 trata específicamente la operación externa Bing Webmaster Tools + AI Performance. Los datos de Bing pueden alimentar B.5, pero no sustituyen el benchmark multi-plataforma.

## 9. Frecuencia recomendada de #135

- semanal: smoke factual P0 y stale facts críticos cuando tenga sentido;
- mensual: benchmark Tier A completo + citas/referrals disponibles;
- trimestral: Tier B, perfiles externos y cambios de documentación de crawlers/proveedores;
- adicional tras lanzamiento, cambio de ISBN/editorial, nueva obra, rediseño importante o incidente factual.

La frecuencia puede ajustarse al coste real. No automatizar miles de prompts para producir volumen de datos sin decisión asociada.

## 10. Guardrails operativos

- corpus versionado;
- locale documentado;
- separar search rápido de deep research;
- guardar respuesta/citas solo cuando los términos del producto/API lo permitan;
- no scrapear interfaces consumidor en contra de términos;
- no usar proxies/cuentas masivas para falsear locales;
- no usar el propio modelo medido como único juez de exactitud;
- hechos P0 comparados con autoridad canónica;
- recomendación revisada por humano;
- no almacenar datos personales innecesarios;
- no enviar conversaciones reales del asistente a herramientas GEO.

## 11. Definition of Done

### Historia recuperada

- [x] hipótesis manual original;
- [x] `ALREADY_COVERED` de revisión;
- [x] `IMPLEMENTAR` operacional de matriz explicado;
- [x] autoridad final `ALREADY_COVERED`;
- [x] benchmark actual inspeccionado;
- [x] R.82 Clarity AI Citations preservado;
- [x] revalidación independiente preservada.

### Ejecución futura

- [ ] corpus versionado ejecutado con fecha/plataforma;
- [ ] errores y citas guardados;
- [ ] Bing/Clarity incorporados solo si disponibles;
- [ ] ninguna nota universal inventada;
- [ ] decisiones derivadas documentadas.

## 12. Trazabilidad de #135

Aportan contenido específico:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-DECIMOQUINTA-PASADA-2026-08-28.md` (R.82);
- `docs/ai-discoverability/08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md`.

Se revisaron las restantes pasadas, fuentes, casos y blueprints; no cambian el estado final de B.5.

## 13. Recomendación

**MERGE como reconstrucción completa + `ALREADY_COVERED`.** El siguiente paso legítimo es ejecutar el benchmark existente y registrar resultados, no construir un segundo monitor.