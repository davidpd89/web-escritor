# Alternativa real a Amazon Creators API — precios y catálogo (21/10/2026)

## Diagnóstico verificado

La cuenta no cumple el umbral de ventas requerido para Creators API; el piloto existente devolvió pending_amazon_eligibility. **No debe ser la fuente primaria del precio ni consumir diariamente intentos de autenticación fallidos.** La propuesta previa de caducar los precios Amazon a la hora sigue siendo una salvaguarda técnica, pero no proporciona cobertura sin credenciales elegibles.

Las condiciones españolas de Amazon Asociados añaden dos barreras:
- [Requisitos sobre enlaces](https://afiliados.amazon.es/help/operating/linking): los precios de Amazon solo pueden mostrarse con herramientas o API autorizadas. La cláusula sobre **comparación con otras tiendas** exige incluir el precio Amazon nuevo/usado facilitado por Amazon; sin ese precio no debe mostrarse el comparador. No presentar el importe de Penguin como precio en Amazon.
- [Políticas generales de licencia](https://afiliados.amazon.es/help/operating/policies): datos comerciales, condiciones de API y caducidad. Evitar automatizaciones de navegación, scraping de resultados de Amazon, búsqueda masiva con ChatGPT o hojas Drive que repliquen esas cifras como si estuviesen autorizadas. No basar el sistema en VPN, sesiones privadas o bloqueo de captchas.

**Conclusión:** ninguna API gratuita pública, universal y sin elegibilidad de ventas de Amazon.es ha quedado verificada. Una API de terceros que acceda por scraping a Amazon no convierte esos datos en autorizados. Amazon seguirá pudiendo usarse como **enlace de afiliación sin cifra**, mientras la cuenta sea elegible para sus propios enlaces.

## Fuentes sustitutivas contrastadas

| Fuente | Cobertura | Coste/credenciales | Hallazgo, límites |
|---|---|---|---|
| **Penguin Libros (tienda oficial)** | Libros del editor y sellos asociados; físico/digital si coincide edición | Página pública; ya existe CachedHTTP con robots y caché | **Ficha real comprobada**: [Otros mundos (El Talismán 3), ISBN 9788401039560](https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039560) muestra 25,49 € (oferta) y 26,83 € (referencia). Es precio **de Penguin**, no Amazon. **Pendiente** comprobar en HTML crudo que el nodo data-product expone price_amount/price y que su uso automatizado está permitido. |
| **Google Books API (Google Play Libros)** | Solamente eBooks con ISBN de edición electrónica y saleInfo completo ES | API de búsqueda oficial, clave ya configurada | [saleInfo](https://developers.google.com/books/docs/v1/reference/volumes): saleability FOR_SALE, country ES, isEbook, retailPrice EUR y buyLink. **Piloto anterior respondió 503**, no afirmar conexión operativa. No reutilizar precio del ebook como precio en tapa dura. |
| **Awin: feed de catálogo del anunciante** | Comercios asociados que entreguen ISBN y precio | Requiere cuenta y autorización del programa/anunciante | [Product feeds para publishers](https://help.awin.com/developers/docs/product-feed-publisher) y [guía](https://help.awin.com/developers/docs/introduction-1); fuente estructurada potencialmente más robusta que HTML. **No se ha confirmado acceso ni convenio actual**; fase posterior, no inventar autenticación ni afiliación. |
| Amazon Creators API | Amazon | Elegibilidad por ventas | Preparada en main, sin acceso operativo. No bloquear la ingesta ni la publicación. |
| IA diaria + Drive / bot de navegador Amazon | Precio de Amazon sin fuente contractual | Puede generar coste e introducir errores | **Descartada**: no resuelve derechos, validación de ASIN/edición ni precio fresco; y añadiría puntos de fallo. Drive sí puede servir como cola de revisión interna, no como fuente autónoma de veracidad. |

## Código incorporado a PR #683

### Adaptador de lectura con rechazo seguro

- `scripts/reading_free_prices.py`: `penguin_offer(book, page, now)`, `google_ebook_offer(book, response, now)`, `refresh_penguin`, `refresh_google_ebooks`. Reutiliza `reading_editorial_sources.penguin_edition` y `ProductHTML` y las mismas comprobaciones de ISBN/canonical que la ingesta. **No lee un precio del texto general de la página**, porque podría seleccionar un producto recomendado. Solo permite precio del elemento del ISBN seleccionado, título, autor, formato y URL oficial coincidentes. Devuelve None si el campo cambió o falta.
- `tests/test_reading_free_prices.py`: precios decimales exactos, ISBN, autor, formato, país, divisa, enlaces ajenos, fallo de Google 503 y presupuesto 0. Casos **preparados, no ejecutados**.
- `data/reading-intake-config.json`: `free_price_refresh.enabled=false`, presupuesto Penguin 30, Google ebooks deshabilitado, `amazon_price_refresh.enabled=false` para evitar intentos conocidos como inviables; `purchase_price_mode=amazon_affiliate` por seguridad.
- `assets/reading-free-prices.json`: fichero vacío válido, nunca precios sintéticos en producción.
- `scripts/refresh-reading-catalogue.py`: enchufe al **único publicador** diario con informe de proveedor; no crea otro cron. Solo funciona si se habilita expresamente después del piloto. Respeta SHA, QA, allowlist de `scripts/publish-reading-refresh.py`, y las normas generales de publicación.
- `assets/reading-catalogue.js` y `scripts/build-reading-catalogue.py`: lectura opcional del JSON y render de precio por **tienda, formato y fecha**; la cifra desaparece al caducar y no se presume stock. **Conmutador legal/comercial:** no presenta precios ajenos al lado del enlace afiliado de Amazon.

### Dos modos excluyentes

**A — `amazon_affiliate` (por defecto, conservador):** texto «Ver/Buscar en Amazon», nunca un número sacado de una tienda distinta. `validFreeOffer` desactivado en navegador. Útil para preservar monetización actual, pero sin precios.

**B — `publisher_only` (preparado, sin activar):** el builder quita CTA y enlace de cubierta a Amazon en fichas y tarjetas. Cuando la edición está verificada en Penguin, presenta enlace a la ficha oficial, cuyo precio podrá aparecer si el adaptador confirma una cifra reciente. Para eBooks puede presentar Google Play si coincide ISBN exacto y el proveedor funciona. No enviar al usuario desde una cifra editorial a Amazon. El modo B sacrifica el CTA afiliado de Amazon en esas páginas, deliberadamente.

**No** cambiar el modo en la web publicada hasta verificar las condiciones de Amazon aplicables al sitio y ejecutar QA de HTML/JS sin JavaScript, accesibilidad, navegación y datos estructurados. Si la interpretación de su política comercial sigue ambigua, mantener A y consultar a Amazon por escrito sobre compatibilidad con reseñas y precios externos antes de habilitar B.

### Contrato público propuesto (no incluye precios de Amazon)

```json
{
  "schema_version": 1,
  "offers": [
    {
      "libro_id": "isbn-9788401039560",
      "isbn13": "9788401039560",
      "fuente": "penguin_libros",
      "formato": "tapa-dura",
      "moneda": "EUR",
      "precio_centimos": 2549,
      "precio_referencia_centimos": 2683,
      "url": "https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039560",
      "actualizado_en": "2026-10-21T12:00:00Z",
      "caduca_en": "2026-10-22T12:00:00Z"
    }
  ]
}
```

**Ejemplo ilustrativo de estructura con los importes visibles en la ficha**, no dato generado ni almacenado en producción: el verdadero fichero de esta PR contiene `"offers": []`. El reloj de ejemplo tampoco representa una lectura real.

## Pasos cerrados para Claude: activar solo si el piloto aprueba

1. **Comprobar permisos:** leer robots.txt y las condiciones vigentes de Penguin para consultas automatizadas de precio. Si no hay permiso suficiente, no activar rastreo. Preguntar por feed autorizado o fuente alternativa.
2. **Confirmar HTML crudo**, no texto interpretado por navegador: 10–20 ISBN de géneros y formatos diferentes, comprobar data-product.price_amount/price, currency/tax, IVA y precio de referencia; si hay elementos múltiples o formato ambiguo, dejar en pendiente. Evaluar tasa de coincidencias y cobertura entre nuestros 26+ libros.
3. **Validar fuente secundaria** con un eBook ISBN realmente electrónico y `saleInfo.country=ES`. Si Google Books vuelve a dar 503, conservarla desactivada. No suponer que ISBN de papel tiene precio de ebook.
4. **Probar contratos en checkout aislado**, exclusivamente tras autorización de tests: Python unittest de `test_reading_free_prices.py`, `test_reading_price_mode.py`, tests existentes de catálogo y comercio; browser a 360/390/768/1440 px, JS off, 200 títulos, lectores de pantalla, cambio de hora Madrid, caducidad y filtros.
5. **No insertar un precio en el HTML estático** sin caducidad. El fichero de ofertas se sirve aparte, se consulta desde JS y se filtra por fecha/hora (24 horas de frescura editorial propuesta, no SLA garantizado). La carga diaria ocurre en el proceso existente, con presupuesto y comprobación de robots. Para consultar precios se fuerza respuesta HTTP fresca (`ttl=0`): nunca se presenta la fecha de ejecución como si fuera la fecha de un documento de caché anterior. Si el proveedor falla, no se renueva el sello temporal. Bajo incidencia, **no mostrar precio** y conservar «Consultar precio» del vendedor autorizado en el modo elegido.
6. **Versionar `assets/reading-catalogue.js` desde la plantilla** (`scripts/templates/reading-catalogue.html.tmpl`) y regenerar HTML/artifacts únicamente en fase de validación. Este borrador modifica el JS fuente, pero todavía no recompila HTML ni certifica su ejecución en la web pública.
7. **En modo B**, comprobar con tests que no quedan links afiliados en tarjetas, cubierta, formatos alternativos y ficha del mismo libro; que ninguna cifra editorial se etiquete como Amazon. En modo A, comprobar que `reading-free-prices.json` no activa una comparación accidental. Decidir modo mediante configuración, no valores implícitos en el navegador.
8. **SEO/comercio:** Schema Book ya existe. No añadir `Offer` JSON-LD de Amazon ni mezclas de vendedores con precios no vigentes. La información externa debe ser visible y exacta para marcarla; no proclamar rich results garantizados. Respetar políticas de reseñas: Goodreads es fuente externa atribuida, no reseña verificada propia.
9. **Métricas:** ofertas válidas / ISBN elegibles, fallos fuente, edad de oferta, coste de peticiones, porcentaje de fichas con precio tras 24 h, clics al vendedor, INP/LCP y peso JSON; no afirmar cobertura completa.
10. **Activación tras aceptación:** `free_price_refresh.enabled=true`; de ser legal y útil, `purchase_price_mode=publisher_only`; fijar el presupuesto razonable por día y confirmar que el publicador reproduce PR, CI, deploy y smoke del mismo SHA. No abrir otro workflow ni publicar datos privados.

## Autores, editoriales, fichas homogéneas, reseñas y SEO

La auditoría integral previa de la PR continúa vigente. **No recrear** lo existente: autor → libros publicados → editoriales → categorías, con Book/Person, sitemap, Pagefind, catálogo de 24 visibles y render de todas las tarjetas. Hay código para biografías Penguin, con fuente y protección de homónimos; estado de recepción editorial requiere su prueba independiente. Para páginas más atractivas y comparables, usar una plantilla única con jerarquía: cubierta/título/autores → sinopsis diferenciada de metadatos → etiquetas → precio o enlace permitido según modo → ficha de edición/ISBN → reseñas por proveedor → relacionados → fuentes. No autoescribir resúmenes críticos ni biografías inventadas. Vigilar la futura escalada del DOM a 500–1000 libros antes de publicar miles de páginas.

Documentación ampliada: `docs/research/lecturas-calendario-fuentes-2026-10-21.md` y `docs/catalogo-lecturas-automatizacion.md` (este último requiere actualizarse al fusionar porque aún describe la dependencia de Amazon).
