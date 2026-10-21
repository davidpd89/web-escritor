# Catálogo de lectura: automatización editorial

Implementación de PR #661, sobre las fichas y el diseño ya publicados por #660.

## Un solo ciclo diario

`reading-catalogue-sync.yml` se ejecuta a las 06:30 UTC cuando `READING_INTAKE_ENABLED=true`. `data/reading-intake-config.json` permite detener la ingesta (`enabled`) o su publicación (`autopublish`). El disparo manual admite `dry_run=true`.

1. Descubre fichas en las páginas públicas de novedades e inicio de Penguin Libros España. Es la primera fuente conectada; no representa todos los libros de España ni todas las altas de Amazon.
2. Comprueba robots, limita el ritmo a 1,5 segundos y el presupuesto a 80 solicitudes físicas. Reutiliza respuestas con caducidad. Los candidatos incompletos se aplazan tres días.
3. Extrae los datos de la edición seleccionada: ISBN-13, URL canónica, idioma, región, autores completos, sello, fecha, encuadernación y portada. No importa sinopsis comerciales, precios ni reseñas de clientes.
4. Admite sellos existentes en `data/editoriales.json`, con alias explícitos. El estado de recepción de manuscritos no determina si puede recomendarse un libro del sello.
5. Añade como máximo cinco obras por ejecución y revisa hasta dos fichas automáticas cuya comprobación tenga siete días. Cada candidato pasa el validador real del catálogo completo en un entorno aislado. Un fallo no elimina fichas publicadas ni detiene otros candidatos válidos.
6. Genera texto bibliográfico propio mediante plantilla y clasifica por materias y edades declaradas. Optimiza la cubierta auténtica a WebP con variante de 320 px. No inventa imágenes ni presupone licencia abierta para Pinterest.
7. Genera ficha, perfil bibliográfico del autor, enlaces con editoriales, registro de contenido, mapa del sitio, sitemap y Pagefind. Los perfiles no inventan biografías o fechas de nacimiento.
8. Crea una PR de artefactos generados. Ejecuta las pruebas reales del commit y respeta las reglas de `main`, sin `--admin`. Después de fusionar solicita Pages y espera el despliegue y smoke de producción del commit exacto. IndexNow recibe el intervalo real de cambios.

Se reutiliza el coordinador de publicación del radar. Las operaciones con `GITHUB_TOKEN` requieren disparos explícitos de CI y Pages; no basta con crear la PR o fusionar. Véase la [documentación de GitHub](https://docs.github.com/en/actions/concepts/security/github_token).

Una PR automática abierta se conserva y se reanuda antes de descubrir otro lote. Si está detrás de main, se solicita su actualización normal, sin resolver conflictos a ciegas. Un fallo de pruebas, conflicto o despliegue deja evidencia y hace fallar la tarea.

## Identidad y actualizaciones

- ISBN y obra normalizada evitan duplicados; categorías y formatos comparten una URL. Las URLs existentes permanecen estables.
- Coraline y las biografías manuales revisadas se mantienen fijadas. Drive sigue siendo opcional y su importador conserva los libros editoriales con registro de ingesta.
- La revisión conserva enlaces de compra verificados, reseñas y fragmentos añadidos. Cambios de cubierta o autoría quedan pendientes y mantienen la ficha publicada anterior.
- `Novedad` usa la fecha completa de publicación en el día civil de Madrid: desde su publicación hasta antes de cumplir 15 días. La detección o revisión no reinicia el plazo. Años o meses incompletos no reciben un día inventado. Hay filtros de 15/30/90/180 días y próximos 30 días.
- Procedencia y estado están en `data/reading-intake-state.json`. Los cuerpos HTTP solo van a caché de Actions. Los informes factuales duran siete días como artifacts y no contienen secretos o snapshots privados de Drive.

## Amazon, Goodreads y audio

La ingesta editorial no requiere Creators API ni clave de Google Books. Sus adaptadores permanecen separados para futuras ampliaciones; el ciclo no llama a ningún LLM ni API de pago.

Amazon es el destino de compra. Se conservan los productos/ASIN y formatos verificados. Sin producto comprobado aparece **Buscar este ISBN en Amazon**, con `davidporto-21`: una búsqueda no acredita stock, precio ni existencia del producto. Nunca se transforma un ISBN en ASIN supuesto. La identificación de afiliación está en el criterio editorial del pie común.

Las nuevas fichas enlazan a una búsqueda de reseñas por ISBN en Goodreads. Eso no equivale a una reseña, puntuación importada o conexión a su API. El snapshot puntual de Coraline caduca el 27/10/2026; los filtros de estrellas se desactivan si no quedan valoraciones vigentes. Precios y ofertas siguen sin proveedor conectado. `assets/reading-market.json` conserva la caducidad de 24 horas para ofertas y siete días para valoraciones.

Coraline conserva su MP3 Elvira y fragmento oficial. `scripts/reading_audio.py` reutiliza narraciones por hash de texto propio, pero **`generate_audio=false`**: el proveedor rechazó las nuevas narraciones en esta prueba. No se muestran reproductores vacíos ni se sustituye Elvira por otra voz. No se descargan ni narran automáticamente capítulos ajenos.

Pinterest conserva el recorrido pin → ficha web → Amazon. Esta ingesta no publica pines ni concede derechos sobre las cubiertas para otros usos. La integración RSS/Pinterest de otras PR se incorpora por separado.

## Operación y comprobaciones

```sh
python -m unittest discover -s tests -p 'test_reading*.py' -v
python tests/test-reading-publication.py
python tests/test-radar-publication.py
python scripts/reading_intake_pipeline.py --live --max-new 5
# En checkout limpio, con GH_TOKEN y dependencias instaladas:
python scripts/refresh-reading-catalogue.py --publish
```

La prueba inicial incorpora 20 libros reales de ocho sellos, además de Coraline. El informe de QA de esta fase documentará CI y producción. No se promete ausencia absoluta de errores futuros ni cobertura exhaustiva.
