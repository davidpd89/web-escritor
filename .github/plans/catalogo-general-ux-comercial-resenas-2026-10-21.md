# Codex — segunda fase del catálogo: TODOS los libros, experiencia uniforme, afiliación y reseñas moderadas
**Fecha:** 21/10/2026 · **Encargo nuevo** que toma como base `main` tras las PR #660/#661/#664. **Esta rama aún no está implementada; es una especificación + auditoría programable para reducir trabajo de Codex.** No desplegar nada sin pruebas.

## 0. Rectificación obligatoria de estrategia (propietario)
**NO limitar el catálogo a fantasía, romantasy, juvenil ni ningún nicho.** Se busca el mayor número posible de **libros reales de editoriales de todos los géneros**, con visitantes interesados en CUALQUIER lectura y enlaces Amazon.es afiliados. Cocina, nutrición, ensayo, biografías, poesía, infantil, ficción, divulgación, filosofía, etc. son **deseables**. No filtrar ni dar menor peso a una categoría por no ser fantasía. Escalar cantidad y diversidad **con datos fiables y páginas útiles**, ampliando fuentes, editoriales y asignación temática.

La priorización por género que se sugirió en el comentario anterior de PR #664 estaba equivocada y **ya se corrigió expresamente en aquel comentario**. No recuperarla en código ni QA.

## 1. Estado real y fuentes de verdad
- `main`: **26 libros** (Coraline + 25 automáticos), PR #664 fusionada y Pages publicado.
- `data/reading-catalogue.json`: fuente canónica de libros/categorías M:N. `scripts/build-reading-catalogue.py`: validación y HTML. `assets/reading-catalogue.js`: filtros, novedades y mercado. `scripts/reading_intake_pipeline.py`: captación editorial, textos y portadas. `data/reading-authors.json`, `data/editoriales.json`: autores y editoriales ya existentes. `data/content-registry.json`, sitemap/Pagefind y `scripts/build-public-dist.py`: SEO y publicador estático; NO cambiar de framework.
- `data/reading-intake-config.json`: una única fuente automática por ahora (Penguin); `max_new_books=5`, `max_requests=80`, `autopublish=true`, `generate_audio=false`, afiliado `davidporto-21`. Workflow `reading-catalogue-sync.yml` tiene cron diario condicionado por `vars.READING_INTAKE_ENABLED`; no duplicar writers.
- 25 fichas nuevas usan `amazon_busqueda_isbn=https://www.amazon.es/s?k=<ISBN13>&tag=davidporto-21`; Coraline usa 4 `formatos_compra` directos. **La búsqueda es suficiente como enlace principal a Amazon si no hay ASIN verificado**. Amazon remunera artículos que cumplan sus condiciones dentro de ventana de atribución; una búsqueda no garantiza que el usuario compre ese ISBN ni comisiones por cada venta. Fuente oficial: https://afiliados.amazon.es/help/node/topic/G9SMD8TQHFJ7728F . El usuario quiere simplificar también Coraline, **sin perder enlaces directos mejores ya comprobados si interesan**: usar un componente compra común que funcione con ambos tipos y ofrezca UNA acción principal.
- La **portada de las 25 fichas nuevas NO tiene clic hacia Amazon**, porque `render_book()` solo envuelve `image()` en enlace si hay `url_amazon_afiliada`. El botón de búsqueda sí funciona. Corregir con misma función de resolución de destino.
- El catálogo piloto de Drive está en https://docs.google.com/spreadsheets/d/1hHtp-B66CdnXgV6IT7ClcLGLxLUw8tKOLQThVD5KHCs/edit , **pestaña `08_RESEÑAS` YA CREADA** el 21/10/2026; aún NO recibe envíos públicos ni alimenta la web.
- La PR #662 sigue abierta/draft para Pinterest RSS; no confundir este encargo con publicar pines.

## 2. Lista completa de encargos del propietario y aceptación (16 puntos)

