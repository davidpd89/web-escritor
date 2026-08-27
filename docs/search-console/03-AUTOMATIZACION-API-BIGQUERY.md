# 03 — Automatización: BigQuery + Search Console API

**Objetivo:** disponer de histórico propio, análisis reproducibles y alertas sin depender de abrir manualmente Search Console.  
**Filosofía:** automatizar lectura, clasificación y alertas; mantener decisiones editoriales/técnicas bajo revisión humana.  
**Seguridad:** ningún token OAuth, refresh token, credencial de service account ni fichero JSON secreto debe versionarse en Git.

---

## 1. Arquitectura recomendada

```text
Google Search Console
├── UI
│   ├── análisis humano
│   ├── Live URL Inspection
│   ├── GenAI reports / controls
│   └── anotaciones
├── Bulk export → BigQuery
│   ├── histórico diario completo disponible
│   ├── SQL por territorios
│   ├── dashboards
│   └── alertas/anomalías
└── Search Console API
    ├── Search Analytics (fallback / backfill / consultas concretas)
    ├── Sitemaps
    ├── Sites/properties
    └── URL Inspection (estado indexado)
```

### Autoridades

- **BigQuery:** histórico analítico principal desde el día de activación.
- **Search Console UI:** diagnósticos exclusivos, live testing, controles y funciones nuevas no expuestas por API.
- **API:** automatización de estado/consultas concretas.
- **Repositorio:** metodología, scripts y tests; **no** dumps completos de queries ni credenciales.

---

## 2. BigQuery bulk export — por qué activarlo pronto

Google permite exportar diariamente los datos de rendimiento de una propiedad a BigQuery, excepto consultas anonimizadas.

La ventaja decisiva es temporal: la exportación empieza a acumular desde la configuración. No debe posponerse hasta «cuando tengamos más SEO» porque entonces faltará histórico propio anterior.

### Requisitos oficiales

1. proyecto de Google Cloud;
2. facturación habilitada;
3. BigQuery API;
4. BigQuery Storage API;
5. conceder a `search-console-data-export@system.gserviceaccount.com`:
   - BigQuery Job User;
   - BigQuery Data Editor;
6. configurar export en Search Console: `Settings > Bulk data export`.

### Coste

Google Cloud puede cobrar almacenamiento/consulta por encima del free tier. Para un sitio de este tamaño el volumen debería ser moderado, pero no asumir coste cero: configurar presupuestos/alertas y limitar scans por partición.

### Retención

Los datos se acumulan indefinidamente salvo que se configure expiración de particiones. Google recomienda gestionar la retención para controlar costes.

**Recomendación del proyecto:** inicialmente conservar histórico completo si el coste es insignificante. Si crece, nunca bajar de una ventana que impida análisis estacional; cualquier expiración debe documentarse.

Fuentes: SC-BQ-OVERVIEW, SC-BQ-SETUP.

---

## 3. Tablas creadas por Search Console

Dataset por defecto: `searchconsole` (personalizable).

### `searchdata_site_impression`

Datos agregados a nivel de propiedad.

Campos clave incluyen:

- `data_date`;
- `site_url`;
- `query`;
- `is_anonymized_query`;
- `country`;
- `search_type`;
- `device`;
- impresiones/clics;
- sumas necesarias para posición.

### `searchdata_url_impression`

Datos a nivel URL, con campos como:

- `data_date`;
- `site_url`;
- `url`;
- `query`;
- `is_anonymized_query`;
- `is_anonymized_discover`;
- `country`;
- `search_type`;
- `device`;
- booleanos `is_[search_appearance]`;
- `impressions`;
- `clicks`;
- `sum_position`.

### `ExportLog`

Registra exportaciones **correctas**. Importante: los intentos fallidos no se registran como fila fallida; por eso conviene también monitorizar la página de estado de exportación en Search Console.

Campos relevantes:

- `agenda`;
- namespace/table;
- `data_date`;
- `epoch_version`;
- `publish_time`.

