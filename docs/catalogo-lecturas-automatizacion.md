# Libros recomendados: piloto y automatización

## Ya implementado

- Archivo de Cuaderno: seis artículos originales y dos guías de lectura, con temas integrados como accesos contextuales. Se mantienen las URLs previas.
- Libros recomendados: buscador y filtros al inicio, una ficha por obra, categorías combinables, portada local optimizada y metadatos de libro. Piloto real: Coraline, ISBN 9788498382372.
- Reseñas, fuentes, fragmento y datos bibliográficos en desplegables nativos. El capítulo se abre en la fuente editorial; no se convierte automáticamente un texto ajeno a audiolibro.
- MP3 de la sinopsis original de Coraline con Elvira, español de España. Generación editorial con `scripts/build-reading-audio.py`; dependencia fijada en `scripts/requirements-reading-audio.txt`. Audio estático con nombre ligado al hash del texto y la voz, sin depender del navegador del lector.
- `scripts/import-reading-sheet.py`: adapta las pestañas actuales `01_LIBROS`, `02_CATEGORIAS`, `03_PORTADAS`, `04_ENLACES`, `05_FUENTES`. Conserva un snapshot y separa revisión editorial de datos recibidos. Se puede repetir; un libro sin aprobación entra como borrador y no se publica.
- `scripts/discover-reading-books.py`: adaptador de Creators API para buscar candidatos en Amazon.es. OAuth EU, búsquedas acotadas, deduplicación por ASIN, errores explícitos, salida temporal. No descarga imágenes ni mezcla resultados con fichas publicadas.

## Qué hace falta para la tarea diaria

Estado comprobado el 20/10/2026: aplicación `DavidPortoCatalogoLibros` creada; credenciales EU guardadas en GitHub Secrets y autenticación OAuth correcta. La consulta real a un producto devuelve HTTP 403 con el mensaje de cuenta no elegible. Amazon indica diez ventas válidas en treinta días y posible revisión de hasta 48 horas tras crear credenciales. No se promete habilitación automática ni se simulan resultados. La tarea diaria deja un informe `pending_amazon_eligibility` y volverá a probar; otros errores de autenticación o servicio sí hacen fallar la tarea.

El workflow `reading-catalogue-sync.yml` queda instalado pero condicionado a `READING_INTAKE_ENABLED=true`. No se considera conectado hasta validar sus credenciales con una ejecución real.

1. Amazon Afiliados: acceso aprobado a Creators API y credenciales EU. Guardar `AMAZON_CREATORS_CLIENT_ID` y `AMAZON_CREATORS_CLIENT_SECRET` como secretos del repositorio; `AMAZON_PARTNER_TAG=davidporto-21` como variable. No guardar claves en el Drive ni en Git. Un tag de afiliado no concede acceso a la API.
2. Drive privado: cuenta de servicio con acceso de lector solo a esta hoja y Workload Identity Federation para GitHub. Variables `READING_GOOGLE_PROVIDER` y `READING_GOOGLE_ACCOUNT`. No hay que publicar la hoja ni descargar cookies de tu sesión.
3. Activar y ejecutar manualmente el workflow una vez. La ejecución diaria propuesta es 06:30 UTC. Produce una bandeja de revisión de la hoja y Amazon, guardada un día como artifact privado de GitHub. **Esta tarea no hace push a main ni publica candidatos sin revisión.** Una propuesta aprobada se aplica al dataset, se generan las páginas y pasa por la CI de publicación.

El siguiente paso para reducir la revisión a la hoja es incorporar la aprobación editorial y las fuentes de uso en una pestaña específica; el importador actual conserva esa aprobación en `data/reading-import-review.json`. No es necesario reconstruir el catálogo ni copiar HTML para cada libro.

## Por qué no «todos los libros subidos en las últimas 24 horas»

Creators API ofrece búsquedas y páginas de resultados, con máximo diez resultados por solicitud y diez páginas. `NewestArrivals` ordena resultados; no es una suscripción exhaustiva a todas las altas ni acredita la hora de publicación editorial. «Visto por primera vez hoy» y «publicado hoy» son datos distintos. El adaptador no afirma una cobertura completa.

Para una cobertura fiable por editorial conviene combinar fuentes ONIX/RSS/API o catálogos autorizados de esas editoriales con Amazon como destino de compra. Guardar ISBN, editorial, fuente y fechas evita duplicar reediciones y presentar libros antiguos como novedades. Una fecha discrepante permanece sin precisión inventada: Coraline muestra 2009 y queda fuera de novedades.

Las condiciones de Amazon no permiten convertir en permanentes las imágenes de su API mediante descarga y recompresión a WebP/AVIF. Por eso este piloto usa una cubierta editorial identificada, con procedencia y contexto de uso, y la bandeja Amazon no persiste imágenes. Si se integra contenido de Amazon en la web se debe implementar su ciclo de actualización/caducidad antes de mostrarlo. No se copian reseñas ni valoraciones como contenido propio.

Referencias oficiales: [SearchItems y límites](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/search-items), [OAuth EU](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/get-started/using-curl), [licencia de contenido](https://afiliados.amazon.es/help/operating/policies), [autenticación Google para GitHub](https://github.com/google-github-actions/auth).

## Campos para pedir a ChatGPT y añadir al Drive

Mantén las pestañas existentes. Añade una pestaña **08_REVISION** con estas columnas para una futura aprobación desde la propia hoja:

`libro_id, estado, descripcion_original_confirmada, fuente_bibliografica_url, fecha_verificacion, portada_edicion_verificada, autorizacion_o_base_uso, portada_fecha_revision, fecha_publicacion_verificada, fuente_publicacion_url, edad_recomendada, fuente_edad_url, avisos_contenido, lectura_personal_confirmada, evidencia_lectura, fecha_actualizacion`

Estados: `borrador`, `listo`, `publicado`. No marcar «leído» ni inventar permisos o fuentes. Hasta conectar esta pestaña, su equivalente permanece en el JSON de revisión.

Campos útiles adicionales, opcionales y con fuente:

- **Edición:** traductor, ilustrador, título original, año original, formato, páginas e idioma. No mezclar datos de distintas ediciones.
- **Series:** serie, número y si puede leerse de forma independiente. Ayuda a elegir un orden de lectura.
- **Contenido y edad:** orientación editorial, temas sensibles e intensidad. Evitar deducir edades a partir del género.
- **Valor editorial propio:** por qué encaja en cada categoría, a qué lector puede interesar y qué lo distingue. Es más útil que acumular enlaces o copiar la sinopsis comercial.
- **Muestras y audio:** URL oficial, alcance autorizado y, si existe, audio autorizado con narrador y licencia. La disponibilidad de un capítulo gratis no implica permiso para redistribuirlo o narrarlo.
- **Pinterest:** título del pin, descripción original, URL canónica de la ficha, portada y procedencia. Los pines enlazan primero a la ficha de esta web.
- **Seguimiento:** primera detección, última verificación y estado de revisión, separados de la fecha real de publicación. No se imprimen notas privadas en las fichas.

Estos campos pueden incorporarse gradualmente al contrato. No generan automáticamente nuevas páginas de categorías ni preguntas frecuentes: se indexan fichas y colecciones con contenido propio suficiente. Los metadatos Book, breadcrumbs, enlaces internos y fuentes verificables ayudan a describir el contenido a buscadores y sistemas de IA, sin prometer posiciones ni menciones.
