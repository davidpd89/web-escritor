# 01 — Plan maestro de Google Search Console para davidportodiaz.com

**Corte:** 2026-08-27  
**Objetivo:** inventariar las funciones vigentes de Google Search Console y convertir cada una en una acción concreta para esta web.  
**Criterio de investigación:** documentación oficial de Google como fuente primaria. Las funciones nuevas se marcan como `ROLLOUT` o `EXPERIMENTAL` cuando Google no garantiza disponibilidad para todas las propiedades.

---

## 1. Modelo de propiedades

### 1.1 Propiedad principal: dominio

**Recomendación:** usar `davidportodiaz.com` como propiedad operativa principal de tipo **Domain property**, verificada mediante DNS.

Razones:

- cubre HTTP/HTTPS y subdominios;
- habilita informes que requieren nivel raíz, como robots.txt y Crawl Stats;
- evita fragmentar el histórico;
- permite que el análisis principal represente la entidad web completa;
- los filtros de Rendimiento y BigQuery ya permiten segmentar carpetas sin crear propiedades adicionales.

### 1.2 Propiedades URL-prefix

Crear solo si hay un caso operativo que no puede resolverse con filtros. No crear una propiedad por `/cuaderno/`, `/herramientas/`, etc. por costumbre.

Motivo adicional: el filtro nativo **de marca / sin marca** no está disponible en subpropiedades.

### 1.3 Propiedades de plataforma — NUEVO 2026 · ROLLOUT

Google está desplegando propiedades para cuentas/canales de:

- Instagram;
- TikTok;
- X;
- YouTube.

Estas propiedades miden cómo aparece el contenido de esas plataformas en **Google**, no las vistas nativas dentro de Instagram/TikTok/X/YouTube.

#### Acción para este proyecto

El contrato público actual del repositorio confirma:

- Instagram: `@davidportodiaz`;
- TikTok: `@davidportoescritor`.

Si el selector «Añadir propiedad» ofrece propiedades de plataforma:

1. añadir Instagram;
2. completar la verificación/conexión;
3. añadir TikTok;
4. comprobar que la conexión permanece verificada;
5. revisar sus informes de Rendimiento/Estadísticas de forma independiente;
6. no añadir X o YouTube hasta que exista una cuenta/canal canónico confirmado en el proyecto.

**Valor:** permite medir si un vídeo/post social está generando descubrimiento desde Google aunque no lleve inmediatamente al dominio.

Fuente: SC-PLATFORM.

---

## 2. Usuarios, propietarios y permisos

Search Console distingue:

- propietario verificado;
- propietario delegado;
- usuario con acceso total;
- usuario restringido;
- asociaciones con servicios externos.

### Política propuesta

- mantener al menos un **propietario verificado** bajo una cuenta controlada directamente;
- si se añade una segunda cuenta de recuperación, que también esté controlada y documentada;
- Claude/agencias/colaboradores: dar solo el nivel que necesiten;
- revisar trimestralmente usuarios y permisos;
- retirar cuentas que ya no participen;
- no compartir credenciales: añadir usuarios individualmente.

### Checklist trimestral

- [ ] ¿Los propietarios son reconocibles y necesarios?
- [ ] ¿Sigue vigente el token DNS/HTML de verificación?
- [ ] ¿Hay propietarios delegados antiguos?
- [ ] ¿Alguna cuenta externa tiene acceso total sin necesitarlo?
- [ ] ¿Las asociaciones siguen justificadas?

Fuente: SC-USERS.

---

## 3. Resumen y Recomendaciones

El panel Overview es el triage de entrada.

### Qué mirar

- cambios fuertes de rendimiento;
- indexación;
- mejoras/rich results;
- acciones manuales;
- seguridad;
- **Recommendations**.

### Recommendations

Google puede mostrar tres familias:

- **Issues:** algo que corregir;
- **Opportunities:** oportunidad de tráfico;
- **Configuration:** mejora de configuración.

No son órdenes. Pueden cambiar o caducar.

### Regla del proyecto

Toda recomendación se clasifica antes de ejecutar:

1. evidencia;
2. URLs afectadas;
3. impacto esperado;
4. compatibilidad con arquitectura/canon editorial;
5. riesgo;
6. cambio propuesto;
7. forma de medir después.

No modificar producción solo porque Search Console muestre una tarjeta.

Fuente: SC-RECOMMENDATIONS.

---

## 4. Anotaciones — MUY ALTO VALOR

Search Console dispone de anotaciones del sistema y personalizadas.

### Límites actuales relevantes

