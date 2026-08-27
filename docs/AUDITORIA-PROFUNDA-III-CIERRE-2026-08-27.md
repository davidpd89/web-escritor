# Auditoría Profunda III — cierre operativo (2026-08-27)

Estado de la auditoría: **CERRADA COMO DIAGNÓSTICO; PR NO APTA TODAVÍA PARA MERGE**.

Este documento actualiza y aterriza `AUDITORIA-PROFUNDA-III-SUPERFICIE-PUBLICA-Y-CONTRATOS-MACHINE-2026.md` sobre el estado real recuperado el 27 de agosto de 2026. La base original (`85dc4f2`) había quedado atrás. La rama `audit/profunda-iii-superficie-publica-machine-2026` se sincronizó con `main` `21d86b244f17c869b08d673f7499580d87b5575c` antes de implementar correcciones.

No se ha hecho merge a `main`, deploy, activación del asistente ni publicación de Workers.

## Resumen ejecutivo

La auditoría confirmó un problema de frontera repo→publicación: `scripts/build-public-dist.py` y `.assetsignore` eran include-by-default/denylist. Eso permitía que material operativo nuevo entrase en el árbol público por omisión. Se ha sustituido por una frontera **allowlist-first** y se ha añadido un gate transversal de CI sobre el artefacto final.

El cambio ya impide por defecto publicar `docs/`, `qa/`, `lab/`, `migrations/`, `scripts/`, `tests/`, `data/`, Workers, Wrangler, package manifests, Lighthouse y clases técnicas equivalentes. Se preservan explícitamente rutas editoriales, `assets/`, Pagefind, PWA, machine-readable y press-kit público legítimo. `press-kit/package-manifest.json` permanece en el repositorio como contrato interno, pero queda fuera del artefacto público.

También se ha eliminado del JSON público de Manecillas la referencia a `knownEditorialIncident` y la instrucción interna de saltos/generación de ZIP, manteniendo el bloqueo de cubierta en alta resolución y el gate interno real.

Persisten cuatro deudas que no deben mezclarse con el P0 ya corregido: limpieza de instrucciones de mantenimiento en `llms-full.txt`; derivación/paridad más fuerte de hechos mutables del asistente; normalización del registry de `La memoria de las tierras del norte`; y coherencia semántica de `lectores-beta.searchIndex` con su `noindex` actual.

---

## Hallazgos

### AIII-01 — frontera pública include-by-default

- **Severidad:** P0
- **Estado:** CORREGIDO EN RAMA
- **Área:** public dist / seguridad por minimización
- **Evidencia:** el builder anterior incluía cualquier fichero tracked salvo exclusiones conocidas.
- **Archivos/rutas:** `scripts/build-public-dist.py`, `.assetsignore`
- **Impacto:** nuevos ficheros técnicos podían servirse estáticamente sin intención explícita.
- **Causa raíz:** denylist como frontera de publicación.
- **Solución propuesta:** output positivo por clases de artefacto.
- **Implementación concreta:** `PUBLIC_DIR_PREFIXES` + `PUBLIC_ROOT_FILES`; exclusiones nested; estados gated derivados de `data/content-registry.json`; clases técnicas prohibidas; manifiesto tipado del output fuera del dist.
- **Pruebas de aceptación:** `tests/test-public-artifact-contract.py`; build real; required runtime; gated source absent.
- **Dependencias:** ninguna de despliegue.
- **Riesgo de regresión:** medio; mitigado por CI transversal.
- **Orden recomendado:** 1.

### AIII-02 — Worker/Wrangler/migraciones podían entrar en assets estáticos

- **Severidad:** P0
- **Estado:** CORREGIDO EN RAMA
- **Área:** backend/configuración/superficie pública
- **Evidencia:** `cloudflare-worker-assistant.js`, `wrangler.assistant.jsonc`, `wrangler.assistant.example.jsonc`, `migrations/assistant-quota.sql` no pertenecen al runtime web estático.
- **Archivos/rutas:** los anteriores; `scripts/build-public-dist.py`; `.assetsignore`
- **Impacto:** exposición innecesaria de topología, bindings, IDs y código operativo. No se confirmó fuga de credenciales.
- **Causa raíz:** misma frontera include-by-default.
- **Solución propuesta:** privados por defecto + defensa en profundidad por clase.
- **Implementación concreta:** no se permiten sus raíces; además se rechazan `wrangler*.jsonc`, `cloudflare-worker-*.js`, `*.sql`, `.env*`, `*.pem`, `*.key`, `*.tfstate` incluso dentro de namespaces públicos.
- **Pruebas de aceptación:** fixtures nested bajo `assets/` deben ser privados.
- **Dependencias:** ninguna.
- **Riesgo de regresión:** bajo con el nuevo gate.
- **Orden recomendado:** 1.

