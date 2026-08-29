# A.6 · Breadcrumbs visibles + `BreadcrumbList`

Fecha de reconstrucción: 2026-08-29  
Idea original: añadir breadcrumbs visibles y schema `BreadcrumbList` a rutas profundas si faltan.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico reconstruido: `PARTIAL_AUDIT`.

> **Nota de autoridad:** este documento conserva la arqueología y el blueprint histórico de #135. La implementación y semántica de producción actuales viven en `A06-PRODUCTION-REVALIDATION-2026-08-29.md` y `scripts/check-breadcrumb-parity.py`. La documentación oficial vigente de Google permite omitir Home y/o la página actual del `BreadcrumbList`, por lo que cualquier frase histórica que exija siempre “último item = canonical” debe leerse como blueprint previo, no como regla de producción.

## Veredicto histórico reconciliado

**PARTIAL_AUDIT. YA EXISTE EN SUPERFICIES IMPORTANTES; MEDIR COBERTURA Y PARIDAD ANTES DE MODIFICAR HTML.**

Google mantiene soporte para `BreadcrumbList`, pero #135 encontró que la web ya lo usa en rutas importantes. La mejora neta era auditar qué familias realmente necesitan breadcrumb, comprobar visible ↔ JSON-LD ↔ canonical/registry y corregir únicamente gaps reales.

## 1. Regla de reconstrucción

Esta PR usa directamente el corpus histórico de #135. Conserva la oscilación relevante `PARTIAL_AUDIT` → `IMPLEMENTAR/VERIFICAR` → `PARTIAL_AUDIT` final, el estado del repo, el blueprint W4, fuentes, tests y límites.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía:

> si no existen ya en todas las rutas profundas (`libros/`, `cuaderno/`, `recomendaciones/`), añadir breadcrumbs visibles + `BreadcrumbList` para navegación/rich snippets.

La condición “si no existe ya” terminó siendo decisiva: sí existía en varias familias.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `PARTIAL_AUDIT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` concluyó:

- Google seguía soportando `BreadcrumbList`;
- varias rutas ya podían tenerlo;
- la tarea correcta era auditar cobertura y paridad visible ↔ JSON-LD;
- derivar de navegación/registry cuando fuera posible.

No autorizó un rollout ciego.

### 3.2 · Fuente primaria

Google Search Central · Breadcrumb structured data  
https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

Schema.org · BreadcrumbList  
https://schema.org/BreadcrumbList

Puntos relevantes preservados por #135:

- la cadena representa una ruta típica/útil, no necesariamente la estructura literal de carpetas;
- `ListItem` debe tener orden/posición y labels adecuados;
- structured data debe representar contenido real;
- schema no sustituye navegación útil ni obliga a meter una barra visual en toda URL.

### 3.3 · Repo cross-check → capacidad parcial ya existente

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` encontró breadcrumbs visibles + `BreadcrumbList` en varias rutas importantes.

Conclusión:

> la tarea útil no es “añadir breadcrumbs”, sino medir cobertura/paridad por familia y corregir solo gaps.

Estado: `PARTIAL_AUDIT`.

### 3.4 · Matriz intermedia → `IMPLEMENTAR/VERIFICAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` resumió A.6 como:

> breadcrumb visible + `BreadcrumbList` en rutas profundas donde falte, generado desde autoridad de navegación y con test de paridad.

El verbo `IMPLEMENTAR` estaba condicionado por `donde falte`; no significaba que #135 hubiese demostrado falta sitewide.

La autoridad final volvió a `PARTIAL_AUDIT`, que es más precisa: primero inventario, luego cambios.

### 3.5 · Blueprint neto W4 → especificación técnica recuperada

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` dejó un blueprint específico para A.6.

Nombre propuesto históricamente:

`scripts/check-breadcrumb-parity.py`

W4 proponía:

1. seleccionar rutas profundas públicas/indexables;
2. detectar breadcrumb visible solo si la plantilla/familia lo pretende;
3. extraer `BreadcrumbList`;
4. comparar ordered URLs/names;
5. comprobar relación con la URL canónica;
6. reportar:
   - `missing-visible`;
   - `missing-jsonld`;
   - `order-drift`;
   - `url-drift`.

Pseudocódigo histórico:

```python
for route in public_indexable_routes:
    html = read(route.sourceFile)
    visible = parse_visible_breadcrumb(html)
    jsonld = find_breadcrumb_list(html)
    if not visible and not jsonld:
        continue
    assert [x.url for x in visible] == [x.url for x in jsonld]
    # La implementación final reevalúa la relación con canonical conforme
    # a la documentación Google vigente; current no es obligatorio.
```

W4 también prohíbe:

- exigir breadcrumb a Home;
- crear una segunda autoridad manual si ya lo genera un builder;
- mezclar en esta PR `Person @id`, cubierto por otro checker.

### 3.6 · Autoridad machine-readable final

`data/web-improvement-decisions-2026-08-28.json`:

```json
{"id":"A.6","area":"seo","status":"PARTIAL_AUDIT"}
```

Semántica de #135: un `PARTIAL_AUDIT` necesitaba evidencia del gap antes de código.

