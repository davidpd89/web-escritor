# Investigación ejecutable — ratings y precios para el catálogo (21/10/2026)

**Objetivo del propietario:** catálogo generalista y masivo de libros publicados por editoriales, 0 € recurrentes y 0 tokens IA. Cada ficha con fuente, fecha y puntuaciones/precios reales siempre que exista una fuente que los proporcione. No restringir por género.

## 1. Código abierto realmente revisado (rutas concretas)

| Implementación existente | Qué hace realmente | Decisión |
| --- | --- | --- |
| [Bookery de JoeCotellese (MIT)](https://github.com/JoeCotellese/bookery) → [hardcover.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/hardcover.py), [cache.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/cache.py), [googlebooks.py](https://github.com/JoeCotellese/bookery/blob/main/src/bookery/metadata/googlebooks.py) | GraphQL de Hardcover por ISBN, rating/ratings_count, autores y serie. Caché SQLite con TTL por proveedor/consulta/clave. Valida coincidencia de edición. | **Reutilizado el patrón**, no copiado código; `scripts/reading_ratings_refresh.py` implementa dos fuentes, valida ISBN/título/autor y conserva procedencia. Para gran catálogo, añadir caché SQLite como en `cache.py` en lugar de miles de llamadas idénticas. |
| [Hardcover API docs (MIT)](https://github.com/hardcoverapp/hardcover-docs) y [cliente gratuito Hardcover MCP](https://github.com/muhyousri/hardcover-mcp) | API GraphQL con token de cuenta; el cliente comunitario documenta **5.000 solicitudes/día y 60/min** en tier gratuito, además de datos agregados de valoraciones atribuibles a Hardcover. | Segunda fuente operativa **en código** con `--hardcover` y secreto `HARDCOVER_API_KEY`. Activarla **tras verificar condiciones vigentes en documentación de Hardcover**, asociación comercial y disponibilidad real de ISBN españoles. No mezclar medias con Goodreads/Google Books; atribuir «Hardcover». |
| [Price Tracker Playwright](https://github.com/daraakinbola/price-tracker) → [scraper.py](https://github.com/daraakinbola/price-tracker/blob/main/backend/app/scraper.py), [db.py](https://github.com/daraakinbola/price-tracker/blob/main/backend/app/db.py) | Chromium entra en Amazon.com y lee `.a-price .a-offscreen`, guarda precio histórico con SQLite. Código no prueba Amazon.es; extrae US dollars con `replace(",", "")`. **En Amazon ES «19,95 €» se convertiría erróneamente en 1995** con ese parser. Tiene selectores frágiles y fallback de número por regex. | **NO copiar/ejecutar**: ejemplos públicos no garantizan la exactitud, disponibilidad ni derecho de republicar precios de Amazon.es en un sitio afiliado. La lección útil es almacenar fuente/fecha y nunca mostrar precio si no coincide producto y moneda. Sin licencia explícita verificada, solo usar como ejemplo, no como biblioteca. |
| [Amazon Price Checker Playwright](https://github.com/afsal-backer/Amazon-Price-Checker-Using-Playwright) → [test automatizado](https://github.com/afsal-backer/Amazon-Price-Checker-Using-Playwright/blob/main/tests/amazon.spec.ts) y [workflow](https://github.com/afsal-backer/Amazon-Price-Checker-Using-Playwright/blob/main/.github/workflows/playwright.yml) | Busca `a-price-whole` en Amazon.in, compara texto con precio esperado y envía aviso. Último commit observado **14/12/2023**. No valida edición/moneda, no funciona como captador de Amazon.es ni como integrador de Afiliados. | No asumir mantenimiento actual ni reutilizar para publicación automática de precios. |
| [open-library-api-rs (MIT)](https://github.com/aVOIDSTARch/open-library-api-rs) → [obtener ratings de obra](https://github.com/aVOIDSTARch/open-library-api-rs/blob/master/README.md) | Usa `/works/OL...W/ratings.json` con `summary.average` y `summary.count`. | API REAL, pero Open Library [advierte explícitamente](https://openlibrary.org/developers/api) que **no está destinada a ser backend comercial masivo**: no configurar un cron de miles de consultas sin confirmarlo con ellos. Puede servir para pruebas puntuales o acuerdo específico. |

## 2. Buenas fuentes gratuitas para valoraciones, separadas por nombre

**A. Google Books** (fuente recomendada para empezar). [Documentación oficial de volumeInfo](https://developers.google.com/books/docs/v1/reference/volumes): `averageRating` (1–5), `ratingsCount` y `industryIdentifiers`. La API requiere identificar la app mediante `GOOGLE_BOOKS_API_KEY`: [guía oficial](https://developers.google.com/books/docs/v1/using). El código implementado:
- `scripts/reading_ratings_refresh.py --live --budget 40` consulta `q=isbn:<ISBN>`, verifica ISBN-13 **y** título/autor, conserva el volumen con más votos, produce `{libro_id,fuente:'google_books',puntuacion,numero_valoraciones,url,actualizado_en,caduca_en}`. Un libro sin rating **no recibe cero estrellas**; no se reutilizan datos de otro autor o edición.
- Puede ejecutarse en `.github/workflows/reading-catalogue-sync.yml` **una sola vez al día**, el proceso `refresh-reading-catalogue.py` ahora lo invoca incluso si no hay nuevas fichas. Se necesita configurar el GitHub Secret `GOOGLE_BOOKS_API_KEY`; de lo contrario no realiza ninguna petición y conserva el sitio.
- Presupuesto inicial **40 consultas/día** con cola rotativa por día. Con 26 libros se intentará cubrir el catálogo; al crecer a cientos o miles, **no todas las puntuaciones estarán actualizadas semanalmente** con 40/día: aumentar cuota si Google lo permite, usar TTL y priorizar fichas visitadas, o caché por ISBN. La web caduca puntuaciones a 7 días.
- `assets/reading-catalogue.js` ahora admite `google_books`, lo enlaza a `books.google.com/books?id=...` y lo atribuye claramente. Goodreads preexistente sigue mostrado mientras esté fresco, sin crear votos nuevos ni scraping.
- El origen Google Books no es «Goodreads actualizado». **No inventar atribución**.

**B. Hardcover** (complemento optativo). GraphQL `editions(where: isbn_13 eq isbn)` → `book.rating`, `book.ratings_count`, autor, slug. `scripts/reading_ratings_refresh.py --hardcover` y `HARDCOVER_API_KEY`, con `hardcover_requests_per_day=40` por defecto **solo si existe la clave**; cuenta gratuita + token, permiso oficial de medias agregadas con atribución y mostrar crédito «Hardcover». Su fuente es por **obra**: aunque se encuentra una edición por ISBN, los votos pueden agregarse a otras ediciones. No decir que son «valoraciones de esta tapa blanda específica», sino de la obra enlazada. Documentación [Hardcover API](https://api.hardcover.app/).

**C. Open Library**: endpoint rating JSON gratis, pero limitaciones expresas en API para uso continuo en un comercio. No configurada para el cron.

**D. Goodreads**: sus [condiciones oficiales](https://www.goodreads.com/about/terms) no permiten usar scrapers/robots/extracción en una página comercial sin permiso. La antigua herramienta [reviews_widget_iframe](https://www.goodreads.com/topic/show/765985-are-reviews-no-longer-available-in-the-api) exigía developer ID de una API antigua, no hay evidencia de que permita un widget nuevo hoy. Investigar solo si Goodreads ofrece actualmente widget servido por ellos y **válido para esta cuenta**; no prometerlo. Mantener un link directo a Goodreads en las fichas cuando hay libro identificado y conservar las valoraciones históricas hasta caducidad. **No diseñar bots con sesión para republicar rating de Goodreads**.

## 3. Precios de Amazon: tres caminos con orden de preferencia

**Amazon exige en sus [políticas del Programa de Afiliados](https://afiliados.amazon.es/help/operating/policies) que el precio mostrado proceda de un enlace servido por Amazon o de Creators API/PA-API autorizada**. Consecuencia: no basta con que Playwright consiga leer un precio. Amazon.es puede variar por cuenta, CP, terceros, moneda, formato y sesión; guardar «16,95 €» sin producto/ASIN/fecha no es fiable. La cuenta reportó `AssociateNotEligible` en Creators API.

1. **Candidato gratis más prometedor SIN API:** comprobar en Amazon Afiliados ES → **Crear enlaces → Enlaces de productos → vista optimizada (Enhanced Product Link)**. La [ayuda de Amazon.es](https://afiliados.amazon.es/help/node/topic/G5KVDATAT5RKBBBG) describe expresamente un enlace optimizado **servido por Amazon** que incluye el precio dinámico. Si la interfaz actual ofrece esa opción **para su ID de afiliado**, probar el HTML legítimo de Amazon en **Coraline** con ASIN concreto, comprobar precio real durante un día y probar responsive, cookies y accesibilidad. Este método solo cubre productos directos, **NO** búsquedas ISBN generales. Los documentos actuales de SiteStripe solo garantizan el enlace de texto y no bastan para prometer el widget; verificar **en la propia cuenta** antes de desplegar.
2. **Cuando Amazon autorice Creators API**, generar precio con el adaptador oficial, cotejar ASIN y caducar a <=24h, no almacenarlo indefinidamente.
3. **Sin fuente oficial**, mostrar siempre CTA `Consultar precio en Amazon` con `tag=davidporto-21`. Es automático y lleva al dato actual en Amazon, pero **no es un precio visible en nuestra web**. Para ofrecer un filtro de gasto sin esa API, se podría usar **PVP de editorial**, **solo** si la editorial lo publica y con etiqueta «Precio de catálogo editorial», **nunca** «Precio Amazon». Un PVP no demuestra stock/importe final en Amazon; etiquetarlo bien evita engañar.

**No habilitar extracción automática de precios publicados mediante `.a-price`** solo porque haya scripts gratuitos. El usuario podría usar inspección puntual interna de precio, pero eso **no autoriza reproducirlo como precio vigente de Amazon en la web afiliada**.

## 4. Esquema y flujo del sistema ya modificado en PR #665

```
RSS/editoriales → libros en data/reading-catalogue.json → misma GitHub Action diaria
                                                        ↓
       GOOGLE_BOOKS_API_KEY (opcional) → Google Books ISBN → ratings fuente Google
       HARDCOVER_API_KEY (opcional) → Hardcover ediciones → ratings fuente Hardcover
                                                        ↓
              assets/reading-market.json (Goodreads heredado aparte)
                                                        ↓
              generated-only PR → checks → main → deploy Pages → filtro rating
```

Archivos ya modificados:
- `scripts/reading_ratings_refresh.py`: cliente Google Books + Hardcover, fuentes atribuidas, ISBN + autor + título y cuota, modo fixture o live explícito.
- `assets/reading-catalogue.js`: reconocimiento y presentación de `goodreads`, `google_books` y `hardcover` con URL del propio proveedor, nunca suma o promedia votos cruzados.
- `scripts/refresh-reading-catalogue.py`: actualiza ratings aunque editoriales devuelvan **cero libros nuevos**, sin añadir segundo escritor.
- `scripts/publish-reading-refresh.py`: añade `assets/reading-market.json` a los cambios publicables tras QA.
- `data/reading-intake-config.json`: `ratings_refresh.enabled`, 40 Google/day y 40 Hardcover/day, cada fuente solo si está configurada su clave.
- `.github/workflows/reading-catalogue-sync.yml`: recibe secretos sin imprimirlos.
- `tests/test_reading_ratings_refresh.py` y `.github/workflows/reading-general-catalogue-ux-qa.yml`: ISBN exacto, rechazo homónimo/otra edición, sin votos, errores 429, presupuesto, dos fuentes independientes y JS sintácticamente válido.

**Limitaciones que hay que cerrar en CI antes de activar:** no se puede afirmar que haya una API key de Google Books en los secrets. Añadirla manualmente en GitHub Secrets, probar `--live` con 3 ISBN y reportar **cobertura real**. Comprobar que un PR con solo `assets/reading-market.json` se publica/despliega a través del gate y el SHA publicado. Los cambios iniciales del builder de PR #665 obligan además a regenerar HTML de las 26 fichas y `recomendaciones/index.html` antes de fusionar: tests focalizados no equivalen a gate universal aprobado.

## 5. Qué debe ejecutar Codex, sin repetir investigación

```bash
# Offline y sin credenciales, desde esta rama:
python -m unittest discover -s tests -p 'test_reading_ratings_refresh.py' -v
node --check assets/reading-catalogue.js
# Luego instalar clave oficial, prueba acotada:
GOOGLE_BOOKS_API_KEY=<secreto> python scripts/reading_ratings_refresh.py --live --budget 3 --out .ci/reading-intake/ratings-pilot.json
# Revisar cuántos ISBN devuelven rating y las URLs exactas; no cambiar productivo antes de QA.
```

**Aceptación mínima para «actualización automática»:** una ejecución **programada real** con secret, un libro puntuado con enlace a proveedor correcto, valoración que caduca/oculta sin reintento, otro libro sin votos sin estrellas falsas, un día con cero libros nuevos pero rating actualizado en un PR separado protegido que despliegue, y un fallo 429 que conserva los datos viejos. Todos los tests del generador y página en verde. Los precios Amazon aún dependen de verificar Enhanced Links o API autorizada, no de un bot.

### Verificación nueva en documentación oficial de Hardcover
En [`hardcoverapp/hardcover-docs/src/content/docs/api/Getting-Started.mdx`](https://github.com/hardcoverapp/hardcover-docs/blob/main/src/content/docs/api/Getting-Started.mdx), sección «Commercial API Use», se permite explícitamente usar **aggregate data** en un sitio comercial **si se atribuye a Hardcover**. No permite recuperar datos individuales de las bibliotecas personales, reseñas o ratings de usuarios sin autorización; no estamos haciendo eso. La API exige que el token permanezca en el servidor, no en JS. El proveedor nuevo únicamente consulta valoraciones agregadas de la obra. **No reutilizar imágenes subidas por usuarios a Hardcover** para nuestras fichas/Pinterest.
