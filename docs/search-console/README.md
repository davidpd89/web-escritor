# Google Search Console — plan maestro 2026 para davidportodiaz.com

**Fecha de corte de la investigación:** 27 de agosto de 2026  
**Sitio:** `https://davidportodiaz.com/`  
**Propósito:** convertir Google Search Console en un sistema continuo de descubrimiento, diagnóstico, priorización editorial y control técnico; no en una pantalla que se mira ocasionalmente.  
**Estado:** documentación operativa. Esta PR no modifica producción, no cambia SEO por sí sola, no configura Google Cloud ni solicita indexaciones.

## Cómo usar esta carpeta

Leer en este orden:

1. [`01-PLAN-MAESTRO.md`](./01-PLAN-MAESTRO.md) — inventario completo de funciones vigentes y qué hacer con cada una en esta web.
2. [`02-RUNBOOK-OPERATIVO.md`](./02-RUNBOOK-OPERATIVO.md) — qué revisar a diario, semanalmente, mensualmente, trimestralmente y después de cada lanzamiento o cambio técnico.
3. [`03-AUTOMATIZACION-API-BIGQUERY.md`](./03-AUTOMATIZACION-API-BIGQUERY.md) — cómo dejar de depender de la interfaz: exportación diaria a BigQuery, Search Console API, URL Inspection API, modelos de datos, alertas y consultas.
4. [`04-FUENTES-Y-ESTADO-2026.md`](./04-FUENTES-Y-ESTADO-2026.md) — fuentes oficiales de Google, funciones en rollout/experimental y anomalías de datos conocidas a la fecha de corte.

## Resumen ejecutivo

Search Console puede aportar bastante más que «ver clics y palabras clave». Para esta web hay seis usos de alto valor:

1. **Descubrimiento editorial:** detectar qué temas, artículos, herramientas, libros y entidades están ganando demanda orgánica; separar búsquedas de marca y genéricas; localizar consultas con impresiones pero baja captación de clics.
2. **Control de indexación:** saber si las páginas que queremos en Google están realmente indexadas y, a la vez, comprobar que legales, staging, beta/noindex o URLs duplicadas quedan fuera por el motivo correcto.
3. **Diagnóstico de calidad técnica real:** Core Web Vitals de usuarios reales, HTTPS, rastreo, robots, canónicas elegidas por Google, errores estructurados, seguridad y acciones manuales.
4. **Descubrimiento en IA de Google:** monitorizar impresiones en AI Overviews/Modo IA y, cuando esté disponible para la propiedad, en IA generativa de Discover. Mantener la inclusión activa mientras el objetivo sea maximizar alcance.
5. **Presencia del autor fuera de la web:** aprovechar las nuevas **propiedades de plataforma** de Search Console para medir cómo aparecen en Google las cuentas sociales del autor. En el repositorio están verificadas como canónicas Instagram y TikTok; esas son las primeras propiedades a añadir si el rollout ya está disponible en la cuenta.
6. **Base de datos SEO propia:** activar cuanto antes la exportación diaria completa de Search Console a BigQuery. Esta es la recomendación estratégica más importante para no perder granularidad histórica y poder construir análisis propios, alertas y comparaciones sin el límite de la interfaz.

## Prioridades

### P0 — hacer primero

