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
- `THEV06` — `Post Views` (agregación `SUM`), **no publicar como `views_30d`**: la ficha no acredita si corresponde a rendimiento acumulado de publicaciones creadas en el período o a actividad generada dentro de él.
**NO** sumar vistas con impresiones, alcance, personas únicas o likes dados por el autor.


### Corrección de semántica validada contra documentación oficial (22/10/2026)

El documento [**Diferencia entre posts publicados y posts vistos en el periodo**](https://help.metricool.com/es/diferencia-entre-posts-publicados-y-posts-vistos-en-el-periodo-2pwtf) explica un riesgo real: los **posts publicados** se filtran por fecha de publicación pero su rendimiento se mide acumulado hasta ayer; los **posts vistos** incluyen la actividad ocurrida durante el rango (incluso de publicaciones antiguas). La [ficha oficial Threads](https://help.metricool.com/threads-metrics-90qhd) aplica este criterio a las vistas de publicaciones.

`THEV06` se denomina `Threads Evolution > Post Views`; la descripción del catálogo del conector no certifica que su serie represente *vistas generadas durante* esos 30 días. **Error anterior de esta PR:** el normalizador sumaba los valores y los exponía como `views_30d` si estaban completos. Esto podía generar una cifra comercial engañosa incluso sin fallos técnicos. **Corrección implantada:** `views_30d` permanece `null` siempre; se conservan únicamente diagnósticos de cobertura y el dato `THEV01` de seguidores. Tests de regresión comprueban que ni siquiera 30 valores generan un total publicado y que con una serie dispersa se conserva el dato de seguidores. Si se necesita tráfico mensual, deberá elegirse una métrica del apartado *posts vistos en el periodo*, demostrar su semántica y abrir un cambio acotado adicional.


**Precisión del alcance:** `THEV11` en el catálogo de Threads se describe como **Account Views / Profile views**. Tampoco debe usarse para sustituir `THEV06` ni para titular «visualizaciones de publicaciones»; representa visitas al perfil. Esto se verificó en el catálogo real `getAnalyticsAvailableMetrics(network="threads",connector="evolution")` y coincide con las categorías de la ficha oficial de Threads.

## 3. Código real añadido — normalizador ejecutable de Threads

- [scripts/research/gpt_metricool_threads.py](../../../../scripts/research/gpt_metricool_threads.py): lee un **fichero privado de exportación** y escribe en stdout un registro limpio. Acepta 30 días completos, fecha por fila, orden de columnas explícito, cadenas decimales que representen enteros y nulos; no accede a red.
- [tests/test_gpt_metricool_threads.py](../../../../tests/test_gpt_metricool_threads.py): 17 pruebas offline efectivamente ejecutadas y superadas, incluidas fechas sin ordenar, tipo incorrecto, cero, `null`, falta de días, duplicación de día, orden de columnas y fallo del CLI.
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

**Atención: no publicar esas cifras de ejemplo.** La salida fija `views_30d=null` **incluso con 30 valores** porque aún no se ha demostrado que `THEV06` mida visualizaciones generadas dentro de esas fechas. `status=ok` significa solamente que el dato final de seguidores es válido. Los seguidores se obtienen de la fecha final, nunca se arrastran desde un día anterior ni se convierten ausencias en 0. Se mantiene `coverage.days_with_post_views` como diagnóstico, no como prueba de cobertura de tráfico mensual.

### Procedimiento de prueba

1. Consultar en el MCP la marca conectada con los campos **en este orden** `["THEV01","THEV06"]` y un período de **30 días naturales completos**, indicando franja local de España (sin día actual en curso). Guardar la respuesta `rows` **solo localmente** en un JSON privado, junto con esos dos IDs y `from/to` exactos. El MCP devuelve `rows` sin descripción de columnas; el envoltorio evita intercambiarlas por error.
2. Ejecutar:

~~~bash
python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v
python scripts/research/gpt_metricool_threads.py /ruta/privada/export-threads.json
~~~

3. Comparar `followers` con Threads en Metricool para la fecha final. **No comparar el valor de `views_30d`** porque está deliberadamente suprimido; para publicarlo en el futuro hay que identificar y validar primero una métrica de **actividad vista durante el período**, no el rendimiento acumulado de publicaciones hechas en él.

### En qué punto se conecta después

El script devuelve un objeto `id=threads`, `followers`, `views_30d`, `period`, `coverage`, `observed_at`, `source` y `status`. **No escribirlo directamente en `data/social-metrics.generated.json`**, cuyo contrato exige `schema_version` y `networks[]`. El compositor común tendrá que validar y transformar estos registros, cotejarlos con la fuente de perfil de la PR #708 y publicarlos únicamente con autorización.

## 4. Puertas de validación que siguen abiertas

- El modo offline y los tests están probados; **no existe exportación autónoma MCP → repositorio**. No presentar como «automático» un proceso que todavía requiere recopilar el JSON manualmente.
- API REST: comprobar primero si el titular tiene plan Advanced/Custom y acceso a token; si no, **no desarrollar** llamadas `X-Mc-Auth`. Si lo tiene, usar el esquema Swagger oficial para construir la llamada concreta y probar contra un período real; no inferir que `THEV01` es nombre de parámetro REST.
- **Consulta real adicional** a Metricool (22/10/2026) para 22/09–21/10, con `THEV01` y `THEV06` en ese orden: 30 filas/días únicos, followers con dato 30/30; `THEV06` con dato **12/30** y `null` en **18/30**. Solo se registran coberturas aquí, no los valores personales. No se conoce si esos `null` reflejan días sin publicaciones o carencia de información. No imputar cero. Comparación de los valores con el panel visual pendiente.
- Las pruebas no incluyen red ni fueron ejecutadas por Actions. Después de validar la ingesta, conectar al normalizador general en una PR posterior; ejecutar la suite completa únicamente con permiso explícito.

**Resultado:** un camino probado para convertir matrices MCP a un dato de Threads auditable, y una restricción comercial contrastada que evita una integración REST de pago construida a ciegas.


## 5. Alternativa de automatización sin pagar API: piloto MCP → Make (NO ejecutado)

La hipótesis inicial «sin Advanced no hay automatización posible» resulta demasiado amplia. Fuentes primarias revisadas el 22/10/2026:

- [Metricool explica la conexión con Make](https://help.metricool.com/es/como-conectar-el-mcp-de-metricool-eqp9h): en un escenario Make añadir MCP, conectar `https://ai.metricool.com/mcp` y autorizar por OAuth. No necesita copiar una clave de la API HTTP.
- [Documentación oficial Make: MCP Client](https://apps.make.com/c5ZhYquO55e90hoCJ0rzt?baseline=219837): el módulo **Call a tool** invoca una herramienta concreta con argumentos mapeados (no necesita pasar por «Execute an action with AI»); todavía es **beta**, por lo que condiciones/precios pueden cambiar.
- [Precios Make](https://www.make.com/en/pricing): el plan Free anuncia **1.000 créditos/mes**, dos escenarios activos y mínimo 15 minutos entre ejecuciones. Una pasada diaria representa ~30 ejecuciones de la programación, pero el gasto real depende del número de módulos y llamadas: medirlo con un piloto.
- [MCP vs API Metricool](https://help.metricool.com/mcp-vs-api-access-what-is-the-difference-5y3ib): confirmar que se usa OAuth **MCP**, no el modo de token de API que requeriría Advanced/Custom.

### Prueba mínima que decidirá si merece la pena

1. En Make, crear un escenario **desactivado** con `MCP Client → Call a tool`, conectar la URL oficial y conceder autorización manual. No pedir credenciales ni tokens aquí.
2. Examinar el catálogo real de herramientas de ese servidor: seleccionar la herramienta de lectura de analítica con los **dos campos** `THEV01` y `THEV06` para una ventana de 30 días completos. **No asumir que el identificador interno de la herramienta coincide con el nombre del conector de ChatGPT.**
3. Ejecutar **una vez** manualmente; comprobar que devuelve fechas, métricas en el orden pedido y datos legibles sin errores de permisos/plan. Anotar créditos consumidos y si la conexión OAuth sobrevive a una segunda ejecución; no programar todavía.
4. Si funciona, mapear solo `metrics/from/to/rows` hacia el importador local de esta PR; no trasladar tokens, IDs privados ni toda la respuesta bruta a un repositorio público. Diseñar un transporte autenticado cuando exista un backend aprobado.
5. Si falla en Free por cuota, restricciones del cliente, OAuth no renovable o inaccesibilidad del catálogo: **descartar Make** sin introducir nuevos servicios. La vía pública de Bluesky/Mastodon sigue independiente.

**Estado correcto:** oficialmente documentados la conexión Metricool→Make y el módulo Call a tool; **NO verificadas aún** la ejecución del escenario con esta cuenta, la persistencia OAuth, el gasto real de créditos ni el traslado a GitHub. Esta investigación no implica autorizar a Make hoy.

### Repositorio «oficial» no disponible: evitar copiar forks a ciegas

[Metricool afirma que publica un MCP oficial](https://help.metricool.com/faqs-about-the-metricool-mcp-1i3w0) como `metricool/mcp-metricool`. Comprobado hoy por la API pública GitHub: esa URL devolvió **404**; solo `metricool/servers` es público en la organización y no demuestra ser el servidor de Metricool. Hay forks y adaptadores de terceros que usan el nombre «Metricool MCP» y en algunos casos requieren **API Advanced**. **No se han copiado ni recomendado como alternativa gratis.** La referencia de código funcional para esta PR es el propio importador y su test offline, y para acceso MCP remoto la integración oficial documentada con Make.