### 3.7 · Autoridad humana final

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md`:

> inventariar Breadcrumb visible + `BreadcrumbList` en rutas profundas; completar solo donde falte y derivar desde navegación canónica.

### 3.8 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` mantuvo A.6 y volvió a citar la documentación oficial de Breadcrumb structured data. No encontró razón para convertir la auditoría en rollout general.

Secuencia:

```text
hipótesis: añadir si falta
→ PARTIAL_AUDIT
→ repo demuestra cobertura parcial
→ matriz: IMPLEMENTAR/VERIFICAR solo gaps
→ blueprint W4 de paridad
→ final: PARTIAL_AUDIT
→ revalidación mantiene
→ 29/08: gap de QA confirmado e implementado en #155
```

## 4. Evidencia del repo preservada

### Samuel

`/libros/samuel-entre-mundos/` contiene `BreadcrumbList`:

```text
Inicio → Libros → Samuel entre mundos
```

pero no una barra de breadcrumb visual dedicada. La implementación final no lo trata como fallo automático porque la UI ya ofrece navegación contextual y Google no obliga a duplicarla.

### Las manecillas del recuerdo

`/las-manecillas-del-recuerdo/` contiene structured breadcrumb dentro de su grafo JSON-LD.

### Topic collections

El trabajo histórico de topic collections preservó `BreadcrumbList` y breadcrumb visible en `/cuaderno/temas/fantasia-de-portales/`.

### Recomendaciones

`/recomendaciones/portal-fantasy-espanol/` mantiene breadcrumb visible + `BreadcrumbList`.

Por tanto A.6 nunca debe redactarse como “la web no tiene breadcrumbs”.

## 5. Preguntas que resolvió el audit de producción

1. ¿qué páginas ya tienen breadcrumb visible?;
2. ¿cuáles publican `BreadcrumbList`?;
3. ¿visible y JSON-LD expresan los mismos destinos intermedios cuando ambos existen?;
4. ¿las URLs son canónicas, same-origin y públicas?;
5. ¿el current page aparece en una posición imposible?;
6. ¿hay varias rutas estructuradas válidas?;
7. ¿un breadcrumb visual adicional sería redundante con navegación contextual existente?

## 6. Fuente de verdad

La jerarquía ya vive en autoridades como `data/content-registry.json` (`parentId`, `hubId`, labels, aliases) y navegación/builders existentes.

**No crear `data/breadcrumbs.json`.**

La estructura de carpetas tampoco es una autoridad semántica suficiente.

## 7. Implementación materializada

El blueprint se convirtió en:

```bash
python scripts/check-breadcrumb-parity.py
python scripts/check-breadcrumb-parity.py --json artifacts/breadcrumbs.json
```

La implementación final:

- inventaría rutas públicas/indexables HTML del registry;
- detecta visible + structured;
- valida posiciones y URLs;
- compara rutas intermedias de forma semántica;
- acepta múltiples trails;
- acepta structured sin barra visual dedicada;
- acepta omitir Home/current en structured data;
- usa aliases del registry para labels equivalentes;
- bloquea drift objetivo, no preferencias de diseño.

El JSON opcional es evidencia de auditoría, no una segunda fuente de verdad.

## 8. Qué NO hacer

- generar breadcrumbs por slugs/carpetas sin autoridad editorial;
- añadirlos a Home/404 para “tener schema”;
- duplicar `section-context` sin necesidad UX;
- exponer noindex/gated en cadenas públicas sin sentido;
- keyword stuffing en labels;
- inventar páginas para completar una cadena;
- crear un segundo registro manual de breadcrumbs;
- mezclar esta tarea con Person/Book entity IDs;
- exigir que toda página con `BreadcrumbList` renderice una segunda fila visible;
- exigir Home/current en structured data contra la documentación vigente.

## 9. Tests materializados

`tests/test-breadcrumb-parity.py` cubre:

- visible + structured correcto;
- JSON-LD-only válido;
- visible-only sin structured;
- omisión válida Home/current;
- aliases;
- order/url drift;
- URLs externas;
- current en posición intermedia;
- posiciones no consecutivas;
- múltiples trails;
- JSON-LD breadcrumb malformado;
- páginas sin contrato;
- enlaces relativos ambiguos.

## 10. Definition of Done histórica vs actual

### Historia recuperada

- [x] hipótesis original;
- [x] primera revisión;
- [x] repo cross-check;
- [x] matriz intermedia;
- [x] blueprint W4;
- [x] autoridad final humana/JSON;
- [x] revalidación independiente.

### Producción 29/08/2026

- [x] gap real de QA demostrado;
- [x] documentación oficial actual revalidada;
- [x] checker W4 implementado sin segundo registry;
- [x] semántica actual corrige el supuesto histórico de current obligatorio;
- [x] tests de regresión;
- [x] integración CI;
- [x] no rollout visual indiscriminado.

**Conclusión:** #135 hizo bien en dejar A.6 como `PARTIAL_AUDIT`. La revisión de producción encontró finalmente el gap concreto: faltaba un guardrail reproducible de paridad. Ese gap se implementa en #155 sin convertir breadcrumbs en decoración SEO sitewide.