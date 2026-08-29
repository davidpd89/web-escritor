# A.7 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #156  
Decisión operativa: **IMPLEMENTED_IN_PR · REMOVE_KNOWN_FAQPAGE · PRESERVE_HUMAN_FAQ**

## Corrección de la primera revalidación

La primera pasada de esta PR afirmó que el `main` actual contenía `0` usos de `FAQPage`. Esa conclusión procedía de una búsqueda de código de GitHub que devolvió un falso negativo.

La inspección directa posterior encontró **dos** superficies reales con `FAQPage` dentro de JSON-LD:

1. `libros/samuel-entre-mundos/index.html`;
2. `universo/noveris/index.html`.

El segundo caso apareció al revalidar B.9 y demuestra por qué una búsqueda indexada no puede utilizarse como única prueba de ausencia. Ambas páginas tienen FAQ humana visible, por lo que retirar el markup no elimina contenido ni funcionalidad.

A.7, por tanto, **no estaba cerrada como docs-only**. Esta PR corrige los dos casos concretos conocidos y deja una regresión que lee directamente los ficheros reales.

## Decisión final

Google retiró la feature de FAQ rich results de Search. Las FAQs humanas de Samuel y Noveris siguen siendo útiles; mantener `FAQPage` con el objetivo histórico de esa presentación ya no aporta ese beneficio.

La solución aplicada es deliberadamente estrecha:

- retirar el nodo `FAQPage` de Samuel;
- retirar el nodo `FAQPage` de Noveris;
- mantener intactas las dos FAQs humanas visibles;
- preservar `Book`/`WebPage` en Samuel;
- preservar `WebPage` y `DefinedTermSet` en Noveris;
- no sustituir `FAQPage` por `QAPage`;
- no imponer una prohibición tecnológica global y eterna sobre todo uso futuro del vocabulario;
- proteger las dos regresiones concretas mediante un único test propietario.

## Revalidación oficial vigente

Fuente primaria:

- `https://developers.google.com/search/updates`

Google documenta:

- **7 de mayo de 2026:** los FAQ rich results dejan de aparecer en Google Search;
- **8 de mayo de 2026:** se añade el aviso de deprecación a la documentación;
- **junio de 2026:** Google elimina la documentación de FAQ rich results porque la feature ya no se muestra.

La retirada no implica que `FAQPage` deje de existir como vocabulario Schema.org. La decisión de esta PR es más concreta: no conservar en estas superficies un markup cuyo beneficio Google que motivó la táctica ha desaparecido.

## Estado real corregido del repo

### Samuel

Antes de esta PR contenía un nodo `FAQPage` junto a `WebPage`, `Book` y otras entidades. La página contiene además una sección FAQ humana visible con ocho `<details>`.

Tras esta PR:

- `FAQPage` desaparece;
- `Book` y `WebPage` permanecen;
- la FAQ humana sigue visible y navegable.

### Noveris

Antes de esta PR contenía:

- `WebPage`;
- `DefinedTermSet` con el glosario canónico de Noveris;
- `FAQPage` con cinco preguntas.

La misma URL contiene además una FAQ humana visible con cinco `<details>` bajo `id="preguntas-frecuentes"`.

Tras esta PR:

- `FAQPage` desaparece;
- `WebPage` permanece;
- `DefinedTermSet` permanece intacto;
- el glosario visible permanece intacto;
- la FAQ humana sigue visible.

El caso de Noveris pertenece a A.7 aunque se haya descubierto durante B.9. B.9 no debe absorber esta corrección porque su owner es el glosario/`DefinedTermSet`, no el retiro de FAQ rich-result markup.

## Guardrail implementado

El primer guardrail creado era `tests/test-samuel-faq-schema-retirement.py`. Al aparecer el segundo caso real se sustituye por:

`tests/test-faq-schema-retirement.py`

El test:

1. comprueba Samuel y Noveris directamente;
2. exige que ambas FAQs humanas sigan presentes;
3. exige al menos ocho `<details>` en Samuel y cinco en Noveris;
4. parsea todos sus scripts JSON-LD;
5. falla si cualquier nodo de esas superficies vuelve a declarar `FAQPage`;
6. exige que Samuel conserve `Book` y `WebPage`;
7. exige que Noveris conserve `WebPage` y `DefinedTermSet`.

No es un regex global que prohíba para siempre el vocabulario en todo el repositorio: cubre las regresiones concretas que existían realmente.

## Por qué `QAPage` no es sustituto

`QAPage` representa otra experiencia: una página centrada en una pregunta y sus respuestas. No es un reemplazo semántico para una FAQ editorial con múltiples preguntas.

Cambiar `FAQPage` por `QAPage` únicamente para conservar markup sería modelar una experiencia que la página no ofrece.

## Scope deliberado

Esta PR no toca `Book.review`/ratings de Amazon. Ese problema pertenece a A.12 y se corrige por separado en #165.

Tampoco elimina `DefinedTermSet`: B.9 demuestra que el glosario de Noveris es una entidad distinta y coherente con el contenido visible.

## Triggers de reapertura

A.7 solo se reconsidera si:

- Google u otro consumidor real vuelve a documentar una feature relevante basada en `FAQPage`;
- aparece un consumidor no-Google real y medible que necesite el tipo;
- aparece otro `FAQPage` legado real que deba evaluarse;
- se rediseña una FAQ por una necesidad editorial/UX independiente del schema.

## Definition of Done

- [x] historia de #135 preservada;
- [x] retirada de FAQ rich results 2026 revalidada;
- [x] falso negativo de la primera búsqueda corregido;
- [x] `FAQPage` de Samuel localizado y retirado;
- [x] `FAQPage` de Noveris localizado y retirado;
- [x] FAQs humanas de ambas páginas preservadas;
- [x] `Book`/`WebPage` de Samuel preservados;
- [x] `WebPage`/`DefinedTermSet` de Noveris preservados;
- [x] `QAPage` descartado como sustituto incorrecto;
- [x] guardrail consolidado sobre las dos regresiones reales;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Conclusión

A.7 queda **implementada sobre las superficies reales encontradas**, no simplemente rechazada en papel. Se retira markup asociado a una feature Google ya desaparecida, se conservan las FAQs humanas y el glosario canónico de Noveris, y el test deja de depender de que un índice de búsqueda encuentre correctamente el token `FAQPage`.
