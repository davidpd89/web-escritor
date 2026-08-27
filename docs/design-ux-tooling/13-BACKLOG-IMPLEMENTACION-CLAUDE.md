# 13 — Backlog ejecutable para Claude

**Propósito:** convertir esta investigación en trabajo secuenciado.  
**Regla:** ninguna tarea de cuenta/credencial/servicio se considera hecha porque esté documentada. Claude debe comprobar el estado real y pedir acción del usuario cuando corresponda.

## Convenciones

**Actores**

- `REPO` — Claude puede preparar cambios en rama/PR.
- `LOCAL` — configuración local de Claude/entorno.
- `ACCOUNT` — requiere acción/autorización en servicio externo.
- `HUMAN` — decisión/revisión humana.
- `RESEARCH` — investigación/estudio.
- `DEVICE` — test en navegador/dispositivo real.

**Prioridades**

- `P0` — antes de rediseñar familias.
- `P1` — infraestructura necesaria para trabajo visual serio.
- `P2` — madurez/escala.
- `DEFER` — solo cuando aparezca necesidad.

---

# FASE 0 — Ground truth

## DUX-001 · Snapshot de `main`

- Prioridad: P0
- Actor: REPO
- Acción: registrar SHA actual antes de cualquier implementación visual.
- Aceptación: evidence pack identifica commit/deploy exacto.

## DUX-002 · Inventario de familias CSS

- P0 · REPO
- Mapear Home, Book, Samuel, Identity, Editorial, Tools, Resources, Shell.
- Aceptación: cada ruta piloto sabe qué CSS gobierna su composición.

## DUX-003 · Inventario de contratos Drive

- P0 · RESEARCH
- Confirmar documentos 13,16,17,18,25,29,30,34,35,36 y cualquier revisión posterior.
- Aceptación: context map con IDs/URLs/revisión; no copiar versiones antiguas sobre decisiones nuevas.

## DUX-004 · Capture matrix baseline

- P0 · REPO/LOCAL
- Implementar script Playwright de capturas 320/390/430/768/1024/1440/1728 + landscape.
- Aceptación: artefacto reproducible, no screenshots manuales sueltos.

## DUX-005 · Long-scroll contact sheets

- P0 · REPO
- Generar full-page + versión reducida por familia.
- Aceptación: se puede comparar densidad macro entre Home/interiores.

## DUX-006 · Geometry report

- P0 · REPO
- Extraer bounding boxes, gaps, widths, headings, media, backgrounds, borders.
- Aceptación: JSON/Markdown por ruta/viewport.

## DUX-007 · Typography report

- P0 · REPO
- Extraer computed type metrics y relación con viewport/body.
- Aceptación: detecta H1/H2/lead/body/metadata sin valores inventados.

## DUX-008 · Image role audit

- P0 · REPO/RESEARCH
- Inventariar assets usados en rutas piloto y rol actual.
- Aceptación: cada imagen prioritaria tiene source/path, dimensiones y función o queda marcada `unknown`.

## DUX-009 · Current-state accessibility spot check

- P0 · REPO
- Reutilizar Pa11y/Playwright y hacer manual 320/zoom/text spacing en rutas piloto.
- Aceptación: baseline antes del rediseño.

## DUX-010 · Current-state performance spot check

- P0 · REPO
- Lighthouse existente + DevTools trace en Home/Book/Article/Tool 390 y desktop.
- Aceptación: LCP candidate/media/fonts identificados.

---

# FASE 1 — Tooling local sin secretos

## DUX-011 · Instalar Chrome DevTools plugin

- P0 · LOCAL
- Comando documentado en 03.
- Aceptación: Claude puede abrir página, screenshot, inspect DOM/styles y trace.

## DUX-012 · Validar Skills Chrome

- P0 · LOCAL
- Reiniciar y comprobar `/skills`.
- Aceptación: no duplicar plugin + segundo MCP accidentalmente.

## DUX-013 · Política de telemetría DevTools

- P1 · HUMAN/LOCAL
- Decidir usage statistics/CrUX queries según necesidades.
- Aceptación: flags/config documentados localmente.

## DUX-014 · Instalar Playwright MCP

- P0 · LOCAL
- Aceptación: navegación/captura/focus reproducibles.

## DUX-015 · Fijar versión para CI visual

- P1 · REPO
- Tras piloto, fijar versión de dependencia relevante en workflows/scripts.
- Aceptación: CI no depende ciegamente de `latest`.