### AIII-03 — package/Lighthouse/QA/docs/lab públicos por omisión

- **Severidad:** P1
- **Estado:** CORREGIDO EN RAMA
- **Área:** metadata operativa
- **Evidencia:** `package.json`, `package-lock.json`, `lighthouserc*.json`, `docs/`, `qa/`, `lab/` no son runtime browser.
- **Archivos/rutas:** mismos + builder.
- **Impacto:** ruido público, topología/tooling innecesario y ampliación de superficie.
- **Causa raíz:** denylist incompleta.
- **Solución/implementación:** quedan fuera por clasificación positiva; clases package/Lighthouse también se bloquean nested.
- **Pruebas:** contrato de artefacto y build real.
- **Dependencias:** ninguna.
- **Riesgo:** bajo.
- **Orden:** 1.

### AIII-04 — CI no protegía transversalmente repo→artefacto

- **Severidad:** P1
- **Estado:** CORREGIDO EN RAMA
- **Área:** CI/release gate
- **Evidencia:** Release Readiness no ejecutaba el builder y su workflow estaba limitado por paths; staging smoke comprueba una URL ya desplegada, no compone el artefacto.
- **Archivos:** `.github/workflows/public-artifact-contract.yml`
- **Impacto:** una PR no relacionada podía añadir un artefacto técnico sin ejecutar un gate de frontera.
- **Causa raíz:** validaciones por subsistema, no sobre el output final.
- **Solución:** gate sin `paths:` para toda PR a `main`.
- **Implementación:** compila builder/tests, ejecuta regresión, comprueba `.assetsignore`, construye dist y vuelve a inspeccionarlo.
- **Pruebas:** GitHub Actions `Public artifact contract`.
- **Dependencias:** GitHub Actions.
- **Riesgo:** bajo.
- **Orden:** 1.

### AIII-05 — detalles internos en press-kit público de Manecillas

- **Severidad:** P1
- **Estado:** CORREGIDO EN RAMA
- **Área:** press-kit / machine-readable
- **Evidencia:** `press.coverReleaseNote` exponía `knownEditorialIncident` e instrucciones de no generar/publicar ZIP saltándose un gate.
- **Archivos:** `press-kit/las-manecillas-del-recuerdo.json`, `press-kit/package-manifest.json`
- **Impacto:** mezcla de información útil para prensa con proceso interno.
- **Causa raíz:** estado de release y copy público compartían la misma superficie.
- **Solución:** conservar el gate interno; publicar solo el estado útil para medios.
- **Implementación:** nota pública: cubierta alta resolución pendiente de autorización editorial; el manifest interno conserva `blocked-pending-editorial-clearance`.
- **Pruebas:** Machine authority + Public artifact contract.
- **Dependencias:** autorización editorial futura.
- **Riesgo:** bajo.
- **Orden:** 2.

### AIII-06 — `press-kit/package-manifest.json` dentro del namespace público

- **Severidad:** P1
- **Estado:** CORREGIDO EN RAMA
- **Área:** press-kit/build
- **Evidencia:** es un contrato de empaquetado y gate, no un recurso de prensa.
- **Archivos:** `press-kit/package-manifest.json`, builder, `.assetsignore`
- **Impacto:** exposición de arquitectura de build y estado interno.
- **Causa raíz:** ubicación física confundida con publicabilidad.
- **Solución:** conservar fichero interno, excluirlo de la proyección pública.
- **Pruebas:** required public press JSON presentes; package-manifest ausente.
- **Dependencias:** ninguna.
- **Riesgo:** bajo.
- **Orden:** 2.

### AIII-07 — `llms-full.txt` mezcla hechos e instrucciones de mantenimiento

- **Severidad:** P1
- **Estado:** ABIERTO
- **Área:** IA/search authority
- **Evidencia:** aparecen conceptos de `runner`, `rama`, decisión temporal de implementación, `Offer` y contrato editorial interno junto a datos públicos.
- **Archivos:** `llms-full.txt`
- **Impacto:** contexto machine-readable más ruidoso y orientado al mantenimiento que a la verificación pública.
- **Causa raíz:** el archivo evolucionó como documentación de QA además de contexto público.
- **Solución propuesta:** conservar hechos y cautelas públicas; mover decisiones de pipeline al contrato interno/docs.
- **Implementación concreta pendiente:** reescribir solo secciones de disponibilidad/jerarquía, sin alterar ISBN, fechas, páginas, premios, URLs ni cautela de retailer.
- **Pruebas:** `tests/test-machine-authority.py` + diff semántico de hechos.
- **Dependencias:** ninguna.
- **Riesgo:** medio por superficie SEO/IA.
- **Orden:** 3.

