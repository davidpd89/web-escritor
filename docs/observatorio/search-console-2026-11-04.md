# Revisión de Search Console — 4 de noviembre de 2026

Propiedad: `sc-domain:davidportodiaz.com`. Lectura de la sesión autenticada
existente en Edge, `127.0.0.1:9221`. Base del repositorio: `b1567c4`.
Esta revisión corresponde a Search Console y la web pública; no audita las
otras cuentas del observatorio. No contiene cookies ni credenciales.

## Resultado y correcciones

No hay acciones manuales ni problemas de seguridad. La propiedad figura como
verificada. El sitemap está correcto y se leyó el 4 de noviembre: 1.138 URLs.
HTTPS muestra 43 URLs HTTPS, cero no HTTPS y ningún problema crítico.

En los informes detallados sí aparecen avisos no críticos que el resumen no
expone:

1. **Perfil de autor:** un `ProfilePage` con `dateCreated` y `dateModified`
   de precisión de día, rechazados por el parser de Google, que espera
   `DateTime`. La corrección mantiene esas fechas editoriales en `WebPage`
   y da al perfil un nodo propio enlazado, sin fechas opcionales de precisión
   desconocida. Ambos conservan la misma entidad de autor. No se inventan
   horas ni se adelanta `lastmod` por esta reparación de metadatos.
2. **Eventos:** cinco representaciones de las firmas pasadas de Madrid y
   Aranjuez, repartidas entre agenda, ferias y crónica, publicaban `Offer`
   sin URL de entradas ni disponibilidad. Dos tampoco tenían `validFrom`.
   Se retiran esas ofertas de los eventos históricos. Se conserva
   `isAccessibleForFree`, las fechas, ubicaciones y `EventScheduled` histórico.
   No se afirma que queden entradas ni que se agotaran. La información visible
   de gratuidad permanece intacta. Esto no promete eliminar todo aviso opcional:
   Google puede recomendar `offers` incluso en un evento archivado; no se debe
   crear una oferta ficticia para conseguir un contador a cero.