## DUX-016 · Crear `.design-evidence` contract

- P0 · REPO
- Definir estructura/manifest y exclusión de public dist.
- Aceptación: evidencia no se publica accidentalmente.

## DUX-017 · Script de grayscale/contact sheet

- P1 · REPO
- Aceptación: review macro automatizable.

## DUX-018 · Script text-spacing stress

- P1 · REPO
- Inyectar solo en test stylesheet WCAG spacing.
- Aceptación: screenshots/checks sin alterar producción.

## DUX-019 · Script webfont-fallback

- P2 · REPO
- Aceptación: detecta cambios de layout/overflow.

## DUX-020 · Resize hot test 1024→320

- P1 · REPO
- Aceptación: no reload, no stale JS layout.

---

# FASE 2 — Figma MCP

## DUX-021 · Confirmar cuenta/plan Figma

- P0 · ACCOUNT/HUMAN
- Aceptación: sabemos qué capacidades MCP reales tiene la cuenta; no se supone Enterprise.

## DUX-022 · Conectar Figma MCP remoto

- P0 · ACCOUNT/LOCAL
- OAuth.
- Aceptación: Claude lee/escribe solo en fichero de laboratorio autorizado.

## DUX-023 · Crear fichero web design lab

- P0 · ACCOUNT/HUMAN
- Estructura definida en doc 04.
- Aceptación: separado de campañas/promocionales.

## DUX-024 · Importar baselines 390/768/1440

- P0 · LOCAL/Figma
- Aceptación: frames etiquetados con URL/SHA/fecha/browser.

## DUX-025 · Foundations read-only mirror

- P1 · Figma/REPO
- Representar tokens actuales sin cambiarlos.
- Aceptación: drift map Figma↔CSS.

## DUX-026 · Kill-list visible en Figma

- P1 · Figma
- Aceptación: review page/nota con anti-patterns del contrato 16 + doc 15.

## DUX-027 · Primer pilot: Article mobile

- P0 · Figma
- Crear exactamente 2–3 hipótesis de jerarquía 390.
- Aceptación: ninguna depende de cards/background alterno por defecto.

## DUX-028 · Pilot Book mobile

- P1 · Figma
- Explorar orden título/portada/contexto/CTA.
- Aceptación: Manecillas y Samuel mantienen personalidad distinta.

## DUX-029 · Pilot Autor mobile

- P1 · Figma
- Retrato + bio + ledger.
- Aceptación: no avatar/card profile.

## DUX-030 · Pilot Tools open

- P1 · Figma
- Distinguir tarea/result/context.
- Aceptación: funcionalidad domina.

## DUX-031 · Figma critique pass independiente

- P0 · LOCAL/Claude
- Ejecutar agente crítico sobre cada pilot.
- Aceptación: rationale de rechazo/selección.

## DUX-032 · Code Connect decision

- DEFER · HUMAN/REPO
- Solo evaluar con componentes de código reales.
- Aceptación: no migración React por tooling.

---

# FASE 3 — Jerarquía mobile por familia

## DUX-033 · Definir scene map de Article

- P0 · REPO/Figma
- Apertura, orientación, body, chapter breaks, figures, close.
- Aceptación: long screenshot tiene cortes perceptibles.

## DUX-034 · Reducir repetición de heading signals

- P1 · REPO
- Basado en audit, no cambio global a ciegas.
- Aceptación: H1/H2/eyebrows tienen roles distintos.

## DUX-035 · Revisar TOC mobile

- P1 · REPO/Figma
- Aceptación: orienta sin parecer una segunda portada.

## DUX-036 · Revisar article figure treatment

- P1 · REPO/Figma
- Aceptación: media real puede crear cambio de registro.

## DUX-037 · Revisar article closing/related

- P1 · REPO
- Aceptación: final de lectura y siguiente ruta perceptibles.

## DUX-038 · Book first-screen audit

- P0 · REPO/Figma
- Aceptación: título/obra/portada/acción accesibles sin hero desproporcionado.

## DUX-039 · Book technical ledger mobile

- P1 · REPO
- Aceptación: metadata secundaria, no chips.

## DUX-040 · Book synopsis→fragment transition

- P1 · REPO
- Aceptación: cambio de registro perceptible sin card.

## DUX-041 · Author opening composition

