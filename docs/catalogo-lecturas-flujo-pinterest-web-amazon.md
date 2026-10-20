# Flujo editorial y técnico: Pinterest → ficha de libro → Amazon.es

**Decisión del propietario · 20/10/2026**  
Complemento de la [PR #659](https://github.com/davidpd89/web-escritor/pull/659) y de `docs/catalogo-lecturas-automatizacion.md`.  
**Fuente maestra:** [Google Sheets «Catálogo de recomendaciones de lectura»](https://docs.google.com/spreadsheets/d/1hHtp-B66CdnXgV6IT7ClcLGLxLUw8tKOLQThVD5KHCs/edit).

## 1. Objetivo no negociable: dos clics, dos destinos

El flujo buscado es **Pinterest → davidportodiaz.com → Amazon.es con afiliación**.

1. **Pinterest.** Una persona encuentra un pin temático sobre un libro. La imagen del pin puede contener una **portada auténtica de la edición correcta**, integrada en una composición visual adecuada para Pinterest. El **enlace de destino del pin** es **SIEMPRE la ficha individual del libro en nuestra web** (`https://davidportodiaz.com/recomendaciones/libros/<slug>/`). El pin **NO enlaza directamente a Amazon**.
2. **Ficha en davidportodiaz.com.** Muestra **título, autor, portada, breve descripción propia, categorías múltiples, datos editoriales, reseñas y fragmentos cuando existan**. El lector puede leer la información sin necesidad de comprar ni salir inmediatamente de la web.
3. **Amazon.es.** **Solo si el visitante decide pulsar voluntariamente** en la portada de la ficha web o en el botón «Ver/Comprar en Amazon», se abre **el producto concreto en Amazon.es con el tag de afiliado del propietario**. Imagen y botón deben apuntar al mismo ASIN/edición revisada.

**La portada de Pinterest y la portada de la ficha web son dos recursos/instancias diferentes, aunque visualmente puedan mostrar la misma edición del mismo libro.** Lo que cambia no es el ISBN ni la identidad de la cubierta, sino el origen técnico de la imagen, el contexto y el enlace que se acciona.

### Ejemplo piloto actual: Coraline

- Libro: `LIB-0001`, slug `coraline`, ISBN-13 `9788498382372`.
- Categorías compartidas: `halloween|terror|fantasia-juvenil|fantasia-oscura|mundos-paralelos|misterio`.
- Destino de TODOS los pines sobre Coraline: `https://davidportodiaz.com/recomendaciones/libros/coraline/`.
- Destino del botón y de la **portada clicable en la web**: **URL de producto Amazon.es con tag de afiliado existente**, sin salto automático. Codex ya ha incorporado un botón afiliado en el piloto; **la portada es actualmente un `<img>` sin enlace** y debe envolverse con un enlace accesible al **mismo URL afiliado**, cuando esté configurado.
- La ficha conserva URL canónica propia. No crear una URL por categoría ni duplicar libros por temporada.

## 2. Fuentes de portada y destinos: separar técnicamente

**A. Activo del pin (origen NO Amazon Creators API)**

- `pinterest_image_url`: imagen del pin con portada auténtica y edición comprobada, obtenida de una fuente separada de la API de Amazon (p. ej., recurso editorial aplicable, fotografía real propia del libro o material facilitado para divulgación). No crear ni inventar portadas de obras reales.
- `pinterest_pin_destination_url`: siempre URL web de la ficha, con UTM opcionales.
- Imagen vertical preferente de prueba **2:3, 1000×1500**; fotografía real del libro/portada real y rótulo en español cuando ayude al usuario. No empezar de una ilustración fantasy generada. Mantener proporciones auténticas del libro físico.
- Nunca usar como recurso del pin el enlace de imagen o contenido extraído de **Amazon Creators API** para redirigir a nuestra web: ese recurso Amazon debe apuntar a Amazon según sus condiciones.

**B. Portada en la web**

- Fuente preferida **cuando Creators API esté habilitada**: `amazon_image_url` obtenida por la integración oficial para el **ASIN correcto**. Al usar el recurso Amazon en la ficha, **su imagen debe vincular a Amazon**, no a otra página. Revisar requisitos técnicos vigentes sobre caché, caducidad y actualización de URL, y no descargar ni perpetuar imágenes de la API como archivos propios.
- Alternativa operativa **sin Creators API**: conservar la portada local/editorial de la edición que ya utiliza el piloto en `/assets/reading-covers/`; **la portada en la ficha también puede ser un enlace al Amazon afiliado correspondiente**, por decisión de UX.
- Si Amazon no ofrece esa edición, la ficha puede mantener su contenido y un enlace de compra solo cuando exista producto correcto. No confundir ISBN con ASIN ni prometer existencia de stock.
- `amazon_affiliate_url`: enlace de producto al ASIN correcto en Amazon.es con el tag que realmente pertenezca al autor. En la rama actual Codex ha usado `davidporto-21`: **reutilizar la configuración real del repo y no introducir nuevos tags inventados**. Si es preciso habilitar API/confirmar permisos o datos, pedirlo al propietario.
- El botón debe identificar claramente **«Amazon»**; su apertura no puede sustituirse por una redirección automática o invisible. Divulgación de afiliación visible y `rel="sponsored nofollow noopener noreferrer"` donde proceda.
- Imagen de la ficha clicable con `<a href="...">`, atributo accesible que indique «Ver <título> en Amazon (enlace afiliado)» y navegación por teclado. El botón Amazon usa la misma URL. Si hay galería interactiva o ampliación, no debe robar el clic de compra de forma engañosa.

**Conclusión técnica:** **no hace falta duplicar fichas ni usar dos URLs de libro**. Hace falta separar la **URL de destino del pin (web)** de la **URL de destino de la imagen/botón de la ficha (Amazon)**, con sus respectivas imágenes.

## 3. Google Sheets y contrato de importación

La hoja actual incluye las pestañas `01_LIBROS`, `02_CATEGORIAS`, `03_PORTADAS`, `04_ENLACES`, `05_FUENTES`, `06_IMPORTACION` y `07_PINTEREST`. No crear una fila distinta del libro por cada categoría.

**Clave estable:** `libro_id` → `01_LIBROS.id`. La lista `01_LIBROS.categorias[]` contiene slugs separados por `|` y referencia la tabla `02_CATEGORIAS`. Esa relación es **muchos-a-muchos**, no una duplicación del libro.

Campos ya presentes/reutilizables:

- `01_LIBROS`: `id`, `slug`, `titulo`, `autor`, `isbn13`, `asin_amazon`, `categorias[]`, `url_ficha_web`, `amazon_tracking_id`.
- `03_PORTADAS`: `libro_id`, `isbn_edicion`, `asin_amazon`, `url_imagen_amazon`, `url_imagen_editorial`, `url_imagen_en_web`, `modo_imagen`.
- `04_ENLACES`: una fila de tipo `amazon_afiliado`, una de tipo `amazon_producto`, más `fragmento`, `editorial`, `resenas`, etc.
- `07_PINTEREST`: una fila por **variante de pin**, no por libro; varias variantes pueden compartir `libro_id` y `url_destino_web`. Campos de la pestaña pueden ampliarse sin tocar la clave maestra.

**Esquema ya preparado en `07_PINTEREST` de Google Sheets**, para utilizarlo en la futura PR de publicación (el importador de libros no debe exigir estos campos para publicar fichas):

`pin_id,libro_id,categoria_objetivo,keyword_principal,keywords_secundarias,consulta_validada,tablero_pinterest,pin_titulo,pin_descripcion,url_imagen_pin,url_origen_imagen_pin,url_destino_web,utm_campaign,utm_content,fecha_programada,estado_publicacion,pinterest_pin_id,url_pin_publicado,impresiones,guardados,clics_salientes,fecha_medicion,notas`

- `pin_id` identificador **único por variante creativa**, distinto de `libro_id`. P. ej. `LIB-0001-halloween-001` y `LIB-0001-fantasia-oscura-001` apuntan ambos a la ficha de Coraline.
- `url_destino_web` debe ser una URL canónica publicada; añadir UTM al publicar si queremos atribución, manteniendo la canonical de la ficha limpia.
- Evitar guardar contraseñas, tokens o secretos en Sheets; el importador usa configuración de entorno.
- En la PR de automatización establecer el mapeo exacto entre estos campos y la interfaz de publicación que Pinterest tenga disponible entonces. No suponer permisos API ni publicación automática hasta verificarlos.

## 4. Investigación de posicionamiento Pinterest **antes** de automatizar

No imponer ahora títulos genéricos por intuición. Preparar una **investigación específica en español** y registrar consultas, resultados y fechas. Fuentes:

1. **Pinterest Trends** (cuando proporcione resultados del país/idioma aplicable) y buscador de Pinterest: consultas reales, sugerencias y términos relacionados.
2. Comparación de búsquedas: libro/autor `Coraline`; intención de lectura `libros para Halloween`, `libros de terror juvenil`, `fantasía oscura juvenil`, `libros de mundos paralelos`; títulos estacionales versus atemporales. No suponer volúmenes no publicados.
3. Análisis de pines y tableros visibles que respondan a cada búsqueda: títulos, enfoques, formato gráfico, originalidad visual, destino, idioma, pertinencia de categoría. No tomar «aparecer en búsqueda» como prueba de conversiones.
4. Definir tablero principal y variante visual/titular por **intención de búsqueda**. Un libro puede generar varios pines verdaderamente distintos, **sin publicar duplicados masivos** de la misma cubierta.
5. Probar **título de búsqueda concreto** frente a **título de recomendación contextual**, manteniendo descripción que complemente el pin y esté alineada con la ficha. Usar español de España con tildes y eñes correctas.
6. Pinterest indica **100 caracteres para el título y hasta 800 para la descripción** de un pin de imagen; recomienda incluir términos relevantes y coherentes en título, descripción, tablero y landing. La descripción contribuye a la relevancia aunque normalmente no se muestre en el feed.
7. Empezar las campañas estacionales con antelación: investigar cuándo despega cada consulta y planificar Halloween, Navidad, vuelta a las clases, etc. No asumir el mismo calendario para cada tema.
8. Para formatos visuales: empezar por **foto humana real** y portada auténtica si aparece un libro; probar composición limpia con título editorial versus foto de estantería/libro en mano. El texto del pin NO debe limitarse a repetir el caption/descrición de forma literal.

**Fuentes oficiales consultadas el 20/10/2026:**

- [Pinterest: especificaciones de pins](https://help.pinterest.com/es/article/review-pin-specs).
- [Pinterest: distribución y rendimiento](https://help.pinterest.com/es/business/article/pin-performance-and-distribution).
- [Pinterest: crear pines y añadir enlaces](https://help.pinterest.com/es/guide/guide-to-creating-pins).
- [Pinterest: Pines detallados (Rich Pins)](https://help.pinterest.com/es/business/article/rich-pins).
- [Amazon.es: políticas y licencia de imágenes/contenido API](https://afiliados.amazon.es/help/operating/policies).

**No interpretar esta investigación pendiente como promesa de alcance orgánico.** Debe compararse con Analytics de la cuenta y con clics reales a la web.

## 5. Recorrido de publicación y medición para la PR futura

**Ingesta → verificación → imagen para Pinterest → metadatos → publicación → seguimiento.**

1. Detectar libros publicados/aprobados en Sheets y fichas web ya desplegadas, con URL web que devuelva 200, canonical correcta y cubierta auténtica.
2. Recuperar fuentes y categoría(s); seleccionar **intención concreta de búsqueda** y determinar pin/variación; no crear una ficha nueva por cada variante.
3. Generar/componer la imagen de pin desde su **fuente no Amazon**, con foto real y portada auténtica si corresponde. Nombrar archivo y mantener relación `pin_id` → `libro_id`.
4. Crear título/descripción basados en investigación de búsquedas y tableros; comprobar dimensiones de imagen y coherencia con el texto de la ficha.
5. Asignar **destino WEB obligatorio**: `https://davidportodiaz.com/recomendaciones/libros/<slug>/?utm_source=pinterest&utm_medium=organic&utm_campaign=<campana>&utm_content=<pin_id>`. URL de Amazon nunca entra en este campo.
6. Publicar/programar **solo cuando exista integración real con Pinterest o revisión manual confirmada**. Guardar ID/URL de pin y estado; registrar errores, duplicados y reintentos sin publicar dos veces por accidente.
7. Desde la web, medir `landing_view`/visitas a ficha provenientes de Pinterest; medir también `amazon_click` cuando pulsen portada o botón, registrando `libro_id` y, si es posible, el origen del tráfico de forma respetuosa con la privacidad. Ventas/atribución Amazon solo si su programa proporciona informes relevantes; no equiparar clic con venta.
8. Analizar **impresiones, guardados y clics salientes de Pinterest**, **visitas a ficha** y **clics afiliados desde la web**. Comparar `pin_id`, temporada, título y tablero y reutilizar aprendizajes en siguientes tandas.

### Aceptación funcional mínima

- [ ] Un pin de Coraline enlaza directamente a **`/recomendaciones/libros/coraline/`** y jamás a Amazon.
- [ ] La ficha muestra la portada correcta, sinopsis, etiquetas múltiples, reseñas y capítulo si están disponibles.
- [ ] **La portada de la ficha es clicable hacia Amazon afiliado** y el botón «Ver en Amazon» usa el mismo URL. Ambos abren el producto de edición correcta.
- [ ] Si se usa imagen API de Amazon, ésta solo actúa como contenido que lleva a Amazon; la imagen Pinterest usa origen independiente.
- [ ] Otro pin para una categoría diferente de Coraline mantiene **la misma URL web** y no duplica la ficha en el catálogo.
- [ ] URL de la ficha abre correctamente sin parámetros; las UTM no cambian la canonical ni crean páginas duplicadas.
- [ ] La publicación de Pinterest no se activa automáticamente en esta fase. La investigación, la automatización y el mapeo ampliado de Sheets se implementarán y validarán en PR posterior.

## 6. Relación con el trabajo **ya existente** en #659

La PR ya implementa ficha `/recomendaciones/libros/coraline/`, botón Amazon afiliado y adaptador Creators API, pero las consultas a Amazon no están operativas por elegibilidad de la cuenta (véase `docs/catalogo-lecturas-automatizacion.md`). No bloquear el flujo de Pinterest por esa cuenta si existe una cubierta editorial separada y un enlace afiliado verificado.

**Cambio pequeño para revisar en esta PR:** hacer clicable la **portada de la ficha de Coraline** para abrir el mismo enlace Amazon que usa el botón, sin alterar el paso anterior Pinterest → web. La automatización del paso Pinterest queda documentada para su fase posterior.

**No fusionar por el mero hecho de añadir este documento**: mantener las comprobaciones y decisiones de integración habituales de la PR.
