# Auditoría de la PR #660 antes de ejecutar #661 — 20/10/2026

**Objetivo:** congelar el contrato del catálogo publicado para que la futura ingesta masiva lo reutilice, sin retroceder los cambios de la PR #660 ni desplegar fichas incompletas.

## Comprobado sobre código real

- PR #660 **fusionada** al commit `c3c98a74e7a930347d6514a89b484cbe2b993416`, con controles visuales y funcionales descritos en `docs/qa/catalogo-lecturas-fase-2-2026-10-20.md`. La PR #661 ya ha sido sincronizada con este commit de `main` (merge de dos padres), sin tocar producción.
- Ficha principal `Coraline`: ISBN-13 `9788498382372`, tapa blanda, 160 páginas; edición de junio de 2009 contrastada con https://www.agapea.com/libros/Coraline-9788498382372-i.htm y https://www.casadellibro.com/libro-coraline/9788498382372/1258566 . No inventar fecha diaria si la fuente solo indica mes/año.
- `scripts/build-reading-catalogue.py` comprueba ISBN, obras duplicadas, categorías múltiples, portada local y dimensiones reales, texto original marcado, enlace de compra con tag, URLs canónicas, imágenes OpenGraph y datos estructurados Book/BreadcrumbList/WebPage.
- En `render_book`, portada clicable con `url_amazon_afiliada`, bloque de compra con `formatos_compra` individualizados, fragmento enlazado a la editorial, audio de descripción y reseñas externas si existen; el perfil Neil Gaiman está en `data/reading-authors.json`.
- `assets/reading-catalogue.js` invalida ofertas tras 24 horas y ratings tras 7 días; el JSON `assets/reading-market.json` tiene rating de Coraline con fecha final 27/10/2026. **No es bug del filtro**: desaparecerá si no se refresca, y el usuario ya sabe que Goodreads no tiene actualización autónoma. No basar una ficha en un rating efímero.
- Validación de navegador de #660 prueba 3 tamaños, selección de formatos, URLs afiliadas, rating caducado, UTM, botones y perfiles. **No se ha efectuado aquí una auditoría propia completa con navegador en producción**: las evidencias independientes proceden del código y GitHub/QA de #660.

## Aspectos que #661 DEBE resolver antes de publicar muchos libros

### P0. No bloquear todo el lote por un candidato incompleto

`validate(data, root)` actualmente valida todas las fichas `listo/publicado` y falla globalmente si falta una portada, hay bytes de cubierta duplicados, descripción repetida, ISBN erróneo, metadatos desconocidos o link Amazon inadecuado. Esto es correcto para proteger el catálogo **publicado**, pero en ingesta automática obliga a **aislar cada libro en staging**: validar/enriquecer candidato por candidato y pasar a `data/reading-catalogue.json` solo registros compatibles. Una candidata inválida **no debe impedir publicar las demás**. No relajar las reglas globales como solución rápida.

### P0. Fuente autor/editorial + perfil escalable

`data/reading-authors.json` contiene actualmente **solo Neil Gaiman**. `author_records()` exige una descripción biográfica verificable, fecha de nacimiento y fuentes; y `main()` genera páginas solo para autores de esa lista. Los nuevos autores sin ficha manual pueden aparecer en `autores` de un libro, **pero no obtendrán página individual automáticamente**. La fase #661 debe implementar un generador de perfiles opcional a partir de datos bibliográficos comprobados, sin inventar nacimiento/biografía, o permitir que el libro se publique aunque su autor todavía no tenga perfil. No generar una página vacía por nombre.

Las 150 páginas de `editoriales/` también deben relacionar automáticamente libros por `slug` de `data/editoriales.json`: el catálogo usa el campo de editorial como texto y **el render actual no actualiza por sí solo la página del sello**. Verificar vínculo real por nombre canónico, no por grupo editorial ambiguo.

### P0. Amazon: búsqueda por ISBN aún NO es compatible con el builder

`scripts/reading_intake_core.py` de #661 puede construir `https://www.amazon.es/s?k=<isbn>&tag=...` con `tipo=busqueda_isbn`, pero **el validador de la PR #660 rechaza expresamente una URL de búsqueda en `url_amazon_afiliada`**. `formatos_compra[]` también exige /dp/ASIN con `tag`.

