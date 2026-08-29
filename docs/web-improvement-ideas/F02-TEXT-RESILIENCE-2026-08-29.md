# F.2 · Text Resilience: 200% + WCAG Text Spacing

**Estado histórico final de PR #135:** `IMPLEMENT_NOW`  
**Prioridad histórica:** P0 dentro de la ola de accesibilidad posterior a #135  
**Base normativa:** WCAG 1.4.4 Resize Text + 1.4.12 Text Spacing  
**Naturaleza de esta PR:** documentación; no modifica todavía el QA.

## 1. Idea original

F.2 nació como una propuesta para verificar explícitamente el algoritmo de espaciado de texto de WCAG y detectar recortes, solapes o pérdidas funcionales que una auditoría de contraste no descubre.

La investigación adquirió mucha más fuerza cuando el propio repositorio produjo evidencia de un falso negativo: una comprobación basada en `zoom=2` podía estar verde mientras `font-size:200%` seguía rompiendo componentes reales.

## 2. Evidencia decisiva: PR #133

El historial posterior a la hipótesis original aporta una prueba concreta, no teórica:

- en el ecosistema de Samuel apareció overflow bajo `font-size:200%`;
- el QA sitewide que aplicaba una forma de zoom/reflow no había detectado el mismo defecto;
- #133 corrigió primero `.samuel-route-list` y después un residual equivalente en `.samuel-proof__stream li` usando `minmax(0,1fr)`;
- se añadió cobertura a `/libros/samuel-entre-mundos/` dentro de `qa/samuel-ecosystem-browser.mjs`;
- el propio PR verificó que el test fallaba al revertir localmente el fix y pasaba con él.

Conclusión de #135: **`zoom:2` y `font-size:200%` no son sustitutos entre sí**. La web necesita un contrato explícito de resiliencia de texto.

## 3. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Automatizar WCAG Text Spacing en plantillas clave. |
| Revisión 108/108 | `IMPLEMENT_NOW` | Añade `font-size:200%` por la evidencia de #133; exige offender report. |
| Matriz operativa | `IMPLEMENTAR P0` | Text Spacing **y** 200%; no considerar `zoom:2` equivalente. |
| Blueprint W1 | implementación detallada | Reusar el crawler/medición de Sitewide Reflow, aplicar CSS de estrés, viewports mínimos y artifact diagnóstico. |
| Orden neto de #135 | prioridad 1 | “F.2 Text Resilience sitewide real” queda por delante de las otras tareas nuevas de accesibilidad. |
| Autoridad final | `IMPLEMENT_NOW` | CI debe probar ambas modalidades. |
| Revalidación independiente | mantenido | W3C/WAI sustenta la decisión; no cambia status. |
| Revalidación actual | cobertura parcial concreta, no sitewide demostrada | #133 protege parte de Samuel, pero no convierte el contrato global de W1 en `ALREADY_COVERED`. |

## 4. Fuentes normativas

Fuentes conservadas por #135:

- WCAG Text Spacing 1.4.12: `https://www.w3.org/WAI/WCAG22/Understanding/text-spacing`
- WCAG Resize Text 1.4.4: `https://www.w3.org/WAI/WCAG21/Understanding/resize-text`

La intención no es verificar que el CSS tenga ciertas propiedades, sino que el contenido siga siendo legible y funcional cuando el usuario cambia tamaño/espaciado dentro de los escenarios normativos.

## 5. Blueprint W1 recuperado

#135 especificó reutilizar la infraestructura de `qa/sitewide-reflow-browser.mjs` en vez de crear un segundo crawler. Las piezas históricas a extraer/reutilizar eran:

- `collectRoutes()`;
- `applyInspectorStyles()`;
- `measureOverflow()`;
- offender selectors;
- persistencia de JSON diagnóstico incluso cuando el run falla.

CSS histórico de estrés propuesto:

```js
const TEXT_RESILIENCE_CSS = `
html { font-size: 200% !important; }
html * {
  line-height: 1.5 !important;
  letter-spacing: .12em !important;
  word-spacing: .16em !important;
}
html p { margin-bottom: 2em !important; }
`;
```

La futura implementación debe validar la semántica exacta contra el estándar vigente y la arquitectura actual antes de copiar literalmente este bloque, pero no debe rebajar sus valores para conseguir verde.

Viewports mínimos históricos:

- 320×900;
- 390×900;
- 768×1000.

## 6. Qué debe detectar

Como mínimo:

- overflow horizontal no intencionado;
- texto cortado por alturas fijas;
- solapes entre labels, iconos, botones y contenido;
- grids cuya columna mínima crece por min-content y excede viewport;
- controles inaccesibles al aumentar texto;
- diálogos/sticky UI que ocultan contenido;
- truncados/ellipsis que eliminan información necesaria;
- contenido que queda fuera del flujo o detrás de otra capa;
- cambios de orden/visibilidad que impidan completar una acción.

Un contenedor expresamente scrollable puede ser válido si sigue ofreciendo acceso completo y comprensible al contenido. Debe tratarse como excepción documentada, no ocultarse con `overflow-x:hidden` global.

## 7. Estado real actual

El historial de #133 demuestra que hay cobertura específica en el ecosistema Samuel y un test que ya aplica modos `qa-text-200`/`qa-text-spacing` en esa familia. Eso es evidencia útil para reutilizar patrones.

No hay evidencia suficiente, en este corte, de que el **contrato sitewide W1 completo** esté integrado en todas las rutas públicas ni en un required context universal. Por eso el estado histórico `IMPLEMENT_NOW` no se rebaja a `ALREADY_COVERED`.

La implementación futura debe inspeccionar primero el QA vigente: si una PR posterior a este corte ya incorporó W1 globalmente, se extiende esa autoridad y se actualiza la conclusión; nunca se crea una segunda suite paralela.

## 8. Guardrails

- No `overflow-x:hidden` global para esconder offenders.
- No clipping de texto como “fix”.
- No bajar `font-size:200%`, line-height o spacing para pasar.
- No sustituir el modo por CSS `zoom`.
- No excluir una ruta porque falla sin documentar el motivo.
- No hardcodear únicamente las URLs conocidas de Samuel; el objetivo es cobertura por familia/rutas públicas.
- No confiar en Pa11y/axe como única prueba: la geometría necesita navegador.
- El artifact de offenders debe producirse también cuando falla el job.

## 9. Plan de implementación futuro

1. Revisar la versión vigente de `qa/sitewide-reflow-browser.mjs` y `qa/samuel-ecosystem-browser.mjs`.
2. Extraer/reusar route discovery y medición existente.
3. Crear modos separados para Resize Text 200% y Text Spacing, o una combinación deliberada que no oculte cuál falla.
4. Ejecutar en 320/390/768 y añadir otros breakpoints solo por evidencia.
5. Registrar offender, selector, rect, overflow y screenshot/artifact.
6. Resolver fallos en la autoridad CSS/builder propietaria, no con excepciones amplias.
7. Ejecutar tests de regresión que demuestren que un bug conocido vuelve a fallar al revertir el fix cuando sea práctico.
8. Integrar en un contexto CI que realmente proteja merges, sin duplicar Sitewide Reflow.

## 10. Definition of Done

- [ ] todas las rutas públicas elegibles se descubren mediante autoridad existente;
- [ ] se prueba Resize Text 200%, no solo zoom;
- [ ] se prueba Text Spacing 1.4.12;
- [ ] overflow no intencionado <=1px según el contrato histórico;
- [ ] no hay recorte/solape/pérdida funcional;
- [ ] excepciones scrollables están justificadas y accesibles;
- [ ] artifact diagnóstico se conserva también en fallo;
- [ ] la regresión forma parte de un check que no sea decorativo;
- [ ] Sitewide Reflow y Pa11y siguen verdes;
- [ ] no se rebaja el estrés para hacer pasar el test.

## 11. Relación con otras ideas

- **F.1:** targets deben continuar operables al ampliar texto.
- **F.4:** foco debe seguir visible/no oculto cuando la composición crece.
- **F.5:** F.2 es la alternativa correcta al modo de texto grande propio rechazado.
- **D.2:** también reduce la necesidad de un Reader Mode propio.
- **R.1:** Focus Not Obscured debe probarse bajo composiciones expandidas cuando sea relevante.

## 12. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis Text Spacing.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — incorpora evidencia #133 y `font-size:200%`.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — WCAG.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — QA existente.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` / `...OVERRIDES-REPO...` — reconciliación repo.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR P0`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W1 detallado.
- `data/web-improvement-decisions-2026-08-28.json` — `IMPLEMENT_NOW`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida.
- PR #133 y handoff #134 — evidencia de falso negativo y residual real.
- orden neto de la propia #135 — F.2 queda como primera tarea nueva tras reconciliación.
- pasadas posteriores — revisadas; Forced Colors/contrast son ondas adyacentes, no sustituyen F.2.

## 13. Cierre

F.2 existe porque el proyecto ya demostró que un QA aparentemente verde podía no representar cómo rompe la página cuando el usuario aumenta realmente el texto. El contrato correcto es sitewide, browser-based y diagnóstico: 200% + Text Spacing, sin trucos de overflow ni equivalencias falsas con `zoom`.