### AIII-08 — asistente local duplica hechos mutables

- **Severidad:** P1
- **Estado:** ABIERTO
- **Área:** asistente / source-of-truth
- **Evidencia:** `assets/assistant-local-knowledge.mjs` contiene frases factuales escritas a mano, incluida fecha/editorial de Manecillas.
- **Archivos:** `assets/assistant-local-knowledge.mjs`, `editorial-facts.json`, `scripts/check-assistant-contract.py`
- **Impacto:** una actualización editorial puede dejar el asistente coherente estructuralmente pero factual desfasado.
- **Causa raíz:** registry de fuentes generado, respuestas factuales manuales.
- **Solución propuesta:** generar constantes/respuestas factuales o un módulo de hechos públicos desde el contrato, manteniendo copy conversacional estable.
- **Pruebas:** fixtures de mutación de fecha/ISBN/editorial que obliguen a regenerar/paridad.
- **Dependencias:** decidir qué campos son factual vs. copy.
- **Riesgo:** medio.
- **Orden:** 4.

### AIII-09 — fecha manual de revisión en `/ai/`

- **Severidad:** P2
- **Estado:** ABIERTO
- **Área:** autoridad machine-readable
- **Evidencia:** sello de revisión factual manual.
- **Impacto:** puede envejecer sin que cambien los hechos.
- **Causa raíz:** metadata editorial no derivada.
- **Solución:** o eliminar fecha decorativa o derivarla de cambios factuales reales, nunca del reloj del runner.
- **Pruebas:** estabilidad temporal/idempotencia.
- **Dependencias:** AIII-10.
- **Riesgo:** bajo.
- **Orden:** 5.

### AIII-10 — no existe una proyección pública generada única desde el contrato interno

- **Severidad:** P1
- **Estado:** MITIGADO, NO CERRADO
- **Área:** source-of-truth / machine-readable
- **Evidencia:** `tests/test-machine-authority.py` cruza exhaustivamente superficies, pero los JSON/LLM/AI siguen siendo autoría separada.
- **Impacto:** la paridad se detecta después de editar, no se evita por construcción.
- **Causa raíz:** múltiples superficies manuales.
- **Solución:** proyección pública explícita o generadores pequeños por superficie; mantener `editorial-facts.json` fuera del dist.
- **Pruebas:** generación idempotente + 584 checks existentes + public artifact contract.
- **Dependencias:** AIII-07/AIII-08.
- **Riesgo:** medio.
- **Orden:** 3-4.

### AIII-11 — `work-memoria-norte` conserva destino externo en registry

- **Severidad:** P2
- **Estado:** ABIERTO
- **Área:** arquitectura / source-of-truth
- **Evidencia:** el registry sigue con URL externa y `sourceFile:index.html`, mientras `/libros/#memoria-tierras-norte` existe como continuidad interna.
- **Archivos:** `data/content-registry.json`, `libros/index.html`, derivados de navegación/assistant.
- **Impacto:** autoridad de catálogo no refleja la ruta editorial ya diseñada.
- **Causa raíz:** deuda de migración del registry.
- **Solución:** actualizar a `/libros/#memoria-tierras-norte` y `libros/index.html`, regenerar derivados atómicamente.
- **Pruebas:** discoverability, navigation coverage, assistant registry parity, internal graph.
- **Dependencias:** regeneradores de shell/registry.
- **Riesgo:** medio si se cambia de forma aislada.
- **Orden:** 6.

### AIII-12 — `lectores-beta` noindex pero `searchIndex:true`

- **Severidad:** P2
- **Estado:** ABIERTO COMO DEUDA DE CONTRATO
- **Área:** SEO / búsqueda interna
- **Evidencia:** HTML `noindex,follow`; registry `sitemap:false`, `searchIndex:true`.
- **Impacto:** no provoca indexación en Google, pero deja intención contradictoria entre superficies internas.
- **Causa raíz:** Pagefind/búsqueda global pospuestos frente a política SEO de la página.
- **Solución:** decidir explícitamente si debe ser encontrable en búsqueda interna aunque no indexable externamente; documentar esa semántica o poner `searchIndex:false`.
- **Pruebas:** Pagefind eligibility + global discoverability.
- **Dependencias:** decisión de producto.
- **Riesgo:** bajo.
- **Orden:** 7.

