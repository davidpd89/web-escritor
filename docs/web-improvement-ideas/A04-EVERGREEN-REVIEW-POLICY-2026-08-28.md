# A.4 · Revisión programada de contenido evergreen

Fecha de reconstrucción: 2026-08-29  
Idea original: añadir una fecha de revisión objetivo a `content-registry.json` y refrescar fechas visibles tras cambios sustantivos en contenido evergreen.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: plan/documentación; no implementa todavía el lifecycle.

## Veredicto reconciliado

**IMPLEMENT_AFTER_CURRENT_DEBT.**

La capacidad aporta valor real, especialmente para contenido que depende de hechos externos, pero #135 no la dejó como implementación inmediata. Debe integrarse en las autoridades ya existentes y, de forma explícita, **extender `scripts/check-article-dates.py` en lugar de crear otro checker paralelo**.

La idea original contenía una premisa peligrosa: tratar el cambio de fecha visible como señal de frescura. #135 la corrigió. La fecha pública y `dateModified` solo cambian después de una modificación material; revisar una pieza y confirmar que sigue correcta no autoriza un “freshness bump”.

## 1. Regla de reconstrucción de #135

Esta PR recupera A.4 directamente desde el snapshot histórico de #135, no solo desde #148.

Se preservan:

- hipótesis original;
- estado inicial y final;
- corrección contra fake freshness;
- fuente primaria sobre fechas;
- hallazgo del checker ya existente;
- blueprint técnico neto;
- variantes históricas de nomenclatura (`reviewAt`, `reviewBy`, `reviewCadence`, `verifiedAt`);
- autoridad humana/JSON final;
- revalidación independiente;
- tests y límites.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía:

> marcar en `content-registry.json` una fecha de revisión objetivo para artículos de recomendaciones/guías y refrescar la fecha visible después de cambios sustantivos, presentado en parte como señal de frescura para Google.

Había dos ideas mezcladas:

1. una buena: controlar obsolescencia editorial;
2. una que requería corrección: convertir fechas en una táctica SEO de “frescura”.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` aprobó el problema real y corrigió la semántica:

- añadir `reviewAt`/`verifiedAt` a evergreen;
- `dateModified` solo tras actualización sustantiva;
- **no refrescar `datePublished` artificialmente**.

A.4 quedó como trabajo válido, de alto valor, pero posterior a la deuda técnica/QA activa.

### 3.2 · Fuentes primarias → no fake freshness

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` fijó como autoridad:

Google Search Central · Article publication date best practices  
https://developers.google.com/search/docs/appearance/publication-dates

Y, en la investigación posterior:

Google · Creating helpful, reliable, people-first content  
https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Schema.org · `dateModified`  
https://schema.org/dateModified

Conclusión de #135:

- `datePublished` representa publicación original;
- `dateModified` representa cambio material real;
- fecha visible y structured data deben mantener coherencia;
- revisar contenido sin cambiarlo no justifica simular actualización pública.

### 3.3 · Matriz intermedia → `IMPLEMENTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` resumió A.4 como:

> añadir `reviewBy/reviewCadence` a contenido evergreen; fecha visible solo cambia tras actualización material; nunca “freshness bump” automático.

Ese `IMPLEMENTAR` describía una mejora aprobada, pero la autoridad final machine-readable conservó la prioridad `IMPLEMENT_AFTER_CURRENT_DEBT`.

### 3.4 · Inspección profunda del repo → extender `check-article-dates.py`

Este es un hallazgo crítico que la primera versión de esta PR individual había perdido.

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` dice expresamente:

> A.4 sigue pendiente, pero debe extender `scripts/check-article-dates.py` y la autoridad actual; no crear otro validador independiente.

Además fija la semántica que debe distinguirse:

- `publishedAt`;
- `modifiedAt`;
- `verifiedAt`;
- `reviewAt`.

Por tanto **queda descartada** la propuesta anterior de esta PR de crear `scripts/check-content-review-dates.py` como sistema paralelo.

### 3.5 · Blueprint neto W5 → implementación concreta

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` dedica W5 a A.4.

Autoridad existente a reutilizar:

- `scripts/check-article-dates.py`;
- `data/content-registry.json` cuando corresponda;
- builders que ya renderizan fechas visibles/JSON-LD.

Modelo orientativo histórico:

```json
{
  "publishedAt": "2026-08-01",
  "modifiedAt": "2026-08-28",
  "verifiedAt": "2026-08-28",
  "reviewAt": "2027-02-28"
}
```

Semántica:

- `publishedAt`: publicación original;
- `modifiedAt`: modificación material publicada;
- `verifiedAt`: fecha de comprobación factual aunque no haya cambio textual;
- `reviewAt`: deuda/fecha objetivo interna, nunca mostrada automáticamente como “actualizado”.