- compartidas a nivel de propiedad;
- propietarios y usuarios completos pueden crearlas/eliminarlas;
- usuarios restringidos solo las ven;
- máximo 200 anotaciones por propiedad;
- texto de hasta 120 caracteres;
- las personalizadas con más de 500 días se eliminan;
- no se muestran en modo comparación ni en vista de 24 h;
- no se editan: si hay un error, se elimina y se crea otra.

### Convención propuesta

Formato corto:

`TIPO · alcance · cambio`

Ejemplos:

- `RELEASE · Manecillas · lanzamiento editorial`
- `SEO · Cuaderno · títulos/metas cluster portales`
- `NAV · global · nueva navegación V1`
- `TECH · global · cambio CDN/cache`
- `SCHEMA · eventos · Event JSON-LD`
- `INDEX · sitemap · regeneración completa`
- `CONTENT · editoriales · +10 fichas verificadas`
- `INCIDENT · hosting · 5xx 18 min`

### Obligatorio anotar

- lanzamiento de libro;
- publicación de un cluster grande;
- cambio de navegación;
- cambio de dominio/URL/canónicas;
- cambio de sitemap/robots;
- cambio de plantilla que afecte títulos, schema o enlaces internos;
- migración/performance importante;
- incidente de disponibilidad;
- corrección de indexación a escala.

Fuente: SC-ANNOTATIONS.

---

## 5. Rendimiento de resultados de Búsqueda

Es el informe central para decisiones editoriales.

### Métricas

- clics;
- impresiones;
- CTR;
- posición media.

### Dimensiones

- consultas;
- páginas;
- países;
- dispositivos;
- apariencia en búsqueda;
- fechas.

### Tipos de búsqueda

Según disponibilidad de datos:

- web;
- imágenes;
- vídeo;
- noticias.

### Regla de lectura

1. **Impresiones** = demanda/visibilidad potencial.
2. **Clics** = tráfico captado.
3. **CTR** = capacidad de captación dentro del contexto de SERP/posición/intención.
4. **Posición** = señal diagnóstica, no objetivo aislado.

No perseguir «posición media» sin saber para qué consultas y páginas se está agregando.

Fuente: SC-PERFORMANCE.

---

## 6. Marca vs. sin marca — ALTO VALOR

Google dispone de filtro nativo de consultas **de marca / sin marca** desde el 11 de marzo de 2025.

Características:

- funciona en web, imagen, vídeo y noticias;
- clasificación informativa mediante sistemas de Google, no señal de ranking;
- puede equivocarse;
- no aparece en subpropiedades;
- puede no aparecer si el sitio tiene pocas impresiones.

### KPI estratégico

Para una web de autor, separar:

- **marca:** ya conocen a David/las obras/entidades;
- **sin marca:** Google nos está descubriendo ante gente que busca un tema, género, recurso o problema.

El crecimiento sostenible debe buscar especialmente aumento de **clics e impresiones sin marca** sin perder demanda de marca.

### Qué revisar cada semana

- variación de clics genéricos;
- páginas que captan nuevas consultas genéricas;
- consultas de alto volumen relativo con baja respuesta;
- si herramientas/directorios/Cuaderno están ampliando el universo no-branded;
- consultas que Google clasifica erróneamente y que conviene interpretar manualmente.

Fuentes: SC-BRAND, SC-PERFORMANCE-DIMENSIONS.

---

## 7. Vista de 24 horas

Search Console ofrece una vista reciente con datos horarios/preliminares cuando está disponible.

### Usarla para

- lanzamiento de Manecillas;
- publicación de un artículo con interés temporal;
- aparición en prensa;
- cambio técnico importante;
- detectar rápidamente una caída abrupta.

### No usarla para

- declarar tendencia SEO estable;
- comparar periodos largos;
- evaluar una reescritura pocas horas después;
- sustituir datos finalizados.

Las anotaciones personalizadas no aparecen en esta vista; registrar el evento igualmente para el histórico normal.

---

## 8. Segmentación por familias de páginas

No crear propiedades separadas. Utilizar filtro Page / regex o BigQuery.

### Obras

Regex conceptual:

`^https://davidportodiaz\.com/(libros/|las-manecillas-del-recuerdo/|fragmento/|clubes-de-lectura/|universo/)`

Analizar:

- título de obra;
- autor + título;
- términos de género;
- fragmentos;
- club de lectura;
- Noveris/magia/portal fantasy.

### Cuaderno

`^https://davidportodiaz\.com/cuaderno/`

Analizar:

- qué temas crean demanda sostenida;
- qué clusters se refuerzan entre sí;
- artículos que reciben muchas impresiones pero pocos clics;
- artículos que empiezan a ganar consultas distintas de la consulta objetivo original.

### Herramientas

`^https://davidportodiaz\.com/herramientas/`

Analizar:

- utilidad por herramienta;
- consultas problema/solución;
- herramientas con muchas impresiones y poca activación por snippet débil;
- canibalización entre herramientas parecidas.

### Recursos para escritores

`^https://davidportodiaz\.com/(herramientas|editoriales|convocatorias-escritores|metodologia-editorial|recursos)/`

Objetivo: medir el motor evergreen que puede atraer escritores y backlinks.

### Recomendaciones

`^https://davidportodiaz\.com/recomendaciones/`

Objetivo: demanda de lectura y long-tail temática.

### Entidad/autor/prensa

Filtrar las URLs concretas:

- `/`;
- `/autor.html`;
- `/prensa.html`;
- `/premios.html`;
- `/eventos.html`;
- `/ferias.html`;
- `/ai/`.

Objetivo: identidad, reputación, búsquedas de autor, premios, eventos y apariciones.

---

## 9. Playbook CTR

### No usar «CTR bajo» sin contexto

Una query informativa en posición 8 y una branded en posición 1 no tienen el mismo CTR esperable.

### Proceso

1. elegir periodo 28 días;
2. filtrar territorio;
3. ordenar por impresiones;
4. identificar queries/páginas con volumen suficiente para ser relevantes;
5. revisar posición y SERP real;
6. revisar intención;
7. comprobar si Google ha reescrito title/snippet de forma visible;
8. decidir si mejorar:
   - title;
   - meta description;
   - H1/lead;
   - foco del contenido;
   - fecha visible;
   - imagen;
   - datos estructurados compatibles;
9. anotar el cambio;
10. medir 28 días vs. periodo comparable.

### Priorizar

- posiciones aproximadamente competitivas (por ejemplo 2–10) + muchas impresiones;
- páginas estratégicas;
- consultas donde el snippet promete algo distinto de lo que busca el usuario;
- consultas genéricas que amplían audiencia.

No cambiar títulos de páginas que ya funcionan solo por optimización compulsiva.

---

## 10. Estadísticas / Search Console Insights — ROLLOUT

El informe Estadísticas integra una lectura editorial simplificada de los datos.

Puede mostrar, según disponibilidad:

- clics e impresiones;
- contenido principal;
- contenido con crecimiento/descenso;
- consultas principales;
- consultas con crecimiento/descenso;
- países;
- tráfico de marca/genérico;
- fuentes adicionales como imágenes, vídeo, noticias o Discover;
- agrupaciones de consultas en propiedades con suficiente volumen.

### Uso para esta web

Semanalmente, usarlo como detector de preguntas:

- «¿por qué este artículo sube?»;
- «¿qué herramienta acaba de ganar tracción?»;
- «¿qué búsqueda genérica nueva nos descubre?»;
- «¿qué contenido antiguo vuelve a crecer?».

Después pasar al informe Rendimiento para análisis exacto.

### Social channel insights — EXPERIMENTAL

Google está experimentando con insights de canales sociales que puede identificar automáticamente (por ejemplo YouTube/Instagram/TikTok). No confundir con las nuevas **propiedades de plataforma**.

- social insights: descubrimiento/agrupación automática dentro de Insights;
- platform properties: propiedad verificable independiente de la cuenta/canal.

No asumir que la cuenta permite seleccionar manualmente canales en el módulo experimental.

Fuente: SC-INSIGHTS.

---

## 11. IA generativa en Google Search — NUEVO 2026 · ROLLOUT

### 11.1 Informe de rendimiento de IA generativa (Search)

Google está desplegando un informe específico para:

- AI Overviews / Vistas creadas con IA;
- AI Mode / Modo IA.

Actualmente se centra en **impresiones** y permite analizar, entre otros, página, país, dispositivo y fecha.

No todas las propiedades lo ven y puede requerir suficientes impresiones.

### Acciones

Si aparece:

1. registrar fecha de primera disponibilidad;
2. exportar baseline;
3. identificar páginas con impresiones generativas;
4. agruparlas por territorio;
5. comparar qué páginas Google considera útiles para respuestas generativas;
6. reforzar contenido original, claro, verificable y bien enlazado;
7. no «escribir para IA» a costa del lector;
8. no confundir impresiones con visitas.

### 11.2 Informe de IA generativa de Discover

Google documenta un informe separado para funciones generativas en Discover, en rollout.

Mantenerlo separado del informe normal de Search porque fuentes y anomalías pueden diferir.

### 11.3 Search Labs

Los experimentos de Search Labs no se incluyen en estos informes.

Fuente: SC-GENAI-REPORT.

---

## 12. Control de IA generativa — NUEVO 2026 · ROLLOUT

Ruta documentada por Google:

`Settings > Search generative AI`

Permite decidir inclusión en:

- AI Overviews;
- AI Mode;
- funciones generativas de Discover.

### Decisión para davidportodiaz.com

**Mantener incluido** mientras la estrategia sea maximizar descubrimiento y visibilidad.

No confundir con `Google-Extended`:

- el control de Search Console gobierna participación en funciones generativas de Search/Discover;
- Google-Extended se relaciona con usos de contenido para determinados sistemas de IA y no es un control de ranking de Search.

No excluir por miedo genérico. Excluir solo por decisión editorial/legal consciente y documentada, sabiendo que se pierden enlaces/impresiones en esas funciones.

Fuente: SC-GENAI-CONTROL.

---

## 13. Anomalías de datos — OBLIGATORIO ANTES DE DIAGNOSTICAR CAÍDAS

A 27/08/2026 Google registra anomalías relevantes recientes:

- **13 de agosto de 2026:** problema de logging en Discover/IA generativa de Discover, con caída reportada de clics/impresiones;
- **13–17 de agosto de 2026:** problema de logging en IA generativa de Search, con menos impresiones reportadas.

Estos son problemas de **registro de datos**, no necesariamente caídas reales de visibilidad.

### Protocolo

Antes de abrir una incidencia SEO por caída:

1. mirar anotaciones de sistema en el gráfico;
2. consultar la página oficial de anomalías de Search Console;
3. comprobar si afecta al informe exacto;
4. comparar Search web vs. Discover vs. GenAI;
5. solo después investigar cambios propios.

Fuente: SC-ANOMALIES.

---

## 14. Sitemaps

El sitio ya declara en `robots.txt`:

`Sitemap: https://davidportodiaz.com/sitemap.xml`

### Qué hacer en Search Console

Enviar además explícitamente el sitemap raíz en el informe **Sitemaps**.

Beneficios:

- saber cuándo Google lo leyó;
- ver errores;
- entrar en Indexación filtrada por sitemap;
- tener una referencia operativa, no solo discovery por robots.

### Política de sitemaps

- un sitemap debe contener URLs canónicas, indexables y que realmente queremos en Search;
- `lastmod` debe representar cambio significativo, no «hoy» por regenerar;
- no introducir `noindex`, staging o duplicadas;
- no enviar dos sitemaps con las mismas URLs solo para segmentación.

El repo también conserva `editoriales-sitemap.xml`, mientras el sitemap raíz ya contiene las URLs de Editoriales. Para el tamaño actual, mantener **un sitemap raíz como autoridad operativa** es más limpio. Si en el futuro se segmenta, hacerlo mediante sitemaps **no solapados** o sitemap index y documentar el motivo.

### API

La Search Console API permite enviar/consultar/eliminar sitemaps programáticamente. Solo automatizar cuando exista un flujo de generación estable; no hacer ping compulsivo tras cada cambio menor.

Fuentes: SC-SITEMAPS, SC-API.

---

## 15. Indexación de páginas

No perseguir «todo verde». El objetivo es:

- páginas importantes indexadas;
- páginas que no deben indexarse excluidas por el motivo previsto;
- cero exclusiones inesperadas persistentes.

### Clasificación propuesta

#### Esperado indexado

- home;
- Autor;
- Obras y fichas de libros;
- Cuaderno + artículos publicables;
- Herramientas públicas;
- Editoriales publicables;
- Convocatorias;
- Recomendaciones;
- Prensa/Premios/Eventos;
- recursos indexables.

#### Esperado no indexado

Según contrato actual del repositorio:

- páginas legales con `noindex`;
- staging/gated;
- páginas deliberadamente noindex;
- duplicadas/canónicas secundarias que el sistema cree intencionadamente.

### Motivos a investigar con prioridad

- `Crawled - currently not indexed` en URL estratégica;
- `Discovered - currently not indexed` persistente en contenido prioritario;
- `Duplicate, Google chose different canonical` cuando no era lo esperado;
- `Blocked by robots.txt` en página que debería indexarse;
- `Excluded by noindex` en página que debería indexarse;
- soft 404 en contenido real;
- 5xx;
- redirect inesperado.

### Validar corrección

Usar «Validate fix» solo tras haber arreglado la causa a escala. No iniciar validaciones repetidas sin cambio.

Fuente: SC-PAGE-INDEXING.

---

## 16. URL Inspection — interfaz

Para una URL individual, URL Inspection permite ver:

- estado de la versión indexada;
- discovery/crawl;
- indexabilidad;
- canonical declarada y elegida por Google;
- datos estructurados detectados;
- vídeo/otros elementos cuando corresponda;
- prueba en vivo;
- solicitud de indexación.

### Lista de inspección prioritaria

Tras cambios grandes, comprobar al menos:

1. `/`;
2. `/autor.html`;
3. `/libros/`;
4. `/las-manecillas-del-recuerdo/`;
5. `/libros/samuel-entre-mundos/`;
6. `/cuaderno/`;
7. artículo estratégico nuevo;
8. `/herramientas/`;
9. herramienta estratégica nueva;
10. `/editoriales/`;
11. `/convocatorias-escritores/`;
12. `/recomendaciones/`;
13. `/prensa.html`;
14. `/premios.html`.

### Request indexing

Usarlo para:

- página nueva prioritaria;
- corrección importante en página clave;
- recuperación de bloqueo/noindex accidental.

No usarlo como ritual diario ni como sustituto de sitemap/enlazado interno.

Fuente: SC-URL-INSPECTION.

---

## 17. URL Inspection API

La API permite inspeccionar el estado que Google tiene de una URL.

Importante:

- informa sobre la **versión indexada**;
- no ejecuta la prueba live de la interfaz;
- cuota oficial: 2.000 inspecciones/día por sitio y 600/minuto por sitio.

### Uso propuesto

Mantener un inventario pequeño de URLs de prioridad P0/P1 y ejecutar auditoría periódica para detectar:

- deja de estar indexada;
- canonical inesperada;
- bloqueo/robots;
- estado de cobertura nuevo;
- datos estructurados que dejan de detectarse.

No inspeccionar cada URL del sitio cada día: no aporta valor proporcional.

Fuentes: SC-URL-API, SC-API-QUOTAS.

---

## 18. Core Web Vitals

Search Console usa datos de campo de usuarios reales y agrupa URLs similares.

Métricas:

- LCP;
- INP;
- CLS.

Estados:

- Good;
- Needs improvement;
- Poor.

### Relación con el repositorio

El repositorio ya utiliza QA/Lighthouse. Eso es **lab**; GSC CWV es **field**.

Ambos deben convivir:

- Lighthouse/CI detecta regresiones antes de desplegar;
- Search Console confirma experiencia real agregada después.

### Priorización

1. grupos `Poor`;
2. grupos con URLs de alto tráfico/alta importancia;
3. causa común en plantilla;
4. fix técnico;
5. esperar datos de campo;
6. validar corrección.

Fuente: SC-CWV.

---

## 19. HTTPS

Objetivo: **0 URLs HTTP indexadas**.

El informe HTTPS ayuda a detectar:

- versiones HTTP todavía indexadas;
- canónicas HTTP;
- problemas de certificado;
- problemas de disponibilidad;
- sitemap/canonical inconsistentes.

El sitio ya opera en HTTPS; Search Console debe confirmar que Google también lo entiende así.

Fuente: SC-HTTPS.

---

## 20. Crawl Stats

Informe avanzado disponible en propiedades raíz.

Incluye:

- solicitudes de crawl;
- tamaño descargado;
- tiempo medio de respuesta;
- estado del host;
- respuesta HTTP;
- tipo de fichero;
- propósito del rastreo (discovery/refresh);
- tipo de Googlebot;
- ejemplos de URLs.

### Para un sitio de este tamaño

No optimizar «crawl budget» de forma obsesiva. Google indica que sitios pequeños normalmente no necesitan gestionar ese nivel.

Sí usarlo para:

- detectar 5xx;
- detectar host/DNS problemático;
- comprobar impacto de cambio de CDN/hosting;
- descubrir loops/redirects/URLs basura rastreadas;
- diagnosticar caída de crawl tras incidente.

Fuente: SC-CRAWL-STATS.

---

## 21. robots.txt report

El informe muestra los robots detectados por Google en los principales hosts, última lectura, errores/avisos y permite pedir recrawl en emergencias.

### Estado actual del repo

El `robots.txt`:

- permite rastreo general;
- no bloquea Google Search;
- declara el sitemap raíz;
- contiene políticas específicas para otros crawlers/controles IA.

### Uso

- revisar tras cualquier modificación de robots;
- solicitar recrawl solo si se ha corregido un bloqueo grave o un error de lectura;
- recordar que robots controla **rastreo**, no desindexación.

Fuente: SC-ROBOTS.

---

## 22. Resultados enriquecidos y datos estructurados

Search Console crea informes por tipo de rich result **cuando detecta un tipo compatible** en la propiedad.

### Tipos relevantes para este proyecto según la documentación actual de Google

- `Article` / `BlogPosting` para Cuaderno;
- `BreadcrumbList`;
- `Event` para eventos reales;
- `Organization`/entidad cuando proceda;
- `ProfilePage` cuando encaje semánticamente;
- `Product` solo si el caso real cumple requisitos;
- metadatos de imágenes;
- otros que Google detecte y sean semánticamente válidos.

