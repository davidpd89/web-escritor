# 07 — Anomalías de datos de Search Console en 2026

**Corte:** 27 de agosto de 2026  
**Objetivo:** impedir diagnósticos SEO falsos causados por problemas de logging, cambios de metodología o datos incompletos de Google.

Este documento no afirma que davidportodiaz.com haya sufrido estas caídas reales de tráfico. Registra periodos en los que Google documentó problemas de **medición/reporting** que pueden contaminar comparaciones.

---

## 1. Regla obligatoria antes de diagnosticar una caída

Antes de atribuir un descenso a una PR, contenido, algoritmo o competencia:

1. identificar informe exacto: Search / Discover / Google News / GenAI / bulk export;
2. revisar anotaciones del sistema en Search Console;
3. consultar la página oficial de anomalías;
4. comprobar si el periodo está afectado;
5. distinguir clics de impresiones;
6. distinguir caída de reporting de caída real de tráfico;
7. excluir o marcar el periodo contaminado en SQL/dashboards;
8. solo después investigar la web.

Fuente oficial viva:

https://support.google.com/webmasters/answer/6211453

---

## 2. 13 de agosto de 2026 — Discover / IA generativa de Discover

Google documentó un problema de logging que provocó una caída de clics e impresiones reportados en Discover y en funciones generativas de Discover.

### Consecuencia analítica

- no comparar ese día de forma ingenua con el anterior;
- no abrir una incidencia de contenido solo porque el gráfico caiga;
- marcar el día en cualquier dataset propio.

### BigQuery

Si esos datos forman parte de exportaciones disponibles, conservarlos con una tabla/calendario de anomalías para que las consultas puedan excluir o etiquetar el periodo.

---

## 3. 13–17 de agosto de 2026 — IA generativa de Search

Google documentó un problema de logging que produjo menos **impresiones reportadas** en el informe de IA generativa de Search.

### Importante

El síntoma documentado es de reporting de impresiones. No convertir automáticamente esa caída en:

- pérdida de inclusión en AI Overviews;
- pérdida de AI Mode;
- penalización;
- fallo de indexación.

### Baselines

Si el informe GenAI aparece por primera vez cerca de estas fechas, no usar 13–17 de agosto como baseline limpio.

---

## 4. 24 de junio de 2026 — Discover / IA generativa de Discover

Google registró una caída de reporting en Discover y funciones generativas de Discover.

### Acción

Marcar el periodo antes de cualquier análisis trimestral que abarque junio.

---

## 5. 21 de mayo de 2026 — Discover

Google documentó una anomalía de logging de Discover.

### Acción

Excluir/etiquetar ese día cuando se estudien tendencias de Discover en mayo.

---

## 6. 7–8 de mayo de 2026 — Discover

Google documentó una anomalía de logging de Discover alrededor de estas fechas.

### Coincidencia importante

El 7 de mayo de 2026 también es la fecha desde la que Google dejó de mostrar FAQ rich results. Son fenómenos distintos:

- anomalía Discover = reporting;
- retirada FAQ rich results = cambio de producto/appearance.

No mezclar ambos en un mismo diagnóstico.

---

## 7. 7 de mayo de 2026 — retirada de FAQ rich results

Desde esta fecha, Google dejó de mostrar FAQ rich results en Search.

En agosto de 2026 Google está retirando también el soporte de esa search appearance en la Search Console API.

### Implicaciones para histórico

- dashboards históricos pueden contener una dimensión FAQ antigua;
- consultas API futuras no deben depender de ese appearance;
- una caída a cero de FAQ después del 7 de mayo es esperada por retirada del feature, no una regresión del sitio;
- mantener FAQ visible solo si ayuda a usuarios, no para perseguir el rich result retirado.

Fuente complementaria oficial:

https://developers.google.com/webmaster-tools/v1/searchanalytics/query

---

## 8. 16–27 de abril de 2026 — job listing / job detail

Google documentó un problema de logging para apariencias relacionadas con ofertas/detalles de empleo.

### Aplicación a este proyecto

Actualmente no es un territorio relevante de davidportodiaz.com. Se registra por completitud y para que una futura herramienta/dashboard no interprete esas dimensiones históricas como señal fiable durante el periodo.

---

## 9. 3 de abril de 2026 — corrección histórica de impresiones

Google documentó un problema de reporting histórico que afectaba a impresiones desde aproximadamente el **13 de mayo de 2025 hasta el 27 de abril de 2026**, posteriormente corregido.

Según la documentación de anomalías, podía afectar métricas derivadas de impresiones como:

- impresiones;
- CTR;
- posición.

Los clics no estaban afectados del mismo modo.

### Riesgo para análisis longitudinal

Si se conservan exports antiguos hechos antes de la corrección y se comparan con datos reconsultados después, pueden existir diferencias.

### Regla BigQuery/API

- guardar origen y fecha de extracción de backfills;
- permitir reimportar/reconciliar periodos corregidos;
- no asumir que un snapshot exportado manualmente meses atrás es idéntico a la versión corregida que Google ofrece después.

