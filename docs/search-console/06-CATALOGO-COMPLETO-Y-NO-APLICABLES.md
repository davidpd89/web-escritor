# 06 — Catálogo completo: funciones vigentes, condicionales y no aplicables

Este fichero existe para evitar un sesgo habitual: documentar solo las funciones que parecen útiles hoy y olvidar capacidades que Search Console mostrará si el sitio cambia. Se contrasta contra el catálogo oficial de informes/herramientas vigente a 27/08/2026.

---

## 1. Informes/herramientas actuales cubiertos por esta PR

- Overview / Descripción general.
- Insights / Estadísticas.
- Performance — Search web.
- Performance — Discover, si hay datos.
- Performance — Google News, si hay datos.
- URL Inspection.
- Page Indexing.
- Sitemaps.
- Removals + SafeSearch.
- Core Web Vitals.
- Rich result status reports detectados.
- Manual Actions.
- Security Issues.
- Links.
- Achievements.
- Property verification.
- Users & permissions.
- Associations.
- Change of Address.
- Bulk data export.
- robots.txt report.
- Crawl Stats.
- Search Console API / URL Inspection API.
- 2026 annotations.
- branded/non-branded filter.
- 2026 GenAI Search report.
- 2026 Search generative AI control.
- GenAI Discover cuando esté disponible.
- 2026 platform properties.

Los siguientes apartados completan lo que no es prioritario hoy.

---

## 2. Video Indexing — CONDICIONAL

Search Console genera un informe de **Indexación de vídeos** para sitios con páginas indexadas donde Google detecta vídeos.

El informe distingue, a grandes rasgos:

- páginas indexadas con vídeo indexado;
- páginas indexadas donde Google encontró vídeo pero no pudo indexarlo;
- motivos del fallo;
- detalle inspeccionable por URL.

Google solo puede asociar/indexar vídeo desde una **watch page indexada** que cumpla requisitos. El informe cuenta páginas con vídeo, no un inventario exhaustivo de vídeos únicos.

### Aplicación a davidportodiaz.com

**Estado actual:** no se ha identificado en esta auditoría una familia de «watch pages» como eje del sitio. Por tanto no se propone crear vídeo/schema solo para conseguir este informe.

### Cuándo activarlo como prioridad

Si en el futuro se crean:

- trailers oficiales de libros;
- entrevistas;
- lecturas de fragmentos;
- vídeos de eventos/presentaciones;
- vídeos editoriales con URL propia y valor de búsqueda,

entonces:

1. página individual indexable por vídeo importante;
2. vídeo prominente;
3. thumbnail accesible;
4. VideoObject si cumple la documentación vigente;
5. sitemap/video metadata si compensa;
6. URL Inspection;
7. revisar Video Indexing.

**No confundir** un vídeo de YouTube indexado en Google con la indexación del vídeo asociado a una página de davidportodiaz.com.

Fuente oficial:
https://support.google.com/webmasters/answer/9495631?hl=es

---

## 3. AMP report — NO APLICABLE ACTUALMENTE

Search Console mantiene un informe de estado AMP cuando el sitio tiene páginas AMP detectadas.

### Decisión para este proyecto

No implementar AMP únicamente para «tener el informe» o por una idea antigua de SEO. El sitio actual tiene su propio sistema responsive/performance y no se ha detectado una necesidad de una variante AMP.

Si algún día aparece el informe AMP inesperadamente:

- investigar si una URL/plantilla lo está declarando;
- confirmar que es intencional;
- si AMP se adopta de forma consciente, objetivo = cero errores críticos;
- si no es intencional, eliminar la variante/relación en origen.

Fuente oficial:
https://support.google.com/webmasters/answer/7450883?hl=es

---

## 4. Shopping / Merchant opportunities — NO APLICABLE COMO MERCHANT HOY

Search Console puede mostrar una sección **Shopping** cuando Google identifica el sitio como comercio online o detecta Product structured data.

Puede incluir:

- Merchant opportunities;
- Product snippet rich result report;
- Merchant listing rich result report;
- Shipping and returns settings.

### Definición operativa importante de Google

Un online merchant, a efectos de estos informes, vende productos/servicios **directamente al consumidor en su propio sitio**. Un sitio que redirige al usuario a retailers externos y no permite completar la compra allí no se considera merchant online para este propósito.

### Aplicación actual

`davidportodiaz.com` es web de autor/editorial, no ecommerce propio confirmado. Samuel enlaza a retailers externos y Manecillas no debe inventar disponibilidad/Offer mientras no exista fuente comercial verificada.

