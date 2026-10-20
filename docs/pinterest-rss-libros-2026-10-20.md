# Encargo operativo a Codex — Pinterest automático desde el catálogo web (20/10/2026)

**PR independiente de #661:** no espera ni pisa el motor de captación de libros. La PR #660 también está abierta y puede cambiar el esquema del catálogo. La rama principal de esta PR se creó desde `main`; rebasar/ajustar campos antes de integrar.

## Descubrimiento decisivo: Pinterest publica pines AUTOMÁTICAMENTE desde RSS

**Esta es la arquitectura elegida por el propietario: 0 € / 0 llamadas GPT / sin OAuth Pinterest en el cron**:

```
Amazon / Google Books / editoriales → web-escritor (PR #661 cuando exista)
   → solo libro con ficha pública /recomendaciones/libros/<slug>/
   → portada REAL alojada por davidportodiaz.com
   → scripts/build-reading-pinterest-rss.py
   → un feed RSS 2.0 por intención/tablero
   → Pinterest Business: "Crear Pines en lote → Conectar feed RSS" (UNA VEZ)
   → pin de Pinterest → ficha web del mismo libro
   → clic voluntario en portada/botón de ficha → Amazon.es con el tag de afiliado
```

Pinterest confirma oficialmente:
- Cuenta **Business** + **dominio reclamado**; la opción de conectar RSS solo se muestra con web reclamada.
- Admite feeds RSS 2.x y RSS 1.x, **NO Atom**. Metadatos de `<item>`: `<title>`, `<description>`, `<link>` al dominio reclamado e imagen mediante **una** etiqueta `media:content` / `enclosure` / `image`.
- Varios feeds y un tablero distinto por feed. Pinterest crea pines al actualizarse el feed en **hasta 24 h**, publica **primero el contenido más antiguo**, permite hasta **200 pines al día**. Ese máximo no es objetivo: empezar con **2 al día** y contenido diferenciado.
- NO asegura que un GUID impida al 100 % los duplicados; probar con un solo pin, auditar la publicación y dejar estable GUID/URL/media en las repeticiones.
- Un Pin enlaza al destino indicado en `<link>`. NUNCA meter enlace Amazon ni imagen de Amazon Creators API en el RSS para redirigir a web.
- **No usar Pinterest Product Pins / catálogo de merchant**: no vendemos el libro dentro de nuestra web, sino que la ficha informa y remite a Amazon. Nuestra finalidad es **tráfico editorial**, no Merchant Program.

Guías oficiales (consultadas el 20/10/2026):
- https://help.pinterest.com/es/business/article/auto-publish-pins-from-your-rss-feed
- https://help.pinterest.com/es/business/article/claim-your-website
- https://help.pinterest.com/es/business/article/pin-performance-and-distribution
- https://help.pinterest.com/es/article/review-pin-specs
- https://help.pinterest.com/es/business/article/pinterest-trends
- https://help.pinterest.com/es/business/article/pinterest-analytics
- https://help.pinterest.com/es/business/article/rich-pins

## Estado REAL del repo de RRSS privado (verificado)

`https://github.com/davidpd89/rrss-davidporto-CODE` existe y es **privado**. Se han leído sus archivos **actuales**, no ejemplos inventados:

- `00_OPERATIVO/README.md`, `00_OPERATIVO/01_CONTEXTO_UNICO.md`: el flujo manda; piezas revisables.
- `00_OPERATIVO/REDES/pinterest/estrategia.md`: Pinterest es buscador visual; keyword antes que hashtag, tablero SEO, imágenes verticales, enlace a página exacta; **ritmo editorial 2 pines/día**, un tablero nuevo con al menos 10 pines previstos.
- `SISTEMA_DIARIO_PINTEREST/ESTADO.md`, `PROCESO.md`, `REGLAS.md`: desde 28/09 **publicación manual**; Metricool está cancelado, **NO USAR**; hay problemas históricos de links a home/IDs visibles/reutilización de imágenes IG.
- `tools/pinterest_execute.py`: **preflight offline** del contrato `manual_pin` (copy, ALT, media, tablero, link específico); **NO PUBLICA**.
- `tools/pinterest_scan.py`: stub deshabilitado, NO reutilizar.
- `tools/pinterest_api_audit.py` y `SISTEMA_DIARIO_PINTEREST/AUDITORIA_API_OFICIAL.md`: auditoría opcional **lectora** de API v5 con identidad @davidportodiaz, paginación, títulos, links, ALT y métricas, **no publicación**.
- `SISTEMA_DIARIO_PINTEREST/PENDIENTES.md`: reclama de `davidportodiaz.com` figura **pendiente**; no asumirlo conectado, ni afirmar que existen todos los tableros históricos en la cuenta.
- `00_OPERATIVO/REDES/pinterest/estrategia.md` enumeraba "Libros de fantasía juvenil", "Portal fantasy y mundos mágicos", "Samuel entre mundos" y otros tableros. Reutilizar los nombres existentes si ya los tiene; adaptar otros a necesidades reales y **verificar en Pinterest antes de duplicar**.

