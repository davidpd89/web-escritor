# E.1 — Escalera AVIF → WebP y auditoría de formatos de imagen

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`PARTIAL_AUDIT`**

## 1. Qué reconstruye esta PR

La idea E.1 nació como una propuesta bastante amplia: migrar imágenes a AVIF, usar `<picture>`, servir WebP/JPEG como fallback y reducir peso.

La investigación de #135 descubrió que el repositorio **ya tenía una implementación real y deliberadamente selectiva**. Por eso la idea dejó de ser “construir soporte AVIF” y pasó a ser:

> auditar qué imágenes importantes siguen sin escalera moderna y ampliar la autoridad existente solo cuando el ahorro material y el consumo real lo justifican.

Esta PR es documental. No convierte imágenes ni modifica manifests productivos.

## 2. Veredicto

**`PARTIAL_AUDIT`**.

No crear un nuevo pipeline. No convertir todo el repositorio a AVIF.

Autoridad ya existente:

- `scripts/build-image-format-ladder.py`;
- `scripts/check-image-format-ladder.py`;
- `data/image-format-ladder.json`;
- `scripts/check-responsive-images.py` y tests asociados;
- derivados AVIF versionados para los assets declarados.

La deuda neta es descubrir candidatos restantes y medirlos.

## 3. Hipótesis original

La lista inicial de ideas proponía:

- AVIF primero;
- WebP de respaldo;
- JPEG/PNG como fallback final;
- pipeline de build, no runtime;
- posible ahorro sustancial frente a JPEG/WebP.

Era una hipótesis tecnológica general y todavía no incorporaba la arquitectura real del repositorio.

## 4. Evolución de la decisión

| Fase | Estado | Razón |
|---|---|---|
| Idea original | migración amplia | AVIF como formato de mayor compresión + fallback. |
| Revisión 108/108 | `PARTIAL_AUDIT` | AVIF→WebP ya existía parcialmente; medir top assets antes de ampliar. |
| Repo cross-check | `PARTIAL_AUDIT` reforzado | Se localiza builder, checker, manifest con procedencia y responsive QA. |
| Matriz final | `YA_CUBIERTO PARCIAL / AUDITAR` | No hacer migración blanket. |
| Autoridad final | `PARTIAL_AUDIT` | Medir assets restantes y bytes antes de migrar masivamente. |
| Revalidación independiente | mantenida | No aparece motivo para sustituir la autoridad existente. |
| `main` actual | `PARTIAL_AUDIT` | Pipeline y manifest siguen vivos; solo cuatro tamaños de cubierta Manecillas están declarados. |

## 5. Hallazgo clave de arqueología del repo

La inspección profunda cambió la interpretación porque encontró una solución que ya cumplía gran parte de la idea.

### 5.1 Builder

`scripts/build-image-format-ladder.py` produce derivados desde una fuente declarada.

### 5.2 Checker

`scripts/check-image-format-ladder.py` verifica que manifest, fuentes y derivados no hayan derivado.

### 5.3 Manifest de autoridad

`data/image-format-ladder.json` mantiene:

- fuente;
- derivado;
- hash SHA-256 de la fuente;
- hash del derivado;
- encoder;
- versión del encoder;
- calidad/parámetros;
- política explícita de no convertir masivamente.

### 5.4 Responsive images

La escalera no vive aislada: el repo también tiene contratos para tamaños responsive, de modo que “usar AVIF” no sustituye elegir un tamaño físico adecuado.

## 6. Genealogía de implementación

La historia de Git muestra que E.1 no es una idea teórica.

### `d5eae66a1660473ce7337ec54db73f62caac1057`

Mensaje:

`L.1-L.2: escalera AVIF/WebP para cubierta Manecillas, autoridad unica de microcopy del asistente`

Es el punto de materialización de la escalera para la cubierta de Manecillas.

### `6f945e137ca6bd5e25e92db8789bc7449da99c18`

`fix(images): make AVIF builder provenance-aware`

Endurece la solución con procedencia reproducible.

### `0d4d05e19c5ca746f9847efa9542aac3685b9225`

`fix(images): let builder initialize and repair provenance safely`

Corrige la inicialización/reparación de esa procedencia.

Esta genealogía explica por qué #135 termina en `PARTIAL_AUDIT`: reconstruir otro pipeline sería regresivo.

## 7. Estado actual de `main`

En `main` `291c8c677aaa7df635142687d1a6848e80ffcaa2`, `data/image-format-ladder.json` sigue con schema 2 y declara explícitamente una política selectiva.

Los items actualmente revisados son cuatro tamaños de la cubierta de Manecillas:

- 320;
- 512;
- 768;
- 1024.

Cada WebP declarado tiene su hermano AVIF con hashes y encoder fijados.

Esto demuestra:

- `IMPLEMENTED`: sí, para esa familia;
- cobertura universal: no;
- necesidad de un segundo pipeline: no.

## 8. Qué pregunta queda abierta

No es:

> ¿soporta el sitio AVIF?

La pregunta útil es:

> ¿qué imágenes públicas importantes siguen consumiendo bytes evitables y se beneficiarían de entrar en la escalera existente?

## 9. Auditoría correcta