### 1. «Novedad» salta de una tipografía/apariencia a otra
`novelty()` emite inicialmente un `span` con fallback «Libros recomendados» o géneros; el JS calcula `isNew` y cambia texto/clase después de cargar. Solucionar el **flash of unstyled/changed content**, reservando lugar/estilos y renderizando el estado inicial coherente con el día civil Europe/Madrid. Alternativa: misma tipografía, peso y altura estable para fallback y badge; JS no debe provocar CLS. No guardar una etiqueta permanente «Novedad» en JSON; desaparece en cuanto vence plazo actual de **15 días**, incluso sin cron. Pruebas con reloj congelado en día 0, 14, 15, Madrid DST/recarga y sin JS.

### 2. Categorías siempre visibles, también con «Novedad»
Separar la etiqueta temporal del contenedor estable de **chips de categorías**. Novedad + etiquetas pueden coexistir en cada tarjeta: género, tema, temporada, edad u otras relevantes, con límite razonable visible + «ver más» si necesario. Tras día 15 desaparece solo badge, no categorías. En ficha individual mantener categorías completas y coherentes. No quitar los géneros de cocina u otros.

### 3. Metadatos homogéneos: fecha natural, editorial y edad
En todas las tarjetas mostrar **fecha de publicación** en formato español («20 de octubre de 2026», o «octubre de 2026»/«2009» según precisión), editorial y páginas cuando existan. Edad, si existe, debe presentarse **aparte con etiqueta explícita**, no reemplazar editorial. En Coraline NO inventar día exacto si fuente solo verifica el año/mes: auditar su edición y consistencia; su visualización actual fue reportada como «2009 8 12». Separar fecha de edición, actualización de ficha y detección de novedades.

### 4. Compra Amazon disponible desde la tarjeta del catálogo
Agregar `Ver en Amazon` / `Buscar este ISBN en Amazon` visible en tarjetas (sin entrar en ficha). Resolver URL **una sola vez** por libro: `producto directo verificado > búsqueda ISBN afiliada > sin acción`, nunca un enlace sin `tag`. Para portada de ficha usar el mismo destino que el botón. En tarjeta, **la portada enlaza a nuestra ficha** (no Amazon) y la tarjeta contiene dos destinos diferenciados: «Ver ficha» y «Amazon». Esto preserva el recorrido Pinterest → ficha → Amazon y facilita compra desde listado. En Coraline no exigir siempre desplegar cuatro formatos: CTA principal y `Ver otros formatos` opcional.

### 5. Valoraciones Goodreads actualizadas diariamente
**Bloqueo externo real:** Goodreads dejó de emitir claves API nuevas en diciembre de 2020 y prevé retirar su API pública: https://www.goodreads.com/group/show/8095-goodreads-developers . **NO prometer que se puede rellenar Goodreads para todos gratis y cada día** ni copiar puntuaciones por scraping no probado. Investigar integraciones oficiales válidas de la cuenta; si no hay endpoint autorizado, mantener enlace a Goodreads sin estrellas.
**Alternativa técnica gratis:** `Google Books Volume.volumeInfo.averageRating` y `ratingsCount` están documentados: https://developers.google.com/books/docs/v1/reference/volumes . Investigar cuota gratis/clave, hacer matching **ISBN/edición y autor**, mostrar «Valoración de Google Books» (no Goodreads), conteo, fuente y fecha. Solo calcular y activar filtro sobre valores frescos disponibles; NO mezclar fuentes ni atribuir Google Books a Goodreads. Las **reseñas propias aprobadas** (apartado 16) serán otra fuente separada.

### 6. Precios Amazon diariamente
**Bloqueo de datos:** Amazon Afiliados ES solo permite reproducir precio/disponibilidad desde enlace o widget ofrecido por Amazon o **Creators API/PA API autorizado**, con las condiciones de actualización/sello temporal: https://afiliados.amazon.es/help/operating/policies. La cuenta del propietario aún devolvía `AssociateNotEligible` para Creators API. No resolver mediante scraping con navegador, precio inventado, Google Books `saleInfo` (es precio de Google Play Books, NO de Amazon) ni precios de editoriales presentados como Amazon. Verificar **si hay widget oficial de Amazon que presente precio en la web sin acceso a la API**, o botón «Consultar precio en Amazon». Cuando exista acceso autorizado, sincronizar precios cada ≤24h con timestamp + desactivar en fallo. Si no, no mostrar filtros vacíos ni texto de disculpa.