**Conclusión:** reutilizar las decisiones/editoriales y el preflight; NO copiar una supuesta autenticación existente. El RSS nativo de Pinterest evita crear app, OAuth, SDK y programador. No editar el repo privado sin un encargo cruzado: esta PR afecta a la web y registra qué comprobar allí.

## Trabajo de código ya incorporado en ESTA PR

- `scripts/build-reading-pinterest-rss.py` sin dependencias externas:
  - Requiere `estado=publicado`, **ruta HTML real** `/recomendaciones/libros/<slug>/index.html`, portada local auténtica ya existente `/assets/reading-covers/...webp/jpg/png`, título/autor/descripción.
  - Un libro → **un solo tablero principal**. Prioriza novedades con fecha editorial diaria verificada y después nichos temáticos; no crea 6 pines de Coraline porque tenga 6 categorías.
  - Cola estable `data/reading-pinterest-state.json`, `--assign` explícito, 2 nuevos libros/día total, GUID fijo por libro, fecha de cola guardada para no publicar todos los libros históricos a la vez ni duplicar tras regeneración.
  - Escribe XML `assets/pinterest/feeds/<tablero>.xml`: estos `assets/` están incluidos por `scripts/build-public-dist.py` y su `.assetsignore`. Cada item incluye **un solo** `media:content`, título SEO, descripción natural y `link` SIEMPRE a `https://davidportodiaz.com/recomendaciones/libros/<slug>/?utm_source=pinterest&utm_medium=organic&utm_campaign=<tablero>&utm_content=<libro_id>`. La canonical HTML de la ficha queda sin UTM.
  - `--preview` y `--check` para revisión y CI. **No crea tableros online ni pines en la cuenta**.
  - Sin llamadas a ChatGPT/LLM/Metricool/Pinterest API/Amazon API; datos ya preparados por PR #661, no depende de Amazon Creators API.
- `data/reading-pinterest-boards.json`: propuestas de nombres, descripciones, prioridades, palabras clave y ritmo. **Flag funcional `rss_enabled=false`**: los XML son válidos pero **sin ítems**, y `--assign` falla de forma expresa. Solo ponerla en `true` tras preparar/vincular la cuenta, comprobar el dominio y disponer el primer piloto. Desactivar no borra los pines ya publicados en Pinterest.
- `tests/test_reading_pinterest_rss.py`: RSS válido, XML con tildes, imágenes correctas, un tablero por libro, no duplicados, cola 2/día y borradores excluidos.
- `scripts/export-reading-pinterest-plan.py`: genera un JSON opcional `manual_pin` a partir de la misma cola; se puede validar con `tools/pinterest_execute.py` del repositorio privado RRSS, sin copiar código ni activar publicación. Es SOLO respaldo/manual y no debe usarse para publicar el mismo libro que ya haya entrado por RSS.
- Pendiente Codex: pruebas CI, integración real en el batch final de #661 (build → RSS → public-dist → deploy), imágenes de pin 2:3 de mejor calidad y verificación RSS/ALT en Pinterest.

## Preparación de tableros SEO — empezar con pocos, no vacíos

Propuestas en `data/reading-pinterest-boards.json`, basadas en la estrategia existente, **keywords a investigar, NO volúmenes demostrados**:

| Orden de la regla | Tablero propuesto | Cuándo usarlo | Motivo de búsqueda |
|---|---|---|---|
| 1 | **Novedades de fantasía y romantasy** | Libro de nicho con fecha editorial completa, últimos 90 días | "novedades de fantasía" |
| 2 | **Libros de terror y fantasía oscura** | Terror, fantasía oscura, Halloween, misterio | "libros de fantasía oscura"; "libros para Halloween" |
| 3 | **Libros de romantasy y fantasía romántica** | Romantasy / romance | "libros de romantasy" |
| 4 | **Portal fantasy y mundos mágicos** | Portales, mundos paralelos | "fantasía de portales" |
| 5 | **Libros de fantasía juvenil** | General / resto | "libros de fantasía juvenil" |