- P1 · REPO/Figma
- Aceptación: retrato es presencia, no inserción genérica.

## DUX-042 · Author bio measure/rhythm

- P1 · REPO
- Aceptación: reading flow y hitos distinguibles.

## DUX-043 · Author work hierarchy

- P1 · REPO
- Aceptación: Manecillas dominante; Samuel pleno pero secundario donde corresponda; no cards clonadas.

## DUX-044 · Press ledger mobile

- P1 · REPO
- Aceptación: medio/fecha/material/fuente jerarquizados.

## DUX-045 · Events ledger mobile

- P1 · REPO
- Aceptación: temporalidad clara sin timeline app.

## DUX-046 · Tools hub composition

- P1 · REPO/Figma
- Aceptación: workbench/listado por utilidad, no SaaS tiles.

## DUX-047 · Tool task/result/context separation

- P0 · REPO/Figma
- Aceptación: resultado aparece como región propia y accesible.

## DUX-048 · Directory scanning hierarchy

- P1 · REPO/Figma
- Aceptación: nombre/verificación/datos/acción escaneables sin cardification.

## DUX-049 · Resources family audit

- P2 · REPO
- Aceptación: no heredar plantilla por comodidad si task difiere.

## DUX-050 · 404 identity check

- P2 · REPO/Figma
- Aceptación: recuperación clara, sin ilustración IA/portal cliché.

---

# FASE 4 — Media/art direction

## DUX-051 · Asset inventory machine-readable

- P1 · REPO/RESEARCH
- Crear `data/media-art-direction.json` o equivalente interno.
- Aceptación: no inventar provenance/rights.

## DUX-052 · Focal points

- P1 · RESEARCH/Figma
- Para retratos/eventos principales.
- Aceptación: crop 390/768/1440 documentado.

## DUX-053 · Portada treatment audit

- P1 · Figma/REPO
- Aceptación: no crop destructivo, escala contextual.

## DUX-054 · Autor photography gap analysis

- P2 · HUMAN/RESEARCH
- Aceptación: shot list de material realmente faltante.

## DUX-055 · Manecillas physical-material shot list

- P2 · HUMAN
- Solo con libro/material autorizado disponible.
- Aceptación: no mockups IA.

## DUX-056 · Samuel physical-material review

- P2 · HUMAN
- Aceptación: identidad propia, no replicar Manecillas.

## DUX-057 · Article image necessity gate

- P1 · REPO/EDITORIAL
- Aceptación: no hero genérico para piezas sin asset útil.

## DUX-058 · Responsive image audit

- P1 · REPO
- `srcset/sizes/picture/dimensions/lazy/preload`.
- Aceptación: no bytes/CLS regresados.

## DUX-059 · Connect Canva MCP

- P2 · ACCOUNT
- Solo si hay uso real de media/moodboard.
- Aceptación: OAuth, fichero/Brand context autorizado.

## DUX-060 · Canva role boundary

- P2 · HUMAN
- Aceptación: no web layout source-of-truth.

---

# FASE 5 — BrowserStack + visual regression

## DUX-061 · Confirmar BrowserStack access

- P1 · ACCOUNT
- Aceptación: plan/capacidad real verificados.

## DUX-062 · Conectar BrowserStack MCP

- P1 · ACCOUNT/LOCAL
- OAuth remoto preferido cuando disponible.
- Aceptación: una sesión de device real reproducible.

## DUX-063 · Definir device matrix Tier A

- P1 · DEVICE/HUMAN
- Aceptación: Safari iOS + Chrome Android actuales y al menos un tamaño estrecho.

## DUX-064 · Safari iOS baseline

- P1 · DEVICE
- Home, Article, Book, Tool, Explorar.
- Aceptación: portrait/landscape/browser bars.

## DUX-065 · Chrome Android baseline

- P1 · DEVICE
- Mismas superficies.
- Aceptación: keyboard/touch/rotation.

## DUX-066 · Elegir Percy vs Chromatic

- P1 · HUMAN/REPO
- Pilot real con misma PR.
- Aceptación: decisión documentada; solo uno baseline principal.

## DUX-067 · Crear secret visual service

- P1 · ACCOUNT
- Solo después de decisión/autorización.
- Aceptación: secret no visible en repo/logs.

## DUX-068 · Visual regression pilot Article

- P1 · REPO
- Aceptación: 390/1440 diffs reviewables.

## DUX-069 · Expand baseline Book/Identity

