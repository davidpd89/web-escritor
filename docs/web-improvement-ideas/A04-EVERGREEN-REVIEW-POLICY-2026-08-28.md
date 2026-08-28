# A.4 · Revisión programada de contenido evergreen

Fecha de revisión: 2026-08-28
Idea original: añadir una fecha de revisión objetivo a `content-registry.json` y refrescar fechas visibles al actualizar contenido evergreen.

## Veredicto

**IMPLEMENTAR, PERO CON UNA CORRECCIÓN IMPORTANTE: revisar contenido sí; “refrescar fechas” automáticamente no.**

El problema real existe: directorios, recomendaciones, convocatorias, recursos y guías con hechos externos pueden quedarse obsoletos. Un calendario de revisión reduce stale facts y mejora confianza editorial.

La parte peligrosa de la idea original es usar cambios de fecha como “señal de frescura”. Google desaconseja cambiar fechas o hacer cambios superficiales para aparentar contenido reciente. `dateModified` y la fecha visible deben representar una actualización significativa, no el paso del calendario.

## Fuentes primarias

1. Google Search Central · Creating helpful, reliable, people-first content
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content
   - Google pregunta explícitamente si se cambia la fecha de páginas para hacerlas parecer recientes aunque el contenido no haya cambiado sustancialmente.
   - Añadir/eliminar mucho contenido para aparentar frescura no ayuda por sí mismo.

2. Google Search Central · Article publication date best practices
   https://developers.google.com/search/docs/appearance/publication-dates
   - Google estima fechas usando múltiples señales.
   - Puede utilizar fechas visibles y `datePublished` / `dateModified`.
   - La fecha visible y structured data deben ser coherentes.
   - `dateModified` debe corresponder a una modificación real/relevante.

3. Schema.org `dateModified`
   https://schema.org/dateModified
   - Propiedad para la fecha de última modificación real de la CreativeWork/WebPage.

## Estado del repo

`data/content-registry.json` ya es el inventario canónico de contenido y contiene `id`, `url`, `type`, `territory`, `parentId`, `hubId`, `discoverability`, `sourceFile`, etc. **No contiene actualmente una política de revisión temporal genérica.**

Hay familias con distinta volatilidad:

### Alta volatilidad

- `/convocatorias-escritores/` y datos de oportunidades;
- directorios de editoriales cuando se afirma “recibe manuscritos”/estado verificable;
- eventos futuros;
- recursos que dependen de APIs/plataformas/funciones externas.

### Media

- recomendaciones cuando citan disponibilidad/ediciones/datos externos;
- artículos prácticos sobre plataformas/SEO/herramientas;
- metodología con enlaces a políticas que pueden cambiar.

### Baja/estable

- fichas de libros publicados (salvo hechos comerciales);
- biografía estable del autor;
- fragmentos literarios;
- artículos de proceso/ensayo que no dependen de información cambiante.

Aplicar una cadencia uniforme sería ruido.

## Modelo propuesto

No reutilizar `dateModified` como deadline. Añadir metadata explícita y separada:

```json
{
  "id": "recommend-portal-es",
  "reviewPolicy": {
    "class": "medium",
    "lastReviewed": "2026-08-28",
    "reviewBy": "2026-11-28",
    "reason": "ediciones, enlaces y disponibilidad externa pueden cambiar",
    "owner": "editorial"
  }
}
```

Para contenido estable:

```json
{
  "id": "work-samuel",
  "reviewPolicy": {
    "class": "event-driven",
    "triggers": ["new-edition", "retailer-change", "publisher-change"]
  }
}
```

No hace falta añadir `reviewPolicy` a cada entrada si se pueden definir defaults por `type`/familia y overrides concretos.

## Script propuesto

`scripts/check-content-review-dates.py`

Modos:

```bash
python scripts/check-content-review-dates.py
python scripts/check-content-review-dates.py --json artifacts/content-review.json
python scripts/check-content-review-dates.py --strict
```

Comportamiento:

- `INFO`: próxima revisión dentro de 30 días;
- `WARNING`: `reviewBy` vencido;
- `ERROR` en `--strict` solo para contenido con política que el proyecto haya declarado release-critical;
- nunca modifica HTML/JSON automáticamente;
- nunca actualiza `lastReviewed` por el mero hecho de ejecutar el script.

Pseudocódigo:

```python
for entry in registry["entries"]:
    policy = resolve_review_policy(entry)
    if not policy or policy["class"] == "event-driven":
        continue
    if date.today() > parse(policy["reviewBy"]):
        findings.append({"id": entry["id"], "status": "OVERDUE"})
```

## Flujo editorial correcto

1. El checker dice que una pieza toca revisión.
2. Claude/persona revisa fuentes primarias y enlaces.
3. Si no cambia nada sustancial:
   - actualizar `lastReviewed`/`reviewBy` del registry;
   - **no** cambiar fecha visible ni `dateModified` del artículo.
4. Si cambia contenido sustancial:
   - actualizar texto;
   - actualizar `dateModified` y, si el diseño lo muestra, “Actualizado el …”;
   - mantener `datePublished` original;
   - registrar fuente/evidencia cuando proceda.

## Qué significa “sustancial”

Ejemplos válidos para `dateModified`:

- se reescribe una sección material;
- se añaden/eliminan recomendaciones por cambios reales;
- cambia metodología o criterios;
- se corrige un hecho relevante;
- se actualizan datos que cambian la utilidad de la página.

No válido:

- corregir una tilde;
- regenerar HTML;
- cambiar CSS;
- renovar `reviewBy` tras comprobar que todo sigue igual;
- cambiar la fecha para que Google vea contenido “fresco”.

## Integración con builders

No dispersar fechas en plantillas manuales. Si una familia generada muestra fecha de actualización:

- el source of truth debe ser su data/registry;
- el builder debe generar HTML + JSON-LD desde ese mismo valor;
- `--check` debe detectar drift.

## Tests

1. schema de `reviewPolicy` válido;
2. `reviewBy >= lastReviewed`;
3. ninguna fecha futura usada como `lastReviewed`;
4. entries `event-driven` no requieren deadline artificial;
5. checker no muta ficheros;
6. fixture overdue genera warning/error esperado;
7. cuando una página expone `dateModified`, structured data y fecha visible deben coincidir si existe fecha visible;
8. `datePublished` no se reemplaza por `dateModified`.

## Automatización

Recomendación: workflow semanal **informativo**, no bot de edición:

```yaml
name: Content review due
on:
  schedule:
    - cron: "17 7 * * 1"
  workflow_dispatch:
```

Puede generar summary/artifact o issue solo cuando existan vencimientos. Evitar commits automáticos de fechas.

## Coste / beneficio

Beneficio: **alto** para directorios/oportunidades y contenido externo cambiante; medio para recomendaciones; bajo para contenido literario estable.
Coste: bajo/medio.
Riesgo si se implementa mal: fake freshness y ruido editorial.

## Definition of Done

- [ ] clasificar familias por volatilidad real;
- [ ] añadir policy solo donde aporte valor;
- [ ] implementar checker read-only;
- [ ] test de fechas/schema;
- [ ] documentar diferencia `lastReviewed` vs `dateModified`;
- [ ] workflow informativo opcional;
- [ ] ninguna actualización automática de fecha visible;
- [ ] validar con 3 casos reales: convocatoria/editorial, recomendación y página estable.

## Recomendación de merge

**MERGE como plan de implementación.** Es una de las primeras diez ideas que sí aporta una capacidad nueva clara, siempre que se implemente como control de obsolescencia y no como manipulación de frescura SEO.