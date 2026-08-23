# Pendiente S — Auditoría Claude líneas 401–600

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `claude pending.txt`, líneas 401–600 exactamente.

## Regla de alcance

Este brief solo recoge deuda que sigue siendo real después de contrastar la fuente con HEAD, todas las PR abiertas, código y QA actuales. El documento histórico `27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md` ya no es una cola automática de ejecución: `ADOPTAR`, `P0`, `P1` o un filename propuesto allí no bastan para abrir trabajo nuevo.

No tocar `main`, no desplegar producción y no activar auto-merge desde esta rama.

---

# S.1 — La entidad Book de Manecillas no enlaza su muestra gratuita

**Clasificación: DEUDA NUEVA REAL.**

## Evidencia actual

La ficha canónica:

`/las-manecillas-del-recuerdo/`

define una entidad:

```json
{
  "@type": "Book",
  "@id": "https://davidportodiaz.com/#book-manecillas",
  "name": "Las manecillas del recuerdo",
  "isbn": "979-8-90514-935-1",
  "numberOfPages": 272,
  "datePublished": "2026-09-03"
}
```

pero no declara `hasPart`, `subjectOf` ni una relación equivalente hacia la muestra pública existente:

`https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/`

La página de fragmentos sí modela el otro lado:

- `WebPage.about` → `https://davidportodiaz.com/#book-manecillas`;
- `Collection` `#sample` con `isBasedOn` → `#book-manecillas`;
- tres `CreativeWork` con `isPartOf` → `#book-manecillas`;
- `isAccessibleForFree: true`;
- canonical propio y tres fragmentos identificados.

Por tanto, la relación semántica existe desde la muestra hacia el libro, pero la entidad principal del libro no expone de forma explícita que esa muestra es parte/derivación accesible de la obra.

No hay PR abierta que contenga `hasPart`, `ReadAction` o este vínculo Book↔fragmentos.

## Contrato vigente

Schema.org permite `hasPart` en `CreativeWork`; `Book` hereda de `CreativeWork`. Es suficiente para expresar una relación estructurada sin inventar entidades nuevas.

La implementación debe elegir la representación más simple y consistente con el grafo actual. Preferencia de contrato:

```json
{
  "@type": "Book",
  "@id": "https://davidportodiaz.com/#book-manecillas",
  "hasPart": {
    "@id": "https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#sample"
  }
}
```

Alternativamente puede justificarse una relación equivalente soportada por Schema.org si mantiene los mismos IDs canónicos y no duplica contenido.

`ReadAction` puede estudiarse como complemento, pero **no es requisito para cerrar S.1**. No añadir markup más complejo solo porque aparecía en una receta histórica.

## Qué NO hacer

- No crear `Chapter` para los tres fragmentos si el contenido actual no los modela editorialmente como capítulos independientes completos.
- No copiar en la página del libro las tres entidades `CreativeWork` que ya viven en la página de muestra.
- No crear una segunda entidad Book con otro `@id`.
- No introducir `Offer`, precio, URL de compra o retailer no verificado para resolver este punto.
- No alterar ISBN, número de páginas, editorial, fecha, género o descripción desde este scope.
- No publicar contenido nuevo.
- No recrear obligatoriamente el filename histórico `apply-book-sample-schema.py`; importa el contrato, no aquella receta concreta.

## Autoridad de IDs

Preservar:

- Book: `https://davidportodiaz.com/#book-manecillas`
- muestra: `https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#sample`
- página: `https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/`

`scripts/check-canonical-entity-ids.py` ya fija `#book-manecillas` como ID canónico y debe seguir pasando.

## QA requerido

Añadir una regresión determinista —extensión de un checker existente o test estrecho— que falle si:

1. la entidad canónica `Book` de Manecillas desaparece o cambia de `@id`;
2. la ficha del libro deja de apuntar al `#sample` canónico;
3. el `#sample` de `/fragmentos/` deja de relacionarse con `#book-manecillas`;
4. los tres fragmentos dejan de pertenecer al libro o se rompe el grafo JSON-LD;
5. aparecen dos IDs distintos para la misma obra.

El test debe parsear JSON-LD, no hacer un simple grep de strings.

Como mínimo, ejecutar al cerrar:

```bash
python scripts/check-canonical-entity-ids.py
python scripts/validate-jsonld.py
```

y el nuevo/extendido test del contrato Book↔sample.

Si la ruta tiene un builder o fuente de datos que pueda regenerar el JSON-LD, modificar primero la autoridad correspondiente; no parchear únicamente el HTML generado si eso introduce drift.

---

# Hallazgos reutilizados — NO abrir deuda paralela

## Runtime / INP del botón «Volver al inicio»

**Clasificación: YA DETECTADO — #61 H.1.**

El HEAD confirma que el click aún hace:

```js
scheduleTask(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
}, "user-visible");
```

