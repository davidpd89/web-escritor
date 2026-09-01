# A.1 · Auditoría de topical authority

Fecha de reconstrucción: 2026-08-28  
Idea original: organizar Cuaderno, Recomendaciones y Libros en clusters pilar + satélite explícitos.  
Fuente histórica principal: PR #135, snapshot conservado en `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado actual de esta PR: documentación y decisión; no crea URLs ni modifica runtime.

## Veredicto reconciliado

**ALREADY_COVERED para la hipótesis de implementación original. PARTIAL_AUDIT únicamente para medición/extensión si aparece un gap real.**

La formulación inicial proponía construir una arquitectura explícita de “pillar + satellite” porque ese patrón se presentaba como dominante para SEO y citación por IA. La investigación completa de #135 terminó demostrando dos cosas distintas:

1. **La premisa SEO fuerte no estaba sustentada como regla de Google.** Google no documenta un “topical authority score”, un número de satélites requerido ni una receta de pillar pages que produzca por sí misma mejora de ranking o citación IA.
2. **La capacidad editorial legítima ya existía en el repositorio.** `data/topic-collections.json`, `scripts/build-topic-collections.py` y `tests/test-topic-collections.py` ya modelaban, generaban y protegían colecciones/series temáticas con un gate explícito contra hubs artificiales.

Por eso A.1 no autoriza construir otra taxonomía, otro generador de clusters ni nuevas páginas por keyword. Lo que sí puede seguir teniendo valor es **auditar con evidencia de Search Console/Bing, intención y grafo** si una colección existente necesita mejora o si aparece una familia temática nueva suficientemente sustancial.

Esta conclusión reproduce la decisión histórica final de #135: `ALREADY_COVERED`. La etiqueta `PARTIAL_AUDIT` queda reservada a un posible informe/medición posterior, no a la capacidad base.

---

## 1. Por qué esta PR reconstruye #135 directamente

La PR #148 recuperó de #135 únicamente conclusiones duraderas. Eso era deliberado: el test de cierre histórico de #135 decía expresamente que debía proteger las conclusiones consolidadas y **no convertirse en un catálogo de todas las pasadas de investigación**.

Para A.1 esa condensación es insuficiente si queremos conservar cómo se llegó a la decisión, qué se descartó y qué evidencias cambiaron el criterio. Esta PR usa por tanto como corpus histórico el snapshot `8e72321...`, anterior al reset/cierre de #135, y reconstruye la evolución completa de A.1.

Regla de esta reconstrucción:

- se conserva cada **hallazgo único** relativo a A.1;
- cuando varias pasadas repiten exactamente la misma conclusión, se consolida la redacción pero se mantiene la trazabilidad;
- se registran también contradicciones intermedias;
- las pasadas R.* que se revisaron y no modificaron A.1 se identifican como tales, en vez de copiar contenido ajeno;
- #148 puede servir como control de consistencia final, pero **no es la fuente histórica de esta reconstrucción**.

---

## 2. Hipótesis original de #135

El banco original `docs/IDEAS-MEJORA-WEB-2026-08-27.md` formulaba A.1 aproximadamente así:

> Auditoría de topical authority. Organizar `cuaderno/`, `recomendaciones/` y `libros/` en clusters pilar + satélite explícitos; una página pilar por tema, por ejemplo “fantasía juvenil en español”, enlazando artículos satélite. Se presentaba el modelo como dominante en 2026 para SEO clásico y citación por IA.

Ese documento era un **banco de hipótesis encontradas durante investigación**, no un backlog aprobado. Su propia metodología advertía que cada punto debía contrastarse con:

- estado real del repositorio;
- coste y mantenimiento;
- dependencias;
- contexto editorial;
- fuentes fiables;
- riesgo de duplicar capacidades existentes.

Por tanto, la afirmación “modelo dominante en 2026” nunca debe leerse como una verdad técnica consolidada: era parte de la hipótesis a verificar.

### Intuición válida que sí contenía

La hipótesis mezclaba una receta SEO discutible con una necesidad real:

- agrupar contenido relacionado cuando existe una relación editorial auténtica;
- ofrecer un punto de entrada humano a un tema;
- conectar piezas relacionadas mediante enlaces rastreables y útiles;
- evitar artículos aislados;
- facilitar que lectores y crawlers entiendan qué piezas forman un conjunto.

La investigación posterior conservó esa parte y rechazó convertirla en una fórmula de producción de URLs.

---

## 3. Evolución cronológica de la decisión en #135

### 3.1 · Banco original → propuesta de arquitectura explícita

**Estado:** hipótesis sin validar.

Propuesta:

```text
tema
  ↓
pillar page
  ├── satélite 1
  ├── satélite 2
  ├── satélite 3
  └── ...
```

Riesgo todavía no resuelto en esa fase: asumir que el patrón “pillar/satellite” era un requisito o ventaja demostrada para SEO/IA y empezar a crear contenido para completar la estructura.

### 3.2 · Primera revisión 108/108 → `PARTIAL_AUDIT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` rebajó la idea a **PARTIAL_AUDIT**.

La revisión concluyó:

- “topical authority” no es un score oficial de Google ni una feature que se active;
- sí merece analizarse la cobertura de intención/query;
- sí merece revisar canibalización;
- sí merece revisar hubs y enlaces internos;
- **no** merece crear páginas solo para completar clusters.

Fue el primer cambio importante: A.1 dejó de ser “construir clusters” y pasó a “medir primero si existe un problema”.

### 3.3 · Fuentes primarias → se desmonta la lectura de “receta SEO/GEO”

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` fijó la jerarquía de evidencia y varias fuentes relevantes:

1. Google · AI optimization guide  
   https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

   La lectura de #135 fue que no existen hacks especiales de AEO/GEO, `llms.txt`, chunking artificial o una arquitectura secreta para IA que sustituya SEO técnico y contenido útil/original.

2. Google · Link best practices  
   https://developers.google.com/search/docs/crawling-indexing/links-crawlable

   Las páginas importantes deben poder encontrarse mediante enlaces rastreables y contextuales. Eso sí respalda una buena arquitectura interna, pero **no un número mágico de enlaces o satélites**.

3. Google · Spam policies  
   https://developers.google.com/search/docs/essentials/spam-policies

   Crear muchas páginas de intención casi equivalente para ampliar cobertura puede entrar en scaled content/doorway-like behaviour si el valor independiente es insuficiente.

La regla metodológica quedó formulada de forma más general:

```text
fuente primaria > blog/tendencia
estado real del repo > idea genérica
necesidad real > checklist
contenido útil > completar una taxonomía
```

### 3.4 · Cross-check del repositorio → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` localizó una capacidad que las primeras pasadas no habían ponderado correctamente:

- `data/topic-collections.json`;
- `scripts/build-topic-collections.py`;
- `tests/test-topic-collections.py`.

Esto cambió sustancialmente A.1.

La conclusión pasó a **ALREADY_COVERED** porque el proyecto ya tenía un sistema editorial de colecciones/series que resolvía la necesidad legítima mejor que una nueva taxonomía SEO.

Además se encontró un guardrail especialmente relevante: una colección `ready` exige un mínimo de tres piezas reales, mientras una serie con solo dos piezas permanece `draft`. La investigación lo interpretó como una defensa explícita contra fabricar contenido para “completar el cluster”.