`epoch_version` puede subir si Google vuelve a publicar/corregir datos antiguos. Un pipeline serio no debe asumir inmutabilidad eterna de una partición pasada.

Fuente: SC-BQ-TABLES.

---

## 4. Regla SQL crítica: agregar siempre

Google advierte que las filas no tienen por qué estar consolidadas por fecha/query/URL. Por tanto:

**Incorrecto:** leer una fila como total.

**Correcto:** `SUM(impressions)`, `SUM(clicks)` y agregación explícita.

### Posición media

A nivel URL:

```sql
(SUM(sum_position) / SUM(impressions)) + 1.0
```

A nivel site, usar el campo de posición superior documentado por Google (`sum_top_position`) y sumar antes de dividir.

### Coste

Filtrar SIEMPRE por `data_date` para aprovechar particionamiento y reducir bytes procesados.

Fuente: SC-BQ-QUERY-GUIDELINES.

---

## 5. Vistas lógicas recomendadas

No materializar todo desde el primer día. Empezar con views/queries versionadas.

### 5.1 `gsc_daily_web`

```sql
SELECT
  data_date,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
  (SAFE_DIVIDE(SUM(sum_top_position), SUM(impressions)) + 1.0) AS avg_position
FROM `PROJECT.searchconsole.searchdata_site_impression`
WHERE search_type = 'WEB'
  AND data_date BETWEEN @start_date AND @end_date
GROUP BY data_date
ORDER BY data_date;
```

### 5.2 `gsc_pages_web`

```sql
SELECT
  url,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
  (SAFE_DIVIDE(SUM(sum_position), SUM(impressions)) + 1.0) AS avg_position
FROM `PROJECT.searchconsole.searchdata_url_impression`
WHERE search_type = 'WEB'
  AND data_date BETWEEN @start_date AND @end_date
GROUP BY url
ORDER BY clicks DESC;
```

### 5.3 `gsc_queries_web`

```sql
SELECT
  query,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr
FROM `PROJECT.searchconsole.searchdata_site_impression`
WHERE search_type = 'WEB'
  AND query != ''
  AND data_date BETWEEN @start_date AND @end_date
GROUP BY query
ORDER BY impressions DESC;
```

`query = ''` puede representar consultas anonimizadas; excluirla cuando el análisis requiera texto de query, pero conservar sus impresiones/clics en totales de propiedad.

---

## 6. Clasificador de territorios por URL

Crear un `CASE` reproducible:

```sql
CASE
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/las-manecillas-del-recuerdo/') THEN 'obra-manecillas'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/libros/samuel-entre-mundos/') THEN 'obra-samuel'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/(libros/|fragmento/|clubes-de-lectura/|universo/)') THEN 'obras-ecosistema'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/cuaderno/') THEN 'cuaderno'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/herramientas/') THEN 'herramientas'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/editoriales/') THEN 'editoriales'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/convocatorias-escritores/') THEN 'convocatorias'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/recomendaciones/') THEN 'recomendaciones'
  WHEN REGEXP_CONTAINS(url, r'^https://davidportodiaz\.com/recursos/') THEN 'recursos'
  WHEN url IN (
    'https://davidportodiaz.com/',
    'https://davidportodiaz.com/autor.html',
    'https://davidportodiaz.com/prensa.html',
    'https://davidportodiaz.com/premios.html',
    'https://davidportodiaz.com/eventos.html',
    'https://davidportodiaz.com/ferias.html',
    'https://davidportodiaz.com/ai/'
  ) THEN 'entidad-autor'
  ELSE 'otros'
END AS territory
```

### Mejora futura

No mantener este CASE duplicado para siempre. Claude debería poder generar la clasificación desde `data/content-registry.json`/territorios canónicos o desde un mapa versionado único para GSC.

---

## 7. Marca / no marca en BigQuery

Search Console UI tiene filtro nativo que debemos preferir para su clasificación oficial. En BigQuery, si Google no exporta directamente esa etiqueta como dimensión, crear una **clasificación analítica local** y marcarla como heurística.

### Regex inicial conservadora

