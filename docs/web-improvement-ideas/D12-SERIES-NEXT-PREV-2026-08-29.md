# D.12 — Navegación siguiente/anterior en series editoriales

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`CONDITIONAL`**

## 1. Alcance

D.12 proponía ampliar la navegación contextual existente con enlaces “anterior / siguiente” cuando varias piezas formen una **serie editorial auténtica**.

Esta reconstrucción recupera directamente el razonamiento de #135 y evita convertir una idea condicional en paginación universal.

La PR es documental. No añade campos `series`, no cambia `content-registry.json` y no genera navegación nueva.

## 2. Veredicto

**`CONDITIONAL`**.

Implementar solo cuando exista al menos una serie real cuya secuencia tenga significado editorial y pueda modelarse explícitamente en la autoridad de contenido.

No ordenar artículos por:

- fecha;
- slug;
- orden del filesystem;
- posición actual en un listado;
- `relatedIds`;
- heurística automática.

#135 fue explícita: si se construye, el orden debe derivar de datos canónicos como `series` + `position`, no inferirse.

## 3. Idea original

La formulación inicial mezclaba tres conceptos:

1. breadcrumbs visuales;
2. contextual navigation ya existente;
3. “siguiente/anterior” en series del Cuaderno.

La revisión posterior separó responsabilidades. Los breadcrumbs terminaron tratados en A.6 y la navegación de sección ya tenía su propia arquitectura. El residuo neto de D.12 pasó a ser exclusivamente la navegación secuencial de **series auténticas**.

Esa reducción de alcance es una parte importante de la investigación y no debe perderse.

## 4. Evolución de la decisión

| Fase | Decisión | Razón |
|---|---|---|
| Lista original | propuesta | Facilitar continuidad entre capítulos/artículos de una serie. |
| Revisión 108/108 | `CONDITIONAL` | Solo series reales; modelar `series/position` en registry. |
| Matriz intermedia | `CONDICIONAL` | No secuenciar artículos arbitrariamente. |
| Autoridad final | `CONDITIONAL` | Derivar del registry. |
| Revalidación independiente | mantenida | No aparece evidencia para hacerla global. |
| `main` actual | sigue condicional | Registry usa relaciones, pero no se ha localizado un campo explícito `series/position`. |

## 5. Problema que sí podría resolver

En una serie deliberada, una persona puede llegar desde Search o desde un enlace directo al episodio 2/5. Sin contexto secuencial puede no saber:

- que existe una parte anterior;
- qué orden recomienda el autor;
- cuál es la siguiente entrega;
- cuándo ha terminado la serie.

En ese caso, next/prev puede aportar findability y continuidad reales.

## 6. Problema que NO debe crear

Un Cuaderno general no es una novela ordenada. Añadir “siguiente” por fecha puede transmitir una relación editorial inexistente.

Ejemplo incorrecto:

```text
Artículo sobre portal fantasy
→ siguiente porque se publicó después:
Crónica de la Feria del Libro
```

La secuencia sería técnicamente válida pero semánticamente arbitraria.

## 7. Autoridad correcta

La propuesta madura de #135 era extender la autoridad de contenido, no mantener una lista paralela en HTML/JS.

Esquema conceptual:

```json
{
  "id": "article-example-02",
  "series": "como-construi-noveris",
  "position": 2
}
```

El naming exacto debe decidirse al implementar según la versión vigente del registry. Lo importante es el contrato:

- identificador estable de serie;
- posición explícita;
- unicidad de posición dentro de la serie;
- solo contenido público/elegible;
- generación determinista;
- no inferencia por fecha/URL.

## 8. Reconciliación con `content-registry.json` actual

El `main` revisado continúa usando una autoridad central para rutas y relaciones, con campos como:

- `id`;
- `url`;
- `parentId`;
- `hubId`;
- `relatedIds`;
- flags de descubribilidad/indexación.

En la revisión de 2026-08-29 no se ha localizado un campo canónico explícito `series` que materialice el contrato de D.12.

Eso **no significa** que el sitio carezca de cualquier enlace anterior/siguiente ni que debamos implementarlo ahora. Significa que el modelo específico exigido por #135 no está demostrado como existente.

## 9. Diferencia entre `relatedIds` y una serie

`relatedIds` responde a:

> ¿qué contenidos están relacionados?

Una serie responde a:

> ¿qué contenidos forman una secuencia ordenada y cuál es la posición de este?

No son equivalentes.

Usar `relatedIds` para generar next/prev introduciría orden implícito y convertiría una relación semántica en una secuencia que quizá el autor no pretendía.

## 10. Diferencia con A.6 breadcrumbs

A.6 cubre jerarquía/ruta contextual:

```text
Inicio > Cuaderno > Tema > Artículo
```

D.12 cubre una secuencia lateral entre hermanos editoriales:

```text
Parte 1 ← Parte 2 → Parte 3
```

Una página puede necesitar ambas, una o ninguna.

No deben fundirse en un único sistema ambiguo.

