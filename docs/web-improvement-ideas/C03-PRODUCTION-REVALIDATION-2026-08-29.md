# C.3 · Revalidación de producción — preguntas reales → contenido

Fecha de revalidación: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #178  
Documento histórico preservado: `C03-READER-QUESTIONS-CONTENT-2026-08-29.md`

## Veredicto final

**ALREADY_PILOTED · EXISTING_EDITORIAL_OWNER · TRACEABILITY_GAP · NO_NEW_CONTENT**

C.3 no necesita una nueva aplicación, un segundo backlog ni una fábrica de páginas. El mecanismo editorial ya existe de facto:

- hay cuatro superficies públicas materializadas a partir de necesidades/intenciones de audiencia;
- el proyecto ya mantiene en Drive un backlog editorial que exige `Pregunta real · Ángulo propio · Fuentes · CTA natural · Enlaces internos · Responsable y fecha de revisión`;
- el registry público ya modela esas URLs dentro de la arquitectura actual;
- la deuda real es conservar de forma consistente la **procedencia agregada de la demanda** que justificó una decisión editorial.

Por tanto, esta PR no crea nuevas URLs, no importa conversaciones, no duplica el backlog de Drive y no introduce un dataset paralelo.

## 1. Piloto real comprobado en `main`

Se inspeccionaron directamente, sin depender del índice de búsqueda de GitHub, las cuatro superficies asociadas históricamente a C.3:

1. `/cuaderno/que-es-el-portal-fantasy/`
2. `/cuaderno/portal-fantasy-vs-fantasia-epica/`
3. `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`
4. `/universo/noveris/`

Las cuatro existen en `main`, tienen HTML real y forman parte de la arquitectura pública. `data/content-registry.json` contiene además los nodos correspondientes (`article-que-es-portal`, `article-portal-vs-epica`, `article-fantasia-juvenil-portales` y `samuel-noveris`).

Conclusión: C.3 no es una idea pendiente de demostrar. **El piloto ya ocurrió.**

## 2. Owner editorial existente

El fichero de Drive `14_BACKLOG_DE_ARTICULOS.md` ya funciona como autoridad editorial de la cola de contenidos. Su contrato de entrada exige:

> `Pregunta real · Ángulo propio · Fuentes · CTA natural · Enlaces internos · Responsable y fecha de revisión`

También prioriza resolver la cola/deuda existente antes de abrir URLs nuevas.

### Decisión de arquitectura

No crear en GitHub:

- `audience-questions.json`;
- otro backlog Markdown;
- una base de datos de preguntas;
- una app de captura;
- un workflow que copie emails/DMs/comentarios;
- un segundo sistema de priorización.

El backlog existente sigue siendo el owner editorial. Esta revalidación solo fija el contrato de trazabilidad que debe acompañar a una señal de demanda cuando se use para justificar una decisión.

## 3. Hueco real: provenance de demanda

La regla `Pregunta real` evita ideación completamente sintética, pero por sí sola no permite reconstruir después:

- de qué clase de fuente vino la señal;
- en qué ventana se observó;
- si fue una observación aislada o repetida;
- qué intención se normalizó;
- si se decidió enriquecer una URL existente, añadir una sección, crear una URL o no actuar.

Ese es el hueco real de C.3.

### Contrato mínimo de trazabilidad

Cuando una pregunta/señal pase a briefing editorial, registrar —en el propio brief o registro que ya gobierne esa pieza— los siguientes campos no personales:

| Campo | Valores / regla |
| --- | --- |
| `sourceClass` | `search_console`, `bing`, `site_search`, `email`, `dm`, `comment`, `interview`, `event`, `assistant`, `other` |
| `observationWindow` | fecha o intervalo suficientemente preciso para repetir la lectura |
| `aggregateObservations` | número agregado cuando exista; `null` si la fuente no permite un conteo responsable |
| `normalizedIntent` | necesidad editorial normalizada, sin PII |
| `existingCanonical` | URL actual que ya responde, o `null` |
| `disposition` | `existing_page`, `section`, `new_url`, `no_action` |
| `evidenceRef` | referencia reproducible no secreta; nunca copiar conversación privada completa por defecto |
| `reviewOwner` | responsable editorial |
| `reviewDate` | fecha de la decisión/revisión |

No es obligatorio convertir estos campos en JSON. El objetivo es trazabilidad, no estructuración por sí misma.

## 4. Jerarquía de decisión

Para cada señal:

1. normalizar la intención sin conservar datos personales innecesarios;
2. comprobar si una URL pública ya responde;
3. si existe, preferir `existing_page` o `section`;
4. solo considerar `new_url` si la intención es distinta y la pieza puede ser sustantiva/original;
5. registrar `no_action` cuando la señal sea débil, duplicada, fuera de foco o no permita aportar valor;
6. medir después la hipótesis original con la fuente adecuada, sin inventar causalidad.

Una query distinta no equivale a una intención distinta. Variantes léxicas no justifican páginas separadas.

## 5. R.21 — corrección de nivel de evidencia

La reconstrucción histórica de C.3 conserva que R.21 habría observado aproximadamente `91 impresiones / 1 clic` para «portal fantasy» en un snapshot operativo de Search Console.

Durante esta revalidación se buscó la fuente original por:

- snapshot histórico de #135;
- referencias a `R21`;
- `Search Console`;
- `91 impresiones`;
- `70 consultas`;
- materiales de Drive localizados por esos términos.

No se recuperó el artefacto primario que permita reproducir esas cifras.

