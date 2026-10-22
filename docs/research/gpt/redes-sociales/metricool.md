# #705 · Metricool: seguidores de Threads, una sola métrica

**Estado 22/10/2026:** adaptador Python y 17 pruebas offline ejecutadas. Un GET real a través del **conector Metricool conectado** confirma la forma de respuesta. **No hay exportación automática, backend ni publicación en la web.** Hija de [#699](https://github.com/davidpd89/web-escritor/pull/699).

## Problema y decisión

La propuesta anterior pedía 30 días de `THEV01` (seguidores) y `THEV06` (Post Views). Pero `THEV06` no se publicaba: Metricool [distingue vistas acumuladas de posts publicados y vistas ocurridas en el período](https://help.metricool.com/es/diferencia-entre-posts-publicados-y-posts-vistos-en-el-periodo-2pwtf). Pedir una métrica descartada aumenta consultas, datos incompletos y fallos. **Eliminada** del contrato y del código. `views_30d` e `impressions_30d` siguen `null`.

**Solución validada:** usar exclusivamente `THEV01` (catálogo real del conector: `Threads Evolution > Followers`, `dataAggregation=LAST`), con un **único día natural ya terminado**. Una llamada real el 22/10/2026 con rango 21/10/2026 00:00–23:59:59 hora de Madrid, solicitando solo `["THEV01"]`, devolvió **una fila de dos columnas**, contador decimal en texto y fecha `"20261021"`. Cuatro días consecutivos consultados por separado confirmaron el mismo formato. Los valores de la cuenta no se incluyen en el repositorio.

## Archivos de código — ya en la rama de esta PR

- [scripts/research/gpt_metricool_threads.py](../../../../scripts/research/gpt_metricool_threads.py): Python estándar, sin credenciales ni peticiones propias de red; valida que `metrics=["THEV01"]`, `from=to`, única fila `[followers, YYYYMMDD]` y fecha exacta. Convierte `"232.0"` (ejemplo inventado) a entero sin redondear. Rechaza booleanos, negativos, decimales fraccionarios, fechas distintas, filas duplicadas y claves extra. Produce un **registro de Threads por stdout**; no modifica datos públicos.
- [tests/test_gpt_metricool_threads.py](../../../../tests/test_gpt_metricool_threads.py): **17/17 PASS**, ejecutados localmente el 22/10/2026 con `python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v`. Hashes Git de los dos archivos probados contrastados con sus hashes en la rama; mismo código. No es el CI general del sitio.

### Contrato de entrada: envoltorio privado sobre la respuesta MCP

El MCP entrega únicamente `{"rows":[["232.0","20261021"]]}` para una métrica en ese día; para no confundir campos ni fechas, quien exporte el resultado debe envolverlo **localmente**, sin IDs de marca ni tokens:

~~~json
{
  "metrics": ["THEV01"],
  "from": "2026-10-21",
  "to": "2026-10-21",
  "rows": [["232.0", "20261021"]]
}
~~~

**232 es una cifra ficticia.** No registrar snapshots reales en Git ni compartir tokens. Reproducir:

~~~bash
python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v
python scripts/research/gpt_metricool_threads.py /ruta/privada/threads.json
~~~

Salida: `id=threads`, `followers` (entero o `null`), `observed_at` (día de la métrica), `source=metricool-mcp-export`, `generated_at`, `status` y las dos métricas de vistas como `null`. **Un contador ausente no se convierte en cero**. La salida no es el documento agregado `data/social-metrics.generated.json`; requiere el compositor central de #699 antes de mostrarse en #704.

## Puerta de integración: lo que funciona y lo que NO

**Demostrado:** existencia y semántica `LAST` de `THEV01` en catálogo, llamada de lectura real con una fecha, estructura exacta de 2 columnas, normalización sin conexión y los 17 casos offline. Al simplificar, se eliminó toda obligación de consultar `THEV06`.

**Pendiente:** comparación del valor contra la interfaz de Metricool, entrega automatizada y autorizada del resultado al servidor, gestión de fallos/caducidad (se recomienda ocultar contador si no hay lectura reciente). No escribir `data/social-metrics.generated.json` desde este importador ni ejecutar Actions antes de aprobarlo.

**Coste y automatización:** [Metricool confirma](https://help.metricool.com/es/planes-complementos-y-acceso-a-la-api-explicados-xux1u) que **MCP está disponible incluso en Free**; la API HTTP independiente exige Advanced o Custom. Por tanto, NO escribir hoy un cron que dependa de un token API inexistente. [La guía oficial de conexión MCP](https://help.metricool.com/es/como-conectar-el-mcp-de-metricool-eqp9h) incluye clientes externos, entre ellos Make. El siguiente experimento sería una única llamada `MCP Client → Call a tool` desde Make, autorizada por OAuth, revisando retorno y créditos. **No se ha ejecutado ese piloto; no se puede prometer refresco automático.**

**Fuente de código público:** la funcionalidad de lectura la presta el **MCP oficial de Metricool**, cuyo servidor está documentado públicamente; no hemos clonado ni copiado un SDK comunitario sin necesidad, y el importador es código propio de Python estándar. La documentación de Metricool declara un repo `metricool/mcp-metricool`, pero el acceso a esa URL devolvió 404 durante esta investigación: no se ha considerado fuente de código verificable.

### Entrega a Claude

Antes de merge, **solo** ejecutar lectura de un día terminado, cotejar seguidores en Metricool, decidir el transporte backend y validar caché/caducidad. Si se adopta Make, primero prueba manual y después recurrencia; si falla el piloto, continuar con Bluesky/Mastodon públicos sin inventar una API de pago. Mantener PR separadas, no tocar `main` y ejecutar suite/Actions únicamente cuando el usuario lo autorice.