### 7. Páginas de autores automáticas con contenido útil
`update_authors()` produce el párrafo repetitivo «Libros de X incluidos en este catálogo…». Mejorar automáticamente con hechos contrastados (fuentes editoriales, catálogo propio, colecciones/sagas, cronología, número de libros publicados en la web, lista de obras relacionadas y novedades). No inventar biografía, fechas ni `sameAs`. Mostrar contenido suficiente o **no crear páginas de autor con cero información diferenciadora**; siempre mantener enlace al autor/obras del catálogo. Relacionar desde editoriales → autores → libros y vuelta, sitemap/Pagefind; URLs estables.

### 8. Sinopsis que resuma la obra + páginas/filtro de extensión
Separar `sinopsis_breve` de `descripcion_bibliografica` y `numero_paginas`, migrar `descripcion_breve` con compatibilidad:
- Sinopsis: de qué trata realmente el libro, como Coraline (no fórmula «X de Y en tapa dura de Z con N páginas»).
- Edición: hechos técnicos en la sección Datos.
- Los nuevos textos deben proceder de fuentes verificadas y generarse **sin LLM recurrente**. Investigar el resumen editorial `og:description`, JSON-LD `description`, `meta description`, datos públicos apropiados, permiso de utilización y método factual sin inventar tramas ni plagiar bloques enteros. Si no hay sinopsis utilizable, mostrar una ficha bibliográfica honesta y **no inventar una trama**. Marcar cobertura real; la "descripción única" fabricada con title/ISBN no mejora automáticamente SEO.
- Tarjetas: `fecha · editorial · N páginas`. Filtro numérico de **longitud**: `<200`, `200–399`, `400–599`, `600+` o selector min/max; libros sin páginas quedan en «Sin dato» y no se consideran 0. Mostrar clasificación por género/fecha/precio/rating sin confundir conceptos.

### 9. Fichas en pestaña nueva
Al pulsar portada/título/«Ver ficha» de una tarjeta de `/recomendaciones/`, abrir libro en otra pestaña (`target="_blank" rel="noopener noreferrer"`) con indicación accesible «se abre en otra pestaña»; mantener la página de resultados y sus filtros. Enlace Amazon también pestaña nueva con `rel=sponsored nofollow noopener noreferrer`. En enlaces de navegación interna secundarios (breadcrumbs) NO imponer nueva pestaña.

### 10. Unificar Coraline y las otras 25 fichas
Crear estructura estable, donde cada bloque opcional SOLO aparece si tiene datos:
- «Sinopsis», «Datos de edición», «Temas y categorías», «Autores», «Editorial», «Páginas», «Opiniones» (de la fuente etiquetada) y «Fuentes de los datos» uniformes.
- Audio Elvira de Coraline, muestras/fragmentos oficiales y los 4 formatos solo si disponibles; como el usuario busca homogeneidad, **evaluar retirar audio y fragmento de Coraline** si no se puede escalar gratuitamente, o dejar claramente como bloque opcional que nunca deje huecos en otros libros. Mantenerlos hasta decisión concreta y nunca eliminar material útil inadvertidamente.
- No presentar enlaces de búsqueda en Goodreads como "reseñas verificadas"; distinguir plataforma externa, resumen propio y reseñas locales moderadas.
- Revisar jerarquía visual, tipografías, responsive móvil/tablet/escritorio, márgenes, contraste, tamaños táctiles, lectura sin JS, no CLS.
- SEO: canonical por ficha, Book/Person/BreadcrumbList schema, `og:image`, títulos/metas distintos, evitar contenido masivo superficial. Meta 100 en Lighthouse no prueba posicionamiento.

