# Auditoría conservadora de higiene del repositorio — 2026-08-27

## 0. Objetivo

Esta auditoría reduce basura real del repositorio sin confundir «antiguo», «audit», «pendiente» o «no publicado» con «inútil».

Regla de borrado de esta PR:

> Un fichero solo se elimina cuando puede demostrarse que ya no cumple ninguna función de runtime, build, QA, operación, trazabilidad vigente, decisión futura o material de diseño todavía reutilizable.

Si existe una duda razonable, NO se elimina. Se clasifica como `KEEP`, `ARCHIVE-CANDIDATE` o `REVIEW`.

La historia de Git conserva los ficheros eliminados. Esta PR limpia el árbol activo y la superficie pública; no reescribe el historial Git.

## 1. Importante: «aligerar la web» y «aligerar el repo» son dos cosas distintas

El contrato de publicación actual es allowlist-first (`scripts/build-public-dist.py`). `docs/`, `qa/`, `lab/`, `scripts/`, `tests/`, `data/`, migrations y configuración técnica no forman parte del artefacto público normal.

Por tanto:

- borrar documentación obsoleta reduce ruido del checkout, búsquedas y contexto para humanos/agentes, pero no reduce directamente los bytes descargados por un lector;
- borrar una superficie accidental dentro de un namespace público, como `herramientas/auditor-web/`, sí reduce el artefacto publicado;
- el gran peso físico del repo está en `assets/`, no en Markdown. No se aborda todavía de forma destructiva porque existe material de campaña y diseño que está deliberadamente sin referenciar mientras el rediseño sigue abierto.

No se realizará history rewriting (`git filter-repo`, BFG, force-push) dentro de esta limpieza. Es una operación distinta y de mucho mayor riesgo.

## 2. Estados usados

- `DELETE-NOW`: se demuestra que es basura o implementación histórica ya cerrada.
- `KEEP`: tiene función actual o una decisión futura explícita.
- `ARCHIVE-CANDIDATE`: parece histórico/sustituido, pero todavía contiene información que debe consolidarse antes de borrar.
- `REVIEW`: falta evidencia suficiente para decidir.

## 3. Borrados seguros de esta primera ronda

### 3.1 `.claude/settings.local.json` — DELETE-NOW

Motivos:

- por convención es configuración local de Claude Code;
- contiene rutas concretas de una máquina Windows y permisos personales;
- incluye permisos amplios como `git push` y `gh api *` que no deben convertirse en política compartida del repositorio;
- no contiene una configuración de producto que necesite versionarse;
- mantenerlo trackeado aumenta el riesgo de que en el futuro se añadan tokens, rutas privadas o permisos locales al repo.

Acción:

- eliminar el fichero versionado;
- añadir `.claude/settings.local.json` a `.gitignore`.

### 3.2 `qa/.pr61-runtime-trigger` — DELETE-NOW

El propio contenido dice literalmente:

`PR61 runtime cleanup trigger; remove before final review.`

Es un trigger one-shot de una PR ya pasada. No tiene valor futuro ni debe permanecer como QA.

### 3.3 `scripts/audit-author-web.py` + `herramientas/auditor-web/` — DELETE-NOW

Ficheros:

- `scripts/audit-author-web.py`
- `herramientas/auditor-web/index.html`
- `herramientas/auditor-web/report.txt`

Motivos:

- el script solo genera `herramientas/auditor-web/report.txt` mediante una pasada de `validate_jsonld.py`;
- `herramientas/auditor-web/` no figura en `data/tools-hub.json`;
- tampoco figura en `data/content-registry.json`;
- no es una herramienta para usuarios: es un informe técnico de mantenimiento;
- al vivir bajo `herramientas/`, entra en el namespace que sí se publica y deja accesible una superficie técnica `noindex` sin necesidad;
- el repo actual ya tiene gates más fuertes de JSON-LD, machine authority, discoverability, content indexes y QA, por lo que no hace falta publicar un `report.txt` estático para mantener esta comprobación.

NO confundir con `herramientas/auditor-pagina-libro/`: ese sí es un producto público real, aparece en `tools-hub.json`, tiene reglas propias (`assets/book-page-audit-rules.js`) y se conserva.

