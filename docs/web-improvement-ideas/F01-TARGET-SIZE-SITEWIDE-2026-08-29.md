# F.1 · Auditoría sitewide de Target Size

**Estado histórico final de PR #135:** `IMPLEMENT_NOW`  
**Base normativa:** WCAG 2.2 · 2.5.8 Target Size (Minimum)  
**Principio del proyecto:** 24×24 CSS px es el mínimo normativo con excepciones; no autoriza a rebajar contratos visuales propios de 42px.  
**Naturaleza de esta PR:** documentación/arqueología; no cambia tamaños de controles.

## 1. Hipótesis original

La lista original pedía extender a toda la web la disciplina que ya se había aplicado al hamburger: auditar todos los controles táctiles, no solo un componente aislado.

La idea era correcta, pero #135 la refinó para evitar dos errores opuestos:

1. considerar que todo elemento menor de 24px es automáticamente un fallo, ignorando las excepciones de WCAG para targets inline/spacing;
2. usar el mínimo WCAG de 24px como excusa para rebajar componentes que el diseño del proyecto ya protege a 42px.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis abierta | Llevar la disciplina del hamburger a toda la web. |
| Revisión 108/108 | `IMPLEMENT_NOW` | WCAG 2.5.8: 24×24 CSS px o spacing/excepción válida. El contrato de 42px del proyecto sigue siendo más estricto donde ya existe. |
| Matriz operativa | `IMPLEMENTAR` | Auditor sitewide, no simple grep de CSS; proteger el diseño actual. |
| Blueprint W2 | implementación concreta | Descubrir targets en navegador, medir caja real, clasificar excepciones y mantener una lista mínima de contratos superiores como `.explore-trigger`/`.header-search` = 42. |
| Historia posterior del repo | evidencia práctica | PR #128 relajó una aserción del hamburger a 24px; la reconciliación #130 registró que hacerlo debilitaba el regression bar porque el CSS seguía implementando deliberadamente 42px. |
| Autoridad final | `IMPLEMENT_NOW` | Auditoría sitewide con norma de 24px y contratos superiores explícitos. |
| Revalidación independiente | mantenido | WCAG 2.2 confirma el criterio. |

## 3. Fuente normativa

Fuente primaria conservada por #135:

- W3C/WAI, WCAG 2.2 Understanding 2.5.8 Target Size (Minimum): `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum`

El contrato que #135 extrae de esa fuente es deliberadamente preciso:

- el tamaño mínimo general es 24×24 CSS px;
- existen excepciones, entre ellas targets inline y situaciones donde el spacing permite cumplir el requisito;
- la auditoría debe analizar geometría/relación espacial real, no solo ancho/alto aislado de cualquier `<a>`;
- una organización puede mantener objetivos más grandes por UX/diseño; cumplir 24px no obliga a reducirlos.

## 4. Evidencia real del proyecto

### Hamburger / header

Antes y durante #135 el proyecto ya utilizaba un contrato de aproximadamente 42px para determinados controles móviles. Esto era una decisión de diseño/UX, no una lectura equivocada de WCAG.

La secuencia #128 → #130 es evidencia importante:

- #128 cambió una aserción QA a `>=24px` al corregir supuestos obsoletos del test;
- #130 observó después que ese cambio reducía el regression bar respecto al comportamiento real de 42×42px y exigió volver a proteger el contrato superior mientras el CSS siguiera implementándolo.

Por tanto, F.1 no debe homogeneizar toda la web a 42px ni rebajar toda la web a 24px: debe distinguir **mínimo normativo**, **excepciones válidas** y **contratos de producto más estrictos**.

## 5. Blueprint W2 recuperado

El auditor browser propuesto por #135 parte de una lista de elementos interactivos equivalente a:

```js
const INTERACTIVE = [
  'a[href]',
  'button',
  'input:not([type="hidden"])',
  'select',
  'textarea',
  'summary',
  '[role="button"]',
  '[role="link"]'
].join(',');
```

Y debe ignorar targets no utilizables/visibles:

- `display:none`;
- `visibility:hidden`;
- cajas de 0×0;
- elementos inertes/no interactivos según corresponda.

Por cada target útil interesa registrar al menos:

- URL/ruta;
- selector o identificación reproducible;
- tag/role;
- ancho y alto reales de `getBoundingClientRect()`;
- texto/label accesible o fragmento identificativo;
- `href` cuando exista;
- clasificación: cumple por tamaño, excepción inline, cumple por spacing, o fallo real;
- contrato superior aplicable, si existe.

## 6. Contratos superiores