## 11. Diferencia con topic collections

Las colecciones temáticas de A.1 agrupan contenido coherente, pero una colección tampoco implica orden.

Ejemplo:

```text
/fantasia-de-portales/
```

puede ser un hub temático sin que sus artículos deban leerse de primero a último.

Solo una colección declarada además como serie justificaría D.12.

## 12. Gate de implementación

Reabrir D.12 cuando se cumpla:

```text
EXISTE una serie editorial real
AND tiene al menos 2 piezas públicas
AND el orden es relevante para comprender/seguir el contenido
AND puede modelarse sin duplicar otra autoridad
```

Antes de eso, el estado permanece `CONDITIONAL`.

## 13. Blueprint si se activa

### 13.1 Datos

Añadir el mínimo contrato al registry o a la autoridad que lo haya sustituido:

```text
seriesId
seriesPosition
```

Opcionalmente metadatos de serie si existe una necesidad real:

```text
seriesTitle
seriesHubId
```

pero solo si no duplican `topic-collections`.

### 13.2 Validación

El checker debe detectar:

- posición duplicada;
- huecos si la política exige continuidad;
- miembro apuntando a serie inexistente;
- miembro no público;
- serie de un solo elemento si no tiene sentido;
- next/prev hacia noindex/gated;
- drift entre HTML generado y datos.

### 13.3 Render

La navegación debería generarse en build y contener:

- nombre de la serie cuando ayude;
- anterior solo si existe;
- siguiente solo si existe;
- etiquetas descriptivas, no solo flechas;
- enlaces crawlables normales `<a href>`;
- orden lógico en DOM.

### 13.4 Accesibilidad

- `nav` con `aria-label` específico;
- targets táctiles suficientes;
- foco visible;
- no sticky por defecto;
- título del destino legible;
- no depender solo de iconos.

## 14. No hacer

- `prev/next` por orden alfabético;
- por fecha de publicación;
- por array incidental del builder;
- por `relatedIds` sin contrato de orden;
- JS que calcula vecinos en runtime;
- navegación invisible para crawlers;
- hardcodear enlaces manualmente en cada HTML;
- crear una segunda base de URLs;
- añadir next/prev a cada artículo solo por consistencia visual.

## 15. Medición

Si se implementa en una serie real, las métricas útiles serían:

- click-through a anterior/siguiente;
- abandono entre piezas;
- acceso a la serie desde entradas profundas;
- navegación en móvil.

No vender la función como factor SEO. Su valor principal es continuidad, findability e internal linking semántico.

## 16. Riesgo de canibalización de arquitectura

El repo ya tiene distintas autoridades:

- content registry;
- topic collections;
- navegación contextual de sección;
- grafo interno/checkers.

D.12 debe ampliar una autoridad existente, no crear:

```text
data/series-links.json
```

si esos datos pueden vivir correctamente en registry/colección.

## 17. Revalidación contra `main`

A fecha de esta reconstrucción:

- `content-registry.json` sigue siendo autoridad de contenido/rutas;
- existen relaciones `parentId`, `hubId` y `relatedIds`;
- no se ha localizado un modelo explícito de serie/posición;
- no hay razón para inferirlo automáticamente.

Por tanto no se cambia el estado a `ALREADY_COVERED`, pero tampoco a `IMPLEMENT_NOW`: falta el trigger editorial real.

## 18. Pasadas posteriores de #135

Las pasadas tardías no revirtieron D.12. Las investigaciones sobre registry, discoverability y QA refuerzan el principio de datos canónicos y generación determinista.

La revalidación independiente mantuvo las decisiones D salvo cambios explícitos en otras ideas; D.12 permaneció condicional.

## 19. Estado de verdad

- `DOCUMENTED`: sí.
- `IMPLEMENTED_IN_PR`: no.
- `MERGED_MAIN`: no.
- `CONFIGURED_LIVE`: no aplica todavía.
- `VERIFIED_E2E`: no.

No se considera implementación el hecho de que existan enlaces relacionados o navegación de sección.

## 20. DoD de esta reconstrucción

- [x] alcance original recuperado;
- [x] separación respecto a breadcrumbs/context nav documentada;
- [x] estado `CONDITIONAL` preservado;
- [x] requisito `series/position` recuperado;
- [x] prohibición de inferir por URL/fecha preservada;
- [x] registry actual contrastado;
- [x] límites con A.1/A.6/relatedIds documentados;
- [x] no se modifica runtime ni datos productivos.

## 21. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- cross-checks y pasadas posteriores de arquitectura.

Fuente actual:

- `data/content-registry.json` en `main` `291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## 22. Conclusión

D.12 permanece **`CONDITIONAL`**. “Anterior/siguiente” solo merece existir cuando el contenido forma una secuencia editorial verdadera. Cuando llegue ese caso, la solución correcta es declararlo en la autoridad de contenido y generar navegación determinista, no convertir el orden accidental del Cuaderno en una serie artificial.