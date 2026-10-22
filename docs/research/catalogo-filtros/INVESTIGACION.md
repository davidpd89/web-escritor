# Filtros acumulativos del catálogo — investigación aplicable

> 22-10-2026 · PR #715 · Solo investigación. No hay cambios en producción, Actions ni merge.

## Problema y resultado buscado

En `scripts/build-reading-catalogue.py::render_filters()` los selectores admiten una categoría o formato. En `assets/reading-catalogue.js`, `values()` recoge `f.value` y `matches()` compara escalares; no sirve pasarles un array sin adaptación. Se necesitan **varias opciones dentro de cada filtro (OR) y cruces entre filtros (AND)** sin romper precio, orden, enlaces, paginación, test de lectura ni acceso sin JavaScript.

Datos contrastados sobre `recomendaciones/index.html` de `main` el 22-10-2026:

| Selección | Libros únicos |
| --- | ---: |
| Tapa blanda / tapa dura | 32 / 24 |
| Tapa blanda **O** tapa dura | 55 |
| Fantasía / Terror | 7 / 3 |
| Fantasía **O** Terror | 8 |
| Cocina **Y** Fantasía | 0 |
| Cocina **Y** (Fantasía **O** Cocina) | 10 |

Un libro puede tener varios formatos o géneros, por eso las uniones no son sumas. Son cifras de referencia, **no constantes para futuros tests**, porque el catálogo crece automáticamente.

## Una biblioteca real, código completo y licencia

