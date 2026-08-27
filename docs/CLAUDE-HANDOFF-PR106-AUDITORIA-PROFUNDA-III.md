# Claude handoff — continuación de la Auditoría Profunda III

## Punto de partida

Repositorio: `davidpd89/web-escritor`

PR anterior ya mergeada: `#106`

Merge commit de `main`: `e185f4a3275bad8ecfaa02909b89574bd084461b`

Rama de continuación: `audit/profunda-iii-followup-claude`

Esta rama se crea DESPUÉS de mergear #106 para que los pendientes no se pierdan. La intención es que Claude desarrolle aquí las mejoras restantes, las revise, deje CI verde y después decida el merge.

No reiniciar la auditoría desde cero. Leer primero:

- `docs/AUDITORIA-PROFUNDA-III-SUPERFICIE-PUBLICA-Y-CONTRATOS-MACHINE-2026.md`
- `docs/AUDITORIA-PROFUNDA-III-CIERRE-2026-08-27.md`

No desplegar Workers ni activar servicios externos desde esta PR sin autorización expresa.

---

# 1. Código que YA quedó implementado y mergeado en #106

## 1.1 Public dist allowlist-first

Archivo: `scripts/build-public-dist.py`

Se sustituyó el modelo include-by-default/denylist por allowlist-first.

El artefacto público solo admite namespaces/ficheros explícitamente clasificados. Nuevos directorios técnicos quedan privados por defecto.

Privados por defecto, entre otros:

- `docs/`
- `qa/`
- `lab/`
- `migrations/`
- `scripts/`
- `tests/`
- `data/`
- Workers
- Wrangler
- package metadata
- Lighthouse configs

También existe defensa por clases prohibidas incluso dentro de raíces públicas:

- `wrangler*.jsonc`
- `cloudflare-worker-*.js`
- `package*.json`
- `lighthouserc*.json`
- `*.sql`
- `.env*`
- `*.pem`
- `*.key`
- `*.tfstate`

No revertir a denylist-first.

## 1.2 `.assetsignore` generado desde la misma política

Archivo: `.assetsignore`

Comandos:

```bash
python scripts/build-public-dist.py --emit-assetsignore
python scripts/build-public-dist.py --check-assetsignore
```

No editar a mano sin modificar también el generador.

## 1.3 Gate transversal de CI

Archivo: `.github/workflows/public-artifact-contract.yml`

Deliberadamente sin `paths:` para que cualquier PR contra `main` compruebe la frontera repo -> publicación.

## 1.4 Tests

- `tests/test-public-artifact-contract.py`
- `tests/test-staging-publication-gate.py`

El fixture mínimo de staging usa `require_runtime=False`; producción/CLI conservan `require_runtime=True`. No eliminar esa distinción.

## 1.5 Press-kit de Manecillas

`press-kit/las-manecillas-del-recuerdo.json` ya no expone nombres internos de incidentes ni instrucciones de pipeline.

`press-kit/package-manifest.json` sigue existiendo como contrato interno, pero queda fuera del dist público.

---

# 2. Pendientes P1 que deben desarrollarse

## AIII-07 — limpiar `llms-full.txt`

### Problema

`llms-full.txt` mezcla hechos públicos con instrucciones internas de mantenimiento/pipeline: referencias a contrato interno, runner/rama, decisiones de implementación temporal y lenguaje técnico tipo `Offer`.

### Archivos

- `llms-full.txt`
- `tests/test-machine-authority.py`

### No cambiar

Conservar exactamente los hechos canónicos ya validados:

- nombre del autor;
- títulos;
- editoriales;
- ISBN;
- páginas;
- fechas;
- PVP;
- premios/reconocimientos;
- URLs;
- Noveris;
- ausencia de `purchaseUrl` verificada para Manecillas;
- cautela de no inventar retailer ni disponibilidad.

No reabrir la decisión editorial ya testeada de presentar Manecillas como “publicada el 3 de septiembre de 2026” antes de la fecha.

### Implementación recomendada

Reescribir solo las secciones de disponibilidad, jerarquía de verificación y notas machine-readable:

- eliminar vocabulario de build/QA que no aporta al lector/agente;
- sustituir referencias a “contrato interno”, “runner”, “rama” por formulación pública o eliminarlas;
- mantener “no existe una URL de compra verificada”;
- mantener que PVP/fecha no prueban disponibilidad comercial.

### Aceptación

```bash
python tests/test-machine-authority.py
```

Debe pasar sin relajar hechos ni checks.

---

## AIII-08 + AIII-10 — hechos mutables del asistente y proyección pública

### Problema

`assets/assistant-local-knowledge.mjs` contiene respuestas factuales escritas a mano. Ejemplo real:

```js
"La fecha de publicación de «Las manecillas del recuerdo» es el 3 de septiembre de 2026, con Monza Ediciones."
```

El registry del asistente sí está generado/parificado; esas frases no.

Una actualización editorial puede dejar el asistente factual desfasado aunque el contrato técnico permanezca verde.

### Archivos implicados

