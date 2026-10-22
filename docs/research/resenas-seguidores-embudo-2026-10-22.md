# Investigación aplicada: reseñas de lectores y seguimiento de autor (22-10-2026)

**Estado: investigación con auditor offline y pruebas preparadas; ninguna acción de producción activada.** Objetivo: conseguir más lectores que lleguen a los lugares donde pueden seguir al autor o dejar valoraciones propias, distinguir los clics en la web de las acciones completadas y priorizar por rendimiento medible.

**No duplicar:** #717 posee Amazon Author Central/Follow, tags, escaparate y auditor de URLs; #397/#470 poseen identidad y ediciones de Goodreads; #683 posee importación de ratings/precios del catálogo general. Esta PR se concentra en **adquisición de reseñas de lectores para los dos libros propios y medición del embudo**.

## Resultado ejecutivo: tres hallazgos que sí cambian una decisión

1. **Amazon dice que el número de seguidores NO altera la clasificación de los más vendidos.** Sí puede servir para alertas de libros elegibles y descubrimiento de nuevos lanzamientos, sujeto a ajustes del lector; contabilización en Author Central. Decisión: priorizar seguidores reales como público futuro, no como truco de ranking. Fuente primaria: https://kdp.amazon.com/es_ES/help/topic/G200644310
2. **La web ya solicita reseñas en Samuel pero no en Manecillas.** En main, la ficha Samuel, línea ~410, incluye «Dejar reseña en Amazon» y «Valorar en Goodreads»; Manecillas tiene URL de obra Goodreads en JSON-LD pero ningún CTA visible equivalente. La página del autor enlaza Amazon #customerReviews con texto «Ver todas las reseñas en Amazon España y Goodreads», aunque ese enlace lleva solo a Amazon. Decisión: introducir CTAs claros, distintos y sobrios en Manecillas y corregir el texto engañoso del enlace genérico.
3. **Falso positivo analítico comprobable en el código actual.** script.js, bloque delegado tras _gcEvent, cuenta TODO href que contenga amazon.es/amzn.to como evento comprar-amazon. Pulsar «Dejar reseña en Amazon» o «Ver reseñas» dispara el evento de compra. Decisión: añadir identificación semántica de objetivo y excluir de «comprar-amazon» los enlaces de reseñas/seguir. No confundir clic con compra o reseña publicada.

## Evidencia de la web y destinos, sin inventar cifras

| Superficie | Ya disponible en main | Falta verificable / siguiente acción |
|---|---|---|
| /autor.html | Goodreads autor https://www.goodreads.com/author/show/66843136.David_Porto_D_az ; Amazon en sameAs https://www.amazon.es/stores/author/B0GZFP1JV3 | CTA visible «Seguir al autor en Amazon». Mantener separado del CTA de compra y sin tag afiliado |
| /libros/samuel-entre-mundos/ | «Dejar reseña en Amazon» a https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21#customerReviews ; «Valorar en Goodreads» a https://www.goodreads.com/book/show/245605636-samuel-entre-mundos | El enlace Amazon abre el área de opiniones, NO garantiza abrir el formulario de escritura. Evento específico, no de compra |
| /las-manecillas-del-recuerdo/ | URL Goodreads presente en JSON-LD: https://www.goodreads.com/book/show/258289637-las-manecillas-del-recuerdo ; dos formatos Amazon registrados en #396/#717 | Enlaces visibles de reseñar Goodreads/Amazon para la edición correcta; comprobar en navegador los destinos papel/Kindle antes de publicarlos. No copiar un ASIN no validado |
| Casa del Libro · Samuel | Ficha real: https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720 ; 5 reseñas visibles el 22/10/2026; botón de reseña para usuario logado | CTA contextual para lectores que compraron allí. El enlace de ficha lleva a la ficha, no al formulario autenticado |
| Goodreads · Manecillas | Ficha identificada por búsqueda pública, con valoración y reseñas; no se verificó una sesión autenticada actual | Usar URL canónica ya enlazada en el repo; NO prometer escritura anónima o por API |