### 3.4 `publicar-web/index.html` — DELETE-NOW

Es una checklist interna `noindex` con instrucciones como ejecutar `build-sitemap.py`, validar JSON-LD y revisar enlaces. No está en `content-registry`, no está en la allowlist pública y duplica runbooks/scripts actuales. Además enlaza a una página `lecturas/` que hoy es fixture no publicado.

No aporta valor como HTML mantenido en la raíz. Git conserva su historial.

### 3.5 `docs/CLAUDE-HANDOFF-PR106-AUDITORIA-PROFUNDA-III.md` — DELETE-NOW

Su único objetivo declarado era servir de handoff a la PR #109, sucesora de #106. La PR #109 está cerrada y mergeada (merge commit `d279076dc3dff46f3588ead2f801e4c8e98c430d`).

Conservar el handoff después de ejecutar la PR hace que futuros agentes puedan volver a tratar como pendientes tareas ya implementadas. Se conservan, por ahora, los documentos de auditoría/cierre de Profunda III como registro del diagnóstico.

### 3.6 `docs/PENDIENTE-I-PLAYWRIGHT-UNIFY.md` — DELETE-NOW

Es el diario de una implementación ya terminada: unificación de Playwright/CI. El estado actual del repo ya contiene `package.json`/lock y Playwright `1.62.1`; el documento marca sus pruebas como completadas.

La autoridad actual es el código/lockfile/workflows, no el diario de la PR.

### 3.7 `docs/PENDIENTE-J-SHELL-BOILERPLATE.md` — DELETE-NOW

Describe una refactorización one-shot ya aplicada para retirar boilerplate duplicado de builders y documenta outputs byte-identical/tests completados. No contiene una decisión operativa futura que deba seguir consultándose.

Git conserva el cambio y su explicación histórica.

## 4. Carpetas y ficheros revisados que se conservan

### 4.1 `herramientas/` — KEEP salvo `auditor-web`

El inventario actual contiene herramientas públicas reales como contador, diálogo, legibilidad, repeticiones, variedad léxica, POV, metadatos, JSON-LD, kit de prensa, entrevista familiar, etc. `data/tools-hub.json` actúa como inventario explícito de producto.

Decisión:

- `auditor-pagina-libro/`: KEEP — producto público real.
- `auditor-web/`: DELETE-NOW — informe técnico accidental.
- resto de herramientas registradas: KEEP.

Regla futura: cualquier nueva carpeta bajo `herramientas/` debe estar en `tools-hub.json` o estar explícitamente marcada como interna y fuera del artefacto público.

### 4.2 `scripts/audit-private-tools.py` — KEEP

Aunque contiene `audit` en el nombre, no es un informe histórico. Es un preflight reutilizable que protege la promesa de privacidad de las herramientas de manuscrito: detecta red, storage, recursos remotos, CSP y forms que podrían sacar texto del navegador.

Borrarlo reduciría una garantía técnica real.

### 4.3 familia `scripts/check-*.py` — KEEP por defecto

Los `check-*` actuales son contratos de regresión, no documentos de auditoría one-shot. Entre otros cubren:

- AI discoverability;
- taxonomía analítica;
- fechas;
- versiones de assets;
- contrato/copy del asistente;
- entidades canónicas;
- hechos editoriales;
- discoverability;
- headings;
- enlaces/graph;
- imágenes;
- navegación;
- cuarentena Noveris;
- assets huérfanos;
- recomendaciones;
- runtime scoping;
- secretos;
- social cards.

No se eliminará un checker simplemente por no estar llamado desde todos los workflows. Primero hay que demostrar que su contrato está absorbido por otro checker y sus fixtures/tests.

### 4.4 `scripts/check-orphan-assets.py` + `docs/PENDIENTE-G-ORPHAN-ASSETS.md` — KEEP

Este es precisamente el instrumento que debe usarse en una limpieza posterior de `assets/`.

La decisión documentada del 22/08 es no borrar todavía los cientos de assets sin referencia porque mezclan:

- campañas sociales que no se enlazan desde HTML;
- fotografía/arte destinado al rediseño todavía abierto;
- posibles huérfanos reales.

