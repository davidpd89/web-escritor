# Clasificación: infantil primero, sin temporadas, segunda opinión de GPT aplicada — 2026-11-23

## Origen
«El lago de los monstruos (INFANTIL)» salía como Terror (y se anunció así en Telegram). La palabra «terror» venía de las
categorías de Amazon; no había regla de coherencia en la web (solo un filtro de canal en Telegram).

## Cambios
- `scripts/reading_taxonomy.py`
  - Fuera las temporadas (Halloween, Navidad, Verano, San Valentín, Día de la Madre/Padre): reglas y derivadas. `drop_seasons`
    las retira de los datos en cada pasada, así que no vuelven.
  - `repair_children_genres`: un libro infantil (sin público juvenil) pierde Terror, Romance, Romantasy, Amor y pareja y
    Poesía (salvo que el título hable de poemas/versos/rimas). Corre en cada carga y en cada alta (idempotente).
  - `category_priority`: «infantil» va el primero en etiquetas.
  - `apply_second_opinion`: aplica `data/reading-classification-gpt.json` (público infantil que faltaba, género que falta;
    quita un género de ficción que solo respaldaba el título). Solo con discrepancia y motivo.
- `scripts/reading-texts.py`: la segunda opinión ya no se queda en `.local`; `publish` la lleva a
  `data/reading-classification-gpt.json` (permitido en `publish-reading-refresh.py`). `discrepancias` lee ambos.
- `scripts/reading_telegram.py`: el género principal de un libro infantil es «Infantil y juvenil».
- `scripts/build-reading-catalogue.py`: sin tipo «temporada» (tipos, prioridad, keywords del JSON-LD).
- Datos: `data/reading-catalogue.json` reparado (962 libros tocados; temporadas 0; terror 155→145; poesía 336→323;
  amor y pareja 46→44).
- Tests: nuevo `tests/test_reading_taxonomy_children.py` (incluye guardia sobre el catálogo real: ningún infantil con género
  de adultos, ninguna temporada); Telegram; derivadas/taxonomía actualizadas; fixtures sin «halloween».

## Añadido después
- `last_resort_genre`: ningún libro publicado se queda sin género (había 23, también en main): tema aunque solo lo pusiera un
  nodo, título de actividades/colorear/pegatinas, cuentos/monstruos → infantil, rama del tema → narrativa/ensayo.
  Guardia en el catálogo real (`test_published_catalogue_has_no_adult_genre_on_children_or_seasons`, ya en `DATA_CONTRACTS`).
- Carril de contenido: `data/reading-classification-gpt.json` añadido a `CONTENT_GLOBS` y a los 8 workflows.
- CI: el gate superó 45 min una vez (saturación de Actions, no un test); `Tool engine tests` falla en main desde el 22/10.
- Sonar: duplicación 59,7 % por las páginas regeneradas (inherente a regenerar el catálogo).

## Verificado
- `test_reading_taxonomy_children`, `_derived`, `test_reading_taxonomy`, `test_reading_telegram`: 63 OK.
- `test_reading_pinterest_rss`: 10 OK.

## Pendiente / no comprobado
- Artefactos generados (fichas, catálogo, pagefind): ver estado del PR.
- La segunda opinión de GPT solo existe para libros nuevos y no hay datos publicados aún (el archivo local no existía):
  no se sabe cuántas veces discrepa. Para los ~5.900 libros ya con texto haría falta un modo «clasificar» barato
  (prompt solo de clasificación); hoy los cubre la regla determinista.
- Rediseño P0 de GPT (20/11: recalcular facetas desde evidencias, sin acumular; Thema/ONIX): sin implementar.
- Casos dudosos que se quedan: infantiles de monstruos que podrían merecer «Halloween» — ya no existe esa etiqueta.