Fuentes:
- Amazon KDP: https://kdp.amazon.com/es_ES/help/topic/G200644310 y https://kdp.amazon.com/es_ES/help/topic/G202101910
- Amazon recomendaciones a autores: https://kdp.amazon.com/en_US/help/topic/G200673650
- Goodreads Author Program: https://www.goodreads.com/author/program
- Goodreads pauta de opiniones: https://www.goodreads.com/review/guidelines
- Casa del Libro, proceso de opinar: https://www.casadellibro.com/tu-opinion-tiene-premio
- Casa del Libro, ficha Samuel: https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720

### Qué podemos demostrar y qué no

- **Confirmado por Amazon:** número de seguidores de autor no altera Best Sellers Rank; seguir puede ayudar en notificaciones/discovery de futuros libros, no promete avisos a todos.
- **Confirmado por Amazon:** los lectores pueden comentar desde su ficha/pedidos; se comprueba su publicación; dar una copia gratuita o rebajada no obliga a recibir ninguna reseña. Amazon calcula estrellas con modelos, no media aritmética simple. El efecto causal de X reseñas en la posición de búsqueda o BSR NO está demostrado aquí.
- **Confirmado por Goodreads:** autores con perfil reclamado pueden interactuar, lectores pueden valorar obras; el programa no ofrece atajo para asignar reseñas.
- **Confirmado por Casa del Libro:** cuenta logada y botón en la ficha; NO hay API pública de creación de reseñas verificada en esta investigación.
- **NO comprobado:** tasa de conversión externa, seguidores iniciales en Author Central, reseñas finales creadas tras clic, capacidad de la cuenta editorial/KDP para editar las fichas, correspondencia efectiva de shortlinks actuales.

## Único repositorio externo con código aplicable: GoatCounter

**Repositorio vivo:** https://github.com/arp242/goatcounter ; licencia del script cliente public/count.js: **ISC**, confirmada en https://github.com/arp242/goatcounter/blob/main/LICENSE . API/documentación de eventos: https://www.goatcounter.com/help/events

Ejemplo **literal** de la documentación oficial del software (no reescritura, funcional si count.js está cargado):

~~~html
<a href="https://example.com" data-goatcounter-click="ext-example.com">Example</a>
~~~

Es precisamente el problema ya resuelto por este proyecto: el contador está integrado desde script.js, que carga https://gc.zgo.at/count.js en el dominio de producción y expone _gcEvent(path, title). **No copiar ni empaquetar de nuevo public/count.js:** eso duplicaría un sistema probado. **No añadir data-goatcounter-click a un enlace ya instrumentado manualmente:** evitar doble conteo. El selector debería ser exclusivo.

Extracto **abreviado** de la función existente en script.js (para consultar el código exacto, abrir el archivo original; aquí se han omitido comentarios y condensado el callback final):

~~~js
function _gcEvent(path, title) {
  const payload = { path, title, event: true };
  const send = () => {
    try {
      window.goatcounter.count(payload);
    } catch {
      // Analytics is never allowed to break the interaction that reported it.
    }
  };
  if (window.goatcounter && window.goatcounter.count) {
    send();
    return;
  }
  scheduleTask(() => {
    if (window.goatcounter && window.goatcounter.count) send();
  }, "background");
}
~~~

El código anterior ya funciona dentro de script.js (depende de scheduleTask del propio proyecto). Para evitar errores de integración, **reutilizar esta función en su archivo**, no crear un segundo loader ni copiar la función en un script independiente.

## Propuesta implementable tras la revisión (sin desplegarla hoy)

**Mecanismo A (preferido):** cada CTA de reseñar/seguir recibe atributos estables data-reader-action y data-book, con valores controlados. El listener delegado existente, en script.js, comprueba primero data-reader-action: si es un objetivo de reseña o seguimiento emite evento propio y retorna ANTES del bloque genérico comprar-amazon. Los enlaces de compra mantienen su lógica existente. Beneficios: estadísticas separadas, compatibilidad con nodos añadidos tras carga y dependencia cero.

Bloque de integración propuesto, **código propio inspirado en el patrón delegado ya utilizado en script.js** (no atribuirlo al tercero):