**No crear automáticamente 5 tableros vacíos.** Primero verificar los tableros existentes y mantener alias/nombre si el usuario ya tiene uno útil. Tras mínimo 10 libros elegibles por tablero o autorización expresa, crear los adicionales desde la cuenta Business; usar **un feed independiente por tablero**.

Ejemplo de URLs **futuras al desplegar la PR** (no afirmar que ahora respondan 200):
- `https://davidportodiaz.com/assets/pinterest/feeds/fantasia-juvenil.xml`
- `https://davidportodiaz.com/assets/pinterest/feeds/terror-fantasia-oscura.xml`
- `https://davidportodiaz.com/assets/pinterest/feeds/novedades-fantasia.xml`

### Conexión manual inicial: imprescindible, luego automática

1. En la cuenta Pinterest Business, comprobar si `davidportodiaz.com` aparece en **Sitios reclamados**.
2. Si no: `Configuración → Vincular a Pinterest → Reclamar sitio web`, copiar **meta HTML real de Pinterest**, ponerla en `<head>` de la web (o subir fichero verificable a raíz / TXT DNS), desplegar y pulsar **Verificar**. Nunca inventar una etiqueta de verificación. No publicar pines hasta confirmar.
3. Crear o elegir tablero público por categoría, con nombre/descrición SEO y contenido suficiente. No probar con tableros secretos si se desea alcance.
4. `Configuración → Crear Pines en lote → Publicar automáticamente → Conectar feed RSS`: pegar la URL XML de **ese tablero** y seleccionar ese tablero.
5. Piloto: un pin de **Coraline** (solo una vez, verificar que no esté ya publicado). Comprobar título, descripción, URL de imagen, clic a la ficha exacta y enlace afiliado solo desde la ficha web; comprobar ALT y dimensiones visualmente. Pinterest crea el pin hasta 24 horas después; no marcarlo publicado antes de verlo.
6. Añadir otros tableros gradualmente. **Una vez conectados**, nuevas fichas en web entran en RSS y Pinterest las puede crear sin tokens ni programador externo.

La vinculación de dominio y la configuración de feeds requieren sesión y acción inicial en la cuenta. Esta PR **NO puede ejecutar esas operaciones** a través de GitHub.

## Creatividad visual y SEO — priorizar experimentos reales

**Oficial confirmado**: Pinterest recomienda formato vertical **2:3 ≈ 1000×1500**, imagen nítida, contexto y coincidencia de palabras clave con la página de destino. Título de Pin máx. 100 caracteres, descripción máx. 800; la descripción no aparece habitualmente en el feed pero Pinterest la usa para relevancia. `webp` figura admitido como imagen orgánica. No asumir que la imagen de cubierta vertical pero estrecha obtiene rendimiento idéntico a un diseño 2:3. La documentación recomienda contenido original semanalmente y advierte de repetición de pines.

**Primer ciclo**: utilizar la **cubierta real** de la edición, alojada en la web, sin descargar la imagen Amazon API ni crear una cubierta ficticia. **Siguiente mejora visual**: imagen vertical editorial realizada con foto humana real del libro físico o estantería de verdad; recortar sin deformar la cubierta, texto superpuesto de 3–8 palabras en español y legible en móvil, producida con Pillow/plantilla local **solo si hay fotos reales verificadas**. Imagen separada de la ficha si conviene. No generar ilustración fantasy de una portada bajo nombre real.

**Ejemplos de títulos a testear (hipótesis)**:
- `Coraline: fantasía oscura para Halloween`
- `Coraline, de Neil Gaiman: terror juvenil y misterio`
- `5 libros de fantasía juvenil con mundos paralelos` — SOLO cuando el destino sea un artículo LISTA de 5 libros, jamás la ficha de 1 libro.

**Descripción de Coraline de ejemplo, diferente del titular visual:**
"En su nueva casa, una puerta conduce a una versión inquietante del hogar. Consulta los datos de la edición española de Coraline, sus géneros y dónde leer un fragmento antes de decidir tu próxima lectura."