```sql
REGEXP_CONTAINS(
  NORMALIZE_AND_CASEFOLD(query),
  r'(david\s*porto|david\s*porto\s*d[ií]az|davidportodiaz|samuel\s+entre\s+mundos|las\s+manecillas\s+del\s+recuerdo|noveris)'
)
```

### Reglas

- comparar el resultado heurístico con el filtro nativo de GSC;
- ampliar alias solo con evidencia real;
- no etiquetar términos genéricos de género como marca;
- mantener lista versionada con motivo/fecha.

---

## 8. Query: crecimiento por territorio 28d vs 28d

Esquema conceptual:

```sql
WITH base AS (
  SELECT
    url,
    CASE ... END AS territory,
    IF(data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY), 'current', 'previous') AS period,
    SUM(clicks) AS clicks,
    SUM(impressions) AS impressions
  FROM `PROJECT.searchconsole.searchdata_url_impression`
  WHERE search_type = 'WEB'
    AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 56 DAY)
  GROUP BY url, territory, period
)
SELECT
  territory,
  SUM(IF(period='current', clicks, 0)) AS clicks_current,
  SUM(IF(period='previous', clicks, 0)) AS clicks_previous,
  SUM(IF(period='current', impressions, 0)) AS impressions_current,
  SUM(IF(period='previous', impressions, 0)) AS impressions_previous
FROM base
GROUP BY territory;
```

No alertar por porcentaje si el denominador es casi cero. Añadir mínimo de volumen o confidence band según madure el sistema.

---

## 9. Query: oportunidades CTR

El objetivo no es ordenar por CTR más bajo, sino encontrar volumen + posición competitiva + CTR mejorable.

```sql
SELECT
  url,
  query,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
  (SAFE_DIVIDE(SUM(sum_position), SUM(impressions)) + 1.0) AS avg_position
FROM `PROJECT.searchconsole.searchdata_url_impression`
WHERE search_type = 'WEB'
  AND data_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
                    AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND query != ''
GROUP BY url, query
HAVING impressions >= @min_impressions
   AND avg_position BETWEEN @min_position AND @max_position
ORDER BY impressions DESC;
```

Parámetros deben calibrarse con volumen real. No hardcodear `1000 impressions` si el sitio todavía opera en otra escala.

---

## 10. Query: páginas que ganan/pierden

Construir dos ventanas equivalentes y calcular:

- delta clicks;
- delta impressions;
- delta CTR;
- delta position solo como contexto;
- cambio absoluto además de porcentaje.

Ordenar primero por **impacto absoluto**, luego relativo.

Motivo: `1 → 2 clicks = +100 %` no debe superar a `500 → 350 = -150 clicks`.

---

## 11. Query: nuevas consultas

Definir «nueva» como query con impresiones/clicks en periodo actual y cero en una ventana previa suficiente.

Usos:

- detectar demanda emergente;
- encontrar sinónimos reales;
- enriquecer páginas existentes;
- encontrar gaps.

No crear automáticamente un artículo por cada query nueva.

---

## 12. Query: canibalización potencial

```sql
SELECT
  query,
  COUNT(DISTINCT url) AS urls,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ARRAY_AGG(STRUCT(url, impressions, clicks) ORDER BY impressions DESC LIMIT 10) AS candidates
FROM (...agregado query+url...)
GROUP BY query
HAVING COUNT(DISTINCT url) > 1
ORDER BY impressions DESC;
```

Luego revisión humana. Dos URLs para una query no son automáticamente un problema.

---

## 13. Query: Search type

Agrupar por:

- WEB;
- IMAGE;
- VIDEO;
- DISCOVER;
- NEWS/GOOGLE_NEWS según tabla/dato.

Objetivo:

- detectar si portadas/imágenes generan descubrimiento;
- separar Discover de Search;
- no atribuir una subida visual al texto SEO de forma errónea.

---

## 14. Query: países y dispositivos

Usar solo si hay volumen suficiente.

Preguntas útiles:

- ¿España domina o crece Latinoamérica?
- ¿móvil tiene peor CTR para las mismas query/pages?
- ¿un problema de CWV móvil coincide con pérdida de tráfico móvil?

No dividir tanto los datos que queden muestras irrelevantes.

---

## 15. Monitor del ExportLog

Consulta diaria:

- comprobar última `data_date` esperada;
- confirmar filas para las dos tablas;
- observar `epoch_version`;
- detectar lag anormal.

### Importante

`ExportLog` registra exportaciones correctas, no intentos fallidos. Si faltan fechas, revisar también Search Console > Bulk data export status.

---

## 16. Search Console API: arquitectura

### Autorización

Elegir OAuth/identidad de servicio compatible con propiedad y entorno.

Requisitos de seguridad:

- scopes mínimos (`webmasters.readonly` si solo lectura);
- secretos en GitHub Secrets/secret manager, no repo;
- rotación y revocación documentadas;
- ninguna credencial en logs/artifacts.

### Servicios

- Search Analytics;
- Sitemaps;
- Sites;
- URL Inspection.

---

## 17. Search Analytics API — estrategia de extracción

Google recomienda evitar consultas enormes y repetidas.

### Patrón propuesto

- datos finalizados: extraer por **día**;
- retraso: procesar D-3 (y opcionalmente revalidar D-7);
- `rowLimit = 25000`;
- paginar con `startRow` hasta respuesta vacía;
- guardar idempotentemente por fecha/dimensiones;
- no reconsultar meses completos cada ejecución.

### Límite de datos

Google documenta hasta **50.000 filas/día/tipo/propiedad** disponibles vía API.

Para más granularidad/exhaustividad a largo plazo, preferir bulk export.

Fuentes: SC-API-EXPORT, SC-API-QUERY.

---

## 18. Search Analytics API — payload base

Ejemplo conceptual:

```json
{
  "startDate": "2026-08-24",
  "endDate": "2026-08-24",
  "dimensions": ["query", "page", "device", "country"],
  "type": "web",
  "dataState": "final",
  "rowLimit": 25000,
  "startRow": 0
}
```

### Datos recientes

`dataState=all` incluye datos frescos/incompletos.

`dataState=hourly_all` permite desglose horario cuando se usa dimensión `hour`, pero puede ser parcial. Guardar metadata de `first_incomplete_date`/`first_incomplete_hour` y nunca mezclarlo silenciosamente con datos finales.

Fuente: SC-API-QUERY.

---

## 19. Cuotas API

### Search Analytics

- 1.200 QPM por sitio;
- 1.200 QPM por usuario;
- 30.000.000 QPD por proyecto;
- 40.000 QPM por proyecto;
- además existen cuotas de carga a corto/largo plazo.

Consultas por página + query y rangos largos son más costosos.

### URL Inspection

- 2.000 QPD por sitio;
- 600 QPM por sitio;
- 10.000.000 QPD por proyecto;
- 15.000 QPM por proyecto.

### Otros recursos

- 20 QPS / 200 QPM por usuario;
- 100M QPD por proyecto.

Fuente: SC-API-QUOTAS.

---

## 20. URL Inspection API — monitor de prioridad

### Limitación esencial

La API devuelve el estado de la **versión del índice de Google**. No puede ejecutar la prueba live de la URL publicada.

### Inventario inicial

Crear configuración, no hardcode disperso:

```yaml
priority_urls:
  - https://davidportodiaz.com/
  - https://davidportodiaz.com/autor.html
  - https://davidportodiaz.com/libros/
  - https://davidportodiaz.com/las-manecillas-del-recuerdo/
  - https://davidportodiaz.com/libros/samuel-entre-mundos/
  - https://davidportodiaz.com/cuaderno/
  - https://davidportodiaz.com/herramientas/
  - https://davidportodiaz.com/editoriales/
  - https://davidportodiaz.com/convocatorias-escritores/
  - https://davidportodiaz.com/recomendaciones/
  - https://davidportodiaz.com/prensa.html
  - https://davidportodiaz.com/premios.html
```

Mejor futuro: derivar prioridades desde el content registry con un campo/tabla específica de monitorización.

