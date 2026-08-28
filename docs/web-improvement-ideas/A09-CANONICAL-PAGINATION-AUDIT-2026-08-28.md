# A.9 · Auditoría de canonicals y paginación

Fecha de reconstrucción: 2026-08-29  
Idea original: confirmar canonicals correctos en páginas con parámetros/query views y paginación, especialmente posibles filtros de Herramientas/Recomendaciones.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: decisión `ALREADY_COVERED`; mantiene guardrails para futuras vistas.

## Veredicto reconciliado

**ALREADY_COVERED para la arquitectura actual. MANTENER LOS CONTRATOS EXISTENTES Y DEFINIR POLÍTICA SOLO CUANDO APAREZCAN VISTAS REALES CON PARÁMETROS/PAGINACIÓN.**

#135 empezó con `PARTIAL_AUDIT` porque canonicals ya existían pero no se había comprobado toda la superficie. La inspección profunda encontró que `scripts/check-internal-graph.py`, browser QA y el contrato registry/sitemap ya cubrían la parte material, y que el sitio estático no tenía una familia pública de filtros/paginación indexable que justificase infraestructura nueva.

## 1. Regla de reconstrucción

Esta PR recupera A.9 directamente del snapshot histórico de #135. Conserva:

- hipótesis original sobre query/filter/pagination;
- `PARTIAL_AUDIT` inicial;
- estado intermedio `YA_CUBIERTO/MANTENER`;
- evidencia de checker/browser QA;
- override profundo a `ALREADY_COVERED`;
- política de futuras vistas;
- autoridad humana/JSON final;
- revalidación independiente.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía:

> confirmar que toda página con parámetros de query o vistas alternativas declara `rel=canonical` correcto, especialmente si herramientas o recomendaciones generan filtros.

La formulación era preventiva: no afirmaba que esas variantes existieran realmente.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `PARTIAL_AUDIT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` reconoció que las canonicals ya existían y propuso:

- confirmar self-canonical HTTPS;
- coherencia con sitemap;
- evitar query variants indexables accidentalmente;
- fortalecer un checker periódico.

Aún no se había probado que el repo ya cubriese la mayor parte.

### 3.2 · Fuente primaria

Google Search Central · Canonicalization  
https://developers.google.com/search/docs/crawling-indexing/canonicalization

Google · Consolidate duplicate URLs  
https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

Google · Canonicalization troubleshooting  
https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting

Conclusiones aplicables:

- parámetros, filtros, ordenación, host/protocolo pueden crear variantes;
- redirects, `rel=canonical`, sitemap e internal linking deben ser coherentes;
- canonical no sustituye `noindex` cuando la intención es excluir una superficie;
- no canonicalizar contenido realmente distinto solo para “concentrar SEO”.

### 3.3 · Matriz intermedia → `YA_CUBIERTO/MANTENER`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` ya había reducido la tarea:

> canonical/indexability ya tiene QA fuerte. Añadir únicamente casos reales con parámetros si aparecen; no crear sistema de paginación inexistente.

### 3.4 · Repo cross-check → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` encontró:

- `scripts/check-internal-graph.py` controla canonicals ausentes y colisiones;
- browser QA verifica canonical exacto en rutas críticas;
- el sitio estático no expone actualmente paginación indexable por query.

Decisión:

> `ALREADY_COVERED` mientras no aparezca una nueva familia de filtros/paginación pública.

### 3.5 · Override profundo → no crear infraestructura hipotética

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` formaliza:

- checker actual ya audita canonicals;
- browser QA protege rutas representativas;
- no existe hoy paginación indexable por query que necesite política propia;
- si aparece una nueva vista filtrada/query indexable, definir entonces canonical/noindex;
- **no construir infraestructura de paginación hipotética**.

### 3.6 · Blueprints netos → A.9 no es una nueva implementación

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` solo describe trabajo neto pendiente. Canonicals/grafo existentes no aparecen como algo que reconstruir.

### 3.7 · Autoridad machine-readable final → `ALREADY_COVERED`

`data/web-improvement-decisions-2026-08-28.json`:

```json
{"id":"A.9","area":"seo","status":"ALREADY_COVERED"}
```

### 3.8 · Autoridad humana final

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md`:

> Canonical/indexability ya tiene QA fuerte. Añadir casos de query/paginación solo si aparecen realmente.

### 3.9 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` mantuvo A.9 sin correcciones.

Secuencia:

```text
hipótesis preventiva sobre parámetros
→ PARTIAL_AUDIT
→ matriz YA_CUBIERTO/MANTENER
→ repo demuestra checker + QA + ausencia de paginación pública
→ override ALREADY_COVERED
→ final JSON/humano ALREADY_COVERED
→ revalidación mantiene
```

## 4. Estado real del repo preservado

### `scripts/check-internal-graph.py`

Ya cubre:

- missing canonical en páginas indexables;
- canonical collisions;
- resolución de enlaces contra URL canónica.

### `scripts/check-global-discoverability.py`

El contrato transversal histórico verifica:

- canonical/indexable ↔ sitemap ↔ registry;
- exclusión de superficies internas/gated;
- registry como autoridad del inventario público.

### Browser QA

Rutas críticas verifican canonical exacto, complementando los checkers estáticos.

### Operación Search Console

La auditoría histórica clasificó variantes `http://` y `www` como redirects correctos hacia la canonical HTTPS, no como URLs que deban indexarse por separado.

