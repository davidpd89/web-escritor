# Viajes literarios · contrato preliminar de datos y Google Sheets (v0.1)

**Estado:** diseño; ninguna hoja Drive creada ni sincronizador activado. El catálogo de libros sigue siendo autoridad sobre obras/ediciones y afiliados. Cuando un libro exista allí, registrar reading_book_id y no duplicar portada ni ISBN.

## 1. Claves y normalización

Claves inmutables, independientes de etiquetas traducidas: destino_id (dst-...), lugar_id (lug-...), obra_id (obr-...), autor_id (aut-...), relacion_id (rel-...), fuente_id (fue-...), ruta_id (rut-...). Usar slug SEO editable con historial de redirección. Desambiguar homónimos de ciudades con país/región, de librerías con sede y de obras con autor/edición. Un POI existe una vez aunque aparezca en muchos filtros o sagas. Coordenadas WGS84 decimales; geocodificación solo para ubicaciones concretas comprobadas. País ISO-3166-1 alfa-2, idioma BCP-47, fechas ISO-8601 exactas únicamente cuando consten.

## 2. Hojas sugeridas (cabeceras literales por validar antes de importador)

**01_DESTINOS** — una fila por ciudad/ámbito geográfico:
destino_id | slug | nombre | pais_iso2 | region | localidad | tipo_destino | lat_centro | lon_centro | precision_centro | intro_original | estado | fuente_id | fecha_verificacion | fecha_revision | fecha_publicacion | notas_internas
Una ciudad NO implica que cada punto pertenezca geográficamente al centro; definir región/polígono o parent_destino_id si procede.

**02_LUGARES** — entidad física con ficha y datos editoriales:
lugar_id | slug | nombre | nombre_alternativo | destino_id | pais_iso2 | direccion_publica | lat | lon | precision_geo | tipo_lugar | resumen_original | historia_original | motivo_visita_original | visitabilidad | coste_acceso_texto | accesibilidad_verificada | sitio_oficial_url | reserva_oficial_url | url_mapa_externa | osm_id | wikidata_qid | imagen_id_principal | estado | fecha_verificacion | fecha_revision | notas_internas
Tipos: libreria, biblioteca, museo, archivo, casa_museo, monumento, calle, plaza, edificio, paisaje, festival, escenario, otro. Si no se puede fijar posición precisa, lat/lon vacíos y precision_geo=ciudad/zona/sin_localizar. Visitabilidad: interior_visitable, exterior, requiere_reserva, no_visitable, desconocida. No publicar tarifas/horarios permanentes copiados como estáticos; si se muestran, guardarlos en tabla de datos variables con caducidad y fuente. URL externa de reservas solo si es página real verificada, nunca generada por patrón.

**03_OBRAS** — referencia bibliográfica, no reemplaza catálogo:
obra_id | reading_book_id | titulo_canonico | autores_texto | autor_id_principal | tipo_obra | saga | wikidata_qid | openlibrary_work_id | google_books_volume_id | isbn_referencia | estado | fuente_bibliografica_id | notas_internas
Las adaptaciones pueden registrarse como tipo_obra=adaptacion_audiovisual y obra_original_id; verificar el medio y fechas. ISBN identifica edición, no obra.

**04_AUTORES** — entidad editorial y vínculos públicos:
autor_id | nombre | slug | openlibrary_author_id | wikidata_qid | bio_original | web_oficial_url | estado | fecha_verificacion | notas_internas
Sin campo «dirección donde vive». Casas-museo y espacios históricos se relacionan mediante 05_RELACIONES con tipo adecuado.

**05_RELACIONES** — la tabla más importante; una fila por afirmación verificable:
relacion_id | lugar_id | obra_id | adaptacion_obra_id | autor_id | ruta_id | tipo_relacion | descripcion_original | capitulo_o_referencia_sin_cita | nivel_evidencia | estado | spoiler | fuente_id_principal | fecha_verificacion | fecha_revision | revisado_por | notas_internas
No exigir obra_id para librería/biblioteca de interés intrínseco, pero sí al menos un sujeto válido en relaciones literarias. Reglas distintas: ambientacion_literal requiere obra_id; rodaje_adaptacion requiere adaptacion_obra_id; vida_autor_publica requiere autor_id; fuentes atribuyen LA RELACIÓN, no solo existencia del POI.
Niveles: primaria (texto o creador/institución relevante), oficial (autoridad/institución), secundaria_contrastada, popular_sin_contrastar. El nivel NO debe confundirse con una probabilidad matemática de la IA; el estado verificado exige revisión humana. La atribución popular puede quedar rechazada.

**06_FUENTES** — bibliografía y rastro de comprobación:
fuente_id | url | titulo | entidad_emisora | tipo_fuente | licencia_datos | uso_permitido | fecha_publicacion_fuente | fecha_consulta | resumen_evidencia_propias_palabras | ubicacion_evidencia | verificacion_manual | estado_enlace | ultima_comprobacion | notas_internas
Admite tablas de unión adicionales 06B_RELACION_FUENTES: relacion_id | fuente_id | papel (principal/corroboracion/refutacion); una sola fuente por fila no basta para relaciones controversiales. No almacenar largos textos protegidos.

