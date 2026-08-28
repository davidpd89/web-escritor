# A.7 · `FAQPage` en páginas de libro

Fecha de revisión: 2026-08-28
Idea original: añadir preguntas frecuentes reales a las páginas de cada obra y marcarlas con `FAQPage` para mejorar rich snippets.

## Veredicto

**REJECT como táctica SEO/Google rich results. CONSERVAR FAQs visibles solo si ayudan al lector.**

La idea original está desactualizada. Google retiró la función de resultados enriquecidos de FAQ de Search a partir del **7 de mayo de 2026** y posteriormente retiró su documentación específica porque ya no se muestra. Por tanto, añadir `FAQPage` a las páginas de Samuel o Manecillas con la expectativa de ocupar más SERP no aporta ese beneficio.

## Fuente primaria y fecha

Google Search Central · Documentation updates
https://developers.google.com/search/updates

Registro de mayo/junio de 2026:

- 8 mayo: anuncio de retirada; los FAQ rich results dejan de aparecer desde el 7 de mayo de 2026.
- posteriormente Google retiró la documentación de la función porque ya no aparece en Search.

Referencia histórica del cambio previo de 2023:
https://developers.google.com/search/blog/2023/08/howto-faq-changes

En 2023 Google ya había restringido fuertemente FAQ rich results a sitios gubernamentales/salud de alta autoridad. En 2026 la feature de rich result fue retirada completamente de Google Search.

## Importante: FAQ visible ≠ FAQ schema

Una sección visible de preguntas frecuentes puede seguir siendo excelente contenido si responde dudas reales:

- ¿de qué género es el libro?;
- ¿puedo leer un fragmento?;
- ¿es autoconclusivo? **solo si esto está confirmado**;
- ¿qué edición/formato existe?;
- ¿dónde comprar? solo con retailer/URL real verificado;
- ¿hay guía para club de lectura?

Lo que se rechaza es añadir `FAQPage` **por SEO** o generar preguntas inventadas para producir schema.

## Estado del proyecto

El historial del repo ya había detectado esta deuda:

- PR #66: identificó `FAQPage` legacy en recomendaciones y pidió retirar el schema preservando el FAQ visible.
- PR #75 y #76 reutilizaron explícitamente esa decisión en auditorías posteriores.

Esto es coherente con la evolución oficial de Google.

## Qué haría en las páginas de libros

### Samuel

Si hay preguntas reales y verificadas, mostrarlas como HTML normal dentro de la ficha o enlazar a recursos existentes. No añadir `FAQPage`.

### Manecillas

Lo mismo. Evitar especialmente preguntas comerciales anticipadas (`¿dónde comprar?`) mientras no exista URL real verificable.

### Noveris / club de lectura

Puede haber formato pregunta-respuesta por razones editoriales. Eso no obliga a `FAQPage`. Si el contenido es realmente una página comunitaria con una pregunta y múltiples respuestas de usuarios, eso sería otro tipo (`QAPage`) y requiere cumplir sus condiciones; no aplica automáticamente a FAQs redactadas por el autor.

## Structured data que sí merece prioridad

En fichas de libro, priorizar exactitud de:

- `Book`;
- `WebPage`;
- `Person`/author por `@id`;
- publisher real;
- ISBN/páginas/fecha/formatos reales;
- `BreadcrumbList` donde corresponda;
- `ImageObject`;
- relaciones `hasPart`/fragmentos cuando sean factuales.

No añadir schema por tener más tipos.

## Guardrail propuesto

Añadir un test simple para evitar reintroducirlo por una futura recomendación SEO desactualizada:

`tests/test-no-faqpage-seo-regression.py`

Pseudocódigo:

```python
for html in public_indexable_html():
    graphs = parse_jsonld(html)
    assert not contains_type(graphs, "FAQPage"), (
        f"{html}: FAQPage rich results were retired by Google in 2026; "
        "visible FAQ is allowed, schema requires a documented non-Google consumer"
    )
```

### Excepción

No convertirlo en prohibición dogmática del vocabulario Schema.org. Si en el futuro existe un consumidor real/no-Google que requiera `FAQPage`, la excepción debe documentar:

- consumidor;
- beneficio;
- páginas;
- fecha de verificación;
- por qué compensa mantenerlo.

Pero no se autoriza por “quizá ayuda a las IA”.

## Qué NO hacer

- añadir 8–12 preguntas genéricas a cada libro para SEO;
- generar FAQ automáticamente desde People Also Ask;
- repetir la sinopsis en forma de preguntas;
- añadir `FAQPage` esperando snippets grandes;
- confundir `QAPage` con FAQ editorial;
- marcar preguntas/respuestas que no son visibles;
- inventar edades, audiolibro, saga, disponibilidad o retailer.

## Impacto

Implementar la idea original: **valor SEO nulo/obsoleto + mantenimiento innecesario**.
Mantener FAQs visibles útiles: **valor UX/contenido potencialmente alto**.
Añadir guardrail anti-regresión: **coste bajo / valor alto** porque ya hubo FAQPage legacy en el repo.

## Definition of Done

- [x] confirmar retirada oficial de FAQ rich results en 2026;
- [ ] escanear `main` actual por `"@type": "FAQPage"`;
- [ ] si quedan instancias públicas, clasificarlas y retirar solo el schema cuando no tenga consumidor vigente;
- [ ] preservar preguntas visibles útiles;
- [ ] añadir guardrail si no existe ya uno equivalente;
- [ ] no introducir FAQs ficticias en Samuel/Manecillas.

## Recomendación de merge

**MERGE como `REJECT` documentado + guardrail recomendado.** Esta PR evita que Claude implemente una práctica de Google retirada en 2026.