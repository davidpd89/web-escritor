# 08 — Herramientas retiradas, legacy y anti-patrones

**Corte:** 27/08/2026  
**Objetivo:** impedir que el proyecto implemente recomendaciones SEO antiguas, APIs inadecuadas o herramientas de alto riesgo por inercia.

---

## 1. Indexing API ≠ API general de indexación

Google mantiene una **Indexing API**, pero no debe utilizarse para avisar de artículos, libros, herramientas, fichas de editoriales o cualquier página normal del sitio.

A fecha de corte Google limita esta API a páginas con:

- `JobPosting`; o
- `BroadcastEvent` embebido en `VideoObject` para emisiones en directo.

### Decisión para davidportodiaz.com

**NO IMPLEMENTAR** Indexing API para el contenido ordinario de la web.

Para páginas normales usar:

- sitemap;
- buen enlazado interno;
- URL Inspection / Request indexing en casos prioritarios;
- rastreo natural.

Si algún script futuro propone `indexing.googleapis.com/v3/urlNotifications:publish` para cada artículo o libro, debe rechazarse en revisión.

Fuente oficial:
https://developers.google.com/search/apis/indexing-api/v3/using-api?hl=es

---

## 2. Crawl Rate Limiter — RETIRADO

Google retiró el limitador manual de frecuencia de rastreo de Search Console el **8 de enero de 2024**.

Googlebot ajusta automáticamente el ritmo según respuesta del servidor, latencia y errores.

### Decisión

No buscar ni intentar automatizar un «crawl rate setting» inexistente.

Si hay rastreo excesivo/problemático:

1. revisar Crawl Stats;
2. revisar 5xx/latencia;
3. usar respuestas del servidor adecuadas;
4. recurrir al formulario de actividad inusual de Googlebot en casos excepcionales.

Fuente oficial:
https://developers.google.com/search/blog/2023/11/sc-crawl-limiter-byebye?hl=es

---

## 3. International Targeting — RETIRADO

El informe **Segmentación internacional** ya no está disponible.

Google sigue utilizando `hreflang`, pero Search Console ya no ofrece country targeting manual.

### Aplicación actual

El sitio opera principalmente en español y no tiene hoy una arquitectura internacional multiidioma que requiera hreflang complejo.

No buscar una configuración de «target España» en Search Console: ya no existe.

Fuente oficial:
https://support.google.com/webmasters/answer/12474899?hl=es

---

## 4. URL Parameters Tool — RETIRADO

Google retiró la herramienta de parámetros de URL en 2022.

### Decisión

No diseñar procedimientos que dependan de configurar parámetros manualmente dentro de Search Console.

Si aparecen URLs parametrizadas problemáticas, resolver mediante arquitectura web:

- enlaces limpios;
- canonical;
- redirects cuando proceda;
- robots solo para control de rastreo justificado;
- evitar crear combinaciones infinitas en origen.

Fuente oficial:
https://developers.google.com/search/blog/2022/03/url-parameters-tool-deprecated?hl=es

---

## 5. Mobile Usability report / Mobile-Friendly Test — RETIRADOS

Google retiró desde el **1 de diciembre de 2023**:

- el informe Mobile Usability de Search Console;
- Mobile-Friendly Test;
- Mobile-Friendly Test API.

Esto NO significa que mobile deje de importar.

### Sustitución en este proyecto

- responsive QA del repo;
- Pa11y/browser tests;
- Lighthouse;
- Core Web Vitals de campo;
- pruebas reales mobile.

No intentar recuperar/consultar una API de mobile-friendly eliminada.

Fuente oficial:
https://developers.google.com/search/blog/2023/04/page-experience-in-search?hl=es

---

## 6. Page Experience como score único — NO EXISTE COMO KPI SIMPLE

Google transformó el antiguo informe Page Experience y retiró también el filtro de Search appearance «Good page experience».

La experiencia de página sigue importando, pero no debe reducirse a una insignia única de Search Console.

### Para este sitio

Evaluar conjuntamente:

- Core Web Vitals;
- HTTPS;
- mobile UX;
- accesibilidad;
- estabilidad visual;
- navegación;
- ausencia de interstitials intrusivos;
- calidad de contenido.

No abrir tareas buscando «poner Page Experience en verde» como objetivo independiente.

Fuente oficial:
https://developers.google.com/search/blog/2023/04/page-experience-in-search?hl=es

---

## 7. Indexing crawler setting — RETIRADO

Tras completar mobile-first indexing, Google eliminó de Settings la información/configuración específica del crawler de indexación.

Para saber qué Googlebot rastrea el sitio, usar Crawl Stats.

No intentar seleccionar desktop/mobile crawler desde Search Console.

Fuente oficial:
https://developers.google.com/search/blog/2023/10/mobile-first-is-here?hl=es

---

## 8. Disavow Links Tool — EXISTE, PERO ES EXCEPCIONAL

Google mantiene la herramienta Disavow, pero advierte que es una función avanzada que puede perjudicar rendimiento si se usa incorrectamente.

Google indica que la mayoría de sitios **no la necesitan**.

Solo debería considerarse cuando concurran esencialmente:

1. gran cantidad de backlinks spam/artificiales/de baja calidad; y
2. esos enlaces hayan provocado o probablemente vayan a provocar una acción manual por esquemas de enlaces.

Antes, intentar retirar enlaces problemáticos de origen cuando sea viable.

### Particularidad importante

La herramienta Disavow **no funciona con Domain properties**. Requiere una URL-prefix property compatible.

### Decisión del proyecto

- no generar `disavow.txt` automáticamente desde el informe Links;
- no desautorizar dominios por métricas de terceros;
- no usarlo como «limpieza SEO» periódica;
- solo abrir este flujo con evidencia de enlace artificial + riesgo real/manual action.

Fuente oficial:
https://support.google.com/webmasters/answer/2648487?hl=en

---

## 9. Rich-result types retirados

Search Console y Google Search retiran apariencias con el tiempo.

### FAQ — 2026

Desde 07/05/2026 FAQ rich results dejaron de mostrarse y en agosto 2026 Google retira esa apariencia de la API.

### Otros tipos retirados en 2025

Google retiró de Search/soporte Search Console tipos como:

- Course Info;
- Claim Review;
- Estimated Salary;
- Learning Video;
- Special Announcement;
- Vehicle Listing.

### Regla

No mantener schemas solo para perseguir una apariencia eliminada. El markup puede seguir siendo semánticamente válido en otros contextos, pero no debe justificarse con un rich result que Google ya no soporta.

Fuente oficial:
https://developers.google.com/search/blog/2025/06/simplifying-search-results?hl=es

---

## 10. Data Highlighter — LEGACY, EVITAR

Aunque el catálogo legacy puede seguir mostrando Data Highlighter, este repo controla su HTML/JSON-LD y tiene QA reproducible.

Usarlo introduciría configuración manual no versionada.

**Decisión:** structured data en código + tests, no Data Highlighter.

---

## 11. Request indexing masivo — ANTI-PATRÓN

URL Inspection permite solicitar indexación, pero no es una API/promesa de inclusión ni un mecanismo para «forzar ranking».

### No hacer

- solicitud diaria para las mismas URLs;
- automatizar clicks/scraping de la interfaz;
- usarla para todo el sitemap;
- asumir que request indexing corrige una página de baja calidad/canonical incorrecta.

### Sí hacer

- página nueva muy prioritaria;
- corrección importante;
- recuperación tras `noindex`/bloqueo accidental;
- lanzamiento relevante.

---

## 12. Resubmit sitemap compulsivo — ANTI-PATRÓN

Un sitemap accesible y correctamente enviado no necesita volver a enviarse por cada cambio menor.

El crawler puede leerlo de nuevo y `lastmod` debe informar cambios significativos.

Reenviar solo por motivo operativo:

- sitemap nuevo/cambio de URL;
- corrección de error;
- migración estructural;
- recuperación de un problema de lectura.