- P1 · REPO
- Solo tras resolver deuda visual principal.

## DUX-070 · Visual review checklist PR

- P1 · REPO
- Aceptación: no `accept all` sin rationale.

---

# FASE 6 — Accessibility expert tooling

## DUX-071 · Pilot Stark

- P1 · ACCOUNT/LOCAL
- OAuth.
- Aceptación: evaluar misma página/estados del pilot.

## DUX-072 · Pilot axe MCP

- P1 · ACCOUNT/LOCAL
- OAuth/API según producto.
- Aceptación: misma página/estados.

## DUX-073 · Seleccionar herramienta a11y experta

- P1 · HUMAN
- Criterios: hallazgos, ruido, remediation, integration, coste.

## DUX-074 · No duplicar Pa11y

- P1 · REPO
- Aceptación: nueva herramienta cubre gap real, no mismo scanner en CI.

## DUX-075 · Text spacing automated fixture

- P1 · REPO
- Aceptación: routes pilot PASS.

## DUX-076 · Target-size audit mobile

- P1 · REPO/DEVICE
- Aceptación: controles principales conservan objetivo interno apropiado.

## DUX-077 · Focus-under-sticky audit

- P1 · REPO
- Aceptación: anchors/controls visibles.

## DUX-078 · Dialog height/zoom audit

- P1 · REPO/DEVICE
- Aceptación: 390×600, landscape bajo, 200%.

## DUX-079 · Motion/reduced-motion paired captures

- P2 · REPO
- Aceptación: información idéntica.

## DUX-080 · DOM-order review tras recomposición

- P1 · REPO
- Aceptación: visual order no contradice lectura/focus.

---

# FASE 7 — UX research

## DUX-081 · Diseñar baseline study mobile hierarchy

- P1 · RESEARCH
- Aceptación: pregunta/tareas/segmento sin leading copy.

## DUX-082 · Configurar Maze si se aprueba

- P1 · ACCOUNT
- Aceptación: estudio piloto, no integración permanente innecesaria.

## DUX-083 · Test current Article

- P1 · RESEARCH
- Aceptación: baseline de segmentación/recuerdo.

## DUX-084 · Test proposed Article

- P1 · RESEARCH
- Aceptación: comparación con misma tarea.

## DUX-085 · Book task study

- P2 · RESEARCH
- Find fragment/understand fit/action.

## DUX-086 · Author press-contact study

- P2 · RESEARCH
- Especialmente perfil prensa/organizador.

## DUX-087 · Tools task study

- P2 · RESEARCH
- Identificar/usar/interpretar resultado.

## DUX-088 · Research repository

- P1 · REPO
- Sin PII.
- Aceptación: findings/decisions versionados.

## DUX-089 · Clarity privacy assessment

- DEFER · HUMAN/RESEARCH
- Aceptación: decisión explícita `do-not-use` o plan consentido.

## DUX-090 · Clarity limited experiment

- DEFER · ACCOUNT/REPO
- Solo si 089 lo aprueba.
- Aceptación: tiempo/páginas/purpose/retirement definidos.

---

# FASE 8 — Performance de diseño

## DUX-091 · Confirmar CrUX data availability

- P1 · RESEARCH
- Sin key si consulta manual basta; API si automatiza.

## DUX-092 · Crear Google API key restringida

- P2 · ACCOUNT
- Solo si automatización aprobada.

## DUX-093 · CrUX report por origin/URLs críticas

- P2 · REPO
- Aceptación: `no data` tratado correctamente.

## DUX-094 · PSI remote spot-check

- P2 · REPO
- No duplicar Lighthouse por commit.

## DUX-095 · LCP media regression gate

- P1 · REPO
- Para cambios hero/cover/portrait.

## DUX-096 · CLS typography/media gate

- P1 · REPO
- Aceptación: fonts/images con dimensions/preload apropiados.

## DUX-097 · Motion cost review

- P2 · REPO
- Aceptación: no continuous main-thread animation innecesaria.

## DUX-098 · Font payload audit

- P2 · REPO
- Aceptación: no añadir pesos/estilos sin uso.

## DUX-099 · WebPageTest deep dive trigger

- DEFER · RESEARCH
- Usar solo si waterfall/render issue no queda claro.

## DUX-100 · Performance note obligatorio en PR visual grande

- P1 · REPO
- Aceptación: qué cambió y evidencia.

---