### Libros y Product

No convertir una ficha de libro automáticamente en Merchant Listing.

Google distingue:

- Product snippet: página donde el producto puede describirse aunque no se compre directamente;
- Merchant listing: páginas donde el cliente puede comprar directamente al merchant.

Actualmente el proyecto no debe inventar `Offer`, disponibilidad o venta directa de Manecillas sin una fuente comercial verificada. Search Console no justifica romper ese contrato.

### FAQ — RETIRADO

Google dejó de mostrar FAQ rich results desde el **7 de mayo de 2026** y documenta la retirada de la apariencia FAQ de la Search Console API en agosto de 2026.

Consecuencia:

- no invertir tiempo en FAQ schema para obtener un rich result de Google;
- conservar FAQs solo si sirven al lector/semántica, no como táctica SERP.

### Proceso de errores

1. abrir informe del tipo;
2. priorizar errores críticos comunes a plantilla;
3. comprobar ejemplos;
4. Rich Results Test;
5. URL Inspection;
6. corregir;
7. Validate fix.

Fuentes: SC-RICH-RESULTS, GOOGLE-STRUCTURED-GALLERY, GOOGLE-FAQ-RETIREMENT.

---

## 23. Discover

El informe aparece solo si la propiedad alcanza un mínimo de impresiones en Discover.

Dimensiones típicas:

- página;
- país;
- tipo de aparición;
- día.

### Uso para el Cuaderno

Si aparece:

- identificar piezas que entran en Discover;
- estudiar formato, tema, actualidad, imágenes y señales editoriales comunes;
- no clonar contenidos porque «funcionó una vez»;
- distinguir tráfico Discover de Search web.

No hay garantía de aparecer en Discover.

Fuente: SC-DISCOVER.

---

## 24. Google News

El informe de Google News cubre `news.google.com` y apps de Google News.

No confundir con:

- pestaña News dentro de Google Search → se analiza en Rendimiento de Search con `search type = news`.

Para un sitio de autor/Cuaderno puede no aparecer si no hay suficiente tráfico. Si aparece, medirlo por separado.

Fuente: SC-NEWS.

---

## 25. Enlaces externos

El informe Links permite ver:

- páginas más enlazadas;
- sitios con más enlaces;
- anchor text;
- detalle dominio → página;
- muestras/exportaciones.

Caveats:

- no es un índice completo de backlinks;
- tablas generalmente limitadas a 1.000 filas;
- Google ofrece exportaciones de ejemplos/enlaces recientes de hasta 100.000 filas en algunas vistas.

### Objetivos del proyecto

Comprobar si reciben enlaces las páginas que deberían acumular autoridad:

- Autor;
- Manecillas;
- Samuel;
- Cuaderno evergreen;
- herramientas destacadas;
- directorio de editoriales;
- recursos originales/citables;
- prensa/premios cuando corresponda.

### Oportunidad editorial

Si un artículo/herramienta recibe enlaces externos orgánicos, proteger su URL, mantenerla actualizada y reforzar internal linking hacia los hubs relevantes.

Fuente: SC-LINKS.

---

## 26. Enlaces internos

Search Console muestra qué páginas tienen más enlaces internos según Google.

### Uso

Validar que la arquitectura implementada se refleja en crawl real:

- Obras;
- Manecillas;
- Autor;
- Cuaderno;
- Herramientas;
- recursos estratégicos.

Si una página estratégica casi no recibe enlaces internos, revisar navegación/contextual linking antes de intentar «SEO externo».

No perseguir números absolutos: evaluar jerarquía relativa y rutas de usuario.

Fuente: SC-LINKS.

---

## 27. Acciones manuales

Cualquier acción manual es P0.

### Protocolo

1. no hacer cambios impulsivos;
2. identificar exactamente el tipo y alcance;
3. conservar evidencia;
4. corregir causa completa;
5. auditar plantillas y contenido relacionado;
6. documentar lo modificado;
7. pedir reconsideración solo cuando esté realmente corregido;
8. monitorizar mensajes.

No existe ninguna evidencia en esta PR de que haya una acción manual actual; hay que comprobarla en la cuenta real.

Fuente: SC-MANUAL-ACTIONS.

---

## 28. Problemas de seguridad

Cualquier warning de:

- malware;
- hacking;
- phishing;
- descargas dañinas;
- comportamiento peligroso

es P0 y debe activar respuesta de incidente.

### Integración con el repo

Tras incidente:

- revisar commits/deploy;
- secretos y credenciales;
- Workers/CDN;
- dependencias;
- contenido inyectado;
- URLs generadas;
- logs disponibles;
- limpiar;
- solicitar revisión en Search Console.