### 11. Clasificación exhaustiva y coherente en TODOS los géneros
Auditar `classify()` y catálogo M:N: **edad «Adultos» sola NO es categoría temática**. Bug concreto `La fibra es la solución` ISBN `9788425374869`: solo `adultos`, se pierde de los filtros de nutrición/salud. Ampliar taxonomía (nutrición, salud, bienestar, cocina, divulgación, historia, psicología, cómic, infantil, poesía, etc.) desde etiquetas reales, pero también temas, tono, longitud, estación, formato, idioma, público y series verificadas. Sin asignar etiquetas por ocurrencia ingenua de palabra; clasificador determinista por `materias` y equivalencias comprobadas. Conservar categorías manuales al refrescar, permitir retirar etiquetas erróneas con un mecanismo explícito de revisión; pruebas con 200 libros y autores repetidos.

### 12. Mejoras adicionales de escalabilidad
- Ampliar **editoriales de todos los géneros**, no solo Penguin: conectores gratuitos con tests y límites por fuente, sin requisito de tokens IA. 150 editoriales existentes a reutilizar; más cuando fuentes auténticas lo permitan, sin duplicar nombre/sello/grupo.
- Descubrir catálogos y próximos lanzamientos, fechas completas/precisión, ratio de candidatas aceptadas, ISBN/ASIN verificado, caché y retries; no publicar 5 primeros solo por orden HTML sino diversificar editores/temas **sin excluir ninguno**.
- Vista de **novedades** y «Próximamente» con filtros, calendario de publicaciones, enlaces de títulos y series, relacionados automáticos, páginas de serie únicamente si hay datos únicos y 2+ obras.
- Medir clics por libro y por botón **sin datos personales**: campañas UTM y métricas agregadas para conocer qué filtros y libros convierten, evitar redireccionadores que rompan el tracking de Amazon. Datos agregados, ninguna venta inventada.
- IndexNow/Sitemap/Pagefind y check de todas las rutas, build incremental, `main` protegido.
- La PR #662 Pinterest RSS no está fusionada. No publicar pines hasta revisión de imagen real por edición, cuenta/feeds, y evitar filas sin sinopsis relevante.

### 13. «Novedad» se retira sola después del período
`assets/reading-catalogue.js` ya calcula 15 días relativos a Europe/Madrid. Añadir test extremo fechas 0, 14, 15, 16, 30; leap/DST; recarga en nuevo día **sin nuevo deploy**. Nunca basarse en `fecha_alta` ni `fecha_actualizacion`.

### 14. Fechas/precios/valoraciones: que SE VEA el desplegable
`render_filters()` actual usa `<details class="catalogue-more-filters"><summary>Fechas, precios y valoraciones</summary>`; rehacer sumario más evidente, con borde/chevrón, foco visible, estados `open` y diseño táctil sin desplazar contenido. Si precio/rating no están disponibles NO dejar controles engañosos en el wizard; mostrar solo opciones reales. Pruebas visuales móviles y teclado/lector pantalla, y contraste WCAG.

### 15. Eliminar mensaje de filtros de precio y oferta no disponibles
Eliminar del hub `data-market-note` el texto «Los filtros de precio y oferta estarán disponibles cuando haya precios vigentes.» y su equivalente de JavaScript cuando sin datos. No generar párrafo vacío ni ocultar controles aún funcionales. No mostrar precio estimado.

### 16. Test interactivo «¿Qué te apetece leer?» + reseñas propias aprobadas
**Asistente de filtros (sin GPT):** CTA al principio «¿No sabes qué leer? Encuentra tu próximo libro» y wizard de preguntas progresivas que usa **exactamente el motor de filtros existente** (no crear otro backend). Ejemplos:
1. ¿Buscas una novedad, un clásico o te da igual?
2. ¿De qué temática te apetece? (TODOS los géneros; temporada Halloween/Navidad/Verano si existen, combinar).
3. ¿Qué extensión? (libro breve / mediano / largo / cualquiera).
4. ¿Te importa la valoración? (solo si hay reseñas reales suficientes y su procedencia).
5. ¿Tienes presupuesto? (solo si precios Amazon autorizados y actualizados; si no, saltar).
6. Orden y resultados; permitir volver, cambiar respuesta y reiniciar. **Ramificación dinámica** basada en el subconjunto real de resultados; no ofrecer caminos que llevan a 0 resultados sin aviso/alternativa. Sin imponer restricciones del nicho. Wizard accesible con teclado, lectura por pantalla, JS degradable, filtros visibles y URL con criterios compartibles; progreso «pregunta 2 de 5» según pasos disponibles.

