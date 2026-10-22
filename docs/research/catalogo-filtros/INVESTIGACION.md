# Investigación aplicada: filtros y presentación del catálogo de libros (22-10-2026)

**Ámbito:** https://davidportodiaz.com/recomendaciones/ · PR de origen [#665](https://github.com/davidpd89/web-escritor/pull/665), ampliación [#687](https://github.com/davidpd89/web-escritor/pull/687) y arranque [#659](https://github.com/davidpd89/web-escritor/pull/659). Las tres están fusionadas; esta investigación se abre sobre `main` y **no modifica producción**. Objetivo: dejar decisiones, código y criterios comprobables para la implementación posterior por Claude.

## Hallazgo 1 (P0): los filtros normales NO son facetas dependientes

**Evidencia comprobada sobre el código actual (22-10-2026):**
- `scripts/build-reading-catalogue.py` → `render_filters()` (aprox. líneas 399-418): los <option> se escriben desde **todas** las `categorias` activas, no desde las obras que cumplen los demás filtros.
- `assets/reading-catalogue.js` → `matches()` y `apply()`: filtra tarjetas correctamente, pero no actualiza las opciones de los demás <select>.
- `data/reading-catalogue.json`: 55 libros, 54 categorías activas repartidas en género (22), temática (20), contenido (1), temporada (3), edad (6), época (2); 185 relaciones libro-categoría. Conteos calculados a partir del JSON leído desde `main`, no estimados.
- `recomendaciones/index.html`: 55 tarjetas; tipos: Cocina 14, Novela 15, Crecimiento personal 7, Infantil y juvenil 8, Biografías y memorias 10, Historia y ensayo 1. Los contadores se imprimen en `group_selector()` y no se actualizan en `apply()`.

**Reproducción lógica determinista:** elige «Cocina». El filtro «Género» sigue ofreciendo «Fantasía» porque su HTML se creó con la taxonomía global. No hay tarjetas de tipo Cocina etiquetadas `fantasia`; esa combinación muestra cero resultados. Análogamente, una búsqueda por «Coraline» no actualiza el contador estático de tipo Cocina (14).

**Decisión recomendada A (P0):** recalcular las opciones de cada faceta usando **todos los filtros salvo la propia faceta** («self-excluding»). Así, cambiar «Género» sigue siendo posible, pero «Temática» muestra solo temas compatibles con los demás filtros. En los <select> nativos, ofrecer las opciones con resultados y conservar cualquier opción ya seleccionada aunque su cuenta caiga a cero, con una explicación. Mostrar la cifra «Fantasía (5)» calculada y no una cifra global obsoleta.

**Alternativa B:** siempre mostrar las 54 categorías, desactivar las que no dan resultados y etiquetar sus cuentas (0). Más estable visualmente, pero obliga a recorrer opciones inútiles en móvil. Reservar para ensayo de usabilidad si A provoca desorientación; no implantar dos patrones a la vez.

**Código prototipo propio y unit tests (sin tocar producción):**
- [`facets-prototype.mjs`](./facets-prototype.mjs): `calculateFacetOptions({records,selected,facet,choices,match})`, `activeFilters()`, `updateSelect()`.
- [`facets-prototype.test.mjs`](./facets-prototype.test.mjs): siete contratos sobre tipos, facetas cruzadas, selecciones imposibles, búsqueda y eliminación individual. La muestra de prueba es sintética y pequeña; los **conteos anteriores** proceden del catálogo real. **Estos tests quedan escritos, no se afirma que hayan pasado Actions ni navegador.**

El algoritmo reutiliza `matches(card,v)` existente como predicado para no tener dos motores de filtrado. Complejidad esperada `O(libros × opciones × coste de match)`; medir con el fixture existente de 100/200 libros antes de fusionar. No incorporar Algolia ni Meilisearch: añadir infraestructura y peticiones para un catálogo estático de 55 libros carece de justificación demostrada.

