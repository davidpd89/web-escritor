# Encargo para Codex · Catálogo de recomendaciones de lectura

Fecha: 2026-10-20 · Repositorio: `davidpd89/web-escritor` · Web: https://davidportodiaz.com

## 0. Objetivo y decisiones cerradas

Convertir **Recomendaciones de lectura** en un catálogo visual de muchos libros de otros autores, integrado en **Cuaderno**. Cada ficha muestra **portada real**, título, autor y una **descripción breve y útil**; permite descubrir títulos por múltiples categorías y abrir un enlace de compra en **Amazon con afiliación**, cuando esté aprobado y verificado. Cada ficha tendrá una URL propia y estable de `davidportodiaz.com`, destinada a enlazarse desde futuros pines de Pinterest. El visitante llega **primero a la web del autor**, NO directamente a Amazon. Se prevé un gran catálogo que se alimentará después con un Google Drive organizado por libros, categorías, imágenes y enlaces.

**Secuencia de trabajo establecida por el propietario:**
1. **ESTA FASE / ESTA RAMA (Codex):** adaptar la estructura, navegación, diseño, modelos y plantillas de la web; conservar las páginas existentes y su SEO.
2. **FASE POSTERIOR (usuario + asistente):** crear el Google Drive/Google Sheets maestro y recopilar muchos libros, datos, categorías, descripciones, portadas reales y enlaces afiliados.
3. **OTRA PR POSTERIOR:** importar/volcar todo el catálogo del Drive a la web mediante el formato acordado.
4. **OTRA PR POSTERIOR:** automatizar/configurar los pines de Pinterest para que cada pin lleve a la ficha correspondiente en la web.

No cambiar el plan ni sustituirlo por una estrategia distinta. **No empezar las fases 2, 3 ni 4 en esta PR.** No descargar masivamente portadas, no inventar fichas, reseñas, ISBN ni enlaces. Diseñar la infraestructura extensible ahora.

## 1. Situación real del repositorio (verificada en main)

- Sitio **HTML/CSS/JS estático, publicado directamente**, sin build de aplicación Node. `package.json` solo reúne utilidades CI/QA.
- `cuaderno/index.html`: archivo de artículos, con navegación contextual «Archivo | Temas | Recomendaciones».
- `cuaderno/temas/index.html` y `cuaderno/temas/fantasia-de-portales/index.html`: colecciones editoriales existentes.
- `recomendaciones/index.html`: hub de recomendaciones con las dos listas editoriales actuales.
- `recomendaciones/portal-fantasy-espanol/index.html`, `recomendaciones/magia-con-coste/index.html`, `recomendaciones/politica-de-recomendaciones/index.html`: conservar íntegros, enlazados y localizables.
- `convocatorias-escritores/index.html`, `assets/radar-convocatorias.{css,js}`, `convocatorias-escritores/opportunities.json`: referencia de **experiencia de menú/filtros + fichas**, NO de contenido, ni para duplicar lógica sin adaptación.
- `data/content-registry.json` y `data/navigation.json`: fuente de verdad para estructura/discoverability.
- `scripts/build-section-context-nav.py` + `assets/v1-editorial-interior-v4.js`: navegación contextual generada en paralelo (ver comentarios de los propios archivos).
- `data/recommendations-evidence.json`: normas editoriales sobre edición verificada y no fingir lecturas.
- `lecturas/index.html` y `data/reading-list.json` son **fixture/demostración con noindex**, NO el nuevo catálogo; no exponer su contenido como fichas reales.
- El repositorio ya incorpora políticas de enlaces afiliados, navegación, diseño editorial v1, CSP, SEO, Pagefind y pruebas; **respetar el sistema actual**.

## 2. Arquitectura de información y navegación

- Dentro de **Cuaderno**, consolidar la experiencia para evitar tres puertas que muestran casi lo mismo («Archivo», «Temas», «Recomendaciones»).
- `/cuaderno/` mantiene **todos los artículos actuales**, agrupados de forma clara; el acceso se denomina **«Artículos»**.
- `/recomendaciones/` mantiene la misma URL indexada/canonical y pasa a denominarse visiblemente **«Recomendaciones de lectura»**: el nuevo catálogo de portadas y categorías. Debe ser accesible desde Cuaderno y la navegación contextual sin duplicar el archivo de artículos.
- Conservar `/cuaderno/temas/` y cada tema ya indexado; pueden pasar a ser accesos secundarios/contextuales desde el Cuaderno para quitar redundancia visual, **sin eliminarlos ni desindexarlos arbitrariamente**.
- Las guías anteriores de `/recomendaciones/portal-fantasy-espanol/` y `/recomendaciones/magia-con-coste/` deben aparecer en una zona «Guías y artículos de lectura» del nuevo hub, junto con las piezas existentes pertinentes del Cuaderno; son enlaces a artículos **reales**, sin duplicar texto ni generar thin content.
- Propuesta de ruta estable para fichas de cada libro: **`/recomendaciones/libros/<slug-estable>/`**; cada portada/tarjeta enlaza a la ficha web. La página de libro incluye enlace de regreso al catálogo y enlaces a categorías. El slug no debe depender de una temporada ni del orden de clasificación.

