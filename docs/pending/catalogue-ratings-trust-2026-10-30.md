# Encargo de confianza editorial: ausencia de valoración no significa cero estrellas

Estado: **BORRADOR, SIN IMPLEMENTAR**. P1 de presentación editorial del catálogo.
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

- [ ] Propuesta antes/después en tarjetas reales sin rating y con rating verificado.
- [ ] Regresiones: sin dato, caducado, proveedor fallido, 1–4 opiniones y >=5 opiniones.
- [ ] Ningún estado no verificado muestra cero numérico como nota real.
- [ ] Aria-label y texto visible describen lo mismo, sin afirmar hechos desconocidos.
- [ ] La fuente y fecha de muestras válidas se conservan; no degradar filtros/orden.
- [ ] Catálogo 390/768/1280, JS/no-JS, sin saltos de layout ni nuevas peticiones externas.
- [ ] Pruebas existentes de ratings/market y browser ampliadas con semántica visual.
- [ ] Inventario de superficies, versiones/hashes y CI antes de publicar; SHA verificado.

No se garantiza una mejora de ranking: es un arreglo de confianza y calidad de
presentación, relevante para UX y coherencia editorial. Cualquier conclusión
SEO debe contrastarse posteriormente con Search Console si está disponible.

Esta PR solo contiene el encargo. Otra IA continúa esta rama con diseño, código,
tests y despliegue. No fusionar el documento como si solucionara las valoraciones.