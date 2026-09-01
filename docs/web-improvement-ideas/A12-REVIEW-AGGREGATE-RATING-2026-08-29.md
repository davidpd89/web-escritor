# A.12 · `Review` / `AggregateRating` en páginas de obra

Fecha de reconstrucción: 2026-08-29  
Idea original: marcar reseñas reales de lectores/prensa con `Review`/`AggregateRating`.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `REJECT` para reconstruir ratings/reviews externos; solo reconsiderar reviews propias visibles y válidas.

## Veredicto reconciliado

**REJECT en su formulación práctica actual. NO RECONSTRUIR AMAZON/GOODREADS/TERCEROS COMO `Review`/`AggregateRating` PROPIO.**

#135 empezó con una hipótesis razonable —usar schema si había reseñas citables—, la estrechó a un condicional muy estricto y finalmente la rechazó para el caso real de esta web al contrastarla con las directrices de Google y el riesgo de agregar valoraciones ajenas como propias.

Las citas editoriales/prensa visibles, atribuidas y enlazadas pueden seguir existiendo como contenido humano. Eso no obliga a convertirlas en rating estructurado.

## 1. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía:

> Si hay reseñas de lectores o prensa citables, marcarlas con schema `Review`/`AggregateRating` en las páginas de obra, con permiso/atribución real y nunca inventadas.

La idea original ya incluía una salvaguarda correcta: no fabricar reviews.

## 2. Evolución cronológica en #135

### 2.1 · Revisión exhaustiva → `REJECT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` concluyó que Google prohíbe agregar reviews/ratings de otros sitios como si fueran propios. El ejemplo de riesgo era recuperar estrellas/puntuaciones de Amazon o Goodreads y trasladarlas al JSON-LD de davidportodiaz.com.

La revisión dejó una única puerta abierta: **reviews propias, visibles en la página, recogidas mediante un sistema real y compatibles con las directrices**.

### 2.2 · Matriz final → `CONDICIONAL ESTRICTO`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` formuló el límite como:

- `Review` solo para reviews visibles y válidas que el sitio tenga derecho a publicar;
- nunca copiar/agregar ratings de Amazon/Goodreads como propios.

Esta matriz no reabrió el caso externo: describió las condiciones mínimas que tendría que cumplir un caso futuro propio.

### 2.3 · Override de alternativas → mantener rechazo externo

`docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` conserva A.12 entre los descartes y propone la alternativa correcta:

- citas editoriales/prensa visibles con atribución y URL;
- reviews propias solo si existe un sistema real de recogida y cumple las directrices.

### 2.4 · Autoridad final → `REJECT`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` cierra:

> No reconstruir `Review/AggregateRating` con Amazon/Goodreads/terceros. Las citas visibles y atribuidas pueden existir editorialmente; no agregarlas como rating propio.

`data/web-improvement-decisions-2026-08-28.json` mantiene `REJECT`.

### 2.5 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` volvió a revisar Google Review Snippets y mantuvo A.12 rechazado. La falsación explícita dice que A.7/A.12 están correctamente descartadas por políticas Google.

Secuencia:

```text
hipótesis: marcar reseñas reales
→ revisión: terceros agregados no son válidos = REJECT
→ matriz: solo reviews propias visibles bajo condiciones estrictas
→ override: alternativa = citas humanas atribuidas
→ autoridad final: REJECT para Amazon/Goodreads/terceros
→ revalidación independiente: mantiene
```

## 3. Estado real de `main`

La búsqueda actual del repo no localiza `AggregateRating`. Esto es coherente con la decisión de no reintroducir estrellas agregadas externas como schema.

Las páginas de obra sí disponen de entidades `Book` y otros datos estructurados. La ausencia de `AggregateRating` no es deuda por sí misma.

## 4. Fuentes primarias revalidadas

Google Search Central:

- Review snippet structured data: https://developers.google.com/search/docs/appearance/structured-data/review-snippet
- Structured data general guidelines: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- Search documentation updates: https://developers.google.com/search/updates

La revalidación de 2026 conserva dos principios relevantes:

1. el contenido marcado debe ser real, visible y cumplir las políticas de la feature;
2. no se debe presentar una agregación de valoraciones de otros sitios como rating propio.

Google añadió además una recomendación en enero de 2025: cuando un sitio acepte ratings/reviews, conviene que estén acompañados de comentario y nombre del autor para aportar contexto. Eso refuerza la exigencia de un **sistema de reviews propio y sustantivo**, no una media de estrellas copiada.

