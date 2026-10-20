# Catálogo: navegación, formatos y filtros — 20/10/2026

Validación local del cambio de la PR 660:

- Contratos de datos, renderizado determinista e importador de Sheets: pasan.
- Catálogo en 320, 390, 768 y 1440 px; filtros combinados, reset, URL, teclado, audio y navegación sin JavaScript: pasan.
- 27 combinaciones de tamaño, texto al 200 % y espaciado personalizado, más 12 casos con todos los acordeones abiertos y el pie común: sin desbordamiento horizontal.
- Ofertas sintéticas aisladas del catálogo público: precio y descuento del mismo formato, ordenación, fechas, umbrales de Goodreads, caducidad, fuentes inválidas, monedas no admitidas y conservación de UTM: pasan.
- Destinos reales de los cuatro formatos de Coraline con el tag existente, perfil local de autor, fuente Wikipedia y una identificación de afiliación en el pie: pasan.
- Sitemap: 212 URLs. Búsqueda local: 209 páginas. Fuentes locales y perfiles de navegador excluidos del sitemap con prueba de regresión.
- Artefacto público: contiene el JSON comercial necesario y excluye el dataset privado de autores/revisión.
- Baselines de las ocho rutas representativas en tres tamaños capturados en Ubuntu mediante Actions. Se mantienen los umbrales existentes.

## Comprobación de rendimiento

Lighthouse del catálogo en Actions confirmó accesibilidad 100, SEO 100 y CLS 0. El rendimiento varió entre ejecuciones (57–72 en dos capturas del mismo código de producto; la versión anterior marcaba 83). No se trata como una garantía de rendimiento ni se relajan los límites.

Para investigar se compararon tres cargas frías por variante en Chromium, 390×844, latencia 150 ms, descarga 160.000 bytes/s y CPU ×4, sin red externa:

| Variante | LCP en las tres cargas (ms) | Mediana (ms) |
| --- | --- | --- |
| Main anterior, 17e91e62 | 2664, 2644, 2428 | 2644 |
| Catálogo nuevo antes de precargar fuentes | 2988, 3652, 2788 | 2988 |
| Catálogo nuevo con precarga de fuentes existentes | 2524, 2760, 2612 | 2612 |

Se incorpora la precarga de Instrument Serif y Manrope ya utilizadas, sin añadir fuentes ni cambiar su política de visualización. La mejora observada corresponde a este ensayo local; debe contrastarse con CI y con visitas reales. Ninguna de estas cargas solicita MP3. El audio de descripción conserva `preload="none"`.

## Límites reales de los datos

No se publican precios ni descuentos: falta una fuente autorizada actualizable. Los controles se habilitan cuando existen ofertas vigentes. Goodreads procede de una consulta puntual, con fuente, votos y caducidad de siete días; no se simula una API ni se atribuye como reseña propia. El fragmento de Coraline permanece en la fuente editorial: narrarlo requiere autorización. La tarea de Amazon continúa informando de elegibilidad pendiente, sin publicar candidatos inventados.
