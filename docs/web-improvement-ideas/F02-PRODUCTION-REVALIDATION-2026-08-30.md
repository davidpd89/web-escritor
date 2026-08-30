# F.2 · Revalidación de producción — Resize Text 200% + Text Spacing

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `IMPLEMENTED_IN_PR · SITEWIDE_ENFORCED · RESIZE_TEXT_200_AND_TEXT_SPACING_SEPARATE · ZERO_RESIDUAL_FINDINGS`

## 1. Gap real confirmado en `main`

El Sitewide Reflow vigente en `main` ya era una autoridad importante, pero su escenario histórico combinaba:

- WCAG Text Spacing;
- `document.documentElement.style.zoom = '2'`.

Eso prueba una forma útil de presión de layout, pero **no equivale a Resize Text 200%**.

Existe además cobertura más precisa en `qa/samuel-ecosystem-browser.mjs`, donde cuatro superficies de Samuel/Noveris usan dos modos separados (`qa-text-200` y `qa-text-spacing`). Esa cobertura demuestra el patrón correcto, pero no es sitewide.

F.2 cubre exactamente ese hueco sin crear un segundo crawler.

## 2. Requisito normativo revalidado

Fuentes vigentes:

- WCAG 2.2 Understanding 1.4.4 Resize Text: <https://www.w3.org/WAI/WCAG22/Understanding/resize-text>
- WCAG 2.2 Understanding 1.4.12 Text Spacing: <https://www.w3.org/WAI/WCAG22/Understanding/text-spacing>

El contrato de esta PR usa escenarios independientes:

### Resize Text 200%

```css
html { font-size: 200% !important; }
```

### Text Spacing

```css
* {
  line-height: 1.5 !important;
  letter-spacing: .12em !important;
  word-spacing: .16em !important;
}
p { margin-bottom: 2em !important; }
```

No se rebajan estos valores para conseguir verde y `zoom` no se presenta como sustituto.

## 3. Reutilización de la autoridad existente

`qa/sitewide-reflow-browser.mjs` sigue siendo el owner de descubrimiento y geometría.

La PR amplía ese mismo checker con:

- `TEXT_RESILIENCE_MODE=off|report|enforce`;
- viewports 320×900, 390×900 y 768×1000 para F.2;
- escenario `resize-text-200`;
- escenario `text-spacing`;
- overflow horizontal >1 px como fallo;
- detección de texto realmente cortado por `overflow:hidden|clip`;
- artifact separado por escenario con selector, rect/geometría y texto de muestra.

El escenario histórico de Sitewide Reflow se conserva; F.2 no lo reemplaza ni altera su significado.

## 4. Hallazgos y remediación

La primera auditoría sitewide reveló residuos de min-content/intrinsic sizing que no justificaban ocultar overflow.

Las correcciones se hicieron en los owners CSS responsables, entre otros:

- formularios y campos fluidos;
- mastheads y metadata compacta;
- acciones flex con label/glyph;
- navegación y grids editoriales;
- tablas y fuentes de artículos;
- tarjetas/offsets de Home;
- CTA sticky de fragmentos;
- disponibilidad de Manecillas;
- hero de Samuel;
- tarjetas de Prensa;
- findings de herramientas.

Se reutiliza `assets/v1-reflow-hardening-v7.css` para hardening transversal y se añade `assets/v1-text-resilience-v8.css` para los residuos específicos descubiertos por F.2.

No se introduce `overflow-x:hidden` global ni clipping como reparación.

## 5. Baseline reproducible

Run de Sitewide Reflow en modo collector/report sobre HEAD previo `67701a6426f36a48baf374f6de20330808e1c4e1`:

- workflow run: `33306816794`;
- 76 rutas públicas/elegibles;
- legacy reflow: 152 checks, 0 fallos;
- F.2: 456 checks = 76 rutas × 3 viewports × 2 escenarios;
- 0 fallos por overflow horizontal tras las correcciones.

El detector bruto encontró 296 casos de clipping visual. La inspección demostró que todos correspondían a tres patrones deliberados y source-backed:

- fallback textual del wordmark cuando existe imagen de marca;
- texto visualmente oculto del botón compacto `.header-search` en móvil, cuyo control conserva nombre accesible;
- utilidad canónica `.sr-only`.

Por ello se añadió `qa/text-resilience-report-gate.mjs`: el collector sigue siendo bruto y diagnóstico, mientras el reconciliador solo permite patrones explícitos respaldados por su owner CSS.

Resultado reconciliado del baseline:

- `checkCount: 456`;
- `failureCount: 0`;
- `masthead-logo-text-fallback: 6`;
- `compact-header-search-label: 276`;
- `sr-only-utility: 60`.

La clasificación tiene tests unitarios y cualquier clipping no clasificado sigue siendo fallo residual.

## 6. Gate final

En HEAD `95731be788890d24009e3403bab200595e6f9aa7` el workflow queda con:

1. collector F.2 en `report`, para conservar evidencia bruta;
2. reconciliador en `TEXT_RESILIENCE_GATE_MODE=enforce`;
3. cualquier overflow o clip residual no permitido bloquea `Sitewide Reflow QA`.

La separación es deliberada: no se silencian findings dentro del detector base.

## 7. Dependencia de integración con F.1

F.1 y F.2 son PR separadas sobre el mismo `main` y ambas amplían:

- `qa/sitewide-reflow-browser.mjs`;
- `.github/workflows/sitewide-reflow-qa.yml`.

Por tanto el orden de merge importa.

Al integrar:

- si F.1 entra primero, F.2 debe rebasarse/reconciliarse conservando **target-size + text-resilience** en el mismo Sitewide Reflow owner;
- si F.2 entra primero, F.1 debe hacer la misma reconciliación inversa.

No es válido resolver el conflicto escogiendo un fichero completo de una rama y perdiendo el otro gate.

Estado deseado final tras integración de ambas: un único crawler/sitewide workflow que ejecute Reflow + F.1 Target Size + F.2 Resize Text/Text Spacing.

## 8. Definition of Done

- [x] Resize Text 200% se prueba de forma independiente de `zoom`.
- [x] Text Spacing usa los valores WCAG completos.
- [x] cobertura basada en las rutas descubiertas por la autoridad sitewide existente.
- [x] viewports 320/390/768.
- [x] overflow >1 px detectable.
- [x] clipping de texto detectable.
- [x] findings brutos preservados en artifact.
- [x] excepciones visuales limitadas a patrones source-backed.
- [x] reconciliador con tests.
- [x] gate final en modo `enforce`.
- [x] sin `overflow-x:hidden` global ni reducción del estrés.
- [x] coexistencia con el legacy Reflow preservada.
- [ ] reconciliar con F.1 según el orden real de merge, porque ambas PR siguen DRAFT.

## 9. Cierre

F.2 deja de ser una hipótesis de accesibilidad: existe una auditoría sitewide reproducible para 200% de texto y Text Spacing, con diagnóstico bruto, excepciones explícitas y bloqueo de residuos reales.

La única tarea futura no es funcional sino de integración entre PR hermanas: conservar simultáneamente F.1 y F.2 cuando una de ellas aterrice primero en `main`.