**07_RUTAS** — recorrido curado:
ruta_id | slug | titulo | destino_id | introduccion_original | tipo_ruta | nivel_esfuerzo | medio_sugerido | duracion_verificada_min | duracion_fuente_id | visible_spoilers | estado | fecha_verificacion | notas_internas

**08_RUTA_PARADAS** — orden y comentario por parada:
ruta_id | lugar_id | orden | motivo_original | orden_en_narrativa | tramo_transporte_verificado | fuente_id
Integridad de pares ruta_id + orden y ruta_id + lugar_id; ruta no tiene por qué coincidir con la cronología narrativa.

**09_IMAGENES** — inventario autorizado:
imagen_id | lugar_id | url_origen | ruta_local | autor_foto | licencia | enlace_licencia | atribucion_requerida | modificaciones | ancho | alto | fecha_revision | estado_derechos | alt_original
Estado derechos explícito: pendiente, valido, rechazado. Imágenes sin derecho justificable NO salen en la exportación pública; atribuir según licencia.

**10_CAMBIOS_Y_REVISIONES** — histórico interno:
cambio_id | entidad_tipo | entidad_id | campo | valor_anterior | valor_nuevo | quien_reviso | fecha | motivo | enlace_fuente | estado
El historial puede implementarse con commits y/o una tabla; evitar exposición web de nombres privados y notas editoriales.

Se podría simplificar a 6 pestañas iniciales (Destinos, Lugares, Obras, Relaciones, Fuentes e Imágenes) y activar Autores/Rutas/Paradas/Revisiones cuando haya volumen. La separación de **RELACIONES y FUENTES** no es opcional.

## 3. Estados, requisitos y publicación

Estados editoriales: **propuesto → investigando → listo_para_revision → aprobado → publicado**, más **rechazado**, **suspendido**, **retirado**. No permitir salto a publicado por autocompletar con IA.
Para lugar público: ID/slug único, destino activo, categoría válida, descripción ORIGINAL, ubicación con precisión honesta, hecho cultural principal y su fuente, fecha de verificación, al menos una relación cultural explícita o tipo biblioteca/librería de interés propio. Para una asociación obra-lugar: un vínculo con tipo, afirmación limitada, URL que verdaderamente sustente esa conexión y verificación individual; las relaciones no aprobadas se omiten. Autor: cero domicilios privados. Para imagen: licencia y créditos válidos.

Cualquier enlace no verificado, selector desconocido, HTML inyectado o valor de prueba provoca rechazo/omisión, nunca publicación por defecto. Un elemento eliminado conserva tombstone y se evalúa su URL/redirect para no crear 404 inútiles.

## 4. Exportación prevista: Sheets → snapshot → web (NO en esta PR)

- Propuesta de arquitectura: IA/humano generan **candidatos** con fuentes concretas → curación en Sheets → validador/importador de futuro script → snapshot JSON privado de campos editoriales y JSON público reducido → generador de páginas estáticas → gates de QA → revisión y despliegue autorizado.
- No dar al frontend una clave ni leer Sheets desde el navegador. No convertir el Drive en backend de cada visita. Una llamada al modelo puede preparar un borrador de afirmaciones, nunca declararlas verificadas.
- Para automatización futura usar Google Sheets API autenticada y permisos mínimos (o exportación aprobada), lecturas por lotes, paginación/reintentos, caché, trazabilidad, diff, gate de cambios y snapshot estable. No escribir secretos en Git. Evitar dos cronjobs que editen la misma rama; integrar en la publicación existente **solo cuando se autorice**.
- Un trabajo de actualización revalida vínculos rotos, cambios de visita, cierres definitivos, licencias de foto y cambios editoriales; no modifica contenido público sin pasar control. Una fecha de alta no equivale a fecha de verificación.
- Contrato de versión: schema_version y generated_at en cada exportación, source_sheet_revision o hash cuando sea viable; importación determinista, normalización de locales/decimales, IDs estables y errores detallados por fila. Sanitizar celdas peligrosas para fórmula al exportar CSV.

## 5. Caducidad por campo (hipótesis que validaremos)

- Relación entre libro y lugar: revisar anualmente o por alerta de refutación.
- Datos de visita, entradas y horarios: 30–90 días según criticidad; preferible enlazar información oficial en vez de duplicarla.
- Existencia de librería/evento y accesibilidad: revisar cada 60–180 días o tras cambios.
- Enlaces e imágenes: comprobación técnica periódica y auditoría de licencia editorial; no equiparar HTTP 200 con autorización.
La frecuencia real debe basarse en coste/volumen y fuentes. Las fechas no se simulan.

## 6. Ejemplos de filas propuestas, NO VERIFICADAS Y NO PUBLICABLES

- Destino: Madrid / España, estado=propuesto.
- Lugar: Barrio de las Letras, categoría zona/barrio, estado=investigando; sin coordenada puntual exacta.
- Libro: Juego de tronos, estado=propuesto; si un sitio es rodaje de adaptación se relaciona con esa adaptación, no automáticamente con libro.
- Lugar: librería histórica de París, nombre [[pendiente]], estado=propuesto, sin fotografía ni horarios.
Ningún ejemplo constituye afirmación de inspiración, rodaje, dirección o visita hasta tener fuente contrastada.

**Enlaces relevantes internos:** data/atlas-literario.json; docs/catalogo-lecturas-contrato-drive.md; data/reading-catalogue.json; data/content-registry.json; data/navigation.json.
