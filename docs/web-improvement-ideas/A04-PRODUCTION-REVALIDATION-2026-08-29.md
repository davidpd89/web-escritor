# A.4 · Revalidación e implementación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #153  
Decisión operativa: **IMPLEMENTED_IN_PR · READY_AFTER_CI**

> Autoridad operativa: este documento y el código del HEAD actual describen la implementación final. `A04-EVERGREEN-REVIEW-POLICY-2026-08-28.md` conserva la arqueología de #135 y, por ello, contiene formulaciones históricas de “futura implementación” que ya han sido ejecutadas en esta PR.

## Problema real confirmado

`main` ya tenía una autoridad correcta para fechas públicas: `scripts/check-article-dates.py` comprobaba la paridad entre:

- `datePublished` JSON-LD y la fecha visible de publicación;
- `dateModified` JSON-LD y la fecha visible de actualización;
- ausencia de “Actualizado” cuando `dateModified == datePublished`.

Pero no existía un lifecycle editorial separado para responder dos preguntas distintas:

1. **¿Cuándo se verificaron por última vez los hechos o fuentes de una pieza?**
2. **¿Cuándo debe volver a revisarse editorialmente?**

Usar `dateModified` para responderlas sería incorrecto: una revisión factual que no modifica sustancialmente la página no debe fabricar una fecha pública de actualización.

## Revalidación con fuentes primarias actuales

### Google · contenido people-first

https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Google pregunta expresamente si se cambian las fechas de páginas para que parezcan recientes cuando el contenido no ha cambiado de forma sustancial. También aclara que E-E-A-T no es por sí mismo un factor de ranking único. A.4, por tanto, se implementa como control editorial, no como truco de frescura.

### Google · fechas de publicación/actualización

https://developers.google.com/search/docs/appearance/publication-dates

Google distingue publicación de actualización significativa, recomienda coherencia entre fecha visible y structured data y desaconseja fechas futuras. Esto respalda mantener el reloj público separado del reloj interno de verificación.

### Google · Article structured data

https://developers.google.com/search/docs/appearance/structured-data/article

`datePublished` representa la publicación inicial y `dateModified` la modificación más reciente del artículo. No son campos de auditoría factual interna.

### Schema.org · `dateModified`

https://schema.org/dateModified

La propiedad describe la fecha en que un `CreativeWork` fue modificado. No modela una revisión que concluye “no hay nada que cambiar”.

## Schema final elegido

Se descartan las variantes históricas `lastVerified`, `lastVerifiedAt`, `lastReviewed`, `lastReviewedAt`, `reviewAt`, `reviewCadence` y calendarios paralelos.

La única forma autorizada es añadir opcionalmente **en una entrada concreta**, nunca en `defaults`, de `data/content-registry.json`:

```json
{
  "verifiedAt": "2026-08-29",
  "reviewBy": "2026-11-29"
}
```

Semántica:

- `verifiedAt`: última fecha en que se revisaron de verdad los hechos/fuentes relevantes de la pieza;
- `reviewBy`: fecha objetivo de la siguiente revisión editorial;
- ambos son `YYYY-MM-DD` y se declaran juntos;
- son metadatos internos de operación, no se proyectan automáticamente a JSON-LD ni a una fecha visible;
- `verifiedAt` **puede ser posterior a `dateModified`** si la revisión no exigió cambiar el contenido;
- si una página declara un `dateModified` posterior a `verifiedAt`, la verificación queda obsoleta y el checker falla hasta que los hechos vuelvan a comprobarse;
- `reviewBy` próximo (30 días) se reporta como `INFO`;
- `reviewBy` vencido se reporta como `WARNING`, no como error de integridad del build;
- los campos lifecycle no se admiten en `defaults`: una verificación es un acto editorial de una pieza concreta, no una fecha heredable global;
- los nombres históricos/experimentales se rechazan explícitamente para impedir que reaparezcan dos schemas equivalentes.

No se crea un segundo registry: el lifecycle vive en `content-registry.json`, que ya relaciona IDs, URLs y `sourceFile`.

## Correcciones tras la falsación final

La primera implementación de esta PR cometía dos excesos:

1. limitaba lifecycle a `cuaderno/**`, aunque #135 identifica recomendaciones, directorios, convocatorias y otras superficies con hechos externos como casos especialmente útiles;
2. convertía cualquier `reviewBy` vencido en un fallo de CI, contradiciendo la propia arquitectura histórica de #135, que separaba deuda editorial de corrupción de datos.

Ambos puntos quedan corregidos en el HEAD actual.

La revisión final detectó además dos vías de **schema drift** que también quedan cerradas:

3. declarar `verifiedAt`/`reviewBy` dentro de `defaults`, lo que permitiría heredar una misma fecha de verificación/revisión a piezas que no fueron auditadas individualmente;
4. reintroducir aliases históricos como `lastVerified`, `lastReviewed`, `reviewAt` o `reviewCadence`, creando dos vocabularios para la misma responsabilidad.

El checker rechaza ambos casos.

El lifecycle es ahora **source-agnostic**: cualquier entrada del registry con `sourceFile` real puede optar a `verifiedAt/reviewBy`. El contrato de fecha visible sigue siendo específico de los artículos de Cuaderno que ya controlaba el checker; no se fuerza una plantilla de fecha pública sobre páginas que no la tenían.

## Código implementado

### `scripts/check-article-dates.py`

Se extiende el checker existente, no se crea uno paralelo.

Conserva el contrato previo de fechas visibles del Cuaderno y añade:

- fechas de calendario reales, no solo forma `YYYY-MM-DD`;
- `dateModified >= datePublished` en el contrato existente;
- pareja obligatoria `verifiedAt` + `reviewBy` cuando una entrada activa lifecycle;
- lifecycle obligatorio por entrada concreta: se rechazan estos campos en `defaults`;
- aliases históricos/experimentales (`lastVerified*`, `lastReviewed*`, `reviewAt`, `reviewCadence`) rechazados;
- `verifiedAt` no puede estar en el futuro;
- `reviewBy` no puede preceder a `verifiedAt`;
- `sourceFile` debe existir;
- no puede haber dos lifecycle distintos para el mismo `sourceFile`;
- lifecycle permitido en cualquier familia del registry, no solo `cuaderno/**`;
- si el `sourceFile` expone `dateModified` en un `Article`, `BlogPosting`, `NewsArticle` o `WebPage`, `verifiedAt` no puede ser anterior a esa modificación sustancial;
- revisión dentro de 30 días = `INFO`;
- revisión vencida = `WARNING`;
- metadata incoherente, schema drift o fuente inválida = error de CI;
- ejecución estrictamente read-only.

Añade `--as-of YYYY-MM-DD` para tests y auditorías reproducibles y `--root`/`--registry` para fixtures deterministas.

### `tests/test-article-dates-lifecycle.py`

Cubre explícitamente 13 contratos:

1. compatibilidad con el comportamiento previo sin lifecycle;
2. `verifiedAt > dateModified` sin fake freshness;
3. review vencida visible pero no bloqueante;
4. modificación sustancial posterior a la verificación;
5. pareja incompleta de campos;
6. fecha imposible como `2026-02-30`;
7. `reviewBy < verifiedAt`;
8. `dateModified < datePublished`;
9. lifecycle real fuera de `cuaderno/**`, usando una superficie tipo Recomendaciones;
10. aviso `INFO` dentro de 30 días;
11. garantía read-only sobre HTML y registry;
12. lifecycle prohibido en `defaults`;
13. aliases lifecycle históricos rechazados para mantener un único schema.

### CI

`.github/workflows/content-index-check.yml` ejecuta:

- `python scripts/check-article-dates.py --check`;
- `python tests/test-article-dates-lifecycle.py`.

Además `Required merge gate` ejecuta todos los `tests/test-*.py`, así que el contrato semántico también queda protegido por el gate universal del repositorio.

## Por qué no se migran fechas lifecycle ficticias

El mecanismo está implementado, pero esta PR **no inventa una primera `verifiedAt`** para afirmar que un artículo o recomendación ha sido auditado factual y documentalmente cuando esa revisión concreta no se ha realizado dentro de A.4.

Eso no es una feature incompleta: es un guardrail. Activar lifecycle exige una verificación real del contenido y sus fuentes. Solo entonces se añaden `verifiedAt` y el siguiente `reviewBy` a la entrada correspondiente.

Una pieza estable puede permanecer sin lifecycle. Una pieza volátil puede incorporarlo cuando se haga su primera revisión factual. El checker ya soporta ambas familias.

## Política de severidad definitiva

```text
ERROR
  fecha imposible o futura
  verifiedAt/reviewBy incompletos
  reviewBy < verifiedAt
  sourceFile inexistente
  modificación sustancial posterior a verifiedAt
  lifecycle declarado en defaults
  alias lifecycle histórico/experimental
  incoherencia de fecha pública en el contrato ya existente

WARNING
  reviewBy vencido

INFO
  reviewBy dentro de los próximos 30 días
```

No existe un `ERROR` por simple paso del calendario. Si una futura familia necesita bloqueo release-critical, debe declararlo como un contrato explícito propio; A.4 no lo presupone.

## Alternativas descartadas definitivamente

1. **Actualizar `dateModified` cada vez que alguien “revisa” la página** — fake freshness.
2. **Usar mtime de Git/filesystem como fecha editorial** — una edición técnica no equivale a cambio sustancial.
3. **Crear `data/content-review-schedule.json`** — duplicaría IDs/URLs/sourceFile del registry existente.
4. **Mantener varios nombres equivalentes** — se fija `verifiedAt` + `reviewBy` y el checker rechaza aliases históricos.
5. **Cambiar `<lastmod>` al verificar hechos sin editar** — mezcla revisión interna con modificación pública.
6. **Programar todas las páginas con la misma cadencia** — la volatilidad real varía por familia; por eso lifecycle tampoco puede vivir en `defaults`.
7. **Hacer fallar cada PR porque venció un recordatorio** — confunde deuda editorial con integridad de build y genera bloqueos calendar-driven sin riesgo release-critical demostrado.
8. **Limitar lifecycle al Cuaderno** — impediría usar la capacidad precisamente en recomendaciones/directorios/convocatorias, donde más valor puede aportar.

## Definition of Done final

- [x] investigación histórica #135 preservada;
- [x] `main@291c8c6…` inspeccionado;
- [x] fuentes Google/Schema actuales revalidadas;
- [x] schema único `verifiedAt` + `reviewBy` elegido;
- [x] lifecycle obligatorio por entrada y no heredable desde `defaults`;
- [x] aliases históricos bloqueados para evitar schema drift;
- [x] código implementado sobre `check-article-dates.py`;
- [x] lifecycle separado de la fecha pública;
- [x] scope source-agnostic;
- [x] severidad de deuda editorial separada de errores de integridad;
- [x] fake freshness evitado estructuralmente;
- [x] 13 contratos de regresión cubiertos;
- [x] checker read-only probado;
- [x] integración CI existente mantenida;
- [x] no se fabrican verificaciones ni calendarios para rellenar el sistema.

**Conclusión:** A.4 está implementada en esta PR. Tras CI verde del HEAD final no queda una alternativa técnica superior pendiente dentro de su alcance.