~~~js
const readerActions = {
  "amazon-follow": "seguir-autor-amazon",
  "amazon-review": "resenar-amazon",
  "goodreads-review": "resenar-goodreads",
  "casa-review": "resenar-casa-del-libro"
};
document.addEventListener("click", (event) => {
  const link = event.target?.closest?.("a[data-reader-action]");
  if (!link) return;
  const kind = link.dataset.readerAction;
  const book = link.dataset.book || "autor";
  if (!Object.hasOwn(readerActions, kind)) return;
  if (!/^(autor|samuel|manecillas)$/.test(book)) return;
  _gcEvent(readerActions[kind] + "-" + book, "Lector: " + kind + " · " + book);
});
~~~

**Cambio indispensable adicional** en listener actual comprar-amazon: justo después de comprobar si existe el link, insertar:

~~~js
if (link.hasAttribute("data-reader-action")) return;
~~~

Los eventos son **clics hacia la plataforma**, nunca reseñas confirmadas ni seguidores efectivos. Para medir seguidores reales, introducir manualmente el saldo de Author Central en una serie semanal; para reseñas, series semanales por obra/plataforma/edición desde las fichas públicas; no atribuir causalidad automáticamente a la web.

**Mecanismo B:** usar data-goatcounter-click directamente por enlace, según documentación del proyecto externo, en lugar del listener propio; menos código, pero no debería combinarse con _gcEvent ni con un listener genérico de Amazon. Recomendación A por reuso de la instrumentación actual.

CTAs propuestos, contenido neutral:
- Seguir al autor en Amazon → https://www.amazon.es/stores/author/B0GZFP1JV3
- Samuel: dejar tu opinión en Amazon, Goodreads o Casa del Libro (enlaces directos a las fichas verificadas arriba).
- Manecillas: valorar en Goodreads (URL real verificada por búsqueda y presente en JSON-LD); Amazon papel/Kindle solo después de validar la correspondencia comercial y la experiencia del formulario.

## Embudo y diseño A/B pequeño

- **A:** CTAs al final de las fichas, junto al bloque de reseñas actual. **B:** mismo bloque al acabar el fragmento/capítulo de muestra; no pop-up en primera visita. Mantener uno solo activo por página durante la observación para comparar.
- Medición semanal: páginas vistas → clics salientes por CTA → reseñas públicas nuevas por obra/plataforma, y diferencia neta de seguidores Amazon solo donde Author Central lo muestre.
- No introducir contador de reseñas agregado en JSON-LD si no hay procedencia y datos válidos. No afirmar incremento de BSR sin datos de ventas/ranking independientes. Ninguna cuenta artificial ni publicación automática de reseñas pertenece a este desarrollo.

## Implementado en esta rama

1. scripts/audit-reader-engagement-links.py: auditor local (HTMLParser de la librería estándar, sin dependencias ni red) para detectar CTAs visibles de reseñar/seguir y la colisión del enlace Amazon con el listener de compra. Salida JSON reproducible.
2. tests/test_audit_reader_engagement_links.py: cuatro pruebas aisladas para distinguir reseña real de enlace de compra/perfil, destino Follow y aria-label.
3. Este documento de evidencias + fragmentos listos para integrar en una PR hija de interfaz cuando se apruebe el diseño.

**Estado de comprobación:** inspección del código de main y fuentes públicas sí; pruebas automatizadas escritas pero **no ejecutadas**; CI, Actions, despliegue, merges, scraping, envío de emails y modificaciones de la web pública **no realizados**.

## Criterios de aceptación de la futura integración

- Un clic en CTA de reseña Amazon cuenta una vez como resenar-amazon y **cero** como comprar-amazon.
- Un clic en Comprar sigue contando una sola vez como comprar-amazon.
- Un clic en Seguir Amazon cuenta una vez, sin afirmar que realmente haya comenzado a seguir al autor.
- Links válidos y accesibles en móvil y escritorio; sin prometer acceso directo a formulario si el enlace apunta a ficha o #customerReviews.
- Evento separado por libro y canal; formato de edición correcto; sin introducir dependencias de analytics adicionales.
- No se incorporan plataformas donde no esté disponible la obra o donde no se haya verificado el flujo.

**No priorizados**: BookBub solo tiene alertas gratuitas de nuevos títulos con alcance estadounidense y requisitos específicos de eBook; no sustituye un embudo ES para los libros existentes (https://support.bookbub.com/articles/bookbubs-marketing-tools/). StoryGraph permite reseñas por lectores pero no existe una integración pública confirmada para crearlas: sin implementación adicional.
