# #708 · Threads — integración sin duplicar la fuente ni inventar visualizaciones

**22/10/2026, hija de #699.** La implementación útil de seguidores se encuentra en [#705 Metricool](https://github.com/davidpd89/web-escritor/pull/705); el contrato de salida está implementado y probado en [#704](https://github.com/davidpd89/web-escritor/pull/704). **No duplicar esos archivos en esta PR ni introducir OAuth de Meta sin pruebas**.

## Problema detectado y corrección

La primera versión de este documento proponía:

~~~python
"views_30d": metricool_record.get("THEV06")
~~~

Esa equivalencia era injustificada y **queda expresamente anulada**. [Metricool distingue las métricas de publicaciones creadas durante el periodo de las visualizaciones producidas durante él](https://help.metricool.com/es/diferencia-entre-posts-publicados-y-posts-vistos-en-el-periodo-2pwtf). En el catálogo real, `THEV06` es `Threads Evolution > Post Views`, pero no está demostrada su equivalencia con «visualizaciones que ocurrieron en estos últimos 30 días». `THEV11` corresponde a visitas al perfil y tampoco sustituye las vistas de publicaciones. El código de #705 ya **no consulta `THEV06`**.

## Camino de integración comprobado, concreto

1. URL de cuenta: `https://www.threads.com/@davidportodiaz`, verificada contra `autor.html` y `scripts/build-site-shell.py`.
2. El conector Metricool conectado identifica `THEV01` como seguidores, agregación **LAST**; una consulta de **un único día cerrado** devolvió una fila `[contador_texto_decimal, YYYYMMDD]`. La cuenta no necesita una ventana de 30 días para saber sus seguidores.
3. **Usar, sin copiar ni reimplementar:** `scripts/research/gpt_metricool_threads.py` de #705 (17 pruebas offline, normalización de `THEV01` a entero o `null`). Escribe un registro `{"id":"threads","followers":N,"observed_at":"YYYY-MM-DD","source":"metricool-mcp-export","status":"ok"}` y campos de vistas explícitamente nulos.
4. Tras fusionar las ramas en la padre **cuando el usuario autorice**, pasar ese registro al compositor `scripts/research/gpt_social_compose.py` de #704, que comprueba identidad, fecha local de cierre, caducidad y cobertura. Su salida sigue siendo un borrador en `/tmp`; el publicador automático y la página web no se han creado.

Reproducción, desde la futura rama integrada que contenga #705 y #704:

~~~bash
python -m unittest discover -s tests -p test_gpt_metricool_threads.py -v
python -m unittest discover -s tests -p test_gpt_social_compose.py -v
python scripts/research/gpt_metricool_threads.py /ruta/privada/threads.json > /tmp/threads-normalized.json
python scripts/research/gpt_social_compose.py /tmp/threads-normalized.json > /tmp/social-metrics-preview.json
~~~

`N` representa una cifra obtenida, **no un dato de ejemplo para publicar**. El fichero de entrada debe provenir de una extracción privada con `["THEV01"]` y un día local cerrado. No guardar identificadores de marca, tokens, respuesta bruta ni datos personales de analítica en GitHub.

## Ruta alternativa Meta — todavía NO aceptada

[API oficial de Threads, colección Meta](https://www.postman.com/meta/threads/) y [endpoint Post Insights](https://www.postman.com/meta/threads/request/34203612-385abc7d-b3cc-4e5d-9937-ebbe7174e041). Son referencias reales, pero **aún no está probado** que la cuenta disponga de token/scope autorizados, permisos válidos y dato de seguidores equivalente a `THEV01` para su extracción desatendida. Por tanto, no añadir clientes OAuth ni copiar ejemplos de publicación de contenido: sería código no probado y redundante.

**Gate concreto para Claude:** comparar seguidores `THEV01` contra la interfaz real de Metricool; validar extracción MCP automatizada (piloto Make documentado en #705) y el transporte privado; aplicar el contrato de #704; si se desea visualizaciones, primero demostrar una métrica de *actividad generada dentro de la ventana*, no «posts publicados en ventana». No crear un segundo colector de Threads hasta probar que aporta un campo importante no cubierto.

No se ha ejecutado ninguna prueba nueva en la rama #708, creado workflow, actualizado el sitio o hecho merge. Las pruebas antes citadas están en sus respectivas PR. No afirmar integración end-to-end.
