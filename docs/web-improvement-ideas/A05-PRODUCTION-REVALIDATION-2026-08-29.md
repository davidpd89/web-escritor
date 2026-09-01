# A.5 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #154  
Decisión operativa: **CONDITIONAL · POLICY_COMPLETE · NO_RUNTIME**

## Decisión cerrada

A.5 no autoriza una cuota de enlaces externos ni una automatización SEO. La regla definitiva es editorial:

> **Se enlaza una fuente externa cuando una afirmación concreta depende de evidencia, datos, documentación o contexto externos y ese enlace mejora materialmente la verificabilidad o la utilidad para el lector.**

No se añade un enlace solo para “parecer autoritativo”, aumentar E-E-A-T, alcanzar un número mínimo, obtener una métrica de dominio o fabricar una bibliografía ornamental.

La ausencia de enlace externo también es correcta cuando:

- la afirmación es experiencia/opinión propia claramente presentada como tal;
- el contenido explica una decisión interna del proyecto;
- la fuente no añade verificabilidad ni contexto útil;
- enlazar introduciría una referencia peor, indirecta o comercialmente sesgada frente a la evidencia disponible.

## Revalidación con fuentes primarias actuales

### Google · link best practices

https://developers.google.com/search/docs/crawling-indexing/links-crawlable

La documentación vigente indica que enlazar a otros sitios puede ayudar a establecer confianza, por ejemplo al citar fuentes, y que debe hacerse cuando tenga sentido y con contexto para el lector. No prescribe cuotas ni dominios concretos.

Conclusión para A.5: el valor procede de **citar una evidencia útil y contextual**, no del mero hecho de crear un outbound link.

### Google · qualify outbound links

https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links

Google distingue:

- enlace editorial normal: no necesita `rel` especial;
- publicidad/paid placement: `rel="sponsored"` es el valor preferido;
- `nofollow` sigue siendo aceptable para enlaces pagados, aunque `sponsored` es más específico;
- UGC: `rel="ugc"` cuando corresponda;
- pueden combinarse varios valores.

A.5 no convierte `nofollow` en atributo universal de enlaces externos: eso sería una política incorrecta.

### Google · spam policies

https://developers.google.com/search/docs/essentials/spam-policies

Google define link spam como enlaces creados principalmente para manipular rankings e incluye intercambios excesivos, automatización de enlaces y colocaciones pagadas que transmiten señales de ranking. También aclara que publicidad y sponsorship son normales si sus enlaces se califican adecuadamente.

Las políticas vigentes distinguen además la **thin affiliation**: una página de afiliación es problemática cuando replica contenido del merchant sin valor añadido; en cambio, una página afiliada con contenido significativo/original puede ser legítima. Y, dentro de site reputation abuse, Google enumera como caso no abusivo el uso de affiliate links correctamente tratados.

Esto descarta definitivamente link swaps, cuotas de enlaces y cualquier programa de outbound linking diseñado como palanca algorítmica, pero también evita sobrerreaccionar tratando la afiliación editorial legítima como spam por definición.

### Google · actualización de Site Reputation Policy del 28/08/2026

https://developers.google.com/search/blog/2026/08/update-site-reputation-policy

Se revisó expresamente la actualización publicada **ayer, 28 de agosto de 2026**, porque modifica desde el 30 de agosto el efecto de determinadas manual actions en el EEA y clarifica la aplicación de la política a contenido de terceros.

No cambia la decisión A.5 ni convierte la página de recomendaciones actual en un problema: el riesgo descrito es publicar contenido de terceros principalmente para explotar las señales ya establecidas del host. La superficie revisada de `davidportodiaz.com` es contenido editorial first-party del propio sitio y sus enlaces afiliados están calificados. La política de spam de Google continúa citando explícitamente los affiliate links correctamente tratados como ejemplo que no constituye site reputation abuse por sí mismo.

Por tanto, no se añade infraestructura reactiva por esta actualización. El trigger sí queda claro: si en el futuro la web aloja contenido comercial/editorial producido por terceros, deberá evaluarse esa superficie por finalidad, control editorial, disclosure y política vigente antes de publicarla.

### Google · people-first content / E-E-A-T

https://developers.google.com/search/docs/fundamentals/creating-helpful-content

La evaluación debe priorizar contenido útil, fiable y creado para personas. E-E-A-T no es un factor único que pueda “subirse” añadiendo dos enlaces oficiales a una página.

## Jerarquía editorial de fuentes

Cuando una afirmación sí requiera apoyo externo, se elige la fuente por proximidad a la evidencia, no por DA/DR:

1. fuente primaria u organismo oficial responsable;
2. propietario/responsable original del dato o documentación;
3. estudio, paper, norma o documentación técnica original;
4. fuente secundaria reputada cuando aporta síntesis, contexto o contraste que la primaria no ofrece;
5. fuente terciaria solo si es la mejor evidencia realmente disponible y se deja claro su alcance.

Una fuente secundaria puede ser preferible a una primaria si la afirmación que estamos haciendo es precisamente una síntesis, comparación o interpretación y la secundaria es la evidencia pertinente. La jerarquía no sustituye al juicio editorial.

## Contrato para enlaces comerciales y de afiliación

Regla definitiva:

- enlace editorial sin relación económica: `rel` especial no obligatorio;
- afiliación, publicidad, patrocinio o paid placement: incluir `sponsored`;
- `nofollow` puede coexistir con `sponsored`, pero no sustituye la obligación editorial de identificar correctamente la relación;
- `noopener`/`noreferrer` son decisiones de seguridad/privacidad del enlace y no una señal de autoridad;
- UGC, si en el futuro existe una superficie donde usuarios puedan publicar enlaces, usa `ugc` según el contrato de esa superficie.

El estado real de `main` ya demuestra la práctica correcta en `recomendaciones/portal-fantasy-espanol/index.html`: los enlaces de compra afiliados se califican como `rel="sponsored nofollow noopener noreferrer"` y la página declara transparencia de afiliación. A.5 no necesita duplicar esa infraestructura para resolver su alcance editorial.

## Relación con A.4

A.4 y A.5 se complementan sin acoplarse:

- A.5 decide **qué evidencia externa merece citarse**;
- A.4 permite registrar internamente **cuándo se verificaron de verdad los hechos/fuentes** mediante `verifiedAt` y cuándo conviene revisarlos con `reviewBy`;
- una verificación factual sin cambio sustancial no debe alterar `dateModified`;
- A.5 no obliga a activar lifecycle en cada pieza; se usa A.4 cuando la volatilidad o criticidad de hechos externos lo justifica.

## Por qué NO se implementa un validator semántico

No hay un contrato de máquina fiable para decidir automáticamente si:

- una fuente es realmente primaria;
- una referencia apoya la afirmación exacta;
- una fuente secundaria añade contexto mejor que la original;
- una pieza necesita una fuente externa en primer lugar;
- un artículo tiene “suficientes” enlaces externos.

Convertir esas decisiones en regex, conteos o listas de dominios introduciría falsos positivos y premiaría cumplimiento cosmético.

Lo que sí es objetivamente automatizable —integridad de enlaces, atributos comerciales cuando exista una autoridad de datos que los identifique, inventario de afiliación, etc.— debe vivir en el checker propietario de esa futura autoridad. Hoy A.5 no tiene un inventario estructurado de “todos los enlaces remunerados” que un nuevo test pueda validar sin reconstruir heurísticamente el HTML.

## Alternativas descartadas definitivamente

1. **“2 enlaces .gov/.edu por artículo”** — dominio no equivale a relevancia ni calidad y crea padding editorial.
2. **Cuota mínima/máxima de outbound links** — no existe evidencia oficial que la justifique.
3. **DA/DR como criterio de fuente** — métricas de terceros que no demuestran proximidad a la evidencia.
4. **`nofollow` en todo enlace externo** — contradice la guía oficial para enlaces editoriales normales.
5. **Bibliografía automática al final de cada página** — separa la evidencia de la afirmación y puede añadir referencias irrelevantes.
6. **Link swaps/reciprocidad sistemática** — entra en terreno de manipulación y link spam.
7. **Autoenlazado sitewide a autoridades externas** — coste de UX, mantenimiento y privacidad sin beneficio humano demostrado.
8. **Validator por lista blanca de dominios** — una URL de un dominio oficial puede no apoyar la afirmación y una fuente secundaria puede ser la evidencia correcta.
9. **Checker de “calidad” semántica por IA como merge gate** — resultado no determinista y sin contrato objetivo suficiente para bloquear releases.
10. **Crear un gate específico por la actualización Site Reputation del 28/08/2026** — la superficie actual es first-party y no existe el patrón de abuso que la política pretende resolver.

## Trigger de reapertura

A.5 solo requiere nuevo runtime/test si aparece uno de estos hechos concretos:

- se crea una autoridad estructurada que identifique enlaces afiliados/pagados y sea necesario garantizar su `rel="sponsored"`;
- se añade UGC con enlaces externos;
- se incorpora contenido comercial/editorial producido por terceros y hay que evaluar site reputation abuse/disclosure;
- aparece un fallo reproducible de disclosure/rel comercial no cubierto por los checks propietarios de esa superficie;
- una familia editorial de alta volatilidad activa A.4 y necesita un contrato de fuentes estructurado que pueda validarse objetivamente.

En esos casos se extiende la autoridad que posea los datos; no se crea un “SEO outbound checker” genérico.

## Definition of Done final

- [x] historia de #135 preservada;
- [x] `main@291c8c6…` inspeccionado;
- [x] Google Link Best Practices revalidado;
- [x] Google outbound link qualification revalidado;
- [x] spam policies revalidadas;
- [x] actualización Site Reputation Policy de 28/08/2026 revalidada y clasificada como no aplicable a la superficie first-party actual;
- [x] interpretación E-E-A-T como cuota de enlaces descartada;
- [x] jerarquía de fuentes definida;
- [x] afiliación/sponsorship definido;
- [x] relación con A.4 definida;
- [x] estado real de afiliación del repo contrastado;
- [x] no existe un gap de runtime demostrable dentro de A.5;
- [x] triggers objetivos de reapertura definidos.

**Conclusión:** A.5 queda cerrada como política editorial condicional y completa. No hay desarrollo pendiente hoy: implementar un contador, crawler paralelo o clasificador de “autoridad” empeoraría la precisión y la mantenibilidad. Si en el futuro aparece un dato estructurado o una superficie comercial/UGC/third-party nueva, se automatiza el contrato concreto que corresponda y nada más.