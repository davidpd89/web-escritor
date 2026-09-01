# Plan de implementación — solo mejoras aprobadas/condicionales

Este documento convierte la autoridad 108/108 en trabajo ejecutable. No contiene `REJECT` ni convierte `CONDITIONAL` en obligación.

## Orden recomendado

### Fase 0 — cerrar medición y contratos baratos

#### E.8 · Auditoría de terceros — `IMPLEMENT_NOW`

**Pregunta:** ¿GoatCounter, Metricool, Turnstile o cualquier script remoto está costando LCP/INP/bytes o cargándose donde no aporta?

**Archivos a inspeccionar:**
- `script.js`
- `scripts/build-site-shell.py`
- shell generado en páginas públicas
- CSP del shell
- workflows Lighthouse/browser QA

**Implementación:**
1. Inventario machine-readable: proveedor, URL, rutas donde aparece, `async/defer`, propósito, bytes transferidos, main-thread ms, condición de carga.
2. Chrome/Playwright trace de Home + artículo + herramienta + libro.
3. No retirar telemetría por intuición: cada script necesita coste observado y función.
4. Si un tercero no necesita estar en first paint, cargarlo sin bloquear parser/critical path.
5. Contrato estático que impida volver a introducir protocol-relative URLs y terceros no declarados.

**DoD:** informe before/after + ningún cambio de analítica sin confirmar que los eventos necesarios siguen llegando.

#### F.1 · Target size sitewide — `IMPLEMENT_NOW`

**Base normativa:** WCAG 2.5.8 AA 24×24 CSS px con excepciones; el proyecto conserva 42 px donde ese contrato ya fue deliberado.

**Plan:**
- ampliar QA browser para enumerar `a[href]`, `button`, inputs y controles custom visibles;
- no aplicar 42 px indiscriminadamente a enlaces inline;
- distinguir `WCAG_MINIMUM`, `PROJECT_PRIMARY_CONTROL=42` y excepciones;
- reportar selector + rect + separación, no solo “falló”.

**DoD:** ningún control principal táctil cae por debajo del contrato del componente; ninguna relajación 42→24 para poner CI verde.

#### F.2 · Resize 200% + Text Spacing — `IMPLEMENT_NOW`

El repositorio ya demostró que `zoom:2` y `font-size:200%` detectan fallos distintos.

**Nuevo QA recomendado:** `qa/sitewide-text-resilience-browser.mjs`.

Pseudo-código:

```js
await page.addStyleTag({content: `
  html { font-size: 200% !important; }
  * { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }
  p { margin-bottom: 2em !important; }
`});
// medir overflow, clipping, controls fuera de viewport y scroll containers inesperados
```

No sustituir el reflow existente: ambos modos deben coexistir.

#### I.2 · Matriz de privacidad de terceros — `IMPLEMENT_NOW`

Crear una autoridad tipo `data/third-party-integrations.json` con:

```json
{
  "id": "goatcounter",
  "purpose": "aggregate analytics",
  "loadsOn": ["public-shell"],
  "cookiesExpected": false,
  "piiAllowed": false,
  "consentGate": "documented-policy",
  "owner": "site",
  "lastVerified": "YYYY-MM-DD"
}
```

No asumir “cookieless = jurídicamente irrelevante”; registrar comportamiento real y revisar la política publicada.

#### Q.3 · Registro de experimentos — `IMPLEMENT_NOW`

Crear `data/experiments.json` y test de esquema. Campos mínimos:

```json
{
  "id": "EXP-2026-001",
  "hypothesis": "...",
  "primaryMetric": "...",
  "guardrails": ["CLS", "a11y"],
  "start": "YYYY-MM-DD",
  "end": null,
  "status": "planned|running|concluded|aborted",
  "result": null,
  "decision": null
}
```

Regla: no declarar una mejora por una sola métrica post-hoc.

### Fase 1 — auditorías que deciden si hay implementación

#### A.6 · Breadcrumb coverage

Crear script read-only que compare rutas profundas del registry con:
- breadcrumb visible;
- `BreadcrumbList` parseable;
- URLs canónicas;
- igualdad de orden/nombre entre visible y JSON-LD cuando aplique.