Orden recomendado:

1. inventariar imágenes públicas realmente usadas;
2. agrupar por familia/rol;
3. obtener bytes actuales por tamaño;
4. identificar LCP/hero/portadas de alto tráfico;
5. comprobar si ya tienen tamaños responsive;
6. generar candidato AVIF con parámetros controlados;
7. comparar bytes;
8. revisar calidad perceptual/editorial;
9. confirmar que el HTML realmente consumirá el derivado;
10. solo entonces añadir al manifest.

## 10. Priorización

Prioridad mayor:

```text
LCP/hero pesado y repetido
> portada/editorial grande de alto tráfico
> imagen muy pesada below-the-fold
> asset pequeño/decorativo con ahorro irrelevante
```

No usar número de archivos convertidos como KPI.

## 11. Bytes antes que moda

AVIF no gana automáticamente en todos los activos.

Casos donde puede no compensar:

- WebP ya muy pequeño;
- ilustración donde el encoder introduce artefactos;
- imagen servida siempre a tamaño pequeño;
- derivado AVIF casi igual o mayor;
- coste de mantenimiento superior al ahorro real.

El manifest selectivo actual refleja precisamente esta conclusión.

## 12. `<picture>` no es el objetivo por sí mismo

Un `<picture>` correcto puede servir:

```html
<picture>
  <source type="image/avif" srcset="...">
  <source type="image/webp" srcset="...">
  <img src="..." alt="...">
</picture>
```

pero si el navegador descarga un asset sobredimensionado, el formato moderno no resuelve el problema completo.

E.1 debe coordinarse con responsive images y LCP, no perseguir sintaxis.

## 13. No hacer

- script que recorra todas las imágenes y genere AVIF indiscriminadamente;
- borrar WebP/JPEG originales porque existe AVIF;
- derivadas sin procedencia reproducible;
- reencodear un derivado desde otro derivado si la autoridad define fuente original;
- cambiar quality para “ganar” bytes sin revisión visual;
- convertir assets no consumidos;
- introducir SaaS/CDN de imágenes solo para esta idea;
- duplicar `image-format-ladder.json`;
- atribuir mejoras de ranking a usar AVIF.

## 14. Relación con E.3 / LCP

Una imagen puede ser candidata a la escalera por impacto LCP. Pero:

- E.1 optimiza representación/bytes;
- E.3 controla prioridad de fetch del candidato LCP.

No son intercambiables.

## 15. Relación con performance budget

E.5 puede detectar crecimiento de bytes agregado. E.1 es una de las acciones posibles cuando una familia de imágenes domina el budget.

El budget no debe obligar automáticamente a reencodear imágenes sin revisar calidad.

## 16. Relación con social cards

Las imágenes OG tienen requisitos de compatibilidad distintos. Una card social puede necesitar JPEG aunque la misma imagen visual tenga AVIF/WebP en página.

No convertir tarjetas sociales ciegamente.

## 17. Gate para añadir una imagen

Un candidato debe cumplir:

```text
PUBLIC_CONSUMED
AND bytes_saving_material
AND quality_acceptable
AND responsive_variant_plan_correct
AND markup_consumes_derivative
```

Si falla cualquiera, no se añade por cumplir una checklist.

## 18. DoD de una futura ampliación

Por cada nuevo source:

- hash fuente registrado;
- encoder/version/quality registrados;
- derivado reproducible;
- checker verde;
- bytes before/after registrados;
- revisión visual suficiente;
- HTML real usa la variante;
- fallback se conserva;
- no regresión responsive/LCP.

## 19. Pasadas tardías

Las pasadas posteriores de #135 no promueven una migración masiva. La quinta/décima pasada refuerzan el patrón “medir antes de optimizar”, incluido Coverage para CSS/JS como principio equivalente.

La revalidación independiente mantiene E.1.

## 20. Fuentes primarias históricas

#135 consolidó, entre otras:

- web.dev — optimización LCP;
- documentación de buenas prácticas de performance;
- evidencia propia del pipeline del repo.

La decisión final depende más de la implementación real y mediciones que de porcentajes genéricos de ahorro publicados por terceros.

## 21. Estado de verdad

- `DOCUMENTED`: sí, esta PR.
- `IMPLEMENTED_IN_PR`: no, docs-only.
- `IMPLEMENTED_MAIN` de la capacidad base: sí, existe la escalera.
- `MERGED_MAIN` de esta PR: no.
- `CONFIGURED_LIVE`: no se verifica aquí qué variantes negocia cada navegador live.
- `VERIFIED_E2E`: no.

## 22. Fuentes históricas consultadas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- pasadas posteriores de performance.

Evidencia actual:

- `data/image-format-ladder.json`;
- builders/checkers actuales;
- historial de commits `d5eae66…`, `6f945e1…`, `0d4d05e…`.

## 23. Conclusión

E.1 permanece **`PARTIAL_AUDIT`**. El trabajo valioso no es “añadir AVIF”: esa capacidad ya existe con una autoridad reproducible. Lo pendiente es detectar imágenes de impacto real que aún no estén cubiertas, medir ahorro/calidad y ampliar exactamente el pipeline vigente sin convertir el repositorio entero por moda tecnológica.