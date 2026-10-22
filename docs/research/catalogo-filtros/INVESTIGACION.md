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

En [`demo-multifiltro.html`](./demo-multifiltro.html) hay un **laboratorio sin despliegue** que carga el bundle real de Choices, lee las 55 tarjetas de `/recomendaciones/index.html` y sus categorías de `data/reading-catalogue.json` y muestra resultados filtrados. No usa ejemplos inventados para su base de datos. Se puede abrir con un servidor estático desde la raíz del repo, por ejemplo `python -m http.server 8000` y `http://localhost:8000/docs/research/catalogo-filtros/demo-multifiltro.html`. **El laboratorio todavía requiere comprobación visual/teclado con navegador; no se etiqueta como validado.**

[Tests del contrato](./multifacet-contract.test.mjs): **10/10 PASADOS con Node 22, localmente, el 22-10-2026**, sin GitHub Actions. Los casos incluyen dos formatos, dos géneros, cruces OR/AND, facetas dependientes, preservar una selección imposible, hashes antiguos, nuevo formato multi y deduplicación de URL. Cuatro títulos y sus formatos/categorías usados por los tests proceden del HTML real; el ejemplo pequeño de pruebas NO equivale a 55 casos completos ni prueba la librería visual.

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
- [x] Contrato específico OR/AND y compatibilidad URL: **10 tests locales Node pasados**.
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
