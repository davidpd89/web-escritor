# Atlas literario mundial — ÍNDICE CANÓNICO Y DECISIONES (ADR-000)

Actualizado **21 de octubre de 2026**. Esta es la **única referencia vigente** para producto, decisiones, dependencias y estados. El resto de archivos de esta PR y sus hijas contienen evidencia o investigación **histórica**, no nuevas decisiones por defecto. Ante contradicción: este ADR > código validado de la PR hija > notas antiguas. La decisión definitiva antes del merge exige revisar el código y los tests.

**Situación:** [PR padre #666](https://github.com/davidpd89/web-escritor/pull/666) y [#667–#673](https://github.com/davidpd89/web-escritor/pulls). Ninguna rama fusionada ni web alterada por este programa. No ejecutar Actions, workflows ni despliegue sin orden.

## 1. Alcance y rutas — DECISIONES

| ID | Decisión vigente | Motivo |
|---|---|---|
| ADR-01 | Nombre editorial **Viajes literarios**, ruta heredada **/atlas-literario/** | [#59](https://github.com/davidpd89/web-escritor/pull/59) dejó builder para esa ruta; evitar duplicar /viajes-literarios/; confirmar canonical actual antes del desarrollo |
| ADR-02 | Cobertura objetivo **mundial y multilingüe**; idioma UI español inicialmente | Madrid/París únicamente pilotos, no límites |
| ADR-03 | Tres puertas conectadas: **destino → lugares; libro → lugares; autor → lugares**, además de rutas posteriores | **Un solo grafo**, nunca tres catálogos redundantes |
| ADR-04 | Relación factual **por vínculo** y tipo: escenario de obra, inspiración, biografía pública, rodaje de adaptación, homenaje | Un POI Overture o una placa no prueban que una escena literaria ocurra allí |
| ADR-05 | Catálogo comercial de obras y enlaces Amazon en **/recomendaciones/**, no duplicar libros ni cambiar importador | [#660](https://github.com/davidpd89/web-escritor/pull/660), [#661](https://github.com/davidpd89/web-escritor/pull/661) |
| ADR-06 | Candidatos masivos **fuera** del HTML público; publicar solo registros aprobados con evidencia y contenido editorial real | Evitar spam SEO, información falsa y exposición de datos privados |
| ADR-07 | Fuentes mundiales principales: **Open Library dumps** (obras), **Wikidata CC0** (vínculos candidatos), **Overture Places/Geofabrik** (POIs), **GeoNames** (identidad geográfica), **FilmMap CC0** (rodajes de adaptaciones candidatos); fuentes oficiales para confirmar | Gratis en acceso a datos según condiciones; CPU/disco/hosting no necesariamente gratuitos |
| ADR-08 | **Site estático y HTML SSR/generado**, datos JSON por ciudad/destino + índice pequeño, JS de filtros sólo si se interactúa, mapa por demanda | No penalizar home, Core Web Vitals, crawl ni carga inicial |
| ADR-09 | Facetas UX: país, ciudad, libro, saga, autor, POI, tipo de relación, ruta y época **cuando exista evidencia**; **sin generar una URL indexable por combinación** | Google advierte sobre espacios de URLs de navegación por facetas |
| ADR-10 | Google Sheets para **revisión editorial**, no backend de visitantes; snapshots auditables. **Un solo publicador serializado**, aprovechando el pipeline #661 cuando se autorice | Evitar carreras de sitemap/Pagefind/content-registry; primera tanda por PR manual |
| ADR-11 | **Código externo solamente con licencia válida**: conservar upstream íntegro por archivo, licencia, SHA y aviso; no copiar datasets de libros ni fotos sin permiso | Repo público ≠ autorización de copia o relicencia |
| ADR-12 | Las PR hijas están **en draft** y son independientes de main; ejecutar suites/QA y revisar compatibilidad antes de marcarlas listas. **El usuario controla merges.** | No simular estado probado |

## 2. Estado real y orden de trabajo

| PR | Una responsabilidad | Estado actual / bloqueo antes de merge |
|---|---|---|
| [#666](https://github.com/davidpd89/web-escritor/pull/666) padre | ADR canónico, auditoría #59 y referencias | Documentación, draft |
| [#667](https://github.com/davidpd89/web-escritor/pull/667) | Datasets/APIs globales; Overture y FilmMap CC0, taxonomía septiembre 2026 | Investigar licencia de cada fuente/uso de dump; contrastar métricas divergentes |
| [#668](https://github.com/davidpd89/web-escritor/pull/668) | **Archivo upstream con licencias MIT/BSD/ISC**: Read the Places, mapas/facetas, Simplify, Supercluster y servidor FilmMap MCP | No están integrados ni ejecutados; dependencia de Astro/TS/Bun/sharp y derechos de teselas |
| [#669](https://github.com/davidpd89/web-escritor/pull/669) | Contrato JSON Schema/validador relacional | Validación real no ejecutada; hay que fijar migración y eliminar ambigüedades del esquema |
| [#670](https://github.com/davidpd89/web-escritor/pull/670) | Orquestación, fases, publicación serializada | Es diseño, no cron ni publicador implementado |
| [#671](https://github.com/davidpd89/web-escritor/pull/671) | Extractor **parcial** de Works dump de Open Library | No tiene checkpoint global ni adaptador Wikidata; **nunca** describirlo como cobertura mundial completa |
| [#672](https://github.com/davidpd89/web-escritor/pull/672) | Prototipo HTML/SEO + facetas por ciudad + JS progresivo | Vista previa, no integrada al shell/sitemap/CSP/Pagefind; QA pendiente; filtro global libro/autor aún por resolver |
| [#673](https://github.com/davidpd89/web-escritor/pull/673) | Overture GeoJSON **por bbox pequeño** y taxonomía CSV verificada | No es importador mundial GeoParquet; adaptar `places` al contrato antes del lanzamiento |
| [#675](https://github.com/davidpd89/web-escritor/pull/675) | Pleiades: nombres, periodos y centro aproximado de topónimos históricos | Solo JSON individual y candidatos; NO genera escenario de novela ni ficha web |

**Orden recomendado sin apilar código entre ramas:** #667/#668 como referencias; #669 como contrato; #671/#673 como candidatos; importar/deduplicar y revisar en Sheets (PR futura); #672 con vista pública; coordinar publicación de #661 y SEO real (PR futura). Las PR documentales pueden revisarse sin compilar. Nunca suponer que una rama draft es «mergeable» sin QA.

## 3. Métrica Overture — dos cifras legítimas, no declarar una única verdad

**Explorador oficial de taxonomía versión `2026-09-23.0`**: [78.517.770](https://docs.overturemaps.org/guides/places/taxonomy-browser/) en su interfaz. **Notas oficiales de la versión `2026-09-23.0`**: [81.455.425](https://docs.overturemaps.org/blog/2026/09/23/release-notes/) *Places* (y ruta de parche `2026-09-23.1`). Las fuentes **no coinciden**, posiblemente conteos/filtros/actualización distintos; **NO usar 78M u 81M como cifra exacta de plazas importables sin reconciliar con manifiesto de release**. Ambas son puntos de interés genéricos, **no** relaciones literarias.

Regla: **fijar `provider_release`, versión de esquema y taxonomía por lote**; `taxonomy` y `basic_category` reemplazan `categories` desde septiembre 2026. El [CSV 2026-09-23.0](https://github.com/OvertureMaps/docs/blob/main/static/taxonomy/2026-09-23.0/taxonomy.csv) confirma `bookstore`, `used_bookstore`, `academic_bookstore`, `comic_books_store`, `library`, `museum`, `historic_site` y `memorial_site`. NO inferir historicidad literaria de un taxón.

## 4. Contrato vigente, sin multiplicar versiones de arquitectura

- **9 colecciones de primera fase**: `destinations`, `places`, `works`, `authors`, `adaptations`, `sources`, `relationships`, `images`, `routes`. Un nodo tipo común de esquema NO es una décima entidad.
- `source` acredita procedencia/derechos; `relationship` acredita vínculo específico con obra/autor/adaptación. **No reemplazar uno por otro**.
- Los lugares reales con historia literaria pública pueden tener ficha sin novela concreta solo con fuente oficial y texto propio; una novela sin escena geolocalizable no recibe pin falso.
- Identificadores OSM type+id, Overture GERS, GeoNames, Open Library Work ID, Wikidata QID; claves internas estables. Distinguir obra de edición ISBN.
- Precisión geográfica `point/building/area/city/unlocated`, no publicar coordenada de edificio para zona narrativa inferida.
- En Sheets el registro es editorial; la web consume **proyección pública minimizada**, no el snapshot crudo ni notas de revisión.

## 5. Plan de interfaz SEO/performance

- URLs indexables con utilidad: hub /atlas-literario/, destinos aprobados, lugares aprobados; **obra** enlaza a /recomendaciones/libros/<slug>/ cuando la tenga, autor a ficha propia existente cuando proceda; rutas en fase posterior.
- Índices precompuestos por país/destino y **páginas HTML completas**. Filtros interactivos combinados sólo para navegación, no URLs infinitas indexables.
- Mapas externos al principio; miniaturas estáticas/licenciadas opcionales; mapa interactivo solo a petición. Objetivos p75 LCP ≤2,5 s, INP ≤200 ms, CLS ≤0,1 **sin afirmar medidas**.
- Google eliminó el *sitelinks search box* en noviembre 2024. El código MIT `SearchAction` de Read the Places está archivado **como fuente, no como especificación vigente**.
- Cualquier CSS/HTML vendorizado Astro se **adapta al site shell existente**, nunca se introduce una segunda home/framework por comodidad.

## 6. Control de cambios — mantener orden sin documentos contradictorios

- Este README es el **registro de decisiones**. Los docs numerados `00…08` de #666 son investigación por fecha. **NO seguir agregando decisiones contradictorias a cada uno**; si cambia una decisión, actualizar **aquí**, poner fecha y motivo.
- Las hijas tienen cada una **1 scope**, documentación de uso y pruebas pendientes. No crear nuevas PR para el mismo problema si cabe corregir su rama actual.
- Auditoría previa a integración: lista de decisiones ADR y diffs contra main, licencias, compatibilidad con #660/#661/#665 ya fusionadas y #662 aún abierta, tests locales autorizados, SEO, seguridad, peso de JS, Pagefind, sitemap, canonical, no URLs huérfanas, QA móvil/desktop y verificación en producción.
- Ningún Action, test ni merge ejecutado en esta ronda. Los hallazgos no suponen que algo ya esté desplegado.

## 7. Próximo desarrollo concretamente definido (no abierto/ejecutado)

1. Corregir y comprobar contrato #669, normalizador de IDs y CSV/Google Sheets.
2. Importar candidates Open Library/Overture con checkpoint real, Wikidata P840/P915, deduplicación y atribución.
3. Construir **proyección publicable** y 3 plantillas homogéneas con shell existente (destino/lugar/ruta opcional); enlazar desde catálogo sin duplicar libros.
4. Indexación Pagefind, sitemap y JSON-LD de entidades verificadas; filtros país, ciudad, obra y autor con shards.
5. QA real + permisos de fuentes + pruebas de rendimiento, publicación por PR manual; automatizar escritor serial después de estabilizar.

### 21/10/2026 — hallazgo adicional en cobertura de rodajes

[Flightmussy/filmmap-dataset](https://github.com/Flightmussy/filmmap-dataset) tiene instantánea **CC0** de agosto 2026 con 15.272 lugares/161 países/12.762 producciones según su README. [#667](https://github.com/davidpd89/web-escritor/pull/667) documenta importación. [#668](https://github.com/davidpd89/web-escritor/pull/668) contiene una copia literal MIT del servidor MCP asociado, **sin integrar** ni incluir la base compacta que necesita para funcionar. Es fuente de P915 rodaje (cine/TV) y P840 ambientación de otras clases audiovisuales, nunca prueba de escena individual ni de novela; combinar con obra original solo si la adaptación concreta se demuestra. Film commissions municipales como [DataSF](https://data.sf.gov/Culture-and-Recreation/Film-Locations-in-San-Francisco/yitu-d5am/about_data) complementan la evidencia. No cambia ADR-01 a ADR-12.

### Estado de sincronización Git revisado al cierre de la ronda, 21/10/2026

Se detectó movimiento de `main` mientras continuaba esta investigación: al comparar de nuevo las PR #666–#673, **todas están 1 commit por detrás de main**, abiertas, draft y sin fusionar. **No se ha intentado hacer rebase, actualizar rama, merge ni ejecutar Actions**, para no generar ejecuciones de CI o conflictos involuntarios. Antes de revisión final hay que inspeccionar el commit entrante de main, comprobar que no altera `data/atlas-literario.json`, shell, sitemap ni catálogo, y recién entonces revalidar las PR implicadas. Este estado es un corte temporal, no una propiedad permanente del repositorio.

**Verificación posterior de la divergencia con main:** el commit `d31181d6287798f5d8447b7f371559a766d7cfe7` fusionó [PR #665 — catálogo generalista/UX/filtros/reseñas](https://github.com/davidpd89/web-escritor/pull/665) el **21/10/2026 a las 12:10 UTC**. Afectó a `data/reading-catalogue.json`, `assets/reading-catalogue.js/css`, configuración de automatización, Pagefind y RSS. Por tanto **#665 YA ESTÁ FUSIONADA** y deja de ser una dependencia draft. **#662 sigue abierta** en la verificación de esta ronda. Prioridad antes de integrar Atlas: revisar el nuevo contrato de catálogo y los procesos de publicación resultantes; no actualizar ramas ni ejecutar Actions automáticamente.

### Nuevas fuentes mundiales verificadas (21/10/2026): patrimonio, bibliografía e imágenes

[#667, nota 05](https://github.com/davidpd89/web-escritor/blob/research/atlas-global-fuentes-2026-10-21/docs/atlas-global/05-fuentes-no-exploradas-historia-bibliotecas-patrimonio-2026-10-21.md) cubre Pleiades (antiguo, CC BY 3.0), NHLE Historic England (OGL y atribución), Mérimée Francia (Licence Ouverte 2.0), Library of Congress authorities, BookBrainz (core CC0/API alfa) e IIIF (metadatos e imágenes con derechos **por objeto**). **Son fuentes opcionales de enriquecimiento y corroboración**, no requisito para librerías genéricas ni licencias fotográficas universales. [#675](https://github.com/davidpd89/web-escritor/pull/675) contiene adaptador especializado, sin redes ni publicación.

La [PR #670](https://github.com/davidpd89/web-escritor/pull/670) contiene ahora un [contrato operativo de integración y gates](https://github.com/davidpd89/web-escritor/blob/research/atlas-pipeline-publicacion-2026-10-21/docs/atlas-pipeline/contrato-integracion-y-gates.md) con artefactos propuestos, claves, validación, SEO, seguridad, dependencia de #661 y definition of done. El algoritmo de filtros de [#672](https://github.com/davidpd89/web-escritor/pull/672) recibió un guard para **descartar descargas de ciudad obsoletas** ante cambios rápidos de selector. Sigue sin QA ejecutado.
