# Fuentes primarias — mejoras web

**Corte:** 2026-08-28.  
Solo se consideran autoridad normativa/funcional las fuentes del proveedor/estándar. Blogs SEO, agencias y listicles pueden inspirar búsquedas, pero no justifican una decisión.

## Google Search

| Clave | Fuente | Uso |
|---|---|---|
| S-GOOGLE-BREADCRUMB | https://developers.google.com/search/docs/appearance/structured-data/breadcrumb | `BreadcrumbList`; elegibilidad/guías. Google documenta que breadcrumbs aparecen en desktop, no deben venderse como mejora móvil. |
| S-GOOGLE-FAQ | https://developers.google.com/search/docs/appearance/structured-data/faqpage | `FAQPage`; disponibilidad restringida, no táctica general de autor. |
| S-GOOGLE-REVIEWS | https://developers.google.com/search/docs/appearance/structured-data/review-snippet | `Review`/`AggregateRating`; contenido visible, genuino; **no agregar reviews/ratings de otros sitios**. |
| S-GOOGLE-CANONICAL | https://developers.google.com/search/docs/crawling-indexing/canonicalization | canonicalización; redirect/canonical/sitemap como señales, Google puede elegir otra canonical. |
| S-GOOGLE-CANONICAL-TROUBLE | https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting | diagnóstico con URL Inspection; re-evaluación puede tardar. |
| S-GOOGLE-SITEMAP | https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap | sitemaps generales y extensiones. |
| S-GOOGLE-IMAGE-SITEMAP | https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps | útil especialmente para imágenes no descubribles de otro modo. |
| S-GOOGLE-VIDEO-SITEMAP | https://developers.google.com/search/docs/crawling-indexing/sitemaps/video-sitemaps | útil para vídeo nuevo/importante/difícil de descubrir. |
| S-GOOGLE-HREFLANG | https://developers.google.com/search/docs/specialty/international/localized-versions | `hreflang` solo con variantes localizadas reales; todas se referencian mutuamente. |
| S-GOOGLE-SPONSORED | https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links | paid/affiliate: `rel=sponsored` preferido; `nofollow` aceptado. |
| S-GOOGLE-SPAM | https://developers.google.com/search/docs/essentials/spam-policies | doorway/scaled content/link spam/cloaking y otros anti-patrones. |
| S-GOOGLE-AI | https://developers.google.com/search/docs/appearance/ai-features | visibilidad en funciones de IA: fundamentos SEO/people-first, no “schema GEO” secreto. |
| S-GOOGLE-PREFERRED | https://developers.google.com/search/docs/appearance/preferred-sources | Preferred Sources; selección por usuario, no boost general de ranking. |
| S-GOOGLE-FAVICON | https://developers.google.com/search/docs/appearance/favicon-in-search | requisitos vigentes de favicon en resultados. |

### Decisiones derivadas

- A.7 se rechaza como táctica de rich results general.
- A.12 nunca usa Amazon/Goodreads/Babelio como `AggregateRating` propio.
- C.5 no genera una URL por variante de keyword.
- K.3 marca relaciones pagadas/afiliadas.
- N.1/N.2 esperan versiones lingüísticas reales.

## Bing / IndexNow

| Clave | Fuente | Uso |
|---|---|---|
| S-BING-AI-PERFORMANCE | https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview | citas, páginas citadas, grounding queries, tendencias. El propio Bing aclara que cita ≠ ranking/authority/placement. |
| S-BING-GROUNDING | https://blogs.bing.com/search/February-2026/Elevating-the-Role-of-Grounding-on-the-AI-Web | contexto oficial de grounding y observabilidad. |
| S-INDEXNOW | https://www.indexnow.org/documentation | protocolo; notificar URLs añadidas/actualizadas/eliminadas. Respuesta de API no equivale a indexación garantizada. |

### Política IndexNow

- Ejecutar **después** de publicar y verificar el artifact.
- Solo URLs públicas cambiadas; excluir `noindex`, privadas, gated y assets internos.
- Una key en origen según especificación; secreto/gestión fuera de Git si aplica.
- Loguear URL, fecha, respuesta y release SHA.
- No usarlo como “factor de ranking”.

## Accesibilidad / plataforma web

| Clave | Fuente | Uso |
|---|---|---|
| S-WCAG22 | https://www.w3.org/TR/WCAG22/ | Resize Text 200%, Text Spacing, Target Size (Minimum) 24×24 CSS px con excepciones, foco, etc. |
| S-MDN-PUSH | https://developer.mozilla.org/en-US/docs/Web/API/Push_API | Push requiere suscripción/service worker y servidor/sender; permisos y seguridad. |
| S-MDN-MANIFEST | https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/shortcuts | shortcuts del manifest. |
| S-MDN-BADGING | https://developer.mozilla.org/en-US/docs/Web/API/Badging_API | Badging y compatibilidad/contexto. |

