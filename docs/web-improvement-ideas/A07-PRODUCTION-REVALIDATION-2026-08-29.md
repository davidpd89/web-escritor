# A.7 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #156  
Decisión operativa: **IMPLEMENTED_IN_PR · REMOVE_FAQPAGE · PRESERVE_HUMAN_FAQ**

## Corrección de la primera revalidación

La primera pasada de esta PR afirmó que el `main` actual contenía `0` usos de `FAQPage`. Esa conclusión procedía de una búsqueda de código de GitHub que devolvió un falso negativo.

La inspección directa posterior de `libros/samuel-entre-mundos/index.html` encontró un nodo `FAQPage` real dentro del `@graph` JSON-LD de Samuel.

Por tanto, A.7 **no estaba cerrada como docs-only**. Esta PR corrige el runtime y documenta expresamente el fallo de la primera comprobación para que no vuelva a tomarse una búsqueda indexada como prueba suficiente de ausencia.

## Decisión final

Google retiró la feature de FAQ rich results de Search. La FAQ humana de Samuel sigue siendo útil; el `FAQPage` orientado a esa feature ya no aporta el beneficio que justificó su existencia.

La solución aplicada es deliberadamente estrecha:

- retirar el nodo `FAQPage` de la ficha Samuel;
- mantener intacta la sección humana `<section id="faq">` con sus preguntas y respuestas;
- no sustituirla por `QAPage`;
- no prohibir `FAQPage` globalmente para cualquier consumidor futuro;
- añadir una regresión específica de Samuel que comprueba a la vez ausencia de schema y preservación del contenido humano.

## Revalidación oficial vigente

Fuente primaria:

- `https://developers.google.com/search/updates`

Google documenta:

- **7 de mayo de 2026:** los FAQ rich results dejan de aparecer en Google Search;
- **8 de mayo de 2026:** se añade el aviso de deprecación a la documentación;
- **15 de junio de 2026:** Google elimina la documentación de FAQ rich results porque la feature ya no se muestra.

La retirada no implica que la palabra `FAQPage` deje de existir en Schema.org ni que sea técnicamente inválida para cualquier consumidor. Implica que ya no debe mantenerse en esta web como táctica para una presentación de Google retirada.

## Estado real corregido del repo

Antes de esta PR, Samuel contenía:

```json
{
  "@type": "FAQPage",
  "mainEntity": [
    {"@type": "Question", "...": "..."}
  ]
}
```

La misma página contiene además una FAQ humana visible basada en `<details>`.

Tras esta PR:

- el nodo `FAQPage` desaparece del JSON-LD;
- `Book`, `WebPage`, `BreadcrumbList`, `Organization` y demás entidades no afectadas permanecen;
- la FAQ visible conserva al menos sus ocho respuestas;
- no se elimina información útil para lectores.

## Guardrail implementado

Se añade `tests/test-samuel-faq-schema-retirement.py`.

El test:

1. exige que `id="faq"` siga existiendo;
2. exige el encabezado visible `Preguntas frecuentes.`;
3. exige al menos ocho `<details>`;
4. parsea los scripts JSON-LD reales;
5. falla si cualquier nodo vuelve a declarar `FAQPage`;
6. comprueba que `Book` y `WebPage` sigan presentes para evitar una eliminación accidental del graph completo.

El test es **específico de la regresión real de Samuel**, no una prohibición global del vocabulario `FAQPage`.

## Por qué `QAPage` no es sustituto

Google sigue documentando `QAPage`, pero su semántica es distinta: una página centrada en una pregunta con sus respuestas. La propia documentación indica que no debe utilizarse para páginas FAQ con múltiples preguntas.

Cambiar `FAQPage` por `QAPage` solo para conservar un rich result sería un cambio semánticamente falso.

## Scope deliberado

Esta PR no toca las reseñas Amazon/`Book.review` detectadas durante la misma auditoría. Ese problema pertenece a A.12 y se corrige por separado en #165.

Separar ambos cambios evita mezclar dos decisiones históricas distintas y mantiene PRs revisables.

## Triggers de reapertura

A.7 solo se reconsidera si:

- Google u otro consumidor real vuelve a documentar una feature relevante basada en `FAQPage`;
- aparece un consumidor no-Google real y medible que necesite el tipo;
- se rediseña la experiencia FAQ por una necesidad editorial/UX independiente del schema.

## Definition of Done

- [x] historia de #135 preservada;
- [x] retirada del 07/05/2026 revalidada;
- [x] eliminación documental del 15/06/2026 revalidada;
- [x] falso negativo de la primera búsqueda corregido;
- [x] `FAQPage` real localizado por inspección directa;
- [x] nodo `FAQPage` retirado de Samuel;
- [x] FAQ humana preservada;
- [x] `QAPage` descartado como sustituto incorrecto;
- [x] guardrail específico añadido;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Conclusión

A.7 queda **implementada**, no simplemente rechazada en papel. Se retira el markup de una feature de Google ya desaparecida, se conserva el contenido que sí aporta valor a lectores y se deja una regresión que prueba directamente el HTML/JSON-LD en lugar de confiar en una búsqueda indexada.