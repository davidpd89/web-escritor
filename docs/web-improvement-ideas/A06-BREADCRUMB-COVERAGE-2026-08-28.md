# A.6 · Breadcrumbs visibles + `BreadcrumbList`

Fecha de reconstrucción: 2026-08-29  
Idea original: añadir breadcrumbs visibles y schema `BreadcrumbList` a rutas profundas si faltan.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: auditoría/plan; no añade breadcrumbs indiscriminadamente.

## Veredicto reconciliado

**PARTIAL_AUDIT. YA EXISTE EN SUPERFICIES IMPORTANTES; MEDIR COBERTURA Y PARIDAD ANTES DE MODIFICAR HTML.**

Google mantiene soporte para `BreadcrumbList`, pero #135 encontró que la web ya lo usa en rutas importantes. La mejora neta es auditar qué familias realmente necesitan breadcrumb, comprobar visible ↔ JSON-LD ↔ canonical/registry y corregir únicamente gaps reales.

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

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` sí dejó un blueprint específico para A.6.

Nombre propuesto históricamente:

`scripts/check-breadcrumb-parity.py`

La versión corta de esta PR había sugerido `check-breadcrumb-coverage.py`; ambos nombres describen el mismo objetivo, pero **si se implementa debe preferirse/reevaluarse el nombre histórico W4 y evitar dos scripts**.

W4 exige:

1. seleccionar rutas profundas públicas/indexables;
2. detectar breadcrumb visible solo si la plantilla/familia lo pretende;
3. extraer `BreadcrumbList`;
4. comparar ordered URLs/names;
5. exigir que el último item resuelva a la URL canónica actual;
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
        continue  # después clasificar si esa familia debe llevar breadcrumb
    assert [x.url for x in visible] == [x.url for x in jsonld]
    assert jsonld[-1].url == route.canonical
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

Semántica de #135: un `PARTIAL_AUDIT` necesita evidencia del gap antes de código.

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
```

## 4. Evidencia del repo preservada

### Samuel

`/libros/samuel-entre-mundos/` contiene:

```text
Inicio → Libros → Samuel entre mundos
```

integrado en el grafo JSON-LD.

### Las manecillas del recuerdo

`/las-manecillas-del-recuerdo/` contiene:

```text
Inicio → Libros → Las manecillas del recuerdo
```

### Topic collections

El trabajo histórico de topic collections preservó `BreadcrumbList` en `/cuaderno/temas/` y `/cuaderno/temas/fantasia-de-portales/`.

Por tanto A.6 nunca debe redactarse como “la web no tiene breadcrumbs”.

## 5. Preguntas que debe responder el audit

1. ¿qué familias tienen una jerarquía editorial donde breadcrumb ayuda?;
2. ¿cuáles ya tienen visible + JSON-LD?;
3. ¿visible y JSON-LD expresan el mismo orden/destinos?;
4. ¿el último item coincide con canonical actual?;
5. ¿`parentId`/`hubId` contradice la cadena?;
6. ¿un builder produce drift dentro de una misma familia?;
7. ¿el breadcrumb visual duplicaría sin valor el `section-context`?

## 6. Familias candidatas

Auditar:

- libros/obras;
- Cuaderno/colecciones;
- recomendaciones;
- herramientas individuales;
- directorios/recursos profundos;
- clubes/guías hijas.

No imponer por defecto:

- Home;
- 404;
- legales/noindex;
- machine/utility;
- páginas de un solo nivel donde la UI añadiría ruido.

## 7. Fuente de verdad

La jerarquía ya vive en autoridades como `data/content-registry.json` (`parentId`, `hubId`) y navegación/builders existentes.

**No crear `data/breadcrumbs.json`.**

La estructura de carpetas tampoco es una autoridad semántica suficiente.

Ejemplo de cadena derivada:

```text
child.parentId -> parent
parent.parentId -> hub
hub.parentId -> root family
```

El checker debe comparar lo derivable con markup real solo donde la familia tenga contrato de breadcrumb.

## 8. Implementación propuesta, si el audit demuestra gaps

Preferencia histórica:

```bash
python scripts/check-breadcrumb-parity.py
python scripts/check-breadcrumb-parity.py --json artifacts/breadcrumbs.json
```

Salida mínima:

```text
PASS  work-samuel
PASS  work-manecillas
WARN  tool-x missing-jsonld
ERROR article-y url-drift expected=/cuaderno/ actual=/otra/
```

Reglas:

- JSON-LD parseable;
- posiciones consecutivas;
- URLs same-origin/absolutas cuando aplique;
- destinos conocidos/canónicos;
- último item representa la página actual;
- visible ↔ JSON-LD comparados de forma semántica razonable;
- exclusiones explícitas;
- no inferir jerarquía solo por URL.

## 9. Breadcrumb visible vs JSON-LD

Si la familia usa breadcrumb visual:

```html
<nav aria-label="Migas de pan">…</nav>
```

- enlaces `<a href>` reales;
- último item como texto o `aria-current="page"`;
- navegación útil para personas;
- evitar duplicación gratuita con `section-context`.

No asumir que tener `BreadcrumbList` obliga a una segunda fila visual en todas las plantillas.

## 10. Ejemplo de structured data

```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Inicio",
      "item": "https://davidportodiaz.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Cuaderno",
      "item": "https://davidportodiaz.com/cuaderno/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Qué es el portal fantasy"
    }
  ]
}
```

Es ejemplo, no plantilla a copiar indiscriminadamente.

## 11. Qué NO hacer

- generar breadcrumbs por slugs/carpetas sin autoridad editorial;
- añadirlos a Home/404 para “tener schema”;
- duplicar `section-context` sin necesidad UX;
- exponer noindex/gated en cadenas públicas sin sentido;
- keyword stuffing en labels;
- inventar páginas para completar una cadena;
- crear un segundo registro manual de breadcrumbs;
- mezclar esta tarea con Person/Book entity IDs;
- convertir `PARTIAL_AUDIT` en cambios HTML antes del inventario.

## 12. Tests

- fixture `missing-visible`;
- fixture `missing-jsonld`;
- `order-drift`;
- `url-drift`/canonical final incorrecto;
- `parentId` inexistente/ciclo;
- familia required sin breadcrumb;
- familia exempt sin falso fallo;
- JSON-LD parseable;
- URLs absolutas/canónicas según contrato;
- builder parity si se modifica una familia generada.

## 13. Coste / beneficio

Auditar: bajo coste / valor medio.  
Corregir gaps reales: bajo/medio.  
Añadir barra visual sitewide sin evidence: coste visual/UX y mantenimiento potencialmente mayor que beneficio.

## 14. Definition of Done

### Historia ya recuperada

- [x] hipótesis original preservada;
- [x] `PARTIAL_AUDIT` inicial preservado;
- [x] evidencia de breadcrumbs existentes recuperada;
- [x] `IMPLEMENTAR/VERIFICAR` de matriz registrado como estado intermedio condicionado;
- [x] blueprint W4 completo recuperado;
- [x] nombre histórico `check-breadcrumb-parity.py` recuperado;
- [x] estados de error W4 preservados;
- [x] autoridad JSON final = `PARTIAL_AUDIT`;
- [x] autoridad humana final preservada;
- [x] revalidación independiente mantuvo A.6.

### Futuro audit/implementación

- [ ] definir familias `required / optional / exempt` desde autoridades actuales;
- [ ] ejecutar inventario antes de cambios;
- [ ] corregir solo gaps/contradicciones;
- [ ] reutilizar builders/registry;
- [ ] añadir checker/parity solo una vez;
- [ ] mantener structured-data/UX QA verde.

## 15. Trazabilidad del corpus histórico de #135 revisado para A.6

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `PARTIAL_AUDIT`.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — BreadcrumbList oficial.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — capacidad parcial ya existente.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR/VERIFICAR` histórico.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W4 de coverage/parity.
- `data/web-improvement-decisions-2026-08-28.json` — estado final machine-readable.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión/fuente revalidadas.

### Revisados sin cambio específico adicional

Overrides no aplicables a A.6, cuarta a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch fueron revisados y no contienen una modificación única adicional para esta idea.

## 16. Recomendación de merge

**MERGE como reconstrucción completa + `PARTIAL_AUDIT`.**

Clara/Claude debe empezar ejecutando/creando el audit de paridad, no modificando todas las páginas. Solo después de evidencia concreta se corrigen familias o builders.