# Open Library Works dump — extractor local de candidaturas

**PR hija de #666.** Dependencias lógicas: [#667](https://github.com/davidpd89/web-escritor/pull/667) (fuentes) y [#669](https://github.com/davidpd89/web-escritor/pull/669) (modelo). No incluye sus commits.

Fuente: [Open Library dumps](https://openlibrary.org/developers/dumps) y [recomendación oficial de usar dumps para volumen](https://openlibrary.org/data).

Archivos: scripts/atlas_openlibrary_dump_candidates.py y tests/test_atlas_openlibrary_dump_candidates.py. No descargan nada. El lector acepta volcado local TSV de works de 5 columnas, comprimido gzip o sin comprimir; procesa en streaming, filtra subject_places, conserva work ID y autor IDs, y emite únicamente datos de CANDIDATOS. No extrae el texto de las novelas, imágenes ni descripciones protegidas.

Modo seguro por defecto: examina hasta 100.000 filas y devuelve como máximo 100 candidatos; muestra solo estadísticas si no se proporciona --output. Para guardar JSONL se exige --output con ruta nueva y se rechaza sobrescritura. Se puede pasar --place Paris --place London y límites --max-rows/--max-candidates. Cualquier salida es investigación interna, jamás dataset publicable.

**Limitación crítica:** limitar a primeras 100.000 filas NO representa una muestra mundial aleatoria. Para cobertura global en P6 hará falta checkpoint/cursor o proceso continuo de todo el stream acotando tiempo/espacio, no repetir siempre el principio. Los archivos de Open Library ocupan varios GB; guardar los dumps fuera de GitHub/CI. No hay cron creado ni API llamada.

**Advertencia de evidencia:** subject_places puede indicar tema geográfico, y NO demuestra escenario literal ni calle; relationship_type se fija a unverified_subject_place. No publicar sin cruzar fuente primaria, QID correcto y aprobación editorial. La licencia de reutilización masiva de metadatos tiene que revisarse por separado.

QA futuro autorizado: python -m unittest discover -s tests -p 'test_atlas_openlibrary_dump_candidates.py'. Tests creados, NO EJECUTADOS. Validación pendiente contra fragmento real del dump, condiciones de licencia, esquema #669 y reanudación global.

Estado: sin acciones sobre main, web, Pages, cron ni Amazon; no hacer merge automático.
