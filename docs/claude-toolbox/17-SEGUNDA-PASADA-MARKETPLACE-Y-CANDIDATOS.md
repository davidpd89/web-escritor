# 17 — Segunda pasada del marketplace: candidatos que parecen útiles y decisión

Esta segunda pasada revisa nombres que aparecen actualmente en el marketplace de plugins de Claude y que podrían parecer atractivos para WEB DAVID PORTO. Su objetivo es evitar dos errores: ignorar una capacidad realmente útil o instalarla solo por descripción comercial.

## 1. Superdesign — PILOT de alto interés

El marketplace actual describe `superdesign` como una herramienta que diseña/rediseña UI y gráficos en un canvas infinito, lee el codebase, prepara un design system y genera drafts ramificables.

El producto actual se distribuye como skill/plugin; el repositorio antiguo de la extensión VS Code de 2025 está archivado y el propio vendor indica usar ahora `superdesign-skill`/superdesign.dev.

Setup Claude Code documentado por el vendor al corte:

```text
/plugin marketplace add superdesigndev/superdesign-skill
/plugin install superdesign@superdesign
```

El flujo del vendor también usa su CLI/login.

### Por qué merece pilot

Es exactamente una capacidad que hoy puede ser útil: **explorar varias direcciones de composición antes de modificar el repo**, partiendo del código existente.

### Por qué NO es INSTALL_NOW

Su posicionamiento promete “design judgment” y anti-AI-slop, pero eso no garantiza alineación con nuestra dirección de arte. Un agente puede sustituir un AI-slop por otro estilo trendy.

### Pilot propuesto

Problema único: artículo mobile plano.

1. Chrome DevTools produce baseline/evidence.
2. Dar a Superdesign el design contract, código/captura y problema; no “hazlo premium”.
3. Producir 3 drafts con diferencias de composición, no de “theme”.
4. Pasarlos por `david-design-critic` a ciegas.
5. Compararlos con 2 hipótesis hechas mediante Figma/Frontend Design.
6. Selección humana.
7. Implementar únicamente la hipótesis seleccionada.

### Gate

Se conserva si:

- genera alternativas que no habríamos producido con el stack actual;
- parte de nuestro sistema, no lo sustituye;
- permite comparar/forkear sin ensuciar el repo;
- reduce tiempo de exploración;
- no tiende a importar template aesthetics.

## 2. Miro — DEFER / opcional para arquitectura y workshops

El plugin oficial actual de Miro usa OAuth/MCP y puede leer/escribir boards, diagrams, docs y tables; incluye skills para extraer specs y visualizar PRs.

### Utilidad potencial

- information architecture maps;
- user journeys;
- workshop de contenidos;
- diagramar sistema de fuentes/territorios;
- presentar cambios complejos a un colaborador.

### Por qué no ahora

Ya tenemos Drive docs, Figma/FigJam puede cubrir parte visual y el repo no necesita otra fuente de verdad. Instalar Miro solo si existe un board/workflow real.

Estado: `DEFER`, no `REJECT`.

## 3. Cloudinary — DEFER

Plugin actual de Cloudinary expone varios MCP para asset management, transforms, metadata, análisis y Mediaflows, con OAuth; algunas funciones pueden requerir key.

### Puede resolver

- responsive transformations;
- format/quality;
- crops;
- background removal;
- video transformations;
- asset metadata.

### Por qué no se adopta

La web usa un pipeline de assets estáticos y una política de materialidad/provenance. Introducir Cloudinary implica:

- dependencia runtime/CDN externa;
- nuevas URLs/origins/CSP;
- gestión de cuenta/assets;
- potencial coste;
- pipeline nuevo.

Primero mejorar nuestro pipeline `<picture>`/WebP/manifest. Reabrir si el volumen de media vuelve inviable ese modelo.

## 4. Fullstory — DEFER

Plugin actual permite a Claude consultar behavioral analytics/session replays.

Solo aporta algo si Fullstory se instala en producción. Hacerlo cambiaría privacidad/tracking/consent y no se justifica para que Claude “vea usuarios”.

No adoptar mediante esta toolbox.