La siguiente fase deberá clasificar cada asset con procedencia y uso previsto. No se ejecuta `--delete` a ciegas.

### 4.5 `docs/PENDIENTE-K-MINIFICATION-REPORT.md` + `scripts/report-minification-savings.py` — KEEP

La decisión de producción sigue abierta: el informe mide beneficio real de minificación, pero introducir minificación implica una decisión sobre build/deploy. Tiene valor futuro hasta que esa decisión se cierre.

### 4.6 `docs/PENDIENTE-CLS-FERIA-MADRID-2026-08-27.md` — KEEP

El commit actual de `main` referencia explícitamente este fichero como trazabilidad del residual CLS que sigue sin explicación completa. No es histórico cerrado.

### 4.7 `lab/` — REVIEW, no borrar en esta PR

El lab está fuera del artefacto público, pero contiene prototipos, migration matrices, QA, signatures y familias visuales todavía relacionadas con el rediseño activo y con la PR de diseño/UX.

Puede existir mucho material superado, pero una eliminación global sería prematura. Debe auditarse archivo a archivo comparándolo con:

- diseño actualmente implementado;
- contratos vigentes de Drive;
- PR #114 y siguientes;
- cualquier asset/prototipo que siga sirviendo de referencia.

Objetivo posterior: conservar solo masters/decisiones vigentes y retirar variantes descartadas.

### 4.8 `lecturas/` — REVIEW, no borrar todavía

`lecturas/index.html` es actualmente un fixture `noindex,nofollow` y no entra en la allowlist pública. Podría parecer basura, pero existe `scripts/build-reading-list.py` y un CSS específico, por lo que hay una feature potencial detrás.

Antes de borrar hay que decidir si la funcionalidad «Qué estoy leyendo» seguirá en roadmap. Hasta entonces no cumple el estándar `100% innecesario`.

### 4.9 `migrations/assistant-quota.sql` — KEEP

La capa remota del asistente está desactivada, pero la arquitectura futura no se ha eliminado. La migración sirve si se reactiva el backend; no es un temporal demostrado.

## 5. `docs/`: primera pasada fichero a fichero

La carpeta `docs/` mezcla cuatro clases distintas y esa mezcla explica buena parte del ruido:

1. contratos/runbooks que siguen gobernando el sistema;
2. auditorías con decisiones pendientes;
3. diarios/handoffs de PR ya completadas;
4. evidencia/provenance puntual.

No se debe borrar toda la clase `AUDITORIA-*` o `PENDIENTE-*` por nombre.

### DELETE-NOW confirmado

- `CLAUDE-HANDOFF-PR106-AUDITORIA-PROFUNDA-III.md`
- `PENDIENTE-I-PLAYWRIGHT-UNIFY.md`
- `PENDIENTE-J-SHELL-BOILERPLATE.md`

### KEEP confirmado en esta ronda

- `PENDIENTE-G-ORPHAN-ASSETS.md` — decisión futura vigente.
- `PENDIENTE-K-MINIFICATION-REPORT.md` — decisión build/deploy abierta.
- `PENDIENTE-CLS-FERIA-MADRID-2026-08-27.md` — investigación activa referenciada desde `main`.
- `BREVO-WORKER-DEPLOY.md` — runbook operativo.
- `CLOUDFLARE-OPERATIONS-ALERTS-STAGING.md` — runbook operativo.
- `CLOUDFLARE-ZONE-CDN-SECURITY-RUNBOOK.md` — runbook operativo.
- `CLOUDFLARE-FINAL-OPTIMIZATION-ADDENDUM.md` — conservar hasta consolidar decisiones Cloudflare en una única autoridad.
- `ASSISTANT-ARCHITECTURE-RESEARCH-V3.md`, `ASSISTANT-CONVERSATION-CATALOG-V3.md`, `ASSISTANT-EDITORIAL-UX-V2.md`, `ASSISTANT-FREE-FIRST-BENCHMARK-V4.md` — arquitectura/futuro del asistente; no se demuestra obsolescencia solo porque el remoto esté desactivado.

### ARCHIVE-CANDIDATE / requiere consolidación antes de borrar

