# Catálogo de lectura: automatización editorial

Implementación inicial de PR #661, ampliada en [#665](https://github.com/davidpd89/web-escritor/pull/665) y con recuperación de cargas antiguas en [#676](https://github.com/davidpd89/web-escritor/pull/676).

## Un solo ciclo diario

`reading-catalogue-sync.yml` se ejecuta a las 06:30 UTC cuando `READING_INTAKE_ENABLED=true`. `data/reading-intake-config.json` permite detener la ingesta (`enabled`) o su publicación (`autopublish`). El disparo manual admite `dry_run=true`.

1. Descubre fichas en las páginas públicas de novedades e inicio de Penguin Libros España. Es la primera fuente conectada; no representa todos los libros de España ni todas las altas de Amazon.
2. Comprueba robots, limita el ritmo a 1,5 segundos y el presupuesto a 80 solicitudes físicas. Reutiliza respuestas con caducidad. Los candidatos incompletos se aplazan tres días.
3. Extrae los datos de la edición seleccionada: ISBN-13, URL canónica, idioma, región, autores completos, sello, fecha, encuadernación, páginas y portada. Conserva un extracto de sinopsis editorial de hasta 24 palabras con fuente enlazada, separado de los datos técnicos. Una ficha sin sinopsis válida no se incorpora ni sustituye la sinopsis anterior.
4. Admite sellos existentes en `data/editoriales.json`, con alias explícitos. El estado de recepción de manuscritos no determina si puede recomendarse un libro del sello.
5. Añade como máximo cinco obras por ejecución y revisa hasta dos fichas automáticas cuya comprobación tenga siete días. Cada candidato pasa el validador real del catálogo completo en un entorno aislado. Un fallo no elimina fichas publicadas ni detiene otros candidatos válidos.
6. Clasifica por materias y edades declaradas, preservando etiquetas manuales y exclusiones revisadas. Optimiza la cubierta auténtica a WebP con variantes de 320 y 800 px. No inventa imágenes ni presupone licencia abierta para Pinterest.
7. Genera ficha, perfil del autor, enlaces con editoriales, registro de contenido, mapa plegable, sitemap y Pagefind. Refresca como máximo siete biografías editoriales breves por día dentro del presupuesto HTTP; una biografía verificada se conserva hasta su revisión mensual. No inventa datos personales y mantiene las biografías manuales.
8. Crea una PR de artefactos generados. Ejecuta las pruebas reales del commit y respeta las reglas de `main`, sin `--admin`. Después de fusionar solicita Pages y espera el despliegue y smoke de producción del commit exacto. IndexNow recibe el intervalo real de cambios.

