# #704 · Contrato público y composición segura de estadísticas sociales

**22/10/2026 · PR hija de #699.** El cambio es un **compositor de datos ejecutable y probado**, NO una página desplegada. Ningún cambio a `autor.html`, navegación, Actions o `main`.

## QA de las cuatro PR — resultado definitivo (22/10/2026)

**152/152 pruebas offline correctas y 0 omitidas**, ejecutadas en un directorio temporal con archivos contrastados por sus **hashes Git idénticos** a las ramas de #704, #705, #706 y #707. Python 3.13: **130** casos; Node 22: **22** casos. No hay lecturas live, CI/Actions ni merge.

**Problemas reales corregidos durante la revisión:** una prueba cruzada seguía esperando tres elementos aunque ahora hay seis perfiles (los otros tres pueden quedar `pending`). Además, se limitó la caducidad máxima verificable por el lector JS a 48 h desde `generated_at`: aunque un JSON erróneo declare `valid_until=2099`, no podrá mostrar contadores indefinidamente. El productor Python rechaza números superiores a `2**53-1` o sumas que superen el rango de enteros exactos en JavaScript; el lector JS no muestra totales imprecisos. Las cinco regresiones nuevas pasan.

**Nuevo ejecutor reproducible:** [`scripts/research/run_social_cross_pr_qa.sh`](../../../../scripts/research/run_social_cross_pr_qa.sh) lee **16 archivos exactos** de las cuatro refs remotas y comprueba SHA antes de ejecutar las pruebas. No modifica el working tree, no fusiona ramas, no ejecuta Actions, no consulta APIs y borra sus temporales. El ejecutor también se probó en un repositorio Git sintético local con esas mismas versiones: **130 Python + 22 Node PASS**. Tras `git fetch` de las cuatro ramas (comando completo más abajo):

~~~bash
bash scripts/research/run_social_cross_pr_qa.sh
~~~

Cobertura por archivo: compositor **37**; pipeline entre cuatro lectores **8**; identidades **10**; fechas/caducidad/precisión numérica **9**; Metricool un campo **17**; Metricool multired **18**; Bluesky **13**; Mastodon **18**; lector Node **19**; contrato Python→JS **3**. Los **17 casos exploratorios** antiguos quedan expresamente fuera del total. Los únicos datos utilizados en todas las pruebas son sintéticos.

**Sigue pendiente:** acceso real a Bluesky/Mastodon (DID/ID), automatización de la extracción Metricool, HTML/CSS/navegación de la página y suite global del sitio. Esta puerta valida el **código de estadísticas**, no el despliegue.

## Problema concreto

Los lectores de #705 (Metricool/Threads), #706 (Bluesky) y #707 (Mastodon) producen **objetos distintos**: Metricool identifica `observed_at` con `YYYY-MM-DD` de un día cerrado y las APIs públicas incluyen hora UTC. Si sumamos sus seguidores sin validar fechas, identidad y nulos, el dashboard puede mostrar cifras antiguas, duplicadas, de otro perfil o un «total» presentado como personas únicas.

**Solución implementada:** [scripts/research/gpt_social_compose.py](../../../../scripts/research/gpt_social_compose.py) recibe registros de los lectores o el lote `metricool-follower-candidates` de #705. Del lote **selecciona Threads, Instagram, TikTok y Pinterest** porque los identificadores de las cuentas conectadas a Metricool coinciden con los enlaces ya presentes en la web. Ignora los candidatos de Bluesky (se mantiene AppView), Facebook, X y YouTube. Hay [37 casos unitarios declarados](../../../../tests/test_gpt_social_compose.py): 27 de la versión anterior y 10 nuevos para este contrato.

Las URL canónicas de **estas seis redes** proceden de `autor.html` y `scripts/build-site-shell.py` (revisados en el repositorio vigente). Los identificadores conectados de Instagram, TikTok, Pinterest, Threads y Bluesky se han cotejado con `getBrandSettings` de Metricool el 22/10/2026. No se publican en Git el ID interno de marca, el correo de titular ni sus cifras. No introducir URLs devueltas por APIs sin comparar antes con esas fuentes.

## Comportamiento del código

