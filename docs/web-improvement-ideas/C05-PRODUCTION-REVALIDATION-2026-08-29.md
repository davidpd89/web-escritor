# C.5 · Revalidación de producción — expansión de recomendaciones por subgénero/edad/tono

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #180  
Estado: **REJECT_MECHANICAL_EXPANSION · CURRENT_ARCHITECTURE_COMPACT · DEMAND_GATE_REQUIRED · NO_CODE**

## Veredicto

No se debe ampliar ahora `recomendaciones/` con páginas generadas por combinaciones de subgénero, edad, tono o filtros similares.

La arquitectura real es compacta y suficiente para el estado actual: el directorio público contiene el hub, la política editorial y dos superficies temáticas canónicas con intención distinta:

- `/recomendaciones/portal-fantasy-espanol/`;
- `/recomendaciones/magia-con-coste/`.

No existe una colección mecánica de páginas por edad/tono que haya que completar ni un hueco técnico que obligue a producir más URLs.

## Evidencia directa de `main`

### Portal fantasy

`/recomendaciones/portal-fantasy-espanol/` es una lista editorial propia de diez obras disponibles en español. Declara criterio de selección, edición verificada, transparencia de afiliación y una entidad `ItemList` propia.

### Magia con coste

`/recomendaciones/magia-con-coste/` resuelve otra intención: seis obras donde reglas, recursos o consecuencias de la magia tienen peso narrativo. El texto distingue expresamente coste de magia y hard magic en vez de duplicar el enfoque de portal fantasy.

### Política editorial

`/recomendaciones/politica-de-recomendaciones/` mantiene `noindex, follow` y separa:

- hechos bibliográficos verificables;
- juicio editorial;
- experiencia personal;
- afiliación;
- presencia de obra propia;
- correcciones.

No hay necesidad de crear otra política o dataset para C.5.

## R.21 — degradación correcta de evidencia

La reconstrucción histórica cita aproximadamente `91 impresiones / 1 clic` para la consulta «portal fantasy».

Durante la revalidación C.3 se buscó el artefacto primario en el snapshot histórico y Drive y no se recuperó. Por tanto C.5 hereda el estado correcto:

`R21 = HISTORICAL_UNVERIFIED`

Consecuencias:

- no usar 91/1 como baseline actual;
- no fijar thresholds a partir de ese número;
- no afirmar que esa oportunidad sigue teniendo hoy el mismo volumen;
- sí conservarlo como antecedente histórico de #135.

La lógica de decisión no depende de ese número concreto: primero se optimizan activos existentes cuando existe demanda medible y solo se abre una URL nueva si su intención es realmente distinta.

## Gate para una URL nueva

Reabrir C.5 únicamente si se cumplen simultáneamente:

```text
measured demand
AND distinct user/search intent
AND existing pages cannot satisfy it cleanly
AND substantial original editorial analysis
AND maintenance owner/capacity
AND no scaled-template pattern
```

Fuentes de demanda válidas:

- Search Console/Bing dentro de una ventana reproducible;
- preguntas reales agregadas y sin PII (C.3);
- referrals/enlaces hacia una necesidad concreta;
- Google Trends como contexto, no como volumen absoluto;
- necesidad editorial demostrada.

## Jerarquía de decisión

1. `ENRICH_EXISTING`
2. `ADD_SECTION_OR_FILTER_WITHOUT_NEW_INDEXABLE_URL`
3. `NEW_URL` solo si la intención es autónoma
4. `NO_ACTION`

Una query diferente no equivale automáticamente a una intención distinta.

## Riesgo vigente de scaled content

La política de spam de Google sigue definiendo *scaled content abuse* como la creación de muchas páginas principalmente para manipular rankings y con poco o ningún valor para usuarios, independientemente de cómo se generen.

C.5 no debe convertirse en:

- una URL por edad;
- una URL por tono;
- una URL por combinación de filtros;
- listas sintetizadas desde retailers;
- cuerpos prácticamente idénticos con titles diferentes;
- páginas creadas solo para completar un cluster.

## Qué sí puede crecer

La colección puede crecer cuando una nueva pieza tenga una razón editorial independiente. Eso puede incluir una nueva recomendación temática, pero debe demostrar:

- criterio propio;
- selección razonada;
- edición/fuentes verificables donde corresponda;
- transparencia de afiliación/obra propia;
- suficiente diferencia respecto a las dos páginas existentes.

## Relación con C.3

C.3 es una fuente de demanda, no una fábrica de páginas. Si varias preguntas reales apuntan a una segmentación que no cabe en las URLs existentes, C.5 puede reabrirse; de lo contrario se enriquece una superficie existente.

## DoD

- [x] arquitectura real inspeccionada directamente;
- [x] política editorial inspeccionada;
- [x] dos páginas temáticas inspeccionadas;
- [x] R.21 degradado a `HISTORICAL_UNVERIFIED`;
- [x] gate NEW vs ENRICH definido;
- [x] política Google vigente revalidada;
- [x] no se crea contenido nuevo;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**REJECT_MECHANICAL_EXPANSION · CURRENT_ARCHITECTURE_COMPACT · DEMAND_GATE_REQUIRED · NO_CODE**
