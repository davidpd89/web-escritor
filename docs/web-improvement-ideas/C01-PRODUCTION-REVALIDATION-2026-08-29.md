# C.1 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #176  
Decisión operativa: **IMPLEMENTED_IN_PR · OPERATIONAL_RUNBOOK · NO_EXECUTION_FICTION**

## Resultado

La hipótesis histórica de C.1 sigue siendo útil, pero no como calendario editorial autónomo ni como nueva fuente de facts. El repo actual ya posee las autoridades que deben gobernar el lanzamiento:

- `editorial-facts.json`: facts canónicos de Manecillas;
- `docs/CONTENT-PARITY-MANECILLAS-V1.md`: contrato de propagación/gating;
- `data/analytics-events.json`: taxonomía única de eventos;
- landing, fragmentos, prensa y newsletter existentes.

Lo que **no existía** en `main` era un runbook operativo de campaña que conectara fechas, estado, evidencia, métrica y gate sin fingir que acciones externas ya se habían ejecutado.

Por eso C.1 se implementa documentalmente con `C01-LAUNCH-OPERATIONS-RUNBOOK-2026.md`. No se crea código, app, segundo fichero de facts ni segundo sistema de analítica.

## Corrección de la reconstrucción histórica

El documento histórico recupera fases en las que aparecía Duomo como supuesto editorial. Esa información se conserva porque forma parte de la historia de #135, pero **no es autoridad de producción**.

La autoridad actual del repo fija para *Las manecillas del recuerdo*:

- editorial: Monza Ediciones;
- publicación: 2026-09-03;
- ISBN: `979-8-90514-935-1`;
- 272 páginas;
- PVP editorial: 16 €;
- formato: Paperback;
- `purchaseUrl: null`.

`docs/CONTENT-PARITY-MANECILLAS-V1.md` confirma la misma autoridad y prohíbe derivar un `Offer`, retailer o CTA comercial de la fecha/PVP mientras no haya destino real verificado.

## Estado real al 29/08/2026

### Evidencia de repo

El repo demuestra:

- landing canónica de Manecillas;
- fecha 03/09/2026 y Monza en HTML/JSON-LD;
- 272 páginas, ISBN y PVP coherentes con la autoridad;
- tres fragmentos públicos aprobados;
- fuente newsletter `manecillas`;
- eventos `newsletter-manecillas`, `leer-fragmento-manecillas`, `sample-start-manecillas` y `sample-complete-manecillas`;
- ausencia deliberada de URL comercial de Manecillas mientras `purchaseUrl` sea `null`.

### Evidencia web actual

La búsqueda web del 29/08/2026 devuelve la home pública de `davidportodiaz.com` con “Las manecillas del recuerdo · 3 septiembre 2026”. La copia indexada de la URL específica de la obra sigue mostrando una versión antigua “En proceso de publicación”, lo que demuestra precisamente por qué una respuesta del índice web no debe utilizarse como fuente factual superior al repo actual.

No se pudo obtener mediante la búsqueda disponible una ficha indexada de Monza para revalidar independientemente el detalle comercial. Por tanto, esta PR **no declara compra/preventa/retailer live** y mantiene el gate `purchaseUrl:null`.

## Ausencia comprobada de owner operativo

Se inspeccionaron directamente las colecciones `docs/` y `data/` del árbol de `main`. No existe `docs/launch/`, `data/lanzamiento-manecillas.json` ni otro calendario/scorecard de campaña vigente que deba extenderse.

`CONTENT-PARITY-MANECILLAS-V1.md` no es ese owner: gobierna facts y paridad de superficies, no ejecución de acciones externas.

Esto hace legítimo un runbook C.1, pero solo como **coordinador operativo subordinado** a las autoridades ya existentes.

## Contrato del runbook añadido

El runbook introduce seis estados explícitos:

- `VERIFIED_REPO`;
- `VERIFIED_EXTERNAL`;
- `UNVERIFIED_EXTERNAL`;
- `PLANNED`;
- `BLOCKED`;
- `NOT_APPLICABLE`.

Las acciones históricas del 20–27/08 no se convierten en `DONE` solo porque su fecha haya pasado. Cuando el repo solo demuestra la superficie web pero no la publicación social/newsletter, se separan ambas capas.

La ventana 29/08–17/09 queda convertida en una secuencia ejecutable con:

- objetivo;
- métrica real existente;
- gate factual/spoiler/comercial/assets;
- condición de cancelación;
- evidencia requerida.

## Métricas

No se crea un score compuesto de lanzamiento. Se preservan dimensiones independientes:

- tráfico a landing;
- newsletter accepted (`newsletter-manecillas`), sin confundirlo con DOI confirmado;
- clic a fragmentos;
- sample start;
- sample completion;
- compra solo si llega a existir una fuente comercial verificable;
- señales cualitativas con evidencia.

El runbook prohíbe traducir clics/tráfico a ventas o causalidad sin evidencia.

## Gates que permanecen

### Comercio

`purchaseUrl:null` sigue siendo el gate. La decisión editorial de presentar el libro como “publicado el 3 de septiembre de 2026” antes de esa fecha está expresamente documentada en `editorial-facts.json` y **no** equivale a disponibilidad comercial.

### Cubierta / high-res

La incidencia editorial `knownEditorialIncident.coverInstagramPrinted` sigue `must-not-propagate`. No se desbloquea press-kit/high-res ni campañas que amplifiquen ese error por el mero lanzamiento.

### Spoilers

Se reutilizan premisa y fragmentos ya aprobados. El calendario no autoriza material nuevo con spoilers.

## Qué no se implementa

- no se toca HTML por una necesidad inexistente;
- no se crea `/lanzamiento/` público;
- no se crea JSON de campaña;
- no se crea workflow cron;
- no se automatizan posts/newsletters;
- no se inventa ejecución pasada;
- no se inventa retailer/preventa;
- no se duplica analytics;
- no se reescribe el documento histórico para borrar Duomo de su contexto original.

## Definition of Done

- [x] snapshot histórico preservado;
- [x] `main` real inspeccionado directamente;
- [x] factual authority actual revalidada;
- [x] paridad landing/facts comprobada;
- [x] ausencia de owner operativo comprobada en `docs/` y `data/`;
- [x] hueco real convertido en runbook auditable;
- [x] métricas reutilizan taxonomía existente;
- [x] ejecución externa no falsificada;
- [x] compra sigue gated por `purchaseUrl`;
- [x] incidencia de cubierta preservada;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Conclusión

C.1 queda **implementada como capa operativa mínima**. El repo ya tenía facts, superficies y analítica; faltaba coordinación de campaña. El nuevo runbook rellena ese hueco sin competir con las autoridades existentes y, sobre todo, sin convertir un calendario deseado en un registro ficticio de acciones ejecutadas.