- `PENDIENTE-H-CSP-PUBLICO.md`: la implementación está terminada y existe workflow CSP; contiene todavía razonamiento sobre limitaciones del CSP por `<meta>` que conviene consolidar antes de borrar.
- `PENDIENTE-H-GPT-LINEAS-1-200.md`: gran parte de H.1/H.2/H.3 figura implementada, pero el documento también registra gates editoriales/externos. Debe compararse con autoridades posteriores.
- `PENDIENTE-I-GPT-LINEAS-201-400.md`: la taxonomía analítica ya se implementó, pero conserva gates editoriales/legal/externos.
- `PENDIENTE-K-GPT-LINEAS-401-600.md`: contiene estado de implementación, pero también contratos sobre evidencia de recomendaciones, cross-engine y cuarentenas. Confirmar que todos quedaron absorbidos antes de retirar.
- `AUDITORIA-MIGRACION-2026-08-22.md`: histórico de migración; revisar referencias vigentes.
- `AUDITORIA-PROFUNDA-III-*`: mantener por ahora como diagnóstico/cierre; una futura consolidación puede retirar el detalle una vez exista un ADR/estado actual equivalente.

### REVIEW todavía no cerrado

- `PENDIENTE-A-UPDATE-DATES.md` — probablemente ligado al gate de 03/09/2026; revisar después del lanzamiento.
- `PENDIENTE-B-BREVO-WORKER-DOI.md` — configuración externa aún relevante hasta verificar Brevo real.
- `PENDIENTE-BROWSER-BLOCKED-TASKS.md`
- `PENDIENTE-D-SEO-CONTENIDO.md`
- `PENDIENTE-E-QA-SMOKE-TEST.md`
- `PENDIENTE-F-HERRAMIENTAS-GAPS.md`
- `PENDIENTE-FUNCIONALIDAD-2026-08-22.md`
- `PENDIENTE-J-OPERATIVA-WEBS-EXTERNAS.md`
- `PENDIENTE-L-GPT-LINEAS-801-1000.md`
- `PENDIENTE-M-GPT-LINEAS-1001-1200.md`
- `PENDIENTE-N-GPT-LINEAS-1201-1400.md`
- `PENDIENTE-NUEVAS-IDEAS-MOBILE-CONTENT-RESILIENCE-QA.md`
- `HOYMADRID-VERIFICACION-2026-08-22.md` — evidencia puntual; comprobar si facts/provenance ya están en autoridad canónica antes de retirar.
- `CONTENT-PARITY-MANECILLAS-V1.md`
- `BANNER-ART-DIRECTION-V5.md`
- `DISENO-FINAL-AE-CONNECTION-SYSTEM.md`

La segunda ronda de esta misma PR debe continuar esta tabla uno a uno antes de marcar la PR lista.

## 6. `scripts/`: primera pasada

### DELETE-NOW

- `audit-author-web.py` — único objetivo: generar el informe técnico público que también se retira.

### KEEP confirmado

- `audit-private-tools.py`
- `apply-manecillas-launch-state.py` — gate operativo próximo al 03/09/2026.
- `build-public-dist.py` — contrato de publicación.
- `build-public-editorial-facts.py` — proyección machine-readable.
- `build-site-shell.py` + `site_shell.py` — shell vigente.
- `build-sitemap.py`, `build-pagefind-index.py`, `build-feed.py` — derivados vigentes.
- `build-tools-hub.py`, `build-writer-tools.py`, `build-article-tools.py` — generadores funcionales.
- familia `check-*` — contratos de regresión; revisión individual necesaria antes de cualquier fusión/eliminación.
- `release-readiness.py` — gate de release.
- `validate_jsonld.py` y resto de `validate-*` — no borrar por nombre; son validadores reutilizables.
- `scripts/brevo/` — tooling operativo/read-only de Brevo; además existe trabajo futuro específico.

### REVIEW