- `assets/assistant-local-knowledge.mjs`
- `editorial-facts.json`
- `scripts/check-assistant-contract.py`
- `tests/test-assistant-contract.py`
- `tests/test-machine-authority.py`
- generador público nuevo a crear

### Arquitectura recomendada

NO hacer que el navegador lea `editorial-facts.json`. Ese fichero es interno y debe seguir fuera del dist.

Crear una proyección pública generada y minimalista desde `editorial-facts.json`.

Opción concreta:

- nuevo generador: `scripts/build-public-editorial-facts.py` o equivalente;
- salida pública generada: `assets/editorial-public-facts.mjs`;
- cabecera `AUTO-GENERATED`;
- modo `--check` para CI;
- importar esa proyección desde `assistant-local-knowledge.mjs`;
- construir las respuestas factuales desde esos valores.

Campos iniciales suficientes:

Manecillas:

- `title`
- `publisher`
- `publicationDate`
- `isbn`
- `numberOfPages`
- `priceEUR`
- `purchaseUrl` / estado público de disponibilidad

Samuel:

- `title`
- `publisher`
- `publicationYear`
- `isbn`
- `numberOfPages`
- `asin`
- URLs comerciales verificadas

Autor/reconocimientos:

- premio Letras Como Espada;
- finalista Juan Andrés Teno con limitación de fuente;
- no atribuir esos reconocimientos a Samuel.

No proyectar:

- incidentes;
- gates internos;
- paths de build;
- secretos;
- decisiones de despliegue;
- campos internos no necesarios para respuesta pública.

### Qué derivar primero

Prioridad 1:

- fecha/editorial de Manecillas;
- disponibilidad/compra futura;
- premios/reconocimientos;
- ISBN/páginas/año si aparecen en respuestas locales.

El copy conversacional no factual puede seguir manual.

### Tests de mutación que faltan

Añadir tests que prueben:

1. cambiar `publicationDate` en fixture -> `--check` falla hasta regenerar;
2. cambiar `publisher` -> respuesta derivada cambia;
3. cambiar ISBN/páginas -> no queda literal obsoleto;
4. ningún campo interno aparece en la proyección pública;
5. generación idempotente byte a byte.

### Aceptación

- `editorial-facts.json` sigue siendo fuente única;
- proyección pública generada;
- asistente sin duplicación manual de los hechos cubiertos;
- `Assistant contract`, `Machine authority`, `Tool engine tests` verdes;
- public-artifact contract confirma que el contrato interno sigue fuera y solo sale la proyección autorizada.

---

# 3. Pendientes P2 / arquitectura

## AIII-09 — fecha manual de revisión en `/ai/`

Archivo principal: `ai/index.html`

Problema: sello/fecha de revisión factual manual que puede envejecer sin representar un cambio factual real.

Resolver preferentemente junto con AIII-10:

- eliminar la fecha si es decorativa; o
- derivarla de un campo factual versionado real.

No usar `date.today()`, `new Date()`, `Date.now()` ni reloj del runner. Debe ser determinista e idempotente.

---

## AIII-11 — `work-memoria-norte` sigue con URL externa en registry

Estado actual en `data/content-registry.json`:

- URL externa de Diversidad Literaria;
- `sourceFile: index.html`.

Pero ya existe continuidad interna:

- `/libros/#memoria-tierras-norte`
- `libros/index.html`.

### Cambio recomendado

Actualizar atómicamente:

```json
"url": "/libros/#memoria-tierras-norte",
"sourceFile": "libros/index.html"
```

La URL externa puede seguir como enlace editorial visible dentro de la tarjeta, pero no como URL canónica de la entidad del registry.

### No hacer cambio aislado

Regenerar/verificar derivados afectados:

- shell/navegación;
- assistant source registry;
- mapa/graph si deriva del registry;
- coverage/discoverability.

Revisar/ejecutar según estado actual:

- `scripts/build-site-shell.py`
- `scripts/build-assistant-source-registry.mjs`
- tests de navigation coverage territories
- Global discoverability closure QA
- Check content indexes

---

## AIII-12 — Lectores beta: `noindex` vs `searchIndex:true`

Estado:

HTML:

```html
<meta name="robots" content="noindex, follow">
```

Registry:

- `sitemap:false`
- `searchIndex:true`

No provoca indexación externa; la deuda es semántica interna.

Decidir explícitamente:

A. noindex externo pero encontrable por búsqueda interna -> mantener `searchIndex:true` y documentarlo;

B. tampoco debe entrar en Pagefind -> `searchIndex:false`.

Recomendación actual: B salvo que exista caso de uso claro para localizar “Lectores beta” desde búsqueda interna.

Ejecutar Pagefind eligibility, global discoverability y content-index QA.

---

# 4. Pendientes operativos con fecha/infra

## AIII-13 — lanzamiento de Manecillas, 3 de septiembre de 2026

NO es un bug y NO debe automatizarse a ciegas.

Archivo:

- `scripts/apply-manecillas-launch-state.py`

El 3 de septiembre o después:

```bash
python scripts/apply-manecillas-launch-state.py --date 2026-09-03
python scripts/apply-manecillas-launch-state.py --check --date 2026-09-03
```