1. Reconoce exclusivamente `bluesky`, `mastodon`, `threads`, `instagram`, `tiktok` y `pinterest`. Rechaza IDs desconocidos, repetidos, enlaces diferentes de los oficiales y también fuentes asignadas a la red equivocada (`bluesky-public-appview`, `mastodon-public-search`, `metricool-mcp-export`). Faltantes figuran como `pending`; no se transforman en cero.
2. Acepta seguidores solo si son un entero no negativo (**`True` no es `1`**). `views_30d`, `impressions_30d` e `interactions_30d` deben ser `null` o estar ausentes: ninguna vista ambigua puede sumarse.
3. Normaliza ISO con zona horaria para Bluesky/Mastodon y fechas de cierre de día `YYYY-MM-DD` para Metricool con `zoneinfo.ZoneInfo("Europe/Madrid")`. Rechaza días inacabados y marcas temporales futuras.
4. Política **provisional y explícita de frescura: 48 horas** desde la observación. Un seguidor de fecha caducada se convierte en `null` con estado `stale` y **sale del total**. El resumen informa de cobertura, p. ej., «2 de 6 redes con datos vigentes». Ese plazo es una decisión editorial propia, NO una obligación de ninguna API.
5. El sumatorio se denomina **«Seguidores sumados en redes con datos vigentes (no personas únicas)»**. No presupone que la misma persona no siga dos redes; `coverage/eligible` cuentan las **seis redes admitidas**, no todas las redes sociales del autor.
6. No copia del origen `DID`, ID local, token ni datos auxiliares. El formato público contiene exclusivamente `id`, `profile_url` canónica, `followers`, `observed_at`, `source`, `status`, fecha de generación y sumatorio/cobertura.
7. Salida por defecto a **stdout**. Si se indica `--output`, escribe temporal en el mismo directorio y reemplaza con `os.replace`; errores de formato no sobrescriben el archivo anterior. Bloquea `--output` sin fuentes y destino igual a un archivo de entrada. **No** se añadió un workflow ni escritura automática al directorio público.

### Ejecución reproducible (sin servicios externos)

~~~bash
python -m unittest discover -s tests -p 'test_gpt_social_compose.py' -v
python scripts/research/gpt_social_compose.py  # JSON válido, 3 cuentas pending, ningún cero inventado

# Solo después de obtener y validar snapshots privados de #705-#707:
python scripts/research/gpt_social_compose.py \
  /ruta/privada/bluesky.json /ruta/privada/mastodon.json /ruta/privada/threads.json \
  --output /tmp/social-metrics.json
~~~

Salida estructural sin cifras inventadas:

~~~json
{
  "schema_version": 1,
  "generated_at": "2026-10-22T12:00:00Z",
  "networks": [
    {
      "id": "bluesky",
      "profile_url": "https://bsky.app/profile/davidportoescritor.bsky.social",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "mastodon",
      "profile_url": "https://mastodon.social/@davidportodiaz",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "threads",
      "profile_url": "https://www.threads.com/@davidportodiaz",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "instagram",
      "profile_url": "https://www.instagram.com/davidportodiaz/",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "tiktok",
      "profile_url": "https://www.tiktok.com/@davidportoescritor",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    },
    {
      "id": "pinterest",
      "profile_url": "https://www.pinterest.com/davidportodiaz/",
      "followers": null,
      "observed_at": null,
      "valid_until": null,
      "source": null,
      "status": "pending"
    }
  ],
  "totals": {
    "follower_relationships": null,
    "valid_until": null,
    "coverage": 0,
    "eligible": 6,
    "label": "Seguidores sumados en redes con datos vigentes (no personas únicas)"
  }
}
~~~

La fecha del ejemplo representa una ejecución de prueba, no un dato extraído de una API. La futura ruta `data/social-metrics.generated.json` se mantiene **sin crear**; el programa permite probar en `/tmp` antes de autorizar la publicación.

## Pruebas cruzadas sin fusionar PR

[tests/test_gpt_social_pipeline.py](../../../../tests/test_gpt_social_pipeline.py) importa **los propios normalizadores de las tres PR hermanas**, construye respuestas sintéticas, compone sus salidas, escribe un fichero real en un directorio temporal y valida cifras y privacidad. Si esas ramas no están presentes, los **8 tests quedan `skipped`**: la PR #704 aislada no afirma tener los módulos de las otras hijas.

Reproducción exacta de la prueba cruzada en un directorio local temporal desde un checkout del repositorio. Solo lectura: **NO merge, NO Actions, NO commits y NO métricas reales**:

~~~bash
git fetch origin \
  +refs/heads/research/gpt-social-ux-2026-10-22:refs/remotes/origin/research/gpt-social-ux-2026-10-22 \
  +refs/heads/research/gpt-social-metricool-2026-10-22:refs/remotes/origin/research/gpt-social-metricool-2026-10-22 \
  +refs/heads/research/gpt-social-bluesky-2026-10-22:refs/remotes/origin/research/gpt-social-bluesky-2026-10-22 \
  +refs/heads/research/gpt-social-mastodon-2026-10-22:refs/remotes/origin/research/gpt-social-mastodon-2026-10-22