### 3.5 · Override por inspección profunda → `ALREADY_COVERED` prevalece

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` declaró expresamente que sus conclusiones prevalecían sobre la matriz base cuando la inspección profunda descubría una capacidad ya existente.

Para A.1 fijó:

**Estado final:** `ALREADY_COVERED`.

**Evidencia:**

- `fantasia-de-portales` ya estaba `ready`;
- `como-construi-noveris` estaba deliberadamente `draft`;
- el builder generaba `/cuaderno/temas/` y `/cuaderno/temas/{slug}/`;
- una colección `ready` necesitaba al menos tres piezas sustanciales;
- el test protegía ese contrato.

**Instrucción histórica para Claude:** no crear otra arquitectura pillar/cluster. Si aparece una familia temática nueva, extender la autoridad existente. No vender topic clusters como factor mágico de ranking; su valor es arquitectura, findability y coherencia editorial.

### 3.6 · Matriz intermedia → oscilación a `PILOTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` introdujo después una inconsistencia histórica: A.1 apareció como **PILOTAR**, con esta intención:

- auditoría de cobertura temática/intención y grafo;
- no imponer `pillar+satellite`;
- identificar queries/URLs reales mediante GSC/Bing antes de actuar.

La parte de auditoría era razonable, pero el status podía interpretarse otra vez como trabajo pendiente de la capacidad base, contradiciendo el override del repo que ya había demostrado que el sistema existía.

Esta contradicción es importante conservarla porque explica por qué una condensación posterior puede dar la impresión de que A.1 “cambió” sin mostrar el camino.

### 3.7 · Blueprints netos → A.1 deja de ser trabajo de construcción

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` declaraba que solo incluía trabajo **neto** después de contrastar las 108 ideas con el repo y citaba expresamente `topic collections` entre las capacidades ya existentes que no debían reconstruirse.

A.1 no recibió un nuevo motor de implementación en ese backlog neto.

Eso confirma la interpretación correcta:

```text
capacidad temática base = existente
medición futura = posible
nueva arquitectura = no aprobada
```

### 3.8 · Autoridad machine-readable final → `ALREADY_COVERED`

`data/web-improvement-decisions-2026-08-28.json` fijó finalmente:

```json
{"id":"A.1","area":"seo","status":"ALREADY_COVERED"}
```

El mismo fichero define la semántica:

> `ALREADY_COVERED` significa mejorar la autoridad existente, nunca duplicarla.

También distingue `PARTIAL_AUDIT`: requiere evidencia de un gap antes de escribir código.

### 3.9 · Autoridad humana final → `ALREADY_COVERED`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` consolidó A.1 así:

- ya existen colecciones/hubs y `build-topic-collections.py`;
- usar GSC/Bing para encontrar huecos reales;
- no imponer `pillar+satellite` como receta.

