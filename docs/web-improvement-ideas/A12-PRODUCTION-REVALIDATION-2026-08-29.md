# A.12 · Revalidación de producción · 2026-08-29

## Veredicto

**IMPLEMENTED_IN_PR · REMOVE_THIRD_PARTY_REVIEW_SCHEMA · PRESERVE_EDITORIAL_QUOTES**

La reconstrucción histórica acertaba al rechazar ratings/reviews agregados desde terceros, pero la primera revalidación de esta PR comprobó solo `AggregateRating` y pasó por alto un caso real en `main`: la ficha de **Samuel entre mundos** incluía nueve objetos `Review` dentro de `Book.review`, todos con `reviewRating` 5/5 y `publisher: Amazon España`.

Ese hallazgo cambia A.12 de docs-only a corrección de producción.

## Evidencia real encontrada

`libros/samuel-entre-mundos/index.html` contenía:

- `Book.review` con nueve reseñas procedentes de Amazon España;
- cada objeto incluía `reviewRating` 5/5;
- el bloque humano de la página mostraba extractos atribuidos a Amazon;
- la copy visible decía que ninguna reseña había sido resumida ni editada, aunque varios blockquotes eran extractos abreviados de los `reviewBody` estructurados.

No existía `AggregateRating`, pero eso no hacía correcto el `Book.review` importado de otro sitio.

## Revalidación oficial vigente

Google Search Central mantiene `Book` entre los tipos compatibles con review snippets, pero exige que el contenido marcado sea visible y establece expresamente que no se deben agregar reseñas o ratings de otros sitios web.

Fuente primaria:

- `https://developers.google.com/search/docs/appearance/structured-data/review-snippet`

La política general de structured data sigue exigiendo que el markup represente fielmente el contenido de la página y no sea engañoso.

## Implementación de esta PR

### JSON-LD

Se elimina únicamente `Book.review` de Samuel.

Se preservan:

- `Book` y su `@id` canónico;
- ISBN, año, páginas, formato, género, publisher, imagen, `sameAs`, descripción y `ReadAction`;
- `FAQPage` existente, que pertenece a A.7 y se corrige en su PR propietaria separada;
- resto del graph y del HTML.

No se añade `AggregateRating` ni un reemplazo sintético.

### Contenido humano

Las opiniones no se eliminan. Se mantienen como **extractos editoriales visibles y atribuidos a Amazon España**.

La copy se corrige para no afirmar que son textos completos o no editados:

- eyebrow: `Reseñas publicadas · Amazon España`;
- disclosure: `Extractos abreviados de reseñas publicadas en Amazon España, atribuidos a sus autores. Consulta las reseñas completas en Amazon.`

Así se conserva prueba social humana sin representarla como review estructurada propia.

### Guardrail

Se amplía `tests/test-samuel-ecosystem-parity.py`, autoridad ya existente del ecosistema Samuel, para exigir:

- ausencia de `aggregateRating`;
- ausencia de `Book.review` de marketplaces;
- ausencia de la afirmación falsa `Ninguna ha sido resumida ni editada`;
- presencia del disclosure de extractos abreviados.

No se crea un segundo checker SEO.

## Scope deliberado

A.12 no elimina FAQs visibles, no toca `FAQPage` y no modifica el resto de la ficha. A.7 conserva la propiedad de la retirada de `FAQPage` para evitar mezclar dos decisiones históricas y dos PRs.

## Reapertura futura

Solo reconsiderar `Review`/`AggregateRating` si davidportodiaz.com opera un sistema propio y real de reviews que cumpla, como mínimo:

1. reseñas recogidas por el propio sitio;
2. contenido visible en la página marcada;
3. autor/origen/fecha trazables;
4. consentimiento, moderación y retirada;
5. política contra spam/incentivos engañosos;
6. agregado estadísticamente honesto si se usa `AggregateRating`;
7. compatibilidad con la documentación vigente de Google en ese momento.

## Definition of Done

- [x] se detecta el drift real omitido por la primera búsqueda;
- [x] se elimina `Book.review` de terceros;
- [x] no se introduce `AggregateRating`;
- [x] se mantienen las citas humanas atribuidas;
- [x] se corrige la copy que describía los extractos como íntegros;
- [x] se añade regresión en el owner existente;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Cierre

A.12 deja de ser una mera reconstrucción documental: la política histórica se aplica al caso real que había escapado al primer audit. La corrección es mínima, trazable y no destruye el contenido editorial útil.