No añadir breadcrumbs a una página donde no mejoren navegación; Google los muestra principalmente en desktop.

#### C.8 · `empieza-aqui/`

Auditar con tareas reales: “quiero conocer al autor”, “quiero empezar por el libro actual”, “quiero herramientas”, “quiero leer una muestra”. Cambiar solo si alguna tarea necesita demasiados pasos o compite con otra.

#### E.1 · AVIF

Script de inventario, no conversión masiva:

```text
asset | bytes | dimensiones | uso above-fold | formato actual | candidato AVIF | ahorro medido
```

Solo convertir si el ahorro neto justifica nueva variante/picture/build complexity.

#### E.7 · Compresión live

No inferir desde Cloudflare DNS.

Smoke conceptual:

```bash
curl -sS -D - -o /dev/null --compressed https://davidportodiaz.com/
curl -sS -D - -o /dev/null --compressed https://davidportodiaz.com/assets/v1-base.css
curl -sS -D - -o /dev/null --compressed https://davidportodiaz.com/script.js
```

Registrar `content-encoding`, `content-type`, `content-length`/transfer, `vary`, cache headers y fecha. Si no hay compresión útil, identificar si corresponde a origin, GitHub Pages/CDN o Cloudflare antes de cambiar configuración.

#### F.6 · Asistente + lector de pantalla

Casos mínimos:
- apertura/cierre de diálogo;
- foco inicial y retorno;
- historial de mensajes (`role=log`/alternativa apropiada);
- estado “pensando/error” sin repetición invasiva;
- teclado Escape/Tab;
- NVDA + Firefox/Chrome y VoiceOver + Safari si disponible.

#### G.1 · Recomendación conversacional

Antes de ampliar el asistente, crear evals:
- 10 prompts donde Samuel/Manecillas sí encajan;
- 10 donde no;
- 10 ambiguos;
- exigir fuentes internas/canon;
- prohibir inventar edad oficial, retailer, premio u obra.

Solo después cambiar runtime/prompts.

#### J.3 · ICS

Reutilizar `herramientas/eventos-ics/`; no crear segunda librería. Extraer motor reutilizable solo si el club/eventos necesita exactamente la misma semántica.

#### J.6 · Lectores beta

No ampliar programa hasta evidencia E2E:
`form → Worker → DOI/alta → lista beta correcta → no newsletter general sin consentimiento`.

#### M.1 · Cabeceras live

Auditarlas en producción, no en HTML solamente:
- HSTS;
- CSP efectiva;
- `X-Content-Type-Options`;
- `frame-ancestors`/frame protection;
- cache headers relevantes;
- redirects HTTP→HTTPS / www.

No activar HSTS preload como parte de este audit.

#### Q.1 · CrUX

Consultar origin/page. Si no hay muestra suficiente, estado = `NO_FIELD_DATA`, no “malo” ni “bueno”. Mantener Lighthouse como laboratorio separado.

### Fase 2 — mejoras válidas después de deuda actual

#### A.4 · Cadencia editorial

Añadir a `data/content-registry.json` solo para contenido sensible a obsolescencia:

```json
"reviewCadenceDays": 90,
"reviewBy": "2026-11-26",
"verificationSource": "..."
```

No cambiar `datePublished` por revisar ortografía o recompilar.

#### B.7 · IndexNow

**Arquitectura recomendada:** post-deploy, después de verify-production.

1. comparar manifest de release anterior/actual;
2. obtener URLs públicas cambiadas/creadas/eliminadas;
3. filtrar `noindex`, gated, privadas y machine-internal;
4. enviar batch a IndexNow;
5. loguear respuesta y SHA;
6. nunca bloquear el deploy porque un endpoint de IndexNow esté temporalmente caído; sí alertar.

Payload orientativo:

```json
{
  "host": "davidportodiaz.com",
  "key": "<managed-key>",
  "keyLocation": "https://davidportodiaz.com/<key>.txt",
  "urlList": ["https://davidportodiaz.com/cuaderno/nueva-pieza/"]
}
```

