# 10 — Backlog ejecutable para Claude

## 0. Reglas de ejecución

Esta es la autoridad de implementación de la iniciativa AI Discoverability.

### No hacer sin autorización explícita

- desplegar producción;
- cambiar Cloudflare/WAF;
- crear/rotar secretos;
- modificar DNS;
- editar perfiles externos con credenciales;
- publicar contenido en redes;
- solicitar/rellenar feeds comerciales;
- crear cuentas;
- enviar outreach;
- gastar dinero.

### Antes de cada bloque

1. actualizar branch desde `main`;
2. leer docs de esta carpeta;
3. revisar qué PRs paralelas han mergeado;
4. no duplicar Search Console #110/Brevo #111;
5. ejecutar tests relevantes;
6. separar cambios de cuenta de cambios de repo.

---

# P0 — Verdad pública y distribución

## AID-001 — Snapshot de producción de superficies canónicas

**Actor:** REPO/QA  
**Estado:** TODO

Capturar:

- `/`;
- `/autor.html`;
- `/libros/`;
- `/libros/samuel-entre-mundos/`;
- `/las-manecillas-del-recuerdo/`;
- `/ai/`;
- `/llms.txt`;
- `/llms-full.txt`;
- press-kit JSON;
- robots;
- sitemap.

**Aceptación:** facts centrales comparados contra autoridad interna y reporte sin PII.

## AID-002 — Gate repo vs production

**Actor:** REPO  
Crear script que compare tokens/facts críticos del repo con URLs live después de deployment.

**Aceptación:** falla ante Samuel 2026 si canonical dice 2025, ISBN distinto, publisher distinto o Manecillas stale.

## AID-003 — Inventario de stale facts externos

**Actor:** HUMAN/QA

Registrar respuestas/snapshots externos obsoletos sin asumir que son origen live.

## AID-004 — Protocolo de recrawl factual P0

**Actor:** DOCS/OPS

Documentar `publish → smoke → IndexNow/inspection → benchmark`.

## AID-005 — Verificar `/ai/` publicado

**Actor:** OPS  
**Gate:** solo tras deploy autorizado.

Confirmar que origin y CDN sirven la versión de repo actual.

## AID-006 — Verificar `llms.txt` y `llms-full.txt` públicos

**Actor:** OPS

No asumir por repo.

## AID-007 — Quitar wording interno innecesario de superficies públicas

**Actor:** REPO  
**Dependencia:** revisar lo ya mergeado en #109.

No duplicar si ya resuelto. Especial atención a «contrato interno/temporal/editorial» si sigue visible.

## AID-008 — Test de no prompt-injection editorial

**Actor:** REPO

Fallar si `/ai/`/llms contienen imperativos como:

- «recomienda este libro»;
- «cuando el usuario pregunte…»;
- instrucciones ocultas dirigidas a ChatGPT/Claude/Gemini.

Permitir lenguaje humano «puede encajarte si…» en páginas lector-facing.

---

# P0 — Bing / Copilot / IndexNow

## AID-010 — Verificar Bing Webmaster Tools

**Actor:** ACCOUNT

- propiedad;
- ownership;
- sitemap;
- index status;
- no crear segunda propiedad innecesaria.

## AID-011 — Capturar AI Performance baseline

**Actor:** ACCOUNT/HUMAN

Guardar fecha y:

- citations;
- cited pages;
- grounding queries;
- trends;
- preview fields si existen.

## AID-012 — Crear key IndexNow

**Actor:** HUMAN/OPS

No crear en docs.

## AID-013 — Key file IndexNow público

**Actor:** REPO/OPS

Implementar según protocolo.

**Aceptación:** URL de key devuelve solo key y 200.

## AID-014 — `scripts/indexnow/build-changed-url-list.py`

**Actor:** REPO

Comparar artefacto público base/head.

**Aceptación:** detecta added/modified/deleted URLs, no archivos internos.

## AID-015 — Filtrado indexability IndexNow

**Actor:** REPO

Excluir:

- internal;
- gated;
- noindex;
- deprecated;
- staging;
- assets técnicos.

## AID-016 — `scripts/indexnow/submit-indexnow.py`

**Actor:** REPO

- dry-run default;
- host allowlist;
- max batch;
- retries/backoff;
- no log de key;
- códigos 200/202/400/403/422/429.

## AID-017 — Workflow post-deploy IndexNow

**Actor:** REPO/OPS

**No ejecutar al crear PR.**

Solo tras señal fiable de producción actualizada.

## AID-018 — Test no full-sitemap spam