Validaciones mínimas propuestas:

```python
assert published_at <= modified_at
assert verified_at <= review_at
```

El blueprint también descarta usar un hash ingenuo del HTML completo para decidir si hubo cambio material: shell, CSS, analytics o regeneración pueden cambiar bytes sin alterar contenido editorial.

### 3.6 · Variación de nombres en la autoridad final

En documentos posteriores aparecen `reviewBy/reviewCadence` en lugar de `reviewAt`. Esto no cambia la capacidad: es una diferencia de diseño de esquema todavía no implementado.

La PR de implementación futura debe escoger **una sola nomenclatura compatible con la autoridad de datos actual**, migrarla de forma explícita y testearla. No mantener simultáneamente `reviewAt`, `reviewBy`, `lastReviewed` y `reviewPolicy` sin una razón.

### 3.7 · Autoridad machine-readable final

`data/web-improvement-decisions-2026-08-28.json` fija:

```json
{"id":"A.4","area":"seo","status":"IMPLEMENT_AFTER_CURRENT_DEBT"}
```

Este es el estado final histórico que debe gobernar esta PR.

### 3.8 · Autoridad humana final

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` consolida:

> añadir `reviewBy/reviewCadence` a evergreen y actualizar fechas visibles solo tras cambios materiales.

### 3.9 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` volvió a revisar las 108 ideas y mantuvo A.4. También volvió a citar la guía oficial de fechas de Google. No surgió una corrección que invalidase la capacidad.

Secuencia histórica:

```text
hipótesis de revisión + frescura
→ IMPLEMENT_AFTER_CURRENT_DEBT
→ corrección: no fake freshness
→ matriz: IMPLEMENTAR
→ repo override: extender check-article-dates.py
→ blueprint W5
→ final: IMPLEMENT_AFTER_CURRENT_DEBT
```

## 4. Problema real que resuelve

Hay contenido con volatilidad muy distinta.

### Alta volatilidad

- convocatorias y oportunidades;
- directorios de editoriales cuando se afirma estado de recepción de manuscritos;
- eventos futuros;
- datos dependientes de plataformas/API/políticas externas.

### Media

- recomendaciones con disponibilidad/ediciones/datos externos;
- artículos prácticos sobre plataformas, SEO o herramientas;
- metodología con enlaces a políticas cambiantes.

### Baja o event-driven

- fichas de libros estables salvo hechos comerciales;
- biografía estable;
- fragmentos literarios;
- ensayos/proceso creativo sin datos externos perecederos.

Una cadencia uniforme sería ruido. Debe aplicarse solo donde el coste de quedar obsoleto sea material.

## 5. Diseño de datos que sobrevive a #135

La intención no es imponer un objeto `reviewPolicy` nuevo si el registry puede resolverlo con campos simples/defaults por familia.

Una implementación válida podría terminar, tras revisar el schema real, en algo equivalente a:

```json
{
  "id": "recommend-portal-es",
  "verifiedAt": "2026-08-28",
  "reviewBy": "2026-11-28",
  "reviewCadenceDays": 90
}
```

O usar `reviewAt` si esa es la nomenclatura elegida en la PR final.

Para contenido estable puede bastar un comportamiento event-driven sin deadline artificial.

Regla: **una sola fuente de verdad y un solo vocabulario final**.

## 6. Implementación correcta

### 6.1 · Extender `scripts/check-article-dates.py`

No crear `check-content-review-dates.py` en paralelo salvo que una limitación concreta del checker existente lo haga imposible y se documente.

El checker existente debe ampliarse para:

- validar campos de lifecycle cuando existan;
- distinguir error de fecha pública frente a deuda editorial interna;
- reportar revisiones próximas/vencidas;
- no mutar contenido;
- no actualizar `verifiedAt` por el mero hecho de ejecutarse;
- conservar sus contratos actuales de `datePublished`/`dateModified`.

### 6.2 · Modo read-only

Comportamiento orientativo:

```text
INFO    review due within 30 days
WARNING review target overdue
ERROR   solo si una familia se declara release-critical y el contrato lo exige
```

No hacer commits automáticos de fechas.

### 6.3 · Flujo editorial

1. el checker identifica una pieza pendiente de revisión;
2. persona/Claude revisa fuentes primarias y datos;
3. si todo sigue correcto:
   - actualizar solo la evidencia interna elegida (`verifiedAt` y siguiente revisión);
   - no cambiar `dateModified` ni fecha visible;
4. si cambia contenido sustancial:
   - actualizar texto/datos;
   - actualizar `modifiedAt`/`dateModified`;
   - actualizar fecha visible si la plantilla la muestra;
   - conservar `publishedAt`/`datePublished` original.

