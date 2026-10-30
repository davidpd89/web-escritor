# Encargo de confianza editorial: ausencia de valoración no significa cero estrellas

Estado: **IMPLEMENTADO** (ver «Implementación»). P1 de presentación editorial del catálogo.
Base: `c369f933e52073604adc2972f902191289992e08`.

## Alcance confirmado

Producción `/recomendaciones/`, Chromium, JS activo, respuestas del propio origen
permitidas y solicitudes ajenas bloqueadas; sin datos de lectores ni envíos:

- 88 tarjetas en el catálogo, 24 visibles por página.
- 62 tarjetas generan enlace con texto `Goodreads ★★★★★ 0,0 (0)` y estrellas vacías.
- 18 de las 24 tarjetas de la primera página muestran ese estado.
- Se reproduce en anchos 390, 768 y 1280 px.
- El HTML fuente no contiene `0,0 (0)`: se introduce por el runtime. No atribuir
  a los datos estructurados estáticos una cifra que no se ha encontrado allí.

## Causa y significado

`assets/reading-catalogue.js`, `renderMarket()`: si `ratingFor()` no devuelve una
valoración y hay ISBN de 13 cifras, fabrica enlace a Goodreads con cero y recuento
cero. El aria-label afirma «aún sin valoraciones públicas».

Sin embargo, `validRating()` puede excluir una muestra por caducidad, fuente,
errores o recuento menor que cinco. No disponer de valoración utilizable en ESTE
sistema no demuestra que Goodreads tenga cero opiniones o que la obra valga cero.
El caso de poca muestra tampoco equivale a ausencia total.

El cero se muestra al visitante justo al decidir qué leer/comprar y genera una
impresión negativa que los datos disponibles no respaldan. No se ha medido su
efecto en ventas; no inventar porcentajes ni una penalización SEO.

## Encargo a la IA implementadora

- Diseñar estados honestos: valoración verificada vigente, muestra insuficiente,
  dato no disponible/caducado y error/carga si procede.
- No representar ausencia de datos como puntuación 0/5 ni afirmar que no hay
  opiniones en la fuente. Usar texto neutral y enlace «Consultar en Goodreads»
  o esconder el bloque según propuesta visual justificada.
- Mantener política de vigencia/muestra sin relajar validaciones para llenar estrellas.
- Sincronizar texto visible, nombre accesible, filtros y orden de valoraciones.
- Revisar otros usos del mismo runtime y constructor, incluidas fichas de libros,
  para que la política editorial sea homogénea, con alcance inventariado.
- No añadir aggregateRating ficticio, recolectar reseñas nuevas ni copiar críticas.

## Aceptación y pruebas

- [x] Propuesta antes/después en tarjetas reales sin rating y con rating verificado.
- [x] Regresiones: sin dato, caducado, proveedor fallido, 1–4 opiniones y >=5 opiniones.
- [x] Ningún estado no verificado muestra cero numérico como nota real.
- [x] Aria-label y texto visible describen lo mismo, sin afirmar hechos desconocidos.
- [x] La fuente y fecha de muestras válidas se conservan; no degradar filtros/orden.
- [x] Catálogo 390/768/1280, JS/no-JS, sin saltos de layout ni nuevas peticiones externas.
- [x] Pruebas existentes de ratings/market y browser ampliadas con semántica visual.
- [x] Inventario de superficies, versiones/hashes y CI antes de publicar; SHA verificado.

No se garantiza una mejora de ranking: es un arreglo de confianza y calidad de
presentación, relevante para UX y coherencia editorial. Cualquier conclusión
SEO debe contrastarse posteriormente con Search Console si está disponible.

## Implementación

Inventario: el único constructor es `renderMarket()` en `assets/reading-catalogue.js`, que
pinta todas las cajas `[data-rating-book]`: el hub `/recomendaciones/` (88 tarjetas) y las 88
fichas `/recomendaciones/libros/*/`. Las páginas de autor y editorial cargan el script pero no
tienen cajas de valoración.
El HTML estático no contiene notas ni `aggregateRating`, así que no hay más superficies.

Estados (atributo `data-rating-state` en el enlace):

| Estado | Cuándo | Visible = nombre accesible |
|---|---|---|
| `verified` | fuente válida, vigente (≤168 h), nota 1–5 y ≥5 opiniones | `Goodreads ★★★★★ 4,2 (12.345)` (estrellas `aria-hidden`), sin cambios |
| `insufficient` | igual pero con 1–4 opiniones | `Goodreads · menos de 5 valoraciones` (con la fuente propia: Hardcover, Google Books), enlace a la ficha de esa fuente |
| `unavailable` | sin dato, caducado, fuente/URL no válida o mercado caído | `Goodreads · consultar ficha`, enlace por ISBN-13; sin ISBN no se pinta nada |

Antes/después en tarjetas reales sin rating: `Goodreads ★★★★★ 0,0 (0)` con aria-label «aún sin
valoraciones públicas» → `Goodreads · consultar ficha`, sin estrellas ni aria-label. Con rating
verificado no cambia nada. Sin aria-label, el nombre accesible coincide con el texto visible.
Filtro y orden de valoración siguen usando solo valoraciones verificadas; no se relaja
`validRating()`. Sin JS no se pinta ninguna nota (como antes).

Pruebas:
- `qa/catalogue-ratings-trust.mjs` (nueva, en recommendations-browser-qa): proveedor caído
  (503), mercado vacío, y mezcla verificado / 4 opiniones / 1 opinión (Hardcover) /
  caducado / host falsificado / sin dato a 390, 768 y 1280 px; filtro, orden, sin JS, sin
  peticiones externas ni scroll horizontal. **Falla en main** («0,0 (0)»).
- Actualizadas: `reading-commerce-browser`, `reading-failure-resilience-browser` y
  `reading-type-selector-browser`, que daban por bueno el estado `0,0 (0)`.
- `reading-catalogue.js` v=22; índice Pagefind regenerado.