Fuente: SC-SECURITY.

---

## 29. Retiradas y SafeSearch

La herramienta Removals permite:

- retirada temporal de URL/prefijo;
- limpiar snippet tras retirar contenido sensible;
- ver solicitudes de contenido obsoleto;
- revisar reportes SafeSearch.

La retirada temporal dura aproximadamente **seis meses / 180 días**.

### Usarla cuando

- aparece información sensible y hay que quitarla de Search rápido;
- una URL publicada por error debe desaparecer mientras se aplica la solución permanente.

### No usarla para

- limpiar 404 corrientes;
- «arreglar» coverage;
- desindexar de forma permanente por sí sola;
- impedir crawl.

Para retirada permanente se necesita 404/410, protección, `noindex` u otra solución real según el caso. Google explícitamente desaconseja usar robots.txt como mecanismo de retirada del índice.

Fuente: SC-REMOVALS.

---

## 30. Asociaciones

Search Console puede asociarse con servicios de Google, entre ellos:

- Google Analytics;
- Google Ads;
- Merchant Center;
- Android/Play;
- Chrome Web Store;
- Vertex AI Agent Builder;
- otros servicios documentados por Google.

### Para este proyecto

#### Google Analytics

Asociar solo si existe/se decide una propiedad GA4 operativa. El sitio actualmente tiene su propio stack de analítica; no añadir GA4 únicamente «porque se puede» sin una decisión de privacidad/medición.

Si se asocia, revisar quién accede a GA porque la asociación comparte datos de Search Console con esa propiedad.

#### Merchant Center

No es prioritario mientras la web no actúe como merchant directo. Si más adelante se vende directamente desde davidportodiaz.com, reevaluar:

- Merchant Center;
- product structured data;
- shipping/returns settings;
- merchant opportunities.

#### Google Ads

Solo si se ejecutan campañas y existe un caso de medición concreto.

Fuente: SC-ASSOCIATIONS.

---

## 31. Achievements

Search Console incluye logros/hitos de rendimiento.

### Uso

- útil como indicador de momentum y comunicación interna;
- no es factor de ranking;
- no sustituye KPI segmentado.

Prioridad baja, pero puede registrarse cuando marque un nuevo máximo relevante de clics orgánicos.

---

## 32. Cambio de dirección

No es una función para el día a día.

Si algún día se migra `davidportodiaz.com` a otro dominio:

- verificar ambas propiedades;
- implementar redirects 301 correctos;
- actualizar canonicals/sitemaps/internal links;
- usar Change of Address;
- monitorizar;
- mantener redirects al menos 180 días y preferiblemente más mientras exista tráfico/señal.

No usar para migraciones de carpetas dentro del mismo dominio.

Fuente: SC-CHANGE-ADDRESS.

---

## 33. Exportación manual

La mayoría de informes se pueden exportar a:

- Google Sheets;
- Excel;
- CSV.

Las exportaciones directas reproducen la vista/report y pueden estar limitadas por lo que muestra el informe; típicamente 1.000 filas de ejemplos en tablas.

### Cuándo usar

- análisis puntual;
- compartir evidencia en una PR;
- baseline antes de cambio grande;
- adjuntar una muestra a un incidente.

### Cuándo no usar

- histórico continuo;
- análisis exhaustivo de queries;
- automatización.

Para eso: API o BigQuery.

Fuente: SC-EXPORT-MANUAL.

---

## 34. BigQuery bulk export — PRIORIDAD ESTRATÉGICA

Search Console puede programar una exportación diaria a BigQuery de los datos de rendimiento disponibles, excepto consultas anonimizadas.

Ventajas:

- volumen superior al UI/API;
- histórico propio acumulativo;
- joins y SQL;
- segmentación exacta;
- dashboards;
- anomalías propias;
- análisis de long-tail;
- conserva datos a partir del momento de activación.

### Acción

Activarlo cuanto antes si se acepta el pequeño coste/operativa potencial de Google Cloud.

La configuración detallada está en `03-AUTOMATIZACION-API-BIGQUERY.md`.

Fuentes: SC-BQ-OVERVIEW, SC-BQ-SETUP.

---

## 35. Search Console API

Servicios documentados:

- Search Analytics;
- Sitemaps;
- Sites/properties;
- URL Inspection.

### Search Analytics

Permite agrupar/filtrar por dimensiones como:

- country;
- device;
- page;
- query;
- searchAppearance;
- date;
- hour (según dataState disponible).

Tipos incluyen, según endpoint/propiedad:

- web;
- image;
- video;
- news;
- discover;
- googleNews.

### Límites importantes

