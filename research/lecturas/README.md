# Investigación aplicada a la automatización de libros · 21 de octubre de 2026

**PR hija lógica de la [#661](https://github.com/davidpd89/web-escritor/pull/661) (ingesta editorial) y de la [#665](https://github.com/davidpd89/web-escritor/pull/665) (catálogo/UX) ya fusionadas.** Se basa en `main` posterior a ambas para evitar conflictos. No sustituye su código ni abre otro publicador. La [#662](https://github.com/davidpd89/web-escritor/pull/662) permanece abierta, pero la #665 ya incorporó una versión posterior de sus feeds; no se copia código de su rama antigua.

## Dictamen ejecutivo (decisiones que Claude puede revisar directamente)

| Idea | Evidencia actual | Decisión propuesta |
| --- | --- | --- |
| **Segunda fuente oficial Planeta** | [Novedades Planeta octubre 2026](https://www.planetadelibros.com/libros-novedades/p/1), fichas con ISBN/edición/fecha/sello; dos ISBN no presentes en el catálogo actual de 26 | **Sí, piloto**: adaptador independiente, reutilizar validador, ISBN, catálogo y único publicador; medir 20 fichas reales antes de ampliar |
| **Añadir libro al calendario y suscribirse a lanzamientos** | `data/reading-catalogue.json` ya incluye `fecha_publicacion`, `estado`, `slug`, `isbn13`; [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545) es interoperable | **Sí, bajo coste**: botón «Añadir al calendario» solo fecha exacta futura y feed `.ics` actualizado en el mismo build diario |
| **Avisarme cuando esté disponible** | No hay servicio de notificaciones/inscripciones conectado para esto | **No afirmar que exista email push**: empezar por recordatorio de calendario local/subscripción; email opcional futuro solo si hay infraestructura de suscripción y evento real de disponibilidad |
| **Navegación por meses/estrenos** | La web ya tiene filtro «próximos 30 días», filtros 15/30/90/180 y paginación | **Iteración mínima**: mostrar timeline «esta semana / mes próximo», chip «Próximamente: 11 nov.» y botón ICS en fichas futuras; NO recrear filtros ni índice |
| **SEO de próximos libros** | [Guía oficial Google: contenido útil](https://developers.google.com/search/docs/fundamentals/creating-helpful-content?hl=es); el catálogo ya tiene HTML/Book/Person/BreadcrumbList | **Conservador**: una landing útil `/recomendaciones/proximos-lanzamientos/` con datos reales, si el piloto obtiene volumen y texto editorial suficiente; no crear 12 páginas casi iguales |
| **Pinterest** | [Pinterest RSS Business oficial](https://help.pinterest.com/es/business/article/auto-publish-pins-from-your-rss-feed), integración [#665](https://github.com/davidpd89/web-escritor/pull/665) | **Mantener RSS único**, no API, ni navegador automático adicional; enlaces existentes a ficha antes de Amazon |
| **Precios y valoraciones** | Google Books, Hardcover, Goodreads y Amazon Creators ya tienen adaptadores/cache/controles en `main` | **No cambiar** sin cobertura y acceso demostrados; no crear otra consulta por visita ni prometer precio previo al lanzamiento |

## 1. Planeta: comprobación hoy en páginas oficiales, no una fuente imaginaria

- [Índice oficial de novedades Planeta](https://www.planetadelibros.com/libros-novedades/p/1), paginado mediante `/p/2`, `/p/3` etc. En el índice se ven géneros/autor y etiqueta «Próximamente», **pero no se debe inferir ISBN o fecha exacta del título solamente**.
- [`Cosamala`, Alana S. Portero](https://www.planetadelibros.com/libro-cosamala/458658): ISBN físico **978-84-322-5143-6**, publicación **14/10/2026**, sello **Seix Barral**, 272 páginas. El ISBN normalizado `9788432251436` **no está** en `main:data/reading-catalogue.json` (26 libros consultados 21/10).
- [`Una corte de alas y ruina`, Sarah J. Maas, edición](https://www.planetadelibros.com/libro-una-corte-de-alas-y-ruina/461239): ISBN **978-84-08-32858-2**, publicación anunciada **11/11/2026**, sello **Booket**, 672 páginas. Ese ISBN `9788408328582` tampoco aparece en los 26; ejemplo inmediato de futuro lanzamiento que podría crear entrada de calendario.
- **Esto demuestra disponibilidad de registros diferentes de nuestra única fuente actual, NO tasa de éxito del scraper**. El HTML real no se ha descargado: las páginas anteriores se han contrastado por su contenido público y el script de prueba usa fixtures equivalentes construidas a mano. Antes de integrar, capturar HTML autorizado y comprobar selectores/parsing en muestra representativa.

### Código disponible ya, qué hace y qué NO

[`research/lecturas/scripts/reading_planeta_offline_probe.py`](scripts/reading_planeta_offline_probe.py): Python stdlib, **sin red**, separa:
1. En documento HTML de índice guardado, extraer **solo links de fichas oficiales** `https://www.planetadelibros.com/libro-<slug>/<id-numérico>`, deduplicados.
2. En HTML de ficha guardada, leer bloque `Ficha Técnica`, título `h1`, ISBN13 y checksum, fecha de día español, sello y páginas. Genera `status=candidate_review` con proveedor/URL. **No intenta generar una ficha publicable**, porque faltan por validar autor, cubierta, sinopsis, encuadernación, idioma/región y categorización.
3. [Seis pruebas sintéticas](tests/test_reading_planeta_offline_probe.py) que simulan la **estructura textual oficial**, cubren host, ISBN checksum, día exacto y casos incompletos; ejecutadas el 27/10/2026 (pasan; se lanzan desde la raíz del repo con `python research/lecturas/tests/test_reading_planeta_offline_probe.py`).

**Límite relevante del pipeline actual:** [`scripts/reading_intake_pipeline.py`](../../scripts/reading_intake_pipeline.py) en main acepta *solo* `provider='penguin'` / `www.penguinlibros.com` (líneas 252–255), descubre links con `product_links()` y obtiene ISBN de `url.rsplit('-',1)[-1]` (línea 315). El identificador de ficha Planeta `/458658` **NO es ISBN**. **No basta con añadir `planetadelibros.com` a `data/reading-intake-config.json`**: ese cambio permitiría URLs incorrectas y saltarse la identidad de edición. Integración correcta futura:

```text
ProviderAdapter.discover(index_html) → [canonical_product_urls]
ProviderAdapter.extract(product_html, url) → normalized EditionCandidate:
  isbn13, titulo, autores, editorial, fecha_publicacion_edicion,
  precision_fecha, formato, encuadernacion, portada_fuente_url,
  sinopsis_breve, idioma, region, fuentes_autores, materias
                              │
                              ▼
state keyed by ISBN13     →  work_key, ISBN+edición, 13-digit checksum
publisher_slug/aliases    →  categorización existente
builder.validate          →  mismo HTML, autores, sitemap, Pagefind
                            mismo publicador (#661), Amazon y Pinterest
```

**QA de integración futuro:** descargar/guardar 20 fichas distintas (incluyendo 2 próximos, 2 con formato múltiple, 2 sinopsis escasas y ISBN repetido), contrastar 100% ISBN/fecha/sello contra fuente, medir nuevos ISBN, controlar caché y límites, revisar coincidencia de editorial con `data/editoriales.json`, probar 429/error proveedor sin bloquear Penguin ni otras tareas. **Sin este QA no decir que Planeta ya funciona en producción.**

## 2. Recordatorio gratuito: eventos `.ics`, no SaaS

[`reading_release_calendar_preview.py`](scripts/reading_release_calendar_preview.py): código completo stdlib que genera:
- `lanzamientos.ics`, un calendario agregado que puede suscribirse mediante URL una vez desplegado, con `UID` determinista por ISBN y actualización en el único build diario;
- `libro-<isbn13>.ics` individual por cada edición futura (descargar/importar en calendario);
- `manifest.json` de propuestas para botón «Añadir al calendario» y enlace opcional «Google Calendar», sin JS de terceros.

**Implementado en el prototipo, verificable al ejecutar**: solo libro `estado=publicado` con fecha exacta y **posterior** al día civil Madrid, hasta 365 días; evento de día completo `DTSTART;VALUE=DATE`, `DTEND` exclusivo de día siguiente, `VALARM TRIGGER:-P1D`, UTF-8 y líneas plegadas a 75 octetos, texto escapado y UID estable y `DTSTAMP` ligado a la revisión editorial (evita falsos cambios diarios si la ficha no cambia). No inserta precio de Amazon ni fecha de disponibilidad inventada.

**Advertencia funcional útil, no obstáculo:** descargar un `.ics` no garantiza actualizarse si cambia la fecha después. **Suscribir** el calendario agregado sí permite que el cliente consulte actualizaciones según sus propias políticas; algunos clientes ignoran `VALARM` de feeds. El botón «Recordármelo» es recordatorio **en su calendario**, NO email/push desde tu web. Si quieres emails hay que añadir sistema de suscripciones más adelante.

### Integración UX concreta con el catálogo existente

1. No reemplazar el filtro existente «próximos 30». En la **tarjeta** futura: chip «Sale el 11 de noviembre» y CTA secundario **«Guardar lanzamiento»**, junto a «Ver ficha» (principal); en la **ficha**: «Añadir a mi calendario» (descarga `.ics`) y alternativa «Google Calendar». No confundir fecha de edición con inventario Amazon.
2. Nueva banda bajo el filtro de novedades: **«Próximas publicaciones»**, agrupadas por mes; una landing indexable *solo* si hay títulos reales y aportación editorial, con enlace «Suscribirse al calendario» `/recomendaciones/lanzamientos.ics`.
3. Siempre el mismo ISBN/editorial de la ficha; si no hay día exacto, mostrar «Previsto para noviembre» **sin botón** que invente día.
4. No cargar frameworks, mapas, servicios de cookies, nuevas cron ni cuentas externas para esta función. HTML anchor hacia el `.ics` generado. El navegador/cliente decide apertura/importación.

**Estado del catálogo real consultado 21/10:** ninguno de sus 26 libros tiene `fecha_publicacion` posterior a 21/10/2026. Por eso `lanzamientos.ics` se generaría **vacío** hasta añadir libros próximos confirmados. Esto es un criterio correcto, no un fallo.

### Fuente de código libre realmente copiada (sin modificar)

Se investigó [`adamgibbons/ics`](https://github.com/adamgibbons/ics), paquete ICS **ISC**, para no reinventar escape de TEXT en una futura interfaz navegador. Se guardaron en [`vendor/ics/`](vendor/ics/):
- [`format-text.js`](vendor/ics/format-text.js) idéntico a [upstream](https://github.com/adamgibbons/ics/blob/master/src/utils/format-text.js), **Git blob SHA `a2d5aba38dc2aabd0cceec05ca4b71a9a18010a1`**.
- [`LICENSE.upstream`](vendor/ics/LICENSE.upstream) idéntica a [licencia original](https://github.com/adamgibbons/ics/blob/master/LICENSE), **Git blob SHA `f6c77f6045bd3fd3af651f05596bc5f0696c7e2f`**.
- Ambas copias se compararon **byte a byte en GitHub**. Es una utilidad JS autocontenida para el escape de campos de texto; **todavía no está importada** porque el generador Python stdlib ya implementa escape localmente. **No vendorizamos el paquete entero ni `fold-line.js`**, que depende de `runes2` y añadiría tamaño/instalación a nuestra web sin ventaja.

[Siete pruebas sintéticas](tests/test_reading_release_calendar_preview.py) ejecutadas el 27/10/2026 (pasan): fechas exactas, rechazo de borradores, UID, VALARM, plegado UTF-8, enlace Google Calendar, ISBN duplicado y estabilidad diaria del feed cuando la ficha no cambia.

## 3. SEO, comparación UX y comercial: no tirar lo que ya funciona

- **Mantener** las fichas `/recomendaciones/libros/<slug>/`, página de autor, editorial, `Book` JSON-LD, Pagefind, tags, paginación, enlaces Amazon con tag y refrescos independientes. No crear un sistema nuevo de valoración/precio ni hacer búsquedas en APIs por visita.
- Planeta [clasifica novedades por tipo](https://www.planetadelibros.com/libros-novedades/p/1) (ficción, no ficción, fantasía, manga) y permite descubrir «Próximamente». **Podemos adoptar esa forma visual** de agrupar estrenos, alimentándola con nuestro catálogo, sin copiar sus páginas ni su diseño.
- Entrada SEO coherente: **«Próximos lanzamientos de libros en español»**, con fechas reales, filtros por género ya existentes, ediciones, autor y breve contexto; los meses no se convierten automáticamente en 12 páginas indexables. [Google recomienda contenido útil y no páginas hechas solo para buscadores](https://developers.google.com/search/docs/fundamentals/creating-helpful-content?hl=es).
- Google [Book actions feed](https://developers.google.com/search/docs/appearance/structured-data/book) **no es un objetivo de integración** para una web de recomendaciones: es un programa especial de proveedores con catálogos amplios y enlaces directos para comprar/prestar, no una mejora de SEO garantizada por añadir una etiqueta. Mantener el `Book` real de la ficha.
- Evaluar en Search Console consultas a `próximos libros de fantasía`, `libros que salen noviembre`, `[título] fecha lanzamiento`, y sesiones desde Pinterest `utm_source=pinterest` que llegan a fichas. Medir CTR e interacciones sin prometer ventas.

## 4. Hoja de ruta mínima para Codex / Claude, sin desordenar el repo

1. **P1 — verificar Planeta con HTML real**: capturar 20 productos desde índice, ajustar parser a markup de verdad, tests fixture + licencias/caché, calcular nuevos ISBN vs Penguin; si aporta poco o markup poco estable, **descartar** fuente sin tocar el publicador.
2. **P2 — integrar solo el adapter que pase QA**: introducir `provider` dispatch, **eliminar** suposición `url suffix = ISBN`, resolver fechas y editoriales y reutilizar el core de #661/#665. No añadir segundo cron ni API de pago.
3. **P3 — calendario ligero**: integrar ICS generator en mismo build, solo si hay próximos libros con día confirmado; tests de calendar normalización y fechas, enlace directo en ficha/tarjeta, diff cero a páginas existentes.
4. **P4 — medir y decidir**: número de ISBN únicos, % fichas que completan autor+foto+sinopsis, Pagefind/sitemap/CWV de lanzamiento, clicks «Guardar», visitas orgánicas y Amazon/UTM. No inferir causalidad de conversión por número de libros.
5. **QA**: la PR **no ejecuta** tests ni Actions ni merge ni publicación. Los 13 casos sintéticos son código escrito en carpeta aislada de investigación; exigir QA real antes de considerarlo listo.

**Limitación intencionada**: esta PR recopila investigación y prototipos *utilizables* sin modificar `scripts/reading_intake_pipeline.py`, `build-reading-catalogue.py`, `data/reading-catalogue.json`, imágenes, precios, Pinterest, workflow o enlaces ya publicados.
