# Catálogo de lecturas · fase 1 · 20 de octubre de 2026

Implementación en la PR #659, que permanece en borrador sin fusionar ni desplegar, conforme al apartado 8 del encargo. Validación local; no se han disparado Actions manuales ni cargas de Drive/Pinterest.

- `/cuaderno/` conserva sus seis artículos. Navegación contextual: Artículos / Recomendaciones de lectura. Temas sigue enlazado desde el archivo y las recomendaciones, con sus rutas y colecciones intactas.
- `/recomendaciones/` es el catálogo extensible; inicialmente vacío, con las dos guías y la política editorial conservadas. Se mantienen las 210 URLs del sitemap; solo se actualiza la fecha editorial del hub.
- Fuente JSON, relaciones múltiples y generación estática de fichas. No hay fichas ni portadas ficticias públicas. Datos sintéticos únicamente en pruebas aisladas. Contrato de Sheets documentado en `docs/catalogo-lecturas-contrato-drive.md`.
- Libro: portada local, clasificación, datos y fuentes, metadatos Book/WebPage/BreadcrumbList, enlaces de reseñas externas y fragmento oficial, lectura de descripción y enlace afiliado opcional con divulgación. No se incorporan reseñas inventadas, precios ni automatización de Pinterest.
- Cache busting: navegación interior JS 4, shell JS 18 y nuevos assets versionados/hash lock. Los numerosos cambios de referencias HTML corresponden al import de navegación compartida y su actualización de caché.

## Validación

- 112 contratos Python aprobados: batería general y repetición en copia limpia de los controles afectados por archivos locales de diagnóstico o acceso concurrente en Windows. La prueba nueva comprueba estados, categorías múltiples, duplicados, ISBN, imágenes, rutas, fuentes, afiliación, escapes, metadatos y sitemap.
- 49 contratos Node aprobados. Se actualiza el contrato de Cuaderno para exigir exactamente las dos entradas acordadas; se conservan los requisitos de las demás familias.
- Recomendaciones: tres rutas, siete tamaños, sin errores de consola/recursos, sin desbordamientos y CLS ≤ 0,1. Se corrigió la aparición tardía del formulario para reservar su espacio desde el HTML inicial.
- Catálogo: 320/390/768/1440 px; estado vacío, filtros combinados, búsqueda con tildes, teclado, restauración por fragmento, novedades por fecha y caducidad de la selección, URL única en varias categorías, ficha, detener voz y navegación sin JavaScript. Las fichas de prueba se interceptan solo en el contexto de QA.
- Cuaderno: trece tamaños y aislamiento de artículos; temas/colección conservados. Paridad del menú contextual en 203 páginas.
- Generadores de catálogo, shell, contexto, sitemap y Pagefind; cobertura de navegación, descubrimiento global, evidencia editorial, ámbito de scripts, versiones de assets y presupuesto de rendimiento verificados. Pagefind conserva 207 páginas elegibles.

Las capturas y logs locales se guardan en `.ci/reading-catalogue/`, `artifacts/recommendations/` y `.ci/reading-clean-results/`; no forman parte del artefacto publicado. La copia limpia se utiliza para evitar que comprobadores históricos que recorren todo el disco incluyan HTML descargados de fuentes o perfiles del navegador. No se ha modificado ni relajado esa política en esta PR.

Antes de publicar: ejecutar la CI habitual y revisar el contenido definitivo. Esta entrega prepara la infraestructura y permite empezar la recopilación de libros con un contrato estable; la importación masiva y Pinterest son fases posteriores.