tmp="$(mktemp -d)"
mkdir -p "$tmp/scripts/research" "$tmp/tests"
copy_from() {
  git show "origin/$1:$2" > "$tmp/$2"
}
copy_from research/gpt-social-ux-2026-10-22 scripts/research/gpt_social_compose.py
copy_from research/gpt-social-ux-2026-10-22 tests/test_gpt_social_compose.py
copy_from research/gpt-social-ux-2026-10-22 tests/test_gpt_social_pipeline.py
copy_from research/gpt-social-metricool-2026-10-22 scripts/research/gpt_metricool_threads.py
copy_from research/gpt-social-metricool-2026-10-22 tests/test_gpt_metricool_threads.py
copy_from research/gpt-social-metricool-2026-10-22 scripts/research/gpt_metricool_followers.py
copy_from research/gpt-social-metricool-2026-10-22 tests/test_gpt_metricool_followers.py
copy_from research/gpt-social-bluesky-2026-10-22 scripts/research/gpt_social_bluesky.py
copy_from research/gpt-social-bluesky-2026-10-22 tests/test_gpt_social_bluesky.py
copy_from research/gpt-social-mastodon-2026-10-22 scripts/research/gpt_social_mastodon.py
copy_from research/gpt-social-mastodon-2026-10-22 tests/test_gpt_social_mastodon.py

python -m unittest discover -s "$tmp/tests" -p 'test_gpt_*.py' -v
~~~

