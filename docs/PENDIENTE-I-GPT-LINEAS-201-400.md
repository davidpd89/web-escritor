# Pendiente I — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 201–400

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR contrasta únicamente las líneas **201–400** del fichero de Drive `pendiente funcionalidad gpt.txt` contra el repositorio real, sus tests/CI y las PR abiertas. El TXT se usa como lista de comprobación, no como autoridad de implementación. No tocar `main`, no desplegar producción y no activar auto-merge.

## 1. Resultado de la auditoría 201–400

### 1.1 Backlog editorial real, pero NO desarrollo de código todavía

Las líneas 201–209 proponen tres territorios editoriales que no constan todavía como piezas publicadas:

- novelas sobre memoria familiar que no idealizan el pasado;
- libros sobre abuelos y nietos para lectores adultos;
- novelas donde los objetos guardan memoria.

El propio documento condiciona su publicación a obras realmente leídas/verificadas. Por tanto, no se deben fabricar páginas o artículos vacíos para cerrar una checklist. Esto queda como **backlog editorial**, no como bug de implementación.

### 1.2 Artículo «fantasía juvenil española 2025–2026» — decisión editorial pendiente

El contenido sigue físicamente presente pero aislado con `noindex, follow`. La auditoría mantiene la conclusión correcta: antes de reindexar hay que **reconstruir, fusionar o retirar** con una decisión editorial explícita.

No se abre una tarea de código para “ponerlo index” ni se elimina automáticamente desde esta PR. La infraestructura de cuarentena ya existe; falta decisión de contenido.

### 1.3 Colección «Manecillas y memoria» — GATED por densidad

El sistema de colecciones temáticas ya aplica un gate de densidad. La colección no debe crearse hasta existir al menos tres piezas reales y suficientemente sustantivas. No hay bug por su ausencia actual.

Cuando el cluster tenga masa crítica, se podrá añadir como dato del sistema de colecciones existente; no hace falta diseñar otra arquitectura.

### 1.4 Search Console — pendiente operativo, no necesariamente código

Las líneas 241–254 piden seguimiento por URL de impresiones, clics, CTR y posición, además de conversiones internas. El repositorio no puede certificar por sí solo el estado real de Search Console.

Esto queda como **gate operativo externo**. No se crea un script ficticio de Search Console ni se da por cerrado mediante CI local.

### 1.5 «Detrás del libro» y club de lectura de Manecillas — GATED editorial

Las piezas de proceso y el club de lectura de Manecillas están expresamente condicionados a que exista contenido real suficiente y al momento editorial adecuado. Samuel sí tiene ecosistema propio; Manecillas no debe copiarlo mecánicamente para cerrar una casilla.

Clasificación: **pendiente editorial / no fallo de implementación**.

### 1.6 Brevo / doble opt-in / automatización — YA CUBIERTO

Las líneas 310, 326 y 354–355 vuelven a señalar la verificación de automatizaciones y doble confirmación. Esa deuda ya está recogida en la **PR #55**, junto con retorno DOI, honeypot y rate limiting. No duplicar aquí.

La configuración y verificación real de Brevo/Cloudflare siguen siendo gates externos incluso después de implementar la parte de repo.

### 1.7 QA final cross-browser / producción — YA CUBIERTO O RELEASE GATE

Las líneas 326 y 359 mencionan QA final Safari/Firefox/Chrome/móvil real y performance/visual sobre el HEAD definitivo.

- Smoke test post-deploy y `build-public-dist --check-contents`: **PR #58**.
- Imágenes responsive/global media QA: **PR #61 H.3**.
- Reflow, Lighthouse, accesibilidad y múltiples suites browser ya existen y el HEAD auditado tiene workflows asociados en verde.
- La certificación humana sobre la build definitiva sigue siendo un **release gate**, no una funcionalidad faltante que deba duplicarse.

### 1.8 `script.js` global — YA CUBIERTO

Las líneas 334–360 vuelven a señalar la modularización pendiente de `script.js`. Esa deuda ya está descrita con criterios de aceptación en **PR #61 H.1**. No crear otra tarea para lo mismo.

### 1.9 Política de privacidad / base jurídica — GATED por revisión legal

La línea 379 detecta correctamente que `privacidad.html` mantiene una formulación general de base legal por consentimiento expreso para todos los tratamientos, incluida medición agregada.

La **PR #14**, ya integrada, dejó esto deliberadamente sin reescribir porque cambiar bases jurídicas por inferencia no es una corrección puramente técnica. El runtime y la página legal tienen QA, pero la elección/redacción de base jurídica debe cerrarse con revisión jurídica o una decisión documentada del responsable.

No modificar desde esta PR el art. 6 RGPD ni introducir una base legal alternativa sin esa decisión.

---

# 2. DEUDA TÉCNICA NUEVA REAL

## I.1 — Falta una taxonomía analítica canónica y sitewide

Las líneas 381–393 del TXT identifican una carencia que **no queda completamente resuelta por la PR #61**.