## 7. Qué es una modificación material

Sí puede justificar `dateModified`:

- reescritura de una sección sustancial;
- altas/bajas de recomendaciones por hechos reales;
- cambio de metodología/criterios;
- corrección factual relevante;
- actualización de datos que cambia la utilidad de la página.

No:

- una tilde;
- regeneración de HTML;
- CSS/shell;
- renovar el deadline tras comprobar que nada cambió;
- tocar fecha para parecer reciente.

## 8. Builders y paridad

Si una familia generada muestra fecha pública:

- datos canónicos → builder → HTML + JSON-LD;
- `--check` o test equivalente debe detectar drift;
- no dispersar fechas manualmente por plantillas;
- una comprobación editorial interna no debe alterar por efecto colateral el markup público.

## 9. Automatización opcional

#135 permitía automatización **informativa**, no edición automática. Un workflow semanal puede reportar vencimientos si existe utilidad operativa.

Ejemplo:

```yaml
name: Content review due
on:
  schedule:
    - cron: "17 7 * * 1"
  workflow_dispatch:
```

Debe consumir el checker existente ampliado. No abrir PRs que solo cambien fechas ni crear issues cada semana si no hay vencimientos.

## 10. Tests

- `publishedAt <= modifiedAt` cuando ambos existan;
- `verifiedAt <= reviewAt/reviewBy` según schema final;
- ninguna verificación futura;
- contenido event-driven no recibe deadline artificial;
- checker read-only no muta ficheros;
- fixture overdue genera salida esperada;
- `dateModified` estructurado y fecha visible mantienen paridad cuando existe fecha visible;
- `datePublished` nunca se reemplaza por `dateModified`;
- cambios de shell/build no se confunden con modificación editorial material;
- tests actuales de `check-article-dates.py` siguen verdes.

## 11. Qué NO hacer

- crear un segundo checker sin demostrar que el existente no puede extenderse;
- usar `dateModified` como deadline;
- cambiar `datePublished` para “refrescar” una URL;
- actualizar fechas automáticamente en CI;
- imponer revisión trimestral a contenido literario estable;
- mantener cuatro nombres equivalentes sin migración/contrato;
- usar hash del HTML completo como prueba de materialidad;
- vender la cadencia como factor de ranking.

## 12. Coste / beneficio

Beneficio alto para directorios/oportunidades y datos externos; medio para recomendaciones; bajo para contenido estable.  
Coste bajo/medio si extiende la autoridad existente.  
Riesgo principal: fake freshness, ruido editorial y una segunda fuente de verdad si se implementa mal.

## 13. Definition of Done

### Historia/decisión ya recuperada

- [x] hipótesis original preservada;
- [x] `IMPLEMENT_AFTER_CURRENT_DEBT` inicial preservado;
- [x] corrección de fake freshness preservada;
- [x] estado `IMPLEMENTAR` de matriz intermedia identificado como histórico;
- [x] override de repo que exige extender `check-article-dates.py` recuperado;
- [x] blueprint W5 recuperado;
- [x] variación `reviewAt` vs `reviewBy/reviewCadence` documentada;
- [x] autoridad JSON final = `IMPLEMENT_AFTER_CURRENT_DEBT`;
- [x] autoridad humana final preservada;
- [x] revalidación independiente mantuvo A.4.

### Para una futura PR de implementación

- [ ] auditar schema/campos actuales antes de elegir nombres;
- [ ] clasificar solo familias realmente volátiles;
- [ ] extender `scripts/check-article-dates.py`;
- [ ] implementar metadata en una autoridad existente;
- [ ] añadir tests de lifecycle y paridad;
- [ ] mantener checker read-only;
- [ ] no tocar fecha visible sin cambio material;
- [ ] validar al menos un caso volátil, uno medio y uno estable/event-driven.

## 14. Trazabilidad del corpus histórico de #135 revisado para A.4

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — estado inicial y corrección de fechas.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — fechas/publication updates.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR` histórico.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — extender `check-article-dates.py`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W5 completo.
- `data/web-improvement-decisions-2026-08-28.json` — estado final machine-readable.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — revalidación/fuente de fechas.

### Revisados sin cambio específico adicional

Cuarta y quinta pasada, sexta y revisión crítica, séptima a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch fueron revisados; no añaden una decisión única adicional para A.4 más allá de lo consolidado arriba.

## 15. Recomendación de merge

**MERGE como reconstrucción completa y plan `IMPLEMENT_AFTER_CURRENT_DEBT`.**

Esta PR no implementa la capacidad. Deja a Clara/Claude la autoridad exacta para desarrollarla después sin repetir la investigación ni crear un checker duplicado.