- `test-worker-subscribe.mjs`: wrapper de 56 bytes que solo importa el test real en `tests/`. Podría ser alias histórico; antes de eliminar comprobar workflows/documentación/uso externo.
- `test-assistant-index-parity.mjs`: revisar si existe test canónico equivalente bajo `tests/` y si algún workflow llama al alias.
- `build-web-lab-index.py` / `validate-web-lab-entry.py`: conservar mientras `lab/` siga vivo; revisar juntos al cerrar el lab.
- generadores visuales de Manecillas (`build-manecillas-*`): conservar al menos hasta lanzamiento/rediseño y hasta documentar provenance/regeneración de los assets finales.

## 7. `qa/` y `tests/`

Principio general: QA no se considera basura porque haya pasado una vez. Un test de regresión existe precisamente para seguir fallando en el futuro si vuelve un bug.

### DELETE-NOW

- `qa/.pr61-runtime-trigger` — marker one-shot explícitamente temporal.

### KEEP por defecto

- browser QA de accesibilidad, reflow, CSP, runtime, analytics, content, etc.;
- fixtures que demuestran que un gate puede ponerse rojo;
- tests unitarios de builders/checkers.

Una limpieza posterior puede detectar duplicación real entre suites, pero exige comparar qué contrato cubre cada una. No se elimina un test solo porque otro también use Playwright.

## 8. `assets/`

NO DELETE en esta primera PR.

`check-orphan-assets.py` ya demostró que existe una enorme cantidad de ficheros sin referencia literal, pero el resultado mezcla basura real y material de campaña/diseño intencionalmente offline.

Fase posterior obligatoria:

1. producir inventario actual, no reutilizar cifras del 22/08;
2. agrupar por prefijo/familia/provenance;
3. identificar source/master/web-optimized/campaign;
4. verificar referencias en HTML/CSS/JS/JSON, builders y documentación de campaña;
5. decidir `KEEP`, `MOVE-OUT-OF-REPO`, `DELETE` por asset;
6. borrar solo tras revisión humana de las piezas visuales pendientes del rediseño.

Para peso histórico, evaluar Git LFS o almacenamiento externo solo después de medir el repo con `git-sizer`; no reescribir historia desde esta PR.

## 9. Otros directorios top-level — estado conservador

- `.github/`: KEEP; workflows son infraestructura. Auditar duplicación de workflows en ronda propia, no borrar por antigüedad.
- `data/`: KEEP; contiene autoridades/catálogos que alimentan builders/checkers.
- `pagefind/`: KEEP; índice runtime comprometido deliberadamente para un sitio estático sin build deploy.
- `press-kit/`: KEEP; materiales públicos y manifest interno con reglas de dist.
- `migrations/`: KEEP por ahora.
- `donde-empieza-la-jaula/`: KEEP; contenido gated/noindex deliberado, no basura.
- páginas públicas (`cuaderno/`, `libros/`, `recomendaciones/`, `editoriales/`, etc.): KEEP salvo una decisión editorial explícita de retirar una URL con su plan SEO.
- `publicar-web/`: DELETE-NOW por ser checklist interna duplicada.
- `lecturas/`: REVIEW por ser fixture ligado a un builder.
- `lab/`: REVIEW/ARCHIVE-CANDIDATE por rediseño activo.

## 10. Herramientas que sí ayudan a mantener el repo limpio

### 10.1 Ya tenemos y debemos explotar

- `scripts/check-orphan-assets.py`: detector específico de media no referenciada. Es más fiable para este repo que un borrado genérico.
- Lychee/broken-links workflow ya existe: no instalar otro link checker para duplicar señal.
- `scripts/check-secrets.py`: mantener como gate propio.

### 10.2 Recomendadas para pilotar, no auto-fix

#### `git-sizer` — P0 para medir el problema real de tamaño

Proyecto oficial de GitHub. Mide tamaño de blobs/trees/commits, objetos gigantes, checkout y otros patrones problemáticos. Debe ejecutarse sobre un clon completo.

Uso:

```bash
git-sizer --verbose
```

Objetivo: diferenciar «el árbol actual pesa mucho» de «el historial contiene blobs enormes» antes de plantear LFS o una limpieza histórica.

#### Knip — PILOT para JS/TS

Knip detecta archivos, dependencias y exports no usados a partir de entry points. En este proyecto requiere configuración explícita porque muchas páginas HTML y scripts del navegador son entry points sin imports convencionales.

