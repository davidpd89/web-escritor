# D.12 · Revalidación de producción — anterior/siguiente en series

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **CONDITIONAL · NO_CANONICAL_SERIES_SEQUENCE · RELATED_IS_NOT_ORDER · NO_CODE**.

## 1. Resultado

D.12 sigue condicionada. El sitio tiene jerarquía, hubs, relaciones y navegación contextual, pero no se ha demostrado una serie editorial canónica que requiera una secuencia `anterior/siguiente`.

No se debe fabricar esa secuencia a partir de fechas, slugs, filesystem o `relatedIds`.

## 2. Evidencia directa de `content-registry.json`

El registry actual define una autoridad clara con defaults y entradas que usan campos como:

- `id`;
- `url`;
- `type`;
- `territory`;
- `parentId`;
- `hubId`;
- `discoverability`;
- `audience`;
- `jobs`;
- `relatedIds`;
- `searchIndex` / `sitemap`;
- `sourceFile`.

En las entradas directamente inspeccionadas de Obras, Samuel, Cuaderno, temas, artículos y recomendaciones no aparece un contrato explícito de posición de serie.

## 3. `relatedIds` no es orden editorial

El registry sí usa `relatedIds`, por ejemplo para conectar una obra con otros contenidos relevantes.

Ese campo responde a una relación semántica, no a una secuencia. Convertir la posición del array en `previous/next` introduciría una semántica nueva no declarada.

Regla:

```text
related content ≠ ordered series
```

## 4. Topic/hub tampoco implica serie

`parentId` y `hubId` sitúan una pieza dentro de la arquitectura. Un tema como fantasía de portales puede agrupar artículos sin que exista un orden recomendado de lectura.

No se deriva next/prev de pertenecer al mismo hub.

## 5. Trigger editorial que falta

D.12 se activa cuando exista una secuencia cuya posición importe de verdad, por ejemplo:

```text
Parte 1
Parte 2
Parte 3
```

y esa intención editorial se declare en datos canónicos.

No basta con tener dos artículos relacionados.

## 6. Contrato mínimo futuro

Cuando aparezca una serie real, ampliar la autoridad existente con el mínimo equivalente a:

```text
seriesId
seriesPosition
```

El naming exacto se decide contra el schema vigente en ese momento.

El checker deberá impedir:

- posiciones duplicadas;
- miembros no públicos/gated como destino navegable;
- serie de un solo elemento si no tiene sentido;
- enlaces generados fuera de la autoridad;
- drift HTML/datos;
- inferencia por fecha o ruta.

## 7. Render futuro

Si el gate se cumple:

- generar en build;
- `<nav>` con etiqueta específica;
- `<a href>` normales y crawlables;
- nombres descriptivos de destinos;
- anterior/siguiente solo cuando existan;
- no sticky por defecto;
- touch/foco visibles;
- integración con la misma plantilla de artículo.

## 8. Qué no hacer

- no next/prev cronológico sitewide;
- no orden alfabético;
- no usar `relatedIds` como lista ordenada;
- no hardcodear vecinos en HTML;
- no crear `series-links.json` paralelo;
- no JavaScript runtime para calcular vecinos;
- no convertir topic collections en series sin intención editorial.

## 9. Estado actual

```text
content registry = PRESENT
related graph = PRESENT
section/context navigation = PRESENT
explicit ordered-series owner = NOT_DEMONSTRATED
editorial trigger = NOT_MET
```

Por ello no se cambia a `ALREADY_COVERED`, pero tampoco procede implementar.

## 10. Definition of Done

- [x] registry actual inspeccionado directamente;
- [x] relaciones existentes diferenciadas de secuencia;
- [x] no se infiere orden accidental;
- [x] trigger editorial preservado;
- [x] contrato futuro mínimo definido;
- [x] sin nueva autoridad ni código.

## Estado para Claude

Mantener D.12 condicionada. Cuando exista una serie auténtica, modelar su orden en la autoridad de contenido y generar navegación desde ahí; hasta entonces no añadir anterior/siguiente general al Cuaderno.