## 5. CodSpeed — DEFER

Plugin del marketplace orientado a benchmarks, flamegraphs y performance de código.

Buen producto para workloads/benchmarks. Menor fit para un sitio cuyo problema de performance principal es browser/network/media/CWV y cuyo runtime es HTML/CSS/JS estático.

Chrome trace + LHCI + CrUX + WebPageTest cubren mejor nuestro problema.

Reabrir únicamente si aparece una función/algoritmo propio de CPU cuyo benchmark sea material.

## 6. Qodo — DEFER

Skills de calidad/testing/security/compliance para SDLC.

El proyecto ya tendrá:

- PR Review Toolkit;
- LSP;
- Security Guidance;
- tests propios;
- posible Semgrep;
- GitHub.

No añadir otra suite general hasta encontrar un gap específico.

## 7. Runway API — DEFER fuera del web tooling

Plugin/skills de generación audiovisual.

Puede ser útil para campañas/promoción en otra PR, pero no mejora el criterio de layout/UX del sitio y el contrato visual rechaza media sintética que pretenda ser material documental real.

No instalar como parte del stack web.

## 8. Shopify `liquid-skills` — REJECT

Incluye CSS/JS/HTML/WCAG guidance, pero está orientado a Shopify Liquid themes. La web no usa Shopify/Liquid.

Modern Web Guidance + nuestras a11y tools son más apropiadas.

## 9. SAP UI Theme Designer / UI5 — REJECT

Capacidades reales, ecosistema equivocado. No introducir Fiori/UI5 semantics en una web editorial estática.

## 10. Sanity — REJECT/DEFER arquitectónico

Plugin real con CMS/MCP/skills. Adoptarlo significaría introducir un CMS y cambiar arquitectura editorial, no “mejorar Claude”.

No instalar salvo una futura decisión independiente de migración de contenidos.

## 11. New Relic — DEFER

Observability/APM potente, pero no existe New Relic como fuente de datos del sitio. Mismo criterio que Sentry: no incorporar SDK/plataforma para justificar el plugin.

## 12. Sourcegraph — DEFER

Muy útil para grandes/múltiples repos. Este repositorio no necesita ahora infraestructura de code intelligence multi-repo adicional a GitHub + LSP + search.

## 13. Serena — mantener PILOT

A diferencia de Sourcegraph, puede aportar semantic symbol navigation local sin una plataforma SaaS. Pilot limitado a refactor JS/Python.

## 14. CodeRabbit / Greptile — reviewers externos

No instalar ambos. Si se desea “un segundo par de ojos” independiente:

- seleccionar un mismo corpus de PRs;
- comparar contra Anthropic Code Review/PR Toolkit;
- medir findings únicos y falsos positivos;
- elegir como máximo uno.

Estado general: `PILOT OPTIONAL`.

## 15. Adobe for Creativity — PILOT condicionado

Está en el marketplace actual bajo Adobe y ofrece retouch/background removal/vectorization.

Puede elevar calidad de assets **reales** si ya existe licencia/flujo Adobe.

No usar para:

- inventar archivo;
- reemplazar una sesión fotográfica;
- crear fondos genéricos para llenar secciones;
- decidir responsive layout.

## 16. Candidatos de base de datos/cloud no aplicables

El marketplace contiene numerosas integraciones de AlloyDB, Aiven, Cosmos, ClickHouse, Redis, Qdrant, etc. No se documentan una a una porque el sitio no usa esos sistemas. Incluirlas “por exhaustividad” sería exactamente el ruido que el usuario pidió evitar.

## 17. Regla de segunda pasada

La pregunta no es “¿qué más hay en el marketplace?”. Es:

> ¿Hay una capacidad disponible que cierre un gap real de nuestro método?

Después de esta pasada, las novedades que realmente cambian la shortlist son:

- **Superdesign → PILOT de diseño comparativo**;
- Miro → opcional si existe workshop/board;
- Cloudinary → solo si cambia estrategia de asset delivery;
- Fullstory/New Relic/CodSpeed → no encajan hoy;
- resto de stacks verticales → no instalar.

Esto mantiene la toolbox amplia pero selectiva.