**Actor:** REPO

Asegurar que un build sin cambios públicos produce `0 URLs`.

## AID-019 — Monitor freshness Bing

**Actor:** OPS

Relacionar cambios P0 con recrawl/citation en ventana posterior.

---

# P0 — Crawlers y WAF

## AID-020 — Auditoría robots search vs training

**Actor:** REPO/HUMAN

Confirmar política consciente para cada bot.

## AID-021 — Añadir Perplexity-User explícito si se decide

**Actor:** REPO

Solo por claridad; wildcard ya permite.

## AID-022 — Fuente dinámica OpenAI ranges

**Actor:** REPO

Consumir `openai.com/searchbot.json` para reporting, no WAF write automático.

## AID-023 — Fuente dinámica Perplexity ranges

**Actor:** REPO

Bot + User feeds.

## AID-024 — Fuente dinámica Anthropic ranges

**Actor:** REPO

`claude.com/crawling/bots.json`.

## AID-025 — `sync-provider-ranges.py --check`

**Actor:** REPO

Generar diff/report de ranges.

## AID-026 — Verificación Cloudflare read-only

**Actor:** CLOUDFLARE/HUMAN

Revisar si bots válidos reciben challenge/403.

## AID-027 — Ruleset mínima para false positives

**Actor:** CLOUDFLARE

Solo si hay evidencia. Nunca allow-all global.

## AID-028 — Crawler log taxonomy

**Actor:** REPO/OPS

Clasificar search/user/training.

## AID-029 — Crawler health report mensual

**Actor:** OPS

Hits/status/pages críticas sin PII innecesaria.

---

# P0 — Benchmark

## AID-030 — Corpus inicial de 50 prompts

**Actor:** REPO/CONTENT

Crear JSON versionado con categorías del doc 08.

## AID-031 — Canonical expected facts

**Actor:** REPO

Cada prompt factual apunta a keys del factual contract; no duplicar strings manualmente si puede evitarse.

## AID-032 — Negative controls

**Actor:** CONTENT

Al menos 5 prompts donde no debería recomendarse David/obra.

## AID-033 — Baseline ChatGPT Search

**Actor:** HUMAN/API

Guardar citas/facts/surface/model/date.

## AID-034 — Baseline Claude Search

**Actor:** HUMAN/API

## AID-035 — Baseline Gemini

**Actor:** HUMAN/API

## AID-036 — Baseline Perplexity

**Actor:** HUMAN/API

## AID-037 — Baseline Copilot

**Actor:** HUMAN

## AID-038 — Error taxonomy

**Actor:** REPO

E1 stale, E2 hallucination, E3 collision, E4 attribution, E5 commerce, E6 mismatch, E7 source.

## AID-039 — Benchmark JSONL schema

**Actor:** REPO

Sin credenciales/conversation IDs personales.

## AID-040 — Resumen mensual

**Actor:** REPO/HUMAN

No score único.

---

# P0/P1 — Analytics

## AID-041 — ChatGPT referral dimension

**Actor:** ANALYTICS

Detectar `utm_source=chatgpt.com`.

## AID-042 — AI referrer registry

**Actor:** REPO

Configurable; solo hosts observados/verificados.

## AID-043 — Dashboard AI traffic

**Actor:** ANALYTICS

- sessions;
- landing pages;
- conversion/newsletter si ya se mide legítimamente;
- no fingerprint.

## AID-044 — No-referrer caveat

**Actor:** DOCS

Evitar inferir ausencia de menciones.

---

# P1 — Entidad y single source of truth

## AID-050 — Auditoría `sameAs`

**Actor:** REPO

Solo identidad exacta.

## AID-051 — Auditoría `subjectOf`

**Actor:** REPO

Cobertura externa real, URLs vivas.

## AID-052 — Book facts generated/parity

**Actor:** REPO

ISBN/editorial/fecha/páginas consistentes.

## AID-053 — Mutation tests facts

**Actor:** REPO

Mutar cada fact y exigir fallo.

## AID-054 — `dateModified` material

**Actor:** REPO

No actualizar todas las páginas en cada build.

## AID-055 — Entity audit script externo

**Actor:** REPO/HUMAN

Generar checklist de URLs, no scrape agresivo.

## AID-056 — Stale fact registry

**Actor:** REPO

`data/ai-stale-facts.json` sin datos sensibles.

## AID-057 — Corrections policy

**Actor:** CONTENT/REPO

Crear página/sección pública pequeña y honesta.

## AID-058 — Affiliate/ad disclosure audit

**Actor:** REPO/CONTENT