### Estado correcto

`HISTORICAL_UNVERIFIED`

Se conserva en el documento histórico porque forma parte de cómo #135 razonó la idea, pero:

- no se usa como baseline actual;
- no se presenta como dato vigente de Search Console;
- no se utiliza para fijar thresholds;
- no se reconstruye de memoria;
- una futura medición debe registrar su propia ventana y evidencia.

La validez de C.3 no depende de esa cifra: las cuatro páginas piloto están verificadas directamente en producción/repo y el owner editorial existe.

## 6. Search Console: limitaciones que debe reflejar el workflow

Documentación oficial vigente:

- Performance report: https://support.google.com/webmasters/answer/7576553
- Dimensions/data groupings: https://support.google.com/webmasters/answer/17011259

Google documenta que Search Console permite analizar consultas, clics e impresiones, pero:

- algunas consultas se omiten para proteger la privacidad (`anonymized queries`);
- los totales pueden incluir esas consultas aunque no aparezcan como filas;
- la tabla está sujeta a truncado y no contiene necesariamente todas las queries.

Consecuencia: `aggregateObservations` es una señal de demanda dentro de una ventana, **no un censo exhaustivo de preguntas reales**.

No inferir identidad, demografía ni atributos sensibles a partir de una query.

## 7. People-first y anti-scaled-content

Fuentes actuales:

- Google Search Central — Creating helpful, reliable, people-first content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google Search spam policies: https://developers.google.com/search/docs/essentials/spam-policies

La política actual sigue favoreciendo información, investigación y análisis originales y contenido creado para ayudar a personas. También clasifica como abuso de contenido a gran escala la creación de muchas páginas principalmente para manipular rankings y con poco valor original, independientemente de si se produjeron con automatización, IA o humanos.

Por eso C.3 debe ser **demanda → decisión editorial**, no `query → URL`.

## 8. Fuentes humanas y privacidad

### Email / DM / comentarios

Guardar la intención normalizada y, si aporta valor, un conteo agregado. No copiar por defecto:

- nombre;
- handle;
- email;
- texto privado completo;
- capturas permanentes;
- atributos personales no necesarios.

Si una cita concreta va a publicarse, su permiso y atribución pertenecen al proceso editorial correspondiente, no a este ledger de demanda.

### Eventos / entrevistas / lectores

Una pregunta repetida puede registrarse como señal agregada. La memoria del autor o del equipo no debe convertirse en un número exacto si no se contabilizó.

### Asistente

No convertir conversaciones del asistente en un dataset editorial indiscriminado. Solo usar señales si la gobernanza vigente permite agregación/minimización y existe una necesidad real.

## 9. Triggers de actuación

### `existing_page`

Usar cuando la intención ya tiene canonical suficiente. Enriquecer solo si la nueva evidencia revela una carencia concreta.

### `section`

Usar cuando la respuesta nueva es útil pero no tiene suficiente independencia/sustancia para una URL.

### `new_url`

Solo si se cumplen simultáneamente:

- demanda o necesidad suficientemente respaldada;
- intención diferenciada de las URLs actuales;
- respuesta sustantiva/original disponible;
- encaje con el foco editorial del sitio;
- enlaces internos y parent/hub claros;
- capacidad de mantener/revisar la pieza.

### `no_action`

Es una decisión válida. Una pregunta puede ser real y aun así no merecer contenido público.

## 10. No crear contenido nuevo desde C.3 ahora

El propio owner editorial mantiene deuda y prioridades existentes. Esta revalidación no identifica una pregunta actual, respaldada y sin canonical que justifique saltarse esa cola.

Por tanto:

- no se añaden artículos;
- no se crean FAQs sintéticas;
- no se amplía el cluster portal fantasy por variantes;
- no se generan páginas desde Trends/PAA;
- no se modifica el registry ni sitemap.

## 11. Hallazgo fuera de scope: FAQPage residual

La inspección directa de las cuatro páginas piloto encontró `FAQPage` JSON-LD residual en:

- `/cuaderno/que-es-el-portal-fantasy/`;
- `/cuaderno/portal-fantasy-vs-fantasia-epica/`;
- `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`;
- `/universo/noveris/`.

Esto **no pertenece a C.3**. Se asigna a A.7/#156, que ya gobierna la retirada del schema FAQ obsoleto. No se corrige en #178 para mantener separación de responsabilidades.

## 12. Definition of Done C.3

- [x] reconstrucción histórica preservada;
- [x] cuatro superficies piloto verificadas directamente;
- [x] presencia en `content-registry` verificada;
- [x] owner editorial de Drive identificado;
- [x] no se duplica backlog/sistema;
- [x] contrato mínimo de provenance definido;
- [x] privacidad/minimización preservadas;
- [x] jerarquía `existing_page` → `section` → `new_url` → `no_action` fijada;
- [x] R.21 degradado correctamente a `HISTORICAL_UNVERIFIED` al no recuperar el artefacto primario;
- [x] fuentes Google 2026 revalidadas;
- [x] sin creación de contenido ni schema fuera de scope;
- [ ] CI del HEAD final verde;
- [ ] revisión de Claude antes de merge.

## Estado para revisión

**ALREADY_PILOTED · EXISTING_EDITORIAL_OWNER · TRACEABILITY_GAP · NO_NEW_CONTENT**

La mejora futura consiste en añadir estos metadatos mínimos al brief/owner existente cuando una señal real se use para decidir contenido. No construir otra plataforma hasta que el volumen demuestre que el flujo manual ya no es suficiente.
