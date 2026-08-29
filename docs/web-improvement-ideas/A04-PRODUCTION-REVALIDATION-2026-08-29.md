# A.4 · Revalidación e implementación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #153  
Decisión operativa: **IMPLEMENTED_IN_PR · READY_AFTER_CI**

## Problema real confirmado

`main` ya tenía una autoridad correcta para fechas públicas: `scripts/check-article-dates.py` comprobaba la paridad entre:

- `datePublished` JSON-LD y la fecha visible de publicación;
- `dateModified` JSON-LD y la fecha visible de actualización;
- ausencia de “Actualizado” cuando `dateModified == datePublished`.

Pero no existía todavía un lifecycle editorial separado para responder dos preguntas distintas:

1. **¿Cuándo se verificaron por última vez los hechos o fuentes de una pieza?**
2. **¿Cuándo debe volver a revisarse editorialmente?**

Usar `dateModified` para responderlas sería incorrecto: una revisión factual que no modifica sustancialmente la página no debe fabricar una fecha pública de actualización.

## Revalidación con fuentes primarias actuales

### Google · contenido people-first

https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Google pregunta expresamente si se cambian las fechas de páginas para que parezcan recientes cuando el contenido no ha cambiado de forma sustancial, y desaconseja esa práctica.

### Google · Article structured data

https://developers.google.com/search/docs/appearance/structured-data/article

`datePublished` representa la fecha de publicación original y `dateModified` la fecha de la modificación más reciente del artículo. Son señales temporales de la página, no un campo de auditoría editorial interna.

### Google · sitemaps

https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

Google indica que `<lastmod>` debe reflejar la última actualización **importante** de la página (contenido principal, structured data o enlaces, por ejemplo), no cambios irrelevantes. Por ello el lifecycle interno tampoco debe empujar artificialmente `lastmod`.

## Schema final elegido

Se descartan las variantes históricas `reviewAt`, `reviewCadence` y múltiples calendarios paralelos.

La única forma autorizada es añadir opcionalmente a la entrada canónica de `data/content-registry.json`:

```json
{
  "lastVerified": "2026-08-29",
  "reviewBy": "2026-11-29"
}
```

Semántica:

- `lastVerified`: última fecha en que se revisaron los hechos/fuentes relevantes de la pieza;
- `reviewBy`: fecha límite de la siguiente revisión editorial;
- ambos son `YYYY-MM-DD` y se declaran juntos;
- son metadatos internos de operación, no se publican automáticamente en JSON-LD;
- `lastVerified` **puede ser posterior a `dateModified`** si la revisión no exigió cambiar el contenido;
- una modificación sustancial posterior a `lastVerified` invalida esa verificación y obliga a verificar de nuevo;
- `reviewBy` vencido hace fallar CI hasta que se haga una revisión real y se reprograme conscientemente.

No se crea un segundo registry: el lifecycle vive en `content-registry.json`, la autoridad que ya relaciona IDs, URLs y `sourceFile`.

## Código implementado en esta PR

### `scripts/check-article-dates.py`

Se extiende el checker existente, no se crea uno paralelo.

Ahora valida además:

- fechas de calendario reales, no solo forma `YYYY-MM-DD`;
- `dateModified >= datePublished`;
- pareja obligatoria `lastVerified` + `reviewBy` cuando se usa lifecycle;
- `lastVerified` no puede estar en el futuro;
- `reviewBy` no puede preceder a `lastVerified`;
- `reviewBy` vencido falla;
- `sourceFile` del lifecycle debe existir;
- no puede haber dos lifecycle distintos para el mismo `sourceFile`;
- el lifecycle debe apuntar a un artículo de Cuaderno realmente inspeccionado;
- si `dateModified` es posterior a `lastVerified`, falla hasta revalidar;
- si `lastVerified` es posterior a `dateModified`, pasa sin alterar la fecha pública.

Añade `--as-of YYYY-MM-DD` para tests y auditorías reproducibles y `--root`/`--registry` para fixtures deterministas.

### `tests/test-article-dates-lifecycle.py`

Cubre de forma explícita:

1. compatibilidad con el comportamiento previo sin lifecycle;
2. reverificación posterior a `dateModified` sin fake freshness;
3. review vencida;
4. modificación posterior a la verificación;
5. pareja incompleta de campos;
6. fecha imposible como `2026-02-30`;
7. `reviewBy < lastVerified`;
8. `dateModified < datePublished`.

### CI

`.github/workflows/content-index-check.yml` ejecuta ahora:

- el checker real `python scripts/check-article-dates.py --check`;
- el test semántico `python tests/test-article-dates-lifecycle.py`.

La feature queda protegida por regresión en todas las PR.

## Por qué no se añaden fechas lifecycle arbitrarias hoy

El mecanismo está implementado, pero esta PR **no inventa calendarios** para artículos que no tengan una obligación editorial acordada.

Añadir `reviewBy` a todas las piezas por defecto produciría deuda artificial y una falsa sensación de precisión. El campo se activa únicamente cuando exista una razón factual concreta para revisar esa pieza (fuentes que cambian, datos externos, disponibilidad, normativa, convocatoria, etc.).

No tener lifecycle en un artículo estable es una decisión válida; tenerlo y dejarlo vencer no lo es.

## Alternativas descartadas definitivamente

1. **Actualizar `dateModified` cada vez que alguien “revisa” la página** — fake freshness.
2. **Usar mtime de Git o filesystem como fecha editorial** — una edición técnica no equivale a cambio sustancial.
3. **Crear `data/content-review-schedule.json`** — duplicaría IDs/URLs/sourceFile del registry existente.
4. **Mantener `reviewAt`, `reviewBy` y `reviewCadence` simultáneamente** — ambigüedad sin beneficio.
5. **Cambiar `<lastmod>` al verificar hechos sin editar** — contradice la semántica de actualización significativa.
6. **Programar todos los artículos con la misma cadencia** — no todos envejecen igual.

## Definition of Done final

- [x] investigación histórica preservada;
- [x] fuentes Google actuales revalidadas;
- [x] schema único elegido;
- [x] código implementado sobre la autoridad existente;
- [x] fake freshness evitado estructuralmente;
- [x] casos límite cubiertos por tests;
- [x] test incorporado a CI;
- [x] no se crean fechas editoriales ficticias para rellenar el sistema.

**Conclusión:** A.4 queda técnicamente implementada en esta PR. Tras CI verde, no queda trabajo de diseño o investigación dentro de su alcance antes del merge.
