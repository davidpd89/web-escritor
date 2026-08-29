# E.4 — Precarga selectiva de fuentes críticas

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`CONDITIONAL`**

## 1. Alcance

E.4 evaluó si debía precargarse la fuente variable/crítica de cabecera para acelerar el first paint. La investigación corrigió la tentación de “preload de fuentes = mejor rendimiento” y terminó en una regla conservadora:

> precargar únicamente la fuente/peso/estilo realmente crítico above-the-fold y solo después de revisar el waterfall.

Esta PR documenta la arqueología completa. No añade ni elimina preloads.

## 2. Veredicto

**`CONDITIONAL`**.

El sitio ya tiene `font-display: swap` y la Home actual precarga Yellowtail 400. Eso demuestra aplicación selectiva, no una deuda para precargar las demás familias.

Cualquier ampliación debe justificar:

- que la fuente se utiliza en el primer viewport;
- que su descubrimiento actual retrasa paint/LCP;
- que el preload no compite de forma negativa con CSS/imagen LCP;
- que se consume realmente en la navegación inicial.

## 3. Hipótesis original

La idea original decía revisar `font-display` y `preload` de fuentes de cabecera y limitar la precarga al peso/estilo realmente usado above-the-fold.

Aunque la formulación ya incluía cautela, todavía no estaba contrastada con el inventario real de fonts/preloads.

## 4. Evolución histórica

| Fase | Estado | Razón |
|---|---|---|
| Idea original | revisar/preload crítico | Evitar retraso de fuente de cabecera. |
| Revisión 108/108 | `CONDITIONAL` | Exceso de preloads compite por ancho de banda; revisar waterfall. |
| Matriz intermedia | `AUDITAR` | “Menos es mejor”; comprobar pesos/estilos realmente above-the-fold. |
| Autoridad final | `CONDITIONAL` | Precargar solo fuentes realmente críticas. |
| Revalidación independiente | mantenida | Sin necesidad de política global. |
| `main` actual | aplicación parcial | Home precarga Yellowtail; todas las faces revisadas usan `font-display: swap`. |

## 5. Fuente primaria recuperada

#135 consolidó:

- web.dev — font best practices;
- web.dev — optimización LCP como contexto de competencia por recursos.

La conclusión importante: el preload adelanta una descarga, pero esa descarga entra en competencia con otros recursos prioritarios. Por eso debe reservarse para fuentes realmente usadas en el primer render.

## 6. Inventario actual de fuentes

`assets/v1-fonts.css` declara actualmente:

- Marcellus 400;
- Inter 400;
- Inter 500;
- Merriweather 400;
- Merriweather 700;
- Yellowtail 400.

Todas utilizan `font-display: swap`.

La existencia de seis faces **no significa que deban existir seis preloads**.

## 7. Evidencia actual de Home

`index.html` ya contiene un preload explícito:

```html
<link rel="preload"
      as="font"
      type="font/woff2"
      href="assets/fonts/yellowtail-normal-400-latin.woff2"
      crossorigin />
```

Esto es coherente con el principio selectivo de #135 si Yellowtail participa realmente en el contenido above-the-fold.

La tarea de E.4 no es replicar automáticamente ese patrón en páginas interiores.

## 8. Qué medir

Para cada plantilla donde se sospeche retraso de fuente:

1. identificar texto first viewport y familia/peso reales;
2. waterfall sin cambios;
3. momento de descubrimiento de CSS y fuente;
4. impacto sobre text paint/LCP;
5. comprobar cache reuse;
6. pilotar preload si hay retraso accionable;
7. comparar bytes/prioridades y paint.

## 9. Riesgos del exceso de preload

### Competencia de red

Un font preload puede competir con:

- CSS crítico;
- imagen LCP;
- script esencial;
- otras fonts realmente prioritarias.

### Descarga no utilizada

Si la fuente no se usa pronto, el navegador puede advertir que el recurso precargado no fue utilizado y se han gastado bytes/priority inútiles.

### Duplicado por atributos incorrectos

Un `crossorigin`/URL/type inconsistente puede provocar que la descarga precargada no sea reutilizada como se esperaba.