### Referencia abierta 1 — Algolia InstantSearch (MIT, código real)

**Version fijada:** commit [152d320](https://github.com/algolia/instantsearch/tree/152d320926a73f527e4fa1b8568534a22a5102a0), 20-10-2026. **Archivo:** [`connectRefinementList.ts`](https://github.com/algolia/instantsearch/blob/152d320926a73f527e4fa1b8568534a22a5102a0/packages/instantsearch.js/src/connectors/refinement-list/connectRefinementList.ts), que admite `and | or`, `count`, `isRefined`, `limit` y `showMoreLimit`. Se verificó el propio código, no solo un artículo.

Extracto literal verificable (licencia MIT, © Algolia; condiciones reproducidas en [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)):

```ts
const DEFAULT_SORT = ['isRefined', 'count:desc', 'name:asc'];
```

```ts
function getLimit() {
  return isShowingMore ? showMoreLimit : limit;
}
```

**Qué copiar conceptualmente:** destacar selección, ordenar por número de resultados, ocultar opciones vacías, «Mostrar más» únicamente cuando haya opciones de sobra. **Qué no copiar:** conector Preact, API de búsqueda o cálculo remoto; el sitio usa HTML estático y JavaScript nativo.

### Referencia abierta 2 — Meilisearch instant-meilisearch (MIT, código real)

**Versión fijada:** commit [702301b](https://github.com/meilisearch/meilisearch-js-plugins/tree/702301b09e486b929af6bf13ce0ad9f768f8bda7), 16-09-2026. Archivo [`facet-distribution-adapter.ts`](https://github.com/meilisearch/meilisearch-js-plugins/blob/702301b09e486b929af6bf13ce0ad9f768f8bda7/packages/instant-meilisearch/src/adapter/search-response-adapter/facet-distribution-adapter.ts): mantiene en la distribución valores que ahora tienen 0 coincidencias.

Extracto literal verificable (MIT, © Meili SAS; condiciones en [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)):

```ts
if (!filledDistribution[facet][facetValue]) {
  filledDistribution[facet][facetValue] = 0
} else {
  filledDistribution[facet][facetValue] =
    facetDistribution[facet][facetValue]
}
```

El [changelog](https://github.com/meilisearch/meilisearch-js-plugins/blob/702301b09e486b929af6bf13ce0ad9f768f8bda7/packages/instant-meilisearch/CHANGELOG.md) describe las distribuciones de facetas excluyendo la propia selección y actualizando las demás: el mismo comportamiento que se propone probar. **Adaptación deliberada:** conservar solo la opción actual cuando vale 0, en lugar de hacer visibles todas las opciones 0. Es una decisión de UX para nuestro catálogo, **no** una copia literal del comportamiento completo de Meilisearch.

## Hallazgo 2 (P1): los chips de filtros activos faltan

La interfaz muestra el resultado y un botón «Restablecer», pero el visitante debe localizar cada valor elegido, incluso dentro de `<details>`. La ruta con hash guarda el estado (`#genero=...&grupo=...&pagina=...`), lo cual **ya funciona** y debe preservarse.

**Propuesta A:** franja compacta debajo del formulario y encima de «El catálogo», con «Filtros: [Cocina ×] [Halloween ×]» y «Quitar todos». Cada chip ejecuta `field.value=''`, dispara el mismo evento de filtro y fija página 1; **no** elimina búsqueda, ordenación ni otras facetas salvo que el visitante pulse expresamente el chip correspondiente. Mantener `aria-label="Quitar filtro Cocina"`. Mostrar el número de filtros dentro del texto del `<summary>` de los avanzados cuando estén cerrados. No crear chip por ordenación.

**Alternativa B:** texto «Cocina · Halloween» sin controles directos; menos elementos pero peor capacidad de deshacer. Elegir A y probar con teclado y lector de pantalla.

**Referencia abierta — Algolia, código literal:** [`CurrentRefinements.tsx`](https://github.com/algolia/instantsearch/blob/152d320926a73f527e4fa1b8568534a22a5102a0/packages/instantsearch.js/src/components/CurrentRefinements/CurrentRefinements.tsx) genera claves estables para las selecciones, presenta etiquetas y un botón de eliminación por selección.

```ts
const createItemKey = ({
  attribute,
  value,
  type,
  operator,
}: CurrentRefinementsConnectorParamsRefinement): string =>
  [attribute, type, value, operator]
    .map((key) => key)
    .filter(Boolean)
    .join(':');
```

**Integración:** no importar Preact. Usar `activeFilters()` del prototipo para crear botones HTML nativos, enlazados a `fields` del script actual; usar `document.createElement` y `textContent`, no HTML interpolado. Mantener un único contador `aria-live="polite"`.

## Hallazgo 3 (P1): el agrupador cuenta libros de forma exclusiva

`book_group(cats)` en `scripts/build-reading-catalogue.py` asigna a cada libro **un solo** grupo siguiendo prioridades. «Coraline» contiene `fantasia-juvenil` pero queda en «Infantil y juvenil». Por tanto, `grupo` NO representa todas las categorías posibles. Cambiarlo a multigrupo sin decisión editorial alteraría conteos y expectativas.

**Decisión A:** conservar los seis grupos como accesos principales exclusivos, explicar visualmente «Tipo de libro» (no sinónimo de género) y usar Género/Temática como facetas múltiples. Recalcular los contadores del agrupador con los demás filtros, sin cambiar el contrato de agrupación.

**Decisión B:** permitir multigrupo y libros repetidos entre «Novela» e «Infantil». No hacerlo por ahora: necesita reglas editoriales, replantear totales y probar ambigüedades. Documentar como futura discusión, no como bug que se deba «arreglar» a ciegas.

## Hallazgo 4 (P1): el test de lectura YA ofrece opciones adaptadas

`setupQuiz()` ya calcula `usable(step)` con `matches(card, criteria)`, omite pasos sin coincidencias, permite volver y traslada los criterios al formulario. **NO reescribir el test**.

**Riesgo de integración concreto:** hoy `optionsFrom()` del cuestionario extrae valores de `fields.find(...).options`. Si el parche de facetas restringe físicamente las opciones de los <select>, el cuestionario heredará opciones recortadas por unos filtros **que no forman parte de su propio estado**.

**Contrato para Claude:** capturar una lista inmutable `originalOptionsByFacet` al iniciar; tanto facetas como `optionsFrom()` deben leer esa lista maestra, pero el test aplica únicamente `criteria`. Nunca leer de los <select> ya reducidos como fuente universal. Probar «filtrar Cocina → abrir test → empezar nuevo», «volver» y «ver resultados».

## Plan de implementación mínimo y preciso (para Claude)

1. En `assets/reading-catalogue.js`: capturar todas las opciones originales por `data-filter` antes de actualizar <select>. Reutilizar `matches()`; probar primero sobre `genero` y `tematica`, después `temporada`, `edad`, `contenido`, `epoca`, `formato`, `paginas`, `novedad` según datos reales. **No** convertir `orden`, fechas ni controles de precio en facetas categóricas.
2. Recalcular `calculateFacetOptions` tras cualquier cambio de filtro; excluir la propia faceta al calcular sus opciones; no borrar selección incompatible ni modificar <select> activo si opciones no cambian (firma/cache `updateSelect`); reset y hash deben conservar el contrato actual.
3. Para `data-type-radio`: conservar botones de tipo existentes, pero mostrar conteos recalculados sobre los demás filtros y desactivar o etiquetar cuando un tipo no tiene opciones; conservar selección actual. Evitar reconstruir el `<fieldset>` completo: se perderían los listeners y el foco.
4. Añadir chips de selecciones activas con eliminación individual y resumen de filtros avanzados, sin duplicar anuncios de `aria-live`. Resultado vacío: «No hay coincidencias» + chips removibles y restablecimiento real (no enlaces a categorías incompatibles).
5. Adaptar `setupQuiz()` a `originalOptionsByFacet`, sin confundir su estado con el del formulario. No añadir dependencias, cuentas externas, rastreadores o llamadas a modelos.
6. Mantener la construcción sin JS: las 55 fichas siguen accesibles y los formularios quedan deshabilitados. No tocar datos SEO, URLs canónicas, feeds, enlaces de afiliación o indexación en esta PR de investigación.

**Puntos de inserción:** `render_filters()` y `group_selector()` en `scripts/build-reading-catalogue.py`; `values()`, `matches()`, `apply()`, `setupQuiz()`, `restore()` en `assets/reading-catalogue.js`; CSS únicamente en `assets/reading-catalogue.css`. Esto evita una reescritura general.

## Aceptación: pruebas que DEBEN ejecutarse en la PR de implementación

| Caso | Contrato esperado |
| --- | --- |
| Tipo Cocina → Género | Solo géneros posibles de esos 14 libros; ningún valor falso |
| Género cambia dos veces | Se puede cambiar sin quitar filtros ajenos |
| URL compartida con selección ahora imposible | La selección permanece visible con 0 y se puede eliminar |
| Buscar «Coraline» | Recuentos por grupo cambian y solo ella aparece |
| Quitar chip «Cocina» | Resto de filtros y ordenación intactos; página vuelve a 1 |
| Restablecer + atrás/adelante del navegador | Estados y hash coherentes, sin controles fantasma |
| Filtros avanzados en móvil 320/390 px | Ni desbordamiento ni chips ilegibles |
| Zoom 200 %, teclado y lector de pantalla | Focus visible, nombres comprensibles y anuncio de resultados |
| Test de lectura tras filtrar + volver | Opciones del test no contaminadas por el formulario |
| Sin JS / sin valoraciones / ofertas caducadas | No se pierde ningún libro ni se inventan precios/estrellas |
| Fixture de 100 y 200 libros | Rendimiento comparado con el test actual `<500 ms`; medir antes/después |

Referencias para modificar los **tests de navegador ya existentes**, no duplicarlos: `qa/reading-catalogue-v2-browser.mjs`, `qa/reading-catalogue-browser.mjs`, `tests/test-reading-catalogue.py`. **No se han ejecutado GitHub Actions ni se afirma que el prototipo esté integrado en la web.** Éxito exigible: pasar los tests nuevos y existentes en la posterior PR de implementación; revisión manual de capturas y de teclado antes de merge.

## Orden de decisión

**Primera iteración:** P0 facetas dependientes + conservación de URL + garantía del test. **Segunda:** chips y contadores dinámicos. **Tercera, solo con evidencia de uso:** selector múltiple, filtros por editorial/autor, búsqueda dentro de facetas, variaciones de tarjetas. Evitar sumar filtros que no mejoren la exploración real.

**Fuentes adicionales:** [GOV.UK Design System: preguntas simples y resultados](https://design-system.service.gov.uk/patterns/check-a-service-is-suitable/), útil para evaluar el test (no para copiar código); [Algolia InstantSearch MIT](https://github.com/algolia/instantsearch/blob/152d320926a73f527e4fa1b8568534a22a5102a0/LICENSE); [Meilisearch MIT](https://github.com/meilisearch/meilisearch-js-plugins/blob/702301b09e486b929af6bf13ce0ad9f768f8bda7/LICENSE). Las dos últimas referencias fueron comprobadas directamente en sus repositorios el 22-10-2026.

**Estado:** diagnóstico sobre el código `main` y los datos **verificado**; fragmentos de código abierto y licencia **verificados**; prototipo de referencia y tests **escritos, no ejecutados en CI**; solución en la web **pendiente de implementación y validación por Claude**.