NO usar reseña personal `me encantó`, `lo he leído`, bestseller, fecha, precio, valoración ni prometer capítulo salvo URL verificada. No copiar literalmente el texto de la imagen en el caption.

**Investigación de posicionamiento** cuando esté disponible la cuenta:
- https://trends.pinterest.com/ → seleccionar **España**; contrastar consultas y estacionalidad por 90/365 días. Pinterest Trends muestra índice relativo **0–100**, **NO búsquedas mensuales absolutas**, y parte de funcionalidades dependen de región/cuenta.
- Comparar los cinco nichos del catálogo y variantes naturales: `libros de fantasía juvenil`, `romantasy en español`, `libros de fantasía oscura`, `libros para Halloween`, `novedades de fantasía`, `mundos paralelos libros`. Registrar fecha, región, índice, keyword y tablero.
- No automatizar Trends API ahora: documentación oficial indica que está enfocada a agencias, Enterprise y partners, no acceso universal. No usar scraping de sugerencias para fabricar métricas.
- Test A/B: no publicar versiones clonadas de una misma portada en un período breve. Una variante real posterior con nuevo encuadre o título, solo si justificada por datos.
- KPI principal: **clics salientes por impresión**, luego sesiones con UTM que visitan ficha y clics en Amazon; también guardados. Ni impresiones ni clics garantizan compras.
- Análisis mensual en Analytics; refinar tableros, keywords, títulos y composiciones, no rellenar texto de hashtags.

## Criterios obligatorios antes de dar el sistema por terminado

1. Reutilizar y no alterar el CSS, plantillas, SEO y canonical de #660; conservar perfil, editorial y futuras fechas de novedades de #661.
2. En fase preparatoria ejecutar `--preview` con `rss_enabled=false`; genera planificación **sin escribir ficheros ni publicar**. Tras conectar Pinterest, activar `rss_enabled=true` en el JSON, ejecutar `python scripts/build-reading-pinterest-rss.py --assign` y seguidamente `--check` en el **mismo día**, repetir para comprobar idempotencia. No simular el feed activo si la conexión real sigue pendiente.
3. XML RSS 2.0 con `media:content`, un item por libro, imagen alojada en la web, destino con UTM a ficha. Publicaciones futuras programadas no aparecen antes de fecha. Solo entradas públicas válidas.
4. `assets/pinterest/feeds` incluido en artefacto Pages (el builder actual `assets/` lo incluye). Verificar feed HTTP 200 y `Content-Type` aceptado por Pinterest antes de conectar.
5. Colas: 2 pines/día **global**, con **una sola cola para todas las categorías**, sin pines duplicados por libros multicategoría ni por ejecución repetida.
6. Evitar que una modificación ordinaria de texto o nueva etiqueta cambie un `guid` o copie otra vez el mismo pin.
7. Todos los tableros están propuestos, no creados. Verificación de cuenta Business, dominio y creación/conexión en Pinterest requieren autorización/acción inicial de David.
8. Probar piloto Coraline en un solo tablero y verificar que el clic llega a la ficha y luego Amazon afiliado. No afirmar publicación hasta ver URL real del pin.
9. Fuente RSS del catálogo **actualizada en el ciclo que publique las nuevas fichas**; si solo ejecutamos RSS cuando alguien haga merge, no es automático. Integrar en el cron único de #661, o cron propio de RSS **sin dos workflows escribiendo los mismos ficheros**. Por ahorro y consistencia, reutilizar la fase final del cron de #661.
10. Medir 30 días y revisar posibles pines duplicados y semántica del campo ALT en los RSS, que la guía no garantiza explícitamente. Si la API de Pinterest está aprobada en el futuro, considerar cliente `pinterest/pinterest-python-generated-api-client` (endpoints Create Pin/Board) como alternativa, **sin reemplazar un RSS que funcione**.

## Referencias open source comprobadas

- https://github.com/pinterest/api-quickstart (Python OAuth y API oficial; requiere app aprobada, no necesario para RSS).
- https://github.com/pinterest/pinterest-python-generated-api-client (modelos/endpoints Pin/Board; opción futura para ALT o métricas).
- https://github.com/aewshopping/history_books/blob/main/.github/workflows/build-and-deploy.yaml (ejemplo real de GitHub Actions para catálogo; **no** resuelve Pinterest).
- `rrss-davidporto-CODE/tools/pinterest_execute.py` y `pinterest_api_audit.py` (reutilizables como especificación de revisión, sin publicador; nunca exponer URL del repo privado fuera de la sesión).