### AIII-13 — dependencia de fecha de lanzamiento

- **Severidad:** P1 operativo
- **Estado:** CONTROL EXISTENTE / NO BUG
- **Área:** lanzamiento Manecillas
- **Evidencia:** `scripts/apply-manecillas-launch-state.py` entra en modo launch desde 2026-09-03 y puede fallar si quedan marcadores prelaunch.
- **Impacto:** el 3 de septiembre exige revisión humana de copy/CTA; no debe convertirse automáticamente en compra sin `purchaseUrl` real.
- **Causa raíz:** separación deliberada entre fecha editorial y disponibilidad comercial.
- **Solución:** ejecutar gate de lanzamiento; añadir retailer solo cuando `editorial-facts.json` tenga URL verificada.
- **Pruebas:** simulación `--date 2026-09-03`; editorial facts check.
- **Dependencias:** URL comercial real.
- **Riesgo:** medio si se omite la revisión del día de lanzamiento.
- **Orden:** antes/durante 2026-09-03.

### AIII-14 — Brevo/lectores beta: rate limiter y lista separada son requisitos de despliegue

- **Severidad:** P1 operativo
- **Estado:** CONTROLADO EN CÓDIGO; VERIFICACIÓN DE INFRA PENDIENTE
- **Área:** formularios / Brevo / privacidad
- **Evidencia:** Worker valida Origin, whitelist de `source`, email, DOI, atributos server-side y lista beta separada; si falta `BREVO_BETA_LIST_ID` falla cerrado. El rate limiter, en cambio, falla abierto si el binding no existe/lanza error.
- **Archivos:** `cloudflare-worker-subscribe.js`, `script.js`, `privacidad.html`, `/lectores-beta/`
- **Impacto:** un deploy con binding ausente conserva disponibilidad, pero reduce protección de abuso del endpoint de DOI.
- **Causa raíz:** trade-off explícito fail-open para rate limiting.
- **Solución:** no cambiar el comportamiento a ciegas; verificar binding real y smoke-test end-to-end antes de cualquier deploy. Mantener lista beta independiente.
- **Pruebas:** tests Worker + smoke real cuando se autorice despliegue.
- **Dependencias:** Cloudflare/Brevo reales; fuera del alcance de esta PR sin deploy.
- **Riesgo:** medio operativo, no exposición estática.
- **Orden:** antes del próximo deploy del Worker.

---

## Matriz de las 40 áreas solicitadas

| # | Área | Resultado 2026-08-27 |
|---|---|---|
| 1 | Public dist / assetsignore | P0 corregido: allowlist-first |
| 2 | Allowlist vs denylist | corregido |
| 3 | docs/ | privado por defecto |
| 4 | qa/ | privado por defecto |
| 5 | lab/ | privado por defecto |
| 6 | migrations/ | privado por defecto |
| 7 | Worker source | privado por defecto + clase prohibida |
| 8 | Wrangler configs | privados + clase prohibida |
| 9 | package manifests | privados; press package manifest interno |
| 10 | Lighthouse configs | privados |
| 11 | machine-readable | hechos consistentes; AIII-07/10 abiertos |
| 12 | press-kit | nota interna saneada; package manifest fuera del dist |
| 13 | PWA | sin regresión confirmada |
| 14 | service worker | v11; `/api` no cacheado |
| 15 | manifest | artefacto requerido por el nuevo gate |
| 16 | robots | sin bloqueo global; contrato machine existente |
| 17 | sitemaps | `/ai/` presente; gated/noindex fuera según contratos actuales |
| 18 | structured data | cubierto por machine/editorial QA; no se confirmó contradicción nueva |
| 19 | headers/CSP | shell CSP sigue centralizado; CI CSP activo |
| 20 | APIs | asistente fail-closed/desactivado; API fuera de PWA |
| 21 | analytics/privacy | GoatCounter/Metricool declarados; taxonomy QA activo |
| 22 | formularios | newsletter DOI; inputs y source server-side acotados |
| 23 | Brevo | lista general + beta separada; AIII-14 operativo |
| 24 | lectores beta | noindex/sitemap coherentes externamente; searchIndex debt AIII-12 |
| 25 | launch state Manecillas | contrato por fecha separado de compra; AIII-13 |
| 26 | dependencia de fechas | no copy SEO por reloj de cliente; gate explícito de lanzamiento |
| 27 | source-of-truth drift | AIII-08/10/11/12 abiertos |
| 28 | duplicaciones | hechos assistant/LLM aún parcialmente manuales |
| 29 | cache/versionado | PWA v11; APIs no cacheadas |
| 30 | seguridad/exposición | P0 de superficie corregido |
| 31 | indexable/noindex | gated excluido físicamente; beta debt semántico documentado |
| 32 | rutas/redirects | no se confirmó nueva rotura en esta fase; discoverability CI debe quedar verde |
| 33 | performance | sin cambio runtime de render; Lighthouse configs ya no públicas |
| 34 | JS/CSS legacy | no se introduce carga nueva; runtime scoping CI debe quedar verde |
| 35 | assets huérfanos | campañas ya excluidas; orphan checker existente |
| 36 | third-party requests | CSP limita GoatCounter/Metricool/Cloudflare/subscribe Worker; no third-party nuevo |
| 37 | enlaces externos | no se afirma validación total de terceros sin Lychee; queda gate independiente |
| 38 | IA/search authority | machine authority fuerte; AIII-07/08/09/10 pendientes |
| 39 | conversión | no se inventa compra Manecillas; newsletter/fragmentos preservados |
| 40 | accesibilidad extrema | cambios de esta PR no alteran UI; Pa11y/reflow deben concluir verdes |