La respuesta visual primaria de un input queda aplazada por `scheduler.postTask`. Se añadió comentario a #61 para resolverlo dentro del runtime scoping/performance, manteniendo background el show/hide ligado a scroll.

## Runtime global / CSS global

**Clasificación: YA DETECTADO — #61 H.1.**

Las recetas antiguas de `split-runtime.py` y `split-runtime-css.py` no son autoridad de filenames. El contrato vigente ya está en #61: scoping real, módulos por responsabilidad y decisión explícita sobre CSS del modal Samuel.

## Fechas visibles y permalinks

- fecha Publicado/Actualizado + checker → **#57 D.1**;
- permalinks de sección → **#57 D.2**, ya declarado opcional;
- `premios.html` / speculationrules → **#57 D.4**.

No duplicar.

## Update dates

**Clasificación: YA DETECTADO — #54.**

`.github/workflows/update-dates.yml` continúa teniendo owner propio para retirar la doble autoridad sobre sitemap.

## Smoke / producción

**Clasificación: YA DETECTADO — #58 + #1/#74.**

El antiguo `check-production-launch.py` no se debe reconstruir por nombre. El contrato vigente es smoke post-deploy, `build-public-dist --check-contents`, CI del SHA final y readiness vivo antes de main.

## FAQPage / compatibilidad

- retirada de `FAQPage` legacy → **#66 K.2**;
- smoke cross-engine / compatibilidad práctica → **#66 K.3**;
- Playwright reproducible/cache → **#65**.

La ausencia de los filenames históricos de visual-regression no demuestra por sí sola deuda: el repo actual dispone de múltiples QA de navegador y #66 ya posee la cobertura cross-engine. No crear una infraestructura de screenshots frágil solo para reproducir el documento 27.

## DOI, honeypot, rate limit

**Clasificación: YA DETECTADO — #55.**

No duplicar desde el documento 16.

## Manecillas «Cómo se escribió»

**Clasificación: YA DETECTADO/GATED — #75 R.1.**

La ruta solo puede activarse cuando existan ≥4 notas reales de proceso. No inventar artículos para satisfacer el gate.

## Autores

**Clasificación: GATED / bug parcial ya #59.**

- builder que crashea → #59 F.1;
- publicación del directorio → gated hasta disponer de perfiles reales/autorizados suficientes.

## Revisor de diálogo

**Clasificación: YA DETECTADO — #59 F.2.**

No confundirlo con la herramienta `/herramientas/dialogo/` ya existente.

---

# Hallazgos que NO se convierten en PR nueva

## «¿Te ha servido esta guía?»

**Clasificación: PROGRESIVO / IDEA HISTÓRICA.**

No hay widget binario actual, pero su ausencia no constituye regresión ni requisito V1 vigente. Requiere primero decidir finalidad, privacidad, almacenamiento/analítica y utilidad real. No abrir código solo porque el documento 27 lo marcaba como mejora.

## IndexNow

**Clasificación: GATED / OPERATIVO.**

El propio material histórico advierte que no debe duplicarse una integración automática del proveedor. Hay clave/root file e indicios de integración Cloudflare; antes de crear un submitter propio hay que verificar el comportamiento real externo. No se abre PR de código en este bloque.

## Visual regression por screenshots

**Clasificación: SUPERADO/PARCIAL.**

El repo actual ya contiene QA browser de reflow, Cuaderno, recomendaciones, identidad, home map, herramientas, Lighthouse, pa11y, etc., y #66 K.3 amplía el contrato cross-engine. Un sistema de baselines pixel-perfect sería una decisión distinta y costosa de mantener, no un hueco demostrado por la mera ausencia del filename propuesto en 2026-08-16.

## Artículos Cuaderno ausentes

**Clasificación: GATED EDITORIAL.**

La fuente menciona varias rutas no publicadas. No se convierten automáticamente en deuda de código: hay que disponer de contenido real, evidencia y decisión editorial. La relación del hub de proceso ya está en #75 R.1.

## Image sitemap

**Clasificación: POSTLAUNCH / PROGRESIVO.**

La propia propuesta histórica la relegaba a P1 postlanzamiento. No es un blocker del release actual ni una deuda autónoma de este bloque.

## Social / Metricool

**Clasificación: OUT OF SCOPE.**

Calendario, posts, reels, programación y publicación social no generan tareas en el repositorio web.

---

# Corte estricto

Las líneas 598–600 empiezan tres ideas del antiguo documento 30:

- «Observatorio de escritura y lectura en español»;
- «Pregunta del mes a escritores»;
- recursos embebibles / tarjeta «Estoy leyendo».

Su contexto continúa después de la línea 600. **No se clasifican todavía** y no generan deuda en S. La auditoría se detiene exactamente en la línea 600; se decidirán únicamente al leer el bloque siguiente.

## Resultado del bloque 401–600

Deuda independiente nueva: **S.1 — relación estructurada Book↔muestra de Manecillas.**

Todo lo demás queda reutilizado, gated, progresivo, superado o fuera de alcance según lo anterior.