#### C.3 · Preguntas reales → contenido

Entrada: preguntas anonimizadas/recogidas editorialmente. Salida: primero map a URL existente; nueva URL solo si intención distinta, demanda real y contenido original suficiente.

#### C.10 · Archivo de prensa

Modelar:

```json
{"date":"YYYY-MM-DD","type":"interview|review|mention|event","publication":"...","url":"https://...","verifiedAt":"YYYY-MM-DD"}
```

Generar vista cronológica desde datos; no duplicar HTML manualmente.

#### D.11 · Estados vacíos

Inventario mínimo: search sin resultado, assistant sin respuesta/error, formularios, futuras listas. Cada estado debe ofrecer siguiente acción útil sin culpar al usuario.

#### E.2 · INP

CrUX p75 primero. Si hay señal, Chrome Performance/Long Animation Frames para interacción concreta. No “optimizar script.js” sin identificar interacción lenta.

#### E.5 · Performance budget

Primera versión warning-only basada en baseline versionado. Luego hard gate cuando exista margen estable. Separar budgets de bytes, Lighthouse y CWV: no son equivalentes.

#### F.4 · Foco

Audit de teclado por componentes compartidos; incluir Focus Not Obscured. No resolver foco con outlines de bajo contraste “porque son feos”.

#### H.1 / H.2 · Brevo

Primero cerrar DOI/routing/delivery. Preferencias: listas/segments como baseline. Consent Groups solo si la feature está realmente habilitada y el coste/plan está aprobado. No crear claves en repo.

#### I.4 / I.5 · atribución + minimización

Usar `SOURCE`/UTM y export manual antes de añadir analytics nuevo. Revisión anual de campos/retención con borrado documentado.

#### M.3 · headers obsoletos

Eliminar `X-XSS-Protection`, `Expect-CT`, HPKP solo si existen; no añadir un “cleanup” que toca headers inexistentes.

#### O.2 · OG por artículo

Build-time y determinista. Plantilla editorial propia, no imagen genérica “AI social card”. Snapshot de dimensiones/text overflow. Mantener una fallback general.

#### P.4 · crosslinks herramientas↔contenido

Añadir relaciones a una autoridad de datos y generar los enlaces. No hardcodear 22×N enlaces que luego se desincronizan.

#### Q.2 · cadencia Google+Bing

Checklist trimestral: indexación, queries/páginas, brand/nonbrand, CTR, errores, Bing AI citations/grounding, anomalías conocidas y decisiones. Guardar snapshot/fecha; no copiar dashboards al repo con PII.

## Condicionales: trigger antes de código

- A.5: afirmación que necesita fuente externa.
- A.11: media importante no descubierta.
- B.3/B.8: pieza donde mejora comprensión.
- B.9/C.7: canon suficiente y caso editorial.
- C.2/C.4: contenido first-party/derechos.
- D.1/D.4/D.9/D.12: necesidad UX concreta.
- E.3/E.4: trace/LCP demuestra cuello.
- F.3: media hablada.
- G.2/G.3: workflow humano de revisión.
- H.3/H.6: estrategia editorial/email madura.
- J.2/J.5: uso real del club/preguntas.
- K.1/K.3: operación comercial real.
- M.4/M.5: requisito de monitor/recovery.
- N.3: proyecto de traducción real.
- O.4: calendario editorial.
- P.1/P.2: herramienta concreta y privacidad compatible.

## Operaciones externas

B.6 (Bing Webmaster Tools) debe realizarse solo con acceso real y registrar evidencia. Search Console ya fue auditado/configurado por separado; no duplicar ese proyecto desde esta PR.

## No implementar

Los IDs `REJECT` y `DEFER` no deben generar tickets de código “para más adelante” salvo que cambie explícitamente su trigger/producto. Eso incluye FAQ rich-result tactic, mass long-tail pages, reciprocal review SEO, reader-mode propio, hover-preview, generic quiz, share-selected-text, custom big-text mode, English metadata without English pages, public analytics dashboard, badges/gamification, web push actual, public tools changelog y similares.
