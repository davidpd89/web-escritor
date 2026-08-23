# Pendiente M — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 1001–1200

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Alcance estricto: únicamente deuda real que sobrevive al contraste de las líneas 1001–1200 con el repositorio actual. No reabrir trabajo ya resuelto, ya detectado o gated. No anticipar lo que continúa después de la línea 1200.

## 1. Resultado del bloque

### 33 — Announcements + time-sensitive UI

**GATED correctamente.** No existe un caso temporal real que justifique construir ahora una infraestructura global de banners/countdowns. No crearla preventivamente.

### 34 — Content resilience + edge states

La deuda de `relatedIds`/grafo editorial ya estaba detectada en auditorías anteriores: no duplicarla.

El TXT también registra como deuda un antiguo truncado de una línea en títulos de recomendaciones (`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`). Al contrastarlo con la capa V1 vigente, esa afirmación ya no describe el estado actual: `assets/v1-recommendations.css` aplica wrapping robusto con `overflow-wrap:anywhere` tanto en los títulos del índice como en `.rec-book-title`. **SUPERADO; no reabrir.**

### 35 — Microtipografía editorial

Sin deuda técnica nueva. La excepción del `<br>` editorial de Home no se convierte en bug sin evidencia visual de regresión. La QA responsive ya es la autoridad para detectarlo si alguna vez rompe un viewport.

### 36 — Mobile runtime + viewport

Sin deuda nueva. La validación física final iOS/Android/TalkBack pertenece al gate de device lab ya conocido.

### 37 — LAB Home V1

Resuelto para su propósito: el LAB permanece aislado/noindex y los elementos elegidos ya se trasladaron al sistema V1. Los gates finales de CWV/device/browser son deudas globales ya registradas, no del LAB.

### 38 — Navegación V1

Aquí sí aparece una desviación nueva y reproducible: el contrato final auditado pide **cinco territorios estables**; `data/navigation.json` declara actualmente seis entradas en `exploreTerritories`:

1. `work-manecillas`
2. `author`
3. `work-samuel`
4. `notebook-hub`
5. `tools-hub`
6. `press`

Sin embargo, `data/content-registry.json` ya modela correctamente `work-manecillas` y `work-samuel` como hijos del territorio `obras`, cuyo hub canónico es `works-hub` (`/libros/`, etiqueta «Obras»).

Resultado: la capa de presentación de Explorar eleva dos obras individuales a la categoría de territorio y omite el territorio estable «Obras».

---

# 2. M.1 — Alinear `exploreTerritories` con los cinco territorios estables

## Problema

El modelo semántico y la navegación de presentación no están alineados:

- registry: `works-hub` es el hub de `territory: obras`;
- `work-manecillas` y `work-samuel` pertenecen a `works-hub`;
- navegación: ambos libros aparecen como territorios independientes;
- `works-hub` no aparece en `exploreTerritories`.

Esto hace que la arquitectura de Explorar dependa de títulos concretos de catálogo, en vez de mantenerse estable cuando crezcan las obras del autor.

## Implementación requerida

1. Ajustar `data/navigation.json` para que `exploreTerritories` represente exactamente cinco territorios estables:
   - `works-hub` — Obras;
   - `author` — Autor;
   - `notebook-hub` — Cuaderno;
   - `tools-hub` — Herramientas;
   - `press` — Prensa.
2. No eliminar el acceso prominente a `Las manecillas del recuerdo` ni a `Samuel entre mundos`; deben seguir accesibles dentro de Obras y mediante las superficies contextuales que ya correspondan. Esta tarea solo corrige la jerarquía de **territorios** de Explorar.
3. Regenerar/actualizar el shell mediante su autoridad existente; no editar docenas de copias de navegación a mano si el builder/contrato puede hacerlo.
4. Mantener `exploreShortcuts`, `footer`, `homeMap` y `localNavSets` salvo que una consecuencia estrictamente necesaria del cambio exija alinearlos. No convertir esta tarea en un rediseño general de navegación.
5. Preservar orden, accesibilidad, preview, teclado, Escape, retorno de foco, no-JS y responsive del diálogo Explorar.
6. Revisar el preview de `works-hub`: debe describir el territorio Obras sin degradar Manecillas como obra actual. No inventar una nueva IA visual.

## Refuerzo de contrato / QA

El checker actual `scripts/check-navigation-coverage.py` valida que cada referencia de `navigation.json` exista y sea pública, pero no comprueba que `exploreTerritories` represente hubs/territorios estables. Por eso el estado actual puede pasar CI aunque la jerarquía sea semánticamente incorrecta.

Añadir una validación determinista que, como mínimo:

- exija exactamente cinco entradas en `exploreTerritories`;
- exija los IDs canónicos acordados: `works-hub`, `author`, `notebook-hub`, `tools-hub`, `press`;
- impida volver a introducir `work-manecillas` o `work-samuel` como territorios de primer nivel;
- confirme que todos los IDs resuelven a entradas públicas del registry;
- compruebe que el shell generado refleja el mismo conjunto y orden;
- mantenga verdes las pruebas de navegación/accesibilidad existentes.

