# #705 · Metricool: seguidores de Threads, una sola métrica

**Estado 22/10/2026:** adaptador Python y 17 pruebas offline ejecutadas. Un GET real a través del **conector Metricool conectado** confirma la forma de respuesta. **No hay exportación automática, backend ni publicación en la web.** Hija de [#699](https://github.com/davidpd89/web-escritor/pull/699).

## Problema y decisión

La propuesta anterior pedía 30 días de `THEV01` (seguidores) y `THEV06` (Post Views). Pero `THEV06` no se publicaba: Metricool [distingue vistas acumuladas de posts publicados y vistas ocurridas en el período](https://help.metricool.com/es/diferencia-entre-posts-publicados-y-posts-vistos-en-el-periodo-2pwtf). Pedir una métrica descartada aumenta consultas, datos incompletos y fallos. **Eliminada** del contrato y del código. `views_30d` e `impressions_30d` siguen `null`.

**Solución validada:** usar exclusivamente `THEV01` (catálogo real del conector: `Threads Evolution > Followers`, `dataAggregation=LAST`), con un **único día natural ya terminado**. Una llamada real el 22/10/2026 con rango 21/10/2026 00:00–23:59:59 hora de Madrid, solicitando solo `["THEV01"]`, devolvió **una fila de dos columnas**, contador decimal en texto y fecha `"20261021"`. Cuatro días consecutivos consultados por separado confirmaron el mismo formato. Los valores de la cuenta no se incluyen en el repositorio.

## Archivos de código — ya en la rama de esta PR

- [scripts/research/gpt_metricool_threads.py](../../../../scripts/research/gpt_metricool_threads.py): Python estándar, sin credenciales ni peticiones propias de red; valida que `metrics=["THEV01"]`, `from=to`, única fila `[followers, YYYYMMDD]` y fecha exacta. Convierte `"123456.0"` (ejemplo inventado) a entero sin redondear. Rechaza booleanos, negativos, decimales fraccionarios, fechas distintas, filas duplicadas y claves extra. Produce un **registro de Threads por stdout**; no modifica datos públicos.
- [tests/test_gpt_metricool_threads.py](../../../../tests/test_gpt_metricool_threads.py): **17/17 PASS**, ejecutados localmente el 22/10/2026 con `python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v`. Hashes Git de los dos archivos probados contrastados con sus hashes en la rama; mismo código. No es el CI general del sitio.

### Contrato de entrada: envoltorio privado sobre la respuesta MCP

El MCP entrega únicamente `{"rows":[["123456.0","20261021"]]}` para una métrica en ese día; para no confundir campos ni fechas, quien exporte el resultado debe envolverlo **localmente**, sin IDs de marca ni tokens:

~~~json
{
  "metrics": ["THEV01"],
  "from": "2026-10-21",
  "to": "2026-10-21",
  "rows": [["123456.0", "20261021"]]
}
~~~

**123456 es una cifra ficticia.** No registrar snapshots reales en Git ni compartir tokens. Reproducir:

~~~bash
python -m unittest discover -s tests -p 'test_gpt_metricool_threads.py' -v
python scripts/research/gpt_metricool_threads.py /ruta/privada/threads.json
~~~

Salida: `id=threads`, `followers` (entero o `null`), `observed_at` (día de la métrica), `source=metricool-mcp-export`, `generated_at`, `status` y las dos métricas de vistas como `null`. **Un contador ausente no se convierte en cero**. La salida no es el documento agregado `data/social-metrics.generated.json`; requiere el compositor central de #699 antes de mostrarse en #704.


## Ampliación probada: ocho contadores en una consulta (22/10/2026)

**Evidencia del conector Metricool conectado:** se consultaron los catálogos `evolution` de ocho redes y todos los campos siguientes aparecen como `dataAggregation=LAST`:

| Red | Campo de seguidores |
|---|---|
| Bluesky | `BKEV01` |
| Threads | `THEV01` |
| Instagram | `IGEV01` |
| Facebook **Page Followers** | `FBEV17` |
| TikTok | `TKEV07` |
| Pinterest | `PIEV09` |
| YouTube **Subscribers** | `YTEV01` |
| X/Twitter | `TTEV01` |

Se ejecutó **una consulta MCP real** para el 21/10/2026 completo (Europe/Madrid), con esos 8 campos y en ese orden. Respuesta constatada: **1 fila, 9 columnas: ocho cadenas numéricas no nulas + fecha `20261021`**. No se incluyen los valores privados de la cuenta. Esto **prueba que el conector puede entregar esas ocho métricas juntas para ese día**, NO que las ocho identidades públicas de la web estén ya confirmadas, ni que el MCP pueda ejecutarse en modo cron.

**Código entregado (sin paquetes externos):**
- [scripts/research/gpt_metricool_followers.py](../../../../scripts/research/gpt_metricool_followers.py), nuevo importador multired: lee la exportación local, exige ID de campo reconocido, prohíbe campos de vistas/alcance, duplicados, fechas contradictorias, filas de longitud errónea y metadatos adicionales. **Reutiliza el validador ya probado `gpt_metricool_threads.py`** para fechas y enteros. Emite solo `{"kind":"metricool-follower-candidates","schema_version":1,"requested_day":"...","records":[...]}` a stdout, sin escribir en la web.
- [tests/test_gpt_metricool_followers.py](../../../../tests/test_gpt_metricool_followers.py), **18/18 pruebas locales PASS** en Python con archivos cuyos hashes Git coinciden con la rama (los dos scripts y este test). Datos de prueba sintéticos; contrato de API real contrastado por separado. La anterior suite de 17 casos de Threads sigue en la rama, sin modificar.

### Uso reproducible

Consulta a través del MCP autorizado con `getAnalyticsDataByMetrics`, período local 21/10/2026 00:00–23:59:59 (+02:00) y `metrics` exactamente en el orden elegido. Envolver la respuesta `rows` localmente con los mismos IDs:

~~~json
{
  "metrics": ["BKEV01","THEV01","IGEV01","FBEV17","TKEV07","PIEV09","YTEV01","TTEV01"],
  "from": "2026-10-21",
  "to": "2026-10-21",
  "rows": []
}
~~~

`rows=[]` es una **muestra sin datos** deliberada: el importador informa de registros parciales, no de seguidores cero. **En una ejecución real sustituir solo `rows` por la respuesta obtenida, sin publicar valores ni IDs de marca en Git**.

~~~bash
python -m unittest discover -s tests -p 'test_gpt_metricool_followers.py' -v
python scripts/research/gpt_metricool_followers.py /ruta/privada/export-8-redes.json
~~~

### Puerta de integración de identidad

La PR #704 acepta ya **seis perfiles elegibles**, pero solo **cuatro registros de este lote**: Threads, Instagram, TikTok y Pinterest. El 22/10/2026 se cotejaron los identificadores `networksData` de la marca conectada con `autor.html` y `scripts/build-site-shell.py`; las cuatro cuentas coinciden. Bluesky sigue leyendo su API AppView propia, Mastodon sigue usando su API pública. **Facebook no se promueve**: el ID de red conectado no coincide directamente con la URL de página publicada. **X no figura conectado a la marca**; YouTube tiene identificador de canal en Metricool, pero no consta la URL en los enlaces públicos del sitio comprobados. El importador multired no incluye URLs ni IDs privados, y no sustituye una verificación de cuenta.

**Beneficio práctico contrastado:** se puede investigar qué ocho contadores proporciona la marca desde **una petición MCP** con el mismo código y una única revisión del contrato. La extracción sin intervención, el transporte a GitHub y la publicación de esas ocho redes siguen pendientes.

**Integración incremental ya preparada:** la [PR #704](https://github.com/davidpd89/web-escritor/pull/704) acepta el resultado completo (`metricool-follower-candidates`) y selecciona **Threads, Instagram, TikTok y Pinterest**, cuyas identidades se confirmaron frente a la web. Mantiene Bluesky con su lectura pública de #706 y descarta Facebook/X/YouTube del lote por identidad no suficientemente contrastada. El enlace entre los módulos se ha probado localmente con **35 casos en total** (18 del lector multired, 7 de integración local y 10 de contrato del nuevo lote). **Esto no es una prueba del proceso automático de extracción ni de las 8 identidades.** La receta de checkout temporal, sin merge, queda en `ux.md` de #704.

## Puerta de integración: lo que funciona y lo que NO

**Demostrado:** existencia y semántica `LAST` de `THEV01` en catálogo, llamada de lectura real con una fecha, estructura exacta de 2 columnas, normalización sin conexión y los 17 casos offline. Al simplificar, se eliminó toda obligación de consultar `THEV06`.

**Pendiente:** comparación del valor contra la interfaz de Metricool, entrega automatizada y autorizada del resultado al servidor, gestión de fallos/caducidad (se recomienda ocultar contador si no hay lectura reciente). No escribir `data/social-metrics.generated.json` desde este importador ni ejecutar Actions antes de aprobarlo.

**Coste y automatización:** [Metricool confirma](https://help.metricool.com/es/planes-complementos-y-acceso-a-la-api-explicados-xux1u) que **MCP está disponible incluso en Free**; la API HTTP independiente exige Advanced o Custom. Por tanto, NO escribir hoy un cron que dependa de un token API inexistente. [La guía oficial de conexión MCP](https://help.metricool.com/es/como-conectar-el-mcp-de-metricool-eqp9h) incluye clientes externos, entre ellos Make. El siguiente experimento sería una única llamada `MCP Client → Call a tool` desde Make, autorizada por OAuth, revisando retorno y créditos. **No se ha ejecutado ese piloto; no se puede prometer refresco automático.**

**Fuente de código público:** la funcionalidad de lectura la presta el **MCP oficial de Metricool**, cuyo servidor está documentado públicamente; no hemos clonado ni copiado un SDK comunitario sin necesidad, y el importador es código propio de Python estándar. La documentación de Metricool declara un repo `metricool/mcp-metricool`, pero el acceso a esa URL devolvió 404 durante esta investigación: no se ha considerado fuente de código verificable.

### Entrega a Claude

Antes de merge, **solo** ejecutar lectura de un día terminado, cotejar seguidores en Metricool, decidir el transporte backend y validar caché/caducidad. Si se adopta Make, primero prueba manual y después recurrencia; si falla el piloto, continuar con Bluesky/Mastodon públicos sin inventar una API de pago. Mantener PR separadas, no tocar `main` y ejecutar suite/Actions únicamente cuando el usuario lo autorice.