Por tanto:

- no crear Merchant Listing artificialmente;
- no crear Merchant Center solo para forzar features de Search Console;
- no publicar shipping/returns ficticios;
- no convertir un PVP editorial en una oferta online.

### Cuándo reevaluar

Si se habilita compra directa en la web:

1. contrato comercial real;
2. checkout directo;
3. Product/Merchant Listing válido;
4. Merchant Center si aporta valor;
5. asociación con Search Console;
6. Shipping/returns verídicos;
7. monitorizar Shopping reports.

Fuentes oficiales:
https://support.google.com/webmasters/answer/12660034?hl=es-es
https://support.google.com/webmasters/answer/14907594?hl=es

---

## 5. Shipping and Returns — NO APLICABLE ACTUALMENTE

Para merchants, Search Console permite gestionar:

- tiempo de entrega;
- gasto de envío;
- plazo de devolución;
- coste de devolución.

Requiere owner o full user. Si existe Merchant Center, debe asociarse.

**Decisión:** no configurar hasta que davidportodiaz.com venda directamente.

---

## 6. Rich Results Test — HERRAMIENTA EXTERNA COMPLEMENTARIA

La prueba de resultados enriquecidos puede validar una URL aunque no pertenezca a una property. URL Inspection da más contexto dentro de una property.

### Uso en este repo

Después de cambiar schema:

1. tests estáticos/CI del repo;
2. Rich Results Test contra deploy/staging accesible cuando proceda;
3. URL Inspection después de producción;
4. rich-result report para seguimiento a escala.

No asumir que «valid JSON-LD» = rich result garantizado.

Catálogo oficial:
https://support.google.com/webmasters/answer/9133276?hl=es

---

## 7. AMP Test — NO APLICABLE

Existe herramienta de prueba AMP independiente. Como no proponemos AMP, no forma parte del runbook normal.

Solo usar si el proyecto introduce AMP explícitamente.

---

## 8. Data Highlighter — LEGACY / NO RECOMENDADO PARA ESTE REPO

Google conserva **Data Highlighter** dentro de herramientas antiguas: sirve para ayudar a extraer datos de páginas de plantilla cuando no se puede implementar markup estructurado en el HTML.

### Decisión

No usar.

Motivo:

- controlamos el código fuente;
- ya usamos JSON-LD/structured data versionado;
- los cambios deben ser auditables en Git;
- una capa manual en Search Console crearía otra fuente de configuración fuera del repo.

Solo tendría sentido en un hosting extremadamente limitado donde no se pudiese tocar el markup, situación que no aplica aquí.

Fuente: catálogo oficial de informes/herramientas.

---

## 9. Web Tools — LEGACY / USO CASO A CASO

El catálogo oficial conserva un acceso a «Web Tools / otras herramientas». No debe convertirse en una dependencia del flujo principal sin un caso concreto y documentación vigente.

Regla:

- si una herramienta legacy resuelve un problema real, investigar su documentación en ese momento;
- no añadir pasos rutinarios por completismo.

---

## 10. Business user data access request — NO APLICABLE

El catálogo menciona un formulario para solicitudes empresariales de datos no disponibles en los informes.

Este proyecto no tiene hoy una necesidad empresarial de acceso a datasets especiales de Google. No abrir solicitudes sin una pregunta de datos concreta.

---

## 11. Apps / Android / Play — NO APLICABLE

Search Console puede asociarse con ecosistemas Android/Play en determinados escenarios.

La web no tiene una app Android canónica documentada. No crear asociaciones vacías.

Si surge una app oficial:

- verificar entidad;
- revisar deep links/indexing vigente;
- asociar solo entonces.

---

## 12. Google Ads association — CONDICIONAL

Puede asociarse si existen campañas y un motivo de análisis/operación.

No es necesario para posicionamiento orgánico. No crear Google Ads únicamente por Search Console.

---

## 13. Google Analytics association — CONDICIONAL

Puede compartir datos de Search Console con Analytics.

El proyecto utiliza actualmente otras soluciones de analítica. Añadir GA4 debe ser una decisión deliberada de medición/privacidad, no un requisito de Search Console.

Si se crea GA4:

- asociación con la property canónica;
- revisar permisos de Analytics porque sus usuarios pueden acceder a los datos compartidos;
- mantener claro qué herramienta es autoridad de cada métrica.

---

## 14. Merchant Center association — CONDICIONAL FUTURO