# FASE 9 — Skills / agents

## DUX-101 · Implement `design-observe-live`

- P1 · REPO
- Aceptación: output evidence-first, no styling advice inicial.

## DUX-102 · Implement `mobile-composition-audit`

- P1 · REPO
- Aceptación: máximo 3 hipótesis, contrato 16/17/36.

## DUX-103 · Implement `figma-explore`

- P1 · REPO
- Aceptación: contenido real, variants, rationale.

## DUX-104 · Implement `media-art-direction`

- P2 · REPO
- Aceptación: provenance/role/crop.

## DUX-105 · Implement `a11y-design-review`

- P1 · REPO
- Aceptación: scanner + manual checklist.

## DUX-106 · Implement `visual-regression-review`

- P1 · REPO
- Aceptación: expected/unexpected reasoning.

## DUX-107 · Implement `ux-study-design`

- P2 · REPO
- Aceptación: no synthetic users/results.

## DUX-108 · Implement `design-pr-gate`

- P1 · REPO
- Aceptación: bloquea falta de mobile/evidence/kill-list violations.

## DUX-109 · Context packs por familia

- P1 · REPO
- Aceptación: no cargar 40 docs enteros en cada task.

## DUX-110 · Independent critic agent

- P1 · REPO
- Aceptación: generador no autoaprueba.

---

# FASE 10 — Governance y referencia

## DUX-111 · Design reference ledger

- P2 · REPO
- Fuente/take/reject/appliesTo/reviewedAt.

## DUX-112 · Media art-direction ledger

- P1 · REPO
- Interno/no público por defecto.

## DUX-113 · Design decision log

- P1 · REPO/Figma
- Aceptación: decisiones importantes tienen rationale.

## DUX-114 · Tool integration inventory

- P1 · REPO/PRIVATE-OPS
- Sin valores de secretos.

## DUX-115 · Review tooling quarterly/on-change

- P2 · HUMAN
- Aceptación: deprecated MCPs removed; versions revisadas.

## DUX-116 · Webby-style quality gate

- P2 · HUMAN/RESEARCH
- Usar categorías como preguntas, no score falso.

## DUX-117 · Anti-slop review obligatorio

- P0 · REPO/Claude
- Toda PR visual sustantiva.

## DUX-118 · Preserve SEO/semantic gate

- P0 · REPO
- URL/canonical/headings/HTML/links/schema/content.

## DUX-119 · Preserve public artifact boundary

- P0 · REPO
- Evidence/design docs/tool configs internos no se publican accidentalmente.

## DUX-120 · Post-merge production review

- P1 · REPO/DEVICE
- Verificar producción real, no asumir preview = prod.

---

# Orden de ejecución recomendado

## Sprint A — ver

DUX-001…020.

No tocar dirección visual importante antes de tener baseline/evidence.

## Sprint B — pensar

DUX-021…032 + piloto Article.

## Sprint C — arreglar una familia

DUX-033…037 + DUX-064/065 + DUX-071/072 + visual diff.

### Gate

Si Article mobile no mejora de forma clara, no escalar el patrón.

## Sprint D — libros/autor/herramientas

DUX-038…050, por PRs pequeñas.

## Sprint E — madurez

Media, research, performance, skills y governance.

---

# Definition of Done de una PR visual sustantiva

```text
[ ] problema reproducido
[ ] baseline SHA/URL
[ ] current captures
[ ] contrato Drive relevante leído
[ ] hipótesis explícita
[ ] Figma/prototipo si la decisión lo necesitaba
[ ] critic review
[ ] 320
[ ] 390
[ ] 768
[ ] 1440
[ ] landscape si aplica
[ ] real Safari iOS / Android Chrome en gate de familia
[ ] 200% zoom/reflow
[ ] text spacing
[ ] keyboard/focus
[ ] reduced motion
[ ] visual regression
[ ] a11y
[ ] performance note
[ ] media provenance/crop si cambió asset
[ ] SEO/semantics preserved
[ ] public artifact preserved
[ ] no kill-list violations sin rationale
[ ] user research si el claim es comprensión/findability
```

# Merge rule

No mergear una gran reforma visual porque:

- CI técnico está verde;
- Figma se ve bien;
- Claude dice que es más moderno;
- el usuario ve una captura 1440 bonita.

Mergear cuando la intención declarada sobreviva **navegador, mobile, accesibilidad, rendimiento y review**.