No duplicar el trabajo del checker global de discoverability ni crear una segunda autoridad de navegación: ampliar el contrato existente.

## Criterios de aceptación

- [ ] `exploreTerritories` contiene exactamente cinco territorios estables.
- [ ] `works-hub` sustituye a los dos libros como territorio de primer nivel.
- [ ] Manecillas y Samuel siguen siendo encontrables desde Obras y sus rutas/contextos existentes.
- [ ] `data/navigation.json` y el shell público no divergen.
- [ ] un test falla si se vuelve a introducir un libro individual como territorio.
- [ ] navegación con teclado, foco, Escape y no-JS sigue funcionando.
- [ ] no se modifica `main`, no se despliega producción y no se activa auto-merge.

---

# 3. No duplicar en esta PR

- `relatedIds` / grafo editorial: deuda ya conocida.
- titles/labels responsive de Recomendaciones: el truncado descrito en el TXT ya está superado en V1.
- device lab / TalkBack / iOS físico: gate ya conocido.
- CWV y cierre final de release: gates globales ya registrados.
- Pagefind: sigue P1/pospuesto según el contrato auditado; no convertir su ausencia en deuda de esta ronda.
- anuncios/countdowns: gated hasta existir un caso temporal real.
- Metricool/redes sociales: fuera del proyecto web por decisión del propietario.

# 4. Límite de la ronda

La auditoría termina **exactamente en la línea 1200**. El documento 38 continúa después; no incorporar en esta PR hallazgos que solo aparezcan a partir de la línea 1201. Si el siguiente bloque modifica o contradice este diagnóstico con autoridad posterior, deberá revisarse en la ronda 1201–1400 antes de integrar.

---

# 5. Estado de implementación (2026-08-23)

- `data/navigation.json`: `exploreTerritories` pasa de 6 entradas
  (`work-manecillas`, `author`, `work-samuel`, `notebook-hub`, `tools-hub`,
  `press`) a exactamente los 5 territorios estables acordados: `works-hub`,
  `author`, `notebook-hub`, `tools-hub`, `press`.
- `scripts/build-site-shell.py`: el copy de `works-hub` (fila y aside del
  preview) ya existía preparado desde antes («La obra actual.», idéntico
  al de `work-manecillas`) pero sin usarse. Se redacta un copy propio que
  describe el territorio Obras en plural **sin degradar** a Manecillas
  como obra actual: «Las manecillas del recuerdo, la obra actual, y el
  resto de novelas publicadas.»
- Shell regenerado en las 59 páginas V1 (`python scripts/build-site-shell.py`).
- Manecillas y Samuel entre mundos **siguen siendo alcanzables**: Manecillas
  vía el atajo «Leer un fragmento» y ambos dentro de Obras (`/libros/`).
  No se ha tocado `exploreShortcuts`, `footer`, `homeMap` ni
  `localNavSets`.
- **Gate reforzado**: `scripts/check-navigation-coverage.py` (ya wireado en
  3 workflows existentes: `content-index-check.yml`,
  `findability-browser-qa.yml`, `global-discoverability-closure-qa.yml`,
  sin duplicar ninguno) ahora exige exactamente los 5 territorios en el
  orden acordado y bloquea explícitamente que `work-manecillas`/
  `work-samuel` vuelvan a aparecer como territorios de primer nivel.
- **Test nuevo**: `tests/test-check-navigation-coverage-territories.py`
  (5 casos, contra el checker real y el `navigation.json` real con
  backup/restauración) + `qa/explore-territories-browser.mjs` (Chromium
  real): confirma los 5 territorios y sus `href`, que Manecillas no es
  territorio de primer nivel pero sigue siendo alcanzable, y que
  apertura/cierre, foco de entrada y retorno de foco con Escape del
  diálogo Explorar siguen intactos.

## Evidencia de ejecución (real)

```
$ python scripts/check-navigation-coverage.py
PASS: navigation coverage (60 registry routes, 54 sitemap routes, 17 interactive tools)

$ python scripts/build-site-shell.py --check
CHECK: shell en 59 páginas

$ python tests/test-check-navigation-coverage-territories.py
  ok   navigation.json real con los 5 territorios estables pasa
  ok   reintroducir work-manecillas como territorio se detecta
  ok   reintroducir work-samuel como territorio se detecta
  ok   menos de 5 territorios se detecta
  ok   orden distinto de los 5 territorios se detecta
tests/test-check-navigation-coverage-territories: OK

$ QA_CHROMIUM_EXECUTABLE_PATH=... node qa/explore-territories-browser.mjs
explore-territories-browser: PASS

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 68 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 88 HTML files scanned; 0 broken local reference(s).

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs

$ node qa/sitewide-reflow-browser.mjs
sitewide-reflow-browser: OK (67 routes, 2 viewports, 134 checks)

$ python tests/test-samuel-ecosystem-parity.py
samuel-ecosystem-parity: OK
```

**Prueba en rojo real**: el propio test
`test-check-navigation-coverage-territories.py` reintroduce
`work-manecillas`/`work-samuel` como territorios y confirma que
`check-navigation-coverage.py` lo bloquea, sobre el `navigation.json` real
del repo (con backup/restauración automática, nunca queda modificado).