- API Search Analytics: hasta 50.000 filas/día/tipo/propiedad expuestas;
- max 25.000 filas por request con paginación;
- 1.200 QPM por sitio y por usuario;
- 30M QPD / 40k QPM por proyecto;
- URL Inspection: 2.000 QPD y 600 QPM por sitio.

Los detalles de extracción están en el documento de automatización.

Fuentes: SC-API, SC-API-EXPORT, SC-API-QUOTAS.

---

## 36. Datos y limitaciones que hay que recordar

Search Console no es un log exhaustivo de cada búsqueda.

Caveats operativos:

- algunas queries se anonimizan por privacidad;
- UI muestra muestras/filas limitadas en múltiples informes;
- totales y filas visibles pueden no cuadrar por anonimización/agregación;
- Search suele atribuir datos a la URL canónica;
- datos finalizados suelen tener retraso de varios días;
- la vista 24 h es preliminar;
- cambios de metodología/logging de Google pueden crear discontinuidades;
- una ausencia de informe (Discover, rich results, GenAI) puede significar que no hay suficiente señal/acceso, no necesariamente error.

### Regla

Cualquier conclusión importante debe registrar:

- propiedad;
- informe;
- periodo;
- filtros;
- comparación;
- si era dato final/preliminar;
- anomalías conocidas;
- URLs/queries afectadas.

---

## 37. Matriz función → acción

| Función | Prioridad | Acción en davidportodiaz.com |
|---|---:|---|
| Domain property | P0 | confirmar DNS + usar como propiedad principal |
| Users/permissions | P0 | auditoría trimestral y mínimo privilegio |
| Overview | P1 | triage de issues y cambios |
| Recommendations | P1 | evaluar, no obedecer automáticamente |
| Annotations | P0 | marcar todos los cambios SEO/release relevantes |
| Search Performance | P0 | análisis semanal y mensual |
| Brand/non-brand | P0 | KPI de crecimiento de descubrimiento |
| 24h | P1 | lanzamientos/incidentes |
| Insights | P1 | detector semanal de tendencias |
| GenAI Search report | P1 rollout | baseline + páginas con impresiones IA |
| GenAI Discover | P2 rollout | monitorizar aparte |
| GenAI control | P0 rollout | mantener incluido |
| Platform properties | P1 rollout | Instagram + TikTok |
| Sitemaps | P0 | enviar root y monitorizar |
| Page indexing | P0 | expected vs unexpected exclusions |
| URL Inspection UI | P0 | URLs estratégicas y post-release |
| URL Inspection API | P2 | monitor automatizado de prioridades |
| Core Web Vitals | P1 | campo real; cruzar con Lighthouse |
| HTTPS | P1 | 0 HTTP indexed |
| Crawl Stats | P2 | incidentes/hosting/5xx |
| robots report | P1 | revisar tras cambios y errores |
| Rich results | P1 | errores de tipos detectados |
| Discover | P2 condicional | estudiar si aparece |
| Google News | P2 condicional | estudiar si aparece |
| Links external | P1 mensual | autoridad y oportunidades |
| Links internal | P1 mensual | jerarquía real |
| Manual actions | P0 | emergencia |
| Security issues | P0 | emergencia |
| Removals | P0 emergencia | solo retirada urgente |
| Associations | P2 | GA/Ads/Merchant solo con caso real |
| Achievements | P3 | momentum, no KPI |
| Change of Address | P0 migración | solo cambio de dominio |
| Manual export | P2 | evidencia puntual |
| BigQuery export | P0/P1 | activar cuanto antes |
| Search Console API | P1/P2 | automatizar lecturas e inspección |

---

## 38. Definition of Done de la implantación Search Console

No basta con que esta documentación exista. El sistema estará realmente implantado cuando:

- [ ] propiedad Domain verificada y gobernada;
- [ ] sitemap raíz enviado y sin errores;
- [ ] mapa de indexabilidad esperado documentado;
- [ ] URLs prioritarias verificadas con URL Inspection;
- [ ] Search Performance segmentado por territorios;
- [ ] marca/sin marca revisado de forma recurrente;
- [ ] convención de anotaciones en uso;
- [ ] BigQuery bulk export activo o decisión explícita de no activarlo con motivo;
- [ ] monitor API diseñado/implantado si compensa;
- [ ] GenAI control revisado y mantenido incluido si está disponible;
- [ ] GenAI report baseline guardado si está disponible;
- [ ] Instagram/TikTok añadidos como platform properties si la función está disponible;
- [ ] runbook semanal/mensual en uso;
- [ ] permisos/asociaciones auditados;
- [ ] procedimiento de acción manual/seguridad/retirada conocido;
- [ ] cualquier alerta genera issue/PR con evidencia, no cambios ad hoc.