La PR #61 H.2 tiene alcance concreto: instrumentar el funnel de **Las manecillas del recuerdo** sin inventar eventos de compra mientras no exista retailer real. Este nuevo hallazgo es más amplio: el sitio carece de un contrato único que gobierne todos los eventos de producto/contenido/newsletter y evite seguir mezclando nombres heredados.

### Evidencia reproducible en el HEAD auditado

`script.js` continúa emitiendo eventos con familias heterogéneas, entre ellas:

- `abrir-modal-comprar`;
- `comprar-amazon`;
- valores `data-gc` como `comprar-amazon-papel` / `comprar-casadellibro`;
- `leer-fragmento`;
- `explorar-noveris`;
- `ver-prensa`;
- `download-press-kit`;
- `newsletter-quiz`;
- `newsletter-<source>`;
- `newsletter-popup`;
- `article-<name>` mediante el bridge `dp:analytics`.

La función `_gcEvent(path, title)` acepta libremente cualquier `path`; no hay un registro canónico de nombres/dimensiones ni un validador que impida drift entre módulos.

En el árbol actual no existe un asset/dato/checker dedicado que actúe como autoridad global de taxonomía analítica. Los workflows del HEAD están verdes, pero ninguno de esos gates demuestra coherencia semántica de los nombres de evento.

### Problema funcional

Con la situación actual:

1. un mismo concepto puede tener nombres distintos según superficie;
2. algunos nombres codifican proveedor (`amazon`) y otros acción (`abrir-modal-comprar`);
3. no existe una dimensión estable y verificable para distinguir libro, destino, fuente o superficie;
4. una refactorización puede introducir otra nomenclatura sin que CI falle;
5. el futuro funnel de Manecillas (#61 H.2) corre el riesgo de añadir una tercera convención si primero no se fija el contrato global.

### Implementación requerida

1. Crear una **autoridad única de eventos** apta para un sitio estático sin framework ni bundler. Puede ser un módulo JS pequeño, JSON validado o combinación equivalente, pero debe existir una sola definición canónica.
2. Definir una convención semántica estable para, como mínimo:
   - lectura/muestra;
   - apertura de selector/compra;
   - salida a retailer;
   - newsletter;
   - navegación editorial relevante;
   - descargas/recursos;
   - eventos de herramientas/artículos que ya pasan por `dp:analytics`.
3. Separar **acción** de **dimensiones/contexto** cuando el proveedor lo permita. Si GoatCounter obliga a codificar contexto en `path`, documentar una serialización determinista y testeable.
4. Migrar los nombres legacy relevantes a la convención elegida sin doble disparo permanente.
5. Mantener compatibilidad temporal solo si es imprescindible para continuidad histórica; si se hace, debe tener fecha/criterio de retirada y nunca generar dos conversiones lógicas por una sola acción.
6. Hacer que #61 H.2 consuma esta taxonomía para Manecillas en vez de inventar otra.
7. No crear eventos de compra de Manecillas mientras `purchaseUrl`/retailers sigan sin verificar.
8. No declarar `newsletter_confirmed` desde el frontend si solo se conoce que el Worker aceptó el alta; una confirmación DOI real exige evidencia del sistema de email.

### Criterios de aceptación

- [ ] existe un contrato canónico documentado y machine-checkable de eventos;
- [ ] cada evento de producto/contenido relevante tiene acción y contexto inequívocos;
- [ ] Samuel y Manecillas no pueden mezclarse en una misma conversión por falta de identidad de obra;
- [ ] retailers se distinguen sin crear nombres ad hoc nuevos en cada HTML;
- [ ] newsletter distingue `submit/accepted` de una confirmación DOI real;
- [ ] el bridge `dp:analytics` queda alineado con el mismo contrato o con una capa de adaptación explícita;
- [ ] un test falla si aparece un evento literal no registrado en las superficies auditadas;
- [ ] un test/browser QA verifica que una acción de usuario produce un único evento lógico;
- [ ] no se rompe GoatCounter ni se introduce GA4/otro proveedor solo para satisfacer nombres históricos;
- [ ] #61 H.2 se rebasa/coordina para usar este contrato cuando se implemente el funnel Manecillas;
- [ ] CI relevante queda en verde sin rebajar assertions.

### Orden recomendado

1. Inventariar todos los eventos actuales del HEAD y sus superficies.
2. Definir contrato canónico y estrategia de compatibilidad histórica.
3. Crear checker/fixture de taxonomía.
4. Migrar runtime común y `data-gc`.
5. Adaptar módulos que emiten `dp:analytics`.
6. Coordinar con #61 H.2 para Manecillas.
7. Ejecutar browser QA y comprobar ausencia de doble conteo.

---

# 3. Lo que esta PR NO debe hacer

- No crear artículos SEO sin fuentes/lecturas reales.
- No reindexar automáticamente el artículo 2025–2026.
- No crear la colección «Manecillas y memoria» antes de la masa crítica.
- No fingir acceso/validación de Search Console desde el repo.
- No publicar «cómo se escribió» ni club de Manecillas sin material autorizado.
- No duplicar #55, #58 o #61.
- No reescribir bases jurídicas de `privacidad.html` por inferencia técnica.
- No inventar retailers, `Offer` ni conversiones de compra de Manecillas.
- No introducir otro proveedor de analítica por conveniencia.

# 4. Estado del HEAD y CI usado como referencia

HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`.

Los workflows asociados consultados para ese SHA aparecen completados con `success`, entre ellos Lighthouse CI, Pa11y, Sitewide Reflow QA, Privacy legal browser QA, Machine authority, Content indexes, Manecillas fragments navigation QA y Release Readiness Pre-Main. Esto acredita la salud del snapshot, pero **no valida una taxonomía analítica que actualmente no tiene checker propio**.

# 5. Límite exacto de esta ronda

La auditoría termina en la **línea 400** del TXT. La sección `10_RECOMENDACIONES_Y_AUTORIDAD.md` empieza en la línea 395, pero sus tres carencias concretas continúan después de la línea 400 y quedan deliberadamente para la siguiente ronda; no se anticipan aquí.

**DRAFT / NO MAIN / NO AUTO-MERGE / NO PRODUCCIÓN.**

---

# 6. Estado de implementación (2026-08-23)

- **Inventario completo** de los eventos emitidos hoy (paso 1 del orden
  recomendado): 16 nombres literales directos (`_gcEvent`/`data-gc`) + 25
  nombres crudos disparados vía el bridge `dp:analytics` desde 12 módulos
  distintos de herramientas del Cuaderno.
- **Autoridad única**: `data/analytics-events.json` — cada nombre literal
  documentado con `action`/`context`/nota, incluida la aclaración
  explícita de que `newsletter-*` es aceptación del Worker, **no**
  confirmación DOI real (criterio de aceptación #8).
- **Checker nuevo**: `scripts/check-analytics-taxonomy.py` (+
  `tests/test-check-analytics-taxonomy.py`, 6 casos) — falla si aparece un
  evento `_gcEvent`/`data-gc` no registrado, o un nombre `dp:analytics` no
  registrado para su módulo. Probado en rojo contra el repo real (ver
  evidencia abajo).
- **Migraciones aplicadas** (sin doble disparo, un solo commit, no queda
  compatibilidad legacy paralela):
  - `abrir-modal-comprar` → `abrir-modal-comprar-samuel` (identidad de
    libro explícita en el nombre).
  - `leer-fragmento` → `leer-fragmento-samuel` / `leer-fragmento-manecillas`.
    **Bug real corregido de paso**: el patrón `/fragmento/` (singular)
    nunca coincidía con la ruta real de Manecillas
    (`/las-manecillas-del-recuerdo/fragmentos/`, plural) — esos clics no
    se contaban en absoluto antes de esta PR.
- **Retailers ya distinguidos** sin nombres ad hoc nuevos:
  `comprar-amazon` (genérico) vs `comprar-amazon-papel`/`comprar-casadellibro`
  (`data-gc` específicos del modal de Samuel) — documentados, no
  renombrados (ya seguían la convención `{acción}-{contexto}`).
- **Coordinación con #61 H.2**: los nombres `leer-fragmento-samuel`/
  `leer-fragmento-manecillas` y la convención de identidad de libro en el
  nombre son los mismos que ya usa #61 (desarrollada en paralelo) — al
  fusionar ambas ramas sobre `implementacion-web-2026`, el conflicto en
  `script.js` es el mismo cambio por ambos lados, trivial de resolver.
- **`dp:analytics`/bridge**: sin cambios de contrato — ya usaba un prefijo
  (`article-`) uniforme; se documenta explícitamente en el registro en vez
  de dejarlo implícito.
- No se ha introducido ningún proveedor de analítica nuevo ni se ha
  tocado GoatCounter.

## Evidencia de ejecución (real)

```
$ python scripts/check-analytics-taxonomy.py --check
Analytics taxonomy check: 64 ficheros JS revisados, 0 incumplimiento(s).

$ python tests/test-check-analytics-taxonomy.py
  ok   evento _gcEvent registrado no genera error
  ok   evento _gcEvent NO registrado se detecta
  ok   data-gc no registrado se detecta
  ok   nombre dp:analytics no registrado se detecta
  ok   nombre dp:analytics registrado no genera error
  ok   fichero nuevo con dp:analytics sin registrar se detecta
tests/test-check-analytics-taxonomy: OK

$ node qa/analytics-taxonomy-browser.mjs
analytics-taxonomy-browser: PASS

$ node --check script.js
(sin errores)

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 68 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 88 HTML files scanned; 0 broken local reference(s).

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs
```

**Prueba en rojo real** (regla de la casa: no inventar un PASS): se añadió
temporalmente `_gcEvent("evento-jamas-registrado", "x")` a `script.js` →
`check-analytics-taxonomy.py --check` lo detectó y falló como se esperaba
→ revertido antes de continuar.