Referencias: [ProfilePage de Google](https://developers.google.com/search/docs/appearance/structured-data/profile-page)
y [Event de Google](https://developers.google.com/search/docs/appearance/structured-data/event).

## Cobertura: resumen antiguo frente a inspección individual

El resumen de páginas indica actualización del **23 de octubre**, con 150
indexadas y 216 excluidas: 6 `noindex`, 3 redirecciones, 69 rastreadas sin
indexar y 138 descubiertas sin indexar. Sus ejemplos incluyen rastreos
posteriores a la fecha indicada en la cabecera: no tratar el conjunto como
una fotografía temporal coherente ni como un inventario completo de fallos.

La inspección individual realizada en esta sesión confirma **«La URL está
en Google» / «La página está indexada»** para:

- `/`
- `/autor.html`
- `/las-manecillas-del-recuerdo/`
- `/las-manecillas-del-recuerdo/fragmentos/`
- `/libros/`
- `/libros/samuel-entre-mundos/`
- `/cuaderno/`
- `/herramientas/`
- `/lectores-beta/`
- `/lectores-beta/enviar-manuscrito/`
- `/editoriales/alfaguara/`
- `/recomendaciones/autores/alice-austen/`
- `/recomendaciones/libros/la-vida-nueva-de-pedrito-de-andia-9788467083354/`

Las dos rutas de lectores beta ya son indexables en producción, y Google
las tiene indexadas aunque sigan entre los seis ejemplos antiguos de `noindex`.
Las otras cuatro (`/asistente/`, aviso legal, privacidad y política de
recomendaciones) mantienen su exclusión deliberada. No se ha quitado
`noindex` ni solicitado una validación global que incluiría esas exclusiones.
Las inspecciones son una muestra: **no prueban que las 207 páginas de las
otras dos categorías estén todas indexadas**.

## Otros informes

- Vídeos: el único ejemplo es el fondo decorativo de la portada,
  `hero-tinta-david-porto.mp4?v=2`. La portada está indexada; no se convierte
  en una página de visualización solo para indexar su fondo.
- Rutas de exploración: 35 válidas, cero no válidas.
- Eventos: 5 válidos, cero no válidos; avisos opcionales descritos arriba.
- Perfil: 1 válido, cero no válidos; dos avisos de fechas descritos arriba.
- Reseñas: cero elementos válidos y cero no válidos; no equivale a un fallo.
- Core Web Vitals: sin datos suficientes de usuarios reales. No atribuir
  calificación buena, mala ni una mejora cuantificada.
- Rastreo (actualización 2/11): unas 3.700 solicitudes, 49,6 MB y 77 ms de
  respuesta media. El host tuvo problemas históricos de DNS y robots.txt;
  el detalle indica **porcentaje de error aceptable actualmente** en ambos,
  y conectividad del servidor aceptable. No se modifican DNS ni robots.txt
  basándose en una incidencia pasada que ahora no se reproduce.

## Rendimiento y oportunidades

| Periodo observado | Clics | Impresiones | CTR | Posición media |
|---|---:|---:|---:|---:|
| 3/8–2/11/2026 | 352 | 18.900 aprox. | 1,9 % | 14,5 |
| 6/10–2/11/2026 | 233 | 13.000 aprox. | 1,8 % | 11,2 |

No son periodos de igual duración: no calcular crecimiento comparando
directamente estas dos filas. El panel destaca más impresiones para Carolina
Lapausa. Entre las consultas de 28 días: «treinta y cuatro libro» tiene
166 impresiones y un clic; «enviar manuscrito a editorial planeta», 62 y uno.
Son oportunidades para estudiar intención y posición por consulta, no prueba
de títulos defectuosos ni motivo para prometer subidas de CTR. No se han
reescrito fichas ni inventado contenido para responder al estado antiguo.

## Verificación ejecutada

Antes de los cambios, sobre la web publicada:

- `node qa/production-metadata-artifacts-audit.mjs`: PASS; 1.144 rutas HTML,
  450 imágenes sociales y 7 archivos de descubrimiento/datos.
- `node qa/production-global-integrity-audit.mjs`: PASS; 1.144 rutas,
  sitemap y respuestas 404 reales.
- `node qa/production-http-semantics.mjs`: PASS; 33 rutas, HEAD, 404 y medios.
- `node qa/production-url-alias-canonical.mjs`: PASS; 7 alias `index.html`.
- `node qa/production-jsonld-link-integrity.mjs`: PASS; 1.166 bloques,
  1.142 fuentes y 1.593 URLs propias referenciadas.

Son comprobaciones de producción durante esta sesión, sin fijar
`EXPECTED_RELEASE_SHA`; no prueban que la corrección local esté desplegada.

Tras las correcciones locales:

- Regresión de `ProfilePage`: el checker rechaza fechas de día tanto con
  tipo simple como múltiple, y acepta DateTime o ausencia de fecha opcional.
- Cinco nodos históricos: sin ofertas, conservando gratuidad y estado.
- 13 pruebas de calendarios; paridad factual entre agenda y ferias;
  gratuidad respaldada en el texto; rechazo de cronologías inversas.
- Semántica temporal: PASS sobre 1.142 archivos y 1.166 bloques JSON-LD.
- Sitemap: PASS, mismas 1.138 URLs; no requiere regeneración.
- Entidades canónicas: PASS, 910 entidades coherentes.
- Breadcrumbs: PASS; solo tres avisos informativos preexistentes por marcado
  opcional ausente, sin defectos de integridad.
- Metadatos SEO e índice de enlaces internos: PASS antes de la reparación;
  cero errores y cero avisos en el grafo, 1.138 páginas indexables.

## Cierre después de publicar

1. Comprobar que producción contiene el perfil separado y ya no contiene
   ofertas en los cinco eventos archivados.
2. Probar la URL publicada de `/autor.html` y comprobar el nuevo perfil.
   Solicitar rastreo si sigue mostrando la versión anterior.
3. Revisar perfil y eventos después del siguiente rastreo. Usar «Validar
   corrección» solo para una incidencia realmente resuelta y publicada;
   no validar como resuelta la falta de ofertas en todo el archivo histórico.
4. No declarar el contador de cobertura corregido hasta que Google actualice
   el informe. Si una URL concreta sigue fuera, inspeccionarla individualmente
   y decidir a partir del motivo vigente.

No se han enviado solicitudes de indexación redundantes ni cambiado
configuraciones de las cuentas. El siguiente rastreo y la indexación final
dependen de Google.