---

## DESCARTADOS / NO BUG

1. **ISBN de Manecillas:** no hay discrepancia actual. Valor canónico `979-8-90514-935-1`.
2. **Samuel 2025 / público:** la guía actual ya usa 2025 y «lectores juveniles y adultos»; no se reabre el falso positivo antiguo.
3. **PWA cacheando API:** descartado; `/api` y `/api/*` salen antes del manejo de cache.
4. **`ASSISTANT_ENABLED`:** sigue desactivado. Esta PR no lo activa.
5. **Wrangler = secreto filtrado:** formulación incorrecta. Hay topología/IDs/configuración operativa, no se confirmó API key/Turnstile secret comprometido. El problema era exposición innecesaria.
6. **PVP = disponibilidad:** falso. Manecillas sigue sin `purchaseUrl` verificada; no se crea `Offer` ni retailer supuesto.
7. **`noindex` como control de acceso:** falso por definición y ya cubierto por el gate físico del public-dist.
8. **Automatizar el cambio de copy por fecha:** descartado como solución; el proyecto exige revisión editorial humana y separa fecha de publicación de disponibilidad comercial.

---

## Cambios realizados en la rama

- `scripts/build-public-dist.py`
- `.assetsignore`
- `.github/workflows/public-artifact-contract.yml`
- `tests/test-public-artifact-contract.py`
- `tests/test-staging-publication-gate.py`
- `press-kit/las-manecillas-del-recuerdo.json`
- este documento de cierre

La rama se sincronizó previamente con `main` para incorporar el estado actual antes de editar.

## QA y criterio de merge

El primer `Public artifact contract` ejecutado tras crear el workflow pasó sobre el dist real. Un run posterior de `Tool engine tests` detectó una incompatibilidad de fixture introducida por el checker estricto: el test de staging usa deliberadamente un repo mínimo y no contiene todo el shell/PWA. Se corrigió separando `require_runtime=False` únicamente para ese fixture; CLI y producción conservan `require_runtime=True`.

A fecha de este documento, los workflows del HEAD final deben revisarse tras el último commit. **No declarar esta PR lista para merge mientras exista cualquier check relevante pendiente o rojo.**

Además, incluso con CI verde, AIII-07, AIII-08 y AIII-10 siguen siendo P1 de arquitectura machine-readable. La recomendación es no mezclar un refactor generador amplio con el cierre P0 si ello aumenta riesgo; pueden cerrarse en una PR técnica inmediatamente posterior. AIII-11/AIII-12 son P2 y deben resolverse de forma atómica con sus derivados.

## Orden recomendado restante

1. Esperar/revisar todos los checks del HEAD de PR #106.
2. Limpiar `llms-full.txt` de instrucciones de pipeline sin tocar hechos.
3. Definir proyección/generación factual pública y enlazar el asistente a esa autoridad.
4. Corregir `work-memoria-norte` atómicamente y regenerar derivados.
5. Resolver semántica `lectores-beta.searchIndex` según la decisión de búsqueda interna.
6. El 3 de septiembre ejecutar el gate de lanzamiento; añadir compra solo con URL verificada.
7. Antes de desplegar Worker Brevo, verificar binding de rate limit, lista beta y DOI reales.