Codex debe **evolucionar el contrato sin romper Coraline**: usar una propiedad explícita `amazon_destino_tipo=busqueda_isbn|producto_verificado` (o equivalente) y un campo URL de compra tipado; solo los ASIN verificados deben mostrarse como «Comprar / Ver este formato»; una búsqueda se rotula `Buscar este ISBN en Amazon`. Nunca presentar el resultado de búsqueda como producto específico garantizado. Si el libro solo tiene `formatos_compra` pero no `url_amazon_afiliada`, hacer la portada clicable hacia un formato principal si corresponde, o mostrar una portada no clicable coherente con la ficha.

La prueba de Coraline usa distintos productos reales para cuatro formatos, **pero** los `fuente_url` de `tapa-dura`, `ebook` y `audiolibro` siguen apuntando al ASIN de la tapa blanda. Es un problema de trazabilidad editorial **interno**, aunque los `url` de compra sean distintos. Corregir el campo fuente por formato al cargar más libros. Además, las distintas ediciones tienen ISBN y años propios: por ejemplo, tapa dura de Coraline ISBN `9788478885794` (2003), distinto del ISBN de la portada principal. Referencia: https://www.iberlibro.com/buscar-libro/isbn/847888579x/ .

### P1. Fechas y novedades

El filtro actual de JavaScript `isNew()` usa una ventana de **180 días**, no los listados dinámicos deseados de 30/90 días y 30 días de próximos lanzamientos. `Coraline` solo guarda `anio_publicacion=2009`, no una fecha `fecha_publicacion` diaria; eso es **correcto** para evitar convertir su incorporación a la web en «novedad».

#661 debe conservar precisión de fecha (año/mes/día) y habilitar nuevos filtros por **fecha editorial de edición** solo cuando esté comprobada al día. La fecha de captación (`first_seen`) no demuestra lanzamiento. No mezclar `fecha_actualizacion` (sitio) con fecha de edición (libro). Preservar el comportamiento JS en ausencia de datos y la canonical en URL sin filtros.

### P1. SEO y filtros a escala

Revisar al menos **20 libros reales, cinco sellos, múltiples categorías**, y que `render_hub`, fichas, perfiles, `data/content-registry.json`, sitemap y Pagefind permanezcan coherentes después de cada lote. Evitar duplicar obras por edición, ISBN/autor, o registrar como novedad una reedición de hace años. No generar páginas triviales sin descripción propia o datos bibliográficos.

### P2. Valoraciones Goodreads y precios

Actualmente `assets/reading-market.json` no contiene precios activos y la única valoración caduca en siete días. Eso es esperado. No bloquear ingesta por carecer de Goodreads ni precios. Mantener los filtros de precio deshabilitados mientras no haya proveedor y actualización autorizados; evitar llamar a GPT por libro para simularlo.

## Nueva prueba que se añade a la PR #661

`tests/test_reading_intake_multibook_contract.py`: **3 libros ficticios solo en memoria/directorio temporal**, 3 ISBN válidos, 3 portadas de distinta imagen, seis relaciones de categorías y opciones de eBook con tag, sin llamadas externas. Verifica 3 páginas con canónicas propias, 1 catálogo común, 3 entradas de registro, bloqueo de obra duplicada aunque cambie ISBN, rechazo de portada ausente y que un libro en borrador no impida las otras dos. Ejecuta **el generador auténtico de #660**, no una imitación.

El workflow `.github/workflows/reading-intake-qa.yml` instala ahora `scripts/requirements.txt` y ejecuta esta prueba junto a los tests previos de ingesta. **No declarar su aprobación hasta ver la ejecución CI terminada**.

## Orden para Codex

1. Confirmar QA de PR #660 en `main` y corregir cualquier fallo nuevo de la suite; PR #661 ya está sincronizada con ella.
2. Implementar normalizador `candidato → ficha validable` y aislamiento por libro, con test real de al menos 3 libros y luego 20 candidatos verificados.
3. Resolver el contrato de **enlaces afiliados de búsqueda** vs ASIN comprobado.
4. Añadir relaciones automáticas con autores/editoriales sin exigir biografías inventadas; nuevas fichas listas con páginas de autor cuando haya datos suficientes.
5. Completar portadas, fechas, fragmentos, render/sitemap/Pagefind, un solo commit incremental, deploy de Pages y comprobar producción.
6. En segunda fase integrar PR #662 RSS, hacer piloto Coraline y verificar pin → web → Amazon; cero llamadas a modelos en tareas programadas.

**Veredicto:** #660 es una base adecuada para comenzar #661, **no** una demostración de autosuficiencia para cientos de libros todavía.