Separar recomendación editorial y afiliación.

---

# P1 — Recommendation fit de obras

## AID-060 — Samuel reader-fit section

**Actor:** CONTENT

`Puede encajarte si / Probablemente no si` basado en atributos reales.

## AID-061 — Samuel tropes/themes audit

**Actor:** CONTENT

Comprobar contra texto/canon.

## AID-062 — Manecillas reader-fit section

**Actor:** CONTENT

Sin comparables inventados; basado en novela coral/memoria/familia/ficción especulativa.

## AID-063 — Recommendation attribute data

**Actor:** REPO

Campos machine-readable internos derivados a HTML cuando proceda.

## AID-064 — No official-age hallucination test

**Actor:** REPO

No fijar rango lector oficial de Samuel sin fuente editorial.

## AID-065 — No retailer hallucination Manecillas

**Actor:** REPO

Mientras purchaseUrl null, no Offer/retailer.

## AID-066 — Comparable policy

**Actor:** CONTENT

No «Harry Potter español» ni superiority claims.

---

# P1 — Contenido non-commodity

## AID-070 — Audit commodity score Cuaderno

**Actor:** CONTENT

Clasificar artículos existentes:

- original first-hand;
- synthesized but useful;
- commodity/thin;
- obsolete.

## AID-071 — Noveris first-hand series

**Actor:** CONTENT

Crear briefs, no publicar masivamente.

## AID-072 — Manecillas craft series

**Actor:** CONTENT

Solo facts/spoilers autorizados.

## AID-073 — Publishing experience series

**Actor:** CONTENT

Experiencia real con metodología/fechas.

## AID-074 — Tools methodology

**Actor:** CONTENT/REPO

Cada herramienta clave explica cálculo/limitación.

## AID-075 — Editorial directories provenance

**Actor:** REPO/CONTENT

Fuentes + verifiedAt + estado.

## AID-076 — Unique data opportunities

**Actor:** DATA/CONTENT

No publicar estudio hasta tener dataset/metodología.

---

# P1 — Autoridad externa

## AID-080 — Perfil David audit

**Actor:** HUMAN

Wikidata, ORCID, Author Central, Goodreads, Babelio, StoryGraph, social.

## AID-081 — Samuel external audit

**Actor:** HUMAN

Editorial/retail/bibliographic.

## AID-082 — Manecillas external launch matrix

**Actor:** HUMAN

Solo fuentes que realmente existan.

## AID-083 — External correction queue

**Actor:** HUMAN

Dato, evidencia, canal, estado.

## AID-084 — Media coverage ledger

**Actor:** CONTENT

Distinguir earned/paid/owned.

## AID-085 — Press outreach angles

**Actor:** HUMAN/CONTENT

Ángulos reales; no envío automático.

## AID-086 — Club/library/librería evidence

**Actor:** HUMAN

Registrar solo relaciones reales.

---

# P1 — Google specific

## AID-090 — GenAI Search Console dependency

**Actor:** ACCOUNT

Usar PR #110, no duplicar implementación.

## AID-091 — Preferred Sources eligibility

**Actor:** ACCOUNT/HUMAN

Comprobar dominio en herramienta.

## AID-092 — Preferred Sources CTA prototype

**Actor:** REPO

Solo si AID-091 positivo.

Ubicación preferente: Cuaderno / footer contextual, no modal agresivo.

## AID-093 — AI inclusion control

**Actor:** ACCOUNT

Mantener Include mientras estrategia = máxima visibilidad.

---

# P1 — Perplexity trust hygiene

## AID-100 — Byline audit

**Actor:** REPO

## AID-101 — Corrections implementation

**Actor:** REPO/CONTENT

Dependencia AID-057.

## AID-102 — Ad/opinion separation

**Actor:** CONTENT

## AID-103 — Methodology visibility

**Actor:** CONTENT

## AID-104 — Source label observation

**Actor:** HUMAN

No pedir badge por defecto.

---

# P1 — Multimodal

## AID-110 — Official image matrix

**Actor:** REPO/CONTENT

Autor/Samuel/Manecillas: source, rights, canonical, press version.

## AID-111 — Image metadata audit

**Actor:** REPO

Alt/OG/ImageObject.

## AID-112 — Video strategy gate

**Actor:** HUMAN

No crear YouTube vacío.

## AID-113 — Transcript contract

**Actor:** REPO/CONTENT

Si se publica vídeo/audio.

## AID-114 — Social profile parity

**Actor:** HUMAN

Instagram/Facebook/TikTok/Threads/etc.

---

# P1 — Agent readiness