#135 propuso una lista pequeña y deliberada, no una regla global de “42 para todo”. Ejemplo histórico:

```json
{
  ".explore-trigger": 42,
  ".header-search": 42
}
```

La semántica correcta es:

- 24px = baseline WCAG donde aplica;
- 42px = decisión local del producto que debe seguir protegida mientras continúe siendo la intención visual/UX;
- otros valores superiores solo se añaden si existe una decisión real documentada.

No se deben añadir contratos superiores arbitrarios para inflar el test.

## 7. Veredicto reconciliado

F.1 sigue siendo `IMPLEMENT_NOW` como capacidad de QA. La implementación correcta es un **auditor sitewide con reporte y clasificación de excepciones**, no una regla CSS masiva.

La existencia de algunos controles ya protegidos no convierte F.1 en `ALREADY_COVERED`: la idea es precisamente ampliar la cobertura a todas las superficies públicas elegibles y evitar regresiones silenciosas.

## 8. Qué no hacer

- No fallar cada enlace inline que mida menos de 24×24.
- No añadir padding visual indiscriminado a enlaces dentro de párrafos.
- No transformar iconos/enlaces en tarjetas o círculos solo para pasar el checker.
- No usar 24px para rebajar un control de 42px que el diseño sigue requiriendo.
- No usar 42px como nuevo mínimo universal si no está justificado.
- No medir solo CSS declarado; la caja renderizada real es la que importa.
- No considerar Pa11y/axe suficiente para cerrar geometría táctil sitewide.
- No ocultar overflow o cambiar zoom para esconder un fallo de target.

## 9. Plan de implementación futuro

1. Reutilizar el descubrimiento de rutas públicas/capacidades browser existente en QA, evitando otro crawler.
2. Ejecutar en viewports táctiles representativos, incluido móvil estrecho.
3. Recoger geometría de todos los targets visibles.
4. Clasificar automáticamente casos evidentes y generar reporte para excepciones contextuales.
5. Mantener un fichero pequeño de contratos superiores del producto, no una lista infinita de selectores.
6. Corregir únicamente fallos reales en el componente/autoridad propietaria.
7. Añadir regresión al contexto CI que de verdad bloquee merge si esa es la política aprobada.
8. Generar artifact diagnóstico aunque el run falle para no perder offenders.

## 10. Definition of Done

- [ ] todas las familias públicas elegibles quedan auditadas;
- [ ] targets invisibles/inert no generan falsos positivos;
- [ ] enlaces inline y otras excepciones se clasifican conforme a WCAG, no por heurística simplista;
- [ ] los contratos superiores existentes se prueban por separado;
- [ ] no se reduce silenciosamente ningún contrato 42→24;
- [ ] el reporte identifica URL + componente + dimensiones + motivo;
- [ ] los fallos reales tienen fixture/regresión o caso browser reproducible;
- [ ] mobile/reflow existentes siguen verdes;
- [ ] la documentación deja claro qué es WCAG y qué es decisión de diseño propia.

## 11. Relación con otras ideas/pasadas

- **F.2:** target size debe sobrevivir también a `font-size:200%` y Text Spacing sin solapes/cortes.
- **F.4:** foco visible y no-obscured necesita targets realmente operables por teclado/touch.
- **D.11:** empty states pueden introducir nuevos botones/enlaces; deben entrar en el auditor.
- **R.1 Focus Not Obscured:** complementa F.4, no sustituye F.1.
- **R.8/R.13:** Forced Colors/`prefers-contrast` son otra wave de accesibilidad; no mezclar su paleta con geometría de target.

## 12. Trazabilidad del corpus histórico

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — origen de F.1.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `IMPLEMENT_NOW`, 24px frente a 42px.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — W3C/WAI.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — QA/controles existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y `...OVERRIDES-REPO...` — reglas de no duplicación y evidencia posterior.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W2 íntegro.
- `data/web-improvement-decisions-2026-08-28.json` — `IMPLEMENT_NOW` final machine-readable.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — estado y redacción final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — status mantenido contra WCAG 2.2.
- historial de PR #128/#130 — evidencia posterior concreta de por qué 24px no debe rebajar el contrato propio de 42px.
- pasadas posteriores — revisadas; las ondas de contraste/foco son adyacentes y no cambian el estado final de F.1.

## 13. Cierre

F.1 no consiste en “poner todo a 42px”. Consiste en conocer la geometría táctil real del sitio, aplicar correctamente WCAG 2.5.8 y preservar, donde existen, contratos de producto más exigentes sin confundirlos con el mínimo normativo.