Se reutiliza el coordinador de publicación del radar. Las operaciones con `GITHUB_TOKEN` requieren disparos explícitos de CI y Pages; no basta con crear la PR o fusionar. Véase la [documentación de GitHub](https://docs.github.com/en/actions/concepts/security/github_token).

Una PR automática actual se reanuda antes de descubrir otro lote. Si quedó detrás de main, el escritor comprueba autoría del bot y rutas exclusivamente generadas, conserva la propuesta y su rama como referencia, cierra esa propuesta antigua y regenera el lote desde las fuentes con el código actual. No cierra propuestas humanas ni acepta cambios de código en el lote. Las comprobaciones se vuelven a ejecutar sobre el nuevo commit; un fallo de pruebas o despliegue deja evidencia y hace fallar la tarea.

## Identidad y actualizaciones

- ISBN y obra normalizada evitan duplicados; categorías y formatos comparten una URL. Las URLs existentes permanecen estables.
- Coraline y las biografías manuales revisadas se mantienen fijadas. Drive sigue siendo opcional y su importador conserva los libros editoriales con registro de ingesta.
- La revisión conserva enlaces de compra verificados, reseñas y fragmentos añadidos. Cambios de cubierta o autoría quedan pendientes y mantienen la ficha publicada anterior.
- `Novedad` usa la fecha completa de publicación en el día civil de Madrid: desde su publicación hasta antes de cumplir 15 días. La detección o revisión no reinicia el plazo. Años o meses incompletos no reciben un día inventado. Hay filtros de 15/30/90/180 días y próximos 30 días.
- Procedencia y estado están en `data/reading-intake-state.json`. Los cuerpos HTTP solo van a caché de Actions. Los informes factuales duran siete días como artifacts y no contienen secretos o snapshots privados de Drive.

## Amazon, Goodreads y audio

La ingesta editorial no requiere Creators API ni clave de Google Books. Después de la ingesta, el mismo escritor actualiza diariamente valoraciones y consulta los precios de Amazon cuando existen las credenciales. Los fallos de un proveedor no impiden consultar los demás ni renuevan la fecha de datos antiguos. El ciclo no llama a ningún LLM ni API de pago.

Amazon es el destino de compra. Se conservan los productos/ASIN y formatos verificados. Sin producto comprobado aparece **Buscar este ISBN en Amazon**, con `davidporto-21`: una búsqueda no acredita stock, precio ni existencia del producto. Nunca se transforma un ISBN en ASIN supuesto. La identificación de afiliación está en el criterio editorial del pie común.

Goodreads se consulta por ISBN desde su ficha pública, sin fingir acceso a su antigua API. Se comprueban ISBN, título y autor. Hardcover y Google Books son proveedores independientes y atribuidos, con sus secretos en GitHub. El piloto real de 26 libros del 21/10/2026 obtuvo 15 valoraciones de Goodreads y una de Hardcover para 15 libros distintos; Google Books respondió 503. No se inventan puntuaciones para los libros sin coincidencia. La evidencia y límites están en [acceso a proveedores](qa/catalogue-provider-access-2026-10-21.md).

Creators API tiene adaptador diario y secretos configurados, pero la prueba real sigue sin acceso elegible y no hay precios publicados. No basta con crear una aplicación o credenciales. Solo se admiten ofertas EUR de compra nueva, formato/edición verificados y fecha vigente; se excluyen suscripciones, usado y promociones exclusivas. `assets/reading-market.json` limita ofertas a 24 horas y valoraciones a siete días. Los controles sin datos válidos se ocultan.

Audio y fragmentos están retirados de la interfaz de todas las fichas para mantener el catálogo homogéneo. El MP3 de Elvira, los archivos y datos anteriores de Coraline permanecen para no romper URLs. **`generate_audio=false`**: no se descargan ni narran automáticamente capítulos ajenos.

Pinterest conserva el recorrido pin → ficha web → Amazon. El código de #662 y sus siete feeds forman parte del único escritor diario, incluso cuando no hay libros nuevos, pero `rss_enabled=false`: no se han conectado tableros ni publicado pines. Véase [flujo RSS](pinterest-rss-libros-2026-10-20.md). Las reseñas locales solo se publican si son auténticas, consentidas y aprobadas; el formulario y la hoja privada no están conectados.

## Operación y comprobaciones

```sh
python -m unittest discover -s tests -p 'test_reading*.py' -v
python tests/test-reading-publication.py
python tests/test-radar-publication.py
python scripts/reading_intake_pipeline.py --live --max-new 5
# En checkout limpio, con GH_TOKEN y dependencias instaladas:
python scripts/refresh-reading-catalogue.py --publish
```

La prueba inicial de #661 incorporó 20 libros reales de ocho sellos, además de Coraline. #665 se publicó con 26 libros y se verificaron sus 106 archivos públicos exactos, cinco resoluciones, filtros, test, pestañas nuevas, sitemap plegado y funcionamiento sin JavaScript. La carga diaria añade como máximo cinco obras por ejecución; el número vigente y la evidencia del ciclo completo se consultan en Actions y las PR automáticas.

La paginación muestra 24 resultados y filtra el catálogo completo; el HTML conserva todas las fichas para navegación sin JavaScript e indexación. Los escenarios de 100/200 libros pasan, pero no prueban rendimiento ilimitado: el gate global de todas las rutas tarda unos 40–45 minutos. La propuesta para repartirlo sin omitir rutas ni debilitar controles está [registrada en la PR](https://github.com/davidpd89/web-escritor/pull/665#issuecomment-6315095933). No se promete ausencia absoluta de errores futuros ni cobertura exhaustiva.