Solo cuando haya un modelo merchant real o necesidades de producto que lo justifiquen.

No confundir ISBN/libro con merchant eligibility.

---

## 15. Vertex AI Agent Builder association — NO APLICABLE ACTUALMENTE

Search Console documenta Vertex AI Agent Builder entre tipos de asociación posibles.

No tiene relación directa con el asistente web Cloudflare actualmente diseñado en el repositorio. No asociar servicios solo porque Search Console permita hacerlo.

---

## 16. Search Appearance types — DINÁMICOS

La dimensión `searchAppearance` puede cambiar con las funciones que Google soporte/detecte.

Regla del sistema:

- no hardcodear una lista eterna;
- inventariar periódicamente valores reales en UI/API/BigQuery;
- documentar tipos nuevos;
- evitar análisis históricos que rompan cuando se retire un appearance.

### Caso FAQ 2026

Desde 07/05/2026 Google dejó de mostrar FAQ rich results. En agosto de 2026 retira soporte FAQ de la Search Console API.

No mantener dashboards/alertas que consideren FAQ una oportunidad futura.

---

## 17. Search performance de Images

Aunque el informe principal se trate en `01`, para esta web merece un recordatorio específico.

### Por qué importa

- portadas de libros;
- mockups;
- recursos gráficos;
- imágenes de autor/prensa;
- posibles búsquedas visuales.

### Acción mensual

Filtrar Search type = Image:

- top pages;
- top queries;
- imágenes/URLs que traen clicks;
- verificar que las imágenes importantes están en páginas indexables y con contexto/alt apropiado.

No inferir qué archivo concreto generó una impression solo desde page-level data si GSC no lo identifica.

---

## 18. Search performance de Video

Aunque no haya Video Indexing report relevante, Search Performance puede tener `search type = video` si existe tráfico suficiente.

Si aparece:

- separar de web;
- identificar landing pages;
- valorar si crear watch pages tiene sentido editorial.

---

## 19. Search performance de News

Dos conceptos distintos:

- `search type = news` en Search Performance → pestaña Noticias de Google Search;
- Google News performance → news.google.com + apps.

Nunca fusionarlos sin etiqueta de fuente.

---

## 20. Search Console achievements — utilidad limitada

Los logros pueden marcar hitos de clicks (por ejemplo primeros 1.000).

Uso:

- motivación/momentum;
- posible nota interna;
- no KPI de calidad;
- no factor de ranking.

No orientar estrategia para «desbloquear un logro».

---

## 21. Configuraciones que pueden aparecer y no requieren acción

La interfaz de Search Console es dinámica por property. Si aparece una nueva sección:

1. buscar documentación oficial;
2. comprobar estado GA/rollout/experimental;
3. entender elegibilidad;
4. decidir si tiene caso real en esta web;
5. añadirla a `04-FUENTES-Y-ESTADO-2026.md`;
6. solo entonces crear tarea.

No ejecutar una función nueva basándonos en el nombre de la tarjeta.

---

## 22. Matriz «si aparece, qué hacemos»

| Función | Si aparece | Si no aparece |
|---|---|---|
| Video Indexing | auditar páginas de vídeo | no crear vídeos para forzarlo |
| AMP | verificar si AMP es intencional | correcto; no hace falta AMP |
| Shopping | confirmar si Google entiende merchant/Product | no forzar merchant |
| Product snippets | validar schema real | no crear Product sin caso semántico |
| Merchant listings | comprobar venta directa | no aplica sin checkout propio |
| Shipping/returns | configurar datos reales del merchant | no inventar políticas |
| Discover | crear baseline y estudiar winners | no es error |
| Google News | baseline separado | no es error |
| Rich result report | resolver errors/warnings relevantes | no significa schema inválido |
| GenAI report | baseline + monitor | rollout/insufficient data |
| Platform properties | añadir cuentas canónicas | rollout pendiente |
| Social Insights | usar como pista | experimental/no señal suficiente |

---

## 23. Fuente de completitud

Catálogo oficial de informes y herramientas de Search Console, consultado el 27/08/2026:

https://support.google.com/webmasters/answer/9133276?hl=es

Shopping:

https://support.google.com/webmasters/answer/12660034?hl=es-es

Video Indexing:

https://support.google.com/webmasters/answer/9495631?hl=es

AMP:

https://support.google.com/webmasters/answer/7450883?hl=es

La regla para futuras revisiones es volver primero a este catálogo, no asumir que el menú de Search Console de 2026 permanecerá igual.