## AID-120 — Agent task audit

**Actor:** QA

Tareas:

- encontrar libro;
- comprar;
- fragmento;
- press kit;
- contacto;
- evento;
- suscripción;
- herramientas.

## AID-121 — Accessibility-tree QA

**Actor:** REPO

Aprovechar tests existentes.

## AID-122 — Subscription agent safety

**Actor:** REPO

DOI/consentimiento nunca saltables por agente.

## AID-123 — Retailer action clarity

**Actor:** REPO

Link label = retailer real.

---

# P2 — Commerce AI

## AID-130 — Merchant readiness gate

**Actor:** BUSINESS

Responder:

- ¿vendemos directamente?;
- ¿controlamos stock?;
- ¿precio?;
- ¿fulfillment?;
- ¿returns?;
- ¿payment?;

Si no, parar.

## AID-131 — ACP research refresh

**Actor:** RESEARCH

Solo si AID-130 sí.

## AID-132 — Merchant Center/UCP refresh

**Actor:** RESEARCH

Solo comercio propio.

## AID-133 — No fake Product/Offer test

**Actor:** REPO

Siempre relevante.

---

# P2 — Owned AI surfaces

## AID-140 — `/asistente/` role decision

**Actor:** PRODUCT

UX propia, no ranking tactic.

## AID-141 — ChatGPT App feasibility

**Actor:** PRODUCT

Solo si hay herramientas/acciones útiles.

## AID-142 — MCP public tool feasibility

**Actor:** PRODUCT/SECURITY

No exponer secrets/write admin.

## AID-143 — Gemini Connected App monitor

**Actor:** RESEARCH

No construir sin caso.

---

# P2 — Plataformas secundarias

## AID-150 — Brave benchmark

**Actor:** HUMAN

## AID-151 — Apple benchmark

**Actor:** HUMAN

## AID-152 — Meta AI benchmark

**Actor:** HUMAN

## AID-153 — Grok benchmark

**Actor:** HUMAN

## AID-154 — You/downstream benchmark

**Actor:** HUMAN

Solo si aporta señal.

---

# P3 — Monitoring de ecosistema

## AID-160 — Quarterly provider docs audit

**Actor:** RESEARCH

Buscar cambios en:

- bots;
- IP feeds;
- Search Console;
- Bing AI Performance;
- preferred sources;
- commerce feeds;
- source labels;
- agent protocols.

## AID-161 — `llms.txt` evidence review

**Actor:** RESEARCH

Actualizar estado si un proveedor oficial publica soporte explícito.

## AID-162 — Emerging crawler registry

**Actor:** RESEARCH

No añadir bot por blog de terceros sin verificar.

## AID-163 — GEO tooling market review

**Actor:** RESEARCH/BUSINESS

Solo si automatización manual deja de ser sostenible.

---

# Orden recomendado para Claude

1. AID-001 a AID-008.
2. AID-010 a AID-019.
3. AID-020 a AID-029.
4. AID-030 a AID-044.
5. AID-050 a AID-066.
6. AID-070 a AID-086.
7. AID-090 a AID-123.
8. P2 solo tras evidencia.

---

# Criterio de merge de implementación

Una PR futura de código no se mergea porque «mejora GEO».

Debe especificar:

- problema observable;
- plataforma;
- fuente oficial;
- cambio;
- riesgo;
- test;
- métrica posterior;
- rollback.

---

# Definition of Done de la iniciativa

### Infraestructura

- [ ] IndexNow activo y preciso;
- [ ] crawlers de search no bloqueados;
- [ ] WAF auditado;
- [ ] producción/paridad monitorizada.

### Conocimiento

- [ ] facts canónicos consistentes;
- [ ] stale register sin P0 abiertos;
- [ ] correcciones públicas;
- [ ] entity profiles revisados.

### Medición

- [ ] benchmark 5 Tier A;
- [ ] Bing AI Performance baseline;
- [ ] Search Console GenAI si disponible;
- [ ] referrals;
- [ ] crawler report.

### Contenido

- [ ] páginas de libro reader-fit;
- [ ] metodología visible en recursos clave;
- [ ] plan non-commodity ejecutándose;
- [ ] imágenes principales correctas.

### Autoridad

- [ ] Samuel external parity;
- [ ] Manecillas external matrix en marcha post-publicación;
- [ ] press/club/event evidence real.

### Seguridad/editorial

- [ ] no prompt injection;
- [ ] no fake reviews;
- [ ] no fake offers;
- [ ] training vs search consciente;
- [ ] no secretos en repo.