**Regla del proyecto:** cumplir WCAG AA no obliga a rebajar componentes que ya tienen un contrato visual más estricto. Si el proyecto protege 42 px, el test conserva 42 px aunque WCAG 2.5.8 permita 24 px en su mínimo AA.

## Rendimiento / field data

| Clave | Fuente | Uso |
|---|---|---|
| S-WEBDEV-INP | https://web.dev/articles/inp | INP; p75, <=200 ms como “good”. |
| S-CRUX | https://developer.chrome.com/docs/crux/api/ | CrUX API de campo. |
| S-CRUX-HISTORY | https://developer.chrome.com/docs/crux/history-api/ | series históricas de CrUX. |
| S-CLOUDFLARE-COMPRESSION | https://developers.cloudflare.com/speed/optimization/content/compression/ | comportamiento de compresión cuando Cloudflare la aplica; **no sustituye medir la respuesta live del sitio**. |

**Corrección crítica respecto a investigación histórica:** que DNS/zone esté en Cloudflare no demuestra que una respuesta concreta esté comprimida ni qué capa la comprimió. E.7 requiere observar `Content-Encoding` con requests reales.

## Brevo

| Clave | Fuente | Uso |
|---|---|---|
| S-BREVO-CONSENT | https://help.brevo.com/hc/es/articles/208771869-Crear-un-formulario-de-suscripci%C3%B3n-en-Brevo | multi-list y disponibilidad de Consent Groups; la ayuda actual los sitúa en Professional/Enterprise. |
| S-BREVO-CONSENT-API | https://developers.brevo.com/changelog/2026/6/30 | endpoints Consent Groups cuando la feature está habilitada; devuelve `CONSENT_GROUP_NOT_ENABLED` si no. |
| S-BREVO-CHANGELOG | https://developers.brevo.com/changelog | cambios 2026, OAuth scopes y deprecaciones. |

### Regla

No subir de plan por H.1 salvo que el preference center/consent model justifique el coste. Con el plan actual, listas/segmentos siguen siendo baseline válido.

## Microsoft Clarity MCP

| Clave | Fuente | Uso |
|---|---|---|
| S-CLARITY-MCP | https://learn.microsoft.com/en-us/clarity/third-party-integrations/clarity-mcp-server | documentación oficial Microsoft; MCP activo. |
| S-CLARITY-MCP-REPO | https://github.com/microsoft/clarity-mcp-server | repo oficial, paquete `@microsoft/clarity-mcp-server`, actividad 2026. |
| S-MICROSOFT-MCP-CATALOG | https://github.com/microsoft/mcp | catálogo oficial incluye Microsoft Clarity. |

**Corrección crítica:** cualquier documento que afirme “Clarity MCP fue retirado el 16/01/2026” es incorrecto. A 2026-08-28 el servidor oficial sigue documentado/activo (package 2.0.x y actividad 2026). La razón para no instalar Clarity por defecto es privacidad/hipótesis de investigación, no inexistencia del MCP.

## Herramientas de segunda opinión

No son autoridad del producto ni deben convertirse en CI por defecto.

- Ahrefs Webmaster Tools: https://ahrefs.com/webmaster-tools — auditoría/links para propiedades verificadas; útil como segunda opinión.
- Screaming Frog SEO Spider: https://www.screamingfrog.co.uk/seo-spider/ — crawl local; edición gratuita con límite de URLs según condiciones vigentes.
- Pagefind: https://pagefind.app/ — ya usado en el repo; priorizar tuning de la solución existente antes de búsqueda semántica remota.

## Libros / distribución

Estas fuentes solo se activan con derechos/catálogo reales:

- Google Books Partner Center: https://support.google.com/books/partner/
- Google Books APIs: https://developers.google.com/books
- BookBub Partners: https://partners.bookbub.com/
- Books2Read: https://books2read.com/

No crear perfiles/ofertas/feeds como estrategia SEO si no existe ebook, retailer compatible, derecho de gestión o catálogo que lo justifique.

## Fuentes que NO son autoridad final

Se excluyen como fundamento de decisiones: agencias SEO, posts de tendencias, blogs de herramientas no proveedoras, listicles “2026”, métricas propietarias tipo DA/SEO score y afirmaciones no contrastadas sobre “GEO”. Si una idea nació allí, se conserva únicamente si una fuente primaria o evidencia del repo la sostiene.