## 3. Diseño y experiencia de usuario

Inspiración funcional: la pantalla de convocatorias. Construir, con el **sistema visual editorial propio de la web** y CSS específico si hace falta:
- Cabecera breve, introducción útil y acceso a guías ya existentes.
- Menú de categorías y filtros visibles: búsqueda textual (título/autor), género/subgénero (fantasía, fantasía juvenil, romantasy, romance, fantasía oscura, etc.), temporada/ocasión (Halloween, Navidad...), y «Novedades / últimos lanzamientos».
- **Un libro puede aparecer en varios filtros/categorías y temporadas, pero existe UNA sola ficha, UNA portada verificada y UNA URL canónica.** No crear duplicados por tema.
- Índice de categorías arriba y grid responsivo de portadas, título, autor y descripción breve; las fichas en móvil han de ser utilizables y no perder legibilidad.
- Barra/menú de filtros y contador de resultados; estado vacío claro; búsqueda que funcione por teclado; sin depender exclusivamente de JavaScript para que rastreadores descubran los títulos publicados.
- En detalle de libro: portada real, título, autor, sinopsis breve redactada con palabras propias, clasificación, datos bibliográficos disponibles y botón **«Ver en Amazon»** con afiliación cuando la URL sea válida.
- Mostrar recomendaciones propias (`Samuel entre mundos` y otras obras del autor) solo donde su clasificación sea pertinente, identificando siempre su autoría.
- Preparar URLs de categoría o filtros enlazables **solo cuando haya contenido propio suficiente**. Evitar indexar combinaciones vacías o infinitas de filtros.

**No presentar libros ficticios ni placeholders con portadas falsas como contenido real.** Hasta la carga masiva, la página puede mostrar las guías existentes y un catálogo vacío con estado editorial discreto; si se reutilizan libros ya presentes en guías, no afirmar lectura personal sin constancia explícita y mantener la procedencia verificable.

## 4. Contrato de datos preparado para Google Drive (fase 2 y 3)

Codex debe diseñar y documentar un formato versionable y validable, preferentemente JSON/CSV limpio a partir del futuro Google Sheets. Separar las entidades **Libro**, **Categoría** y su relación muchos-a-muchos. Sin integraciones en vivo con Drive en esta PR. Campos propuestos:

**Libro (obligatorios para publicar):**
- `id` estable, `slug` estable, `titulo`, `autor(es)`, `descripcion_breve` ORIGINAL, `categorias[]`.
- `estado` (borrador / listo / publicado).
- `portada_local` con ruta válida y `portada_fuente_url`, `portada_edicion_verificada`, `derechos_uso` / `autorizacion_o_base_uso` y fecha de revisión. Solo publicar portada real coincidente con edición y cuyo uso sea justificable.
- `url_amazon_afiliada` (opcional; nunca inventarla).
- `fuente_bibliografica_url`, `fecha_verificacion`.

**Libro (opcionales):** `isbn13` y edición, editorial, año/fecha de publicación para novedades, idioma, subgéneros/temas, fecha de alta, última actualización, `url_oficial_editorial`, notas editoriales y `lectura_personal_confirmada` (NO inferirla). Definir cómo tratar obras multiedición y duplicados por ISBN. No fabricar opiniones personales.

**Categoría:** `id`, `slug`, `nombre`, `tipo` (género / temática / temporada / novedad), `descripcion`, `orden`, `activa`; admitir una lista extensible, etiquetas con tildes y claves estables. «Últimos lanzamientos» se calcula por fecha de publicación verificada, no por cuándo se importó el libro, y nunca etiquetar «novedad» un libro antiguo.

Preparar y documentar los **nombres de columnas de Sheets** para que podamos crear el Drive exactamente compatible y después volcarlo en otra PR. Eliminar o aislar datos de ejemplo que no deban indexarse. Establecer validadores para links/covers duplicados, categoría inexistente, ISBN/slug repetidos y metadatos sin fuente.

## 5. SEO, Pinterest, derechos y afiliación