**Reseñas propias/moderación en Google Sheets — pestaña REAL creada:**
https://docs.google.com/spreadsheets/d/1hHtp-B66CdnXgV6IT7ClcLGLxLUw8tKOLQThVD5KHCs/edit
`08_RESEÑAS` tiene `resena_id, libro_id, isbn13, nombre_publico, puntuacion_1a5, titulo_resena, texto_resena, fecha_envio, estado_moderacion, fecha_revision, origen, consentimiento_publicacion, nota_interna`. Valores de estado `pendiente | aprobada | rechazada`, puntuación 1–5. **Solo los aprobados y consentidos** se muestran en la web. No exponer la hoja completa ni emails/datos privados en `main`.

Fases del servicio gratis:
A) Desde ya, **reseñas redactadas y aprobadas por propietario** en la pestaña. Añadir importador determinista de filas aprobadas por ID/ISBN a `data/reading-reviews-approved.json`; revisar fuente/consistencia, nunca publicar comentarios pendientes o rechazados. Si el acceso a Google Sheets todavía es manual, importación puntual CSV aprobada, luego cron Google Sheets API con credenciales restringidas del propietario para sincronizar solo la pestaña.
B) Cuando se quiera permitir visitantes: **Google Forms ligado a hoja privada**, formulario con libro precargado (URL `prefilled` por `libro_id`/ISBN), alias público, estrellas y comentario, sin exigir una cuenta en la web; requiere crear/vincular el formulario una vez. Google Forms/App Script documentado: https://developers.google.com/apps-script/reference/forms/form-response . El público no escribe en JSON/repositorio ni en la pestaña de aprobados. Moderación `pendiente` en el Panel, propietario aprueba/rechaza, sync periódico publica exclusivamente aprobadas. Escapar HTML, limitar tamaño, anti-spam/rate limiting cuando se habiliten envíos públicos.
C) Mostrar en cada ficha «Opiniones de lectores» y media de **reseñas propias** con número real y 1–5 estrellas. **Nunca sumar Goodreads o Google Books a esa media**. Google Search permite `Review`/`AggregateRating` para `Book` con opiniones genuinas visibles: https://developers.google.com/search/docs/appearance/structured-data/review-snippet . Añadir schema SOLO de reseñas aprobadas publicadas, autor público/fecha/estrellas, y media idéntica a visible. No fabricar ni autogenerar reseñas ni puntuaciones.
D) Editor puede corregir moderación: si una reseña aprobada se retira, el siguiente sync la quita del JSON, la ficha, el contador y los datos estructurados; pruebas de borrado/edición sin duplicar/reintroducir.

## 3. Plan técnico y pruebas obligatorias
**No rediseñar toda la web ni crear un segundo publicador.** Orden recomendado:
1. Primer PR funcional: UX de `/recomendaciones/` (puntos 1–4, 9, 13–15), visual móvil/desktop con Playwright 320/390/768/1024/1440, vista en recarga, Nov 15 días; libro nuevo y Coraline.
2. Segundo PR funcional: `sinopsis_breve`/datos de edición/páginas y taxonomía multicategoría (8, 10, 11), 25 libros históricos + nuevos. No romper contratos `BOOK_FIELDS` del validador ni las canónicas.
3. Tercero: autores, editoriales y conectores de TODOS los géneros (7, 12); informes semanales sin IA.
4. Cuarto: widget «elige libro» 100% local JS, filtros comunes y accesibilidad (16A).
5. Quinto: integración `08_RESEÑAS` aprobadas (16B), Google Form opcional para lectores y estructura Book Review, pipeline privado → artefacto público solo aprobado.
6. Precios Amazon **cuando** haya datos autorizados, y ratings Google Books si coincidencia por ISBN y fuente fiable. Goodreads: no prometer API. No bloquear el resto por 5/6.

