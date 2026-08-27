# 14 — Productos Google y oportunidades condicionales

## Objetivo

Separar:

- productos que aportan señales/medición directamente relevantes para Search;
- productos que pueden ampliar descubrimiento;
- productos útiles solo bajo determinadas condiciones;
- productos que **no** debemos activar por ritual SEO.

Nada de esta matriz implica que usar más productos de Google haga que Google premie orgánicamente a la web.

---

# 1. Matriz ejecutiva

| Producto / superficie | Estado para el proyecto | Prioridad | Motivo |
|---|---|---:|---|
| Google Search Console | USAR | P0 | observabilidad Search |
| Search Console Insights | USAR si disponible | P1 | tendencias/contenido |
| Search Console BigQuery bulk export | EVALUAR/USAR | P1 | histórico/granularidad |
| Google Trends | USAR | P1 | interés relativo/estacionalidad |
| Google Preferred Sources | EVALUAR elegibilidad | P1 | lectores pueden elegir fuente |
| Knowledge Panel claim | SOLO SI EXISTE | P1 | corregir/controlar entidad elegible |
| Google Books | EVALUAR con derechos/editorial | P1 | discoverability de libros |
| Google Play Books | EVALUAR comercialmente | P2 | distribución ebook, no SEO requisito |
| Google Images | USAR orgánicamente | P1 | portadas/autor/eventos |
| Discover | ELEGIBILIDAD AUTOMÁTICA | P1 | alcance editorial |
| Google News | ELEGIBILIDAD AUTOMÁTICA | P2 | solo contenido news-like |
| YouTube | EVALUAR con estrategia real | P2 | vídeo/discovery |
| Google Business Profile | N/A AHORA | — | no crear perfil local ficticio |
| Merchant Center | N/A AHORA | — | no somos merchant directo general |
| Google Shopping | N/A AHORA | — | no inventar catálogo/ofertas |
| Google Ads | CANAL SEPARADO | — | paid ≠ organic ranking |
| Google Analytics | OPCIONAL/medición | — | no factor ranking; privacidad/stack actual |
| Google Scholar | N/A | — | web literaria, no publicación académica |
| AMP | NO IMPLEMENTAR POR SEO | — | no requisito |
| Publisher Center para “dar de alta News” | OBSOLETO COMO SUBMISSION | — | News automático desde 2025 |
| Indexing API para libros/artículos | NO USAR | — | tipo de contenido no elegible |

---

# 2. Search Console

Ya documentado exhaustivamente en:

`docs/search-console/`

No duplicar.

## Para SEO

Usarlo para cerrar:

- indexación;
- canonical;
- queries;
- CTR;
- CWV;
- links;
- enhancements;
- manual actions;
- security;
- AI/Discover/platform data cuando esté disponible.

---

# 3. Search Console Insights

Usarlo como detector de:

- contenido con crecimiento;
- queries nuevas;
- páginas en tendencia;
- fuentes y patrones.

No convertir una tarjeta de Insights en orden automática de publicar más del mismo tema.

Decision flow:

`signal → inspect query/page → Search Analytics detail → editorial fit → action`

---

# 4. BigQuery bulk export

El plan Search Console recomienda activarlo temprano si se aprueba proyecto GCP/billing.

SEO value:

- histórico propio;
- análisis de cohorts;
- query/page matrices;
- canibalización;
- experiment baselines;
- brand/nonbrand;
- anomaly detection.

No es un factor de ranking. Es infraestructura de decisión.

---

# 5. Google Trends

Google Trends normaliza interés:

- por tiempo;
- por geografía;
- escala relativa 0–100.

No equivale a volumen absoluto.

## Usos

### Géneros

Comparar:

- portal fantasy;
- fantasía de portales;
- fantasía juvenil;
- worldbuilding;
- escritura creativa.

### Estacionalidad

- Feria del Libro;
- concursos literarios;
- editoriales/manuscritos;
- regalos/libros;
- lecturas verano/Navidad.

### Eventos

Detectar cuándo un tema gana interés, sin crear páginas solo por trending.

## No hacer

- interpretar 100 como 100 búsquedas;
- comparar términos con volumen extremadamente bajo como precisión estadística;
- cambiar estrategia por pico de 24h.

---

# 6. Preferred Sources

Google publicó guía específica actualizada el 20/08/2026.

Cuando un usuario selecciona un dominio como fuente preferida:

- su contenido es más probable que aparezca en Top Stories para ese usuario;
- puede destacarse con badge `preferred`;
- también puede destacarse en AI Mode/AI Overviews donde esas features estén disponibles.

## Importante

- es una preferencia del usuario;
- no es un ranking boost universal;
- solo dominios/subdominios, no subdirectory;
- el sitio debe aparecer en la herramienta de source preferences.

## Implementación oficial posible

Google ofrece:

- botón JS estándar;
- SDK/custom UI;
- deeplink.

## Propuesta

Antes de tocar runtime:

1. comprobar si `davidportodiaz.com` aparece en la herramienta;
2. si sí, crear un pequeño experimento en Cuaderno;
3. revisar CSP porque el script oficial carga desde infraestructura Google News;
4. respetar performance/privacy;
5. no poner botón en cada página.

### Ubicación candidata

`/cuaderno/`

Copy discreto y humano.

No popup.

---

# 7. Knowledge Panel

No es un producto al que «dar de alta» la entidad.

Google genera panels automáticamente.

## Gate

Buscar la entidad.

Si panel existe y permite claim:

- reclamar;
- verificar mediante métodos disponibles;
- revisar facts;
- proponer corrections con fuentes.

## No hacer

- pagar a servicios que prometen crear Knowledge Panel;
- fabricar Wikipedia;
- llenar Wikidata de promoción;
- crear perfiles vacíos.

---

# 8. Google Books

El Google Books Partner Program permite a autores y publishers enviar libros para:

- preview en Google Books;
- descubrimiento mediante Book Search;
- links a comprar/pedir prestado/descargar cuando corresponda;
- venta en Google Play Books si se configura y el territorio es compatible.

## Oportunidad real

Los libros podrían beneficiarse de una ficha/preview correcta en Google Books.

## Gate de derechos

No subir archivos porque «ayuda al SEO» si:

- la editorial gestiona derechos digitales;
- contrato no lo permite;
- ya existe gestión editorial/distribuidor;
- crearía duplicados/conflictos.

### Samuel

Consultar primero:

- contrato;
- Libros Indie;
- si ya existe Google Books entry/partner feed.

### Manecillas

Coordinar con Monza.

No tomar decisión unilateral de ebook/preview.

---

# 9. Google Play Books

Partner Center está abierto a autores/publishers elegibles.

Funciones:

- bibliographic metadata;
- PDF/EPUB;
- preview;
- Google Play sale;
- pricing;
- territories;
- reports.

## SEO vs distribución

Esto es principalmente **distribución comercial/discovery de libros**, no una táctica de ranking de davidportodiaz.com.

Evaluar si encaja en la estrategia editorial del libro.

No hacerlo solo para obtener un enlace Google.

---

# 10. Google Books metadata parity

Si se participa:

Campos deben coincidir con autoridad editorial:

- title;
- subtitle si existe;
- ISBN;
- author;
- publisher;
- publication date;
- language;
- description;
- cover;
- page count/formats.

No introducir un description SEO que contradiga la editorial.

---

# 11. Google Images

No requiere cuenta/product setup.

Prioridad:

- portadas;
- retrato;
- eventos;
- imágenes editoriales propias.

Medición:

Search Console `Search type: Image` cuando haya datos.

No confundir impressions Image con Web.

---

# 12. Discover

No hay alta.

Contenido indexado y conforme es automáticamente elegible.

No existe una cuenta Discover que configurar.

Search Console puede mostrar Performance Discover si alcanza umbral/datos.

No producir clickbait.

---

# 13. Google News

Desde 2025, páginas de publicación son generadas automáticamente.

No dedicar trabajo a tutoriales de:

- «enviar RSS a Publisher Center para que Google te acepte»

como vía de inclusión general.

## Cuándo importa

Si Cuaderno desarrolla piezas de actualidad frecuentes, transparentes y originales.

No convertirlo en periódico artificial.

---

# 14. YouTube

No crear canal vacío solo para tener `sameAs`.

## Evaluar cuando exista pipeline

Tipos:

- entrevistas;
- lecturas;
- worldbuilding;
- proceso;
- eventos;
- explicación de herramientas.

## Beneficios posibles

- audience;
- Search/Video discovery;
- embeds;
- entidad;
- material multimodal.

No tratar subscriptions/views como factor de ranking web directo.

---

# 15. Google Business Profile

Google exige que el negocio:

- tenga una ubicación física que los clientes puedan visitar; o
- viaje hasta los clientes.

## Estado del proyecto

David es un autor con web personal. La residencia en Madrid no justifica por sí misma un GBP.

No:

- publicar dirección privada;
- crear `David Porto Díaz Escritor Madrid` como keyword name;
- elegir categoría ficticia;
- usar coworking/virtual office sin elegibilidad.

## Gate futuro

Solo si existe una actividad real elegible, por ejemplo un negocio de servicios con atención según políticas.

Entonces investigar de nuevo.

---

# 16. Local SEO para eventos sin GBP

Sí podemos aparecer en búsquedas locales mediante:

- Event pages;
- organizer pages;
- local media;
- venue/librería;
- event schema;
- content.

No se necesita un GBP del autor para cada firma.

---

# 17. Merchant Center / Shopping

No encaja mientras davidportodiaz.com:

- no sea merchant directo real de catálogo;
- no controle checkout/price/availability/shipping.

Retailer externo vende libros; eso no convierte al sitio oficial en merchant.

No crear feed de productos falso.

---

# 18. Product structured data

Misma regla.

Book factual != Product Offer.

Solo si en el futuro la web vende directamente y cumple políticas se reevalúa:

- Product;
- Offer;
- Merchant Center;
- shipping/returns;
- Merchant listings.

---

# 19. Google Ads

Separado del ranking orgánico.

Ads puede servir a objetivos comerciales/promoción, pero:

- pagar no compra posiciones orgánicas;
- Google Ads data puede informar términos/comercial intent si se usa;
- no justificar gasto como «mejorar SEO».

No forma parte del backlog orgánico salvo coordinación de landing/measurement.

---

# 20. Keyword Planner

Está dentro del ecosistema Ads.

Puede dar estimaciones de keywords, pero:

- datos están orientados a publicidad;
- rangos pueden ser amplios;
- no sustituye Search Console.

No abrir campañas solo para acceder a SEO data sin valorar condiciones/coste.

---

# 21. Google Analytics

El proyecto usa una estrategia analytics propia con GoatCounter/Metricool y privacidad definida.

No instalar GA4 «porque Google premia usar Google Analytics».

No existe base para esa afirmación.

Evaluar GA4 solo si hay una necesidad de medición que compense:

- privacy;
- cookies/consent cuando aplique;
- JS;
- mantenimiento.

---

# 22. Looker Studio

Puede ser útil para reporting con Search Console/BigQuery.

No es necesario si ya existe dashboard adecuado.

Uso:

- visualization;
- stakeholder reporting.

No ranking effect.

---

# 23. Search Console API

Ya documentada.

Automatizar read-only:

- search analytics;
- sitemap;
- inspection priority URLs.

No usar como auto-editor de titles/content.

---

# 24. Indexing API

No para este contenido.

Solo JobPosting y BroadcastEvent in VideoObject según Google.

Nuestros `Event` normales no se convierten en BroadcastEvent por conveniencia.

---

# 25. Rich Results Test

Herramienta útil de validación.

No tiene que estar automatizada por scraping.

Usar manualmente en releases de:

- Book;
- Event;
- ProfilePage;
- Article;
- SoftwareApplication changes.

---

# 26. PageSpeed Insights

Útil para:

- field CrUX cuando existe;
- lab diagnostics.

No perseguir score móvil exacto como factor de ranking.

Cruzar con Search Console CWV.

---

# 27. Lighthouse

Ya integrado en CI.

No hace falta duplicarlo con herramientas Google externas.

---

# 28. Search Status Dashboard

Añadir a operación.

Antes de diagnosticar una caída:

- ranking update;
- serving issue;
- indexing issue.

Al corte 27/08 no había incidentes activos recuperados en la investigación.

---

# 29. Search Central updates RSS

Google publica feed de cambios de documentación.

Útil para mantener este plan vivo.

No hacer polling cada hora; revisión mensual/trimestral o automation diaria resumida si se desea en otro sistema.

---

# 30. Google Alerts

Puede utilizarse para monitorización de menciones si el servicio sigue siendo útil para el usuario.

No se presenta como SEO feature de ranking.

Queries:

- nombre autor;
- títulos;
- ISBN.

Complementar, no sustituir monitoring más completo.

---

# 31. Google Scholar

No target.

ORCID no convierte la producción literaria en académica.

No subir contenido irrelevante con formato paper para aparecer en Scholar.

---

# 32. AMP

No implementar por SEO.

Google no exige AMP para ranking/Top Stories.

La web responsive actual es la dirección correcta.

---

# 33. Web Stories

Google ha reducido/retirado varias superficies de Web Stories a lo largo del tiempo.

No invertir sin una necesidad editorial específica y documentación actual que lo justifique.

No crear Stories solo por «más superficie Google».

---

# 34. Shopping/commerce AI

Las capacidades generativas/comerciales se tratan en `docs/ai-discoverability/`.

Mismo gate:

no somos merchant real → no fake feed/offers.

---

# 35. Maps

Eventos pueden aparecer en ecosistema local a través del venue/organizador.

No intentar añadir «lugares» ficticios de Noveris o dirección privada del autor.

---

# 36. Product priorities

## Hacer ahora

- Search Console;
- Trends para research;
- comprobar Knowledge Panel;
- comprobar Preferred Sources eligibility;
- verificar Google Books presence/rights con editoriales;
- Images/Discover optimización normal.

## Cuando haya caso

- YouTube;
- Google Play Books;
- News maturity;
- event individual pages.

## No ahora

- GBP;
- Merchant Center;
- Shopping feed;
- AMP;
- Indexing API;
- Scholar.

---

# 37. Acceptance criteria

- ningún producto se activa por superstición SEO;
- Search Console sigue como autoridad de medición;
- Trends se interpreta como interés relativo;
- Preferred Sources solo tras eligibility;
- Google Books solo con derechos/editorial alignment;
- GBP no se crea falsamente;
- Merchant/Shopping solo si hay venta directa real;
- Ads no se vende como organic ranking;
- News/Discover no se tratan como formularios de alta;
- YouTube solo con estrategia;
- APIs se usan dentro de su scope real.