### 3.10 · Revalidación independiente → la decisión sobrevive al intento de falsación

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` realizó una revisión independiente para intentar falsar las decisiones antes del merge. Para A.1–A.12 mantuvo los estados alcanzados; las correcciones materiales de esa pasada afectaron a otros IDs, no a A.1.

Por tanto, la última revisión independiente de #135 **no reabrió A.1**.

### 3.11 · Test de cierre → se reconoce que la historia se iba a condensar

El commit histórico `8e72321...` añadió `tests/test-pr135-final-authority.py` con una declaración clave:

> el test protege deliberadamente solo conclusiones duraderas y no debe convertirse en catálogo de todas las pasadas históricas.

Además exigía que la antigua “matriz final” quedara marcada como `SUPERSEDED`, `NON-AUTHORITATIVE` o `HISTORICAL` si permanecía en el repo.

Esto resuelve la aparente contradicción de estados: el `PILOTAR` de la matriz intermedia es historia; la autoridad humana + JSON final convergen en `ALREADY_COVERED`.

---

## 4. Qué existía realmente en el sistema de topic collections

### 4.1 · `data/topic-collections.json`

En el snapshot histórico de #135 y también en el `main` revisado durante esta reconstrucción existen dos casos que explican muy bien la intención del sistema.

#### `fantasia-de-portales`

```text
status = ready
mode = collection
items = 3
```

Piezas:

1. `/cuaderno/que-es-el-portal-fantasy/`
2. `/cuaderno/portal-fantasy-vs-fantasia-epica/`
3. `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`

La propia introducción de la colección dice que son tres piezas independientes que responden preguntas diferentes sobre el mismo subgénero y pueden leerse en cualquier orden.

Esto es una agrupación editorial legítima: cada URL tiene una intención propia y el hub explica la relación.

#### `como-construi-noveris`

```text
status = draft
mode = series
items = 2
```

Piezas:

1. `/cuaderno/sistema-de-magia-noveris/`
2. `/cuaderno/worldbuilding-noveris-ciudad-magica/`

La propia autoridad de datos dice que todavía son solo dos entregas y que **no se fuerza una tercera únicamente para alcanzar el mínimo del hub**.

Este caso es especialmente importante para A.1 porque demuestra que la solución ya implementada contiene el guardrail que la investigación quería preservar: contenido primero, estructura después.

### 4.2 · `scripts/build-topic-collections.py`

El builder no reescribe las URLs de los artículos ni crea satélites. Su función es crear índices editoriales para colecciones `ready`:

```text
/cuaderno/temas/
/cuaderno/temas/{slug}/
```

Contratos relevantes:

- `status`: `draft | ready`;
- `mode`: `collection | series`;
- URLs internas limpias;
- no URLs externas como miembros;
- no URLs duplicadas;
- campos editoriales obligatorios;
- fecha `updated` válida;
- miembros existentes;
- miembros no `noindex`;
- canonical esperado presente;
- una colección `ready` con menos de tres piezas falla.

La validación histórica expresa literalmente la intención:

```text
status=ready exige al menos 3 piezas; ...
Déjala en draft hasta que exista una tercera pieza real.
```

### 4.3 · `tests/test-topic-collections.py`

La suite histórica no era un test superficial. Cubría:

- colección `ready` con 2 items → FAIL;
- URL externa → FAIL;
- URL duplicada → FAIL;
- colección válida de 3 piezas → genera hub;
- serie válida → mantiene el orden declarado;
- colección libre → `<ul>`;
- serie ordenada → `<ol>`;
- `--check` → detecta salida desactualizada;
- HTML generado → H1 + links `<a href>` rastreables;
- miembro `noindex` → FAIL;
- repo real → exactamente una colección publicada en ese corte (`fantasia-de-portales`).

Por tanto A.1 no partía de una agrupación manual frágil: ya había datos + builder + regresión.

---

## 5. Qué parte de la idea original quedó descartada

La investigación de #135 descarta o desautoriza estas interpretaciones de A.1:

### 5.1 · “Pillar page por keyword”

No crear una página central solo porque exista una keyword o una herramienta SEO la denomine “pillar opportunity”.

### 5.2 · “Hay que completar el cluster”

No producir un tercer artículo sin necesidad editorial para que una colección alcance un número arbitrario. El propio builder adopta el comportamiento contrario: dejarla en `draft`.

### 5.3 · “Topical authority score” como métrica Google

No tratar puntuaciones propietarias de herramientas como un dato interno de Google ni como Definition of Done.

### 5.4 · “Pillar + satellites es el modelo dominante para citación IA”

La investigación no encontró una exigencia oficial de Google/IA que justifique esa afirmación como regla de producto.

### 5.5 · Arquitectura paralela

No crear:

- otro JSON de clusters;
- otra taxonomía visible;
- otro builder de hubs;
- otra familia de URLs que compita con `/cuaderno/temas/`;
- una navegación temática separada del sistema editorial existente.

### 5.6 · KPI de número de páginas/enlaces

No imponer:

- N satélites por tema;
- N enlaces internos por artículo;
- densidad de keyword;
- longitud mínima por hub;
- score de “cobertura” sin intención humana.

### 5.7 · Scaled/doorway content

No generar variantes casi idénticas del tipo:

```text
portal-fantasy-para-X
portal-fantasy-para-Y
portal-fantasy-para-Z
```

si no existe una intención distinta y contenido propio suficiente.

---

## 6. Qué sí sobrevivió de A.1

### 6.1 · Colecciones editoriales reales

Cuando tres o más piezas sustanciales responden preguntas diferentes sobre un mismo territorio, un hub puede mejorar:

- orientación del lector;
- findability;
- navegación;
- contexto entre contenidos;
- rastreo mediante enlaces HTML reales.

### 6.2 · Series reales

Cuando el orden importa, el modo `series` conserva orden explícito. No convertir una colección libre en serie solo por SEO.

### 6.3 · GSC/Bing antes de fabricar una nueva URL

Una colección o nueva pieza merece estudio si existe evidencia como:

- queries relacionadas con intención distinta;
- varias URLs compitiendo/confundiendo una misma intención;
- piezas útiles dispersas que el lector necesita explorar conjuntamente;
- una tarea humana que un índice resolvería;
- contenido first-party suficiente para que el hub tenga valor aunque Google no existiera.

### 6.4 · Enlazado contextual

Los miembros y hubs deben poder descubrirse mediante anchors HTML útiles. Eso sí está respaldado por las guías de Google sobre enlaces rastreables.

### 6.5 · Auditoría sin convertir el informe en otra fuente de verdad

Puede ser útil un informe de cobertura, pero sus datos deben derivarse de autoridades existentes. Un report no debe convertirse en el lugar donde se editan manualmente temas, URLs o relaciones.

---

## 7. Diferencia entre A.1, A.2 y A.3

Esta separación quedó implícita en #135 y conviene hacerla explícita para no duplicar trabajo entre PRs.

### A.1 · colección temática

Pregunta:

> ¿Existen piezas distintas sobre un tema común que merecen un índice editorial?

Autoridad principal existente:

- `data/topic-collections.json`;
- `scripts/build-topic-collections.py`.

### A.2 · hub canónico de una obra/universo

Pregunta:

> ¿Cuál es la URL central de Samuel, Manecillas o Noveris y cómo se conecta su ecosistema?

No crear un nuevo “pillar hub” para resolver A.1 si esa función pertenece al hub canónico de A.2.

### A.3 · grafo interno

Pregunta:

> ¿Hay URLs importantes huérfanas, enlaces rotos o relaciones de descubrimiento insuficientes?

Autoridad existente:

- `scripts/check-internal-graph.py`.

A.1 puede consumir información del grafo, pero no debe reimplementar A.3.

---

## 8. Estado actual del repo comprobado para esta reconstrucción

La inspección actual confirma que `data/topic-collections.json` conserva la misma arquitectura sustancial que encontró #135:

- `fantasia-de-portales` continúa `ready` con sus tres piezas;
- `como-construi-noveris` continúa `draft` con dos piezas y la explicación de que no se fuerza una tercera.

Por tanto no ha aparecido una evidencia nueva que invalide el `ALREADY_COVERED` histórico.

Además siguen siendo relevantes las autoridades transversales ya documentadas en esta PR:

- `data/content-registry.json` como inventario canónico general;
- `scripts/check-internal-graph.py` para grafo/huérfanas/canonicals;
- `scripts/check-global-discoverability.py` para reconciliación de superficies;
- hubs de `/libros/`, Samuel, Manecillas y Noveris;
- `/recomendaciones/` como familia editorial distinta.

Importante: **no migrar `topic-collections.json` a `content-registry.json` solo por unificar datos**. Son autoridades con funciones distintas. Si alguna vez se demuestra solapamiento dañino, eso requerirá una decisión arquitectónica separada.

---

## 9. Evidencia primaria actual que conserva la decisión

### Google · helpful, reliable, people-first content

https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Lectura aplicable:

- propósito/foco claro del sitio;
- experiencia/conocimiento real;
- contenido útil para personas;
- no producir volumen únicamente para captar búsquedas.

No documenta una cuota de páginas pilar/satélite.

### Google · link best practices

https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Lectura aplicable:

- las páginas importantes deben recibir enlaces rastreables;
- anchor text/contexto ayudan a entender destinos;
- no existe un número mágico de enlaces.

### Google · spam policies

https://developers.google.com/search/docs/essentials/spam-policies

Lectura aplicable:

- scaled content/doorway abuse impide interpretar A.1 como permiso para generar muchas variaciones de intención débil.

### Google · AI optimization guide

https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

Lectura de #135 que se conserva:

- no existe una arquitectura secreta de “GEO clusters” que sustituya el trabajo de contenido/SEO base;
- no reformatear el sitio entero para una teoría de citación IA sin evidencia.

---

## 10. Auditoría opcional si aparece una necesidad real

A.1 no necesita ahora un nuevo sistema. Si GSC/Bing/editorial detectan un gap, el trabajo correcto sería **auditar antes de modificar**.

### Preguntas de auditoría

1. ¿Existe una intención concreta que varias piezas resuelven de forma complementaria?
2. ¿Ya hay un hub adecuado?
3. ¿Las piezas son suficientemente distintas y sustanciales?
4. ¿Hay canibalización o simplemente cobertura complementaria?
5. ¿Los miembros enlazan al hub cuando ayuda al lector?
6. ¿El hub enlaza a miembros válidos/canónicos?
7. ¿La colección debe ser libre (`collection`) u ordenada (`series`)?
8. ¿Existe una pieza nueva por valor editorial propio o solo para “llegar a tres”?

### Opción de reporting mínima

Si existe un consumidor real para salida machine-readable, preferir ampliar capacidades existentes antes de otro crawler. Por ejemplo:

```bash
python scripts/check-internal-graph.py --report --json artifacts/internal-graph.json
```

Un report útil podría combinar —sin convertirse en fuente editable—:

```json
{
  "topic": "fantasia-de-portales",
  "hub": "/cuaderno/temas/fantasia-de-portales/",
  "mode": "collection",
  "status": "ready",
  "members": 3,
  "inboundToHub": 0,
  "memberInboundCounts": {}
}
```

Solo implementar esa salida si Claude/CI/editorial van a consumirla. No crear `report-topic-coverage.py` únicamente para poder decir que A.1 tiene un script propio.

---

## 11. Tests que protegen la decisión correcta

Capacidad base ya existente:

- `tests/test-topic-collections.py` debe seguir verde cuando se toque el builder/data;
- colección `ready` con menos de tres piezas debe seguir fallando salvo decisión editorial explícita de cambiar el contrato;
- miembros externos/duplicados/noindex deben seguir rechazándose;
- `--check` debe detectar drift;
- miembros deben existir y conservar canonical válido;
- hubs generados deben usar anchors rastreables.

Integración transversal:

- `scripts/check-internal-graph.py` sin huérfanas/roturas nuevas;
- `scripts/check-global-discoverability.py` sin drift de inventario público;
- sitemap/registry/canonical siguen sincronizados cuando se añade una URL nueva legítima.

No añadir un test del tipo:

```text
cada tema debe tener >= N artículos en todo el sitio
```

El mínimo de tres pertenece al contrato concreto del builder para **publicar un hub**, no es una regla de ranking ni una cuota editorial global.

---

## 12. Coste / beneficio reconstruido

### Crear ahora otra arquitectura de clusters

- beneficio: **negativo / redundante**;
- coste: alto;
- riesgo: taxonomías paralelas, URLs duplicadas, canibalización, contenido artificial y mantenimiento duplicado.

### Mantener la capacidad existente

- beneficio: alto para organización/findability cuando hay contenido real;
- coste: ya asumido;
- riesgo: bajo porque existen datos, validación y tests.

### Añadir un informe de auditoría si aparece un consumidor real

- beneficio: medio;
- coste: bajo si reutiliza grafo/registry/topic collections;
- riesgo: bajo si permanece derivado/read-only;
- decisión: `PARTIAL_AUDIT` / condicional a una pregunta concreta.

### Crear páginas para “cubrir topical authority”

- beneficio SEO directo: no demostrado;
- coste editorial: medio/alto;
- riesgo de thin/scaled/canibalización: real;
- decisión: no autorizado.

---

## 13. Definition of Done de A.1

### Ya demostrado

- [x] la hipótesis original de pillar/satellite fue recuperada;
- [x] se preservó la transición `hipótesis → PARTIAL_AUDIT → ALREADY_COVERED`;
- [x] se documentó la contradicción intermedia `PILOTAR` y su resolución posterior;
- [x] se localizaron las autoridades reales de topic collections;
- [x] existe una colección publicada con tres piezas distintas;
- [x] existe una serie deliberadamente `draft` que demuestra el anti-filler gate;
- [x] builder y tests protegen la capacidad;
- [x] la decisión machine-readable final de #135 fue `ALREADY_COVERED`;
- [x] la autoridad humana final de #135 fue `ALREADY_COVERED`;
- [x] la revalidación independiente no la reabrió;
- [x] el estado actual de `topic-collections.json` sigue compatible con esa conclusión.

### Solo si aparece nueva evidencia

- [ ] recoger la query/intención/hallazgo que justifica revisar una familia;
- [ ] comprobar primero si encaja en una colección/hub ya existente;
- [ ] no publicar una colección antes de que existan piezas reales suficientes;
- [ ] no crear otra fuente de verdad;
- [ ] si se añade reporting, demostrar consumidor y test de paridad;
- [ ] si se crea una URL nueva, pasar registry/sitemap/canonical/internal-graph/discoverability QA.

---

## 14. Trazabilidad del corpus histórico de #135 revisado para A.1

### Contienen evidencia o decisión específica de A.1

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — primer `PARTIAL_AUDIT`.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — fuentes/metodología primaria.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — descubrimiento del sistema existente y cambio a `ALREADY_COVERED`.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — override `ALREADY_COVERED` que prevalece sobre matrices anteriores.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — oscilación histórica a `PILOTAR`; posteriormente queda como historia/superseded.
- `data/web-improvement-decisions-2026-08-28.json` — autoridad machine-readable final: `ALREADY_COVERED`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final: `ALREADY_COVERED`.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — intento de falsación; A.1 se mantiene.
- `docs/PR135-MERGE-READINESS-2026-08-28.md` — explica por qué las pasadas históricas iban a consolidarse/podarse y Git conservaría la arqueología.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — topic collections excluidas del backlog de construcción por existir ya.
- `data/topic-collections.json` — evidencia de producto.
- `scripts/build-topic-collections.py` — implementación real.
- `tests/test-topic-collections.py` — contrato/regresión.
- `tests/test-pr135-final-authority.py` en `8e72321...` — declara deliberadamente que la autoridad final no preservaría todas las pasadas.

### Revisados y sin cambio específico adicional para A.1

Se revisaron también las pasadas posteriores conservadas en el snapshot de #135, entre ellas:

- cuarta pasada R.1–R.8;
- quinta pasada R.9–R.13;
- sexta pasada y su revisión crítica/blueprints;
- séptima pasada R.30–R.34;
- octava pasada R.35–R.49;
- novena pasada R.50–R.54;
- décima pasada R.55–R.57;
- undécima pasada R.58–R.59;
- duodécima pasada TTS;
- decimotercera pasada R.61–R.70;
- decimocuarta pasada R.71–R.80;
- decimoquinta pasada R.81–R.88;
- `IDEAS-MEJORA-WEB-CASOS-EVIDENCIA-Y-LIMITES-2026-08-28.md`;
- `IDEAS-MEJORA-WEB-FUENTES-ADICIONALES-2026-08-28.md`;
- `IDEAS-MEJORA-WEB-REPOS-EVALUADOS-2026-08-28.md`.

Esas pasadas añadieron o corrigieron otras capacidades, pero no aportaron un hallazgo único que cambiase A.1. No se copian aquí para evitar mezclar otras ideas con esta PR.

---

## 15. Recomendación de merge

**MERGE como reconstrucción completa + `ALREADY_COVERED` de la capacidad base.**

A.1 queda cerrada en los siguientes términos:

```text
NO construir “topical authority”.
SÍ conservar y mejorar las colecciones editoriales existentes.
NO crear páginas para completar clusters.
SÍ usar evidencia de GSC/Bing/lector antes de abrir una nueva colección o URL.
NO duplicar topic-collections, hubs ni el grafo interno.
SÍ auditar solo cuando exista una pregunta concreta.
```

La próxima implementación relacionada con A.1 solo debe abrirse ante un gap reproducible de la autoridad existente; no porque una checklist SEO vuelva a recomendar pillar pages.