Regla: usar solo en modo informe al principio. Nada de `--fix` hasta que la configuración reconozca HTML, workers, scripts de CI y generators.

#### Vulture — PILOT para Python

Puede ayudar a encontrar funciones/imports Python aparentemente no usados. Tiene riesgo alto de falsos positivos en scripts CLI, funciones invocadas dinámicamente y herramientas ejecutadas desde workflows.

Nunca borrar automáticamente; usar como lista de candidatos y contrastar con workflows/tests/docs.

#### jscpd — P2 para duplicación

Útil para localizar copy/paste entre scripts, QA y HTML, pero «duplicado» no significa «borrable». Puede ayudar a descubrir dos checkers que mantienen la misma lógica y deberían consolidarse.

### 10.3 Plugins Claude útiles para esta disciplina

- `claude-code-setup`: auditoría read-only de estructura y automaciones; útil trimestralmente, no como limpiador automático.
- `claude-md-management`: mantener `CLAUDE.md` conciso y actualizado para que no se convierta en otra carpeta `docs/` infinita.
- `hookify`: crear guardrails como «no commitear `settings.local.json`», «no añadir triggers temporales sin cleanup», «no generar docs de handoff sin condición de retirada».

Reglas Hookify candidatas:

1. bloquear edición/commit de `.claude/settings.local.json`;
2. advertir si se crea `*.tmp`, `*trigger*`, `*probe*`, `*-debug*` bajo paths versionados;
3. advertir al crear un doc `HANDOFF`/`PENDIENTE` sin campo `Retire when:`;
4. advertir si se añade una carpeta nueva bajo `herramientas/` que no entra en `data/tools-hub.json`;
5. advertir antes de `git push --force`, history rewrite o borrado masivo de assets.

## 11. Convención propuesta para evitar que vuelva a crecer la basura

Todo fichero nuevo de trabajo temporal debe caer en una de estas categorías:

### Temporal local — NO versionar

- screenshots/probes/logs/results ad hoc;
- settings personales;
- snapshots de APIs;
- scripts de una sola ejecución que no aportan reproducibilidad futura.

Ubicación: directorios ya ignorados (`artifacts/`, `qa-artifacts/`, `_tools/`) o tmp local.

### Reutilizable — versionar

- checker que protege un contrato;
- generator que reconstruye un artefacto;
- test que detecta una regresión;
- runbook operativo que se necesitará de nuevo.

### Handoff/pendiente — versionar solo si tiene retirada explícita

Todo nuevo documento de este tipo debería declarar:

```text
Status: OPEN | IMPLEMENTED | SUPERSEDED
Owner/authority: ...
Retire when: <condición comprobable>
Superseded by: <fichero/PR si aplica>
```

Cuando `Retire when` se cumpla, la misma PR que cierra el trabajo elimina el handoff.

## 12. Definition of Done de esta PR

Antes de marcarla lista:

- [ ] todos los borrados `DELETE-NOW` tienen evidencia y no dependen de búsquedas por nombre únicamente;
- [ ] public artifact contract verde;
- [ ] content indexes / navigation / discoverability verdes;
- [ ] ninguna herramienta real desaparece de `tools-hub.json`;
- [ ] `herramientas/auditor-pagina-libro/` sigue intacto;
- [ ] `lab/`, `assets/` y `lecturas/` no se borran sin completar su auditoría específica;
- [ ] continuar la tabla de `docs/` uno a uno y borrar solo los casos cerrados con certeza;
- [ ] revisar aliases/wrappers de `scripts/` antes de retirar ninguno;
- [ ] documentar la medición de `git-sizer` cuando Claude pueda ejecutarla sobre el clon local;
- [ ] revisar diff completo contra `main` final;
- [ ] CI verde en el HEAD definitivo.

## 13. Resultado esperado

Esta PR no busca maximizar el número de ficheros borrados. Busca cambiar el repositorio de «acumula todo por si acaso» a «cada fichero activo tiene una razón actual para existir».

La primera ronda elimina únicamente basura demostrada. Las siguientes rondas pueden ser mucho más agresivas una vez que `docs/`, `lab/`, `assets/`, aliases de scripts y branches estén clasificados con la misma evidencia.
