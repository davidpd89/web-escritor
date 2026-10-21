# Catálogo generalista: implementación y verificación de los 17 puntos

La entrega se prepara en la PR #665. El código de la PR #662 se incorpora con
sus pruebas; los feeds permanecen desactivados hasta la conexión y prueba real
de Pinterest. Los resultados definitivos de CI, el SHA fusionado y el despliegue
se registran en la PR para que la evidencia corresponda al commit publicado.

| Punto | Implementación |
| --- | --- |
| 1 | Novedad usa la misma fuente local Yellowtail, precargada, con altura reservada. Solo aparece con su fuente lista; si falla la fuente se muestra una alternativa estable. El test ya está en el HTML, evitando insertarlo sobre contenido pintado. |
| 2 | Categorías independientes del distintivo, tres visibles y el resto en un desplegable; en la ficha se muestran todas. Género/tema antes que edad. |
| 3 | Fechas españolas con la precisión disponible, editorial, páginas y edad identificada. Coraline conserva 2009: no se inventa un día. |
| 4 | Amazon en todas las tarjetas con destino verificado o búsqueda exacta por ISBN y tag. Misma función para portada y compra en la ficha. |
| 5 | Consulta diaria pública por ISBN a Goodreads y APIs opcionales de Hardcover/Google Books, con identidad, fuente y caducidad. No inventa valoraciones cuando no hay coincidencia. Los secretos de ambas APIs están configurados. |
| 6 | Consulta diaria de Creators API preparada con los secretos existentes. Solo precios EUR de compra nueva y edición/formato verificado; excluye suscripciones, usado y ofertas exclusivas de Prime. Caducidad máxima 24 horas y menor si la oferta vence antes. La falta de elegibilidad detiene el lote y se comprueba de nuevo al día siguiente. |
| 7 | 25 biografías editoriales breves, fuentes verificadas y refresco mensual acotado dentro del escritor diario. La biografía manual de Neil Gaiman se conserva. Todas las páginas incluyen temas, editoriales y ediciones por fecha, generadas desde el catálogo. |
| 8 | Sinopsis de las 25 fichas automáticas separada de datos técnicos: extractos breves de hasta 24 palabras, atribuidos y enlazados a la editorial; extracción determinista sin modelos. Filtro por extensión y orden por páginas, con categoría explícita sin dato. |
| 9 | Portada, título y ficha de la tarjeta abren otra pestaña; Amazon también, con noopener/noreferrer y atributos de afiliación. Los breadcrumbs conservan la navegación normal. |
| 10 | Misma estructura para las 26 obras. Audio y fragmentos retirados de la interfaz por no disponer de automatización homogénea. Se conservan sus archivos y datos previos para no romper URLs. Compras con una acción principal y formatos adicionales opcionales. |
| 11 | Todos los géneros/editoriales admisibles. Una edad sola no clasifica el tema. Materias nuevas conservan su etiqueta editorial. Se preservan categorías manuales y hay exclusiones explícitas que no reaparecen al refrescar. Amadoca se corrige como novela histórica, excluyendo crianza; nutrición tiene género y tema. |
| 12 | Paginación de 24 resultados; búsqueda y filtros sobre todo el catálogo, sin indexar combinaciones infinitas. Índices de precios y valoraciones en memoria. Lecturas relacionadas estáticas. RSS en el único escritor diario incluso sin libros nuevos. Selección diaria determinista de candidatas, sin favorecer el orden HTML ni un género. |
| 13 | Distintivo relativo a la fecha editorial completa, días 0–14 en Madrid; desaparece el día 15 sin despliegue, al volver a la pestaña y con el temporizador. No depende de la revisión de ficha. |
| 14 | Más filtros tiene borde, signo de apertura, estado abierto diferenciado y objetivo táctil. Los controles comerciales se ocultan si no tienen datos válidos. |
| 15 | Eliminada la frase de filtros de precio/oferta no disponibles; sin párrafo vacío equivalente. |
| 16 | Test local, compartiendo el motor de filtros. Preguntas y opciones según resultados posibles, volver/reiniciar y URL reproducible. Se omiten precios y valoraciones ausentes. Base de reseñas locales: exportación de aprobadas/consentidas, renderizado escapado y Review/AggregateRating solo cuando existan opiniones reales publicadas. No se publican ejemplos ficticios. |
| 17 | Revisadas las PR 665 y 662. Integración de datos, fichas, autores, editoriales, mapa plegable, sitemap, Pagefind, metadatos Book/Person/Breadcrumbs y enlaces machine-readable. Pruebas de 100/200 libros, teclado, sin JS, cinco resoluciones y relojes Madrid/DST. |

## Evidencia local antes del gate completo

- 99 pruebas unitarias de ingesta, valoraciones, precios, taxonomía, autores,
  moderación y RSS aprobadas.
- Navegador: fixtures de 100 y 200 obras con ISBN/cubiertas/relaciones validados,
  paginación, límites de páginas, wizard adaptativo y búsqueda completa.
- Tiempo medido para filtrar: 2 ms con 100 libros, 3 ms con 200, en este equipo.
  Son mediciones locales, no una promesa de rendimiento en todos los dispositivos.
- Vistas 320, 390, 768, 1024 y 1440; comprobación sin JavaScript y fuente ausente.
- Suites previas de catálogo y comercio aprobadas; la de ingesta verifica cada
  libro, autor y sello, más límites temporales.
- 25 sinopsis migradas desde caché sin nuevas peticiones. Biografías editoriales
  verificadas por nombre y URL, con identidad comprobada y sin texto completo copiado.

## Límites externos que deben figurar en el informe final

- Ningún proveedor garantiza que todos los libros tengan valoración. El piloto
  local de Hardcover obtuvo una coincidencia (Coraline) y 25 sin datos, sin errores.
  Goodreads funcionó para Coraline; no se presenta como cobertura completa.
- Google Books devolvió HTTP 503 y `Service temporarily unavailable.` La clave
  está creada y restringida, pero eso no demuestra disponibilidad del proveedor.
- La cuenta de Amazon confirma al 21/10/2026 el requisito de diez ventas válidas
  en treinta días y hasta 48 horas de revisión de credenciales. Los precios no
  se dan por activados hasta recibir y validar una respuesta real. Documentación:
  https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
- No se ha creado ni activado un formulario público de reseñas. La sincronización
  de una hoja privada requiere identidad de lectura y moderación de opiniones
  auténticas; el exportador y el renderizado están preparados sin exponer la hoja.
- Pinterest: feeds preparados, sin afirmar creación de tableros, conexión RSS
  o publicación de pines. Se mantiene el piloto de Coraline hasta verificar la cuenta.

Las limitaciones de acceso no justifican precios, estrellas, reseñas, fechas de
obra ni publicaciones externas inventados. El gate protegido y la comprobación
del SHA de producción son requisitos para considerar desplegada esta entrega.