### Multiplicación por plantilla

Copiar todos los preloads sitewide por comodidad destruye la selección basada en uso.

## 10. `font-display: swap`

El repo ya lo aplica a las faces revisadas. E.4 no necesita construir esta política desde cero.

`swap` reduce el riesgo de texto invisible prolongado, pero no significa que un cambio de font nunca produzca layout shift. Por eso las métricas visuales/CLS siguen siendo relevantes.

## 11. Relación con CLS

La historia reciente del proyecto presta especial atención a CLS. Una optimización de fuente no puede evaluarse solo por “se ve antes”.

Revisar:

- métricas compatibles;
- fallback stack;
- diferencias de ancho/altura;
- cambios de línea;
- estabilidad de header/hero.

No introducir hacks de tamaño solo para forzar métricas iguales sin revisar diseño.

## 12. Relación con E.3

Fuente crítica e imagen LCP compiten por prioridad. Añadir ambos preloads sin waterfall puede empeorar una página.

La decisión debe ser por contributor real:

- si LCP espera imagen → E.3;
- si paint espera font → E.4;
- si espera CSS/TTFB → resolver eso.

## 13. Relación con E.5

Los fonts son parte del budget de bytes del shell/familia. Si la arquitectura acumula demasiados pesos, E.5 puede detectar crecimiento; E.4 decide cuáles necesitan adelantarse, no cuántos pueden existir.

## 14. No hacer

- preload de todas las fonts declaradas;
- preload de todos los pesos “por si acaso”;
- precargar fonts below-the-fold;
- crear versiones duplicadas solo para preload;
- cambiar `font-display` sin revisar impacto visual;
- inlinear grandes WOFF2 en CSS;
- meter un SaaS de fonts externo;
- asumir que una fuente de marca siempre es el LCP contributor;
- considerar un warning de “unused preload” como algo que deba silenciarse sin corregir causa.

## 15. Gate de una nueva precarga

```text
USED_ABOVE_FOLD
AND DISCOVERY_DELAY_MEASURABLE
AND PRELOAD_REUSED
AND NO_IMPORTANT_RESOURCE_STARVATION
AND BEFORE_AFTER_IMPROVES
```

Si no se cumple, no añadirla.

## 16. Auditoría por familias

Muestra sugerida:

- Home;
- hub de obras;
- Manecillas;
- Samuel;
- Cuaderno hub;
- artículo largo;
- herramientas;
- autor/prensa.

No hace falta que todas terminen con la misma lista de preloads.

## 17. Criterio de éxito

Éxito no es:

> “cada plantilla tiene preload de fuente”.

Es:

- primer paint correcto;
- LCP no degradado;
- CLS controlado;
- no descargas prioritarias inútiles;
- cache reuse útil;
- dirección tipográfica preservada.

## 18. Pasadas tardías

Las pasadas posteriores no cambian E.4. Las investigaciones de Coverage/performance refuerzan la disciplina de medir uso antes de introducir optimizaciones globales.

## 19. Estado de verdad

- `DOCUMENTED`: sí.
- `font-display: swap` en autoridad actual: sí.
- preload selectivo en Home: sí.
- `IMPLEMENTED_IN_PR`: no.
- cobertura sitewide evaluada en browser waterfall: no.
- `VERIFIED_E2E`: no.

## 20. DoD de futura auditoría

- inventario de faces/pesos por plantilla;
- first viewport real observado;
- waterfall before;
- candidato justificado;
- preload consumido sin doble descarga;
- comparación before/after;
- CLS/reflow sin regresión;
- no preloads genéricos innecesarios.

## 21. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`.

Evidencia actual:

- `assets/v1-fonts.css`;
- `index.html`;
- `main` `291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## 22. Conclusión

E.4 permanece **`CONDITIONAL`**. El repositorio ya tiene la base correcta —WOFF2 locales, `font-display: swap` y al menos un preload selectivo—. La mejora no consiste en multiplicar hints, sino en comprobar el waterfall de cada familia y adelantar únicamente una fuente cuyo descubrimiento esté retrasando de forma medible el primer render.