- Mantener `/cuaderno/`, `/cuaderno/temas/`, `/recomendaciones/`, las dos guías y artículos existentes. **No cambiar canonicals indexados ni introducir redirecciones/404** sin necesidad comprobada.
- Páginas de ficha con URL canónica auto-referida, `title` específico, meta description única, imagen social (`og:image` absoluta de la portada legítima), `og:title`, `og:description`, `twitter:card`, breadcrumbs y JSON-LD apropiado (`Book`/ `CollectionPage` / `BreadcrumbList` cuando correspondan, **sin valoraciones ni reseñas inventadas**).
- Los pines futuros deben poder vincularse a la **ficha web del libro** que contiene esa imagen, nunca a la URL Amazon directamente. Preparar imágenes y landing pages; **no implementar automatización de Pinterest** hasta la fase 4.
- Las imágenes son de **portadas reales verificadas**, sin alteraciones de diseño ni sustituciones generadas. Guardar procedencia y justificación/autorización de uso. No asumir que aparecer en Internet implica permiso para descargar y redistribuir.
- En la ficha, si se incluye enlace Amazon afiliado, distinguirlo claramente y mostrar divulgación visible de afiliación conforme a los requisitos del programa. Usar `rel="sponsored nofollow noopener noreferrer"` y `target="_blank"` cuando proceda. Sin enlaces afiliados hasta disponer de los enlaces correctos. No inventar cuentas/tags.
- HTML accesible indexable; textos alt descriptivos, portada responsive con tamaños explícitos/imagen optimizada, lazy loading por debajo del primer pliegue, compatibilidad CSP y enlaces internos consistentes.
- Preparar inclusión correcta en `sitemap.xml`, `robots.txt` (sin bloquear fichas), Pagefind y navegación/contenidos registrados. Evitar indexación de resultados vacíos de búsquedas y filtros con querystring.
- Mantener política editorial de `/recomendaciones/politica-de-recomendaciones/` y `data/recommendations-evidence.json`: «verificado» no equivale a «leído».

## 6. Implementación en esta misma rama: alcance esperado de Codex

1. Revisar todos los archivos generadores antes de editar HTML derivado; cambiar fuentes de verdad y **regenerar** con scripts existentes, sin parches manuales a bloques marcados como generados.
2. Rediseñar `recomendaciones/index.html` como nueva portada de **Recomendaciones de lectura**, navegación/filtros/listado extensible y sus estilos / scripts necesarios.
3. Ajustar navegación de Cuaderno para separar **Artículos** y **Recomendaciones de lectura**; quitar redundancia visual de «Archivo/Temas/Recomendaciones» conservando rutas y páginas.
4. Implementar plantilla/pipeline de ficha individual con HTML estático indexable (sin imponer nuevo framework ni servicio externo) y contrato de datos válido y documentado. El archivo fuente de datos deberá servir para carga masiva posterior, evitando copiar manualmente HTML por cada libro.
5. Conservar y mostrar las guías/artículos originales dentro de la nueva experiencia.
6. Preparar divulgación Amazon, metadatos por ficha, navegación SEO y destino web listo para Pinterest; no incluir imágenes sin derechos verificados, comprar nada ni publicar pines.
7. Añadir las pruebas mínimas para navegación, URLs históricas, accesibilidad de filtros, datos, metadatos, enlaces internos, categorías múltiples y estado vacío.
8. Entregar una **nota para nosotros** con columnas exactas de Google Sheets, formato de categorías, convenciones para imágenes, URLs, estados de publicación y pasos de importación de fase 3.

## 7. Requisitos para considerar terminada la fase

- Cuaderno sigue mostrando **todos** sus artículos, sin páginas desaparecidas.
- Acceso inequívoco a «Recomendaciones de lectura» desde Cuaderno; las antiguas listas conservan URL y se descubren desde el nuevo hub.
- Los filtros funcionan y el diseño recuerda funcionalmente a convocatorias, no es un clon visual.
- Un libro en dos o más categorías conserva la **misma URL propia**, con portada real, breve texto y enlace a Amazon condicionado a disponibilidad.
- Una ficha pública puede compartirse en Pinterest y llevar al visitante **primero a davidportodiaz.com**.
- Todo SEO/indexación existente permanece intacto; tests pertinentes sin regresiones.
- El contrato para Google Sheets está listo **antes de empezar a recopilar cientos de portadas**.
- NO cargar masivamente libros, NO tocar Drive y NO automatizar Pinterest en esta fase.

## 8. Operativa de la PR

Esta PR comienza con **solo este encargo**. Codex debe incorporar la implementación en **esta misma rama/PR**, revisar el diff y reportar cambios; no fusionar sin decisión expresa del propietario. Tener en cuenta que existen otras PR de QA abiertas y una cola histórica con CI aplazado: no activar despliegues, ejecución masiva de Actions ni merge por iniciativa propia; coordinar la validación cuando el propietario lo autorice.