---

## 13. Robots.txt para desindexar — ANTI-PATRÓN

`robots.txt` evita rastreo, no garantiza eliminación del índice.

Para retirar permanentemente una página elegir según caso:

- `noindex` con acceso de crawl;
- 404/410;
- auth/protección;
- redirect cuando haya reemplazo real.

Removals puede acelerar una retirada urgente, pero no sustituye la solución permanente.

---

## 14. Removals como limpieza rutinaria — ANTI-PATRÓN

No usar Removals para:

- 404 normales;
- URLs obsoletas que Google eliminará tras recrawl;
- coverage warnings;
- reordenar resultados.

Sí usar para contenido sensible/publicado por error o necesidad urgente de ocultación temporal mientras se corrige origen.

---

## 15. Schema por SEO sin realidad subyacente — ANTI-PATRÓN

No añadir:

- Offer sin oferta;
- MerchantListing sin venta directa;
- Event sin evento real;
- Review/Rating sin evidencia real;
- FAQ solo por rich result retirado;
- Product para representar cualquier obra sin estudiar el caso semántico.

Structured data debe representar contenido visible y verdadero.

---

## 16. Convertir cada query en una página — ANTI-PATRÓN

Search Console descubre long-tail, pero una query nueva no justifica una URL nueva.

Antes de crear contenido:

- ¿hay intención diferente?
- ¿tenemos algo original que decir?
- ¿encaja con territorio editorial?
- ¿se puede mantener?
- ¿ya responde una página existente?

Preferir mejorar una autoridad existente antes que crear thin content.

---

## 17. Optimizar para CTR sin mirar SERP — ANTI-PATRÓN

Un CTR «bajo» puede deberse a:

- posición;
- query informativa;
- módulos de SERP;
- respuesta directa;
- branded vs generic;
- imágenes/vídeo;
- intención distinta.

Nunca automatizar reescritura de titles por un threshold de CTR aislado.

---

## 18. Confundir impressions de IA con tráfico — ANTI-PATRÓN

El informe GenAI 2026 se centra en impresiones.

No convertir:

- +impressions = +visitas;
- -impressions = penalización;
- aparecer en AI Overview = cita/endorsement.

Evaluar como señal adicional de descubrimiento.

---

## 19. Confundir Google-Extended con Search GenAI control — ANTI-PATRÓN

`Google-Extended` no es un user-agent de Search ranking convencional y el nuevo control Search generative AI de Search Console es un mecanismo distinto.

Mantener documentados por separado:

- política robots/crawlers;
- política de uso extendido de Google;
- inclusión en features GenAI de Search/Discover.

---

## 20. Confundir Search Console con analítica onsite — ANTI-PATRÓN

Search Console mide interacción **en resultados de Google** y estado de Search; no sustituye analítica de comportamiento dentro de la web.

No usar GSC para responder directamente:

- conversiones newsletter;
- clics internos;
- scroll;
- uso de herramientas;
- compra externa;
- sesiones completas.

Cruzar con la analítica onsite solo cuando exista una clave/agrupación compatible y respetuosa con privacidad.

---

## 21. Checklist para revisar propuestas futuras de Claude/GPT

Rechazar una propuesta si dice cualquiera de estas cosas sin matices/evidencia:

- «usar Indexing API para todos los artículos»;
- «subir el crawl rate en Search Console»;
- «configurar España en International Targeting»;
- «usar URL Parameters tool»;
- «hacer todos los backlinks tóxicos disavow»;
- «poner FAQ schema para rich snippets»;
- «activar AMP para posicionar»;
- «solicitar indexación cada día»;
- «reenviar sitemap diariamente»;
- «bloquear con robots para desindexar»;
- «crear Merchant listing aunque Amazon haga la venta»;
- «crear una página por keyword»;
- «cambiar titles automáticamente si CTR < X»;
- «la caída de GenAI impressions prueba una penalización».

Todas son recetas obsoletas, incompletas o peligrosas en el contexto actual.