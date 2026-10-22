# Investigación de GPT — índice vivo (22 de octubre de 2026)

**Estado: investigación en curso; PR madre DRAFT. No fusionar.** Este archivo es el punto de entrada cuando el usuario diga «siguiente investigación de GPT». El trabajo efectivo vive en PR hijas independientes; este índice solo contiene decisiones, prioridades y dependencias.

## 1. Punto de partida verificado en GitHub

- **En `main`**: ingesta diaria de Penguin, control de ISBN/portadas, plantillas estáticas, autores, relaciones de editoriales y autopublicación condicionada a checks (PR #661 y #665 fusionadas). `data/reading-catalogue.json`: 31 libros; `data/reading-authors.json`: 31 autores, 30 biografías con fuente; `data/editoriales.json`: 150 editoriales, 72 recepción abierta, 45 cerrada, 26 desconocida, 7 indirecta. Todas tienen sitio web; 54 incluyen correo específico de manuscritos. Son instantáneas, no promesa de frescura diaria.
- **PR #687 ABIERTA, no integrada**: 55 libros, 55 autores, 41 biografías y registro separado `data/reading-publishers.json` (11 sellos) para editoriales descubiertas en fichas, sin información automática completa de contactos ni recepción de manuscritos. Prioridad: resolver QA/CI de #687 y sincronizar nuevas ramas **sin tocarla desde aquí**.
- **Precios/valoraciones y calendarios**: #683 DRAFT (alternativas a Creators API, atribución, calendario, SEO), #680 DRAFT (Planeta y otro calendario). NO replicar su código.
- **Concursos**: #688 ABIERTA (monitor de fuentes y revisión humana; no cambiar fechas sin prueba). **Atlas de viajes literarios**: #666 DRAFT y sus hijas (investigación/prototipos, no publicado).
- Datos de partida de **22/10/2026**: comprobar de nuevo en la siguiente pasada; no presentarlos como métricas actuales sin consulta.

## 2. Investigación propia, nueva y no duplicada

| Prioridad | Línea | Vacío real | PR hija |
|---|---|---|---|
| P0 | Editoriales universales + contactos | Hay directorio de recepción y registro bibliográfico de sellos, **pero no descubrimiento y enriquecimiento integrados**; no conocemos con qué permiso acceder masivamente a la base pública ISBN | [#692 — Investigación de GPT: editoriales](https://github.com/davidpd89/web-escritor/pull/692) |
| P1 | Autores: identidad, biografías y relaciones | La biografía automática depende sobre todo de Penguin; faltan fuentes independientes y resolución de homónimos, actualización de fuentes y enriquecimiento verificable sin biografías copiadas en bloque | [#693 — Investigación de GPT: autores](https://github.com/davidpd89/web-escritor/pull/693) |
| P2 | Catálogo: fichas, SEO y escalado | Formato común para libro/autor/editorial, páginas útiles sin contenido inventado, rendimiento a 500–1000 obras, cobertura de enlaces, metadata y sincronización con #687 | [#694 — Investigación de GPT: fichas/SEO](https://github.com/davidpd89/web-escritor/pull/694) |

**Referencias preexistentes, sin nuevas PR redundantes**: #683 (precios y ratings, incl. Goodreads/Google Books y límites Amazon), #680 (fuente Planeta), #688 (concursos), #666 (Atlas), #613 (auditoría técnica global). Si surge un subtema nuevo que merezca rama, justificar aquí por qué no cabe en una existente.

## 3. Protocolo para cada pasada de investigación

1. Leer **este índice** y la **PR hija correspondiente**, consultar estado actual de `main` y de las PR relacionadas. Seleccionar el **primer experimento no resuelto**; no reformular lo que ya existe.
2. Buscar documentación primaria actual, APIs oficiales, licencias/condiciones y repositorios abiertos activos. En cada hallazgo registrar: URL, fecha de comprobación, costes/credenciales, cuotas, licencia SPDX y archivo de atribución, limitaciones, versión, resultado verificado y decisión (apto / piloto / descartado).
3. Preparar el **cambio más pequeño posible**: contrato, prueba sintética sin red, adaptador offline o fixture sintético; preferir biblioteca estándar y reutilizar scripts existentes. Reutilizar código de terceros solo con licencia explícita compatible, atribución, archivo de licencia y procedencia; **un repo público sin licencia no autoriza copiarlo**. No copiar contenido de páginas ni biografías completas por defecto.
4. Distinguir **ficha bibliográfica verificable** de **dato dinámico** (precio, contacto, recibe manuscritos, disponibilidad). Para dato dinámico: fuente primaria + marca temporal + caducidad + retirada si cambia; nunca deducir «acepta manuscritos» por silencio.
5. Medir impacto frente a la base: cobertura, rechazos, errores, peticiones externas, coste €0/mes, tamaño HTML/JSON, accesibilidad y LCP/INP/CLS. Confirmar que no hay páginas SEO vacías, duplicadas o ficticias.
6. Actualizar la PR hija en pocas líneas: qué se verificó, qué se escribió, qué falló, siguiente hipótesis. Actualizar aquí solo si cambia prioridad/decisión o aparecen PR nuevas.

**Límites de esta fase**: borradores separados basados en `main`; commits `[skip ci]`; no ejecutar tests, CI, despliegues ni merges; no modificar `main`; no activar crawling masivo, Pinterest, proveedores ni publicador diario. Una PR de investigación no constituye código listo para producción.

## 4. Fuentes iniciales contrastadas (a verificar en cada pasada)

- [Ministerio de Cultura — base de datos de editoriales españolas](https://www.cultura.gob.es/cultura/libro/isbn/base-de-datos-de-editoriales.html): inventario público alimentado por registros ISBN, incluye autores-editores y entidades esporádicas. El conjunto publicado en [datos.gob.es](https://datos.gob.es/es/catalogo/e05234201-base-de-datos-de-editoriales) declara **distribución XHTML**, no API JSON ni derecho implícito al scraping masivo.
- [DILVE — estándar ONIX](https://web.dilve.es/onix/estandar-versiones-editeur/): ONIX 3.1 soporta ISBN, editoriales, metadatos y precios; estudiar únicamente feeds autorizados, no asumir acceso libre a DILVE.
- [Open Library — API y política de uso](https://openlibrary.org/developers/api): consultas humanas de bajo volumen; su API **no** debe usarse como backend de ingesta masiva. Para lotes, dumps mensuales y política de licencia/atribución.
- [Google Books — volumen, valoraciones y ventas](https://developers.google.com/books/docs/v1/reference/volumes): metadatos de volumen, `averageRating`, `ratingsCount`, `saleInfo` condicionada por país; exigir edición/ISBN correctos, nunca confundir puntuaciones con reseñas locales.
- [Wikidata — acceso a datos](https://www.wikidata.org/wiki/Help:Data_access): desambiguación de entidades con QID y propiedades verificadas; no lanzar consultas SPARQL mundiales sin acotar ni usar la base como única evidencia de contactos.
- [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) (MIT): candidato opcional para **sugerir** coincidencias y homónimos, nunca para unir automáticamente autores/sellos de nombre similar.

## 5. Próxima ejecución

**Siguiente investigación de GPT → comenzar por la PR hija P0 (editoriales)**: comprobar fuente oficial del ISBN, disponibilidad real de datos exportables y permisos; diseñar resolución única de `data/editoriales.json` y `data/reading-publishers.json`; preparar piloto offline con tres casos de alias/homónimo y contrato de contactos/recepción. Después P1 autores y P2 fichas.

**Regla operativa:** Ninguna PR hija se fusiona directamente. Cualquier integración posterior debe conciliarse con el `main` del momento y con #687/#683/#680; Claude/Codex revisarán calidad y permisos antes de ejecutarla.