- [ ] Confirmar que existe y se usa como propiedad principal una **propiedad de dominio** `davidportodiaz.com`, verificada por DNS.
- [ ] Auditar propietarios/usuarios y conservar al menos un propietario verificado bajo control directo del proyecto; aplicar mínimo privilegio al resto.
- [ ] Enviar explícitamente `https://davidportodiaz.com/sitemap.xml` en el informe Sitemaps aunque ya figure en `robots.txt`, porque el envío explícito da observabilidad del estado y errores.
- [ ] Confirmar que el sitemap raíz es el sitemap operativo canónico. No enviar sitemaps duplicados con las mismas URLs solo para «hacer más SEO».
- [ ] Revisar Indexación de páginas y crear un mapa **esperado vs. inesperado**: URL indexable que falta = problema; URL `noindex`/gated excluida = estado correcto.
- [ ] Inspeccionar manualmente las URLs críticas: home, Autor, Obras, Manecillas, Samuel, Cuaderno, Herramientas, Editoriales, Convocatorias, Recomendaciones, Prensa, Premios y páginas nuevas prioritarias.
- [ ] Activar **exportación diaria en bloque a BigQuery** si se acepta crear un proyecto Google Cloud con facturación. La exportación comienza desde la configuración y no reconstruye automáticamente el pasado anterior.
- [ ] Si aparece el control «IA generativa de la Búsqueda», mantener **incluido** el sitio para AI Overviews, Modo IA y funciones generativas de Discover. El objetivo actual es descubrimiento, no exclusión.
- [ ] Añadir una **anotación personalizada** cada vez que haya un cambio que pueda alterar Search: rediseño, cambio de navegación, nueva obra, lanzamiento, migración, redirects, gran lote de metadatos, cambios de schema, sitemap, robots o contenido.
- [ ] Comprobar Acciones manuales y Problemas de seguridad. Cualquier incidencia aquí es prioridad máxima.

### P1 — máximo aprovechamiento

- [ ] Usar Rendimiento con segmentación por **marca/sin marca**. La métrica estratégica de crecimiento debe ser especialmente el tráfico genérico, porque representa descubrimiento de lectores que todavía no conocen al autor.
- [ ] Construir segmentos por familias de URL: Obras, Cuaderno, Herramientas, Recursos para escritores, Recomendaciones, Autor/Prensa/Entidad.
- [ ] Crear una disciplina semanal de oportunidades CTR: páginas/consultas con impresiones relevantes, posiciones competitivas y CTR inferior al esperable para su contexto.
- [ ] Comparar 7d/7d, 28d/28d y periodos equivalentes; no reaccionar a un solo día sin comprobar anotaciones y anomalías oficiales de datos.
- [ ] Revisar Estadísticas/Insights para contenidos y consultas en tendencia, países, marca/genérico y fuentes adicionales.
- [ ] Si aparece «Rendimiento de IA generativa», monitorizar qué páginas obtienen impresiones en AI Overviews y Modo IA y reforzar aquellas donde ya existe señal de demanda.
- [ ] Si aparece «IA generativa en Discover», monitorizarla por separado y no mezclar sus anomalías con Search web.
- [ ] Añadir propiedades de plataforma de **Instagram** y **TikTok** si Search Console ofrece la función a la cuenta. No crear X/YouTube de forma ficticia: no constan como cuentas canónicas en el estado actual del repositorio.
- [ ] Revisar Core Web Vitals como datos de campo; los tests Lighthouse del repositorio no sustituyen esta señal.
- [ ] Revisar Enlaces para comprobar autoridad externa y jerarquía interna real.
- [ ] Monitorizar informes de resultados enriquecidos solo para tipos que Google detecte; no asumir que ausencia de un informe significa schema inválido.

### P2 — automatización y madurez

- [ ] Crear un proyecto de lectura automatizada de Search Console API con OAuth/service account según el modelo de acceso elegido.
- [ ] Extraer diariamente Search Analytics con retraso operativo de 2–3 días para datos finalizados; usar BigQuery como autoridad de largo plazo si está habilitado.
- [ ] Usar URL Inspection API para una lista pequeña de URLs prioritarias y detectar cambios de indexación/canónica; la API inspecciona la versión indexada y no sustituye la prueba en vivo de la interfaz.
- [ ] Diseñar un dashboard propio por territorios editoriales y alertas de cambio material.
- [ ] Auditar trimestralmente usuarios, asociaciones, exportación BigQuery, propiedades sociales y configuración de IA generativa.

## Arquitectura de medición recomendada

### Territorios

La web no debe evaluarse como una sola bolsa de URLs. Search Console debe analizarse al menos en estos territorios:

| Territorio | Ejemplos | Qué queremos aprender |
|---|---|---|
| Entidad/autor | `/`, `/autor.html`, `/prensa.html`, `/premios.html`, `/eventos.html`, `/ai/` | Si Google entiende y encuentra al autor y su actualidad |
| Obras | `/libros/`, `/las-manecillas-del-recuerdo/`, `/libros/samuel-entre-mundos/`, fragmentos, clubes, Noveris | Demanda por títulos, intención de lectura/compra y descubrimiento por género |
| Cuaderno | `/cuaderno/` | Qué contenidos editoriales construyen tráfico y autoridad temática |
| Herramientas | `/herramientas/` | Qué utilidades captan demanda evergreen de escritores |
| Directorios/recursos | `/editoriales/`, `/convocatorias-escritores/`, `/metodologia-editorial/`, `/recursos/` | Qué recursos generan búsquedas genéricas y enlaces naturales |
| Recomendaciones | `/recomendaciones/` | Descubrimiento por intención de lectura y temas relacionados |

### KPIs que sí deben guiar decisiones

- clics orgánicos y su tendencia;
- impresiones y tendencia de demanda;
- consultas de marca vs. genéricas;
- páginas que ganan/pierden clics e impresiones;
- CTR contextual, nunca aislado de consulta/posición/SERP;
- páginas prioritarias indexadas;
- exclusiones esperadas vs. inesperadas;
- canónica declarada vs. canónica elegida por Google en URLs críticas;
- porcentaje/grupos de URLs con Core Web Vitals `Good` frente a `Poor`;
- HTTPS sin URLs HTTP indexadas;
- 5xx/host failures en rastreo;
- errores de datos estructurados que afectan tipos relevantes;
- impresiones en IA generativa, si el informe está disponible;
- visibilidad en Google de Instagram/TikTok, si las propiedades de plataforma están disponibles;
- enlaces externos a Autor, Obras y activos editoriales estratégicos;
- distribución de enlaces internos hacia los hubs prioritarios.

## Lo que NO debe hacerse

- No intentar «indexar el 100 % de las URLs». Algunas deben quedar fuera por diseño.
- No usar `robots.txt` como mecanismo de `noindex`.
- No solicitar indexación repetidamente como táctica de posicionamiento.
- No usar Retiradas para limpiar 404 normales; la herramienta es para retiradas urgentes y temporales.
- No tomar la posición media como KPI principal.
- No interpretar un descenso de un día sin revisar anomalías de datos de Google.
- No crear subpropiedades innecesarias si los filtros/BigQuery ya segmentan las carpetas; algunas funciones nuevas, como marca/sin marca, no están disponibles en subpropiedades.
- No introducir `Product`/Merchant Listing u ofertas ficticias para libros que no se venden directamente en la web.
- No perseguir resultados enriquecidos FAQ: Google dejó de mostrar los FAQ rich results el 7 de mayo de 2026 y está retirando esa apariencia de la API en agosto de 2026.
- No desautorizar enlaces automáticamente por parecer spam; el informe de enlaces es una muestra y Google ya ignora gran cantidad de spam conocido. Escalar solo con evidencia de riesgo real o acción manual.
- No desactivar la inclusión en IA generativa mientras la estrategia sea maximizar descubrimiento, salvo decisión editorial/legal expresa.

## Estado técnico del repositorio relevante para Search Console

A fecha de corte:

- `robots.txt` permite rastreo general y declara `Sitemap: https://davidportodiaz.com/sitemap.xml`.
- El sitemap raíz incluye las principales familias públicas de contenido y herramientas.
- El repositorio dispone de contratos de indexabilidad/noindex y QA de discoverability; Search Console debe utilizarse como la comprobación externa de lo que Google realmente ha rastreado e indexado.
- La web ya mantiene contenidos de Autor, Obras, Cuaderno, Herramientas, Editoriales, Convocatorias, Prensa, Premios, Eventos, Recomendaciones y recursos machine-readable, por lo que una única lectura global de GSC ocultaría señales importantes.
- Las cuentas sociales canónicas registradas incluyen Instagram y TikTok, por lo que las nuevas propiedades de plataforma son directamente relevantes.

## Regla de oro

**Search Console no es la fuente de verdad editorial del sitio; es la fuente de verdad sobre cómo Google está descubriendo, rastreando, indexando y mostrando esa verdad editorial.**

Los cambios de contenido se deciden con evidencia de demanda + estrategia editorial + calidad. Un dato de Search Console no justifica por sí solo degradar la arquitectura, duplicar páginas, crear contenido vacío o alterar hechos canónicos.