---

## 10. 28 de febrero y 1 de marzo de 2026 — bulk export incompleto

Google documentó ausencia de datos en algunas exportaciones bulk para esas fechas y señaló que los datos no podían recuperarse.

### Implicación

Un hueco en BigQuery en esas fechas puede ser externo al pipeline propio.

### Monitor de export

El sistema futuro debe distinguir:

- `expected_gap_google`;
- `pipeline_failure`;
- `export_not_started_yet`;
- `normal_lag`.

No abrir alerta perpetua por dos particiones oficialmente irrecuperables.

---

## 11. Tabla de calendario para SQL

Cuando se active BigQuery, crear una tabla pequeña propia, por ejemplo:

`gsc_known_anomalies`

Campos recomendados:

```text
start_date DATE
end_date DATE
surface STRING
metric_scope STRING
kind STRING
source_url STRING
note STRING
exclude_from_trend BOOL
```

Ejemplo conceptual:

```sql
SELECT DATE '2026-08-13' AS start_date,
       DATE '2026-08-17' AS end_date,
       'GENAI_SEARCH' AS surface,
       'impressions' AS metric_scope,
       'google_logging_issue' AS kind,
       'https://support.google.com/webmasters/answer/6211453' AS source_url,
       'Lower reported impressions; do not interpret as confirmed visibility loss.' AS note,
       TRUE AS exclude_from_trend;
```

No guardar una tabla estática y olvidarla: actualizarla cuando Google publique nuevas anomalías.

---

## 12. Etiqueta en dashboards

Todo gráfico debería poder marcar periodos con:

- `Google data anomaly`;
- `own site annotation`;
- `preliminary data`;
- `final data`.

Así se evita correlacionar automáticamente un release del sitio con una caída que en realidad coincide con un fallo de logging de Google.

---

## 13. Datos preliminares y vista de 24 h

Aunque no exista una anomalía oficial:

- los datos recientes pueden ser preliminares;
- Search Analytics API con `dataState=all` puede incluir datos incompletos;
- `hourly_all` puede tener horas incompletas;
- usar metadata de fecha/hora incompleta cuando la API la devuelva.

### Regla de alertas

Alertas críticas de tráfico no deben dispararse solo con datos preliminares salvo un incidente técnico evidente y corroborado por otras señales.

---

## 14. Queries anonimizadas

Por privacidad, Search Console no expone todas las consultas de baja frecuencia.

Consecuencias:

- la suma de filas de query puede no igualar los totales;
- BigQuery omite el texto de queries anonimizadas pero conserva agregados relevantes mediante campos de anonimización;
- no atribuir la diferencia a «datos perdidos» del pipeline.

### SQL

Para totales: incluir impresiones/clics anonimizados.

Para análisis textual de queries: excluir `query=''` / `is_anonymized_query` según esquema.

---

## 15. Canonicalización y atribución de datos

Google suele atribuir performance a la URL canónica. Por tanto:

- una URL alternativa puede recibir cero datos aunque haya sido mostrada/rastreada;
- consolidación de canonical puede mover métricas entre URLs;
- antes de declarar una «pérdida de tráfico de URL» revisar canonical elegida.

Esto es especialmente relevante si el proyecto cambia trailing slash, redirects o consolida páginas.

---

## 16. Cambios de metodología de Google

Además de anomalías explícitas, Search Console puede cambiar:

- definición de una appearance;
- clasificación de marca;
- filtros;
- reporting de funciones IA;
- métricas disponibles;
- forma de agregación.

### Regla de gobierno

Cuando una serie cambia bruscamente en la misma fecha para muchas URLs sin causa propia:

1. buscar actualización oficial;
2. revisar Search Console help/changelog/anomalies;
3. registrar `methodology_change` si procede;
4. no normalizar los datos manualmente sin evidencia.

---

## 17. Qué debe hacer Claude con este documento

Si implementa `scripts/search-console/`:

- cargar un calendario de anomalías versionado o mantenible;
- permitir excluir/etiquetar periodos;
- testear las fechas 2026 conocidas;
- distinguir datos preliminares/finales;
- no crear alertas sobre gaps de 28/02–01/03/2026;
- no esperar FAQ appearance después de su retirada;
- registrar source URL para cada anomalía;
- no modificar datos crudos: aplicar filtros en capa analítica.

---

## 18. Checklist antes de atribuir un descenso a nuestra web

- [ ] ¿El informe es Search web, Discover, News o GenAI?
- [ ] ¿El periodo coincide con anomalía oficial?
- [ ] ¿Son datos finalizados?
- [ ] ¿Cayeron clics e impresiones o solo una métrica?
- [ ] ¿Es branded o non-branded?
- [ ] ¿Afecta todas las URLs o una familia?
- [ ] ¿Cambió canonical/indexación?
- [ ] ¿Hubo anotación/release propio?
- [ ] ¿Hay estacionalidad/demanda?
- [ ] ¿El cambio supera ruido normal por volumen?

Solo tras responder esto se abre una hipótesis de SEO/técnica propia.