**Histórico anterior a este cambio:** 81/81 pruebas offline pasadas en la combinación de cuatro lectores, sin red. **Validación de esta ampliación:** 35/35 pruebas locales correctas (18 unitarias del lector multired #705, siete de integración local lector→compositor y diez casos nuevos equivalentes a los añadidos a #704). Se comprobaron contra blobs de GitHub los hashes exactos de `gpt_social_compose.py` (hash de la prueba histórica: `8b69952d`; hash actual verificado en el ejecutor), `gpt_metricool_threads.py` (`cccaa4cf`), `gpt_metricool_followers.py` (`4acede8b`) y su test de 18 casos (`9e09f449`). **Estado actualizado:** el conjunto completo de 152 pruebas versionadas ya se ejecutó correctamente; los números anteriores son históricos.

**Casos de integración:** las tres salidas producen suma y cobertura correctas; archivos fuente → CLI → JSON público; salida sin DID ni ID local; los seguidores caducados no inflan totales; vistas no verificadas se rechazan; identidades falsas se rechazan antes de componer.

**Pendiente:** comprobar Bluesky/Mastodon contra las API reales, integración del frontend, accesibilidad y transporte automatizado de Metricool. Las 81 pruebas offline NO equivalen a despliegue funcional.

## Protección probada contra JSON caducado (actualización 22/10/2026)

**Problema:** el compositor conserva el último archivo correcto si fallan todos los lectores, pero un frontend ingenuo que mire el campo almacenado `status=ok` puede seguir mostrando seguidores obsoletos **indefinidamente** si no se ejecuta el generador. No basta con filtrar la caducidad cuando se escribe.

**Código nuevo ya incluido, sin tocar la web publicada:**

- [`scripts/research/gpt_social_compose.py`](../../../../scripts/research/gpt_social_compose.py) añade `valid_until` UTC por red a partir de la observación y la política provisional de **48 h**; en `totals.valid_until` registra la **primera caducidad** de las redes que participan en el sumatorio. Los `null` no se convierten en cero.
- [`scripts/research/gpt_social_reader.mjs`](../../../../scripts/research/gpt_social_reader.mjs): selector de lectura para la futura página estática. Comprueba `valid_until` con el reloj real del navegador y **recalcula los totales** únicamente con contadores vigentes; nunca confía ciegamente en `totals.follower_relationships` ni en el `status=ok` que quedó almacenado. Solo devuelve los seis IDs admitidos, no expone URL externas del JSON y diferencia cero de ausencia.
- [`tests/test_gpt_social_expiration.py`](../../../../tests/test_gpt_social_expiration.py): **7 pruebas Python**, incluidas fechas UTC, expiración del día cerrado de Madrid, zero/null, suma y cambio de horario del 25/10/2026.
- [`tests/test_gpt_social_reader.mjs`](../../../../tests/test_gpt_social_reader.mjs): **16 pruebas Node.js** de caducidad, cifra cero, duplicación, fuente incorrecta, tiempo futuro, total almacenado manipulado y URL externa inyectada.
- [`tests/test_gpt_social_python_to_js.mjs`](../../../../tests/test_gpt_social_python_to_js.mjs): **3 pruebas de contrato cruzado reales**. Node invoca el compositor Python por subprocess con datos sintéticos, consume **el JSON que emite**, y verifica que tras 48 h los números desaparecen aunque el archivo y su estado original permanezcan. Nada de red, credenciales o Actions.

### Comandos localmente ejecutados

~~~bash
python -m unittest discover -s tests -p 'test_gpt_social_expiration.py' -v
node --test tests/test_gpt_social_reader.mjs tests/test_gpt_social_python_to_js.mjs
~~~

**Resultados:** 7/7 Python y 19/19 Node (16 de lector + 3 cruces) PASS; también se reejecutaron **35** pruebas locales anteriores del puente Metricool→compositor. En esa sesión se obtuvieron **42 Python + 16 Node = 58 pruebas locales correctas** en total; 17 de los 42 Python corresponden a pruebas exploratorias locales del puente que no forman parte de estos archivos de la PR. Ese subtotal es histórico, no representa el total: el resultado vigente es **152/152 offline**. Los cinco ficheros nuevos/modificados se cotejaron por hash Git blob con la versión probada.

**Integración pendiente:** el módulo MJS de lectura está preparado pero **no se importa todavía desde ninguna página**; hasta que se construya `/redes-sociales/` no se puede afirmar que el navegador público o su caché hayan sido comprobados. La UI deberá leer `data/social-metrics.generated.json` y usar **solo** el resultado de `visibleSocialMetrics(snapshot)`, junto con enlaces de perfil canónicos de la web. Si no hay métricas vigentes, mostrar las tarjetas y ocultar cifras/totales en lugar de un cero ficticio.

## Verificación realizada

**Versión anterior:** 27/27 pruebas unitarias del compositor, con hash verificado. **Versión nueva:** diez casos añadidos al mismo fichero (37 declarados), más dos pruebas cruzadas nuevas en `test_gpt_social_pipeline.py` (8 declaradas; saltan mientras #705–#707 están en ramas separadas). El equivalente de los diez casos nuevos y la conexión con el lector #705 pasaron localmente; repetir la suite exacta de los archivos finales al unir las ramas.

Las pruebas abarcan: formatos concretos de #705/#706, inclusión de #707; sumatorios y cobertura; `null` frente a 0; duplicados y URLs impostoras; métricas no verificadas; campos extra no expuestos; 48 h exactas y caducidad; zonas de hora de Madrid en 21 y 25/10/2026 (cambio a horario de invierno); fechas futuras y sin zona; escritura atómica; no sobrescribir cuando no hay fuentes ni cuando el destino coincide con un origen.

**No probado:** conexión real entre ramas hijas, página pública, validación con la suite del repo, compatibilidad Windows sin base IANA de zonas ni publicación automatizada. En Windows `zoneinfo` podría requerir [tzdata](https://docs.python.org/3/library/zoneinfo.html); comprobarlo antes de integración multiplataforma.

### Uso del lote MCP de ocho contadores, sin publicar redes no verificadas

~~~bash
# En un checkout combinado (sin merge en GitHub), con un export PRIVADO del MCP:
python scripts/research/gpt_metricool_followers.py /ruta/privada/metricool.json > /tmp/metricool-candidates.json
python scripts/research/gpt_social_compose.py /tmp/metricool-candidates.json /ruta/privada/bluesky.json /ruta/privada/mastodon.json --output /tmp/social-metrics.json
~~~

El compositor acepta el contenedor `metricool-follower-candidates` de #705, verifica que la solicitud corresponda al día informado y que no haya IDs duplicados ni métricas de período prohibidas, pero **selecciona `threads`, `instagram`, `tiktok` y `pinterest`**. El contador de Bluesky de ese mismo lote no sustituye su lectura AppView; se excluyen también Facebook (ID conectado distinto de la URL pública), X (no conectado a esta marca) y YouTube (canal conectado, pero sin enlace público confirmado dentro del sitio). Si no queda ninguna cifra vigente y se indicó `--output`, la salida anterior permanece intacta. **Esto valida el contrato con archivos sintéticos, no la autenticidad ni actualización automática de un export real.**

## Ampliación de 3 a 6 perfiles: evidencia real de identidad (22/10/2026)

**Comprobación de cuenta vinculada, no mera coincidencia de nombres:** `getBrandSettings` del Metricool conectado devuelve identificadores de cuenta para Instagram (`davidportodiaz`), TikTok (`davidportoescritor`), Pinterest (`davidportodiaz`), Threads (`davidportodiaz`) y Bluesky (`davidportoescritor.bsky.social`). Se compararon con los enlaces explícitos de `autor.html` y `scripts/build-site-shell.py` en GitHub; coinciden. La lectura Metricool de 21/10/2026 confirmó valores `LAST` no nulos para las ocho redes del lote. **No se documentan aquí cifras privadas ni identificadores internos.**

**Decisión aplicada al código:** ampliar `PROFILES` y `EXPECTED_SOURCES` del compositor y `NETWORKS` del lector JS **solo con Instagram, TikTok y Pinterest**. El lote Metricool puede aportar esas tres y Threads, de manera que tenemos seis perfiles elegibles con Bluesky/Mastodon leídos de sus endpoints propios. **No se ha demostrado aún extracción desatendida.** No promover automáticamente Facebook: el ID conectado no coincide directamente con la URL publicada; X no consta conectado a la marca; YouTube tiene ID de canal conectado pero no figuraba entre las URL sociales de la web inspeccionadas.

**QA realizado en la etapa de ampliación:** `python -m unittest discover -s tests -p 'test_*.py' -v` pasó **52/52 casos locales** (35 en pruebas subidas a #704/#705 y 17 exploratorios en un entorno temporal). `node --test tests/test_gpt_social_reader.mjs tests/test_gpt_social_python_to_js.mjs` pasó **19/19**. Se contrastaron los hashes Git de los dos scripts y la nueva [suite de 10 pruebas de identidad](../../../../tests/test_gpt_social_verified_profiles.py) con los archivos de estas ramas. **Actualizado:** los 37 del compositor y toda la suite cruzada ya se ejecutaron con los archivos actuales; resultado total **152/152 offline**.

**No equivale a seis conectores funcionando en producción:** la web aún no importa el lector ni hay cron. El término «elegible» significa identidad URL verificada para el contrato, no cuenta validada como accesible públicamente en cada sesión.

## Diseño concreto del futuro bloque de la página (#704, NO implementado todavía)

- Encabezado editorial sugerido: **«Donde seguimos hablando de libros»**. Subtexto: «Lecturas, escritura y cultura, también en mis redes».
- Seis tarjetas previstas, **Bluesky, Mastodon, Threads, Instagram, TikTok y Pinterest**, con enlaces canónicos ya presentes en la web y CTA **«Ver perfil»** hacia cada cuenta oficial. No simular una acción «Seguir» que requiera autorización del visitante.
- Mostrar seguidores solo si `status=ok`; si `stale` o `pending`, mostrar **«Dato no disponible»** o **«Última cifra sin actualizar»** con fecha si existe.
- Encima de las tarjetas, mostrar suma **solo con `coverage > 0`** y la cobertura visible (**«X de 6 redes con datos vigentes»**). Nunca presentar la cifra como comunidad única ni extender «3» a las demás cuentas activas.
- Sin JS, enlaces y contenido principal deben seguir accesibles; no usar iframes ni terceros para obtener métricas desde el navegador. Los SVG pueden extraerse de iconos **ya existentes** en el shell; consultar antes de importar librerías adicionales.

## Fuentes y por qué se eligió esta implementación

- **Código comprobado del repositorio:** `scripts/build-human-site-stats.py` ya genera JSON local en la arquitectura GitHub Pages estática. Se reutiliza **el patrón de separar generador y dato publicado**, no sus métricas de libros.
- [JSON Schema, especificación y pruebas oficiales](https://json-schema.org/understanding-json-schema/reference/object): los objetos permiten propiedades adicionales si no se prohíben explícitamente. El compositor aplica **lista permitida de campos de salida**, sin vendoring de validadores ni dependencias; la [suite oficial](https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft2020-12/additionalProperties.json) demuestra el comportamiento que se evita. No se ha copiado código de terceros a esta PR.
- [Python `zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) calcula el huso de Madrid con DST; [`os.replace`](https://docs.python.org/3.13/library/os.html#os.replace) permite sustitución atómica en el mismo filesystem.

**Puerta de integración para Claude:** confirmar identidad real y lectores de #705–#707; conectar el lector MJS de caducidad al HTML antes de mostrar números; decidir el TTL definitivo; ejecutar la suite global del sitio y crear la UI/navigation/sitemap solo en PR aparte cuando esté aprobado. **No confundir las pruebas offline con un despliegue.**