### Alertar si

- verdict pasa de indexed a no indexed;
- coverage state cambia de forma perjudicial;
- `googleCanonical` deja de coincidir con canonical esperada en prioridad P0;
- robots state cambia;
- last crawl envejece de forma extraña junto a otros síntomas;
- rich results críticos desaparecen donde antes existían.

No alertar por cualquier diferencia textual del API.

Fuente: SC-URL-API.

---

## 21. Sitemaps API

Usos:

- listar sitemap enviado;
- consultar estado;
- enviar sitemap tras cambio estructural real;
- eliminar envío obsoleto si cambia arquitectura.

No hacer submit diario si el mismo sitemap ya está accesible y Google lo procesa.

---

## 22. Almacenamiento local / privacidad

### No guardar en Git

- queries completas exportadas;
- datos de país/dispositivo sin necesidad;
- OAuth tokens;
- account IDs innecesarios;
- dumps de Search Console;
- credenciales GCP.

### Sí versionar

- SQL parametrizado;
- schemas propios;
- lista de territorios;
- reglas de alertas;
- tests;
- documentación;
- snapshots sintéticos/anonimizados para tests.

---

## 23. Dashboard recomendado

### Página 1 — Executive

- clicks 28d;
- impressions 28d;
- non-brand clicks;
- change vs prev 28d;
- territory share;
- indexing alerts;
- CWV summary manual/importado;
- GenAI impressions si existe/importable.

### Página 2 — Editorial discovery

- top non-brand queries;
- new queries;
- rising pages;
- CTR opportunities;
- query groups;
- content territories.

### Página 3 — Works

- Manecillas;
- Samuel;
- fragmentos;
- branded queries;
- generic genre/theme queries;
- images/search-type.

### Página 4 — Writers acquisition

- Tools;
- Editoriales;
- Convocatorias;
- Recursos;
- queries de intención.

### Página 5 — Technical

- URL Inspection priority status;
- sitemap status;
- export freshness;
- known anomaly flags;
- manual/security imported only if API/source available or checklist status.

---

## 24. Alertas recomendadas

### A. Tráfico

No usar porcentaje puro. Requerir:

- baseline mínimo;
- caída absoluta significativa;
- persistencia 3–7 días;
- no anomaly window oficial;
- segmentación por territorio.

### B. Nuevas queries

Digest semanal, no alerta inmediata.

### C. Indexación

Immediate:

- home/book pages no indexed;
- canonical externa inesperada.

Daily digest:

- otras priority URLs.

### D. Export

Alertar si:

- no aparece partición esperada tras margen razonable;
- `ExportLog` queda atrasado;
- estado bulk export informa error.

### E. GenAI

No automatizar todavía contra un endpoint no documentado. El informe GenAI 2026 tiene export manual, pero la API pública actual no documenta un endpoint específico GenAI. No inventarlo.

---

## 25. Integración con GitHub

### Fase 1 — read-only

Posibles scripts futuros:

```text
scripts/search-console/
├── README.md
├── fetch-search-analytics.py
├── inspect-priority-urls.py
├── check-sitemap-status.py
├── classify-territories.py
└── report-anomalies.py
```

### Workflows futuros

```text
.github/workflows/search-console-daily.yml
.github/workflows/search-console-weekly.yml
```

Solo crear cuando:

- auth esté resuelta de forma segura;
- no haya secrets en fork logs;
- output no contenga queries sensibles;
- user haya aprobado coste/Cloud project.

### Salida segura

Preferir summaries agregados:

```json
{
  "date": "2026-08-24",
  "territories": {
    "cuaderno": {"clicks": 0, "impressions": 0},
    "herramientas": {"clicks": 0, "impressions": 0}
  },
  "alerts": []
}
```

No commitear este ejemplo como dato real: ceros son placeholders.

---

## 26. Integración con content-registry

Una mejora importante sería que la monitorización no tenga una segunda arquitectura de rutas manual.

### Propuesta

Derivar del registry:

- URL;
- status public/gated;
- sitemap expected;
- searchIndex expected;
- territory;
- priority tier opcional.

Entonces el monitor puede detectar automáticamente:

- `status=public + searchIndex=true` pero URL no indexada;
- `status!=public` pero URL indexada inesperadamente;
- sitemap drift;
- territory dashboards.

### Cuidado

No asumir que **toda** URL `public/searchIndex=true` debe aparecer siempre en Google. Search Console puede no indexar una página por calidad/duplicación. El monitor debe señalar discrepancia para revisión, no declararla bug automáticamente.

---

## 27. Integración con anotaciones

La API pública actual no debe asumirse capaz de crear anotaciones si Google no documenta endpoint. Mantener la creación de anotaciones como paso humano en GSC hasta que exista API oficial.

Automatización puede generar el texto sugerido:

`RELEASE · Manecillas · publicación 03/09/2026`

pero no intentar hacer scraping/automatización UI.

---

## 28. GenAI: limitaciones de automatización actuales

A fecha 27/08/2026:

- existe informe específico GenAI Search en rollout;
- Google permite exportarlo desde la UI;
- existe control de inclusión en rollout;
- la documentación pública de Search Console API enumera Search Analytics, Sitemaps, Sites y URL Inspection;
- no se documenta un endpoint dedicado `generative-ai-performance`.

Por tanto:

- **no inventar API**;
- capturar/exportar manualmente baseline si aparece;
- revisar futuras actualizaciones oficiales;
- BigQuery Search web puede contener performance general, pero no asumir que permite aislar AI Overview/AI Mode si Google no documenta un campo específico para ello.

---

## 29. Social platform properties: automatización futura

Tratar Instagram/TikTok como propiedades distintas.

Si la Search Console API empieza a exponerlas como sites compatibles y la autenticación lo permite, se pueden incluir en el inventario de properties. Hasta confirmar:

- crear/verificar en UI;
- medir en UI;
- no asumir que BigQuery bulk export o todos los endpoints funcionan igual para propiedades de plataforma sin documentación específica.

---

## 30. Backfill histórico

Bulk export no debe asumirse retroactivo.

Al activar:

1. guardar fecha `BULK_EXPORT_START_DATE`;
2. para histórico anterior necesario, usar Search Analytics API/UI exports dentro de la ventana disponible;
3. marcar origen de cada dataset (`api_backfill` vs `bulk_export`);
4. no mezclar sin reconciliar diferencias de agregación/anonimización.

---

## 31. Testing de scripts futuros

Fixtures sintéticos deben cubrir:

- anonymized query `''`;
- zero impressions;
- múltiples filas para misma query/url;
- `epoch_version` revisado;
- URL nueva;
- URL no indexada;
- Google canonical diferente;
- 404 esperada;
- territorio desconocido;
- datos incompletos `all/hourly_all`;
- anomalía oficial activa;
- Search types distintos.

Tests nunca deben depender de la cuenta real de Google.

---

## 32. Definition of Done — automatización

### BigQuery

- [ ] proyecto GCP creado;
- [ ] billing controlado;
- [ ] APIs habilitadas;
- [ ] cuenta de export con roles mínimos oficiales;
- [ ] bulk export activo;
- [ ] tablas reciben datos;
- [ ] `ExportLog` monitorizado;
- [ ] costes/retención documentados;
- [ ] SQL usa particiones y agregaciones.

### API

- [ ] auth segura;
- [ ] readonly donde sea posible;
- [ ] extracción diaria idempotente;
- [ ] paginación correcta;
- [ ] respeto de cuotas;
- [ ] priority URL inspection;
- [ ] secrets fuera del repo;
- [ ] logs sin queries/credenciales innecesarias;
- [ ] tests sintéticos;
- [ ] alertas no modifican producción.

### Gobierno

- [ ] documentación de propietario GCP;
- [ ] procedimiento de revocación;
- [ ] presupuesto/alerta Cloud;
- [ ] revisión trimestral;
- [ ] nadie puede convertir automáticamente una señal SEO en un deploy.