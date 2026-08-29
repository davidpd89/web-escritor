# F.4 · Focus visible + Focus Not Obscured

**Estado histórico final de PR #135:** `IMPLEMENT_AFTER_CURRENT_DEBT`  
**Ampliación material posterior:** WCAG 2.4.11 Focus Not Obscured (Minimum) se incorpora al alcance.  
**Naturaleza de esta PR:** documentación; no modifica CSS ni journeys.

## 1. Idea original

F.4 pedía revisar que todos los elementos interactivos nuevos —quiz, buscador, toggles, formularios y navegación— mantuvieran un indicador de foco visible y con contraste suficiente, en vez de confiar únicamente en componentes previamente certificados.

La investigación posterior descubrió que “el foco tiene un anillo” no era suficiente: un elemento puede tener `:focus-visible` correcto y quedar parcialmente oculto por un header sticky, diálogo u otra UI persistente. Esa extensión se consolidó como **Focus Not Obscured**.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Auditar `focus-visible` consistente. |
| Revisión 108/108 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Focus visible es una obligación real, pero Pa11y por sí solo no certifica journeys. |
| Matriz | `IMPLEMENTAR` | Añade browser QA manual/automatizado sobre dialog/menu/quiz/forms. |
| Pasadas posteriores | R.1 | El alcance se amplía explícitamente a Focus Not Obscured bajo headers, dialogs y sticky UI. |
| Orden neto de #135 | prioridad alta tras F.2 | R.1 aparece como segunda pieza de la ola de accesibilidad. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Une foco visible + WCAG 2.4.11 y exige keyboard/browser QA. |
| Revalidación independiente | mantenido | W3C/WAI 2.4.11 afianza la ampliación. |

La matriz intermedia usó “IMPLEMENTAR”; la autoridad final es la que prevalece: `IMPLEMENT_AFTER_CURRENT_DEBT`. La diferencia es de prioridad/secuenciación, no de validez técnica.

## 3. Fuente primaria

Fuente preservada por #135:

- WCAG 2.2, Focus Not Obscured (Minimum) 2.4.11: `https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum`

El foco también debe seguir siendo perceptible/visible conforme al resto de criterios aplicables. F.4 no se limita a verificar que exista una regla CSS `:focus-visible`.

## 4. Qué debe auditarse

### Perceptibilidad

- enlace, botón, input, select, textarea, summary y controles con roles interactivos;
- indicador suficientemente distinguible del estado normal;
- contraste/forma que sobreviva a las superficies visuales reales;
- no eliminar outline sin sustitución equivalente.

### Journey de teclado

- shell/header;
- abrir y cerrar Explorar;
- buscador/asistente;
- formularios/newsletter;
- herramientas;
- quizzes si existen;
- diálogos/modales;
- controles sticky/fixed;
- estados error/loading/retry;
- devolución razonable de foco después de cerrar overlays.

### No-obscured

Al avanzar con Tab/Shift+Tab el elemento enfocado no debe quedar oculto por:

- header sticky;
- banners/CTAs fixed;
- diálogo/overlay mal apilado;
- footer/sticky controls;
- teclado virtual/viewport reducido cuando el journey sea aplicable;
- contenido desplazado bajo barras persistentes.

## 5. Por qué Pa11y/axe no bastan

#135 fue explícita: el cumplimiento de foco depende de **secuencias y geometría en navegador**. Un auditor estático puede detectar ciertos problemas semánticos/CSS, pero no demuestra que:

- el foco siga el orden esperado;
- aparezca el control correcto al abrir un diálogo;
- vuelva al trigger al cerrar;
- el elemento no esté tapado en el viewport real;
- un sticky header no cubra el target tras `scrollIntoView`/Tab;
- estados dinámicos no secuestren el foco.

Por tanto F.4 requiere browser journeys y una capa manual representativa, no un simple “Pa11y green”.

## 6. Relación con cambios posteriores del proyecto

La web ha continuado endureciendo shell, reflow y diálogos después de #135. Eso reduce riesgo, pero no cambia la naturaleza del contrato: una capacidad nueva debe entrar en los journeys existentes en vez de abrir un checker paralelo por componente.

Si el `main` futuro ya contiene un auditor de Focus Not Obscured, F.4 se implementa extendiendo ese auditor. Esta PR no afirma que la auditoría global esté hoy cerrada sin ejecutar esos journeys.

## 7. Plan de implementación futuro

1. Reutilizar route discovery/browser harness existente.
2. Definir journeys mínimos por familia en vez de tabular ciegamente todos los nodos de todas las páginas.
3. Registrar el elemento activo en cada paso y su rectángulo visible.
4. Comparar el rectángulo con viewport y regiones persistentes/overlays que puedan ocultarlo.
5. Capturar screenshot/selector/paso al fallar.
6. Validar indicadores en modos de contraste/forced colors si la wave correspondiente está habilitada.
7. Probar apertura/cierre y devolución de foco de dialogs.
8. Corregir la autoridad propietaria (shell/componente), evitando parches por URL.

## 8. Anti-patrones

- No añadir `outline: 2px solid ...` global y declarar F.4 terminado.
- No usar `outline:none` sin sustitución visible.
- No mover foco programáticamente en cada render.
- No crear `tabindex` positivos para arreglar orden.
- No esconder un sticky conflictivo solo en tests.
- No confundir `:hover` con focus.
- No considerar un screenshot desktop suficiente para móvil.
- No rebajar contraste/visibilidad para mantener estética.
- No marcar F.4 `VERIFIED_E2E` sin journey real.

## 9. Definition of Done

- [ ] journeys definidos para shell, diálogo, formularios y herramientas representativas;
- [ ] cada control enfocable muestra estado perceptible;
- [ ] Tab/Shift+Tab mantienen orden funcional;
- [ ] overlays reciben/devuelven foco correctamente;
- [ ] ningún target del journey queda obscured por UI persistente;
- [ ] 200%/Text Spacing no introduce ocultación nueva en journeys relevantes;
- [ ] artifacts permiten reproducir URL/paso/elemento;
- [ ] auditoría manual keyboard/browser complementa automatización;
- [ ] Pa11y/axe siguen como capas complementarias, no sustitutas.

## 10. Relación con otras ideas

- **F.1:** target grande pero sin foco visible sigue siendo insuficiente.
- **F.2:** reflow/text expansion puede hacer que un foco antes visible quede tapado.
- **F.6:** asistente necesita su propio journey de foco y announcements; F.6 no debe duplicar el auditor global.
- **R.1:** es la ampliación histórica Focus Not Obscured absorbida por F.4.
- **R.8/R.13:** forced colors/contrast ayudan a validar la perceptibilidad del indicador, pero son contratos adyacentes.

## 11. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — focus-visible original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `IMPLEMENT_AFTER_CURRENT_DEBT`, journeys más allá de Pa11y.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — WCAG.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — componentes/QA existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y `...OVERRIDES-REPO...` — revisados para no duplicar autoridades.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — estado intermedio `IMPLEMENTAR`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — wave de accesibilidad y reuse.
- `data/web-improvement-decisions-2026-08-28.json` — final `IMPLEMENT_AFTER_CURRENT_DEBT`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — incorpora explícitamente Focus Not Obscured 2.4.11.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión afianzada por W3C/WAI.
- pasadas posteriores / R.1 — aporte único: ampliar F.4 de visible a visible **y no oculto**.

## 12. Cierre

La versión madura de F.4 no pregunta únicamente “¿hay un outline?”. Pregunta si una persona que navega con teclado puede seguir el foco, percibirlo y verlo completo durante los journeys reales, incluso bajo la UI sticky/modal del sitio.