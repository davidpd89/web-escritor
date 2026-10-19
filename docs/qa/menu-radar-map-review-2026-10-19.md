# Revisión de menú, radar y mapa · 19 de octubre de 2026

## Incidencias corregidas

- Home: la protección antigua de foco impedía abandonar `lrb-compact` cuando el botón de Explorar conservaba el foco. El botón ya permanece visible en ambos estados; se elimina el bloqueo. La prueba de regresión falla antes del cambio y pasa después.
- Radar: el reloj del cliente se calculaba una sola vez. Ahora se revisa cada minuto y al recuperar una pestaña suspendida o restaurada. Se actualizan estados, filtros, contador y secciones sin recargar ni perder la búsqueda.
- Automatización: las PR nocturnas creadas con `GITHUB_TOKEN` no iniciaban los checks normales; auto-merge quedaba esperando. La tarea ejecuta ahora diez workflows mediante `workflow_dispatch`, espera resultados del SHA exacto y comprueba además los seis jobs obligatorios. Publica sus resultados reales como estados del commit, enlazados al job, porque las ejecuciones dispatch no se asocian a la pestaña de checks de la PR. Solo después solicita una fusión normal, sin bypass. Cualquier fallo mantiene la PR abierta y falla la tarea. Tras fusionar solicita Pages explícitamente, ya que el push del bot tampoco dispara Pages.
- Mapa humano: las 150 fichas editoriales quedan en un `details` nativo cerrado inicialmente. El enlace al directorio sigue visible; no se elimina ningún enlace HTML ni URL del sitemap XML.
- Enlaces externos: JANUS devuelve 403 al robot de GitHub, pero sus bases responden 200 en GET y Chromium normales; se documenta una excepción exacta. Para informes que solo contienen tiempos agotados o 500/502/503/504 se añade una segunda comprobación mediante cURL/IPv4, limitada a esas URL. Exige un 2xx real tras seguir redirecciones. Cualquier 4xx, error no temporal, informe desconocido o reintento fallido conserva el fallo; no se aceptan estados finales nuevos ni se excluyen dominios.
- Elena Santiago: la comprobación independiente identifica que la noticia del ILC agota el tiempo también fuera de GitHub. Se sustituye por el PDF oficial firmado que enlaza esa misma noticia y responde 200. Se vuelven a contrastar fecha, premio, extensión y requisitos territoriales/de trayectoria; sigue vencida y fuera del calendario activo.
- Getafe Negro: la noticia del festival responde 200 en navegación normal, pero GitHub no consigue conectar por TLS ni con cURL/IPv4. Se usa la página oficial de Escuela de Escritores, coorganizadora, con la edición XIX, el mismo plazo y el formulario de participación. Se contrasta de nuevo el contenido; no se añade una excepción de red para esta fuente.

## Evidencia y alcance

- Regresión de Explorar a 390, 768 y 1440 px: scroll con menú abierto, cierre con botón/Escape/fondo, foco y posición de lectura, recuperación posterior del masthead. Incluye el manejador de fondo cuando el diálogo ocupa toda la pantalla.
- Doce casos de caducidad en navegador: medianoche de Madrid en CET, CEST y ambos cambios de hora, mediante temporizador, `visibilitychange` y `pageshow`; visitante en Los Ángeles y filtros conservados.
- Funcionalidad de recursos: 150 editoriales, 85 convocatorias abiertas y 13 en seguimiento a la fecha de revisión. Las cinco pendientes de verificación siguen fuera del calendario.
- Cobertura de Drive: 162 filas contrastadas con 157 destinos públicos. Se mantienen los criterios de verificación, la retención de vencidas y los calendarios generados existentes.
- Prueba del coordinador: cada workflow fallido impide fusión y despliegue; se rechaza un job omitido aunque el workflow termine en verde; no se aceptan resultados de otro SHA ni ejecuciones antiguas.
- Revisión visual y de teclado del mapa, con los enlaces presentes y el desplegable funcional sin JavaScript.

Las bases externas pueden cambiar. La caducidad sigue el día civil de Madrid; los horarios específicos de las bases se conservan en las fichas. Una ejecución nocturna detenida por CI no publica artefactos nuevos: los lectores con JavaScript siguen protegidos por el reloj del cliente y la ejecución queda fallida para revisión. No se promete funcionamiento futuro absoluto a partir de una batería de pruebas.

Referencias de plataforma: [GITHUB_TOKEN y eventos](https://docs.github.com/en/actions/concepts/security/github_token), [estados reales de commits](https://docs.github.com/en/rest/commits/statuses), [enlaces rastreables de Google](https://developers.google.com/search/docs/crawling-indexing/links-crawlable).
