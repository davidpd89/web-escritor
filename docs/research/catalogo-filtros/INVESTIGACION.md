# PR #715 · Decisión técnica: filtros acumulativos y UX del catálogo

**Revisado el 22 de octubre de 2026.** Catálogo en `main`: 55 libros, 54 categorías activas (22 de género, 20 de temática, 12 de otros tipos) y 185 relaciones libro-categoría. Relacionada con las PR fusionadas [#665](https://github.com/davidpd89/web-escritor/pull/665), [#687](https://github.com/davidpd89/web-escritor/pull/687) y [#659](https://github.com/davidpd89/web-escritor/pull/659).

**Autocrítica y corrección:** la primera versión de esta PR proponía un algoritmo propio de **un solo valor**, citaba líneas sueltas de Algolia/Meilisearch y no tenía tests locales ejecutados. Era insuficiente para una implementación directa. **Se han retirado esos prototipos y referencias secundarias** en favor de UNA solución visual lista para usar, su código exacto y un adaptador de integración comprobado en Node. Este documento reemplaza las recomendaciones anteriores.

## Evidencia del problema, no intuiciones

1. `scripts/build-reading-catalogue.py::render_filters` genera un `<select>` **de un solo valor por dimensión** con todas las opciones globales. `assets/reading-catalogue.js::values/matches/apply` usa `f.value` y comprueba un único valor por dimensión. No es posible elegir Tapa blanda **o** Tapa dura ni Fantasía **o** Terror sin repetir búsquedas.
2. `apply()` filtra tarjetas pero NO recalcula las opciones de las otras facetas. Elegir tipo Cocina (14 obras) sigue dejando seleccionar género Fantasía, pese a haber **cero** libros que coincidan. Los recuentos del selector de tipos proceden de `group_selector` y son estáticos.
3. `setupQuiz::optionsFrom()` lee las opciones actuales de los selects. Si una implementación nueva las elimina dinámicamente, puede contaminar el test de lectura con los filtros previos. Hay que conservar una taxonomía maestra inmutable, separada del estado del test.
4. `book_group()` es exclusivo; «Coraline» está en Infantil aunque también tenga la categoría Fantasía. No confundir «Tipo de libro» con «Género» ni duplicar un libro al cambiar los contadores.
5. `data-formats` contiene formatos conocidos. Las ofertas temporales de `reading-market.json` se validan y expiran; **filtrar formato no significa necesariamente que exista un precio vigente**. No combinar por error el precio de ebook con la selección Tapa dura.

Comprobación sobre el HTML publicado en el repositorio: 55 tarjetas, 14 Cocina, cero Cocina+Fantasía. Estos números NO son un test de usuario.

## Qué comportamiento adoptar

**OR dentro del mismo filtro; AND entre filtros diferentes.** Es el patrón avalado por el estudio de uso de Baymard de [23-01-2024](https://baymard.com/research-articles/allow-applying-of-multiple-filter-values) y su [guía de filtrado de 2026](https://baymard.com/blog/ecommerce-filter-ui). No extrapolar estadísticas de comercio electrónico a una supuesta tasa de conversión de esta web; se adopta **el comportamiento**, no un porcentaje de mejora inventado.

| Selección | Resultado esperado |
| --- | --- |
| Formatos: Tapa blanda + Tapa dura | Libro que tenga **cualquiera** de los dos; sin duplicar fichas |
| Géneros: Fantasía + Terror | Libro que tenga **cualquiera** de los dos |
| Ambos grupos anteriores | (Tapa blanda OR Tapa dura) **AND** (Fantasía OR Terror) |
| Tipo: Cocina + Género: Fantasía | Ninguna tarjeta; mantener chip activo para poder quitarlo |
| Otro filtro seleccionado | Las opciones incompatibles dejan de ofrecerse, salvo las ya seleccionadas, que quedan visibles con cuenta cero |
| Eliminar un valor | No elimina los demás valores del mismo filtro, ni los otros grupos |

Mantener ordenación, paginación a 24 fichas, búsqueda, navegación, URL compartible, test de lectura, HTML sin JS, enlaces comerciales y precios fiables.

### Solución visual elegida: Choices.js v11.2.4, código completo VERIFICADO

**Producto real:** [Choices.js](https://github.com/Choices-js/Choices), una biblioteca de selección múltiple sin jQuery, buscador de opciones y eliminación individual, con suite de tests y [ejemplos interactivos](https://choices-js.github.io/Choices/). **Publicación v11.2.4:** [release del 23-08-2026](https://github.com/Choices-js/Choices/releases/tag/v11.2.4), con [publicación npm concluida](https://github.com/Choices-js/Choices/actions/runs/32672415206). La ejecución de ese workflow NO equivale a probar nuestras adaptaciones.

Se han copiado **literalmente los tres archivos del release**, sin fragmentos parciales, en `upstream/`:

- [`choices-v11.2.4.min.js`](./upstream/choices-v11.2.4.min.js) — bundle de producción de 77.325 caracteres; **SHA de blob Git idéntico al original**: `0c37de23e3c35d4a89fd62b56587beff6d9f9b4d`.
- [`choices-v11.2.4.min.css`](./upstream/choices-v11.2.4.min.css) — CSS original de 10.809 caracteres; **SHA idéntico**: `474ed5f27c2d059d18c601eebb017b22cfa566cc`.
- [`CHOICES-LICENSE.txt`](./upstream/CHOICES-LICENSE.txt) — licencia MIT original completa, **SHA idéntico**: `432f18873762b3f277abea8da35cd97982cedc6a`.

Código de activación **según la API documentada del proyecto**; el control visual y el teclado los gestiona el upstream, no una imitación propia:

```html
<link rel="stylesheet" href="/assets/vendor/choices.min.css">
<select id="filtro-formato" name="formato" multiple>
  <option value="tapa-blanda">Tapa blanda</option>
  <option value="tapa-dura">Tapa dura</option>
  <option value="ebook">Libro electrónico</option>
</select>
<script src="/assets/vendor/choices.min.js" defer></script>
```

```js
const formatos = new Choices(document.querySelector('#filtro-formato'), {
  removeItemButton: true,
  searchEnabled: true,
  shouldSort: false,
  allowHTML: false,
  itemSelectText: '',
});
```

**Importante:** en esta PR los archivos están en `docs/research/...`, no en `assets/vendor/`. Los ejemplos de rutas de producción son objetivos para Claude, **no son rutas ya desplegadas**. No cargar Choices en toda la web: solo en `/recomendaciones/`, y comprobar CSS/teclado antes de hacerlo. No presupone que sus estilos encajen sin ajustes con el diseño actual.

### Qué adaptar localmente (mínimo imprescindible)

En [`multifacet-contract.mjs`](./multifacet-contract.mjs) están los únicos cálculos específicos del catálogo: arrays de selecciones, OR por dimensión, AND entre dimensiones, facetas que excluyen su propia selección para calcular las opciones y URL que conserva los hashes antiguos. Es **código de adaptación nuestro**, no código original de Choices.

En [`demo-multifiltro.html`](./demo-multifiltro.html) hay un **laboratorio sin despliegue** que carga el bundle real de Choices, lee las 55 tarjetas de `/recomendaciones/index.html` y sus categorías de `data/reading-catalogue.json` y muestra resultados filtrados. No usa ejemplos inventados para su base de datos. Se puede abrir con un servidor estático desde la raíz del repo, por ejemplo `python -m http.server 8000` y `http://localhost:8000/docs/research/catalogo-filtros/demo-multifiltro.html`. **El laboratorio todavía requiere comprobación visual/teclado con navegador; no se etiqueta como validado.** Incluye paginación real (24 por página) y restauración en `hashchange`. Archivo de prueba navegador preparado: [`qa-demo.mjs`](./qa-demo.mjs); ejecutar con `node docs/research/catalogo-filtros/qa-demo.mjs` mientras se sirve la raíz del repo en el puerto 4173. La prueba está escrita, **no ejecutada**.

[Tests del contrato](./multifacet-contract.test.mjs): **12/12 PASADOS con Node 22, localmente, el 22-10-2026**, sin GitHub Actions. Los casos incluyen dos formatos, dos géneros, cruces OR/AND, facetas dependientes, preservar una selección imposible, hashes antiguos, nuevo formato multi y deduplicación de URL. Cuatro títulos y sus formatos/categorías usados por los tests proceden del HTML real; el ejemplo pequeño de pruebas NO equivale a 55 casos completos ni prueba la librería visual.

## Corrección incremental posterior: tres regresiones evitadas

Al inspeccionar la integración original de este laboratorio se encontraron **defectos concretos**, distintos del diseño de filtros:

1. `hashchange` estaba vacío: al pegar un hash o navegar por historial las selecciones visibles podían divergir de la URL. Ahora se reconstruyen las opciones desde `master` y se restauran los valores con la API oficial `setChoiceByValue()`.
2. El hash admitía `pagina=2`, pero el laboratorio siempre mostraba las primeras 24 tarjetas. Ahora calcula `totalPages`, limita `pagina` al rango y dibuja botones Anterior/Siguiente solo cuando corresponde.
3. `writeHash(parseHash(url))` **borraba condiciones que ya existían** en la página actual (`paginas`, `novedad`, `precio_min`, `precio_max`, `desde`, `hasta`, `descuento`, `valoracion`). Reproducción anterior: `#genero=fantasia&paginas=breve&novedad=30&precio_max=20` terminaba reducido a `#genero=fantasia`. Se ha añadido `SCALAR` para preservar esos ocho parámetros con la misma URL, **sin introducir su filtrado en la demo**. Las dos últimas pruebas Node verifican el contrato.

El laboratorio también limita la reconstrucción de Choice.js a cuando cambian de verdad los valores o conteos de una faceta, y repuebla las selecciones desde el estado canónico; la validación de **foco/duplicados del control real** está todavía pendiente de `qa-demo.mjs`. Verificación de código upstream: [`choices.ts` del release v11.2.4](https://github.com/Choices-js/Choices/blob/v11.2.4/src/scripts/choices.ts), métodos `setChoices()`, `clearChoices()` y `setChoiceByValue()`.

**Advertencia útil:** la demo solo enseña multiselección de formatos, géneros y temática. Preservar parámetros antiguos en la URL NO implica que esta demo esté aplicando ya los filtros de precio, fecha o valoraciones; se aplican en la web pública actual y deben seguir aplicándose en la implementación final. No fusionar el adaptador directamente sobre `matches()` sin mantener su lógica financiera.

## Comprobación de calidad incremental: datos reales y catálogo automático

En una revisión posterior de la PR se volvió a procesar el HTML **real** de `recomendaciones/index.html` (55 tarjetas, 22-10-2026) para validar el significado exacto de la multiselección:

| Selección | Obras únicas encontradas |
| --- | ---: |
| Tapa blanda | 32 |
| Tapa dura | 24 |
| Tapa blanda OR tapa dura | 55 |
| Fantasía | 7 |
| Terror | 3 |
| Fantasía OR Terror | 8 |
| (Fantasía OR Terror) AND (Blanda OR Dura) | 8 |
| Tipo Cocina AND Fantasía | 0 |
| Tipo Cocina AND (Fantasía OR Cocina) | 10 |
| Audiolibro | 1 |

Las cifras son un **snapshot del catálogo del 22-10-2026**, no límites fijos para las pruebas. Por ejemplo, 32 + 24 = 56, pero la unión tiene 55 obras, porque un título admite ambos formatos; no duplicar tarjetas. Fantasía 7 + Terror 3 = 10, pero la unión tiene 8 por coincidencias entre etiquetas.

**Regresión detectada al revisar el laboratorio:** «Quitar todos los filtros» solo vaciaba `formato/genero/tematica` y dejaba escondidos en el hash parámetros como `paginas`, `precio_max` o `novedad`; se corrigió restableciendo `parseHash('')` completo. Se amplió `qa-demo.mjs` para exigir hash vacío tras restablecer.

**Otra regresión evitada:** el primer `qa-demo.mjs` suponía exactamente 55 libros y 24 en la segunda página. Como la incorporación de libros está automatizada, se corrigió: ahora lee el total que realmente devuelve el laboratorio y calcula la segunda página con `Math.min(24,total-24)`. Se preserva el requisito de paginación con más de 24 fichas; no se codifica una cifra editorial transitoria.

**Estado de estas nuevas comprobaciones:** inspección y cálculo contra HTML de `main` **realizados**, código actualizado en GitHub y pruebas browser **preparadas pero pendientes de ejecución**. No se afirma validación visual ni de Choices.js dentro de Chromium hasta ejecutar `qa-demo.mjs` en una copia completa de la rama.

**Evitar destruir el foco al seleccionar múltiples valores:** el laboratorio utilizaba una firma de caché que incluía `selected`, por lo que reconstruía el mismo desplegable en cada clic aunque sus opciones y recuentos no cambiasen. Como el recuento de una faceta excluye su propia selección, ahora la firma depende de `[value,count]`; al seleccionar otra opción en ese mismo control, Choices.js mantiene internamente el estado, sin `setChoices()` redundante. Es una corrección de flujo de renderizado verificada por inspección de código, **no una prueba de foco en el navegador**. La prueba de teclado/foco continúa abierta.

**Evidencia reproducible del contrato exacto:** se cotejaron localmente los SHA de blob Git de `multifacet-contract.mjs` (`75256ba50ee06f67d077125bc7884e8511b1301c`) y `multifacet-contract.test.mjs` (`0463b440b1db4ce12003148330b49316430fdf4a`) con los de la rama de la PR. Ejecutados esos mismos archivos con `node --test`: **12/12 aprobados, 0 fallos**. No se extrapola ese éxito al HTML/browser.

**Alcance del laboratorio: evitar filtros invisibles.** Se verificó por lectura de código que, al restaurar hashes antiguos, podían activarse `q`, `grupo`, `temporada`, `edad`, `contenido` y `epoca` sin que el laboratorio mostrase controles para retirarlos. El laboratorio ahora calcula resultados y opciones sobre `labState()`, que aplica **solo formato, género y temática**. Conserva otros parámetros en la URL para ensayar la compatibilidad, pero avisa expresamente que no se aplican en la demo. `qa-demo.mjs` incluye un caso de URL antigua con tres filtros sin control visible; ejecución pendiente de Playwright. **No replicar este recorte en producción:** la página real sí tiene esos filtros y debe seguir aplicándolos.

## Validación incremental adicional (22-10-2026)

**Nuevo caso con prueba:** una URL antigua puede contener `genero=no-existe`. El anterior `matchesMulti()` no mostraba libros, aunque el selector no presentara ninguna opción que desmarcar. `sanitizeFacetSelections(state,master)` elimina únicamente valores ausentes de la **taxonomía maestra**, antes de cargar/restaurar el hash; **no** elimina selecciones existentes con cuenta 0. Se han añadido 3 tests para este contrato.

**Ejecución independiente:** se cargaron desde esta misma rama los archivos JS del adaptador y su suite y se ejecutaron en un intérprete V8, con implementación mínima de `URLSearchParams` para las pruebas. **15/15 pasaron**. Esta ejecución no sustituye el `node --test` nativo; solo los **12 tests anteriores** fueron ejecutados previamente como suite Node en local. Además, 9 combinaciones se calcularon ejecutando el adaptador exacto sobre las **55 tarjetas reales**: 9/9 iguales a los conteos esperados.

**Corregido el test Playwright, no la web:** cuatro comprobaciones hacían `new URLSearchParams(location.hash)`. Node confirma que `#formato` no equivale a `formato`; se cambió por `location.hash.slice(1)`. El QA ahora usa `data-value` del código oficial Choices.js y cubre dos formatos, dos géneros y dos temáticas elegidos simultáneamente, además de enlaces obsoletos. Todos los módulos JS superan **comprobación sintáctica V8**, pero **no** se ha ejecutado aún Chromium con la rama completa. No marcar verde el navegador.

## Incidencia verificada: una categoría activa puede tener cero libros

La taxonomía de `data/reading-catalogue.json` contiene **54 categorías activas**. En el catálogo actual, **49 aparecen en las tarjetas** y cinco aún no tienen ninguna obra: `romantasy` (género), `portales` (temática), `magia-con-coste` (contenido), `navidad` y `verano` (temporada). **No son etiquetas obsoletas**.

El primer laboratorio construía `master` filtrando `used.has(c.id)`, lo que confundía categoría activa sin libros con categoría eliminada. Al restaurar `#genero=romantasy`, `sanitizeFacetSelections()` borraba una selección legítima en vez de mantenerla visible a cero. **Corrección aplicada:** `master` toma **todas las categorías activas** de `genero` y `tematica`. `availableOptions()` oculta categorías sin libros cuando no están seleccionadas, pero conserva las seleccionadas con cuenta cero. Los slugs realmente inexistentes sí se depuran.

**Comprobaciones:** prueba adicional de contrato de sanitización (ahora **16/16 casos superados en V8** con `URLSearchParams` mínimo compatible, **no** ejecutados aún como 16 pruebas nativas de Node); prueba de navegador escrita para restaurar `romantasy` y `portales` al cambiar el hash, aún sin ejecutar Playwright. En la primera ejecución de la prueba V8 se detectó un **error en la expectativa del fixture** (3 libros de Fantasía, no 2); corregido ese valor, la suite pasó 16/16. No se alteró el algoritmo para forzar el resultado.

## Contrato económico: formato y precio de LA MISMA oferta

**Defecto potencial concreto en la integración:** el `matchingOffers()` vigente en [`assets/reading-catalogue.js`](../../../assets/reading-catalogue.js) filtra por un solo `v.formato`. Al introducir `['tapa-blanda','tapa-dura']`, no basta con comprobar por separado que «existe tapa dura» y «el libro tiene una oferta de 10 €»: esa oferta podría ser la blanda y la dura costar 25 €. No deben cruzarse dos ofertas distintas.

**Solución implementada en esta PR, solo como contrato de investigación:** `matchingOffersMulti(offers, state)` en [`multifacet-contract.mjs`](./multifacet-contract.mjs). En una sola pasada filtra OR de formatos, precio mínimo, precio máximo y descuento mínimo, **todo sobre cada oferta individual**. Ejemplo: tapa blanda a 9,50 € y tapa dura a 25,90 €; la selección «solo tapa dura + máximo 10 €» devuelve **cero** ofertas; «blanda O dura + máximo 10 €» devuelve **solo la blanda**. Para ordenar por precio, usar el mínimo de las ofertas que pasaron **todos** los filtros.

El helper **presupone ofertas ya validadas** por `validOffer()`/`fresh()` de la implementación existente y no altera autenticidad ni vigencia de los precios. No se deben inventar ofertas de mercado: `assets/reading-market.json` tiene actualmente **cero ofertas**. Cuando el usuario aplica un filtro de precio, no deben contarse libros sin oferta vigente que satisfaga todas sus condiciones. Cuando no hay filtro de precio, las opciones editoriales siguen disponibles. Integración mínima propuesta:

```js
// Dentro de assets/reading-catalogue.js; adaptar la nueva multiselección sin
// sustituir validOffer(), fresh(), renders ni el resto de matches().
const matchingOffers = (card, v) =>
  matchingOffersMulti(offersFor(card.dataset.bookId), v);
```

Añadidos **cinco tests semánticos**: oferta equivocada (regresión), OR correcto, combinación precio/descuento, compatibilidad formato escalar, y mínimo de precios por formato. Resultado de ejecución en intérprete V8 sobre el código GitHub exacto: **21/21 tests correctos** (incluidos los 16 anteriores). Esta verificación V8 usa `URLSearchParams` mínimo compatible; **no** es una ejecución nativa Node de los 21 ni una prueba de navegador. El laboratorio visual permanece deliberadamente sin filtro de precio: no presentar precios ficticios donde el mercado no aporta ofertas.

## Estado vacío: UX comprobable, no panel decorativo

Una selección válida como `#genero=romantasy` produce cero obras. Antes quedaba un listado en blanco; ahora aparece `#empty`: «No hay libros con esta combinación. Puedes quitar algún filtro o pulsar Quitar todos los filtros». Se oculta automáticamente al quitar esa selección. Prueba Playwright escrita para el mensaje y su desaparición tras restablecer; **aún no ejecutada**.

## Bloqueo de prueba de navegador (estado verificable)

Se comprobó el entorno local: `/usr/bin/chromium` y Playwright Python están disponibles, pero el contenedor no resuelve `github.com`/`raw.githubusercontent.com` (error DNS) y no tiene montada la rama completa ni el JS upstream. Por eso **no se ha ejecutado con la biblioteca real** `qa-demo.mjs`. No reemplazar Choices.js por un simulador y etiquetarlo como prueba exitosa. Los casos de teclado, foco, CSS y móvil siguen pendientes.

## Riesgo real y condiciones para Claude

La PR de implementación NO debe reemplazar `reading-catalogue.js` a ciegas: ya resuelve 24 fichas/página, sort, filtros financieros con caducidad, rating y test. Iniciar con **género y formato multiselección**, luego temática. El resto de facetas solo después de verificar que sus opciones producen resultados reales. Mantener el selector «Tipo de libro» exclusivo y su orden editorial salvo decisión posterior.

**Integración detallada obligatoria:**
1. Construir `<select multiple>` para `genero`, `formato` y `tematica` desde `render_filters()`. Instanciar Choices.js una sola vez por control tras habilitar el formulario; preferir CSS de la web sin modificar el upstream, con overrides de estilo mínimos.
2. Sustituir para esas dimensiones `values()[key]=f.value` por arrays de `selectedOptions`. Cambiar `matches()` para usar OR interno; **no** cambiar la lógica de búsqueda, fecha, ofertas verificadas, rating ni la regla de un grupo por libro. Detectar todos los formatos conocidos, incluidos los del mercado cuando no están caducados.
3. Calcular opciones de cada faceta con todos los filtros menos su propia faceta. Refrescar el control mediante `Choices.setChoices(choices, 'value', 'label', true, false, false)`: el último `false` impide borrar items seleccionados, **según documentación de la API**, pero hay que probarlo sobre nuestros datos y teclado. Guardar **opciones originales** independientemente de las visibles; el quiz debe leer esas opciones maestras.
4. URL: `URLSearchParams.append('genero', 'fantasia')` y `append('genero', 'terror')`, leer con `getAll()`. Aceptar hashes antiguos de un único valor; al deseleccionar un chip conservar los demás. Mantener `pagina` y hash al navegar. No imprimir valores HTML sin escapar.
5. Los chips individuales del control los proporciona Choices. Evitar duplicarlos salvo que la prueba de usuarios muestre dificultad para ver filtros activos fuera del control; ofrecer resumen compacto «2 formatos, 3 géneros» junto al contador.
6. En móvil probar formulario con desplegables, cierre, foco, scroll, teclado y tamaño táctil a 320/390 px. No diseñar un panel lateral adicional por estética sin probar primero el control; Baymard recomienda reducir fricción en móvil, no acumular controles.

### Puertas de validación antes de marcar la implementación como preparada

- [x] Copia **completa y exacta** de la biblioteca con permiso MIT, fijada a una versión publicada.
- [x] Contrato específico OR/AND y compatibilidad URL: **12 tests locales Node pasados**.
- [ ] Ejecutar demo de 55 libros en navegador real; seleccionar/desmarcar varias opciones repetidamente, abrir/cerrar el dropdown y comprobar que `setChoices` no pierde selecciones ni foco.
- [ ] Capturas + Playwright 320/390/768/1440, zoom 200 %, teclado y lector de pantalla (el lector de pantalla requiere comprobación accesible, no solo ausencia de errores JS).
- [ ] Comparar 100/200 libros con `qa/reading-catalogue-v2-browser.mjs`; sin degradar el umbral actual, sin borrar ni reescribir los tests existentes.
- [ ] Probar quiz tras filtros acumulativos, restauración tras hashchange y páginas previas/siguientes, datos del mercado no disponibles, y sin JavaScript.
- [ ] Comprobar que libro con eBook barato y tapa dura cara NO supera por error un filtro de precio barato aplicado al formato tapa dura.
- [ ] Revisión visual de marca y escaneabilidad: etiquetas legibles, estados activos, selección acumulada y «Limpiar».

## Descartes sustentados (NO copiar)

**Shopify Dawn:** su [código de filtros](https://github.com/Shopify/dawn/blob/main/assets/facets.js) está publicado y funciona en Shopify, pero su [LICENSE.md](https://github.com/Shopify/dawn/blob/main/LICENSE.md) **restringe la reutilización a temas que integran/interoperan con Shopify**. Este sitio no usa ese motor; **no copiar ni trasplantar**.

**Algolia InstantSearch / Meilisearch:** tienen componentes y facetas reales, pero copiar el conector de API/React o su motor de búsqueda implica infraestructura ajena al catálogo estático. Por eso **se retiraron sus extractos sueltos** de esta PR.

**Sistema de filtrado totalmente nuevo:** innecesario para 55 libros. Choices aporta el selector probado, nuestro adaptador únicamente traduce selecciones al `matches()` existente. Si las pruebas visuales de Choices fallan, no se despliega por prestigio: se documenta el fallo y se reevalúa otra biblioteca.

**Estado preciso:** investigación y artefactos completos para la primera prueba; la decisión de UX está justificada; **biblioteca original verificada y publicada, adaptador probado en Node, navegador de integración pendiente**. Nada fusionado ni desplegado.