## 5. Diferenciar cuatro cosas

### 5.1 · Cita de prensa

Ejemplo: una frase breve atribuida a un medio, con URL y fecha. Puede mostrarse editorialmente si existe derecho/uso legítimo. No implica `Review` ni rating.

### 5.2 · Reseña de lector recibida por el propio sitio

Solo sería candidata futura si:

- el sitio realmente la recoge;
- hay autor/identidad pública adecuada o política clara;
- el texto se muestra al usuario;
- existe moderación/consentimiento/retirada;
- no se seleccionan solo reviews positivas para fabricar una nota agregada;
- cumple las directrices de Google.

### 5.3 · Rating de Amazon/Goodreads/Babelio/StoryGraph

Es dato de un tercero. No debe copiarse y agregarse como si fuese la valoración propia de davidportodiaz.com.

### 5.4 · Testimonio promocional autorizado

Puede ser una cita humana visible, pero no se convierte automáticamente en `Review` elegible ni en una base estadística para `AggregateRating`.

## 6. Trigger para reconsiderar A.12

Solo reabrir si existe un **producto real de reviews propias**. Antes de escribir schema:

1. documentar cómo se recoge cada reseña;
2. consentimiento/licencia de publicación;
3. moderación y retirada;
4. política anti-spam/duplicado;
5. contenido visible en la misma página;
6. definir si existe escala suficiente para un agregado honesto;
7. comprobar elegibilidad Google vigente;
8. validar con Rich Results Test;
9. medir si añade una feature real, no solo más JSON-LD.

Si ese sistema no existe, `NO_ACTION`.

## 7. Qué sí hacer con autoridad externa

La alternativa de #135 es más sólida para este proyecto:

- archivo de prensa cronológico;
- citas visibles y breves con atribución;
- URL a la fuente original;
- fecha y medio;
- `verifiedAt` interno;
- press-kit factual;
- `sameAs`/identificadores externos cuando sean verdaderos;
- no fingir una puntuación agregada.

Esto mejora verificabilidad sin convertir opiniones externas en un número propio.

## 8. Qué NO hacer

- scrape de estrellas Amazon/Goodreads;
- copiar conteos de reviews ajenos;
- calcular una media cross-platform;
- inventar `ratingValue`, `reviewCount` o `bestRating`;
- marcar testimonios seleccionados como si fueran muestra representativa;
- ocultar las reviews marcadas;
- JSON-LD que no coincide con contenido visible;
- crear reviews sintéticas/IA;
- añadir schema porque un validador lo permite sintácticamente;
- presentar estrellas externas como «rating oficial» del libro.

## 9. Tests/guardrails futuros

Si algún día existe review propia:

- schema y contenido visible deben coincidir;
- cada review debe tener origen/autor/fecha trazable;
- ningún dominio externo debe convertirse automáticamente en `AggregateRating`;
- fixture negativo para Amazon/Goodreads;
- no permitir conteos inventados;
- Rich Results Test manual tras cambios;
- Search Console solo demuestra procesamiento/errores, no garantiza rich result.

## 10. Coste / beneficio

Para ratings externos: **beneficio inválido y riesgo alto** → rechazo.

Para un sistema propio de reviews: coste de producto, moderación, privacidad y mantenimiento considerable. Solo tendría sentido si se desea realmente esa función para lectores, no como táctica SEO.

## 11. Definition of Done

### Historia recuperada

- [x] hipótesis original preservada;
- [x] `REJECT` de revisión preservado;
- [x] condicional estricto de matriz explicado;
- [x] alternativa editorial del override preservada;
- [x] autoridad final `REJECT`;
- [x] revalidación independiente;
- [x] fuente Google Review Snippet revalidada.

### Contrato futuro

- [ ] no ratings externos como propios;
- [ ] reabrir solo con sistema propio real;
- [ ] visible + consentimiento + moderación + políticas;
- [ ] validar feature vigente antes de implementar.

## 12. Trazabilidad de #135

Aportan contenido específico:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`.

Se revisaron además corpus de fuentes primarias/adicionales, pasadas cuarta–decimoquinta, blueprints, casos y repos/tooling; no contienen una corrección posterior que reabra A.12.

## 13. Recomendación

**MERGE como reconstrucción completa + `REJECT` del uso de reviews/ratings externos.** Mantener la puerta futura únicamente para un sistema propio de reviews real y compatible.