Revisar manualmente marcadores prelaunch.

No convertir CTA a compra solo porque llegó la fecha.

Solo añadir retailer/Offer/disponibilidad cuando exista `purchaseUrl` verificada.

Cuando exista URL comercial real:

1. actualizar `editorial-facts.json`;
2. propagar/generar superficies públicas;
3. revisar JSON-LD, press-kit, llms y asistente;
4. ejecutar editorial facts + machine authority + launch-state QA.

---

## AIII-14 — Brevo / Lectores beta / rate limiting

Archivo:

- `cloudflare-worker-subscribe.js`

Ya implementado:

- CORS/Origin restringido;
- DOI Brevo;
- validación email;
- whitelist server-side de `source`;
- atributos construidos server-side;
- lista beta separada con `BREVO_BETA_LIST_ID`;
- si falta la lista beta, falla cerrado y NO cae en lista general.

Pendiente real: `RATE_LIMITER` falla abierto si falta el binding, devuelve resultado inválido o lanza error.

No cambiar ese trade-off sin revisar impacto en disponibilidad.

Antes del próximo deploy del Worker:

1. verificar binding `RATE_LIMITER` real en Cloudflare;
2. verificar límites/namespace;
3. verificar `BREVO_LIST_ID`;
4. verificar `BREVO_BETA_LIST_ID` distinto;
5. verificar `BREVO_DOI_TEMPLATE_ID`;
6. verificar `BREVO_DOI_REDIRECT_URL`;
7. smoke test real de home, fragmento, Manecillas, Cuaderno, popup, quiz y lectores-beta;
8. confirmar en Brevo que beta no aterriza en lista general;
9. no prometer automatizaciones de email que no estén verificadas en panel.

No desplegar desde esta PR sin autorización expresa.

---

# 5. QA obligatorio antes de merge

Antes de mergear esta PR de continuación:

1. sincronizar con `main` si ha avanzado;
2. resolver conflictos sin perder allowlist-first;
3. revisar todos los workflows del HEAD final;
4. no marcar un rojo como flaky sin leer log;
5. build real + contrato de artefacto;
6. confirmar que no entra material técnico nuevo;
7. confirmar `press-kit/package-manifest.json` fuera;
8. confirmar los JSON públicos de prensa dentro;
9. confirmar `donde-empieza-la-jaula/` fuera físicamente;
10. confirmar `editorial-facts.json` fuera.

Comandos mínimos:

```bash
python tests/test-public-artifact-contract.py
python tests/test-staging-publication-gate.py
python scripts/build-public-dist.py --check-assetsignore
python scripts/build-public-dist.py
python tests/test-machine-authority.py
python tests/test-assistant-contract.py
```

Workflows a revisar:

- Public artifact contract
- Tool engine tests
- Editorial facts check
- Machine authority check
- Runtime scoping QA
- Check content indexes
- Global discoverability closure QA
- Sitewide Reflow QA
- Accessibility baseline
- CSP public shell QA
- broken links si se dispara por los cambios

---

# 6. Lo que NO debe reabrirse sin nueva evidencia

- ISBN Manecillas: `979-8-90514-935-1`.
- Samuel: publicación 2025 ya corregida.
- PWA: `/api` y `/api/*` no se cachean.
- `ASSISTANT_ENABLED=false` sigue siendo la política actual.
- Wrangler expuesto no equivalía a fuga de API keys; era exposición innecesaria de topología/config.
- PVP de Manecillas NO equivale a disponibilidad.
- `noindex` NO es control de acceso.
- No automatizar copy/compra únicamente por fecha.

---

# 7. Orden recomendado para Claude

1. Leer este handoff y los dos documentos de auditoría.
2. Revisar diff de #106 ya mergeado para entender lo implementado.
3. Sin cambiar nada todavía, verificar estado de CI de `main` y de esta PR.
4. Cerrar AIII-07 primero.
5. Diseñar e implementar AIII-08 + AIII-10 como una sola arquitectura.
6. Resolver AIII-09 dentro de esa proyección si encaja.
7. Resolver AIII-11 atómicamente con derivados.
8. Resolver AIII-12 con decisión explícita de búsqueda interna.
9. Ejecutar toda la matriz QA.
10. Revisar diff completo de la PR.
11. Merge solo con CI verde y sin deploy accidental.
12. El 3 de septiembre seguir AIII-13.

---

# 8. Definition of Done

Esta PR puede mergearse cuando:

- la frontera pública siga allowlist-first;
- `.assetsignore` esté sincronizado;
- el dist real pase;
- no haya material técnico interno expuesto;
- `llms-full.txt` no publique instrucciones de pipeline innecesarias;
- los hechos mutables del asistente cubiertos estén derivados o tengan paridad fuerte desde la autoridad canónica;
- AIII-09/11/12 estén resueltos o, si se decide separarlos, convertidos en una PR/issue explícita antes de cerrar esta;
- todos los checks del HEAD final estén verdes;
- no se haya desplegado ni activado ningún servicio externo accidentalmente.