### Matriz de tests que debe añadir Codex
- 26 libros + 100/200 ficticios: integridad URL/ISBN/ASIN-tag, categorías temáticas (edad sola = error), ficheros de portada reales, links autor/editorial y reciprocidad.
- Una etiqueta Novedad + categorías estables + resumen de fecha editorial/páginas y Amazon directo desde tarjeta. A día 15 desaparece badge sin mutación de categorías.
- Coraline + libro por búsqueda ISBN: clic portada ficha → Amazon tag; clic portada tarjeta → ficha NUEVA pestaña; botón Amazon tarjeta → Amazon NUEVA pestaña.
- Filtro páginas (numérico incl. vacío), varios filtros AND, clasificación de todos los géneros, wishlist/quiz (sin 0 opciones), fecha/mes/año, reseña fuente/fecha.
- No hay precios falsos ni texto del punto 15; sin controles deshabilitados visibles si no sirven.
- Simular reseñas pendientes/aprobadas/rechazadas, XSS, cambio de estado/revocación, ISBN inexistente, rating 0/6, títulos largos, homónimos, duplicados y latencia.
- Lighthouse y CLS en mobile/tres tamaños; accesibilidad tab/teclado y pantallas sin JS; no romper sitemap/OG/Pagefind/IndexNow ni seguridad general.
- `--check` y segundo cron no generan diffs espurios. Verify real deployment SHA y URLs de libros/autores/mapa.

## 4. Ideas extra que aumentan utilidad y clic sin coste
- **Guardar búsqueda** en fragmento URL reproducible; filtros desde un pin llevan al mismo subconjunto.
- **Colecciones de páginas por editorial, autor, tema, novedad y páginas** generadas a partir del mismo JSON, solo si tienen suficientes libros para aportar valor; no duplicar contenido ni indexar facetas infinitas.
- **«También te puede interesar»** calculado determinísticamente por género + autores/editorial + extensión, sin modelos, excluyendo el propio libro, con 3–4 títulos de géneros diversos afines.
- **Disponible esta semana** solo ediciones con fecha del sello confirmada; próximos lanzamientos separados de publicados.
- **Auditoría de pendientes automática:** editoriales desconocidas, materias sin mapa, ausencia de páginas/sinopsis, ISBN duplicados, portada mala, enlaces afiliados corruptos, sin bloquear resto.
- **Enlaces reales de muestras gratuitas** si editorial los ofrece y se pueden verificar; no prometer capítulos donde no hay URL.
- **Reporte cuantificado**: fuente → libros descubiertos → válidos → publicados → autores/editoriales vinculados → sinopsis reales → porcentajes de clic a Amazon por libro. No almacenar datos privados de lectores.

## 5. Fuentes oficiales revisadas 21/10/2026
- Amazon ES atribución 24 horas: https://afiliados.amazon.es/help/node/topic/G9SMD8TQHFJ7728F
- Amazon SiteStripe genera enlaces a cualquier página Amazon: https://afiliados.amazon.es/help/node/topic/GJMMT7G4C8K4Y3AY
- Amazon precios y condiciones: https://afiliados.amazon.es/help/operating/policies
- Goodreads API retirada de nuevas claves desde 2020: https://www.goodreads.com/group/show/8095-goodreads-developers
- Google Books `averageRating`, `ratingsCount`, ISBN, `pageCount`, `previewLink`: https://developers.google.com/books/docs/v1/reference/volumes
- Google Search reseñas `Book`: https://developers.google.com/search/docs/appearance/structured-data/review-snippet
- Google Search contenido útil: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google Apps Script cuota gratis (límite por cuenta): https://developers.google.com/apps-script/guides/services/quotas

**Resultado que se busca:** catálogo completamente generalista y extensible, automatizado sin tokens de IA, filtros verdaderamente útiles, mismos criterios visuales y de campos para libros antiguos/nuevos, sinopsis de obra diferenciadas, enlace Amazon afiliado fácil, reseñas propias bajo aprobación y SEO verificable. Ninguna promesa de ingresos ni de precios/Goodreads diarios sin fuente operativa.