**Choices.js v11.2.4**, release del 23-08-2026: [upstream](https://github.com/Choices-js/Choices/releases/tag/v11.2.4). Multiselección, búsqueda dentro de opciones, chips removibles y teclado; no requiere jQuery.

- [`upstream/choices-v11.2.4.min.js`](./upstream/choices-v11.2.4.min.js): JS completo original, SHA Git `0c37de23e3c35d4a89fd62b56587beff6d9f9b4d`.
- [`upstream/choices-v11.2.4.min.css`](./upstream/choices-v11.2.4.min.css): CSS completo original, SHA `474ed5f27c2d059d18c601eebb017b22cfa566cc`.
- [`upstream/CHOICES-LICENSE.txt`](./upstream/CHOICES-LICENSE.txt): MIT completo original, SHA `432f18873762b3f277abea8da35cd97982cedc6a`.

Los blobs de estos tres archivos fueron cotejados con el tag. **No se modificó el código original.** No incorporar código de Shopify Dawn como si fuera MIT: su licencia no autoriza libre reutilización fuera de temas Shopify.

## Qué hay preparado y probado

- [`demo-multifiltro.html`](./demo-multifiltro.html): laboratorio sin despliegue, con 55 tarjetas y taxonomía extraídas al cargar del catálogo real. Presenta únicamente formato, género y temática, cuenta resultados y pagina 24 fichas. No inventa precios. Los parámetros ocultos de URL se conservan para comprobar compatibilidad, pero **no se aplican en esta demo limitada**.
- [`multifacet-contract.mjs`](./multifacet-contract.mjs): `parseHash`/`writeHash` (valores repetidos, compatibilidad con valores antiguos, preservación de filtros escalares); `matchesMulti` (OR/AND); `availableOptions` (recuento excluyendo su propia faceta); `sanitizeFacetSelections` y `matchingOffersMulti`.
- [`multifacet-contract.test.mjs`](./multifacet-contract.test.mjs): **25/25 superados con Node.js 22 local** usando los archivos **idénticos** a la rama; ver hashes y ejecución en la sección QA. Cubren cruces, URL, selecciones a cero, formatos y precios en la misma oferta, y compatibilidad de valores escalares con el test de lectura.
- [`qa-demo.mjs`](./qa-demo.mjs): prueba real de Choices.js en Playwright, cuatro anchuras (320, 390, 768 y 1440), selección múltiple por `data-value`, paginación, restauración de URL, filtros antiguos y reset. **Es código preparado, no ejecutado.**

### Dos errores de integración que no se deben repetir

**1. Compatibilidad con el test de lectura.** En `assets/reading-catalogue.js::setupQuiz()`, `criteria` contiene strings (`{genero: 'fantasia'}`), no arrays. La versión anterior de `matchesMulti()` llamaba `.some()` sobre ese string y fallaría. Ahora `selection(wanted)` convierte tanto un escalar como un array a lista internamente y `availableOptions()` compara IDs exactos; `fantasia-juvenil` no marca también `fantasia`. Cuatro pruebas Node protegen estos casos. La nueva prueba verifica que `writeHash({genero: 'fantasia'})` conserva el género entero: antes `new Set('fantasia')` lo descomponía en letras sueltas.

**2. Precio/formato de una misma oferta.** Un libro puede tener blanda a 9,50 € y dura a 25,90 €. `Solo dura + precio máximo 10 €` debe dar cero, no usar el precio de la blanda. `matchingOffersMulti(offers, state)` evalúa simultáneamente OR de formatos, precio mínimo/máximo y descuento por **cada oferta individual**. Se alimenta de `offersFor()` —que ya aplica `validOffer()`/`fresh()`—; no sustituir la validación del mercado existente. Actualmente `assets/reading-market.json` contiene **cero ofertas**: no atribuir precios inexistentes ni afirmar que se ha probado con precios en directo.

## Reglas precisas de facetas

- **OR dentro de una dimensión**: `formato=tapa-blanda&formato=tapa-dura` o `genero=fantasia&genero=terror`; **AND entre dimensiones**.
- Para contar las opciones de una dimensión, retirar solo esa dimensión temporalmente. Mostrar recuentos contextualizados sin eliminar un chip elegido que ahora tenga cero resultados.
- La taxonomía tiene 54 categorías activas; 49 usadas en las tarjetas. `romantasy`, `portales`, `magia-con-coste`, `navidad`, `verano` siguen **activas con 0 libros**. Conservarlas si están elegidas; eliminar solo slugs inexistentes. El laboratorio ya distingue ambas situaciones.
- Si una combinación devuelve cero, mostrar un mensaje y una acción para limpiar, no un listado blanco.
- Respetar parámetros actuales de búsqueda, grupos, extensión, fechas, valoración, novedades, precios, ofertas, orden y página. No perder ninguno al serializar la URL.

## Integración mínima en producción (aún no aplicada)

1. Generar `<select multiple>` para las dimensiones multiseleccionables desde `render_filters()` **sin eliminar las opciones originales de la taxonomía**. Inicializar Choices.js después de habilitar el `fieldset`; permitir comportamiento nativo si no carga JavaScript.
2. En `values()`, leer `selectedOptions` de los multiselect como arrays. Mantener los campos escalares existentes. En `matches()`, aplicar OR/AND mediante `matchesMulti()` pero **conservar** las comprobaciones de páginas, fecha, valoración, grupo y novedad. Los formatos detectados en ofertas vigentes deberán agregarse al modelo, igual que hace hoy `matches()`.
3. Sustituir únicamente el predicado de oferta de `matchingOffers()` por `matchingOffersMulti(offersFor(card.dataset.bookId), v)`; cuando se filtra por precio/descuento, el libro solo pasa si existe **una oferta válida** que cumple precio y formato juntos. La ordenación por precio y el bloque «Desde…» deben utilizar esas mismas ofertas elegibles.
4. **Cuestionario / reset / hashchange:** no basta con asignar `field.value = 'fantasia'` a un `<select multiple>` gestionado por Choices.js. Sincronizar las selecciones del widget después de aplicar estado externo, usando las APIs del upstream `removeActiveItems()`, `setChoices()` y `setChoiceByValue()`; evitar recursión de eventos y recalcular una vez. El laboratorio muestra una estrategia para restaurar y restablecer, pero falta comprobarla en navegador. El test de lectura actual tiene que seguir ofreciendo todas las opciones maestras (`setupQuiz()::optionsFrom`) aunque las facetas visibles estén recortadas.
5. Conservar ordenación original, 24 por página, enlaces comerciales y estados sin JavaScript. Probar 55 obras reales, la fixture de 100/200 del QA existente y cuatro anchuras, incluido teclado, foco y zoom 200 %. No duplicar un segundo motor de filtrado.

Referencia de la API upstream utilizada: [choices.ts en v11.2.4](https://github.com/Choices-js/Choices/blob/v11.2.4/src/scripts/choices.ts), métodos `setChoices`, `setChoiceByValue`, `removeActiveItems` y `refresh`.

## Evidencia y puerta de aceptación

**Ejecutado el 22-10-2026** en contenedor local:

```sh
node --test /mnt/data/catalogue-check/research/multifacet-contract.test.mjs
# 25 tests, 25 pass, 0 fail — Node v22.16.0
git hash-object /mnt/data/catalogue-check/research/multifacet-contract.mjs
# 5076ccffe3bab5008b858171fd75064ce1241a2b
git hash-object /mnt/data/catalogue-check/research/multifacet-contract.test.mjs
# a2dd3a99a5498f0db6b765602a272f7ae1e17162
```

Los dos SHA coinciden con GitHub. Adicionalmente se calcularon 9 combinaciones ejecutando el motor sobre los 55 registros de la página: **9/9 correctas**.

**Pendiente — no presentar como verde:** ejecutar el laboratorio con **el Choices.js íntegro** en Chromium. El contenedor tiene Chromium y Playwright Python, pero no dispone de la rama completa ni resuelve `raw.githubusercontent.com`; no se ha fingido esta prueba con controles simulados.

Comandos al disponer de una copia local de la rama y sus dependencias existentes:

```sh
# Desde la raíz del repositorio, en terminal 1:
python -m http.server 4173
# En terminal 2, usando el Playwright del package.json:
node docs/research/catalogo-filtros/qa-demo.mjs
```

La PR permanece en **borrador** hasta superar navegación por teclado, foco, selección y eliminación repetida, URLs, reset, móvil y ausencia de errores JavaScript. **Sin Actions y sin merge.**
