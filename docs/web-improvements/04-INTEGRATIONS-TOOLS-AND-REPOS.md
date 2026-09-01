# Integraciones, herramientas y repositorios evaluados

No son “instalar todo”. Cada entrada necesita trigger, coste/riesgo y owner.

## Bing Webmaster Tools + AI Performance

**Estado:** recomendado como operación externa si aún no está configurado.  
**Fuente:** https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview

Aporta datos que Search Console no da con el mismo enfoque: citas en respuestas IA, URLs citadas, grounding queries y tendencias. Bing advierte que número de citas no equivale a ranking/authority/placement.

**Onboarding:** propiedad verificada → sitemap/indexación → baseline AI Performance → export/snapshot trimestral. No crear un “AI score” propio.

## IndexNow

**Estado:** implementar después de deuda actual.  
**Fuente:** https://www.indexnow.org/documentation

Integración post-deploy, no pre-build. Debe enviar solo URLs públicas cambiadas y registrar release SHA/respuesta. 200/202 = solicitud recibida/procesándose, no indexación confirmada.

## Ahrefs Free

**Estado:** segunda opinión opcional.  
**Fuente:** https://ahrefs.com/webmaster-tools

La oferta actual para sitios verificados incluye Site Audit, Site Explorer y Web Analytics con límites gratuitos. Puede detectar divergencias respecto a nuestros checkers o aportar otra vista de backlinks/queries.

**No hacer:** instalar su analytics además de los actuales solo porque sea gratis; perseguir scores propietarios como KPI; duplicar cada warning en tickets sin reproducirlo.

## Screaming Frog SEO Spider

**Estado:** segunda opinión local opcional.  
**Fuentes:** https://www.screamingfrog.co.uk/seo-spider/ y https://www.screamingfrog.co.uk/seo-spider/pricing/

La edición gratuita mantiene límite de 500 URLs, suficiente para el tamaño actual del sitio. Útil para crawl independiente de status/canonical/meta/links.

**Uso recomendado:** export ad-hoc durante auditorías grandes. Si encuentra algo que nuestros contratos no encuentran, convertir ese hallazgo en test del repo; no meter Screaming Frog en CI por defecto.

## Microsoft Clarity + MCP

**Estado:** condicional por privacidad/hipótesis UX.  
**Fuentes:**
- https://learn.microsoft.com/en-us/clarity/third-party-integrations/clarity-mcp-server
- https://github.com/microsoft/clarity-mcp-server
- https://github.com/microsoft/mcp

El MCP oficial está activo en 2026 y el paquete `@microsoft/clarity-mcp-server` existe. Permite consultar analytics/recordings desde clientes MCP.

**Gate:** no instalar Clarity tracking para justificar el MCP. Primero formular una pregunta que no respondan browser QA, GoatCounter u observación manual; después revisar privacidad/consentimiento/mascarado/retención. Token en secret local, nunca Git.

Ejemplo documentado por Microsoft:

```bash
npx @microsoft/clarity-mcp-server --clarity_api_token="$CLARITY_API_TOKEN"
```

No copiar el token en `.mcp.json` versionado.

## Brevo Consent Groups

**Estado:** condicional a feature/plan; listas/segments siguen siendo baseline.  
**Fuentes:**
- https://developers.brevo.com/changelog/2026/6/30
- https://help.brevo.com/hc/es/articles/208771869-Crear-un-formulario-de-suscripci%C3%B3n-en-Brevo

La API existe cuando Consent Groups está habilitado; la ayuda actual indica disponibilidad Professional/Enterprise. Un `403 CONSENT_GROUP_NOT_ENABLED` es un estado válido, no una razón automática para upgrade.

## CrUX API / History

**Estado:** usar cuando haya field data suficiente.  
**Fuentes:**
- https://developer.chrome.com/docs/crux/api/
- https://developer.chrome.com/docs/crux/history-api/

API key de GCP como secreto. No interpretar ausencia de datos como rendimiento bueno/malo.

## Google Books / Google Play Books

**Estado:** condicional a derechos.  
**Fuentes:**
- https://support.google.com/books/partner/
- https://support.google.com/books/partner/answer/1079107
- https://support.google.com/books/partner/answer/10010291
- https://developers.google.com/books

Puede mejorar descubrimiento/previews y, cuando proceda, venta de ebook. Solo quien tenga derecho/capacidad de gestión debe subir archivos/configurar disponibilidad. Para libros con editorial, confirmar contrato/operativa antes.

## BookBub / Books2Read

**Estado:** defer/condicional.  
**Fuentes:** https://partners.bookbub.com/ y https://books2read.com/

Mayor encaje cuando exista ebook en retailers compatibles o múltiples destinos de compra. No crear perfiles vacíos ni smart links sin catálogo/URLs reales.

## Herramientas que ya existen en el repo y tienen prioridad sobre sustituirlas

- Pagefind para búsqueda: `scripts/build-pagefind-index.py`.
- Grafo interno/discoverability: checkers existentes.
- ICS: `herramientas/eventos-ics/`.
- Lighthouse/Pa11y/Playwright/browser QA: suite existente.
- Service Worker/offline/manifest shortcuts: PWA existente.
- Feed: `feed.xml`, generado por `scripts/build-feed.py`.

La regla es mejorar primero la solución existente. Una herramienta externa entra cuando demuestra un gap, no por prestigio o novedad.