**El servicio nativo RSS de Pinterest es precisamente la solución ya existente que buscábamos**: más simple que hospedar nuestro propio bot/API y compatible con el motor automático de libros en preparación.

## Revisión de fallos corregidos después de contrastar fuentes oficiales (20/10/2026)

Fuente oficial actual consultada: [Pinterest: autopublicar desde RSS](https://help.pinterest.com/es/business/article/auto-publish-pins-from-your-rss-feed), [Pinterest: distribución](https://help.pinterest.com/es/business/article/pin-performance-and-distribution) y [Pinterest: conectar sitio](https://help.pinterest.com/es/business/article/claim-your-website). La documentación confirma RSS 1.x/2.x (no Atom), `media:content`, un `link` por item al dominio reclamado, creación en 24h, **contenido antiguo primero** y múltiples feeds por tablero. También advierte que crear repetidos puede tratarse como spam. **El RSS conecta pines, no garantiza impresiones ni conversiones.**

Tres regresiones detectadas y corregidas con tests offline:

1. **Novedades de fantasía no equivale a cualquier novedad.** El primer prototipo clasificaba todo libro reciente en ese tablero. Ahora exige **fecha completa de la edición y coincidencia con categorías de fantasía/romantasy** (lista de slugs de `data/reading-pinterest-boards.json`), sin mezclar poesía, ensayo u otros nichos.
2. **Cambio de categoría/antigüedad no puede trasladar un pin programado a otro feed.** Los registros `data/reading-pinterest-state.json` conservan `board_slug` fijo. Incluso cuando termina la ventana de 90 días, el pin **permanece en el mismo RSS**, con GUID estable y sin perderse antes de que Pinterest lo importe.
3. **Activación controlada de RSS.** `rss_enabled=false` en el JSON significa que **los XML se generan VACÍOS de libros**. La CLI `--assign` se niega a asignar nuevas publicaciones mientras esté desactivada. `--preview` sí informa qué libros serían elegibles/qué cola se generaría, sin persistir nada. CI activa RSS solo dentro de un runner efímero y verifica `--assign --check --assign --check`.

**Limitación que persiste (no inferir otra cosa):** aunque el estado tenga un calendario de 2 pines/día, Pinterest no tiene acceso al estado interno, solo al XML público. Si el propietario **activa el feed pero espera semanas antes de conectarlo a Pinterest**, pueden acumularse muchas entradas vencidas y Pinterest importarlas al conectar. Por eso no activar `rss_enabled=true` hasta el **día real de conexión**, probar primero con Coraline, y comprobar cuántos `<item>` son visibles. Codex debe ofrecer una opción `--max-initial-items=1` / modo primer piloto o documentar procedimiento equivalente antes del despliegue real.

**Otro riesgo pendiente:** Pinterest menciona que puede crear pines de **varias imágenes** dentro de un item e incluso de páginas con varias imágenes. Nuestro XML expone un solo `media:content`; aun así, auditar el primer pin publicado y no asumir que Pinterest solo interpretará una imagen de la página enlazada. Si produce duplicados, limitar creatividades o cambiar a API v5 aprobada. No dar por resuelta esta semántica solo con una prueba XML.

**Qué debe ejecutar Codex cuando toque activar:**

```bash
python -m unittest discover -s tests -p 'test_reading_pinterest_rss.py' -v
python scripts/build-reading-pinterest-rss.py --preview --today 2026-10-20
# Una vez rss_enabled=true en configuración:
python scripts/build-reading-pinterest-rss.py --assign
python scripts/build-reading-pinterest-rss.py --check
python scripts/export-reading-pinterest-plan.py --out .ci/pinterest/manual-review.json
python scripts/build-public-dist.py --out .preview-dist
python scripts/build-public-dist.py --check-contents --out .preview-dist
```

**Prueba final obligatoria**: consultar la URL RSS desplegada (respuesta 200 XML); verificar nombre de tablero **existente** en Pinterest, pin real y destino web, imagen real sin deformación, botón Amazon voluntario, carga móvil, y persistencia en ejecuciones posteriores sin duplicados. Después de #661 integrar RSS en el **mismo workflow que actualiza el catálogo** y comprobar que se refresca cada día incluso cuando no aparecen libros nuevos.