### Arquitectura

No se encontró:

- `/cuaderno/?page=2` indexable;
- paginación clásica pública;
- combinaciones facetadas indexables de herramientas/recomendaciones.

Las rutas editoriales relevantes usan URLs canónicas explícitas.

## 5. Qué significa `ALREADY_COVERED`

No significa “cualquier query futura estará bien automáticamente”. Significa:

```text
hoy no hay una superficie problemática que construir/arreglar
autoridad actual ya protege canonicals
futuro filtro/paginación debe traer su propio contrato SEO
```

## 6. Política para futuras vistas

### Caso A · estado de UI

Ejemplo:

```text
/herramientas/?categoria=manuscrito
```

Si solo filtra el mismo corpus:

- base sigue siendo la superficie indexable principal;
- evitar enlaces crawlables a combinaciones infinitas;
- query/hash/history pueden conservar estado UI;
- si Google puede rastrear variantes HTML, decidir canonical/noindex explícitamente.

### Caso B · intención editorial independiente

Si una combinación merece posicionarse por valor propio, preferir una URL editorial canónica real, por ejemplo:

```text
/recomendaciones/portal-fantasy-espanol/
```

No dejarla como parámetro improvisado.

### Caso C · paginación real

Si el corpus crece y necesita páginas 2+:

- navegación mediante `<a href>` real;
- cada página con canonical coherente con su contenido;
- no canonicalizar todas a página 1 si contienen items distintos;
- evitar combinaciones infinitas de filter/order;
- mantener ruta humana clara.

Google no usa `rel=prev/next` como señal de indexación; no reintroducirlo como requisito SEO.

## 7. Guardrails opcionales, no backlog obligatorio

### Variantes conocidas

Puede mantenerse una tabla de invariantes HTTP/host en smoke si no existe ya:

```json
[
  {
    "url": "http://davidportodiaz.com/",
    "expect": "redirect",
    "canonical": "https://davidportodiaz.com/"
  },
  {
    "url": "https://www.davidportodiaz.com/",
    "expect": "redirect",
    "canonical": "https://davidportodiaz.com/"
  }
]
```

### Query URLs nuevas

Un guardrail read-only puede reportar internal hrefs con `?` para revisión:

```python
if "?" in internal_href:
    findings.append({"type": "query-url-review", "href": href, "source": source})
```

No debe fallar automáticamente: formularios, Pagefind o parámetros funcionales pueden ser legítimos.

## 8. Qué NO hacer

- `<link rel=canonical>` duplicado;
- apuntar todos los filtros a la base sin entender contenido;
- canonicalizar páginas distintas solo para “concentrar SEO”;
- parámetros crawlables infinitos;
- crear paginación sin volumen;
- bloquear por robots una URL que necesita ser rastreada para procesar canonical/noindex;
- tratar “Google chose different canonical” como error automático sin inspección;
- crear nuevo checker que replique internal-graph/discoverability;
- implementar A.9 por checklist sin una vista nueva.

## 9. Tests

- cada página indexable del registry tiene canonical válida;
- canonical indexable y sitemap coherentes salvo excepción explícita;
- no dos indexables reclamando misma canonical sin contrato;
- HTTP/www terminan en canonical HTTPS;
- nuevas query URLs internas se reportan/revisan si se adopta ese guardrail;
- futura paginación obtiene fixtures de links/canonical por página;
- canonical no se usa para sustituir redirect/noindex correcto.

## 10. Coste / beneficio

Nueva implementación grande hoy: bajo valor.  
Mantener contratos existentes: alto valor.  
Guardrail futuro al introducir filtros/paginación: bajo coste / alto valor preventivo.

## 11. Definition of Done

### Historia ya recuperada

- [x] hipótesis original preservada;
- [x] `PARTIAL_AUDIT` inicial preservado;
- [x] `YA_CUBIERTO/MANTENER` intermedio preservado;
- [x] checker/browser QA encontrados;
- [x] ausencia de paginación indexable registrada;
- [x] override profundo `ALREADY_COVERED` preservado;
- [x] ausencia del backlog neto explicada;
- [x] autoridad JSON final = `ALREADY_COVERED`;
- [x] autoridad humana final preservada;
- [x] revalidación independiente mantuvo A.9.

### Futuras features

- [ ] definir política canonical/noindex antes de publicar nueva familia de parámetros;
- [ ] mantener una única autoridad de URLs;
- [ ] añadir fixtures concretos de la nueva superficie;
- [ ] no crear infraestructura hasta que exista necesidad real.

## 12. Trazabilidad del corpus histórico de #135 revisado para A.9

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `PARTIAL_AUDIT`.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — canonicalization oficial.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `YA_CUBIERTO/MANTENER`.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — checker + ausencia de paginación.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — override final y trigger futuro.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no nueva construcción neta.
- `data/web-improvement-decisions-2026-08-28.json` — estado final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — revalidación.

### Revisados sin cambio específico adicional

Overrides generales no aplicables, cuarta a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch fueron revisados; no cambian A.9.

## 13. Recomendación de merge

**MERGE como reconstrucción completa + `ALREADY_COVERED`.**

No genera trabajo productivo hoy; deja a Clara/Claude el contrato exacto para no introducir deuda canonical cuando aparezcan filtros/paginación reales.