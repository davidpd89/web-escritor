# Metricool — decisión verificable y contrato de importación

Actualizado 22/10/2026. **PR #705 hija de #699.** Objetivo concreto: aprovechar métricas ya conectadas sin comprometer un coste mensual antes de demostrar el valor. No se ejecutan Actions, no se despliega la web y no se guardan números privados en Git.

## 1. Hallazgo que cambia la arquitectura

Según la **guía oficial actual** de Metricool:
- [MCP vs API](https://help.metricool.com/mcp-vs-api-access-what-is-the-difference-5y3ib): su **MCP funciona también en Free** y permite consultar métricas desde asistentes compatibles.
- [Planes y API](https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u): su **API HTTP externa requiere Advanced o Custom**. Disponer de este conector de ChatGPT **no** habilita automáticamente consultas en un cron/Actions.
- [Guía de autenticación](https://help.metricool.com/es/guia-basica-para-la-integracion-con-la-api-r97af): las peticiones API requieren `X-Mc-Auth` más `userId` y `blogId`; no incluir estos datos ni tokens en la web o repositorio.
- [Swagger OFICIAL consultado](https://app.metricool.com/api/swagger.json): documenta `GET /v2/analytics/timelines` con parámetros de red y métrica; pero **no se ha hecho una petición API autenticada** porque el nivel de plan/credencial autónoma no está verificado. No inventar compatibilidad entre endpoints REST y códigos Data Studio del MCP.

**Decisión:** mantener el frontend estático. Un proceso backend autorizado podrá generar JSON más adelante; **ahora** usar el MCP para comprobación/exportación de lectura y normalizar **offline**, sin scraping de Metricool, tokens en cliente ni upgrade de pago. Esta PR no activa refresco automático por sí sola.

## 2. Evidencia práctica sin exponer la cuenta

El conector asociado a la marca devolvió realmente `{"rows":[...]}` para campos solicitados; se verificaron matrices de **5 filas y 12 columnas** al solicitar 11 métricas para 17–21/10/2026. La última columna contiene fechas `YYYYMMDD`. Las filas vinieron **desordenadas**; algunos valores eran `null` y los numéricos se representaron como cadenas `"123.0"`. Los números de ese ejemplo se omiten intencionadamente de la PR; no son material para publicar.

Para mantener el cambio pequeño, se seleccionan **solo dos campos de Threads**, ambos consultados en el catálogo actual `getAnalyticsAvailableMetrics(network="threads",connector="evolution")`:
- `THEV01` — seguidores (agregación `LAST`).
- `THEV06` — visualizaciones de publicaciones (agregación `SUM`).
**NO** sumar vistas con impresiones, alcance, personas únicas o likes dados por el autor.

## 3. Código real añadido — normalizador ejecutable de Threads

- [scripts/research/gpt_metricool_threads.py](../../../../scripts/research/gpt_metricool_threads.py): lee un **fichero privado de exportación** y escribe en stdout un registro limpio. Acepta 30 días completos, fecha por fila, orden de columnas explícito, cadenas decimales que representen enteros y nulos; no accede a red.
- [tests/test_gpt_metricool_threads.py](../../../../tests/test_gpt_metricool_threads.py): 15 pruebas offline efectivamente ejecutadas y superadas, incluidas fechas sin ordenar, tipo incorrecto, cero, `null`, falta de días, duplicación de día, orden de columnas y fallo del CLI.
- **No se añade fixture con datos reales.** Las pruebas construyen series **sintéticas** de 30 días en memoria.

Entrada EXACTA que acepta el script; las filas aquí son una **explicación de forma** (para procesar habrá que aportar la serie real completa de 30 días):

~~~json
{
  "metrics": ["THEV01", "THEV06"],
  "from": "2026-09-22",
  "to": "2026-10-21",
  "rows": [
    ["123.0", "8.0", "20260922"],
    ["124.0", "9.0", "20260923"]
  ]
}
~~~

**Atención: no publicar esas cifras de ejemplo.** La salida marcará `views_30d=null` y `status=partial` porque aquí faltan 28 días. Para producir `views_30d` necesita cada día entre `from` y `to`, ambos inclusive, con un valor válido. Los seguidores se obtienen únicamente de la fecha final; nunca arrastrar un valor de otro día ni convertir falta de dato en 0. Los snapshots parciales son inspeccionables; **el consumidor público debe omitir métricas nulas**.

### Procedimiento de prueba

1. Consultar en el MCP la marca conectada con los campos **en este orden** `["THEV01","THEV06"]` y un período de **30 días naturales completos**, indicando franja local de España (sin día actual en curso). Guardar la respuesta `rows` **solo localmente** en un JSON privado, junto con esos dos IDs y `from/to` exactos. El MCP devuelve `rows` sin descripción de columnas; el envoltorio evita intercambiarlas por error.
2. Ejecutar:

~~~bash
python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v
python scripts/research/gpt_metricool_threads.py /ruta/privada/export-threads.json
~~~

3. Comparar `followers` y `views_30d` con la sección de Threads en Metricool, mismo período y misma cuenta. Si el campo de vistas devuelve `null` algún día, no publicar una suma aparentemente completa. Conservar fecha, cobertura y fuente `metricool-mcp-export`.

### En qué punto se conecta después

El script devuelve un objeto `id=threads`, `followers`, `views_30d`, `period`, `coverage`, `observed_at`, `source` y `status`. **No escribirlo directamente en `data/social-metrics.generated.json`**, cuyo contrato exige `schema_version` y `networks[]`. El compositor común tendrá que validar y transformar estos registros, cotejarlos con la fuente de perfil de la PR #708 y publicarlos únicamente con autorización.

## 4. Puertas de validación que siguen abiertas

- El modo offline y los tests están probados; **no existe exportación autónoma MCP → repositorio**. No presentar como «automático» un proceso que todavía requiere recopilar el JSON manualmente.
- API REST: comprobar primero si el titular tiene plan Advanced/Custom y acceso a token; si no, **no desarrollar** llamadas `X-Mc-Auth`. Si lo tiene, usar el esquema Swagger oficial para construir la llamada concreta y probar contra un período real; no inferir que `THEV01` es nombre de parámetro REST.
- El ejemplo de 5 días de la cuenta real confirma **la forma de respuesta, no** que haya una serie completa de 30 días. La comparación de valores con el panel queda pendiente.
- Las pruebas no incluyen red ni fueron ejecutadas por Actions. Después de validar la ingesta, conectar al normalizador general en una PR posterior; ejecutar la suite completa únicamente con permiso explícito.

**Resultado:** un camino probado para convertir matrices MCP a un dato de Threads auditable, y una restricción comercial contrastada que evita una integración REST de pago construida a ciegas.
